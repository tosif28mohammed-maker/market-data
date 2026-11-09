"""Daily 'what did we miss' review (user 9 Nov 2026): top 20 gainers + top 20 losers (A/B shares, never D) of the day.
For each: (1) did our robot have it yesterday (decision score, 200 DMA, 20d high, RSI2, volume build-up, 4H/1H zone)?
(2) was there a known date (results / board meeting / dividend / bonus)? (3) news: did our news files have it BEFORE 9:15,
and what does Google News say today (cause + source)? (4) sector or whole market move?
-> verdict 'pehle pata chal sakta tha?' + lesson. Writes data/movers/<date>.md, appends data/movers/log.csv,
keeps data/movers/summary.md (running %: caught / cause / sources we lacked) and data/movers/follow.txt (names for news robot).
Study only."""
import os, re, csv, glob, time, html, urllib.parse, urllib.request, datetime as dt, xml.etree.ElementTree as ET
import numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(R, 'data', 'movers'); os.makedirs(D, exist_ok=True)
rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C, H, L_, V = rd('close.csv.gz'), rd('high.csv.gz'), rd('low.csv.gz') if os.path.exists(os.path.join(R, 'data', 'daily_all', 'low.csv.gz')) else None, rd('volume.csv.gz')
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
AV = set(open(os.path.join(R, 'paper', 'avoid_liquidity_D.txt')).read().split())
AB = [s for s in C.columns if liq.get(s) in ('A', 'B') and s not in AV]
c = C[AB].ffill(limit=3); day = c.index[-1].date()
ret = (c.iloc[-1] / c.iloc[-2] - 1) * 100
ret = ret[c.iloc[-1].notna() & c.iloc[-2].notna() & (V[AB].iloc[-1] > 0)]
up, dn = ret.nlargest(20), ret.nsmallest(20)
I = pd.read_csv(os.path.join(R, 'data', 'fund', 'info.csv')).set_index('symbol')
ind = I.industry.reindex(ret.index); ind_med = ret.groupby(ind).median()
nf = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
nret = (nf.iloc[-1] / nf.iloc[-2] - 1) * 100 if nf.index[-1].date() == day else np.nan

# ---- company names (NSE equity list, cached) ----
NP = os.path.join(R, 'data', 'fund', 'names.csv')
if not os.path.exists(NP) or (time.time() - os.path.getmtime(NP)) > 30 * 86400:
    try:
        import requests, io
        r = requests.get('https://archives.nseindia.com/content/equities/EQUITY_L.csv', headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        n = pd.read_csv(io.StringIO(r.text)); n.columns = [x.strip() for x in n.columns]
        n[['SYMBOL', 'NAME OF COMPANY']].rename(columns={'SYMBOL': 'symbol', 'NAME OF COMPANY': 'company'}).to_csv(NP, index=False)
    except Exception as e: print('names', e)
NAME = pd.read_csv(NP).set_index('symbol').company.to_dict() if os.path.exists(NP) else {}
def short(s):
    n = NAME.get(s, s)
    n = re.sub(r'\b(Limited|Ltd\.?|India|Industries|Corporation|Company|Co\.)\b', '', n, flags=re.I).strip(' .,&-')
    return n if len(n) >= 3 else s

# ---- what our robot knew yesterday (state as of the previous close; decision.csv is still yesterday's when this runs) ----
dec = pd.read_csv(os.path.join(R, 'data', 'decision.csv')).set_index('symbol') if os.path.exists(os.path.join(R, 'data', 'decision.csv')) else pd.DataFrame()
tfz = pd.read_csv(os.path.join(R, 'data', 'tf_zone.csv')) if os.path.exists(os.path.join(R, 'data', 'tf_zone.csv')) else pd.DataFrame()
TFZ = set(tfz[tfz.get('in_zone', False) == True].symbol) if len(tfz) else set()
p = c.iloc[:-1]  # up to yesterday
a200 = p.rolling(200, min_periods=150).mean().iloc[-1]; hi20 = p.iloc[-21:-1].max(); last = p.iloc[-1]
d1 = p.diff()
def rsi2(s):
    g = d1[s].clip(lower=0).ewm(alpha=0.5).mean().iloc[-1]; l = (-d1[s].clip(upper=0)).ewm(alpha=0.5).mean().iloc[-1]
    return 100 - 100 / (1 + g / l) if l > 0 else 100
vv = V[AB].iloc[:-1]; vspike = vv.iloc[-5:].mean() / vv.iloc[-55:-5].mean()
BM = pd.read_csv(os.path.join(R, 'data', 'corp', 'board_meetings.csv')) if os.path.exists(os.path.join(R, 'data', 'corp', 'board_meetings.csv')) else pd.DataFrame(columns=['symbol', 'date', 'purpose'])
BM['d'] = pd.to_datetime(BM.date, errors='coerce', dayfirst=True).dt.date
ACT = pd.read_csv(os.path.join(R, 'data', 'corp', 'actions_all.csv')) if os.path.exists(os.path.join(R, 'data', 'corp', 'actions_all.csv')) else pd.DataFrame(columns=['symbol', 'subject', 'ex_date'])
ACT['d'] = pd.to_datetime(ACT.ex_date, errors='coerce', dayfirst=True).dt.date

# ---- news we already had (all our news files, last 4 days) ----
NEWS = []
for f in sorted(glob.glob(os.path.join(R, 'data', 'news', '20*.csv')))[-4:]:
    try: NEWS += list(csv.DictReader(open(f, encoding='utf-8')))
    except Exception: pass
def pub(x):
    try: return dt.datetime.strptime(x, '%a, %d %b %Y %H:%M:%S %Z')
    except Exception: return None
OPEN_UTC = dt.datetime.combine(day, dt.time(3, 45))  # 9:15 IST
def our_news(s):
    key = [k for k in {s.lower(), short(s).lower()} if len(k) >= 4]
    hits = [r for r in NEWS if any(k in r['title'].lower() for k in key)]
    before = [r for r in hits if (pub(r['published']) or OPEN_UTC) < OPEN_UTC]
    return hits, before

def gnews(q):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': f'"{q}" when:2d', 'hl': 'en-IN', 'gl': 'IN', 'ceid': 'IN:en'})
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20) as r: root = ET.fromstring(r.read())
        return [dict(title=html.unescape(i.findtext('title', '')), source=(i.find('source').text if i.find('source') is not None else ''),
                     published=i.findtext('pubDate', '')) for i in root.iter('item')][:8]
    except Exception: return []

CAUSE = [('nateeje (results)', r'\bq[1-4]\b|result|net profit|profit (jumps|falls|rises|surges|declines|dips)|earnings|revenue|ebitda|quarter'),
         ('order / contract', r'\border\b|contract|bags|wins|tender|loi\b'),
         ('brokerage call / target', r'target price|upgrade|downgrade|buy rating|sell rating|brokerage|initiates|coverage|morgan stanley|jefferies|goldman|clsa|nomura|motilal'),
         ('deal / M&A / stake', r'acqui|merger|stake|block deal|bulk deal|promoter|ofs\b|qip\b|fund rais|demerger'),
         ('regulator / court / FDA', r'sebi|usfda|fda|warning letter|court|tribunal|nclt|ban\b|penalty|raid|probe|gst notice'),
         ('corporate action', r'dividend|bonus|split|buyback|record date'),
         ('sector / policy', r'policy|government|ministry|tariff|duty|subsidy|pli\b|budget|price hike|prices')]
def cause_of(titles):
    t = ' | '.join(titles).lower()
    for name, pat in CAUSE:
        if re.search(pat, t): return name
    return ''

rows = []
for side, ser in (('UP', up), ('DOWN', dn)):
    for s, r_ in ser.items():
        x = dict(date=str(day), side=side, symbol=s, company=NAME.get(s, ''), liq=liq.get(s), ret=round(r_, 2), industry=ind.get(s, ''),
                 ind_med=round(float(ind_med.get(ind.get(s), np.nan)), 2) if ind.get(s) in ind_med else np.nan)
        x['score_yday'] = int(dec.score.get(s, 0)) if len(dec) and 'score' in dec else 0
        x['dist200'] = round((last[s] / a200[s] - 1) * 100, 1) if not pd.isna(a200.get(s)) else np.nan
        x['near20hi'] = round((last[s] / hi20[s] - 1) * 100, 1)
        x['rsi2'] = round(rsi2(s), 0); x['vol5x'] = round(float(vspike.get(s, np.nan)), 2); x['tf_zone'] = s in TFZ
        bm = BM[(BM.symbol == s) & BM.d.notna()]; bm = bm[(bm.d >= day - dt.timedelta(days=3)) & (bm.d <= day)]
        x['known_date'] = ('board meeting ' + str(bm.d.iloc[0])) if len(bm) else ''
        ac = ACT[(ACT.symbol == s) & ACT.d.notna()]; ac = ac[(ac.d >= day - dt.timedelta(days=1)) & (ac.d <= day + dt.timedelta(days=3))]
        if len(ac): x['known_date'] = (x['known_date'] + '; ' if x['known_date'] else '') + 'ex ' + str(ac.d.iloc[0]) + ' ' + str(ac.subject.iloc[0])[:40]
        hits, before = our_news(s)
        g = gnews(short(s)); time.sleep(0.8)
        x['our_news_before'] = len(before); x['our_news_any'] = len(hits)
        x['g_headline'] = g[0]['title'][:160] if g else ''; x['g_source'] = g[0]['source'] if g else ''
        x['cause'] = cause_of([h['title'] for h in g] + [h['title'] for h in hits])
        if not x['cause']:
            if abs(x['ind_med']) >= 2 and np.sign(x['ind_med']) == np.sign(r_): x['cause'] = 'poora sector'
            elif not pd.isna(nret) and abs(nret) >= 1.5 and np.sign(nret) == np.sign(r_): x['cause'] = 'poora bazaar'
            else: x['cause'] = 'pata nahi (khabar nahi mili)'
        sig = []
        if x['score_yday'] >= 3: sig.append(f"robot score {x['score_yday']} tha")
        if x['tf_zone']: sig.append('4H/1H zone mein tha')
        if x['near20hi'] >= -2 and side == 'UP': sig.append('20-din high ke paas tha (breakout)')
        if x['rsi2'] <= 10 and side == 'UP': sig.append('RSI2 bahut neeche tha (bounce)')
        if x['vol5x'] >= 1.8: sig.append(f"5 din se volume {x['vol5x']}x (koi jaanta tha?)")
        if not pd.isna(x['dist200']) and x['dist200'] < 0 and side == 'UP': sig.append('200 DMA ke neeche tha')
        x['signals'] = '; '.join(sig)
        if x['score_yday'] >= 3: v = 'HAAN — robot ki list mein tha' + (' (sahi disha)' if side == 'UP' else ' (ULTA gaya — galti)')
        elif x['our_news_before']: v = 'KHABAR THI — hamari news files mein 9:15 se pehle thi, par score mein nahi judi'
        elif x['known_date']: v = 'TAREEKH PATA THI — ' + x['known_date'] + ' (disha nahi)'
        elif sig: v = 'HALKA ISHAARA — ' + sig[0]
        else: v = 'NAHI — koi signal/khabar nahi thi' + (f" (khabar source: {x['g_source']})" if x['g_source'] else '')
        x['verdict'] = v
        rows.append(x)
df = pd.DataFrame(rows)
logp = os.path.join(D, 'log.csv')
old = pd.read_csv(logp) if os.path.exists(logp) else pd.DataFrame()
if len(old): old = old[old.date != str(day)]
allv = pd.concat([old, df]); allv.to_csv(logp, index=False)

# ---- report ----
M = [f'# Aaj ke sabse bade chadhe / gire shares — {day} (Nifty {nret:+.2f}%)', '',
     'Sawaal: kya hum pehle jaan sakte the? kahan galti hui? kaun si khabar/source hamare paas nahi tha?', '']
for side, t in (('UP', '## Top 20 chadhe'), ('DOWN', '## Top 20 gire')):
    M.append(t)
    for x in df[df.side == side].itertuples():
        M.append(f"- **{x.symbol}** {x.ret:+.1f}% ({x.industry}, sector {x.ind_med:+.1f}%) — wajah: {x.cause}. {x.verdict}. "
                 f"{('Khabar: ' + x.g_headline + ' [' + x.g_source + ']') if x.g_headline else ''}")
    M.append('')
n = len(df); up_ = df[df.side == 'UP']
M += ['## Aaj ka sabak',
      f"- Top 20 chadhe mein se robot ki list mein: {int((up_.score_yday >= 3).sum())}; khabar pehle se files mein: {int((up_.our_news_before > 0).sum())}; "
      f"tareekh pata thi (results/ex-date): {int((up_.known_date != '').sum())}; bilkul andhera: {int(up_.verdict.str.startswith('NAHI').sum())}",
      f"- Wajah ginti (40 shares): " + ', '.join(f'{k} {v}' for k, v in df.cause.value_counts().items()),
      f"- Gire shares jo robot ki list mein the (galti): {', '.join(df[(df.side == 'DOWN') & (df.score_yday >= 3)].symbol) or 'koi nahi'}", '']
open(os.path.join(D, f'{day}.md'), 'w').write('\n'.join(M) + '\n'); open(os.path.join(D, 'latest.md'), 'w').write('\n'.join(M) + '\n')
# running summary + sources we lacked
a = allv.copy(); a['dark'] = a.verdict.astype(str).str.startswith('NAHI')
S = [f'# Movers review — {a.date.nunique()} din ka hisaab', '',
     a.groupby('side').agg(shares=('symbol', 'size'), robot_list=('score_yday', lambda z: round((z >= 3).mean() * 100)),
                           news_pehle=('our_news_before', lambda z: round((z > 0).mean() * 100)), andhera=('dark', lambda z: round(z.mean() * 100))).to_string(),
     '', '(%) robot_list = hamari kharid list mein the; news_pehle = 9:15 se pehle hamari files mein khabar; andhera = koi ishaara nahi', '',
     '## Wajah (sab din)', a.cause.value_counts().to_string(), '',
     '## Jin sources ne khabar di (andhere wale shares) — inhe news robot mein jodna', a[a.dark].g_source.value_counts().head(15).to_string()]
open(os.path.join(D, 'summary.md'), 'w').write('\n'.join(S) + '\n')
# follow these names for 5 days in the news robot (learning)
recent = allv[pd.to_datetime(allv.date) >= pd.Timestamp(day) - pd.Timedelta(days=7)]
open(os.path.join(D, 'follow.txt'), 'w').write('\n'.join(sorted({f'{s} | {short(s)}' for s in recent.symbol})) + '\n')
print('\n'.join(M[:12]))
