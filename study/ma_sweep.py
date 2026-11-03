"""Every MA length 2..500 (SMA and EMA) on every timeframe (1M,1W,1D,4H,3H,2H,1H) - user, 3 Nov 2026:
'1 se 500 tak sab dekho, koi specific number nahi; kam trade, zabardast fayda'.
Trade rule tested for each MA: BUY at the close when price is far below the MA (its own 10% lowest distance, learned on the first half, fresh);
SELL when the candle's high touches the MA (exit at the MA value) or after W candles at the close (W ~ 1 month: 1H 140, 2H 80, 3H 40, 4H 40, 1D 21, 1W 4, 1M 2).
Also a stop variant: exit at -X% where X = 2.5 x that MA's typical deep-dip further fall (no look-ahead: from first half).
Records per (series, tf, typ, L, half): trades, trades/year, win%, avg %, median %, worst 10% %, avg candles held, back-to-MA %.
Halves: hourly = first/second half (~1.5y each); daily+ = 2013-20 (ex-crisis) vs 2021-26 (+Nov23).
python study/ma_sweep.py out.pkl daily_dir1 [daily_dir2]  (env CHUNK=k/N, ONLY=..., FO=1 for F&O stocks only)"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); H1 = '/home/claude/intrarepo/intra/h1'
OUT = sys.argv[1]; files = {}
for D in sys.argv[2:]:
    for f in sorted(glob.glob(os.path.join(D, '*.csv.gz'))): files.setdefault(os.path.basename(f)[:-7], f)
L = pd.read_csv(os.path.join(ROOT, 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
fo = pd.read_csv(os.path.join(ROOT, 'universe/fo_list.csv')); fo.columns = [c.strip() for c in fo.columns]; FO = set(fo.SYMBOL.str.strip())
names = ['NIFTY', 'BANKNIFTY'] + [s for s in files if L.get(s) in ('A', 'B') and (not os.environ.get('FO') or s in FO)]
if os.environ.get('ONLY'): names = os.environ['ONLY'].split(',')
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); names = names[k_::n_]
TFS = os.environ.get('TFS', '1M,1W,1D,4H,3H,2H,1H').split(',')
W = {'1H': 140, '2H': 80, '3H': 40, '4H': 40, '1D': 21, '1W': 4, '1M': 2}; PERYEAR = {'1H': 1750, '2H': 1000, '3H': 500, '4H': 500, '1D': 248, '1W': 52, '1M': 12}
LENS = list(range(2, 501))
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
def load_daily(s):
    f = os.path.join(ROOT, f'data/{s}.csv') if s in ('NIFTY', 'BANKNIFTY') else files[s]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').set_index('date').sort_index()
    d = d[(d.close > 0) & (d.index >= '2003-01-01')]; j = d.close.pct_change().abs(); bad = np.flatnonzero((j > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    d['high'] = np.maximum(d.high, d.close); d['low'] = np.minimum(d.low, d.close); return d[['open', 'high', 'low', 'close']]
def load_hourly(s):
    f = os.path.join(H1, f'{s}.csv.gz')
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['close']).drop_duplicates('time').set_index('time').sort_index()
    d = d[d.index.strftime('%H:%M').isin(['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15'])]
    if len(d) < 1500 or (d.close.pct_change().abs() > 0.25).any(): return None
    return d[['open', 'high', 'low', 'close']]
def group_h(h, edges):
    hm = h.index.strftime('%H:%M'); grp = np.zeros(len(h), int)
    for k, e in enumerate(edges): grp[hm >= e] = k
    key = h.index.normalize() + pd.to_timedelta(grp, unit='m')
    return h.groupby(key).agg(open=('open', 'first'), high=('high', 'max'), low=('low', 'min'), close=('close', 'last'))
rows = []
def sweep(s, tf, d):
    n = len(d)
    if n < (120 if tf == '1M' else 400): return
    c = d.close.to_numpy(float); hi = d.high.to_numpy(float); lo = d.low.to_numpy(float); idx = d.index; Wn = W[tf]
    if tf in ('1H', '2H', '3H', '4H'): mid = idx[n // 2]; per = {'A': idx < mid, 'B': idx >= mid}
    elif tf == '1M': per = {'A': (idx >= '2005-01-01') & (idx < '2016-01-01'), 'B': idx >= '2016-01-01'}
    else:
        cr = np.zeros(n, bool)
        for a, b in CR: cr |= (idx >= a) & (idx <= b)
        per = {'A': (idx >= '2013-01-01') & (idx < '2021-01-01') & ~cr, 'B': idx >= '2021-01-01', 'N': idx >= '2023-11-01'}
    cs = pd.Series(c, index=idx)
    for typ in ('SMA', 'EMA'):
        for Ln in LENS:
            if n < Ln + (40 if tf == '1M' else 150): break
            ma = (cs.rolling(Ln).mean() if typ == 'SMA' else cs.ewm(span=Ln, adjust=False).mean()).to_numpy(dtype=float, copy=True); ma[:Ln] = np.nan
            dist = c / ma - 1; first = per['A'] & ~np.isnan(ma)
            if first.sum() < (25 if tf == '1M' else 60): continue
            thr = np.nanquantile(dist[first], 0.10)
            sig = (dist <= thr) & ~(np.r_[np.nan, dist[:-1]] <= thr) & ~np.isnan(ma)
            ent = np.flatnonzero(sig)
            if len(ent) == 0: continue
            res = np.full(n, np.nan); held = np.full(n, np.nan); back = np.zeros(n, bool); mae = np.full(n, np.nan)
            last_exit = -1
            for i in ent:
                if i <= last_exit or i >= n - 1: continue   # one trade at a time
                j2 = min(i + Wn, n - 1); seg = np.flatnonzero(hi[i + 1:j2 + 1] >= ma[i + 1:j2 + 1])
                if len(seg): k = i + 1 + seg[0]; res[i] = max(ma[k], lo[k]) / c[i] - 1; back[i] = True
                else: k = j2; res[i] = c[k] / c[i] - 1
                held[i] = k - i; mae[i] = lo[i + 1:k + 1].min() / c[i] - 1; last_exit = k
            for p, m in per.items():
                sel = m & ~np.isnan(res)
                k = int(sel.sum())
                if k == 0: continue
                x = res[sel]; yrs = max(m.sum() / PERYEAR[tf], 0.25)
                rows.append((s, tf, typ, Ln, p, k, k / yrs, float((x > 0).mean()), float(x.mean()), float(np.median(x)), float(np.quantile(x, 0.1)) if k >= 5 else float(x.min()),
                             float(np.nanmean(held[sel])), float(back[sel].mean()), float(np.nanmedian(mae[sel])), float(thr)))
for s in names:
    try:
        dd = load_daily(s)
        if '1D' in TFS: sweep(s, '1D', dd)
        if '1W' in TFS: sweep(s, '1W', dd.resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        if '1M' in TFS: sweep(s, '1M', dd.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last'}).dropna())
        hh = load_hourly(s)
        if hh is not None:
            if '1H' in TFS: sweep(s, '1H', hh)
            if '2H' in TFS: sweep(s, '2H', group_h(hh, ['09:15', '11:15', '13:15', '15:15']))
            if '3H' in TFS: sweep(s, '3H', group_h(hh, ['09:15', '12:15']))
            if '4H' in TFS: sweep(s, '4H', group_h(hh, ['09:15', '13:15']))
    except Exception as e: print('ERR', s, e)
    print(s, flush=True)
R = pd.DataFrame(rows, columns=['stock', 'tf', 'typ', 'L', 'per', 'trades', 'per_year', 'win', 'avg', 'med', 'p10', 'held', 'back', 'mae', 'thr'])
for c_ in R.columns:
    if R[c_].dtype == 'float64': R[c_] = R[c_].astype('float32')
R.to_pickle(OUT); print('done', len(R))
