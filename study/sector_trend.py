"""Which sectors/industries lead now (user 5 Nov 2026: 'aajkal market ka trend kya chal raha hai, 3-10 mahine'). Uses data/daily_all (A/B universe, 2y daily)
and Yahoo sector/industry from data/fund/info.csv. Median returns 1/3/6/12 months, share above 200 DMA, share near 52w high; plus history check:
did last 6-month top industries keep leading in the next 3 months? (rolling, within the 2y data)."""
import numpy as np, pandas as pd
C = pd.read_csv('data/daily_all/close.csv.gz', index_col=0, parse_dates=True).ffill(limit=5)
H = pd.read_csv('data/daily_all/high.csv.gz', index_col=0, parse_dates=True)
I = pd.read_csv('data/fund/info.csv').set_index('symbol')
AV = {l.strip() for l in open('paper/avoid_liquidity_D.txt') if l.strip() and not l.startswith('#')}
C = C[[c for c in C.columns if c not in AV and c in I.index]]
c = C.iloc[-1]
def ret(n): return C.iloc[-1] / C.iloc[-1 - n] - 1
df = pd.DataFrame({'sector': I.sector.reindex(C.columns), 'industry': I.industry.reindex(C.columns), 'r1m': ret(21), 'r3m': ret(63), 'r6m': ret(126), 'r12m': ret(250),
                   'above200': c > C.rolling(200).mean().iloc[-1], 'near52': c / H[C.columns].iloc[-250:].max() >= 0.9})
out = {}
for lev in ('sector', 'industry'):
    g = df.groupby(lev).agg(stocks=('r3m', 'size'), r1m=('r1m', 'median'), r3m=('r3m', 'median'), r6m=('r6m', 'median'), r12m=('r12m', 'median'),
                            above200=('above200', 'mean'), near52w=('near52', 'mean'))
    g = g[g.stocks >= (5 if lev == 'industry' else 10)]
    for k in ['r1m', 'r3m', 'r6m', 'r12m']: g[k] = (g[k] * 100).round(1)
    g[['above200', 'near52w']] = (g[['above200', 'near52w']] * 100).round(0)
    g['score'] = (g.r3m.rank(pct=True) + g.r6m.rank(pct=True) + g.above200.rank(pct=True)).round(2)
    out[lev] = g.sort_values('score', ascending=False)
# persistence check: industry 6m rank -> next 3m median return (monthly steps inside 2y)
ind = df.industry; rows = []
for t in range(126, len(C) - 63, 21):
    p6 = C.iloc[t] / C.iloc[t - 126] - 1; f3 = C.iloc[t + 63] / C.iloc[t] - 1
    g = pd.DataFrame({'ind': ind, 'p6': p6, 'f3': f3}).dropna().groupby('ind').agg(n=('p6', 'size'), p6=('p6', 'median'), f3=('f3', 'median'))
    g = g[g.n >= 5]; g['q'] = pd.qcut(g.p6.rank(method='first'), 5, labels=False)
    rows.append(g.groupby('q').f3.mean())
pers = pd.DataFrame(rows).mean().round(4) * 100
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 200)
print(out['sector'].to_string()); print(out['industry'].head(25).to_string()); print(out['industry'].tail(10).to_string())
print('industry 6m-momentum quintile -> next 3m median return % (0=weakest,4=strongest):', pers.to_dict())
out['sector'].to_csv('study/results/sector_now.csv'); out['industry'].to_csv('study/results/industry_now.csv')
