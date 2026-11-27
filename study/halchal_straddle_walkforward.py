"""HALCHAL signal (disha nahi, bada move) -> ATM STRADDLE kharid, walk-forward (27 Nov 2026).
Signal (shock_watch.py jaisa, nateeje wala hissa chhod kar - uska itihaas nahi): kal +5%, RS 3m top 10%, volume 5d 1.8x, 52w high paas; score>=3.
Sirf F&O shares (data/fo_lots.csv). Close par ATM CE+PE, expiry ~20 kaarobaari din, 5 din rakh kar bech.
IV ka asli itihaas NAHI hai -> IV = k x pichhle 60 din ki asli chaal (k=1.15 aur 1.35 dono; +5% din ke baad IV aksar badha hota hai). MODEL.
Tulna: wahi straddle bina signal (har F&O share, har 10 din). Cost: premium ka 3%.
NATEEJA (27 Nov 2026; data/daily_all sirf Nov 2024-Nov 2026, 496 halchal saude):
 HALCHAL straddle avg -4.7% (IV 1.15x) / -7.6% (1.35x), jeet 18-24%, 2x+ ~0%. Bina signal -4.0%. => FAIL, signal straddle ko nahi bachata
 (halchal ka |chaal| 1.8x hai par option pehle se mehenga). Lamba test universe500 branch (2002+) par baaki.
Run: python3 study/halchal_straddle_walkforward.py
"""
import pandas as pd, numpy as np, math
from math import log, sqrt
N=lambda x:0.5*(1+math.erf(x/sqrt(2)))
def bs(S,K,T,v,cp):
    if T<=0: return max(0,(S-K) if cp=='C' else (K-S))
    s=v*sqrt(T); d1=(log(S/K)+(0.065+v*v/2)*T)/s; d2=d1-s
    return S*N(d1)-K*math.exp(-0.065*T)*N(d2) if cp=='C' else K*math.exp(-0.065*T)*N(-d2)-S*N(-d1)
rd=lambda f: pd.read_csv(f'data/daily_all/{f}',index_col=0,parse_dates=True)
C,V,H=rd('close.csv.gz'),rd('volume.csv.gz'),rd('high.csv.gz')
fo=set(pd.read_csv('data/fo_lots.csv').iloc[:,0].astype(str))
cols=[c for c in C.columns if c in fo]; C,V,H=C[cols],V[cols],H[cols]
C=C[C.index>='2012-01-01']; V=V.reindex(C.index); H=H.reindex(C.index)
r1=C.pct_change(fill_method=None); r1=r1.where(r1.abs()<0.4)
rv60=r1.rolling(60,min_periods=40).std()*sqrt(252)
f1=r1>=0.05; f2=(C/C.shift(63)-1).rank(axis=1,pct=True)>=0.9
f3=V.rolling(5).mean()>=1.8*V.shift(5).rolling(50).mean(); f4=C>=0.95*H.rolling(250).max()
score=f1.astype(int)+f2.astype(int)+f3.astype(int)+f4.astype(int)
idx=C.index; rows=[]
def trade(i,s,kk):
    S=C[s].iloc[i]; S5=C[s].iloc[i+5]; v=rv60[s].iloc[i]
    if not (S>0 and S5>0 and v>0): return None
    iv=v*kk; K=S; p0=bs(S,K,20/252,iv,'C')+bs(S,K,20/252,iv,'P')
    p1=bs(S5,K,15/252,iv,'C')+bs(S5,K,15/252,iv,'P')
    return p1/p0-1-0.03
for i in range(260,len(idx)-6):
    sig=score.iloc[i]; hit=sig[sig>=3].index
    for s in hit:
        for kk in (1.15,1.35):
            x=trade(i,s,kk)
            if x is not None: rows.append(dict(day=idx[i],sym=s,k=kk,grp='HALCHAL',ret=x))
    if i%10==0:
        for s in cols:
            x=trade(i,s,1.15)
            if x is not None and not np.isnan(x): rows.append(dict(day=idx[i],sym=s,k=1.15,grp='bina signal',ret=x))
X=pd.DataFrame(rows).dropna()
for st in ('2013-01-01','2018-01-01','2023-11-27'):
    for (g,k),x in X[X.day>=st].groupby(['grp','k']):
        print(st[:4],'+',g,'IVx',k,'| saude',len(x),'| avg %+.1f%%'%(100*x.ret.mean()),'| jeet %.0f%%'%(100*(x.ret>0).mean()),'| 2x+ %.1f%%'%(100*(x.ret>=1).mean()))
