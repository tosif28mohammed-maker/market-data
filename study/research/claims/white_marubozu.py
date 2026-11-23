# ROBOT
"""ET-02: White Marubozu (daily) bullish? Event: (C-O)/(H-L)>=0.9, C/O-1>=3%, range>=1.5x 20d avg range.
Placebo: up-days with C/O-1>=3% and range>=1.5x avg but body/range<0.6 (wicks). Buy at close; excess vs EW mkt."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, evaluate, thin, REPO
P = load(); o, h, l, c = P['o'], P['h'], P['l'], P['a']
rng = (h - l); body = (c - o)
avg = rng.rolling(20).mean().shift(1)
big = (c / o - 1 >= 0.03) & (rng >= 1.5 * avg) & (P['v'] > 0)
ratio = body / rng.replace(0, np.nan)
ev = big & (ratio >= 0.9); pl = big & (ratio < 0.6) & (ratio > 0)
ev = thin(ev, 10); pl = thin(pl, 10)
F, _ = fwd(P)
R = pd.DataFrame(evaluate(ev, F, 'marubozu', placebo=pl) + evaluate(pl, F, 'wick_placebo'))
pd.set_option('display.width', 250)
print(R.to_string())
od = f'{REPO}/study/research/r057_sector_avoid_porter'; os.makedirs(od, exist_ok=True)
R.to_csv(f'{od}/marubozu.csv', index=False)
# recent 2/4/6 months (20d excess)
raw, ex = F[20]
last = c.index[-1]
for m in (2, 4, 6, 8):
    st = last - pd.DateOffset(months=m)
    sub = ex.where(ev).loc[st:]; sp = ex.where(pl).loc[st:]
    print(f"since {m}m (20d ex): marubozu {sub.stack().mean():+.2f} n{int(sub.notna().sum().sum())}  placebo {sp.stack().mean():+.2f}")
