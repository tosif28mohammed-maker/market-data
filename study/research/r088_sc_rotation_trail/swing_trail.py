# r088 test_queue: (1) Daily swing screen: C>EMA20>EMA50, C>Supertrend(10,3), ADX14>20 & rising, RSI14 55-70, 12d ret>5%, vol>1.5x20d
# (2) Multi-tier trailing exit: SL 5%, at +5% -> BE, at +10% -> +5%, EOD exit if close<SMA5; vs fixed 5%SL/10%T; max 20 days.
# Entry next-day open. Cost 0.25% round trip. Control: uptrend-only (C>EMA20>EMA50) random sample same count/month.
import sys,numpy as np,pandas as pd,numba as nb
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); C=P['c'].loc['2004':]; cols=C.columns; idx=C.index
f=lambda k:P[k].reindex(index=idx,columns=cols)
r=(P['a']/P['c']).reindex(index=idx,columns=cols)
c=C*r; o=f('o'); h=f('h'); l=f('l'); v=f('v')
e20=c.ewm(span=20,adjust=False).mean(); e50=c.ewm(span=50,adjust=False).mean()
pc=c.shift(1); tr=pd.concat([h-l,(h-pc).abs(),(l-pc).abs()]).groupby(level=0).max().reindex(idx)
atr14=tr.ewm(alpha=1/14,adjust=False).mean(); atr10=tr.ewm(alpha=1/10,adjust=False).mean()
up=h-h.shift(1); dn=l.shift(1)-l
pdm=up.where((up>dn)&(up>0),0.); mdm=dn.where((dn>up)&(dn>0),0.)
pdi=100*pdm.ewm(alpha=1/14,adjust=False).mean()/atr14; mdi=100*mdm.ewm(alpha=1/14,adjust=False).mean()/atr14
dx=100*(pdi-mdi).abs()/(pdi+mdi); adx=dx.ewm(alpha=1/14,adjust=False).mean()
d=c.diff(); rs=d.clip(lower=0).ewm(alpha=1/14,adjust=False).mean()/(-d.clip(upper=0)).ewm(alpha=1/14,adjust=False).mean(); rsi=100-100/(1+rs)
@nb.njit
def st_dir(H,L,Cc,A):
    T,N=Cc.shape; out=np.zeros((T,N))
    for j in range(N):
        fu=np.nan; fl=np.nan; dirn=0
        for t in range(T):
            if np.isnan(Cc[t,j]) or np.isnan(A[t,j]): continue
            m=(H[t,j]+L[t,j])/2; bu=m+3*A[t,j]; bl=m-3*A[t,j]
            if np.isnan(fu): fu=bu; fl=bl; dirn=1; out[t,j]=dirn; continue
            pcl=Cc[t-1,j]
            fu = bu if (bu<fu or pcl>fu) else fu
            fl = bl if (bl>fl or pcl<fl) else fl
            if Cc[t,j]>fu: dirn=1
            elif Cc[t,j]<fl: dirn=-1
            out[t,j]=dirn
    return out
std=pd.DataFrame(st_dir(h.values,l.values,c.values,atr10.values),index=idx,columns=cols)
trend=(c>e20)&(e20>e50)
sig=trend&(std>0)&(adx>20)&(adx>adx.shift(1))&(rsi>=55)&(rsi<=70)&(c/c.shift(12)>1.05)&(v>1.5*v.rolling(20).mean())
sma5=c.rolling(5).mean()
@nb.njit
def sim(S,O,H,L,Cc,S5,mode,maxd):
    T,N=Cc.shape; res=[]
    for j in range(N):
        t=0
        while t<T-2:
            if not S[t,j]: t+=1; continue
            e=O[t+1,j]
            if np.isnan(e) or e<=0: t+=1; continue
            sl=e*0.95; tg=e*1.10; hi=e; ex=np.nan; k=t+1; hit=0
            while k<T and k<=t+maxd:
                if np.isnan(Cc[k,j]): k+=1; continue
                if L[k,j]<=sl: ex=min(O[k,j],sl) if k>t+1 else sl; break
                if mode==0 and H[k,j]>=tg: ex=max(O[k,j],tg) if k>t+1 else tg; hit=1; break
                if mode==1:
                    hi=max(hi,H[k,j])
                    if Cc[k,j]<S5[k,j] and k>t+1: ex=Cc[k,j]; break
                    if hi>=e*1.10: sl=max(sl,e*1.05)
                    elif hi>=e*1.05: sl=max(sl,e)
                k+=1
            if np.isnan(ex):
                k=min(k,T-1)
                while k>t and np.isnan(Cc[k,j]): k-=1
                ex=Cc[k,j]
            res.append((t,j,(ex/e-1)*100-0.25,hit,k-t))
            t=k+1
    return res
def rep(nm,R):
    D=pd.DataFrame(R,columns=['t','j','ret','hit','days']); D['d']=idx[D.t.values]
    def s(x): 
        w=x.ret[x.ret>0]; L_=x.ret[x.ret<=0]
        return f'N{len(x):6d} win {np.mean(x.ret>0)*100:4.1f}% tgt {x.hit.mean()*100:4.1f}% avgW {w.mean():+5.2f} avgL {L_.mean():+5.2f} net {x.ret.mean():+5.2f} days {x.days.mean():4.1f}'
    print(nm,'ALL',s(D))
    for a_,b_ in [('2004','2012'),('2013','2020'),('2021','2026')]: print('   ',a_,b_,s(D[(D.d>=a_)&(D.d<=b_+'-12-31')]))
    for m in (6,4,2): print('    last',m,'m',s(D[D.d>=idx[-1]-pd.DateOffset(months=m)]))
    return D
Sv=sig.fillna(False).values
print('signals',int(Sv.sum()),'per day',round(Sv.sum()/len(idx),1))
args=(o.values,h.values,l.values,c.values,sma5.values)
rep('SCREEN fixed5/10',sim(Sv,*args,0,20)); rep('SCREEN multi-tier',sim(Sv,*args,1,20))
# control: random uptrend days, same monthly count
rng=np.random.default_rng(7); Tv=trend.fillna(False).values; ctl=np.zeros_like(Tv)
per=idx.to_period('M')
for p in per.unique():
    rows=np.where(per==p)[0]; n=int(Sv[rows].sum())
    cand=np.argwhere(Tv[rows]);
    if n==0 or len(cand)==0: continue
    pick=cand[rng.choice(len(cand),min(n,len(cand)),replace=False)]
    ctl[rows[pick[:,0]],pick[:,1]]=True
rep('CONTROL uptrend fixed',sim(ctl,*args,0,20)); rep('CONTROL uptrend multi-tier',sim(ctl,*args,1,20))
print('today signals:',list(cols[Sv[-1]])[:20])
