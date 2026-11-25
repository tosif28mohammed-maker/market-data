# r067b: stock closes down N+ consecutive days (Jupiter Wagons '12% after 8-day fall' news) -> bounce?
import sys; sys.path.insert(0,'/home/claude/market-data/study')
import numpy as np, pandas as pd
from ni_common import load, fwd, ERAS, CRISIS, COST
P=load(); a=P['a']; c=P['c']
r=a.pct_change(fill_method=None); r=r.where(r.abs()<0.5)
dn=(r<0).astype(int)
# streak length
st=dn.copy()*0
grp=(dn==0).cumsum()
st=dn.groupby(grp).cumsum() if False else None
arr=dn.values; s=np.zeros_like(arr)
for i in range(1,len(arr)): s[i]=(s[i-1]+1)*arr[i]
s[0]=arr[0]; S=pd.DataFrame(s,index=dn.index,columns=dn.columns)
F,mkt=fwd(P,(1,5,20))
ma200=a.rolling(200).mean()
def ev(mask,lab):
    out=[]
    for h in (1,5,20):
        ex=F[h][1][mask].stack().dropna(); raw=F[h][0][mask].stack().dropna()
        out.append(f'h{h} ex {ex.mean():+.2f} raw {raw.mean():+.2f} n {len(ex)} win {(raw>0).mean()*100:.0f}%')
    print(lab,' | '.join(out))
    ex=F[20][1][mask].stack().dropna()
    for nm,s0,e0 in ERAS:
        x=ex.loc[s0:e0]; print('   ',nm,f'{x.mean():+.2f} n{len(x)}')
    for m in (2,4,6):
        st0=a.index.max()-pd.DateOffset(months=m+1); x=F[20][1][mask].loc[st0:].stack().dropna(); print(f'    last{m}m h20ex {x.mean():+.2f} n{len(x)}')
for N in (5,6,7,8,10):
    ev(S==N,f'exactly-hit {N} down days:')
# with trend filter
ev((S==8)&(a>ma200),'8 down & >200DMA:')
ev((S==8)&(a<ma200),'8 down & <200DMA:')
# placebo: random day with same stock & dates shifted 10 days
ev((S==8).shift(10,fill_value=False),'placebo (8-down shifted +10d):')
# stop/target -5/+10 within 20d from close entry for S==8
h=P['h']; l=P['l']; res=[]
ix=np.argwhere(((S==8)&(a>0)).values)
A=a.values;H=h.values;L=l.values
for i,j in ix:
    if i+21>=len(A): continue
    e=A[i,j]; o=None
    for k in range(i+1,i+21):
        if np.isnan(L[k,j]): break
        if L[k,j]<=e*0.95: o=-5;break
        if H[k,j]>=e*1.10: o=10;break
    if o is None:
        if np.isnan(A[i+20,j]): continue
        o=(A[i+20,j]/e-1)*100
    res.append(o)
res=np.array(res); net=res-COST
print(f'stop5/tgt10 20d: n{len(res)} target {np.mean(res==10)*100:.1f}% stop {np.mean(res==-5)*100:.1f}% exp net {net.mean():+.2f}% avgwin {net[net>0].mean():+.2f} avgloss {net[net<=0].mean():+.2f}')
