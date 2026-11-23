# ROBOT
"""AI-07BCC4 (arXiv 1510.03704 via Gemini): BSE Mid/Small monthly returns persist (lag-1) -> hold index next month
only if last month was positive. Proxy indices: equal-weight of stocks ranked by 60-day median traded value at each
month-end: Large = rank 1-100, Mid = 101-250, Small = 251-750. Also Nifty (data/NIFTY.csv). Cost 0.1% per switch
(ETF-like). Survivorship: current-list universe (bias up, mostly for small)."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import ni_common as c
P = c.load(); A, C, V = P['a'], P['c'], P['v']
r1 = A.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
tv = (C * V).rolling(60, min_periods=40).median()
me = A.resample('ME').last().index
me = [A.index[A.index.searchsorted(d, side='right') - 1] for d in me]
rk = tv.loc[me].rank(axis=1, ascending=False)
grp = {'Large': (1, 100), 'Mid': (101, 250), 'Small': (251, 750)}
series = {}
for g, (lo, hi) in grp.items():
    m = []
    for i in range(len(me) - 1):
        mem = rk.loc[me[i]]; mem = mem[(mem >= lo) & (mem <= hi)].index
        seg = r1.loc[(r1.index > me[i]) & (r1.index <= me[i + 1]), mem]
        m.append((me[i + 1], (np.prod(1 + seg.mean(axis=1).fillna(0)) - 1) * 100))
    series[g] = pd.Series(dict(m))
n = pd.read_csv(os.path.join(c.REPO, 'data/NIFTY.csv'), parse_dates=['date' if 'date' in open(os.path.join(c.REPO, 'data/NIFTY.csv')).readline() else 0])
n = n.set_index(n.columns[0]); cl = [x for x in n.columns if x.lower() in ('close', 'adj close', 'adj')][0]
series['Nifty'] = n[cl].resample('ME').last().pct_change().dropna() * 100
out = []
for g, s in series.items():
    s = s.loc['2003-01-01':]
    sig = (s.shift(1) > 0)
    sw = sig.astype(int).diff().abs().fillna(0)
    strat = s.where(sig, 0) - sw * 0.1
    for era, a, b in [('all', '2003', '2026'), ('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('last12m', '2025-11', '2026'), ('last6m', '2026-05', '2026')]:
        x, y, z = s.loc[a:b], strat.loc[a:b], sig.loc[a:b]
        out.append(dict(index=g, era=era, months=len(x), bh_pm=round(x.mean(), 2),
                        after_up_pm=round(x[z].mean(), 2), after_down_pm=round(x[~z].mean(), 2),
                        strat_cagr=round(((1 + y / 100).prod() ** (12 / len(y)) - 1) * 100, 1),
                        bh_cagr=round(((1 + x / 100).prod() ** (12 / len(x)) - 1) * 100, 1),
                        strat_maxdd=round(((1 + y / 100).cumprod() / (1 + y / 100).cumprod().cummax() - 1).min() * 100, 1),
                        bh_maxdd=round(((1 + x / 100).cumprod() / (1 + x / 100).cumprod().cummax() - 1).min() * 100, 1),
                        corr_lag1=round(x.autocorr(1), 3)))
o = pd.DataFrame(out); print(o.to_string(index=False))
o.to_csv(os.path.join(c.REPO, 'study/research/claims/out/ai07bcc4_monthly_mom.csv'), index=False)
