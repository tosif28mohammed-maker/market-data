"""Feature table for every gap day (|gap| >= 1%) of every stock, 2012-2026. Only facts known at 9:15 on that day.
Outcomes: green (close > open), oc (open->close), held (close beyond prev close in the gap direction), o3 (open -> close 2 days later).
python study/gapfeat.py out.pkl dir1 [dir2 ...]   (env CHUNK=k/N)"""
import sys, os, glob, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k, n = map(int, os.environ['CHUNK'].split('/')); files = files[k::n]
HJ = pd.read_csv(os.path.join(HERE, 'hijri_tbla.csv'), parse_dates=['date']).set_index('date').hijri
NF = pd.read_csv(os.path.join(ROOT, 'data/NIFTY.csv'), parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index()
VX = pd.read_csv(os.path.join(ROOT, 'data/INDIAVIX.csv'), parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index().close
mk = pd.DataFrame({'nifty_gap': NF.open / NF.close.shift() - 1, 'nifty_prev': NF.close.pct_change().shift(), 'nifty_vs200': (NF.close / NF.close.rolling(200).mean() - 1).shift(),
                   'nifty_ret20': (NF.close / NF.close.shift(20) - 1).shift(), 'vix_prev': VX.reindex(NF.index).ffill().shift()})
mk.loc[mk.nifty_gap.abs() > 0.1, 'nifty_gap'] = np.nan
cal = pd.Series(NF.index[NF.index >= '2007-01-01'])
def expd(s):
    out = set()
    for (y, m), g in s.groupby([s.dt.year, s.dt.month]):
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0); tgt = 1 if pd.Timestamp(y, m, 1) >= pd.Timestamp(2025, 9, 1) else 3
        while last.dayofweek != tgt: last -= pd.Timedelta(days=1)
        c = g[g <= last]
        if len(c): out.add(c.iloc[-1])
    return out
E_ = sorted(expd(cal)); m_ = cal.dt.to_period('M')
CAL = pd.DataFrame(index=pd.DatetimeIndex(cal))
CAL['tday_of_month'] = cal.groupby(m_).cumcount().values + 1; CAL['tdays_left'] = cal.groupby(m_).cumcount(ascending=False).values
nxt_exp = pd.Series(pd.DatetimeIndex(E_)).searchsorted(cal); ex = pd.DatetimeIndex(E_)
CAL['days_to_expiry'] = [int(np.busday_count(d.date(), ex[i].date())) if i < len(ex) else np.nan for d, i in zip(cal, nxt_exp)]
CAL['after_expiry'] = CAL.index.isin([cal.iloc[i + 1] for i in range(len(cal) - 1) if cal.iloc[i] in set(E_)])
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[(d.close > 0) & (d.open > 0)].reset_index(drop=True)
    if len(d) < 400: continue
    c = d.close; pc = c.shift(); gap = d.open / pc - 1; cc = c / pc - 1
    bad = (d.open == pc) | (d.open > d.high * 1.001) | (d.open < d.low * 0.999) | (cc.abs() > 0.2) | (gap.abs() > 0.15) | (d.high == d.low)
    # facts known at the open (all based on yesterday and before)
    F = pd.DataFrame({'stock': s, 'date': d.date, 'gap': gap})
    for L in (5, 10, 20, 50, 100, 200): F[f'vs_ma{L}'] = (pc / c.rolling(L).mean().shift() - 1)
    F['vs_ema20'] = pc / c.ewm(span=20, adjust=False).mean().shift() - 1
    F['ret1'] = cc.shift(); F['ret5'] = (c / c.shift(5) - 1).shift(); F['ret20'] = (c / c.shift(20) - 1).shift(); F['ret250'] = (c / c.shift(250) - 1).shift()
    dl = c.diff(); up = dl.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean(); dn = (-dl.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    F['rsi14'] = (100 - 100 / (1 + up / dn.replace(0, np.nan))).shift()
    rng_ = (d.high - d.low).shift(); F['prev_close_pos'] = ((pc - d.low.shift()) / rng_.replace(0, np.nan))
    F['prev_range'] = (rng_ / pc)
    F['atr_pct'] = ((d.high - d.low) / c).rolling(20).mean().shift()
    F['gap_in_atr'] = gap / F.atr_pct
    F['near_52w_high'] = pc / c.rolling(250).max().shift() - 1; F['near_52w_low'] = pc / c.rolling(250).min().shift() - 1
    F['vol_ratio_prev'] = (d.volume / d.volume.rolling(20).mean()).shift() if 'volume' in d else np.nan
    F['streak'] = np.sign(cc).groupby((np.sign(cc) != np.sign(cc).shift()).cumsum()).cumcount().add(1).mul(np.sign(cc)).shift()
    # outcomes
    F['green'] = (c > d.open).astype(float); F['oc'] = c / d.open - 1
    F['held'] = np.where(gap > 0, c > pc, c < pc).astype(float); F['o3'] = c.shift(-2) / d.open - 1
    F['hi_oc'] = d.high / d.open - 1; F['lo_oc'] = d.low / d.open - 1
    F = F[(~bad) & (gap.abs() >= 0.01) & (d.date >= '2012-01-01')]
    rows.append(F); print(s, flush=True)
X = pd.concat(rows, ignore_index=True)
X = X.join(mk, on='date').join(CAL, on='date')
X['dow'] = X.date.dt.dayofweek; X['dom'] = X.date.dt.day; X['month'] = X.date.dt.month
h = HJ.reindex(X.date).values; X['h_month'] = pd.Series(h).str[5:7].astype(float).values; X['h_day'] = pd.Series(h).str[8:10].astype(float).values
X.to_pickle(OUT); print('rows', len(X))
