# r075b discipline check: checklist #5 says 'no cash/intraday entry 9:15-9:30', paper INTRA_GAPFADE enters 9:20.
# Rule (pehle likha): same trades (liq A/B, gap>=2%, top5 by gap/day), entry at close of candle ending 9:20 / 9:30 / 9:45,
# stop = highest high since 9:15 up to entry *1.005, exit 15:15, cost 0.12%. Compare mean, win%, avgW/avgL, worst day, halves.
import glob, os, numpy as np, pandas as pd
G = '/home/claude/market-data/data/gapday'
GU = pd.read_csv('/home/claude/market-data/paper/gap_universe.csv').set_index('symbol'); ok = set(GU.index[GU.liq.isin(['A', 'B'])])
days = sorted(os.path.basename(f)[:10] for f in glob.glob(G + '/2026-*.csv.gz'))
out = []
for day in days:
    z = pd.read_csv(f'{G}/{day}.csv.gz', parse_dates=['time']); cands = []
    for sym, d in z.groupby('symbol'):
        d = d.sort_values('time'); d = d[d.time.dt.strftime('%H:%M') <= '15:15'].reset_index(drop=True)
        if len(d) < 10 or sym not in ok: continue
        g = d.open.iloc[0] / d.prev_close.iloc[0] - 1
        if g >= 0.02: cands.append((g, sym, d))
    cands.sort(key=lambda x: x[0], reverse=True)
    for g, sym, d in cands[:5]:
        for lab, k in [('9:20', 0), ('9:30', 2), ('9:45', 5)]:
            if len(d) <= k + 2: continue
            entry = d.close.iloc[k]; stop = d.high.iloc[:k + 1].max() * 1.005; ex = None
            for r in d.iloc[k + 1:].itertuples():
                if r.high >= stop: ex = stop; break
            if ex is None: ex = d.close.iloc[-1]
            out.append(dict(day=day, sym=sym, t=lab, pnl=(entry / ex - 1) * 100 - 0.12, risk=(stop / entry - 1) * 100))
R = pd.DataFrame(out); half = days[len(days) // 2]
for t, y in R.groupby('t'):
    w = y.pnl[y.pnl > 0]; l = y.pnl[y.pnl <= 0]; dd = y.groupby('day').pnl.sum()
    print(t, 'n', len(y), 'mean', round(y.pnl.mean(), 3), 'win%', round(len(w) / len(y) * 100, 1), 'avgW', round(w.mean(), 2), 'avgL', round(l.mean(), 2),
          'avg risk%', round(y.risk.mean(), 2), 'mean/risk', round((y.pnl / y.risk).mean(), 3), 'worst day', round(dd.min(), 2),
          'H1', round(y[y.day < half].pnl.mean(), 3), 'H2', round(y[y.day >= half].pnl.mean(), 3))
p = R.pivot_table(index=['day', 'sym'], columns='t', values='pnl').dropna()
rng = np.random.default_rng(0)
for b in ['9:30', '9:45']:
    dlt = (p[b] - p['9:20']); dday = dlt.groupby(level=0).mean()
    bs = [rng.choice(dday.values, len(dday)).mean() for _ in range(3000)]
    print(b, '-9:20 per trade', round(dlt.mean(), 3), 'day-bootstrap 95%', np.percentile(bs, [2.5, 97.5]).round(3))
