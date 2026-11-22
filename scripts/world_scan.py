"""World scan robot (Tosif, 22 Nov 2026): Gemini + Google Search looks at the whole world's market talk
(India first, then USA, Japan, Korea, China, Europe, Gulf; and social media: Reddit, X/Twitter, StockTwits,
TradingView ideas, YouTube, Telegram/forums where indexed) and pulls out ONLY concrete testable claims
(setup, entry/exit, stop/target, timing, filters, numbers, sector thesis, policy change with market impact).
No person stories, no profit boasts. Groq then tags each claim: testable? new vs study/ai/known_rules.txt?
Rotates topics so free quota lasts (SCAN_TOPICS per run, default 6).
Outputs: study/experts/world_scan/<date>.md, study/experts/world_claims.csv, study/experts/world_scan/state.json"""
import os, csv, json, sys, hashlib, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_client import gemini, groq, parse_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'study', 'experts', 'world_scan'); os.makedirs(W, exist_ok=True)
CSV = os.path.join(ROOT, 'study', 'experts', 'world_claims.csv'); ST = os.path.join(W, 'state.json')
N = int(os.environ.get('SCAN_TOPICS', '6')); now = dt.datetime.utcnow(); day = now.strftime('%Y-%m-%d')
TOPICS = [
 ('India', 'NSE/BSE Nifty BankNifty swing or intraday trading setups and backtest results discussed this week (Indian traders, blogs, YouTube, Telegram, Twitter/X)'),
 ('India', 'Indian stock market sector rotation, FII/DII flow views, SEBI/RBI/government policy changes this week with stock or sector impact'),
 ('India-social', 'Reddit r/IndianStockMarket r/IndiaInvestments, X/Twitter fintwit India: concrete trading rules or screens people are testing this week'),
 ('USA', 'US stock market quantitative trading studies, backtested rules, seasonality, market breadth or volatility signals published this week (blogs, SSRN, quant newsletters)'),
 ('USA-social', 'Reddit r/algotrading r/stocks, StockTwits, TradingView ideas: backtested strategy results with numbers this week'),
 ('Japan', 'Japan Nikkei TOPIX market trading strategies, BOJ policy and yen impact on stocks this week'),
 ('Korea', 'Korea KOSPI market: value-up program, foreign flows, trading strategy research this week'),
 ('China', 'China Hong Kong stock market policy stimulus, A-share trading patterns, research findings this week'),
 ('Europe', 'European stock market research papers or quant studies on momentum, value, factor timing this week'),
 ('Gulf', 'Gulf GCC stock markets Saudi Tadawul Kuwait Boursa UAE: flows, index changes, oil link, research this week'),
 ('Global-macro', 'Global macro this week: oil, gold, dollar, US yields, Fed — specific numbers and what history says happens next for emerging markets and India'),
 ('Papers', 'New free research papers (SSRN, arXiv q-fin, CFA, central banks) this month on emerging market or India equity anomalies'),
]
st = json.load(open(ST)) if os.path.exists(ST) else {'next': 0}
pick = [(st['next'] + i) % len(TOPICS) for i in range(N)]
known = open(os.path.join(ROOT, 'study', 'ai', 'known_rules.txt'), encoding='utf-8').read()[:4000]
PROMPT = """Google Search se aaj ({day}) is vishay par sabse taaza aur bharosemand cheezein dhoondho: "{q}".
Sirf CONCRETE aur TEST karne layak baatein nikalo: setup, entry/exit, stop/target, samay, filters, numbers, backtest nateeje,
sector thesis, policy badlav jiska share/sector par asar ho. Bolne wale ki life story, kamai ke daave, course/telegram prachar, aam salah (discipline, risk-reward) BILKUL NAHI.
Har baat ke saath asli source link (URL) aur tareekh do. Agar kuch kaam ka nahi mila to items khali chhodo - kuch banao mat.
Sirf JSON: {{"items": [{{"claim": "ek line, numbers ke saath", "category": "setup|timing|filter|sector|policy|macro|paper",
"market": "...", "numbers_given": true/false, "source": "site/channel naam", "url": "...", "date": "YYYY-MM-DD"}}]}}"""
cols = ['date', 'region', 'claim_id', 'claim', 'category', 'market', 'numbers_given', 'source', 'url', 'src_date', 'testable', 'new_or_known', 'status']
rows = list(csv.DictReader(open(CSV, encoding='utf-8'))) if os.path.exists(CSV) else []
have = {r['claim_id'] for r in rows}; md = [f'# World scan {day} (Gemini + Google Search; Groq ने छाँटा)', '']; added = []
for k in pick:
    reg, q = TOPICS[k]
    txt, info = gemini(PROMPT.format(day=day, q=q), search=True)
    js = parse_json(txt) or {}
    its = js.get('items', []) if isinstance(js, dict) else []
    md.append(f'## {reg}: {q[:80]}  ({len(its)} items{"" if txt else ", fail: " + str(info)})')
    for it in its:
        c = (it.get('claim') or '').strip()
        if not c: continue
        cid = 'WS-' + hashlib.md5(c.lower().encode()).hexdigest()[:6].upper()
        if cid in have: continue
        have.add(cid)
        r = dict(date=day, region=reg, claim_id=cid, claim=c, category=it.get('category', ''), market=it.get('market', ''),
                 numbers_given=it.get('numbers_given', ''), source=it.get('source', ''), url=it.get('url', ''), src_date=it.get('date', ''),
                 testable='', new_or_known='', status='new')
        rows.append(r); added.append(r); md.append(f"- {c}  ({r['source']}, {r['src_date']}) {r['url']}")
    md.append('')
if added:   # Groq: quick tagging only (not a fact source)
    txt, info = groq('Har claim ke liye JSON do: n, testable (yes|partly|no: kya purane price/fundamental data par computer se test ho sakta hai), '
                     'new_or_known (known agar neeche ki known list jaisa ho). Output {"items":[...]}\nKNOWN:\n' + known + '\nCLAIMS:\n' +
                     '\n'.join(f'{i}: {r["claim"][:220]}' for i, r in enumerate(added)), json_out=True)
    for it in ((parse_json(txt) or {}).get('items', []) if txt else []):
        try: added[int(it['n'])].update(testable=it.get('testable', ''), new_or_known=it.get('new_or_known', ''))
        except Exception: pass
with open(CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore'); w.writeheader(); w.writerows(rows)
p = os.path.join(W, f'{day}.md'); old = open(p, encoding='utf-8').read() + '\n' if os.path.exists(p) else ''
open(p, 'w', encoding='utf-8').write(old + '\n'.join(md) + '\n')
st['next'] = (st['next'] + N) % len(TOPICS); st['last'] = now.strftime('%Y-%m-%d %H:%M'); st['added_last'] = len(added)
json.dump(st, open(ST, 'w'), indent=1)
print(f'world scan: topics {[TOPICS[k][0] for k in pick]}, new claims {len(added)}')
