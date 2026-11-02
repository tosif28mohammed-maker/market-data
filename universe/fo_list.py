"""NSE F&O stock list (lot sizes) -> universe/fo_list.csv"""
import requests, io, pandas as pd
H = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*', 'Referer': 'https://www.nseindia.com/'}
for url in ['https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv', 'https://archives.nseindia.com/content/fo/fo_mktlots.csv']:
    try:
        r = requests.get(url, headers=H, timeout=30); r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text)); df.columns = [c.strip() for c in df.columns]
        df = df.apply(lambda c: c.str.strip() if c.dtype == object else c)
        df.to_csv('universe/fo_list.csv', index=False); print(len(df)); break
    except Exception as e: print(url, e)
