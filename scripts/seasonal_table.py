"""f81 same-month seasonality table (Heston-Sadka effect, passes in India every era: top 10% minus bottom 10% = +1.3%/month).
For every share: average excess return (vs all shares) in each calendar month over the last 5 years -> rank per month.
Needs the long panel (universe500), so it runs in the weekly ideas.yml; writes data/seasonal/same_month.csv (symbol, month, avg5, rank)."""
import os, sys, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(R, 'study')); import ni_common as nc
A = nc.load()['a']; M = A.resample('ME').last(); mr = M.pct_change(fill_method=None).clip(-0.6, 1.5); mr = mr.sub(mr.mean(axis=1), axis=0)
last = mr.index[-1]; rows = []
for m in range(1, 13):
    x = mr[(mr.index.month == m) & (mr.index < last)].tail(5)   # last 5 finished occurrences of that month
    ok = x.notna().sum() >= 5; avg = x.mean()[ok]; rk = avg.rank(pct=True)
    rows.append(pd.DataFrame({'symbol': avg.index, 'month': m, 'avg5': (avg * 100).round(2).values, 'rank': rk.round(3).values, 'up_years': (x.loc[:, ok] > 0).sum().values}))
os.makedirs(os.path.join(R, 'data', 'seasonal'), exist_ok=True)
T = pd.concat(rows); T.to_csv(os.path.join(R, 'data', 'seasonal', 'same_month.csv'), index=False); print(len(T), T.month.value_counts().iloc[0])
