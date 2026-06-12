#!/usr/bin/env python3
"""
Live score poller for FIFA World Cup 2026.
Runs via GitHub Actions every minute, or can run locally.
Polls free public APIs and updates Supabase with live scores, minutes, status.
"""
import urllib.request, json, os, sys, time

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://mnprhloxeqybmqcljpuq.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ucHJobG94ZXF5Ym1xY2xqcHVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk5NTI2NjMsImV4cCI6MjA5NTUyODY2M30.y5nUUb-Xw8cPQjMJjeUrpDv2BfFYFlaYq20SyCz76Bo')

def supabase(method, path, body=None):
    url = f'{SUPABASE_URL}/rest/v1/{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('apikey', SUPABASE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_KEY}')
    if body:
        req.add_header('Content-Type', 'application/json')
        req.add_header('Prefer', 'return=representation')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f'  Supabase error: {e}')
        return None

def fetch_json(url, headers=None):
    """Fetch JSON with proper User-Agent."""
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f'  Fetch error: {e}')
        return None

# ── World Cup match ID mapping ──
# We have 104 matches in Supabase (id 1-104)
# Need to map external API match IDs to our IDs
# For now, we match by team names + date

def get_db_matches():
    """Get matches from Supabase that are today or yesterday."""
    today = time.strftime('%Y-%m-%d')
    # Get matches from last 2 days through next 1 day
    r = supabase('GET', f'matches?select=*&order=id&match_date=lte.{today}')
    return r if r else []

def get_external_scores():
    """
    Try multiple free sources and return normalized match data.
    Returns list of {home_team, away_team, home_score, away_score, status, minute, injury_time}
    """
    # Source 1: openfootball worldcup.json (post-match results)
    try:
        data = fetch_json('https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json')
        if data and 'rounds' in data:
            print('  Using openfootball data')
            return parse_openfootball(data)
    except Exception as e:
        print(f'  openfootball failed: {e}')

    # Source 2: Try sofascore-style API
    try:
        # World Cup 2026 unique ID on Sofascore
        data = fetch_json('https://api.sofascore.com/api/v1/unique-tournament/16/season/56966/events/round/1')
        if data and 'events' in data:
            print('  Using sofascore data')
            return parse_sofascore(data)
    except Exception as e:
        print(f'  sofascore failed: {e}')

    return []

def parse_openfootball(data):
    """Parse openfootball worldcup.json format."""
    results = []
    for round_data in data.get('rounds', []):
        for match in round_data.get('matches', []):
            if match.get('score') and match['score'].get('ft'):
                ft = match['score']['ft']
                base_status = 'finished'
            elif match.get('score') and match['score'].get('ht'):
                base_status = 'halftime'
            else:
                continue  # skip unplayed matches

            results.append({
                'home_team': match.get('team1', {}).get('name', ''),
                'away_team': match.get('team2', {}).get('name', ''),
                'home_score': match.get('score', {}).get('ft', [None, None])[0],
                'away_score': match.get('score', {}).get('ft', [None, None])[1],
                'status': base_status,
                'minute': match.get('minute', 90) if base_status == 'finished' else match.get('minute', 0),
                'injury': match.get('injury_time', 0),
            })
    return results

def parse_sofascore(data):
    """Parse sofascore API format."""
    results = []
    for event in data.get('events', []):
        home = event.get('homeTeam', {}).get('name', '')
        away = event.get('awayTeam', {}).get('name', '')
        score = event.get('homeScore', {})

        status_type = event.get('status', {}).get('type', '')
        if status_type == 'finished':
            status = 'finished'
        elif status_type == 'inprogress':
            status = 'live'
        elif status_type == 'halftime':
            status = 'halftime'
        else:
            continue

        results.append({
            'home_team': home,
            'away_team': away,
            'home_score': score.get('current', event.get('homeScore', {}).get('normaltime', 0)),
            'away_score': event.get('awayScore', {}).get('current', 0),
            'status': status,
            'minute': event.get('status', {}).get('displayTime', 0) if status == 'live' else 90,
            'injury': event.get('status', {}).get('injuryTime', 0)
        })
    return results

def match_to_db(external, db_matches):
    """Match external data to database match IDs by fuzzy team name matching."""
    for dbm in db_matches:
        h_match = fuzzy_match(external['home_team'], dbm.get('home_team', ''))
        a_match = fuzzy_match(external['away_team'], dbm.get('away_team', ''))
        if h_match and a_match:
            return dbm['id']
    return None

def fuzzy_match(a, b):
    """Simple fuzzy match - one contains the other or share key words."""
    a_clean = a.lower().strip().replace(' ', '').replace('-', '')
    b_clean = b.lower().strip().replace(' ', '').replace('-', '')
    if a_clean == b_clean:
        return True
    # One contains the other
    if len(a_clean) >= 4 and len(b_clean) >= 4:
        if a_clean in b_clean or b_clean in a_clean:
            return True
    return False

def update_match(match_id, fields):
    """Update a single match in Supabase."""
    # Only update if data actually changed
    current = supabase('GET', f'matches?id=eq.{match_id}&select=home_score,away_score,status,match_minute,injury_time')
    if not current or len(current) == 0:
        print(f'  Match #{match_id} not found in DB')
        return False

    cur = current[0]
    changed = False
    for key in ['home_score', 'away_score', 'status', 'match_minute', 'injury_time']:
        if key in fields and fields[key] != cur.get(key):
            changed = True
            break

    if not changed:
        return True  # no update needed

    result = supabase('PATCH', f'matches?id=eq.{match_id}', fields)
    if result:
        m = result[0]
        print(f"  ✅ #{match_id} {m.get('home_team','')} {m.get('home_score','')}-{m.get('away_score','')} {m.get('away_team','')} [{m.get('status','')}] minute={m.get('match_minute','')}")
        return True
    return False

def main():
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Polling live scores...')

    # Get matches that need updating (today's matches that have scores or are live)
    db_matches = get_db_matches()
    if not db_matches:
        print('  No matches in DB')
        return

    # Filter to matches that could be live (today + have scores set or are already live/finished)
    active_matches = [m for m in db_matches
                      if m.get('home_score') is not None
                      and m.get('status') in ('live', 'halftime', 'upcoming', 'finished')]

    print(f'  DB matches total: {len(db_matches)}, active: {len(active_matches)}')

    # For now, the auto-minute-ticker approach:
    # If a match is "live" in DB, auto-increment its minute every run (~60s)
    # This handles the display timer without needing external source
    for m in active_matches:
        if m['status'] == 'live':
            cur_min = m.get('match_minute') or 0
            cur_inj = m.get('injury_time') or 0

            # Don't auto-tick past 45 in first half or 90 in second
            if cur_min < 45:
                new_min = cur_min + 1
                new_inj = cur_inj
                new_status = 'live'
            elif cur_min == 45:
                # Don't auto-advance past HT - operator must set halftime status
                new_min = cur_min
                new_inj = cur_inj
                new_status = 'live'
            elif cur_min < 90:
                new_min = cur_min + 1
                new_inj = cur_inj
                new_status = 'live'
            else:
                # 90+ — auto-increment injury
                new_min = 90
                new_inj = cur_inj + 1
                new_status = 'live'

            update_match(m['id'], {
                'match_minute': new_min,
                'injury_time': new_inj,
                'status': new_status
            })

    # Also try to fetch from external sources for score updates
    external = get_external_scores()
    if external:
        for ext in external:
            mid = match_to_db(ext, db_matches)
            if mid:
                update_match(mid, {
                    'home_score': ext['home_score'],
                    'away_score': ext['away_score'],
                    'status': ext['status'],
                    'match_minute': ext['minute'],
                    'injury_time': ext['injury']
                })

    print('Done.')

if __name__ == '__main__':
    main()
