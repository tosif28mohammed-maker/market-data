"""Zenodo 10899828: Nifty spot+futures+options 1-MINUTE data 2017-2020 (free, open). G2 data gap (27 Nov 2026).
Robot download -> har option file (strike/CE-PE, mahine ka folder) se har din ki chhoti line:
date, folder, file, strike, cp, o_0915, h, l, c_1515, c_last, rows  -> data/options_hist/nifty_opt_daily_2017_2020.csv.gz
Pehli baar format pata nahi -> data/options_hist/zenodo_structure.txt mein file list + pehli lines likhta hai (Claude dekh kar sudhaare).
"""
import os, re, io, sys, zipfile, urllib.request, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(ROOT, 'data', 'options_hist')
URL = 'https://zenodo.org/records/10899828/files/Nifty%20Options%20Data.zip?download=1'
ZP = '/tmp/nifty_opt.zip'
if not os.path.exists(ZP):
    print('downloading...', flush=True); urllib.request.urlretrieve(URL, ZP)
z = zipfile.ZipFile(ZP); names = [n for n in z.namelist() if not n.endswith('/')]
st = [f'files: {len(names)}', *names[:40]]
def read(n):
    b = z.read(n)
    if n.lower().endswith(('.xlsx', '.xls')): return pd.read_excel(io.BytesIO(b))
    return pd.read_csv(io.BytesIO(b))
for n in names[:3]:
    try: st += ['', f'== {n}', read(n).head(5).to_string()]
    except Exception as e: st += [f'== {n} read fail {e}']
open(os.path.join(OUT, 'zenodo_structure.txt'), 'w').write('\n'.join(st))
rows = []; bad = 0
for n in names:
    m = re.search(r'(\d{4,6})\s*(CE|PE)', os.path.basename(n), re.I)
    if not m: continue
    try: d = read(n)
    except Exception: bad += 1; continue
    cols = {c.lower().strip(): c for c in d.columns}
    g = lambda *k: next((cols[c] for c in cols if any(x in c for x in k)), None)
    dc, tc = g('date'), g('time'); o, h, l, c = g('open'), g('high'), g('low'), g('close')
    if not (dc and o and c): bad += 1; continue
    ts = pd.to_datetime(d[dc].astype(str) + (' ' + d[tc].astype(str) if tc and tc != dc else ''), errors='coerce', dayfirst=True)
    d = d.assign(ts=ts).dropna(subset=['ts']); d['day'] = d.ts.dt.date; d['hm'] = d.ts.dt.strftime('%H:%M')
    for day, x in d.groupby('day'):
        x = x.sort_values('ts'); a1515 = x[x.hm <= '15:15']
        rows.append(dict(date=str(day), folder=os.path.dirname(n), file=os.path.basename(n), strike=int(m.group(1)), cp=m.group(2).upper()[0],
                         o_0915=x[o].iloc[0], h=x[h].max() if h else None, l=x[l].min() if l else None,
                         c_1515=a1515[c].iloc[-1] if len(a1515) else None, c_last=x[c].iloc[-1], rows=len(x)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'nifty_opt_daily_2017_2020.csv.gz'), index=False)
print('option-days', len(rows), 'bad files', bad)
