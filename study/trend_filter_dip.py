"""Does the stock's own trend decide whether a deep-dip buy works? (user, 3 Nov 2026: 'buy only when sideways or up; in a long down-trend the
MA comes down to the price and the "touch" is fake').
Dip = fresh close below its own 10% lowest distance from SMA20 (learned 2013-20). Exit: first close >= previous day's SMA20, or 21 days. Cost 0.35%.
Trend labels on the entry day (no look-ahead):
  long  : 200-DMA slope over 20 days (>+1% up, <-1% down, else flat) and price vs 200 DMA
  mid   : 50-DMA slope over 10 days (>+1% up, <-1% down, else flat)
  short : 20-DMA slope over 5 days
  52w   : return over 250 days (<-20% / -20..+20 / >+20%)
Also: market breadth gate (>=20%) x long trend. Periods 2013-20 (ex-COVID), 2021-26, Nov23-now.
python study/trend_filter_dip.py panel_close.pkl out.pkl"""
import sys, numpy as np, pandas as pd
P = pd.read_pickle(sys.argv[1]); P = P[P.index >= '2011-01-01']; cov = P.notna().sum(1); P = P[P.index <= cov[cov >= 0.7 * cov.max()].index.max()].ffill(limit=5)
ma20 = P.rolling(20).mean(); ma50 = P.rolling(50).mean(); ma200 = P.rolling(200).mean(); dist = P / ma20 - 1
A = (P.index >= '2013-01-01') & (P.index < '2021-01-01'); thr = dist[A].quantile(0.10)
deep = dist.le(thr, axis=1) & dist.notna(); fresh = deep & ~deep.shift(1, fill_value=False)
br = deep.sum(1) / dist.notna().sum(1)
def lab(s, up, dn): return np.where(s > up, 'up', np.where(s < dn, 'down', 'flat'))
sl200 = ma200 / ma200.shift(20) - 1; sl50 = ma50 / ma50.shift(10) - 1; sl20 = ma20 / ma20.shift(5) - 1; r52 = P / P.shift(250) - 1
Pv = P.to_numpy(); MAv = ma20.to_numpy(); n = len(P); rows = []
ii, jj = np.nonzero(fresh.to_numpy())
for i, j in zip(ii, jj):
    if np.isnan(sl200.iat[i, j]) or i >= n - 2: continue
    e = Pv[i, j]; k = i + 1; low = e
    for k in range(i + 1, min(i + 22, n)):
        low = min(low, Pv[k, j]) if not np.isnan(Pv[k, j]) else low
        if Pv[k, j] >= MAv[k - 1, j] or k == min(i + 21, n - 1): break
    rows.append((P.index[i], P.columns[j], Pv[k, j] / e - 1 - 0.0035, k - i, low / e - 1, sl200.iat[i, j], P.iat[i, j] > ma200.iat[i, j], sl50.iat[i, j], sl20.iat[i, j], r52.iat[i, j], br.iat[i]))
T = pd.DataFrame(rows, columns=['date', 'stock', 'ret', 'held', 'mae', 'sl200', 'above200', 'sl50', 'sl20', 'r52', 'breadth'])
T['long'] = lab(T.sl200, 0.01, -0.01); T['mid'] = lab(T.sl50, 0.01, -0.01); T['short'] = lab(T.sl20, 0.01, -0.01)
T['y52'] = np.where(T.r52 < -0.2, 'down>20%', np.where(T.r52 > 0.2, 'up>20%', 'flat'))
T['gate'] = np.where(T.breadth >= 0.2, 'panic', 'calm')
covid = (T.date >= '2020-02-15') & (T.date <= '2020-06-30'); gfc = (T.date >= '2008-01-01') & (T.date <= '2009-06-30')
PER = {'2013-20 बिना COVID': (T.date >= '2013-01-01') & (T.date < '2021-01-01') & ~covid, '2021-26': T.date >= '2021-01-01', 'Nov23-अब': T.date >= '2023-11-01'}
out = []
def agg(name, key):
    for per, m in PER.items():
        for g, x in T[m].groupby(key):
            out.append(dict(view=name, group=' | '.join(g) if isinstance(g, tuple) else g, period=per, trades=len(x), win=round((x.ret > 0).mean(), 3),
                            avg_pct=round(x.ret.mean() * 100, 2), med_pct=round(x.ret.median() * 100, 2), worst10=round(x.ret.quantile(.1) * 100, 1),
                            mae_med=round(x.mae.median() * 100, 1), held=round(x.held.mean(), 1)))
T['all'] = 'सब dip'; agg('सब', 'all')
agg('लंबा trend (200 DMA ढलान)', 'long')
T['a2'] = np.where(T.above200, '200 के ऊपर', '200 के नीचे'); agg('200 DMA के ऊपर/नीचे', 'a2')
agg('मध्य trend (50 DMA)', 'mid'); agg('छोटा trend (20 DMA)', 'short'); agg('52 हफ्ते का return', 'y52')
agg('लंबा × मध्य', ['long', 'mid']); agg('घबराहट × लंबा', ['gate', 'long']); agg('घबराहट × 52w', ['gate', 'y52'])
R = pd.DataFrame(out); pd.to_pickle(dict(table=R, trades=T), sys.argv[2])
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 400); print(R.to_string(index=False))
