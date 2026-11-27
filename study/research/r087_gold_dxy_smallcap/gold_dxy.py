# r087 AI-A63247: gold/silver weak when DXY up AND US10y up (and Nasdaq down)? Daily, monthly-sampled non-overlap.
import pandas as pd, numpy as np
G='/home/claude/market-data/data/global/'
def L(f): x=pd.read_csv(G+f+'.csv',parse_dates=['date']).set_index('date'); return x['close'][x['close']>0]
gold,silv,dxy,y10,nq=[L(f) for f in ['CMD_GOLD','CMD_SILVER','FX_DOLLAR_INDEX','US_10Y','US_NASDAQ']]
D=pd.concat({'g':gold,'s':silv,'d':dxy,'y':y10,'n':nq},axis=1).dropna()
D=D[D.index>='2001-01-01']
lb=20
sig_d=D.d/D.d.shift(lb)-1>0; sig_y=D.y-D.y.shift(lb)>0; sig_n=D.n/D.n.shift(lb)-1<0
for asset in ['g','s']:
  for h in [20,60]:
    fwd=D[asset].shift(-h)/D[asset]-1
    print(f'--- {asset} fwd {h}d (sampled every {h}d, non-overlap)')
    for name,s in [('ALL',pd.Series(True,index=D.index)),('DXY up & 10y up',sig_d&sig_y),('DXY up & 10y up & Nasdaq down',sig_d&sig_y&sig_n),('DXY down & 10y down',(~sig_d)&(~sig_y))]:
      for era,a,b in [('2001-10','2001','2010'),('2011-18','2011','2018'),('2019-26','2019','2026'),('all','2001','2026')]:
        f=fwd[a:b][s[a:b]].dropna()
        # non-overlap: take one obs per h days
        f=f.iloc[::h] if len(f) else f
        if len(f)<3: continue
        print(f'{name:32s} {era:8s} N{len(f):4d} avg {f.mean()*100:+6.2f}% up {np.mean(f>0)*100:4.0f}%')
# recent 2/4/6 months: count of signal days and gold fwd 20d
fwd=D.g.shift(-20)/D.g-1; s=sig_d&sig_y
for m in [2,4,6]:
  st=D.index[-1]-pd.DateOffset(months=m); f=fwd[st:][s[st:]].dropna()
  print(f'last {m}m signal days {len(f)} gold fwd20 avg {f.mean()*100 if len(f) else float("nan"):+.2f}% (all days {fwd[st:].dropna().mean()*100:+.2f}%)')
print('last date',D.index[-1].date(),'signal today',bool(s.iloc[-1]))
