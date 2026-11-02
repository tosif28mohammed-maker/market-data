"""Today's candle vs the candles of the previous 1..5 days (user, 2 Nov 2026).
Features of day t-L (L=1..5): body (open->close), whole-day move (close->close), upper wick, lower wick, where it closed in its range,
range size, gap at open; multi-day moves (2,3,5 days); and today's open vs yesterday's high/low (known at 9:15).
Outcomes today: green (close>open), up (close>prev close), new high (high > yesterday high), new low (low < yesterday low), today's open->close and close->close.
Aggregates counts per (feature, lag, bucket, period, crisis, weekday-of-today) per stock + a 6% random row sample for modelling.
python study/candle_link.py out_prefix dir1 [dir2]  (env CHUNK=k/N)"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
P = lambda *x: [-np.inf, *x, np.inf]
BK = {'body': P(-0.03, -0.01, -0.003, 0.003, 0.01, 0.03), 'move': P(-0.03, -0.01, -0.003, 0.003, 0.01, 0.03), 'upwick': P(0.003, 0.01, 0.02, 0.04),
      'lowwick': P(0.003, 0.01, 0.02, 0.04), 'closepos': P(0.1, 0.3, 0.5, 0.7, 0.9), 'range': P(0.01, 0.02, 0.03, 0.05), 'gap': P(-0.02, -0.005, -0.001, 0.001, 0.005, 0.02),
      'move2': P(-0.05, -0.02, 0, 0.02, 0.05), 'move3': P(-0.06, -0.03, 0, 0.03, 0.06), 'move5': P(-0.08, -0.04, 0, 0.04, 0.08),
      'open_vs_prevhigh': P(-0.02, -0.005, 0, 0.005, 0.02), 'open_vs_prevlow': P(-0.02, -0.005, 0, 0.005, 0.02),
      'wpos': P(0.1, 0.3, 0.5, 0.7, 0.9), 'wrange': P(0.02, 0.04, 0.07, 0.12, 0.2), 'open_vs_whigh': P(-0.08, -0.04, -0.02, -0.005, 0, 0.01), 'open_vs_wlow': P(-0.01, 0, 0.005, 0.02, 0.04, 0.08),
      'open_vs_avghigh': P(-0.04, -0.02, -0.005, 0, 0.005, 0.02), 'open_vs_avglow': P(-0.02, -0.005, 0, 0.005, 0.02, 0.04), 'close_vs_avgclose': P(-0.05, -0.02, -0.005, 0.005, 0.02, 0.05),
      'wmove': P(-0.08, -0.03, -0.01, 0.01, 0.03, 0.08)}
aggs = []; samp = []; rng = np.random.default_rng(23)
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[(d.close > 0) & (d.open > 0) & (d.date >= '2003-01-01')].reset_index(drop=True)
    if len(d) < 500: continue
    o, h, l, c = d.open, np.maximum(d.high, d.close), np.minimum(d.low, d.close), d.close; pc = c.shift()
    bad = (o == pc) | (o > h * 1.001) | (o < l * 0.999) | ((c / pc - 1).abs() > 0.2) | ((o / pc - 1).abs() > 0.15) | (h == l)
    base = pd.DataFrame({'body': c / o - 1, 'move': c / pc - 1, 'upwick': (h - np.maximum(o, c)) / pc, 'lowwick': (np.minimum(o, c) - l) / pc,
                         'closepos': (c - l) / (h - l), 'range': (h - l) / pc, 'gap': o / pc - 1})
    base[bad] = np.nan
    Y = pd.DataFrame({'green': (c > o).astype(float), 'up': (c > pc).astype(float), 'newhigh': (h > h.shift()).astype(float), 'newlow': (l < l.shift()).astype(float),
                      'oc': c / o - 1, 'cc': c / pc - 1, 'hi': h / o - 1, 'lo': l / o - 1}); Y[bad] = np.nan
    F = {}
    for L in range(1, 6):
        for k in ('body', 'move', 'upwick', 'lowwick', 'closepos', 'range', 'gap'): F[(k, L)] = base[k].shift(L)
    for k, n in (('move2', 2), ('move3', 3), ('move5', 5)): F[(k, 1)] = (c / c.shift(n) - 1).shift(1)
    F[('open_vs_prevhigh', 0)] = o / h.shift() - 1; F[('open_vs_prevlow', 0)] = o / l.shift() - 1
    for N in (2, 3, 4, 5, 8, 15):   # windows of the last N days (ending yesterday)
        hN = h.rolling(N).max().shift(); lN = l.rolling(N).min().shift(); ahN = h.rolling(N).mean().shift(); alN = l.rolling(N).mean().shift()
        acN = c.rolling(N).mean().shift(); oN = o.shift(N)
        F[('wpos', N)] = (pc - lN) / (hN - lN)               # where yesterday closed inside the N-day high-low range
        F[('wrange', N)] = hN / lN - 1                       # how wide the N-day range is
        F[('open_vs_whigh', N)] = o / hN - 1                 # today's open vs N-day highest
        F[('open_vs_wlow', N)] = o / lN - 1                  # today's open vs N-day lowest
        F[('open_vs_avghigh', N)] = o / ahN - 1              # today's open vs average of N daily highs
        F[('open_vs_avglow', N)] = o / alN - 1               # today's open vs average of N daily lows
        F[('close_vs_avgclose', N)] = pc / acN - 1           # yesterday close vs N-day average close
        F[('wmove', N)] = pc / oN - 1                        # N-day move from the first day's open to yesterday's close
        for k_ in ('wpos', 'wrange', 'open_vs_whigh', 'open_vs_wlow', 'open_vs_avghigh', 'open_vs_avglow', 'close_vs_avgclose', 'wmove'): F[(k_, N)][bad] = np.nan
    F[('open_vs_prevhigh', 0)][bad] = np.nan; F[('open_vs_prevlow', 0)][bad] = np.nan
    dt = d.date; era = np.select([dt < '2013-01-01', dt < '2021-01-01'], ['2003-12', '2013-20'], '2021-26'); cr = np.zeros(len(d), bool)
    for a, b in CR: cr |= ((dt >= a) & (dt <= b)).values
    n23 = (dt >= '2023-11-01').values; wd = dt.dt.dayofweek.values
    ok = Y.green.notna().values
    for (k, L), x in F.items():
        b = pd.cut(x, BK[k], labels=False).values; m = ok & ~np.isnan(b)
        T = pd.DataFrame({'era': era[m], 'cr': cr[m], 'n23': n23[m], 'wd': wd[m], 'b': b[m], 'green': Y.green.values[m], 'up': Y.up.values[m], 'newhigh': Y.newhigh.values[m], 'newlow': Y.newlow.values[m], 'oc': Y.oc.values[m], 'cc': Y.cc.values[m], 'hi': Y.hi.values[m], 'lo': Y.lo.values[m]}); T['oc2'] = T.oc ** 2
        g = T.groupby(['era', 'cr', 'n23', 'b']).agg(n=('green', 'size'), green=('green', 'sum'), up=('up', 'sum'), newhigh=('newhigh', 'sum'), newlow=('newlow', 'sum'), soc=('oc', 'sum'), scc=('cc', 'sum'), soc2=('oc2', 'sum'), shi=('hi', 'sum'), slo=('lo', 'sum')).reset_index()
        g['feat'] = k; g['lag'] = L; g['stock'] = s; aggs.append(g)
    X = pd.DataFrame({f'{k}_{L}': v for (k, L), v in F.items()}); X = pd.concat([X, Y], axis=1); X['date'] = dt; X['stock'] = s; X['wd'] = wd
    X = X[ok & (rng.random(len(X)) < 0.06)]; samp.append(X.astype({c_: 'float32' for c_ in X.columns if c_ not in ('date', 'stock', 'wd')}))
    print(s, flush=True)
A = pd.concat(aggs)
for c_ in ('n', 'green', 'up', 'newhigh', 'newlow'): A[c_] = A[c_].astype('int32')
A.to_pickle(OUT + '_agg.pkl'); pd.concat(samp).to_pickle(OUT + '_sample.pkl'); print('done')
