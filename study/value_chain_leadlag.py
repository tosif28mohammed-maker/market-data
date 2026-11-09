"""Value chain lead-lag (user 9 Nov 2026: 'Mahindra ki maang badhe to uske supplier bhi badhenge').
Monthly: anchor basket return (equal weight) in month t -> supplier basket excess return vs all stocks in t+1 (and t+1..t+3).
Strong-anchor months = anchor basket in its own top third (expanding, no look-ahead). Placebo: reverse (supplier leads anchor).
Map: data/chain/value_chain.csv (curated, well-known relationships). Panel 2003-26 adjusted close."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = nc.load()['a']; M = A.resample('ME').last(); r = (M.pct_change() * 100).where(lambda x: x.abs() <= 60)
mkt = r.median(axis=1)
VC = pd.read_csv(os.path.join(R, 'data', 'chain', 'value_chain.csv'))
for ch, g in VC.groupby('chain'):
    an = [s for s in g[g.role == 'anchor'].symbol if s in r]; su = [s for s in g[g.role == 'supplier'].symbol if s in r]
    a = r[an].median(axis=1); s = r[su].median(axis=1) - mkt; a_ex = a - mkt
    df = pd.DataFrame({'a': a_ex, 's': s, 's1': s.shift(-1), 's3': s.shift(-1).rolling(3).sum().shift(-2), 'a1': a_ex.shift(-1)}).dropna()
    df = df[(r[an].notna().sum(axis=1) >= 2) & (r[su].notna().sum(axis=1) >= 3)].dropna()
    thr = df.a.expanding(24).quantile(2 / 3).shift(1); lo = df.a.expanding(24).quantile(1 / 3).shift(1)
    strong, weak = df[df.a >= thr], df[df.a <= lo]
    print(f'\n== {ch}: anchors {len(an)}, suppliers {len(su)}, months {len(df)} ({df.index[0]:%Y}-{df.index[-1]:%Y})')
    print(f'  same month corr anchor/supplier: {df.a.corr(df.s):+.2f}')
    print(f'  anchor(t) -> supplier(t+1) corr {df.a.corr(df.s1):+.3f} | placebo supplier(t) -> anchor(t+1) {df.s.corr(df.a1):+.3f}')
    for nm, x in (('strong anchor month', strong), ('weak anchor month', weak)):
        t = x.s1.mean() / x.s1.std() * np.sqrt(len(x)) if len(x) > 2 else np.nan
        print(f'  {nm:20s} n {len(x):3d}: supplier next month vs market {x.s1.mean():+.2f}% (t {t:.1f}, up {(x.s1 > 0).mean() * 100:.0f}%), next 3 months {x.s3.mean():+.2f}%')
    for per, (a_, b_) in (('2003-12', ('2003', '2012')), ('2013-20', ('2013', '2020')), ('2021-26', ('2021', '2026'))):
        x = strong.loc[a_:b_]
        if len(x) > 3: print(f'    {per}: strong-anchor -> supplier next month {x.s1.mean():+.2f}% (n {len(x)})')
