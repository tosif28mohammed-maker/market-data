# Option bechne ki strategies — asli NSE bhaav (2010-2026, 29,181,612 rows)

## INDEX (Nifty/BankNifty)
```
                                trades  win_pct       avg_ror  median_ror  worst_ror  stops_pct  rs_lot_avg
symbol    strat            k                                                                               
BANKNIFTY BEAR CALL SPREAD 1.0  1603.0     81.0  1.398409e+10        5.14     -100.1       10.0        60.0
                           1.5  1579.0     87.0  2.800000e-01        2.04     -100.0       10.0        52.0
          BULL PUT SPREAD  1.0  1607.0     83.0  3.439513e+10        8.15     -101.6        9.0       374.0
                           1.5  1595.0     87.0  1.230000e+00        4.07     -100.0        9.0       213.0
          IRON CONDOR      1.0  1608.0     73.0  5.616479e+10       11.36     -100.8        7.0       272.0
                           1.5  1594.0     83.0  1.380000e+00        5.57     -100.2        8.0       274.0
FINNIFTY  BEAR CALL SPREAD 1.0   624.0     85.0  2.020000e+00        4.30     -102.8        8.0         NaN
                           1.5   595.0     90.0  2.000000e+00        1.87     -100.0        7.0         NaN
          BULL PUT SPREAD  1.0   640.0     87.0  6.669095e+10        7.46     -148.3        9.0         NaN
                           1.5   629.0     89.0  2.510000e+00        3.47     -100.1        9.0         NaN
          IRON CONDOR      1.0   649.0     79.0  7.149985e+10        9.94     -108.2        6.0         NaN
                           1.5   636.0     86.0  4.330000e+00        4.85     -100.3        7.0         NaN
NIFTY     BEAR CALL SPREAD 1.0  1497.0     84.0 -2.200000e-01        2.13     -100.0       11.0       -57.0
                           1.5  1270.0     84.0  6.022693e+09        0.53      -73.2       14.0        11.0
          BULL PUT SPREAD  1.0  1521.0     84.0  6.319599e+09        4.44     -100.2       10.0       136.0
                           1.5  1490.0     88.0  3.300000e-01        1.76     -100.0       10.0        82.0
          IRON CONDOR      1.0  1521.0     78.0  7.800000e-01        6.01     -100.6        9.0        32.0
                           1.5  1477.0     85.0  1.170000e+00        2.13     -100.0       11.0        65.0
```
Daur-war (avg return on risk %, sab k/dte):
```
era               2010-12       2013-20       2021-23  2024-26
strat                                                         
BEAR CALL SPREAD     0.69  1.192122e+10  9.600000e-01     0.11
BULL PUT SPREAD     -0.62  2.442043e+10  1.574408e+10     0.25
IRON CONDOR         -0.97  3.410611e+10  1.704128e+10     0.06
```
Trend ke hisaab se (spread sahi taraf?):
```
                        trades  win_pct       avg_ror  worst_ror
strat            trend                                          
BEAR CALL SPREAD down   1107.0     82.0  2.715928e+10     -100.1
                 mixed  2640.0     85.0  4.400000e-01     -102.8
                 up     3421.0     85.0  7.400000e-01     -100.1
BULL PUT SPREAD  down   1116.0     83.0  5.814076e+10     -101.6
                 mixed  2709.0     84.0  1.575571e+10     -148.3
                 up     3657.0     88.0  1.880000e+00     -100.4
IRON CONDOR      down   1117.0     75.0  8.085316e+10     -100.8
                 mixed  2710.0     79.0  1.712303e+10     -108.2
                 up     3658.0     82.0  2.310000e+00     -100.5
```

## SHARES (F&O stocks, monthly)
```
                           trades  win_pct       avg_ror  median_ror     worst_ror  stops_pct  rs_lot_avg
strat            k   dte                                                                                 
BEAR CALL SPREAD 1.0 8    30647.0     76.0  1.757725e+07        7.71 -2.509000e+02       20.0         NaN
                     15   27310.0     73.0 -3.061076e+07        9.85 -8.359800e+11       24.0         NaN
                 1.5 8    24760.0     78.0  5.068013e+07        4.15 -2.079000e+02       21.0         NaN
                     15   18239.0     73.0  6.832776e+07        5.59 -6.644000e+02       25.0         NaN
BULL PUT SPREAD  1.0 8    30587.0     71.0  1.308880e+08        6.79 -2.634000e+02       24.0         NaN
                     15   27501.0     68.0  4.627468e+07        8.65 -3.063000e+02       28.0         NaN
                 1.5 8    24409.0     74.0  5.871400e+07        3.43 -2.086000e+02       23.0         NaN
                     15   18178.0     69.0  1.880807e+08        4.44 -3.026000e+02       29.0         NaN
IRON CONDOR      1.0 8    31050.0     71.0  4.263198e+08       12.50 -1.831000e+02        5.0         NaN
                     15   27771.0     68.0  2.375835e+08       15.86 -2.870000e+02        3.0         NaN
                 1.5 8    25141.0     80.0  3.152369e+08        7.22 -2.297000e+02        5.0         NaN
                     15   18584.0     77.0  6.264373e+08        9.84 -2.062000e+02        4.0         NaN
```
Daur-war (avg return on risk %, sab k/dte):
```
era                    2010-12       2013-20       2021-23      2024-26
strat                                                                  
BEAR CALL SPREAD  7.300000e-01  6.559027e+06  1.979116e+07  64244552.65
BULL PUT SPREAD   7.972254e+07  1.567220e+08  6.778367e+07  37924933.79
IRON CONDOR       7.381440e+08  3.302644e+08  6.956902e+08        -1.16
```
Trend ke hisaab se (spread sahi taraf?):
```
                         trades  win_pct       avg_ror     worst_ror
strat            trend                                              
BEAR CALL SPREAD down   24431.0     75.0  6.200000e-01 -2.817000e+02
                 mixed  39628.0     75.0  3.144822e+07 -3.491000e+02
                 up     36897.0     76.0  2.595198e+07 -8.359800e+11
BULL PUT SPREAD  down   24223.0     68.0  2.284659e+08 -3.026000e+02
                 mixed  39463.0     71.0  8.009706e+07 -3.063000e+02
                 up     36989.0     72.0  3.874530e+07 -1.873000e+02
IRON CONDOR      down   24781.0     71.0  3.268302e+08 -2.870000e+02
                 mixed  40261.0     73.0  4.741345e+08 -1.807000e+02
                 up     37504.0     75.0  3.256701e+08 -2.062000e+02
```

## Index: "shaant" ishaare (regime score) ke saath — 2018 ke baad (rule 2008-17 se chuna)
```
                             trades  win_pct       avg_ror  worst_ror  rs_lot_avg
strat            qs                                                              
BEAR CALL SPREAD 0           1586.0     85.0  1.895670e+10     -102.1        99.0
                 1 ishaara   1353.0     86.0  6.500000e-01     -100.1       126.0
                 2+ ishaare  2795.0     86.0  5.400000e-01     -102.8       -33.0
BULL PUT SPREAD  0           1623.0     84.0  6.627683e+10     -101.6       115.0
                 1 ishaara   1416.0     87.0  2.200000e+00     -148.3       376.0
                 2+ ishaare  2944.0     87.0  1.900000e+00     -100.4       281.0
IRON CONDOR      0           1622.0     80.0  8.428877e+10     -100.8       303.0
                 1 ishaara   1417.0     82.0  2.670000e+00     -108.2       471.0
                 2+ ishaare  2948.0     81.0  1.970000e+00     -102.8       110.0
```
