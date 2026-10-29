"""Runs on GitHub every 15 minutes during Indian market hours: 5-minute candles (Yahoo, ~delayed) for Nifty, VIX and the
Nifty-50 stocks -> data/intraday/<SYMBOL>_5m.csv (keeps the last 60 days). Claude reads with git clone."""
import os, time, pandas as pd, yfinance as yf
from fetch_list import TICKERS
os.makedirs('data/intraday', exist_ok=True)
for name, tk in TICKERS.items():
    try:
        first = not os.path.exists(f'data/intraday/{name}_5m.csv')
        df = yf.download(tk, period='60d' if first else '5d', interval='5m', auto_adjust=False, progress=False, threads=False)
    except Exception as e:
        print(name, e); continue
    if df is None or not len(df): continue
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={'Datetime':'time','Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})
    df['time'] = pd.to_datetime(df.time).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
    df = df[['time','open','high','low','close','volume']]
    path = f'data/intraday/{name}_5m.csv'
    if os.path.exists(path): df = pd.concat([pd.read_csv(path, parse_dates=['time']), df])
    df = df.drop_duplicates('time', keep='last').sort_values('time')
    df = df[df.time >= df.time.max() - pd.Timedelta(days=60)]
    df.to_csv(path, index=False, float_format='%.4f'); time.sleep(0.5)
open('data/intraday/STATUS.txt','w').write(f'updated {pd.Timestamp.now(tz="Asia/Kolkata"):%Y-%m-%d %H:%M} IST\n')
