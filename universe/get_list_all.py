"""All NSE equity (series EQ/BE) symbols -> universe/all_eq.csv (symbol, company, industry from Nifty 500 list when known)."""
import io, sys, requests, pandas as pd
H={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept':'text/csv,*/*'}
df=None
for u in ['https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv','https://archives.nseindia.com/content/equities/EQUITY_L.csv']:
    try:
        r=requests.get(u,headers=H,timeout=30)
        if r.ok and 'SYMBOL' in r.text[:300]: df=pd.read_csv(io.StringIO(r.text)); print('ok',u,len(df)); break
        print('bad',u,r.status_code)
    except Exception as e: print('err',u,e)
if df is None: sys.exit(1)
df.columns=[c.strip() for c in df.columns]; df=df[df['SERIES'].str.strip().isin(['EQ','BE'])]
out=df[['SYMBOL','NAME OF COMPANY']].rename(columns={'SYMBOL':'symbol','NAME OF COMPANY':'company'})
n5=None
for u in ['https://www.niftyindices.com/IndexConstituent/ind_nifty500list.csv','https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv']:
    try:
        r=requests.get(u,headers={**H,'Referer':'https://www.niftyindices.com/'},timeout=30)
        if r.ok and 'Symbol' in r.text[:500]: n5=pd.read_csv(io.StringIO(r.text)); break
    except Exception: pass
if n5 is not None:
    n5.columns=[c.strip() for c in n5.columns]; out=out.merge(n5[['Symbol','Industry']].rename(columns={'Symbol':'symbol','Industry':'industry'}),on='symbol',how='left')
    out['nifty500']=out.industry.notna()
out['industry']=out.get('industry',pd.Series(dtype=str)).fillna('NA'); out.to_csv('universe/all_eq.csv',index=False); print(len(out))
