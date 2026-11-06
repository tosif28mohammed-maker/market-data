"""Dividend / corporate-action robot (user 5 Nov 2026: 'dividend kab milega yeh pata kaise chalega').
Source: NSE public API corporates-corporateActions (same session method as ipo.py). BSE fallback if NSE fails.
Writes:
  data/corp/actions_<date>.json (raw), data/corp/actions_all.csv (running history, de-duplicated),
  data/corp/div_upcoming.csv  = every announced dividend with ex-date ahead + yield on last close,
  data/corp/div_candidates.csv = f64 rule: yield >= 2%, liquidity not D, ex-date 2-12 trading days ahead,
                                 buy_from = ex-6 trading days (2:15-3:25 PM), sell_on = ex-1 trading day (cum date), stop -6%.
Runs inside daily.yml (no new schedule). Study only, no orders.
"""
import os, re, json, time, datetime as dt, requests, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'data', 'corp'); os.makedirs(D, exist_ok=True)
IST = dt.timezone(dt.timedelta(hours=5, minutes=30)); today = dt.datetime.now(IST).date()
HOL = {dt.date(2026, 11, 10), dt.date(2026, 11, 24), dt.date(2026, 12, 25)}  # extend as NSE publishes


def tdays(a, b):
    """trading days from a (exclusive) to b (inclusive)."""
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in HOL: n += 1
    return n


def shift_td(d, k):
    step = 1 if k > 0 else -1
    while k:
        d += dt.timedelta(days=step)
        if d.weekday() < 5 and d not in HOL: k -= step
    return d


def nse():
    s = requests.Session(); s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                                              'Accept-Language': 'en-US,en;q=0.9', 'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-actions'})
    s.get('https://www.nseindia.com', timeout=20); time.sleep(1)
    f = (today - dt.timedelta(days=10)).strftime('%d-%m-%Y'); t = (today + dt.timedelta(days=90)).strftime('%d-%m-%Y')
    r = s.get(f'https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={f}&to_date={t}', timeout=40)
    j = r.json(); print('NSE', r.status_code, len(j) if isinstance(j, list) else type(j))
    json.dump(j, open(os.path.join(D, f'actions_{today}.json'), 'w'), indent=0)
    rows = []
    for x in j if isinstance(j, list) else []:
        rows.append(dict(symbol=x.get('symbol'), series=x.get('series'), company=x.get('comp'), subject=x.get('subject'),
                         ex_date=x.get('exDate'), record_date=x.get('recDate'), face=x.get('faceVal'), src='NSE'))
    return pd.DataFrame(rows)


def bse():
    h = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.bseindia.com/', 'Origin': 'https://www.bseindia.com'}
    f = (today - dt.timedelta(days=10)).strftime('%Y%m%d'); t = (today + dt.timedelta(days=90)).strftime('%Y%m%d')
    u = f'https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w?Fdate={f}&Purposecode=&TDate={t}&ddlcategorys=E&ddlindustrys=&scripcode=&segment=0&strSearch=S'
    r = requests.get(u, headers=h, timeout=40); j = r.json(); print('BSE', r.status_code, len(j) if isinstance(j, list) else type(j))
    rows = []
    for x in j if isinstance(j, list) else []:
        rows.append(dict(symbol=x.get('short_name'), series='EQ', company=x.get('long_name'), subject=x.get('Purpose'),
                         ex_date=x.get('Ex_date'), record_date=x.get('RD_Date'), face=None, src='BSE'))
    return pd.DataFrame(rows)


try:
    A = nse()
    if A.empty: raise ValueError('empty')
except Exception as e:
    print('NSE failed', e); A = bse()
if A.empty:
    raise SystemExit('no corporate actions fetched')
A['fetched'] = str(today)
allp = os.path.join(D, 'actions_all.csv')
if os.path.exists(allp):
    A = pd.concat([pd.read_csv(allp), A])
A = A.drop_duplicates(['symbol', 'subject', 'ex_date'], keep='last')
A.to_csv(allp, index=False)

# dividends ahead
A['exd'] = pd.to_datetime(A.ex_date, errors='coerce', dayfirst=True).dt.date
div = A[A.subject.fillna('').str.contains('dividend', case=False) & A.exd.notna()].copy()
div = div[div.exd > today]


def amount(s):
    v = re.findall(r'(?:Rs\.?|Re\.?|INR|₹)\s*([0-9]+(?:\.[0-9]+)?)', str(s), flags=re.I)
    return sum(float(x) for x in v) if v else np.nan


div['div_rs'] = div.subject.apply(amount)
close = pd.read_csv(os.path.join(ROOT, 'data', 'daily_all', 'close.csv.gz'), index_col=0)
last = close.ffill().iloc[-1]
div['last_close'] = div.symbol.map(last)
for sym in div.symbol[div.last_close.isna()]:
    p = os.path.join(ROOT, 'data', f'{sym}.csv')
    if os.path.exists(p):
        div.loc[div.symbol == sym, 'last_close'] = pd.read_csv(p).close.dropna().iloc[-1]
div['yield_pct'] = (div.div_rs / div.last_close * 100).round(2)
bad = set(open(os.path.join(ROOT, 'paper', 'avoid_liquidity_D.txt')).read().split()) if os.path.exists(os.path.join(ROOT, 'paper', 'avoid_liquidity_D.txt')) else set()
div['liq_D'] = div.symbol.isin(bad)
div['tdays_to_ex'] = div.exd.apply(lambda d: tdays(today, d))
div['buy_from'] = div.exd.apply(lambda d: shift_td(d, -6))
div['sell_on_cum'] = div.exd.apply(lambda d: shift_td(d, -1))
div = div.sort_values('exd')
cols = ['symbol', 'company', 'subject', 'div_rs', 'last_close', 'yield_pct', 'ex_date', 'record_date', 'tdays_to_ex', 'buy_from', 'sell_on_cum', 'liq_D', 'src']
div[cols].to_csv(os.path.join(D, 'div_upcoming.csv'), index=False)
cand = div[(div.yield_pct >= 2) & (~div.liq_D) & div.tdays_to_ex.between(2, 12)].copy()
cand['stop'] = (cand.last_close * 0.94).round(2)
cand['rule'] = np.where(cand.yield_pct >= 4, 'f64 strong (4%+)', 'f64 (2-4%)')
cand[cols + ['stop', 'rule']].to_csv(os.path.join(D, 'div_candidates.csv'), index=False)
print('dividends ahead', len(div), 'candidates', len(cand))
print(cand[['symbol', 'div_rs', 'yield_pct', 'ex_date', 'buy_from', 'sell_on_cum']].to_string())


# ---- board meetings (results dates) next 10 days: no new buy before results (d05 rule) ----
try:
    s2 = requests.Session(); s2.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                                                'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-board-meetings'})
    s2.get('https://www.nseindia.com', timeout=20); time.sleep(1)
    f = today.strftime('%d-%m-%Y'); t = (today + dt.timedelta(days=14)).strftime('%d-%m-%Y')
    j = s2.get(f'https://www.nseindia.com/api/corporate-board-meetings?index=equities&from_date={f}&to_date={t}', timeout=40).json()
    bm = pd.DataFrame([dict(symbol=x.get('bm_symbol'), date=x.get('bm_date'), purpose=x.get('bm_purpose')) for x in (j if isinstance(j, list) else [])])
    bm.to_csv(os.path.join(D, 'board_meetings.csv'), index=False); print('board meetings', len(bm))
except Exception as e:
    print('board meetings failed', e)
