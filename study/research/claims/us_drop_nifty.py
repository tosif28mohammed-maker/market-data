# ROBOT
# NW-02: बड़ी US tech गिरावट (Nasdaq <=-2%) / Kospi <=-3% के बाद Nifty: gap, open->close, 5 दिन
import pandas as pd, numpy as np
def ld(p):
    d=pd.read_csv(p,parse_dates=['date']).set_index('date').sort_index()
    return d[~d.index.duplicated()]
n=ld('data/NIFTY.csv'); q=ld('data/global/US_NASDAQ.csv'); k=ld('data/global/KR_KOSPI.csv')
n=n[(n.open>0)&(n.close>0)]
n['pc']=n.close.shift(1)
n['gap']=n.open/n.pc-1
n['oc']=n.close/n.open-1
n['c5']=n.close.shift(-5)/n.pc-1     # पिछले close से 5 दिन
n['o5']=n.close.shift(-5)/n.open-1   # gap पर open खरीद, 5 दिन
qr=q.close.pct_change()
kr=k.close.pct_change()
# Nifty दिन d के लिए: d से पहले का आख़िरी US close
qs=qr.reindex(n.index - pd.Timedelta(days=1), method='ffill').values
n['us']=qs
n['ko']=kr.reindex(n.index).values  # Kospi उसी दिन (12:00 IST बंद)
n=n.dropna(subset=['gap','us'])
bad=(n.gap.abs()<1e-6).mean()
print('gap==0 दिनों का हिस्सा (पुराना bad open data):',round(bad,3))
n=n[n.gap.abs()>1e-6]
def era(d):
    y=d.year
    return '2007-12' if y<=2012 else ('2013-20' if y<=2020 else '2021-26')
n['era']=[era(d) for d in n.index]
def show(mask,name):
    s=n[mask]; b=n
    print(f'\n== {name}: N={len(s)}')
    for col in ['gap','oc','c5','o5']:
        print(f'  {col}: signal mean {s[col].mean()*100:+.2f}% median {s[col].median()*100:+.2f}% | सब दिन mean {b[col].mean()*100:+.2f}%  | win% {100*(s[col]>0).mean():.0f} vs {100*(b[col]>0).mean():.0f}')
    o5c=s.o5-0.0025
    print(f'  open खरीद 5d after 0.25% cost: mean {o5c.mean()*100:+.2f}%  win {100*(o5c>0).mean():.0f}%')
    for e,g in s.groupby('era'):
        print(f'   {e}: N={len(g)} gap {g.gap.mean()*100:+.2f} oc {g.oc.mean()*100:+.2f} o5 {g.o5.mean()*100:+.2f} (सब दिन o5 {b[b.era==e].o5.mean()*100:+.2f})')
    last=n.index.max()
    for m in (2,4,6,12):
        g=s[s.index>last-pd.DateOffset(months=m)]
        print(f'   last {m}m: N={len(g)} gap {g.gap.mean()*100:+.2f} oc {g.oc.mean()*100:+.2f} o5 {g.o5.mean()*100:+.2f}')
show(n.us<=-0.02,'Nasdaq <= -2% (पिछली रात)')
show(n.us<=-0.03,'Nasdaq <= -3%')
show((n.ko<=-0.03),'Kospi उसी दिन <= -3%')
show((n.us<=-0.02)&(n.gap<=-0.005),'Nasdaq<=-2% और Nifty gap-down <= -0.5%')
# placebo: Nasdaq >= +2%
show(n.us>=0.02,'placebo: Nasdaq >= +2%')
# गिरावट के बाद gap कितना "भरता" है: oc का sign gap के उल्टा
s=n[n.us<=-0.02]
print('\nNasdaq<=-2%: Nifty gap और US ret का corr', round(np.corrcoef(s.us,s.gap)[0,1],2), '| सब दिन corr', round(np.corrcoef(n.us,n.gap)[0,1],2))
print('gap का कितना हिस्सा उसी दिन भरा (oc/-gap median, gap<-0.5%):', round((s.oc/-s.gap)[s.gap<-0.005].median(),2))
