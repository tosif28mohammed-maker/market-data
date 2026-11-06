"""EVENT / JHATKA STUDY (user 6 Nov 2026): झटके वाली candle (अच्छी/बुरी खबर, बाज़ार-भर का धक्का) के बाद
कितने candle तक और कितना चाल जारी रहती है — हर शेयर, हर timeframe; देर से entry (उसी दिन दोपहर / अगले दिन) पर क्या मिलता है.
Parts:
 A. STOCK SHOCKS (every TF): candle return (close/prev close) z >= +3 / <= -3 vs own last-60-candle std; split into
    'own' (stock-specific: market move small) and 'market' (whole market moved). Entry E0 = shock candle close (afternoon
    entry), E1 = next candle close (late entry). For h = 1,2,3,5,10,20: P(up), avg return, excess vs market.
    Continuation: consecutive candles in the same direction after entry; best high / worst low in next 20 candles (OHLC);
    candles to peak; distribution (min, p10, p25, median, p75, p90, max). Placebo = random ordinary candles of same stocks.
    Per stock: half1 vs half2 consistency vs chance.
 B. MARKET EVENTS (daily): Nifty ±2% day, 3-day ±4%, 10-day +5% thrust, S&P500 ±2.5% night, Brent ±5% day / -10% 5 days,
    US VIX +30%, USDINR ±1%, US election / midterm results. Forward Nifty + equal-weight basket 1..20 days, run length,
    max/min; which industries move most (half-split checked).
 C. BONUS / SPLIT (daily, yfinance splits): ex-date window -40..-1 and +1..+60 vs market.
Groups: daily (1W,1D + B + C) | hourly (4H,3H,2H,1H) | m15 (45m,30m,15m) | m5 (5m). Never liquidity D.
"""
import os, sys, glob, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'study', 'results'); os.makedirs(OUT, exist_ok=True)
G = sys.argv[1]
HS = [1, 2, 3, 5, 10, 20]; Z = 3.0; GAP = 10
liq = pd.read_csv(os.path.join(R, 'study', 'results', 'liq_all.csv'))
BAD = set(liq.loc[liq.liquidity.astype(str).str[0] == 'D', 'symbol'])
av = os.path.join(R, 'paper', 'avoid_liquidity_D.txt')
if os.path.exists(av): BAD |= {l.strip() for l in open(av) if l.strip() and not l.startswith('#')}
rng = np.random.default_rng(11)
U = os.environ.get('U500', os.path.join(R, '..', 'u500')); I = os.environ.get('INTRA', os.path.join(R, '..', 'ih'))
LIM = int(os.environ.get('LIMIT', '0'))


def per_day_group(d, n):
    if n == 1: return d
    d = d.copy(); d['day'] = d.time.dt.date; d['k'] = d.groupby('day').cumcount() // n
    g = d.groupby(['day', 'k'], sort=True)
    return pd.DataFrame({'time': g.time.last(), 'open': g.open.first(), 'high': g.high.max(), 'low': g.low.min(),
                         'close': g.close.last(), 'volume': g.volume.sum()}).reset_index(drop=True)


def load_daily():
    seen = set()
    for f in glob.glob(f'{U}/u1000/daily/*.csv.gz') + glob.glob(f'{U}/u2000/daily/*.csv.gz'):
        s = os.path.basename(f)[:-7]
        if s in BAD or s in seen: continue
        seen.add(s)
        d = pd.read_csv(f, parse_dates=['date']).dropna(subset=['open', 'close']).drop_duplicates('date').sort_values('date')
        d = d[(d.open > 0) & (d.close > 0)]
        if len(d) < 300: continue
        r = (d.adj / d.close).values
        D = pd.DataFrame({'time': d.date.values, 'open': d.open.values * r, 'high': d.high.values * r, 'low': d.low.values * r,
                          'close': d.adj.values, 'volume': d.volume.values})
        W = D.set_index('time').resample('W-FRI').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'}).dropna().reset_index()
        yield s, {'1D': D, '1W': W}


def load_intra(sub, tfs):
    for f in sorted(glob.glob(f'{I}/intra/{sub}/*.csv.gz')):
        s = os.path.basename(f)[:-7]
        if s in BAD or s.startswith('^'): continue
        d = pd.read_csv(f, parse_dates=['time']).dropna(subset=['open', 'close']).drop_duplicates('time').sort_values('time')
        d = d[(d.open > 0) & (d.close > 0)].reset_index(drop=True)
        if len(d) < 300: continue
        yield s, {nm: per_day_group(d, n) for nm, n in tfs}


SRC = {'daily': (['1W', '1D'], load_daily, [('ALL', '1900', '2100'), ('2003-12', '2003', '2012-12-31'), ('2013-20', '2013', '2020-12-31'),
                                            ('2021-26', '2021', '2026-12-31'), ('Nov23-now', '2023-11-01', '2026-12-31')]),
       'hourly': (['4H', '3H', '2H', '1H'], lambda: load_intra('h1', [('4H', 4), ('3H', 3), ('2H', 2), ('1H', 1)]),
                  [('ALL', '1900', '2100'), ('half1', '2023-11-01', '2025-04-30'), ('half2', '2025-05-01', '2026-12-31')]),
       'm15': (['45m', '30m', '15m'], lambda: load_intra('m15', [('45m', 3), ('30m', 2), ('15m', 1)]), [('ALL', '1900', '2100')]),
       'm5': (['5m'], lambda: load_intra('m5_all', [('5m', 1)]), [('ALL', '1900', '2100')])}
TFS, LOADER, ERAS = SRC[G]

# -------- pass 1: load all, build equal-weight market return per TF --------
data = {tf: {} for tf in TFS}
for i, (s, fr) in enumerate(LOADER()):
    if LIM and i >= LIM: break
    for tf, D in fr.items():
        if len(D) >= 120: data[tf][s] = D.set_index('time')
    if i % 300 == 0: print('load', i, s, flush=True)


def fwd_stats(c, h_, l_, i, sign, mk):
    """from entry index i (close), sign +1 up / -1 down. returns dict."""
    e = c[i]; out = {}
    for h in HS:
        if i + h < len(c):
            r = (c[i + h] / e - 1) * 100
            out[f'r{h}'] = r; out[f'x{h}'] = r - mk[h]
    j = i + 1; run = 0
    while j < len(c) and j <= i + 20 and np.sign(c[j] - c[j - 1]) == sign: run += 1; j += 1
    out['run'] = run
    w = slice(i + 1, min(i + 21, len(c)))
    if i + 1 < len(c):
        hi, lo = h_[w].max(), l_[w].min()
        best = (hi / e - 1) * 100 if sign > 0 else (1 - lo / e) * 100      # move in event direction (OHLC)
        worst = (lo / e - 1) * 100 if sign > 0 else (1 - hi / e) * 100      # adverse
        k_peak = int(np.argmax(c[w])) + 1 if sign > 0 else int(np.argmin(c[w])) + 1
        out.update(best=best, worst=worst, to_peak=k_peak)
    return out


def summarize(df, tag):
    if len(df) == 0: return {}
    r = dict(kind=tag, n=len(df))
    for h in HS:
        if f'r{h}' in df:
            v = df[f'r{h}'].dropna().clip(-90, 300); x = df[f'x{h}'].dropna().clip(-90, 300)
            r[f'up{h}_%'] = round((v > 0).mean() * 100, 1); r[f'ret{h}'] = round(v.mean(), 2); r[f'exc{h}'] = round(x.mean(), 2)
    q = df.run
    r.update({'run_min': int(q.min()), 'run_p25': q.quantile(.25), 'run_med': q.median(), 'run_p75': q.quantile(.75), 'run_p90': q.quantile(.9),
              'run_max': int(q.max()), 'run>=2_%': round((q >= 2).mean() * 100, 1), 'run>=3_%': round((q >= 3).mean() * 100, 1)})
    if 'best' in df:
        b, w = df.best.dropna(), df.worst.dropna()
        r.update({'best20_p25': round(b.quantile(.25), 2), 'best20_med': round(b.median(), 2), 'best20_p75': round(b.quantile(.75), 2),
                  'best20_p90': round(b.quantile(.9), 2), 'best20_max': round(b.max(), 1), 'worst20_med': round(w.median(), 2),
                  'worst20_p10': round(w.quantile(.1), 2), 'to_peak_med': df.to_peak.median()})
    return r


rows, per_rows = [], []
for tf in TFS:
    S = data[tf]
    if not S: continue
    C = pd.DataFrame({s: d.close for s, d in S.items()}).sort_index()
    ret = C.pct_change(fill_method=None).clip(-0.2, 0.2)
    mret = ret.mean(axis=1); msd = mret.rolling(60, min_periods=40).std().shift(1)
    mz = (mret / msd)
    mcum = np.log1p(mret.fillna(0)).cumsum()
    ev_rows = []; pl_rows = []
    for s, d in S.items():
        c = d.close.values.astype(float); h_ = d.high.values.astype(float); l_ = d.low.values.astype(float)
        t = d.index; v = d.volume.values.astype(float)
        r = np.r_[np.nan, c[1:] / c[:-1] - 1]
        sd = pd.Series(r).rolling(60, min_periods=40).std().shift(1).values
        z = r / sd
        vm = pd.Series(v).rolling(50, min_periods=30).median().shift(1).values
        vr = np.where(vm > 0, v / vm, np.nan)
        mzs = mz.reindex(t).values; mc = mcum.reindex(t).ffill().values
        last = -999
        for i in np.flatnonzero(np.abs(np.nan_to_num(z)) >= Z):
            if i - last < GAP or i + 1 >= len(c): continue
            last = i; sign = int(np.sign(z[i]))
            kind = 'market' if abs(np.nan_to_num(mzs[i])) >= 2.5 and np.sign(mzs[i]) == sign else 'own'
            for ent, j in (('E0', i), ('E1', i + 1)):
                if j >= len(c): continue
                mk = {h: (np.expm1(mc[j + h] - mc[j]) * 100 if j + h < len(c) else np.nan) for h in HS}
                fs = fwd_stats(c, h_, l_, j, sign, mk)
                ev_rows.append(dict(symbol=s, time=t[i], dir='UP' if sign > 0 else 'DOWN', kind=kind, entry=ent, z=z[i],
                                    move=r[i] * 100, vol2x=bool(np.nan_to_num(vr[i]) >= 2), **fs))
        # placebo: ordinary candles (|z|<1), 3% sample
        cand = np.flatnonzero(np.abs(np.nan_to_num(z, nan=9)) < 1)
        for i in rng.choice(cand, size=min(len(cand), max(5, len(cand) // 33)), replace=False) if len(cand) else []:
            if i + 1 >= len(c): continue
            sign = 1 if r[i] >= 0 else -1
            mk = {h: (np.expm1(mc[i + h] - mc[i]) * 100 if i + h < len(c) else np.nan) for h in HS}
            pl_rows.append(dict(symbol=s, time=t[i], dir='UP' if sign > 0 else 'DOWN', **fwd_stats(c, h_, l_, i, sign, mk)))
    E = pd.DataFrame(ev_rows); P = pd.DataFrame(pl_rows)
    E.to_csv(f'{OUT}/events_{tf}_list.csv.gz', index=False)
    for era, a, b in ERAS:
        e = E[(E.time >= a) & (E.time <= b)]; p = P[(P.time >= a) & (P.time <= b)]
        for dr in ('UP', 'DOWN'):
            pp = p[p.dir == dr]
            rows.append(dict(tf=tf, era=era, dir=dr, **summarize(pp, 'PLACEBO ordinary candle')))
            for kind in ('own', 'market'):
                for ent in ('E0', 'E1'):
                    x = e[(e.dir == dr) & (e.kind == kind) & (e.entry == ent)]
                    rows.append(dict(tf=tf, era=era, dir=dr, **summarize(x, f'{kind} shock, entry {ent}')))
                    if era == 'ALL' and ent == 'E0':
                        rows.append(dict(tf=tf, era=era, dir=dr, **summarize(x[x.vol2x], f'{kind} shock + volume 2x, entry E0')))
    # per-stock consistency (own shocks, E0, excess 5 candles): half1 vs half2
    e = E[(E.kind == 'own') & (E.entry == 'E0')].dropna(subset=['x5']).copy()
    if len(e):
        mid = e.time.quantile(0.5); e['half'] = np.where(e.time < mid, 1, 2)
        for dr in ('UP', 'DOWN'):
            g = e[e.dir == dr].groupby(['symbol', 'half']).x5.agg(['mean', 'count']).unstack()
            g = g[(g[('count', 1)] >= 3) & (g[('count', 2)] >= 3)]
            if len(g) < 20: continue
            m1, m2 = g[('mean', 1)], g[('mean', 2)]
            sh = []
            for _ in range(200): sh.append(np.corrcoef(m1.values, rng.permutation(m2.values))[0, 1])
            per_rows.append(dict(tf=tf, dir=dr, stocks=len(g), corr_half1_half2=round(np.corrcoef(m1, m2)[0, 1], 3),
                                 chance_corr_p95=round(np.quantile(sh, .95), 3),
                                 both_positive=int(((m1 > 0) & (m2 > 0)).sum()), expected_by_chance=round((m1 > 0).mean() * (m2 > 0).mean() * len(g), 1)))
    print('tf done', tf, len(E), flush=True)
T = pd.DataFrame(rows); T.to_csv(f'{OUT}/events_{G}_summary.csv', index=False)
PS = pd.DataFrame(per_rows); PS.to_csv(f'{OUT}/events_{G}_perstock.csv', index=False)

# -------- B + C (daily only) --------
if G == 'daily':
    C = pd.DataFrame({s: d.close for s, d in data['1D'].items()}).sort_index()
    eq = (1 + C.pct_change(fill_method=None).clip(-.2, .2).mean(axis=1).fillna(0)).cumprod()
    gl = lambda n: pd.read_csv(os.path.join(R, 'data', 'global', f'{n}.csv'), parse_dates=['date']).set_index('date').close.dropna()
    nf = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close.dropna()
    ix = eq.index
    def to_india(dates, same_day=True):
        """map event dates to the India session that first reacts (global: next India date after the US date)."""
        out = []
        for d in dates:
            k = ix.searchsorted(d if same_day else d + pd.Timedelta(days=1))
            if k < len(ix): out.append(ix[k])
        return sorted(set(out))
    spx, brent, uvix, inr = gl('US_SP500'), gl('CMD_BRENT'), gl('US_VIX'), gl('FX_USDINR')
    nfr = nf.pct_change() * 100; n3 = (nf / nf.shift(3) - 1) * 100; n10 = (nf / nf.shift(10) - 1) * 100
    ev = {
        'Nifty day +2%': to_india(nfr[nfr >= 2].index), 'Nifty day -2%': to_india(nfr[nfr <= -2].index),
        'Nifty 3 din +4%': to_india(n3[n3 >= 4].index), 'Nifty 3 din -4%': to_india(n3[n3 <= -4].index),
        'Nifty 10 din +5% (thrust)': to_india(n10[n10 >= 5].index),
        'S&P500 raat +2.5%': to_india(spx[spx.pct_change() * 100 >= 2.5].index, False),
        'S&P500 raat -2.5%': to_india(spx[spx.pct_change() * 100 <= -2.5].index, False),
        'Brent din -5%': to_india(brent[brent.pct_change() * 100 <= -5].index, False),
        'Brent din +5%': to_india(brent[brent.pct_change() * 100 >= 5].index, False),
        'Brent 5 din -10%': to_india(brent[(brent / brent.shift(5) - 1) * 100 <= -10].index, False),
        'US VIX +30% (dar)': to_india(uvix[uvix.pct_change() * 100 >= 30].index, False),
        'Rupee kamzor (USDINR +1%)': to_india(inr[inr.pct_change() * 100 >= 1].index),
        'Rupee mazboot (USDINR -0.8%)': to_india(inr[inr.pct_change() * 100 <= -0.8].index),
        'US chunav natija': to_india(pd.to_datetime(['2004-11-03', '2008-11-05', '2012-11-07', '2016-11-09', '2020-11-04', '2024-11-06'])),
        'US midterm natija': to_india(pd.to_datetime(['2006-11-08', '2010-11-03', '2014-11-05', '2018-11-07', '2022-11-09'])),
    }
    BADEV = {'Nifty day -2%', 'Nifty 3 din -4%', 'S&P500 raat -2.5%', 'Brent din +5%', 'US VIX +30% (dar)', 'Rupee kamzor (USDINR +1%)'}
    mrows = []
    for nm, ds in ev.items():
        # non-overlap 10 sessions
        keep, last = [], None
        for d in ds:
            if last is None or ix.get_loc(d) - ix.get_loc(last) >= GAP: keep.append(d); last = d
        for lab, ser in (('NIFTY', nf.reindex(ix).ffill()), ('ALL-SHARE basket', eq)):
            c = ser.values; vals = []
            for d in keep:
                i = ix.get_loc(d)
                sign = -1 if nm in BADEV else 1
                mk = {h: 0.0 for h in HS}
                vals.append(fwd_stats(c, c, c, i, sign, mk))
            df = pd.DataFrame(vals)
            if len(df):
                s_ = summarize(df, nm); s_['market'] = lab; s_['dates'] = len(keep)
                for era, a, b in [('2013+', '2013', '2100'), ('Nov23+', '2023-11-01', '2100')]:
                    sub = df[[a <= str(d.date()) <= b for d in keep]]
                    if len(sub) >= 3: s_[f'ret5_{era}'] = round(sub.r5.mean(), 2); s_[f'up5_{era}'] = round((sub.r5 > 0).mean() * 100, 0)
                mrows.append(s_)
    pd.DataFrame(mrows).to_csv(f'{OUT}/events_market.csv', index=False)
    # industries: which move most after Nifty +2% / S&P -2.5% / Brent -5% (excess 5 days), half-split
    info = pd.concat([pd.read_csv(f'{U}/u1000/list1000.csv'), pd.read_csv(f'{U}/u2000/list_extra.csv')]).drop_duplicates('symbol').set_index('symbol').industry
    x5 = (C.shift(-5) / C - 1).sub(eq.shift(-5) / eq - 1, axis=0) * 100
    irows = []
    for nm in ('Nifty day +2%', 'Nifty day -2%', 'S&P500 raat -2.5%', 'Brent din -5%', 'Brent din +5%', 'US VIX +30% (dar)', 'Nifty 10 din +5% (thrust)'):
        ds = [d for d in ev[nm] if d in x5.index]
        if len(ds) < 8: continue
        h1, h2 = ds[:len(ds) // 2], ds[len(ds) // 2:]
        a1 = x5.loc[h1].mean().groupby(info).mean(); a2 = x5.loc[h2].mean().groupby(info).mean()
        df = pd.DataFrame({'half1': a1, 'half2': a2}).dropna()
        df['event'] = nm; df['both_same_sign'] = np.sign(df.half1) == np.sign(df.half2)
        irows.append(df.reset_index().rename(columns={'index': 'industry'}))
    if irows: pd.concat(irows).round(2).to_csv(f'{OUT}/events_industry.csv', index=False)
    # C. bonus / split
    try:
        import yfinance as yf
        srows = []
        for k, s in enumerate(C.columns):
            try:
                sp = yf.Ticker(f'{s}.NS').splits
            except Exception:
                continue
            for d, ratio in sp.items():
                d = pd.Timestamp(d).tz_localize(None).normalize()
                if d < C.index[0] or d > C.index[-1] or ratio <= 1: continue
                i = C.index.searchsorted(d)
                if i < 45 or i + 61 >= len(C): continue
                cs = C[s].values
                if np.isnan(cs[i - 40]) or np.isnan(cs[i + 60]): continue
                m = eq.values
                row = dict(symbol=s, ex_date=d.date(), ratio=ratio)
                for nm, a, b in (('pre40', i - 41, i - 1), ('pre10', i - 11, i - 1), ('exday', i - 1, i), ('post5', i, i + 5), ('post20', i, i + 20), ('post60', i, i + 60)):
                    row[nm] = round(((cs[b] / cs[a]) - (m[b] / m[a])) * 100, 2)
                srows.append(row)
            if k % 200 == 0: print('splits', k, len(srows), flush=True)
        SP = pd.DataFrame(srows); SP.to_csv(f'{OUT}/events_bonus_split.csv', index=False)
    except Exception as ex:
        print('splits failed', ex)

# -------- markdown --------
L = [f'# Event/jhatka study — {G}', '']
show = ['kind', 'n', 'up1_%', 'up2_%', 'up3_%', 'exc1', 'exc3', 'exc5', 'exc20', 'run_med', 'run_p90', 'run_max', 'run>=2_%', 'best20_med', 'best20_p90', 'worst20_med', 'to_peak_med']
for tf in TFS:
    for dr in ('UP', 'DOWN'):
        x = T[(T.tf == tf) & (T.era == 'ALL') & (T.dir == dr)]
        L += [f'## {tf} {dr} झटका (ALL)', '```', x[[c for c in show if c in x]].to_string(index=False), '```']
    if len(ERAS) > 1:
        y = T[(T.tf == tf) & (T.kind.isin(['own shock, entry E1', 'market shock, entry E1', 'PLACEBO ordinary candle']))]
        L += [f'{tf} दौर-वार exc5 (late entry E1):', '```', y.pivot_table(index=['dir', 'kind'], columns='era', values='exc5').round(2).to_string(), '```', '']
if len(PS): L += ['Per-stock half1 vs half2 (own shock, 5 candle excess):', '```', PS.to_string(index=False), '```']
if G == 'daily' and os.path.exists(f'{OUT}/events_market.csv'):
    M = pd.read_csv(f'{OUT}/events_market.csv')
    L += ['## Bazaar-bhar ke events (entry = India ka pehla din close)', '```',
          M[[c for c in ['kind', 'market', 'dates', 'up1_%', 'up3_%', 'ret1', 'ret3', 'ret5', 'ret20', 'run_med', 'run_max', 'best20_med', 'worst20_med', 'ret5_2013+', 'ret5_Nov23+'] if c in M]].to_string(index=False), '```']
    if os.path.exists(f'{OUT}/events_bonus_split.csv'):
        SP = pd.read_csv(f'{OUT}/events_bonus_split.csv')
        L += [f'## Bonus/Split ({len(SP)} events, excess vs bazaar %)', '```', SP[['pre40', 'pre10', 'exday', 'post5', 'post20', 'post60']].describe().round(2).to_string(), '```',
              'Positive %: ' + ', '.join(f'{c} {(SP[c] > 0).mean() * 100:.0f}%' for c in ['pre40', 'pre10', 'exday', 'post5', 'post20', 'post60'])]
open(f'{OUT}/events_{G}.md', 'w').write('\n'.join(L)); print('\n'.join(L)[:6000])
