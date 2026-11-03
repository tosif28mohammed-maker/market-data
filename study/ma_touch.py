"""MA 'touch & return' study on many timeframes and MA lengths (user, 3 Nov 2026: '200 rarely touched, 113 touched often;
far below -> buy, near -> avoid; check month, week, day, 4h, 3h, 2h, 1h, 125m, 75m').
Timeframes: 1M, 1W, 1D (daily 2003-26); 4H, 3H, 2H, 1H (built from 1-hour candles, ~3 years). (75m/125m need long 5-min history - being collected.)
MA: SMA and EMA, lengths 5,10,14,20,30,50,70,100,113,150,200 on close.
Per series x timeframe x MA:
  touch_rate     share of candles whose high-low range contains the MA (how often price meets the MA)
  gap_bars       median candles between touches
  DEEP (close below its own 10% lowest distance from the MA, learned on the first half, fresh):
     back%      share that touched the MA again within H candles (H ~ 2 weeks: 1H 70, 2H 40, 3H 20, 4H 20, 1D 10, 1W 2, 1M 1; and ~1 month x2)
     bars_back  median candles until the touch; mae = median further fall before the touch; gain = median move from entry to the MA at touch
     ret_H      move after H candles (drift-adjusted)
  NEAR (|distance| <= 0.5%): forward H-candle move and its spread vs all candles  ('avoid zone' check)
Halves: hourly TFs = first vs second half of ~3 years; daily+ = 2013-20 (ex-crisis) vs 2021-26 (+ Nov23-now).
python study/ma_touch.py out.pkl daily_dir1 [daily_dir2]  (env CHUNK=k/N, ONLY=NIFTY,BANKNIFTY)"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H1 = '/home/claude/intrarepo/intra/h1'
OUT = sys.argv[1]; files = {}
for D in sys.argv[2:]:
    for f in sorted(glob.glob(os.path.join(D, '*.csv.gz'))): files.setdefault(os.path.basename(f)[:-7], f)
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
names = ['NIFTY', 'BANKNIFTY'] + [s for s in files if L.get(s) in ('A', 'B')]
if os.environ.get('ONLY'): names = os.environ['ONLY'].split(',')
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); names = names[k_::n_]
LENS = [5, 10, 14, 20, 30, 50, 70, 100, 113, 150, 200]
HZ = {'1H': 70, '2H': 40, '3H': 20, '4H': 20, '1D': 10, '1W': 2, '1M': 1}
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def load_daily(s):
    f = os.path.join(ROOT, f'data/{s}.csv') if s in ('NIFTY', 'BANKNIFTY') else files[s]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').set_index('date').sort_index()
    d = d[(d.close > 0) & (d.index >= '2003-01-01')]; j = d.close.pct_change().abs(); bad = np.flatnonzero((j > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    d['high'] = np.maximum(d.high, d.close); d['low'] = np.minimum(d.low, d.close)
    return d[['open', 'high', 'low', 'close']]
def load_hourly(s):
    f = os.path.join(H1, f'{s}.csv.gz')
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close']).drop_duplicates('time').set_index('time').sort_index()
    d = d[d.index.strftime('%H:%M').isin(['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15'])]
    if len(d) < 1500 or (d.close.pct_change().abs() > 0.25).any(): return None
    return d[['open', 'high', 'low', 'close']]
def group_h(h, edges):   # edges: list of slot-start strings; each candle starts at an edge
    hm = h.index.strftime('%H:%M'); grp = np.zeros(len(h), int)
    for k, e in enumerate(edges): grp[hm >= e] = k
    key = h.index.normalize() + pd.to_timedelta(grp, unit='m')
    return h.groupby(key).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
rows = []
def study(s, tf, d):
    n = len(d)
    if n < (100 if tf == '1M' else 300): return
    c = d.close.to_numpy(float); hi = d.high.to_numpy(float); lo = d.low.to_numpy(float); idx = d.index; H = HZ[tf]
    fH = np.full(n, np.nan); fH[:-H] = c[H:] / c[:-H] - 1; f2 = np.full(n, np.nan); f2[:-2 * H] = c[2 * H:] / c[:-2 * H] - 1
    if tf in ('1H', '2H', '3H', '4H'): mid = idx[n // 2]; per = {'A': idx < mid, 'B': idx >= mid}
    else:
        cr = np.zeros(n, bool)
        for a, b in CR: cr |= (idx >= a) & (idx <= b)
        per = {'A': (idx >= '2013-01-01') & (idx < '2021-01-01') & ~cr, 'B': idx >= '2021-01-01', 'N': idx >= '2023-11-01'}
        if tf == '1M': per = {'A': (idx >= '2005-01-01') & (idx < '2016-01-01'), 'B': idx >= '2016-01-01'}
    cs = pd.Series(c, index=idx)
    for typ in ('SMA', 'EMA'):
        for Ln in LENS:
            if n < Ln + 60: continue
            ma = (cs.rolling(Ln).mean() if typ == 'SMA' else cs.ewm(span=Ln, adjust=False).mean()).to_numpy(dtype=float, copy=True); ma[:Ln] = np.nan
            ok = ~np.isnan(ma); touch = ok & (lo <= ma) & (hi >= ma); dist = c / ma - 1
            first = per['A'] & ok
            if first.sum() < (30 if tf == '1M' else 60): continue
            thr = np.nanquantile(dist[first], 0.10)
            deep = ok & (dist <= thr) & ~(np.r_[np.nan, dist[:-1]] <= thr)
            near = ok & (np.abs(dist) <= 0.005)
            tidx = np.flatnonzero(touch)
            for p, m in per.items():
                mm = m & ok
                if mm.sum() < 50: continue
                tr = touch[mm].mean(); ep = touch & ~np.r_[False, touch[:-1]]; ti = np.flatnonzero(ep & mm); gap = float(np.median(np.diff(ti))) if len(ti) > 3 else np.nan   # candles between separate touch episodes
                sel = np.flatnonzero(deep & m)
                back = []; bars = []; mae = []; gain = []; back2 = []
                for i in sel:
                    j1 = min(i + H, n - 1); j2 = min(i + 2 * H, n - 1)
                    if i + 1 > n - 1: continue
                    seg = np.flatnonzero(hi[i + 1:j2 + 1] >= ma[i + 1:j2 + 1])
                    hit1 = len(seg) and seg[0] + 1 <= H; hit2 = len(seg) > 0
                    back.append(bool(hit1)); back2.append(bool(hit2))
                    if hit2:
                        k = i + 1 + seg[0]; bars.append(k - i); gain.append(ma[k] / c[i] - 1); mae.append(lo[i + 1:k + 1].min() / c[i] - 1)
                    else: mae.append(lo[i + 1:j2 + 1].min() / c[i] - 1 if j2 > i else np.nan)
                drift = np.nanmean(fH[mm])
                rec = dict(stock=s, tf=tf, typ=typ, L=Ln, per=p, bars_total=int(mm.sum()), touch_rate=float(tr), gap_bars=gap, thr=float(thr), n_deep=len(back),
                           back_H=float(np.mean(back)) if back else np.nan, back_2H=float(np.mean(back2)) if back2 else np.nan,
                           bars_back=float(np.median(bars)) if bars else np.nan, mae=float(np.nanmedian(mae)) if mae else np.nan, mae90=float(np.nanquantile(mae, 0.1)) if len(mae) > 4 else np.nan,
                           gain=float(np.median(gain)) if gain else np.nan, retH_deep=float(np.nanmean(fH[sel]) - drift) if len(sel) else np.nan,
                           n_near=int((near & m).sum()), retH_near=float(np.nanmean(fH[near & m]) - drift) if (near & m).sum() else np.nan,
                           sdH_near=float(np.nanstd(fH[near & m])) if (near & m).sum() > 5 else np.nan, sdH_all=float(np.nanstd(fH[mm])))
                rows.append(rec)
for s in names:
    try:
        dd = load_daily(s); study(s, '1D', dd)
        study(s, '1W', dd.resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        study(s, '1M', dd.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        hh = load_hourly(s)
        if hh is not None:
            study(s, '1H', hh)
            study(s, '2H', group_h(hh, ['09:15', '11:15', '13:15', '15:15']))
            study(s, '3H', group_h(hh, ['09:15', '12:15']))
            study(s, '4H', group_h(hh, ['09:15', '13:15']))
    except Exception as e: print('ERR', s, e)
    print(s, flush=True)
R = pd.DataFrame(rows)
for c_ in R.columns:
    if R[c_].dtype == 'float64': R[c_] = R[c_].astype('float32')
R.to_pickle(OUT); print('done', len(R))
