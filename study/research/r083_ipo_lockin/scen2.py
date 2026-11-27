import pandas as pd, numpy as np
ALL=pd.read_pickle('events.pkl'); R=ALL[90]; R=R[R.d>='2022-07-01'].copy()
import sys; sys.path.insert(0,'/home/claude/market-data/study'); from ni_common import load
P=load(); a=P['a']
R['run']=pd.qcut(R.runup,3,labels=['losers','mid','winners'])
R['absrun']=np.where(R.abs_run>0,'above listing','below listing')
for col in ['run','absrun','bull']:
    print(col, R.groupby(col,observed=True)['pre-10_-1'].agg(['count','mean']).round(2).to_dict('index'))
print('%neg pre', round((R['pre-10_-1']<0).mean()*100), 'median', round(R['pre-10_-1'].median(),2))
print('panel last date', a.index[-1].date())
first=a.apply(lambda s: s.first_valid_index())
rec=first[first>='2026-06-01'].sort_values(); print('recent listings in panel:', len(rec)); print(rec.tail(15).to_string())
