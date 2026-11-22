"""Iron condor / short strangle-with-hedge — BADA GRID test, asli NSE option bhaav (user 22 Nov 2026: 'aage-peeche sab try karo,
Nifty ke alawa BankNifty, shares bhi, phir conclusion do').
Model-free: forward F = K* + C - P (|C-P| sabse kam wala strike), ek SD chaal EM = 1.25 x ATM straddle (bazaar ki apni umeed).
Short call = pehla strike >= F + z*EM, short put = aakhri strike <= F - z*EM; hedge = short se w*EM aur door (kam se kam 1 strike).
Entry: din ke CLOSE par; entry par chaaron leg mein asli trade (contracts>0) zaroori — warna hafta chhoda (nakli settle bhaav nahi).
Entry din: after = pichhli expiry ke agle din, d3 = expiry se 3 trading din pehle, d1 = 1 din pehle (+ d10 monthly ke liye).
Exit (din ke close par check): hold (expiry tak), T50 (50% target), T50S100, T50S200, S100 (sirf SL), T60S150 (dost ka Pine).
Expiry: intrinsic, expiry-din ka underlying = put-call parity (traded close) — 'settle' column expiry par underlying/0 hota hai, isliye nahi. Kharcha: slippage har leg har taraf max(0.05, 1% index / 2.5% share bhaav),
  brokerage Rs20+GST har order, STT 0.1% sell premium, exchange 0.0353% (+GST) -> points mein (aaj ke lot se).
Metric: har trade ka nateeja / max risk (hedge chaudai - credit) = 'ret'. Rs = points x aaj ka lot (index).
Usage: OPT_PKL=<pickle of symbols> python study/condor_grid.py  -> study/results/cg_*.csv / cg_condor_grid.md
"""
import os, sys, math, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results')
PKL = os.environ.get('OPT_PKL', '/home/claude/opt18.pkl')
LOT = dict(NIFTY=65, BANKNIFTY=30, FINNIFTY=60, MIDCPNIFTY=120, RELIANCE=500, HDFCBANK=550, ICICIBANK=700, INFY=400, TCS=175, SBIN=750,
           AXISBANK=625, KOTAKBANK=400, LT=175, ITC=1600, BHARTIARTL=475, BAJFINANCE=750, MARUTI=50, HINDUNILVR=300)
IDX = {'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY'}
ZS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0); WS = (0.5, 1.0)
EXITS = {'hold': (0, 0), 'T50': (50, 0), 'T50S100': (50, 100), 'T50S200': (50, 200), 'S100': (0, 100), 'T60S150': (60, 150),
         'S100i': (0, 100), 'T50S100i': (50, 100), 'T60S150i': (60, 150)}  # ...i = SL din ke andar (sold HIGH - hedge LOW), pessimistic
ONLY = sys.argv[1:]

D = pd.read_pickle(PKL)
D['date'] = pd.to_datetime(D.date); D['exp'] = pd.to_datetime(D.exp); D['type'] = D.type.astype(str).str[0]
for c in ('open', 'high', 'low', 'close', 'settle', 'contracts'): D[c] = pd.to_numeric(D[c], errors='coerce').fillna(0)
D = D.drop_duplicates(['symbol', 'date', 'exp', 'type', 'K'])
D['tr'] = D.contracts > 0
D['px'] = np.where(D.tr, D.close, D.settle)
D['hi'] = np.where(D.tr, D.high, D.px); D['lo'] = np.where(D.tr, D.low, D.px)


def slip(p, sym):
    return max(0.05, (0.01 if sym in IDX else 0.025) * p)


def fixed_cost_pts(sym, orders, sell_prem, turnover):
    rs = orders * 20 * 1.18 + 0.001 * sell_prem * LOT[sym] + 0.000353 * 1.18 * turnover * LOT[sym]
    return rs / LOT[sym]


def run_symbol(sym):
    x = D[D.symbol == sym]
    chains = {}
    for (d, e), g in x.groupby(['date', 'exp']):
        chains[(d, e)] = {(t, k): (p, s, tr, h, l) for t, k, p, s, tr, h, l in zip(g.type, g.K, g.px, g.settle, g.tr, g.hi, g.lo)}
    exps = sorted(x.exp.unique()); exps = [pd.Timestamp(e) for e in exps]
    dates = sorted(x.date.unique()); dates = pd.DatetimeIndex(dates)
    rows = []
    for p_, e in zip(exps, exps[1:]):
        Dd = dates[(dates > p_) & (dates < e)]
        if not len(Dd) or (e, e) not in [(e, e)]: continue
        cyc = 'weekly' if (e - p_).days <= 8 else 'monthly'
        ent = {'after': Dd[0], 'd1': Dd[-1]}
        if len(Dd) >= 3: ent['d3'] = Dd[-3]
        if cyc == 'monthly' and len(Dd) >= 10: ent['d10'] = Dd[-10]
        if ent.get('d3') == ent['after']: ent.pop('d3')
        expch = chains.get((e, e))
        if expch is None: continue
        bb = None
        for k in sorted({k for (t, k) in expch}):
            c, pp = expch.get(('C', k)), expch.get(('P', k))
            if c and pp and c[2] and pp[2]:
                dif = abs(c[0] - pp[0])
                if bb is None or dif < bb[0]: bb = (dif, k + c[0] - pp[0])
        if bb is None: continue
        exp_S = bb[1]
        path_days = list(dates[(dates > Dd[0] - pd.Timedelta(days=1)) & (dates < e)])
        for en, d0 in ent.items():
            ch = chains.get((d0, e))
            if not ch: continue
            Ks = sorted({k for (t, k) in ch})
            best = None
            for k in Ks:
                c, pp = ch.get(('C', k)), ch.get(('P', k))
                if c and pp and c[2] and pp[2]:
                    dif = abs(c[0] - pp[0])
                    if best is None or dif < best[0]: best = (dif, k, c[0], pp[0])
            if best is None: continue
            _, ka, ca, pa = best
            F = ka + ca - pa; EM = 1.25 * (ca + pa)
            if EM <= 0: continue
            step = min(np.diff(Ks)) if len(Ks) > 1 else 1
            later = [d for d in path_days if d > d0]
            for z in ZS:
                sc = next((k for k in Ks if k >= F + z * EM), None); sp = next((k for k in reversed(Ks) if k <= F - z * EM), None)
                if sc is None or sp is None: continue
                for w in WS:
                    bc = next((k for k in Ks if k >= sc + max(w * EM, step)), None); bp = next((k for k in reversed(Ks) if k <= sp - max(w * EM, step)), None)
                    if bc is None or bp is None: continue
                    legs = [('C', sc), ('P', sp), ('C', bc), ('P', bp)]
                    q = [ch.get(l) for l in legs]
                    if any(v is None or not v[2] for v in q): continue  # asli trade zaroori
                    pr = [v[0] for v in q]
                    cr = pr[0] + pr[1] - pr[2] - pr[3]
                    if cr <= 0: continue
                    width = max(bc - sc, sp - bp)
                    risk = width - cr
                    if risk <= 0: continue
                    ent_slip = sum(slip(v, sym) for v in pr)
                    # settlement: intrinsic on expiry-day underlying (put-call parity, traded closes)
                    Se = exp_S
                    exp_val = max(Se - sc, 0) - max(Se - bc, 0) + max(sp - Se, 0) - max(bp - Se, 0)
                    # daily path values (close)
                    pv = []
                    for d in later:
                        c2 = chains.get((d, e))
                        if not c2: continue
                        vv = [c2.get(l) for l in legs]
                        if any(v is None for v in vv): continue
                        wst = max(vv[0][3] - vv[2][4] + vv[1][0] - vv[3][0], vv[1][3] - vv[3][4] + vv[0][0] - vv[2][0])
                        pv.append((d, vv[0][0] + vv[1][0] - vv[2][0] - vv[3][0], [v[0] for v in vv], min(wst, width)))
                    for xn, (tg, sl) in EXITS.items():
                        xv, how, xd, xpr = exp_val, 'expiry', e, None
                        intr = xn.endswith('i')
                        for d, v, vp, wst in pv:
                            if intr and sl and wst - cr >= cr * sl / 100:
                                lvl = cr * (1 + sl / 100); xv, how, xd, xpr = lvl, 'SLi', d, vp; break
                            if tg and cr - v >= cr * tg / 100: xv, how, xd, xpr = v, 'target', d, vp; break
                            if sl and v - cr >= cr * sl / 100: xv, how, xd, xpr = v, 'SL', d, vp; break
                        if xpr is not None:
                            ex_slip = sum(slip(v, sym) for v in xpr); orders = 8; turn = sum(pr) + sum(xpr)
                        else:
                            ex_slip = 0; orders = 4; turn = sum(pr)
                        cost = ent_slip + ex_slip + fixed_cost_pts(sym, orders, pr[0] + pr[1], turn)
                        pts = cr - xv - cost
                        rows.append((sym, cyc, en, z, w, xn, d0, e, sc, sp, bc, bp, round(F, 2), round(cr, 2), round(width, 2), round(pts, 3), round(pts / risk, 4), how, xd, round(cost, 3)))
    return pd.DataFrame(rows, columns=['sym', 'cyc', 'entry', 'z', 'w', 'exit', 'd0', 'exp', 'sc', 'sp', 'bc', 'bp', 'F', 'credit', 'width', 'pts', 'ret', 'how', 'xd', 'cost'])


if __name__ == '__main__':
    syms = ONLY or sorted(D.symbol.unique())
    for s in syms:
        T = run_symbol(s)
        T.to_csv(os.path.join(OUT, f'cg_trades_{s}.csv.gz'), index=False, compression='gzip')
        print(s, len(T), flush=True)
