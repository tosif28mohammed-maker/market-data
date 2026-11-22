"""Claim test DHAN-14 (Dhan YouTube 'I Scan Stocks at 3:30 PM for Swing Trades | 25 & 55 EMA + RSI Setup', https://www.youtube.com/watch?v=LpCo69ZZBRg).
Description: bullish = 25 EMA above 55 EMA (trend) + RSI >= 40 (momentum); screener = close >= 20 & 50 EMA + RSI >= 40. Scan at 3:30 PM, buy next day.
RULES WRITTEN BEFORE RESULTS: CROSS = EMA25 crosses above EMA55 today, close>both, RSI14>=40. SCAN = close>=EMA20 & >=EMA50 & RSI>=40 (sampled 1 in 10).
CONTROL = any day sampled 1 in 10. Entry next day OPEN; stops A = 5-day low (skip risk>8%), B = 1.5 ATR; target 2R; max 20 days; cost 0.25%.
Run: U500=/home/claude/u500 python3 study/research/claims/dhan14_ema2555_rsi.py
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from ni_common import load

P = load(); A = P['a']; r = A / P['c']
C, H, L, O = A, P['h'], P['l'], P['o']
syms, idx = C.columns, C.index
ema = lambda x, s: x.ewm(span=s, adjust=False, min_periods=s).mean()
e20, e50, e200 = ema(C, 20), ema(C, 50), ema(C, 200)
e25, e55 = ema(C, 25), ema(C, 55)
# RSI14 (Wilder)
d = C.diff(); up = d.clip(lower=0).ewm(alpha=1/14, adjust=False).mean(); dn = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
rsi = 100 - 100 / (1 + up / dn)
# ADX14
tr = pd.concat([H - L, (H - C.shift()).abs(), (L - C.shift()).abs()]).groupby(level=0).max().reindex(idx)
atr = tr.ewm(alpha=1/14, adjust=False).mean()
pdm = (H - H.shift()); ndm = (L.shift() - L)
pdm2 = pdm.where((pdm > ndm) & (pdm > 0), 0.0); ndm2 = ndm.where((ndm > pdm) & (ndm > 0), 0.0)
pdi = 100 * pdm2.ewm(alpha=1/14, adjust=False).mean() / atr; ndi = 100 * ndm2.ewm(alpha=1/14, adjust=False).mean() / atr
dx = 100 * (pdi - ndi).abs() / (pdi + ndi); adx = dx.ewm(alpha=1/14, adjust=False).mean()
ADXUP = adx > adx.shift(5)
ok = C.notna() & e200.notna()
rng = np.random.default_rng(7)
samp = pd.DataFrame(rng.random(C.shape) < 0.1, index=idx, columns=syms)
CROSS = (e25 > e55) & (e25.shift(1) <= e55.shift(1)) & (C > e25) & (C > e55) & (rsi >= 40)
SCAN = (C >= e20) & (C >= e50) & (rsi >= 40)
V = {'CROSS': ok & CROSS, 'CROSS_RSI50+': ok & CROSS & (rsi >= 50), 'SCAN(1/10)': ok & SCAN & samp, 'CONTROL(1/10)': ok & samp}
Hv, Lv, Ov, Cv, ATv = H.values, L.values, O.values, C.values, atr.values
ll5 = L.rolling(5).min().values
mk = C.pct_change(20, fill_method=None).shift(-20).mean(axis=1)  # eq-wt market fwd 20d from signal close (approx)
n, m = Cv.shape


def sim(sig, mode):
    rows = []; sv = sig.values
    for j in range(m):
        busy = -1
        for i in np.flatnonzero(sv[:, j]):
            if i <= busy or i + 2 >= n: continue
            e = Ov[i + 1, j]
            if np.isnan(e) or e <= 0: continue
            sl = ll5[i, j] if mode == 'A' else e - 1.5 * ATv[i, j]
            risk = e - sl
            if not (risk > 0) or risk / e > 0.08: continue
            tg = e + 2 * risk; out = None; k = i + 1
            for k in range(i + 1, min(i + 21, n)):
                l_, h_ = Lv[k, j], Hv[k, j]
                if np.isnan(l_): continue
                if k > i + 1 and Ov[k, j] <= sl: out = ('SL', Ov[k, j]); break
                if l_ <= sl: out = ('SL', sl); break
                if k > i + 1 and Ov[k, j] >= tg: out = ('TG', Ov[k, j]); break
                if h_ >= tg: out = ('TG', tg); break
            if out is None: out = ('TO', Cv[k, j])
            rows.append((idx[i], syms[j], out[0], (out[1] / e - 1) * 100 - 0.25, risk / e * 100, k - i))
            busy = k
    return pd.DataFrame(rows, columns=['date', 'sym', 'exit', 'ret', 'risk', 'days'])


ERAS = [('ALL', '2003', '2026'), ('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'),
        ('last2y', '2024-11', '2026'), ('last6m', '2026-05', '2026'), ('last4m', '2026-07', '2026'), ('last2m', '2026-09', '2026')]
lines = []
for name, sig in V.items():
    for sm in ('A', 'B'):
        T = sim(sig.fillna(False), sm)
        for era, a, b in ERAS:
            t = T[(T.date >= a) & (T.date <= f'{b}-12-31')]
            if len(t) < 20: continue
            w, l_ = t[t.ret > 0], t[t.ret <= 0]
            lines.append(dict(variant=name, stop=sm, era=era, n=len(t), target_hit=round((t.exit == 'TG').mean() * 100, 1),
                              stop_hit=round((t.exit == 'SL').mean() * 100, 1), win_pct=round(len(w) / len(t) * 100, 1),
                              avg_win=round(w.ret.mean(), 2), avg_loss=round(l_.ret.mean(), 2), avg_net=round(t.ret.mean(), 2),
                              med_risk=round(t.risk.median(), 2), days=round(t.days.mean(), 1)))
R = pd.DataFrame(lines)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dhan14_ema2555_rsi.csv')
R.to_csv(out, index=False)
pd.set_option('display.width', 200); print(R.to_string(index=False))
