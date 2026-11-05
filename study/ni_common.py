"""New-ideas study (Nov 2026) common loader + event evaluator.
Panel: u1000 + u2000 daily files (universe500 branch), liquidity D dropped.
Returns use adj close (dividends included); OHLC scaled by adj/close.
Event evaluation: buy at event-day close (proxy for 2:15-3:25 buy), excess vs
equal-weight market of all stocks same dates; eras; crisis removed; costs 0.25%.
"""
import os, glob, gzip, numpy as np, pandas as pd
U = os.environ.get('U500', '/home/claude/u500')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get('NI_CACHE', '/tmp/ni_panel.pkl')
COST = 0.25  # % round trip (delivery STT 0.1+0.1 + charges)
ERAS = [('2003-12', '2003-01-01', '2012-12-31'), ('2013-20', '2013-01-01', '2020-12-31'),
        ('2021-26', '2021-01-01', '2026-12-31'), ('Nov23-now', '2023-11-01', '2026-12-31')]
CRISIS = [('2008-01-01', '2009-06-30'), ('2020-02-15', '2020-06-30')]


def load():
    if os.path.exists(CACHE):
        return pd.read_pickle(CACHE)
    liq = pd.read_csv(f'{REPO}/study/results/liq_all.csv')
    bad = set(liq.loc[liq.liquidity.astype(str).str.startswith('D'), 'symbol'])
    try:
        bad |= set(open(f'{REPO}/paper/avoid_liquidity_D.txt').read().split())
    except Exception:
        pass
    good = set(liq.symbol) - bad
    fr = {k: {} for k in ['o', 'h', 'l', 'c', 'a', 'v']}
    for f in glob.glob(f'{U}/u1000/daily/*.csv.gz') + glob.glob(f'{U}/u2000/daily/*.csv.gz'):
        s = os.path.basename(f)[:-7]
        if s not in good or s in fr['c']:
            continue
        d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date')
        d = d[d.close > 0]
        if len(d) < 250:
            continue
        r = d.adj / d.close
        fr['o'][s] = d.open * r; fr['h'][s] = d.high * r; fr['l'][s] = d.low * r
        fr['c'][s] = d.close; fr['a'][s] = d.adj; fr['v'][s] = d.volume
    P = {k: pd.DataFrame(v).sort_index() for k, v in fr.items()}
    P = {k: v.loc['2002-07-01':] for k, v in P.items()}
    pd.to_pickle(P, CACHE)
    return P


def fwd(P, hs=(5, 20, 60)):
    a = P['a']
    ret1 = a.pct_change(fill_method=None)
    ret1 = ret1.where(ret1.abs() < 0.5)  # glitch guard
    mkt = ret1.mean(axis=1)
    out = {}
    lr = np.log1p(ret1.fillna(0)); lm = np.log1p(mkt.fillna(0))
    cl, cm = lr.cumsum(), lm.cumsum()
    for h in hs:
        fr = np.expm1(cl.shift(-h) - cl) * 100
        fm = np.expm1(cm.shift(-h) - cm) * 100
        fr = fr.where(a.shift(-h).notna())
        out[h] = (fr, fr.sub(fm, axis=0))
    return out, mkt


def era_mask(idx):
    m = {'ALL': np.ones(len(idx), bool)}
    for n, s, e in ERAS:
        m[n] = (idx >= s) & (idx <= e)
    nc = np.ones(len(idx), bool)
    for s, e in CRISIS:
        nc &= ~((idx >= s) & (idx <= e))
    m['ex-crisis'] = nc
    return m


def evaluate(ev, F, name, hs=(5, 20, 60), placebo=None, rng=0):
    """ev: bool DataFrame (dates x stocks). Returns table rows per era x horizon.
    Basket method: average excess per event date first (dates are units), then t-stat over dates.
    placebo: bool DataFrame of comparable non-event days (same filter) for chance comparison."""
    rows = []
    idx = ev.index
    em = era_mask(idx)
    for h in hs:
        raw, ex = F[h]
        e = ex.where(ev)
        rr = raw.where(ev)
        for era, m in em.items():
            sub = e[m]; subr = rr[m]
            n = int(sub.notna().sum().sum())
            if n < 20:
                rows.append(dict(study=name, h=h, era=era, n=n)); continue
            bydate = sub.mean(axis=1).dropna()
            t = bydate.mean() / (bydate.std(ddof=1) / np.sqrt(len(bydate))) if len(bydate) > 2 else np.nan
            vals = sub.stack().dropna()
            row = dict(study=name, h=h, era=era, n=n, dates=len(bydate),
                       excess=round(vals.mean(), 2), excess_med=round(vals.median(), 2),
                       win_vs_mkt=round((vals > 0).mean() * 100, 1),
                       raw=round(subr.stack().dropna().mean(), 2), raw_net=round(subr.stack().dropna().mean() - COST, 2),
                       raw_win=round((subr.stack().dropna() > COST).mean() * 100, 1), t_dates=round(t, 2))
            if placebo is not None:
                pv = ex.where(placebo)[m].stack().dropna()
                row['placebo_excess'] = round(pv.mean(), 2) if len(pv) else np.nan
                row['vs_placebo'] = round(row['excess'] - row['placebo_excess'], 2)
            rows.append(row)
    return rows


def thin(ev, gap=20):
    """keep at most one event per stock per `gap` trading days (non-overlap)."""
    arr = ev.values.copy()
    for j in range(arr.shape[1]):
        last = -10**9
        for i in np.flatnonzero(arr[:, j]):
            if i - last < gap:
                arr[i, j] = False
            else:
                last = i
    return pd.DataFrame(arr, index=ev.index, columns=ev.columns)


def mfe_mae(P, ev, h=20):
    """OHLC view: average best high and worst low within h days after event close (in %)."""
    a = P['a']; hi = P['h'].rolling(h).max().shift(-h); lo = P['l'].rolling(h).min().shift(-h)
    up = (hi / a - 1).where(ev).stack().dropna() * 100; dn = (lo / a - 1).where(ev).stack().dropna() * 100
    return round(up.mean(), 2), round(dn.mean(), 2), round((dn < -10).mean() * 100, 1)
