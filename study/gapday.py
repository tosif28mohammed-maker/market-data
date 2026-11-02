"""Morning gap vs the day (daily OHLC, 2003-2026), per stock (user, 2 Nov 2026: timing study).
on = overnight (prev close -> open), oc = open -> close same day, o3 = open -> close 2 days later, o5 = open -> close 4 days later.
Conditions known before or at the open (gap size, previous day, weekday, calendar). For each stock, rule and period:
mean excess of the outcome on condition days vs all days of that period (Welch t). Control: the same number of random days.
Days where open == previous close exactly, or open outside the day's range, are dropped (Yahoo fills missing opens).
python study/gapday.py out.pkl dir1 [dir2 ...]   (env CHUNK=k/N)"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k, n = map(int, os.environ['CHUNK'].split('/')); files = files[k::n]
rng = np.random.default_rng(7)
PER = {'2003-12': ('2003-01-01', '2012-12-31'), '2013-20': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2026-12-31'),
       'R1 2021-Oct23': ('2021-01-01', '2023-10-31'), 'R2 Nov23-now': ('2023-11-01', '2026-12-31')}
def expd(s):
    out = set()
    for (y, m), g in s.groupby([s.dt.year, s.dt.month]):
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0); tgt = 1 if pd.Timestamp(y, m, 1) >= pd.Timestamp(2025, 9, 1) else 3
        while last.dayofweek != tgt: last -= pd.Timedelta(days=1)
        c = g[g <= last]
        if len(c): out.add(c.iloc[-1])
    return out
nifty = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).date
cal = pd.Series(sorted(nifty[nifty >= '2002-01-01'].unique())); m_ = cal.dt.to_period('M'); E_ = expd(cal); L_ = list(cal)
CAL = pd.DataFrame(index=pd.DatetimeIndex(cal))
CAL['expiry'] = CAL.index.isin(E_); CAL['after_expiry'] = CAL.index.isin([L_[i + 1] for i in range(len(L_) - 1) if L_[i] in E_])
CAL['first3'] = CAL.index.isin(cal[cal.groupby(m_).cumcount() < 3]); CAL['month_last'] = CAL.index.isin(cal[m_ != m_.shift(-1)])
CAL['d11_24'] = CAL.index.day.isin(range(11, 25))
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'high', 'low', 'close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[(d.close > 0) & (d.open > 0)].reset_index(drop=True)
    if len(d) < 500: continue
    pc = d.close.shift(); on = d.open / pc - 1; oc = d.close / d.open - 1; cc = d.close / pc - 1
    bad = (d.open == pc) | (d.open > d.high * 1.001) | (d.open < d.low * 0.999) | (cc.abs() > 0.2) | (on.abs() > 0.15)
    o3 = d.close.shift(-2) / d.open - 1; o5 = d.close.shift(-4) / d.open - 1
    for k_ in (1, 2, 3, 4): bad_f = bad.shift(-k_, fill_value=False)
    o3[bad | bad.shift(-1, fill_value=False) | bad.shift(-2, fill_value=False)] = np.nan
    o5[bad | sum(bad.shift(-j, fill_value=False) for j in range(1, 5)).astype(bool)] = np.nan
    on[bad] = np.nan; oc[bad] = np.nan
    pr = d.high.shift() - d.low.shift(); pos = (pc - d.low.shift()) / pr.replace(0, np.nan)   # where yesterday closed in its range
    pcc = cc.shift(); poc = oc.shift()
    wd = d.date.dt.dayofweek; cl = CAL.reindex(d.date).fillna(False).astype(bool).reset_index(drop=True)
    C = {'gap_up_1%': on > 0.01, 'gap_up_2%': on > 0.02, 'gap_down_1%': on < -0.01, 'gap_down_2%': on < -0.02,
         'flat_open': on.abs() < 0.002,
         'prev_day_down_2%': pcc < -0.02, 'prev_day_up_2%': pcc > 0.02, 'prev_closed_at_low': pos < 0.2, 'prev_closed_at_high': pos > 0.8,
         'prev_intraday_down_1%': poc < -0.01, 'prev_intraday_up_1%': poc > 0.01,
         'gap_down_after_down_day': (on < -0.005) & (pcc < -0.01), 'gap_up_after_up_day': (on > 0.005) & (pcc > 0.01),
         'Mon': wd == 0, 'Tue': wd == 1, 'Wed': wd == 2, 'Thu': wd == 3, 'Fri': wd == 4,
         'expiry_day': cl.expiry, 'after_expiry': cl.after_expiry, 'first3_days': cl.first3, 'month_last_day': cl.month_last, 'dates_11_24': cl.d11_24}
    Y = {'on': on, 'oc': oc, 'o3': o3, 'o5': o5}
    gapc = {'gap_up_1%', 'gap_up_2%', 'gap_down_1%', 'gap_down_2%', 'flat_open', 'gap_down_after_down_day', 'gap_up_after_up_day'}
    for pn, (a, b) in PER.items():
        pm = ((d.date >= a) & (d.date <= b)).values
        if pm.sum() < 200: continue
        for yn, y in Y.items():
            yv = y.values; base = pm & ~np.isnan(yv)
            if base.sum() < 150: continue
            allv = yv[base]; mu_all = allv.mean(); sd_all = allv.std()
            for cn, c in C.items():
                if yn == 'on' and cn in gapc: continue
                cv = c.fillna(False).values.astype(bool) & base; nn = int(cv.sum())
                if nn < 15: continue
                x = yv[cv]; ex = x.mean() - mu_all; t = ex / (x.std(ddof=1) / np.sqrt(nn) + 1e-12)
                ridx = rng.choice(np.flatnonzero(base), nn, replace=False); xr = yv[ridx]; exr = xr.mean() - mu_all; tr = exr / (xr.std(ddof=1) / np.sqrt(nn) + 1e-12)
                rows.append((s, pn, yn, cn, nn, x.mean(), ex, t, (x > 0).mean(), mu_all, exr, tr, (xr > 0).mean()))
    print(s, flush=True)
R = pd.DataFrame(rows, columns=['stock', 'period', 'out', 'cond', 'n', 'mean', 'excess', 't', 'win', 'base_mean', 'excess_rand', 't_rand', 'win_rand'])
R.to_pickle(OUT); print('rows', len(R))
