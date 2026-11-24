# ROBOT
"""ET-02 part 2: White Marubozu + stop/target styles + trend filters. Entry = event close.
Styles: (A) stop = candle low, target 2R; (B) stop -5%, target +10%; (C) stop -8%, target +8%; time exit 20d. Cost 0.25% round trip.
Filters: all / stock>200DMA / stock>200DMA & EW-market>200DMA. Placebo = wick big up-days, same rules."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, thin, REPO
P = load(); o, h, l, c = P['o'], P['h'], P['l'], P['a']
rng = h - l; avg = rng.rolling(20).mean().shift(1)
big = (c / o - 1 >= 0.03) & (rng >= 1.5 * avg) & (P['v'] > 0)
ratio = (c - o) / rng.replace(0, np.nan)
ma200 = c.rolling(200).mean()
mkt = c.pct_change().mean(axis=1).fillna(0).add(1).cumprod(); mreg = mkt > mkt.rolling(200).mean()
up = c > ma200
base = {'marubozu': thin(big & (ratio >= 0.9), 10), 'wick_placebo': thin(big & (ratio < 0.6) & (ratio > 0), 10)}
H, L, C = h.values, l.values, c.values; idx = c.index; N = len(idx)
def sim(i, j, stop, tgt, T=20):
    e = C[i, j]
    for k in range(i + 1, min(i + 1 + T, N)):
        if np.isnan(L[k, j]): continue
        if L[k, j] <= stop: return stop / e - 1, 'stop', k
        if H[k, j] >= tgt: return tgt / e - 1, 'tgt', k
    k = min(i + T, N - 1)
    if i + T >= N: return np.nan, 'open', k
    return C[k, j] / e - 1, 'time', k
rows = []
for name, ev in base.items():
    for filt in ('all', 'stock>200', 'stock>200&mkt>200'):
        m = ev.copy()
        if filt != 'all': m &= up
        if filt == 'stock>200&mkt>200': m = m & pd.DataFrame(np.repeat(mreg.values[:, None], m.shape[1], 1), index=m.index, columns=m.columns)
        ii, jj = np.nonzero(m.values)
        for style in ('A_low_2R', 'B_5_10', 'C_8_8'):
            res = []
            for i, j in zip(ii, jj):
                e = C[i, j]
                if style == 'A_low_2R':
                    s = L[i, j]; r = e - s
                    if not (r > 0) or r / e > 0.15: continue
                    st, tg = s, e + 2 * r
                elif style == 'B_5_10': st, tg = e * 0.95, e * 1.10
                else: st, tg = e * 0.92, e * 1.08
                ret, why, k = sim(i, j, st, tg)
                if why == 'open': continue
                res.append((idx[i], ret - 0.0025, why))
            d = pd.DataFrame(res, columns=['dt', 'r', 'why'])
            if d.empty: continue
            def summ(x, tag):
                w = x.r[x.r > 0]; ls = x.r[x.r <= 0]
                return dict(ev=name, filt=filt, style=style, part=tag, n=len(x), tgt_hit=round((x.why == 'tgt').mean() * 100, 1),
                            win=round((x.r > 0).mean() * 100, 1), avg_win=round(w.mean() * 100, 2), avg_loss=round(ls.mean() * 100, 2),
                            exp=round(x.r.mean() * 100, 2))
            rows.append(summ(d, 'all'))
            for a, b, tag in (('2003', '2012', '03-12'), ('2013', '2020', '13-20'), ('2021', '2026', '21-26')):
                x = d[(d.dt >= a) & (d.dt <= b + '-12-31')]
                if len(x): rows.append(summ(x, tag))
            last = idx[-1]
            for mo in (2, 4, 6):
                x = d[d.dt >= last - pd.DateOffset(months=mo)]
                if len(x): rows.append(summ(x, f'last{mo}m'))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
print('data till', idx[-1].date()); print(R.to_string(index=False))
R.to_csv(f'{REPO}/study/research/r063_marubozu_stops/results.csv', index=False)
