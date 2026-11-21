# ROBOT
"""Claim tests 22 Nov 2026 (02:11 run).
DHAN-09 (Dhan 'ORB, Darvas Box & NR7', https://www.youtube.com/watch?v=iPss0F6CLPk): NR7 day = narrowest high-low range of last 7 days;
  breakout above NR7 high next day -> long, stop = NR7 low. ASSUMED: trend filter close>SMA50; entry at NR7 high (or open if gap above),
  targets 1R/1.5R/2R, max 10 days, stop checked first on same bar (conservative). Control = same rules on prior-day-high breakout
  WITHOUT NR7 (any day). Costs 0.25%. Liquidity D excluded (ni_common).
BF-01 (Ben Felix 'The Truth About Investing at All-Time Highs', https://www.youtube.com/watch?v=WEClhtPD5Ko): buying Nifty at an
  all-time high gives no worse forward return than other days. Test on data/NIFTY.csv 20/60/120/250-day forward returns.
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, COST
P = load()
o, h, l, c = P['o'], P['h'], P['l'], P['a']
rng = h - l
nr7 = (rng <= rng.rolling(7).min()) & (c > c.rolling(50).mean())
pdh = (c > c.rolling(50).mean())  # control: every trend day
H, L, O, C = h.values, l.values, o.values, c.values
dates = c.index
def sim(sig, tgtR):
    out = []
    S = sig.values
    for j in range(S.shape[1]):
        last = -99
        for i in np.flatnonzero(S[:, j]):
            if i <= last or i + 1 >= len(dates):
                continue
            hi, lo = H[i, j], L[i, j]
            if not (hi > lo > 0) or np.isnan(H[i+1, j]):
                continue
            if H[i+1, j] < hi:
                continue  # no breakout next day
            ent = max(hi, O[i+1, j]); risk = ent - lo
            if risk <= 0 or risk / ent > 0.10:
                continue
            tgt = ent + tgtR * risk; res = None
            for k in range(i+1, min(i+11, len(dates))):
                if L[k, j] <= lo: res = ('stop', lo, k); break
                if H[k, j] >= tgt and k > i+1 or (k == i+1 and C[k, j] >= tgt): res = ('tgt', tgt, k); break
            if res is None:
                k = min(i+10, len(dates)-1); res = ('time', C[k, j], k)
            if np.isnan(res[1]): continue
            out.append((dates[i+1], res[0], (res[1]/ent-1)*100 - COST)); last = res[2]
    return pd.DataFrame(out, columns=['date', 'exit', 'net'])
def summ(df, name):
    rows = []
    end = dates[-1]
    for era, s, e in [('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'),
                      ('last6m', end - pd.DateOffset(months=6), end), ('last4m', end - pd.DateOffset(months=4), end),
                      ('last2m', end - pd.DateOffset(months=2), end), ('ALL', '2003', '2026')]:
        d = df[(df.date >= pd.Timestamp(s)) & (df.date <= (pd.Timestamp(e) + pd.offsets.YearEnd(0) if isinstance(e, str) else e))]
        if len(d) < 20: rows.append(dict(test=name, era=era, n=len(d))); continue
        w, ls = d[d.net > 0].net, d[d.net <= 0].net
        rows.append(dict(test=name, era=era, n=len(d), tgt_hit=round((d.exit == 'tgt').mean()*100, 1),
                         win=round((d.net > 0).mean()*100, 1), avg_win=round(w.mean(), 2), avg_loss=round(ls.mean(), 2),
                         avg_net=round(d.net.mean(), 3)))
    return rows
R = []
for t in (1.0, 1.5, 2.0):
    R += summ(sim(nr7, t), f'NR7_{t}R')
    R += summ(sim(pdh & ~nr7, t), f'CTRL_{t}R')
res = pd.DataFrame(R)
# BF-01 Nifty ATH
n = pd.read_csv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'NIFTY.csv'))
n.columns = [x.lower() for x in n.columns]
n['date'] = pd.to_datetime(n['date']); n = n.set_index('date').sort_index()
cl = n['close'].astype(float)
ath = cl >= cl.cummax()
bf = []
for hz in (20, 60, 120, 250):
    f = (cl.shift(-hz) / cl - 1) * 100
    for era, s, e in [('ALL', '1990', '2026'), ('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026')]:
        m = (cl.index >= s) & (cl.index <= e + '-12-31') & f.notna().values
        a, na = f[m & ath.values], f[m & ~ath.values]
        bf.append(dict(test='BF01_ATH', h=hz, era=era, n_ath=len(a), ath_avg=round(a.mean(), 2), other_avg=round(na.mean(), 2),
                       ath_pos=round((a > 0).mean()*100, 1), other_pos=round((na > 0).mean()*100, 1)))
out = os.path.join(os.path.dirname(__file__), 'dhan_nr7_ath.csv')
pd.concat([res, pd.DataFrame(bf)]).to_csv(out, index=False)
pd.set_option('display.width', 200); print(res.to_string()); print(pd.DataFrame(bf).to_string()); print('Nifty data', cl.index[0], cl.index[-1])
