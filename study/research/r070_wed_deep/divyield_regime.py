# ROBOT  (needs universe500 data via U500)
"""r065 follow-up: blue chip (top-100 traded value) div yield>3% split by market regime at formation.
Regime = Nifty close vs 200DMA (data/NIFTY.csv, 2007-09+ so formation from 2008-07). Hold 60/250d.
Per-trade: win rate (raw > cost), avg win vs avg loss after 0.25% cost. Also -10/+20 stop/target within 250d."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, fwd, era_mask, COST
REPO = os.path.join(os.path.dirname(__file__), '..', '..', '..')
P = load(); a, c, v, h_, l_ = P['a'], P['c'], P['v'], P['h'], P['l']
f = a / c; fr = f / f.shift(1)
drop = (1 - 1 / fr).where((fr > 1.0005) & (fr < 1 / 0.85), 0)
ttm = drop.rolling(250, min_periods=200).sum() * 100
rank = (c * v).rolling(250, min_periods=200).median().rank(axis=1, ascending=False)
blue = rank <= 100
N = pd.read_csv(f'{REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
reg = (N > N.rolling(200).mean()).reindex(a.index, method='ffill')
reg_ok = N.rolling(200).mean().reindex(a.index, method='ffill').notna()
F, mkt = fwd(P, hs=(60, 250))
dates = [d for d in a.index.to_series().groupby(a.index.to_period('M')).first().values if d >= pd.Timestamp('2008-07-01')]
# stop/target sim on adj-scaled high/low (h,l already adj-scaled), entry at close
A = a.values; H = h_.values; L = l_.values; idx = {d: i for i, d in enumerate(a.index)}
def st(i, j, sl=-10, tp=20, hold=250):
    e = A[i, j]
    if not np.isfinite(e): return np.nan
    for k in range(i + 1, min(i + hold + 1, len(A))):
        if not np.isfinite(L[k, j]): continue
        lo = (L[k, j] / e - 1) * 100; hi = (H[k, j] / e - 1) * 100
        if lo <= sl: return sl
        if hi >= tp: return tp
    k = min(i + hold, len(A) - 1)
    return (A[k, j] / e - 1) * 100 if np.isfinite(A[k, j]) else np.nan
rows = []; trades = []
for hh in (60, 250):
    raw = F[hh][0]
    for d in dates:
        if not reg_ok.loc[d]: continue
        b = blue.loc[d]; y = ttm.loc[d]
        hi = b & (y > 3); lo = b & (y <= 3) & y.notna()
        if hi.sum() < 3: continue
        rr = raw.loc[d]
        rows.append(dict(h=hh, date=d, bull=bool(reg.loc[d]), hi=rr[hi].mean(), ctrl=rr[lo].mean()))
        if hh == 250:
            for s in hi[hi].index:
                x = rr[s]
                if pd.notna(x):
                    trades.append(dict(date=d, sym=s, bull=bool(reg.loc[d]), ret=x - COST,
                                       st=st(idx[d], a.columns.get_loc(s)) - COST))
R = pd.DataFrame(rows).dropna(); T = pd.DataFrame(trades).dropna()
pd.set_option('display.width', 200)
print('formation months by regime, mean basket returns (raw, before cost):')
out = []
for hh in (60, 250):
    for b in (True, False, None):
        s = R[(R.h == hh) & ((R.bull == b) if b is not None else True)]
        for era, m in era_mask(pd.DatetimeIndex(s.date)).items():
            if era not in ('ALL', '2003-12', '2013-20', '2021-26'): continue
            q = s[m]
            if len(q) < 3: continue
            dd = q.hi - q.ctrl
            out.append(dict(h=hh, regime={True: 'bull', False: 'bear', None: 'all'}[b], era=era, months=len(q),
                            hi=round(q.hi.mean(), 2), ctrl=round(q.ctrl.mean(), 2), diff=round(dd.mean(), 2),
                            pct_better=round((dd > 0).mean() * 100, 1)))
O = pd.DataFrame(out); print(O.to_string(index=False))
print('\nper-trade 250d (hi-yield blue chips), after cost:')
tr = []
for b in (True, False):
    t = T[T.bull == b]
    for col in ('ret', 'st'):
        x = t[col]; w = x[x > 0]; ls = x[x <= 0]
        tr.append(dict(regime='bull' if b else 'bear', kind='hold250' if col == 'ret' else 'SL-10/TP+20', n=len(x),
                       win=round((x > 0).mean() * 100, 1), avg_win=round(w.mean(), 2), avg_loss=round(ls.mean(), 2),
                       exp=round(x.mean(), 2), years=t.date.dt.year.nunique()))
TR = pd.DataFrame(tr); print(TR.to_string(index=False))
t = T[~T.bull]
print('\nbear-regime trades by year: ', t.groupby(t.date.dt.year).ret.agg(['count', 'mean']).round(1).to_dict('index'))
# today
d = a.index[-1]; print('\ntoday', d.date(), 'Nifty>200DMA:', bool(reg.iloc[-1]), '| hi-yield blue chips:', sorted(blue.loc[d][blue.loc[d] & (ttm.loc[d] > 3)].index))
O.to_csv(os.path.join(os.path.dirname(__file__), 'divyield_regime.csv'), index=False)
TR.to_csv(os.path.join(os.path.dirname(__file__), 'divyield_regime_trades.csv'), index=False)
