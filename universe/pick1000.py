"""Pick top 1000 by median daily turnover (Nifty 500 always kept), recent data only. python universe/pick1000.py art_dir out_dir"""
import sys, os, glob, shutil, pandas as pd
A,O=sys.argv[1],sys.argv[2]; S=pd.concat([pd.read_csv(f) for f in glob.glob(f'{A}/daily-*/stats_*.csv')]); L=pd.read_csv(glob.glob(f'{A}/list*/all_eq.csv')[0])
S=S.merge(L,on='symbol',how='left'); S['last']=pd.to_datetime(S['last'])
S=S[S['last']>=S['last'].max()-pd.Timedelta(days=10)]
S=S.sort_values('turnover_cr',ascending=False); S['rank']=range(1,len(S)+1)
keep=S[(S['rank']<=1000)|(S.nifty500==True)]
os.makedirs(f'{O}/daily',exist_ok=True)
for s in keep.symbol:
    src=glob.glob(f'{A}/daily-*/daily/{s}.csv.gz')
    if src: shutil.copy(src[0],f'{O}/daily/{s}.csv.gz')
keep.to_csv(f'{O}/list1000.csv',index=False); S.to_csv(f'{O}/all_ranked.csv',index=False); print('kept',len(keep),'of',len(S))
