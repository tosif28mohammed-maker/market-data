"""Macro history downloader (robot): World Bank annual India series + FRED monthly series -> data/macro/*.csv
Run: python scripts/macro_history.py   (no keys needed)"""
import csv, json, os, urllib.request
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'macro'); os.makedirs(OUT, exist_ok=True)
WB = {  # World Bank indicator -> column
    'NY.GDP.MKTP.CN': 'gdp_nominal_inr', 'NY.GDP.MKTP.CD': 'gdp_nominal_usd', 'NY.GDP.MKTP.KD.ZG': 'gdp_real_growth_pct',
    'NY.GDP.DEFL.KD.ZG': 'gdp_deflator_pct', 'FP.CPI.TOTL.ZG': 'cpi_inflation_pct', 'CM.MKT.LCAP.GD.ZS': 'mcap_to_gdp_pct',
    'CM.MKT.LCAP.CD': 'mcap_usd', 'FR.INR.LEND': 'lending_rate_pct', 'NE.GDI.TOTL.ZS': 'gross_capital_formation_pct_gdp',
    'BN.CAB.XOKA.GD.ZS': 'current_account_pct_gdp', 'PA.NUS.FCRF': 'usdinr_avg'}
FRED = {'INDIRLTLT01STM': 'india_10y_gsec_pct', 'INDCPIALLMINMEI': 'india_cpi_index', 'DEXINUS': 'usdinr_daily',
        'INDPROINDMISMEI': 'india_iip_index', 'DGS10': 'us_10y_pct', 'NGDPRNSAXDCINQ': 'india_real_gdp_q_inr'}
import subprocess
def get(u):
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        return urllib.request.urlopen(req, timeout=25).read().decode()
    except Exception:
        return subprocess.run(['curl', '-s', '-f', '-m', '40', '-A', 'Mozilla/5.0', u], capture_output=True, text=True, check=True).stdout
status = {}
rows = {}
for ind, col in WB.items():
    try:
        d = json.loads(get(f'https://api.worldbank.org/v2/country/IND/indicator/{ind}?format=json&per_page=200'))[1] or []
        for x in d:
            if x['value'] is not None: rows.setdefault(int(x['date']), {})[col] = x['value']
        status[col] = len([x for x in d if x['value'] is not None])
    except Exception as e: status[col] = f'fail {e}'
cols = list(WB.values())
with open(f'{OUT}/india_annual_worldbank.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['year'] + cols)
    for y in sorted(rows): w.writerow([y] + [rows[y].get(c, '') for c in cols])
for sid, name in FRED.items():
    try:
        t = get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}')
        open(f'{OUT}/{name}.csv', 'w').write(t); status[name] = t.count('\n') - 1
    except Exception as e: status[name] = f'fail {e}'
json.dump(status, open(f'{OUT}/status.json', 'w'), indent=1)
print(status)
