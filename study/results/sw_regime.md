# Sideways / shaant bazaar — kab? (Nifty 2008-26)
Shaant (5 din) = agle 5 din Nifty ka high/low aaj ke close se +-2% ke andar (iron condor +-2% bach jaata). Shaant (1 din) = agle din range < 0.8%.

### nifty_5d: base P(shaant) = 38.8% (4520 din)
Sabse shaant halaat (dono aadhe mein sahi = holds):
```
                            feature     level    n  p_quiet  lift  first_half  second_half  holds
                                VIX       <12  419     72.6  1.87        86.2         70.1   True
                   10d realised vol sabse kam  936     60.6  1.56        60.6         60.6   True
                                VIX     12-14  715     57.5  1.48        55.7         58.0   True
                                VIX     14-16  803     53.7  1.39        50.4         56.2   True
                   10d realised vol       kam  936     51.4  1.33        48.6         53.1   True
                          20 DMA se     +1..3 1256     50.5  1.30        45.4         54.6   True
                       aaj ki chaal     <0.3% 1299     46.0  1.19        38.8         52.0  False
Bollinger squeeze (20% sabse patla)      haan 1067     45.3  1.17        34.0         57.5  False
                       aaj ki chaal   0.3-0.8 1542     43.3  1.12        34.0         50.4  False
                          20 DMA se      +-1% 1362     42.6  1.10        32.8         49.9  False
                       VIX 5d badla      flat 1867     42.8  1.10        35.2         50.1  False
                     expiry tak din      6-10 1106     42.0  1.08        34.7         49.0  False
                            tareekh       1-3  425     40.7  1.05        32.2         48.8  False
                     results season      haan 1765     40.4  1.04        31.0         49.1  False
```
Sabse kam shaant (yahan option bechna khatarnaak):
```
         feature       level   n  p_quiet  lift  first_half  second_half  holds
             VIX         30+ 432      2.3  0.06         2.4          1.6   True
10d realised vol sabse zyada 820     10.2  0.26         6.3         19.6   True
       20 DMA se        -3%+ 456     10.7  0.28         8.4         15.8   True
             VIX       22-30 642     16.2  0.42        14.5         19.6   True
    aaj ki chaal       >1.5% 671     18.5  0.48        15.2         25.0   True
    VIX 5d badla       +15%+ 383     23.8  0.61        18.2         30.5   True
             VIX       18-22 851     28.6  0.74        29.4         27.6   True
10d realised vol       zyada 897     28.9  0.74        23.5         37.1  False
```

### nifty_1d: base P(shaant) = 29.8% (4520 din)
Sabse shaant halaat (dono aadhe mein sahi = holds):
```
                            feature     level    n  p_quiet  lift  first_half  second_half  holds
                                VIX       <12  419     66.3  2.22        66.2         66.4   True
                   10d realised vol sabse kam  936     55.4  1.86        48.1         58.0   True
                                VIX     12-14  715     54.5  1.83        53.8         54.8   True
                          20 DMA se     +1..3 1256     43.9  1.47        32.6         53.2  False
                   10d realised vol       kam  936     40.0  1.34        34.4         43.3  False
                                VIX     14-16  803     38.7  1.30        41.4         36.6   True
                       aaj ki chaal     <0.3% 1299     37.3  1.25        27.8         45.1  False
Bollinger squeeze (20% sabse patla)      haan 1067     36.7  1.23        26.6         47.7  False
                       aaj ki chaal   0.3-0.8 1542     36.6  1.23        27.8         43.5  False
  NR7 (7 din ki sabse chhoti range)      haan  711     35.7  1.20        22.2         48.0  False
                          20 DMA se      +-1% 1362     35.6  1.19        28.1         41.2  False
                       VIX 5d badla   -5..-15 1104     35.1  1.18        23.9         45.4  False
                                din       Tue  910     33.3  1.12        25.9         40.5  False
                       VIX 5d badla      flat 1867     32.9  1.10        25.3         40.2  False
```
Sabse kam shaant (yahan option bechna khatarnaak):
```
         feature       level   n  p_quiet  lift  first_half  second_half  holds
             VIX         30+ 432      1.6  0.05         1.9          0.0   True
       20 DMA se        -3%+ 456      3.1  0.10         1.9          5.5   True
             VIX       22-30 642      4.7  0.16         3.2          7.7   True
10d realised vol sabse zyada 820      5.1  0.17         2.4         11.4   True
    aaj ki chaal       >1.5% 671      9.3  0.31         7.6         12.5   True
    VIX 5d badla       +15%+ 383     10.4  0.35         6.2         15.5   True
10d realised vol       zyada 897     17.2  0.58        15.5         19.7   True
             VIX       18-22 851     18.4  0.62        16.4         21.0   True
```

Pehle aadhe se chune "shaant" ishaare (dono aadhe sahi): VIX=12-14, VIX=14-16, VIX=<12, 10d realised vol=kam, 10d realised vol=sabse kam, 20 DMA se=+1..3
  0+ ishaare saath: 4521 din, P(5 din shaant) 38.8% (pehla aadha 30.0, doosra 47.3)
  1+ ishaare saath: 2828 din, P(5 din shaant) 51.1% (pehla aadha 45.1, doosra 54.9)
  2+ ishaare saath: 1671 din, P(5 din shaant) 59.8% (pehla aadha 59.0, doosra 60.1)
  3+ ishaare saath: 566 din, P(5 din shaant) 67.8% (pehla aadha 74.7, doosra 65.2)

### Shares (A, 2 saal): base P(agle 10 din +-5% ke andar) = 17.4%
  apni vol sabse kam 20% (sab shares mein):  33.8% (pehla 33.7, doosra 33.8)
  apni vol sabse zyada 20%                :   6.3% (pehla 6.9, doosra 5.8)
  NR7                                     :  18.8% (pehla 19.0, doosra 18.7)
  squeeze (apna 20% patla)                :  23.5% (pehla 25.2, doosra 21.8)
  aaj 4%+ chaal                           :   6.4% (pehla 5.9, doosra 6.9)
  200 DMA ke upar                         :  19.8% (pehla 27.7, doosra 17.7)
  low-vol + squeeze dono                  :  37.9%
