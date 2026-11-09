"""Season-to-season LINKS (user 9 Nov 2026: 'simple nahi, ghuma-phira kar: is saal thand mein gira to agle saal? thand upar to
garmi upar/neeche? 3 saal lagatar?...'). Honest handling of 'bahut saare jod': for each family of rules we take the STRONGEST
rule and ask how strong the strongest rule is when the years are shuffled (1000 shuffles) -> adjusted p. p < 0.05 = asli.
 A. Index season chain: 6 ritu returns in order; does ritu X's direction tell ritu X+k (k = 1..12 seasons ahead)? 72 rules.
    Sensex 1997-2026, S&P 1928-2026, + Nikkei, DAX, FTSE, Hang Seng as outside check.
 B. Streak: same ritu up/down 1, 2, 3 years running -> same ritu next year.
 C. Weather link: how hot / how wet a ritu was (Delhi+Mumbai+4 cities, vs normal) -> Sensex in the next 1..6 ritu. 72 rules.
 D. Shares (cross-section, 1,500 shares 2003-26): shares that did best in THIS SAME calendar month in the past 1-5 years ->
    this month again (Heston-Sadka effect), and same for ritu; top 10% minus bottom 10%, by era. Also 'other months' control.
"""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); rng = np.random.default_rng(11)
MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)
RN = ['Vasant', 'Grishma', 'Varsha', 'Sharad', 'Hemant', 'Shishir']
def ritu_id(d):  # season index 0..5 and season-year (Vasant starts the year on 15 Mar)
    m = d.month * 100 + d.day
    k = 0 if 315 <= m < 515 else 1 if 515 <= m < 715 else 2 if 715 <= m < 915 else 3 if 915 <= m < 1115 else 4 if (m >= 1115 or m < 115) else 5
    y = d.year if m >= 315 else d.year - 1
    return y, k
def season_table(close):
    r = np.log(close).diff().dropna()
    key = [ritu_id(d) for d in r.index]
    t = r.groupby([[k[0] for k in key], [k[1] for k in key]]).sum().unstack()
    n = r.groupby([[k[0] for k in key], [k[1] for k in key]]).size().unstack()
    return (t.where(n >= 25) * 100)
def ix(n):
    d = pd.read_csv(os.path.join(R, 'data', 'global', f'{n}.csv'), parse_dates=['date']).set_index('date').close.dropna()
    return d[~d.index.duplicated()].sort_index()
def tval(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float); m = np.isfinite(a) & np.isfinite(b); a, b = a[m], b[m]
    if len(a) < 12 or a.std() == 0 or b.std() == 0: return np.nan, len(a)
    c = np.corrcoef(a, b)[0, 1]; return c * np.sqrt((len(a) - 2) / max(1 - c * c, 1e-9)), len(a)
def chain_rules(T):
    """T: years x 6 table. rule (s, k): season s in year y -> the season k steps later."""
    flat = T.values.flatten(); out = {}
    for s in range(6):
        for k in range(1, 13):
            a = flat[s::6]; j = s + k; b = flat[j::6][:len(a)]
            b = np.concatenate([b, [np.nan] * (len(a) - len(b))])
            out[(s, k)] = tval(a, b)[0]
    return out
def shuffled(T):
    X = T.values.copy()
    for c in range(6):
        idx = rng.permutation(len(X)); X[:, c] = X[idx, c]
    return pd.DataFrame(X, index=T.index, columns=T.columns)

md('# Mausam-se-mausam ke jod (season links)')
md('Har parivaar mein sabse mazboot jod liya, phir saal ulat-pulat karke 1000 baar dekha ki kismat se sabse mazboot jod kitna mazboot hota hai (adjusted p). p < 0.05 ho tabhi asli.')
md('\n## A. Ek ritu ki disha -> aage ki ritu (1 se 12 ritu aage; 72 jod har bazaar mein)')
TAB = {}
for nm, f in (('Sensex', 'IN_SENSEX'), ('S&P 500', 'US_SP500'), ('Nikkei', 'JP_NIKKEI'), ('DAX', 'EU_DAX'), ('FTSE', 'EU_FTSE'), ('Hang Seng', 'HK_HANGSENG')):
    try: T = season_table(ix(f)).dropna(how='all')
    except Exception as e: print(nm, e); continue
    TAB[nm] = T; rl = chain_rules(T); best = max(rl, key=lambda k: abs(rl[k]) if np.isfinite(rl[k]) else 0)
    mx = [np.nanmax(np.abs(list(chain_rules(shuffled(T)).values()))) for _ in range(1000)]
    p = float(np.mean(np.array(mx) >= abs(rl[best])))
    s, k = best; to = RN[(s + k) % 6]; yrs = (s + k) // 6
    top3 = sorted(rl, key=lambda q: -abs(rl[q]) if np.isfinite(rl[q]) else 0)[:3]
    md(f'- **{nm}** ({len(T)} saal): sabse mazboot jod: {RN[s]} -> {yrs} saal baad ki {to}' + (' (usi saal)' if yrs == 0 else '') + f' , t {rl[best]:+.1f} ({"usi disha" if rl[best] > 0 else "ulti disha"}); kismat se itna mazboot jod milne ka chance = {p * 100:.0f}% -> {"ASLI ho sakta" if p < 0.05 else "kismat"}')
    md('  - top 3: ' + '; '.join(f'{RN[a]}->{RN[(a + b) % 6]}(+{b} ritu) t {rl[(a, b)]:+.1f}' for a, b in top3))
if 'Sensex' in TAB:
    rs = chain_rules(TAB['Sensex']); md('- Sensex ke top 5 jod doosre bazaaron mein (same disha mein t >= 1.5 ho to "mila"):')
    for a, b in sorted(rs, key=lambda q: -abs(rs[q]) if np.isfinite(rs[q]) else 0)[:5]:
        oth = {n: chain_rules(T)[(a, b)] for n, T in TAB.items() if n != 'Sensex'}
        md(f'  - {RN[a]} -> {RN[(a + b) % 6]} (+{b}): Sensex t {rs[(a, b)]:+.1f} | ' + ', '.join(f'{n} {v:+.1f}' for n, v in oth.items()) + f' | mila {sum(1 for v in oth.values() if np.isfinite(v) and v * rs[(a, b)] > 0 and abs(v) >= 1.5)}/{len(oth)}')

md('\n## B. Lagatar saal: wahi ritu 1/2/3 saal lagatar upar (ya neeche) -> agle saal wahi ritu')
for nm in ('Sensex', 'S&P 500'):
    T = TAB[nm]
    for n in (1, 2, 3):
        for dirn, lab in ((1, 'upar'), (-1, 'neeche')):
            hit = tot = 0; base_h = base_t = 0
            for c in range(6):
                x = T.iloc[:, c].values
                for i in range(n, len(x)):
                    if not np.isfinite(x[i]) or not np.all(np.isfinite(x[i - n:i])): continue
                    base_t += 1; base_h += x[i] > 0
                    if np.all(np.sign(x[i - n:i]) == dirn): tot += 1; hit += x[i] > 0
            md(f'- {nm}: {n} saal lagatar {lab} ({tot} baar) -> agle saal upar {hit / max(tot, 1) * 100:.0f}% (aam taur par {base_h / max(base_t, 1) * 100:.0f}%)')

md('\n## C. Ritu ka mausam (kitni garmi / kitni baarish, normal se) -> Sensex agli 1..6 ritu (72 jod)')
try:
    Wd = os.path.join(R, 'data', 'weather'); cities = ['Mumbai', 'Delhi', 'Kolkata', 'Chennai', 'Nagpur', 'Lucknow']
    Wt = pd.concat([pd.read_csv(os.path.join(Wd, f'{c}.csv.gz'), parse_dates=['time']).set_index('time') for c in cities], keys=cities)
    temp = Wt.temperature_2m_max.unstack(0).mean(axis=1); rain = Wt.precipitation_sum.unstack(0).mean(axis=1)
    def wtab(s, how):
        key = [ritu_id(d) for d in s.index]; g = s.groupby([[k[0] for k in key], [k[1] for k in key]])
        t = (g.mean() if how == 'mean' else g.sum()).unstack(); return t - t.mean()
    WT, WR = wtab(temp, 'mean'), wtab(rain, 'sum'); S = TAB['Sensex']; yrs = S.index.intersection(WT.index)
    def wrules(S_):
        out = {}; sf = S_.loc[yrs].values.flatten()
        for vn, Wx in (('garmi', WT), ('baarish', WR)):
            wf = Wx.loc[yrs].values.flatten()
            for s in range(6):
                for k in range(1, 7):
                    a = wf[s::6]; b = sf[s + k::6][:len(a)]; b = np.concatenate([b, [np.nan] * (len(a) - len(b))])
                    out[(vn, s, k)] = tval(a, b)[0]
        return out
    rl = wrules(S); best = max(rl, key=lambda q: abs(rl[q]) if np.isfinite(rl[q]) else 0)
    mx = []
    for _ in range(1000):
        Sx = S.copy(); Sx.loc[yrs] = S.loc[yrs].values[rng.permutation(len(yrs))]  # shuffle market years against weather years
        mx.append(np.nanmax(np.abs(list(wrules(Sx).values()))))
    p = float(np.mean(np.array(mx) >= abs(rl[best]))); vn, s, k = best
    md(f'- Sabse mazboot: {RN[s]} mein zyada {vn} -> {k} ritu baad ({RN[(s + k) % 6]}) Sensex {"upar" if rl[best] > 0 else "neeche"}, t {rl[best]:+.1f}; kismat se milne ka chance {p * 100:.0f}% -> {"ASLI ho sakta" if p < 0.05 else "kismat"}')
    md('  - top 5: ' + '; '.join(f'{RN[b]} {a} -> {RN[(b + c) % 6]} t {rl[(a, b, c)]:+.1f}' for a, b, c in sorted(rl, key=lambda q: -abs(rl[q]) if np.isfinite(rl[q]) else 0)[:5]))
except Exception as e:
    md('- mausam data nahi mila:', e)

md('\n## D. Shares: jo share pichhle saalon mein ISI mahine / ISI ritu mein sabse achha raha, wo is baar bhi? (1,500 shares)')
P = nc.load(); A = P['a']; M = A.resample('ME').last(); mr = M.pct_change(fill_method=None).clip(-0.6, 1.5)
mr = mr.sub(mr.mean(axis=1), axis=0)
def spread(sig, ret, lab):
    rk = sig.rank(axis=1, pct=True); top = ret.where(rk >= 0.9).mean(axis=1); bot = ret.where(rk <= 0.1).mean(axis=1); sp = (top - bot).dropna() * 100
    parts = []
    for a, b in (('2005', '2012'), ('2013', '2020'), ('2021', '2026'), ('2023-11', '2026')):
        x = sp[a:b]; parts.append(f'{a[:4]}-{b[2:]}: {x.mean():+.2f}%/m (t {x.mean() / x.std() * np.sqrt(len(x)):.1f})')
    md(f'- {lab}: top 10% minus neeche 10% = {sp.mean():+.2f}%/mahina (t {sp.mean() / sp.std() * np.sqrt(len(sp)):.1f}) | ' + ' | '.join(parts) + f' | sirf top 10% bazaar se {top.dropna().mean() * 100:+.2f}%/m')
    return sp
for yrs_ in (1, 3, 5):
    same = sum(mr.shift(12 * k) for k in range(1, yrs_ + 1)) / yrs_
    spread(same, mr, f'isi mahine ka pichhle {yrs_} saal ka ausat')
other = (mr.rolling(60).sum().shift(1) - sum(mr.shift(12 * k) for k in range(1, 6))) / 55
spread(other, mr, 'CONTROL: baaki mahinon ka 5 saal ka ausat (isi mahine ko chhod kar)')
# ritu version: 2-month seasons
r2 = np.log1p(A.pct_change(fill_method=None).clip(-0.4, 0.4)); key = [ritu_id(d) for d in r2.index]
SR = r2.groupby([[k[0] for k in key], [k[1] for k in key]]).sum(min_count=25)
SR = SR.sub(SR.mean(axis=1), axis=0)
SR.index = pd.MultiIndex.from_tuples(SR.index); pos = SR.index
sig = pd.DataFrame(index=SR.index, columns=SR.columns, dtype=float)
for (y, k) in SR.index:
    prev = [(y - j, k) for j in (1, 2, 3) if (y - j, k) in SR.index]
    if len(prev) == 3: sig.loc[(y, k)] = SR.loc[prev].mean().values
rk = sig.rank(axis=1, pct=True); sp = (SR.where(rk >= 0.9).mean(axis=1) - SR.where(rk <= 0.1).mean(axis=1)).dropna() * 100
md(f'- isi RITU ka pichhle 3 saal ka ausat -> is baar wahi ritu: top-bottom {sp.mean():+.2f}% prati ritu (t {sp.mean() / sp.std() * np.sqrt(len(sp)):.1f}, {len(sp)} ritu); 2013+ {sp[[i for i in sp.index if i[0] >= 2013]].mean():+.2f}, 2021+ {sp[[i for i in sp.index if i[0] >= 2021]].mean():+.2f}')
byk = sp.groupby(level=1).mean(); md('  - ritu-war: ' + ', '.join(f'{RN[k]} {v:+.1f}%' for k, v in byk.items()))
open(os.path.join(R, 'study', 'results', 'season_links.md'), 'w').write('\n'.join(MD) + '\n')
