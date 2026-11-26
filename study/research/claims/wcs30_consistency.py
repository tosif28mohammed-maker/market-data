# WCS30 R12: stocks that beat the equal-weight market in EACH of the last N years -> next 1/3/5y excess. Rule fixed before results.
import os,sys,numpy as np,pandas as pd
sys.path.insert(0,'study'); pass
import ni_common as nc
P=nc.load(); a=P['a']
ye=a.resample('YE').last()                          # year-end adj price
ry=ye.pct_change(fill_method=None).where(lambda x:x.abs()<5)
mk=ry.mean(axis=1); ex=ry.sub(mk,axis=0)
out=[]
for N in (3,5):
    beat=(ex>0).astype(float).where(ex.notna()).rolling(N).sum().eq(N)
    for H in (1,3,5):
        fwd=np.log1p(ry).rolling(H).sum().shift(-H); fm=np.log1p(mk).rolling(H).sum().shift(-H)
        fx=(np.expm1(fwd).sub(np.expm1(fm),axis=0))*100
        for era,(s,e) in {'ALL':('2005','2025'),'2005-12':('2005','2012'),'2013-20':('2013','2020'),'2021-25':('2021','2025')}.items():
            m=(ye.index.year>=int(s))&(ye.index.year<=int(e))
            x=fx[m].where(beat[m]).stack().dropna(); y=fx[m].where(~beat[m]&ry[m].notna()).stack().dropna()
            if len(x)<30: continue
            out.append(dict(N=N,H=H,era=era,n=len(x),excess_mean=round(x.mean(),1),excess_med=round(x.median(),1),pct_beat=round((x>0).mean()*100,1),others_mean=round(y.mean(),1),others_med=round(y.median(),1)))
print(pd.DataFrame(out).to_string(index=False))
