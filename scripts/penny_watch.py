"""Saste share (bhaav < Rs 100) ki chhaanti — user 15 Nov 2026: 'saste share mein fundamental, kaam, malik dekho; achhe hon to
chhota paisa long term'. Itihaas (f88, study/penny_hist.py): sasta share = LOTTERY — ausat achha (kuch multibagger) par median
share bazaar se ~13% peeche, 60% haarte; UPTREND (200 DMA upar + 52w high ke 10% andar) har bhaav-band mein bahut behtar;
'bahut gira' (high se 50%+ neeche) = bura. Isliye: achhe fundamentals + uptrend + chhota paisa, gire hue se door.
Sirf A/B liquidity (D kabhi nahi). Output: data/penny.md, data/penny.csv, data/penny_profiles.json (kaam/malik, 30 din cache).
"""
import os, json, datetime as dt, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(R, *a)
rd = lambda f: pd.read_csv(P('data', 'daily_all', f), index_col=0, parse_dates=True)
C = rd('close.csv.gz')
liq = pd.read_csv(P('study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
F = pd.read_csv(P('data', 'fund', 'summary.csv')).set_index('symbol')
try: names = pd.read_csv(P('data', 'fund', 'names.csv')).set_index('symbol').company
except Exception: names = pd.Series(dtype=str)
try: AV = set(pd.read_csv(P('data', 'shock_avoid.csv')).symbol)
except Exception: AV = set()
try: AZ = pd.read_csv(P('data', 'andaza_today.csv'), index_col=0)
except Exception: AZ = pd.DataFrame(columns=['p', 'dec'])
today = C.index[-1]; px = C.iloc[-1]
up200 = px > C.rolling(200, min_periods=180).mean().iloc[-1]
hi52 = px / C.iloc[-250:].max()
U = [s for s in C.columns if pd.notna(px[s]) and px[s] < 100 and liq.get(s) in ('A', 'B') and s in F.index]
rows = []
for s in U:
    f = F.loc[s]; g = lambda k, d=np.nan: f[k] if k in f and pd.notna(f[k]) else d
    good, bad = [], []
    if g('quality_score', 0) >= 6: good.append(f"quality {int(g('quality_score'))}/9")
    if g('loss_years', 9) == 0: good.append('koi ghaate ka saal nahi')
    elif g('loss_years', 0) >= 2: bad.append(f"{int(g('loss_years'))} saal ghaata")
    de = g('debt_equity')
    if pd.notna(de) and de < 0.5: good.append(f'karz kam (D/E {de:.1f})')
    elif pd.notna(de) and de > 1.5: bad.append(f'karz zyada (D/E {de:.1f})')
    if g('rev_g1', 0) > 0.1: good.append(f"bikri +{g('rev_g1') * 100:.0f}%")
    elif g('rev_g1', 0) < -0.05: bad.append(f"bikri {g('rev_g1') * 100:.0f}%")
    if g('np_g1', 0) > 0.1: good.append(f"munafa +{g('np_g1') * 100:.0f}%")
    if g('roe', 0) >= 0.15: good.append(f"ROE {g('roe') * 100:.0f}%")
    if g('ocf_to_np_3y', 0) >= 0.7: good.append('munafa cash mein aata')
    elif pd.notna(g('ocf_to_np_3y')) and g('ocf_to_np_3y') < 0.3: bad.append('munafa cash mein nahi')
    ins = g('heldPercentInsiders')
    if pd.notna(ins) and ins >= 0.45: good.append(f'promoter {ins * 100:.0f}%')
    elif pd.notna(ins) and ins < 0.25: bad.append(f'promoter sirf {ins * 100:.0f}%')
    pe = g('trailingPE')
    if pd.notna(pe) and 0 < pe < 20: good.append(f'PE {pe:.0f}')
    elif pd.isna(pe) or pe <= 0: bad.append('PE nahi (ghaata?)')
    trend = bool(up200.get(s, False)) and hi52.get(s, 0) >= 0.9
    if hi52.get(s, 1) <= 0.5: bad.append(f'52w high se {100 - hi52[s] * 100:.0f}% neeche (bahut gira)')
    if s in AV: bad.append('AVOID list (f86)')
    dec = AZ.dec.get(s, np.nan) if 'dec' in AZ else np.nan
    if pd.notna(dec) and dec <= 2: bad.append(f'andaza kamzor ({int(dec)}/10)')
    fscore = len(good) - len(bad)
    cls = ('ACHHA SASTA' if fscore >= 4 and not bad and trend else 'NAZAR MEIN (trend ka intezaar)' if fscore >= 4 and len(bad) <= 1
           else 'DOOR RAHO' if len(bad) >= 2 else 'theek-thaak')
    rows.append(dict(symbol=s, company=names.get(s, ''), price=round(px[s], 2), liq=liq.get(s), industry=g('industry', ''), sector=g('sector', ''),
                     trend=trend, hi52_pct=round(hi52.get(s, np.nan) * 100), andaza_dec=dec, fscore=fscore, cls=cls,
                     achha='; '.join(good), kharab='; '.join(bad), mcap_cr=round(g('marketCap', 0) / 1e7) if pd.notna(g('marketCap')) else np.nan))
D = pd.DataFrame(rows).sort_values(['cls', 'fscore'], ascending=[True, False])
D.to_csv(P('data', 'penny.csv'), index=False)
# ---- kaam + chalane wale (Yahoo profile), sirf achhe/nazar wale, 30 din cache ----
PF = P('data', 'penny_profiles.json')
prof = json.load(open(PF)) if os.path.exists(PF) else {}
want = D[D.cls.str.startswith(('ACHHA', 'NAZAR'))].symbol.tolist()[:40]
try:
    import yfinance as yf
    for s in want:
        old = prof.get(s, {})
        if old and (dt.date.today() - dt.date.fromisoformat(old.get('as_of', '2000-01-01'))).days < 30: continue
        try:
            inf = yf.Ticker(s + '.NS').info
            off = [f"{o.get('name')} ({o.get('title')})" for o in (inf.get('companyOfficers') or [])[:3]]
            prof[s] = dict(as_of=str(dt.date.today()), kaam=(inf.get('longBusinessSummary') or '')[:400], log=off, website=inf.get('website', ''),
                           city=inf.get('city', ''), employees=inf.get('fullTimeEmployees'))
        except Exception as e:
            print('profile', s, e)
    json.dump(prof, open(PF, 'w'), ensure_ascii=False, indent=1)
except Exception as e:
    print('yfinance nahi', e)
o = [f'# Saste share (bhaav < Rs100, A/B) — {today:%d %b %Y}', '',
     'Itihaas (f88): sasta share = lottery. Ausat achha dikhta (kuch multibagger) par AADHE SE ZYADA bazaar se peeche (median -13%/saal).',
     'Uptrend (200 DMA upar + 52w high ke 10% andar) wale har bhaav mein kaafi behtar; "bahut gira" wale bure. Data mein doobe share kam hain',
     '(survivor bias) -> asli nateeja aur kharab. NIYAM: sirf ACHHA SASTA, chhota paisa (portfolio ka max ~5%), stop -15% close, 6-12 mahine.', '',
     f"Kul {len(D)} saste A/B share: " + ', '.join(f'{k} {v}' for k, v in D.cls.value_counts().items()), '']
for k in ['ACHHA SASTA', 'NAZAR MEIN (trend ka intezaar)']:
    x = D[D.cls == k]
    o += [f'## {k} ({len(x)})']
    for r in x.head(15).itertuples():
        p_ = prof.get(r.symbol, {})
        o += [f"- **{r.symbol}** ₹{r.price} ({r.liq}) — {r.company} | {r.industry} | mcap ~₹{r.mcap_cr:,.0f} cr | 52w high ka {r.hi52_pct}%"
              f"{' | andaza ' + str(int(r.andaza_dec)) + '/10' if pd.notna(r.andaza_dec) else ''}",
              f"  ✅ {r.achha}" + (f"  ⚠️ {r.kharab}" if r.kharab else '')]
        if p_.get('log'): o += [f"  👤 {', '.join(p_['log'])}"]
        if p_.get('kaam'): o += [f"  🏭 {p_['kaam'][:220]}…"]
    o += ['']
x = D[D.cls == 'DOOR RAHO']
o += [f'## DOOR RAHO ({len(x)}) — sabse kharab 15'] + [f'- {r.symbol} ₹{r.price}: {r.kharab}' for r in x.sort_values("fscore").head(15).itertuples()]
open(P('data', 'penny.md'), 'w').write('\n'.join(o) + '\n'); print('\n'.join(o))
