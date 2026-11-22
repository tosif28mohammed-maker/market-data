# ROBOT
"""BF-01b: Nifty distance below all-time high (drawdown bucket) -> forward 20/60/120/250-day returns.
Claim tested: buying near ATH is fine; does buying deeper below ATH give better forward returns? Eras + last 2/4/6 months."""
import os, pandas as pd, numpy as np
here=os.path.dirname(os.path.abspath(__file__))
n=pd.read_csv(os.path.join(here,'..','..','..','data','NIFTY.csv'),parse_dates=['date']).dropna(subset=['close']).sort_values('date').reset_index(drop=True)
cl=n['close'].values; dd=(cl/np.maximum.accumulate(cl)-1)*100
bins=[-100,-20,-15,-10,-5,-0.0001,1]; labs=['>20%','15-20','10-15','5-10','0-5','ATH']
n['b']=pd.cut(dd,bins=bins,labels=labs)
rows=[]
for hz in [20,60,120,250]:
    f=pd.Series(cl).shift(-hz)/pd.Series(cl)*100-100
    for era,(a,b) in {'all':('2007','2027'),'2007-13':('2007','2014'),'2014-19':('2014','2020'),'2020-26':('2020','2027')}.items():
        m=(n.date>=a)&(n.date<b)&f.notna()
        base=f[m].mean()
        for l in labs:
            x=f[m&(n.b==l)]
            if len(x)<15: continue
            rows.append(dict(h=hz,era=era,bucket=l,days=len(x),avg=round(x.mean(),2),pos=round((x>0).mean()*100,1),base=round(base,2)))
r=pd.DataFrame(rows); pd.set_option('display.width',200); print(r.to_string(index=False))
print('\ncurrent dd %.2f%% on %s'%(dd[-1],n.date.iloc[-1].date()))
for mo in [2,4,6]:
    s=n.date.iloc[-1]-pd.DateOffset(months=mo); m=n.date>=s
    print(f'last {mo}m: days in each bucket', n.b[m].value_counts().to_dict())
