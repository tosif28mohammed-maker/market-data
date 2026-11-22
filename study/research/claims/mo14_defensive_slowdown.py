# MO-14 (Motilal WCS 2008-13): in slowdown/tough markets IT, Pharma, Consumer beat the market.
# Test: month-end regime from Nifty (below 200DMA / 12m return<0). Next 6m & 12m equal-weight sector basket
# return minus equal-weight all-stock market. Sectors from data/fund/info.csv (current, survivorship caveat).
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from ni_common import load, REPO
P = load(); a = P['a']
info = pd.read_csv(f'{REPO}/data/fund/info.csv').set_index('symbol')['sector']
n = pd.read_csv(f'{REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date')['close'].sort_index()
me = a.resample('ME').last().index
am = a.resample('ME').last()
ret1m = am.pct_change(fill_method=None).where(lambda x: x.abs() < 3)
nm = n.resample('ME').last(); dma = n.rolling(200).mean().resample('ME').last()
reg = pd.DataFrame({'below200': nm < dma, 'neg12m': nm.pct_change(12) < 0}).reindex(me)
def fwdret(cols, h):
    r = ret1m[cols].mean(axis=1).fillna(0)
    return np.exp(np.log1p(r).rolling(h).sum().shift(-h)) - 1
mkt = {h: fwdret(list(a.columns), h) for h in (6, 12)}
rows = []
sectors = info.dropna().unique()
for sec in sectors:
    cols = [c for c in a.columns if info.get(c) == sec]
    if len(cols) < 15: continue
    for h in (6, 12):
        ex = (fwdret(cols, h) - mkt[h]) * 100
        for name, mask in [('all', pd.Series(True, index=me)), ('below200', reg.below200 == True),
                           ('neg12m', reg.neg12m == True), ('above200', reg.below200 == False)]:
            for era, s, e in [('2003-12', '2003', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('ALL', '2003', '2026')]:
                x = ex[mask.fillna(False)].loc[s:e].dropna()
                if len(x) < 6: continue
                rows.append(dict(sector=sec, n_stocks=len(cols), h=h, regime=name, era=era, months=len(x),
                                 mean_ex=round(x.mean(), 2), median_ex=round(x.median(), 2), pct_pos=round((x > 0).mean() * 100, 1)))
R = pd.DataFrame(rows)
out = f'{REPO}/study/research/claims/mo14_result.csv'; R.to_csv(out, index=False)
pv = R[(R.era == 'ALL')].pivot_table(index='sector', columns=['h', 'regime'], values='mean_ex')
print(pv.round(1).to_string())
print(R[(R.sector.isin(['Technology', 'Healthcare', 'Consumer Defensive'])) & (R.regime.isin(['below200', 'neg12m'])) & (R.h == 12)].to_string())
print('months below200', int(reg.below200.sum()), 'neg12m', int(reg.neg12m.sum()))
