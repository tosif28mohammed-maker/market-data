# ROBOT  (needs universe500 data via U500)
"""r065 आगे: PSU vs private relative momentum switch.
दो groups: (A) 4 sectors (Utilities/Basic Mat/Energy/Industrials) PSU vs private, (B) banks PSU vs private.
हर महीने: पिछले 250d (और 120d) basket return जिसका ज़्यादा → अगले 60d उसी group को hold. तुलना: हमेशा private, हमेशा PSU, 50/50.
Switch की लागत: हर बार group बदले 0.25%."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, COST
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'r065_dividend_yield'))
src = open(os.path.join(os.path.dirname(__file__), '..', 'r065_dividend_yield', 'psu_excl.py')).read()
PSU = eval(src.split('PSU = ')[1].split('\nSECT')[0])
I = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'fund', 'info.csv')).set_index('symbol')
P = load(); a, c, v = P['a'], P['c'], P['v']
sec = I.sector.reindex(a.columns); ind = I.industry.reindex(a.columns) if 'industry' in I else pd.Series('', index=a.columns)
ispsu = pd.Series(a.columns.isin(list(PSU)), index=a.columns)
grpA = sec.isin({'Utilities', 'Basic Materials', 'Energy', 'Industrials'})
grpB = ind.astype(str).str.contains('Bank', case=False) & ~ind.astype(str).str.contains('Invest|Capital Market', case=False)
print('banks in panel:', int(grpB.sum()), 'psu banks:', int((grpB & ispsu).sum()))
rank = (c * v).rolling(250, min_periods=200).median().rank(axis=1, ascending=False)
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
dates = list(a.index.to_series().groupby(a.index.to_period('M')).first().values)
H = 21  # एक महीना hold, हर महीने दोबारा फ़ैसला (non-overlap)
def run(grp, name, top=300, lb=250):
    rows = []
    for i, d in enumerate(dates[:-1]):
        d = pd.Timestamp(d); nd = pd.Timestamp(dates[i + 1])
        if d < pd.Timestamp('2004-01-01'): continue
        t = (rank.loc[d] <= top) & grp
        ps, pr = t & ispsu, t & ~ispsu
        if ps.sum() < 3 or pr.sum() < 3: continue
        loc = a.index.get_loc(d)
        if loc < lb: continue
        past = a.iloc[loc] / a.iloc[loc - lb] - 1
        fut = (1 + r1.loc[(r1.index > d) & (r1.index <= nd)]).prod(min_count=1) - 1
        rows.append(dict(date=d, mp=past[ps].mean(), mr=past[pr].mean(), fp=fut[ps].mean(), fr=fut[pr].mean()))
    R = pd.DataFrame(rows).set_index('date').dropna()
    pick_pr = R.mr > R.mp
    R['sw'] = np.where(pick_pr, R.fr, R.fp)
    R['chg'] = pick_pr.astype(int).diff().abs().fillna(0) * COST / 100
    R['sw_net'] = R.sw - R.chg
    R['half'] = (R.fr + R.fp) / 2
    R['contra'] = np.where(pick_pr, R.fp, R.fr) - R.chg
    print(f'\n== {name} (lookback {lb}d, 1 महीना hold) months={len(R)} switches={int(R.chg.gt(0).sum())}')
    def ann(x): return ((1 + x).prod() ** (12 / len(x)) - 1) * 100
    def dd(x):
        e = (1 + x).cumprod(); return ((e / e.cummax()) - 1).min() * 100
    eras = {'ALL': R.index >= '2000', '2004-12': R.index <= '2012-12-31', '2013-20': (R.index >= '2013') & (R.index <= '2020-12-31'),
            '2021-26': R.index >= '2021', 'last 6m': R.index >= R.index.max() - pd.DateOffset(months=6), 'last 12m': R.index >= R.index.max() - pd.DateOffset(months=12)}
    for e, m in eras.items():
        s = R[m]
        if len(s) < 3: continue
        print(f'  {e:9s} n={len(s):3d} CAGR: switch {ann(s.sw_net):+6.1f} | private {ann(s.fr):+6.1f} | PSU {ann(s.fp):+6.1f} | 50/50 {ann(s.half):+6.1f} | उल्टा(placebo) {ann(s.contra):+6.1f} | switch>50/50 महीने {100*(s.sw_net>s.half).mean():.0f}%')
    print(f'  maxDD: switch {dd(R.sw_net):.0f} private {dd(R.fr):.0f} PSU {dd(R.fp):.0f} 50/50 {dd(R.half):.0f}')
    print('  आज का चुनाव:', 'private' if pick_pr.iloc[-1] else 'PSU', f'(12m past pvt {R.mr.iloc[-1]*100:+.1f}% psu {R.mp.iloc[-1]*100:+.1f}%)')
    return R
for lb in (250, 120):
    run(grpA, 'A: 4 sectors PSU vs private', lb=lb)
    run(grpB, 'B: banks PSU vs private', top=500, lb=lb)
