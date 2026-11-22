"""Report for study/condor_grid.py — pre-registered pass rules (22 Nov 2026, pehle tay, nateeje dekhne se pehle):
 PASS = n>=60, teeno daur (symbol ke samay ke 3 barabar hisse) mein avg ret > 0, profit factor >= 1.15,
        aur paas wali setting (z ek step upar/neeche, baaki same) bhi overall avg ret > 0.
 OOS  = har (symbol, cycle) mein pehle aadhe samay ka best combo chuno (n>=30) -> doosre aadhe mein uska nateeja.
"""
import os, glob, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(R, 'study', 'results')
T = pd.concat([pd.read_csv(f, parse_dates=['d0', 'exp']) for f in sorted(glob.glob(os.path.join(OUT, 'cg_trades_*.csv.gz')))])
LOT = dict(NIFTY=65, BANKNIFTY=30, FINNIFTY=60, MIDCPNIFTY=120)
ZS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
K = ['sym', 'cyc', 'entry', 'z', 'w', 'exit']
MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s); MD.append(s)

# eras per (sym,cyc)
gg = T.groupby(['sym', 'cyc']).d0
lo, hi = gg.transform('min'), gg.transform('max'); span = hi - lo
T['era'] = np.where(T.d0 < lo + span / 3, 1, np.where(T.d0 < lo + 2 * span / 3, 2, 3)); T['half'] = np.where(T.d0 < lo + span / 2, 1, 2)

def agg(g):
    w = g.pts[g.pts > 0].sum(); l = -g.pts[g.pts <= 0].sum()
    e = g.groupby('era').ret.mean()
    return pd.Series(dict(n=len(g), win=round((g.pts > 0).mean() * 100, 1), ret=round(g.ret.mean() * 100, 2), pf=round(w / l, 2) if l > 0 else np.nan,
                          worst=round(g.ret.min() * 100, 0), e1=round(e.get(1, np.nan) * 100, 2), e2=round(e.get(2, np.nan) * 100, 2), e3=round(e.get(3, np.nan) * 100, 2),
                          pts=round(g.pts.sum(), 1), first=g.d0.min().date(), last=g.d0.max().date()))
S = pd.DataFrame([dict(zip(K, k), **agg(g)) for k, g in T.groupby(K)])
S['rs_lot'] = S.apply(lambda r: round(r.pts * LOT[r.sym]) if r.sym in LOT else np.nan, axis=1)
# neighbour check
idx = S.set_index(K).ret
def nb(r):
    i = ZS.index(r.z); out = []
    for j in (i - 1, i + 1):
        if 0 <= j < len(ZS):
            k = (r.sym, r.cyc, r.entry, ZS[j], r.w, r.exit)
            if k in idx.index: out.append(idx[k] > 0)
    return all(out) and len(out) > 0
S['nb_ok'] = S.apply(nb, axis=1)
S['PASS'] = (S.n >= 60) & (S.e1 > 0) & (S.e2 > 0) & (S.e3 > 0) & (S.pf >= 1.15) & S.nb_ok
S.to_csv(os.path.join(OUT, 'cg_summary.csv'), index=False)

md('# Iron condor BADA GRID — asli NSE bhaav, 4 index + 14 shares (2010-2026)')
md(f'Trades simulated: {len(T):,}; combos: {len(S):,}. ret = har trade nateeja / max risk (%), kharcha ghata kar. Rs/lot = aaj ka lot (sirf index).')
md('Pass niyam pehle tay: n>=60, teeno daur plus, PF>=1.15, paas wali z setting bhi plus.')
md('\n## 1. Kitne combos plus / pass')
c = S.groupby(['sym', 'cyc']).agg(combos=('ret', 'size'), plus=('ret', lambda x: int((x > 0).sum())), passed=('PASS', 'sum'), best_ret=('ret', 'max'), median_ret=('ret', 'median')).reset_index()
md('```\n' + c.to_string(index=False) + '\n```')
md(f'\nKul: {int((S.ret > 0).sum())} / {len(S)} combos plus ({(S.ret > 0).mean() * 100:.0f}%), PASS {int(S.PASS.sum())}.')

md('\n## 2. Jo PASS hue (sab)')
P = S[S.PASS].sort_values('ret', ascending=False)
cols = ['sym', 'cyc', 'entry', 'z', 'w', 'exit', 'n', 'win', 'ret', 'pf', 'worst', 'e1', 'e2', 'e3', 'rs_lot', 'first', 'last']
md('```\n' + (P[cols].to_string(index=False) if len(P) else '(koi nahi)') + '\n```')

md('\n## 3. Out-of-sample: pehle aadhe ka best -> doosre aadhe mein')
oo = []
for (s, cy), g in T.groupby(['sym', 'cyc']):
    h1 = g[g.half == 1].groupby(['entry', 'z', 'w', 'exit']).ret.agg(['mean', 'size'])
    h1 = h1[h1['size'] >= 30]
    if not len(h1): continue
    b = h1['mean'].idxmax()
    h2 = g[(g.half == 2) & (g.entry == b[0]) & (g.z == b[1]) & (g.w == b[2]) & (g.exit == b[3])]
    oo.append(dict(sym=s, cyc=cy, best_first_half=f'{b[0]} z{b[1]} w{b[2]} {b[3]}', first_ret=round(h1['mean'].max() * 100, 2), second_ret=round(h2.ret.mean() * 100, 2) if len(h2) else np.nan, n2=len(h2)))
OO = pd.DataFrame(oo); md('```\n' + OO.to_string(index=False) + '\n```')
if len(OO): md(f'Doosre aadhe mein plus: {int((OO.second_ret > 0).sum())} / {len(OO)}; avg pehla {OO.first_ret.mean():.2f}% -> doosra {OO.second_ret.mean():.2f}%')

md('\n## 4. Har setting ka "sab symbols par" haal (cycle, entry, z, w, exit)')
U = S.groupby(['cyc', 'entry', 'z', 'w', 'exit']).agg(symbols=('sym', 'size'), plus_syms=('ret', lambda x: int((x > 0).sum())), avg_ret=('ret', 'mean'), passed=('PASS', 'sum')).reset_index()
U['avg_ret'] = U.avg_ret.round(2)
md('Top 15 (plus symbols ke hisaab se):')
md('```\n' + U.sort_values(['plus_syms', 'avg_ret'], ascending=False).head(15).to_string(index=False) + '\n```')

md('\n## 5. Entry din / exit / z ka asar (sab symbols, sab combos ka median ret %)')
for col in ('entry', 'exit', 'z', 'w'):
    m = S.groupby(['cyc', col]).ret.median().unstack(0).round(2)
    md(f'{col}:\n```\n' + m.to_string() + '\n```')

md('\n## 6. Dost ke tarah ki setting (weekly index, after-entry, hold) har index par')
F_ = S[(S.cyc == 'weekly') & (S.entry == 'after') & (S.exit.isin(['hold', 'T60S150']))][['sym', 'z', 'w', 'exit', 'n', 'win', 'ret', 'pf', 'e1', 'e2', 'e3', 'rs_lot']]
md('```\n' + F_.sort_values(['sym', 'exit', 'z', 'w']).to_string(index=False) + '\n```')
open(os.path.join(OUT, 'cg_condor_grid.md'), 'w').write('\n'.join(MD) + '\n')
