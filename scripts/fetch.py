"""Runs on GitHub (free) every trading day after market close: downloads daily OHLCV for Nifty, India VIX and the
Nifty-50 stocks from Yahoo Finance and saves data/<SYMBOL>.csv (full history, updated) + data/latest.csv (last row of each).
Claude reads this repository with git clone."""
import os, time, pandas as pd, yfinance as yf
from fetch_list import TICKERS
os.makedirs('data', exist_ok=True); last=[]; bad=[]
for name, tk in TICKERS.items():
    path=f'data/{name}.csv'; old=pd.read_csv(path, parse_dates=['date']) if os.path.exists(path) else None
    for attempt in range(3):
        try:
            df=yf.download(tk, period='max' if old is None else '1mo', interval='1d', auto_adjust=False, progress=False, threads=False)
            if df is not None and len(df): break
        except Exception as e: print(name, 'retry', e)
        time.sleep(5)
    else:
        bad.append(name); continue
    if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    df=df.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adj','Volume':'volume'})
    df=df[['date','open','high','low','close','adj','volume']].dropna(subset=['close']); df['date']=pd.to_datetime(df.date).dt.tz_localize(None).dt.normalize()
    if old is not None: df=pd.concat([old, df])   # keep every old day; newer download wins on the same date
    df=df.drop_duplicates('date', keep='last').sort_values('date'); df.to_csv(path, index=False, float_format='%.4f')
    r=df.iloc[-1]; last.append(dict(symbol=name, date=r.date.date(), open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume))
    time.sleep(1)
pd.DataFrame(last).to_csv('data/latest.csv', index=False)
open('data/STATUS.txt','w').write(f'updated {pd.Timestamp.utcnow():%Y-%m-%d %H:%M} UTC; ok {len(last)}; failed {bad}\n')
print('ok', len(last), 'failed', bad)
