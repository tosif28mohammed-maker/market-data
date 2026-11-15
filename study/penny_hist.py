"""Saste (kam bhaav wale) shares ka itihaas (user 15 Nov 2026: 'saste share mein chhota paisa, long term fayda?').
Har mahine (21 din) A/B jaise share (us waqt >= Rs 1 cr/din) ko us waqt ke ASLI bhaav se baanto: <20, 20-50, 50-100, 100-500, 500+.
Agle 3/6/12 mahine bazaar (sab ka barabar ausat) se excess; daur-war; 2008/COVID hata kar; kharcha 0.25%.
Saath mein: sasta + uptrend (200 DMA upar + 52w high ke 10% andar) aur sasta + giravat (52w high se 50%+ neeche).
Survivor bias: data mein doobe/delist hue share kam hain -> saste shares ke nateeje ASLI se BEHTAR dikhenge (saavdhaan).
Output study/results/penny_hist.csv"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
P = nc.load(); a, c, v = P['a'], P['c'], P['v']
tv = (c * v).rolling(20, min_periods=15).median(); liq = tv >= 1e7
up200 = a > a.rolling(200, min_periods=180).mean(); hi = a / a.rolling(252, min_periods=200).max()
F, mkt = nc.fwd(P, hs=(63, 126, 252))
bands = {'<20': (0, 20), '20-50': (20, 50), '50-100': (50, 100), '100-500': (100, 500), '500+': (500, 1e9)}
mdays = a.index[260::21]
rows = []
for name, (lo, hi_) in bands.items():
    base = liq & (c >= lo) & (c < hi_)
    for sub, cond in (('sab', base), ('+uptrend', base & up200 & (hi >= 0.9)), ('+bahut gira', base & (hi <= 0.5))):
        ev = cond.loc[mdays].reindex(a.index).fillna(False)
        for r in nc.evaluate(ev, F, f'{name} {sub}', hs=(63, 126, 252)): rows.append(r)
T = pd.DataFrame(rows); T['excess_net'] = T.excess - nc.COST
T.to_csv(os.path.join(nc.REPO, 'study', 'results', 'penny_hist.csv'), index=False)
pd.set_option('display.width', 250)
x = T[T.era.isin(['ALL', '2003-12', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'])]
print(x.pivot_table(index=['study'], columns=['h', 'era'], values='excess_net', aggfunc='first').round(1).loc[:, [252]].to_string())
print(x[(x.h == 252) & (x.era == 'ALL')][['study', 'n', 'excess_med', 'win_vs_mkt', 'raw_net', 't_dates']].to_string(index=False))
