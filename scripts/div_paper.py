"""PAPER: DIV_RUNUP — dividend run-up (user OK 5 Nov 2026 'Ha dal do'; study f64, study/ni_dividend.py). No real money.
Rules (fixed in advance, same as the backtest):
 - Source: data/corp/actions_all.csv (NSE corporate actions robot scripts/corp_actions.py). Only announced dividends.
 - Entry at that day's close (~2:15-3:25 PM): ex-date 2..6 trading days ahead (backtest entry = ex-6), dividend/close >= 2%,
   never liquidity D, price in data/daily_all. One entry per symbol+ex-date. Rs 50,000 each, Rs 5,00,000 book, max 10 open.
 - Exit at close on the cum day (1 trading day before ex). Stop -6%: if day low <= entry*0.94 exit at min(open, stop).
 - Cost 0.25% per round trip (delivery STT 0.1%+0.1% + charges). Dividend itself is NOT counted (we sell before ex).
Files: paper/div_state.json, paper/div_journal.csv; section in paper/reports/<date>.md."""
import os, json, re, datetime as dt, pandas as pd, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P = os.path.join(ROOT, 'paper')
SF, JF = os.path.join(P, 'div_state.json'), os.path.join(P, 'div_journal.csv')
IST = dt.timezone(dt.timedelta(hours=5, minutes=30)); now = dt.datetime.now(IST)
SIZE, SLOTS, COST, STOP, MINY = 50000.0, 10, 0.0025, 0.06, 2.0
HOL = {dt.date(2026, 11, 10), dt.date(2026, 11, 24), dt.date(2026, 12, 25)}


def tdays(a, b):
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in HOL: n += 1
    return n


def amount(s):
    v = re.findall(r'(?:Rs\.?|Re\.?|INR|₹)\s*([0-9]+(?:\.[0-9]+)?)', str(s), flags=re.I)
    return sum(float(x) for x in v) if v else np.nan


rd = lambda f: pd.read_csv(os.path.join(ROOT, 'data', 'daily_all', f), index_col=0, parse_dates=True)
C, L, O = rd('close.csv.gz'), rd('low.csv.gz'), rd('open.csv.gz')
day = C.index[-1]; today = day.date()
state = json.load(open(SF)) if os.path.exists(SF) else {'cash': 500000.0, 'pos': {}, 'done': [], 'start': str(today), 'last_day': None}
journal = pd.read_csv(JF).to_dict('records') if os.path.exists(JF) else []
lines = []
if state['last_day'] == str(today):
    print('already ran for', today)
else:
    px, lo, op = C.loc[day], L.loc[day], O.loc[day]
    # exits
    for key, q in list(state['pos'].items()):
        s = q['symbol']; exd = dt.date.fromisoformat(q['ex_date'])
        c_, l_, o_ = px.get(s), lo.get(s), op.get(s)
        if pd.isna(c_): continue
        stop = q['entry'] * (1 - STOP); why = None
        if not pd.isna(l_) and l_ <= stop: price, why = min(o_ if not pd.isna(o_) else stop, stop), 'stop -6%'
        elif tdays(today, exd) <= 1: price, why = float(c_), 'cum दिन'
        if why:
            ret = (price / q['entry'] - 1) * 100 - COST * 100
            state['cash'] += q['units'] * price - q['units'] * q['entry'] * COST
            journal.append(dict(symbol=s, ex_date=q['ex_date'], yield_pct=q['yield_pct'], entry_date=q['entry_date'], entry=q['entry'],
                                exit_date=str(today), exit=round(price, 2), why=why, ret_pct=round(ret, 2), pnl=round(q['units'] * q['entry'] * ret / 100)))
            lines.append(f'- बेचा {s} @{price:.2f} ({why}), {ret:+.2f}% खर्च बाद')
            del state['pos'][key]
    # entries
    af = os.path.join(ROOT, 'data', 'corp', 'actions_all.csv'); av = os.path.join(P, 'avoid_liquidity_D.txt')
    AV = {l_.strip() for l_ in open(av) if l_.strip() and not l_.startswith('#')} if os.path.exists(av) else set()
    if os.path.exists(af):
        A = pd.read_csv(af)
        A = A[A.subject.fillna('').str.contains('dividend', case=False)].copy()
        A['exd'] = pd.to_datetime(A.ex_date, errors='coerce', dayfirst=True).dt.date
        A = A[A.exd.notna() & (A.exd > today)].drop_duplicates(['symbol', 'exd'])
        A['div_rs'] = A.subject.apply(amount)
        A['close'] = A.symbol.map(px)
        A['yield_pct'] = A.div_rs / A.close * 100
        A['td'] = A.exd.apply(lambda d: tdays(today, d))
        A = A[(A.td >= 2) & (A.td <= 6) & (A.yield_pct >= MINY) & ~A.symbol.isin(AV) & A.close.notna()].sort_values('yield_pct', ascending=False)
        for _, r in A.iterrows():
            key = f'{r.symbol}_{r.exd}'
            if key in state['pos'] or key in state['done'] or len(state['pos']) >= SLOTS or state['cash'] < SIZE: continue
            units = int(SIZE // r.close)
            if units < 1: continue
            state['cash'] -= units * r.close
            state['pos'][key] = dict(symbol=r.symbol, ex_date=str(r.exd), yield_pct=round(r.yield_pct, 2), entry=round(float(r.close), 2), entry_date=str(today), units=units)
            state['done'].append(key)
            lines.append(f'- खरीदा {r.symbol} @{r.close:.2f} × {units} (dividend ₹{r.div_rs}, yield {r.yield_pct:.2f}%, ex {r.exd}; stop {r.close * (1 - STOP):.2f}, बेच ex से एक दिन पहले)')
    state['last_day'] = str(today)
    json.dump(state, open(SF, 'w'), indent=1); pd.DataFrame(journal).to_csv(JF, index=False)

px = C.iloc[-1]
val = state['cash'] + sum(q['units'] * float(px.get(q['symbol'], q['entry'])) for q in state['pos'].values())
J = pd.DataFrame(journal)
rep = ['', '## Dividend run-up (DIV_RUNUP, f64) — paper',
       f"- किताब ₹{val:,.0f} (शुरू ₹5,00,000, {state['start']} से), नकद ₹{state['cash']:,.0f}; बंद सौदे {len(J)}"
       + (f", जीत {(J.ret_pct > 0).mean() * 100:.0f}%, औसत {J.ret_pct.mean():+.2f}%" if len(J) else '')] + lines
rep += [f"- खुला {q['symbol']}: {q['entry']} → {float(px.get(q['symbol'], q['entry'])):.2f}, ex {q['ex_date']}" for q in state['pos'].values()]
if not lines and not state['pos']:
    rep.append('- आज कोई dividend नियम में नहीं (yield 2%+ और ex 2-6 दिन आगे वाला नहीं)')
rf = os.path.join(P, 'reports', f'{now.date()}.md'); os.makedirs(os.path.dirname(rf), exist_ok=True)
with open(rf, 'a') as fh: fh.write('\n'.join(rep) + '\n')
print('\n'.join(rep))
