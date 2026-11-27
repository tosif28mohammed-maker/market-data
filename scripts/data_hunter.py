"""Data hunter (Tosif 27 Nov 2026: 'data ki kami par kaam roko mat - source dhoondho, doosre AI se bhi poochho').
Har khule gap (study/ai/data_gaps.csv, status=open) ke liye:
  Gemini + Google Search -> free/legal source (URL, kitne saal, timeframe, format, login/API key chahiye?, script se download ho sakta?)
  Groq -> doosri raay (bina search; sirf idea, verify Gemini/Claude karega)
Output: study/ai/data_hunt.md (naya upar). Claude padh kar robot fetcher banata hai ya Tosif se key/login maangta hai.
"""
import os, csv, json, datetime as dt, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_client import gemini, groq
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAPS = os.path.join(ROOT, 'study', 'ai', 'data_gaps.csv'); OUT = os.path.join(ROOT, 'study', 'ai', 'data_hunt.md')
Q = """Indian stock market research project (Python backtests, GitHub Actions robot, no money for paid data).
DATA NEEDED: {data}
WHY: {why}
ALREADY KNOWN SOURCES (verify they still work, then find MORE): {known}
Find the best FREE and LEGAL sources. NSE website scraping is NOT allowed (NSE terms) - prefer Kaggle, Zenodo, GitHub, Google Drive datasets,
broker APIs with free accounts (Angel SmartAPI, Dhan, Upstox, Fyers, ICICI Breeze, Zerodha needs paid), BSE, NSDL/CDSL, RBI, Yahoo, Stooq, Investing etc.
For EACH source give: name, exact URL, period covered (from-to), timeframe/granularity, instruments, format, size, login/API key needed (yes/no, free?),
can a Python script on GitHub Actions download it (yes/no + how), licence/terms, reliability notes. Then rank the top 3 and say exactly what to do first.
Only real URLs you found in search results - if unsure, say 'not verified'."""
def main():
    gaps = [g for g in csv.DictReader(open(GAPS, encoding='utf-8')) if g['status'] == 'open']
    only = os.environ.get('GAP', '')
    if only: gaps = [g for g in gaps if g['gap_id'] in only.split()]
    out = [f"# Data hunt {dt.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n"]
    for g in gaps[:int(os.environ.get('MAX_GAPS', '7'))]:
        q = Q.format(data=g['data'], why=g['why_needed'], known=g['known_sources'])
        gt, gi = gemini(q, search=True)
        rt, ri = groq(q[:6000])
        out += [f"## {g['gap_id']}: {g['data']}", "### Gemini (Google search ke saath)", gt or f'(nahi mila: {gi})',
                "### Groq (doosri raay, bina search - verify karna)", rt or f'(nahi mila: {ri})', '']
        print(g['gap_id'], 'gemini', bool(gt), 'groq', bool(rt), flush=True)
    old = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
    open(OUT, 'w', encoding='utf-8').write('\n'.join(out) + '\n\n---\n' + old[:200000])
if __name__ == '__main__':
    main()
