"""Add new symbols on request: python scripts/add_symbols.py "IRCTC, ZYDUSLIFE, BANKNIFTY"
Each NSE code becomes CODE.NS on Yahoo (indices via INDEX_MAP). Checks Yahoo has data, saves to symbols_extra.txt,
downloads the FULL daily history (data/CODE.csv) and 60 days of 5-minute candles. Daily/intraday robots then keep them updated."""
import os, sys, time, pandas as pd, yfinance as yf
from fetch_list import TICKERS, INDEX_MAP
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); EX = os.path.join(ROOT, 'symbols_extra.txt')
names = [x.strip().upper().replace(' ', '') for x in ' '.join(sys.argv[1:]).replace(';', ',').split(',') if x.strip()]
added, failed = [], []
for n in names:
    tk = TICKERS.get(n) or INDEX_MAP.get(n) or (n if n.startswith('^') or '.' in n else f'{n}.NS')
    name = n.replace('^', '').replace('.NS', '').replace('.BO', '')
    df = None
    for t in ([tk] if tk.startswith('^') or not tk.endswith('.NS') else [tk, tk[:-3] + '.BO']):
        try:
            df = yf.download(t, period='max', interval='1d', auto_adjust=False, progress=False, threads=False)
        except Exception as e:
            print(n, t, e)
        if df is not None and len(df): tk = t; break
    if df is None or not len(df): failed.append(n); continue
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df = df.reset_index().rename(columns={'Date':'date','Open':'open','High':'high','Low':'low','Close':'close','Adj Close':'adj','Volume':'volume'})
    df = df[['date','open','high','low','close','adj','volume']].dropna(subset=['close']); df['date'] = pd.to_datetime(df.date).dt.tz_localize(None).dt.normalize()
    df.drop_duplicates('date', keep='last').sort_values('date').to_csv(os.path.join(ROOT, 'data', f'{name}.csv'), index=False, float_format='%.4f')
    try:
        x = yf.download(tk, period='60d', interval='5m', auto_adjust=False, progress=False, threads=False)
        if x is not None and len(x):
            if isinstance(x.columns, pd.MultiIndex): x.columns = x.columns.get_level_values(0)
            x = x.reset_index().rename(columns={'Datetime':'time','Open':'open','High':'high','Low':'low','Close':'close','Volume':'volume'})
            x['time'] = pd.to_datetime(x.time).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None)
            os.makedirs(os.path.join(ROOT, 'data', 'intraday'), exist_ok=True)
            x[['time','open','high','low','close','volume']].to_csv(os.path.join(ROOT, 'data', 'intraday', f'{name}_5m.csv'), index=False, float_format='%.4f')
    except Exception as e: print(n, 'intraday', e)
    lines = open(EX).read().splitlines() if os.path.exists(EX) else ['# NAME,YAHOO_TICKER (added on request)']
    if not any(l.split(',')[0] == name for l in lines): lines.append(f'{name},{tk}')
    open(EX, 'w').write('\n'.join(lines) + '\n')
    added.append(f'{name} ({tk}) {df.date.min().date()} -> {df.date.max().date()}, {len(df)} days'); time.sleep(1)
msg = f'added: {added}; failed: {failed}'
print(msg); open(os.path.join(ROOT, 'data', 'ADD_STATUS.txt'), 'w').write(msg + '\n')
