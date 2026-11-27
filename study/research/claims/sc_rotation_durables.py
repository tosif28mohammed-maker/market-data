# ROBOT
# r087 AI-14BEFA: Smallcap250 (^CNXSC) 12m outperformance vs Nifty >17-18% -> rotate to large? fwd 3/6/12m relative.
# r087 AI-CCEDA6: Nifty Consumer Durables vs Nifty 50, 2-year hold relative CAGR distribution (~+4% claim).
import subprocess, sys
subprocess.run([sys.executable,'-m','pip','install','-q','yfinance'],check=False)
import numpy as np, pandas as pd, yfinance as yf
def get(t):
    x=yf.download(t,start='2004-01-01',progress=False,auto_adjust=False)
    if isinstance(x.columns,pd.MultiIndex): x.columns=x.columns.get_level_values(0)
    s=x['Close'].dropna(); s=s[s>0]; print(t,len(s),s.index[0].date() if len(s) else '',s.index[-1].date() if len(s) else ''); return s
N=get('^NSEI'); SC=get('^CNXSC'); CD=get('NIFTY_CONSR_DURBL.NS')
if len(CD)<500: CD=get('^CNXCONSUM')  # fallback proxy (Nifty Consumption) - note
D=pd.concat({'n':N,'sc':SC},axis=1).dropna()
rel=(D.sc/D.sc.shift(252))-(D.n/D.n.shift(252))
print('\n=== AI-14BEFA Smallcap250 minus Nifty 12m return; fwd relative (SC - Nifty), monthly samples')
m=D.index.to_series().groupby(D.index.to_period('M')).last().values
for h,lab in [(63,'3m'),(126,'6m'),(252,'12m')]:
    fr=(D.sc.shift(-h)/D.sc)-(D.n.shift(-h)/D.n)
    for name,mask in [('ALL',rel.notna()),('rel>17%',rel>0.17),('rel>25%',rel>0.25),('rel<-17%',rel<-0.17)]:
        f=fr[mask].reindex(m).dropna()
        if len(f)<3: print(f' {lab} {name:9s} N{len(f)}'); continue
        print(f' {lab} {name:9s} N{len(f):3d} SC-Nifty avg {f.mean()*100:+6.2f}pp  SC better {np.mean(f>0)*100:4.0f}%')
# episodes: first month crossing >17%
cross=(rel>0.17)&(rel.shift(1)<=0.17)
print(' episodes (first cross >17%), fwd 6m/12m rel:')
for d in rel.index[cross]:
    i=D.index.get_loc(d)
    r6=(D.sc.iloc[min(i+126,len(D)-1)]/D.sc.iloc[i])-(D.n.iloc[min(i+126,len(D)-1)]/D.n.iloc[i])
    r12=(D.sc.iloc[min(i+252,len(D)-1)]/D.sc.iloc[i])-(D.n.iloc[min(i+252,len(D)-1)]/D.n.iloc[i])
    print(f'  {d.date()} rel {rel.loc[d]*100:+.0f}% -> 6m {r6*100:+.1f}pp 12m {r12*100:+.1f}pp')
print(' today rel 12m', round(rel.iloc[-1]*100,1), D.index[-1].date())
E=pd.concat({'n':N,'cd':CD},axis=1).dropna()
print('\n=== AI-CCEDA6 Consumer Durables vs Nifty, 2y hold (monthly start points)')
fr2=((E.cd.shift(-504)/E.cd)**0.5-1)-((E.n.shift(-504)/E.n)**0.5-1)
mm=E.index.to_series().groupby(E.index.to_period('M')).last().values
for era,a,b in [('all','2005','2026'),('2005-12','2005','2012'),('2013-19','2013','2019'),('2020-24','2020','2024')]:
    f=fr2[a:b].reindex([x for x in mm if str(a)<=str(x.year)<=str(b)]).dropna()
    if len(f)<3: continue
    print(f' {era:8s} N{len(f):3d} CAGR diff avg {f.mean()*100:+.2f}pp median {f.median()*100:+.2f}pp  CD better {np.mean(f>0)*100:.0f}%  >=+4pp {np.mean(f>=0.04)*100:.0f}%')
tot=(E.cd.iloc[-1]/E.cd.iloc[0])**(252/len(E))-1-((E.n.iloc[-1]/E.n.iloc[0])**(252/len(E))-1)
print(f' full-period CAGR diff {tot*100:+.2f}pp ({E.index[0].date()} to {E.index[-1].date()}); NOTE price index (no dividends) both')
