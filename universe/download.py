"""Download full daily history for one chunk of the Nifty 500 list: python universe/download.py CHUNK N_CHUNKS"""
import os, sys, time, pandas as pd, yfinance as yf
k,n=int(sys.argv[1]),int(sys.argv[2]); L=pd.read_csv('universe/nifty500.csv'); os.makedirs('out/daily',exist_ok=True); bad=[]
for s in L.symbol.tolist()[k::n]:
    df=None
    for t in (f'{s}.NS',f'{s}.BO'):
        for a in range(3):
            try:
                df=yf.download(t,period='max',interval='1d',auto_adjust=False,progress=False,threads=False); break
            except Exception as e: print(s,e); time.sleep(5)
        if df is not None and len(df): break
    if df is None or not len(df): bad.append(s); continue
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df=df.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adj','Volume':'volume'})
    df=df[['date','open','high','low','close','adj','volume']].dropna(subset=['close']); df['date']=pd.to_datetime(df.date).dt.tz_localize(None).dt.normalize()
    df.drop_duplicates('date',keep='last').sort_values('date').to_csv(f'out/daily/{s}.csv.gz',index=False,float_format='%.4f',compression='gzip'); time.sleep(0.7)
open(f'out/bad_{k}.txt','w').write('\n'.join(bad)); print('chunk',k,'bad',bad)
