"""Claude's daily PAPER trading (no real money). Fixed rules decided in advance, filled only with data that came AFTER the decision.
Strategies (Hindi names in the report):
  EQ_DIP     equity swing: stock closes far below its 20-day EMA (its own 10% lowest distance since 2021, fresh) -> buy next open,
             SL 1.5 ATR, target = EMA20 of signal day, max 20 days. Rs 1,00,000 per trade, max 3 new/day, 6 open.
  FUT_DIP    Nifty futures (index as proxy) same dip rule, 1 lot (65).
  FUT_EXP    Nifty futures: buy at weekly expiry-day close (Tuesday), sell next day close (day-after-expiry effect).
  INTRA_ORB  Nifty intraday: 9:15-9:30 range; first 5-min close above/below -> long/short, SL other side, target 2x range, exit 15:15.
  OPT_SELL   naked short strangle at +-1 sigma (from VIX) for next weekly expiry, entered Tuesday close if 11 <= VIX <= 22, stop 2x credit.
  HEDGE_IC   same but iron condor (wings 300 points further): hedged option selling.
  OPT_BUY_EXP buy ATM call at Tuesday close, sell Wednesday close.
  OPT_BUY_DIP buy ATM call (expiry >= 7 days) when FUT_DIP fires; exit Nifty >= EMA20, -50% premium, or 5 days.
Options are priced with Black-Scholes using India VIX as volatility (estimate: real premiums differ, no skew).
Usage: python paper/engine.py [--start YYYY-MM-DD]   (state in paper/state.json; first run replays from --start)"""
import os, sys, json, math, datetime as dt
import numpy as np, pandas as pd
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); P=os.path.join(ROOT,'paper'); DATA=os.path.join(ROOT,'data')
LIVE_FROM='2026-10-29'; LOT=65; R=0.065; IST=dt.timezone(dt.timedelta(hours=5,minutes=30))
SYMS=[f[:-4] for f in os.listdir(DATA) if f.endswith('.csv') and f not in ('latest.csv',)]
STOCKS=[s for s in SYMS if s not in ('NIFTY','INDIAVIX')]
def load(s):
    d=pd.read_csv(os.path.join(DATA,f'{s}.csv'),parse_dates=['date']).dropna(subset=['close']).drop_duplicates('date').set_index('date').sort_index()
    return d[['open','high','low','close']]
DAY={s:load(s) for s in SYMS}
def intra(s):
    f=os.path.join(DATA,'intraday',f'{s}_5m.csv')
    if not os.path.exists(f): return {}
    x=pd.read_csv(f,parse_dates=['time']); x['d']=x.time.dt.normalize()
    return {k:g.sort_values('time') for k,g in x.groupby('d')}
INTRA={}
def bars(s,day):
    if s not in INTRA: INTRA[s]=intra(s)
    return INTRA[s].get(day)
# ---------- indicators (no look-ahead: value at date t uses data up to t) ----------
IND={}
def ind(s):
    if s in IND: return IND[s]
    d=DAY[s].copy(); c=d.close
    d['ema']=c.ewm(span=20,adjust=False).mean(); d['dist']=c/d.ema-1
    tr=pd.concat([d.high-d.low,(d.high-c.shift()).abs(),(d.low-c.shift()).abs()],axis=1).max(axis=1); d['atr']=tr.rolling(14).mean()
    e=d.dist.where(d.index>='2021-01-01'); d['thr']=e.expanding(min_periods=120).quantile(0.10)
    IND[s]=d; return d
def bs(S,K,T,vol,cp):
    if T<=0: return max(0.0,(S-K) if cp=='C' else (K-S))
    v=vol*math.sqrt(T); d1=(math.log(S/K)+(R+vol*vol/2)*T)/v; d2=d1-v; N=lambda x:0.5*(1+math.erf(x/math.sqrt(2)))
    return S*N(d1)-K*math.exp(-R*T)*N(d2) if cp=='C' else K*math.exp(-R*T)*N(-d2)-S*N(-d1)
def next_tuesday(day,min_days=1):
    t=day+pd.Timedelta(days=min_days)
    while t.dayofweek!=1: t+=pd.Timedelta(days=1)
    return t
def opt_val(legs,S,day,vix):
    return sum(q*bs(S,k,max((exp-day).days,0)/365,vix/100,cp) for (cp,k,q,exp) in legs)   # q>0 long, q<0 short (points)
# ---------- state ----------
SF=os.path.join(P,'state.json'); JF=os.path.join(P,'journal.csv')
state=json.load(open(SF)) if os.path.exists(SF) else {'last':None,'open':[],'pending':[],'seq':0}
journal=pd.read_csv(JF).to_dict('records') if os.path.exists(JF) else []
def nid(): state['seq']+=1; return f"T{state['seq']:05d}"
def close_pos(p,day,price,reason,pnl_rs):
    j=dict(p); j.update(exit_date=str(day.date()),exit_price=round(price,2),exit_reason=reason,pnl_rs=round(pnl_rs,0)); j.pop('legs',None)
    j['mode']='live' if j['entry_date']>=LIVE_FROM else 'replay'; journal.append(j); TODAY_CLOSED.append(j)
# ---------- dates ----------
nifty=DAY['NIFTY']; vixd=DAY['INDIAVIX'].close
dates=list(nifty.index); now=dt.datetime.now(IST)
if dates and dates[-1].date()==now.date() and (now.hour*60+now.minute)<16*60+30: dates=dates[:-1]   # today's row not final yet
start=pd.Timestamp(sys.argv[sys.argv.index('--start')+1]) if '--start' in sys.argv else pd.Timestamp(LIVE_FROM)
todo=[d for d in dates if (state['last'] is None and d>=start) or (state['last'] and d>pd.Timestamp(state['last']))]
REPORTS=[]
for day in todo:
    TODAY_CLOSED=[]; ix=dates.index(day); prev=dates[ix-1]
    S=float(nifty.close[day]); vix=float(vixd.get(day,vixd[:day].iloc[-1]))
    # 1) fill pending next-open orders
    for o in state['pending']:
        d=DAY[o['symbol']]
        if day not in d.index: continue
        px=float(d.open[day]); p=dict(o); p.update(entry_date=str(day.date()),entry_price=round(px,2),days=0)
        if o['strategy']=='EQ_DIP': p['qty']=int(100000//px)
        state['open'].append(p)
    state['pending']=[o for o in state['pending'] if o['symbol'] in DAY and day not in DAY[o['symbol']].index]
    # 2) manage swing positions (equity, FUT_DIP) with 5-min bars when available
    keep=[]
    for p in state['open']:
        st=p['strategy']
        if st in ('EQ_DIP','FUT_DIP'):
            d=DAY[p['symbol']]
            if day not in d.index: keep.append(p); continue
            p['days']+=1; done=None
            b=bars(p['symbol'],day)
            path=[(r.high,r.low) for r in b.itertuples()] if b is not None and len(b) else [(float(d.high[day]),float(d.low[day]))]
            for hi,lo in path:
                if lo<=p['sl']: done=(p['sl'],'SL'); break      # if both in one bar, SL first (conservative)
                if hi>=p['target']: done=(p['target'],'Target'); break
            if not done and p['days']>=20: done=(float(d.close[day]),'20 दिन')
            if done:
                q=p['qty']; cost=0.0025*q*p['entry_price'] if st=='EQ_DIP' else 100
                close_pos(p,day,done[0],done[1],(done[0]-p['entry_price'])*q-cost)
            else: keep.append(p)
        elif st=='FUT_EXP':
            close_pos(p,day,S,'अगले दिन close',(S-p['entry_price'])*LOT-100)
        elif st in ('OPT_SELL','HEDGE_IC','OPT_BUY_EXP','OPT_BUY_DIP'):
            legs=[tuple(l[:2])+(l[2],pd.Timestamp(l[3])) for l in p['legs']]; val=opt_val(legs,S,day,vix)   # current value (points, + = we own)
            pnl_pts=val-p['entry_val']; p['days']+=1; exp=pd.Timestamp(p['expiry']); reason=None
            if day>=exp: reason='Expiry'
            elif st in ('OPT_SELL','HEDGE_IC') and pnl_pts<=-2*abs(p['entry_val']): reason='SL 2x'
            elif st=='OPT_BUY_EXP': reason='अगले दिन close'
            elif st=='OPT_BUY_DIP':
                if pnl_pts<=-0.5*p['entry_val']: reason='SL -50%'
                elif S>=float(ind('NIFTY').ema[day]): reason='Nifty EMA20 छुआ'
                elif p['days']>=5: reason='5 दिन'
            if reason: close_pos(p,day,val,reason,pnl_pts*LOT-60*len(legs))
            else: p['mark']=round(pnl_pts*LOT,0); keep.append(p)
        else: keep.append(p)
    state['open']=keep
    # 3) intraday ORB on Nifty (rule fixed in advance, evaluated on today's 5-min bars)
    b=bars('NIFTY',day)
    if b is not None and len(b)>=20:
        b=b[(b.time.dt.time>=dt.time(9,15))&(b.time.dt.time<dt.time(15,30))]
        orb=b[b.time.dt.time<dt.time(9,30)]; rest=b[b.time.dt.time>=dt.time(9,30)]
        if len(orb)>=3 and len(rest):
            H,Lw=orb.high.max(),orb.low.min(); rng=H-Lw; pos=None
            for r in rest.itertuples():
                t=r.time.time()
                if pos is None and t<dt.time(14,30):
                    if r.close>H: pos=dict(side=1,entry=r.close,sl=Lw,tg=r.close+2*rng,time=t)
                    elif r.close<Lw: pos=dict(side=-1,entry=r.close,sl=H,tg=r.close-2*rng,time=t)
                    continue
                if pos:
                    if (pos['side']==1 and r.low<=pos['sl']) or (pos['side']==-1 and r.high>=pos['sl']): ex,why=pos['sl'],'SL'
                    elif (pos['side']==1 and r.high>=pos['tg']) or (pos['side']==-1 and r.low<=pos['tg']): ex,why=pos['tg'],'Target'
                    elif t>=dt.time(15,15): ex,why=r.close,'15:15 बंद'
                    else: continue
                    p=dict(id=nid(),strategy='INTRA_ORB',symbol='NIFTY',side='Long' if pos['side']==1 else 'Short',qty=LOT,entry_date=str(day.date()),
                           entry_price=round(pos['entry'],2),sl=round(pos['sl'],2),target=round(pos['tg'],2),note=f"entry {pos['time']}, range {rng:.0f}")
                    close_pos(p,day,ex,why,pos['side']*(ex-pos['entry'])*LOT-100); break
    # 4) new positions at today's close
    is_exp=day.dayofweek==1
    if is_exp:
        state['open'].append(dict(id=nid(),strategy='FUT_EXP',symbol='NIFTY',side='Long',qty=LOT,entry_date=str(day.date()),entry_price=round(S,2),sl=None,target=None,days=0,note='expiry-day close'))
        nexp=next_tuesday(day); T=(nexp-day).days/365
        atm=round(S/50)*50; prem=bs(S,atm,T,vix/100,'C')
        state['open'].append(dict(id=nid(),strategy='OPT_BUY_EXP',symbol=f'NIFTY {atm} CE',side='Buy',qty=LOT,entry_date=str(day.date()),entry_price=round(prem,2),entry_val=prem,
            legs=[('C',atm,1,str(nexp.date()))],expiry=str(nexp.date()),days=0,sl=None,target=None,note=f'VIX {vix:.1f}'))
        if 11<=vix<=22:
            sig=S*vix/100*math.sqrt(7/365); ck=math.ceil((S+sig)/50)*50; pk=math.floor((S-sig)/50)*50
            for st,legs in (('OPT_SELL',[('C',ck,-1,nexp),('P',pk,-1,nexp)]),('HEDGE_IC',[('C',ck,-1,nexp),('P',pk,-1,nexp),('C',ck+300,1,nexp),('P',pk-300,1,nexp)])):
                v=opt_val(legs,S,day,vix)
                state['open'].append(dict(id=nid(),strategy=st,symbol=f'NIFTY {pk}PE/{ck}CE'+(' +wings' if st=='HEDGE_IC' else ''),side='Sell',qty=LOT,entry_date=str(day.date()),
                    entry_price=round(-v,2),entry_val=v,legs=[(a,k,q,str(e.date())) for a,k,q,e in legs],expiry=str(nexp.date()),days=0,sl=None,target=None,note=f'credit {-v:.1f} pts, VIX {vix:.1f}'))
    # dip signals (equity + Nifty) -> pending for next open
    held={p['symbol'] for p in state['open']}|{o['symbol'] for o in state['pending']}
    cands=[]
    for s in STOCKS+['NIFTY']:
        d=ind(s)
        if day not in d.index: continue
        i=d.index.get_loc(day)
        if i<1: continue
        x=d.iloc[i]; y=d.iloc[i-1]
        if pd.notna(x.thr) and x.dist<=x.thr and y.dist>x.thr and pd.notna(x.atr): cands.append((x.dist/x.thr,s,x))
    cands.sort(key=lambda c:-c[0]); n_eq=sum(1 for p in state['open'] if p['strategy']=='EQ_DIP'); new=0
    for _,s,x in cands:
        if s in held: continue
        if s=='NIFTY':
            state['pending'].append(dict(id=nid(),strategy='FUT_DIP',symbol='NIFTY',side='Long',qty=LOT,signal_date=str(day.date()),sl=round(x.close-1.5*x.atr,2),target=round(x.ema,2),note=f'dist {x.dist*100:.1f}%'))
            nexp=next_tuesday(day,7); atm=round(S/50)*50; prem=bs(S,atm,(nexp-day).days/365,vix/100,'C')
            state['open'].append(dict(id=nid(),strategy='OPT_BUY_DIP',symbol=f'NIFTY {atm} CE',side='Buy',qty=LOT,entry_date=str(day.date()),entry_price=round(prem,2),entry_val=prem,
                legs=[('C',atm,1,str(nexp.date()))],expiry=str(nexp.date()),days=0,sl=None,target=None,note=f'VIX {vix:.1f}'))
        elif n_eq+new<6 and new<3:
            state['pending'].append(dict(id=nid(),strategy='EQ_DIP',symbol=s,side='Buy',qty=0,signal_date=str(day.date()),sl=round(x.close-1.5*x.atr,2),target=round(x.ema,2),note=f'dist {x.dist*100:.1f}% (limit {x.thr*100:.1f}%)'))
            new+=1
    state['last']=str(day.date()); REPORTS.append((day,TODAY_CLOSED,S,vix))
# ---------- save ----------
J=pd.DataFrame(journal); J.to_csv(JF,index=False)
json.dump(state,open(SF,'w'),ensure_ascii=False,indent=1,default=str)
NAME={'EQ_DIP':'Equity swing (dip)','FUT_DIP':'Nifty future (dip)','FUT_EXP':'Nifty future (expiry के बाद)','INTRA_ORB':'Intraday Nifty ORB',
      'OPT_SELL':'Option sell (naked strangle)','HEDGE_IC':'Hedge: Iron condor','OPT_BUY_EXP':'Option buy (expiry के बाद CE)','OPT_BUY_DIP':'Option buy (dip CE)'}
def summary(J):
    rows=[]
    for st in NAME:
        x=J[J.strategy==st] if len(J) else J
        if not len(x): rows.append(dict(strategy=NAME[st],trades=0)); continue
        eq=x.pnl_rs.cumsum(); dd=(eq-eq.cummax()).min()
        rows.append(dict(strategy=NAME[st],trades=len(x),win_pct=round((x.pnl_rs>0).mean()*100),pnl_rs=int(x.pnl_rs.sum()),avg_rs=int(x.pnl_rs.mean()),
                         best=int(x.pnl_rs.max()),worst=int(x.pnl_rs.min()),max_dd=int(dd)))
    return pd.DataFrame(rows)
if len(J):
    for mode in ('replay','live'):
        summary(J[J['mode']==mode]).to_csv(os.path.join(P,f'summary_{mode}.csv'),index=False)
os.makedirs(os.path.join(P,'reports'),exist_ok=True)
for day,closed,S,vix in REPORTS[-5:]:
    L=[f'# Paper trading रिपोर्ट {day.date()} (कोई असली पैसा नहीं)',f'Nifty {S:.0f}, VIX {vix:.2f}','','## आज बंद हुए trade']
    L+=[f"- {NAME[c['strategy']]}: {c['symbol']} {c['side']} {c['entry_price']} -> {c['exit_price']} ({c['exit_reason']}) = Rs {c['pnl_rs']:+,.0f}" for c in closed] or ['- कोई नहीं']
    L+=['','## खुले trade']+([f"- {NAME[p['strategy']]}: {p['symbol']} {p['side']} @ {p['entry_price']} (SL {p.get('sl')}, target {p.get('target')}, अभी Rs {p.get('mark','-')})" for p in state['open']] or ['- कोई नहीं'])
    L+=['','## कल open पर (pending)']+([f"- {NAME[o['strategy']]}: {o['symbol']} खरीद, SL {o['sl']}, target {o['target']} ({o['note']})" for o in state['pending']] or ['- कोई नहीं'])
    open(os.path.join(P,'reports',f'{day.date()}.md'),'w').write('\n'.join(L)+'\n')
print('processed',len(todo),'days; last',state['last'],'; journal',len(J),'; open',len(state['open']),'; pending',len(state['pending']))
if len(J): print(summary(J[J['mode']=='replay']).to_string(index=False)); print(summary(J[J['mode']=='live']).to_string(index=False))
