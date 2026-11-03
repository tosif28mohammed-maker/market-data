"""Daily FII/FPI and DII cash-market net buying (NSE provisional) -> data/fii_dii.csv (user, 3 Nov 2026: 'FII bahut paisa laga rahe the - ye signal miss hua').
Columns: date, fii_buy, fii_sell, fii_net, dii_buy, dii_sell, dii_net (Rs crore). Runs in daily.yml after market close."""
import os, requests, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); F = os.path.join(ROOT, 'data', 'fii_dii.csv')
s = requests.Session(); s.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9'})
s.get('https://www.nseindia.com', timeout=20)
j = s.get('https://www.nseindia.com/api/fiidiiTradeReact', timeout=30).json()
row = {}
for x in j:
    k = 'fii' if 'FII' in x['category'] else 'dii'; row['date'] = str(pd.to_datetime(x['date']).date())
    row[f'{k}_buy'], row[f'{k}_sell'], row[f'{k}_net'] = float(x['buyValue']), float(x['sellValue']), float(x['netValue'])
D = pd.read_csv(F) if os.path.exists(F) else pd.DataFrame()
D = pd.concat([D, pd.DataFrame([row])]).drop_duplicates('date', keep='last').sort_values('date'); D.to_csv(F, index=False); print(row)
