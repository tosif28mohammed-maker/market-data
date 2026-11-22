"""Shared free-AI client for the robot (Tosif, 22 Nov 2026). Claude = manager; Gemini = reading/facts; Groq = fast sorting.
- Model fallback lists, retry with backoff, stops a provider for the run after repeated 429 (free quota used up).
- Keys only from env (GitHub Secrets); never written to any file. Usage counts -> study/ai/usage.csv."""
import json, os, time, datetime, urllib.request, urllib.error, csv, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USAGE = os.path.join(ROOT, 'study', 'ai', 'usage.csv')
GEMINI_MODELS = ['gemini-3.6-flash', 'gemini-3.8-flash', 'gemini-3.7-flash', 'gemini-3.5-flash', 'gemini-flash-latest', 'gemini-2.5-flash']
GROQ_MODELS = ['openai/gpt-oss-120b', 'llama-3.3-70b-versatile', 'openai/gpt-oss-20b']
_dead = set()   # providers out of quota in this run

def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)

def _log(provider, model, ok, note=''):
    os.makedirs(os.path.dirname(USAGE), exist_ok=True)
    new = not os.path.exists(USAGE)
    with open(USAGE, 'a', newline='') as f:
        w = csv.writer(f)
        if new: w.writerow(['utc', 'provider', 'model', 'ok', 'note'])
        w.writerow([datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M'), provider, model, int(ok), note[:120]])

def _call(provider, models, fn, tries=2):
    """fn(model) -> text. Tries every model, each `tries` times. Returns (text, model) or (None, error)."""
    if provider in _dead: return None, 'quota used up this run'
    last, n429 = '', 0
    for m in models:
        for a in range(tries):
            t0 = time.time()
            try:
                t = fn(m)
                if t and t.strip():
                    print(f'  [{provider} {m}] OK {time.time()-t0:.0f}s', flush=True)
                    _log(provider, m, True, f'{time.time()-t0:.0f}s'); return t, m
                last = 'empty answer'
            except urllib.error.HTTPError as e:
                last = f'HTTP {e.code}'
                if e.code == 429:
                    n429 += 1
                    if n429 >= 4: _dead.add(provider); _log(provider, m, False, 'quota 429 x4 -> stop'); return None, last
                if e.code in (400, 404): break          # model not available / bad input -> next model
            except Exception as e:
                last = str(e)[:120]
            print(f'  [{provider} {m}] fail {time.time()-t0:.0f}s: {last}', flush=True)
            time.sleep(4 * (a + 1))
        _log(provider, m, False, last)
    return None, last

def gemini(prompt, video_url=None, json_out=False, models=None, timeout=300, search=False):
    key = os.environ.get('GEMINI_API_KEY', '')
    parts = []
    if video_url: parts.append({'fileData': {'fileUri': video_url, 'mimeType': 'video/*'}})
    parts.append({'text': prompt})
    body = {'contents': [{'parts': parts}], 'generationConfig': {'temperature': 0.2}}
    if video_url: body['generationConfig']['mediaResolution'] = 'MEDIA_RESOLUTION_LOW'
    if json_out: body['generationConfig']['responseMimeType'] = 'application/json'
    if search: body['tools'] = [{'google_search': {}}]
    def fn(m):
        r = _post(f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}', body, {}, timeout)
        return ''.join(p.get('text', '') for p in r['candidates'][0]['content'].get('parts', []))
    return _call('gemini', models or GEMINI_MODELS, fn)

def groq(prompt, json_out=False, models=None, timeout=120, max_tokens=4000):
    key = os.environ.get('GROQ_API_KEY', '')
    def fn(m):
        body = {'model': m, 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.1, 'max_tokens': max_tokens}
        if json_out: body['response_format'] = {'type': 'json_object'}
        r = _post('https://api.groq.com/openai/v1/chat/completions', body,
                  {'Authorization': f'Bearer {key}', 'User-Agent': 'market-data-bot'}, timeout)
        return r['choices'][0]['message']['content']
    return _call('groq', models or GROQ_MODELS, fn)

def parse_json(txt):
    """Tolerant JSON parse (strips ``` fences)."""
    if not txt: return None
    t = re.sub(r'^```(?:json)?|```$', '', txt.strip(), flags=re.M).strip()
    try: return _one(json.loads(t))
    except Exception:
        m = re.search(r'(\{.*\}|\[.*\])', t, re.S)
        try: return _one(json.loads(m.group(1))) if m else None
        except Exception: return None

def _one(x):
    """Gemini sometimes wraps the object in a list -> take the first dict."""
    if isinstance(x, list) and x and isinstance(x[0], dict) and 'items' not in x[0] and len(x) == 1: return x[0]
    return x
