"""Historical NSE archives for the 'world techniques' study (user 6 Nov 2026).
Usage: python scripts/fetch_nse_hist.py mto <year>   -> nse_hist/deliv/<year>.csv.gz   (date,symbol,qty,deliv_qty,deliv_pct) EQ only
       python scripts/fetch_nse_hist.py fo <year>    -> nse_hist/fo/<year>.csv.gz      per symbol per day:
            fut_close (near month), fut_oi (all expiries), ce_oi, pe_oi  (stock + index)
Weekdays are tried; holidays just 404. Polite delay. Never needs credentials.
"""
import os, sys, io, time, zipfile, datetime as dt, requests, pandas as pd
kind, year = sys.argv[1], int(sys.argv[2])
OUT = os.environ.get('OUTDIR', 'nse_hist'); os.makedirs(f'{OUT}/{"deliv" if kind == "mto" else "fo"}', exist_ok=True)
S = requests.Session()
S.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
                  'Accept': '*/*', 'Referer': 'https://www.nseindia.com/'})
try: S.get('https://www.nseindia.com', timeout=20)
except Exception: pass


def get(url):
    for a in range(3):
        try:
            r = S.get(url, timeout=40)
            if r.status_code == 200 and len(r.content) > 200: return r.content
            if r.status_code == 404: return None
        except Exception:
            pass
        time.sleep(2 + 3 * a)
    return None


days = [d for d in pd.bdate_range(f'{year}-01-01', min(pd.Timestamp(f'{year}-12-31'), pd.Timestamp.today()))]
frames = []; ok = 0
for d in days:
    if kind == 'mto':
        b = get(f'https://nsearchives.nseindia.com/archives/equities/mto/MTO_{d:%d%m%Y}.DAT')
        if not b: continue
        rows = []
        for line in b.decode(errors='ignore').splitlines():
            p = line.split(',')
            if len(p) >= 7 and p[0].strip() == '20' and p[3].strip() in ('EQ', 'BE', 'BZ', 'SM'):
                try: rows.append((d.date(), p[2].strip(), p[3].strip(), float(p[4]), float(p[5]), float(p[6])))
                except ValueError: pass
        if rows:
            frames.append(pd.DataFrame(rows, columns=['date', 'symbol', 'series', 'qty', 'deliv_qty', 'deliv_pct'])); ok += 1
    else:
        new = d >= pd.Timestamp('2024-07-08')
        mon = d.strftime('%b').upper()
        url = (f'https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip' if new else
               f'https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{d.year}/{mon}/fo{d:%d}{mon}{d.year}bhav.csv.zip')
        b = get(url)
        if not b: continue
        try:
            z = zipfile.ZipFile(io.BytesIO(b)); x = pd.read_csv(z.open(z.namelist()[0]))
        except Exception:
            continue
        if new:
            x = x.rename(columns={'FinInstrmTp': 'INSTRUMENT', 'TckrSymb': 'SYMBOL', 'XpryDt': 'EXPIRY_DT', 'OptnTp': 'OPTION_TYP',
                                  'ClsPric': 'CLOSE', 'OpnIntrst': 'OPEN_INT'})
            x['INSTRUMENT'] = x.INSTRUMENT.map({'STF': 'FUTSTK', 'IDF': 'FUTIDX', 'STO': 'OPTSTK', 'IDO': 'OPTIDX'})
        x.columns = [c.strip() for c in x.columns]
        x['EXP'] = pd.to_datetime(x.EXPIRY_DT, errors='coerce', dayfirst=not new)
        fut = x[x.INSTRUMENT.isin(['FUTSTK', 'FUTIDX'])]
        near = fut.sort_values('EXP').groupby('SYMBOL').first()
        f_oi = fut.groupby('SYMBOL').OPEN_INT.sum()
        opt = x[x.INSTRUMENT.isin(['OPTSTK', 'OPTIDX'])]
        ce = opt[opt.OPTION_TYP.astype(str).str.upper().str.startswith('C')].groupby('SYMBOL').OPEN_INT.sum()
        pe = opt[opt.OPTION_TYP.astype(str).str.upper().str.startswith('P')].groupby('SYMBOL').OPEN_INT.sum()
        g = pd.DataFrame({'fut_close': near.CLOSE, 'fut_oi': f_oi, 'ce_oi': ce, 'pe_oi': pe}).dropna(subset=['fut_close'])
        g['date'] = d.date(); g.index.name = 'symbol'
        frames.append(g.reset_index()); ok += 1
    time.sleep(0.4)
    if ok and ok % 50 == 0: print(kind, year, d.date(), ok, flush=True)
print(kind, year, 'days ok', ok, 'of', len(days))
if frames:
    pd.concat(frames).to_csv(f'{OUT}/{"deliv" if kind == "mto" else "fo"}/{year}.csv.gz', index=False)
