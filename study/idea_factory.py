"""IDEA FACTORY (user 9 Nov 2026: 'robot khud naye naye idea sochta rahe, har hafte nayi strategy khode; kismat wala 50-50 nahi').
Every run (weekly robot, ideas.yml) it:
  1. builds ~60 atomic conditions (price, trend, momentum, volume, candle, volatility, calendar, market mood) on 1,500 Indian
     shares 2002-2026 (adj close, liquidity D removed) — everything measured at the day's close, no look-ahead;
  2. tests famous PUBLIC expert strategies once (Minervini trend template, Weinstein stage 2, Darvas box, Turtle 55-day,
     George-Hwang 52w-high, Clenow momentum, O'Neil-type pocket pivot, Connors 3-day-down in uptrend);
  3. invents NEW combinations: 150 untested random 2-3 condition combos per run (seeded by run number, never repeated —
     study/results/idea_ledger.csv keeps every combo ever tested);
  4. judges each one the strict way: excess return vs equal-weight market after 0.25% cost, 5 and 20 days,
     DISCOVERY 2003-2016 must give t >= 3, then HOLDOUT 2017-2026 must be positive (t >= 2), every recent era
     (2013-20, 2021-26, Nov23-now) positive, still positive without 2008 and COVID; non-overlapping dates (every 5th / 20th day).
  5. writes data/ideas.md: new PASS ideas this run, all-time pass list, and how many failed (so we see the luck rate).
A PASS is a candidate only: it goes to paper trading after the user's OK, never straight to real money.
"""
import os, sys, json, itertools, hashlib, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LED = os.path.join(R, 'study', 'results', 'idea_ledger.csv'); OUT = os.path.join(R, 'data', 'ideas.md')
NEW_PER_RUN = int(os.environ.get('IDEAS_N', '150'))

P = nc.load()
A = P['a'].astype('float32'); O, H, L, C, V = (P[k].astype('float32') for k in ('o', 'h', 'l', 'c', 'v'))
A = A.loc[:, A.notna().sum() > 250]; cols = A.columns
O, H, L, C, V = (x.reindex(columns=cols) for x in (O, H, L, C, V))
r = A.pct_change(fill_method=None).clip(-0.4, 0.4)  # bad-data spikes clipped (they blew up the market average)
mkt = r.mean(axis=1)
idx = A.index
def rk(x): return x.rank(axis=1, pct=True)
sma = lambda n: A.rolling(n, min_periods=int(n * 0.8)).mean()
s20, s50, s100, s200 = sma(20), sma(50), sma(100), sma(200)
hi250 = H.rolling(250, min_periods=200).max(); lo250 = L.rolling(250, min_periods=200).min()
d_ = A.diff(); g2 = d_.clip(lower=0).ewm(alpha=0.5).mean(); l2 = (-d_.clip(upper=0)).ewm(alpha=0.5).mean(); rsi2 = 100 - 100 / (1 + g2 / l2)
g14 = d_.clip(lower=0).ewm(alpha=1 / 14).mean(); l14 = (-d_.clip(upper=0)).ewm(alpha=1 / 14).mean(); rsi14 = 100 - 100 / (1 + g14 / l14)
v50 = V.rolling(50, min_periods=30).mean().shift(1)
rng = (H - L); pos = (C - L) / rng.replace(0, np.nan)
vol20 = r.rolling(20).std()
mk_lvl = (1 + mkt.fillna(0)).cumprod(); mk200 = mk_lvl > mk_lvl.rolling(200).mean()
breadth = (A > s200).sum(axis=1) / A.notna().sum(axis=1)
rowb = lambda s: pd.DataFrame(np.repeat(s.values[:, None], len(cols), axis=1), index=idx, columns=cols)
ret = lambda n: A / A.shift(n) - 1
COND = {  # name: (family, bool frame)
    'kal -5% ya zyada': ('move', r <= -0.05), 'kal +5% ya zyada': ('move', r >= 0.05),
    '5 din -10%': ('move', ret(5) <= -0.10), '5 din +10%': ('move', ret(5) >= 0.10),
    '20 din -15%': ('move', ret(20) <= -0.15), '20 din +20%': ('move', ret(20) >= 0.20),
    '3m RS top 10%': ('mom', rk(ret(63)) >= 0.9), '3m RS neeche 10%': ('mom', rk(ret(63)) <= 0.1),
    '1 saal top 20%': ('mom', rk(ret(250)) >= 0.8), '1 saal neeche 20%': ('mom', rk(ret(250)) <= 0.2),
    '12-1 momentum top 10%': ('mom', rk(A.shift(21) / A.shift(250) - 1) >= 0.9),
    '200 DMA ke upar': ('trend', A > s200), '200 DMA ke neeche': ('trend', A < s200), '50 DMA ke upar': ('trend', A > s50),
    '20 DMA se 8%+ neeche': ('trend', A <= s20 * 0.92), '20 DMA se 10%+ upar': ('trend', A >= s20 * 1.10),
    '50 DMA > 200 DMA': ('trend', s50 > s200), '200 DMA chadh rahi': ('trend', s200 > s200.shift(21)),
    '52w high ke 5% paas': ('level', C >= hi250 * 0.95), 'aaj naya 52w high': ('level', H >= hi250),
    '52w low ke 5% paas': ('level', C <= lo250 * 1.05), '55 din breakout': ('level', C > H.shift(1).rolling(55).max()),
    '20 din breakout': ('level', C > H.shift(1).rolling(20).max()),
    'RSI2 <= 10': ('osc', rsi2 <= 10), 'RSI2 >= 90': ('osc', rsi2 >= 90), 'RSI14 <= 30': ('osc', rsi14 <= 30), 'RSI14 >= 70': ('osc', rsi14 >= 70),
    'volume 3x': ('volu', V >= 3 * v50), 'volume 5 din 2x': ('volu', V.rolling(5).mean() >= 2 * v50), 'volume aadha': ('volu', V <= 0.5 * v50),
    'gap up 3%+': ('candle', O >= C.shift(1) * 1.03), 'gap down 3%+': ('candle', O <= C.shift(1) * 0.97),
    'close din ke top 10% par': ('candle', pos >= 0.9), 'close din ke neeche 10% par': ('candle', pos <= 0.1),
    'NR7': ('candle', rng <= rng.rolling(7).min()), 'inside day': ('candle', (H <= H.shift(1)) & (L >= L.shift(1))),
    '3 din lagatar gira': ('candle', (r < 0).rolling(3).sum() == 3), '3 din lagatar chadha': ('candle', (r > 0).rolling(3).sum() == 3),
    'kam volatility (20% sabse shaant)': ('vola', rk(vol20) <= 0.2), 'zyada volatility (20%)': ('vola', rk(vol20) >= 0.8),
    'bhaav < 100': ('size', C < 100), 'bhaav > 1000': ('size', C > 1000),
    'Somvaar': ('cal', rowb(pd.Series(idx.dayofweek == 0, index=idx))), 'Shukravaar': ('cal', rowb(pd.Series(idx.dayofweek == 4, index=idx))),
    'mahine ke 1-3 din': ('cal', rowb(pd.Series(idx.day <= 3, index=idx))), 'mahine ke 25-31': ('cal', rowb(pd.Series(idx.day >= 25, index=idx))),
    'Nov-Jan': ('cal', rowb(pd.Series(idx.month.isin([11, 12, 1]), index=idx))),
    'bazaar 200 DMA upar': ('mkt', rowb(mk200)), 'bazaar 200 DMA neeche': ('mkt', rowb(~mk200)),
    'bazaar 5 din -4%': ('mkt', rowb((mk_lvl / mk_lvl.shift(5) - 1) <= -0.04)), 'bazaar 10 din +5%': ('mkt', rowb((mk_lvl / mk_lvl.shift(10) - 1) >= 0.05)),
    'breadth < 30% (ghabrahat)': ('mkt', rowb(breadth < 0.3)), 'breadth > 70%': ('mkt', rowb(breadth > 0.7)),
}
COND = {k: (f, m.fillna(False).values) for k, (f, m) in COND.items()}
valid = (A.notna() & ((H - L) > 0.002 * C)).values  # circuit-locked days (H=L) cannot be bought -> excluded (fake +5%/5d found in run 1)
NAMED = {
    'EXPERT: Minervini trend template': ['200 DMA ke upar', '50 DMA > 200 DMA', '200 DMA chadh rahi', '52w high ke 5% paas', '1 saal top 20%'],
    'EXPERT: Weinstein stage-2 breakout': ['200 DMA chadh rahi', '55 din breakout', 'volume 3x'],
    'EXPERT: Darvas box (52w high + breakout)': ['aaj naya 52w high', '20 din breakout', 'volume 5 din 2x'],
    'EXPERT: Turtle 55-day breakout': ['55 din breakout'],
    'EXPERT: George-Hwang 52w high': ['52w high ke 5% paas'],
    'EXPERT: Clenow momentum (bazaar upar)': ['12-1 momentum top 10%', '200 DMA ke upar', 'bazaar 200 DMA upar'],
    'EXPERT: Pocket pivot type (volume + trend)': ['50 DMA ke upar', 'volume 3x', 'close din ke top 10% par'],
    'EXPERT: Connors 3 din gira, uptrend': ['200 DMA ke upar', '3 din lagatar gira'],
    'EXPERT: Bollinger/NR7 squeeze breakout': ['NR7', '20 din breakout'],
}

fwd = {}
for h in (5, 20):
    f_ = (A.shift(-h) / A - 1).clip(-0.6, 1.5).values
    fwd[h] = f_ - np.nanmean(f_, axis=1)[:, None]  # excess vs equal-weight average of the same shares
COSTP = nc.COST / 100
yrs = idx.year.values
crisis = np.zeros(len(idx), bool)
for a, b in nc.CRISIS: crisis |= (idx >= a) & (idx <= b)


def evaluate(names):
    m = valid.copy()
    for n in names: m &= COND[n][1]
    res = {}
    for h, step in ((5, 5), (20, 20)):
        F = fwd[h]; cnt = m.sum(axis=1)
        with np.errstate(invalid='ignore'):
            s = np.where(m, F, 0).sum(axis=1) / np.where(cnt > 0, cnt, np.nan) - COSTP
        s[~np.isfinite(F).any(axis=1)] = np.nan
        sel = np.zeros(len(idx), bool); sel[::step] = True
        ser = pd.Series(np.where(sel, s, np.nan), index=idx).dropna()
        def st(x):
            x = x.dropna()
            return (x.mean() * 100, x.mean() / x.std() * np.sqrt(len(x)) if len(x) > 5 and x.std() > 0 else np.nan, len(x))
        disc, hold = ser[ser.index < '2017-01-01'], ser[ser.index >= '2017-01-01']
        eras = {nm: st(ser[(ser.index >= a) & (ser.index <= b)])[0] for nm, a, b in nc.ERAS}
        nocr = st(ser[~pd.Series(crisis, index=idx).reindex(ser.index).values])
        res[h] = dict(disc=st(disc), hold=st(hold), eras=eras, nocrisis=nocr, per_day=float(np.nanmean(cnt[cnt > 0])) if (cnt > 0).any() else 0)
    return res


def verdict(res):
    for h, thr in ((5, 0.3), (20, 1.0)):
        x = res[h]; dm, dt_, dn = x['disc']; hm, ht, hn = x['hold']
        if dn >= 60 and hn >= 40 and dt_ >= 3 and hm >= thr and ht >= 2 and all(v > 0 for v in x['eras'].values() if np.isfinite(v)) and x['nocrisis'][0] > 0:
            return f'PASS {h}d'
    for h in (5, 20):
        x = res[h]
        if x['disc'][1] >= 3 and x['hold'][0] <= 0: return 'FAIL (purane data mein tha, naye mein gayab = data-mining)'
    return 'FAIL'


led = pd.read_csv(LED) if os.path.exists(LED) else pd.DataFrame(columns=['key'])
done = set(led.key.astype(str))
run_no = int(led.run.max()) + 1 if 'run' in led and len(led) else 1
todo = []
for nm, conds in NAMED.items():
    k = ' & '.join(sorted(conds))
    if k not in done: todo.append((nm, conds))
rng_ = np.random.default_rng(1000 + run_no)
names = list(COND); fams = {n: COND[n][0] for n in names}
tries = 0
while len([t for t in todo if not t[0].startswith('EXPERT')]) < NEW_PER_RUN and tries < 20000:
    tries += 1; k_ = int(rng_.choice([2, 3], p=[0.6, 0.4])); pick = list(rng_.choice(names, k_, replace=False))
    if len({fams[p] for p in pick}) < k_: continue
    key = ' & '.join(sorted(pick))
    if key in done or key in {' & '.join(sorted(c)) for _, c in todo}: continue
    todo.append((f'NEW #{run_no}-{len(todo) + 1}', pick))
rows = []
for nm, conds in todo:
    res = evaluate(conds); v = verdict(res)
    b = res[5] if 'PASS 20d' not in v else res[20]
    rows.append(dict(run=run_no, name=nm, key=' & '.join(sorted(conds)), verdict=v, per_day=round(res[5]['per_day'], 1),
                     disc5=round(res[5]['disc'][0], 2), disc5_t=round(res[5]['disc'][1], 1), hold5=round(res[5]['hold'][0], 2), hold5_t=round(res[5]['hold'][1], 1),
                     disc20=round(res[20]['disc'][0], 2), disc20_t=round(res[20]['disc'][1], 1), hold20=round(res[20]['hold'][0], 2), hold20_t=round(res[20]['hold'][1], 1),
                     eras=json.dumps({k: round(v_, 2) for k, v_ in b['eras'].items()})))
    print(nm, rows[-1]['key'], v, rows[-1]['hold5'], rows[-1]['hold20'], flush=True)
new = pd.DataFrame(rows)
led = pd.concat([led, new], ignore_index=True); led.to_csv(LED, index=False)

L = [f'# Idea Factory — run {run_no} ({pd.Timestamp.now(tz="Asia/Kolkata"):%d %b %Y})', '',
     'Har idea: 1,500 shares 2003-26, bazaar se fark, 0.25% kharcha ghata kar. Pehle 2003-16 mein t>=3, phir 2017-26 mein bhi + (t>=2), har naye daur mein +, 2008/COVID hata kar bhi +.',
     f'Is run mein {len(new)} idea jaanche: PASS {new.verdict.str.startswith("PASS").sum()}, data-mining jaal {new.verdict.str.contains("data-mining").sum()}, baaki FAIL.',
     f'Ab tak kul {len(led)} idea jaanche, PASS {led.verdict.astype(str).str.startswith("PASS").sum()}.', '']
for title, df in (('## Is run ke PASS', new[new.verdict.str.startswith('PASS')]), ('## Ab tak ke sab PASS', led[led.verdict.astype(str).str.startswith('PASS')])):
    L.append(title)
    if not len(df): L.append('- koi nahi'); continue
    for x in df.sort_values('hold20', ascending=False).itertuples():
        L.append(f'- **{x.name}**: {x.key} → {x.verdict}; 2017-26: 5 din {x.hold5:+.2f}% (t {x.hold5_t}), 20 din {x.hold20:+.2f}% (t {x.hold20_t}); roz ~{x.per_day} shares; daur {x.eras}')
    L.append('')
ex = new[new.name.str.startswith('EXPERT')]
if len(ex):
    L.append('## Mashhoor experts ki public strategies (pehli baar jaanchi)')
    for x in ex.itertuples(): L.append(f'- {x.name} ({x.key}): {x.verdict}; 2017-26 5d {x.hold5:+.2f}% / 20d {x.hold20:+.2f}%')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
