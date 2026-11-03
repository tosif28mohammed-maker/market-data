"""Dip-buying gated by market breadth (f57, 3 Nov 2026).
breadth = share of liquid A/B stocks whose close is below their own 10% lowest distance from SMA-L (learned 2013-20).
Trade: fresh deep dip below SMA-L -> buy at close; sell at first close >= previous day's SMA-L, or after 21 days. Cost 0.35%.
Gate: only on days with breadth >= 20% (market-wide sell-off); optional filter stock above its 200 DMA.
python study/breadth_dip.py panel_close.pkl out.pkl"""
import sys, numpy as np, pandas as pd
P = pd.read_pickle(sys.argv[1]); P = P[P.index >= '2012-01-01']; cov = P.notna().sum(1); P = P[P.index <= cov[cov >= 0.7 * cov.max()].index.max()].ffill(limit=5)
out = []; allT = []; brs = {}
for L in (20, 30):
    ma = P.rolling(L).mean(); dist = P / ma - 1
    A = (P.index >= '2013-01-01') & (P.index < '2021-01-01'); thr = dist[A].quantile(0.10)
    deep = dist.le(thr, axis=1) & dist.notna(); fresh = deep & ~deep.shift(1, fill_value=False)
    br = deep.sum(1) / dist.notna().sum(1); brs[L] = br; up200 = P > P.rolling(200).mean()
    Pv = P.to_numpy(); MAv = ma.to_numpy(); n = len(P)
    for gate in (0.0, 0.2):
        for filt in ('all', 'above200'):
            trades = []
            for i in np.flatnonzero((br >= gate).to_numpy()):
                f = fresh.iloc[i].to_numpy()
                if filt == 'above200': f = f & up200.iloc[i].to_numpy()
                for j in np.flatnonzero(f):
                    e = Pv[i, j]
                    for k in range(i + 1, min(i + 22, n)):
                        if Pv[k, j] >= MAv[k - 1, j] or k == min(i + 21, n - 1): break
                    trades.append((P.index[i], P.columns[j], Pv[k, j] / e - 1 - 0.0035, k - i))
            T = pd.DataFrame(trades, columns=['date', 'stock', 'ret', 'held']); T['L'] = L; T['gate'] = gate; T['filter'] = filt; allT.append(T)
            for per, (a, b) in {'2013-20': ('2013-01-01', '2020-12-31'), '2013-20 बिना COVID': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2026-12-31'), 'Nov23-अब': ('2023-11-01', '2026-12-31')}.items():
                x = T[(T.date >= a) & (T.date <= b)]
                if 'COVID' in per: x = x[~((x.date >= '2020-02-15') & (x.date <= '2020-06-30'))]
                out.append(dict(L=L, breadth_gate=gate, filter=filt, period=per, trades=len(x), win=round((x.ret > 0).mean(), 3), avg_pct=round(x.ret.mean() * 100, 2),
                                worst10_pct=round(x.ret.quantile(.1) * 100, 1), held_days=round(x.held.mean(), 1)))
R = pd.DataFrame(out); pd.to_pickle(dict(table=R, breadth=pd.DataFrame(brs), trades=pd.concat(allT)), sys.argv[2])
pd.set_option('display.width', 250); print(R.to_string(index=False))
