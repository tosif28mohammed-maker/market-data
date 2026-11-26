# r076 value chain (capital-market chain, 26 Nov: BSE +6%, MCX +8% record, KFin/NSE-linked up):
# Rule (pehle likha): leader day = BSE or MCX close-to-close excess vs EW market >= +4%. Followers = the OTHER members of
# {BSE, MCX, CDSL, CAMS, KFINTECH, ANGELONE, MOTILALOFS, 360ONE, NUVAMA, IIFL}. Buy follower at NEXT day open, outcomes:
# next-day open->close, 5d and 20d excess (from next open). cost 0.25% delivery for 5/20d. Control: same followers on random days.
# Scenario: follower already up >=3% excess on leader day (caught up) vs not; Nifty above/below 200DMA.
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
P = nc.load(); a = P['a']; o = P['o']
ret = a.pct_change(fill_method=None); ret = ret.where(ret.abs() < .4); mkt = ret.mean(axis=1)
ex = ret.sub(mkt, axis=0) * 100
grp = [s for s in ['BSE', 'MCX', 'CDSL', 'CAMS', 'KFINTECH', 'ANGELONE', 'MOTILALOFS', '360ONE', 'NUVAMA', 'IIFL'] if s in a.columns]
print('in panel', grp)
n = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
up200 = (n > n.rolling(200).mean()).reindex(a.index).ffill()
lm = np.log(a); lmk = np.log1p(mkt.fillna(0)).cumsum()
def fwd_ex(sym, t0i, h):  # from next open (t0i+1 open) to close t0i+h
    i1 = t0i + 1; i2 = t0i + h
    if i2 >= len(a.index): return np.nan
    p0 = o[sym].iloc[i1]; p1 = a[sym].iloc[i2]
    m = np.expm1(lmk.iloc[i2] - lmk.iloc[i1 - 1]) * 100  # approx market close->close
    return (p1 / p0 - 1) * 100 - m
rows = []
idx = a.index
for L in ['BSE', 'MCX']:
    if L not in a.columns: continue
    days = ex[L][ex[L] >= 4].index
    for d in days:
        ti = idx.get_loc(d)
        for f in grp:
            if f == L or pd.isna(a[f].iloc[ti]) or ti + 1 >= len(idx): continue
            od = (a[f].iloc[ti + 1] / o[f].iloc[ti + 1] - 1) * 100 - (mkt.iloc[ti + 1] * 100)
            rows.append(dict(date=d, L=L, f=f, f_day0=ex[f].iloc[ti], od=od, x5=fwd_ex(f, ti, 5) - .25, x20=fwd_ex(f, ti, 20) - .25, up200=up200.iloc[ti]))
E = pd.DataFrame(rows).dropna(subset=['od'])
# control: random days, same followers
rng = np.random.default_rng(0); cr = []
for _ in range(4000):
    ti = rng.integers(250, len(idx) - 21); f = grp[rng.integers(len(grp))]
    if pd.isna(a[f].iloc[ti]) or pd.isna(o[f].iloc[ti + 1]): continue
    cr.append(dict(od=(a[f].iloc[ti + 1] / o[f].iloc[ti + 1] - 1) * 100 - mkt.iloc[ti + 1] * 100, x5=fwd_ex(f, ti, 5) - .25, x20=fwd_ex(f, ti, 20) - .25))
Cn = pd.DataFrame(cr)
print('leader days', E.groupby('L').date.nunique().to_dict(), 'follower-events', len(E))
print('EVENT  mean', E[['od', 'x5', 'x20']].mean().round(2).to_dict(), 'win5%', round((E.x5 > 0).mean() * 100, 1))
print('CONTROL mean', Cn[['od', 'x5', 'x20']].mean().round(2).to_dict(), 'win5%', round((Cn.x5 > 0).mean() * 100, 1))
E['caught'] = np.where(E.f_day0 >= 3, 'already up>=3', 'lagged')
print(E.groupby('caught')[['od', 'x5', 'x20']].agg(['size', 'mean']).round(2).to_string())
print(E.groupby('up200')[['od', 'x5', 'x20']].mean().round(2).to_string())
E['yr'] = E.date.dt.year; print(E.groupby('yr')[['x5', 'x20']].agg(['size', 'mean']).round(2).to_string())
# date-clustered t for x5 (lagged followers)
for lab, y in [('all', E), ('lagged', E[E.caught == 'lagged'])]:
    d = y.groupby('date').x5.mean(); d20 = y.groupby('date').x20.mean()
    print(lab, 'dates', len(d), 'x5 t', round(d.mean() / d.std() * np.sqrt(len(d)), 2), 'x20 t', round(d20.mean() / d20.std() * np.sqrt(len(d20)), 2))
E.to_csv('/home/claude/market-data/study/research/r076_capmkt_chain/events.csv', index=False)
print('last 26 Nov leader?', ex.loc['2026-11-26', [g for g in grp]].round(2).to_dict())
