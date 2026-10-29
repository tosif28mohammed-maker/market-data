"""Combine 500-stock battery results: real vs chance counts, per-stock score, focus list, workbook.
Usage: python study/agg500.py res_0.csv res_1.csv ... --basket basket.csv --out Nifty500_Study.xlsx"""
import sys, numpy as np, pandas as pd, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
args = sys.argv[1:]; out = args[args.index('--out') + 1]; bk = args[args.index('--basket') + 1]
files = [a for a in args if a.endswith('.csv') and a not in (bk,)]
R = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
P = ['split', 'E3E4', 'R1R2']; PN = {'split': 'पुराना 60% -> नया 40%', 'E3E4': '2013-20 -> 2021-26', 'R1R2': '2021-Oct23 -> Nov23-आज'}
rows = []
for kind, kn in (('trend', 'MA trend (ऊपर तो hold)'), ('buy', 'MA से बहुत नीचे खरीद'), ('sell', 'MA से बहुत ऊपर short')):
    for p in P:
        c = f'{kind}_{p}_pass'
        if c not in R: continue
        x = R[R[c].notna()]
        rows.append({'तरीका': kn, 'परख': PN[p], 'शेयर': len(x), 'असली में चला': int(x[c].astype(bool).sum()), 'नकली (संयोग) में चला': int(x['shuf_' + c].astype(bool).sum())})
for c, kn in (('cal_holdout', 'तारीख़ नियम (पहले 2/3 -> आख़िरी 1/3)'), ('cal_E3E4', 'तारीख़ नियम 2013-20 -> 2021-26'), ('cal_R1R2', 'तारीख़ नियम 2021-23 -> 2023-26')):
    if c not in R: continue
    x = R[R[c + '_p'].notna()]
    rows.append({'तरीका': kn, 'परख': 'p<=0.05 वाले शेयर', 'शेयर': len(x), 'असली में चला': int((x[c + '_p'] <= 0.05).sum()), 'नकली (संयोग) में चला': round(len(x) * 0.05, 1)})
CNT = pd.DataFrame(rows); CNT['असली / संयोग'] = (CNT['असली में चला'] / CNT['नकली (संयोग) में चला'].replace(0, np.nan)).round(2)
# per-stock score: robust passes (both long-history tests) count double
def b(c): return R[c].fillna(False).astype(bool) if c in R else pd.Series(False, index=R.index)
R['cal_hits'] = sum((R[c + '_p'] <= 0.05).fillna(False).astype(int) for c in ('cal_holdout', 'cal_E3E4', 'cal_R1R2') if c + '_p' in R)
for k in ('trend', 'buy', 'sell'): R[f'{k}_hits'] = sum(b(f'{k}_{p}_pass').astype(int) for p in P)
R['score'] = R.cal_hits + R.trend_hits + R.buy_hits + R.sell_hits
R['robust'] = ((R.cal_hits >= 2) | (R.trend_hits >= 2) | (R.buy_hits >= 2) | (R.sell_hits >= 2))
def why(r):
    w = []
    for c, kn in (('cal_holdout', 'तारीख़(2/3)'), ('cal_E3E4', 'तारीख़(13-20->21-26)'), ('cal_R1R2', 'तारीख़(21-23->23-26)')):
        if c + '_p' in r and pd.notna(r[c + '_p']) and r[c + '_p'] <= 0.05: w.append(f"{kn}: {r[c + '_rules']}")
    for k, kn in (('trend', 'Trend'), ('buy', 'नीचे खरीद'), ('sell', 'ऊपर short')):
        for p in P:
            if bool(r.get(f'{k}_{p}_pass', False)) is True: w.append(f"{kn} {PN[p]}: {r.get(f'{k}_{p}_MA')}")
    return ' | '.join(w)
R['कारण'] = R.apply(why, axis=1)
S = R.sort_values(['score', 'robust'], ascending=False)
# chance for score>=2: from shuffle flags (MA parts) + 5% calendar
shuf_score = sum(b(f'shuf_{k}_{p}_pass').astype(int) for k in ('trend', 'buy', 'sell') for p in P)
BK = pd.read_csv(bk)
wb = openpyxl.Workbook(); ws0 = wb.active; ws0.title = 'नतीजा'
B_ = Font(bold=True); HD = PatternFill('solid', fgColor='DDEBF7'); GR = PatternFill('solid', fgColor='C6EFCE')
def sheet(name, df, title, note='', pct=(), wide=13, fill=None):
    ws = wb.create_sheet(name); ws['A1'] = title; ws['A1'].font = Font(bold=True, size=13); ws['A2'] = note; r0 = 4
    for j, c in enumerate(df.columns, 1):
        x = ws.cell(r0, j, str(c)); x.font = B_; x.fill = HD; x.alignment = Alignment(wrap_text=True, vertical='top'); ws.column_dimensions[x.column_letter].width = wide
    for i, row in enumerate(df.itertuples(index=False), r0 + 1):
        for j, v in enumerate(row, 1):
            if v is None or (isinstance(v, float) and np.isnan(v)): continue
            if isinstance(v, (bool, np.bool_)): v = 'हाँ' if v else ''
            x = ws.cell(i, j, v if isinstance(v, str) else float(v) if isinstance(v, (int, float, np.number)) else str(v))
            if df.columns[j - 1] in pct: x.number_format = '0%'
            elif isinstance(v, (float, np.floating)): x.number_format = '0.00'
        if fill and fill(row):
            for j in range(1, len(df.columns) + 1): ws.cell(i, j).fill = GR
    ws.freeze_panes = ws.cell(r0 + 1, 2); return ws
sheet('असली बनाम संयोग', CNT, 'हर तरीका: कितने शेयरों में पुराने में मिला नियम नए में भी चला (असली बनाम नकली डेटा)', 'असली / संयोग 1.5 से ऊपर = तरीके में कुछ दम; 1 के आसपास = संयोग.', fill=lambda r: (r[5] or 0) >= 1.5, wide=22)
cols = ['symbol', 'company', 'industry', 'start', 'score', 'robust', 'cal_hits', 'trend_hits', 'buy_hits', 'sell_hits', 'कारण']
F = S[S.score >= 2][cols].copy(); F.columns = ['शेयर', 'कंपनी', 'Industry', 'डेटा शुरू', 'कुल पास', 'दो परख में पक्का', 'तारीख़', 'Trend', 'नीचे खरीद', 'ऊपर short', 'क्या चला']
ws = sheet('Focus list', F, 'Focus: जिन शेयरों पर 2 या ज़्यादा परख पास हुईं', f'नकली डेटा में (सिर्फ़ MA वाली परख) 2+ पास वाले शेयर: {(shuf_score >= 2).sum()} ; असली (MA वाली): {((R.trend_hits + R.buy_hits + R.sell_hits) >= 2).sum()}. हरा = एक ही तरीका दो अलग परख में पास.', fill=lambda r: r[5] is True or r[5] == 'हाँ' or r[5] == True)
ws.column_dimensions['K'].width = 120; ws.column_dimensions['B'].width = 30
A = S[cols].copy(); A.columns = F.columns; sheet('सारे शेयर', A, 'Nifty 500: हर शेयर का हिसाब', '')
IND = R.groupby('industry').agg(शेयर=('symbol', 'size'), औसत_पास=('score', 'mean'), तारीख़=('cal_hits', 'sum'), Trend=('trend_hits', 'sum'), नीचे_खरीद=('buy_hits', 'sum'), ऊपर_short=('sell_hits', 'sum')).reset_index().sort_values('औसत_पास', ascending=False)
sheet('Industry', IND, 'Industry के हिसाब से', '')
E = BK[BK.key == 'event'].pivot(index='val', columns='era', values='excess').reindex(columns=[c for c in ['ALL', 'E1', 'E2', 'E3', 'E4', 'R1', 'R2'] if c in BK.era.unique()])
T = BK[BK.key == 'event'].pivot(index='val', columns='era', values='t').reindex(columns=E.columns)
EV = pd.concat([E.round(1).add_prefix('ज़्यादा % '), T.round(1).add_prefix('t ')], axis=1).reset_index().rename(columns={'val': 'घटना'})
sheet('500 basket: घटनाएँ', EV, 'Nifty 500 (सारे शेयर): ख़ास दिनों में आम दिनों से कितने % ज़्यादा शेयर ऊपर, हर दौर में', 'E1 2002 तक, E2 2003-12, E3 2013-20, E4 2021-26, R1 2021-Oct23, R2 Nov23-आज. t>=2 मज़बूत.')
X = BK[BK.key != 'event']; XT = X.pivot_table(index=['key', 'val'], columns='era', values='t'); XE = X.pivot_table(index=['key', 'val'], columns='era', values='excess')
XS = pd.concat([XE.round(1).add_prefix('ज़्यादा % '), XT.round(1).add_prefix('t ')], axis=1).reset_index()
sheet('500 basket: तारीख़ें', XS, 'Nifty 500 basket: हर तारीख़/वार/महीना/हिजरी तारीख़ हर दौर में', '')
pd.to_pickle(dict(R=R, CNT=CNT, BK=BK), out.replace('.xlsx', '.pkl'))
wb.save(out); print(CNT.to_string()); print('focus', len(F), 'robust', int(S.robust.sum()))
