# r073 B2: same, but stock 'peak' = all-time high since listing in panel (news definition: 75% of Nifty500 >15% below peak)
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
n = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
a = nc.load()['a'].loc['2005-01-01':]
hi = a.cummax(); ok = a.notna() & (a.notna().cumsum() >= 250)
pf = ((a < hi * .85) & ok).sum(axis=1) / ok.sum(axis=1).replace(0, np.nan) * 100
s = n.reindex(pf.index).ffill()
near = s >= s.rolling(250, min_periods=200).max() * .97
F = pd.DataFrame({h: (s.shift(-h) / s - 1) * 100 for h in (20, 60, 120, 250)}); F['pf'] = pf; F = F[near & F[20].notna()]
print('pf quantiles on near-high days', F.pf.quantile([.1, .25, .5, .75, .9]).round(1).to_dict())
for lo, hi_ in [(0, 50), (50, 60), (60, 70), (70, 101)]:
    x = F[(F.pf >= lo) & (F.pf < hi_)]
    print(f'pf {lo}-{hi_}: N{len(x)}', x[[20, 60, 120, 250]].mean().round(2).to_dict())
print('today(2 Nov) pf', round(pf.iloc[-1], 1))
