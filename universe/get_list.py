"""Download the official Nifty 500 constituent list (NSE / niftyindices). Writes universe/nifty500.csv."""
import io, sys, requests, pandas as pd
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept':'text/csv,*/*','Referer':'https://www.niftyindices.com/'}
URLS=['https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv','https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv','https://archives.nseindia.com/content/indices/ind_nifty500list.csv']
for u in URLS:
    try:
        r=requests.get(u,headers=H,timeout=30)
        if r.ok and 'Symbol' in r.text[:500]:
            df=pd.read_csv(io.StringIO(r.text)); df.columns=[c.strip() for c in df.columns]
            df=df[['Company Name','Industry','Symbol']].rename(columns={'Company Name':'company','Industry':'industry','Symbol':'symbol'})
            df.to_csv('universe/nifty500.csv',index=False); print('ok',u,len(df)); sys.exit(0)
        print('bad',u,r.status_code)
    except Exception as e: print('err',u,e)
sys.exit(1)
