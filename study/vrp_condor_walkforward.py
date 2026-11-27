"""VIX ooncha vs asli chaal (volatility risk premium) par HEDGED iron condor — walk-forward 2010-26 (27 Nov 2026).
Har 5 kaarobaari din: Nifty close par 4 legs: short CE/PE = close +- k * (VIX-weekly SD), long wings aur 2% door. 5 din baad expiry (intrinsic).
Bhaav = Black-Scholes + VIX x skew (MODEL, asli nahi), cost = Rs 160 + premium ka 3% (4 legs slippage). Lot 65.
Filter: ratio = VIX / pichhle 20 din ki asli chaal (annualised). 'ooncha' = pichhle 1 saal ke ratio ka top 1/3 (sirf pichhla data).
NATEEJA (27 Nov 2026, model bhaav):
 k=1.0 (short strike 1 SD): 2010-26 822 saude, 80% jeet, risk par +1.9%, max giravat Rs -76k (1 lot). 2023+ sirf +0.9%.
 VIX/asli OONCHA filter: 2010+ +2.2% (thoda behtar) PAR 2023+ -2.8% (FAIL). k=1.5: lagbhag zero.
 => weekly condor ka fayda patla aur model par tika; VRP filter bharose layak nahi. 'Rakhna/analysis' - asli bhaav (Zenodo G2) se dobara.
Run: python3 study/vrp_condor_walkforward.py
"""
import pandas as pd, numpy as np, math
from math import log, sqrt
N=lambda x:0.5*(1+math.erf(x/sqrt(2))); R=0.065
def bs(S,K,T,v,cp):
    if T<=0: return max(0,(S-K) if cp=='C' else (K-S))
    s=v*sqrt(T); d1=(log(S/K)+(R+v*v/2)*T)/s; d2=d1-s
    return S*N(d1)-K*math.exp(-R*T)*N(d2) if cp=='C' else K*math.exp(-R*T)*N(-d2)-S*N(-d1)
iv=lambda vix,S,K: vix/100*min(1.6,max(0.6,0.973-5.36*log(K/S)))
rd=lambda p: pd.read_csv(p,parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index()
n=rd('data/NIFTY.csv').close.dropna(); vx=rd('data/INDIAVIX.csv').close.dropna()
df=pd.concat([n.rename('c'),vx.rename('v')],axis=1).dropna(); df=df[df.index>='2009-01-01']
df['rv']=np.log(df.c).diff().rolling(20).std()*sqrt(252)*100; df['ratio']=df.v/df.rv
df['rq']=df.ratio.rolling(250,min_periods=120).apply(lambda x:(x[:-1]<x[-1]).mean(),raw=True)
rows=[]; idx=df.index
for i in range(260,len(idx)-5,5):
    d=idx[i]; S=df.c.iloc[i]; v=df.v.iloc[i]; ST=df.c.iloc[i+5]; T=5/252
    for k in (1.0,1.5):
        sd=S*v/100*sqrt(T); kc=round((S+k*sd)/50)*50; kp=round((S-k*sd)/50)*50; wc=kc+round(S*0.02/50)*50; wp=kp-round(S*0.02/50)*50
        cr=bs(S,kc,T,iv(v,S,kc),'C')+bs(S,kp,T,iv(v,S,kp),'P')-bs(S,wc,T,iv(v,S,wc),'C')-bs(S,wp,T,iv(v,S,wp),'P')
        pay=max(0,ST-kc)-max(0,ST-wc)+max(0,kp-ST)-max(0,wp-ST)
        maxloss=(wc-kc)-cr
        pnl=(cr-pay)*65-160-0.03*cr*65
        rows.append(dict(day=d,k=k,ratio_q=df.rq.iloc[i],vix=v,pnl=pnl,risk=maxloss*65))
X=pd.DataFrame(rows).dropna()
def show(x,name):
    c=x.pnl.cumsum(); return f"{name}: {len(x)} saude, jeet {100*(x.pnl>0).mean():.0f}%, kul Rs {x.pnl.sum()/1e3:+.0f}k, avg/sauda Rs {x.pnl.mean():+.0f}, risk par {100*x.pnl.sum()/x.risk.sum():+.1f}%, max giravat Rs {(c-c.cummax()).min()/1e3:.0f}k"
for k in (1.0,1.5):
    for st in ('2010-01-01','2016-11-27','2023-11-27'):
        x=X[(X.k==k)&(X.day>=st)]
        print(f'k={k} {st[:4]}+ |', show(x,'SAB'), '||', show(x[x.ratio_q>=0.67],'VIX/asli OONCHA'), '||', show(x[x.ratio_q<=0.33],'neecha'))
