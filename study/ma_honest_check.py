"""Honest check of the generic 'deep below MA -> sell back at MA' rule:
 - exit limit = PREVIOUS candle's MA (known in advance), not the same-candle MA
 - control = entries when price is below the MA but NOT deep (between its 10% and 50% distance), same exit rule
 - cost 0.25% per trade (delivery) / 0.1% (hourly intraday-ish) subtracted
Halves as in ma_sweep."""
import sys, os, glob, numpy as np, pandas as pd
sys.argv = ['x', 'none']
S = '/tmp/claude-0/-home-claude/d80f8346-ebcf-5b0f-b547-7bcd27753fa4/scratchpad'; ROOT = '/home/claude/market-data'; H1 = '/home/claude/intrarepo/intra/h1'
files = {}
for D in ['/home/claude/u500repo/u1000/daily', '/home/claude/u500repo/u2000/daily']:
    for f in sorted(glob.glob(os.path.join(D, '*.csv.gz'))): files.setdefault(os.path.basename(f)[:-7], f)
L = pd.read_csv(f'{ROOT}/study/results/liq_all.csv').set_index('symbol').liquidity.str[0]
names = ['NIFTY', 'BANKNIFTY'] + [s for s in files if L.get(s) in ('A', 'B')]
CHK = {'1D': [5, 10, 14, 20, 30, 50, 100, 113, 200, 300], '1W': [3, 5, 10, 15, 20, 50], '1M': [3, 5, 10], '4H': [10, 20, 50, 100, 200], '1H': [20, 50, 100, 200]}
W = {'1H': 140, '4H': 40, '1D': 21, '1W': 4, '1M': 2}; COST = {'1H': 0.0025, '4H': 0.0025, '1D': 0.0025, '1W': 0.0025, '1M': 0.0025}
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
exec(open(f'{ROOT}/study/ma_sweep.py').read().split('rows = []')[0].split("LENS = list(range(2, 501))")[1].replace('CR = [', 'CR0 = ['))  # load_daily, load_hourly, group_h
rows = []
def run(s, tf, d):
    n = len(d)
    if n < (120 if tf == '1M' else 400): return
    c = d.close.to_numpy(float); hi = d.high.to_numpy(float); lo = d.low.to_numpy(float); idx = d.index
    if tf in ('1H', '4H'): mid = idx[n // 2]; per = {'A': idx < mid, 'B': idx >= mid}
    elif tf == '1M': per = {'A': (idx >= '2005-01-01') & (idx < '2016-01-01'), 'B': idx >= '2016-01-01'}
    else:
        cr = np.zeros(n, bool)
        for a, b in CR: cr |= (idx >= a) & (idx <= b)
        per = {'A': (idx >= '2013-01-01') & (idx < '2021-01-01') & ~cr, 'B': idx >= '2021-01-01', 'N': idx >= '2023-11-01'}
    cs = pd.Series(c, index=idx)
    for typ in ('SMA', 'EMA'):
        for Ln in CHK[tf]:
            if n < Ln + 150 and tf != '1M': continue
            ma = (cs.rolling(Ln).mean() if typ == 'SMA' else cs.ewm(span=Ln, adjust=False).mean()).to_numpy(dtype=float, copy=True); ma[:Ln] = np.nan
            dist = c / ma - 1; first = per['A'] & ~np.isnan(ma)
            if first.sum() < 25: continue
            q10, q50 = np.nanquantile(dist[first], [0.10, 0.5]); q50 = min(q50, 0)
            prevd = np.r_[np.nan, dist[:-1]]
            groups = {'DEEP': (dist <= q10) & ~(prevd <= q10), 'CTRL': (dist > q10) & (dist < q50) & ~((prevd > q10) & (prevd < q50))}
            for gname, sig in groups.items():
                ent = np.flatnonzero(sig & ~np.isnan(ma)); res = np.full(n, np.nan); last = -1
                for i in ent:
                    if i <= last or i >= n - 1: continue
                    j2 = min(i + W[tf], n - 1); lim = ma[i:j2]   # limit for candle k = MA of candle k-1
                    seg = np.flatnonzero(hi[i + 1:j2 + 1] >= lim)
                    if len(seg): k = i + 1 + seg[0]; px = ma[k - 1]
                    else: k = j2; px = c[k]
                    res[i] = px / c[i] - 1 - COST[tf]; last = k
                for p, m in per.items():
                    x = res[m & ~np.isnan(res)]
                    if len(x): rows.append((s, tf, typ, Ln, gname, p, len(x), (x > 0).mean(), x.mean()))
for s in names:
    try:
        dd = load_daily(s); run(s, '1D', dd)
        run(s, '1W', dd.resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        run(s, '1M', dd.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        hh = load_hourly(s)
        if hh is not None: run(s, '1H', hh); run(s, '4H', group_h(hh, ['09:15', '13:15']))
    except Exception as e: print('ERR', s, e)
R = pd.DataFrame(rows, columns=['stock', 'tf', 'typ', 'L', 'grp', 'per', 'n', 'win', 'avg']); R.to_pickle(f'{S}/sw_check.pkl')
# pooled: trade-weighted
R['sw'] = R.win * R.n; R['sa'] = R.avg * R.n
T = R.groupby(['tf', 'typ', 'L', 'grp', 'per']).agg(n=('n', 'sum'), sw=('sw', 'sum'), sa=('sa', 'sum'), med_avg=('avg', 'median')).reset_index()
T['win'] = T.sw / T.n; T['avg'] = T.sa / T.n
X = T.pivot_table(index=['tf', 'typ', 'L', 'per'], columns='grp', values=['n', 'win', 'avg']).round(4)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); print(X.to_string())
