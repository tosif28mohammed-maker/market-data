# r081: RH-01 RBI hike-cycle start -> Sensex/BankNifty forward; DXY-01 dollar monthly winning streak -> Sensex/EEM next months
import pandas as pd, numpy as np, json
g='data/global/'
sx=pd.read_csv(g+'IN_SENSEX.csv',parse_dates=['date']).set_index('date').close
bn=pd.read_csv('data/BANKNIFTY.csv',parse_dates=['date']).set_index('date').close
dx=pd.read_csv(g+'FX_DOLLAR_INDEX.csv',parse_dates=['date']).set_index('date').close
em=pd.read_csv(g+'ETF_EM_EEM.csv',parse_dates=['date']).set_index('date').adj
inr=pd.read_csv(g+'FX_USDINR.csv',parse_dates=['date']).set_index('date').close
out={}
def fwd(s,d,days):
    s=s.dropna(); i=s.index.searchsorted(pd.Timestamp(d))
    return None if i+days>=len(s) else round((s.iloc[i+days]/s.iloc[i]-1)*100,2)
H=[63,126,250]
starts=['2004-10-27','2008-06-11','2010-03-19','2013-07-15','2018-06-06','2022-05-04']
rows=[]
for d in starts:
    r={'start':d}
    for h in H: r[f'sx{h}']=fwd(sx,d,h); r[f'bn{h}']=fwd(bn,d,h)
    rows.append(r)
df=pd.DataFrame(rows); print(df.to_string())
# base: all days since 1997 / 2007
base={h:round(((sx.shift(-h)/sx-1)*100).dropna().mean(),2) for h in H}
bnb={h:round(((bn.shift(-h)/bn-1)*100).dropna().mean(),2) for h in H}
# bank relative to sensex
rel={h:round(np.nanmean([ (r[f'bn{h}'] or np.nan)-(r[f'sx{h}'] or np.nan) for r in rows if r[f'bn{h}'] is not None]),2) for h in H}
# placebo: random 6-date sets, share with mean sx250 <= observed
rng=np.random.default_rng(1); f250=((sx.shift(-250)/sx-1)*100).dropna(); f250=f250['2003':]
obs=np.nanmean([r['sx250'] for r in rows if r['sx250'] is not None])
pl=[f250.sample(6,random_state=int(k)).mean() for k in rng.integers(0,1e9,2000)]
out['RH01']={'events':rows,'base_sx':base,'base_bn':bnb,'bank_minus_sx':rel,'obs_sx250':round(obs,2),'placebo_pct_below':round(np.mean(np.array(pl)<=obs)*100,1)}
print(out['RH01'])
# DXY monthly streak
m=dx.resample('ME').last(); up=(m.pct_change()>0).astype(int)
streak=up.groupby((up!=up.shift()).cumsum()).cumsum()*up
smx=sx.resample('ME').last(); emm=em.resample('ME').last(); im=inr.resample('ME').last()
res={}
for k in [3,4,5,6]:
    sig=streak[streak==k].index  # first month reaching k (no overlap within streak)
    sig=sig[sig>='1997-08-01']
    rr={}
    for h in [1,3,6]:
        a=[((smx.shift(-h)/smx-1)*100).get(t) for t in sig]; a=[x for x in a if pd.notna(x)]
        e=[((emm.shift(-h)/emm-1)*100).get(t) for t in sig]; e=[x for x in e if pd.notna(x)]
        rr[f'sx{h}m']=(len(a),round(np.mean(a),2) if a else None,round(np.mean(np.array(a)>0)*100) if a else None)
        rr[f'em{h}m']=(len(e),round(np.mean(e),2) if e else None)
    # eras for 3m
    for lab,lo,hi in [('1997-2012','1997','2012'),('2013-26','2013','2026')]:
        a=[((smx.shift(-3)/smx-1)*100).get(t) for t in sig if lo<=str(t.year)<=hi]; a=[x for x in a if pd.notna(x)]
        rr['sx3m_'+lab]=(len(a),round(np.mean(a),2) if a else None)
    res[k]=rr
bs={h:round(((smx.shift(-h)/smx-1)*100)['1997-08':].mean(),2) for h in [1,3,6]}
be={h:round(((emm.shift(-h)/emm-1)*100).mean(),2) for h in [1,3,6]}
out['DXY01']={'by_streak':res,'base_sx':bs,'base_em':be,'current_streak':int(streak.iloc[-1]),'last_month':str(streak.index[-1].date())}
print(json.dumps(out['DXY01'],indent=1))
json.dump(out,open('study/research/r081_rbi_hike_dxy/summary.json','w'),indent=1,default=str)
