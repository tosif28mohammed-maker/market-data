# ROBOT: control (other blue chips, yield<=3%) SL-10/TP+20 in bear regime, for comparison with divyield_regime.py
import sys, os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divyield_regime.py')).read().split("rows = []; trades = []")[0])
import numpy as np
out = []
for d in dates:
    if not reg_ok.loc[d] or reg.loc[d]: continue
    b = blue.loc[d]; y = ttm.loc[d]; lo = b & (y <= 3) & y.notna()
    if (b & (y > 3)).sum() < 3: continue
    for s in lo[lo].index:
        out.append(st(idx[d], a.columns.get_loc(s)) - COST)
x = pd.Series(out).dropna()
print('bear ctrl SL-10/TP+20: n', len(x), 'win', round((x > 0).mean() * 100, 1), 'avg_win', round(x[x > 0].mean(), 2), 'avg_loss', round(x[x <= 0].mean(), 2), 'exp', round(x.mean(), 2))
