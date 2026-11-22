"""Weekly scoreboard (Tosif, 22 Nov 2026): not 'how many studies' but WHICH RULE IS ACTUALLY MAKING MONEY in paper trading.
Pure Python from paper/*journal*.csv (no AI). Bar (Tosif 19 Nov): hit >= 40% (never < 35%) AND real avg win >= ~2x avg loss, net > 0.
Writes data/scoreboard.md + data/scoreboard_history.csv (one row per strategy per week)."""
import os, csv, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)
def rd(p): return list(csv.DictReader(open(P(p), encoding='utf-8'))) if os.path.exists(P(p)) else []
def f(x):
    try: return float(x)
    except Exception: return None

T = []   # (strategy, mode, exit_date, pnl)
for r in rd('paper/journal.csv'):
    if r.get('exit_date') and f(r.get('pnl_rs')) is not None: T.append((r['strategy'], r.get('mode') or 'live', r['exit_date'], f(r['pnl_rs'])))
for r in rd('paper/intra_journal.csv'):
    if f(r.get('pnl_rs')) is not None: T.append(('IP_' + r['strat'], 'live', r['date'], f(r['pnl_rs'])))
for r in rd('paper/condor_journal.csv'):
    if r.get('exit_date') and f(r.get('rs')) is not None: T.append(('CONDOR_' + r['book'], 'live', r['exit_date'], f(r['rs'])))
for r in rd('paper/div_journal.csv'):
    if r.get('exit_date') and f(r.get('pnl')) is not None: T.append(('DIV_RUNUP', 'live', r['exit_date'], f(r['pnl'])))
for r in rd('paper/breadth_journal.csv'):
    if r.get('exit_date') and f(r.get('pnl_rs')) is not None: T.append((r['strategy'], 'replay' if r['exit_date'] < '2026-11-01' else 'live', r['exit_date'], f(r['pnl_rs'])))
for name in ('fut_learn_journal', 'rare_fut_journal'):
    for r in rd(f'paper/{name}.csv'):
        if r.get('status') != 'OPEN' and f(r.get('fut_pnl')) is not None: T.append((name.upper().replace('_JOURNAL', ''), 'live', r.get('close_date', ''), f(r['fut_pnl'])))

today = dt.date.today(); wk = (today - dt.timedelta(days=7)).isoformat()
def stats(xs):
    w = [x for x in xs if x > 0]; l = [-x for x in xs if x <= 0]
    hit = 100 * len(w) / len(xs) if xs else 0
    aw = sum(w) / len(w) if w else 0; al = sum(l) / len(l) if l else 0
    ratio = aw / al if al else (9.9 if aw else 0)
    net = sum(xs)
    if len(xs) < 10: verdict = 'अभी कम सौदे'
    elif hit >= 40 and ratio >= 1.8 and net > 0: verdict = '✅ पास (कमा रहा)'
    elif net > 0 and (hit >= 35 and ratio >= 1.3 or hit >= 55): verdict = '🟡 ठीक-ठाक'
    else: verdict = '❌ फेल'
    return dict(n=len(xs), hit=round(hit), aw=round(aw), al=round(al), ratio=round(ratio, 2), net=round(net), verdict=verdict)

strats = sorted({(s, m) for s, m, _, _ in T})
rows = []
for s, m in strats:
    xs = [p for s2, m2, d, p in T if s2 == s and m2 == m]
    xw = [p for s2, m2, d, p in T if s2 == s and m2 == m and d >= wk]
    st = stats(xs); st.update(strategy=s, mode=m, week_n=len(xw), week_net=round(sum(xw))); rows.append(st)
rows.sort(key=lambda r: (r['mode'] != 'live', -r['net']))
md = [f'# Scoreboard — {today} (कौन सा नियम paper में सच में कमा रहा है)', '',
      'पास का पैमाना: जीत ≥40% और असली औसत जीत ≥ ~2× औसत हार, कुल फ़ायदा > 0 (10+ सौदे होने पर ही फ़ैसला)', '',
      '| नियम | किस्म | सौदे | जीत % | औसत जीत ₹ | औसत हार ₹ | जीत/हार | कुल ₹ | इस हफ़्ते (सौदे, ₹) | फ़ैसला |', '|---|---|---|---|---|---|---|---|---|---|']
for r in rows:
    md.append(f"| {r['strategy']} | {'असली-समय' if r['mode']=='live' else 'पुराना replay'} | {r['n']} | {r['hit']} | {r['aw']} | {r['al']} | {r['ratio']} | {r['net']} | {r['week_n']}, {r['week_net']} | {r['verdict']} |")
open(P('data', 'scoreboard.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
hp = P('data', 'scoreboard_history.csv'); new = not os.path.exists(hp)
with open(hp, 'a', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    if new: w.writerow(['week', 'strategy', 'mode', 'trades', 'hit', 'avg_win', 'avg_loss', 'ratio', 'net', 'verdict'])
    for r in rows: w.writerow([today.isoformat(), r['strategy'], r['mode'], r['n'], r['hit'], r['aw'], r['al'], r['ratio'], r['net'], r['verdict']])
print('\n'.join(md))
