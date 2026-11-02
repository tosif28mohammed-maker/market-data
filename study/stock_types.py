"""Stock behaviour groups per period (user, 2 Nov 2026).
Per stock and period: CAGR, annual volatility, max drawdown, R2 of log price vs time (smooth trend), % of 52-week windows positive,
beta and downside capture vs Nifty (weekly), variance ratio VR(20) (<1 = swings back = range-like), range oscillations
(number of full trips bottom-20% -> top-20% of its own 120-day range), and crisis behaviour (2008 and COVID drawdown vs Nifty, days to recover).
Periods: 2005-12, 2013-19 (pre-COVID), 2021-26, and 'ex-crisis' versions. python study/stock_types.py out.pkl dir1 [dir2]"""
import sys, os, glob, numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]; files = []
for D in sys.argv[2:]: files += sorted(glob.glob(os.path.join(D, '*.csv.gz')))
if os.environ.get('CHUNK'): k_, n_ = map(int, os.environ['CHUNK'].split('/')); files = files[k_::n_]
NF = pd.read_csv(os.path.join(ROOT, 'data/NIFTY.csv'), parse_dates=['date']).drop_duplicates('date').set_index('date').close.sort_index()
CRISIS = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]
PER = {'2005-12': ('2005-01-01', '2012-12-31'), '2013-19': ('2013-01-01', '2019-12-31'), '2021-26': ('2021-01-01', '2026-12-31'), 'Nov23-अब': ('2023-11-01', '2026-12-31')}
def crisis_mask(idx):
    m = np.zeros(len(idx), bool)
    for a, b in CRISIS: m |= (idx >= a) & (idx <= b)
    return m
def metrics(c, nifty, excl):
    c = c.dropna()
    if len(c) < 400: return None
    r = np.log(c).diff().dropna()
    if excl: r = r[~crisis_mask(r.index)]
    yrs = len(r) / 248; cagr = np.exp(r.sum() / yrs) - 1; vol = r.std() * np.sqrt(248)
    lp = r.cumsum(); dd = (lp - lp.cummax()).min(); mdd = np.exp(dd) - 1
    t = np.arange(len(lp)); r2 = np.corrcoef(t, lp.values)[0, 1] ** 2 if len(lp) > 10 else np.nan
    slope_sign = np.sign(np.polyfit(t, lp.values, 1)[0])
    w = c.resample('W-FRI').last().dropna(); y52 = (w / w.shift(52) - 1).dropna()
    if excl: y52 = y52[~crisis_mask(y52.index)]
    pos52 = (y52 > 0).mean()
    wr = np.log(w).diff().dropna(); nw = np.log(nifty.resample('W-FRI').last()).diff().reindex(wr.index).dropna(); wr = wr.reindex(nw.index)
    if excl: keep = ~crisis_mask(wr.index); wr, nw = wr[keep], nw[keep]
    beta = np.cov(wr, nw)[0, 1] / nw.var() if len(nw) > 30 else np.nan
    dn = nw < 0; down_cap = wr[dn].mean() / nw[dn].mean() if dn.sum() > 10 else np.nan; up_cap = wr[~dn].mean() / nw[~dn].mean() if (~dn).sum() > 10 else np.nan
    v1 = r.var(); r20 = np.log(c).diff(20).dropna(); vr = r20.var() / (20 * v1) if v1 > 0 else np.nan
    hi = c.rolling(120).max(); lo = c.rolling(120).min(); pos = (c - lo) / (hi - lo); state = 0; trips = 0
    for p in pos.dropna().values:
        if p <= 0.2 and state != -1: state = -1
        elif p >= 0.8 and state == -1: trips += 1; state = 1
    trips_per_year = trips / max(yrs, 0.5)
    rng_ratio = (c.max() / c.min())
    return dict(cagr=cagr, vol=vol, maxdd=mdd, r2=r2 * slope_sign, pos52=pos52, beta=beta, down_cap=down_cap, up_cap=up_cap, vr20=vr, trips_yr=trips_per_year, hi_lo=rng_ratio, days=len(r))
def crisis_dd(c, a, b):
    x = c[(c.index >= a) & (c.index <= b)].dropna()
    if len(x) < 20: return np.nan, np.nan
    peak = x.iloc[:15].max(); dd = x.min() / peak - 1; tmin = x.idxmin()
    after = c[c.index > tmin]; rec = after[after >= peak]
    return dd, (rec.index[0] - tmin).days if len(rec) else np.nan
rows = []
for f in files:
    s = os.path.basename(f)[:-7]
    d = pd.read_csv(f, parse_dates=['date'], usecols=['date', 'close']).dropna().drop_duplicates('date').set_index('date').close.sort_index()
    d = d[d > 0]; jr = d.pct_change().abs(); bad = np.flatnonzero((jr > 0.35).values)
    if len(bad): d = d.iloc[bad[-1]:]
    for pn, (a, b) in PER.items():
        c = d[(d.index >= a) & (d.index <= b)]
        if len(c) < 400 or c.index[0] > pd.Timestamp(a) + pd.Timedelta(days=200): continue
        for excl in (False, True):
            if excl and pn in ('2021-26', 'Nov23-अब'): continue
            m = metrics(c, NF, excl)
            if m: rows.append(dict(stock=s, period=pn + (' (संकट हटाकर)' if excl else ''), **m))
    g8 = crisis_dd(d, '2007-12-01', '2009-12-31'); gc = crisis_dd(d, '2020-01-20', '2021-06-30')
    rows.append(dict(stock=s, period='crisis', dd2008=g8[0], rec2008=g8[1], ddcovid=gc[0], reccovid=gc[1]))
    print(s, flush=True)
pd.DataFrame(rows).to_pickle(OUT); print('done')
