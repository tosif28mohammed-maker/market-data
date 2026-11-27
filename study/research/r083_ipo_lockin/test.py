# r083 (i06): IPO lock-in expiry (anchor 30d / 90d, pre-IPO 6m / 1y, promoter 18m) -> share कमज़ोर?
# Rule (लिखा पहले): listing date = panel में पहली trading date (>=2005, panel 2002-07 से).
# Event day = listing + K calendar days के बाद पहला trading day. K = 30, 90, 180, 365, 540.
# Window excess vs EW market (log-cum): pre[-10,-1], post[0,+5], [0,+10], [0,+20]; plus [-10,+20].
# Placebo: same stocks, K' = 60, 120, 240, 300, 450 (कोई lock-in नहीं). Chance: random offsets 20-600d.
import sys, numpy as np, pandas as pd
sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); a=P['a']; v=P['v']; c=P['c']
r1=a.pct_change(fill_method=None); r1=r1.where(r1.abs()<0.4)
mkt=r1.mean(axis=1)
lr=np.log1p(r1.fillna(0)).cumsum(); lm=np.log1p(mkt.fillna(0)).cumsum(); ex=lr.sub(lm,axis=0)
idx=a.index
first=a.apply(lambda s: s.first_valid_index())
first=first[first>=pd.Timestamp('2005-01-01')]
print('IPOs (first date>=2005):',len(first), 'by yr', first.dt.year.value_counts().sort_index().to_dict())
N=pd.read_csv('/home/claude/market-data/data/NIFTY.csv',parse_dates=['date']).set_index('date').close
dma=N.rolling(200).mean()
def win(s,i,lo,hi):
    if i+lo<1 or i+hi>=len(idx): return np.nan
    x=ex[s]
    return (x.iloc[i+hi]-x.iloc[i+lo-1])*100
W={'pre-10_-1':(-10,-1),'d0_5':(0,5),'d0_10':(0,10),'d0_20':(0,20),'-10_+20':(-10,20)}
def events(K):
    rows=[]
    for s,f in first.items():
        t=f+pd.Timedelta(days=K); j=idx.searchsorted(t)
        if j>=len(idx)-21: continue
        if pd.isna(a[s].iloc[j]): continue
        i0=idx.get_loc(f)
        # run since listing: excess from listing close to day -11
        runup=(ex[s].iloc[j-11]-ex[s].iloc[i0])*100 if j-11>i0 else np.nan
        abs_run=(a[s].iloc[j-1]/a[s].iloc[i0]-1)*100
        vol_pre=v[s].iloc[max(i0,j-30):j-5].mean(); vol_post=v[s].iloc[j:j+3].mean()
        d=idx[j]
        r={'s':s,'d':d,'K':K,'runup':runup,'abs_run':abs_run,'volx':vol_post/vol_pre if vol_pre>0 else np.nan,
           'bull': bool(N.asof(d)>dma.asof(d)) if not np.isnan(dma.asof(d)) else np.nan}
        for k,(lo,hi) in W.items(): r[k]=win(s,j,lo,hi)
        rows.append(r)
    return pd.DataFrame(rows)
def summ(R,lab):
    out={'N':len(R)}
    for k in W: out[k]=round(R[k].mean(),2)
    out['%neg d0_20']=round((R['d0_20']<0).mean()*100)
    out['t d0_20']=round(R['d0_20'].mean()/R['d0_20'].std()*np.sqrt(R['d0_20'].count()),2)
    print(lab, out)
ALL={}
for K in (30,90,180,365,540):
    R=events(K); ALL[K]=R; summ(R,f'K={K}')
    for era,(y0,y1) in {'2005-12':(2005,2012),'2013-20':(2013,2020),'2021-26':(2021,2026)}.items():
        x=R[(R.d.dt.year>=y0)&(R.d.dt.year<=y1)]
        if len(x)>=15: summ(x,f'   {era}')
print('--- placebo offsets')
for K in (60,120,240,300,450): summ(events(K),f'placebo K={K}')
# chance: random offsets 20-600 days, 200 draws mean of d0_20
rng=np.random.default_rng(0)
base=[]
pool={K:events(K) for K in range(20,601,20) if K not in (20,40) }
mat=pd.concat([pool[K].assign(K=K) for K in pool])
m=mat.groupby('K')[['d0_5','d0_20','pre-10_-1']].mean().round(2)
print('offset curve (mean excess by K):'); print(m.T.to_string())
pd.to_pickle(ALL,'events.pkl'); mat.to_csv('offset_events.csv.gz',index=False)
