"""DHAN-16 (Dhan live G_o3hSSwkVo, MTF swing scan): price above MA (uptrend) + ADX>20 AND rising
+ RSI 55-70 + unusual volume today. Assumed: close>EMA20>EMA50, ADX14>20 & ADX>ADX 3d ago,
RSI14 in [55,70], volume > 1.5x 20d avg. Buy at close. Control = uptrend days only (close>EMA20>EMA50).
Trade view: stop = 10-day low, target 2R, max 20 days, cost 0.25%."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
import ni_common as N
P = N.load(); c = P['a']; h, l, v = P['h'], P['l'], P['v']
w = lambda x, n=14: x.ewm(alpha=1/n, adjust=False).mean()
e20, e50 = c.ewm(span=20, adjust=False).mean(), c.ewm(span=50, adjust=False).mean()
d = c.diff(); rsi = 100 - 100/(1 + w(d.clip(lower=0))/w((-d).clip(lower=0)))
up = h.diff(); dn = -l.diff()
pdm = up.where((up > dn) & (up > 0), 0.0); ndm = dn.where((dn > up) & (dn > 0), 0.0)
tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()]).groupby(level=0).max().reindex(c.index)
atr = w(tr); pdi = 100*w(pdm)/atr; ndi = 100*w(ndm)/atr
adx = w(100*(pdi-ndi).abs()/(pdi+ndi))
trend = (c > e20) & (e20 > e50)
volx = v > 1.5*v.rolling(20).mean()
ev = trend & (adx > 20) & (adx > adx.shift(3)) & (rsi >= 55) & (rsi <= 70) & volx
ev = N.thin(ev.fillna(False), 10); ctrl = N.thin(trend.fillna(False), 10)
F, _ = N.fwd(P, (5, 10, 20))
L = []
for nm, e in [('DHAN-16', ev), ('control uptrend', ctrl)]:
    for r in N.evaluate(e, F, nm, (5, 10, 20)):
        if r['era'] in ('ALL', '2003-12', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis') and 'excess' in r:
            L.append(f"{nm:16s} h{r['h']:2d} {r['era']:9s} n{r['n']:6d} excess {r['excess']:+.2f} med {r['excess_med']:+.2f} win {r['win_vs_mkt']:.0f}% raw_net {r['raw_net']:+.2f}")
# trade sim
cv, hv, lv = c.values, h.values, l.values
lo10 = l.rolling(10).min().values
def sim(e, start=None):
    res = []
    for i, j in zip(*np.nonzero(e.values)):
        if start is not None and c.index[i] < pd.Timestamp(start): continue
        ent = cv[i, j]; st = lo10[i, j]
        if not np.isfinite(st) or st >= ent: continue
        R = ent - st; tg = ent + 2*R; out = None
        for k in range(i+1, min(i+21, len(cv))):
            if lv[k, j] <= st: out = (st/ent-1, 'stop'); break
            if hv[k, j] >= tg: out = (tg/ent-1, 'tgt'); break
        if out is None:
            k = min(i+20, len(cv)-1)
            if not np.isfinite(cv[k, j]) or k == i: continue
            out = (cv[k, j]/ent-1, 'time')
        res.append((c.index[i], out[0]*100 - N.COST, out[1]))
    return pd.DataFrame(res, columns=['d', 'net', 'how'])
ctrl40 = N.thin(trend.fillna(False), 40)
for nm, e in [('DHAN-16', ev), ('control', ctrl)]:
    for lab, s in [('all', None), ('2013+', '2013-01-01'), ('Nov23+', '2023-11-01'), ('last6m', '2026-05-01'), ('last4m', '2026-07-01'), ('last2m', '2026-09-01')]:
        T = sim(e if nm == 'DHAN-16' else ctrl40, s)
        if len(T) == 0: continue
        wn = T.net[T.net > 0]; ls = T.net[T.net <= 0]
        L.append(f"TRADE {nm:8s} {lab:7s} n{len(T):6d} tgt {100*(T.how=='tgt').mean():.1f}% stop {100*(T.how=='stop').mean():.1f}% avg {T.net.mean():+.2f}% avgwin {wn.mean():+.2f} avgloss {ls.mean():+.2f}")
print('\n'.join(L))
