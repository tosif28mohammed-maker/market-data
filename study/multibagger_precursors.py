"""Multibagger precursors (user 21 Nov 2026: 'kis share me 10x/100x hota hai, uski qualities kya').
Idea source: Mayer '100 Baggers', Phelps '100 to 1', Motilal Oswal Wealth Creation Studies
(small size at start, growth, patience, buy-and-hold through big drawdowns).
Price-only version on our panel (u1000+u2000, liquidity D dropped):
  base = every January 2004..2016 (10y) / 2004..2021 (5y)
  outcome: 10x in 10y, 5x in 5y (adj close, dividends in)
  features at base: size proxy (median daily traded value prior year), prior 12m return,
  distance from 12m high, price vs 10-month average, 12m volatility, raw share price.
  Also for 10x winners: worst drawdown on the way and years taken.
CAVEAT: universe = stocks alive/listed today -> survivorship bias inflates hit rates;
compare quintiles with each other, not with absolute numbers.
Run: U500=/home/claude/u500 python3 study/multibagger_precursors.py
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ni_common import load

P = load()
A, C, V = P['a'], P['c'], P['v']
A = A.where(A > 0)
M = A.resample('ME').last()
TV = (C * V).rolling(250, min_periods=150).median().resample('ME').last() / 1e7  # Rs cr/day
ret_m = M.pct_change(fill_method=None).clip(-0.6, 1.5)

feat = {
    'size_tv_cr': TV,
    'ret12': M / M.shift(12) - 1,
    'dist_hi': M / M.rolling(12).max() - 1,
    'vs_10m_avg': M / M.rolling(10).mean() - 1,
    'vol12': ret_m.rolling(12).std(),
    'price': C.resample('ME').last(),
}
rows = []
for y in range(2004, 2022):
    t = pd.Timestamp(f'{y-1}-12-31')
    t = M.index[M.index.get_indexer([t], method='nearest')[0]]
    i = M.index.get_loc(t)
    for H, mult, name in [(60, 5, 'x5_in5y'), (120, 10, 'x10_in10y')]:
        if i + H >= len(M.index):
            continue
        base = M.iloc[i]
        fwd = M.iloc[i + H] / base
        path = M.iloc[i:i + H + 1]
        ok = base.notna() & fwd.notna() & feat['size_tv_cr'].loc[t].notna()
        for s in base.index[ok]:
            r = {'year': y, 'sym': s, 'horizon': name, 'fwd': fwd[s], 'hit': fwd[s] >= mult}
            for k, f in feat.items():
                r[k] = f.loc[t, s] if s in f.columns else np.nan
            if name == 'x10_in10y' and fwd[s] >= mult:
                p = path[s] / base[s]
                r['maxdd_on_way'] = (p / p.cummax() - 1).min()
                r['years_to_10x'] = (np.argmax(p.values >= 10)) / 12
            rows.append(r)
D = pd.DataFrame(rows)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
D.to_csv(f'{out}/multibagger_events.csv.gz', index=False)

lines = []
for h in ['x10_in10y', 'x5_in5y']:
    d = D[D.horizon == h].copy()
    lines.append(f'\n=== {h}: n={len(d)}, base hit rate {d.hit.mean()*100:.1f}% , median fwd {d.fwd.median():.2f}x')
    d['era'] = np.where(d.year <= 2010, 'base<=2010', 'base>2010')
    for k in feat:
        d['q'] = d.groupby('year')[k].transform(lambda x: pd.qcut(x.rank(method='first'), 5, labels=False) + 1)
        t = d.groupby(['q']).agg(hit=('hit', 'mean'), med_fwd=('fwd', 'median'), n=('hit', 'size'))
        e = d.groupby(['era', 'q']).hit.mean().unstack(0)
        lines.append(f'-- {k} (q1=lowest .. q5=highest)')
        for q in t.index:
            lines.append(f'   q{int(q)}: hit {t.hit[q]*100:5.1f}%  medfwd {t.med_fwd[q]:.2f}x  n={t.n[q]}  | '
                         + '  '.join(f'{c}:{e.loc[q, c]*100:.1f}%' for c in e.columns))
w = D[(D.horizon == 'x10_in10y') & D.hit]
if len(w):
    lines.append(f'\n10x winners: n={len(w)} (unique stocks {w.sym.nunique()}); worst drawdown on the way: '
                 f'median {w.maxdd_on_way.median()*100:.0f}%, 25th pct {w.maxdd_on_way.quantile(.25)*100:.0f}%; '
                 f'years to first touch 10x: median {w.years_to_10x.median():.1f}')
    lines.append('share of 10x winners that fell >=50% on the way: '
                 f'{(w.maxdd_on_way <= -0.5).mean()*100:.0f}%')
txt = '\n'.join(lines)
open(f'{out}/multibagger_precursors.txt', 'w').write(txt)
print(txt)
