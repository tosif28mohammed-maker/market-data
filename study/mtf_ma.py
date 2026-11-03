"""Multi-timeframe moving-average study (user, 3 Nov 2026: 'day, week, 4 hours, 1 hour - aur koi bhi MA').
Timeframes: 1H (1-hour candles ~3 years), 4H (two candles per day: 9:15-13:15, 13:15-15:30), 1D (daily 2003-2026), 1W (weekly).
MAs: SMA and EMA, lengths 5,10,20,50,100,113,150,200 (on close; high/low used for touches).
Signals per MA:
  XU  close crosses above the MA                XD  close crosses below the MA
  DIP close far below the MA (its own 10% lowest distance, learned on the first half), fresh
  TOUCH_UP  in an uptrend (MA rising, close above) the candle's LOW touches the MA and closes above it (pullback buy)
Outcomes (direction-adjusted for XD): return after ~1 week and ~1 month of trading (1H: 35/140 bars, 4H: 10/40, 1D: 5/21, 1W: 1/4),
  minus the series' normal drift for that horizon; win = outcome > 0; for DIP also 'touched the MA within ~1 month'.
Halves: 1H/4H = first half vs second half of the ~3 years; 1D/1W = 2013-20 (ex-crisis) vs 2021-26 (+ Nov23-now).
Placebo: signal dates moved by 1/3 of the sample (circular) -> chance level.
python study/mtf_ma.py out.pkl daily_dir1 [daily_dir2]   (hourly from /home/claude/intrarepo/intra/h1; env CHUNK=k/N; env ONLY=NIFTY,BANKNIFTY)"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H1 = '/home/claude/intrarepo/intra/h1'
OUT = sys.argv[1]; files = {}
for D in sys.argv[2:]:
    for f in sorted(glob.glob(os.path.join(D, '*.csv.gz'))): files.setdefault(os.path.basename(f)[:-7], f)
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
names = [s for s in files if L.get(s) in ('A', 'B')]
if os.environ.get('ONLY'): names = os.environ['ONLY'].split(',')
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); names = names[k_::n_]
LENS = [5, 10, 20, 50, 100, 113, 150, 200]; HZ = {'1H': (35, 140), '4H': (10, 40), '1D': (5, 21), '1W': (1, 4)}
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def load_daily(s):
    if s in ('NIFTY', 'BANKNIFTY'): d = pd.read_csv(os.path.join(ROOT, f'data/{s}.csv'), parse_dates=['date'])
    else: d = pd.read_csv(files[s], parse_dates=['date'])
    d = d.dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').set_index('date').sort_index(); d = d[(d.close > 0) & (d.index >= '2003-01-01')]
    j = d.close.pct_change().abs(); bad = np.flatnonzero((j > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    return d[['open', 'high', 'low', 'close']]
def load_hourly(s):
    f = os.path.join(H1, f'{s}.csv.gz')
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close']).drop_duplicates('time').set_index('time').sort_index()
    d = d[(d.close > 0)]; d = d[d.index.strftime('%H:%M').isin(['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15'])]
    j = d.close.pct_change().abs()
    if (j > 0.25).any(): return None
    return d[['open', 'high', 'low', 'close']]
def to4h(h):
    g = np.where(h.index.strftime('%H:%M') < '13:15', 0, 1); key = h.index.normalize() + pd.to_timedelta(g * 4, unit='h')
    return h.groupby(key).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
def toW(d): return d.resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna()
rows = []
def study(s, tf, d):
    n = len(d)
    if n < 400: return
    c = d.close.to_numpy(float); lo = d.low.to_numpy(float); idx = d.index; h1, h2 = HZ[tf]
    f1 = np.full(n, np.nan); f2 = np.full(n, np.nan); f1[:-h1] = c[h1:] / c[:-h1] - 1; f2[:-h2] = c[h2:] / c[:-h2] - 1
    if tf in ('1H', '4H'):
        mid = idx[n // 2]; per = {'A': idx < mid, 'B': idx >= mid}
    else:
        cr = np.zeros(n, bool)
        for a, b in CR: cr |= (idx >= a) & (idx <= b)
        per = {'A': (idx >= '2013-01-01') & (idx < '2021-01-01') & ~cr, 'B': idx >= '2021-01-01', 'N': idx >= '2023-11-01'}
    drift = {p: (np.nanmean(f1[m]), np.nanmean(f2[m])) for p, m in per.items()}
    cs = pd.Series(c, index=idx)
    for typ in ('SMA', 'EMA'):
        for Ln in LENS:
            if n < Ln * 2 + 50: continue
            ma = (cs.rolling(Ln).mean() if typ == 'SMA' else cs.ewm(span=Ln, adjust=False).mean()).to_numpy(dtype=float, copy=True)
            ma[:Ln] = np.nan
            above = c > ma; prev = np.r_[False, above[:-1]]; valid = ~np.isnan(ma) & ~np.isnan(np.r_[np.nan, ma[:-1]])
            dist = c / ma - 1
            first = per['A']; thr = np.nanquantile(dist[first & valid], 0.10) if (first & valid).sum() > 100 else np.nan
            dip = valid & (dist <= thr) & ~(np.r_[np.nan, dist[:-1]] <= thr)
            rising = np.r_[np.full(5, False), ma[5:] > ma[:-5]]
            touch = valid & rising & (lo <= ma) & (c > ma) & np.r_[False, (c > ma)[:-1]]
            sig = {'XU': (1, valid & above & ~prev), 'XD': (-1, valid & ~above & prev), 'DIP': (1, dip), 'TOUCH_UP': (1, touch)}
            # did price get back to the MA within the 1-month horizon (for DIP)
            for nm, (dr, sg) in sig.items():
                for plc in (False, True):
                    g = np.roll(sg, n // 3) if plc else sg
                    for p, m in per.items():
                        sel = g & m & ~np.isnan(f2)
                        k = int(sel.sum())
                        if k == 0: continue
                        a1 = dr * (f1[sel] - drift[p][0]); a2 = dr * (f2[sel] - drift[p][1])
                        rec = dict(stock=s, tf=tf, typ=typ, L=Ln, sig=nm, per=p, plc=plc, n=k, s1=float(np.nansum(a1)), s2=float(np.nansum(a2)),
                                   w1=int((dr * f1[sel] > 0).sum()), w2=int((dr * f2[sel] > 0).sum()), q2=float(np.nansum(a2 ** 2)))
                        if nm == 'DIP':
                            hit = 0
                            for i in np.flatnonzero(sel):
                                j2 = min(i + h2, n - 1)
                                if (d.high.to_numpy()[i + 1:j2 + 1] >= ma[i + 1:j2 + 1]).any(): hit += 1
                            rec['touch'] = hit
                        rows.append(rec)
for s in names:
    try:
        dd = load_daily(s); study(s, '1D', dd); study(s, '1W', toW(dd))
        hh = load_hourly(s)
        if hh is not None and len(hh) > 1500: study(s, '1H', hh); study(s, '4H', to4h(hh))
    except Exception as e: print('ERR', s, e)
    print(s, flush=True)
R = pd.DataFrame(rows)
for c_ in R.columns:
    if R[c_].dtype == 'float64': R[c_] = R[c_].astype('float32')
R.to_pickle(OUT); print('done', len(R))
