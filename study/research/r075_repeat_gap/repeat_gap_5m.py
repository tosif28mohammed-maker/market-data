# r075 (5-min, exact INTRA_GAPFADE rule): does the fade fail on REPEAT gappers?
# Rule (pehle likha): every liq A/B stock in data/gapday with open >= prev_close*1.02 -> short at 9:20 close (1st candle close),
# stop = 1st candle high*1.005 (5-min high check), exit 15:15 close. cost 0.12%. Scenario by yesterday:
# R = also gap-up >=2% yesterday (in yesterday's gapday file); U = yesterday close/prevclose >= +5% w/o gap; N = rest.
# Also 'top5' = the 5 largest gaps per day (what paper takes). Acceptance: Tosif bar not applicable (no target) -> use mean/trade, win%, avg win/avg loss.
import glob, os, numpy as np, pandas as pd
G = '/home/claude/market-data/data/gapday'
GU = pd.read_csv('/home/claude/market-data/paper/gap_universe.csv').set_index('symbol')
okliq = set(GU.index[GU.liq.isin(['A', 'B'])])
days = sorted(os.path.basename(f)[:10] for f in glob.glob(G + '/2026-*.csv.gz'))
rows = []; prev_gap = set(); prev_ret = {}
for day in days:
    z = pd.read_csv(f'{G}/{day}.csv.gz', parse_dates=['time'])
    today_gap = set(); today_ret = {}
    for sym, d in z.groupby('symbol'):
        d = d.sort_values('time'); d = d[d.time.dt.strftime('%H:%M') <= '15:15']
        if len(d) < 10: continue
        pc = d.prev_close.iloc[0]; g = d.open.iloc[0] / pc - 1
        today_ret[sym] = d.close.iloc[-1] / pc - 1
        if g >= 0.02: today_gap.add(sym)
        if g < 0.02 or sym not in okliq: continue
        entry = d.close.iloc[0]; stop = d.high.iloc[0] * 1.005; ex = None; why = 'close'
        for r in d.iloc[1:].itertuples():
            if r.high >= stop: ex = stop; why = 'SL'; break
        if ex is None: ex = d.close.iloc[-1]
        pnl = (entry / ex - 1) * 100 - 0.12
        sc = 'R-repeat' if sym in prev_gap else ('U-up yday' if prev_ret.get(sym, 0) >= 0.05 else 'N-normal')
        rows.append(dict(day=day, sym=sym, gap=g * 100, pnl=pnl, why=why, sc=sc, liq=GU.loc[sym, 'liq']))
    prev_gap = today_gap; prev_ret = today_ret
R = pd.DataFrame(rows)
R['rk'] = R.groupby('day').gap.rank(ascending=False, method='first'); R['top5'] = R.rk <= 5
R.to_csv('/home/claude/market-data/study/research/r075_repeat_gap/trades_5m.csv', index=False)
def s(g):
    w = g.pnl[g.pnl > 0]; l = g.pnl[g.pnl <= 0]
    return pd.Series({'n': len(g), 'mean': g.pnl.mean(), 'median': g.pnl.median(), 'win%': len(w) / len(g) * 100,
                      'avgW': w.mean(), 'avgL': l.mean(), 'SL%': (g.why == 'SL').mean() * 100})
print('days', len(days), days[0], days[-1])
print('ALL trades\n', R.groupby('sc').apply(s).round(2).to_string())
print('TOP5 (paper-like)\n', R[R.top5].groupby('sc').apply(s).round(2).to_string())
R['half'] = np.where(R.day < days[len(days) // 2], 'H1', 'H2')
print('by half\n', R.groupby(['half', 'sc']).pnl.agg(['size', 'mean']).round(2).unstack('sc').to_string())
R['gb'] = pd.cut(R.gap, [2, 3.5, 5, 8, 50])
print('by gap size\n', R.groupby(['gb', 'sc'], observed=True).pnl.agg(['size', 'mean']).round(2).unstack('sc').to_string())
# chance: shuffle scenario labels 5000x, R minus rest
rng = np.random.default_rng(0); isR = (R.sc == 'R-repeat').values; real = R.pnl[isR].mean() - R.pnl[~isR].mean()
sims = [R.pnl.values[p].mean() - R.pnl.values[~p].mean() for p in (rng.permutation(isR) for _ in range(5000))]
print('R - rest', round(real, 3), 'p', np.mean(np.abs(sims) >= abs(real)))
# what-if: paper top5 excluding repeat -> next candidate fills
Rx = R[R.sc != 'R-repeat'].copy(); Rx['rk2'] = Rx.groupby('day').gap.rank(ascending=False, method='first')
for lab, y in [('paper top5 now', R[R.top5]), ('top5 skip repeat', Rx[Rx.rk2 <= 5])]:
    d = y.groupby('day').pnl.sum()
    print(lab, 'trades', len(y), 'mean/trade', round(y.pnl.mean(), 3), 'sum%', round(y.pnl.sum(), 1), 'worst day', round(d.min(), 2),
          'H1', round(y[y.day < days[len(days)//2]].pnl.mean(), 3), 'H2', round(y[y.day >= days[len(days)//2]].pnl.mean(), 3))
