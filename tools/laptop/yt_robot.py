"""YouTube script robot (Tosif ka laptop) - free.
Kya karta hai:
 1. links.txt (aapke laptop par) + GitHub repo ki study/experts/user_links.txt se video/channel links leta hai
 2. har video ki script (subtitle) nikaalta hai - Hindi/English
 3. scripts/ folder mein .txt save karta hai, done.txt mein yaad rakhta hai (dobara nahi karta)
 4. GitHub token ho to har script repo mein study/experts/transcripts/ mein upload karta hai
Chalana:  python yt_robot.py
"""
import os, re, sys, time, json, base64, random, subprocess
import urllib.request, ssl

def _ctx():
    # 28 Nov: certifi bhi fail ("unable to get local issuer") -> laptop par antivirus/network HTTPS jaanch karta hai,
    # jiska certificate sirf Windows ki list mein hai (isiliye Chrome chalta hai). Hal: Windows ki hi list use karo (truststore).
    for mod in ("truststore", "pip._vendor.truststore"):
        try:
            m = __import__(mod, fromlist=["SSLContext"]); return m.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except Exception: pass
    for mod in ("certifi", "pip._vendor.certifi"):
        try:
            m = __import__(mod, fromlist=["where"]); return ssl.create_default_context(cafile=m.where())
        except Exception: pass
    return ssl.create_default_context()
CTX = _ctx()

REPO = "tosif28mohammed-maker/market-data"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "scripts"); os.makedirs(OUT, exist_ok=True)
DONE = os.path.join(HERE, "done.txt"); FAIL = os.path.join(HERE, "no_subtitle_v2.txt")   # purani no_subtitle.txt ab nahi maani jaati
TOKEN_FILE = os.path.join(HERE, "github_token.txt")
GAP = (25, 40)            # har video ke beech second (YouTube block na kare)
LOOP = "--loop" in sys.argv or os.path.exists(os.path.join(HERE, "loop.txt"))   # office PC: 24 ghante chalta rahe
if LOOP: GAP = (60, 90)   # Tosif 27 Nov: office PC par 1 video/minute bhi chalega - dheere, par block na ho
MAX_PER_RUN = 150         # ek baar mein zyada se zyada
CHANNEL_LAST = 200        # har channel ki aakhri kitni videos

def read_lines(p):
    if not os.path.exists(p): return []
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]

def vid_of(u):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|live/)([A-Za-z0-9_-]{11})", u)
    return m.group(1) if m else None

def channel_videos(url):
    try:
        r = subprocess.run([sys.executable, "-m", "yt_dlp", "--flat-playlist", "--print", "id",
                            "--playlist-end", str(CHANNEL_LAST), url.rstrip("/") + ("" if "/videos" in url or "playlist" in url else "/videos")],
                           capture_output=True, text=True, timeout=300)
        return [x.strip() for x in r.stdout.split() if len(x.strip()) == 11]
    except Exception as e:
        print("  channel list fail:", e); return []

def get_transcript(v):
    from youtube_transcript_api import YouTubeTranscriptApi
    langs = ["hi", "en", "en-IN", "hi-IN"]
    try:                                   # naya version
        api = YouTubeTranscriptApi()
        try: t = api.fetch(v, languages=langs)
        except Exception:
            tl = api.list(v); t = next(iter(tl)).fetch()
        return " ".join(s.text for s in t.snippets)
    except AttributeError:                 # purana version
        try: t = YouTubeTranscriptApi.get_transcript(v, languages=langs)
        except Exception:
            tl = YouTubeTranscriptApi.list_transcripts(v); t = next(iter(tl)).fetch()
        return " ".join(x["text"] for x in t)

def title_of(v):
    try:
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={v}&format=json", timeout=15, context=CTX) as r:
            j = json.load(r); return j.get("title", ""), j.get("author_name", "")
    except Exception: return "", ""

def upload(path, name, token):
    api = f"https://api.github.com/repos/{REPO}/contents/study/experts/transcripts/{name}"
    hdr = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "yt-robot"}
    sha = None
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers=hdr), timeout=30, context=CTX) as r: sha = json.load(r)["sha"]
    except Exception: pass
    body = {"message": f"transcript {name} (laptop robot)", "content": base64.b64encode(open(path, "rb").read()).decode()}
    if sha: body["sha"] = sha
    req = urllib.request.Request(api, data=json.dumps(body).encode(), headers=hdr, method="PUT")
    with urllib.request.urlopen(req, timeout=60, context=CTX) as r: return r.status in (200, 201)

def main():
    links = read_lines(os.path.join(HERE, "links.txt"))
    try:
        with urllib.request.urlopen(f"https://raw.githubusercontent.com/{REPO}/main/study/experts/user_links.txt", timeout=20, context=CTX) as r:
            links += [l.strip() for l in r.read().decode("utf-8", "ignore").splitlines() if "youtu" in l]
    except Exception: print("GitHub ki link list nahi mili (koi baat nahi)")
    done = set(read_lines(DONE)) | set(read_lines(FAIL))
    ids = []
    for u in links:
        v = vid_of(u)
        if v: ids.append(v)
        elif "youtube.com/" in u:
            print("Channel:", u); ids += channel_videos(u)
    ids = [v for v in dict.fromkeys(ids) if v not in done][:MAX_PER_RUN]
    token = open(TOKEN_FILE).read().strip() if os.path.exists(TOKEN_FILE) else ""
    print(f"Baaki videos: {len(ids)}  | GitHub upload: {'HAAN' if token else 'NAHI (token file nahi)'}")
    if token:                               # pehle ki bachi scripts bhi upload karo
        up = os.path.join(HERE, "uploaded.txt"); upd = set(read_lines(up))
        for f in sorted(os.listdir(OUT)):
            if f.endswith(".txt") and f not in upd:
                try:
                    upload(os.path.join(OUT, f), f, token); open(up, "a").write(f + "\n"); print("  upload:", f)
                except Exception as e: print("  upload fail:", f, str(e)[:60])
    ok = 0
    for i, v in enumerate(ids, 1):
        txt = None
        for tries in range(5):                  # net kate to 2 min ruk kar dobara
            try:
                txt = get_transcript(v); break
            except Exception as e:
                err = e; m = str(e)
                if any(k in m for k in ("getaddrinfo", "Max retries", "ConnectionError", "timed out", "NameResolution")):
                    print("  net nahi - 2 minute ruk kar dobara..."); time.sleep(120); continue
                break
        if txt is None:
            e = err
            msg = str(e)[:120]
            if any(k in str(e) for k in ("getaddrinfo", "Max retries", "ConnectionError", "timed out", "NameResolution")):
                print("Net 10 minute se band hai - robot ruk gaya. Net aane par dobara chalaiye. Ab tak:", ok); break
            full = (type(e).__name__ + " " + str(e)).lower()
            open(os.path.join(HERE, "errors_log.txt"), "a", encoding="utf-8").write(f"{v} | {type(e).__name__} | {str(e)[:300]!r}\n")
            if any(k in full for k in ("429", "too many", "block", "sign in to confirm", "captcha")):
                print("YouTube ne thodi der ke liye roka hai - 3-4 ghante baad (ya kal) dobara chalaiye. Ab tak:", ok); break
            print(f"[{i}] {v} subtitle nahi"); open(FAIL, "a").write(v + "\n"); continue
        t, ch = title_of(v)
        p = os.path.join(OUT, f"{v}.txt")
        open(p, "w", encoding="utf-8").write(f"video: https://www.youtube.com/watch?v={v}\ntitle: {t}\nchannel: {ch}\n\n{txt}\n")
        if token:
            try:
                upload(p, f"{v}.txt", token); open(os.path.join(HERE, "uploaded.txt"), "a").write(f"{v}.txt\n")
            except Exception as e: print("  upload fail (agli baar hoga):", str(e)[:80])
        open(DONE, "a").write(v + "\n"); ok += 1
        print(f"[{i}/{len(ids)}] OK {v} {t[:50]}")
        time.sleep(random.uniform(*GAP))
    print("Khatam. Is baar scripts:", ok)

if __name__ == "__main__":
    if not LOOP:
        main()
    else:
        while True:          # har chakkar: GitHub se nayi list, kaam, phir aaram. Block par 3 ghante ruko.
            try: main()
            except Exception as e: print("galti:", str(e)[:150])
            print(time.strftime("%H:%M"), "- agla chakkar 3 ghante baad (window band mat kijiye)"); time.sleep(3 * 3600)
