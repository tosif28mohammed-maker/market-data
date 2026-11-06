"""DAILY CHECKLIST (user 6 Nov 2026: 'sari studies ka nichod roz batao, sirf 20/200 DMA nahi; tezi ke niyam bhi').
Every PASS finding turned into a flag for the NEXT trading day + stock lists for all three buckets.
Output: data/checklist.md (Hindi). Runs in daily.yml after the paper scripts. Study only, no orders.
Sources: findings f06/f20/f22/f37 (calendar), f05 (pre-holiday), f09 (month), f27/f31/f29/f30 (index, VIX),
f57/f58 (breadth dip), f62 (thrust + RS top), f43 breakout, f52 (Connors RSI2<10 above 200 DMA, breakaway gap),
f48 (steady risers), f49 (Friday 2% moves), f64 (dividend), f67 (Diwali/Budget), f45/f46/f54 (timing, gaps), f60 (10-month filter).
"""
import os, datetime as dt, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOL = {dt.date(2026, 11, 10), dt.date(2026, 11, 24), dt.date(2026, 12, 25)}  # NSE 2026 left; add 2027 list when NSE publishes
MUHURAT = {dt.date(2026, 11, 8)}
DIWALI = {2026: dt.date(2026, 11, 8), 2027: dt.date(2027, 10, 29)}
BUDGET = {2027: dt.date(2027, 2, 1)}
STEADY = ['TVSMOTOR', 'EICHERMOT', 'LAURUSLABS', 'UNIONBANK', 'FEDERALBNK', 'TORNTPHARM', 'RBLBANK', 'NYKAA', 'AUBANK',
          'MANAPPURAM', 'NAVINFLUOR', 'KARURVYSYA', 'CUB', 'DCBBANK', 'TMB']  # f48, Nov 2026 list
td = lambda d: d.weekday() < 5 and d not in HOL


def nxt(d, k=1):
    while k:
        d += dt.timedelta(days=1)
        if td(d): k -= 1
    return d


def monthly_expiry(y, m):
    """NSE monthly F&O expiry: last Tuesday (from Sep 2025); holiday -> previous trading day."""
    d = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
    while d.weekday() != 1: d -= dt.timedelta(days=1)
    while not td(d): d -= dt.timedelta(days=1)
    return d


rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C, H, L, O, V = (rd(f'{x}.csv.gz') for x in ('close', 'high', 'low', 'open', 'volume'))
last = C.index[-1].date(); T = nxt(last)          # T = next trading day the advice is for
nf = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
vx = pd.read_csv(os.path.join(R, 'data', 'INDIAVIX.csv'), parse_dates=['date']).set_index('date').close.dropna()
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
AB = [s for s in C.columns if liq.get(s) in ('A', 'B')]
L_ = []
w = L_.append

# ---------- 1. calendar for T ----------
exp_this = monthly_expiry(T.year, T.month)
exp_prev = monthly_expiry((T.replace(day=1) - dt.timedelta(days=1)).year, (T.replace(day=1) - dt.timedelta(days=1)).month)
day_after_exp = nxt(exp_this) if nxt(exp_this) <= T else None
cal = []
if T == nxt(exp_prev) or T == nxt(exp_this):
    cal.append('🟢 **Expiry का अगला दिन** — सबसे पक्का calendar नियम (f06/f37): ~68-71% शेयर ऊपर (आम 56%), हर दौर में; अगले 5 दिन +1.1..1.4%')
first = [d for d in pd.bdate_range(T.replace(day=1), periods=6) if td(d.date())][:3]
if T in [d.date() for d in first]:
    cal.append('🟢 **महीने के पहले 3 कारोबारी दिन** — Up झुकाव (f20/f37)')
if T.day in (1, 31):
    cal.append('🟢 तारीख 1/31 — अच्छी (f20)')
if 11 <= T.day <= 24:
    cal.append('🟠 तारीख 11-24 — हल्का कमज़ोर (f22)' + (' ; 19/24 सबसे कमज़ोर' if T.day in (19, 24) else ''))
if T.day == 30:
    cal.append('🔴 तारीख 30 — Nov 2023 से कमज़ोर (f37)')
mend = max(d.date() for d in pd.bdate_range(T.replace(day=1), T.replace(day=28) + dt.timedelta(days=4)) if d.month == T.month and td(d.date()))
if T == mend:
    cal.append('⚪ महीने का आख़िरी दिन — Nov 2023 से कोई फ़ायदा नहीं')
if not td(T + dt.timedelta(days=1)) and (T + dt.timedelta(days=1)).weekday() < 5:
    cal.append('🟢 छुट्टी से पहले का दिन — ~60% शेयर ऊपर (f05)')
dw = DIWALI.get(T.year)
if dw and 0 < (dw - T).days <= 8:
    cal.append('🟢 Diwali से पहले के 5 दिन — हल्का Up (2013 से 13 में 12 साल, f67)')
if dw and 0 <= (T - dw).days <= 8:
    cal.append('🟢 Diwali/Muhurat के बाद 5 दिन — Nifty औसत +1.2% (f67)')
bd = BUDGET.get(T.year)
if bd and 0 < (bd - T).days <= 8:
    cal.append('🔴 Budget से पहले का हफ़्ता — कमज़ोर (2013 से 17-25% बार ऊपर, f67): नई खरीद धीमी')
if T.month == 1:
    cal.append('🟠 जनवरी — Nifty का कमज़ोर महीना (f09)')
if T.weekday() == 0 and last.weekday() == 4:
    cal.append('ℹ️ सोमवार: शुक्रवार को 2%+ चढ़े शेयर सोमवार और चढ़ते (+0.2..0.7%), 2%+ गिरे फिर गिरते (f49) — नीचे सूची')
w(f'# रोज़ की checklist — {T:%a %d %b %Y} के लिए (डेटा {last})\n')
w('## 1. Calendar')
w('\n'.join(f'- {x}' for x in cal) if cal else '- आज कोई खास calendar झुकाव नहीं (आम दिन)')
w(f'- अगली monthly expiry: {exp_this:%a %d %b} → अगला दिन {nxt(exp_this):%a %d %b} (Up दिन). छुट्टियाँ: ' + ', '.join(f'{d:%d %b}' for d in sorted(HOL) if d >= T) + ('; Muhurat ' + ', '.join(f'{d:%a %d %b}' for d in MUHURAT if d >= last) if any(d >= last for d in MUHURAT) else ''))

# ---------- 2. market regime ----------
n = nf.iloc[-1]; d200 = nf.rolling(200).mean().iloc[-1]; n10 = (n / nf.iloc[-11] - 1) * 100
dd3m = (n / nf.iloc[-63:].max() - 1) * 100; hi52 = (n / nf.iloc[-250:].max() - 1) * 100
m10 = nf.resample('ME').last(); sma10m = m10.rolling(10).mean().iloc[-1]
v = vx.iloc[-1]
side = 90 if v < 12 else 83 if v < 14 else 88 if v < 16 else 80 if v < 18 else 78 if v < 22 else 67 if v < 30 else 38
bh = pd.read_csv(os.path.join(R, 'paper', 'breadth_history.csv'))
br = float(bh.breadth.iloc[-1]) * 100
w('\n## 2. बाज़ार की हालत (mode)')
w(f'- Nifty {n:,.0f}: 200 DMA {d200:,.0f} से {(n / d200 - 1) * 100:+.1f}% ({"ऊपर — पूरा size" if n > d200 else "नीचे — आधा size"}); 10 दिन {n10:+.1f}%; 52w high से {hi52:+.1f}%; 10-महीने SMA {"ऊपर (ETF रखो)" if n > sma10m else "नीचे (Nifty ETF नकद, f60)"}')
w(f'- VIX {v:.1f} → Nifty अगले 20 दिन ±5% में रहने का मौका ~{side}% (f29); असल हलचल VIX से कम ~79% बार (f30)')
modes = []
if n10 >= 5: modes.append('🚀 **तेज़ी mode (f62)**: Nifty 10 दिन +5%+ → बाज़ार आम तौर पर और चढ़ता (20 दिन 67-80% ऊपर). सबसे मज़बूत शेयर (RS top) खरीदो, 8-10 में बाँटकर, stop -8%, 20 दिन review, अच्छे 60 दिन')
if br >= 20: modes.append(f'🛒 **घबराहट/dip mode (f57/f58)**: breadth {br:.0f}% ≥20% → लंबे uptrend वाले शेयरों के dip खरीदो')
if v > 25: modes.append('😨 **डर mode (f31)**: VIX>25 → Nifty अगले 20 दिन औसत +4.8% (73% ऊपर) — index/ETF किश्तें')
if dd3m <= -8: modes.append('📉 Nifty 3 महीने high से -8%+ (f27) → अगले 20 दिन औसत +3.7%')
if not modes: modes.append('😐 शांत mode: न तेज़ी का धक्का, न घबराहट — core लंबा (d06) + Connors/breakout सूची + dividend')
w('\n'.join(f'- {x}' for x in modes))
w(f'- Breadth (गहरे dip वाले शेयर) {br:.1f}%; पिछले 5: ' + ', '.join(f'{x * 100:.0f}%' for x in bh.breadth.iloc[-5:]))

# ---------- 3. stock lists ----------
c = C[AB]; a200 = c.rolling(200, min_periods=180).mean()
r63 = c.iloc[-1] / c.iloc[-64] - 1; r250 = c.iloc[-1] / c.iloc[-250] - 1
hi250 = c.iloc[-250:].max(); up200 = c.iloc[-1] > a200.iloc[-1]
rs = r63[up200].dropna()
rs_top = rs[rs >= rs.quantile(0.9)]
near = rs_top[(c.iloc[-1][rs_top.index] / hi250[rs_top.index]) >= 0.95].sort_values(ascending=False)
w('\n## 3. तेज़ी वाले शेयर (A/B liquidity, 200 DMA ऊपर)')
w(f'- **RS top 10% + 52w high के 5% अंदर (f62)** — {len(near)} शेयर, सबसे मज़बूत 12: ' + ', '.join(f'{s} ({r63[s] * 100:+.0f}% 3m)' for s in near.index[:12]))
# breakout: new ~2-year high (data has ~2 years) after 6-month pause
hi_prev = c.iloc[:-1].max(); hi_6m = c.iloc[-127:-1].max(); hi_old = c.iloc[:-127].max()
bo = [s for s in c.columns if c[s].iloc[-1] > hi_prev[s] and hi_6m[s] < hi_old[s] * 0.99 and c[s].iloc[:-127].notna().sum() > 300]
w(f'- **Breakout (f43)**: नया ~2 साल high, 6 महीने रुकने के बाद (60 दिन +3%, 120-250 दिन +5-7% बाज़ार से) — ' + (', '.join(bo[:15]) if bo else 'आज कोई नहीं') + ' (retest का इंतज़ार नहीं, f43)')
# Connors RSI(2) < 10 above 200 DMA (f52: pullback inside uptrend)
dlt = c.diff(); up = dlt.clip(lower=0).ewm(alpha=1 / 2, adjust=False).mean(); dn = (-dlt.clip(upper=0)).ewm(alpha=1 / 2, adjust=False).mean()
rsi2 = (100 - 100 / (1 + up / dn.replace(0, np.nan))).iloc[-1]
con = rsi2[(rsi2 < 10) & up200 & (r250 > 0.3)].sort_values()
w(f'- **Uptrend में 2-3 दिन की गिरावट (Connors RSI2<10, 200 DMA ऊपर, 52w +30%+; f52)** — तेज़ी में dip: ' + (', '.join(f'{s} (RSI2 {rsi2[s]:.0f})' for s in con.index[:12]) if len(con) else 'आज कोई नहीं'))
# breakaway gap above 20d high (f52)
o_ = O[AB].iloc[-1]; h20 = H[AB].iloc[-21:-1].max()
bag = [s for s in AB if o_.get(s, np.nan) > h20.get(s, np.inf) * 1.01 and c[s].iloc[-1] >= o_[s] and up200.get(s, False)]
w('- **Breakaway gap (20 दिन high के ऊपर gap, हरा बंद; f52)** — ' + (', '.join(bag[:12]) if bag else 'आज कोई नहीं'))
st = [s for s in STEADY if s in c.columns and liq.get(s) != 'D']
w('- **Steady risers (f48, लंबा core)** — ' + ', '.join(f'{s} ({(c[s].iloc[-1] / c[s].rolling(20).mean().iloc[-1] - 1) * 100:+.0f}% 20DMA से)' for s in st))
# 52w trend 60%+ (stock own trend)
t60 = r250[(r250 >= 0.6) & up200].sort_values(ascending=False)
w(f'- 52w trend 60%+ वाले {len(t60)} शेयर (अगले 6-12 महीने बाज़ार से +3..5%, f43/f58) — ऊपर की सूचियों को इनसे मिलाओ')

# ---------- 3b. short timeframes (f56: 4H/1H dip below own MA zone) ----------
zf = os.path.join(R, 'data', 'tf_zone.csv')
w('\n## 3b. छोटे timeframe (1H / 2H / 3H / 4H) — अपने MA से बहुत नीचे = खरीद ज़ोन (f56)')
if os.path.exists(zf):
    Z = pd.read_csv(zf)
    Z = Z[Z.ret52 >= 0]
    inz = Z[Z.in_zone]
    agg = inz.groupby('symbol').agg(tfs=('tf', lambda x: '+'.join(sorted(set(x)))), n=('tf', 'nunique'), close=('close', 'first'),
                                    target=('ma_val', 'max'), ret52=('ret52', 'first')).sort_values(['n', 'ret52'], ascending=False)
    w(f'- अभी ज़ोन में (200 DMA ऊपर, 52w ≥0): {len(agg)} शेयर. सबसे ज़्यादा timeframe एक साथ:')
    for s, r in agg.head(12).iterrows():
        w(f'  - {s}: {r.tfs} | भाव {r.close} | बेच (MA) ~{r.target} | 52w {r.ret52:+.0f}%')
    near = Z[~Z.in_zone & Z.status.ne('जाँच बाकी')].sort_values('gap_to_zone', ascending=False).drop_duplicates('symbol').head(10)
    w('- ज़ोन के पास (2% के अंदर) — यहाँ LIMIT BUY लगा सकते हो: ' + '; '.join(f'{r.symbol} {r.tf} {r.ma} @{r.zone_price}' for r in near.itertuples()))
    w('- नियम: 4H SMA20 और 1H EMA50 पक्के (2021-26 + Nov23 दोनों में); 2H/3H अभी जाँच बाकी. बेच = उस MA पर, या 20 कारोबारी दिन; stop -8%. MA को ऊपर पार करना (cross) = फेल, उस पर नहीं खरीदना.')
else:
    w('- tf_zone.csv अभी नहीं बना')

# ---------- 3c. options / futures (safe zone only) ----------
w('\n## 3c. Option / Future — सिर्फ़ सुरक्षित (defined-risk)')
dte = len([d for d in pd.bdate_range(T, exp_this) if td(d.date())])
sig = n * v / 100 * np.sqrt(max(dte, 1) / 252)
ok_ic = 12 <= v <= 20 and 8 <= dte <= 25 and n10 < 5 and br < 20
w(f'- अगली monthly expiry {exp_this:%d %b} ({dte} कारोबारी दिन). VIX {v:.1f} से 1.5σ दायरा ±{1.5 * sig:,.0f} अंक (91% बार अंदर, f30)')
if ok_ic:
    lo_, hi_ = int((n - 1.5 * sig) // 50 * 50), int(-(-(n + 1.5 * sig) // 50) * 50)
    w(f'- 🟢 Iron condor (paper/सीखने के लिए): SELL {lo_} PE + SELL {hi_} CE, BUY {lo_ - 200} PE + BUY {hi_ + 200} CE (1 lot). बाहर: 50% मुनाफ़ा या नुकसान = 2× credit, और expiry से 5 दिन पहले हर हाल में बंद')
else:
    why = 'तेज़ी का धक्का (एक तरफ़ा चाल का जोखिम)' if n10 >= 5 else 'breadth घबराहट' if br >= 20 else f'VIX {v:.1f} दायरे (12-20) से बाहर' if not 12 <= v <= 20 else f'expiry {dte} दिन (8-25 चाहिए)'
    w(f'- 🔴 आज iron condor नहीं — {why}')
w('- नहीं करना: naked option बेचना, option खरीदना (study फेल), future (आपकी पूँजी के हिसाब से margin/जोखिम बड़ा). Paper में अब तक: naked strangle -₹10.5k, iron condor -₹7.1k (1-1 सौदा) — असली पैसा 10+ paper सौदों के बाद ही')

# ---------- 4. dip bucket ----------
s20 = c.rolling(20).mean().iloc[-1]; dist = (c.iloc[-1] / s20 - 1) * 100
dips = dist[(dist <= -8) & up200 & (r250 > 0.3)].sort_values()
w('\n## 4. Dip वाले (20 DMA से 8%+ नीचे, पर लंबा uptrend; f41/f58)')
w('- ' + (', '.join(f'{s} ({dist[s]:+.0f}%)' for s in dips.index[:12]) if len(dips) else 'आज कोई नहीं') + (' — breadth <20%: छोटा size' if br < 20 else ' — breadth ≥20%: पूरा size'))

# ---------- 5. Friday rule ----------
if last.weekday() == 4:
    r1 = (c.iloc[-1] / c.iloc[-2] - 1) * 100
    w('\n## 5. शुक्रवार नियम (f49)')
    w('- 2%+ चढ़े (सोमवार और चढ़ने का झुकाव): ' + ', '.join(r1[r1 >= 2].sort_values(ascending=False).index[:12]))
    w('- 2%+ गिरे — आज शाम मत खरीदो, सोमवार देखो: ' + ', '.join(r1[r1 <= -2].sort_values().index[:12]))

# ---------- 6. dividend ----------
dc = os.path.join(R, 'data', 'corp', 'div_candidates.csv')
w('\n## 6. Dividend run-up (f64)')
dcd = pd.read_csv(dc) if os.path.exists(dc) else pd.DataFrame()
w('- ' + ('; '.join(f"{r.symbol} ₹{r.div_rs} ({r.yield_pct}%), ex {r.ex_date}, खरीद {r.buy_from} से, बेच {r.sell_on_cum}, stop {r.stop}" for r in dcd.itertuples()) if len(dcd) else 'आज कोई नहीं (yield 2%+ वाला dividend नहीं)'))

# ---------- 7. timing (always) ----------
w('\n## 7. समय के नियम (हमेशा, f45/f46/f54)')
w('- खरीद 2:15-3:25 PM (सबसे अच्छा 3:00-3:25); 9:15 पर नहीं. बेच अगली सुबह/दोपहर; gap-up 1%+ पर पहले 15 मिनट में बेचो')
w('- Gap-down 1%+ पर घबराकर मत बेचो (पहले 15 मिनट वापसी); अच्छा शेयर gap-down = 3-5 दिन का मौका')
w('- US में बड़ी गिरावट की रात: F&O शेयर जो 2%+ gap-down खुलें, 9:15 पर +0.73% (f54) — यह अपवाद है; index पहला घंटा जाने दो')
w('- Option selling: VIX ऊपर देखो; naked strangle नहीं, hedge/iron condor, expiry से 4-5 दिन पहले gap जोखिम')

out = '\n'.join(L_) + '\n'
open(os.path.join(R, 'data', 'checklist.md'), 'w').write(out)
print(out)
