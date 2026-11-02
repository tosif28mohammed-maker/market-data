"""Intraday history for one chunk of the universe: 1-hour (Yahoo keeps ~730 days), 15-minute and 5-minute (60 days).
python universe/intra_all.py CHUNK N_CHUNKS  -> out/h1|m15|m5/<SYM>.csv.gz (times in IST)"""
import os, sys, time, pandas as pd, yfinance as yf
k, n = int(sys.argv[1]), int(sys.argv[2]); L = pd.read_csv('universe/intra_list.csv').symbol.tolist()[k::n]
IDX = {'NIFTY': '^NSEI', 'BANKNIFTY': '^NSEBANK'}
for sub in ('h1', 'm15', 'm5'): os.makedirs(f'out/{sub}', exist_ok=True)
def get(tk, period, interval):
    for a in range(3):
        try:
            df = yf.download(tk, period=period, interval=interval, auto_adjust=False, progress=False, threads=False)
            if df is not None and len(df): break
        except Exception as e: print(tk, interval, e)
        time.sleep(3 + 3 * a)
    else: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index(); df = df.rename(columns={df.columns[0]: 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
    t = pd.to_datetime(df.time); t = t.dt.tz_convert('Asia/Kolkata') if t.dt.tz is not None else t.dt.tz_localize('UTC').dt.tz_convert('Asia/Kolkata')
    df['time'] = t.dt.tz_localize(None); return df[['time', 'open', 'high', 'low', 'close', 'volume']].dropna(subset=['close'])
ok = 0
for s in L:
    tk = IDX.get(s, f'{s}.NS')
    for sub, per, iv in (('h1', '730d', '60m'), ('m15', '60d', '15m'), ('m5', '60d', '5m')):
        df = get(tk, per, iv)
        if df is not None: df.to_csv(f'out/{sub}/{s}.csv.gz', index=False, float_format='%.4f', compression='gzip'); ok += 1
        time.sleep(0.4)
print('chunk', k, 'files', ok)
