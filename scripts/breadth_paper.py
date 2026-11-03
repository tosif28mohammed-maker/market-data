"""PAPER: BREADTH_DIP — buy fresh deep dips only on market-wide sell-off days (user OK 3 Nov 2026 'jod do'; study f57, study/breadth_dip.py). No real money.
Rules (fixed in advance, same as the backtest):
 - Universe: paper/gap_universe.csv (A/B liquidity), never class D (paper/avoid_liquidity_D.txt).
 - Per stock threshold thr = its own 10% lowest distance of close from SMA20, learned on 2013-20 (paper/breadth_thr.csv, fixed).
 - deep = close/SMA20 - 1 <= thr.  breadth = deep stocks / all universe stocks with a valid SMA20 (same as backtest).
 - Entry (at that day's close, ~3:25 PM): breadth >= 20% AND stock freshly deep (not deep yesterday) AND close > its 200-day average.
   Deepest first (most below its threshold); max 10 open positions, Rs 10,000 each from a Rs 1,00,000 book.
 - Exit (at close): first close >= previous day's SMA20, or after 21 trading days. No stop (as tested; worst 10% of trades were -7..-9%).
 - Cost 0.35% per round trip. Replay from 1 Jan 2026 on the first run, then live day by day.
Files: paper/breadth_state.json, breadth_journal.csv, breadth_history.csv (daily book + breadth); section in paper/reports/<date>.md."""
import os, json, time, datetime as dt, numpy as np, pandas as pd, yfinance as yf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(ROOT, 'paper')
SF, JF, HF = (os.path.join(P, f) for f in ('breadth_state.json', 'breadth_journal.csv', 'breadth_history.csv'))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30)); now = dt.datetime.now(IST)
GATE, SLOTS, SIZE, COST, MAXD = 0.20, 10, 10000.0, 0.0035, 21
U = pd.read_csv(os.path.join(P, 'gap_universe.csv')); av_f = os.path.join(P, 'avoid_liquidity_D.txt')
AV = {l.strip() for l in open(av_f) if l.strip() and not l.startswith('#')} if os.path.exists(av_f) else set()
syms = [s for s in U.symbol if s not in AV]
THR = pd.read_csv(os.path.join(P, 'breadth_thr.csv')).set_index('symbol').thr_sma20
state = json.load(open(SF)) if os.path.exists(SF) else {'cash': 100000.0, 'pos': {}, 'last_day': '2025-12-31', 'start': None}
def download(tickers, period):
    out = {}
    for i in range(0, len(tickers), 100):
        part = tickers[i:i + 100]; df = None
        for a in range(3):
            try:
                df = yf.download([f'{s}.NS' for s in part], period=period, interval='1d', auto_adjust=False, progress=False, threads=True, group_by='ticker'); break
            except Exception as e: print(e); time.sleep(5)
        if df is None: continue
        for s in part:
            try: x = df[f'{s}.NS']['Close'].dropna()
            except Exception: continue
            if len(x): x.index = pd.to_datetime(x.index).tz_localize(None).normalize(); out[s] = x
        time.sleep(1)
    return pd.DataFrame(out).sort_index()
C = download(syms, '2y').ffill(limit=5)
C = C[C.index <= pd.Timestamp(now.date())]
if not (now.hour >= 16 or C.index[-1].date() < now.date()): C = C[C.index < pd.Timestamp(now.date())]   # today's candle only after close
ma = C.rolling(20).mean(); ma200 = C.rolling(200).mean(); dist = C / ma - 1
thr = THR.reindex(C.columns)
deep = dist.le(thr, axis=1) & dist.notna() & thr.notna().values
breadth = deep.sum(1) / dist.notna().sum(1).clip(lower=1)
journal = pd.read_csv(JF).to_dict('records') if os.path.exists(JF) else []
hist = pd.read_csv(HF).to_dict('records') if os.path.exists(HF) else []
lines = []
days = [t for t in C.index if t > pd.Timestamp(state['last_day'])]
for t in days:
    i = C.index.get_loc(t); px = C.loc[t]
    # exits
    for s in list(state['pos']):
        q = state['pos'][s]; p = px.get(s)
        if pd.isna(p): continue
        q['days'] += 1
        prev_ma = ma[s].iloc[i - 1]
        if p >= prev_ma or q['days'] >= MAXD:
            proceeds = q['units'] * p * (1 - COST / 2); state['cash'] += proceeds; del state['pos'][s]
            why = 'SMA20 छुआ' if p >= prev_ma else f'{MAXD} दिन पूरे'
            journal.append(dict(strategy='BREADTH_DIP', symbol=s, entry_date=q['date'], entry_price=q['entry'], exit_date=str(t.date()), exit_price=round(float(p), 2),
                                days=q['days'], reason=why, pnl_rs=round(proceeds - q['cost'], 0), ret_pct=round((proceeds / q['cost'] - 1) * 100, 2)))
            if t == C.index[-1]: lines.append(f"- बेचा {s} @ {p:.2f} ({why}), {(proceeds / q['cost'] - 1) * 100:+.1f}%")
    # entries
    b = float(breadth.iloc[i])
    if b >= GATE and i > 0:
        fresh = deep.iloc[i] & ~deep.iloc[i - 1] & (C.iloc[i] > ma200.iloc[i])
        cands = fresh[fresh].index.difference(list(state['pos']))
        cands = (dist.iloc[i][cands] - thr[cands]).sort_values().index
        for s in cands:
            if len(state['pos']) >= SLOTS or state['cash'] < SIZE: break
            e = float(px[s]); state['pos'][s] = dict(units=SIZE * (1 - COST / 2) / e, entry=round(e, 2), date=str(t.date()), cost=SIZE, days=0,
                                                       sma20=round(float(ma[s].iloc[i]), 2)); state['cash'] -= SIZE
            if t == C.index[-1]: lines.append(f"- खरीदा {s} @ {e:.2f} (SMA20 {ma[s].iloc[i]:.2f}, दूरी {dist[s].iloc[i] * 100:.1f}%)")
    val = state['cash'] + sum(q['units'] * float(px.get(s, q['entry'])) for s, q in state['pos'].items() if not pd.isna(px.get(s)))
    hist = [h for h in hist if h['date'] != str(t.date())] + [dict(date=str(t.date()), value=round(val, 0), cash=round(state['cash'], 0), n=len(state['pos']), breadth=round(b, 3))]
    state['last_day'] = str(t.date()); state['start'] = state['start'] or str(t.date())
pd.DataFrame(hist).to_csv(HF, index=False); pd.DataFrame(journal).to_csv(JF, index=False); json.dump(state, open(SF, 'w'), indent=1)
last = C.index[-1]; px = C.iloc[-1]; b = float(breadth.iloc[-1])
val = state['cash'] + sum(q['units'] * float(px.get(s, q['entry'])) for s, q in state['pos'].items())
J = pd.DataFrame(journal)
rep = ['', '## Breadth dip (बाज़ार-भर घबराहट पर dip खरीद) — paper',
       f"- {last.date()}: breadth {b * 100:.1f}% ({'≥20% — खरीद का दिन' if b >= GATE else 'शांत, 20% से कम — नई खरीद नहीं'}); पिछले 5 दिन: " + ', '.join(f'{x * 100:.0f}%' for x in breadth.iloc[-5:]),
       f"- किताब ₹{val:,.0f} (शुरू ₹1,00,000, {state['start']} से replay/live), नकद ₹{state['cash']:,.0f}; बंद सौदे {len(J)}"
       + (f", जीत {(J.ret_pct > 0).mean() * 100:.0f}%, औसत {J.ret_pct.mean():+.2f}%" if len(J) else '')] + lines
rep += [f"- खुला {s}: {q['entry']} → {float(px.get(s, q['entry'])):.2f} ({(float(px.get(s, q['entry'])) / q['entry'] - 1) * 100:+.1f}%), {q['days']} दिन, बेच ≥ SMA20 {ma[s].iloc[-1]:.2f}" for s, q in state['pos'].items()]
rf = os.path.join(P, 'reports', f'{now.date()}.md'); os.makedirs(os.path.dirname(rf), exist_ok=True)
with open(rf, 'a') as fh: fh.write('\n'.join(rep) + '\n')
print('\n'.join(rep))
