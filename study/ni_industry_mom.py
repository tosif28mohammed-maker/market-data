"""Industry (theme) momentum test (user 9 Nov 2026: 'jo industry chal padi uske shares pehle pakdo').
Month-end: industries (today's Yahoo industry labels, >=5 stocks that month) ranked by median 6m return skipping last month.
Buy top-20% industries' stocks (equal weight) next month; compare with all stocks and with bottom 20%. Cost 0.25% per month.
Caveat: labels are today's (survivor bias hits both sides equally)."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__)); from ni_common import load, ERAS
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = load(); C = P['a'] if 'a' in P else P['c']
F = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol').industry
C = C.loc[:, [c for c in C.columns if c in F.index]]
M = C.resample('ME').last(); ret = M.pct_change().shift(-1)  # next month
mom = M.shift(1) / M.shift(7) - 1                            # 6m skip 1
rows = []
for d in M.index[8:-1]:
    m = mom.loc[d].dropna(); r = ret.loc[d].reindex(m.index).dropna(); m = m.reindex(r.index)
    if len(m) < 100: continue
    g = pd.DataFrame({'m': m, 'r': r, 'ind': F.reindex(m.index)}).dropna()
    im = g.groupby('ind').m.median()[g.groupby('ind').size() >= 5]
    if len(im) < 15: continue
    top, bot = im[im >= im.quantile(0.8)].index, im[im <= im.quantile(0.2)].index
    rows.append(dict(date=d, top=g[g.ind.isin(top)].r.mean() * 100 - 0.25, bot=g[g.ind.isin(bot)].r.mean() * 100 - 0.25, all=g.r.mean() * 100))
T = pd.DataFrame(rows).set_index('date')
def show(x, name):
    ex = x.top - x['all']; print(f'{name:12s} months {len(x):3d} | top {x.top.mean():+.2f}%/m  all {x["all"].mean():+.2f}  bottom {x.bot.mean():+.2f} | top-all {ex.mean():+.2f} (t {ex.mean() / ex.std() * np.sqrt(len(ex)):.1f}, beats {(ex > 0).mean() * 100:.0f}%)')
show(T, 'ALL')
for a, b, n in [('2003', '2012', '2003-12'), ('2013', '2020', '2013-20'), ('2021', '2026', '2021-26'), ('2023-11', '2026', 'Nov23-now')]:
    show(T.loc[a:b], n)
x = T.drop(T.loc['2008-01':'2009-06'].index.union(T.loc['2020-02':'2020-06'].index)); show(x, 'ex-crisis')
T.to_csv(os.path.join(R, 'study', 'results', 'industry_mom.csv'))
