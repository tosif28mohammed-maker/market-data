"""PAPER: monthly momentum portfolio (user OK 2 Nov 2026; study f55). No real money.
Rule (fixed in advance):
 - Universe: liquidity A/B stocks in paper/gap_universe.csv (never class D, paper/avoid_liquidity_D.txt).
 - On the last trading day of each month (and once at the start): rank by 12-1 month return (close 21 trading days ago / close 252 days ago - 1)
   among stocks whose close is above their 200-day average. Buy the top 10, equal Rs 10,000 each of a Rs 1,00,000 book (at that day's close).
 - Market filter: if the equal-weight basket of the universe is below its own 200-day average -> hold cash that month.
 - Hold until the next month-end, then rebalance. Cost 0.35% per round trip (delivery STT etc.).
 - Daily: mark positions to the day's close.
Files: paper/mom_state.json, paper/mom_journal.csv (closed positions), paper/mom_history.csv (daily book value);
       appends a section to paper/reports/<date>.md.
Data: Yahoo daily via yfinance (runs inside the daily GitHub robot)."""
import os, json, time, datetime as dt, numpy as np, pandas as pd, yfinance as yf
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(ROOT, 'paper')
SF = os.path.join(P, 'mom_state.json'); JF = os.path.join(P, 'mom_journal.csv'); HF = os.path.join(P, 'mom_history.csv')
IST = dt.timezone(dt.timedelta(hours=5, minutes=30)); now = dt.datetime.now(IST)
U = pd.read_csv(os.path.join(P, 'gap_universe.csv')); av_f = os.path.join(P, 'avoid_liquidity_D.txt')
AV = {l.strip() for l in open(av_f) if l.strip() and not l.startswith('#')} if os.path.exists(av_f) else set()
syms = [s for s in U.symbol if s not in AV]
state = json.load(open(SF)) if os.path.exists(SF) else {'cash': 100000.0, 'pos': {}, 'last_rebal': None, 'start': None}
COST = 0.0035
def download(tickers, period):
    out = {}
    for i in range(0, len(tickers), 100):
        part = tickers[i:i + 100]
        for a in range(2):
            try:
                df = yf.download([f'{s}.NS' for s in part], period=period, interval='1d', auto_adjust=False, progress=False, threads=True, group_by='ticker'); break
            except Exception as e: print(e); time.sleep(5); df = None
        if df is None: continue
        for s in part:
            try: x = df[f'{s}.NS']['Close'].dropna()
            except Exception: continue
            if len(x): x.index = pd.to_datetime(x.index).tz_localize(None).normalize(); out[s] = x
        time.sleep(1)
    return pd.DataFrame(out).sort_index()
held = list(state['pos'])
today = pd.Timestamp(now.date())
nxt = today + pd.offsets.BDay(1)
month_end = nxt.month != today.month
need_rebal = state['last_rebal'] is None or (month_end and state['last_rebal'] != str(today.date()))
closes = download(syms if need_rebal else held, '15mo' if need_rebal else '5d') if (need_rebal or held) else pd.DataFrame()
if len(closes):
    last_day = closes.index.max()
    if last_day.date() != today.date() and now.hour < 23: print('no data for today yet', last_day);
px = closes.ffill().iloc[-1] if len(closes) else pd.Series(dtype=float)
journal = pd.read_csv(JF).to_dict('records') if os.path.exists(JF) else []
lines = []
def value():
    return state['cash'] + sum(p['units'] * float(px.get(s, p['entry'])) for s, p in state['pos'].items())
if need_rebal and len(closes) > 260:
    C = closes.ffill(limit=5); ret = C.pct_change(fill_method=None).clip(-0.3, 0.3); bask = (1 + ret.mean(1).fillna(0)).cumprod()
    reg_ok = bask.iloc[-1] > bask.rolling(200).mean().iloc[-1]
    mom = C.shift(21).iloc[-1] / C.shift(252).iloc[-1] - 1; above = C.iloc[-1] > C.rolling(200).mean().iloc[-1]
    picks = mom[above & mom.notna() & C.iloc[-1].notna()].sort_values(ascending=False).index[:10].tolist() if reg_ok else []
    # sell everything not in picks
    for s in list(state['pos']):
        if s in picks: continue
        p = state['pos'].pop(s); exit_px = float(px.get(s, p['entry'])); proceeds = p['units'] * exit_px * (1 - COST / 2)
        state['cash'] += proceeds
        journal.append(dict(strategy='MOM_MONTHLY', symbol=s, entry_date=p['date'], entry_price=p['entry'], exit_date=str(today.date()), exit_price=round(exit_px, 2),
                            pnl_rs=round(proceeds - p['cost'], 0), ret_pct=round((proceeds / p['cost'] - 1) * 100, 2)))
    val = value(); target = val / 10 if picks else 0
    for s in picks:
        if s in state['pos']: continue
        amt = min(target, state['cash'])
        if amt < 1000: continue
        e = float(px[s]); state['pos'][s] = dict(units=amt * (1 - COST / 2) / e, entry=round(e, 2), date=str(today.date()), cost=amt, mom=round(float(mom[s]) * 100, 1)); state['cash'] -= amt
    state['last_rebal'] = str(today.date()); state['start'] = state['start'] or str(today.date())
    lines.append(f"- आज rebalance ({'बाज़ार filter ठीक: खरीद' if reg_ok else 'बाज़ार 200 DMA के नीचे: नकद'}). नए 10: " + (', '.join(f"{s} (12-1 महीने {state['pos'][s]['mom']}%)" for s in picks if s in state['pos']) or 'कोई नहीं'))
val = value()
hist = pd.read_csv(HF).to_dict('records') if os.path.exists(HF) else []
hist = [h for h in hist if h['date'] != str(today.date())] + [dict(date=str(today.date()), value=round(val, 0), cash=round(state['cash'], 0), n=len(state['pos']))]
pd.DataFrame(hist).to_csv(HF, index=False); pd.DataFrame(journal).to_csv(JF, index=False)
json.dump(state, open(SF, 'w'), indent=1)
pos_lines = [f"- {s}: {p['entry']} → {float(px.get(s, p['entry'])):.2f} ({(float(px.get(s, p['entry'])) / p['entry'] - 1) * 100:+.1f}%)" for s, p in state['pos'].items()]
rep = ['', '## Momentum (महीने के top-10) — paper', f"- किताब: ₹{val:,.0f} (शुरू ₹1,00,000 पर {state['start']}), नकद ₹{state['cash']:,.0f}"] + lines + pos_lines
rf = os.path.join(P, 'reports', f'{today.date()}.md'); os.makedirs(os.path.dirname(rf), exist_ok=True)
with open(rf, 'a') as fh: fh.write('\n'.join(rep) + '\n')
print('\n'.join(rep))
