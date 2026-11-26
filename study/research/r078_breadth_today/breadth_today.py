# r078: BR-01 (r073) आज की breadth, denominator fix (सिर्फ़ उन शेयरों में गिनो जिनका आज भाव है)
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
A = nc.load()['a']
n = pd.read_csv('/home/claude/market-data/data/NIFTY.csv', parse_dates=['date']).set_index('date').close
def pfser(a):
    hi = a.rolling(250, min_periods=200).max(); far = (a < hi * .85).astype(float).where(hi.notna() & a.notna())
    c = far.notna().sum(axis=1); return (far.sum(axis=1) / c * 100)[c >= 150]
for nm, a in [('full-fixed', A), ('today-subset', A.loc[:, A.iloc[-1].notna()])]:
    pf = pfser(a); s = n.reindex(pf.index).ffill()
    near = s >= s.rolling(250, min_periods=200).max() * .97
    F = pd.DataFrame({h: (s.shift(-h) / s - 1) * 100 for h in (20, 60, 120, 250)}); F['near'] = near; F['pf'] = pf
    F = F.dropna(subset=[60]); b = F[F.near]; e = b[b.pf >= 60]; o = b[b.pf < 40]
    ep = e.index[e.index.to_series().diff().dt.days.fillna(999) > 60]
    print(nm, 'N', len(e), 'ep', len(ep), e[[20, 60, 120, 250]].mean().round(2).to_dict(), '| good', len(o), o[[20, 60, 120, 250]].mean().round(2).to_dict())
    print('  today', pf.index[-1].date(), 'pf', round(pf.iloc[-1], 1), 'near', bool(near.iloc[-1]))
