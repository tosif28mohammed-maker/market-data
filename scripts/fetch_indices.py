"""niftyindices.com history (user 6 Nov 2026 world-techniques study): Nifty 50 PE/PB/DY, total-return indices of
factor indices + G-sec. Output data/indices/<name>.csv. Yearly chunks (site limits ranges). No credentials.
Note: factor indices before their launch dates are NSE back-calculated (back-test) data — said in the study.
"""
import os, json, time, datetime as dt, requests, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'data', 'indices'); os.makedirs(OUT, exist_ok=True)
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                  'Content-Type': 'application/json; charset=UTF-8', 'Accept': 'application/json, text/javascript, */*; q=0.01',
                  'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://www.niftyindices.com',
                  'Referer': 'https://www.niftyindices.com/reports/historical-data'})
try: S.get('https://www.niftyindices.com/reports/historical-data', timeout=30)
except Exception as e: print('home', e)


def call(ep, name, a, b):
    body = {'cinfo': json.dumps({'name': name, 'startDate': a.strftime('%d-%b-%Y'), 'endDate': b.strftime('%d-%b-%Y'), 'indexName': name}).replace('"', "'")}
    for k in range(3):
        try:
            r = S.post(f'https://www.niftyindices.com/Backpage.aspx/{ep}', data=json.dumps(body), timeout=60)
            d = r.json().get('d'); return json.loads(d) if isinstance(d, str) else (d or [])
        except Exception as e:
            print('retry', ep, name, a.year, e); time.sleep(3 + 3 * k)
    return []


def hist(ep, name, start=1999):
    rows = []
    for y in range(start, dt.date.today().year + 1):
        rows += call(ep, name, dt.date(y, 1, 1), min(dt.date(y, 12, 31), dt.date.today())); time.sleep(0.6)
    return pd.DataFrame(rows)


def save(df, fname, datecol_guess=('HistoricalDate', 'Date', 'DATE', 'INDEX_DATE')):
    if df.empty: print('EMPTY', fname); return
    dc = next((c for c in datecol_guess if c in df.columns), df.columns[0])
    df['date'] = pd.to_datetime(df[dc], errors='coerce', dayfirst=True)
    df = df.dropna(subset=['date']).drop_duplicates('date').sort_values('date')
    df.to_csv(os.path.join(OUT, fname), index=False); print(fname, len(df), df.date.min().date(), df.date.max().date(), list(df.columns)[:8])


save(hist('getpepbHistoricaldataDBtoString', 'NIFTY 50'), 'NIFTY50_PE.csv')
save(hist('getpepbHistoricaldataDBtoString', 'NIFTY 500', 2005), 'NIFTY500_PE.csv')
TRI = ['NIFTY 50', 'NIFTY 500', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250', 'NIFTY ALPHA LOW-VOLATILITY 30', 'NIFTY100 LOW VOLATILITY 30',
       'NIFTY200 MOMENTUM 30', 'NIFTY200 QUALITY 30', 'NIFTY200 VALUE 30', 'NIFTY50 VALUE 20', 'NIFTY ALPHA 50', 'NIFTY QUALITY LOW-VOLATILITY 30',
       'NIFTY 10 YR BENCHMARK G-SEC', 'NIFTY 1D RATE INDEX']
for n in TRI:
    df = hist('getTotalReturnIndexString', n, 1999)
    if df.empty: df = hist('getHistoricaldatatabletoString', n, 1999)
    save(df, n.replace(' ', '_').replace('-', '_') + '_TRI.csv')
