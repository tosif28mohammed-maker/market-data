"""Daily NSE delivery % (MTO) for the f72 filter: 'SPECULATIVE UP' = up 1.5%+ on low delivery (z<=-1 vs own 60 days)
-> underperforms market (5d -0.6%, 20d -0.8%, 60d -1.1%, every era). Keeps data/deliv_recent.csv.gz (last ~100 days).
Source archives.nseindia.com (nsearchives times out from Actions). No credentials."""
import os, time, datetime as dt, requests, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(R, 'data', 'deliv_recent.csv.gz')
S = requests.Session(); S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36'})
old = pd.read_csv(P, parse_dates=['date']) if os.path.exists(P) else pd.DataFrame(columns=['date', 'symbol', 'deliv_pct'])
have = set(old.date.dt.date) if len(old) else set()
today = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date()
new = []
for d in pd.bdate_range(today - dt.timedelta(days=110), today):
    if d.date() in have: continue
    try:
        r = S.get(f'https://archives.nseindia.com/archives/equities/mto/MTO_{d:%d%m%Y}.DAT', timeout=15)
    except Exception as e:
        print('err', d.date(), e); continue
    if r.status_code != 200 or len(r.content) < 200: continue
    for line in r.text.splitlines():
        p = line.split(',')
        if len(p) >= 7 and p[0].strip() == '20' and p[3].strip() == 'EQ':
            try: new.append((d, p[2].strip(), float(p[6])))
            except ValueError: pass
    time.sleep(0.3)
A = pd.concat([old, pd.DataFrame(new, columns=['date', 'symbol', 'deliv_pct'])])
A = A[A.date >= pd.Timestamp(today - dt.timedelta(days=150))].drop_duplicates(['date', 'symbol'])
A.to_csv(P, index=False); print('delivery days', A.date.nunique(), 'last', A.date.max())
