"""US-fade futures walk-forward (27 Nov 2026). Threshold har din sirf pichhle 5 saal ke S&P moves se (koi aage ka data nahi).
Nifty 65 + BankNifty 30 (aaj ke lot/level par Rs), 9:15 open se ulta, stop 1%, 15:15 band, cost Rs100 + 0.02%.
NATEEJA (Rs 10 lakh par): 1y +5.7%, 2y +29%, 3y +39%, 5y +52%, 10y +124%, 2010+ +185% (1468 saude, 47% jeet).
Par MAX GIRAVAT -54% (2020); ghaate ke saal 2010/16/17/20/23. VIX<=22/20 filter mila-jula (overfit khatra).
=> Niyam mein dam hai par 2 lot Rs10L ke liye bahut; position size asli faisla.
ANGLES (27 Nov raat, 2010-26 / 2016+ / Nov2023+ ; % = Rs10L par, dd = max giravat):
 stop 0.5%: Nifty +30/+27/+19 dd-26 | BankNifty +132/+73/+21 dd-31 | dono +162/+100/+39 dd-47
 stop 1.0%: Nifty +24/+29/+14 dd-28 | BankNifty +162/+95/+24 dd-36 | dono +186/+124/+39 dd-54  (abhi ka paper)
 stop 1.5%: Nifty  -8/+15/+11 dd-39 | BankNifty +182/+116/+19 dd-32 | dono +174/+131/+30 dd-63
 stop 2.0%: Nifty -22/ +5/+13 dd-54 | BankNifty +159/+97/+20 dd-40 | dono +137/+103/+33 dd-81
 => asli edge BANKNIFTY mein; Nifty akela kamzor (16 saal mein sirf +24%). Asli paisa ho to: sirf BankNifty 1 lot, stop 0.5-1%.
    Har ek lot par bhi -30% tak giravat aa chuki hai -> poonji ka chhota hissa. Paper niyam abhi nahi badla (tulna ke liye).
"""
import pandas as pd
rd=lambda p: pd.read_csv(p,parse_dates=['date']).drop_duplicates('date').set_index('date').sort_index()
us=rd('data/global/US_SP500.csv').close.dropna().pct_change().dropna()
res=[]
for sym,lot in (('BANKNIFTY',30),('NIFTY',65)):
    d=rd(f'data/{sym}.csv').dropna(subset=['open','close']); d=d[(d.open>0)&(d.high>=d.low)]
    now=float(d.close.iloc[-1])*lot
    for day,r in d.iterrows():
        if day<pd.Timestamp('2010-01-01'): continue
        prev=us[us.index<day]
        if (day-prev.index[-1]).days>4: continue
        h=prev[prev.index>=day-pd.Timedelta(days=1825)].iloc[:-1]; m=prev.iloc[-1]
        side=-1 if m>=h.quantile(.9) else (1 if m<=h.quantile(.1) else 0)
        if not side or abs(r.open-r.close)/r.open>0.15: continue
        stop=r.open*(1-0.01*side); hit=(side==1 and r.low<=stop) or (side==-1 and r.high>=stop)
        pct=side*((stop if hit else r.close)-r.open)/r.open
        res.append(dict(day=day,sym=sym,rs=pct*now-100-0.0002*now))
R=pd.DataFrame(res).sort_values('day')
for per,st in (('1y','2025-11-27'),('3y','2023-11-27'),('10y','2016-11-27'),('2010+','2010-01-01')):
    x=R[R.day>=st]; c=x.rs.cumsum()
    print(per,len(x),'jeet%',round(100*(x.rs>0).mean()),'Rs10L par %',round(x.rs.sum()/1e4,1),'max giravat %',round((c-c.cummax()).min()/1e4,1))
