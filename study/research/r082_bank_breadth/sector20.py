# AI-FD88E6 हिस्सा: sector (EW, info.csv) 21d >= +20% => "overextended, avoid" ? अगले 21/42/63/126d sector - market
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
I=pd.read_csv('/home/claude/market-data/data/fund/info.csv').set_index('symbol')
a=load()['a']; r1=a.pct_change(fill_method=None); r1=r1.where(r1.abs()<0.5); mkt=r1.mean(axis=1)
sec=I.sector.reindex(a.columns); S={}
for s in sec.dropna().unique():
    c=sec[sec==s].index; n=r1[c].notna().sum(axis=1); S[s]=r1[c].mean(axis=1).where(n>=8)
S=pd.DataFrame(S); lS=np.log1p(S.fillna(0)).cumsum(); lM=np.log1p(mkt.fillna(0)).cumsum(); ex=lS.sub(lM,axis=0)
r21=np.expm1(lS-lS.shift(21))*100; rel21=(ex-ex.shift(21))*100
for thr_nm, cond in [('abs21>=20', r21>=20), ('abs21 10-20', (r21>=10)&(r21<20)), ('rel21>=10 vs mkt', rel21>=10)]:
    rows=[]
    for s in S.columns:
        last=None
        for d in cond.index[cond[s].fillna(False)]:
            if last is not None and (d-last).days<120: continue
            last=d; i=ex.index.get_loc(d)
            r={'sec':s,'d':d}
            for h in (21,42,63,126):
                r[h]=(ex[s].iloc[i+h]-ex[s].iloc[i])*100 if i+h<len(ex) else np.nan
            rows.append(r)
    R=pd.DataFrame(rows).dropna(subset=[63])
    print(thr_nm,'N',len(R),'mean',R[[21,42,63,126]].mean().round(2).to_dict(),'median63',round(R[63].median(),2),'%+63',round((R[63]>0).mean()*100))
    for era,(a1,b1) in {'-2013':(2000,2013),'2014-19':(2014,2019),'2020-26':(2020,2026)}.items():
        x=R[(R.d.dt.year>=a1)&(R.d.dt.year<=b1)]; print('   ',era,len(x),x[[21,63]].mean().round(2).to_dict())
    if thr_nm=='abs21>=20': print('  last', R.tail(6)[['sec','d',21,63]].to_string(index=False))
print('today abs21 >=15:', r21.iloc[-1][r21.iloc[-1]>=15].round(1).to_dict(), r21.index[-1].date())
