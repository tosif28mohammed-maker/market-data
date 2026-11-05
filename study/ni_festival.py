"""Idea 8: festivals / budget / election results.
Markets: equal-weight all-stock basket (2002+) and Nifty (2007-09+). Event day = first trading day on/after date.
Compare each window with ALL same-length windows (chance): mean, % up, and how many years the
event window beat that year's average window. Few events per era -> weak power; said honestly.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

DIWALI = ['2003-10-25', '2004-11-12', '2005-11-01', '2006-10-21', '2007-11-09', '2008-10-28', '2009-10-17', '2010-11-05',
          '2011-10-26', '2012-11-13', '2013-11-03', '2014-10-23', '2015-11-11', '2016-10-30', '2017-10-19', '2018-11-07',
          '2019-10-27', '2020-11-14', '2021-11-04', '2022-10-24', '2023-11-12', '2024-11-01', '2025-10-21']
NAVRATRI = ['2003-09-26', '2004-10-14', '2005-10-04', '2006-09-23', '2007-10-12', '2008-09-30', '2009-09-19', '2010-10-08',
            '2011-09-28', '2012-10-16', '2013-10-05', '2014-09-25', '2015-10-13', '2016-10-01', '2017-09-21', '2018-10-10',
            '2019-09-29', '2020-10-17', '2021-10-07', '2022-09-26', '2023-10-15', '2024-10-03', '2025-09-22']
BUDGET = ['2003-02-28', '2004-07-08', '2005-02-28', '2006-02-28', '2007-02-28', '2008-02-29', '2009-07-06', '2010-02-26',
          '2011-02-28', '2012-03-16', '2013-02-28', '2014-07-10', '2015-02-28', '2016-02-29', '2017-02-01', '2018-02-01',
          '2019-07-05', '2020-02-01', '2021-02-01', '2022-02-01', '2023-02-01', '2024-07-23', '2025-02-01', '2026-02-01']
ELECTION = ['2004-05-13', '2009-05-18', '2014-05-16', '2019-05-23', '2024-06-04']

P = c.load(); _, mkt = c.fwd(P, hs=(5,))
eq = (1 + mkt.fillna(0)).cumprod()
nf = pd.read_csv(f'{c.REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
idx = eq.index


def win(series, dates, a, b):
    """return % from close of (event+a) to close of (event+b), trading-day offsets."""
    s = series.dropna(); ix = s.index; out = {}
    for d in dates:
        i = ix.searchsorted(pd.Timestamp(d))
        if i + a < 0 or i + b >= len(ix) or i >= len(ix):
            continue
        out[ix[i]] = (s.iloc[i + b] / s.iloc[i + a] - 1) * 100
    return pd.Series(out)


def base(series, L):
    s = series.dropna(); r = (s.shift(-L) / s - 1) * 100
    return r.dropna()


def report(name, dates, a, b, series=eq, lab='EQ'):
    w = win(series, dates, a, b); L = b - a
    bs = base(series, L)
    yr_beat = np.mean([w[d] > bs[str(d.year)].mean() for d in w.index]) * 100
    ex = w.drop([d for d in w.index if any(pd.Timestamp(s) <= d <= pd.Timestamp(e) for s, e in c.CRISIS)])
    eras = {}
    for n, s, e in c.ERAS[:3]:
        ww = w[s:e]; eras[n] = f'{ww.mean():+.2f} ({(ww > 0).mean()*100:.0f}% up, n{len(ww)})'
    # t-ish: bootstrap chance of random windows giving this mean
    rng = np.random.default_rng(1)
    sims = np.array([rng.choice(bs.values, len(w)).mean() for _ in range(4000)])
    p = (sims >= w.mean()).mean() if w.mean() >= bs.mean() else (sims <= w.mean()).mean()
    return dict(event=name, mkt=lab, window=f'{a}..{b}', n=len(w), mean=round(w.mean(), 2), up_pct=round((w > 0).mean() * 100),
                normal_mean=round(bs.mean(), 2), normal_up=round((bs > 0).mean() * 100), beat_year_avg=round(yr_beat),
                ex_crisis=round(ex.mean(), 2), p_chance=round(p, 3), **eras)


rows = []
for lab, ser in [('EQ', eq), ('NIFTY', nf)]:
    nav_len = []
    for nv, dw in zip(NAVRATRI, DIWALI):
        i0, i1 = idx.searchsorted(pd.Timestamp(nv)), idx.searchsorted(pd.Timestamp(dw)); nav_len.append(i1 - i0)
    L = int(np.median(nav_len))
    rows.append(report('Navratri start -> Diwali', NAVRATRI, 0, L, ser, lab))
    rows.append(report('Navratri 5 din pehle -> start', NAVRATRI, -5, 0, ser, lab))
    rows.append(report('Diwali se 5 din pehle -> Diwali', DIWALI, -5, 0, ser, lab))
    rows.append(report('Diwali/Muhurat din (-1..0)', DIWALI, -1, 0, ser, lab))
    rows.append(report('Diwali -> +5', DIWALI, 0, 5, ser, lab))
    rows.append(report('Diwali -> +20', DIWALI, 0, 20, ser, lab))
    rows.append(report('Diwali -> +60', DIWALI, 0, 60, ser, lab))
    rows.append(report('Budget se 5 din pehle', BUDGET, -6, -1, ser, lab))
    rows.append(report('Budget din (-1..0)', BUDGET, -1, 0, ser, lab))
    rows.append(report('Budget -> +20', BUDGET, 0, 20, ser, lab))
    rows.append(report('Chunav natije 20 din pehle', ELECTION, -21, -1, ser, lab))
    rows.append(report('Chunav natije din', ELECTION, -1, 0, ser, lab))
    rows.append(report('Chunav natije -> +20', ELECTION, 0, 20, ser, lab))
T = pd.DataFrame(rows)
T.to_csv(f'{c.REPO}/study/results/ni_festival.csv', index=False)
pd.set_option('display.width', 250)
print(T.to_string())
# Diwali year by year (EQ) for the record
w = win(eq, DIWALI, -5, 0); w2 = win(eq, DIWALI, 0, 20)
print(pd.DataFrame({'pre5': w.round(2), 'post20': w2.round(2)}).to_string())
