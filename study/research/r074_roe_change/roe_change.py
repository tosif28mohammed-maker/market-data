# r074 (i84, Motilal WCS 14/15/17): RoE ka BADLAAV (kam se badhta) vs RoE ka STAR -> agle 12 mahine
# Rule (pehle likha): RoE_t = Net Income(common) / Stockholders Equity (FY end, equity>0).
# Cohort FY t in (2024,2025,2026): formation 1 July t (results out), hold to 30 Jun t+1 (FY26: to latest).
# Groups: IMPROVE = RoE_{t-1}<15% & dRoE>=+5pp & RoE_t>0 ; HISTABLE = RoE_t>=20% & |d|<3pp ; FALL = d<=-5pp
# Outcome: buy-hold return minus equal-weight of all stocks with data (same window); cost 0.25%.
# Chance: shuffle group labels within cohort 2000x. Liquidity D dropped (ni_common). Survivorship: today's list.
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
P = nc.load(); A = P['a']; V = P['v']; C = P['c']
f = pd.read_csv('/home/claude/market-data/data/fund/raw.csv.gz'); f = f[f.freq == 'A']
f['fy'] = f.date.str[:4].astype(int) + (f.date.str[5:7].astype(int) > 6) * 0
piv = f.pivot_table(index=['symbol', 'fy'], columns='item', values='value', aggfunc='last')
ni = piv.get('Net Income Common Stockholders').fillna(piv['Net Income'])
eq = piv['Stockholders Equity']; rev = piv['Total Revenue']
roe = (ni / eq).where(eq > 0) * 100
D = pd.DataFrame({'roe': roe, 'rev': rev}).reset_index()
info = pd.read_csv('/home/claude/market-data/data/fund/info.csv').set_index('symbol')
rows = []
for t in (2024, 2025, 2026):
    cur = D[D.fy == t].set_index('symbol'); prv = D[D.fy == t - 1].set_index('symbol')
    x = cur[['roe', 'rev']].join(prv[['roe', 'rev']], rsuffix='_p', how='inner').dropna(subset=['roe', 'roe_p'])
    s0 = pd.Timestamp(f'{t}-07-01'); s1 = min(pd.Timestamp(f'{t+1}-06-30'), A.index[-1])
    ix = A.index[(A.index >= s0) & (A.index <= s1)]
    if len(ix) < 40: continue
    pa = A.reindex(columns=x.index.intersection(A.columns))
    p0 = pa.loc[ix[0]]; p1 = pa.loc[ix[-1]]
    # 12m prior return + size (traded value) at formation
    pre = pa.loc[:ix[0]].iloc[-250:]
    tv = (C * V).reindex(columns=pa.columns).loc[:ix[0]].iloc[-60:].median()
    r = (p1 / p0 - 1) * 100
    ok = r.notna() & (r.abs() < 1000)
    x = x.loc[ok[ok].index]; r = r[ok]
    x['ret'] = r; x['ex'] = r - r.mean() - nc.COST
    x['d'] = x.roe - x.roe_p; x['revg'] = (x.rev / x.rev_p - 1) * 100
    x['pre12'] = (pre.iloc[-1] / pre.iloc[0] - 1).reindex(x.index) * 100
    x['tv'] = tv.reindex(x.index); x['cohort'] = t; x['days'] = len(ix)
    x['sector'] = info.sector.reindex(x.index)
    rows.append(x)
X = pd.concat(rows); X['symbol'] = X.index
X['g'] = np.select([(X.roe_p < 15) & (X.d >= 5) & (X.roe > 0), (X.roe >= 20) & (X.d.abs() < 3), X.d <= -5], ['IMPROVE', 'HISTABLE', 'FALL'], 'other')
X.to_csv('/home/claude/market-data/study/research/r074_roe_change/panel.csv', index=False)
print('cohorts', X.groupby('cohort').agg(n=('ex', 'size'), days=('days', 'first'), ew=('ret', 'mean')).round(1).to_dict('index'))
def tab(Y, lab):
    o = Y.groupby(['cohort', 'g']).ex.agg(['size', 'mean', 'median', lambda s: (s > 0).mean() * 100]).round(1)
    o.columns = ['n', 'mean', 'median', 'hit%']; print(f'\n== {lab}\n', o.unstack('g').to_string())
tab(X, 'ALL')
tab(X[X.sector != 'Financial Services'], 'ex-financials')
# chance: IMPROVE minus HISTABLE, pooled cohort-avg, labels shuffled within cohort
rng = np.random.default_rng(1)
def stat(Y, g):
    m = [Y[(Y.cohort == c) & (g == 'IMPROVE')].ex.mean() - Y[(Y.cohort == c) & (g == 'HISTABLE')].ex.mean() for c in Y.cohort.unique()]
    return np.nanmean(m)
def stat2(Y, g, a, b):
    m = [Y[(Y.cohort == c) & (g == a)].ex.mean() - Y[(Y.cohort == c) & (g == b)].ex.mean() for c in Y.cohort.unique()]
    return np.nanmean(m)
for a, b in [('IMPROVE', 'HISTABLE'), ('IMPROVE', 'other'), ('FALL', 'other'), ('HISTABLE', 'other')]:
    real = stat2(X, X.g.values, a, b); sims = []
    for i in range(2000):
        g = X.g.values.copy()
        for c in X.cohort.unique():
            m = (X.cohort == c).values; g[m] = rng.permutation(g[m])
        sims.append(stat2(X, g, a, b))
    sims = np.array(sims); print(f'{a}-{b}: {real:+.2f}pp  chance p(two-sided)={np.mean(np.abs(sims) >= abs(real)):.3f}')
# quintiles: level vs change (cohort-wise rank, median excess)
for col in ['roe', 'd']:
    X['q'] = X.groupby('cohort')[col].transform(lambda s: pd.qcut(s.rank(method='first'), 5, labels=False) + 1)
    print(f'\nquintile by {col} (mean / median excess, per cohort)\n', X.groupby(['q', 'cohort']).ex.agg(['mean', 'median']).round(1).unstack('cohort').to_string())
# scenarios inside IMPROVE: winners vs losers circumstances
I = X[X.g == 'IMPROVE'].copy(); I['win'] = I.ex > 0
print('\nIMPROVE winners vs losers (median):\n', I.groupby('win')[['roe_p', 'roe', 'd', 'revg', 'pre12', 'tv']].median().round(1).to_string())
for col, cuts in [('revg', [-1e9, 0, 15, 1e9]), ('pre12', [-1e9, 0, 40, 1e9]), ('roe_p', [-1e9, 0, 8, 15])]:
    I['b'] = pd.cut(I[col], cuts)
    print(col, I.groupby(['b', 'cohort'], observed=True).ex.agg(['size', 'mean']).round(1).unstack('cohort').to_string())
