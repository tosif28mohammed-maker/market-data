"""Quick check that the free AI keys (Gemini, Groq) work. Writes only OK/FAIL, never the keys."""
import json, os, urllib.request, datetime

def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.load(r)

out = [f"AI key test {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC"]
Q = "Nifty 50 kya hai? Ek line me Hindi me jawab do."

# Gemini: pick a free Flash model from the live model list
gk = os.environ.get("GEMINI_API_KEY", "")
try:
    models = get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gk}")["models"]
    names = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
    flash = [n for n in names if "flash" in n and "lite" not in n and "image" not in n and "tts" not in n and "live" not in n]
    out.append("Gemini models (generateContent): " + ", ".join(n.split('/')[-1] for n in names[:40]))
    ok = False
    for m in sorted(flash, reverse=True)[:5]:
        try:
            r = post(f"https://generativelanguage.googleapis.com/v1beta/{m}:generateContent?key={gk}",
                     {"contents": [{"parts": [{"text": Q}]}]}, {})
            txt = r["candidates"][0]["content"]["parts"][0]["text"].strip()
            out.append(f"GEMINI OK via {m.split('/')[-1]}: {txt[:200]}")
            ok = True
            break
        except Exception as e:
            out.append(f"Gemini {m.split('/')[-1]} failed: {str(e)[:150]}")
    if not ok:
        out.append("GEMINI FAIL")
except Exception as e:
    out.append(f"GEMINI FAIL: {str(e)[:200]}")

# Groq
qk = os.environ.get("GROQ_API_KEY", "")
for model in ["openai/gpt-oss-120b", "llama-3.3-70b-versatile"]:
    try:
        r = post("https://api.groq.com/openai/v1/chat/completions",
                 {"model": model, "messages": [{"role": "user", "content": Q}]},
                 {"Authorization": f"Bearer {qk}", "User-Agent": "market-data-bot"})
        out.append(f"GROQ OK via {model}: {r['choices'][0]['message']['content'].strip()[:200]}")
        break
    except Exception as e:
        out.append(f"GROQ {model} failed: {str(e)[:200]}")

os.makedirs("study/ai", exist_ok=True)
open("study/ai/keytest.txt", "w").write("\n".join(out) + "\n")
print("\n".join(out))
