"""NSE daily index file (ind_close_all_DDMMYYYY.csv) -> P/E, P/B, Div Yield of ALL NSE indices, every trading day.
Resumable: data/indices/index_valuation.csv (date,index,close,pe,pb,dy) + data/indices/pe_missing.txt (404 dates).
Run repeatedly (robot); each run stops after MAX_MIN minutes. Earliest file on NSE ~2012-2015 (older = 404)."""
import csv, datetime as dt, os, subprocess, time
D = os.path.join(os.path.dirname(__file__), '..', 'data', 'indices'); os.makedirs(D, exist_ok=True)
OUT, MISS = f'{D}/index_valuation.csv', f'{D}/pe_missing.txt'
MAX_MIN = float(os.environ.get('MAX_MIN', '35'))
have = set()
if os.path.exists(OUT):
    for r in csv.DictReader(open(OUT)): have.add(r['date'])
miss = set(open(MISS).read().split()) if os.path.exists(MISS) else set()
new = not os.path.exists(OUT)
f = open(OUT, 'a', newline=''); w = csv.writer(f)
if new: w.writerow(['date', 'index', 'close', 'pe', 'pb', 'dy'])
mf = open(MISS, 'a')
t0 = time.time(); got = 0; fails = 0
day = dt.date.today()
start = dt.date(2010, 1, 1)
today = dt.date.today()
while day >= start and time.time() - t0 < MAX_MIN * 60:
    ds = day.isoformat()
    if day.weekday() < 5 and ds not in have and not (ds in miss and (today - day).days > 7):
        u = f'https://nsearchives.nseindia.com/content/indices/ind_close_all_{day:%d%m%Y}.csv'
        r = subprocess.run(['curl', '-s', '-m', '25', '-A', 'Mozilla/5.0', '-w', '\n%{http_code}', u], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition('\n')
        if code == '200' and 'Index Name' in body[:200]:
            for row in csv.DictReader(body.splitlines()):
                k = {x.strip(): v for x, v in row.items() if x}
                pe, pb, dy = k.get('P/E', ''), k.get('P/B', ''), k.get('Div Yield', '')
                if pe in ('', '-') and pb in ('', '-'): continue
                w.writerow([ds, k.get('Index Name', '').strip(), k.get('Closing Index Value', ''), pe, pb, dy])
            got += 1; f.flush()
        elif code == '404':
            if ds not in miss: mf.write(ds + '\n'); miss.add(ds)
        else:
            fails += 1
            if fails > 30: print('too many fails (blocked?)', code); break
        time.sleep(0.3)
    day -= dt.timedelta(days=1)
print(f'got {got} days, fails {fails}, total days {len(have)+got}, missing {len(miss)}')
