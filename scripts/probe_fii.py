"""One-off probe: which FII/DII data sources are reachable from GitHub Actions (saves raw responses to data/probe/)."""
import os, requests, time
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'probe'); os.makedirs(D, exist_ok=True)
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9'}
s = requests.Session(); s.headers.update(H)
try: s.get('https://www.nseindia.com', timeout=20)
except Exception as e: print('nse home', e)
URLS = {
 'nse_fiidii.json': 'https://www.nseindia.com/api/fiidiiTradeReact',
 'nsdl_daily.html': 'https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx',
 'nsdl_yearwise.html': 'https://www.fpi.nsdl.co.in/web/Reports/Yearwise.aspx?RptType=6',
 'mc_fiidii.html': 'https://www.moneycontrol.com/stocks/marketstats/fii_dii_activity/index.php',
 'mc_fiidii_data.json': 'https://api.moneycontrol.com/mcapi/v1/fii-dii/data?type=cash&period=daily',
 'trendlyne_month.html': 'https://trendlyne.com/macro-data/fii-dii/latest/snapshot-pastmonth/',
 'nse_participant_oi.csv': 'https://archives.nseindia.com/content/nsccl/fao_participant_oi_31102026.csv',
 'nse_participant_vol.csv': 'https://archives.nseindia.com/content/nsccl/fao_participant_vol_31102026.csv',
}
for fn, u in URLS.items():
    try:
        r = s.get(u, timeout=30); open(os.path.join(D, fn), 'wb').write(r.content[:3_000_000]); print(fn, r.status_code, len(r.content))
    except Exception as e: print(fn, 'ERR', e)
    time.sleep(1)
