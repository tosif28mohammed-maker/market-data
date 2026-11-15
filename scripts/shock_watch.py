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
C, V = rd('close.csv.gz'), rd('volume.csv.gz')
liq = pd.read_csv(P('study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
AB = [s for s in C.columns if liq.get(s) in ('A', 'B')]
C, V = C[AB], V[AB]
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
o += ['## Mahine (21 din) ka hisaab — A/B', 'Top 10 chadhe: ' + ', '.join(f'{s} {v * 100:+.0f}%' for s, v in r21.nlargest(10).items()),
      'Top 10 gire: ' + ', '.join(f'{s} {v * 100:+.0f}%' for s, v in r21.nsmallest(10).items()),
      '(gire hue agle 3 mahine bhi aksar peeche — f86; chadhe hue mein aage koi khaas fayda nahi)']
open(P('data', 'shock_watch.md'), 'w').write('\n'.join(o) + '\n'); print('\n'.join(o))
