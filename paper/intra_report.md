# Intraday paper — hisaab aur seekh

Asli paisa nahi. Stocks kharcha 0.1%, options Rs 60/leg + 0.5 pt. Option bhaav andaza (BS + VIX).

## LIVE (asli din, robot ne us din chalaya): 5 din
```
           trades  win_pct  total_rs   avg_rs  avg_R
strat                                               
GAPBOUNCE       4       50    1821.0   455.25   0.46
GAPFADE         4       50    -287.0   -71.75  -0.02
TRENDDAY        2      100    1622.0   811.00   0.90
USNIGHT         1      100    2079.0  2079.00   0.17
KUL            11       64    5235.0   475.91   0.34
```
Galtiyon ki ginti:
```
lesson
Nifty ulti disha mein chala                                      3
din bhar kuch nahi hua = setup kamzor                            2
target ke 75% tak gaya phir palta = trailing stop chahiye tha    1
stop 15 min mein = entry jaldi/galat jagah                       1
```
Discipline niyam ki jaanch (base vs har niyam; jo base se behtar ho wahi rakhenge):
```
                                                 trades  total_rs  win_pct  sabse_bura
niyam                                                                                 
Bina niyam (base)                                    11    5235.0     64.0     -1064.0
D1 din mein 2 haar ya -Rs2,000 -> band (akela)       11    5235.0     64.0     -1064.0
D2 R:R >= 1.5 warna skip (akela)                     10    6260.0     70.0     -1064.0
D3 +1R ke baad stop entry par (akela)                11    5235.0     64.0     -1064.0
D4 Nifty ki disha ke khilaaf entry nahi (akela)      11    5235.0     64.0     -1064.0
D5 din +Rs3,000 -> band (lalach nahi) (akela)        11    5235.0     64.0     -1064.0
SAB niyam ek saath                                   10    6260.0     70.0     -1064.0
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
## Aakhri din 2026-11-16

- GAPFADE MARSONS 09:30->09:45 STOP: Rs -1,025 (-1.00R). gap +5.1%, pehle 15 min laal, Nifty gap +0.25%. Seekh: stop 15 min mein = entry jaldi/galat jagah; Nifty ulti disha mein chala
- GAPBOUNCE NEPHROPLUS 09:30->10:30 STOP: Rs -890 (-1.00R). gap -3.5%, pehle 15 min hara, Nifty gap +0.25%. 
