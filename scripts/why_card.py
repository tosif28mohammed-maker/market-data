"""'Kyun' card (user 9 Nov 2026: har khareed/bikri ke saath kaaran — 200 DMA, calendar, technical, fundamentals, khabar).
For every BUY in data/decision.csv and every holding in paper/my_holdings.csv writes plain-Hindi reasons to data/why.md.
Uses: data/daily_all (price), data/fund/summary.csv (fundamentals), data/news/<latest>.csv (headlines), data/checklist.md (calendar).
Study only, not advice."""
import os, glob, re, pandas as pd, numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C = rd('close.csv.gz').ffill(); H = rd('high.csv.gz'); V = rd('volume.csv.gz')
F = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol') if os.path.exists(os.path.join(R, 'data', 'fund', 'summary.csv')) else pd.DataFrame()
nf = sorted(glob.glob(os.path.join(R, 'data', 'news', '20*.csv')))
NEWS = pd.read_csv(nf[-1]) if nf else pd.DataFrame()
tcol = next((c for c in ('title', 'headline', 'Title') if c in NEWS.columns), None)
r63 = C.pct_change(63).iloc[-1]; rs_rank = r63.rank(pct=True)


def tech(s):
    c = C[s].dropna()
    if len(c) < 210: return ['itihaas chhota (200 din se kam)']
    p = c.iloc[-1]; m200 = c.rolling(200).mean().iloc[-1]; m20 = c.rolling(20).mean().iloc[-1]
    m200_up = c.rolling(200).mean().iloc[-1] > c.rolling(200).mean().iloc[-21]
    hi = H[s].iloc[-250:].max(); r52 = p / c.iloc[-250] - 1 if len(c) >= 250 else np.nan
    v = V[s].iloc[-1] / V[s].iloc[-21:-1].mean() if s in V else np.nan
    L = [f'200 DMA {m200:,.1f} se {(p / m200 - 1) * 100:+.1f}% ({"200 DMA khud chadh rahi" if m200_up else "200 DMA gir rahi — dhyaan"})',
         f'20 DMA se {(p / m20 - 1) * 100:+.1f}%' + (' (tez giravat — dip zone, f41)' if p / m20 - 1 <= -0.08 else (' (bahut upar khincha — chase mat karo)' if p / m20 - 1 >= 0.12 else '')),
         f'52w high se {(p / hi - 1) * 100:+.1f}%, 1 saal {r52 * 100:+.0f}%',
         f'3 mahine ki taakat (RS): 100 mein {rs_rank.get(s, np.nan) * 100:.0f} (100 = sabse mazboot)']
    if not np.isnan(v) and (v >= 2 or v <= 0.5): L.append(f'aaj volume 20 din ke ausat ka {v:.1f}x')
    return L


def fund(s):
    if s not in F.index: return ['fundamentals data nahi']
    f = F.loc[s]; L = []
    sec = f.get('industry') if isinstance(f.get('industry'), str) else f.get('sector')
    if isinstance(sec, str): L.append(f'kaam: {sec}')
    def g(k, fmt, pct=False):
        v = f.get(k)
        return None if pd.isna(v) else fmt.format(v * 100 if pct else v)
    bits = [g('rev_g1', 'bikri 1 saal {:+.0f}%', 1), g('np_g1', 'munafa 1 saal {:+.0f}%', 1), g('q_np_yoy', 'pichhli timahi munafa {:+.0f}%', 1),
            g('roe', 'ROE {:.0f}%', 1), g('debt_equity', 'karz/equity {:.2f}'), g('trailingPE', 'PE {:.0f}'), g('quality_score', 'quality {:.0f}/9')]
    L.append(', '.join(b for b in bits if b))
    warn = []
    if not pd.isna(f.get('debt_equity')) and f.get('debt_equity') > 1.5: warn.append('karz zyada')
    if not pd.isna(f.get('loss_years')) and f.get('loss_years') >= 2: warn.append(f"{int(f.get('loss_years'))} saal ghaata")
    if not pd.isna(f.get('trailingPE')) and f.get('trailingPE') > 80: warn.append('bahut mehnga (PE 80+)')
    if not pd.isna(f.get('q_np_yoy')) and f.get('q_np_yoy') < -0.2: warn.append('pichhli timahi munafa gira')
    if warn: L.append('⚠️ ' + ', '.join(warn))
    return L


def news(s):
    if NEWS.empty or tcol is None: return []
    pat = re.compile(rf'\b{re.escape(s)}\b', re.I)
    hits = NEWS[NEWS[tcol].astype(str).str.contains(pat)][tcol].head(3).tolist()
    return [f'khabar: {h[:140]}' for h in hits] if hits else ['aaj ki khabron mein naam nahi (koi bada jhatka nahi dikha)']


cal = []
ck = os.path.join(R, 'data', 'checklist.md')
if os.path.exists(ck):
    txt = open(ck).read(); sec = txt.split('## 1. Calendar')[1].split('## 2')[0] if '## 1. Calendar' in txt else ''
    cal = [l.strip('- ').strip() for l in sec.splitlines() if l.strip().startswith('- ')][:5]
    m = re.search(r'## 2\. .*?\n(.*?)## 3', txt, re.S)
    mode = [l.strip('- ').strip() for l in (m.group(1).splitlines() if m else []) if l.strip().startswith('- ')][:5]
else:
    mode = []

L = ['# Kyun? — har khareed/bikri ke kaaran', '', '## Aaj ka mausam (calendar + bazaar)'] + [f'- {x}' for x in cal + mode] + ['']
D = pd.read_csv(os.path.join(R, 'data', 'decision.csv')) if os.path.exists(os.path.join(R, 'data', 'decision.csv')) else pd.DataFrame()
dm = open(os.path.join(R, 'data', 'decision.md')).read() if os.path.exists(os.path.join(R, 'data', 'decision.md')) else ''
sel = re.findall(r'^- \*\*([A-Z0-9&\-]+)\*\* \(', dm.split('## खरीद')[1].split('## ')[0], re.M) if '## खरीद' in dm else []
buys = D.set_index('symbol').loc[[x for x in sel if x in set(D.symbol)]].reset_index() if len(D) else D
L.append('## Khareed ke kaaran')
for r in buys.itertuples():
    L += [f'### {r.symbol} — score {r.score}, signal: {r.why}', f'- **Plan**: {r.plan}']
    L += [f'- {x}' for x in tech(r.symbol) + fund(r.symbol) + news(r.symbol)]
    L.append('')
hp = os.path.join(R, 'paper', 'my_holdings.csv')
if os.path.exists(hp):
    L.append('## Holdings — rakhna ya bechna kyun')
    for h in pd.read_csv(hp).itertuples():
        if h.symbol not in C: continue
        p = C[h.symbol].iloc[-1]
        L += [f'### {h.symbol} {h.qty} @{h.avg} → {p:.2f} ({(p / h.avg - 1) * 100:+.1f}%) | stop {h.stop} | target {h.target if not pd.isna(h.target) else "nahi (tezi trade)"}']
        L += [f'- {x}' for x in tech(h.symbol) + fund(h.symbol) + news(h.symbol)]
        L.append('')
open(os.path.join(R, 'data', 'why.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
