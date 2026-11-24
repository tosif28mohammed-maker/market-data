# ROBOT  (needs universe500 data via U500)
"""AI-48006E: Blue chip (top-100 by traded value) with trailing-12m dividend yield > 3% -> buy?
Dividend inferred from adj/close factor drops (ex-date): D/C_prev = 1 - f_t/f_{t-1}.
Monthly formation (first trading day), hold 60 / 250 days. Compare vs other blue chips (control)
and vs EW market. Costs 0.25% round trip. Survivorship: universe = today's u1000+u2000 list."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, era_mask, COST
P = load(); a, c, v = P['a'], P['c'], P['v']
f = a / c
fr = f / f.shift(1)
drop = (1 - 1 / fr).where((fr > 1.0005) & (fr < 1 / 0.85), 0)   # back-adjusted factor rises on ex-date
ttm = drop.rolling(250, min_periods=200).sum() * 100     # trailing yield %
tv = (c * v).rolling(250, min_periods=200).median()
rank = tv.rank(axis=1, ascending=False)
blue = rank <= 100
F, mkt = fwd(P, hs=(60, 250))
dates = a.index.to_series().groupby(a.index.to_period('M')).first().values
dates = [d for d in dates if d >= pd.Timestamp('2004-01-01')]
rows = []
for h in (60, 250):
    raw, ex = F[h]
    rec = []
    for d in dates:
        b = blue.loc[d]; y = ttm.loc[d]
        hi = b & (y > 3); lo = b & (y <= 3) & y.notna()
        if hi.sum() < 3: continue
        rr = raw.loc[d]
        rec.append(dict(date=d, n_hi=int(hi.sum()), hi=rr[hi].mean(), ctrl=rr[lo].mean(),
                        hi_ex=ex.loc[d][hi].mean(), hi_win=(rr[hi] > COST).mean() * 100,
                        ctrl_win=(rr[lo] > COST).mean() * 100))
    R = pd.DataFrame(rec).dropna(subset=['hi', 'ctrl']).set_index('date')
    em = era_mask(R.index)
    for era, m in list(em.items()) + [('last6m', R.index >= R.index.max() - pd.Timedelta(days=180))]:
        s = R[m]
        if len(s) < 3: continue
        dd = s.hi - s.ctrl
        rows.append(dict(h=h, era=era, months=len(s), avg_n=round(s.n_hi.mean(), 1),
                         hi_net=round(s.hi.mean() - COST, 2), ctrl_net=round(s.ctrl.mean() - COST, 2),
                         hi_minus_ctrl=round(dd.mean(), 2), pct_months_hi_better=round((dd > 0).mean() * 100, 1),
                         hi_excess_vs_mkt=round(s.hi_ex.mean(), 2),
                         hi_win=round(s.hi_win.mean(), 1), ctrl_win=round(s.ctrl_win.mean(), 1)))
out = pd.DataFrame(rows)
pd.set_option('display.width', 200)
print(out.to_string(index=False))
# yearly view h=250
print('\nby formation year (h=250, hi minus ctrl):')
raw, ex = F[250]
yr = {}
for d in dates:
    b = blue.loc[d]; y = ttm.loc[d]; hi = b & (y > 3); lo = b & (y <= 3) & y.notna()
    if hi.sum() < 3: continue
    x = raw.loc[d][hi].mean() - raw.loc[d][lo].mean()
    if pd.notna(x): yr.setdefault(pd.Timestamp(d).year, []).append(x)
print({k: round(np.mean(v), 1) for k, v in yr.items()})
out.to_csv(os.path.join(os.path.dirname(__file__), 'results.csv'), index=False)
