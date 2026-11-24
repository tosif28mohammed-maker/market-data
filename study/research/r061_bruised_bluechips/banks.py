# AI-248E4C: private banks long vs PSU banks (value migration) — yearly EW returns
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study')
from ni_common import load
a = load()['a']
psu = ['SBIN','PNB','BANKBARODA','CANBK','UNIONBANK','BANKINDIA','INDIANB','CENTRALBK','IOB','UCOBANK','MAHABANK','PSB']
pvt = ['HDFCBANK','ICICIBANK','KOTAKBANK','AXISBANK','INDUSINDBK','FEDERALBNK','IDFCFIRSTB','BANDHANBNK','RBLBANK','YESBANK','CUB','KARURVYSYA','SOUTHBANK','DCBBANK','J&KBANK','CSBBANK','TMB','EQUITASBNK','AUBANK','UJJIVANSFB']
psu=[s for s in psu if s in a]; pvt=[s for s in pvt if s in a]; print('psu',len(psu),'pvt',len(pvt))
r = a.pct_change(fill_method=None); r = r.where(r.abs()<0.5)
ep, ev = r[psu].mean(axis=1), r[pvt].mean(axis=1)
y = pd.DataFrame({'psu': (1+ep).groupby(ep.index.year).prod()-1, 'pvt': (1+ev).groupby(ev.index.year).prod()-1})*100
y['pvt-psu'] = y.pvt - y.psu; print(y.round(1).to_string())
print('years pvt>psu', (y['pvt-psu']>0).sum(), 'of', len(y))
for lab, s, e in [('2003-12','2003','2012'),('2013-20','2013','2020'),('2021-26','2021','2026'),('last6m','2026-05-01','2026-12'),('last4m','2026-07-01','2026-12'),('last2m','2026-09-01','2026-12')]:
    cp = (1+ep.loc[s:e]).prod()-1; cv=(1+ev.loc[s:e]).prod()-1
    print(lab, 'psu', round(cp*100,1), 'pvt', round(cv*100,1))
# simple rule: 12m momentum switch (hold group that led last 12m) as control
