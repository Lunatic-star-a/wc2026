#!/usr/bin/env python3
"""Update FIFA World Cup 2026 match scores/data in Supabase.

Usage:
  python update_scores.py --match 2 --home 1 --away 0 --minute 23           # live score
  python update_scores.py --match 2 --status halftime                        # halftime
  python update_scores.py --match 2 --status live --minute 46                # 2nd half start
  python update_scores.py --match 2 --home 2 --away 1 --minute 93 --injury 3 # stoppage time
  python update_scores.py --match 2 --home 2 --away 1 --status finished      # full time
  python update_scores.py --show 1,2,3                                       # view scores

Examples for ongoing matches:
  # Korea vs Czech (match 2): goal at 35'
  python update_scores.py --match 2 --home 1 --away 0 --minute 35

  # Korea vs Czech (match 2): halftime
  python update_scores.py --match 2 --status halftime --minute 45

  # Korea vs Czech (match 2): second half, 68', Czech equalized
  python update_scores.py --match 2 --home 1 --away 1 --minute 68

  # Korea vs Czech (match 2): 90+3', Korea leads 2-1
  python update_scores.py --match 2 --home 2 --away 1 --minute 90 --injury 3

  # Korea vs Czech (match 2): full time, Korea wins 2-1
  python update_scores.py --match 2 --home 2 --away 1 --status finished
"""

import urllib.request, urllib.error, json, argparse, os, sys

SUPABASE_URL = 'https://mnprhloxeqybmqcljpuq.supabase.co'
ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ucHJobG94ZXF5Ym1xY2xqcHVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk5NTI2NjMsImV4cCI6MjA5NTUyODY2M30.y5nUUb-Xw8cPQjMJjeUrpDv2BfFYFlaYq20SyCz76Bo'

def supabase_request(method, path, data=None):
    url = f'{SUPABASE_URL}/rest/v1/{path}'
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('apikey', ANON_KEY)
    req.add_header('Authorization', f'Bearer {ANON_KEY}')
    if body:
        req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=representation')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else str(e)
        print(f'  HTTP {e.code}: {err[:300]}')
        return None
    except Exception as e:
        print(f'  Error: {e}')
        return None

def show_matches(match_ids):
    ids = ','.join(str(m) for m in match_ids)
    data = supabase_request('GET', f'matches?id=in.({ids})&select=id,match_date,match_time,home_team,away_team,home_score,away_score,status,match_minute,injury_time,group_name&order=id')
    if not data:
        print('No data returned')
        return
    for m in data:
        score = f"{m.get('home_score','-')}-{m.get('away_score','-')}"
        minute = m.get('match_minute') or ''
        injury = m.get('injury_time') or ''
        time_str = ''
        if m['status'] == 'live' and minute:
            time_str = f" {minute}'"
            if injury:
                time_str += f" (+{injury})"
        elif m['status'] == 'halftime':
            time_str = ' HT'
        elif m['status'] == 'finished':
            time_str = ' FT'
        grp = f" [{m.get('group_name','')}组]" if m.get('group_name') else ''
        print(f"  #{m['id']:3d} {m['match_date']} {m['match_time']} {m['home_team']} {score} {m['away_team']} ({m['status']}{time_str}){grp}")

def update_match(match_id, **fields):
    data = supabase_request('PATCH', f'matches?id=eq.{match_id}', fields)
    if data:
        m = data[0]
        score = f"{m.get('home_score','-')}-{m.get('away_score','-')}"
        minute = m.get('match_minute') or ''
        injury = m.get('injury_time') or ''
        extra = ''
        if m['status'] == 'live' and minute:
            extra = f" {minute}'" + (f"+{injury}" if injury else '')
        elif m['status'] == 'halftime':
            extra = ' 中场'
        elif m['status'] == 'finished':
            extra = ' 已结束'
        print(f"  ✅ #{match_id} {m['home_team']} {score} {m['away_team']} [{m['status']}{extra}]")
        return True
    return False

def main():
    parser = argparse.ArgumentParser(description='Update World Cup 2026 match scores')
    parser.add_argument('--match', type=int, required=False, help='Match ID (1-104)')
    parser.add_argument('--home', type=int, help='Home team score')
    parser.add_argument('--away', type=int, help='Away team score')
    parser.add_argument('--minute', type=int, help='Match minute (0=not started, 45=HT, 90=FT)')
    parser.add_argument('--injury', type=int, help='Injury/stoppage time minutes')
    parser.add_argument('--status', choices=['upcoming','live','halftime','finished'], help='Match status')
    parser.add_argument('--show', type=str, help='Show match data, comma-separated IDs (e.g. 1,2,3)')
    args = parser.parse_args()

    if args.show:
        ids = [int(x.strip()) for x in args.show.split(',')]
        show_matches(ids)
        return

    if not args.match:
        parser.print_help()
        return

    fields = {}
    if args.home is not None:
        fields['home_score'] = args.home
    if args.away is not None:
        fields['away_score'] = args.away
    if args.minute is not None:
        fields['match_minute'] = args.minute
    if args.injury is not None:
        fields['injury_time'] = args.injury
    if args.status:
        fields['status'] = args.status
        # Auto-reset injury_time when switching to halftime or live
        if args.status in ('halftime',):
            if args.minute is None:
                fields['match_minute'] = 45
            if args.injury is None:
                fields['injury_time'] = 0
        if args.status == 'live' and args.minute is None and args.injury is None:
            pass  # keep existing values
        if args.status == 'finished' and args.injury is None:
            fields['injury_time'] = 0

    if not fields:
        print('Nothing to update. Use --home, --away, --minute, --injury, --status')
        return

    print(f'Updating match #{args.match}:')
    for k, v in fields.items():
        print(f'  {k}: {v}')
    update_match(args.match, **fields)

if __name__ == '__main__':
    main()
