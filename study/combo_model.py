"""Sab ishaare milakar ek ANDAZA (user 15 Nov 2026: 'ek-ek study nahi, sab ko correlate karke conclusion; aur andaza kitna sahi baithta hai').
Do model, dono WALK-FORWARD (har saal sirf pichhle saalon ke data se seekha, us saal par jaancha = look-ahead nahi):
 A) SHARE model (cross-section): kaun sa share agle 20 din bazaar (sab A/B ka ausat) se aage rahega.
    Ishaare (din t ke close tak ke): 5/21/63/126 din chaal, 12-1 momentum, 20/50/200 DMA se doori, 1 saal ke high se kitna neeche,
    volume 5d/50d, 20 din volatility, RSI2, liquidity, pichhle 60 din -10% jhatka / kamzor +10% (f86), industry ki 3m chaal,
    industry ke andar share ki taakat (f73). Fundamentals ka ITIHAAS nahi hai (sirf aaj ka) -> backtest mein nahi; live filter alag.
 B) BAZAAR model: Nifty agle 20 din upar? Ishaare: Nifty 10/63 din, 200 DMA, breadth, S&P, sona, Brent, dollar-rupaya, dollar index,
    US 10 saal yield, US VIX (sab 20 din badlaav), mahina.
Har model: logistic (seedha) + gradient boosting (mila-jula). Jaanch: andaze ke 10 hisse (decile) -> asli nateeja; top-10% minus market,
kharcha 0.25% ghata kar; daur-war, 2008+COVID hata kar; PLACEBO = labels ulat-pulat karke wahi model (kismat kitna deti);
sabse achhe AKELE ishaare (12-1 momentum) se tulna — milaane se sach mein behtar hua ya nahi; calibration (60% kaha to 60% hua?).
Data: universe500 (u1000+u2000) via nc.load(), data/NIFTY.csv, data/global/*.csv, data/fund/summary.csv (industry label = aaj ka).
Output: study/results/combo_*.csv, study/results/combo_model.md
"""
import os, sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
R = nc.REPO; OUT = os.path.join(R, 'study', 'results'); STEP = 10; H = 20
P = nc.load(); a, c, h, l, v = P['a'], P['c'], P['h'], P['l'], P['v']
r1 = a.pct_change(fill_method=None); r1 = r1.where(r1.abs() < 0.5)
tv = (c * v).rolling(20, min_periods=15).median(); liq = tv >= 1e7
mkt_r = r1.where(liq).mean(axis=1)
ind = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol').industry.reindex(a.columns)
# ---------- share features ----------
def f(x): return x.astype('float32')
ret = lambda n: a / a.shift(n) - 1
d_ = a.diff(); g_ = d_.clip(lower=0).ewm(alpha=0.5).mean(); l_ = (-d_.clip(upper=0)).ewm(alpha=0.5).mean()
vr1 = v / v.rolling(50, min_periods=40).mean().shift(1)
shock_dn = ((r1 <= -0.10) & (vr1 >= 3)).astype(float).rolling(60, min_periods=1).max()
up200 = a > a.rolling(200, min_periods=180).mean()
shock_upw = ((r1 >= 0.10) & (vr1 >= 3) & up200.shift(1).eq(False)).astype(float).rolling(60, min_periods=1).max()
FE = {
    'r5': ret(5), 'r21': ret(21), 'r63': ret(63), 'r126': ret(126), 'mom12_1': a.shift(21) / a.shift(252) - 1,
    'd20': a / a.rolling(20).mean() - 1, 'd50': a / a.rolling(50).mean() - 1, 'd200': a / a.rolling(200, min_periods=180).mean() - 1,
    'dd252': a / a.rolling(252, min_periods=200).max() - 1, 'vol5_50': v.rolling(5).mean() / v.rolling(50, min_periods=40).mean(),
    'volat20': r1.rolling(20).std(), 'rsi2': 100 - 100 / (1 + g_ / l_), 'logtv': np.log10(tv.clip(lower=1)),
    'shock_dn60': shock_dn, 'shock_upweak60': shock_upw,
}
r63 = ret(63)
indm = r63.where(liq).T.groupby(ind).transform('median').T.reindex(columns=a.columns)         # industry ki 3m chaal (median)
FE['ind_r63'] = indm; FE['r63_vs_ind'] = r63 - indm
fwd = (a.shift(-H) / a - 1)
mk_f = np.expm1(np.log1p(mkt_r.fillna(0)).cumsum().shift(-H) - np.log1p(mkt_r.fillna(0)).cumsum())
exc = fwd.sub(mk_f, axis=0)
dates = a.index[260:-H][::STEP]
rows = []
for d in dates:
    m = liq.loc[d] & exc.loc[d].notna()
    if m.sum() < 50: continue
    df = pd.DataFrame({k: x.loc[d][m] for k, x in FE.items()})
    df['exc'] = exc.loc[d][m]; df['date'] = d; df['sym'] = df.index
    rows.append(df)
D = pd.concat(rows, ignore_index=True).replace([np.inf, -np.inf], np.nan)
X_cols = list(FE)
# cross-sectional rank (har din 0-1) -> bazaar ke level ka asar hata kar sirf 'kaun aage' seekhe
for k in X_cols: D[k] = D.groupby('date')[k].rank(pct=True)
D[X_cols] = D[X_cols].fillna(0.5)
D['y'] = (D.exc > 0).astype(int); D['year'] = D.date.dt.year
print('share rows', len(D), D.date.min().date(), D.date.max().date(), flush=True)

def walk(D, X_cols, years, make, shuffle=False, seed=0):
    out = []; rng = np.random.default_rng(seed)
    for y in years:
        tr = D[D.year < y]; te = D[D.year == y]
        if len(tr) < 5000 or not len(te): continue
        yy = tr.y.values.copy()
        if shuffle: yy = rng.permutation(yy)
        mdl = make(); mdl.fit(tr[X_cols].values, yy)
        p = mdl.predict_proba(te[X_cols].values)[:, 1]
        out.append(te[['date', 'sym', 'exc', 'y', 'year']].assign(p=p))
    return pd.concat(out, ignore_index=True), mdl

LR = lambda: LogisticRegression(C=0.5, max_iter=500)
GB = lambda: HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=500, l2_regularization=1.0)
YEARS = list(range(2008, 2027))
res = {}
res['LR'], lr_last = walk(D, X_cols, YEARS, LR)
res['GB'], gb_last = walk(D, X_cols, YEARS, GB)
res['PLACEBO'], _ = walk(D, X_cols, YEARS, GB, shuffle=True)
one = D[D.year >= 2008][['date', 'sym', 'exc', 'y', 'year']].assign(p=D.loc[D.year >= 2008, 'mom12_1'].values)
res['AKELA mom12_1'] = one

def deciles(Rx):
    Rx = Rx.copy(); Rx['dec'] = Rx.groupby('date').p.transform(lambda s: pd.qcut(s.rank(method='first'), 10, labels=False))
    return Rx

def era_rows(Rx, name):
    Rx = deciles(Rx); out = []
    idx = pd.DatetimeIndex(Rx.date)
    masks = {'ALL': np.ones(len(Rx), bool)}
    for n_, s, e in nc.ERAS: masks[n_] = (idx >= s) & (idx <= e)
    nc_ = np.ones(len(Rx), bool)
    for s, e in nc.CRISIS: nc_ &= ~((idx >= s) & (idx <= e))
    masks['ex-crisis'] = nc_
    for era, mm in masks.items():
        x = Rx[mm]
        if not len(x): continue
        top = x[x.dec == 9].groupby('date').exc.mean() * 100; bot = x[x.dec == 0].groupby('date').exc.mean() * 100
        t = top.mean() / (top.std() / np.sqrt(len(top))) if len(top) > 2 else np.nan
        out.append(dict(model=name, era=era, dates=len(top), top10_exc=round(top.mean(), 2), top10_net=round(top.mean() - nc.COST, 2),
                        top10_t=round(t, 2), top10_win_dates=round((top > 0).mean() * 100, 1), bot10_exc=round(bot.mean(), 2),
                        spread=round(top.mean() - bot.mean(), 2), hit_top=round(x[x.dec == 9].y.mean() * 100, 1)))
    return out

T = pd.DataFrame([r for k, Rx in res.items() for r in era_rows(Rx, k)])
T.to_csv(os.path.join(OUT, 'combo_share_eras.csv'), index=False)
# calibration (GB): predicted prob buckets vs actual share beating market
G = res['GB'].copy(); G['b'] = pd.cut(G.p, [0, .4, .45, .5, .55, .6, .65, 1])
CAL = G.groupby('b', observed=True).agg(n=('y', 'size'), kaha=('p', 'mean'), hua=('y', 'mean'), exc20=('exc', 'mean'))
CAL[['kaha', 'hua']] *= 100; CAL['exc20'] *= 100
CAL.round(2).to_csv(os.path.join(OUT, 'combo_share_calibration.csv'))
# feature importance (LR coefficients on rank features, last model) — kaun sa ishaara kitna
imp = pd.Series(lr_last.coef_[0], index=X_cols).sort_values()

# ---------- B) BAZAAR model ----------
gl = lambda n: pd.read_csv(os.path.join(R, 'data', 'global', f'{n}.csv'), parse_dates=['date']).set_index('date').adj.ffill()
N = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date').close
idx = N.index
G_ = {k: gl(k).reindex(idx, method='ffill') for k in ['US_SP500', 'CMD_GOLD', 'CMD_BRENT', 'FX_USDINR', 'FX_DOLLAR_INDEX', 'US_VIX', 'US_10Y']}
br = up200.where(liq).mean(axis=1).reindex(idx, method='ffill')
M = pd.DataFrame({
    'nifty_r10': N.pct_change(10), 'nifty_r63': N.pct_change(63), 'nifty_d200': N / N.rolling(200).mean() - 1, 'breadth200': br,
    'sp500_r20': G_['US_SP500'].pct_change(20), 'gold_r20': G_['CMD_GOLD'].pct_change(20), 'brent_r20': G_['CMD_BRENT'].pct_change(20),
    'usdinr_r20': G_['FX_USDINR'].pct_change(20), 'dxy_r20': G_['FX_DOLLAR_INDEX'].pct_change(20), 'usvix': G_['US_VIX'],
    'us10y_chg20': G_['US_10Y'].diff(20), 'month': idx.month,
}, index=idx)
M['fwd'] = N.shift(-H) / N - 1; M['y'] = (M.fwd > 0).astype(int); M['year'] = idx.year
M = M.dropna().iloc[::5]
MX = [k for k in M.columns if k not in ('fwd', 'y', 'year')]
mres = []
for y in range(2011, 2027):
    tr, te = M[M.year < y], M[M.year == y]
    if not len(te): continue
    for name, mk_ in (('LR', lambda: LogisticRegression(C=0.3, max_iter=1000)), ('GB', lambda: HistGradientBoostingClassifier(max_iter=100, learning_rate=0.05, max_leaf_nodes=7, min_samples_leaf=40))):
        mdl = mk_()
        Xtr = (tr[MX] - tr[MX].mean()) / tr[MX].std(); Xte = (te[MX] - tr[MX].mean()) / tr[MX].std()
        mdl.fit(Xtr.values, tr.y.values); p = mdl.predict_proba(Xte.values)[:, 1]
        mres.append(te[['fwd', 'y', 'year']].assign(p=p, model=name))
MR = pd.concat(mres)
base_up = M[M.year >= 2011].y.mean()
mt = []
for name, x in MR.groupby('model'):
    hi, lo = x[x.p >= 0.6], x[x.p < 0.45]
    mt.append(dict(model=name, n=len(x), base_up=round(base_up * 100, 1), hi_n=len(hi), hi_up=round(hi.y.mean() * 100, 1), hi_ret=round(hi.fwd.mean() * 100, 2),
                   lo_n=len(lo), lo_up=round(lo.y.mean() * 100, 1), lo_ret=round(lo.fwd.mean() * 100, 2), all_ret=round(x.fwd.mean() * 100, 2)))
MT = pd.DataFrame(mt); MT.to_csv(os.path.join(OUT, 'combo_market.csv'), index=False)
# single-factor macro table (user ke udaharan: sona gira -> bazaar?, crude gira -> bazaar?)
sf = []
for k in ['gold_r20', 'brent_r20', 'sp500_r20', 'usdinr_r20', 'dxy_r20', 'us10y_chg20', 'usvix', 'breadth200', 'nifty_r10']:
    q = M[k].rank(pct=True)
    for era, mm in (('2008-26', M.year >= 2008), ('2013-20', (M.year >= 2013) & (M.year <= 2020)), ('2021-26', M.year >= 2021)):
        x = M[mm]; qq = q[mm]
        sf.append(dict(ishaara=k, era=era, neeche20_nifty20d=round(x[qq <= .2].fwd.mean() * 100, 2), upar20_nifty20d=round(x[qq >= .8].fwd.mean() * 100, 2),
                       sab=round(x.fwd.mean() * 100, 2)))
SF = pd.DataFrame(sf); SF.to_csv(os.path.join(OUT, 'combo_macro_single.csv'), index=False)
pd.set_option('display.width', 250)
md = ['# Combo andaza model (f87)', '', '## A) Share model — top 10% andaza, agle 20 din bazaar se excess', '```',
      T[T.era.isin(['ALL', '2003-12', '2013-20', '2021-26', 'Nov23-now', 'ex-crisis'])].to_string(index=False), '```',
      '## Calibration (GB): kaha vs hua', '```', CAL.round(1).to_string(), '```',
      '## Ishaaron ka wazan (LR, aakhri saal) — minus = share peeche rehta', '```', imp.round(3).to_string(), '```',
      '## B) Bazaar model (Nifty agle 20 din)', '```', MT.to_string(index=False), '```',
      '## Akele macro ishaare: neeche 20% vs upar 20% hone par Nifty agle 20 din (%)', '```', SF.to_string(index=False), '```']
open(os.path.join(OUT, 'combo_model.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md))
import joblib; joblib.dump(dict(gb=gb_last, lr=lr_last, X=X_cols), os.path.join(OUT, 'combo_share_model.pkl'))
