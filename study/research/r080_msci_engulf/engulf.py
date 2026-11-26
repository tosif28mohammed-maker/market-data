import pandas as pd, numpy as np, sys
sys.path.insert(0,'study'); import ni_common as nc
P=nc.load(); o,h,l,c,a,v=[P[k] for k in 'ohlcav']
c=a  # adj close (o,h,l already scaled)
F,mkt=nc.fwd(P,(5,20))
po,pc=o.shift(1),c.shift(1)
eng=(pc<po)&(c>o)&(o<=pc)&(c>=po)&((c-o)>(po-pc))
low60=l.shift(1).rolling(60).min()
sup=(l<=low60*1.02)  # touched/near 60d low (support)
vr=v/v.shift(1).rolling(20).mean()
liqok=(c*v).rolling(20).mean()>2e7
base=eng&sup&liqok
groups={'eng+sup+hiVol(>1.5x)':base&(vr>1.5),'eng+sup+lowVol(<1x)':base&(vr<1),'eng+sup all':base,'eng anywhere':eng&liqok,'sup only(no eng, green)':sup&(c>o)&liqok&~eng}
# stop/target: stop=pattern low, target=2R, 20d, entry close
H=h.values; L=l.values; C=c.values
def sim(ev,R=2,hz=20):
    res=[]
    st=np.minimum(l.values,l.shift(1).values)
    ii,jj=np.nonzero(ev.values)
    for i,j in zip(ii,jj):
        e=C[i,j]; s=st[i,j]
        if not np.isfinite(e) or not np.isfinite(s) or s>=e: continue
        risk=e-s
        if risk/e>0.10: continue
        t=e+R*risk; out=None
        for k in range(i+1,min(i+1+hz,len(C))):
            if not np.isfinite(L[k,j]): continue
            if L[k,j]<=s: out=(-risk/e*100,'stop');break
            if H[k,j]>=t: out=(R*risk/e*100,'tgt');break
        if out is None:
            k=min(i+hz,len(C)-1)
            if np.isfinite(C[k,j]): out=((C[k,j]/e-1)*100,'time')
        if out: res.append((c.index[i],out[0]-nc.COST,out[1]))
    d=pd.DataFrame(res,columns=['d','r','x'])
    return d
for g,ev in groups.items():
    ev=nc.thin(ev.fillna(False),10)
    rows=nc.evaluate(ev,F,g,hs=(5,20))
    for r in rows:
        if r['era'] in('ALL','2003-12','2013-20','2021-26','Nov23-now') and 'excess' in r:
            print(g,r['h'],r['era'],'n',r['n'],'ex',r['excess'],'med',r['excess_med'],'t',r['t_dates'])
    if g.startswith('eng+sup'):
        for R in (1,2):
            d=sim(ev,R)
            w=d[d.r>0].r.mean(); ls=d[d.r<=0].r.mean()
            print('  SIM R',R,'n',len(d),'tgt%',round((d.x=='tgt').mean()*100,1),'stop%',round((d.x=='stop').mean()*100,1),'avg',round(d.r.mean(),2),'avgwin',round(w,2),'avgloss',round(ls,2))
            for a_,b_ in [('2003','2012'),('2013','2020'),('2021','2026'),('2026-05','2026'),('2026-09','2026')]:
                q=d[(d.d>=a_)&(d.d<=b_+'-12-31' if len(b_)==4 else d.d>=a_)]
                print('    ',a_,b_,len(q),round((q.x=='tgt').mean()*100,1),round(q.r.mean(),2))
