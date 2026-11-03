"""Weekly: append the last 5 days of 5-minute candles for every liquid A/B stock (paper/gap_universe.csv) to branch 'intraday_hist'
folder intra/m5_all/<SYM>.csv.gz, so a long 5-minute history builds up (Yahoo only serves 60 days). Run on GitHub (archive_5m.yml)."""
import os, sys, time, pandas as pd, yfinance as yf
U = pd.read_csv('paper/gap_universe.csv').symbol.tolist() + ['^NSEI', '^NSEBANK']
OUT = sys.argv[1] if len(sys.argv) > 1 else 'intra/m5_all'; os.makedirs(OUT, exist_ok=True)
for i in range(0, len(U), 100):
    part = U[i:i + 100]
    try: df = yf.download([s if s.startswith('^') else f'{s}.NS' for s in part], period='8d', interval='5m', group_by='ticker', auto_adjust=False, progress=False, threads=True)
    except Exception as e: print(e); continue
    for s in part:
        tk = s if s.startswith('^') else f'{s}.NS'; name = {'^NSEI': 'NIFTY', '^NSEBANK': 'BANKNIFTY'}.get(s, s)
        try: x = df[tk].dropna(subset=['Close']).reset_index()
        except Exception: continue
        x = x.rename(columns={x.columns[0]: 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
        t = pd.to_datetime(x.time); x['time'] = (t.dt.tz_convert('Asia/Kolkata') if t.dt.tz is not None else t).dt.tz_localize(None)
        x = x[['time', 'open', 'high', 'low', 'close', 'volume']]; f = os.path.join(OUT, f'{name}.csv.gz')
        if os.path.exists(f): x = pd.concat([pd.read_csv(f, parse_dates=['time']), x])
        x.drop_duplicates('time', keep='last').sort_values('time').to_csv(f, index=False, float_format='%.4f', compression='gzip')
    time.sleep(2)
print('ok')
