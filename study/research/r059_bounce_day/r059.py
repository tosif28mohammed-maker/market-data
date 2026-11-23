"""r059 (23 Nov 2026): after a crash, does the FIRST big up-day mark a turn or a dead-cat bounce?
RULE WRITTEN BEFORE RESULTS:
 event gold: daily return >= +2.5% while close is >= 20% below running peak OR below 200DMA (first in 20 trading days)
 event silver: daily return >= +5% under the same condition.
 forward 5/20/60 trading days from the event close; also 'retest' = did price close below the pre-event 20-day low within 60 days.
 chance = all days with the same condition (below 200DMA or >=20% dd) without the up-day.
 eras: 2000-14 vs 2015-26; currencies: USD, INR (x FX_USDINR), KWD (x FX_USDKWD).
"""
import numpy as np, pandas as pd
R='/home/claude/market-data'
def g(f):
    s=pd.read_csv(f'{R}/data/global/{f}.csv',parse_dates=['date']).set_index('date').close
    s=s[~s.index.duplicated()].dropna(); return s[s>0]
G,S,I,K=g('CMD_GOLD'),g('CMD_SILVER'),g('FX_USDINR'),g('FX_USDKWD')
G,S=G[:'2026-11-20'],S[:'2026-11-20']  # exclude today's live bar
ser={}
for n,s in (('GOLD',G),('SILVER',S)):
    ser[n+'_USD']=s; ser[n+'_INR']=(s*I.reindex(s.index).ffill()).dropna(); ser[n+'_KWD']=(s*K.reindex(s.index).ffill()).dropna()
out=[]
for name,s in ser.items():
    th=0.025 if name.startswith('GOLD') else 0.05
    r=s.pct_change(); cond=(s<s.rolling(200).mean())|(s/s.cummax()-1<=-0.20)
    lo20=s.rolling(20).min().shift(1)
    ev=[];last=-99
    for i in range(201,len(s)):
        if cond.iloc[i] and r.iloc[i]>=th and i-last>20: ev.append(i); last=i
    for era,(a,b) in (('2000-14',('2000','2014')),('2015-26',('2015','2026'))):
        for h in (5,20,60):
            fw=(s.shift(-h)/s-1)*100
            e=[i for i in ev if a<=str(s.index[i].year)<=b and i+h<len(s)]
            if not e: continue
            x=fw.iloc[e]; base=fw[cond & (r<th)].loc[a:b].dropna()
            rt=np.mean([ (s.iloc[i+1:i+61]<lo20.iloc[i]).any() for i in e])*100 if h==60 else np.nan
            t=(x.mean()-base.mean())/(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>2 else np.nan
            out.append(dict(series=name,era=era,h=h,n=len(x),avg=round(x.mean(),2),up=round((x>0).mean()*100),chance=round(base.mean(),2),t=round(t,2),retest60=round(rt) if h==60 else ''))
df=pd.DataFrame(out); print(df.to_string(index=False))
df.to_csv(f'{R}/study/research/r059_bounce_day/r059.csv',index=False)
