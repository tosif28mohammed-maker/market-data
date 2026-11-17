# Intraday paper — hisaab aur seekh

Asli paisa nahi. Stocks kharcha 0.1%, options Rs 60/leg + 0.5 pt. Option bhaav andaza (BS + VIX).

## LIVE (asli din, robot ne us din chalaya): 6 din
```
           trades  win_pct  total_rs  avg_rs  avg_R
strat                                              
GAPBOUNCE       5       40     774.0  154.80   0.17
GAPFADE         5       40   -1039.0 -207.80  -0.17
TRENDDAY        2      100    1622.0  811.00   0.90
USNIGHT         2       50     846.0  423.00  -0.15
KUL            14       50    2203.0  157.36   0.11
```
Galtiyon ki ginti:
```
lesson
Nifty ulti disha mein chala                                      4
din bhar kuch nahi hua = setup kamzor                            2
target ke 75% tak gaya phir palta = trailing stop chahiye tha    1
stop 15 min mein = entry jaldi/galat jagah                       1
disha sahi thi par option ka time decay/IV kha gaya              1
```
Discipline niyam ki jaanch (base vs har niyam; jo base se behtar ho wahi rakhenge):
```
                                                 trades  total_rs  win_pct  sabse_bura
niyam                                                                                 
Bina niyam (base)                                    14    2203.0     50.0     -1233.0
D1 din mein 2 haar ya -Rs2,000 -> band (akela)       14    2203.0     50.0     -1233.0
D2 R:R >= 1.5 warna skip (akela)                     11    5027.0     64.0     -1233.0
D3 +1R ke baad stop entry par (akela)                14    2203.0     50.0     -1233.0
D4 Nifty ki disha ke khilaaf entry nahi (akela)      14    2203.0     50.0     -1233.0
D5 din +Rs3,000 -> band (lalach nahi) (akela)        14    2203.0     50.0     -1233.0
SAB niyam ek saath                                   11    5027.0     64.0     -1233.0
```
## REPLAY (pichhle data par wahi niyam — shuruaati andaza): 59 din
```
           trades  win_pct  total_rs   avg_rs  avg_R
strat                                               
GAPBOUNCE      48       50    9911.0   206.48   0.46
GAPFADE        38       55    -688.0   -18.11   0.02
TRENDDAY       15       60    4031.0   268.73   0.35
USNIGHT         9       78   14502.0  1611.33   0.28
KUL           110       55   27756.0   252.33   0.28
```
Galtiyon ki ginti:
```
lesson
din bhar kuch nahi hua = setup kamzor                            22
Nifty ulti disha mein chala                                      13
target ke 75% tak gaya phir palta = trailing stop chahiye tha    10
stop 15 min mein = entry jaldi/galat jagah                        9
```
Discipline niyam ki jaanch (base vs har niyam; jo base se behtar ho wahi rakhenge):
```
                                                 trades  total_rs  win_pct  sabse_bura
niyam                                                                                 
Bina niyam (base)                                   110   27756.0     55.0     -3229.0
D1 din mein 2 haar ya -Rs2,000 -> band (akela)      110   27756.0     55.0     -3229.0
D2 R:R >= 1.5 warna skip (akela)                     72   28132.0     56.0     -3229.0
D3 +1R ke baad stop entry par (akela)               110   24321.0     49.0     -3229.0
D4 Nifty ki disha ke khilaaf entry nahi (akela)      91   26856.0     57.0     -3229.0
D5 din +Rs3,000 -> band (lalach nahi) (akela)       110   27756.0     55.0     -3229.0
SAB niyam ek saath                                   60   21633.0     48.0     -3229.0
```
## Aakhri din 2026-11-17

- GAPFADE TATAINVEST 09:30->15:10 TIME: Rs -752 (-0.73R). gap +4.4%, pehle 15 min laal, Nifty gap +0.13%. Seekh: Nifty ulti disha mein chala
- GAPBOUNCE HFCL 09:30->10:15 STOP: Rs -1,047 (-1.00R). gap -3.2%, pehle 15 min hara, Nifty gap +0.13%. 
- USNIGHT NIFTY 25400CE 17Nov 10:20->15:10 TIME: Rs -1,233 (-0.48R). S&P raat -1.9% -> 10:15 ke baad Nifty sambhalta (f54). Seekh: disha sahi thi par option ka time decay/IV kha gaya
