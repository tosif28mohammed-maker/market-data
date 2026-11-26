# ROBOT  (needs universe500 data via U500)
"""r070 आगे (AI-48006Ec): bear-regime महीने आपस में जुड़े (overlap). हर bear दौर (Nifty<200DMA लगातार महीने, बीच में
<=1 bull महीना चलेगा) को एक बार गिनो: दौर के पहले महीने में खरीद (blue chip div yield>3% vs बाकी blue chips), 250d।
साथ में: दौर के सब महीनों का औसत (एक दौर = एक वोट)।"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, COST
REPO = os.path.join(os.path.dirname(__file__), '..', '..', '..')
P = load(); a, c, v = P['a'], P['c'], P['v']
f = a / c; fr = f / f.shift(1)
drop = (1 - 1 / fr).where((fr > 1.0005) & (fr < 1 / 0.85), 0)
ttm = drop.rolling(250, min_periods=200).sum() * 100
rank = (c * v).rolling(250, min_periods=200).median().rank(axis=1, ascending=False)
blue = rank <= 100
N = pd.read_csv(f'{REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
reg = (N > N.rolling(200).mean()).reindex(a.index, method='ffill')
F, mkt = fwd(P, hs=(250,)); raw = F[250][0]
dates = [d for d in a.index.to_series().groupby(a.index.to_period('M')).first().values if d >= pd.Timestamp('2008-07-01')]
rows = []
for d in dates:
    b = blue.loc[d]; y = ttm.loc[d]; hi = b & (y > 3); lo = b & (y <= 3) & y.notna()
    rows.append(dict(date=d, bear=not bool(reg.loc[d]), n=int(hi.sum()), hi=raw.loc[d][hi].mean() if hi.sum() >= 3 else np.nan,
                     ctrl=raw.loc[d][lo].mean(), nifty=np.nan))
R = pd.DataFrame(rows)
ep = []; cur = None; gap = 0
for i, r in R.iterrows():
    if r.bear:
        if cur is None: cur = [i]
        else: cur.append(i)
        gap = 0
    elif cur is not None:
        gap += 1
        if gap > 1: ep.append(cur); cur = None; gap = 0
if cur: ep.append(cur)
o = []
for e in ep:
    q = R.loc[e]; first = q.iloc[0]
    o.append(dict(start=first.date.date(), months=len(q), n_hi=first.n, first_diff=round(first.hi - first.ctrl, 1),
                  first_hi_net=round(first.hi - COST, 1), avg_diff=round((q.hi - q.ctrl).mean(), 1)))
O = pd.DataFrame(o); pd.set_option('display.width', 200); print(O.to_string(index=False))
done = O.dropna(subset=['first_diff'])
print('\nepisodes', len(O), 'with 250d result', len(done), '| first-month diff mean', round(done.first_diff.mean(), 2),
      'median', done.first_diff.median(), '>0:', int((done.first_diff > 0).sum()), '| episode-avg diff mean', round(done.avg_diff.mean(), 2),
      '>0:', int((done.avg_diff > 0).sum()))
O.to_csv(os.path.join(os.path.dirname(__file__), 'divyield_episodes.csv'), index=False)
