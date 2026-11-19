"""Dost ka 'Hedged Strangle / Iron Condor' Pine Script — ASLI NSE option bhaav par test (user 19 Nov 2026).
Rules (Pine code ke default):
  Entry  : expiry ke agle trading din, OPEN par (Sep-2025 se pehle Thursday expiry -> Friday entry; ab Tuesday -> Wednesday).
           VIX (pichhla close) 10 se kam ya 22 se zyada -> hafta chhodo.
  Strike : S = Nifty open, em = S * VIX/100 * sqrt(din/365); SELL CE = ceil((S+k*em)/50)*50, SELL PE = floor((S-k*em)/50)*50,
           BUY hedges 300 point aur door.
  Exit   : target 60% premium, SL nuksaan 150% premium, warna expiry par Nifty close par settle.
  Cost   : 0.5 pt/leg/side slippage, Rs 300/lot round trip. Rs hamesha AAJ ke lot 65 par (puraane lot 75/50 nahi) — points asli hain.
Data: nse_opt/opt/*.csv.gz (scripts/fetch_nse_hist.py opt <year>, sideways.yml), NIFTY weekly 2019-02 se.
Variants:
  A  'close'    : target/SL sirf din ke close par (Pine 1H close jaisa, thoda mota)
  B  'intraday' : SL din ke andar chhua (us taraf ke sold leg ka HIGH, hedge ka LOW) to SL level par bahar; target close par
  plus k=1.0/1.25/1.5, VIX filter on/off, hold-to-expiry, entry close par.
Model check: har entry par dost ka Black-Scholes credit (VIX, put +2) vs asli credit.
Usage: NSE_OPT=nse_opt python study/condor_friend.py   -> study/results/cf_*.md / .csv
"""
import os, glob, math, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results'); os.makedirs(OUT, exist_ok=True)
SRC = os.environ.get('NSE_OPT', os.path.join(R, 'nse_opt')); CACHE = os.environ.get('CF_CACHE', '')
MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s); MD.append(s)

if CACHE and os.path.exists(CACHE):
    O = pd.read_pickle(CACHE)
else:
    fr = []
    for f in sorted(glob.glob(os.path.join(SRC, 'opt', '*.csv.gz'))):
        for ch in pd.read_csv(f, chunksize=2_000_000):
            fr.append(ch[ch.symbol == 'NIFTY'])
    O = pd.concat(fr)
    if CACHE: O.to_pickle(CACHE)
O = O.copy(); O['date'] = pd.to_datetime(O.date); O['exp'] = pd.to_datetime(O.exp); O['type'] = O.type.astype(str).str[0]
for c in ('open', 'high', 'low', 'close', 'settle', 'contracts'): O[c] = pd.to_numeric(O[c], errors='coerce').fillna(0)
O['px'] = np.where(O.contracts > 0, O.close, O.settle)
O['hi'] = np.where(O.contracts > 0, O.high, O.px); O['lo'] = np.where(O.contracts > 0, O.low, O.px)
O['op'] = np.where((O.contracts > 0) & (O.open > 0), O.open, np.nan)

def ix(n):
    d = pd.read_csv(os.path.join(R, 'data', f'{n}.csv'), parse_dates=['date']).set_index('date').sort_index()
    return d[~d.index.duplicated()].dropna(subset=['close'])
N = ix('NIFTY'); V = ix('INDIAVIX').close
days = N.index
exps = sorted(O.exp.dropna().unique()); exps = [pd.Timestamp(e) for e in exps if pd.Timestamp(e) >= pd.Timestamp('2019-02-14')]
G = {(d, e): x for (d, e), x in O[O.exp.isin(exps)].groupby(['date', 'exp'])}
LOT, COST, SLIP, STEP, HEDGE = 65, 300.0, 0.5, 50, 300

def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def bs(S, K, T, sg, r, call):
    if T <= 0 or sg <= 0: return max(S - K, 0) if call else max(K - S, 0)
    d1 = (math.log(S / K) + (r + sg * sg / 2) * T) / (sg * math.sqrt(T)); d2 = d1 - sg * math.sqrt(T)
    return S * ncdf(d1) - K * math.exp(-r * T) * ncdf(d2) if call else K * math.exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)
def model_val(S, T, iv, k):
    sc, sp, bc, bp = k
    return bs(S, sc, T, iv / 100, .065, True) + bs(S, sp, T, (iv + 2) / 100, .065, False) - bs(S, bc, T, iv / 100, .065, True) - bs(S, bp, T, (iv + 2) / 100, .065, False)

def legs_of(x):
    return {(t, k): (p, h, l, o) for t, k, p, h, l, o in zip(x.type, x.K, x.px, x.hi, x.lo, x.op)}

def run(k=1.0, vix_filter=True, tgt=60, sl=150, mode='close', entry_at='open', day_before=False, vlo=10, vhi=22):
    rows = []
    prev = None
    for e in exps:
        if prev is None: prev = e; continue
        ed = days[(days > prev) & (days < e)]; prev = e
        if not len(ed): continue
        d0 = ed[-1] if day_before else ed[0]
        if day_before: entry_at = 'close'
        vix = V[V.index <= d0] if day_before else V[V.index < d0]
        if not len(vix): continue
        vix = float(vix.iloc[-1])
        if vix_filter and (vix < vlo or vix > vhi):
            rows.append(dict(entry=d0, exp=e, skip='vix', vix=vix)); continue
        x = G.get((d0, e))
        if x is None: continue
        ch = legs_of(x)
        S = float(N.open[d0]) if entry_at == 'open' else float(N.close[d0])
        cal = (e - d0).days
        em = S * vix / 100 * math.sqrt(cal / 365)
        sc = math.ceil((S + k * em) / STEP) * STEP; sp = math.floor((S - k * em) / STEP) * STEP
        bc, bp = sc + HEDGE, sp - HEDGE
        need = [('C', sc), ('P', sp), ('C', bc), ('P', bp)]
        if any(q not in ch for q in need):
            rows.append(dict(entry=d0, exp=e, skip='strike_missing', vix=vix)); continue
        if entry_at == 'open':
            p = [ch[q][3] for q in need]
            if any(not np.isfinite(v) for v in p):  # no trade at open for a far strike -> use close (flag)
                p = [ch[q][3] if np.isfinite(ch[q][3]) else ch[q][0] for q in need]; flag = 'open_fallback'
            else: flag = ''
        else:
            p = [ch[q][0] for q in need]; flag = ''
        credit = p[0] + p[1] - p[2] - p[3] - 4 * SLIP
        T0 = ((e + pd.Timedelta(hours=15.5)) - (d0 + pd.Timedelta(hours=9.25))).total_seconds() / (365 * 86400)
        mcred = model_val(S, T0, vix, (sc, sp, bc, bp)) - 4 * SLIP
        mc_call = bs(S, sc, T0, vix / 100, .065, True) - bs(S, bc, T0, vix / 100, .065, True)
        mc_put = bs(S, sp, T0, (vix + 2) / 100, .065, False) - bs(S, bp, T0, (vix + 2) / 100, .065, False)
        rc_call, rc_put = p[0] - p[2], p[1] - p[3]
        if credit <= 0:
            rows.append(dict(entry=d0, exp=e, skip='no_credit', vix=vix)); continue
        exit_v, how, xd = None, 'expiry', e
        hold = days[(days >= d0) & (days <= e)]; miss_days = 0
        for d in hold:
            y = G.get((d, e))
            if y is None: continue
            c2 = legs_of(y)
            if any(q not in c2 for q in need): miss_days += 1; continue
            val = c2[need[0]][0] + c2[need[1]][0] - c2[need[2]][0] - c2[need[3]][0]
            if mode == 'intraday' and sl:
                up = float(N.high.get(d, S)) - S >= S - float(N.low.get(d, S))
                if up: worst = c2[need[0]][1] - c2[need[2]][2] + c2[need[1]][0] - c2[need[3]][0]
                else: worst = c2[need[1]][1] - c2[need[3]][2] + c2[need[0]][0] - c2[need[2]][0]
                worst = min(worst, HEDGE)
                if worst - credit >= credit * sl / 100 and not (d == d0 and entry_at == 'close'):
                    exit_v, how, xd = credit * (1 + sl / 100) + 4 * SLIP, 'SL', d; break
            if d == e: break  # expiry din: target/SL close par = settlement hi
            if tgt and credit - val >= credit * tgt / 100:
                exit_v, how, xd = val + 4 * SLIP, 'target', d; break
            if sl and -(credit - val) >= credit * sl / 100:
                exit_v, how, xd = val + 4 * SLIP, 'SL', d; break
        if exit_v is None:
            St = float(N.close.get(e, np.nan))
            if not np.isfinite(St): continue
            exit_v = max(St - sc, 0) - max(St - bc, 0) + max(sp - St, 0) - max(bp - St, 0)
        pts = credit - exit_v
        rows.append(dict(entry=d0, exp=e, skip='', vix=round(vix, 2), S=round(S, 1), sCE=sc, sPE=sp, bCE=bc, bPE=bp, credit=round(credit, 2),
                         model_credit=round(mcred, 2), real_call=round(rc_call, 2), real_put=round(rc_put, 2), model_call=round(mc_call, 2),
                         model_put=round(mc_put, 2), how=how, exit_date=xd, exit_val=round(exit_v, 2), pts=round(pts, 2),
                         rs=round(pts * LOT - COST, 0), flag=flag, miss_days=miss_days, wd=d0.day_name()[:3], exp_wd=e.day_name()[:3]))
    return pd.DataFrame(rows)

def era(d):
    d = pd.Timestamp(d)
    return '2019-22' if d < pd.Timestamp('2023-01-01') else ('2023-Aug25 (Thu exp)' if d < pd.Timestamp('2025-09-01') else 'Sep25-26 (Tue exp)')

def summ(T):
    t = T[T.skip == '']
    if not len(t): return {}
    w, l = t[t.rs > 0], t[t.rs <= 0]
    eq = t.rs.cumsum(); dd = (eq.cummax().clip(lower=0) - eq).max()
    return dict(trades=len(t), skipped=int((T.skip != '').sum()), win_pct=round(len(w) / len(t) * 100, 1), avg_win=round(w.rs.mean(), 0) if len(w) else 0,
                avg_loss=round(l.rs.mean(), 0) if len(l) else 0, net_rs=round(t.rs.sum(), 0), per_trade=round(t.rs.mean(), 0),
                pf=round(w.rs.sum() / -l.rs.sum(), 2) if len(l) and l.rs.sum() < 0 else np.nan, max_dd=round(dd, 0), worst=round(t.rs.min(), 0),
                tgt=int((t.how == 'target').sum()), sl=int((t.how == 'SL').sum()), exp=int((t.how == 'expiry').sum()))

md('# Dost ka Iron Condor (Pine code) — ASLI NSE Nifty option bhaav par test')
md(f'Data: NSE F&O bhavcopy, Nifty weekly {exps[0]:%b %Y} se {O.date.max():%d %b %Y}. Rs = aaj ka lot 65, Rs 300/lot kharcha, 0.5 pt/leg slippage.')
md('Pine backtest Black-Scholes andaza tha; yahan har leg ka ASLI open/close/high/low bhaav hai.')

base = run(); base.to_csv(os.path.join(OUT, 'cf_trades_base.csv'), index=False)
B = base[base.skip == '']
md('\n## 1. Model (Black-Scholes) ka credit vs ASLI credit — har entry par')
r = B.credit / B.model_credit
md(f'- Trades: {len(B)}. Asli credit ka median **{B.credit.median():.1f} pt**, model ka median **{B.model_credit.median():.1f} pt**. '
   f'Asli/model median {r.median():.2f}x (beech ke 50%: {r.quantile(.25):.2f}x - {r.quantile(.75):.2f}x).')
md(f'- Call side: asli median {B.real_call.median():.1f} vs model {B.model_call.median():.1f}. Put side: asli {B.real_put.median():.1f} vs model {B.model_put.median():.1f}.')
md(f'- Model ne credit zyada bataya {int((B.model_credit > B.credit).sum())} baar, kam {int((B.model_credit <= B.credit).sum())} baar.')
for er_, g in B.groupby(B.entry.map(era)):
    md(f'  - {er_}: asli median {g.credit.median():.1f}, model {g.model_credit.median():.1f} ({len(g)} trades)')

md(f'- Data jaanch: open-bhaav na milne par close liya {int((B.flag != "").sum())} trades; kisi din leg ka bhaav gayab (us din check nahi) {int(B.miss_days.sum())} trade-din.')
md('\n## 2. Dost ki exact settings (k=1.0, hedge 300, target 60%, SL 150%, VIX 10-22)')
res = []
for nm, kw in [('A close par check (open entry)', {}), ('B SL din ke andar (open entry)', dict(mode='intraday')),
               ('A close entry', dict(entry_at='close')), ('B close entry', dict(entry_at='close', mode='intraday'))]:
    T = base if not kw else run(**kw)
    s = summ(T); s['variant'] = nm; res.append(s)
    if nm.startswith('B SL din'): T.to_csv(os.path.join(OUT, 'cf_trades_intraday.csv'), index=False); TB = T
md('```\n' + pd.DataFrame(res).set_index('variant').to_string() + '\n```')

md('\nDaur-war (A, open entry):')
ee = []
for er_, g in base.groupby(base.entry.map(era)):
    s = summ(g); s['era'] = er_; ee.append(s)
md('```\n' + pd.DataFrame(ee).set_index('era').to_string() + '\n```')
md('Daur-war (B, SL din ke andar):')
ee = []
for er_, g in TB.groupby(TB.entry.map(era)):
    s = summ(g); s['era'] = er_; ee.append(s)
md('```\n' + pd.DataFrame(ee).set_index('era').to_string() + '\n```')
md('Saal-war net Rs (A / B):')
ya = base[base.skip == ''].groupby(base.entry.dt.year).rs.sum(); yb = TB[TB.skip == ''].groupby(TB.entry.dt.year).rs.sum()
md('```\n' + pd.DataFrame({'A_close': ya, 'B_intraday': yb}).round(0).to_string() + '\n```')

md('\n## 3. Doosri settings (overfitting check — sab dikhaye, sirf best nahi)')
grid = []
for k in (0.8, 1.0, 1.25, 1.5):
    for tg, s_ in ((60, 150), (50, 100), (50, 200), (0, 0)):
        for vf in (True, False):
            T = run(k=k, tgt=tg, sl=s_, vix_filter=vf, mode='intraday')
            s = summ(T); s.update(k=k, target=tg or '-', SL=s_ or 'expiry tak', vix_10_22=vf)
            t = T[T.skip == '']
            for er_, g in t.groupby(t.entry.map(era)): s[er_] = round(g.rs.sum(), 0)
            grid.append(s)
Gd = pd.DataFrame(grid); Gd.to_csv(os.path.join(OUT, 'cf_grid.csv'), index=False)
cols = ['k', 'target', 'SL', 'vix_10_22', 'trades', 'win_pct', 'avg_win', 'avg_loss', 'per_trade', 'net_rs', 'max_dd', 'worst', '2019-22', '2023-Aug25 (Thu exp)', 'Sep25-26 (Tue exp)']
md('(sab variant B: SL din ke andar; Rs lot 65)')
md('```\n' + Gd[[c for c in cols if c in Gd]].to_string(index=False) + '\n```')
pos = Gd[[c for c in ('2019-22', '2023-Aug25 (Thu exp)', 'Sep25-26 (Tue exp)') if c in Gd]].gt(0).all(axis=1)
md(f'\nTeeno daur mein munafa: {int(pos.sum())} of {len(Gd)} settings.')

md('\n## 4. Holiday / Monday expiry hafte (dost ka code yahan galat chalta)')
mon = B[B.exp_wd != B.exp_wd.mode().iloc[0]] if len(B) else B
odd = B[~B.exp_wd.isin(['Thu', 'Tue'])]
md(f'- Thu/Tue ke alawa din par expiry: {len(odd)} hafte (in hafton mein Pine code expiry ka din galat maanta aur agle hafte ki entry chhod deta).')
md(f'- In hafton ka asli nateeja (A): net Rs {odd.rs.sum():,.0f}, win {(odd.rs > 0).mean() * 100 if len(odd) else 0:.0f}%')

md('\n## 5. Sabse bure 8 hafte (B)')
w = TB[TB.skip == ''].nsmallest(8, 'rs')[['entry', 'exp', 'vix', 'S', 'sCE', 'sPE', 'credit', 'how', 'exit_val', 'rs']]
md('```\n' + w.to_string(index=False) + '\n```')
md('\n## 6. Wahi strike/hedge, lekin expiry se 1 din PEHLE close par entry (f75 jaisa) — hold to expiry / target-SL')
rr = []
for vlo, vhi in ((10, 22), (14, 22)):
    for k_ in (1.0, 1.5):
        for tg, s_ in ((0, 0), (60, 150)):
            T = run(k=k_, tgt=tg, sl=s_, day_before=True, vlo=vlo, vhi=vhi, mode='intraday' if s_ else 'close')
            s = summ(T); s.update(VIX=f'{vlo}-{vhi}', k=k_, exit='expiry tak' if not s_ else '60/150 (SL din ke andar)')
            t = T[T.skip == '']
            for er_, g in t.groupby(t.entry.map(era)): s[er_] = round(g.rs.sum(), 0)
            rr.append(s)
            if vlo == 14 and k_ == 1.0 and not s_: T.to_csv(os.path.join(OUT, 'cf_trades_daybefore.csv'), index=False)
cc = ['VIX', 'k', 'exit', 'trades', 'win_pct', 'avg_win', 'avg_loss', 'per_trade', 'net_rs', 'max_dd', 'worst', '2019-22', '2023-Aug25 (Thu exp)', 'Sep25-26 (Tue exp)']
Rr = pd.DataFrame(rr); md('```\n' + Rr[[c for c in cc if c in Rr]].to_string(index=False) + '\n```')
open(os.path.join(OUT, 'cf_condor_friend.md'), 'w').write('\n'.join(MD) + '\n')
