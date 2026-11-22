"""Follow-up tests (Groq review 22 Nov 2026 ke sujhav + Claude): NIFTY weekly umeedwar ki kadi jaanch.
 1 slippage sensitivity (per leg per side +X pt), break-even slippage
 2 bootstrap 95% CI (trade-level resample)
 3 walk-forward: har saal, pichhle 2 saal ka best combo (poore family se) -> agle saal trade (koi hindsight nahi)
 4 expiry settlement = asli Nifty spot close (parity ki jagah)
 5 d2 entry
 6 VIX daur (entry din ka VIX)
 7 sabse bure trade ki width/credit jaanch
"""
import os, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results')
T = pd.read_csv(os.path.join(OUT, 'cg_trades_NIFTY.csv.gz'), parse_dates=['d0', 'exp', 'xd'])
T = T[T.cyc == 'weekly'].copy()
N = pd.read_csv(os.path.join(R, 'data', 'NIFTY.csv'), parse_dates=['date']).set_index('date'); N = N[~N.index.duplicated()]
V = pd.read_csv(os.path.join(R, 'data', 'INDIAVIX.csv'), parse_dates=['date']).set_index('date').close
LOT = 65; MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s); MD.append(s)
key = ['entry', 'z', 'w', 'exit']
T['early'] = T.how.isin(['target', 'SL', 'SLi'])
T['risk'] = T.width - T.credit
T['yr'] = T.d0.dt.year
CAND = [('d3', 1.25, 1.0, 'hold'), ('d3', 1.25, 1.0, 'S100i'), ('d3', 1.0, 1.0, 'S100i'), ('d3', 1.5, 1.0, 'hold'), ('d2', 1.25, 1.0, 'hold'), ('d2', 1.0, 1.0, 'hold'), ('d1', 0.75, 1.0, 'hold')]
def sel(c): return T[(T.entry == c[0]) & (T.z == c[1]) & (T.w == c[2]) & (T.exit == c[3])]
md('# NIFTY weekly condor — follow-up kadi jaanch (22 Nov 2026)')

md('\n## 1. Slippage badhane par (har leg har taraf +X point extra), Rs/lot 2019-26')
rows = []
for c in CAND:
    t = sel(c); r = {'setting': ' '.join(map(str, c)), 'n': len(t), 'credit_med': t.credit.median()}
    for X in (0, 0.25, 0.5, 1.0):
        extra = X * (4 + 4 * t.early)
        r[f'+{X}'] = round(((t.pts - extra) * LOT).sum())
    # break-even X
    lo, hi = 0, 5
    for _ in range(30):
        m = (lo + hi) / 2
        if (t.pts - m * (4 + 4 * t.early)).sum() > 0: lo = m
        else: hi = m
    r['breakeven_X'] = round(lo, 2); rows.append(r)
md('```\n' + pd.DataFrame(rows).to_string(index=False) + '\n```')

md('\n## 2. Bootstrap 95% range (trade resample 10,000x), avg Rs/lot per trade')
rng = np.random.default_rng(7); rows = []
for c in CAND:
    x = (sel(c).pts * LOT).values
    bs = rng.choice(x, size=(10000, len(x))).mean(1)
    rows.append(dict(setting=' '.join(map(str, c)), mean=round(x.mean()), lo=round(np.percentile(bs, 2.5)), hi=round(np.percentile(bs, 97.5)), p_le0=round((bs <= 0).mean(), 3)))
md('```\n' + pd.DataFrame(rows).to_string(index=False) + '\n```')

md('\n## 3. Walk-forward: har saal ke shuru mein pichhle 2 saal ka best combo (n>=40) chuno, wo saal trade karo')
fam = T.groupby(key + ['yr']).agg(s=('pts', 'sum'), n=('pts', 'size')).reset_index()
wf = []
for Y in range(2021, 2027):
    past = fam[fam.yr.isin([Y - 2, Y - 1])].groupby(key).agg(s=('s', 'sum'), n=('n', 'sum')).reset_index()
    past = past[past.n >= 40]
    if not len(past): continue
    b = past.sort_values('s').iloc[-1]
    nxt = fam[(fam.yr == Y) & (fam.entry == b.entry) & (fam.z == b.z) & (fam.w == b.w) & (fam.exit == b.exit)]
    wf.append(dict(year=Y, chosen=f'{b.entry} z{b.z} w{b.w} {b.exit}', past_rs=round(b.s * LOT), next_rs=round(nxt.s.sum() * LOT) if len(nxt) else np.nan))
W = pd.DataFrame(wf); md('```\n' + W.to_string(index=False) + '\n```'); md(f'Walk-forward kul (2021-26): Rs {W.next_rs.sum():,.0f}/lot')

md('\n## 4. Expiry = asli Nifty spot close (hold variants)')
rows = []
for c in CAND:
    t = sel(c); t = t[t.how == 'expiry']
    St = t.exp.map(N.close)
    iv = np.maximum(St - t.sc, 0) - np.maximum(St - t.bc, 0) + np.maximum(t.sp - St, 0) - np.maximum(t.bp - St, 0)
    Sp = None
    rows.append(dict(setting=' '.join(map(str, c)), expiry_trades=len(t), rs_parity=round((t.pts * LOT).sum()),
                     rs_spotclose=round(((t.credit - iv - t.cost) * LOT).sum())))
md('```\n' + pd.DataFrame(rows).to_string(index=False) + '\n```')

md('\n## 5/6. VIX daur (entry din ka VIX close), Rs/lot aur trades')
rows = []
for c in CAND:
    t = sel(c).copy(); t['vix'] = t.d0.map(V)
    t['band'] = pd.cut(t.vix, [0, 12, 14, 16, 20, 99], labels=['<12', '12-14', '14-16', '16-20', '20+'])
    g = t.groupby('band', observed=False).agg(n=('pts', 'size'), rs=('pts', lambda x: round(x.sum() * LOT)))
    rows.append(pd.Series({f'{b} n/Rs': f'{int(g.loc[b, "n"])}/{int(g.loc[b, "rs"]) if g.loc[b, "n"] else 0}' for b in g.index}, name=' '.join(map(str, c))))
md('```\n' + pd.DataFrame(rows).to_string() + '\n```')

md('\n## 7. Sabse bure 6 trade (d3 z1.25 w1.0 hold)')
t = sel(('d3', 1.25, 1.0, 'hold')).nsmallest(6, 'pts')[['d0', 'exp', 'F', 'sc', 'sp', 'bc', 'bp', 'credit', 'width', 'pts']]
t['rs'] = (t.pts * LOT).round(0); md('```\n' + t.to_string(index=False) + '\n```')

md('\n## 8. Saal-war Rs/lot (umeedwar)')
Y = pd.DataFrame({' '.join(map(str, c)): (sel(c).groupby('yr').pts.sum() * LOT).round(0) for c in CAND})
md('```\n' + Y.to_string() + '\n```')
open(os.path.join(OUT, 'cg_followup.md'), 'w').write('\n'.join(MD) + '\n')
