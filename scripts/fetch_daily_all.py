"""Fresh daily OHLCV (2 years) for every A/B stock in paper/gap_universe.csv -> data/daily_all/{open,high,low,close,volume}.csv.gz (wide tables).
Used by the on-demand scanners (scan.yml). Data: Yahoo via yfinance."""
import os, time, pandas as pd, yfinance as yf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, 'data', 'daily_all'); os.makedirs(D, exist_ok=True)
syms = list(pd.read_csv(os.path.join(ROOT, 'paper', 'gap_universe.csv')).symbol)
out = {k: {} for k in ['Open', 'High', 'Low', 'Close', 'Volume']}
for i in range(0, len(syms), 100):
    part = syms[i:i + 100]
    for a in range(3):
        try: df = yf.download([f'{s}.NS' for s in part], period='2y', interval='1d', auto_adjust=False, progress=False, threads=True, group_by='ticker'); break
        except Exception as e: print(e); time.sleep(5); df = None
    if df is None: continue
    for s in part:
        try: x = df[f'{s}.NS'].dropna(subset=['Close'])
        except Exception: continue
        x.index = pd.to_datetime(x.index).tz_localize(None).normalize()
        for k in out: out[k][s] = x[k]
    time.sleep(1)
for k, v in out.items(): pd.DataFrame(v).sort_index().round(3).to_csv(os.path.join(D, f'{k.lower()}.csv.gz'), compression='gzip')
print('stocks', len(out['Close']))
