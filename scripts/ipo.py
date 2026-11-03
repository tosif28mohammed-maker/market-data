"""IPO robot (user, 3 Nov 2026: 'naye IPO ka daily update - QIB/FII/retail kitna apply, company, promoters, fundamentals').
Pulls from NSE public APIs: current issues, upcoming issues, past issues, and for every current issue the category-wise bid book.
Saves raw JSON to data/ipo/raw/<date>_<name>.json and a running table data/ipo/subscription_log.csv (one row per issue x category x run)."""
import os, json, time, datetime as dt, requests, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, 'data', 'ipo'); R = os.path.join(D, 'raw'); os.makedirs(R, exist_ok=True)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30)); now = dt.datetime.now(IST); tag = now.strftime('%Y-%m-%d_%H%M')
s = requests.Session(); s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                                          'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://www.nseindia.com/market-data/all-upcoming-issues-ipo'})
s.get('https://www.nseindia.com', timeout=20); time.sleep(1)
def get(path, name):
    try:
        r = s.get('https://www.nseindia.com/api/' + path, timeout=30); j = r.json()
        json.dump(j, open(os.path.join(R, f'{tag}_{name}.json'), 'w'), indent=1); print(name, r.status_code, len(r.text)); return j
    except Exception as e: print(name, 'ERR', e); return None
cur = get('ipo-current-issue', 'current')
get('all-upcoming-issues?category=ipo', 'upcoming')
get('public-past-issues', 'past')
rows = []
items = cur if isinstance(cur, list) else (cur or {}).get('data', []) if isinstance(cur, dict) else []
for it in items:
    sym = it.get('symbol') or it.get('companyName')
    if not sym: continue
    j = get(f'ipo-active-category?symbol={sym}', f'cat_{sym}')
    time.sleep(1)
    try:
        for c in (j or {}).get('dataList', []):
            rows.append(dict(run=tag, symbol=sym, company=it.get('companyName'), series=it.get('series'), issue_start=it.get('issueStartDate'), issue_end=it.get('issueEndDate'),
                             price_band=it.get('issuePrice'), size=it.get('issueSize'), category=c.get('category'), offered=c.get('noOfShareOffered'),
                             bid=c.get('noOfSharesBid'), times=c.get('noOfTotalMeant')))
    except Exception as e: print('parse', sym, e)
if rows:
    f = os.path.join(D, 'subscription_log.csv'); old = pd.read_csv(f) if os.path.exists(f) else pd.DataFrame()
    pd.concat([old, pd.DataFrame(rows)]).to_csv(f, index=False)
print('categories saved', len(rows))
