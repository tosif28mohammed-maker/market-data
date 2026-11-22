"""Book finder robot (Tosif, 22 Nov 2026): "pehle books padhao, har tarike ki" — YouTube later.
Finds FREE + LEGAL long texts and saves them as study/experts/books/<name>.txt for gemini_reader.py:
 1) Project Gutenberg (public domain, via gutendex.com): old trading/speculation/investing classics
    (Wyckoff, Selden, Hamilton/Dow theory, tape reading, Livermore-era books...)
 2) arXiv q-fin papers (open access): Indian market studies (Nifty, NSE, F&O, momentum, intraday, FII...) + general backtest papers
 3) books/wishlist.csv: official free reports (SEBI/NSE/RBI studies etc.). If a row has no direct PDF url, Gemini + Google Search
    is asked (max 3 per run) to find the official PDF link; robot downloads it.
Then rewrites books/order.txt as a MIX (report, classic, paper, report, ...) so every kind gets read, not one kind only.
Status -> study/experts/books/finder_status.json. Copyrighted paid books are NOT downloaded (only public domain / open access / official free).
"""
import os, re, csv, json, time, subprocess, urllib.request, urllib.parse, datetime as dt, sys, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, 'study', 'experts', 'books'); os.makedirs(B, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (market-data study bot)'}
MAX_GUT, MAX_ARX = int(os.environ.get('MAX_GUT', '25')), int(os.environ.get('MAX_ARX', '30'))
stat = dict(run_utc=dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M'), gutenberg_new=[], arxiv_new=[], wishlist_new=[], fails=[])

def get(url, timeout=60):
    err = None
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()
        except Exception as e: err = e; time.sleep(3 * (a + 1))
    raise err

def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')[:70]

def pdf_to_txt(raw, out):
    tmp = '/tmp/bf.pdf'; open(tmp, 'wb').write(raw)
    subprocess.run(['pdftotext', '-layout', tmp, out], check=True, timeout=180)
    return os.path.getsize(out) > 5000

# ---------- 1) Gutenberg (public domain) ----------
GUT_SEARCH = ['stock market', 'speculation', 'stock exchange', 'tape reading', 'wyckoff', 'investment', 'wall street',
              'commodity', 'panic', 'financial crises', 'money market', 'gold silver', 'dow theory', 'trading', 'securities']
GUT_OK = re.compile(r'stock|specul|invest|wall street|exchange|securit|financ|panic|crises|money|bank|gold|silver|commod|tape|market|wealth|trade|bond|cotton|wheat', re.I)
def gutenberg():
    have = len([f for f in os.listdir(B) if f.startswith('gut_')])
    for q in GUT_SEARCH:
        if have >= MAX_GUT: break
        try: js = json.loads(get('https://gutendex.com/books?languages=en&copyright=false&search=' + urllib.parse.quote(q)))
        except Exception as e: stat['fails'].append(f'gutendex {q}: {e}'); continue
        for b in js.get('results', [])[:10]:
            subj = ' '.join(b.get('subjects', []) + b.get('bookshelves', []))
            if not GUT_OK.search(subj) or re.search(r'fiction|poetry|juvenile|drama', subj, re.I): continue
            name = f"gut_{b['id']}_{slug(b['title'])[:50]}.txt"; out = os.path.join(B, name)
            if os.path.exists(out): continue
            url = next((u for k, u in b['formats'].items() if k.startswith('text/plain') and not u.endswith('.zip')), None)
            if not url: continue
            try:
                t = get(url).decode('utf-8', 'ignore')
                m = re.search(r'\*\*\* ?START OF.*?\*\*\*', t); n = re.search(r'\*\*\* ?END OF', t)
                t = t[m.end() if m else 0: n.start() if n else len(t)]
                if len(t) < 20000: continue
                head = f"{b['title']} — {', '.join(a['name'] for a in b.get('authors', []))} (Project Gutenberg #{b['id']}, public domain)\n\n"
                open(out, 'w', encoding='utf-8').write(head + t); stat['gutenberg_new'].append(b['title'][:80]); have += 1
            except Exception as e: stat['fails'].append(f"gut {b['id']}: {e}")
            if have >= MAX_GUT: break
        time.sleep(2)

# ---------- 2) arXiv (open access papers) ----------
ARX_Q = ['all:"Indian stock market"', 'all:Nifty', 'all:"National Stock Exchange" AND all:India', 'all:"India" AND all:momentum AND cat:q-fin*',
         'all:"Indian" AND all:options AND cat:q-fin*', 'all:"Bank Nifty"', 'all:"India" AND all:intraday AND cat:q-fin*',
         'all:"foreign institutional" AND all:India', 'cat:q-fin.TR AND all:backtest', 'cat:q-fin.TR AND all:seasonality',
         'cat:q-fin.PM AND all:"emerging market"', 'all:gold AND all:"price prediction" AND cat:q-fin*']
def arxiv():
    have = len([f for f in os.listdir(B) if f.startswith('arx_')])
    for q in ARX_Q:
        if have >= MAX_ARX: break
        url = 'http://export.arxiv.org/api/query?' + urllib.parse.urlencode({'search_query': q, 'start': 0, 'max_results': 6, 'sortBy': 'relevance'})
        try: root = ET.fromstring(get(url))
        except Exception as e: stat['fails'].append(f'arxiv {q}: {e}'); continue
        ns = {'a': 'http://www.w3.org/2005/Atom'}
        for en in root.findall('a:entry', ns):
            aid = en.find('a:id', ns).text.rsplit('/', 1)[-1]; title = ' '.join(en.find('a:title', ns).text.split())
            name = f"arx_{slug(aid)}_{slug(title)[:45]}.txt"; out = os.path.join(B, name)
            if os.path.exists(out) or any(f.startswith(f'arx_{slug(aid)}') for f in os.listdir(B)): continue
            try:
                if pdf_to_txt(get(f'https://arxiv.org/pdf/{aid}', 90), out):
                    t = open(out, encoding='utf-8', errors='ignore').read()
                    open(out, 'w', encoding='utf-8').write(f'{title} (arXiv {aid}, open access paper)\n\n' + t)
                    stat['arxiv_new'].append(title[:80]); have += 1
                elif os.path.exists(out): os.remove(out)
            except Exception as e: stat['fails'].append(f'arxiv pdf {aid}: {e}')
            time.sleep(3)                                  # arXiv asks for polite pacing
            if have >= MAX_ARX: break
        time.sleep(3)

# ---------- 3) wishlist: official free reports ----------
WL = os.path.join(B, 'wishlist.csv'); WCOLS = ['name', 'title', 'url', 'status', 'note']
def wishlist():
    if not os.path.exists(WL): return
    rows = list(csv.DictReader(open(WL, encoding='utf-8'))); asked = 0
    for r in rows:
        out = os.path.join(B, f"wl_{slug(r['name'])}.txt")
        if os.path.exists(out): r['status'] = 'downloaded'; continue
        if not r.get('url') and asked < 3 and r.get('status') != 'not_found':
            asked += 1
            try:
                from ai_client import gemini
                txt, _ = gemini(f"Find the OFFICIAL, free, direct PDF download URL (ending in .pdf if possible) for: {r['title']}. "
                                 "Only official sites (sebi.gov.in, nseindia.com, rbi.org.in, bseindia.com, the author's institution). "
                                 "Answer ONLY the URL, or NONE.", search=True, timeout=120)
                u = (re.findall(r'https?://\S+', txt or '') or [''])[0].rstrip(').,]')
                if u: r['url'] = u
                else: r['status'] = 'not_found'
            except Exception as e: stat['fails'].append(f"wl search {r['name']}: {e}")
        if r.get('url'):
            try:
                raw = get(r['url'], 120)
                if raw.startswith(b'%PDF') and pdf_to_txt(raw, out):
                    t = open(out, encoding='utf-8', errors='ignore').read()
                    open(out, 'w', encoding='utf-8').write(f"{r['title']} (official free report)\n\n" + t)
                    r['status'] = 'downloaded'; stat['wishlist_new'].append(r['name'])
                else: r['status'] = 'bad_link'; r['url'] = ''
            except Exception as e: r['status'] = 'download_fail'; r['note'] = str(e)[:80]; stat['fails'].append(f"wl {r['name']}: {e}")
    w = csv.DictWriter(open(WL, 'w', newline='', encoding='utf-8'), fieldnames=WCOLS); w.writeheader()
    for r in rows: w.writerow({k: r.get(k, '') for k in WCOLS})

def write_order():
    """Mix kinds: official/India reports first in each round, then a classic, then a paper, then a Motilal study."""
    fs = sorted(f for f in os.listdir(B) if f.endswith('.txt'))
    kinds = [[f for f in fs if f.startswith('wl_')], [f for f in fs if f.startswith('gut_')],
             [f for f in fs if f.startswith('arx_')], [f for f in fs if f.startswith('motilal')],
             [f for f in fs if not f.startswith(('wl_', 'gut_', 'arx_', 'motilal'))]]
    order = []
    while any(kinds):
        for k in kinds:
            if k: order.append(k.pop(0))
    open(os.path.join(B, 'order.txt'), 'w', encoding='utf-8').write('\n'.join(order) + '\n')
    stat['books_total'] = len(order)

if __name__ == '__main__':
    for step in (wishlist, gutenberg, arxiv):
        try: step()
        except Exception as e: stat['fails'].append(f'{step.__name__}: {e}')
    write_order()
    json.dump(stat, open(os.path.join(B, 'finder_status.json'), 'w'), indent=1, ensure_ascii=False)
    print(json.dumps(stat, indent=1, ensure_ascii=False))
