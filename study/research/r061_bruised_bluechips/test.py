# r061: MO-28 Bruised Blue Chips (Motilal WCS 29) + MO-29 Nov-2024 watchlist forward
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study')
from ni_common import load, COST
P = load(); a = P['a']; c = P['c']; v = P['v']
ret1 = a.pct_change(fill_method=None); ret1 = ret1.where(ret1.abs() < 0.5)
mkt = ret1.mean(axis=1)
lr = np.log1p(ret1.fillna(0)).cumsum(); lm = np.log1p(mkt.fillna(0)).cumsum()
def fwd(h):
    fr = np.expm1(lr.shift(-h) - lr) * 100
    fm = np.expm1(lm.shift(-h) - lm) * 100
    fr = fr.where(a.shift(-h).notna())
    return fr, fr.sub(fm, axis=0)
F = {h: fwd(h) for h in (60, 250, 500)}
tv = (c * v).rolling(250, min_periods=200).median()
rank = tv.rank(axis=1, ascending=False)
hist = a.notna().cumsum()
big = (rank <= 100) & (hist >= 1250)      # blue-chip proxy: top100 liquidity, >=5y history
hi5 = a.rolling(1250, min_periods=1000).max()
dd = a / hi5 - 1
ma200 = a.rolling(200).mean()
def events(cond, rearm=250):
    ev = []
    cond = cond.fillna(False)
    for s in cond.columns:
        idx = np.where(cond[s].values)[0]; last = -10**9
        for i in idx:
            if i - last >= rearm:
                ev.append((cond.index[i], s)); last = i
    return ev
def summ(ev, name):
    rows = []
    for h in (60, 250, 500):
        fr, ex = F[h]
        r = np.array([fr.at[d, s] for d, s in ev]); e = np.array([ex.at[d, s] for d, s in ev])
        m = ~np.isnan(r); r, e = r[m] - COST, e[m] - COST
        dts = [d for (d, s), k in zip(ev, m) if k]
        rows.append(dict(set=name, h=h, n=len(r), mean=r.mean().round(1), median=np.median(r).round(1),
                         win=(r > 0).mean().round(2), ex_mean=e.mean().round(1), ex_med=np.median(e).round(1),
                         ex_win=(e > 0).mean().round(2), n_dates=len(set(pd.Index(dts).to_period('M')))))
    return rows
out = []
for thr in (0.4, 0.5, 0.6):
    ev = events(big & (dd <= -thr))
    out += summ(ev, f'bruised_{int(thr*100)}')
    # healing trigger: after bruise, first close above 200DMA within next 500 days
bru = (big & (dd <= -0.5)).fillna(False)
recent_bru = bru.rolling(500, min_periods=1).max().astype(bool)
cross = (a > ma200) & (a.shift(1) <= ma200.shift(1))
out += summ(events(recent_bru & cross & big.shift(0).fillna(False) | (recent_bru & cross & (hist >= 1250))), 'bruised50_then_200dma_cross')
# control: same universe random (every 60th day per stock)
ctrl = big.copy(); ctrl.iloc[:, :] = False
ctrl.iloc[::60] = big.iloc[::60]
out += summ(events(ctrl, 1), 'control_big_all')
# placebo: big stocks -20..-30% from 5y high
out += summ(events(big & (dd <= -0.2) & (dd > -0.3)), 'placebo_dd20_30')
R = pd.DataFrame(out); print(R.to_string())
# eras for bruised_50 250d
ev = events(big & (dd <= -0.5))
fr, ex = F[250]
E = pd.DataFrame([(d, s, fr.at[d, s] - COST, ex.at[d, s] - COST) for d, s in ev], columns=['date', 'sym', 'r', 'ex']).dropna()
E['era'] = pd.cut(E.date.dt.year, [2000, 2007, 2009, 2012, 2019, 2020, 2026], labels=['03-07', '08-09', '10-12', '13-19', '20', '21-26'])
print(E.groupby('era', observed=True).agg(n=('r', 'size'), mean=('r', 'mean'), med=('r', 'median'), ex_mean=('ex', 'mean'), ex_med=('ex', 'median'), win=('r', lambda x: (x > 0).mean())).round(1))
E.to_csv('/home/claude/market-data/study/research/r061_bruised_bluechips/events_bruised50.csv', index=False)
# without crisis-years entries
nc = E[~E.date.dt.year.isin([2008, 2009, 2020])]
print('ex-crisis 250d: n', len(nc), 'mean', round(nc.r.mean(), 1), 'med', round(nc.r.median(), 1), 'ex_med', round(nc.ex.median(), 1), 'win', round((nc.r > 0).mean(), 2))
# MO-29 watchlist 28-Nov-2024 (dd>=30% from 2020-24 high)
wl = ['ATGL', 'ADANIGREEN', 'ADANIENT', 'GUJGASLTD', 'SBICARD', 'TATAELXSI', 'DMART', 'IRCTC', 'BERGEPAINT', 'ASIANPAINT', 'IOC']
d0 = a.index[a.index.get_indexer([pd.Timestamp('2024-11-28')], method='bfill')[0]]
d1 = a.index[-1]
rows = []
for s in wl:
    if s in a and not np.isnan(a.at[d0, s]):
        rows.append((s, round((a.loc[d1, s] / a.at[d0, s] - 1) * 100, 1)))
    else:
        rows.append((s, None))
W = pd.DataFrame(rows, columns=['sym', 'ret'])
mk = (np.exp(lm.loc[d1] - lm.loc[d0]) - 1) * 100
print('watchlist', d0.date(), '->', d1.date(), W.to_dict('records'), 'mean', round(W.ret.mean(), 1), 'median', W.ret.median(), 'EW market', round(mk, 1))
# compare: other big stocks then
bigs = [s for s in big.columns if big.at[d0, s] and s not in wl and not np.isnan(a.at[d1, s])]
oth = (a.loc[d1, bigs] / a.loc[d0, bigs] - 1) * 100
print('other top100 big: n', len(bigs), 'mean', round(oth.mean(), 1), 'median', round(oth.median(), 1))
R.to_csv('/home/claude/market-data/study/research/r061_bruised_bluechips/summary.csv', index=False)
