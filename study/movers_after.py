"""Top gainers / losers ke BAAD kya hota hai? (user 15 Nov 2026: 'jo haath se nikal gaya, kya hum use pakad sakte the / ab bhi pakad sakte hain')
f74 ne dikhaya: PEHLE se disha batana technical se mumkin nahi (halchal ka ishaara, disha ka nahi). Isliye ab ulta sawaal:
kal ka bada mover dekh kar AGLE din (2:15-3:25 ~ close t+1) kharidne/bechne se kuch milta hai?
Events (A/B shares, D hata kar; signal close t par, ENTRY close t+1 = look-ahead nahi):
  D_UP   din +10%+ aur volume 3x+ (50 din ausat)  -> nateeje/khabar jaisa jhatka
  D_UP_T wahi + 200 DMA upar + 52w high (breakaway)   | D_UP_W wahi + 200 DMA neeche
  D_DN   din -10%+ aur volume 3x+                   | D_DN_T wahi par 200 DMA upar (uptrend mein jhatka)
  W_UP   5 din +20%+ (hafte ka top)  | W_DN 5 din -20%+
  M_UP   21 din mein top 20 (mahine ka top) | M_DN mahine ke bottom 20
Har ek: 5/20/60 din aage, Nifty-jaisa bazaar (sab shares ka ausat) se zyada, kharcha 0.25% ghata kar; daur-war; 2008+COVID hata kar;
placebo = usi din ke baaki A/B shares (excess ka matlab hi yahi); OHLC: agle din open->close, aur 20 din ka best high / worst low.
Ek share ek baar har 20 din (thin) taaki ek hi jhatka baar baar na gine.
Data: universe500 branch (u1000+u2000, 2002-2026), nc.load(). Output study/results/movers_after.csv + print.
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
P = nc.load(); a, c, h, l, o, v = P['a'], P['c'], P['h'], P['l'], P['o'], P['v']
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
vr = v / v.rolling(50, min_periods=40).mean().shift(1)
tv = (c * v).rolling(20, min_periods=15).median()            # traded value (Rs) — no look-ahead liquidity
liq = tv >= 1e7                                             # >= Rs 1 cr/din (A/B jaisa, us waqt ke hisaab se)
up200 = a > a.rolling(200, min_periods=180).mean()
hi52 = a >= a.rolling(250, min_periods=200).max() * 0.98
r5 = a.pct_change(5, fill_method=None); r21 = a.pct_change(21, fill_method=None)
rk21u = r21.where(liq).rank(axis=1, ascending=False); rk21d = r21.where(liq).rank(axis=1)
E = {
    'D_UP': (r1 >= 0.10) & (vr >= 3), 'D_DN': (r1 <= -0.10) & (vr >= 3),
    'W_UP': r5 >= 0.20, 'W_DN': r5 <= -0.20,
    'M_UP': rk21u <= 20, 'M_DN': rk21d <= 20,
}
E['D_UP_T'] = E['D_UP'] & up200.shift(1).fillna(False) & hi52
E['D_UP_W'] = E['D_UP'] & up200.shift(1).eq(False)
E['D_DN_T'] = E['D_DN'] & up200.shift(1).fillna(False)
F, mkt = nc.fwd(P, hs=(5, 20, 60))
rows = []
for k, ev in E.items():
    ev = nc.thin((ev & liq).fillna(False), 20)
    ev1 = ev.shift(1).fillna(False)          # entry close t+1
    rs = nc.evaluate(ev1, F, k, hs=(5, 20, 60))
    # OHLC: next day open->close and gap (t+1), relative to market day move
    oc = ((a.shift(-1) / (o.shift(-1) * 1.0) - 1) * 100).where(ev)  # open t+1 -> close t+1 (a and o both adjusted)
    gp = ((o.shift(-1) / a - 1) * 100).where(ev)
    up, dn, big = nc.mfe_mae(P, ev1, 20)
    for r in rs:
        r.update(next_gap=round(gp.stack().mean(), 2), next_open_close=round(oc.stack().mean(), 2), mfe20=up, mae20=dn, mae20_lt10=big)
    rows += rs
T = pd.DataFrame(rows)
T['excess_net'] = T.excess - nc.COST
out = os.path.join(nc.REPO, 'study', 'results', 'movers_after.csv'); T.to_csv(out, index=False)
pd.set_option('display.width', 250)
show = T[T.era.isin(['ALL', '2003-12', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'])]
print(show.pivot_table(index=['study', 'era'], columns='h', values=['excess_net', 't_dates', 'n'], aggfunc='first').round(2).to_string())
print(T[(T.era == 'ALL') & (T.h == 20)][['study', 'n', 'next_gap', 'next_open_close', 'mfe20', 'mae20', 'mae20_lt10', 'win_vs_mkt']].to_string())
