"""Source collector robot (Tosif, 21 Nov 2026: free GitHub robot does all bulk collecting; Claude only judges).
For every row of study/experts/sources.csv:
  youtube_channel -> https://www.youtube.com/feeds/videos.xml?channel_id=... (new videos) + tries transcript (hi/en) via youtube-transcript-api
  news_rss / blog / govt / podcast / social -> RSS/Atom items (title, link, summary)
New items are keyword pre-filtered (drop motivation / life-story / clickbait; keep numbers, rules, data, policy) and appended to
study/experts/queue.csv (status=new or dropped). Seen ids in study/experts/seen.txt. Source stats in study/experts/source_stats.csv.
Runs from .github/workflows/source_collector.yml 4x/day. No Claude usage."""
import os, re, csv, html, time, json, datetime as dt, urllib.request, xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(ROOT, 'study', 'experts'); TR = os.path.join(E, 'transcripts'); os.makedirs(TR, exist_ok=True)
SRC, Q, SEEN, STATS = (os.path.join(E, f) for f in ('sources.csv', 'queue.csv', 'seen.txt', 'source_stats.csv'))
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) market-data source collector'}
QCOLS = ['added_utc', 'source', 'type', 'item_id', 'title', 'link', 'published', 'score', 'status', 'transcript_file', 'summary']
MAX_TR = int(os.environ.get('MAX_TRANSCRIPTS', '25'))

KEEP = r'(\d+%|\d+ ?(?:dma|ema|sma|rsi|day|din|मिनट|minute|candle)|setup|strategy|stop ?loss|target|entry|exit|breakout|backtest|rule|nifty|bank ?nifty|sensex|' \
       r'rbi|sebi|circular|repo|rate|inflation|cpi|gdp|tariff|export|import|policy|budget|tax|gst|fii|dii|delivery|volume|oi|option|expiry|' \
       r'momentum|value|factor|earnings|results|q[1-4]|margin|crude|gold|silver|copper|dollar|yield|fed|sector|psu|defence|pharma|it |bank|' \
       r'swing|intraday|scalp|vwap|supertrend|fibonacci|support|resistance|trend|screen|filter|anomal|seasonal|study|data|research|framework)'
DROP = r'(motivat|life ?story|journey|struggle|debt|कर्ज|crore se|lakh se|zero to|from \d+ to|millionaire|\brich\b|luxury|car tour|house tour|vlog|' \
       r'podcast with|my story|meri kahani|giveaway|course launch|webinar|join (?:my|our)|telegram|referral|shorts|#shorts|reaction|roast|' \
       r'live stream|livestream|q ?& ?a|\bama\b|celebrat|birthday|wedding|reels|meme|funny|prank|interview with (?:the )?(?:richest|youngest)|' \
       r'analysis for tomorrow|market (?:open|close) live|pre ?market report|post ?market report|black friday|app guide|how to place|' \
       r'invited|launch at|in (?:september|october|november|december) 20|demat account|tax report|ipo: \d+ things|post office|rent(?:ing)? vs)'

def get(url, timeout=25):
    for a in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()
        except Exception as e:
            err = e; time.sleep(2)
    raise err

def clean(s, n=600):
    s = html.unescape(re.sub(r'<[^>]+>', ' ', s or '')); return re.sub(r'\s+', ' ', s).strip()[:n]

def parse_feed(raw):
    root = ET.fromstring(raw); out = []
    ns = {'a': 'http://www.w3.org/2005/Atom', 'yt': 'http://www.youtube.com/xml/schemas/2015', 'm': 'http://search.yahoo.com/mrss/'}
    for it in root.iter('item'):
        out.append(dict(id=it.findtext('guid') or it.findtext('link') or it.findtext('title'), title=clean(it.findtext('title'), 300),
                        link=(it.findtext('link') or '').strip(), published=it.findtext('pubDate') or '', summary=clean(it.findtext('description'))))
    for it in root.iter('{http://www.w3.org/2005/Atom}entry'):
        l = it.find('a:link', ns); vid = it.findtext('yt:videoId', default='', namespaces=ns)
        desc = it.find('.//m:description', ns)
        out.append(dict(id=vid or it.findtext('a:id', default='', namespaces=ns), title=clean(it.findtext('a:title', default='', namespaces=ns), 300),
                        link=l.get('href') if l is not None else '', published=it.findtext('a:published', default='', namespaces=ns),
                        summary=clean(desc.text if desc is not None else it.findtext('a:summary', default='', namespaces=ns)), vid=vid,
                        full=(desc.text or '').split('Download Dhan')[0][:6000] if desc is not None else ''))
    return out

def score(title, summary):
    t = (title + ' ' + summary).lower()
    if re.search(DROP, t): return -1
    pol = 1 if re.search(r'(rbi|sebi|tariff|policy|budget|gst|circular|rate cut|rate hike|\bban\b|duty|subsidy|windfall)', t) else 0
    return len(set(re.findall(KEEP, t))) + pol + (2 if re.search(r'\d', title) else 0)

def transcript(vid):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        tr = api.fetch(vid, languages=['hi', 'en', 'en-IN'])
        txt = ' '.join(s.text for s in tr)
        if len(txt) < 200: return '', 'short'
        fn = os.path.join(TR, f'{vid}.txt'); open(fn, 'w', encoding='utf-8').write(txt)
        return os.path.relpath(fn, ROOT), 'ok'
    except Exception as e:
        return '', type(e).__name__

def fetch_books(srcs):
    """type=book rows: url_or_feed = PDF link. Download once, convert to text (pdftotext) into study/experts/books/. Retries every run until it works."""
    import subprocess
    B = os.path.join(E, 'books'); os.makedirs(B, exist_ok=True); got = []
    for s in srcs:
        if s['type'] != 'book': continue
        name = re.sub(r'[^a-z0-9]+', '_', s['source'].lower()).strip('_')
        txt = os.path.join(B, name + '.txt')
        if os.path.exists(txt): continue
        try:
            raw = get(s['url_or_feed'], timeout=90)
            if not raw.startswith(b'%PDF'): continue
            pdf = '/tmp/' + name + '.pdf'; open(pdf, 'wb').write(raw)
            subprocess.run(['pdftotext', '-layout', pdf, txt], check=True); got.append(s['source'])
        except Exception as e: print('book fail', s['source'], e)
    return got

def main():
    srcs = list(csv.DictReader(open(SRC, encoding='utf-8')))
    seen = set(open(SEEN, encoding='utf-8').read().split('\n')) if os.path.exists(SEEN) else set()
    first_run = not seen
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M')
    rows, stats, tr_done, tr_err = [], [], 0, {}
    books = fetch_books(srcs)
    for s in srcs:
        if s['type'] in ('book', 'off'): continue
        u = s['url_or_feed'].strip()
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={u}' if s['type'] == 'youtube_channel' and not u.startswith('http') else u
        try: items = parse_feed(get(url)); err = ''
        except Exception as e: items, err = [], f'{type(e).__name__}: {str(e)[:80]}'
        new = kept = 0
        for it in items:
            key = f"{s['source']}|{it['id']}"
            if not it['id'] or key in seen: continue
            seen.add(key); new += 1
            sc = score(it['title'], it['summary'])
            st = 'new' if sc >= 2 else 'dropped'
            if first_run and s['type'] != 'youtube_channel': st = 'dropped' if sc < 4 else st   # first run: news backlog -> only strongest
            tf = ''
            if st == 'new' and it.get('vid') and it.get('full'):
                open(os.path.join(TR, f"{it['vid']}.desc.txt"), 'w', encoding='utf-8').write(it['title'] + '\n\n' + it['full'])
            if st == 'new' and it.get('vid') and tr_done < MAX_TR and not s['type'] == 'news_rss':
                tf, why = transcript(it['vid']); tr_done += 1
                if not tf: tr_err[why] = tr_err.get(why, 0) + 1
            kept += st == 'new'
            rows.append(dict(added_utc=now, source=s['source'], type=s['type'], item_id=it['id'][:120], title=it['title'], link=it['link'],
                             published=it['published'], score=sc, status=st, transcript_file=tf, summary=it['summary'][:400]))
        stats.append(dict(run_utc=now, source=s['source'], fetched=len(items), new=new, kept=kept, error=err))
        time.sleep(0.5)
    newf = not os.path.exists(Q)
    with open(Q, 'a', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=QCOLS)
        if newf: w.writeheader()
        w.writerows(rows)
    open(SEEN, 'w', encoding='utf-8').write('\n'.join(sorted(x for x in seen if x)))
    newf = not os.path.exists(STATS)
    with open(STATS, 'a', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=['run_utc', 'source', 'fetched', 'new', 'kept', 'error'])
        if newf: w.writeheader()
        w.writerows(stats)
    ok = sum(1 for r in rows if r['transcript_file'])
    summ = dict(run_utc=now, sources=len(srcs), failed=[x['source'] for x in stats if x['error']], new_items=len(rows),
                kept=sum(r['status'] == 'new' for r in rows), transcripts_ok=ok, transcript_errors=tr_err, books_new=books)
    open(os.path.join(E, 'collector_status.json'), 'w').write(json.dumps(summ, indent=1, ensure_ascii=False))
    print(json.dumps(summ, ensure_ascii=False))

if __name__ == '__main__': main()
