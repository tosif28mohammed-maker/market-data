"""Pick stocks outside the top-1000 that are still liquid enough for small positions (median daily turnover >= Rs 25 lakh).
python universe/pick_extra.py all_ranked.csv out_list.csv"""
import sys, pandas as pd
S=pd.read_csv(sys.argv[1]); x=S[(S['rank']>1000)&(S.turnover_cr>=0.25)]
x[['symbol','company','industry','turnover_cr','rank']].to_csv(sys.argv[2],index=False); print(len(x))
