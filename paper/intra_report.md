# Intraday paper — hisaab aur seekh

Asli paisa nahi. Stocks kharcha 0.1%, options Rs 60/leg + 0.5 pt. Option bhaav andaza (BS + VIX).

## LIVE (asli din, robot ne us din chalaya): 10 din
```
           trades  win_pct  total_rs   avg_rs  avg_R
strat                                               
GAPBOUNCE       8       38    2475.0   309.38   0.36
GAPFADE         5       40   -1039.0  -207.80  -0.17
TRENDDAY        3      100    3017.0  1005.67   1.10
USNIGHT         5       40    6821.0  1364.20  -0.08
KUL            21       48   11274.0   536.86   0.23
```
Galtiyon ki ginti:
```
lesson
Nifty ulti disha mein chala                                      5
din bhar kuch nahi hua = setup kamzor                            5
target ke 75% tak gaya phir palta = trailing stop chahiye tha    1
stop 15 min mein = entry jaldi/galat jagah                       1
disha sahi thi par option ka time decay/IV kha gaya              1
```
Discipline niyam ki jaanch (base vs har niyam; jo base se behtar ho wahi rakhenge):
```
                                                 trades  total_rs  win_pct  sabse_bura
niyam                                                                                 
Bina niyam (base)                                    21   11274.0     48.0     -3670.0
D1 din mein 2 haar ya -Rs2,000 -> band (akela)       21   11274.0     48.0     -3670.0
D2 R:R >= 1.5 warna skip (akela)                     18   14098.0     56.0     -3670.0
D3 +1R ke baad stop entry par (akela)                21   11274.0     48.0     -3670.0
D4 Nifty ki disha ke khilaaf entry nahi (akela)      19   11474.0     53.0     -3670.0
D5 din +Rs3,000 -> band (lalach nahi) (akela)        21   11274.0     48.0     -3670.0
SAB niyam ek saath                                   16   14298.0     62.0     -3670.0
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
## Aakhri din 2026-11-23

- GAPBOUNCE VERANDA 09:30->15:10 TIME: Rs -100 (+0.00R). gap -5.0%, pehle 15 min hara, Nifty gap +0.50%. Seekh: Nifty ulti disha mein chala; din bhar kuch nahi hua = setup kamzor
- USNIGHT NIFTY 25600CE 23Nov 10:20->13:05 STOP: Rs -3,670 (-0.99R). S&P raat -3.7% -> 10:15 ke baad Nifty sambhalta (f54). 
- TRENDDAY FCL 10:20->15:10 TIME: Rs +1,395 (+1.48R). 10:15 tak Nifty -1.20%, 15% core shares open se upar; sabse mazboot FCL -3.2%. 
