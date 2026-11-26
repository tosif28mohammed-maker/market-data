import pandas as pd, numpy as np, sys
sys.path.insert(0,'study'); import ni_common as nc
P=nc.load(); o,h,l,a,v=[P[k] for k in 'ohlav']; c=a
F,_=nc.fwd(P,(5,20))
po,pc=o.shift(1),c.shift(1)
eng=(pc>po)&(c<o)&(o>=pc)&(c<=po)&((o-c)>(pc-po))
hi60=h.shift(1).rolling(60).max(); res=h>=hi60*0.98
vr=v/v.shift(1).rolling(20).mean(); liq=(c*v).rolling(20).mean()>2e7
for g,ev in {'bear+res+hiVol':eng&res&liq&(vr>1.5),'bear+res+lowVol':eng&res&liq&(vr<1),'bear anywhere':eng&liq}.items():
    ev=nc.thin(ev.fillna(False),10)
    for r in nc.evaluate(ev,F,g,hs=(5,20)):
        if r['era'] in('ALL','2003-12','2013-20','2021-26') and 'excess' in r: print(g,r['h'],r['era'],r['n'],'ex',r['excess'],'raw',r['raw'],'t',r['t_dates'])
