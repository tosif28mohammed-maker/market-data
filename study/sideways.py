"""Sideways / quiet-market study (user 9 Nov 2026: 'bazaar shaant/sideways ho tab kya karein — iron condor, bull put / bear call
spread; Nifty, Sensex aur sab F&O shares par; din ka 500-1000 bhi mile to badi baat').
Parts (python study/sideways.py <part>):
  regime  : WHEN is the market quiet? Nifty 2008-26: P(next 5 days stay inside +-2% / next day range < 0.8%) given VIX level,
            VIX change, 10d realised vol, NR7, weekday, days to expiry, mid-month, after a big day, Bollinger squeeze, results season.
            Same for F&O-type stocks (A liquidity, 2 years): P(next 10 days inside +-5%) given own squeeze/NR7/vol rank.
            Learn on first half, check on second half. Output study/results/sw_regime*.csv + .md
  options : REAL NSE option prices (nse_opt branch, 2010-26). Iron condor / bull put spread / bear call spread on NIFTY, BANKNIFTY
            (nearest expiry, entry 5/3/1 trading days before expiry) and F&O stocks (monthly, entry 15/8 days before).
            Short strikes at k * sigma * sqrt(T) (k = 1.0 / 1.5), wings 2% (index) / 5% (stocks) further. Hold to expiry
            (settle on expiring future) or stop at 2x credit (daily close). Costs: Rs 20/leg brokerage both sides, STT 0.1% of sold
            premium, slippage 0.5 pt/leg index, 2% of premium (min 0.1) stocks. Filters: always / quiet-regime / trend side.
            Output study/results/sw_options*.csv + .md (per trade, eras, win %, worst, return on risk, Rs per current lot).
No look-ahead: strikes from data known at entry close; regime rules chosen on 2010-17, tested 2018-26.
"""
import os, sys, glob, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results'); os.makedirs(OUT, exist_ok=True)
part = sys.argv[1] if len(sys.argv) > 1 else 'regime'
MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s); MD.append(s)
HOL_SET = set()


def ix(name):
    d = pd.read_csv(os.path.join(R, 'data', f'{name}.csv'), parse_dates=['date']).set_index('date').sort_index()
    return d[~d.index.duplicated()].dropna(subset=['close'])


def monthly_expiry_dates(idx):
    """last Thursday (till Aug 2025) / last Tuesday (Sep 2025+) per month, moved to the previous trading day present in idx."""
    out = []
    s = pd.Series(idx, index=idx)
    for (y, m), g in s.groupby([idx.year, idx.month]):
        wd = 1 if (y, m) >= (2025, 9) else 3
        last = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)
        while last.weekday() != wd: last -= pd.Timedelta(days=1)
        cand = g[g <= last]
        if len(cand): out.append(cand.iloc[-1])
    return pd.DatetimeIndex(out)


def cond_table(F, target, name, first_end):
    rows = []
    base = target.mean()
    for f in F.columns:
        for lvl in sorted(F[f].dropna().unique()):
            m = F[f] == lvl; n = int(m.sum())
            if n < 40: continue
            a = target[m & (F.index <= first_end)]; b = target[m & (F.index > first_end)]
            rows.append(dict(feature=f, level=lvl, n=n, p_quiet=round(target[m].mean() * 100, 1), lift=round(target[m].mean() / base, 2),
                             first_half=round(a.mean() * 100, 1) if len(a) > 15 else np.nan, second_half=round(b.mean() * 100, 1) if len(b) > 15 else np.nan))
    T = pd.DataFrame(rows)
    T['holds'] = ((T.first_half - base * 100) * (T.second_half - base * 100) > 0) & ((T.first_half - base * 100).abs() >= 5) & ((T.second_half - base * 100).abs() >= 5)
    T.to_csv(os.path.join(OUT, f'sw_regime_{name}.csv'), index=False)
    md(f'\n### {name}: base P(shaant) = {base * 100:.1f}% ({int(target.notna().sum())} din)')
    md('Sabse shaant halaat (dono aadhe mein sahi = holds):')
    md('```\n' + T.sort_values('lift', ascending=False).head(14).to_string(index=False) + '\n```')
    md('Sabse kam shaant (yahan option bechna khatarnaak):')
    md('```\n' + T.sort_values('lift').head(8).to_string(index=False) + '\n```')
    return T


if part == 'regime':
    N = ix('NIFTY'); V = ix('INDIAVIX').close.reindex(N.index).ffill()
    c, h, l = N.close, N.high, N.low
    r = c.pct_change()
    fh5 = pd.concat([h.shift(-k) for k in range(1, 6)], axis=1).max(axis=1); fl5 = pd.concat([l.shift(-k) for k in range(1, 6)], axis=1).min(axis=1)
    q5 = ((fh5 / c - 1 <= 0.02) & (1 - fl5 / c <= 0.02)).astype(float).where(fh5.notna())
    q1 = (((h.shift(-1) - l.shift(-1)) / c) < 0.008).astype(float).where(h.shift(-1).notna())
    rv10 = r.rolling(10).std() * np.sqrt(252) * 100
    rng = (h - l) / c
    nr7 = rng <= rng.rolling(7).min()
    bbw = (c.rolling(20).std() * 4 / c.rolling(20).mean())
    exp = monthly_expiry_dates(N.index)
    nxt = pd.Series(exp, index=exp).reindex(N.index, method='bfill')
    dte = pd.Series([(N.index[(N.index > d) & (N.index <= e)].size if pd.notna(e) else np.nan) for d, e in zip(N.index, nxt)], index=N.index)
    F = pd.DataFrame(index=N.index)
    F['VIX'] = pd.cut(V, [0, 12, 14, 16, 18, 22, 30, 200], labels=['<12', '12-14', '14-16', '16-18', '18-22', '22-30', '30+']).astype(str)
    F['VIX 5d badla'] = pd.cut(V.pct_change(5) * 100, [-100, -15, -5, 5, 15, 500], labels=['-15%+', '-5..-15', 'flat', '+5..15', '+15%+']).astype(str)
    F['10d realised vol'] = pd.qcut(rv10, 5, labels=['sabse kam', 'kam', 'beech', 'zyada', 'sabse zyada']).astype(str)
    F['NR7 (7 din ki sabse chhoti range)'] = nr7.map({True: 'haan', False: 'nahi'})
    F['Bollinger squeeze (20% sabse patla)'] = (bbw <= bbw.rolling(250, min_periods=120).quantile(0.2)).map({True: 'haan', False: 'nahi'})
    F['din'] = N.index.day_name().str[:3]
    F['expiry tak din'] = pd.cut(dte, [-1, 0, 2, 5, 10, 30], labels=['expiry din', '1-2', '3-5', '6-10', '11+']).astype(str)
    F['tareekh'] = pd.cut(N.index.day, [0, 3, 10, 24, 31], labels=['1-3', '4-10', '11-24', '25-31']).astype(str)
    F['aaj ki chaal'] = pd.cut(r.abs() * 100, [-1, 0.3, 0.8, 1.5, 100], labels=['<0.3%', '0.3-0.8', '0.8-1.5', '>1.5%']).astype(str)
    F['20 DMA se'] = pd.cut((c / c.rolling(20).mean() - 1) * 100, [-100, -3, -1, 1, 3, 100], labels=['-3%+', '-1..-3', '+-1%', '+1..3', '+3%+']).astype(str)
    F['results season'] = np.where(N.index.month.isin([1, 4, 7, 10]) & (N.index.day >= 10) | N.index.month.isin([2, 5, 8, 11]) & (N.index.day <= 14), 'haan', 'nahi')
    F = F.replace('nan', np.nan)
    F = F[F.index >= '2008-06-01']
    md('# Sideways / shaant bazaar — kab? (Nifty 2008-26)')
    md('Shaant (5 din) = agle 5 din Nifty ka high/low aaj ke close se +-2% ke andar (iron condor +-2% bach jaata). Shaant (1 din) = agle din range < 0.8%.')
    T5 = cond_table(F, q5.reindex(F.index), 'nifty_5d', pd.Timestamp('2017-06-30'))
    T1 = cond_table(F, q1.reindex(F.index), 'nifty_1d', pd.Timestamp('2017-06-30'))
    # simple combined rule learned on first half
    good = T5[(T5.holds) & (T5.lift >= 1.15)]
    md('\nPehle aadhe se chune "shaant" ishaare (dono aadhe sahi):', ', '.join(f'{a}={b}' for a, b in zip(good.feature, good.level)) or 'koi nahi')
    sc = pd.Series(0, index=F.index)
    for a, b in zip(good.feature, good.level): sc += (F[a] == b).astype(int)
    tq = q5.reindex(F.index)
    for k in range(0, int(sc.max()) + 1):
        m = sc >= k
        if m.sum() >= 30: md(f'  {k}+ ishaare saath: {int(m.sum())} din, P(5 din shaant) {tq[m].mean() * 100:.1f}% (pehla aadha {tq[m & (F.index <= "2017-06-30")].mean() * 100:.1f}, doosra {tq[m & (F.index > "2017-06-30")].mean() * 100:.1f})')
    pd.DataFrame({'score': sc, 'quiet5': tq}).to_csv(os.path.join(OUT, 'sw_regime_nifty_score.csv'))
    # ---- stocks (A liquidity, 2 years daily_all): next 10 days within +-5% ----
    rd = lambda f: pd.read_csv(os.path.join(R, 'data', 'daily_all', f), index_col=0, parse_dates=True)
    C, H, L = rd('close.csv.gz'), rd('high.csv.gz'), rd('low.csv.gz')
    liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv')).set_index('symbol').liquidity.astype(str).str[0]
    A = [s for s in C.columns if liq.get(s) == 'A']
    C, H, L = C[A], H[A], L[A]
    fh = pd.concat([H.shift(-k) for k in range(1, 11)]).groupby(level=0).max().reindex(C.index)
    fl = pd.concat([L.shift(-k) for k in range(1, 11)]).groupby(level=0).min().reindex(C.index)
    qs = ((fh / C - 1 <= 0.05) & (1 - fl / C <= 0.05)).astype(float).where(fh.notna() & C.notna())
    rr = C.pct_change(); rv = rr.rolling(20).std() * np.sqrt(252)
    rgs = (H - L) / C; nr7s = rgs <= rgs.rolling(7).min()
    bw = C.rolling(20).std() / C.rolling(20).mean(); sq = bw <= bw.rolling(120, min_periods=80).quantile(0.2)
    vrank = rv.rank(axis=1, pct=True)
    mov = rr.abs() >= 0.04
    feats = {'apni vol sabse kam 20% (sab shares mein)': vrank <= 0.2, 'apni vol sabse zyada 20%': vrank >= 0.8, 'NR7': nr7s, 'squeeze (apna 20% patla)': sq,
             'aaj 4%+ chaal': mov, '200 DMA ke upar': C > C.rolling(200).mean()}
    base = np.nanmean(qs.values)
    md(f'\n### Shares (A, 2 saal): base P(agle 10 din +-5% ke andar) = {base * 100:.1f}%')
    half = C.index[len(C.index) // 2]
    for k, m in feats.items():
        m = m.reindex_like(qs).fillna(False)
        v = qs.where(m); a = np.nanmean(v[v.index < half].values); b = np.nanmean(v[v.index >= half].values)
        md(f'  {k:40s}: {np.nanmean(v.values) * 100:5.1f}% (pehla {a * 100:.1f}, doosra {b * 100:.1f})')
    m = (vrank <= 0.2) & sq
    v = qs.where(m.reindex_like(qs).fillna(False)); md(f'  {"low-vol + squeeze dono":40s}: {np.nanmean(v.values) * 100:5.1f}%')
    open(os.path.join(OUT, 'sw_regime.md'), 'w').write('\n'.join(MD) + '\n')

elif part == 'options':
    H_ = os.environ.get('NSE_OPT', os.path.join(R, 'nse_opt'))
    files = sorted(glob.glob(os.path.join(H_, 'opt', '*.csv.gz')))
    O = pd.concat([pd.read_csv(f, parse_dates=['date', 'exp']) for f in files], ignore_index=True)
    O['type'] = O.type.astype(str).str[0]; O['px'] = np.where(pd.to_numeric(O.contracts, errors='coerce') > 0, O.close, O.settle)
    O = O[O.px > 0]
    md(f'# Option bechne ki strategies — asli NSE bhaav ({O.date.min():%Y}-{O.date.max():%Y}, {len(O):,} rows)')
    V = ix('INDIAVIX').close
    sc = pd.read_csv(os.path.join(OUT, 'sw_regime_nifty_score.csv'), index_col=0, parse_dates=True).score if os.path.exists(os.path.join(OUT, 'sw_regime_nifty_score.csv')) else pd.Series(dtype=float)
    LOT = {'NIFTY': 65, 'BANKNIFTY': 30}
    trades = []
    for sym, g in O.groupby('symbol'):
        is_idx = sym in ('NIFTY', 'BANKNIFTY', 'FINNIFTY')
        if not is_idx and g.date.nunique() < 120: continue
        g = g.sort_values('date'); fut = g.groupby('date').fut.first()
        if is_idx and sym != 'FINNIFTY':
            sig_s = (V.reindex(fut.index).ffill() / 100)
        else:
            sig_s = fut.pct_change().rolling(20).std() * np.sqrt(252)
        sma20, sma200 = fut.rolling(20).mean(), fut.rolling(200, min_periods=120).mean()
        dates = fut.index; pos = {d: i for i, d in enumerate(dates)}
        entries = (5, 3, 1) if is_idx else (15, 8)
        wing = 0.02 if is_idx else 0.05
        slip = (lambda p: 0.5) if is_idx else (lambda p: max(0.1, 0.02 * p))
        by_d = {d: x for d, x in g.groupby('date')}
        for e, ge in g.groupby('exp'):
            if pd.isna(e) or e not in pos: continue
            ei = pos[e]
            for nd in entries:
                if ei - nd < 0: continue
                d0 = dates[ei - nd]; x = by_d.get(d0)
                if x is None: continue
                x = x[x.exp == e]
                if len(x) < 6: continue
                F0 = fut[d0]; sg = sig_s.get(d0, np.nan)
                if not np.isfinite(sg) or sg <= 0: continue
                T = nd / 252
                chain = {(t, k): p for t, k, p in zip(x.type, x.K, x.px)}
                Ks = np.array(sorted(x.K.unique()))
                def near(target, typ):
                    ks = [k for k in Ks if (typ, k) in chain]
                    return min(ks, key=lambda k: abs(k - target)) if ks else None
                trend = 'up' if F0 > sma20.get(d0, np.nan) and F0 > sma200.get(d0, np.nan) else ('down' if F0 < sma20.get(d0, np.nan) and F0 < sma200.get(d0, np.nan) else 'mixed')
                for kk in (1.0, 1.5):
                    mv = kk * sg * np.sqrt(T)
                    sp, sc_ = near(F0 * (1 - mv), 'P'), near(F0 * (1 + mv), 'C')
                    lp, lc = near(F0 * (1 - mv - wing), 'P'), near(F0 * (1 + mv + wing), 'C')
                    if None in (sp, sc_, lp, lc) or not (lp < sp < F0 < sc_ < lc): continue
                    legs = {'put': (sp, lp), 'call': (sc_, lc)}
                    for strat, use in (('IRON CONDOR', ('put', 'call')), ('BULL PUT SPREAD', ('put',)), ('BEAR CALL SPREAD', ('call',))):
                        credit = 0.0; width = 0.0; ok = True; cost = 0.0
                        for side in use:
                            s_, l_ = legs[side]; t = 'P' if side == 'put' else 'C'
                            ps, pl = chain[(t, s_)], chain[(t, l_)]
                            credit += ps - pl - slip(ps) - slip(pl); width = max(width, abs(s_ - l_)); cost += 0.001 * ps * 2
                        if credit <= 0: continue
                        # walk to expiry: stop at 2x credit (close prices), else settle on expiring future
                        exit_v, how = None, 'expiry'
                        for d in dates[ei - nd + 1: ei]:
                            y = by_d.get(d)
                            if y is None: continue
                            y = y[y.exp == e]; ch = {(t, k): p for t, k, p in zip(y.type, y.K, y.px)}
                            val = 0.0; miss = False
                            for side in use:
                                s_, l_ = legs[side]; t = 'P' if side == 'put' else 'C'
                                if (t, s_) not in ch or (t, l_) not in ch: miss = True; break
                                val += ch[(t, s_)] - ch[(t, l_)]
                            if not miss and val >= 3 * credit:  # loss = 2x credit
                                exit_v, how = val + sum(slip(1) for _ in use) * 2, 'stop'; break
                        if exit_v is None:
                            S = fut.get(e, np.nan)
                            if not np.isfinite(S): continue
                            exit_v = 0.0
                            for side in use:
                                s_, l_ = legs[side]
                                exit_v += (max(s_ - S, 0) - max(l_ - S, 0)) if side == 'put' else (max(S - s_, 0) - max(S - l_, 0))
                        pnl = credit - exit_v - cost - (0.0 if is_idx else 0.0)
                        trades.append(dict(symbol=sym, idx=is_idx, strat=strat, k=kk, dte=nd, entry=d0, exp=e, fut=F0, vix_or_vol=round(sg * 100, 1), trend=trend,
                                           quiet_score=sc.get(d0, np.nan) if is_idx else np.nan, credit=round(credit, 2), width=width, exit=round(exit_v, 2), how=how,
                                           pnl_pts=round(pnl, 2), ror=round(pnl / max(width - credit, 1e-9) * 100, 2), rs_lot=round(pnl * LOT.get(sym, np.nan), 0)))
    T = pd.DataFrame(trades); T.to_csv(os.path.join(OUT, 'sw_options_trades.csv.gz'), index=False)
    T['year'] = pd.to_datetime(T.entry).dt.year
    T['era'] = pd.cut(T.year, [2009, 2012, 2020, 2023, 2027], labels=['2010-12', '2013-20', '2021-23', '2024-26'])
    def summ(x):
        return pd.Series(dict(trades=len(x), win_pct=round((x.pnl_pts > 0).mean() * 100), avg_ror=round(x.ror.mean(), 2), median_ror=round(x.ror.median(), 2),
                              worst_ror=round(x.ror.min(), 1), stops_pct=round((x.how == 'stop').mean() * 100), rs_lot_avg=round(x.rs_lot.mean(), 0) if x.rs_lot.notna().any() else np.nan))
    for grp, nm in ((T[T.idx], 'INDEX (Nifty/BankNifty)'), (T[~T.idx], 'SHARES (F&O stocks, monthly)')):
        if not len(grp): continue
        md(f'\n## {nm}')
        md('```\n' + grp.groupby(['symbol' if grp.idx.all() else 'strat', 'strat' if grp.idx.all() else 'k', 'k' if grp.idx.all() else 'dte'] if grp.idx.all() else ['strat', 'k', 'dte']).apply(summ).to_string() + '\n```')
        md('Daur-war (avg return on risk %, sab k/dte):')
        md('```\n' + grp.groupby(['strat', 'era'], observed=True).ror.mean().unstack().round(2).to_string() + '\n```')
        md('Trend ke hisaab se (spread sahi taraf?):')
        md('```\n' + grp.groupby(['strat', 'trend']).apply(summ)[['trades', 'win_pct', 'avg_ror', 'worst_ror']].to_string() + '\n```')
    ii = T[T.idx & T.quiet_score.notna()]
    if len(ii):
        md('\n## Index: "shaant" ishaare (regime score) ke saath — 2018 ke baad (rule 2008-17 se chuna)')
        z = ii[pd.to_datetime(ii.entry) >= '2018-01-01'].copy(); z['qs'] = np.where(z.quiet_score >= 2, '2+ ishaare', np.where(z.quiet_score >= 1, '1 ishaara', '0'))
        md('```\n' + z.groupby(['strat', 'qs']).apply(summ)[['trades', 'win_pct', 'avg_ror', 'worst_ror', 'rs_lot_avg']].to_string() + '\n```')
    open(os.path.join(OUT, 'sw_options.md'), 'w').write('\n'.join(MD) + '\n')
