"""Groq news sorter (Tosif, 22 Nov 2026). Groq = fast sorting only, NOT a fact source (it once called Nifty a BSE index).
Reads today's data/news/<date>.csv headlines (fetch_news.py), Groq tags each: market-relevant?, stock/sector, direction,
strength, real-news vs rumour/opinion/clickbait. Only BIG + stock-specific items with 'check' flag go to Gemini + Google Search
for a fact check (double check only where it matters).
Writes data/news/sorted_<date>.csv and data/news/sorted.md (what moved / what to watch)."""
import os, csv, json, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_client import groq, gemini, parse_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
N = os.path.join(ROOT, 'data', 'news')
today = dt.datetime.utcnow().strftime('%Y-%m-%d')
src = os.path.join(N, f'{today}.csv')
if not os.path.exists(src):
    cands = sorted(f for f in os.listdir(N) if f[:4].isdigit() and f.endswith('.csv'))
    src = os.path.join(N, cands[-1]); today = cands[-1][:10]
rows = list(csv.DictReader(open(src, encoding='utf-8')))
seen, items = set(), []
for r in rows:
    t = r['title'].strip()
    if t.lower() in seen: continue
    seen.add(t.lower()); items.append(r)

PROMPT = """Neeche Indian share market ke liye khabron ki headlines hain (number: headline). Har ek ke liye JSON do.
Sirf headline ke shabdon se tay karo, apni taraf se fact mat jodo.
fields: n, relevant (true agar Indian shares/index/sector/commodity/rates par asar ho sakta hai), stocks (NSE symbol agar saaf naam ho, warna ""),
sector, direction (positive|negative|mixed|none), strength (1-5; 5 = bada order/results surprise/policy badlav/fraud),
kind (fact|rumour|opinion|clickbait|old_news), check (true agar strength>=4 aur stock-specific ho aur sach hone par shak ho).
Output: {"items": [ ... ]}
"""
out = []
for i in range(0, len(items), 40):
    batch = items[i:i + 40]
    txt, info = groq(PROMPT + '\n'.join(f'{i + j}: {b["title"]}' for j, b in enumerate(batch)), json_out=True)
    js = parse_json(txt) or {}
    for it in js.get('items', []):
        try: k = int(it.get('n'))
        except Exception: continue
        if 0 <= k < len(items):
            b = items[k]
            out.append(dict(n=k, group=b.get('group', ''), title=b['title'], link=b.get('link', ''), published=b.get('published', ''),
                            relevant=it.get('relevant'), stocks=it.get('stocks', ''), sector=it.get('sector', ''),
                            direction=it.get('direction', ''), strength=it.get('strength', 0), kind=it.get('kind', ''),
                            check=it.get('check'), fact_check=''))
# double check only the big, doubtful, stock-specific ones (max 8/day) with Gemini + Google Search
big = [o for o in out if o['check'] and str(o['relevant']).lower() == 'true' and o['stocks']][:8]
for o in big:
    t, info = gemini(f"Is khabar ko Google Search se jaancho (aaj {today}). Headline: \"{o['title']}\". "
                     "Ek line me jawab: SACH / AFWAH / PURANI / PATA NAHI + chhota kaaran + source naam. Andaza mat lagao.", search=True)
    o['fact_check'] = (t or f'check fail: {info}').strip().replace('\n', ' ')[:300]

cols = ['n', 'group', 'title', 'link', 'published', 'relevant', 'stocks', 'sector', 'direction', 'strength', 'kind', 'check', 'fact_check']
with open(os.path.join(N, f'sorted_{today}.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)

def s(o):
    try: return int(o['strength'])
    except Exception: return 0
rel = [o for o in out if str(o['relevant']).lower() == 'true' and o['kind'] in ('fact', 'old_news') and s(o) >= 3]
rel.sort(key=s, reverse=True)
md = [f'# छँटी हुई खबरें — {today} (Groq ने छाँटी, बड़ी शक वाली Gemini+Google से जाँची)', '',
      f'कुल headlines {len(items)}, छँटी {len(out)}, काम की (ताकत ≥3, fact) {len(rel)}, अफ़वाह/राय/clickbait {sum(o["kind"] in ("rumour","opinion","clickbait") for o in out)}', '']
for o in rel[:40]:
    md.append(f"- [{o['strength']}/{o['direction']}] {o['stocks'] or o['sector']}: {o['title'][:160]}" + (f"  \n  जाँच: {o['fact_check']}" if o['fact_check'] else ''))
open(os.path.join(N, 'sorted.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print(f'news sorted {len(out)}/{len(items)}, useful {len(rel)}, fact-checked {len(big)}')
if items and not out: sys.exit(1)
