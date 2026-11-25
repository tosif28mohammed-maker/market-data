# r067a: Nifty PE & earnings-yield/G-sec ratio -> Nifty forward returns (AI-D1EDA5/7292D2/CB739F/0811E2)
import pandas as pd, numpy as np
R='/home/claude/market-data/'
v=pd.read_csv(R+'data/indices/index_valuation.csv',low_memory=False)
v=v[v['index']=='Nifty 50'].copy(); v['date']=pd.to_datetime(v.date); v['pe']=pd.to_numeric(v.pe,errors='coerce')
v=v.dropna(subset=['pe']).drop_duplicates('date').set_index('date').sort_index()
n=pd.read_csv(R+'data/NIFTY.csv',parse_dates=['date']).set_index('date').close
g=pd.read_csv(R+'data/macro/india_10y_gsec_pct.csv',parse_dates=[0]); g=g.set_index(g.columns[0]).iloc[:,0].astype(float)
df=pd.DataFrame({'pe':v.pe}).join(n.rename('nifty'),how='inner')
df['gs']=g.reindex(df.index,method='ffill')
df['ey_gs']=(100/df.pe)/df.gs
for h in (60,120,250):
    df[f'f{h}']=(df.nifty.shift(-h)/df.nifty-1)*100
print('rows',len(df),df.index.min().date(),df.index.max().date())
# methodology break Apr-2021 (standalone->consolidated EPS) : pe within-era percentile
df['era']=np.where(df.index<'2021-04-01','pre21','post21')
df['pe_pct']=df.groupby('era').pe.rank(pct=True)
print(df.groupby('era').pe.describe()[['min','50%','max']])
print(df.ey_gs.describe())
def tab(col,bins,lab):
    d=df.dropna(subset=['f250']).copy(); d['b']=pd.cut(d[col],bins)
    t=d.groupby('b',observed=True).agg(n=('f60','size'),f60=('f60','mean'),f120=('f120','mean'),f250=('f250','mean'),win250=('f250',lambda x:(x>0).mean()*100),months=('f250',lambda x:x.index.to_period('M').nunique()))
    print('\n==',lab); print(t.round(1).to_string())
tab('pe',[0,18,20,22,24,26,40],'PE raw buckets')
tab('pe_pct',[0,.2,.4,.6,.8,1],'PE percentile within era')
tab('ey_gs',[0,.55,.65,.75,.85,2],'EY/G-sec ratio')
# rules from claims
d=df.dropna(subset=['f250'])
print('\nall days f250 mean',round(d.f250.mean(),1),'win',round((d.f250>0).mean()*100))
print('EY/GS<0.87 (avoid) f250',round(d[d.ey_gs<0.87].f250.mean(),1),'n',(d.ey_gs<0.87).sum(),' >=0.87',round(d[d.ey_gs>=0.87].f250.mean(),1),'n',(d.ey_gs>=0.87).sum())
print('EY/GS>=1.4 days:',(df.ey_gs>=1.4).sum(),' PE<=12 days:',(df.pe<=12).sum())
# AI-D1EDA5: fair PE = 1/(0.7*gs) ; gap = pe/fair
df['fair']=100/(0.7*df.gs); df['gap']=df.pe/df.fair
tab('gap',[0,1.0,1.15,1.3,1.5,3],'PE / fairPE(1/(0.7*Gsec))')
# recent
for m in (2,4,6):
    s=df.index.max()-pd.DateOffset(months=m); x=df.loc[s:]
    print(f'last {m}m: pe {x.pe.min():.1f}-{x.pe.max():.1f}  ey/gs {x.ey_gs.min():.2f}-{x.ey_gs.max():.2f}')
print('latest',df.iloc[-1][['pe','gs','ey_gs','gap']].round(2).to_dict())
print('\n== excluding Feb-Jun 2020 crisis')
d=df.dropna(subset=['f250']); d=d[~((d.index>='2020-02-15')&(d.index<='2020-06-30'))]
d=d.assign(b=pd.cut(d.pe_pct,[0,.2,.4,.6,.8,1]))
print(d.groupby('b',observed=True).agg(n=('f250','size'),f120=('f120','mean'),f250=('f250','mean'),win=('f250',lambda x:(x>0).mean()*100),years=('f250',lambda x:sorted(set(x.index.year)))).to_string())
