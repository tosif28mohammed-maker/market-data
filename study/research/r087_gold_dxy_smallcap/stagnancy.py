# r087 AI stagnancy rule: swing trade that fails to expand in 7-8 days -> exit. Same entries, compare exits.
import sys; sys.path.insert(0,'/home/claude/market-data/study')
import numpy as np, pandas as pd, ni_common as nc
P=nc.load(); C=P['a']; H=P['h']; L=P['l']; O=P['o']
syms=C.columns; idx=C.index
hi20=C.rolling(20).max().shift(1); ma50=C.rolling(50).mean()
# entry styles: (1) 20d close breakout above 50DMA, (2) pullback: close>50DMA, 5d ret<-3% (dip in uptrend)
sigs={'breakout20':(C>hi20)&(C>ma50)&(ma50>ma50.shift(20)),
      'dip_uptrend':(C>ma50)&(C/C.shift(5)-1<-0.03)&(ma50>ma50.shift(20))}
COST=0.25
rng=np.random.default_rng(1)
def run(sig,SL=0.07,TG=0.15,MAX=30,day=8,need=0.03):
    S=sig.values; c=C.values; h=H.values; l=L.values; out=[]
    for j in range(len(syms)):
        nxt=-1
        for i in np.where(S[:,j])[0]:
            if i<=nxt or i+MAX+1>=len(idx) or np.isnan(c[i,j]): continue
            e=c[i,j]; resA=None; resB=None; stag=False
            for k in range(i+1,i+MAX+1):
                if np.isnan(c[k,j]): break
                if resA is None:
                    if l[k,j]<=e*(1-SL): resA=(-SL,k-i)
                    elif h[k,j]>=e*(1+TG): resA=(TG,k-i)
                if k-i==day and resA is None:
                    mx=np.nanmax(h[i+1:k+1,j])
                    if mx<e*(1+need): stag=True; resB=(c[k,j]/e-1,day)
                if resA is not None: break
            if resA is None: resA=(c[min(i+MAX,len(idx)-1),j]/e-1,MAX)
            if resB is None: resB=resA
            out.append((idx[i],syms[j],resA[0]*100-COST,resA[1],resB[0]*100-COST,resB[1],stag,resA[0]==TG))
            nxt=i+resA[1]
    return pd.DataFrame(out,columns=['d','s','retA','daysA','retB','daysB','stag','tgtA'])
for name,sig in sigs.items():
  for day,need in [(8,0.03),(7,0.0),(8,0.05)]:
    T=run(sig,day=day,need=need); T['yr']=T.d.dt.year
    print(f'=== {name} exit day{day} if max high < +{need*100:.0f}% | N {len(T)} stagnated {T.stag.mean()*100:.0f}%')
    for era,a,b in nc.ERAS+[('last6m','2026-05-01','2026-12-31'),('last4m','2026-07-01','2026-12-31'),('last2m','2026-09-01','2026-12-31')]:
        t=T[(T.d>=a)&(T.d<=b)]
        if len(t)<10: continue
        st=t[t.stag]
        print(f' {era:9s} N{len(t):6d} A(SL7/TG15/30d) avg {t.retA.mean():+.2f} tgt {t.tgtA.mean()*100:4.1f}% days {t.daysA.mean():4.1f} | B avg {t.retB.mean():+.2f} days {t.daysB.mean():4.1f} | stag N{len(st)} keep {st.retA.mean():+.2f} vs exit {st.retB.mean():+.2f} | per-day A {t.retA.sum()/t.daysA.sum():+.3f} B {t.retB.sum()/t.daysB.sum():+.3f}')
