"""Weather / natural & country events vs markets (user 9 Nov 2026: 'toofan, moosladhaar baarish, bahut garmi/thand, Kashmir mein
barfbaari, desh ke halaat, America ke toofan — us din / baad mein bazaar kaisa raha').
Data: Open-Meteo historical archive (free, no key; ERA5 reanalysis, daily since 1940) for Mumbai (NSE/BSE ka shehar), Delhi, 11 more
Indian cities (monsoon), Srinagar (barf), New York (NYSE) — fetched by the robot into data/weather/.
Markets: Sensex 1997-2026, Nifty 2007-26, S&P 500 1990-2026, all-share Indian average (panel) 2003-26.
Tests (python study/weather.py fetch | study):
  1. Mumbai daily weather -> Sensex same day & next day: sunshine/clouds, heavy rain (50/100 mm+), very hot / very cold for the
     season (top/bottom 5% vs that month's normal), strong wind. New York weather -> S&P same. Placebo: weather of a far city
     (Reykjavik) used against the same market. Halves.
  2. Monsoon: June-Sept rain of 12 Indian cities vs normal -> Sensex and rural shares (tractor, fertiliser, FMCG, auto) Oct-Mar.
  3. Kashmir: Srinagar Dec-Feb snowfall -> Sensex next Mar-May (expected: nothing; checked anyway).
  4. Events: Indian shocks (attacks, war, demonetisation, lockdown, floods, tsunami) and US hurricanes / 9-11 -> index day 0..+20
     vs the same index's normal day (random dates), how often it recovered within 20 days.
"""
import os, sys, json, time, datetime as dt, urllib.request, urllib.parse, numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); WD = os.path.join(R, 'data', 'weather'); os.makedirs(WD, exist_ok=True)
CITIES = {'Mumbai': (19.08, 72.88), 'Delhi': (28.61, 77.21), 'Kolkata': (22.57, 88.36), 'Chennai': (13.08, 80.27), 'Bengaluru': (12.97, 77.59),
          'Hyderabad': (17.39, 78.49), 'Nagpur': (21.15, 79.09), 'Bhopal': (23.26, 77.41), 'Lucknow': (26.85, 80.95), 'Jaipur': (26.91, 75.79),
          'Ahmedabad': (23.02, 72.57), 'Patna': (25.59, 85.14), 'Srinagar': (34.08, 74.80), 'NewYork': (40.71, -74.01), 'Reykjavik': (64.15, -21.94)}
part = sys.argv[1] if len(sys.argv) > 1 else 'study'

if part == 'fetch':
    for c, (la, lo) in CITIES.items():
        q = urllib.parse.urlencode({'latitude': la, 'longitude': lo, 'start_date': '1990-01-01', 'end_date': str(dt.date.today() - dt.timedelta(days=7)),
                                    'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,wind_speed_10m_max,sunshine_duration,cloud_cover_mean',
                                    'timezone': 'auto'})
        for a in range(4):
            try:
                with urllib.request.urlopen('https://archive-api.open-meteo.com/v1/archive?' + q, timeout=120) as r_:
                    j = json.load(r_)
                d = pd.DataFrame(j['daily']); d.to_csv(os.path.join(WD, f'{c}.csv.gz'), index=False); print(c, len(d)); break
            except Exception as e:
                print('retry', c, e); time.sleep(20 + 20 * a)
        time.sleep(3)
    sys.exit()

MD = []
def md(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); MD.append(s)
def W(c):
    d = pd.read_csv(os.path.join(WD, f'{c}.csv.gz'), parse_dates=['time']).set_index('time')
    d['tmax_anom'] = d.temperature_2m_max - d.groupby(d.index.month).temperature_2m_max.transform('mean')
    d['tmin_anom'] = d.temperature_2m_min - d.groupby(d.index.month).temperature_2m_min.transform('mean')
    d['sun_anom'] = d.sunshine_duration - d.groupby(d.index.month).sunshine_duration.transform('mean')
    return d
def IX(name):
    d = pd.read_csv(os.path.join(R, 'data', 'global', f'{name}.csv'), parse_dates=['date']).set_index('date').close.dropna()
    return d[~d.index.duplicated()].sort_index()
def tstat(x):
    x = pd.Series(x).dropna(); return (x.mean() / x.std() * np.sqrt(len(x))) if len(x) > 5 and x.std() > 0 else np.nan

SX, SP = IX('IN_SENSEX'), IX('US_SP500'); SP = SP[SP.index >= '1990-01-01']
md('# Mausam aur bazaar')
for city, mkt, mname, plc in (('Mumbai', SX, 'Sensex', 'Reykjavik'), ('NewYork', SP, 'S&P 500', 'Reykjavik')):
    w = W(city).reindex(mkt.index); p = W(plc).reindex(mkt.index)
    r = mkt.pct_change() * 100; nxt = r.shift(-1)
    half = mkt.index[len(mkt) // 2]
    md(f'\n## {city} ka mausam -> {mname} (sab dinon ka ausat {r.mean():+.3f}%)')
    def show(lbl, m, wsrc):
        rows = []
        for nm, ser in (('usi din', r), ('agle din', nxt)):
            a, b = ser[m & (ser.index < half)], ser[m & (ser.index >= half)]
            rows.append(f'{nm} {ser[m].mean():+.3f}% (t {tstat(ser[m] - ser.mean()):.1f}; pehla aadha {a.mean():+.3f}, doosra {b.mean():+.3f})')
        md(f'- {lbl} [{int(m.sum())} din]: ' + ' | '.join(rows))
    for src, tag in ((w, ''), (p, f' [PLACEBO: {plc} ka mausam]')):
        q = src.sun_anom
        show('bahut dhoop wala din (top 20%)' + tag, q >= q.quantile(0.8), src)
        show('bahut badal (neeche 20% dhoop)' + tag, q <= q.quantile(0.2), src)
        show('moosladhaar baarish 50mm+' + tag, src.precipitation_sum >= 50, src)
        if tag == '':
            show('bahut bhaari baarish 100mm+', src.precipitation_sum >= 100, src)
            show('season ke hisaab se bahut garmi (top 5%)', src.tmax_anom >= src.tmax_anom.quantile(0.95), src)
            show('season ke hisaab se bahut thand (neeche 5%)', src.tmin_anom <= src.tmin_anom.quantile(0.05), src)
            show('tez hawa/toofan (top 2% hawa)', src.wind_speed_10m_max >= src.wind_speed_10m_max.quantile(0.98), src)
            if city == 'NewYork': show('barf 5cm+', src.snowfall_sum >= 5, src)

# ---- monsoon ----
md('\n## Monsoon (June-Sept, 12 shehron ki baarish ka normal se fark) -> Oct-Mar')
rain = pd.concat({c: W(c).precipitation_sum for c in CITIES if c not in ('Srinagar', 'NewYork', 'Reykjavik')}, axis=1)
jjas = rain[rain.index.month.isin([6, 7, 8, 9])].groupby(lambda d: d.year).sum().mean(axis=1)
anom = (jjas / jjas.mean() - 1) * 100
rows = []
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import ni_common as nc
    P = nc.load(); A = P['a']; ind = pd.read_csv(os.path.join(R, 'data', 'fund', 'summary.csv')).set_index('symbol').industry
    rural = [s for s in A.columns if ind.get(s) in ('Agricultural Inputs', 'Farm & Heavy Construction Machinery', 'Packaged Foods', 'Household & Personal Products', 'Auto Manufacturers', 'Farm Products')]
    M = A.resample('ME').last(); mr = M.pct_change(fill_method=None).clip(-0.5, 0.5)
except Exception as e:
    print('panel', e); A = None
for y in anom.index:
    if y < 1997 or y > 2025: continue
    a_, b_ = pd.Timestamp(y, 9, 30), pd.Timestamp(y + 1, 3, 31)
    sx = SX[a_:b_]
    if len(sx) < 50: continue
    row = dict(year=y, rain_anom=round(anom[y], 1), sensex_oct_mar=round((sx.iloc[-1] / sx.iloc[0] - 1) * 100, 1))
    if A is not None and y >= 2003:
        seg = mr[(mr.index > a_) & (mr.index <= b_ + pd.offsets.MonthEnd(0))]
        row['rural_vs_all'] = round(((1 + seg[rural].mean(axis=1)).prod() - (1 + seg.mean(axis=1)).prod()) * 100, 1)
    rows.append(row)
MO = pd.DataFrame(rows); MO.to_csv(os.path.join(R, 'study', 'results', 'weather_monsoon.csv'), index=False)
md(f'- {len(MO)} saal. Corr(baarish, Sensex Oct-Mar) = {MO.rain_anom.corr(MO.sensex_oct_mar):+.2f}' + (f'; corr(baarish, rural shares bazaar se fark) = {MO.rain_anom.corr(MO.rural_vs_all):+.2f}' if 'rural_vs_all' in MO else ''))
for nm, m in (('kam baarish (normal se -10%+)', MO.rain_anom <= -10), ('normal', MO.rain_anom.abs() < 10), ('zyada baarish (+10%+)', MO.rain_anom >= 10)):
    x = MO[m]; md(f'- {nm}: {len(x)} saal, Sensex Oct-Mar avg {x.sensex_oct_mar.mean():+.1f}%' + (f', rural shares bazaar se {x.rural_vs_all.mean():+.1f}%' if 'rural_vs_all' in x else '') + f" ({', '.join(str(v) for v in x.year)})")

# ---- Kashmir snow ----
sn = W('Srinagar').snowfall_sum
rows = []
for y in range(1998, 2026):
    s_ = sn[(sn.index >= f'{y - 1}-12-01') & (sn.index < f'{y}-03-01')].sum()
    x = SX[f'{y}-03-01':f'{y}-05-31']
    if len(x) > 30: rows.append(dict(year=y, snow_cm=round(s_, 1), sensex_mar_may=round((x.iloc[-1] / x.iloc[0] - 1) * 100, 1)))
KS = pd.DataFrame(rows)
md(f'\n## Kashmir (Srinagar Dec-Feb barf) -> Sensex Mar-May: corr {KS.snow_cm.corr(KS.sensex_mar_may):+.2f} ({len(KS)} saal); '
   f'zyada barf (top tihaai) {KS[KS.snow_cm >= KS.snow_cm.quantile(2 / 3)].sensex_mar_may.mean():+.1f}% vs kam barf {KS[KS.snow_cm <= KS.snow_cm.quantile(1 / 3)].sensex_mar_may.mean():+.1f}%')

# ---- events ----
EV_IN = [('2001-12-13', 'Sansad hamla'), ('2004-12-27', 'Tsunami'), ('2005-07-27', 'Mumbai baadh 26/7'), ('2006-07-12', 'Mumbai train blast'),
         ('2008-11-28', 'Mumbai 26/11 hamla'), ('2013-06-17', 'Uttarakhand baadh'), ('2016-09-29', 'Surgical strike'), ('2016-11-09', 'Notebandi'),
         ('2019-02-15', 'Pulwama'), ('2019-02-26', 'Balakot'), ('2020-03-25', 'Lockdown elaan'), ('2022-02-24', 'Russia-Ukraine jung'),
         ('2023-10-09', 'Israel hamla'), ('2025-04-23', 'Pahalgam'), ('2025-05-07', 'Operation Sindoor')]
EV_US = [('2001-09-17', '9/11 (bazaar khula)'), ('2005-08-29', 'Katrina'), ('2012-10-31', 'Sandy'), ('2017-08-28', 'Harvey'), ('2017-09-11', 'Irma'),
         ('2017-09-20', 'Maria'), ('2022-09-28', 'Ian'), ('2024-09-26', 'Helene'), ('2024-10-09', 'Milton')]
for evs, mkt, nm in ((EV_IN, SX, 'Sensex — desh ke bade jhatke'), (EV_US, SP, 'S&P 500 — America ke toofan / 9-11')):
    md(f'\n## {nm} (din 0 = pehla kaarobaari din, pichhle close se)')
    rows = []
    for d, e in evs:
        i = mkt.index.searchsorted(pd.Timestamp(d))
        if i < 1 or i + 20 >= len(mkt): continue
        b = mkt.iloc[i - 1]
        rows.append(dict(event=e, date=str(mkt.index[i].date()), d0=(mkt.iloc[i] / b - 1) * 100, d5=(mkt.iloc[i + 5] / b - 1) * 100, d20=(mkt.iloc[i + 20] / b - 1) * 100))
    E = pd.DataFrame(rows)
    rr = mkt.pct_change()
    base0, base5, base20 = rr.mean() * 100, ((mkt.shift(-5) / mkt.shift(1) - 1) * 100).mean(), ((mkt.shift(-20) / mkt.shift(1) - 1) * 100).mean()
    for x in E.itertuples(): md(f'- {x.date} {x.event}: din 0 {x.d0:+.1f}%, 5 din {x.d5:+.1f}%, 20 din {x.d20:+.1f}%')
    md(f'- **Ausat**: din 0 {E.d0.mean():+.2f}% (aam din {base0:+.2f}), 5 din {E.d5.mean():+.2f}% (aam {base5:+.2f}), 20 din {E.d20.mean():+.2f}% (aam {base20:+.2f}); '
       f'20 din mein upar: {(E.d20 > 0).mean() * 100:.0f}% (aam din se {((mkt.shift(-20) / mkt.shift(1) - 1) > 0).mean() * 100:.0f}%)')
open(os.path.join(R, 'study', 'results', 'weather.md'), 'w').write('\n'.join(MD) + '\n')
