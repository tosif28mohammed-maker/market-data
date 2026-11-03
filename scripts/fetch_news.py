"""News collector (user, 3 Nov 2026: 'international, national aur share-specific news bhi jodo, hamesha update rehna zaroori').
Google News RSS searches (India edition, English + Hindi) for market-wide topics and every stock in data/news/watch.txt.
Saves new headlines to data/news/YYYY-MM-DD.csv (time_utc, group, query, title, source, link, published) and keeps data/news/latest.md
(newest 15 per group) so the daily answer can read it in one place. Runs twice a day from .github/workflows/news.yml."""
import os, csv, time, html, urllib.parse, urllib.request, datetime as dt, xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(ROOT, 'data', 'news'); os.makedirs(D, exist_ok=True)
MARKET = {
    'India market': ['Sensex Nifty today', 'FII DII flows India equities', 'RBI policy repo rate', 'India inflation GDP data', 'SEBI new rule F&O',
                     'Q2 results today India', 'rupee dollar India', 'शेयर बाज़ार आज सेंसेक्स निफ्टी'],
    'World': ['Wall Street stocks close', 'Federal Reserve interest rates', 'crude oil prices Brent', 'US China trade tariffs', 'Iran Israel US oil Hormuz',
              'Japan Nikkei China stocks', 'US jobs inflation data', 'gold price dollar index'],
}
watch_f = os.path.join(D, 'watch.txt')
WATCH = [l.strip() for l in open(watch_f, encoding='utf-8') if l.strip() and not l.startswith('#')] if os.path.exists(watch_f) else []
def fetch(q, hl='en-IN', gl='IN', ceid='IN:en'):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:2d', 'hl': hl, 'gl': gl, 'ceid': ceid})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (market-data news collector)'})
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=20) as r: root = ET.fromstring(r.read())
            out = []
            for it in root.iter('item'):
                src = it.find('source')
                out.append(dict(title=html.unescape(it.findtext('title', '')), link=it.findtext('link', ''), published=it.findtext('pubDate', ''),
                                source=src.text if src is not None else ''))
            return out
        except Exception as e: print('retry', q, e); time.sleep(3)
    return []
now = dt.datetime.now(dt.timezone.utc); day = (now + dt.timedelta(hours=5, minutes=30)).date()
f = os.path.join(D, f'{day}.csv'); seen = set()
if os.path.exists(f):
    with open(f, encoding='utf-8') as fh: seen = {r['link'] for r in csv.DictReader(fh)}
rows = []
jobs = [(g, q) for g, qs in MARKET.items() for q in qs] + [('Stock: ' + w.split('|')[0].strip(), '"' + w.split('|')[-1].strip() + '"') for w in WATCH]
for g, q in jobs:
    hl, ceid = ('hi', 'IN:hi') if any('ऀ' <= ch <= 'ॿ' for ch in q) else ('en-IN', 'IN:en')
    for it in fetch(q, hl=hl, ceid=ceid)[:20]:
        if it['link'] in seen: continue
        seen.add(it['link']); rows.append(dict(time_utc=now.strftime('%Y-%m-%d %H:%M'), group=g, query=q, **it))
    time.sleep(0.7)
new = not os.path.exists(f)
with open(f, 'a', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=['time_utc', 'group', 'query', 'title', 'source', 'link', 'published'])
    if new: w.writeheader()
    w.writerows(rows)
# latest.md: newest headlines per group from today + yesterday
allr = []
for d in (day - dt.timedelta(days=1), day):
    p = os.path.join(D, f'{d}.csv')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as fh: allr += list(csv.DictReader(fh))
def pub(r):
    try: return dt.datetime.strptime(r['published'], '%a, %d %b %Y %H:%M:%S %Z')
    except Exception: return dt.datetime(2000, 1, 1)
lines = [f'# खबरें — {day} (अपडेट {now:%H:%M} UTC)', '']
for g in list(MARKET) + sorted({r['group'] for r in allr if r['group'].startswith('Stock: ')}):
    rs = sorted([r for r in allr if r['group'] == g], key=pub, reverse=True)
    if not rs: continue
    lines += [f'## {g}'] + [f"- {pub(r):%d %b %H:%M} · {r['title']} ({r['source']})" for r in rs[:15]] + ['']
open(os.path.join(D, 'latest.md'), 'w', encoding='utf-8').write('\n'.join(lines))
print('new headlines', len(rows))
