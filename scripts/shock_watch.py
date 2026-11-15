"""Jhatka-watch (f86, user 15 Nov 2026: top gainers/losers se seekho). Roz daily.yml mein.
f86 (2003-26, har daur): (1) kal ke bade gainer ka peechha = FAIL; khaaskar 200 DMA ke NEECHE wala +10% volume-3x share
agle 60 din bazaar se ~4% peeche. (2) -10% volume-3x giravat ke baad share 60 din tak bazaar se ~3.4% peeche (uptrend wala ~4%)
-> 'sasta ho gaya, le lo' galat; aise share ko 60 din AVOID, aur hamare paas ho to bechne par socho.
(3) mahine ke sabse gire 20 share agle 3 mahine bhi peeche (-2.7%). Mahine ke top 20 mein aage koi fayda nahi.
Output data/shock_watch.md + data/shock_avoid.csv (60 kaarobaari din ki AVOID list, decision/briefing ke liye)."""
import os, pandas as pd, numpy as np
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(R, *a)
rd = lambda f: pd.read_csv(P('data', 'daily_all', f), index_col=0, parse_dates=True)
C, V, Hh = rd('close.csv.gz'), rd('volume.csv.gz'), rd('high.csv.gz')
liq = pd.read_csv(P('study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
AB = [s for s in C.columns if liq.get(s) in ('A', 'B')]
C, V, Hh = C[AB], V[AB], Hh[AB]
r1 = C.pct_change(fill_method=None); vr = V / V.rolling(50, min_periods=40).mean().shift(1)
up200 = C > C.rolling(200, min_periods=180).mean()
dn = (r1 <= -0.10) & (vr >= 3)
upw = (r1 >= 0.10) & (vr >= 3) & up200.shift(1).eq(False)
today = C.index[-1]; win = C.index[-60:]
rows = []
for d in win:
    for s in C.columns[dn.loc[d].fillna(False).values]: rows.append((s, d.date(), 'GIRAVAT -10% vol 3x', round(r1.at[d, s] * 100, 1)))
    for s in C.columns[upw.loc[d].fillna(False).values]: rows.append((s, d.date(), 'KAMZOR TREND mein +10% (peechha mat karo)', round(r1.at[d, s] * 100, 1)))
A = pd.DataFrame(rows, columns=['symbol', 'date', 'kyun', 'din_ka_pct']).sort_values('date', ascending=False).drop_duplicates('symbol')
A['liq'] = A.symbol.map(liq); A['avoid_tak'] = [(C.index[min(C.index.get_loc(pd.Timestamp(x)) + 60, len(C.index) - 1)]).date() if C.index.get_loc(pd.Timestamp(x)) + 60 < len(C.index) else 'aage' for x in A.date]
A.to_csv(P('data', 'shock_avoid.csv'), index=False)
H = []
try: H = pd.read_csv(P('paper', 'my_holdings.csv')).symbol.astype(str).tolist()
except Exception: pass
# PAPER jaanch (live): list mein aane ke baad share ne bazaar (sab A/B ka ausat) ke muqable kya kiya
mk = r1.mean(axis=1).fillna(0).add(1).cumprod()
def since(s, d):
    i = C.index.get_loc(pd.Timestamp(d)); 
    if i >= len(C.index) - 1: return np.nan
    x = C[s].iloc[i:].dropna(); return (x.iloc[-1] / x.iloc[0] - mk.iloc[-1] / mk.iloc[i]) * 100 if len(x) > 1 else np.nan
A['baad_mein_vs_bazaar_pct'] = [round(since(r.symbol, r.date), 2) for r in A.itertuples()]
A.to_csv(P('data', 'shock_avoid.csv'), index=False)
# ---- HALCHAL alert (f74 + user 15 Nov: 'disha nahi, par kuch bada hone wala hai — ye bhi kaam ki baat') ----
# f74: kal +5% (lift 3.4), RS 3m top 10% (1.8-2.5), volume 5d 1.8x (2.0-2.4), 52w high paas (1.3-1.6) = top mover banne ka mauka badhta,
# DISHA nahi. + nateeje 10 din mein (movers ka 55% wajah). Score = in ishaaron ki ginti; >=3 = halchal list. Live jaanch: agle 5 din
# ka |chaal| bazaar ke ausat |chaal| se kitna bada (1.0 = kuch khaas nahi). Paise ka faisla isse nahi — sirf nazar aur seekh.
r1p = r1 * 100
feat = {'kal_+5%': r1p.iloc[-1] >= 5, 'RS_top10%': (C.iloc[-1] / C.iloc[-64] - 1).rank(pct=True) >= 0.9,
        'vol_5d_1.8x': V.iloc[-5:].mean() >= 1.8 * V.iloc[-55:-5].mean(), '52w_high_paas': C.iloc[-1] >= 0.95 * Hh.iloc[-250:].max()}
try:
    bm = pd.read_csv(P('data', 'corp', 'board_meetings.csv')); bm['d'] = pd.to_datetime(bm.date, format='%d-%b-%Y', errors='coerce')
    soon = set(bm[(bm.d > today) & (bm.d <= today + pd.Timedelta(days=14))].symbol)
except Exception: soon = set()
feat['nateeje_10din'] = pd.Series({s_: s_ in soon for s_ in C.columns})
FS = pd.DataFrame(feat).fillna(False); FS['score'] = FS.sum(axis=1)
HL = FS[FS.score >= 3].sort_values('score', ascending=False)
HF = P('data', 'halchal_log.csv')
log = pd.read_csv(HF) if os.path.exists(HF) else pd.DataFrame(columns=['date', 'symbol', 'score', 'kyun', 'move5_abs', 'mkt5_abs', 'ratio'])
log = log[log.date != str(today.date())]
log = pd.concat([log, pd.DataFrame([dict(date=str(today.date()), symbol=s_, score=int(r.score), kyun='+'.join(k for k in feat if r[k]))
                                    for s_, r in HL.iterrows()])], ignore_index=True)
absr = r1.abs()
for i, r in log[log.ratio.isna()].iterrows():
    try: j = C.index.get_loc(pd.Timestamp(r.date))
    except KeyError: continue
    if j + 5 < len(C.index) and r.symbol in C.columns:
        m = abs(C[r.symbol].iloc[j + 5] / C[r.symbol].iloc[j] - 1) * 100
        mk5 = (abs(C.iloc[j + 5] / C.iloc[j] - 1) * 100).median()
        log.loc[i, ['move5_abs', 'mkt5_abs', 'ratio']] = [round(m, 2), round(mk5, 2), round(m / mk5, 2) if mk5 else np.nan]
log.to_csv(HF, index=False)
r21 = C.iloc[-1] / C.iloc[-22] - 1
o = [f'# Jhatka-watch — {today:%d %b %Y} (f86)', '',
     'Seekh: bade gainer ka agle din peechha = fayda nahi; -10% volume wali giravat ke baad 60 din kamzori. Isliye ye list = 60 din AVOID.', '']
mine = A[A.symbol.isin(H)]
o += ['## ⚠️ Hamari holdings mein jhatka'] + ([f'- {r.symbol}: {r.date} {r.kyun} ({r.din_ka_pct:+.1f}%) → bechne par socho, stop jaancho' for r in mine.itertuples()] or ['- koi nahi ✅']) + ['']
td = A[A.date == today.date()]
o += [f'## Aaj naye ({len(td)})'] + [f'- {r.symbol} ({r.liq}) {r.kyun} {r.din_ka_pct:+.1f}%' for r in td.itertuples()] + ['']
o += [f'## AVOID list (pichhle 60 din, {len(A)} share) — data/shock_avoid.csv', ', '.join(A.symbol.head(60)), '']
g = A.dropna(subset=['baad_mein_vs_bazaar_pct']).groupby(A.kyun.str[:7]).baad_mein_vs_bazaar_pct.agg(['count', 'mean'])
o += ['## Paper jaanch: list mein aane ke baad bazaar se kitna aage(+)/peeche(-) — minus = niyam sahi'] + [f'- {k}: {int(r["count"])} share, ausat {r["mean"]:+.1f}%' for k, r in g.iterrows()] + ['']
o += [f'## Halchal alert — kuch bada ho sakta hai (disha PATA NAHI), {len(HL)} share'] + \
     [f'- {s_} ({liq.get(s_)}) score {int(r.score)}: ' + ', '.join(k for k in feat if r[k]) + (' ⚠️AVOID list' if s_ in set(A.symbol) else '') for s_, r in HL.head(15).iterrows()]
done = log.dropna(subset=['ratio'])
o += [f'- Live jaanch ({len(done)} purane alert): agle 5 din ki chaal aam share se {done.ratio.median():.1f}x (1.0 = kuch khaas nahi)' if len(done) else '- Live jaanch: 5 din baad se shuru'] + ['']
o += ['## Mahine (21 din) ka hisaab — A/B', 'Top 10 chadhe: ' + ', '.join(f'{s} {v * 100:+.0f}%' for s, v in r21.nlargest(10).items()),
      'Top 10 gire: ' + ', '.join(f'{s} {v * 100:+.0f}%' for s, v in r21.nsmallest(10).items()),
      '(gire hue agle 3 mahine bhi aksar peeche — f86; chadhe hue mein aage koi khaas fayda nahi)']
open(P('data', 'shock_watch.md'), 'w').write('\n'.join(o) + '\n'); print('\n'.join(o))
