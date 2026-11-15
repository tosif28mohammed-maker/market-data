# Intraday paper — hisaab aur seekh

Asli paisa nahi. Stocks kharcha 0.1%, options Rs 60/leg + 0.5 pt. Option bhaav andaza (BS + VIX).

## LIVE (asli din, robot ne us din chalaya): 4 din
```
           trades  win_pct  total_rs   avg_rs  avg_R
strat                                               
GAPBOUNCE     3.0     67.0    2711.0   903.67   0.95
GAPFADE       3.0     67.0     738.0   246.00   0.30
TRENDDAY      2.0    100.0    1622.0   811.00   0.90
USNIGHT       1.0    100.0    2079.0  2079.00   0.17
KUL           9.0     78.0    7150.0   794.44   0.64
```
Galtiyon ki ginti:
```
lesson
Nifty ulti disha mein chala                                      2
din bhar kuch nahi hua = setup kamzor                            2
target ke 75% tak gaya phir palta = trailing stop chahiye tha    1
```
## REPLAY (pichhle data par wahi niyam — shuruaati andaza): 59 din
```
           trades  win_pct  total_rs   avg_rs  avg_R
strat                                               
GAPBOUNCE    48.0     50.0    9911.0   206.48   0.46
GAPFADE      38.0     55.0    -688.0   -18.11   0.02
TRENDDAY     15.0     60.0    4031.0   268.73   0.35
USNIGHT       9.0     78.0   14502.0  1611.33   0.28
KUL         110.0     55.0   27756.0   252.33   0.28
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
## Aakhri din 2026-11-13

- GAPFADE PNGSREVA 09:30->12:15 TARGET: Rs +1,439 (+1.50R). gap +5.4%, pehle 15 min laal, Nifty gap -0.39%. 
- GAPBOUNCE YATRA 09:30->15:10 TIME: Rs +877 (+0.93R). gap -6.0%, pehle 15 min hara, Nifty gap -0.39%. 
