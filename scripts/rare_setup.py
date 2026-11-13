"""BADA MAUKA (rare A+ setup) + futures PAPER kitaab.
User 13 Nov 2026: intraday/futures ROZ nahi karenge (SEBI FY25: 91% F&O traders ghaate mein). Sirf kabhi-kabhar,
jab kai cheezein ek saath milein, tab ek future ka mauka bataana. Ye robot wahi dhundhta hai aur PAPER mein chalata hai
(asli paisa/order nahi). 2-3 mahine baad dekhenge ki aise mauke futures mein sach mein kaam karte hain ya nahi.

A+ shart (sab ek saath):
  1. data/decision.csv mein score >= 6 aur 3+ alag signal family (ek-do signal nahi, kai)
  2. Liquidity A + F&O wala share (paper/gap_universe.csv fo=1)
  3. Koi ⚠️ nahi (khabar wali giravat, kam delivery, kamzor fundamentals/industry/mahina)
  4. Nateeje 10 din mein nahi
  5. Nifty 200 DMA ke upar AUR (tezi mode: 10 din +5%  YA  ghabrahat-dip: breadth >= 20%)
Discipline (experts ke niyam): ek waqt mein sirf 1 khula sauda; mahine mein max 2; lagatar 2 haar -> 10 kaarobaari din band;
R:R kam se kam 1:1.5; stop close par (user ka tareeka); 20 kaarobaari din baad band.
Tulna: wahi margin cash share mein lagaate to kya hota (leverage ka asli asar dikhe).
Output: data/rare_setup.md, paper/rare_fut_journal.csv, data/fo_lots.csv (NSE lot size cache).
"""
import os, io, datetime as dt, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(R, *a)
rd = lambda f: pd.read_csv(P('data', 'daily_all', f), index_col=0, parse_dates=True)
C, H, L, O = rd('close.csv.gz'), rd('high.csv.gz'), rd('low.csv.gz'), rd('open.csv.gz')
today = C.index[-1]
MIN_SCORE, MIN_FAM, MIN_RR, MAX_DAYS, MARGIN = 6, 3, 1.5, 20, 0.20
COST = 0.0006  # futures: brokerage+STT+exchange+slippage ~0.06% notional round trip (andaza)
COST_CASH = 0.0025  # delivery: STT 0.1%x2 + baaki (andaza)

# ---- NSE lot size (cache); fallback = andaza ~Rs 7.5 lakh contract ----
def lots():
    f = P('data', 'fo_lots.csv')
    try:
        import requests
        for u in ('https://archives.nseindia.com/content/fo/fo_mktlots.csv', 'https://nsearchives.nseindia.com/content/fo/fo_mktlots.csv'):
            try:
                r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
                if r.ok and 'SYMBOL' in r.text.upper():
                    d = pd.read_csv(io.StringIO(r.text)); d.columns = [c.strip().upper() for c in d.columns]
                    sym = d['SYMBOL'].astype(str).str.strip()
                    num = d.drop(columns=[c for c in d.columns if c in ('UNDERLYING', 'SYMBOL')]).apply(
                        lambda s: pd.to_numeric(s.astype(str).str.strip(), errors='coerce'))
                    lot = num.bfill(axis=1).iloc[:, 0]
                    out = pd.DataFrame({'symbol': sym, 'lot': lot}).dropna(); out = out[out.lot > 0]
                    out.to_csv(f, index=False); return dict(zip(out.symbol, out.lot.astype(int))), 'NSE'
            except Exception as e:
                print('lots', u, e)
    except Exception as e:
        print('requests', e)
    if os.path.exists(f):
        d = pd.read_csv(f); return dict(zip(d.symbol, d.lot.astype(int))), 'cache'
    return {}, 'andaza'

LOT, LOTSRC = lots()
def lot_of(s, px):
    if s in LOT: return int(LOT[s]), True
    return max(1, int(round(750000 / px))), False

# ---- market mode (same as decision.py) ----
nf = pd.read_csv(P('data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
n10 = (nf.iloc[-1] / nf.iloc[-11] - 1) * 100; above200 = nf.iloc[-1] > nf.rolling(200).mean().iloc[-1]
try: br = float(pd.read_csv(P('paper', 'breadth_history.csv')).breadth.iloc[-1]) * 100
except Exception: br = 0.0
thrust, panic = n10 >= 5, br >= 20
mode_ok = above200 and (thrust or panic)

# ---- journal: update open trades ----
JF = P('paper', 'rare_fut_journal.csv')
cols = ['open_date', 'symbol', 'lot', 'lot_src', 'entry', 'stop', 'target', 'margin', 'status', 'close_date', 'exit', 'days',
        'fut_pnl', 'fut_pct_margin', 'cash_pnl', 'why']
J = pd.read_csv(JF) if os.path.exists(JF) else pd.DataFrame(columns=cols)
for i, t in J[J.status == 'OPEN'].iterrows():
    s = t.symbol
    if s not in C.columns: continue
    after = C.index[C.index > pd.Timestamp(t.open_date)]
    ex = None
    for k, d in enumerate(after, 1):
        h, c = H.at[d, s], C.at[d, s]
        if pd.notna(h) and h >= t.target: ex = (d, max(t.target, O.at[d, s]) if pd.notna(O.at[d, s]) else t.target, 'TARGET', k); break
        if pd.notna(c) and c <= t.stop: ex = (d, c, 'STOP', k); break
        if k >= MAX_DAYS and pd.notna(c): ex = (d, c, 'TIME', k); break
    if ex:
        d, px, why, k = ex; notional = t.lot * t.entry
        fp = t.lot * (px - t.entry) - COST * notional
        qty_cash = int(t.margin // t.entry); cp = qty_cash * (px - t.entry) - COST_CASH * qty_cash * t.entry
        J.loc[i, ['status', 'close_date', 'exit', 'days', 'fut_pnl', 'fut_pct_margin', 'cash_pnl']] = [
            why, d.date().isoformat(), round(px, 2), k, round(fp), round(fp / t.margin * 100, 1), round(cp)]

# ---- discipline gates ----
closed = J[J.status != 'OPEN'].sort_values('close_date')
open_n = int((J.status == 'OPEN').sum())
month_n = int((pd.to_datetime(J.open_date).dt.to_period('M') == today.to_period('M')).sum()) if len(J) else 0
pause = ''
if len(closed) >= 2 and (closed.fut_pnl.tail(2) < 0).all():
    last_loss = pd.Timestamp(closed.close_date.iloc[-1]); gap = len(C.index[C.index > last_loss])
    if gap < 10: pause = f'lagatar 2 haar -> {10 - gap} kaarobaari din aur band'

# ---- today's A+ candidates ----
D = pd.read_csv(P('data', 'decision.csv'))
U = pd.read_csv(P('paper', 'gap_universe.csv')).set_index('symbol')
fo = set(LOT) if LOTSRC != 'andaza' else set(U.index[U.fo == 1])  # NSE ki taaza F&O list pehle
D['why'] = D['why'].fillna('')
cand = D[(D.score >= MIN_SCORE) & (D.families >= MIN_FAM) & (D.liq == 'A') & D.symbol.isin(fo)
         & ~D.why.str.contains('⚠') & D.results.isna()].copy()
cand['rr'] = (cand.target - cand.entry) / (cand.entry - cand.stop)
cand = cand[cand.rr >= MIN_RR].sort_values(['score', 'families'], ascending=False)

near = D[(D.score >= 4) & (D.liq == 'A') & D.symbol.isin(fo)].head(5)
new = None
if mode_ok and len(cand) and open_n == 0 and month_n < 2 and not pause:
    r = cand.iloc[0]; lot, real = lot_of(r.symbol, r.entry)
    new = dict(open_date=today.date().isoformat(), symbol=r.symbol, lot=lot, lot_src='NSE' if real else 'andaza',
               entry=r.entry, stop=r.stop, target=r.target, margin=round(MARGIN * lot * r.entry), status='OPEN',
               why=f'score {r.score}, {r.families} family: {r.fam}')
    J = pd.concat([J, pd.DataFrame([new])], ignore_index=True)
J.to_csv(JF, index=False)

# ---- report ----
o = [f'# Bada mauka (A+ setup) + futures PAPER — {today:%d %b %Y} ka data', '',
     'Niyam (user 13 Nov): intraday/futures roz NAHI. Sirf jab kai cheezein ek saath milein. Ye PAPER hai, asli order nahi.', '',
     f"Bazaar: Nifty 200 DMA {'upar ✅' if above200 else 'neeche ❌'} | 10 din {n10:+.1f}% {'(tezi ✅)' if thrust else ''} | breadth {br:.0f}% {'(ghabrahat-dip ✅)' if panic else ''} → "
     f"{'bazaar shart PURI' if mode_ok else 'bazaar shart adhoori — aaj bada mauka nahi'}", '']
if new:
    lot = new['lot']; risk = lot * (new['entry'] - new['stop'])
    o += [f"## 🔔 AAJ BADA MAUKA: {new['symbol']}",
          f"- Future 1 lot = {lot} share ({new['lot_src']}), saamaan ~₹{lot * new['entry']:,.0f}, margin ~₹{new['margin']:,.0f} (andaza 20%)",
          f"- Entry ~{new['entry']} (2:15-3:25 PM) | stop {new['stop']} close par | target {new['target']} | 20 din",
          f"- Stop lage to nuksaan ~₹{risk:,.0f} = margin ka {risk / new['margin'] * 100:.0f}%  ← leverage ka khatra",
          f"- Kyun: {new['why']}", '- Claude se khabar jaanch karwao. Asli paisa sirf user ki OK aur paper ke achhe nateeje ke baad.', '']
else:
    why = []
    if not mode_ok: why.append('bazaar shart nahi')
    if not len(cand): why.append('koi share saari shartein poori nahi karta')
    if open_n: why.append('ek sauda pehle se khula')
    if month_n >= 2: why.append('is mahine 2 ho chuke')
    if pause: why.append(pause)
    o += ['## Aaj bada mauka: NAHI — ' + '; '.join(why), '']
if len(near):
    o += ['Paas wale (F&O, A, score ≥4 — abhi A+ nahi):'] + [f'- {r.symbol} score {r.score} ({r.fam}){" ⚠️" if "⚠" in r.why else ""}' for r in near.itertuples()] + ['']
op = J[J.status == 'OPEN']
if len(op):
    o += ['## Khula paper sauda'] + [f'- {t.symbol} {t.lot} @ {t.entry} (khola {t.open_date}) | stop {t.stop} | target {t.target} | aaj {C[t.symbol].iloc[-1]:.2f} → '
                                    f'₹{t.lot * (C[t.symbol].iloc[-1] - t.entry):+,.0f}' for t in op.itertuples() if t.symbol in C.columns] + ['']
cl = J[J.status != 'OPEN']
if len(cl):
    o += [f"## Hisaab ({len(cl)} band sauda)", f"- Futures: kul ₹{cl.fut_pnl.sum():+,.0f}, jeet {(cl.fut_pnl > 0).mean() * 100:.0f}%, sabse bura ₹{cl.fut_pnl.min():+,.0f} (margin ka {cl.fut_pct_margin.min():.0f}%)",
          f"- Wahi margin cash share mein: kul ₹{cl.cash_pnl.sum():+,.0f}", '']
o += [f'Lot size source: {LOTSRC}. Kharcha andaza: futures 0.06%, cash 0.25%. 2-3 mahine baad faisla: rakhna ya hatana.']
open(P('data', 'rare_setup.md'), 'w').write('\n'.join(o) + '\n')
print('\n'.join(o))
