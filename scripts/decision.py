"""DECISION REPORT (user 6 Nov 2026: 'sab conclusion nikal ke batao — ye kharidna, ye bechna'; robot zyada kaam kare).
Combines every PASS signal into a per-stock score; acts only when 2+ independent signal families agree (d04 rule).
Holdings (paper/my_holdings.csv) -> SELL / HOLD with orders. Output data/decision.md + data/decision.csv.
Optional: sends decision.md to Telegram if secrets TELEGRAM_TOKEN and TELEGRAM_CHAT are set (no Claude usage needed).
Study only; user places orders himself. Never liquidity D (lists are A/B only).
"""
import os, json, datetime as dt, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(R, 'paper', 'decision_config.json')))
rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C, H, O, V = rd('close.csv.gz'), rd('high.csv.gz'), rd('open.csv.gz'), rd('volume.csv.gz')
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
av = os.path.join(R, 'paper', 'avoid_liquidity_D.txt')
AV = {l.strip() for l in open(av) if l.strip() and not l.startswith('#')} if os.path.exists(av) else set()
AB = [s for s in C.columns if liq.get(s) in ('A', 'B') and s not in AV]
c = C[AB]; last = c.index[-1].date()
nf = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
vx = pd.read_csv(os.path.join(R, 'data', 'INDIAVIX.csv'), parse_dates=['date']).set_index('date').close.dropna()
n10 = (nf.iloc[-1] / nf.iloc[-11] - 1) * 100; above_n200 = nf.iloc[-1] > nf.rolling(200).mean().iloc[-1]
br = float(pd.read_csv(os.path.join(R, 'paper', 'breadth_history.csv')).breadth.iloc[-1]) * 100
thrust, panic = n10 >= 5, br >= 20

a200 = c.rolling(200, min_periods=180).mean().iloc[-1]; up200 = c.iloc[-1] > a200
r63 = c.iloc[-1] / c.iloc[-64] - 1; r250 = (c.iloc[-1] / c.iloc[-250] - 1).fillna(0); hi250 = c.iloc[-250:].max()
s20 = c.rolling(20).mean().iloc[-1]; d20 = (c.iloc[-1] / s20 - 1) * 100
dlt = c.diff(); up = dlt.clip(lower=0).ewm(alpha=.5, adjust=False).mean(); dn = (-dlt.clip(upper=0)).ewm(alpha=.5, adjust=False).mean()
rsi2 = (100 - 100 / (1 + up / dn.replace(0, np.nan))).iloc[-1]
hi_prev = c.iloc[:-1].max(); hi_6m = c.iloc[-127:-1].max(); hi_old = c.iloc[:-127].max()
o_ = O[AB].iloc[-1]; h20 = H[AB].iloc[-21:-1].max()
r1 = (c.iloc[-1] / c.iloc[-2] - 1) * 100
vr = (V[AB] / V[AB].rolling(50, min_periods=40).median().shift(1)).iloc[-5:]
rr = (c.pct_change(fill_method=None) * 100).iloc[-5:]
newscrash = ((vr >= 2) & (rr <= -5)).any()
try:  # f81 same-calendar-month seasonality (table rebuilt weekly by ideas.yml)
    _s = pd.read_csv(os.path.join(R, 'data', 'seasonal', 'same_month.csv')); _s = _s[_s.month == (pd.Timestamp(last) + pd.offsets.BDay(1)).month]
    SEAS = {a: (b, c, d) for a, b, c, d in zip(_s.symbol, _s['rank'], _s.avg5, _s.up_years)}
except Exception as e:
    print('seasonal', e); SEAS = {}
try:
    _F = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol'); FQ = _F.quality_score.dropna(); FL = _F.loss_years.fillna(0)
    # f73: industries in the bottom 20% by 6m (skip 1m) median return lag the market ~0.8%/month (2013-20, 2021-26 t -4)
    _C = rd('close.csv.gz').ffill(); _m = (_C.iloc[-22] / _C.iloc[-148] - 1)
    _g = pd.DataFrame({'m': _m, 'ind': _F.industry.reindex(_m.index)}).dropna()
    _im = _g.groupby('ind').m.median()[_g.groupby('ind').size() >= 5]
    COLD = set(_g[_g.ind.isin(_im[_im <= _im.quantile(0.2)].index)].index); IND = _F.industry
except Exception as e:
    print('fund', e); FQ = FL = pd.Series(dtype=float); COLD = set(); IND = pd.Series(dtype=str)
# f72: up 1.5%+ on LOW delivery (z<=-1 vs own 60 days) underperforms market -> penalty
DZ = pd.Series(dtype=float)
try:
    _d = pd.read_csv(os.path.join(R, 'data', 'deliv_recent.csv.gz'), parse_dates=['date']).pivot_table(index='date', columns='symbol', values='deliv_pct')
    if len(_d) >= 41 and _d.index[-1].date() == pd.Timestamp(last).date():
        DZ = (_d.iloc[-1] - _d.iloc[-61:-1].mean()) / _d.iloc[-61:-1].std()
except Exception as e:
    print('delivery file', e)
STEADY = {'TVSMOTOR', 'EICHERMOT', 'LAURUSLABS', 'UNIONBANK', 'FEDERALBNK', 'TORNTPHARM', 'RBLBANK', 'NYKAA', 'AUBANK',
          'MANAPPURAM', 'NAVINFLUOR', 'KARURVYSYA', 'CUB', 'DCBBANK', 'TMB'}
rs_ok = r63[up200].dropna(); rs_cut = rs_ok.quantile(0.9)
Z = pd.read_csv(os.path.join(R, 'data', 'tf_zone.csv')) if os.path.exists(os.path.join(R, 'data', 'tf_zone.csv')) else pd.DataFrame(columns=['symbol', 'tf', 'ma', 'in_zone', 'zone_price', 'ma_val', 'status'])
Zin = Z[Z.in_zone == True]
dv = os.path.join(R, 'data', 'corp', 'div_candidates.csv'); DV = pd.read_csv(dv) if os.path.exists(dv) else pd.DataFrame(columns=['symbol'])
bmf = os.path.join(R, 'data', 'corp', 'board_meetings.csv'); BM = pd.read_csv(bmf) if os.path.exists(bmf) else pd.DataFrame(columns=['symbol', 'date'])
BM['d'] = pd.to_datetime(BM.date, errors='coerce', dayfirst=True)
soon = BM[(BM.d.dt.date >= last) & (BM.d.dt.date <= last + dt.timedelta(days=10))].sort_values('d').drop_duplicates('symbol').set_index('symbol').d  # dedupe: a share with 2 meetings crashed the robot

bf = os.path.join(R, 'data', 'corp', 'bonus_upcoming.csv'); BU = pd.read_csv(bf) if os.path.exists(bf) else pd.DataFrame(columns=['symbol', 'tdays_to_ex', 'ex_date'])
BUP = dict(zip(BU[BU.tdays_to_ex.between(2, 10)].symbol, BU[BU.tdays_to_ex.between(2, 10)].ex_date)); BALL = dict(zip(BU.symbol, BU.ex_date))
rows = []
for s in AB:
    if pd.isna(c[s].iloc[-1]) or not up200.get(s, False):
        continue
    fam, why, sc = set(), [], 0
    if r63.get(s, -9) >= rs_cut and c[s].iloc[-1] >= 0.95 * hi250[s]:
        sc += 2 if thrust else 1; fam.add('momentum'); why.append('सबसे मज़बूत RS + 52w high पास (f62)')
    if c[s].iloc[-1] > hi_prev[s] and hi_6m[s] < hi_old[s] * 0.99 and c[s].iloc[:-127].notna().sum() > 300:
        sc += 2; fam.add('breakout'); why.append('नया ~2 साल high, 6 महीने बाद (f43)')
    if o_.get(s, np.nan) > h20.get(s, np.inf) * 1.01 and c[s].iloc[-1] >= o_[s]:
        sc += 1; fam.add('breakout'); why.append('breakaway gap (f52)')
    if rsi2.get(s, 50) < 10 and r250.get(s, 0) > 0.3:
        sc += 1; fam.add('pullback'); why.append(f'uptrend में 2-3 दिन गिरावट, RSI2 {rsi2[s]:.0f} (f52)')
    z = Zin[Zin.symbol == s]
    if (z.tf == '4H').any(): sc += 2; fam.add('tfdip'); why.append('4H अपने MA से बहुत नीचे (f56)')
    if (z.tf == '1H').any(): sc += 1; fam.add('tfdip'); why.append('1H अपने MA से बहुत नीचे (f56)')
    if d20.get(s, 0) <= -8 and r250.get(s, 0) > 0.3:
        sc += 2 if panic else 1; fam.add('dailydip'); why.append(f'daily 20 DMA से {d20[s]:.0f}%' + (' + बाज़ार घबराहट (f57)' if panic else ''))
    if s in STEADY: sc += 1; fam.add('quality'); why.append('steady riser (f48)')
    if r250.get(s, 0) >= 0.6: sc += 1; fam.add('trend'); why.append(f'52w {r250[s] * 100:+.0f}% (f43/f58)')
    if s in set(DV.symbol): sc += 2; fam.add('dividend'); why.append('dividend run-up (f64)')
    if s in BUP: sc += 2; fam.add('bonus'); why.append(f'bonus/split ex {BUP[s]} से पहले की चढ़ाई (f71)')
    if pd.Timestamp(last).weekday() == 4 and r1.get(s, 0) >= 2: sc += 1; fam.add('friday'); why.append('शुक्रवार 2%+ चढ़ा (f49)')
    if pd.Timestamp(last).weekday() == 4 and r1.get(s, 0) <= -2: sc -= 2; why.append('शुक्रवार 2%+ गिरा — सोमवार तक रुको (f49)')
    if newscrash.get(s, False) and fam & {'tfdip', 'dailydip', 'pullback'}:
        sc -= 1; why.append('⚠️ 5 दिन में volume 2x के साथ -5%+ गिरा = खबर वाली गिरावट, खबर जाँचो (f41)')
    if r1.get(s, 0) >= 1.5 and DZ.get(s, 0) <= -1:
        sc -= 1; why.append(f'⚠️ आज की चढ़ाई कम delivery पर (z {DZ[s]:.1f}) = सट्टा, आगे बाज़ार से पीछे (f72)')
    if s in FQ.index and (FQ.get(s, 9) <= 3 or FL.get(s, 0) >= 2):  # 9 Nov: weak business (quality <=3/9 or 2+ loss years) -> penalty
        sc -= 2; why.append(f'⚠️ fundamentals kamzor (quality {FQ.get(s, 0):.0f}/9, ghaate ke saal {FL.get(s, 0):.0f})')
    if s in COLD:
        sc -= 1; why.append(f'⚠️ industry ({IND.get(s, "")}) sabse kamzor 20% mein — aisi industry ke shares baazaar se ~0.8%/mahina peeche (f73)')
    sm = SEAS.get(s)
    if sm is not None and sm[0] >= 0.9: sc += 1; fam.add('seasonal'); why.append(f'is mahine ka apna mausam: pichhle 5 saal isi mahine bazaar se ausat {sm[1]:+.1f}%, {sm[2]}/5 saal upar (f81)')
    if sm is not None and sm[0] <= 0.1: sc -= 1; why.append(f'⚠️ is mahine ye share aam taur par kamzor (5 saal ausat {sm[1]:+.1f}%, f81)')
    if sc <= 0: continue
    res = soon.get(s)
    px = float(c[s].iloc[-1])
    # entry / exit plan
    if 'tfdip' in fam or 'dailydip' in fam or 'pullback' in fam:
        zp = z.zone_price.min() if len(z) else px
        entry = round(min(px, zp), 1); tgt = round(max(z.ma_val.max() if len(z) else s20[s], s20[s]), 1); stop = round(entry * 0.90, 1)
        plan = 'dip: आधा entry पर, आधा 3% नीचे; बेच MA पर; 20 दिन'
    else:
        entry = round(px, 1); tgt = None; stop = round(px * 0.92, 1)
        plan = 'तेज़ी: 3:00-3:25 PM LTP के पास LIMIT; कोई fixed target नहीं, 20 दिन review (अच्छे 60 दिन)'
    rows.append(dict(symbol=s, liq=liq[s], score=sc, families=len(fam), fam='+'.join(sorted(fam)), close=round(px, 2), entry=entry,
                     stop=stop, target=tgt, qty=int(cfg['per_trade'] // entry), plan=plan, why='; '.join(why),
                     results=(res.strftime('%d %b') if res is not None and not pd.isna(res) else ''), ret52=round(float(np.nan_to_num(r250.get(s, 0))) * 100)))
D = pd.DataFrame(rows)
if len(D):
    D = D.sort_values(['score', 'families', 'ret52'], ascending=False)
D.to_csv(os.path.join(R, 'data', 'decision.csv'), index=False)
buy = D[(D.score >= cfg['min_score']) & (D.families >= cfg['min_families']) & (D.results == '')] if len(D) else D
wait_res = D[(D.score >= cfg['min_score']) & (D.families >= cfg['min_families']) & (D.results != '')] if len(D) else D

# ---------- holdings ----------
hp = os.path.join(R, 'paper', 'my_holdings.csv'); Hd = pd.read_csv(hp) if os.path.exists(hp) else pd.DataFrame()
CA = C  # all stocks (holding may be any class)
hl = []
for h in Hd.itertuples():
    p = float(CA[h.symbol].dropna().iloc[-1]) if h.symbol in CA else np.nan
    pnl = (p / h.avg - 1) * 100
    days = len(pd.bdate_range(h.buy_date, last)) - 1
    if p <= h.stop: act = f'🔴 SELL — close {p:.2f} stop {h.stop} से नीचे: अगले दिन 2:15-3:25 PM बेचो'
    elif not pd.isna(h.target) and p >= h.target: act = f'🟢 SELL/BOOK — target {h.target} छुआ: LIMIT SELL {h.qty} @{p:.2f}+, सुबह gap-up हो तो पहले 15 मिनट'
    else:
        act = (f'🟡 HOLD — LIMIT SELL {h.qty} @{h.target} (day order, TPIN), stop {h.stop} close पर' if not pd.isna(h.target)
               else f'🟡 HOLD (तेज़ी trade, fixed target नहीं) — stop {h.stop} close पर; 20 दिन पर review')
        if days >= 20: act += f'; {days} दिन हुए — review'
    if h.symbol in BALL: act += f' | ⚠️ bonus/split ex {BALL[h.symbol]}: ex से पहले (cum दिन) बेचो — बाद में ~-6% (f71)'
    res = soon.get(h.symbol); act += (f' | ⚠️ नतीजे {res:%d %b}' if res is not None and not pd.isna(res) else '')
    hl.append(f'- **{h.symbol}** {h.qty} @{h.avg} → {p:.2f} ({pnl:+.1f}%): {act}')

T = pd.Timestamp(last) + pd.offsets.BDay(1)
L = [f'# फ़ैसला — {T:%a %d %b} के लिए (डेटा {last})', '',
     f"Mode: {'🚀 तेज़ी' if thrust else ''}{' 🛒 घबराहट-dip' if panic else ''}{' 😐 शांत' if not (thrust or panic) else ''} | Nifty {nf.iloc[-1]:,.0f} ({'200 DMA ऊपर: पूरा size' if above_n200 else '200 DMA नीचे: आधा size'}) | VIX {vx.iloc[-1]:.1f} | breadth {br:.0f}%",
     '', '## आपकी holdings']
L += hl or ['- (my_holdings.csv खाली)']
op = os.path.join(R, 'paper', 'my_orders.csv')
if os.path.exists(op):
    L += [f'- pending: {o.side} {o.symbol} {o.qty} @{o.price} ({o.type}) — {o.note}' for o in pd.read_csv(op).itertuples()]
L += ['', f"## खरीद (2+ अलग signal एक साथ, score ≥{cfg['min_score']}; ₹{cfg['per_trade']:,} प्रति शेयर; समय 2:15-3:25 PM)"]
if len(buy):
    for r in buy.head(cfg['max_new_per_day']).itertuples():
        L.append(f"- **{r.symbol}** ({r.liq}) score {r.score}: LIMIT {r.qty} @{r.entry} | stop {r.stop} (close पर) | target {r.target if r.target else '20 दिन review'} — {r.why}")
else:
    L.append('- आज कोई शेयर 2+ signal वाला नहीं — नई खरीद नहीं')
if len(wait_res):
    L.append('- नतीजे पास होने से रुको: ' + ', '.join(f'{r.symbol} (नतीजे {r.results})' for r in wait_res.head(8).itertuples()))
L += ['', '## याद रहे', '- हर खरीद से पहले खबर देखो (Claude से पूछो तो वह जाँचेगा); D liquidity कभी नहीं; एक दिन में ज़्यादा से ज़्यादा 5 नए शेयर',
      '- पूरी checklist: data/checklist.md; सभी score: data/decision.csv', '- Study है, पक्की सलाह नहीं.']
out = '\n'.join(L) + '\n'
open(os.path.join(R, 'data', 'decision.md'), 'w').write(out); print(out)

tok, chat = os.environ.get('TELEGRAM_TOKEN'), os.environ.get('TELEGRAM_CHAT')
if tok and chat:
    import requests
    for i in range(0, len(out), 3800):
        requests.post(f'https://api.telegram.org/bot{tok}/sendMessage', data={'chat_id': chat, 'text': out[i:i + 3800]}, timeout=30)
    print('telegram sent')
