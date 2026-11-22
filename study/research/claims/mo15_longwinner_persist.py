# MO-15 (Motilal WCS 2009-16: Eicher/Page/Ajanta in top-10 fastest creators several studies in a row).
# Test: each March-end, rank stocks by trailing 5y price CAGR; top 10 / top decile vs equal-weight market next 12m & 36m.
# Also 3y lookback. Survivorship caveat: panel = stocks alive today (same for all buckets).
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, REPO, COST
P = load(); a = P['a']
ym = a.resample('YE-MAR').last()
rows = []
for lb in (3, 5):
    for i in range(lb, len(ym)):
        past = ym.iloc[i] / ym.iloc[i - lb] - 1
        past = past[(past > -0.99) & (past < 500)].dropna()
        if len(past) < 100: continue
        for h in (1, 3):
            if i + h >= len(ym): continue
            fut = (ym.iloc[i + h] / ym.iloc[i] - 1).reindex(past.index)
            fut = fut.where(fut.abs() < 50)
            mk = fut.mean()
            q = past.rank(pct=True)
            for b, m in [('top10', past.rank(ascending=False) <= 10), ('topdec', q > 0.9), ('mid', (q > 0.4) & (q < 0.6)), ('botdec', q <= 0.1)]:
                f = fut[m].dropna()
                rows.append(dict(lb=lb, h=h, year=ym.index[i].year, bucket=b, n=len(f), ret=(f.mean() - COST / 100) * 100, ex=(f.mean() - mk) * 100,
                                 beat=(f > mk).mean() * 100))
R = pd.DataFrame(rows)
R.to_csv(f'{REPO}/study/research/claims/mo15_result.csv', index=False)
R['era'] = pd.cut(R.year, [2000, 2012, 2020, 2030], labels=['to2012', '2013-20', '2021+'])
print(R.groupby(['lb', 'h', 'bucket']).agg(years=('year', 'count'), ex=('ex', 'mean'), ex_med=('ex', 'median'), beat=('beat', 'mean'), yrs_pos=('ex', lambda x: (x > 0).mean() * 100)).round(1).to_string())
print(R[R.h == 1].pivot_table(index=['lb', 'bucket'], columns='era', values='ex', observed=True).round(1).to_string())
print(R[(R.lb == 5) & (R.h == 1) & (R.bucket == 'top10')][['year', 'n', 'ex']].round(1).to_string())
