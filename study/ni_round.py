"""Idea 9: round-number price levels (actual traded price, not adjusted).
Level step = 10^floor(log10(prev close)) (price 450 -> 100s; 2300 -> 1000s) and half-step (50s, 500s).
Events: CROSS = close crosses above next level, prev 20 closes all below it.
REJECT = day high reaches within 0.5% of level (or above) but close stays below.
Placebo: same spacing, levels shifted by 0.37 step (non-round).
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

P = c.load(); F, mkt = c.fwd(P, hs=(5, 20, 60))
cl = P['c']; q = P['a'] / cl; hi = P['h'] / q
pc = cl.shift(1)
step = 10 ** np.floor(np.log10(pc.where(pc > 1)))
rows = []
liq = cl.rolling(50).count() >= 45
for half in (1.0, 0.5):
    st = step * half
    for off, tag in ((0.0, 'ROUND'), (0.37, 'PLACEBO')):
        L = (np.ceil(pc / st - off) + off) * st
        L = L.where(L > pc, L + st)
        prevmax = cl.shift(1).rolling(20).max()
        cross = (cl >= L) & (prevmax < L) & liq
        rej = (hi >= L * 0.995) & (cl < L) & liq
        nm = f"{tag} step{'1' if half == 1 else '1/2'}"
        rows += c.evaluate(c.thin(cross, 10), F, f'CROSS {nm}')
        rows += c.evaluate(c.thin(rej, 10), F, f'REJECT {nm}', hs=(5, 20))
        # does the price stall: prob that a touch (high >= 0.995L) closes below level
        touch = (hi >= L * 0.995) & liq
        print(nm, 'touch -> close below level %:', round((rej.sum().sum() / touch.sum().sum()) * 100, 1))
T = pd.DataFrame(rows); T.to_csv(f'{c.REPO}/study/results/ni_round.csv', index=False)
print(T[T.era.isin(['ALL', '2013-20', '2021-26', 'Nov23-now'])][['study', 'h', 'era', 'n', 'excess', 'win_vs_mkt', 'raw_net', 't_dates']].to_string())
