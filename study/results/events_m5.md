# Event/jhatka study — m5

## 5m UP झटका (ALL)
```
                              kind     n  up1_%  up2_%  up3_%  exc1  exc3  exc5  exc20  run_med  run_p90  run_max  run>=2_%  best20_med  best20_p90  worst20_med  to_peak_med
           PLACEBO ordinary candle 91515   39.7   40.9   41.6 -0.02 -0.02 -0.02  -0.03      0.0      2.0       15      15.3        0.51        2.20        -0.61          8.0
               own shock, entry E0 55006   36.8   37.4   37.7 -0.12 -0.14 -0.15  -0.20      0.0      2.0       14      15.2        0.65        2.90        -0.99          6.0
   own shock + volume 2x, entry E0 46984   37.3   37.7   37.9 -0.11 -0.13 -0.15  -0.20      0.0      2.0       14      15.3        0.67        2.96        -0.98          6.0
               own shock, entry E1 55006   43.7   44.0   43.8 -0.01 -0.02 -0.04  -0.08      0.0      2.0       13      18.1        0.70        2.87        -0.83          6.0
            market shock, entry E0 17061   42.6   45.7   44.5 -0.06 -0.05 -0.06  -0.08      0.0      2.0       12      20.1        0.72        2.79        -0.80          6.0
market shock + volume 2x, entry E0  5031   41.8   43.5   44.0 -0.06 -0.05 -0.07  -0.09      0.0      2.0       10      18.7        0.73        2.78        -0.81          6.0
            market shock, entry E1 17061   49.7   48.7   48.5  0.00  0.00 -0.01  -0.03      0.0      2.0       11      20.6        0.73        2.62        -0.71          6.0
```
## 5m DOWN झटका (ALL)
```
                              kind     n  up1_%  up2_%  up3_%  exc1  exc3  exc5  exc20  run_med  run_p90  run_max  run>=2_%  best20_med  best20_p90  worst20_med  to_peak_med
           PLACEBO ordinary candle 84584   49.3   49.0   48.6  0.01  0.01  0.01   0.01      0.0      2.0       13      19.5        0.58        1.91        -0.55         11.0
               own shock, entry E0 38978   58.1   58.2   57.6  0.13  0.15  0.15   0.17      0.0      2.0       12      17.0        0.61        2.23        -0.85          9.0
   own shock + volume 2x, entry E0 30221   59.4   59.5   58.3  0.14  0.15  0.16   0.18      0.0      2.0       12      16.2        0.63        2.31        -0.89          9.0
               own shock, entry E1 38978   48.6   49.3   49.1  0.01  0.01  0.03   0.04      0.0      2.0       13      21.1        0.69        2.27        -0.70          9.0
            market shock, entry E0 15262   45.5   45.1   46.2  0.06  0.06  0.06   0.07      1.0      3.0       12      25.9        0.83        2.54        -0.70          8.0
market shock + volume 2x, entry E0  5429   49.3   47.8   52.2  0.06  0.06  0.06   0.08      0.0      3.0       10      24.3        0.66        2.06        -0.81          7.0
            market shock, entry E1 15262   45.9   47.1   45.9 -0.00  0.00  0.01   0.01      1.0      3.0       15      22.1        0.75        2.41        -0.67          9.0
```
Per-stock half1 vs half2 (own shock, 5 candle excess):
```
tf  dir  stocks  corr_half1_half2  chance_corr_p95  both_positive  expected_by_chance
5m   UP    1628             0.210            0.042            172               145.0
5m DOWN    1623             0.286            0.038            791               759.8
```