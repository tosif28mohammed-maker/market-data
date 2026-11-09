"""Theme / mega-trend robot (user 9 Nov 2026: 'duniya ki badi industries, economic forums, sarkaar, private sansthaon, experts
ko follow karo; jaise 4 saal pehle solar, 3-4 saal pehle AI — aisi cheezein pehle pakdo').
Daily (inside news.yml):
  1) BUZZ: Google News RSS for each theme (Indian + global angle) and for big institutions (IMF, World Bank, WEF, OECD, IEA, WTO,
     G20, Fed, ECB, RBI, PIB/Cabinet, NITI Aayog, China State Council, BlackRock/Goldman/McKinsey outlooks, Nvidia/TSMC capex).
     Counts headlines per theme -> data/themes/buzz.csv (history). Institution headlines -> data/themes/institutions.md.
  2) PRICE: India basket per theme (industry names from data/fund/summary.csv + keyword names) -> 3m/6m median return vs all
     stocks, % above 200 DMA. Price must CONFIRM buzz (buzz alone = hype).
  3) data/themes.md: 'shuruaati theme' (buzz rising + price starting), 'chal raha' (both strong), 'thak raha' (price strong, buzz falling),
     + best 5 Indian shares per top theme (A/B liquidity, quality >=6/9, above 200 DMA, own trend).
Buzz needs ~6-8 weeks of history before 'rising' means much; until then the ranking leans on price. Study only.
"""
import os, re, csv, time, html, urllib.parse, urllib.request, datetime as dt, xml.etree.ElementTree as ET
import numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); D = os.path.join(R, 'data', 'themes'); os.makedirs(D, exist_ok=True)
# theme: (news queries, India industries, extra keyword match on industry/symbol)
THEMES = {
    'AI & data centres': (['AI data center investment', 'India data centre capacity investment', 'Nvidia capex hyperscaler spending'],
                          ['Information Technology Services', 'Software - Infrastructure', 'Electronic Components', 'Communication Equipment'], []),
    'Semiconductors & electronics mfg': (['India semiconductor fab plant', 'electronics manufacturing PLI India', 'global chip demand TSMC'],
                                          ['Semiconductors', 'Electronic Components', 'Consumer Electronics', 'Semiconductor Equipment & Materials'], []),
    'Power demand & grid': (['India power demand peak record', 'transmission grid capex India', 'global electricity demand IEA'],
                            ['Utilities - Independent Power Producers', 'Utilities - Regulated Electric', 'Electrical Equipment & Parts'], []),
    'Solar & renewables': (['solar capacity addition India', 'renewable energy auction India', 'IEA renewables outlook'],
                           ['Solar', 'Utilities - Renewable'], []),
    'Nuclear energy': (['nuclear power plant India private', 'small modular reactor investment', 'uranium price nuclear revival'], [], ['nuclear']),
    'Defence': (['India defence orders indigenisation', 'global defence spending NATO', 'defence exports India'], ['Aerospace & Defense'], []),
    'Railways & infra': (['India infrastructure capex budget', 'Indian Railways order Vande Bharat', 'road highway projects NHAI'],
                         ['Engineering & Construction', 'Railroads', 'Farm & Heavy Construction Machinery', 'Building Materials'], []),
    'Copper & metals': (['copper shortage demand electrification', 'steel prices China output', 'aluminium price outlook'],
                        ['Copper', 'Steel', 'Aluminum', 'Other Industrial Metals & Mining'], []),
    'Gold & silver': (['central bank gold buying', 'silver industrial demand solar', 'gold price record'], ['Gold', 'Silver'], []),
    'Oil & gas': (['crude oil outlook OPEC', 'India oil marketing margins', 'natural gas LNG price'],
                  ['Oil & Gas Refining & Marketing', 'Oil & Gas E&P', 'Oil & Gas Integrated', 'Utilities - Regulated Gas'], []),
    'EV & auto': (['electric vehicle sales India', 'auto sales India monthly', 'battery cell manufacturing India'], ['Auto Manufacturers', 'Auto Parts'], []),
    'Pharma & CDMO': (['US FDA India pharma', 'CDMO India biosecure act', 'GLP-1 generic India'],
                      ['Drug Manufacturers - Specialty & Generic', 'Drug Manufacturers - General', 'Biotechnology', 'Diagnostics & Research'], []),
    'Healthcare services': (['hospital expansion India beds', 'health insurance India growth'], ['Medical Care Facilities', 'Medical Instruments & Supplies'], []),
    'Banks & credit': (['India bank credit growth', 'RBI liquidity banks NPA', 'NBFC lending growth'],
                       ['Banks - Regional', 'Banks - Diversified', 'Credit Services', 'Mortgage Finance'], []),
    'Capital markets': (['demat accounts SIP inflows record', 'mutual fund AUM India', 'IPO pipeline India'],
                        ['Capital Markets', 'Asset Management', 'Financial Data & Stock Exchanges'], []),
    'Consumption & FMCG': (['India rural demand FMCG', 'consumer spending India GST cut', 'urban consumption slowdown'],
                           ['Packaged Foods', 'Household & Personal Products', 'Beverages - Non-Alcoholic', 'Confectioners', 'Apparel Retail'], []),
    'Real estate & housing': (['India housing sales quarter', 'real estate launches India'], ['Real Estate - Development', 'Building Products & Equipment'], []),
    'Chemicals': (['specialty chemicals India demand China plus one', 'chemical prices China dumping'], ['Specialty Chemicals', 'Chemicals', 'Agricultural Inputs'], []),
    'Tourism & travel': (['India air traffic record', 'hotel occupancy India'], ['Lodging', 'Travel Services', 'Airlines'], []),
    'Water & agri': (['Jal Jeevan mission water projects', 'monsoon kharif rabi crop'], ['Farm Products', 'Agricultural Inputs', 'Utilities - Regulated Water'], ['water']),
    'Shipping & ports': (['shipbuilding India policy', 'port cargo volumes India', 'freight rates container'], ['Marine Shipping', 'Integrated Freight & Logistics'], ['ship']),
}
INSTITUTIONS = ['IMF World Economic Outlook', 'World Bank report growth', 'World Economic Forum Davos', 'OECD economic outlook', 'IEA report energy',
                'WTO trade forecast', 'G20 summit agreement', 'Federal Reserve Powell', 'ECB Lagarde rates', 'RBI governor policy', 'Union Cabinet approves',
                'NITI Aayog report', 'China State Council stimulus', 'BlackRock outlook 2027', 'Goldman Sachs India outlook', 'McKinsey report industry',
                'Morgan Stanley India strategy', 'Nvidia TSMC capex guidance', 'sovereign wealth fund invests India', 'PLI scheme approval']


def rss(q):
    url = 'https://news.google.com/rss/search?' + urllib.parse.urlencode({'q': q + ' when:7d', 'hl': 'en-IN', 'gl': 'IN', 'ceid': 'IN:en'})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (market-data themes)'})
    for a in range(2):
        try:
            with urllib.request.urlopen(req, timeout=20) as r: root = ET.fromstring(r.read())
            return [dict(title=html.unescape(i.findtext('title', '')), link=i.findtext('link', ''), pub=i.findtext('pubDate', '')) for i in root.iter('item')]
        except Exception as e:
            print('retry', q, e); time.sleep(3)
    return []


today = (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date()
# ---------- 1) buzz ----------
rows, heads = [], {}
for th, (qs, _, _) in THEMES.items():
    items = {}
    for q in qs:
        for it in rss(q): items[it['link']] = it
        time.sleep(0.8)
    # last-24h share of the 7-day window = rising-now signal
    recent = 0
    for it in items.values():
        try:
            if (dt.datetime.utcnow() - dt.datetime.strptime(it['pub'][5:25], '%d %b %Y %H:%M:%S')).total_seconds() < 86400: recent += 1
        except Exception: pass
    rows.append(dict(date=str(today), theme=th, n7=len(items), n1=recent)); heads[th] = [i['title'] for i in list(items.values())[:3]]
bf = os.path.join(D, 'buzz.csv')
B = pd.concat([pd.read_csv(bf), pd.DataFrame(rows)]) if os.path.exists(bf) else pd.DataFrame(rows)
B = B.drop_duplicates(['date', 'theme'], keep='last'); B.to_csv(bf, index=False)
inst = []
for q in INSTITUTIONS:
    for it in rss(q)[:4]: inst.append((q, it['title'], it['pub'][:16]))
    time.sleep(0.8)
with open(os.path.join(D, 'institutions.md'), 'w') as fh:
    fh.write(f'# Badi sansthayein — {today} (pichhle 7 din)\n\n')
    for q in INSTITUTIONS:
        hs = [x for x in inst if x[0] == q]
        if hs: fh.write(f'## {q}\n' + ''.join(f'- {t} ({p})\n' for _, t, p in hs) + '\n')

# ---------- 2) price ----------
rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C = rd('close.csv.gz').ffill()
F = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol')
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
r63, r126 = C.pct_change(63).iloc[-1] * 100, C.pct_change(126).iloc[-1] * 100
a200 = C.iloc[-1] > C.rolling(200).mean().iloc[-1]
m63, m126 = r63.median(), r126.median()
out = []
for th, (_, inds, kws) in THEMES.items():
    ind = F.industry.fillna('')
    mem = F.index[ind.isin(inds) | (ind.str.contains('|'.join(kws), case=False) if kws else False)]
    mem = [s for s in mem if s in C.columns and liq.get(s, 'D') != 'D']
    hist = B[B.theme == th].sort_values('date')
    n7 = hist.n7.iloc[-1]; base = hist.n7.iloc[:-1].tail(40).mean() if len(hist) > 1 else np.nan
    out.append(dict(theme=th, stocks=len(mem), r3m=round(r63[mem].median() - m63, 1) if mem else np.nan,
                    r6m=round(r126[mem].median() - m126, 1) if mem else np.nan, above200=round(a200[mem].mean() * 100) if mem else np.nan,
                    buzz7=n7, buzz_vs_avg=round(n7 / base, 2) if base and base > 0 else np.nan, days=len(hist), members=mem))
T = pd.DataFrame(out)
T['price_score'] = T.r3m.rank(pct=True) * 0.5 + T.r6m.rank(pct=True) * 0.3 + T.above200.rank(pct=True) * 0.2
T['buzz_score'] = T.buzz_vs_avg.rank(pct=True) if T.buzz_vs_avg.notna().sum() >= 5 else T.buzz7.rank(pct=True)
def stage(r):
    if r.price_score >= 0.6 and r.buzz_score >= 0.6: return 'चल रहा (दाम + चर्चा दोनों)'
    if r.price_score >= 0.6: return 'दाम आगे, चर्चा कम (थक रहा या चुपचाप)'
    if r.buzz_score >= 0.6 and r.r3m > r.r6m: return 'शुरुआती? (चर्चा बढ़ी, दाम अभी शुरू)'
    if r.buzz_score >= 0.6: return 'सिर्फ़ चर्चा (दाम साथ नहीं = hype)'
    return 'ठंडा'
T['stage'] = T.apply(stage, axis=1)
T = T.sort_values('price_score', ascending=False)
T.drop(columns=['members']).to_csv(os.path.join(D, 'themes_today.csv'), index=False)

L = [f'# Themes / बड़े रुझान — {today}', '',
     'दाम (India टोकरी, सब शेयरों के median से फ़र्क) + चर्चा (7 दिन की ख़बरें). चर्चा का इतिहास ' + f'{int(T.days.max())} दिन — 6-8 हफ़्ते बाद "बढ़ती चर्चा" भरोसेमंद होगी.', '',
     '| Theme | Stage | 3m vs बाज़ार | 6m vs बाज़ार | 200 DMA ऊपर | ख़बरें 7d | चर्चा/औसत |', '|---|---|---|---|---|---|---|']
for r in T.itertuples():
    L.append(f'| {r.theme} | {r.stage} | {r.r3m:+.1f}% | {r.r6m:+.1f}% | {r.above200:.0f}% | {r.buzz7} | {"" if pd.isna(r.buzz_vs_avg) else r.buzz_vs_avg} |')
L += ['', '## सबसे मज़बूत themes के अच्छे शेयर (A/B, quality ≥6/9, 200 DMA ऊपर, 3m ताकत से)']
for r in T.head(5).itertuples():
    m = [s for s in r.members if a200.get(s, False) and F.quality_score.get(s, 0) >= 6]
    top = sorted(m, key=lambda s: -r63.get(s, -999))[:5]
    L.append(f'- **{r.theme}**: ' + ', '.join(f'{s} ({r63[s]:+.0f}% 3m, Q{F.quality_score[s]:.0f})' for s in top))
# value chain (f74): anchor basket strong last month -> suppliers next month (auto/power held in all eras, ~+1%/month vs weak months)
try:
    VC = pd.read_csv(os.path.join(R, 'data', 'chain', 'value_chain.csv')); r21 = C.pct_change(21).iloc[-1] * 100; mk = r21.median()
    L += ['', '## Value chain (ग्राहक कंपनी मज़बूत → सप्लायर पीछे से चलते हैं; auto/power में असर, telecom में नहीं)']
    for ch, g in VC.groupby('chain'):
        an = [s for s in g[g.role == 'anchor'].symbol if s in r21]; su = [s for s in g[g.role == 'supplier'].symbol if s in r21]
        ax = r21[an].median() - mk
        good = [s for s in su if a200.get(s, False) and F.quality_score.get(s, 0) >= 6]
        lag = sorted(good, key=lambda s: r21[s])[:5]
        L.append(f"- **{ch}**: ग्राहक (anchor) पिछला महीना बाज़ार से {ax:+.1f}% → " + ('मज़बूत: पीछे रहे अच्छे सप्लायर देखो: ' + ', '.join(f'{s} ({r21[s]:+.0f}%)' for s in lag) if ax >= 2 else 'अभी कोई chain signal नहीं'))
except Exception as e:
    print('chain', e)
L += ['', '## आज की चर्चा के नमूने']
for r in T.head(8).itertuples():
    L += [f'- {r.theme}: ' + ' | '.join(h[:110] for h in heads.get(r.theme, []))]
open(os.path.join(R, 'data', 'themes.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
