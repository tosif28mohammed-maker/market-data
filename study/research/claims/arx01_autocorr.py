# ARX-01 (arXiv 1510.03704 / 2012.01160): Indian index returns autocorrelated (not random walk).
# Test: Nifty daily lag-1 autocorr by era; 'follow yesterday' next-day mean after up vs down day; weekly too.
import pandas as pd, numpy as np, os
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
n = pd.read_csv(f'{REPO}/data/NIFTY.csv', parse_dates=['date']).set_index('date')['close'].sort_index()
for freq, lab in [('D', 'daily'), ('W-FRI', 'weekly')]:
    r = (n if freq == 'D' else n.resample(freq).last()).pct_change().dropna() * 100
    for era, s, e in [('to2012', '1990', '2012'), ('2013-20', '2013', '2020'), ('2021-26', '2021', '2026'), ('last6m', '2026-05-23', '2026'), ('ALL', '1990', '2026')]:
        x = r.loc[s:e]
        if len(x) < 20: continue
        up = x.shift(1) > 0
        print(lab, era, len(x), 'ac1=%.3f' % x.autocorr(1), 'after_up=%.3f' % x[up].mean(), 'after_down=%.3f' % x[~up & x.shift(1).notna()].mean(),
              'p_up_after_up=%.1f' % ((x[up] > 0).mean() * 100), 'p_up_after_down=%.1f' % ((x[~up] > 0).mean() * 100))
print('start', n.index[0].date())
