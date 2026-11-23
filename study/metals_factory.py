"""METALS IDEA FACTORY (Tosif 22 Nov 2026: 'jo 500-600 tarike shares par chalaye, sab gold/silver par bhi chala do — Hijri, Gregorian date,
moving average 200 aur 1,2,3,5..10 wale, sab robot ko de do; Indian price, Kuwait price aur USD ounce teeno mein dekho').
Free GitHub robot (.github/workflows/metals.yml), weekly + on demand. Time-series version of study/idea_factory.py.

SERIES (data/global, built inside the run):
  GOLD_USD (GC=F $/oz), SILVER_USD (SI=F), GOLD_INR = USD x USDINR (Rs/oz; MCX/ETF proxy, no import duty), SILVER_INR,
  GOLD_KWD = USD x USDKWD (Kuwait price), SILVER_KWD, GOLDBEES / SILVERBEES (real Indian ETF prices, if fetched).
CONDITIONS (~170, all known at that day's close, no look-ahead):
  move (1/5/20 day), MA (price above/below MA 3,5,8,10,13,20,21,34,50,55,89,100,144,200; fast/slow MA order; fresh crosses;
  distance from MA), level (20/55 day breakout/breakdown, 52w high/low, drawdown from peak 10-60%), RSI2/RSI14, candles,
  volatility (rank vs own past only), Gregorian (weekday, month, day-of-month blocks, month start/end, quarter end),
  HIJRI (month 1-12, day blocks; study/hijri_tbla.csv), Indian season (ritu), macro (dollar index, US 10y, Nifty 200DMA, VIX,
  gold/silver ratio).
TEST (strict, same spirit as idea_factory):
  each idea = 1-3 conditions; LONG and SHORT side; forward 1/5/20 trading days; excess vs that series' own average move in the same
  period (so plain drift is not 'skill'); cost 0.15% round trip (ETF); entries non-overlapping (next entry only after the hold ends).
  DISCOVERY 2000-2014: t >= 3 and n >= 40; HOLDOUT 2015-2026: same sign, t >= 2, mean >= threshold; every era (2000-08, 2009-14,
  2015-20, 2021-26) same sign; still OK without 2008 and COVID crash; and the SAME sign on the other currency versions
  (USD / INR / KWD must agree). For each PASS also Tosif's bar: ATR stop 1.5x, target 3x (2:1), max 20 days -> target-hit %
  and real avg win / avg loss. Ledger: study/results/metals_ledger.csv (never repeat); report: data/metals_ideas.md.
A PASS is a study candidate only (paper first), never straight to real money.
"""
import os, json, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G = os.path.join(R, 'data', 'global')
LED = os.path.join(R, 'study', 'results', 'metals_ledger.csv'); OUT = os.path.join(R, 'data', 'metals_ideas.md')
NEW_PER_RUN = int(os.environ.get('METALS_N', '400'))
COST = 0.0015


def load(name):
    p = os.path.join(G, f'{name}.csv')
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index()
    d = d[d.close > 0]
    return d[['open', 'high', 'low', 'close']].astype(float)


gold, silver = load('CMD_GOLD'), load('CMD_SILVER')
fx = {'INR': load('FX_USDINR'), 'KWD': load('FX_USDKWD')}
S = {'GOLD_USD': gold, 'SILVER_USD': silver}
for cur, f in fx.items():
    if f is None: continue
    for nm, base in (('GOLD', gold), ('SILVER', silver)):
        k = f.close.reindex(base.index).ffill()
        S[f'{nm}_{cur}'] = base.mul(k, axis=0).dropna()
for nm, f in (('GOLDBEES', 'IN_GOLDBEES'), ('SILVERBEES', 'IN_SILVERBEES')):
    d = load(f)
    if d is not None and len(d) > 500: S[nm] = d
FAMILY = {k: ('GOLD' if k.startswith('GOLD') else 'SILVER') for k in S}
print('series', {k: (str(v.index[0].date()), len(v)) for k, v in S.items()})

# ---- macro (same calendar) ----
def cl(name):
    d = load(name); return None if d is None else d.close
dxy, y10, nif, vix = cl('FX_DOLLAR_INDEX'), cl('US_10Y'), cl('IN_SENSEX'), cl('US_VIX')
ratio = (gold.close / silver.close.reindex(gold.index)).dropna()
hij = pd.read_csv(os.path.join(R, 'study', 'hijri_tbla.csv'), parse_dates=['date']).set_index('date').hijri
hm = hij.str.split('/').str[1].astype(int); hd = hij.str.split('/').str[2].astype(int)
HM_NAMES = ['Muharram', 'Safar', 'Rabi-ul-Awwal', 'Rabi-us-Sani', 'Jumada-ul-Ula', 'Jumada-us-Sani', 'Rajab', 'Shaban', 'Ramzan', 'Shawwal', 'Zilqad', 'Zilhij']


def conditions(d):
    c, h, l, o = d.close, d.high, d.low, d.open
    idx = c.index; r = c.pct_change()
    ret = lambda n: c / c.shift(n) - 1
    C = {}
    for n, th in ((1, 0.02), (1, 0.03), (5, 0.05), (5, 0.08), (20, 0.10), (20, 0.15)):
        C[f'{n} din +{int(th*100)}%+'] = ('move', ret(n) >= th); C[f'{n} din -{int(th*100)}%+'] = ('move', ret(n) <= -th)
    MAS = [3, 5, 8, 10, 13, 20, 21, 34, 50, 55, 89, 100, 144, 200]
    ma = {n: c.rolling(n, min_periods=n).mean() for n in MAS}
    for n in MAS:
        C[f'MA{n} ke upar'] = ('ma', c > ma[n]); C[f'MA{n} ke neeche'] = ('ma', c < ma[n])
        C[f'aaj MA{n} upar paar'] = ('macross', (c > ma[n]) & (c.shift(1) <= ma[n].shift(1)))
        C[f'aaj MA{n} neeche toda'] = ('macross', (c < ma[n]) & (c.shift(1) >= ma[n].shift(1)))
    for n, pct in ((20, 5), (50, 8), (200, 10), (200, 20)):
        C[f'MA{n} se {pct}%+ neeche'] = ('madist', c <= ma[n] * (1 - pct / 100)); C[f'MA{n} se {pct}%+ upar'] = ('madist', c >= ma[n] * (1 + pct / 100))
    for a, b in ((5, 20), (10, 50), (20, 50), (50, 200), (20, 100), (13, 34), (8, 21), (3, 10)):
        C[f'MA{a} > MA{b}'] = ('maorder', ma[a] > ma[b]); C[f'MA{a} < MA{b}'] = ('maorder', ma[a] < ma[b])
        C[f'MA{a} ne MA{b} upar kata'] = ('macross2', (ma[a] > ma[b]) & (ma[a].shift(1) <= ma[b].shift(1)))
        C[f'MA{a} ne MA{b} neeche kata'] = ('macross2', (ma[a] < ma[b]) & (ma[a].shift(1) >= ma[b].shift(1)))
    C['MA200 chadh rahi'] = ('maslope', ma[200] > ma[200].shift(21)); C['MA200 gir rahi'] = ('maslope', ma[200] < ma[200].shift(21))
    pk = c.cummax(); dd = c / pk - 1
    for x in (10, 20, 30, 40, 60):
        C[f'peak se {x}%+ neeche'] = ('dd', dd <= -x / 100)
    hi250, lo250 = h.rolling(250, min_periods=200).max(), l.rolling(250, min_periods=200).min()
    C['52w high ke 3% paas'] = ('level', c >= hi250 * 0.97); C['52w low ke 3% paas'] = ('level', c <= lo250 * 1.03)
    for n in (20, 55):
        C[f'{n} din breakout'] = ('level', c > h.shift(1).rolling(n).max()); C[f'{n} din breakdown'] = ('level', c < l.shift(1).rolling(n).min())
    dlt = c.diff()
    for n in (2, 14):
        g_ = dlt.clip(lower=0).ewm(alpha=1 / n).mean(); l_ = (-dlt.clip(upper=0)).ewm(alpha=1 / n).mean(); rsi = 100 - 100 / (1 + g_ / l_)
        lo_, hi_ = (10, 90) if n == 2 else (30, 70)
        C[f'RSI{n} <= {lo_}'] = ('osc', rsi <= lo_); C[f'RSI{n} >= {hi_}'] = ('osc', rsi >= hi_)
    rng = (h - l); pos = (c - l) / rng.replace(0, np.nan)
    C['3 din lagatar gira'] = ('candle', (r < 0).rolling(3).sum() == 3); C['3 din lagatar chadha'] = ('candle', (r > 0).rolling(3).sum() == 3)
    C['5 din me 4+ gira'] = ('candle', (r < 0).rolling(5).sum() >= 4)
    C['close din ke top 20% par'] = ('candle', pos >= 0.8); C['close din ke neeche 20% par'] = ('candle', pos <= 0.2)
    C['NR7'] = ('candle', rng <= rng.rolling(7).min()); C['inside day'] = ('candle', (h <= h.shift(1)) & (l >= l.shift(1)))
    C['gap up 1%+'] = ('candle', o >= c.shift(1) * 1.01); C['gap down 1%+'] = ('candle', o <= c.shift(1) * 0.99)
    vol = r.rolling(20).std(); vrk = vol.expanding(250).rank(pct=True)
    C['shaant (vol neeche 20%)'] = ('vola', vrk <= 0.2); C['tufaan (vol upar 20%)'] = ('vola', vrk >= 0.8)
    # Gregorian
    S_ = lambda a: pd.Series(a, index=idx)
    for i, n in enumerate(['Somvaar', 'Mangal', 'Budh', 'Guru', 'Shukra']):
        C[n] = ('weekday', S_(idx.dayofweek == i))
    for m in range(1, 13):
        C[f'mahina {m}'] = ('month', S_(idx.month == m))
    for a, b in ((1, 3), (4, 10), (11, 20), (21, 24), (25, 31)):
        C[f'tareekh {a}-{b}'] = ('dom', S_((idx.day >= a) & (idx.day <= b)))
    ym = S_(idx.year * 100 + idx.month); dn = ym.groupby(ym).cumcount(); last = ym != ym.shift(-1)
    C['mahine ka pehla kaarobaari din'] = ('mpos', dn == 0); C['mahine ka aakhri kaarobaari din'] = ('mpos', last)
    C['quarter ka aakhri hafta'] = ('mpos', S_(idx.month.isin([3, 6, 9, 12]) & (idx.day >= 24)))
    # Hijri
    hmi, hdi = hm.reindex(idx).ffill(), hd.reindex(idx).ffill()
    for m in range(1, 13):
        C[f'Hijri {HM_NAMES[m-1]}'] = ('hijri_m', hmi == m)
    for a, b in ((1, 7), (8, 15), (16, 23), (24, 30)):
        C[f'Hijri tareekh {a}-{b}'] = ('hijri_d', (hdi >= a) & (hdi <= b))
    md = idx.month * 100 + idx.day
    rit = np.where((md >= 315) & (md < 515), 0, np.where((md >= 515) & (md < 715), 1, np.where((md >= 715) & (md < 915), 2,
          np.where((md >= 915) & (md < 1115), 3, np.where((md >= 1115) | (md < 115), 4, 5)))))
    for k, n in enumerate(['Vasant', 'Grishma', 'Varsha', 'Sharad', 'Hemant', 'Shishir']):
        C[f'ritu {n}'] = ('ritu', S_(rit == k))
    # macro
    def add(series, nm, fam, f):
        if series is None: return
        s = series.reindex(idx).ffill(); C[nm] = (fam, f(s))
    add(dxy, 'dollar 20 din +2%+', 'dollar', lambda s: s / s.shift(20) - 1 >= 0.02)
    add(dxy, 'dollar 20 din -2%+', 'dollar', lambda s: s / s.shift(20) - 1 <= -0.02)
    add(dxy, 'dollar MA200 ke upar', 'dollar', lambda s: s > s.rolling(200).mean())
    add(dxy, 'dollar 8 din lagatar chadha', 'dollar', lambda s: (s.diff() > 0).rolling(8).sum() == 8)
    add(y10, 'US 10y 20 din +0.25 se zyada', 'yield', lambda s: s - s.shift(20) >= 0.25)
    add(y10, 'US 10y 20 din -0.25 se zyada', 'yield', lambda s: s - s.shift(20) <= -0.25)
    add(nif, 'Sensex MA200 ke upar', 'india', lambda s: s > s.rolling(200).mean())
    add(nif, 'Sensex 5 din -4%+', 'india', lambda s: s / s.shift(5) - 1 <= -0.04)
    add(vix, 'US VIX 25+', 'fear', lambda s: s >= 25)
    add(ratio, 'gold/silver ratio 80+', 'ratio', lambda s: s >= 80); add(ratio, 'gold/silver ratio 60 se kam', 'ratio', lambda s: s < 60)
    return {k: (f, m.fillna(False).astype(bool).values) for k, (f, m) in C.items()}


# ---- precompute per series ----
DATA = {}
for nm, d in S.items():
    c = d.close; idx = c.index
    cond = conditions(d)
    fw = {h: (c.shift(-h) / c - 1).values for h in (1, 5, 20)}
    tr = pd.concat([d.high - d.low, (d.high - c.shift()).abs(), (d.low - c.shift()).abs()], axis=1).max(axis=1)
    DATA[nm] = dict(idx=idx, cond=cond, fw=fw, c=c.values, h=d.high.values, l=d.low.values, atr=tr.rolling(14).mean().values)
names = sorted(set.intersection(*[set(v['cond']) for v in DATA.values()]))
fams = {n: DATA['GOLD_USD']['cond'][n][0] for n in names}
ERAS = [('2000-08', '2000-01-01', '2008-12-31'), ('2009-14', '2009-01-01', '2014-12-31'), ('2015-20', '2015-01-01', '2020-12-31'), ('2021-26', '2021-01-01', '2026-12-31')]
CRISIS = [('2008-09-01', '2009-03-31'), ('2020-02-15', '2020-04-30')]


def picks(mask, h):
    """non-overlapping entries: after an entry, skip the next h days"""
    out = []; nxt = -1
    for i in np.flatnonzero(mask):
        if i >= nxt: out.append(i); nxt = i + h
    return np.array(out, int)


def tstat(x):
    x = x[np.isfinite(x)]
    return (x.mean() * 100, x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 5 and x.std() > 0 else np.nan, len(x))


def eval_series(nm, conds, h, side):
    D = DATA[nm]; m = np.ones(len(D['idx']), bool)
    for n in conds: m &= D['cond'][n][1]
    f = D['fw'][h]; ok = np.isfinite(f)
    idx = D['idx']; yrs = idx
    base = pd.Series(f, index=idx)
    # excess vs the series' own average h-day move in the same calendar year (removes drift/regime)
    yr_mean = base.groupby(idx.year).transform('mean').values
    ex = side * (f - yr_mean) - COST
    p = picks(m & ok, h)
    if len(p) == 0: return None
    di = idx[p]; x = ex[p]
    disc, hold = x[di < '2015-01-01'], x[di >= '2015-01-01']
    eras = {e: tstat(x[(di >= a) & (di <= b)])[0] for e, a, b in ERAS}
    cr = np.zeros(len(p), bool)
    for a, b in CRISIS: cr |= (di >= a) & (di <= b)
    return dict(disc=tstat(disc), hold=tstat(hold), eras=eras, nocr=tstat(x[~cr]), n=len(p), last=str(di[-1].date()), p=p)


def bar(nm, p, side):
    """Tosif bar: ATR stop 1.5x, target 3x, max 20 days, cost included"""
    D = DATA[nm]; c, h, l, a = D['c'], D['h'], D['l'], D['atr']; res = []
    for i in p:
        if i + 21 >= len(c) or not np.isfinite(a[i]): continue
        e = c[i]; st = e - side * 1.5 * a[i]; tg = e + side * 3 * a[i]; out = None
        for k in range(i + 1, i + 21):
            if (side > 0 and l[k] <= st) or (side < 0 and h[k] >= st): out = ('stop', side * (st / e - 1)); break
            if (side > 0 and h[k] >= tg) or (side < 0 and l[k] <= tg): out = ('tgt', side * (tg / e - 1)); break
        if out is None: out = ('time', side * (c[i + 20] / e - 1))
        res.append((out[0], out[1] - COST))
    if not res: return {}
    r = np.array([x[1] for x in res]); w, lo = r[r > 0], r[r <= 0]
    return dict(tgt_hit=round(100 * np.mean([x[0] == 'tgt' for x in res]), 1), win=round(100 * (r > 0).mean(), 1),
                avg_win=round(w.mean() * 100, 2) if len(w) else 0, avg_loss=round(lo.mean() * 100, 2) if len(lo) else 0,
                ratio=round(abs(w.mean() / lo.mean()), 2) if len(w) and len(lo) else np.nan, net=round(r.mean() * 100, 2), n=len(r))


THR = {1: 0.10, 5: 0.30, 20: 1.0}


def judge(conds):
    best = None
    for fam in ('GOLD', 'SILVER'):
        prim = f'{fam}_USD'; others = [k for k in S if FAMILY[k] == fam and k != prim and not k.endswith('BEES')]
        for h in (1, 5, 20):
            for side in (1, -1):
                r = eval_series(prim, conds, h, side)
                if r is None: continue
                (dm, dt, dn), (hm_, ht, hn) = r['disc'], r['hold']
                row = dict(fam=fam, h=h, side='LONG' if side > 0 else 'SHORT', disc=round(dm, 2), disc_t=round(dt, 1) if np.isfinite(dt) else None, disc_n=dn,
                           hold=round(hm_, 2), hold_t=round(ht, 1) if np.isfinite(ht) else None, hold_n=hn, last=r['last'],
                           eras=json.dumps({k: round(v, 2) if np.isfinite(v) else None for k, v in r['eras'].items()}))
                ok = dn >= 40 and hn >= 25 and np.isfinite(dt) and dt >= 3 and np.isfinite(ht) and ht >= 2 and hm_ >= THR[h] and \
                    all((v is not None and np.isfinite(v) and v > 0) for v in r['eras'].values()) and r['nocr'][0] > 0
                agree = []
                for o in others:
                    ro = eval_series(o, conds, h, side)
                    agree.append(ro is not None and ro['hold'][0] > 0 and ro['disc'][0] > 0)
                row['other_ccy_agree'] = all(agree) if agree else None
                if ok and all(agree):
                    row['verdict'] = f'PASS {fam} {h}d {row["side"]}'; row.update({f'bar_{k}': v for k, v in bar(prim, r['p'][r['p'] >= 0], side).items()})
                elif np.isfinite(dt) and dt >= 3 and hm_ <= 0:
                    row['verdict'] = 'FAIL (purane data me tha, naye me gayab)'
                else:
                    row['verdict'] = 'FAIL'
                score = (row['verdict'].startswith('PASS'), (ht if np.isfinite(ht) else -9))
                if best is None or score > best[0]: best = (score, row)
    return best[1] if best else dict(verdict='no data')


led = pd.read_csv(LED) if os.path.exists(LED) else pd.DataFrame(columns=['key'])
done = set(led.key.astype(str)); run_no = int(led.run.max()) + 1 if 'run' in led and len(led) else 1
todo = [[n] for n in names if n not in done]                     # every single condition first
rng = np.random.default_rng(7000 + run_no); tries = 0
seen = {' & '.join(sorted(t)) for t in todo}; n_single = len(todo)
while len(todo) - n_single < NEW_PER_RUN and tries < 50000:
    tries += 1; k = int(rng.choice([2, 3], p=[0.65, 0.35])); pk = list(rng.choice(names, k, replace=False))
    if len({fams[p] for p in pk}) < k: continue
    key = ' & '.join(sorted(pk))
    if key in done or key in seen: continue
    seen.add(key); todo.append(pk)
rows = []
for j, conds in enumerate(todo):
    row = judge(conds); row.update(run=run_no, key=' & '.join(sorted(conds)), k=len(conds)); rows.append(row)
    if j % 50 == 0: print(j, row['key'], row['verdict'], flush=True)
new = pd.DataFrame(rows); led = pd.concat([led, new], ignore_index=True); led.to_csv(LED, index=False)

isp = lambda d: d.verdict.astype(str).str.startswith('PASS')
L = [f'# Metals Idea Factory — run {run_no} ({pd.Timestamp.now(tz="Asia/Kuwait"):%d %b %Y} Kuwait)', '',
     'Gold & silver: USD/oz, INR (Indian), KWD (Kuwait), ETF. Har idea long aur short, 1/5/20 din, us saal ke apne average se fark, 0.15% kharcha.',
     'PASS = 2000-14 me t>=3, 2015-26 me bhi (t>=2), har daur me same disha, 2008/COVID hata kar bhi, aur INR/KWD version bhi sahmat.',
     f'Series: {", ".join(f"{k} ({DATA[k]['idx'][0].year}-)" for k in S)}',
     f'Is run me {len(new)} idea: PASS {isp(new).sum()}, data-mining jaal {new.verdict.astype(str).str.contains("gayab").sum()}. Ab tak kul {len(led)}, PASS {isp(led).sum()}.', '']
for title, df in (('## Is run ke PASS', new[isp(new)]), ('## Ab tak ke sab PASS', led[isp(led)])):
    L.append(title)
    if not len(df): L.append('- koi nahi'); L.append(''); continue
    for x in df.sort_values('hold_t', ascending=False).head(60).itertuples():
        b = f" | Tosif bar (1.5 ATR stop / 3 ATR target): target {getattr(x, 'bar_tgt_hit', None)}%, jeet/haar {getattr(x, 'bar_ratio', None)}, net {getattr(x, 'bar_net', None)}%/trade (n {getattr(x, 'bar_n', None)})"
        L.append(f'- **{x.key}** → {x.verdict}; 2000-14 {x.disc:+.2f}% (t {x.disc_t}, n {x.disc_n}), 2015-26 {x.hold:+.2f}% (t {x.hold_t}, n {x.hold_n}); aakhri signal {x.last}; daur {x.eras}{b}')
    L.append('')
L.append('## Akeli shartein (single conditions) — 2015-26 me sabse mazboot 15 (PASS ho ya na ho)')
s1 = led[(led.k == 1)].copy(); s1['hold_t'] = pd.to_numeric(s1.hold_t, errors='coerce')
for x in s1.sort_values('hold_t', ascending=False).head(15).itertuples():
    L.append(f'- {x.key}: {x.fam} {x.h}d {x.side} 2015-26 {x.hold:+.2f}% (t {x.hold_t}), 2000-14 {x.disc:+.2f}% (t {x.disc_t}) → {x.verdict}')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
