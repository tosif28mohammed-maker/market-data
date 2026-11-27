"""Gemini reader robot (Tosif, 22 Nov 2026).
Gemini WATCHES YouTube videos itself (no transcript scraping -> GitHub IP block no longer matters) and READS books,
and pulls out ONLY usable trading rules point-by-point (setup, timing, entry, exit, stop, which shares/index).
No life story, no 'X se Y crore' claims, no generic advice. Already-known rules are skipped (study/ai/known_rules.txt + earlier rules).

Order of work each run:
 1) study/experts/user_links.txt  (links Tosif sends in chat; Claude appends them) - always first
 1b) study/experts/transcripts/<id>.txt full word-for-word transcripts from Tosif's laptop robot (27 Nov) - read as TEXT,
     same PROMPT rules; if Gemini already watched that video, the note gets a '_tr' twin so both can be compared
 2) BOOKS FIRST (Tosif 22 Nov): books/*.txt in books/order.txt order, ~150k-char chunks, up to MAX_BOOK_CHUNKS per run
 3) YouTube queue videos ONLY after every book is fully read
Outputs:
  study/experts/gemini/<id>.md       full point-by-point notes per video/book chunk
  study/experts/rules_ai.csv         one row per extracted rule (testable?, new?, duplicate_of)
  study/experts/test_queue.csv       new + testable rules waiting for a Python test (numbers only from code)
  study/experts/gemini/done.txt, book_progress.json, reader_status.json
"""
import os, csv, json, re, glob, hashlib, datetime as dt, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_client import gemini, parse_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(ROOT, 'study', 'experts'); G = os.path.join(E, 'gemini'); os.makedirs(G, exist_ok=True)
DONE, BOOKP, STATUS = os.path.join(G, 'done.txt'), os.path.join(G, 'book_progress.json'), os.path.join(G, 'reader_status.json')
RULES, TQ, LINKS = os.path.join(E, 'rules_ai.csv'), os.path.join(E, 'test_queue.csv'), os.path.join(E, 'user_links.txt')
MAX_VIDEOS = int(os.environ.get('MAX_VIDEOS', '12'))
MAX_BOOK_CHUNKS = int(os.environ.get('MAX_BOOK_CHUNKS', '1'))
MAX_TRANSCRIPTS = int(os.environ.get('MAX_TRANSCRIPTS', '8'))
TR_DONE = os.path.join(G, 'transcripts_done.txt')
CHUNK = 150_000
RCOLS = ['rule_id', 'date', 'source', 'link', 'title', 'rule', 'type', 'market', 'timeframe', 'entry', 'exit', 'stop',
         'conditions', 'testable', 'data_needed', 'new_or_known', 'duplicate_of', 'gemini_confidence']
now = dt.datetime.utcnow()

def read_csv(p): return list(csv.DictReader(open(p, encoding='utf-8'))) if os.path.exists(p) else []

def known_text():
    k = open(os.path.join(ROOT, 'study', 'ai', 'known_rules.txt'), encoding='utf-8').read()
    prev = [f"{r['rule_id']}: {r['rule'][:110]}" for r in read_csv(RULES)][-200:]
    return k + ('\nPehle nikale gaye niyam (inko dobara mat likho, duplicate_of me id do):\n' + '\n'.join(prev) if prev else '')

PROMPT = """Tum ek share-market research assistant ho. Ek Indian trader (Tosif) ke liye is {kind} ko SHURU SE AAKHIR TAK dhyan se padho/dekho.
Sirf wahi niyam/tarike nikalo jo ek computer program purane data par TEST kar sake ya trading me seedhe kaam aayein:
setup ki pehchaan, samay (kaun sa din/ghanta/mahina), entry, exit, stop-loss, target, kaun se share/index/expiry, filters (volume, delivery, DMA, VIX, FII), position size.
BILKUL MAT LIKHO: bolne wale ki life story, kitna kamaya/karz ('X se Y crore'), unka background, course/telegram/app ka prachar,
aur aam salah jo sab dete hain (discipline, emotions, 1:2 risk-reward, diversify, long term).
Har niyam ko point-by-point, numbers ke saath likho (jaise '20 EMA ke upar 3 din close', 'subah 9:15-9:30 ke high ke upar entry').
Agar bolne wala koi number nahi deta to woh bhi likho ('number nahi diya') - andaza mat lagao.
Neeche jo niyam pehle se jaanche ja chuke hain, unhe dobara mat likho; agar unka koi NAYA twist hai to new_or_known='twist' aur duplicate_of me purana naam.

{known}

Sirf JSON do, is roop me:
{{"title": "...", "useful": true/false, "why_not_useful": "...",
  "detailed_notes": ["har ek kaam ki baat ek alag point, poori detail me", ...],
  "rules": [{{"rule": "ek line me poora niyam", "type": "swing|intraday|options|positional|investing|macro|other",
             "market": "Nifty/BankNifty/stocks/sector/...", "timeframe": "...", "entry": "...", "exit": "...", "stop": "...",
             "conditions": "filters/shartein", "testable": "yes|partly|no", "data_needed": "daily OHLC / 5-min / options chain / fundamentals / news ...",
             "new_or_known": "new|twist|known", "duplicate_of": "", "confidence": "high|medium|low (video me kitna saaf bataya)"}}]}}
"""

def save_rules(src, link, title, js, done_ids):
    rows = read_csv(RULES); tq = read_csv(TQ)
    n0 = len(rows); added = []
    for r in (js.get('rules') or []):
        txt = (r.get('rule') or '').strip()
        if not txt: continue
        rid = 'AI-' + hashlib.md5(txt.lower().encode()).hexdigest()[:6].upper()
        if any(x['rule_id'] == rid for x in rows): continue
        row = dict(rule_id=rid, date=now.strftime('%Y-%m-%d'), source=src, link=link, title=title[:120], rule=txt,
                   type=r.get('type', ''), market=r.get('market', ''), timeframe=r.get('timeframe', ''), entry=r.get('entry', ''),
                   exit=r.get('exit', ''), stop=r.get('stop', ''), conditions=r.get('conditions', ''), testable=r.get('testable', ''),
                   data_needed=r.get('data_needed', ''), new_or_known=r.get('new_or_known', ''), duplicate_of=r.get('duplicate_of', ''),
                   gemini_confidence=r.get('confidence', ''))
        rows.append(row); added.append(row)
        if row['testable'] in ('yes', 'partly') and row['new_or_known'] in ('new', 'twist'):
            tq.append(dict(rule_id=rid, added=row['date'], rule=txt, data_needed=row['data_needed'], status='waiting', result='', link=link))
    for p, data, cols in ((RULES, rows, RCOLS), (TQ, tq, ['rule_id', 'added', 'rule', 'data_needed', 'status', 'result', 'link'])):
        with open(p, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(data)
    return added

def write_note(item_id, src, link, title, js):
    lines = [f"# {js.get('title') or title}", f"स्रोत: {src} · {link} · Gemini ने पढ़ा {now:%Y-%m-%d %H:%M} UTC", '']
    if not js.get('useful', True): lines += [f"**काम का नहीं:** {js.get('why_not_useful', '')}", '']
    lines += ['## Point-by-point'] + [f'- {p}' for p in (js.get('detailed_notes') or [])] + ['', '## Niyam']
    for r in js.get('rules') or []:
        lines.append(f"- [{r.get('new_or_known','')}/{r.get('testable','')}] {r.get('rule','')} | entry: {r.get('entry','')} | exit: {r.get('exit','')} | stop: {r.get('stop','')}")
    open(os.path.join(G, f'{item_id}.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

def yt_id(url):
    m = re.search(r'(?:v=|youtu\.be/|shorts/|live/)([\w-]{11})', url); return m.group(1) if m else None

def main():
    done = set(open(DONE).read().split()) if os.path.exists(DONE) else set()
    known = known_text(); stat = dict(run_utc=now.strftime('%Y-%m-%d %H:%M'), videos_ok=0, videos_fail=[], rules_added=0, book_chunks=0, stopped='')
    import time, ai_client; T0 = time.time(); BUDGET = int(os.environ.get('TIME_BUDGET_MIN', '45')) * 60
    # ORDER (Tosif 22 Nov 2026): BOOKS FIRST. YouTube only after every book is fully read (Tosif's own links still go first).
    # 1) Tosif's own links
    todo_user, todo_q = [], []
    if os.path.exists(LINKS):
        for l in open(LINKS, encoding='utf-8').read().split():
            vid = yt_id(l)
            if vid and vid not in done: todo_user.append(('Tosif link', vid, f'https://www.youtube.com/watch?v={vid}', ''))
    q = [r for r in read_csv(os.path.join(E, 'queue.csv')) if r['type'] == 'youtube_channel' and r['status'] in ('new', 'read') and r['item_id'] not in done]
    q.sort(key=lambda r: (int(r['score'] or 0), r['published']), reverse=True)
    todo_q = [(r['source'], r['item_id'], f"https://www.youtube.com/watch?v={r['item_id']}", r['title']) for r in q]
    def do_videos(lst, cap):
        n = 0
        for src, vid, url, title in lst:
            if n >= cap or stat['stopped'] or time.time() - T0 > BUDGET: break
            print(f'video {vid} ({src}): {title[:70]}', flush=True)
            txt, info = gemini(PROMPT.format(kind='YouTube video', known=known), video_url=url, json_out=True)
            js = parse_json(txt) if txt else None
            if isinstance(js, list): js = {'rules': [r for r in js if isinstance(r, dict)]}
            if not js:
                stat['videos_fail'].append(f'{vid}: {info if not txt else "bad json"}')
                if info == 'quota used up this run': stat['stopped'] = 'Gemini free quota khatam - agle run me'
                continue
            write_note(vid, src, url, title, js); added = save_rules(src, url, js.get('title') or title, js, done)
            stat['videos_ok'] += 1; stat['rules_added'] += len(added); done.add(vid); n += 1
            open(DONE, 'a').write(vid + '\n')
    do_videos(todo_user, MAX_VIDEOS)
    # 1b) Tosif's laptop transcripts (full text, nothing summarised) - before books (user material first)
    trd = set(open(TR_DONE).read().split()) if os.path.exists(TR_DONE) else set()
    trs = [f for f in sorted(glob.glob(os.path.join(E, 'transcripts', '*.txt'))) if not f.endswith('.desc.txt')
           and os.path.basename(f)[:-4] not in trd]
    stat['transcripts_ok'] = 0
    for f in trs:
        if stat['transcripts_ok'] >= MAX_TRANSCRIPTS or stat['stopped'] or time.time() - T0 > BUDGET: break
        vid = os.path.basename(f)[:-4]; body = open(f, encoding='utf-8', errors='ignore').read()
        head = dict(l.split(': ', 1) for l in body.splitlines()[:3] if ': ' in l)
        url = head.get('video', f'https://www.youtube.com/watch?v={vid}'); title = head.get('title', '')
        src = 'transcript: ' + (head.get('channel') or 'Tosif laptop')
        print(f'transcript {vid}: {title[:70]}', flush=True)
        txt, info = gemini(PROMPT.format(kind='YouTube video ki POORI shabd-ba-shabd transcript (auto-caption, numbers galat ho sakte hain - shak ho to "(transcript galat ho sakti hai)" likho)', known=known)
                           + '\n\n---- TRANSCRIPT ----\n' + body[:CHUNK], json_out=True)
        js = parse_json(txt) if txt else None
        if isinstance(js, list): js = {'rules': [r for r in js if isinstance(r, dict)]}
        if not js:
            stat['videos_fail'].append(f'transcript {vid}: {info if not txt else "bad json"}')
            if info == 'quota used up this run': stat['stopped'] = 'Gemini free quota khatam - agle run me'
            continue
        note_id = vid + '_tr' if os.path.exists(os.path.join(G, vid + '.md')) else vid
        write_note(note_id, src, url, title, js); stat['rules_added'] += len(save_rules(src, url, js.get('title') or title, js, done))
        stat['transcripts_ok'] += 1; trd.add(vid); open(TR_DONE, 'a').write(vid + '\n'); done.add(vid)
        if vid not in open(DONE).read().split() if os.path.exists(DONE) else True: open(DONE, 'a').write(vid + '\n')
        time.sleep(15)
    stat['transcripts_left'] = len(trs) - stat['transcripts_ok']
    # 2) books: finish a started book first, then the next one in books/order.txt (mix: study reports, classics, papers)
    prog = json.load(open(BOOKP)) if os.path.exists(BOOKP) else {}
    files = {os.path.basename(b): b for b in glob.glob(os.path.join(E, 'books', '*.txt'))}
    order = [l.strip() for l in open(os.path.join(E, 'books', 'order.txt'), encoding='utf-8')] if os.path.exists(os.path.join(E, 'books', 'order.txt')) else []
    order = [n for n in order if n in files] + sorted(n for n in files if n not in order)
    lens = {n: os.path.getsize(files[n]) for n in order}
    def left(n): return prog.get(n, 0) < len(open(files[n], encoding='utf-8', errors='ignore').read())
    pending = [n for n in order if left(n)]
    pending.sort(key=lambda n: 0 if prog.get(n, 0) > 0 else 1)          # started book first (stable -> order.txt otherwise)
    retried = False
    for name in pending:
        while stat['book_chunks'] < MAX_BOOK_CHUNKS and time.time() - T0 < BUDGET:
            text = open(files[name], encoding='utf-8', errors='ignore').read(); off = prog.get(name, 0)
            if off >= len(text): break
            part = text[off:off + CHUNK]
            txt, info = gemini(PROMPT.format(kind='kitaab/report ka hissa', known=known) + '\n\n---- TEXT ----\n' + part, json_out=True)
            js = parse_json(txt) if txt else None
            if not js and info == 'quota used up this run' and not retried:
                # often a per-MINUTE token limit, not the daily one -> wait once and try again
                retried = True; ai_client._dead.discard('gemini'); print('quota 429 - 75s ruk kar dobara', flush=True); time.sleep(75); continue
            if not js:
                stat['videos_fail'].append(f'book {name}@{off}: {info if not txt else "bad json"}')
                if info == 'quota used up this run': stat['stopped'] = 'Gemini free quota khatam - agle run me'
                break
            cid = f"book_{name[:-4]}_{off // CHUNK:03d}"
            write_note(cid, 'book: ' + name, name, name, js); stat['rules_added'] += len(save_rules('book: ' + name, name, name, js, done))
            prog[name] = off + CHUNK; stat['book_chunks'] += 1
            json.dump(prog, open(BOOKP, 'w'), indent=1)
            time.sleep(20)                                                      # spread tokens (per-minute limit)
        if stat['stopped'] or stat['book_chunks'] >= MAX_BOOK_CHUNKS or time.time() - T0 > BUDGET: break
    stat['books_left'] = sum(1 for n in order if left(n))
    stat['book_chars_left'] = sum(max(0, lens[n] - prog.get(n, 0)) for n in order)
    # 3) YouTube queue ONLY when no book is left
    if stat['books_left'] == 0 and not stat['stopped']: do_videos(todo_q, MAX_VIDEOS)
    todo = todo_user + todo_q
    stat['videos_left'] = max(0, len(todo) - stat['videos_ok'])
    json.dump(stat, open(STATUS, 'w'), indent=1, ensure_ascii=False); print(json.dumps(stat, ensure_ascii=False, indent=1))
    # fail exit only if NOTHING worked and it was not just quota -> workflow retries once
    if stat['videos_ok'] == 0 and stat['book_chunks'] == 0 and todo and not stat['stopped']: sys.exit(1)

if __name__ == '__main__':
    main()
