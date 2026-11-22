# AI-9B587E / WCS12 'young companies (<10 yrs) create more wealth'. Proxy age = years since first trading day in panel
# (only stocks first trading after 2004-01 counted as known age; older = '>=age known'). Each March: next 12m excess vs market.
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load
P = load(); a = P['a']
first = a.apply(lambda s: s.first_valid_index())
ym = a.resample('YE-MAR').last()
rows = []
for i in range(1, len(ym) - 1):
    d = ym.index[i]
    if d.year < 2008: continue
    fut = (ym.iloc[i + 1] / ym.iloc[i] - 1)
    fut = fut[ym.iloc[i].notna()].where(lambda x: x.abs() < 20).dropna()
    mk = fut.mean()
    age = (d - first[fut.index]).dt.days / 365.25
    known = first[fut.index] > pd.Timestamp('2004-01-01')
    for b, m in [('age1-3', known & (age >= 1) & (age < 3)), ('age3-10', known & (age >= 3) & (age < 10)), ('old>=10', (age >= 10) | ~known)]:
        f = fut[m]
        rows.append(dict(year=d.year, bucket=b, n=len(f), ex=(f.mean() - mk) * 100, med_ex=(f.median() - fut.median()) * 100, beat=(f > mk).mean() * 100))
R = pd.DataFrame(rows)
R['era'] = pd.cut(R.year, [2000, 2012, 2020, 2030], labels=['2008-12', '2013-20', '2021+'])
print(R.groupby('bucket').agg(yrs=('year', 'count'), n=('n', 'mean'), ex=('ex', 'mean'), med_ex=('med_ex', 'mean'), yrs_pos=('ex', lambda x: (x > 0).mean() * 100)).round(1))
print(R.pivot_table(index='bucket', columns='era', values='med_ex', observed=True).round(1))
