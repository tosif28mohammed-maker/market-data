"""Idea 6: IPO effects (listing date = first trading day in data, only listings from 2012 on).
(a) After listing: buy listing-day close / day-5 close, excess 20/60/250 days.
(b) Lock-in ends (trading-day approx): 30 cal ~21td (anchor 50%), 90 cal ~62td (anchor rest, from 2023),
    6m ~125td (pre-IPO shareholders), 1y ~248td. Windows: t-5 -> t+5 (h=10) and t -> t+10.
    Placebo: same stocks at day 40 / 100 / 180 after listing.
(c) IPO mania: number of listings in last 63 trading days (survivors in our universe) vs Nifty next 63/126 days.
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

P = c.load(); F, mkt = c.fwd(P, hs=(5, 10, 20, 60, 250))
a = P['a']
first = a.apply(lambda s: s.first_valid_index())
new = first[first >= '2012-01-01']
print('listings in panel since 2012:', len(new))
pos = {d: i for i, d in enumerate(a.index)}
def at(off):
    ev = pd.DataFrame(False, index=a.index, columns=a.columns)
    for s, d in new.items():
        i = pos[d] + off
        if 0 <= i < len(a.index):
            ev.iat[i, a.columns.get_loc(s)] = True
    return ev
rows = []
rows += c.evaluate(at(0), F, 'IPO buy listing close', hs=(20, 60, 250))
rows += c.evaluate(at(5), F, 'IPO buy day5 close', hs=(20, 60, 250))
for nm, d in [('lock30', 21), ('lock90', 62), ('lock6m', 125), ('lock1y', 248), ('PLACEBO d40', 40), ('PLACEBO d100', 100), ('PLACEBO d180', 180)]:
    rows += c.evaluate(at(d - 5), F, f'{nm} t-5->t+5', hs=(10,))
    rows += c.evaluate(at(d), F, f'{nm} t->t+10', hs=(10,))
T = pd.DataFrame(rows)
T.to_csv(f'{c.REPO}/study/results/ni_ipo.csv', index=False)
print(T[T.era.isin(['ALL', '2013-20', '2021-26', 'Nov23-now'])][['study', 'h', 'era', 'n', 'excess', 'excess_med', 'win_vs_mkt', 'raw_net', 't_dates']].to_string())

# (c) mania
nf = pd.read_csv(f'{c.REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
cnt = pd.Series(0, index=a.index); vc = new.value_counts()
cnt.loc[vc.index.intersection(cnt.index)] = vc.reindex(vc.index.intersection(cnt.index)).values
roll = cnt.rolling(63).sum()
nf = nf.reindex(a.index).ffill()
df = pd.DataFrame({'n63': roll, 'f63': (nf.shift(-63) / nf - 1) * 100, 'f126': (nf.shift(-126) / nf - 1) * 100}).loc['2013':].dropna()
df['q'] = pd.qcut(df.n63.rank(method='first'), 5, labels=['Q1 kam', 'Q2', 'Q3', 'Q4', 'Q5 bahut'])
print('\nIPO mania (listings last 3 months) -> Nifty next 3m / 6m, 2013+ (overlapping windows):')
print(df.groupby('q', observed=True)[['n63', 'f63', 'f126']].mean().round(2))
for era, s, e in [('2013-20', '2013', '2020'), ('2021-26', '2021', '2026')]:
    d = df.loc[s:e]; d = d.assign(q=pd.qcut(d.n63.rank(method='first'), 3, labels=['kam', 'beech', 'zyada']))
    print(era, d.groupby('q', observed=True)[['n63', 'f63', 'f126']].mean().round(2).to_dict())
