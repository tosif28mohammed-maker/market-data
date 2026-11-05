"""Idea 7: dividend run-up / ex-date. Ex-dates and yield from Yahoo adj/close ratio jump.
(a) RUNUP: buy close 10 trading days before ex, sell close the day before ex (h=10, pre-dividend, price only).
(b) POST-EX: buy ex-day close, hold 10/20 days.
(c) CAPTURE: buy cum-day close, sell ex-day open: price drop / dividend.
Yield buckets 0.5-2, 2-4, 4%+. Placebo for RUNUP: same stocks, same calendar month, a year earlier+6 months (no ex).
"""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, ni_common as c

P = c.load(); F, mkt = c.fwd(P, hs=(5, 10, 20, 60))
a, cl, o = P['a'], P['c'], P['o']
q = a / cl
y = (1 - q.shift(1) / q) * 100      # dividend yield (%) on ex-date
ex = (y >= 0.5) & (y < 20) & cl.shift(1).notna()
print('ex events', int(ex.sum().sum()), 'per year since 2021', ex.loc['2021':].sum().sum() / 5.8)
rows = []
import sys as _s
for lo_, hi_, nm in ([] if os.environ.get('LATE') else [(0.5, 2, 'y0.5-2'), (2, 4, 'y2-4'), (4, 20, 'y4+'), (0.5, 20, 'all')]):
    e = ex & (y >= lo_) & (y < hi_)
    pre = e.shift(-10, fill_value=False)          # entry 10 days before ex
    plac = e.shift(-10 - 126, fill_value=False)   # same stock, ~6 months earlier window
    rows += c.evaluate(pre, F, f'RUNUP {nm}', hs=(10,), placebo=plac)
    rows += c.evaluate(e, F, f'POSTEX {nm}', hs=(10, 20))
    # capture
    drop = ((cl.shift(1) - o / q) / (cl.shift(1) * y / 100)).where(e)  # o is adj-scaled -> back to price
    dv = drop.stack().dropna(); dv = dv[(dv > -5) & (dv < 5)]
    print(nm, 'events', int(e.sum().sum()), 'open drop / dividend: mean', round(dv.mean(), 2), 'median', round(dv.median(), 2))
T = pd.DataFrame(rows)
if not os.environ.get('LATE'): T.to_csv(f'{c.REPO}/study/results/ni_dividend.csv', index=False)
if len(T): print(T[[k for k in T.columns if k not in ('excess_med',)]].to_string())

# Robustness: later entries (record-date notice under SEBI LODR is >= 7 working days, so t-6/t-4 entry is after announcement)
F2, _ = c.fwd(P, hs=(3, 5))
rows2 = []
for lo_, hi_, nm in [(0.5, 2, 'y0.5-2'), (2, 4, 'y2-4'), (4, 20, 'y4+')]:
    e = ex & (y >= lo_) & (y < hi_)
    rows2 += c.evaluate(e.shift(-6, fill_value=False), F2, f'RUNUP t-6 {nm}', hs=(5,))
    rows2 += c.evaluate(e.shift(-4, fill_value=False), F2, f'RUNUP t-4 {nm}', hs=(3,))
T2 = pd.DataFrame(rows2); T2.to_csv(f'{c.REPO}/study/results/ni_dividend_late.csv', index=False)
print(T2[T2.era.isin(['ALL', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'])][['study', 'era', 'n', 'excess', 'win_vs_mkt', 'raw_net', 'raw_win', 't_dates']].to_string())
