#!/usr/bin/env python3
"""
FIFA World Cup 2026 - Automatic Score Poller
Source: ESPN public API (free, no key required)
Runs: GitHub Actions every minute, or locally: python poll_scores.py
"""
import urllib.request, json, os, re, time, ssl

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://mnprhloxeqybmqcljpuq.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1ucHJobG94ZXF5Ym1xY2xqcHVxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk5NTI2NjMsImV4cCI6MjA5NTUyODY2M30.y5nUUb-Xw8cPQjMJjeUrpDv2BfFYFlaYq20SyCz76Bo')

# ESPN English team name -> our DB Chinese name
TEAM_MAP = {
    'mexico': 'Mex', 'south africa': 'RSA', 'south korea': 'KOR', 'czechia': 'CZE',
    'czech republic': 'CZE', 'canada': 'CAN', 'bosnia and herzegovina': 'BIH',
    'bosnia': 'BIH', 'united states': 'USA', 'usa': 'USA', 'paraguay': 'PAR',
    'qatar': 'QAT', 'switzerland': 'SUI', 'brazil': 'BRA', 'morocco': 'MAR',
    'haiti': 'HAI', 'scotland': 'SCO', 'australia': 'AUS', 'turkey': 'TUR',
    'germany': 'GER', 'curacao': 'CUW', 'curaçao': 'CUW', 'netherlands': 'NED',
    'japan': 'JPN', 'sweden': 'SWE', 'tunisia': 'TUN', 'ivory coast': 'CIV',
    "cote d'ivoire": 'CIV', 'ecuador': 'ECU', 'spain': 'ESP', 'cape verde': 'CPV',
    'belgium': 'BEL', 'egypt': 'EGY', 'saudi arabia': 'KSA', 'uruguay': 'URU',
    'iran': 'IRN', 'new zealand': 'NZL', 'france': 'FRA', 'senegal': 'SEN',
    'iraq': 'IRQ', 'norway': 'NOR', 'argentina': 'ARG', 'algeria': 'ALG',
    'austria': 'AUT', 'jordan': 'JOR', 'portugal': 'POR', 'dr congo': 'COD',
    'congo': 'COD', 'uzbekistan': 'UZB', 'colombia': 'COL', 'england': 'ENG',
    'croatia': 'CRO', 'ghana': 'GHA', 'panama': 'PAN',
}

# ESPN team code -> our DB Chinese name
CODE_TO_CN = {
    'Mex': '墨西哥', 'RSA': '南非', 'KOR': '韩国', 'CZE': '捷克',
    'CAN': '加拿大', 'BIH': '波黑', 'USA': '美国', 'PAR': '巴拉圭',
    'QAT': '卡塔尔', 'SUI': '瑞士', 'BRA': '巴西', 'MAR': '摩洛哥',
    'HAI': '海地', 'SCO': '苏格兰', 'AUS': '澳大利亚', 'TUR': '土耳其',
    'GER': '德国', 'CUW': '库拉索', 'NED': '荷兰', 'JPN': '日本',
    'SWE': '瑞典', 'TUN': '突尼斯', 'CIV': '科特迪瓦', 'ECU': '厄瓜多尔',
    'ESP': '西班牙', 'CPV': '佛得角', 'BEL': '比利时', 'EGY': '埃及',
    'KSA': '沙特', 'URU': '乌拉圭', 'IRN': '伊朗', 'NZL': '新西兰',
    'FRA': '法国', 'SEN': '塞内加尔', 'IRQ': '伊拉克', 'NOR': '挪威',
    'ARG': '阿根廷', 'ALG': '阿尔及利亚', 'AUT': '奥地利', 'JOR': '约旦',
    'POR': '葡萄牙', 'COD': '刚果(金)', 'UZB': '乌兹别克斯坦', 'COL': '哥伦比亚',
    'ENG': '英格兰', 'CRO': '克罗地亚', 'GHA': '加纳', 'PAN': '巴拿马',
}

STATUS_MAP = {
    'STATUS_FULL_TIME': 'finished', 'STATUS_FINAL': 'finished',
    'STATUS_IN_PROGRESS': 'live', 'STATUS_HALF_TIME': 'halftime',
    'STATUS_SCHEDULED': 'upcoming', 'STATUS_POSTPONED': 'upcoming',
}

def fetch_json(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'  Fetch error: {e}')
        return None

def supa(method, path, body=None):
    url = f'{SUPABASE_URL}/rest/v1/{path}'
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('apikey', SUPABASE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_KEY}')
    if body:
        req.add_header('Content-Type', 'application/json')
        req.add_header('Prefer', 'return=representation')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f'  Supabase error: {e}')
        return None

def translate_team(name):
    """Map ESPN English team name -> 3-letter code, then -> Chinese for DB matching."""
    key = name.lower().strip().replace('  ', ' ')
    code = TEAM_MAP.get(key)
    if not code:
        for eng, c in TEAM_MAP.items():
            if eng in key or key in eng:
                code = c
                break
    if not code:
        return name
    return CODE_TO_CN.get(code, code)

def parse_espn_clock(display_clock, period):
    """Parse ESPN clock string to (minute, injury_time)."""
    if not display_clock:
        return 0, 0
    minute, injury = 0, 0
    m = re.match(r"(\d+)'?\s*\+?\s*(\d*)'?", display_clock)
    if m:
        minute = int(m.group(1))
        injury = int(m.group(2)) if m.group(2) else 0
    else:
        nums = re.findall(r'\d+', display_clock)
        if nums:
            minute = int(nums[0])
    if period == 2 and 0 < minute < 45:
        injury = minute
        minute = 45
    return minute, injury

def poll_espn():
    """Fetch live data from ESPN public scoreboard API."""
    data = fetch_json('https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard')
    if not data:
        return []
    results = []
    for event in data.get('events', []):
        comps = event.get('competitions', [{}])[0]
        competitors = comps.get('competitors', [])
        if len(competitors) < 2:
            continue
        home, away = competitors[0], competitors[1]
        h_name = home.get('team', {}).get('displayName', '')
        a_name = away.get('team', {}).get('displayName', '')
        h_score = int(home.get('score', 0) or 0)
        a_score = int(away.get('score', 0) or 0)
        status_info = event.get('status', {})
        status_type = status_info.get('type', {}).get('name', '')
        period = status_info.get('period', 0)
        clock = status_info.get('displayClock', '')
        db_status = STATUS_MAP.get(status_type, 'upcoming')
        minute, injury = parse_espn_clock(clock, period)
        if db_status == 'upcoming' and h_score == 0 and a_score == 0 and not clock:
            continue
        results.append({
            'home_team': translate_team(h_name),
            'away_team': translate_team(a_name),
            'home_score': h_score, 'away_score': a_score,
            'status': db_status, 'match_minute': minute,
            'injury_time': injury, 'period': period, 'raw_clock': clock,
        })
    return results

def main():
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S UTC")}] Polling ESPN...')
    espn = poll_espn()
    if not espn:
        print('  No data from ESPN')
        return
    print(f'  Got {len(espn)} match(es):')
    for e in espn:
        print(f'    {e["home_team"]} {e["home_score"]}-{e["away_score"]} {e["away_team"]} '
              f'[{e["status"]}] m={e["match_minute"]} clock={e.get("raw_clock","")}')

    db_matches = supa('GET', 'matches?select=*&order=id')
    if not db_matches:
        print('  DB fetch failed')
        return

    updated = 0
    for ext in espn:
        h, a = ext['home_team'], ext['away_team']
        dbm = None
        for d in db_matches:
            if d.get('home_team') == h and d.get('away_team') == a:
                dbm = d
                break
        if not dbm:
            print(f'  WARN: No DB match for {h} vs {a}')
            continue

        fields = {k: ext[k] for k in ['home_score','away_score','status','match_minute','injury_time']}

        # Only PATCH if data actually changed
        cur = supa('GET', f'matches?id=eq.{dbm["id"]}&select=home_score,away_score,status,match_minute,injury_time')
        if cur and not any(fields.get(k) != cur[0].get(k) for k in fields):
            updated += 1
            continue

        result = supa('PATCH', f'matches?id=eq.{dbm["id"]}', fields)
        if result:
            m = result[0]
            print(f'    UPD #{dbm["id"]} {m["home_team"]} {m["home_score"]}-{m["away_score"]} '
                  f'{m["away_team"]} [{m["status"]}] m={m["match_minute"]}')
            updated += 1

    print(f'  Done: {updated}/{len(espn)} updated.')

if __name__ == '__main__':
    main()
