import pandas as pd, numpy as np, sys
S=sys.argv[1]
L=pd.read_csv('study/results/liq_all.csv').set_index('symbol')
import os
Ps=[]
for fn in ([] if os.path.exists(f'{S}/sw_P.pkl') else ['sw0a','sw0b','sw1']):
    R=pd.read_pickle(f'{S}/{fn}.pkl'); R=R[~R.stock.isin(['NIFTY','BANKNIFTY'])] if fn!='sw0a' else R
    p=R.pivot_table(index=['stock','tf','typ','L'],columns='per',values=['trades','per_year','win','avg','p10','held','back','thr'])
    p.columns=[f'{a}_{b}' for a,b in p.columns]; Ps.append(p.reset_index()); del R
P=pd.concat(Ps,ignore_index=True).drop_duplicates(['stock','tf','typ','L']) if Ps else pd.read_pickle(f'{S}/sw_P.pkl'); del Ps
print('rows',len(P),'stocks',P.stock.nunique())
P.to_pickle(f'{S}/sw_P.pkl') if not os.path.exists(f'{S}/sw_P.pkl') else None
# 1) pooled landscape: median over stocks of avg_B, win_B by tf x L bucket
P['Lb']=pd.cut(P.L,[1,5,10,15,20,30,50,75,100,125,150,200,250,300,400,500])
land=P[(P.trades_A>=5)&(P.trades_B>=5)].groupby(['tf','Lb'],observed=True).agg(stocks=('stock','nunique'),win_A=('win_A','median'),win_B=('win_B','median'),avg_A=('avg_A','median'),avg_B=('avg_B','median'),per_year=('per_year_B','median'),held=('held_B','median'),back=('back_B','median')).reset_index()
pd.set_option('display.width',250); print(land.round(3).to_string(index=False))
# 2) learn best L on half A, test on half B, per stock x tf; compare with fixed default per tf (median-best L overall)
out=[]
for (s,tf),g in P[(P.trades_A>=6)].groupby(['stock','tf']):
    g=g.copy(); g['scoreA']=g.avg_A*g.win_A
    # neighbour smoothing: rolling mean of scoreA over +-3 lengths within typ
    g=g.sort_values(['typ','L']); g['smA']=g.groupby('typ').scoreA.transform(lambda x:x.rolling(7,center=True,min_periods=3).mean())
    if g.smA.notna().sum()==0: continue
    b=g.loc[g.smA.idxmax()]
    out.append(dict(stock=s,tf=tf,typ=b.typ,L=b.L,trades_A=b.trades_A,win_A=b.win_A,avg_A=b.avg_A,trades_B=b.trades_B,win_B=b.win_B,avg_B=b.avg_B,per_year_B=b.per_year_B,p10_B=b.p10_B,held_B=b.held_B,trades_N=b.get('trades_N',np.nan),win_N=b.get('win_N',np.nan),avg_N=b.get('avg_N',np.nan),
                    medB_all=g.avg_B.median(),medwinB_all=g.win_B.median()))
B=pd.DataFrame(out)
print(B.groupby('tf').agg(stocks=('stock','size'),chosen_avg_B=('avg_B','median'),all_lengths_avg_B=('medB_all','median'),chosen_win_B=('win_B','median'),all_win_B=('medwinB_all','median'),beat_pct=('avg_B',lambda x:np.nan)).round(4).to_string())
B['beats_median']=B.avg_B>B.medB_all; print(B.groupby('tf').beats_median.mean().round(3).to_string())
# 3) robust 'rare & big' picks: chosen L passes in both halves + Nov23
B['liq']=B.stock.map(L.liquidity); B['turn']=B.stock.map(L.turnover_cr)
good=B[(B.trades_B>=5)&(B.win_A>=0.75)&(B.win_B>=0.75)&(B.avg_A>=0.02)&(B.avg_B>=0.02)&((B.tf.isin(['1H','2H','3H','4H']))|(B.trades_N.fillna(0)<3)|(B.win_N>=0.66))&B.liq.str[0].isin(['A','B'])]
print('robust stock picks',len(good)); print(good.groupby('tf').size())
pd.to_pickle((land,B,good),f'{S}/sw_res.pkl')
print(good.sort_values('turn',ascending=False).head(40)[['stock','tf','typ','L','trades_A','win_A','avg_A','trades_B','win_B','avg_B','per_year_B','held_B','win_N','avg_N','liq']].round(3).to_string(index=False))
