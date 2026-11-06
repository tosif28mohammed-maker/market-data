"""WORLD TECHNIQUES STUDY (user 6 Nov 2026): 6 world-known techniques + Benner cycle (shifted, on years/months/days)
+ other markets (US, Japan, Korea, China, HK, Europe, gold, silver, commodities).
Usage: python study/world6.py <part>
 parts: pe | delivery | oi | factor | dualmom | volsize | benner_world | benner_india | global
Honest testing: eras / halves, placebo or chance (shuffled patterns), costs, learn-in-1st-half-test-in-2nd-half.
Outputs: study/results/w6_<part>*.csv + w6_<part>.md
"""
import os, sys, glob, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'study', 'results'); os.makedirs(OUT, exist_ok=True)
PART = sys.argv[1]
NSE = os.environ.get('NSE_HIST', os.path.join(R, 'nse_hist'))
IDX = os.path.join(R, 'data', 'indices'); GL = os.path.join(R, 'data', 'global')
rng = np.random.default_rng(5)
MD = [f'# World techniques — {PART}', '']
def md(*x): MD.extend(x)
def tbl(df): md('```', df.to_string(), '```', '')


def idx_series(fname):
    f = os.path.join(IDX, fname)
    if not os.path.exists(f): return None
    d = pd.read_csv(f, parse_dates=['date'])
    vc = next((c for c in ['TotalReturnsIndex', 'TotalReturnIndex', 'Total Returns Index', 'CLOSE', 'Close', 'close'] if c in d.columns), None)
    if vc is None: return None
    s = pd.to_numeric(d[vc].astype(str).str.replace(',', ''), errors='coerce'); s.index = d.date
    return s.dropna().sort_index()


def gl(name):
    d = pd.read_csv(os.path.join(GL, f'{name}.csv'), parse_dates=['date']).set_index('date')
    return d.close.dropna().sort_index()


def perf(ret, per_year):
    """ret: periodic simple returns series."""
    ret = ret.dropna()
    if len(ret) < 3: return {}
    eq = (1 + ret).cumprod(); yrs = len(ret) / per_year
    cagr = eq.iloc[-1] ** (1 / yrs) - 1; vol = ret.std() * np.sqrt(per_year)
    dd = (eq / eq.cummax() - 1).min()
    return dict(CAGR=round(cagr * 100, 1), vol=round(vol * 100, 1), maxDD=round(dd * 100, 1), sharpe=round((ret.mean() * per_year) / (vol + 1e-12), 2), years=round(yrs, 1))


# =====================================================================================================
if PART == 'pe':
    pe = pd.read_csv(os.path.join(IDX, 'NIFTY50_PE.csv'), parse_dates=['date']).set_index('date')
    pcol = next(c for c in pe.columns if c.lower() == 'pe'); pe = pd.to_numeric(pe[pcol], errors='coerce').dropna()
    tri = idx_series('NIFTY_50_TRI.csv')
    if tri is None: tri = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close
    tri = tri.reindex(pe.index).ffill()
    rows = []
    D = pd.DataFrame({'pe': pe, 'tri': tri}).dropna()
    for yrs in (1, 3, 5):
        n = 252 * yrs
        D[f'f{yrs}y'] = ((D.tri.shift(-n) / D.tri) ** (1 / yrs) - 1) * 100
    bins = [0, 16, 18, 20, 22, 24, 26, 100]; D['band'] = pd.cut(D.pe, bins, labels=['<16', '16-18', '18-20', '20-22', '22-24', '24-26', '26+'])
    T = D.groupby('band', observed=True).agg(days=('pe', 'size'), f1y=('f1y', 'mean'), f1y_up=('f1y', lambda x: (x > 0).mean() * 100),
                                             f3y=('f3y', 'mean'), f3y_min=('f3y', 'min'), f5y=('f5y', 'mean'), f5y_min=('f5y', 'min')).round(1)
    T.to_csv(f'{OUT}/w6_pe.csv')
    md(f'Nifty 50 PE {D.index[0].date()} se {D.index[-1].date()} tak; aaj PE {D.pe.iloc[-1]:.1f} (itihaas ka {(D.pe < D.pe.iloc[-1]).mean() * 100:.0f} percentile)',
       'Har PE band se aage ka saalana return (TRI, dividend sahit), % — overlapping windows, isliye asli "independent" saal kam:')
    tbl(T)
    for nm, a, b in (('1999-2012', '1999', '2012'), ('2013-2026', '2013', '2026')):
        x = D.loc[a:b]; c = x[['pe', 'f1y', 'f3y']].dropna()
        md(f'{nm}: corr(PE, agla 1 saal) {c.pe.corr(c.f1y):.2f}, corr(PE, agle 3 saal) {c.pe.corr(c.f3y):.2f}')
    md('', 'PE ka rule: band ke hisaab se equity % (PE<18: 100%, 18-22: 80%, 22-26: 60%, 26+: 40%; baaki 6.5% FD jaisa):')
    w = pd.cut(D.pe, [0, 18, 22, 26, 100], labels=[1.0, .8, .6, .4]).astype(float)
    m = D.resample('ME').last(); wm = w.resample('ME').last().shift(1)
    rr = m.tri.pct_change(); strat = wm * rr + (1 - wm) * (0.065 / 12)
    tbl(pd.DataFrame({'Nifty buy&hold': perf(rr, 12), 'PE-band mix': perf(strat, 12)}).T)

# =====================================================================================================
elif PART in ('delivery', 'oi', 'volsize', 'factor'):
    import ni_common as c
    P = c.load(); a = P['a']

if PART == 'delivery':
    fs = sorted(glob.glob(f'{NSE}/deliv/*.csv.gz'))
    D = pd.concat([pd.read_csv(f, parse_dates=['date']) for f in fs])
    D = D[D.series == 'EQ']
    dp = D.pivot_table(index='date', columns='symbol', values='deliv_pct').reindex(index=a.index, columns=a.columns)
    md(f'Delivery data: {len(fs)} saal files, {D.date.min().date()} se {D.date.max().date()}, {D.symbol.nunique()} shares')
    F, mkt = c.fwd(P, hs=(5, 20, 60))
    r = a.pct_change(fill_method=None) * 100
    mu, sd = dp.rolling(60, min_periods=40).mean().shift(1), dp.rolling(60, min_periods=40).std().shift(1)
    dz = (dp - mu) / sd
    d20, d60 = dp.rolling(20, min_periods=15).mean(), dp.rolling(60, min_periods=40).mean()
    ma50 = a.rolling(50, min_periods=40).mean(); ok = dp.notna()
    rows = []
    rows += c.evaluate(c.thin(ok & (r >= 1.5) & (dz >= 1.5)), F, 'ACCUMULATION: up 1.5%+ & delivery high (z>=1.5)', placebo=c.thin(ok & (r >= 1.5) & (dz.abs() < .5)))
    rows += c.evaluate(c.thin(ok & (r <= -1.5) & (dz >= 1.5)), F, 'DISTRIBUTION: down 1.5%+ & delivery high', placebo=c.thin(ok & (r <= -1.5) & (dz.abs() < .5)))
    rows += c.evaluate(c.thin(ok & (r >= 1.5) & (dz <= -1)), F, 'SPECULATIVE UP: up 1.5%+ & delivery low', placebo=c.thin(ok & (r >= 1.5) & (dz.abs() < .5)))
    rows += c.evaluate(c.thin(ok & (d20 - d60 >= 8) & (a > ma50)), F, 'DELIVERY TREND: 20d avg 8+ pts above 60d & above 50DMA',
                       placebo=c.thin(ok & ((d20 - d60).abs() < 2) & (a > ma50)))
    rows += c.evaluate(c.thin(ok & (dz >= 2) & (r.abs() < 1)), F, 'QUIET ACCUMULATION: delivery z>=2, price flat', placebo=c.thin(ok & (dz.abs() < .5) & (r.abs() < 1)))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_delivery.csv', index=False)
    tbl(T[T.era.isin(['ALL', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'])][['study', 'h', 'era', 'n', 'excess', 'win_vs_mkt', 'raw_net', 't_dates', 'placebo_excess', 'vs_placebo']].set_index('study'))

if PART == 'oi':
    fs = sorted(glob.glob(f'{NSE}/fo/*.csv.gz'))
    X = pd.concat([pd.read_csv(f, parse_dates=['date']) for f in fs])
    md(f'F&O data: {len(fs)} saal, {X.date.min().date()} se {X.date.max().date()}, {X.symbol.nunique()} symbols')
    fc = X.pivot_table(index='date', columns='symbol', values='fut_close'); fo = X.pivot_table(index='date', columns='symbol', values='fut_oi')
    ce = X.pivot_table(index='date', columns='symbol', values='ce_oi'); pe_ = X.pivot_table(index='date', columns='symbol', values='pe_oi')
    dP = fc.pct_change(fill_method=None) * 100; dO = fo.pct_change(fill_method=None) * 100
    good = (dO.abs() < 40) & (dP.abs() < 15)
    st = {'LONG BUILDUP (P+1%, OI+5%)': (dP >= 1) & (dO >= 5), 'SHORT BUILDUP (P-1%, OI+5%)': (dP <= -1) & (dO >= 5),
          'SHORT COVERING (P+1%, OI-5%)': (dP >= 1) & (dO <= -5), 'LONG UNWINDING (P-1%, OI-5%)': (dP <= -1) & (dO <= -5)}
    plac = {'up': (dP >= 1) & (dO.abs() < 1.5), 'down': (dP <= -1) & (dO.abs() < 1.5)}
    cols = [s for s in fc.columns if s in a.columns]
    F, mkt = c.fwd(P, hs=(1, 3, 5, 10))
    al = lambda m: (m & good).reindex(index=a.index, columns=a.columns).fillna(False).astype(bool)
    rows = []
    for nm, m in st.items():
        pl = plac['up'] if 'P+' in nm else plac['down']
        rows += c.evaluate(c.thin(al(m), 5), F, nm, hs=(1, 3, 5, 10), placebo=c.thin(al(pl), 5))
    pcr = pe_ / ce.replace(0, np.nan)
    hi = pcr >= pcr.rolling(250, min_periods=120).quantile(0.9).shift(1); lo = pcr <= pcr.rolling(250, min_periods=120).quantile(0.1).shift(1)
    rows += c.evaluate(c.thin(al(hi), 5), F, 'STOCK PCR very high (puts heavy)', hs=(1, 3, 5, 10))
    rows += c.evaluate(c.thin(al(lo), 5), F, 'STOCK PCR very low (calls heavy)', hs=(1, 3, 5, 10))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_oi.csv', index=False)
    tbl(T[T.era.isin(['ALL', '2013-20', '2021-26', 'Nov23-now'])][['study', 'h', 'era', 'n', 'excess', 'win_vs_mkt', 'raw', 't_dates', 'placebo_excess', 'vs_placebo']].set_index('study'))
    # Nifty index states -> Nifty next days
    nf = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close
    if 'NIFTY' in fc.columns:
        nrows = []
        f = {h: (nf.shift(-h) / nf - 1) * 100 for h in (1, 3, 5, 10)}
        for nm, m in list(st.items()) + [('ALL DAYS', pd.DataFrame(True, index=fc.index, columns=fc.columns))]:
            dd = m['NIFTY'][m['NIFTY'].fillna(False).astype(bool)].index if nm != 'ALL DAYS' else fc.index
            if nm != 'ALL DAYS':
                dd = fc.index[(((dP['NIFTY'] >= .5) if 'P+' in nm else (dP['NIFTY'] <= -.5)) & ((dO['NIFTY'] >= 3) if 'OI+' in nm else (dO['NIFTY'] <= -3)) & good['NIFTY']).fillna(False).values]
            row = dict(state=nm.replace('1%', '0.5%').replace('5%', '3%'), n=len(dd))
            for h in (1, 3, 5, 10):
                v = f[h].reindex(dd).dropna(); row[f'nifty{h}d'] = round(v.mean(), 2); row[f'up{h}d_%'] = round((v > 0).mean() * 100, 0)
            nrows.append(row)
        md('NIFTY futures state -> Nifty agle din (option buyer ke liye: kya direction pakki hai?)'); tbl(pd.DataFrame(nrows).set_index('state'))

if PART == 'volsize':
    cl, hi_, lo_ = a, P['h'], P['l']
    tr = pd.concat([(hi_ - lo_), (hi_ - cl.shift()).abs(), (lo_ - cl.shift()).abs()]).groupby(level=0).max() if False else np.maximum(hi_ - lo_, np.maximum((hi_ - cl.shift()).abs(), (lo_ - cl.shift()).abs()))
    atrp = (tr.rolling(14, min_periods=10).mean() / cl * 100)
    s20 = cl.rolling(20, min_periods=15).mean(); s200 = cl.rolling(200, min_periods=180).mean(); r52 = cl / cl.shift(250) - 1
    sig = (cl <= s20 * 0.92) & (cl > s200) & (r52 >= 0.3)
    sig = c.thin(sig, 20)
    trades = []
    A = cl.values; S20 = s20.values; AT = atrp.values; idx = cl.index
    for j in range(cl.shape[1]):
        for i in np.flatnonzero(sig.values[:, j]):
            e = A[i, j]
            if np.isnan(e) or np.isnan(AT[i, j]): continue
            k = i + 1; x = np.nan
            while k < len(idx) and k <= i + 20:
                if not np.isnan(A[k, j]) and A[k, j] >= S20[k - 1, j]: x = A[k, j]; break
                k += 1
            if np.isnan(x):
                k = min(i + 20, len(idx) - 1); x = A[k, j]
            if np.isnan(x): continue
            trades.append(dict(entry=idx[i], exit=idx[k], sym=cl.columns[j], ret=(x / e - 1) * 100 - 0.25, atr=AT[i, j]))
    Tt = pd.DataFrame(trades)
    med = Tt.atr.median(); Tt['w_vol'] = (med / Tt.atr).clip(0.25, 3)
    Tt['pnl_eq'] = Tt.ret; Tt['pnl_vol'] = Tt.ret * Tt.w_vol
    Tt['pnl_vol'] *= Tt.pnl_eq.abs().mean() / Tt.pnl_vol.abs().mean()   # same average bet size
    rows = []
    for era, a_, b_ in [('ALL', '2003', '2026'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-now', '2023-11', '2026')]:
        t = Tt[(Tt.entry >= a_) & (Tt.entry <= b_ + '-12-31')]
        mon = t.groupby(t.exit.dt.to_period('M'))[['pnl_eq', 'pnl_vol']].sum()
        for k in ('pnl_eq', 'pnl_vol'):
            rows.append(dict(era=era, sizing='barabar Rs' if k == 'pnl_eq' else 'volatility se', trades=len(t), avg=round(t[k].mean(), 2),
                             worst5pct_trade=round(t[k].quantile(.05), 2), monthly_sharpe=round(mon[k].mean() / mon[k].std() * np.sqrt(12), 2),
                             worst_month=round(mon[k].min(), 1), maxDD_cum=round(((mon[k].cumsum()) - mon[k].cumsum().cummax()).min(), 1)))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_volsize.csv', index=False)
    md('Dip niyam (20 DMA se 8% neeche, 200 DMA upar, 52w +30%), bahar = 20 DMA ya 20 din; kharcha 0.25%. Barabar Rs bnaam volatility se matra (dono ka ausat daav barabar):'); tbl(T.set_index(['era', 'sizing']))

if PART == 'factor':
    m = a.resample('ME').last(); mr = m.pct_change(fill_method=None).clip(-.6, 1.5)
    dr = a.pct_change(fill_method=None).clip(-.5, .5)
    vol = dr.rolling(250, min_periods=200).std().resample('ME').last()
    mom = (m.shift(1) / m.shift(12) - 1)
    out = []
    for nm, score, asc in (('LOW VOLATILITY (1 saal)', vol, True), ('MOMENTUM 12-1 mahina', mom, False)):
        rk = score.rank(axis=1, pct=True, ascending=asc)
        for q in range(5):
            w = ((rk > q / 5) & (rk <= (q + 1) / 5)).astype(float); w = w.div(w.sum(axis=1), axis=0)
            turn = w.diff().abs().sum(axis=1) / 2
            ret = (w.shift(1) * mr).sum(axis=1) - turn.shift(1).fillna(0) * 0.006
            ret = ret[w.shift(1).sum(axis=1) > 0]
            for era, a_, b_ in [('ALL', '2004', '2026'), ('2004-12', '2004', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-now', '2023-11', '2026')]:
                out.append(dict(factor=nm, quintile=f'Q{q + 1}' + (' (best)' if q == 0 else ' (worst)' if q == 4 else ''), era=era, **perf(ret.loc[a_:b_], 12)))
    T = pd.DataFrame(out); T.to_csv(f'{OUT}/w6_factor_own.csv', index=False)
    md('Apne ~1,500 shares par (survivors — purane dead shares nahi, isliye returns thode bade dikhte hain), mahine-war, kharcha 0.6%/turnover:')
    tbl(T[T.quintile.str.contains('best|worst')].pivot_table(index=['factor', 'quintile'], columns='era', values='CAGR'))
    tbl(T[T.quintile.str.contains('best|worst')].pivot_table(index=['factor', 'quintile'], columns='era', values='maxDD'))
    rows = []
    for f in sorted(glob.glob(os.path.join(IDX, '*_TRI.csv'))):
        s = idx_series(os.path.basename(f))
        if s is None or len(s) < 500: continue
        mm = s.resample('ME').last().pct_change()
        for era, a_, b_ in [('2006-12', '2006', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('Nov23-now', '2023-11', '2026')]:
            rows.append(dict(index=os.path.basename(f)[:-8], era=era, **perf(mm.loc[a_:b_], 12)))
    if rows:
        T2 = pd.DataFrame(rows); T2.to_csv(f'{OUT}/w6_factor_indices.csv', index=False)
        md('NSE factor indices (TRI; launch se pehle ka data NSE ka back-test):'); tbl(T2.pivot_table(index='index', columns='era', values='CAGR')); tbl(T2.pivot_table(index='index', columns='era', values='maxDD'))

if PART == 'dualmom':
    nf = idx_series('NIFTY_50_TRI.csv')
    if nf is None:  # niftyindices API dead from Actions (6 Nov 2026): price index + ~1.3%/yr dividend approx
        z = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna().sort_index()
        nf = z * (1 + 0.013 / 252) ** np.arange(len(z)); md('Note: Nifty TRI nahi mila, price + 1.3% dividend approx use kiya.')
    gs = idx_series('NIFTY_10_YR_BENCHMARK_G_SEC_TRI.csv')
    gold = (gl('CMD_GOLD') * gl('FX_USDINR').reindex(gl('CMD_GOLD').index).ffill()).dropna()
    M = pd.DataFrame({'nifty': nf.resample('ME').last() if nf is not None else None, 'gold': gold.resample('ME').last(),
                      'gsec': gs.resample('ME').last() if gs is not None else None}).dropna(subset=['nifty', 'gold'])
    if M.gsec.isna().all(): M['gsec'] = (1 + 0.065 / 12) ** np.arange(len(M))
    M = M.ffill().dropna(); R_ = M.pct_change()
    res = {}
    res['Nifty buy&hold'] = R_.nifty; res['Sona buy&hold'] = R_.gold; res['50/50 Nifty+Sona'] = (R_.nifty + R_.gold) / 2
    for L in (3, 6, 9, 12):
        lb = M / M.shift(L) - 1
        best = np.where(lb.nifty >= lb.gold, 'nifty', 'gold')
        pick = pd.Series(np.where(np.maximum(lb.nifty, lb.gold) > lb.gsec, best, 'gsec'), index=M.index).shift(1)
        ret = pd.Series([R_.loc[d, p] if isinstance(p, str) else np.nan for d, p in pick.items()], index=M.index)
        sw = (pick != pick.shift(1)) & pick.notna(); ret = ret - sw.astype(float) * 0.002
        res[f'Dual momentum {L} mahine'] = ret
    sma = M.nifty.rolling(10).mean(); inn = (M.nifty > sma).shift(1)
    res['Nifty 10-mahine SMA (warna G-sec)'] = pd.Series(np.where(inn, R_.nifty, R_.gsec), index=M.index)
    rows = []
    for k, v in res.items():
        for era, a_, b_ in [('ALL', '2000', '2026'), ('2004-12', '2004', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026')]:
            rows.append(dict(strategy=k, era=era, **perf(v.loc[a_:b_].iloc[13:] if era == 'ALL' else v.loc[a_:b_], 12)))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_dualmom.csv', index=False)
    md(f'Mahine-war, {M.index[0].date()} se; G-sec = Nifty 10 yr G-sec TRI (na mile to 6.5%); switch kharcha 0.2%')
    tbl(T.pivot_table(index='strategy', columns='era', values='CAGR')); tbl(T.pivot_table(index='strategy', columns='era', values='maxDD'))

# =====================================================================================================
# BENNER: buy at C (hard times), sell at B (good times). Cycle 27 units starting at C=0: long [0,3) [9,11) [16,20).
PAT = np.zeros(27, bool); PAT[[0, 1, 2, 9, 10, 16, 17, 18, 19]] = True
YEAR0 = 1996   # Benner C year


def benner_edges(x, pat=PAT):
    """x: unit returns (n). returns edge (mean long - mean out) for each of 27 phases, plus t."""
    n = len(x); t = np.arange(n); out = []
    for p in range(27):
        m = pat[(t + p) % 27]
        if m.sum() < 2 or (~m).sum() < 2: out.append((np.nan, np.nan)); continue
        a1, a2 = x[m], x[~m]
        e = a1.mean() - a2.mean(); se = np.sqrt(a1.var(ddof=1) / len(a1) + a2.var(ddof=1) / len(a2))
        out.append((e, e / se if se > 0 else np.nan))
    return np.array(out)


def oos(x, pat=PAT):
    """pick best phase in 1st half, return edge of that phase in 2nd half (keeping calendar alignment)."""
    h = len(x) // 2
    if h < 27: return np.nan
    e1 = benner_edges(x[:h], pat)[:, 0]
    if np.all(np.isnan(e1)): return np.nan
    p = int(np.nanargmax(e1))
    t = np.arange(len(x)); m = pat[(t + p) % 27]
    x2, m2 = x[h:], m[h:]
    return x2[m2].mean() - x2[~m2].mean()


def chance_oos(x, k=40):
    return np.nanmean([(oos(x, rng.permutation(PAT)) > 0) for _ in range(k)])


if PART == 'benner_world':
    names = ['US_SP500', 'US_NASDAQ', 'US_DOW', 'JP_NIKKEI', 'KR_KOSPI', 'HK_HANGSENG', 'CN_SHANGHAI', 'EU_DAX', 'EU_FTSE', 'TW_TAIEX', 'SG_STI',
             'CMD_GOLD', 'CMD_SILVER', 'CMD_CRUDE_WTI', 'CMD_COPPER', 'IN_SENSEX']
    series = {n: gl(n) for n in names if os.path.exists(os.path.join(GL, f'{n}.csv'))}
    nt = idx_series('NIFTY_50_TRI.csv')
    if nt is not None: series['NIFTY50_TRI'] = nt
    rows = []
    for n, s in series.items():
        y = s.resample('YE').last().pct_change().dropna(); yrs = y.index.year.values
        # exact Benner calendar years: long if year in a C->B window (year after C .. B year)
        ph0 = (yrs - YEAR0) % 27
        exact = {}
        for sh in range(-3, 4):
            m = PAT[(ph0 - 1 - sh) % 27]   # return of year Y counts if bought at end of Y-1
            if m.sum() >= 2 and (~m).sum() >= 2:
                exact[sh] = (y.values[m].mean() - y.values[~m].mean()) * 100
        row = dict(asset=n, years=len(y), first=int(yrs[0]), benner_exact_edge=round(exact.get(0, np.nan), 1),
                   best_shift=max(exact, key=exact.get) if exact else None, best_shift_edge=round(max(exact.values()), 1) if exact else np.nan)
        for unit, rs in (('month', s.resample('ME').last().pct_change().dropna().values), ('day', s.pct_change().dropna().values)):
            E = benner_edges(rs)
            row[f'{unit}_best_t'] = round(np.nanmax(E[:, 1]), 2); row[f'{unit}_oos_edge_bp'] = round(oos(rs) * 1e4, 1)
            row[f'{unit}_chance_oos_pos_%'] = round(chance_oos(rs, 20) * 100)
        rows.append(row)
    # pre-registered test: exact Benner years (shift 0), permutation vs random 27-patterns with 9 long years
    def yedge(y, pat):
        Y = y.index.year.values; mm = pat[(Y - 1 - YEAR0) % 27]
        return y.values[mm].mean() - y.values[~mm].mean()
    ys = {n: s.resample('YE').last().pct_change().dropna() for n, s in series.items()}
    for row in rows:
        y = ys[row['asset']]; e0 = yedge(y, PAT); sims = np.array([yedge(y, rng.permutation(PAT)) for _ in range(3000)])
        row['exact_perm_p'] = round((sims >= e0).mean(), 3)
        Y = y.index.year.values; mm = PAT[(Y - 1 - YEAR0) % 27]; h = Y < np.median(Y)
        row['long_avg_%'] = round(y.values[mm].mean() * 100, 1); row['out_avg_%'] = round(y.values[~mm].mean() * 100, 1)
        row['edge_1st_half'] = round((y.values[mm & h].mean() - y.values[~mm & h].mean()) * 100, 1)
        row['edge_2nd_half'] = round((y.values[mm & ~h].mean() - y.values[~mm & ~h].mean()) * 100, 1)
    eq_names = [n for n in ys if not n.startswith('CMD')]
    tot = lambda pat: np.mean([yedge(ys[n], pat) for n in eq_names])
    e0 = tot(PAT); sims = np.array([tot(rng.permutation(PAT)) for _ in range(2000)])
    md(f'Sab equity indices ek saath (same pattern): ausat edge {e0 * 100:.1f}%/saal, kismat se itna ya zyada p = {(sims >= e0).mean():.3f}')
    yrs_ahead = [Yr for Yr in range(2026, 2041)]
    md('Aage ke saal (Benner): long/khareedi wale saal (return count) = ' + ', '.join(str(Yr) for Yr in yrs_ahead if PAT[(Yr - 1 - YEAR0) % 27]) +
       '; baaki = bahar/kamzor saal: ' + ', '.join(str(Yr) for Yr in yrs_ahead if not PAT[(Yr - 1 - YEAR0) % 27]))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_benner_world.csv', index=False)
    md('Benner: C (hard times) saal ke ant mein khareedo, B (good times) mein becho. Edge = long saalon ka ausat return − baaki saalon ka (% per saal).',
       'Shift -3..+3 = saal aage-peechhe khiskaakar. month/day = wahi 27-unit pattern mahine/din par, har 27 phase; best phase pehle aadhe mein chuna, doosre aadhe mein parkha (oos, basis points per unit); chance = random 27-pattern se oos positive hone ka %.')
    tbl(T.set_index('asset'))
    # decade cycle (year ending 0-9)
    if 'US_SP500' in series:
        y = series['US_SP500'].resample('YE').last().pct_change().dropna()
        dec = y.groupby(y.index.year % 10).agg(['mean', 'count', lambda v: (v > 0).mean()]); dec.columns = ['avg', 'n', 'up']
        h1 = y[y.index.year < 1977].groupby(y[y.index.year < 1977].index.year % 10).mean(); h2 = y[y.index.year >= 1977].groupby(y[y.index.year >= 1977].index.year % 10).mean()
        dec['1928-76'] = h1; dec['1977-2025'] = h2
        md('Decade cycle (saal ka aakhri ank), S&P500 1928 se, saalana return:'); tbl((dec * pd.Series({'avg': 100, 'n': 1, 'up': 100, '1928-76': 100, '1977-2025': 100})).round(1))

if PART == 'benner_india':
    import ni_common as c
    P = c.load(); a = P['a']
    rows = []
    for unit, R_ in (('month', a.resample('ME').last().pct_change(fill_method=None)), ('day', a.pct_change(fill_method=None))):
        R_ = R_.clip(-.5, .5)
        for s in R_.columns:
            x = R_[s].dropna().values
            if len(x) < (120 if unit == 'month' else 1500): continue
            o = oos(x); pr = oos(x, rng.permutation(PAT))
            rows.append(dict(unit=unit, symbol=s, n=len(x), oos_edge=o, chance_oos_edge=pr))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_benner_india.csv.gz', index=False)
    S = T.groupby('unit').agg(stocks=('symbol', 'size'), oos_positive_pct=('oos_edge', lambda v: (v > 0).mean() * 100),
                              chance_positive_pct=('chance_oos_edge', lambda v: (v > 0).mean() * 100),
                              avg_oos_edge_pct=('oos_edge', lambda v: v.mean() * 100), avg_chance_edge_pct=('chance_oos_edge', lambda v: v.mean() * 100)).round(2)
    md('Har Indian share par Benner 27-unit pattern (mahine aur din), har 27 phase; pehle aadhe mein best phase, doosre aadhe mein parkha. Agar pattern asli hai to oos positive % chance se kaafi zyada hona chahiye:'); tbl(S)
    top = T[T.unit == 'month'].nlargest(15, 'oos_edge')[['symbol', 'n', 'oos_edge']]
    md('Sabse achhe 15 (mahina) — dhyaan: 1,500 mein se kuch to kismat se bhi achhe dikhenge:'); tbl(top.set_index('symbol'))

# =====================================================================================================
if PART == 'global':
    names = ['US_SP500', 'US_NASDAQ', 'US_RUSSELL2000', 'JP_NIKKEI', 'KR_KOSPI', 'HK_HANGSENG', 'CN_SHANGHAI', 'EU_DAX', 'EU_FTSE', 'EU_STOXX50',
             'TW_TAIEX', 'SG_STI', 'IN_SENSEX', 'CMD_GOLD', 'CMD_SILVER', 'CMD_CRUDE_WTI', 'CMD_COPPER', 'CMD_NATGAS']
    rows, seas, tom = [], [], []
    for n in names:
        f = os.path.join(GL, f'{n}.csv')
        if not os.path.exists(f): continue
        s = gl(n); m = s.resample('ME').last(); r = m.pct_change()
        half = m.index[len(m) // 2]
        sma10 = m.rolling(10).mean(); inn = (m > sma10).shift(1).fillna(False).astype(bool)
        ts12 = (m / m.shift(12) - 1 > 0).shift(1).fillna(False).astype(bool)
        cash = 0.03 / 12
        strat = {'buy&hold': r, '10-mahine SMA': pd.Series(np.where(inn, r, cash), index=r.index) - inn.astype(int).diff().abs().fillna(0) * 0.001,
                 '12-mahine trend': pd.Series(np.where(ts12, r, cash), index=r.index) - ts12.astype(int).diff().abs().fillna(0) * 0.001}
        for k, v in strat.items():
            for era, x in (('pehla aadha', v.loc[:half]), ('doosra aadha', v.loc[half:])):
                rows.append(dict(asset=n, strategy=k, era=era, start=str(m.index[13].date()), **perf(x.iloc[13:] if era == 'pehla aadha' else x, 12)))
        # sell in May: Nov-Apr vs May-Oct monthly avg, by halves
        mo = r.index.month; win = np.isin(mo, [11, 12, 1, 2, 3, 4])
        for era, sl in (('pehla aadha', r.index < half), ('doosra aadha', r.index >= half)):
            seas.append(dict(asset=n, era=era, nov_apr=round(r[win & sl].mean() * 100, 2), may_oct=round(r[~win & sl].mean() * 100, 2)))
        # turn of month: last day + first 3 days vs rest
        d = s.pct_change().dropna(); dfm = pd.DataFrame({'r': d}); dfm['ym'] = dfm.index.to_period('M')
        dfm['k'] = dfm.groupby('ym').cumcount(); dfm['kr'] = dfm.groupby('ym').cumcount(ascending=False)
        tw = (dfm.k <= 2) | (dfm.kr == 0)
        for era, sl in (('pehla aadha', dfm.index < half), ('doosra aadha', dfm.index >= half)):
            tom.append(dict(asset=n, era=era, turn_of_month_bp=round(dfm.r[tw & sl].mean() * 1e4, 1), other_days_bp=round(dfm.r[~tw & sl].mean() * 1e4, 1)))
    T = pd.DataFrame(rows); T.to_csv(f'{OUT}/w6_global_trend.csv', index=False)
    md('Duniya ke bazaar + commodities: buy&hold vs trend niyam (mahine-war, kharcha 0.1%/switch, bahar = 3%/saal cash). Dono aadhon mein:')
    tbl(T.pivot_table(index=['asset', 'strategy'], columns='era', values='CAGR')); tbl(T.pivot_table(index=['asset', 'strategy'], columns='era', values='maxDD'))
    S1 = pd.DataFrame(seas); S1.to_csv(f'{OUT}/w6_global_sellinmay.csv', index=False)
    md('"Sell in May": Nov-Apr bnaam May-Oct ka ausat mahina %:'); tbl(S1.pivot_table(index='asset', columns='era', values=['nov_apr', 'may_oct']))
    S2 = pd.DataFrame(tom); S2.to_csv(f'{OUT}/w6_global_tom.csv', index=False)
    md('Turn-of-month (mahine ka aakhri + pehle 3 din) bnaam baaki din, basis points/din:'); tbl(S2.pivot_table(index='asset', columns='era', values=['turn_of_month_bp', 'other_days_bp']))
    # gold/silver ratio
    try:
        g, sv = gl('CMD_GOLD'), gl('CMD_SILVER'); gm, sm = g.resample('ME').last(), sv.resample('ME').last()
        ratio = gm / sm; z = (ratio - ratio.rolling(60).mean()) / ratio.rolling(60).std()
        rel6 = (sm.shift(-6) / sm - gm.shift(-6) / gm) * 100
        G = pd.DataFrame({'z': z, 'silver_minus_gold_6m': rel6}).dropna()
        md('Gold/Silver ratio (5 saal ke ausat se z): agle 6 mahine chaandi − sona %:'); tbl(G.groupby(pd.cut(G.z, [-9, -1.5, -0.5, 0.5, 1.5, 9]), observed=True).silver_minus_gold_6m.agg(['mean', 'count']).round(2))
    except Exception as e:
        md(f'gold/silver ratio fail: {e}')
    # US VIX > 30 -> S&P next 1/3/6 months
    try:
        v = gl('US_VIX'); sp = gl('US_SP500').reindex(v.index).ffill()
        f = {h: (sp.shift(-h) / sp - 1) * 100 for h in (21, 63, 126)}
        rows = []
        for lab, mk in (('VIX>30', v > 30), ('VIX>40', v > 40), ('sab din', v > 0)):
            dd = v.index[mk.values]
            rows.append(dict(state=lab, days=len(dd), **{f'sp_{h}d': round(f[h].reindex(dd).mean(), 2) for h in f}, **{f'up_{h}d': round((f[h].reindex(dd) > 0).mean() * 100) for h in f}))
        md('US VIX dar -> S&P500 aage (1, 3, 6 mahine):'); tbl(pd.DataFrame(rows).set_index('state'))
    except Exception as e:
        md(f'vix fail: {e}')

open(f'{OUT}/w6_{PART}.md', 'w').write('\n'.join(MD)); print('\n'.join(MD)[:8000])
