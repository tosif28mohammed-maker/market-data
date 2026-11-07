"""Intraday PAPER trading robot (user 7 Nov 2026: 'din mein 2-4 intraday trade, call/put bhi, galtiyon se seekho').
No real money, no orders. Each loop re-plays TODAY from the first candle up to the last finished 5-min candle
(decision on a finished candle, fill at the NEXT candle's open -> no look-ahead). Same engine replays history.

Strategies (each tagged, so we learn which one works):
  GAPFADE   f46/f47: stock gaps UP 1.5-6% while Nifty gap < +0.3%, first 15 min red -> SHORT 9:30; stop = first-15 high,
            target = prev close (gap fill, max 2R); exit 15:10.
  GAPBOUNCE f46/f47: stock gaps DOWN 2-8%, first 15 min green, Nifty 20d > -6% -> BUY 9:30; stop first-15 low; target prev close.
  USNIGHT   f54: S&P last night >= +1.0% -> Nifty ATM PUT at 9:20, exit 12:15; S&P <= -1.0% -> Nifty ATM CALL at 10:15, exit 15:10.
            stop = Nifty moves 0.6% against.
  TRENDDAY  f71 (experimental): 10:15 Nifty >= +0.5% from open and 70%+ of core stocks above their open -> BUY strongest core
            stock (not > +4%); mirror SHORT on a down day. stop 1% (or VWAP), exit 15:10.
  CONDOR    f26/f29 (experimental, safe zone): weekly-expiry day 11:00, VIX 11-18, Nifty range since open < 0.6% ->
            SELL iron condor (short ~ATM +-0.4%, wings +100; skip if credit < 10 pts); stop if Nifty touches a short strike; exit 15:15.
Options priced with Black-Scholes, IV = India VIX (no live option prices available to the robot) - said in every report.
Limits: max 4 trades/day, 1 per strategy; stock risk Rs 1,000/trade, notional <= Rs 1 lakh; options 1 lot (Nifty 65).
Costs: stocks 0.1% round trip; options Rs 60/leg + 0.5 pt slippage each side.
Usage: python scripts/intra_paper.py live [END_HHMM]   |   python scripts/intra_paper.py replay   |   python scripts/intra_paper.py report
"""
import os, sys, json, time, math, glob, datetime as dt
import numpy as np, pandas as pd

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
J = os.path.join(R, 'paper', 'intra_journal.csv'); REP = os.path.join(R, 'paper', 'intra_report.md')
LIVE = os.path.join(R, 'paper', 'intra_today.md'); RJ = os.path.join(R, 'paper', 'intra_replay.csv')
HOL = {dt.date(2026, 11, 10), dt.date(2026, 11, 24), dt.date(2026, 12, 25)}
LOT, MAXT, RISK, NOTION = 65, 4, 1000.0, 100000.0
SCOST, OCOST, OSLIP = 0.001, 60.0, 0.5


def core_list():
    sys.path.insert(0, os.path.join(R, 'scripts'))
    from fetch_list import TICKERS
    return {k: v for k, v in TICKERS.items() if k not in ('NIFTY', 'INDIAVIX', 'BANKNIFTY') and v.endswith('.NS')}


# ---------------- option pricing ----------------
def ncdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def bs(S, K, T, vol, call, r=0.065):
    if T <= 1e-7: return max(0.0, (S - K) if call else (K - S))
    d1 = (math.log(S / K) + (r + vol * vol / 2) * T) / (vol * math.sqrt(T)); d2 = d1 - vol * math.sqrt(T)
    return S * ncdf(d1) - K * math.exp(-r * T) * ncdf(d2) if call else K * math.exp(-r * T) * ncdf(-d2) - S * ncdf(-d1)


def expiry_for(d):
    e = d + dt.timedelta(days=(1 - d.weekday()) % 7)  # Tuesday
    while e in HOL or e.weekday() >= 5: e -= dt.timedelta(days=1)
    if e < d: e = expiry_for(d + dt.timedelta(days=7 - d.weekday()))
    return e


def tyears(ts, exp):
    end = dt.datetime.combine(exp, dt.time(15, 30))
    return max((end - ts.to_pydatetime()).total_seconds(), 0) / (365 * 24 * 3600)


# ---------------- engine ----------------
def manage(tr, bars, i0, exitT, opt=None):
    """walk bars from i0 (entry bar) until stop/target/time; tr has side, entry, stop, target (prices of the instrument or of Nifty for options)."""
    mfe = mae = 0.0
    for j in range(i0, len(bars)):
        b = bars.iloc[j]; t = b.time.strftime('%H:%M')
        hi, lo = b.high, b.low
        if tr['side'] == 1:
            mfe = max(mfe, hi / tr['ref'] - 1); mae = min(mae, lo / tr['ref'] - 1)
            if lo <= tr['stop']: return j, tr['stop'], 'STOP', mfe, mae
            if tr.get('target') and hi >= tr['target']: return j, tr['target'], 'TARGET', mfe, mae
        else:
            mfe = max(mfe, 1 - lo / tr['ref']); mae = min(mae, 1 - hi / tr['ref'])
            if hi >= tr['stop']: return j, tr['stop'], 'STOP', mfe, mae
            if tr.get('target') and lo <= tr['target']: return j, tr['target'], 'TARGET', mfe, mae
        if t >= exitT: return j, b.close, 'TIME', mfe, mae
    return None, None, 'OPEN', mfe, mae


def run_day(day, S, prev, N, Nprev, V, spx, n20, final):
    """S: {sym: today's 5m bars}, prev: {sym: prev close}, N: Nifty 5m today (or None), V: VIX 5m (or None)."""
    trades = []
    def add(**k):
        if len(trades) < MAXT and k['strat'] not in {t['strat'] for t in trades}: trades.append(k)
    first15 = lambda x: x[x.time.dt.strftime('%H:%M') <= '09:25']
    ngap = (N.open.iloc[0] / Nprev - 1) * 100 if N is not None and len(N) and Nprev else np.nan
    # --- GAPFADE / GAPBOUNCE (signal at 9:25 bar close, fill 9:30 open) ---
    fade, bounce = [], []
    for s, x in S.items():
        if s not in prev or len(x) < 4 or x.time.iloc[0].strftime('%H:%M') != '09:15': continue
        g = (x.open.iloc[0] / prev[s] - 1) * 100; f = first15(x)
        if len(f) < 3: continue
        red = f.close.iloc[-1] < f.open.iloc[0]
        if 1.5 <= g <= 6 and red and (np.isnan(ngap) or ngap < 0.3): fade.append((g, s))
        if -8 <= g <= -2 and not red and n20 > -6: bounce.append((-g, s))
    for lst, strat, side in ((sorted(fade, reverse=True), 'GAPFADE', -1), (sorted(bounce, reverse=True), 'GAPBOUNCE', 1)):
        if not lst: continue
        g, s = lst[0]; x = S[s]; f = first15(x); i0 = len(f)
        if i0 >= len(x): continue
        e = x.open.iloc[i0]
        stop = f.high.max() * 1.002 if side == -1 else f.low.min() * 0.998
        risk = abs(e - stop)
        if risk <= 0 or risk / e > 0.04: continue
        tgt = prev[s] if (prev[s] - e) * side > 0 else None
        if tgt is None or abs(tgt - e) > 2 * risk: tgt = e + side * 2 * risk
        qty = int(min(RISK / risk, NOTION / e))
        if qty < 1: continue
        add(strat=strat, sym=s, side=side, instr='EQ', t_sig=f.time.iloc[-1], i0=i0, bars=x, ref=e, entry=e, stop=stop, target=tgt,
            qty=qty, exitT='15:10', why=f'gap {g * side * -1 if side == -1 else -g:+.1f}%, pehle 15 min {"laal" if side == -1 else "hara"}, Nifty gap {ngap:+.2f}%')
    # --- index-based (need Nifty 5m) ---
    if N is not None and len(N) > 3:
        hm = N.time.dt.strftime('%H:%M')
        vix = float(V.close.iloc[0]) if V is not None and len(V) else 14.0
        exp = expiry_for(day)
        def opt_trade(strat, call, sig_hm, exitT, why):
            k = np.where(hm.values >= sig_hm)[0]
            if not len(k) or k[0] + 1 >= len(N): return
            i0 = k[0] + 1; sp = N.open.iloc[i0]; K = round(sp / 50) * 50
            side = 1 if call else -1
            add(strat=strat, sym=f'NIFTY {K}{"CE" if call else "PE"} {exp:%d%b}', side=side, instr='OPT', i0=i0, bars=N, ref=sp, entry=sp,
                stop=sp * (1 - 0.006 * side), target=None, qty=LOT, exitT=exitT, K=K, call=call, exp=exp, vix=vix,
                t_sig=N.time.iloc[k[0]], why=why)
        if spx is not None and spx >= 1.0: opt_trade('USNIGHT', False, '09:15', '12:15', f'S&P raat {spx:+.1f}% -> India subah kamzor (f54)')
        if spx is not None and spx <= -1.0: opt_trade('USNIGHT', True, '10:15', '15:10', f'S&P raat {spx:+.1f}% -> 10:15 ke baad Nifty sambhalta (f54)')
        # TRENDDAY at 10:15 close
        k = np.where(hm.values == '10:15')[0]
        if len(k) and k[0] + 1 < len(N):
            i = k[0]; t = N.time.iloc[i]; nm = (N.close.iloc[i] / N.open.iloc[0] - 1) * 100
            rets = {}
            for s, x in S.items():
                if s in CORESET and len(x) and x.time.iloc[0].strftime('%H:%M') == '09:15':
                    y = x[x.time <= t]
                    if len(y): rets[s] = (y.close.iloc[-1] / x.open.iloc[0] - 1) * 100
            if len(rets) >= 30:
                up = np.mean([v > 0 for v in rets.values()]) * 100
                for side, ok in ((1, nm >= 0.5 and up >= 70), (-1, nm <= -0.5 and up <= 30)):
                    if not ok: continue
                    c = [(v * side, s) for s, v in rets.items() if v * side <= 4]
                    if not c: continue
                    s = max(c)[1]; x = S[s]; i0 = int(np.where(x.time > t)[0][0]) if (x.time > t).any() else None
                    if i0 is None: continue
                    e = x.open.iloc[i0]; y = x.iloc[:i0]
                    w_ = y.volume.replace(0, 1).fillna(1) if 'volume' in y else pd.Series(1.0, index=y.index)
                    vw = float((y.close * w_).sum() / w_.sum())
                    stop = min(e * 0.99, vw * 0.995) if side == 1 else max(e * 1.01, vw * 1.005)
                    if abs(e - stop) / e > 0.02: stop = e * (1 - 0.02 * side)
                    qty = int(min(RISK / abs(e - stop), NOTION / e))
                    add(strat='TRENDDAY', sym=s, side=side, instr='EQ', i0=i0, bars=x, ref=e, entry=e, stop=stop, target=None, qty=qty,
                        exitT='15:10', t_sig=t, why=f'10:15 tak Nifty {nm:+.2f}%, {up:.0f}% core shares open se upar; sabse mazboot {s} {rets[s]:+.1f}%')
        # CONDOR on expiry day
        k = np.where(hm.values == '11:00')[0]
        if day == exp and len(k) and k[0] + 1 < len(N):
            i = k[0]; rng = (N.high.iloc[:i + 1].max() / N.low.iloc[:i + 1].min() - 1) * 100
            vnow = float(V[V.time <= N.time.iloc[i]].close.iloc[-1]) if V is not None and len(V[V.time <= N.time.iloc[i]]) else vix
            if 11 <= vnow <= 18 and rng < 0.6:
                i0 = i + 1; sp = N.open.iloc[i0]
                ks, kc = math.floor(sp * 0.996 / 50) * 50, math.ceil(sp * 1.004 / 50) * 50
                T_ = tyears(N.time.iloc[i0], exp); v_ = vnow / 100
                cr = bs(sp, ks, T_, v_, False) - bs(sp, ks - 100, T_, v_, False) + bs(sp, kc, T_, v_, True) - bs(sp, kc + 100, T_, v_, True) - 4 * OSLIP
                if cr >= 10: add(strat='CONDOR', sym=f'NIFTY IC {ks}/{kc} (+-100) {exp:%d%b}', side=0, instr='IC', i0=i0, bars=N, ref=sp, entry=sp,
                    stop=None, target=None, qty=LOT, exitT='15:15', ks=ks, kc=kc, exp=exp, vix=vnow, t_sig=N.time.iloc[i],
                    why=f'expiry din, 11:00 tak range {rng:.2f}%, VIX {vnow:.1f}')
    # ---- manage / price ----
    out = []
    for t in trades:
        b = t['bars']; row = {k: v for k, v in t.items() if k not in ('bars', 'i0')}
        row['date'] = str(day); row['entry_time'] = b.time.iloc[t['i0']].strftime('%H:%M')
        if t['instr'] == 'EQ':
            j, px, why, mfe, mae = manage(t, b, t['i0'], t['exitT'])
            if j is None and final: j, px, why = len(b) - 1, b.close.iloc[-1], 'TIME'
            row.update(exit_time=b.time.iloc[j].strftime('%H:%M') if j is not None else '', exit=px, reason=why,
                       mfe_pct=round(mfe * 100, 2), mae_pct=round(mae * 100, 2))
            last = px if px is not None else b.close.iloc[-1]
            row['pnl_rs'] = round(t['side'] * (last - t['entry']) * t['qty'] - SCOST * t['entry'] * t['qty'], 0)
            row['R'] = round(t['side'] * (last - t['entry']) / abs(t['entry'] - t['stop']), 2)
        elif t['instr'] == 'OPT':
            j, px, why, mfe, mae = manage(dict(t, ref=t['entry']), b, t['i0'], t['exitT'])
            if j is None and final: j, why = len(b) - 1, 'TIME'
            jj = j if j is not None else len(b) - 1
            spx_ = px if px is not None else b.close.iloc[jj]
            T0, T1 = tyears(b.time.iloc[t['i0']], t['exp']), tyears(b.time.iloc[jj] + pd.Timedelta(minutes=5), t['exp'])
            v = t['vix'] / 100
            p0 = bs(t['entry'], t['K'], T0, v, t['call']) + OSLIP; p1 = max(bs(spx_, t['K'], T1, v, t['call']) - OSLIP, 0.05)
            row.update(exit_time=b.time.iloc[jj].strftime('%H:%M') if j is not None else '', exit=round(spx_, 1), reason=why,
                       prem_in=round(p0, 1), prem_out=round(p1, 1), mfe_pct=round(mfe * 100, 2), mae_pct=round(mae * 100, 2))
            row['pnl_rs'] = round((p1 - p0) * LOT - OCOST, 0); row['R'] = round((p1 - p0) / p0, 2)
        else:  # iron condor
            stop_j = None
            for jj in range(t['i0'], len(b)):
                if b.high.iloc[jj] >= t['kc'] or b.low.iloc[jj] <= t['ks']: stop_j = jj; break
                if b.time.iloc[jj].strftime('%H:%M') >= t['exitT']: break
            done = stop_j is not None or b.time.iloc[-1].strftime('%H:%M') >= t['exitT'] or final
            jj = stop_j if stop_j is not None else min(jj, len(b) - 1)
            v = t['vix'] / 100
            def ic(S_, T):
                return (bs(S_, t['ks'], T, v, False) - bs(S_, t['ks'] - 100, T, v, False) + bs(S_, t['kc'], T, v, True) - bs(S_, t['kc'] + 100, T, v, True))
            S1 = t['kc'] if stop_j is not None and b.high.iloc[jj] >= t['kc'] else (t['ks'] if stop_j is not None else b.close.iloc[jj])
            c0 = ic(t['entry'], tyears(b.time.iloc[t['i0']], t['exp'])) - 4 * OSLIP
            c1 = ic(S1, tyears(b.time.iloc[jj] + pd.Timedelta(minutes=5), t['exp'])) + 4 * OSLIP
            row.update(exit_time=b.time.iloc[jj].strftime('%H:%M') if done else '', exit=round(S1, 1), reason=('STOP' if stop_j is not None else 'TIME') if done else 'OPEN',
                       prem_in=round(c0, 1), prem_out=round(c1, 1), mfe_pct=np.nan, mae_pct=np.nan)
            row['pnl_rs'] = round((c0 - c1) * LOT - 4 * OCOST, 0); row['R'] = round((c0 - c1) / 100, 2)
        # Nifty direction during the trade (for 'against market' lesson)
        if N is not None and len(N) and t['instr'] == 'EQ':
            a = N[N.time >= b.time.iloc[t['i0']]]; z = a[a.time <= pd.Timestamp(f"{day} {row['exit_time'] or '15:30'}")]
            row['nifty_move'] = round((z.close.iloc[-1] / z.open.iloc[0] - 1) * 100, 2) if len(z) else np.nan
        out.append(row)
    return out


def lessons(r):
    tags = []
    if r.get('reason') == 'STOP':
        try:
            mins = (pd.Timestamp(f"2000-01-01 {r['exit_time']}") - pd.Timestamp(f"2000-01-01 {r['entry_time']}")).seconds / 60
            if mins <= 15: tags.append('stop 15 min mein = entry jaldi/galat jagah')
        except Exception: pass
    if r.get('instr') == 'EQ' and not pd.isna(r.get('nifty_move', np.nan)) and r['side'] * r['nifty_move'] < -0.3: tags.append('Nifty ulti disha mein chala')
    if r.get('reason') in ('STOP', 'TIME') and r.get('mfe_pct', 0) and r.get('target') and r['instr'] == 'EQ':
        need = abs(r['target'] / r['entry'] - 1) * 100
        if need and r['mfe_pct'] >= 0.75 * need: tags.append('target ke 75% tak gaya phir palta = trailing stop chahiye tha')
    if r.get('reason') == 'TIME' and abs(r.get('R', 0)) < 0.2: tags.append('din bhar kuch nahi hua = setup kamzor')
    if r.get('instr') == 'OPT' and r.get('pnl_rs', 0) < 0 and r.get('mfe_pct', 0) > 0.3: tags.append('disha sahi thi par option ka time decay/IV kha gaya')
    return '; '.join(tags)


# ---------------- data ----------------
def yf_5m(tickers, period='1d'):
    import yfinance as yf
    out = {}
    for i in range(0, len(tickers), 100):
        part = tickers[i:i + 100]
        try: df = yf.download(part, period=period, interval='5m', group_by='ticker', auto_adjust=False, progress=False, threads=True)
        except Exception as e: print('yf', e); continue
        for tk in part:
            try: x = (df[tk] if isinstance(df.columns, pd.MultiIndex) else df).dropna(subset=['Close']).reset_index()
            except Exception: continue
            if not len(x): continue
            x = x.rename(columns={x.columns[0]: 'time', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'})
            tt = pd.to_datetime(x.time); x['time'] = (tt.dt.tz_convert('Asia/Kolkata') if tt.dt.tz is not None else tt).dt.tz_localize(None)
            out[tk] = x[['time', 'open', 'high', 'low', 'close', 'volume']]
        time.sleep(1)
    return out


def daily_ctx(day):
    C = pd.read_csv(os.path.join(R, 'data', 'daily_all', 'close.csv.gz'), index_col=0, parse_dates=True)
    C = C[C.index.date < day]; prev = C.ffill().iloc[-1].dropna().to_dict()
    n = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
    n = n[n.index.date < day]; n20 = (n.iloc[-1] / n.iloc[-21] - 1) * 100
    sp = pd.read_csv(os.path.join(R, 'data', 'global', 'US_SP500.csv'), parse_dates=['date']).set_index('date').close.dropna()
    sp = sp[sp.index.date < day]; spx = (sp.iloc[-1] / sp.iloc[-2] - 1) * 100
    return prev, float(n.iloc[-1]), n20, spx


CORESET = set(core_list())


def write_live(rows, day, note=''):
    L = [f'# Intraday paper — {day} (update {pd.Timestamp.now(tz="Asia/Kolkata"):%H:%M} IST)', '',
         'Paper hai, asli paisa/order nahi. Option bhaav Black-Scholes + India VIX se andaza (robot ke paas live option bhaav nahi).', note, '']
    if not rows: L.append('Abhi tak koi setup nahi bana.')
    for r in rows:
        st = 'KHULA' if r['reason'] == 'OPEN' else f"band {r['exit_time']} ({r['reason']})"
        L.append(f"- **{r['strat']}** {r['sym']} {'BUY' if r['side'] == 1 else ('SELL' if r['side'] == -1 else 'IC')} {r['qty']} @{r['entry']:.2f} "
                 f"{r['entry_time']} | stop {r['stop'] if r['stop'] else '-'} | {st} | P&L Rs {r['pnl_rs']:+,.0f} — {r['why']}")
    open(LIVE, 'w').write('\n'.join(L) + '\n')


def save_journal(rows, day):
    df = pd.DataFrame(rows)
    if len(df): df['lesson'] = [lessons(r) for r in rows]
    old = pd.read_csv(J) if os.path.exists(J) else pd.DataFrame()
    if len(old): old = old[old.date != str(day)]
    keep = ['date', 'strat', 'sym', 'instr', 'side', 'qty', 'entry_time', 'entry', 'stop', 'target', 'exit_time', 'exit', 'reason',
            'prem_in', 'prem_out', 'pnl_rs', 'R', 'mfe_pct', 'mae_pct', 'nifty_move', 'why', 'lesson']
    df = df.reindex(columns=keep) if len(df) else pd.DataFrame(columns=keep)
    pd.concat([old, df]).to_csv(J, index=False)


def report():
    L = ['# Intraday paper — hisaab aur seekh', '', 'Asli paisa nahi. Stocks kharcha 0.1%, options Rs 60/leg + 0.5 pt. Option bhaav andaza (BS + VIX).', '']
    for name, f in (('LIVE (asli din, robot ne us din chalaya)', J), ('REPLAY (pichhle data par wahi niyam — shuruaati andaza)', RJ)):
        if not os.path.exists(f): continue
        d = pd.read_csv(f)
        d = d[d.reason != 'OPEN']
        if not len(d): continue
        g = d.groupby('strat').agg(trades=('pnl_rs', 'size'), win_pct=('pnl_rs', lambda x: round((x > 0).mean() * 100)),
                                    total_rs=('pnl_rs', 'sum'), avg_rs=('pnl_rs', 'mean'), avg_R=('R', 'mean'))
        g.loc['KUL'] = [len(d), round((d.pnl_rs > 0).mean() * 100), d.pnl_rs.sum(), d.pnl_rs.mean(), d.R.mean()]
        L += [f'## {name}: {d.date.nunique()} din', '```', g.round(2).to_string(), '```']
        if 'lesson' in d:
            ls = d.lesson.dropna().str.split('; ').explode(); ls = ls[ls != '']
            if len(ls): L += ['Galtiyon ki ginti:', '```', ls.value_counts().to_string(), '```']
    if os.path.exists(J):
        d = pd.read_csv(J); last = d.date.max() if len(d) else None
        if last:
            L += [f'## Aakhri din {last}', '']
            for r in d[d.date == last].itertuples():
                L.append(f'- {r.strat} {r.sym} {r.entry_time}->{r.exit_time} {r.reason}: Rs {r.pnl_rs:+,.0f} ({r.R:+.2f}R). {r.why}. {"Seekh: " + r.lesson if isinstance(r.lesson, str) and r.lesson else ""}')
    open(REP, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


# ---------------- modes ----------------
def live(end_hm):
    IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
    day = dt.datetime.now(IST).date()
    if day.weekday() >= 5 or day in HOL: print('market band'); return
    prev, nprev, n20, spx = daily_ctx(day)
    core = core_list(); U = pd.read_csv(os.path.join(R, 'paper', 'gap_universe.csv')); A = U[U.liq == 'A'].symbol.tolist()
    watch = set(); last_push = time.time()
    while True:
        now = dt.datetime.now(IST); hm = now.strftime('%H%M')
        if hm < '0916': time.sleep(30); continue
        tick = {'^NSEI': 'NIFTY', '^INDIAVIX': 'VIX'}
        tk = ['^NSEI', '^INDIAVIX'] + list(core.values()) + [f'{s}.NS' for s in watch]
        if not watch and hm >= '0931':  # one-time gap scan over all A stocks
            allb = yf_5m([f'{s}.NS' for s in A])
            for t_, x in allb.items():
                s = t_[:-3]
                if s in prev and len(x) and x.time.iloc[0].strftime('%H:%M') == '09:15':
                    g = (x.open.iloc[0] / prev[s] - 1) * 100
                    if g >= 1.5 or g <= -2: watch.add(s)
            print('gap watch', len(watch)); tk += [f'{s}.NS' for s in watch]
        B = yf_5m(sorted(set(tk)))
        N = B.pop('^NSEI', None); V = B.pop('^INDIAVIX', None)
        cut = pd.Timestamp(now.replace(tzinfo=None)) - pd.Timedelta(minutes=5)  # only finished candles
        N = N[N.time <= cut].reset_index(drop=True) if N is not None else None
        V = V[V.time <= cut].reset_index(drop=True) if V is not None else None
        S = {t_[:-3]: x[x.time <= cut].reset_index(drop=True) for t_, x in B.items()}
        S = {s: x[x.time.dt.date == day] for s, x in S.items()}
        if N is not None: N = N[N.time.dt.date == day].reset_index(drop=True)
        if V is not None: V = V[V.time.dt.date == day].reset_index(drop=True)
        final = hm >= '1525'
        if not watch and hm < '0931': S = {s: x for s, x in S.items() if s in CORESET}
        rows = run_day(day, S, prev, N, nprev, V, spx, n20, final)
        write_live(rows, day, f'S&P raat {spx:+.2f}%, Nifty 20 din {n20:+.1f}%, gap watch {len(watch)} shares')
        save_journal(rows, day); print(now.strftime('%H:%M'), len(rows), 'trades')
        if final or hm >= end_hm:
            if final: report()
            return
        if time.time() - last_push > 1500: os.system('bash scripts/push_paper.sh "intraday paper live" || true'); last_push = time.time()
        time.sleep(max(60, 300 - (time.time() % 300) + 20))


def replay():
    """5-min history: data/gapday (gap stocks, ~6 months) + data/intraday (Nifty, VIX, core ~73, ~2 months)."""
    nifty = pd.read_csv(os.path.join(R, 'data', 'intraday', 'NIFTY_5m.csv'), parse_dates=['time'])
    vixd = pd.read_csv(os.path.join(R, 'data', 'intraday', 'INDIAVIX_5m.csv'), parse_dates=['time'])
    coreb = {s: pd.read_csv(f, parse_dates=['time']) for s in CORESET for f in [os.path.join(R, 'data', 'intraday', f'{s}_5m.csv')] if os.path.exists(f)}
    days = sorted({os.path.basename(f)[:10] for f in glob.glob(os.path.join(R, 'data', 'gapday', '*.csv.gz'))} | set(nifty.time.dt.date.astype(str)))
    rows = []
    for ds in days:
        day = dt.date.fromisoformat(ds)
        if day.weekday() >= 5: continue
        try: prev, nprev, n20, spx = daily_ctx(day)
        except Exception: continue
        S = {}
        gf = os.path.join(R, 'data', 'gapday', f'{ds}.csv.gz')
        if os.path.exists(gf):
            g = pd.read_csv(gf, parse_dates=['time'])
            for s, x in g.groupby('symbol'):
                S[s] = x.drop(columns=['symbol', 'prev_close']).reset_index(drop=True); prev[s] = float(x.prev_close.iloc[0])
        for s, x in coreb.items():
            y = x[x.time.dt.date == day]
            if len(y): S.setdefault(s, y.reset_index(drop=True))
        N = nifty[nifty.time.dt.date == day].reset_index(drop=True); V = vixd[vixd.time.dt.date == day].reset_index(drop=True)
        N = N if len(N) > 50 else None
        if N is None:  # Nifty gap from daily file only (for GAPFADE filter)
            n = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date')
            if pd.Timestamp(day) in n.index:
                N0 = pd.DataFrame({'time': [pd.Timestamp(f'{day} 09:15')], 'open': [n.loc[pd.Timestamp(day), 'open']], 'high': [np.nan], 'low': [np.nan], 'close': [np.nan]})
                r_ = run_day(day, S, prev, N0, nprev, None, None, n20, True)
                rows += [x for x in r_ if x['instr'] == 'EQ' and x['strat'].startswith('GAP')]
            continue
        rows += run_day(day, S, prev, N, nprev, V, spx, n20, True)
    df = pd.DataFrame(rows)
    if len(df): df['lesson'] = [lessons(r) for r in rows]
    df.drop(columns=[c for c in ('bars',) if c in df], errors='ignore').to_csv(RJ, index=False)
    print(df.groupby('strat').pnl_rs.agg(['size', 'sum', 'mean', lambda x: (x > 0).mean()]) if len(df) else 'no trades')


if __name__ == '__main__':
    m = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if m == 'live': live(sys.argv[2] if len(sys.argv) > 2 else '1530')
    elif m == 'replay': replay(); report()
    else: report()
