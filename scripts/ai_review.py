"""Send study/ai/review_prompt.md to Gemini (pro first) and Groq (gpt-oss-120b) for an independent critique.
Writes study/ai/review_<tag>_gemini.md and _groq.md (never the keys). Tag = first line of the prompt after 'TAG:'."""
import json, os, urllib.request, time, datetime
P = open('study/ai/review_prompt.md').read()
tag = next((l.split('TAG:')[1].strip() for l in P.splitlines() if l.startswith('TAG:')), datetime.date.today().isoformat())
def post(url, body, headers, to=300):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=to) as r: return json.load(r)
gk = os.environ.get('GEMINI_API_KEY', ''); out = []
for m in ['gemini-3.1-pro-preview', 'gemini-2.5-pro', 'gemini-pro-latest', 'gemini-3.6-flash', 'gemini-2.5-flash']:
    try:
        r = post(f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gk}', {'contents': [{'parts': [{'text': P}]}]}, {})
        txt = ''.join(p.get('text', '') for p in r['candidates'][0]['content']['parts'])
        open(f'study/ai/review_{tag}_gemini.md', 'w').write(f'# Gemini ({m})\n\n{txt}\n'); out.append(f'gemini OK {m}'); break
    except Exception as e:
        out.append(f'gemini {m} fail {str(e)[:120]}'); time.sleep(5)
qk = os.environ.get('GROQ_API_KEY', '')
for m in ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile']:
    try:
        r = post('https://api.groq.com/openai/v1/chat/completions', {'model': m, 'messages': [{'role': 'user', 'content': P}], 'max_tokens': 6000},
                 {'Authorization': f'Bearer {qk}', 'User-Agent': 'market-data-bot'})
        open(f'study/ai/review_{tag}_groq.md', 'w').write(f'# Groq ({m})\n\n{r["choices"][0]["message"]["content"]}\n'); out.append(f'groq OK {m}'); break
    except Exception as e:
        out.append(f'groq {m} fail {str(e)[:160]}'); time.sleep(5)
open(f'study/ai/review_{tag}_status.txt', 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
