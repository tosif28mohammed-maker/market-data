"""Run on Tosif's PC (his home/office IP is not blocked by YouTube like cloud/GitHub IPs).
Reads the public queue.csv from GitHub, fetches FULL transcripts (hi/en, word by word, not summaries) for YouTube items that have none yet,
writes them to ./yt_transcripts/<video_id>.txt next to this script's working folder. The cloud Claude session then stages these files and pushes them to the repo.
Gentle on YouTube: waits GAP seconds (+ random 0-4s) between videos, stops after 3 IpBlocked/RequestBlocked in a row.
Usage: py pc_transcripts.py [max_videos=30] [gap_seconds=8]"""
import os, sys, csv, io, time, random, urllib.request
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 30
GAP = float(sys.argv[2]) if len(sys.argv) > 2 else 8
OUT = os.path.join(os.getcwd(), 'yt_transcripts'); os.makedirs(OUT, exist_ok=True)
Q = 'https://raw.githubusercontent.com/tosif28mohammed-maker/market-data/main/study/experts/queue.csv'
rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(Q, timeout=60).read().decode('utf-8'))))
vids = [r['item_id'] for r in rows if r['type'] == 'youtube_channel' and r['status'] in ('new', 'read') and not r.get('transcript_file')]
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi(); ok = fail = blocked_run = 0; stopped = ''
for v in vids:
    if ok >= MAX: break
    f = os.path.join(OUT, v + '.txt')
    if os.path.exists(f): continue
    try:
        tr = api.fetch(v, languages=['hi', 'en', 'en-IN'])
        open(f, 'w', encoding='utf-8').write('\n'.join(f"[{int(s.start)//60}:{int(s.start)%60:02d}] {s.text}" for s in tr)); ok += 1; blocked_run = 0
        print('ok', v, flush=True)
    except KeyboardInterrupt:
        stopped = ' (Ctrl+C)'; break
    except Exception as e:
        fail += 1; name = type(e).__name__; print('fail', v, name, flush=True)
        if 'Blocked' in name:
            blocked_run += 1
            if blocked_run >= 3:
                stopped = ' (YouTube ne IP block kiya - 6-12 ghante baad dobara chalayein)'; break
        else:
            blocked_run = 0
    time.sleep(GAP + random.uniform(0, 4))
print(f'ok={ok} fail={fail} pending_total={len(vids)} folder={OUT}{stopped}')
