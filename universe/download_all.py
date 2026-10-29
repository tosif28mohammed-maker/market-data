"""Download full daily history for one chunk of all NSE equities + liquidity (median daily turnover, last 6 months).
python universe/download_all.py CHUNK N_CHUNKS"""
import os, sys, time, pandas as pd, yfinance as yf
k,n=int(sys.argv[1]),int(sys.argv[2]); L=pd.read_csv('universe/all_eq.csv'); os.makedirs('out/daily',exist_ok=True); stats=[]
for s in L.symbol.tolist()[k::n]:
    df=None
    for a in range(2):
        try: df=yf.download(f'{s}.NS',period='max',interval='1d',auto_adjust=False,progress=False,threads=False); break
        except Exception as e: print(s,e); time.sleep(5)
    if df is None or not len(df): continue
    if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df=df.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adj','Volume':'volume'})
    df=df[['date','open','high','low','close','adj','volume']].dropna(subset=['close']); df['date']=pd.to_datetime(df.date).dt.tz_localize(None).dt.normalize()
    df=df.drop_duplicates('date',keep='last').sort_values('date')
    last=df[df.date>=df.date.max()-pd.Timedelta(days=183)]
    stats.append(dict(symbol=s,first=df.date.min().date(),last=df.date.max().date(),days=len(df),turnover_cr=float((last.close*last.volume).median()/1e7)))
    df.to_csv(f'out/daily/{s}.csv.gz',index=False,float_format='%.4f',compression='gzip'); time.sleep(0.4)
pd.DataFrame(stats).to_csv(f'out/stats_{k}.csv',index=False); print('chunk',k,len(stats))
