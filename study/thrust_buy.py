"""Buying strength in a strong up-move (user 5 Nov 2026: 'market daba ke upar ja raha hai, sirf dip ka intezaar nahi').
Signal day = Nifty up >= X% in 10 sessions (thrust; first day in 20). Questions:
 (1) Nifty forward 20/60 days after thrust vs all days (by era, crisis windows shown separately).
 (2) Which stocks to buy on thrust days: A/B liquid stocks ranked by 3-month return (relative strength) and position vs 52w high;
     forward 20/60-day return of top-decile RS / near-52w-high / laggards vs equal-weight universe. Cost 0.35%.
python study/thrust_buy.py panel_close.pkl"""
import sys, numpy as np, pandas as pd
P = pd.read_pickle(sys.argv[1]); P = P[P.index >= '2009-01-01']
cov = P.notna().sum(1); P = P[P.index <= cov[cov >= 0.7 * cov.max()].index.max()].ffill(limit=5)
nf = pd.read_csv('data/NIFTY.csv', parse_dates=['date']).drop_duplicates('date').set_index('date').close.reindex(P.index).ffill()
f20n = nf.shift(-20) / nf - 1; f60n = nf.shift(-60) / nf - 1
r10 = nf / nf.shift(10) - 1
PER = {'2009-12': ('2009-07-01', '2012-12-31'), '2013-20': ('2013-01-01', '2020-12-31'), '2021-26': ('2021-01-01', '2026-12-31'), 'Nov23-': ('2023-11-01', '2026-12-31')}
rows = []
for X in (0.05, 0.07):
    sig = (r10 >= X); first = sig & ~sig.rolling(20).max().shift(1).fillna(0).astype(bool)
    days = first[first].index
    for p, (a, b) in PER.items():
        m = (nf.index >= a) & (nf.index <= b); d = [t for t in days if a <= str(t.date()) <= b]
        rows.append(dict(test=f'Nifty 10 दिन में +{int(X*100)}%', period=p, signals=len(d), nifty_20d=round(f20n.reindex(d).mean() * 100, 2), win20=round((f20n.reindex(d) > 0).mean(), 2),
                         base_20d=round(f20n[m].mean() * 100, 2), nifty_60d=round(f60n.reindex(d).mean() * 100, 2), win60=round((f60n.reindex(d) > 0).mean(), 2), base_60d=round(f60n[m].mean() * 100, 2)))
T1 = pd.DataFrame(rows)
# stock selection on thrust days (X=5%)
sig = (r10 >= 0.05); first = sig & ~sig.rolling(20).max().shift(1).fillna(0).astype(bool); days = first[first].index
r63 = P / P.shift(63) - 1; hi52 = P.rolling(250).max(); near = P / hi52; ma200 = P.rolling(200).mean()
F20 = P.shift(-20) / P - 1 - 0.0035; F60 = P.shift(-60) / P - 1 - 0.0035
out = []
for t in days:
    ok = P.loc[t].notna() & F20.loc[t].notna() & r63.loc[t].notna() & hi52.loc[t].notna()
    if ok.sum() < 200: continue
    rs = r63.loc[t][ok]; q = rs.rank(pct=True); nh = near.loc[t][ok]; up = (P.loc[t] > ma200.loc[t])[ok]
    grp = {'सब शेयर (बराबर)': ok[ok].index, 'RS top 10% (3 महीने सबसे मज़बूत)': q[q >= 0.9].index, 'RS top 10% + 52w high के 5% अंदर': q[(q >= 0.9) & (nh >= 0.95)].index,
           '52w high के 3% अंदर + 200 के ऊपर': nh[(nh >= 0.97) & up].index, 'RS bottom 10% (सबसे पिछड़े)': q[q <= 0.1].index,
           'पिछड़े पर 200 के ऊपर (catch-up)': q[(q <= 0.3) & up].index}
    for g, ix in grp.items():
        if len(ix) == 0: continue
        out.append(dict(date=t, group=g, n=len(ix), f20=F20.loc[t, ix].mean(), w20=(F20.loc[t, ix] > 0).mean(), f60=F60.loc[t, ix].mean()))
O = pd.DataFrame(out); rows = []
for p, (a, b) in PER.items():
    x = O[(O.date >= a) & (O.date <= b)]
    for g, y in x.groupby('group'):
        rows.append(dict(period=p, group=g, signals=y.date.nunique(), avg_stocks=round(y.n.mean()), ret20=round(y.f20.mean() * 100, 2), win20=round(y.w20.mean(), 2), ret60=round(y.f60.mean() * 100, 2)))
T2 = pd.DataFrame(rows)
pd.set_option('display.width', 250); print(T1.to_string(index=False)); print(T2.to_string(index=False))
T1.to_csv('study/results/thrust_nifty.csv', index=False); T2.to_csv('study/results/thrust_stocks.csv', index=False)
print('thrust dates since 2023:', [str(t.date()) for t in days if t.year >= 2023])
