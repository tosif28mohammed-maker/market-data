# r074 step 2: is it RoE-improve, or just revenue growth? control groups + chance
import numpy as np, pandas as pd
X = pd.read_csv('/home/claude/market-data/study/research/r074_roe_change/panel.csv')
X['G15'] = X.revg > 15
X['cell'] = np.where(X.g == 'IMPROVE', 'IMP', 'notIMP') + np.where(X.G15, '_rev>15', '_rev<=15')
o = X.groupby(['cohort', 'cell']).ex.agg(['size', 'mean', 'median', lambda s: (s > 0).mean() * 100]).round(1)
o.columns = ['n', 'mean', 'median', 'hit%']; print(o.unstack('cell').to_string())
# HISTABLE + rev>15 too
for g in ['HISTABLE', 'FALL', 'other']:
    y = X[(X.g == g) & X.G15]; print(g, 'rev>15', y.groupby('cohort').ex.agg(['size', 'mean', 'median']).round(1).to_dict('index'))
rng = np.random.default_rng(2)
def st(lab, Y):
    m = [Y[(Y.cohort == c) & (lab == 'IMP_rev>15')].ex.mean() - Y[(Y.cohort == c) & (lab == 'notIMP_rev>15')].ex.mean() for c in (2024, 2025, 2026)]
    return np.mean(m), m
real, per = st(X.cell.values, X)
# shuffle IMPROVE label only among rev>15 stocks within cohort
sims = []
for i in range(3000):
    lab = X.cell.values.copy()
    for c in (2024, 2025, 2026):
        m = ((X.cohort == c) & X.G15).values; lab[m] = rng.permutation(lab[m])
    sims.append(st(lab, X)[0])
print('IMP&rev>15 minus nonIMP&rev>15:', round(real, 2), [round(v, 1) for v in per], 'p', np.mean(np.abs(sims) >= abs(real)))
# trimmed (winsorize 5/95) to remove multibagger effect
def w(s): return s.clip(s.quantile(.05), s.quantile(.95))
X['exw'] = X.groupby('cohort').ex.transform(w)
print('winsorized mean\n', X.groupby(['cohort', 'cell']).exw.mean().round(1).unstack().to_string())
# rev growth quintile alone (is rev growth itself the factor?)
X['rq'] = X.groupby('cohort').revg.transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False) + 1)
print('rev-growth quintile mean/median\n', X.groupby(['rq', 'cohort']).ex.agg(['mean', 'median']).round(1).unstack().to_string())
# sector breadth of IMP&rev>15
y = X[X.cell == 'IMP_rev>15']; print(y.sector.value_counts().head(8).to_dict())
# SL/TP style check on IMP&rev>15 is not applicable (12m hold); 'hit' = excess>0
# avoid-side: IMP without sales growth vs non-IMP without sales growth
def st2(lab):
    return np.mean([X[(X.cohort == c) & (lab == 'IMP_rev<=15')].ex.mean() - X[(X.cohort == c) & (lab == 'notIMP_rev<=15')].ex.mean() for c in (2024, 2025, 2026)])
real2 = st2(X.cell.values); sims = []
for i in range(3000):
    lab = X.cell.values.copy()
    for c in (2024, 2025, 2026):
        m = ((X.cohort == c) & ~X.G15).values; lab[m] = rng.permutation(lab[m])
    sims.append(st2(lab))
print('AVOID IMP&rev<=15 minus nonIMP&rev<=15:', round(real2, 2), 'p', np.mean(np.abs(np.array(sims)) >= abs(real2)))
y = X[X.cell == 'IMP_rev<=15']; print('median d, roe_p, roe, revg', y[['d', 'roe_p', 'roe', 'revg']].median().round(1).to_dict())
