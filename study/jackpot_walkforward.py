"""Jackpot option-buying walk-forward (Tosif 27 Nov 2026: 'chhoti rakam, bada move, stop ke saath').
Har din sirf pichhla data. Option bhaav = Black-Scholes + India VIX x skew (paper/engine.py jaisa) -> MODEL, asli nahi.
Test A: andha strangle (2% OTM CE+PE, 7 trading din expiry) roz / 'squeeze' (shaant bazaar) par - target 3x, stop 50%.
Test B: US-fade disha (S&P raat ka move pichhle 5 saal ke top/bottom 10%) + Nifty ATM option, 9:15 kharid, 15:15 bech, stop 50%.
NATEEJA (27 Nov 2026):
 A: har daur GHAATA (roz avg -14%, squeeze -14 se -48%, bina stop 5x target bhi -11%). Shaant bazaar aksar shaant hi rehta hai.
 B: expiry 1 din -> -10.7%/sauda; 2 din -5.4%; 4 din -3.5% (2010-26). Sirf Nov 2023 ke baad 4-din +5.8%, 2-din +3.7%.
    => disha ka edge (futures mein +) option ke theta mein kha jaata hai. Jackpot (2x+) sirf ~4% saude.
 Pehli quick test (+1%/sauda) mein intraday theta kam gina tha - wo galat tha.
Run: python3 study/jackpot_walkforward.py
"""
import pandas as pd, math
from math import log, sqrt
N=lambda x:0.5*(1+math.erf(x/sqrt(2))); R=0.065
def bs(S,K,T,v,cp):
    if T<=0: return max(0,(S-K) if cp=='C' else (K-S))
    s=v*sqrt(T); d1=(log(S/K)+(R+v*v/2)*T)/s; d2=d1-s
    return S*N(d1)-K*math.exp(-R*T)*N(d2) if cp=='C' else K*math.exp(-R*T)*N(-d2)-S*N(-d1)
iv=lambda vix,S,K: vix/100*min(1.6,max(0.6,0.973-5.36*log(K/S)))
rd=lambda p: pd.read_csv(p,parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index()
d=rd('data/NIFTY.csv').dropna(subset=['open','close']); d=d[(d.open>0)&(d.high>=d.low)]
vx=rd('data/INDIAVIX.csv').close.dropna()
us=rd('data/global/US_SP500.csv').close.dropna().pct_change().dropna()
rows=[]
for day,r in d.iterrows():
    if day<pd.Timestamp('2010-06-01'): continue
    prev=us[us.index<day]; pv=vx[vx.index<day]
    if not len(pv) or (day-prev.index[-1]).days>4: continue
    h5=prev[prev.index>=day-pd.Timedelta(days=1825)].iloc[:-1]; m=prev.iloc[-1]
    side=-1 if m>=h5.quantile(.9) else (1 if m<=h5.quantile(.1) else 0)
    if not side: continue
    o,h,l,c=r.open,r.high,r.low,r.close; cp='C' if side==1 else 'P'; K=round(o/50)*50; v0=pv.iloc[-1]; v1=vx.get(day,v0)
    for nb in (1,2,4):
        T0=nb/252; T1=max(nb-1,0)/252+0.25/252; p0=bs(o,K,T0,iv(v0,o,K),cp)
        if p0<1: continue
        bad=l if cp=='C' else h; w=bs(bad,K,(T0+T1)/2,iv(v0,bad,K),cp)
        ret=-0.5 if w<=0.5*p0 else bs(c,K,T1,iv(v1,c,K),cp)/p0-1
        rows.append(dict(day=day,expiry_days=nb,ret=ret-0.03))
X=pd.DataFrame(rows)
for st in ('2010-06-01','2016-11-27','2023-11-27','2025-11-27'):
    print('from',st, X[X.day>=st].groupby('expiry_days').ret.agg(['count','mean']).round(3).to_dict('index'))
