"""Time-of-day study per stock on 1-hour candles (~2 years, Yahoo) (user, 2 Nov 2026).
Per day: on = prev day last close -> today's first open; h1..h7 = return of each hour (9:15, 10:15, ... 14:15, 15:15 bar; h1 from the open);
rest = close of 10:15 bar... i.e. after the first hour to the day's close; last2 = 14:15 open -> close; day = open -> close;
next_on = today's close -> next open; next_h1 = next day's first hour; hold_next = 15:15 bar open today -> 10:15 next day (buy near close, sell next morning).
Conditions known at that point: gap size, first hour up/down, day so far at 14:15, previous day, weekday, expiry calendar, 'all' (plain average).
Per stock: first half of the days = learn, second half = test. Excess vs all days (or vs 0 for 'all'), Welch t.
Controls: random days (conditions) / random sign flips ('all').  python study/intraday_timing.py out.pkl dir [CHUNK env]"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = sorted(glob.glob(os.path.join(sys.argv[2], '*.csv.gz')))
if os.environ.get('CHUNK'): k, n = map(int, os.environ['CHUNK'].split('/')); files = files[k::n]
rng = np.random.default_rng(11)
def expd(s):
    out = set()
    for (y, m), g in s.groupby([s.dt.year, s.dt.month]):
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0); tgt = 1 if pd.Timestamp(y, m, 1) >= pd.Timestamp(2025, 9, 1) else 3
        while last.dayofweek != tgt: last -= pd.Timedelta(days=1)
        c = g[g <= last]
        if len(c): out.add(c.iloc[-1])
    return out
nifty = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).date
cal = pd.Series(sorted(nifty[nifty >= '2023-01-01'].unique())); m_ = cal.dt.to_period('M'); E_ = expd(cal); L_ = list(cal)
CAL = pd.DataFrame(index=pd.DatetimeIndex(cal))
CAL['expiry'] = CAL.index.isin(E_); CAL['after_expiry'] = CAL.index.isin([L_[i + 1] for i in range(len(L_) - 1) if L_[i] in E_])
CAL['first3'] = CAL.index.isin(cal[cal.groupby(m_).cumcount() < 3]); CAL['month_last'] = CAL.index.isin(cal[m_ != m_.shift(-1)]); CAL['d11_24'] = CAL.index.day.isin(range(11, 25))
SLOTS = ['09:15', '10:15', '11:15', '12:15', '13:15', '14:15', '15:15']
def daytable(d):
    d = d.copy(); d['day'] = d.time.dt.normalize(); d['slot'] = d.time.dt.strftime('%H:%M')
    d = d[d.slot.isin(SLOTS)]
    O = d.pivot_table(index='day', columns='slot', values='open', aggfunc='first').reindex(columns=SLOTS)
    C = d.pivot_table(index='day', columns='slot', values='close', aggfunc='last').reindex(columns=SLOTS)
    ok = O.notna().all(1) & C.notna().all(1); O, C = O[ok], C[ok]
    T = pd.DataFrame(index=O.index)
    prevc = C['15:15'].shift(); T['on'] = O['09:15'] / prevc - 1
    T['h1'] = C['09:15'] / O['09:15'] - 1
    for i in range(1, 7): T[f'h{i + 1}'] = C[SLOTS[i]] / C[SLOTS[i - 1]] - 1
    T['rest'] = C['15:15'] / C['09:15'] - 1; T['last2'] = C['15:15'] / C['13:15'] - 1; T['day'] = C['15:15'] / O['09:15'] - 1
    T['sofar'] = C['14:15'] / O['09:15'] - 1
    T['next_on'] = T.on.shift(-1); T['next_h1'] = T.h1.shift(-1); T['hold_next'] = C['09:15'].shift(-1) / O['15:15'] - 1
    T['prev_day'] = C['15:15'].shift() / C['15:15'].shift(2) - 1
    gap_days = (T.index.to_series().diff().dt.days > 5)
    bad = (T.on.abs() > 0.15) | (T.day.abs() > 0.2) | gap_days
    T.loc[bad, :] = np.nan
    return T.dropna(subset=['h1'])
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['open', 'close'])
    d = d[(d.open > 0) & (d.close > 0)]
    if len(d) < 1500: continue
    T = daytable(d)
    if len(T) < 300: continue
    wd = T.index.dayofweek; cl = CAL.reindex(T.index).fillna(False).astype(bool)
    C = {'all': pd.Series(True, index=T.index), 'gap_up_1%': T.on > 0.01, 'gap_down_1%': T.on < -0.01, 'flat_open': T.on.abs() < 0.002,
         'first_hour_up_1%': T.h1 > 0.01, 'first_hour_down_1%': T.h1 < -0.01, 'gap_down_then_first_hour_down': (T.on < -0.005) & (T.h1 < -0.005),
         'gap_up_then_first_hour_up': (T.on > 0.005) & (T.h1 > 0.005), 'day_down_1.5%_by_2:15': T.sofar < -0.015, 'day_up_1.5%_by_2:15': T.sofar > 0.015,
         'prev_day_down_2%': T.prev_day < -0.02, 'prev_day_up_2%': T.prev_day > 0.02,
         'Mon': pd.Series(wd == 0, index=T.index), 'Tue': pd.Series(wd == 1, index=T.index), 'Wed': pd.Series(wd == 2, index=T.index),
         'Thu': pd.Series(wd == 3, index=T.index), 'Fri': pd.Series(wd == 4, index=T.index),
         'expiry_day': cl.expiry, 'after_expiry': cl.after_expiry, 'first3_days': cl.first3, 'month_last_day': cl.month_last, 'dates_11_24': cl.d11_24}
    # which outcomes are allowed for which condition (no look-ahead: condition known before the outcome starts)
    early = ['on', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'rest', 'last2', 'day', 'next_on', 'next_h1', 'hold_next']
    after1 = ['h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'rest', 'last2', 'next_on', 'next_h1', 'hold_next']
    allowed = {c: early for c in C}
    for c in ('gap_up_1%', 'gap_down_1%', 'flat_open'): allowed[c] = [y for y in early if y != 'on']
    for c in ('first_hour_up_1%', 'first_hour_down_1%', 'gap_down_then_first_hour_down', 'gap_up_then_first_hour_up'): allowed[c] = after1
    for c in ('day_down_1.5%_by_2:15', 'day_up_1.5%_by_2:15'): allowed[c] = ['h7', 'next_on', 'next_h1', 'hold_next']
    half = np.arange(len(T)) >= len(T) // 2
    for hn, hm in (('learn', ~half), ('test', half)):
        for yn in early:
            yv = T[yn].values; base = hm & ~np.isnan(yv)
            if base.sum() < 100: continue
            allv = yv[base]; mu = allv.mean()
            for cn, c in C.items():
                if yn not in allowed[cn]: continue
                cv = c.fillna(False).values.astype(bool) & base; nn = int(cv.sum())
                if nn < 10: continue
                x = yv[cv]
                if cn == 'all':
                    ex = x.mean(); t = ex / (x.std(ddof=1) / np.sqrt(nn) + 1e-12)
                    xr = x * rng.choice([-1, 1], nn); exr = xr.mean(); tr = exr / (xr.std(ddof=1) / np.sqrt(nn) + 1e-12)
                else:
                    ex = x.mean() - mu; t = ex / (x.std(ddof=1) / np.sqrt(nn) + 1e-12)
                    xr = yv[rng.choice(np.flatnonzero(base), nn, replace=False)]; exr = xr.mean() - mu; tr = exr / (xr.std(ddof=1) / np.sqrt(nn) + 1e-12)
                rows.append((s, hn, yn, cn, nn, x.mean(), ex, t, (x > 0).mean(), exr, tr, T.index[base].min(), T.index[base].max()))
    print(s, len(T), flush=True)
R = pd.DataFrame(rows, columns=['stock', 'half', 'out', 'cond', 'n', 'mean', 'excess', 't', 'win', 'excess_rand', 't_rand', 'from', 'to'])
R.to_pickle(OUT); print('rows', len(R))
