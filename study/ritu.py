"""6 ritu / 3 mausam / fasal ke mausam vs bazaar (user 9 Nov 2026). Dates are approximate (ritu follow the lunar-solar calendar;
here fixed Gregorian windows). Sensex 1997-2026 daily, all-share average 2003-26. Avg daily return per season, per era, vs all days;
and t-stat vs the normal day. Per-season annualised for easy reading."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sx = pd.read_csv(os.path.join(R, 'data', 'global', 'IN_SENSEX.csv'), parse_dates=['date']).set_index('date').close.dropna()
sx = sx[~sx.index.duplicated()].sort_index(); rs = sx.pct_change().dropna() * 100
P = nc.load(); ra = P['a'].pct_change(fill_method=None).clip(-0.4, 0.4).mean(axis=1).dropna() * 100
def ritu(d):
    md_ = d.month * 100 + d.day
    if 315 <= md_ < 515: return '1 Vasant (Basant, 15 Mar-14 May)'
    if 515 <= md_ < 715: return '2 Grishma (garmi, 15 May-14 Jul)'
    if 715 <= md_ < 915: return '3 Varsha (baarish, 15 Jul-14 Sep)'
    if 915 <= md_ < 1115: return '4 Sharad (15 Sep-14 Nov)'
    if md_ >= 1115 or md_ < 115: return '5 Hemant (15 Nov-14 Jan)'
    return '6 Shishir (sardi, 15 Jan-14 Mar)'
def teen(d): return '1 Garmi (Mar-Jun)' if d.month in (3, 4, 5, 6) else ('2 Barsaat (Jul-Sep)' if d.month in (7, 8, 9) else '3 Sardi (Oct-Feb)')
def fasal(d): return '1 Kharif buwai (Jun-Jul)' if d.month in (6, 7) else ('2 Kharif katai (Sep-Nov)' if d.month in (9, 10, 11) else ('3 Rabi buwai (Oct-Dec)' if d.month == 12 else ('4 Rabi katai (Mar-Apr)' if d.month in (3, 4) else '5 baaki')))
L = ['# Mausam (ritu) aur bazaar', 'Ausat roz ka return; "saal bhar ki raftaar" = us mausam ki raftaar se poora saal chale to. t = aam din se fark.', '']
for nm, ser, start in (('Sensex 1997-2026', rs, '1997'), ('Sab shares ka ausat 2003-26', ra, '2003')):
    for title, fn in (('6 ritu', ritu), ('3 mausam', teen), ('fasal ke mausam', fasal)):
        g = pd.Series([fn(d) for d in ser.index], index=ser.index)
        L.append(f'## {nm} — {title}')
        L.append('| mausam | roz avg % | saal bhar ki raftaar | t | 1997/2003-2012 | 2013-20 | 2021-26 |'); L.append('|---|---|---|---|---|---|---|')
        base = ser.mean()
        for k in sorted(g.unique()):
            x = ser[g == k]; t = (x.mean() - base) / x.std() * np.sqrt(len(x))
            e = [x[(x.index >= a) & (x.index <= b)].mean() for a, b in ((start, '2012'), ('2013', '2020'), ('2021', '2026'))]
            L.append(f'| {k} | {x.mean():+.3f} | {((1 + x.mean() / 100) ** 250 - 1) * 100:+.0f}% | {t:+.1f} | {e[0]:+.3f} | {e[1]:+.3f} | {e[2]:+.3f} |')
        L.append('')
open(os.path.join(R, 'study', 'results', 'ritu.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
