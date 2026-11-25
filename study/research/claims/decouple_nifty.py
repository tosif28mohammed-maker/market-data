# ROBOT
# NW-03 (25 Nov news: Nasdaq -4% पर भी Nifty +~2%, best session since 6 Nov): US crash के दिन Nifty मज़बूत बंद = ताक़त का संकेत?
# Entry: उसी दिन close (3:25 PM approx) या अगले दिन open. Hold 5/10/20 दिन. Control: सब दिन + 'Nifty +1.5% दिन' (US crash के बिना). Placebo: US crash + Nifty नीचे बंद.
import pandas as pd, numpy as np
def ld(p):
    d=pd.read_csv(p,parse_dates=['date']).set_index('date').sort_index(); return d[~d.index.duplicated()]
n=ld('data/NIFTY.csv'); q=ld('data/global/US_NASDAQ.csv')
n=n[(n.open>0)&(n.close>0)]
n['r']=n.close.pct_change()
n['us']=q.close.pct_change().reindex(n.index-pd.Timedelta(days=1),method='ffill').values
for h in (5,10,20):
    n[f'c{h}']=n.close.shift(-h)/n.close-1
    n[f'o{h}']=n.close.shift(-h)/n.open.shift(-1)-1
n['dma']=n.close/n.close.rolling(200).mean()-1
n=n.dropna(subset=['r','us'])
n['era']=np.where(n.index.year<=2012,'2007-12',np.where(n.index.year<=2020,'2013-20','2021-26'))
C=0.0025
def show(m,name):
    s=n[m]; print(f'\n== {name}: N={len(s)}')
    for h in (5,10,20):
        a=s[f'c{h}'].dropna(); b=n[f'c{h}'].dropna(); o=s[f'o{h}'].dropna()
        print(f'  {h}d close-entry mean {a.mean()*100:+.2f}% (सब दिन {b.mean()*100:+.2f}) excess {100*(a.mean()-b.mean()):+.2f} win {100*(a>0).mean():.0f}% | next-open {o.mean()*100:+.2f} | cost बाद {100*(a.mean()-C):+.2f}')
    for e,g in s.groupby('era'):
        print(f'   {e}: N={len(g)} c10 {g.c10.mean()*100:+.2f} (सब {n[n.era==e].c10.mean()*100:+.2f}) c20 {g.c20.mean()*100:+.2f} (सब {n[n.era==e].c20.mean()*100:+.2f})')
    a=s[s.dma>0]; b=s[s.dma<=0]
    print(f'   >200DMA N={len(a)} c20 {a.c20.mean()*100:+.2f} | <200DMA N={len(b)} c20 {b.c20.mean()*100:+.2f}')
    L=n.index.max()
    for mo in (2,4,6,12):
        g=s[s.index>L-pd.DateOffset(months=mo)]; print(f'   last {mo}m N={len(g)} c5 {g.c5.mean()*100:+.2f} c20 {g.c20.mean()*100:+.2f}')
    print('   आख़िरी 8 दिन:', ', '.join(f"{d.date()} us{r*100:+.1f} nf{x*100:+.1f} c20 {c*100:+.1f}" for d,r,x,c in zip(s.index[-8:],s.us[-8:],s.r[-8:],s.c20[-8:])))
crash=n.us<=-0.02
show(crash&(n.r>=0.01),'SIGNAL: Nasdaq<=-2% और Nifty >=+1% बंद')
show(crash&(n.r>=0),'Nasdaq<=-2% और Nifty >=0 बंद')
show(crash&(n.r<0),'PLACEBO: Nasdaq<=-2% और Nifty नीचे बंद')
show(n.r>=0.015,'CONTROL: कोई भी Nifty +1.5% दिन')
show((n.us<=-0.03)&(n.r>=0.01),'सख़्त: Nasdaq<=-3% और Nifty>=+1%')
