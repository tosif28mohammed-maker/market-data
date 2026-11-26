# r073: (A) Nifty big monthly gain -> next months ; (B) breadth divergence: index near 52w high but most stocks far below
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
n = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
P = nc.load(); a = P['a']
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < .5)
ew = (1 + r1.mean(axis=1).fillna(0)).cumprod()
print('panel', a.index[0].date(), a.index[-1].date(), a.shape[1])
# ---- A: monthly
for name, s in [('NIFTY', n), ('EW-panel', ew)]:
    m = s.resample('ME').last(); mr = m.pct_change() * 100
    res = []
    for h in (1, 3, 6, 12):
        f = (m.shift(-h) / m - 1) * 100
        res.append(f)
    df = pd.concat([mr] + res, axis=1, keys=['m', 'f1', 'f3', 'f6', 'f12']).dropna(subset=['m'])
    print(f'\n== A {name} months {len(df)} ({df.index[0].date()}..)')
    print('all  ', df[['f1', 'f3', 'f6', 'f12']].mean().round(2).to_dict(), 'pos12', round((df.f12 > 0).mean() * 100))
    for th in (6, 8, 10):
        e = df[df.m >= th]
        print(f'm>={th}% N{len(e)}', e[['f1', 'f3', 'f6', 'f12']].mean().round(2).to_dict(), 'pos12', round((e.f12 > 0).mean() * 100) if len(e) else None,
              'dates', [d.strftime('%Y-%m') for d in e.index])
    # exclude crisis rebounds (month inside 2008-09 / 2020)
    e = df[(df.m >= 8) & ~((df.index >= '2008-10-01') & (df.index <= '2009-12-31')) & ~((df.index >= '2020-03-01') & (df.index <= '2020-12-31'))]
    print('m>=8 ex-crisis N', len(e), e[['f1', 'f3', 'f6', 'f12']].mean().round(2).to_dict())
# ---- B: breadth divergence (daily)
hi = a.rolling(250, min_periods=200).max()
far = (a < hi * 0.85).astype(float).where(hi.notna() & a.notna())
cnt = hi.notna().sum(axis=1)
pct_far = far.sum(axis=1) / cnt.replace(0, np.nan) * 100
pct_far = pct_far[cnt >= 150]
for name, s in [('NIFTY', n), ('EW-panel', ew)]:
    s = s.reindex(pct_far.index).ffill().dropna()
    near = s >= s.rolling(250, min_periods=200).max() * 0.97
    pf = pct_far.reindex(s.index)
    fw = {h: (s.shift(-h) / s - 1) * 100 for h in (20, 60, 120, 250)}
    F = pd.DataFrame(fw); F['near'] = near; F['pf'] = pf
    F = F.dropna(subset=[20])
    print(f'\n== B {name} days {len(F)}  index within 3% of 52wH')
    base = F[F.near]
    print('near-high all N', len(base), base[[20, 60, 120, 250]].mean().round(2).to_dict())
    for th in (50, 60, 70):
        e = base[base.pf >= th]; o = base[base.pf < 40]
        # episodes: first day after 60-day gap
        ep = e.index[(e.index.to_series().diff().dt.days.fillna(999) > 60)]
        print(f' >={th}% stocks >15% below high: N{len(e)} ep{len(ep)}', e[[20, 60, 120, 250]].mean().round(2).to_dict(),
              '| pf<40 N', len(o), o[[20, 60, 120, 250]].mean().round(2).to_dict())
        if th == 60:
            print('   episodes', [d.strftime('%Y-%m-%d') for d in ep], 'ep 120d', F.loc[ep, 120].round(1).tolist(), 'ep250', F.loc[ep, 250].round(1).tolist())
            for nm, s0, s1 in nc.ERAS:
                x = e.loc[s0:s1]; y = base.loc[s0:s1]
                print('   era', nm, 'N', len(x), 'e120', round(x[120].mean(), 2), 'base120', round(y[120].mean(), 2))
    print(' today pct_far', round(pct_far.iloc[-1], 1), pct_far.index[-1].date())
