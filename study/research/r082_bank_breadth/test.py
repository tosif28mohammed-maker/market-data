# r082: BNK-01 (BankNifty 1 महीने में >=15% तेज़ी के बाद) + BRD-02 (Nifty -1% पर breadth positive)
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/home/claude/market-data/study'); import ni_common as nc
D='/home/claude/market-data/data/'
rd=lambda f: pd.read_csv(D+f, parse_dates=['date']).set_index('date').close
N, B = rd('NIFTY.csv'), rd('BANKNIFTY.csv')
idx = N.index.intersection(B.index); N, B = N[idx], B[idx]
H=(21,63,126,250)
def fwd(s): return pd.DataFrame({h:(s.shift(-h)/s-1)*100 for h in H})
def episodes(ix, gap=60):
    ix=pd.DatetimeIndex(ix); keep=[]; last=None
    for d in ix:
        if last is None or (d-last).days>gap: keep.append(d)
        last=d
    return pd.DatetimeIndex(keep)
print('=== BNK-01: BankNifty 21d return >=15% ===')
r21=(B/B.shift(21)-1)*100
FB, FN = fwd(B), fwd(N); EX = FB-FN
sig = r21[r21>=15].index; ep = episodes(sig)
print('days', len(sig), 'episodes', len(ep), [d.date().isoformat() for d in ep])
for nm,F in [('Bank abs',FB),('Bank-Nifty',EX),('Nifty abs',FN)]:
    e=F.loc[ep].dropna(how='all'); base=F.dropna(how='all')
    print(f'{nm}: ep', e.mean().round(2).to_dict(), '| %+', (e>0).mean().round(2).to_dict(), '| base', base.mean().round(2).to_dict())
# control: 12-15% (near miss) and excluding crash rebounds (Bank 250d drawdown >25% at signal)
dd=(B/B.rolling(250,min_periods=100).max()-1)*100
ep_nr=[d for d in ep if dd[d]>-25]; ep_r=[d for d in ep if dd[d]<=-25]
print('no-crash-rebound eps', len(ep_nr), FB.loc[ep_nr].mean().round(2).to_dict(), '| rebound eps', len(ep_r), FB.loc[ep_r].mean().round(2).to_dict())
print('today 21d', round(r21.iloc[-1],1), r21.index[-1].date(), 'max21 last month', round(r21.iloc[-25:].max(),1))
for era,(a,b) in {'2007-13':('2007','2013'),'2014-19':('2014','2019'),'2020-26':('2020','2026')}.items():
    e=[d for d in ep if a<=str(d.year)<=b]; print(' era',era,len(e),FB.loc[e].mean().round(2).to_dict())

print('\n=== BRD-02: Nifty <=-1% day but >=50% stocks up ===')
A = nc.load()['c']
ch = A.pct_change(fill_method=None); up=(ch>0).sum(axis=1); cnt=ch.notna().sum(axis=1)
adv=(up/cnt*100)[cnt>=150]
nr=(N/N.shift(1)-1)*100
df=pd.DataFrame({'nr':nr,'adv':adv}).dropna()
for h in (1,5,20): df[f'f{h}']=(N.shift(-h)/N-1).reindex(df.index)*100
big=df[df.nr<=-1].dropna()
pos=big[big.adv>=50]; neg=big[big.adv<30]; mid=big[(big.adv>=30)&(big.adv<50)]
for nm,x in [('adv>=50',pos),('adv30-50',mid),('adv<30',neg),('all -1% days',big)]:
    print(nm,'N',len(x), x[['f1','f5','f20']].mean().round(2).to_dict(), '%+ f5', round((x.f5>0).mean()*100), 'f20', round((x.f20>0).mean()*100))
print('all days base', df[['f1','f5','f20']].mean().round(2).to_dict())
for era,(a,b) in {'-2013':('2000','2013'),'2014-19':('2014','2019'),'2020-26':('2020','2026')}.items():
    x=pos[(pos.index.year>=int(a))&(pos.index.year<=int(b))]; y=neg[(neg.index.year>=int(a))&(neg.index.year<=int(b))]
    print(' era',era,'pos',len(x),x[['f5','f20']].mean().round(2).to_dict(),'| neg',len(y),y[['f5','f20']].mean().round(2).to_dict())
print('dates pos last 10', [d.date().isoformat() for d in pos.index[-10:]])
print('today', df.index[-1].date(), 'nr', round(df.nr.iloc[-1],2), 'adv', round(df.adv.iloc[-1],1))
