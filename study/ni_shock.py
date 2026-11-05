"""Idea 1: news/results shock drift (PEAD proxy, no results-date data available).
Event UP: volume >= 3x own 50-day median, day return (close/prev close) >= +4%,
close in top 30% of day range. DOWN mirror. Non-overlap 20 days per stock.
Placebo: same-size price move (>= +4%, strong close) but volume < 1.5x (no shock).
Also: shock + stock above 200 DMA; shock gap held (next 5 days low stays above event-day open).
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

P = c.load(); F, mkt = c.fwd(P)
a, v, h, l, o = P['a'], P['v'], P['h'], P['l'], P['o']
r = a.pct_change(fill_method=None) * 100
vm = v.rolling(50, min_periods=40).median().shift(1)
vr = v / vm
pos = (a - l) / (h - l).replace(0, np.nan)
liq_ok = (a.rolling(50).count() >= 45)
dma200 = a.rolling(200, min_periods=180).mean()
rows = []
up = (vr >= 3) & (r >= 4) & (r < 20) & (pos >= 0.7) & liq_ok
up_pl = (vr < 1.5) & (r >= 4) & (r < 20) & (pos >= 0.7) & liq_ok
dn = (vr >= 3) & (r <= -4) & (r > -20) & (pos <= 0.3) & liq_ok
dn_pl = (vr < 1.5) & (r <= -4) & (r > -20) & (pos <= 0.3) & liq_ok
upT, dnT = c.thin(up), c.thin(dn)
rows += c.evaluate(upT, F, 'SHOCK_UP vol3x +4%', placebo=c.thin(up_pl))
rows += c.evaluate(dnT, F, 'SHOCK_DOWN vol3x -4%', placebo=c.thin(dn_pl))
rows += c.evaluate(upT & (a > dma200), F, 'SHOCK_UP above200', placebo=c.thin(up_pl & (a > dma200)))
big = c.thin((vr >= 5) & (r >= 6) & (r < 20) & (pos >= 0.7) & liq_ok)
rows += c.evaluate(big, F, 'SHOCK_UP vol5x +6%')
# entry 5 days later only if the shock held (day5 low never below event open) -> buy day-5 close
held = up.copy()
lo5 = l.rolling(5).min().shift(-5)
held = upT & (lo5 > o)
held5 = held.shift(5, fill_value=False)
rows += c.evaluate(held5, F, 'SHOCK_UP held 5d, buy d5')
T = pd.DataFrame(rows)
os.makedirs(f'{c.REPO}/study/results', exist_ok=True)
T.to_csv(f'{c.REPO}/study/results/ni_shock.csv', index=False)
print(T.to_string())
print('OHLC up 20d (best high, worst low, %fell>10%):', c.mfe_mae(P, upT, 20))
print('OHLC down 20d:', c.mfe_mae(P, dnT, 20))
print('events/yr since 2021 up:', upT.loc['2021':].sum().sum() / 5.8)
