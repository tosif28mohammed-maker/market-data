# ROBOT
"""ET-02 part 2b: same as marubozu_stops but entry = NEXT DAY OPEN (no lookahead), filter stock>200DMA, styles B(-5/+10) C(-8/+8), 20d, cost 0.25%."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, thin, REPO
P = load(); o, h, l, c = P['o'], P['h'], P['l'], P['a']
rng = h - l; avg = rng.rolling(20).mean().shift(1)
big = (c / o - 1 >= 0.03) & (rng >= 1.5 * avg) & (P['v'] > 0)
ratio = (c - o) / rng.replace(0, np.nan); up = c > c.rolling(200).mean()
O, H, L, C = o.values, h.values, l.values, c.values; idx = c.index; N = len(idx)
rows = []
for name, ev in {'marubozu': thin(big & (ratio >= 0.9), 10) & up, 'wick_placebo': thin(big & (ratio < 0.6) & (ratio > 0), 10) & up}.items():
    ii, jj = np.nonzero(ev.values)
    for sl, tp in ((0.05, 0.10), (0.08, 0.08)):
        res = []
        for i, j in zip(ii, jj):
            if i + 21 >= N or np.isnan(O[i + 1, j]): continue
            e = O[i + 1, j]; st, tg = e * (1 - sl), e * (1 + tp); out = None
            for k in range(i + 1, i + 21):
                if np.isnan(L[k, j]): continue
                if L[k, j] <= st: out = (-sl, 'stop'); break
                if H[k, j] >= tg: out = (tp, 'tgt'); break
            if out is None: out = (C[i + 20, j] / e - 1, 'time')
            res.append((idx[i], out[0] - 0.0025, out[1]))
        d = pd.DataFrame(res, columns=['dt', 'r', 'why'])
        for tag, x in [('all', d), ('03-12', d[d.dt < '2013']), ('13-20', d[(d.dt >= '2013') & (d.dt < '2021')]), ('21-26', d[d.dt >= '2021'])] + \
                      [(f'last{m}m', d[d.dt >= idx[-1] - pd.DateOffset(months=m)]) for m in (2, 4, 6)]:
            rows.append(dict(ev=name, style=f'-{int(sl*100)}/+{int(tp*100)}', part=tag, n=len(x), dates=x.dt.nunique(), tgt_hit=round((x.why == 'tgt').mean()*100, 1),
                             avg_win=round(x.r[x.r > 0].mean()*100, 2), avg_loss=round(x.r[x.r <= 0].mean()*100, 2), exp=round(x.r.mean()*100, 2)))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); print(R.to_string(index=False))
R.to_csv(f'{REPO}/study/research/r063_marubozu_stops/nextopen.csv', index=False)
