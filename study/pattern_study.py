"""Apply every signal of study/pattern_lib.py to every stock; event study (user, 2 Nov 2026 night).
Entry = next day's open after the signal day close. Outcomes (in the signal's direction, minus the stock's normal drift for that horizon & era):
 d1 = next day open->close, f5/f10/f20 = next open -> close 5/10/20 trading days later. Win = direction-adjusted f10 > 0.
Placebo control: the same signal dates moved 61 trading days later (keeps clustering, breaks the link).
Aggregates per (stock, signal, period, placebo). Periods: 2003-12 ex-crisis, 2013-20 ex-crisis, 2021-26, Nov23-now.
python study/pattern_study.py out.pkl dir1 [dir2]  (env CHUNK=k/N)"""
import sys, os, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pattern_lib import signals
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
LIQ = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'study/results/liq_all.csv')).set_index('symbol').liquidity.str[0]
CR = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    if LIQ.get(s, 'D') == 'D': continue
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').set_index('date').sort_index()
    d = d[(d.close > 0) & (d.open > 0)]
    jr = d.close.pct_change().abs(); bad = np.flatnonzero((jr > 0.3).values)
    if len(bad): d = d.iloc[bad[-1]:]
    d = d[d.index >= '2002-01-01']
    if len(d) < 400: continue
    d['high'] = np.maximum(d.high, np.maximum(d.open, d.close)); d['low'] = np.minimum(d.low, np.minimum(d.open, d.close))
    if 'volume' not in d: d['volume'] = 0
    try: S = signals(d)
    except Exception as e: print('ERR', s, e); continue
    o = d.open.values; c = d.close.values; n = len(d); idx = d.index
    def fwd(k):
        r = np.full(n, np.nan)
        if n > k: r[:n - k] = c[k:] / o[1:n - k + 1] - 1 if k >= 1 else np.nan
        return r
    d1 = np.full(n, np.nan); d1[:-1] = c[1:] / o[1:] - 1
    F = {'d1': d1, 'f5': np.full(n, np.nan), 'f10': np.full(n, np.nan), 'f20': np.full(n, np.nan)}
    for k, nm in ((5, 'f5'), (10, 'f10'), (20, 'f20')):
        if n > k: F[nm][:n - k] = c[k:] / o[1:n - k + 1] - 1
    era = np.select([idx < '2013-01-01', idx < '2021-01-01'], ['2003-12', '2013-20'], '2021-26'); cr = np.zeros(n, bool)
    for a, b in CR: cr |= (idx >= a) & (idx <= b)
    pmask = {'2003-12x': (era == '2003-12') & ~cr, '2013-20x': (era == '2013-20') & ~cr, '2021-26': era == '2021-26', 'Nov23': idx >= '2023-11-01'}
    drift = {p: {k: np.nanmean(v[m]) if m.sum() > 50 else np.nan for k, v in F.items()} for p, m in pmask.items()}
    for name, (dr, sig) in S.items():
        sig = np.asarray(sig, bool)
        if sig.sum() == 0: continue
        for plc in (False, True):
            sg = np.roll(sig, 61) if plc else sig
            if plc: sg[:61] = False
            for p, m in pmask.items():
                sel = sg & m & ~np.isnan(F['f10'])
                k = int(sel.sum())
                if k == 0: continue
                rec = dict(stock=s, sig=name, dir=dr, period=p, plc=plc, n=k)
                for kk, v in F.items():
                    x = dr * (v[sel] - drift[p][kk]); x = x[~np.isnan(x)]
                    rec[f'{kk}_sum'] = float(x.sum()); rec[f'{kk}_n'] = len(x); rec[f'{kk}_sq'] = float((x ** 2).sum())
                rec['win10'] = int((dr * F['f10'][sel] > 0).sum()); rec['win1'] = int((dr * d1[sel] > 0).sum())
                rows.append(rec)
    print(s, flush=True)
R = pd.DataFrame(rows)
for c_ in R.columns:
    if R[c_].dtype == 'float64': R[c_] = R[c_].astype('float32')
R.to_pickle(OUT); print('done', len(R))
