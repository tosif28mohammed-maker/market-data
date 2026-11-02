"""Stock's own eras + long-base breakout study (user idea, 2 Nov 2026, from the Reliance chart: Feb 2017, Jun 2020, Jan 2024 breakouts;
old resistance 1300 later acting as support).
For each stock:
  eras  = dates when the close made a fresh multi-year high (above the highest close of the previous 500 trading days, after at least
          6 months without a new 2-year high = a base) -> 'breakout'; or a fresh 500-day low -> 'breakdown'. These split the chart
          into the stock's own periods.
  study A (breakout): buy at the breakout close; forward 20/60/120/250-day return minus the stock's normal return in that era.
  study B (retest)  : after a breakout, the first close back within -3%..+3% of the old high (the broken line) inside 250 days;
                      forward returns from there, and how often it fell >10% below the line (failed).
Events at least 60 days apart. Eras for comparison: 2003-12, 2013-20, 2021-26.
Usage: python study/breakout.py out.pkl dir1 [dir2 ...]"""
import sys, os, glob, numpy as np, pandas as pd
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += glob.glob(os.path.join(D, '*.csv.gz'))
H = [20, 60, 120, 250]; LB = 500
def era(d): return '2003-12' if d.year <= 2012 else '2013-20' if d.year <= 2020 else '2021-26'
ev = []; regimes = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').sort_values('date').reset_index(drop=True)
    d = d[d.close > 0].reset_index(drop=True)
    r = d.close.pct_change(); bad = np.flatnonzero((r.abs() > 0.25).values)
    if len(bad): d = d.iloc[bad[-1]:].reset_index(drop=True)
    if len(d) < LB + 300: continue
    c = d.close.values; n = len(c); dates = d.date
    hi = pd.Series(c).shift(1).rolling(LB).max().values; lo = pd.Series(c).shift(1).rolling(LB).min().values
    fwd = {h: np.r_[c[h:] / c[:-h] - 1, [np.nan] * h] for h in H}
    base = {}
    for h in H:   # normal forward return per era for this stock
        x = pd.Series(fwd[h]); base[h] = x.groupby(dates.map(era)).mean().to_dict()
    last = -10 ** 9; prev_hi = -10 ** 9; prev_lo = -10 ** 9
    for t in range(LB + 1, n):
        if not np.isfinite(hi[t]): continue
        newhi = c[t] > hi[t]; newlo = c[t] < lo[t]
        brk = newhi and t - prev_hi >= 120      # first new 2-year high after a pause (base) of 6+ months
        dn = newlo and t - prev_lo >= 120
        if newhi: prev_hi = t
        if newlo: prev_lo = t
        if brk or dn: regimes.append(dict(stock=s, date=dates[t].date(), kind='breakout' if brk else 'breakdown', level=round(hi[t] if brk else lo[t], 2), close=c[t]))
        if brk and t - last >= 60:
            last = t; L = hi[t]; e = era(dates[t])
            rec = dict(stock=s, date=dates[t].date(), era=e, kind='A_breakout', level=L, entry=c[t])
            for h in H: rec[f'r{h}'] = fwd[h][t]; rec[f'x{h}'] = fwd[h][t] - base[h].get(e, np.nan)
            ev.append(rec)
            for u in range(t + 5, min(t + 250, n)):   # first retest of the broken line
                if 0.97 * L <= c[u] <= 1.03 * L:
                    e2 = era(dates[u]); rr = dict(stock=s, date=dates[u].date(), era=e2, kind='B_retest', level=L, entry=c[u], days_after=u - t,
                                                  failed=bool((c[u:min(u + 120, n)] < 0.9 * L).any()))
                    for h in H: rr[f'r{h}'] = fwd[h][u]; rr[f'x{h}'] = fwd[h][u] - base[h].get(e2, np.nan)
                    ev.append(rr); break
EV = pd.DataFrame(ev); RG = pd.DataFrame(regimes)
pd.to_pickle(dict(EV=EV, RG=RG), OUT); print('events', len(EV), 'regime points', len(RG))
