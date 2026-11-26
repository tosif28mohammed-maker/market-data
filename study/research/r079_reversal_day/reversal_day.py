"""r079 (26 Nov 2026): gold/silver 'key reversal day' in a deep drawdown -> does it mark a turn?
RULE WRITTEN BEFORE RESULTS (data/global CMD_GOLD, CMD_SILVER daily OHLC; only rows with high>low):
 Zone: gold >=15% / silver >=30% below 252-day high (same as r069).
 Event A: today's LOW is a new 20-day low (below min low of prior 20 days) AND today's CLOSE > yesterday's close
          AND close in upper half of the day range ((c-l)/(h-l) >= 0.6). One event per 15 days.
 Chance C: all zone days. Forward 5/20/60 trading days; extra fall within 60d (median min/entry-1);
 'low held' = share of events where the next 60 days never closed below the event-day LOW.
 Eras 2000-14 vs 2015-26; USD, INR (x FX_USDINR), KWD (x FX_USDKWD) closes for forward returns.
 PASS = A beats C by >=2% at 60d (p<=0.10 by random draw) in both eras and INR agrees; then his 2:1 bar.
 Like 25 Nov 2026: gold low $3,426 (Kitco spot) close $3,576 +0.6%; silver low $38.09 close $41.12.
"""
import numpy as np, pandas as pd
R = '/home/claude/market-data'
def g(f):
    d = pd.read_csv(f'{R}/data/global/{f}.csv', parse_dates=['date']).set_index('date')
    return d[~d.index.duplicated()].dropna()
I = g('FX_USDINR').close; K = g('FX_USDKWD').close
rng = np.random.default_rng(79)
for nm, th in (('CMD_GOLD', .15), ('CMD_SILVER', .30)):
    d = g(nm); d = d[d.close > 0]
    ok = d.high > d.low
    print(f'\n=== {nm}: rows {len(d)}, with real range {ok.mean()*100:.0f}% (from {d[ok].index[0].date()})')
    c = d.close; zone = c / c.rolling(252).max() - 1 <= -th
    lowprev = d.low.where(ok).rolling(20).min().shift(1)
    pos = (d.close - d.low) / (d.high - d.low)
    A = ok & zone & (d.low < lowprev) & (c > c.shift(1)) & (pos >= .6)
    ev = []; last = None
    for t in A[A].index:
        if last is None or (t - last).days > 21: ev.append(t); last = t
    ev = [t for t in ev if t < c.index[-61]] if len(ev) else ev
    for cur, s in (('USD', c), ('INR', (c * I.reindex(c.index).ffill()).dropna()), ('KWD', (c * K.reindex(c.index).ffill()).dropna())):
        for era, a, b in (('2000-14', '2000', '2014'), ('2015-26', '2015', '2026')):
            e = [t for t in ev if a <= str(t.year) <= b and t in s.index]
            if not e: print(f'  {cur} {era}: n0'); continue
            rows = []
            for t in e:
                i = s.index.get_loc(t); fw = s.iloc[i:i + 61]
                rows.append({'d': t.date(), 'f5': (s.iloc[i+5]/s.iloc[i]-1)*100, 'f20': (s.iloc[i+20]/s.iloc[i]-1)*100,
                             'f60': (s.iloc[i+60]/s.iloc[i]-1)*100, 'fall': (fw.min()/s.iloc[i]-1)*100,
                             'held': bool((c.reindex(fw.index).iloc[1:] >= d.low[t]).all())})
            E = pd.DataFrame(rows)
            zc = zone.reindex(s.index).fillna(False); zc = zc[(zc.index.year >= int(a)) & (zc.index.year <= int(b))]
            f60 = (s.shift(-60) / s - 1) * 100; base = f60[zc[zc].index].dropna()
            sims = np.array([rng.choice(base.values, len(E)).mean() for _ in range(4000)]) if len(base) else np.array([np.nan])
            p = (sims >= E.f60.mean()).mean()
            print(f'  {cur} {era}: n{len(E)} f5 {E.f5.mean():+.1f} f20 {E.f20.mean():+.1f} f60 {E.f60.mean():+.1f} (up {100*(E.f60>0).mean():.0f}%) '
                  f'vs chance {base.mean():+.1f} p_hi {p:.2f} | extra fall median {E.fall.median():+.1f} | low held {100*E.held.mean():.0f}%')
            if cur == 'USD': print('    ', E.round(1).to_dict('records'))
