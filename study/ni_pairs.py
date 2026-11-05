"""Idea 5: pairs (same industry, liquidity A, top 8 by turnover per industry).
Pair valid if 250-day return correlation >= 0.6 (known at that date, refreshed monthly).
Signal: z of log(price X / price Y) vs its own 60-day mean/std <= -2 (X lagging) -> buy X at close.
Outcome: X minus Y return over 5/20 days (pair trade, needs futures for short leg) and X vs market (long only).
Non-overlap: one signal per pair per 20 days. Placebo: z between -0.5 and 0.5 (no gap).
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

P = c.load(); F, mkt = c.fwd(P, hs=(5, 20))
a = P['a']; U = c.U
info = pd.concat([pd.read_csv(f'{U}/u1000/list1000.csv'), pd.read_csv(f'{U}/u2000/list_extra.csv')])[['symbol', 'industry', 'turnover_cr']].dropna()
liq = pd.read_csv(f'{c.REPO}/study/results/liq_all.csv')
A = set(liq.loc[liq.liquidity.astype(str).str.startswith('A'), 'symbol'])
info = info[info.symbol.isin(A) & info.symbol.isin(a.columns)].drop_duplicates('symbol')
groups = {k: g.nlargest(8, 'turnover_cr').symbol.tolist() for k, g in info.groupby('industry') if len(g) >= 2}
print('industries', len(groups), 'stocks', sum(len(v) for v in groups.values()))
r = a.pct_change(fill_method=None)
la = np.log(a)
ev = []
months = a.index[a.index.to_series().dt.month.diff().fillna(1) != 0]
for ind, syms in groups.items():
    for i in range(len(syms)):
        for j in range(len(syms)):
            if i == j: continue
            x, y = syms[i], syms[j]
            corr = r[x].rolling(250, min_periods=200).corr(r[y])
            corr_m = corr.where(corr.index.isin(months)).ffill()  # refreshed monthly, known at that time
            lr = la[x] - la[y]
            z = (lr - lr.rolling(60, min_periods=50).mean()) / lr.rolling(60, min_periods=50).std()
            ok = corr_m >= 0.6
            for tag, m in (('SIGNAL', ok & (z <= -2)), ('PLACEBO', ok & (z.abs() <= 0.5))):
                last = -999
                for k in np.flatnonzero(m.values):
                    if k - last < 20: continue
                    last = k
                    d = a.index[k]; row = dict(tag=tag, date=d, x=x, y=y, ind=ind)
                    for h in (5, 20):
                        if k + h >= len(a): break
                        rx = a[x].iloc[k + h] / a[x].iloc[k] - 1; ry = a[y].iloc[k + h] / a[y].iloc[k] - 1
                        row[f'rel{h}'] = (rx - ry) * 100; row[f'xs{h}'] = F[h][1][x].iloc[k]
                    ev.append(row)
E = pd.DataFrame(ev).dropna(subset=['rel5'])
E.to_csv(f'{c.REPO}/study/results/ni_pairs_events.csv.gz', index=False)
out = []
for tag in ('SIGNAL', 'PLACEBO'):
    e = E[E.tag == tag]
    for era, s, t in [('ALL', '2003', '2026')] + [(n, s_, t_) for n, s_, t_ in c.ERAS]:
        d = e[(e.date >= s) & (e.date <= t)]
        if len(d) < 20: continue
        dd = d[~d.date.apply(lambda x: any(pd.Timestamp(a_) <= x <= pd.Timestamp(b_) for a_, b_ in c.CRISIS))] if era == 'ALL' else d
        out.append(dict(tag=tag, era=era, n=len(d), rel5=round(d.rel5.mean(), 2), rel20=round(d.rel20.mean(), 2),
                        rel20_win=round((d.rel20 > 0.5).mean() * 100, 1), pair_net20=round(d.rel20.mean() - 0.5, 2),
                        long_xs5=round(d.xs5.mean(), 2), long_xs20=round(d.xs20.mean(), 2), rel20_excrisis=round(dd.rel20.mean(), 2)))
T = pd.DataFrame(out); T.to_csv(f'{c.REPO}/study/results/ni_pairs.csv', index=False)
print(T.to_string())
# per industry consistency (signal), 2013-20 vs 2021-26
s = E[E.tag == 'SIGNAL'].copy(); s['era'] = np.where(s.date < '2021', 'old', 'new')
pi = s[s.date >= '2013'].groupby(['ind', 'era']).rel20.agg(['mean', 'count']).unstack()
pi = pi[(pi[('count', 'old')] >= 15) & (pi[('count', 'new')] >= 15)]
both = pi[(pi[('mean', 'old')] > 1) & (pi[('mean', 'new')] > 1)]
print('industries tested both periods', len(pi), 'positive >1% both', len(both))
print(both.round(2).to_string())
