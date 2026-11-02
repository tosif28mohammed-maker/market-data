"""After the close: today's 5-minute candles for the gap universe (liquidity A/B, paper/gap_universe.csv); keeps only stocks whose
open gapped 1.5%+ from the previous day's last 5-min close -> data/gapday/<date>.csv.gz (+ data/gapday/<date>_gaps.csv list).
Optional: python scripts/gapday.py DIR_WITH_5M_FILES   (backfill from saved 5-minute history instead of Yahoo)."""
import os, sys, time, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data', 'gapday'); os.makedirs(OUT, exist_ok=True)
U = pd.read_csv(os.path.join(ROOT, 'paper', 'gap_universe.csv'))
def frames_from_yahoo():
    import yfinance as yf
    syms = U.symbol.tolist(); out = {}
    for i in range(0, len(syms), 100):
        part = syms[i:i + 100]
        try: df = yf.download([f'{s}.NS' for s in part], period='5d', interval='5m', group_by='ticker', auto_adjust=False, progress=False, threads=True)
        except Exception as e: print(e); continue
        for s in part:
            try: x = df[f'{s}.NS'].dropna(subset=['Close']).reset_index()
            except Exception: continue
            x = x.rename(columns={x.columns[0]: 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close'})
            t = pd.to_datetime(x.time); x['time'] = (t.dt.tz_convert('Asia/Kolkata') if t.dt.tz is not None else t).dt.tz_localize(None)
            out[s] = x[['time', 'open', 'high', 'low', 'close']]
        time.sleep(2)
    return out
def frames_from_dir(D):
    out = {}
    for s in U.symbol:
        f = os.path.join(D, f'{s}.csv.gz')
        if os.path.exists(f): out[s] = pd.read_csv(f, parse_dates=['time'])[['time', 'open', 'high', 'low', 'close']]
    return out
F = frames_from_dir(sys.argv[1]) if len(sys.argv) > 1 else frames_from_yahoo()
by_day = {}
for s, x in F.items():
    x = x[(x.time.dt.time >= pd.Timestamp('09:15').time()) & (x.time.dt.time <= pd.Timestamp('15:25').time())].copy(); x['day'] = x.time.dt.normalize()
    days = sorted(x.day.unique())
    for a, b in zip(days[:-1], days[1:]):
        prev = x[x.day == a]; cur = x[x.day == b]
        if len(cur) < 60 or cur.time.iloc[0].strftime('%H:%M') != '09:15': continue
        gap = cur.open.iloc[0] / prev.close.iloc[-1] - 1
        if abs(gap) >= 0.015: by_day.setdefault(pd.Timestamp(b), []).append((s, gap, cur.drop(columns='day').assign(symbol=s, prev_close=prev.close.iloc[-1])))
for day, items in by_day.items():
    f = os.path.join(OUT, f'{day.date()}.csv.gz')
    if os.path.exists(f) and len(sys.argv) == 1: continue
    pd.concat([z for _, _, z in items]).to_csv(f, index=False, float_format='%.4f', compression='gzip')
    pd.DataFrame([(s, round(g * 100, 2)) for s, g, _ in items], columns=['symbol', 'gap_pct']).sort_values('gap_pct').to_csv(os.path.join(OUT, f'{day.date()}_gaps.csv'), index=False)
print('days', len(by_day))
