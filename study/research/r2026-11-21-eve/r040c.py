import pandas as pd,numpy as np
exec(open('r040_fed.py').read().split("print('Market (EW all)")[0])
G='/home/claude/market-data/data/global/'
def g(n): d=pd.read_csv(G+n+'.csv',index_col='date',parse_dates=True).close; return d[~d.index.duplicated()].reindex(ix,method='ffill')
dx=g('FX_DOLLAR_INDEX'); br=g('CMD_BRENT'); inr=g('FX_USDINR'); ni=pd.read_csv('/home/claude/market-data/data/IN_SENSEX.csv' if False else G+'IN_SENSEX.csv',index_col='date',parse_dates=True).close.reindex(ix,method='ffill')
df=X[['Capital Goods','Information Technology','cycle']].copy()
df['dxy20']=(dx/dx.shift(20)-1).reindex(df.index)*100
df['brent20']=(br/br.shift(20)-1).reindex(df.index)*100
df['inr20']=(inr/inr.shift(20)-1).reindex(df.index)*100
df['above200']=(ni>ni.rolling(200).mean()).reindex(df.index)
df['mkt20']=mk.values
for col in ['dxy20','brent20','inr20']:
    df['b']=df[col]>df[col].median()
    print(col,'median %.2f'%df[col].median()); print(df.groupby('b')[['Capital Goods','Information Technology']].mean().round(2))
print(df.groupby('above200')[['Capital Goods','Information Technology']].agg(['mean','count']).round(2))
print('CG winners vs losers:'); print(df.groupby(df['Capital Goods']>0)[['dxy20','brent20','inr20','mkt20']].mean().round(2))
print('now: dxy20 %.2f brent20 %.2f inr20 %.2f'%((dx.iloc[-1]/dx.iloc[-21]-1)*100,(br.iloc[-1]/br.iloc[-21]-1)*100,(inr.iloc[-1]/inr.iloc[-21]-1)*100), ix[-1])
