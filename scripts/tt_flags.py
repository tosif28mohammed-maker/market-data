"""Tickertape export -> sirf haan/na flags (user OK 18 Nov 2026, point c).

Raw Tickertape data repo mein KABHI nahi jaata (repo public, paid data).
Ye script chat/computer par chalti hai:  python scripts/tt_flags.py <folder_ya_csv...>
Output: data/tt_flags.csv  -> symbol, asof, aur 0/1 flags (koi asli aankda nahi).

Flags (seema pehle se tay; ye sirf JAANKARI hai, back-test nahi hua, score nahi badalta):
  girvi        promoter ke hisse ka >=10% girvi (pledged)
  promoter_bech promoter ne 3 mahine mein >=1% hissa ghataya
  fii_bech     FII ne 3 mahine mein >=1% hissa ghataya
  mf_khareed   mutual funds ne 3 mahine mein >=0.5% hissa badhaya (achha nishaan)
  insider_bech insider trades 3 mahine ka jod minus mein
  analyst_kam  3 se kam analyst dekhte hain
"""
import sys, os, glob, re, datetime as dt
import pandas as pd

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def norm(c):
    return re.sub(r'[^a-z0-9]', '', str(c).replace('\xa0', ' ').lower())


WANT = {
    'pledge': 'pledgedpromoterholdings',
    'prom3m': 'promoterholdingchange3m',
    'fii3m': 'fiiholdingchange3m',
    'mf3m': 'mfholdingchange3m',
    'insider': 'insidertrades3mcumulative',
    'analysts': 'totalnoofanalysts',
}


def load(paths):
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, '*.csv'))) if os.path.isdir(p) else [p]
    M = None
    for f in files:
        d = pd.read_csv(f, low_memory=False)
        d.columns = [norm(c) for c in d.columns]
        if 'ticker' not in d.columns:
            continue
        d = d.drop_duplicates('ticker').set_index('ticker')
        M = d if M is None else M.join(d[[c for c in d.columns if c not in M.columns]], how='outer')
    if M is None:
        sys.exit('Koi Tickertape CSV (Ticker column ke saath) nahi mili')
    return M


def num(M, k):
    c = WANT[k]
    return pd.to_numeric(M[c], errors='coerce') if c in M.columns else pd.Series(float('nan'), index=M.index)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    M = load(sys.argv[1:])
    asof = os.environ.get('TT_ASOF', dt.date.today().isoformat())
    pl, pr, fi, mf, ins, an = (num(M, k) for k in ['pledge', 'prom3m', 'fii3m', 'mf3m', 'insider', 'analysts'])
    F = pd.DataFrame({
        'girvi': (pl >= 10),
        'promoter_bech': (pr <= -1),
        'fii_bech': (fi <= -1),
        'mf_khareed': (mf >= 0.5),
        'insider_bech': (ins < 0),
        'analyst_kam': ((an < 3) | an.isna()) if WANT['analysts'] in M.columns else False,
    }, index=M.index).astype(int)
    F.index.name = 'symbol'
    F = F[F.index.notna()]
    F.insert(0, 'asof', asof)
    out = os.path.join(R, 'data', 'tt_flags.csv')
    F.sort_index().to_csv(out)
    missing = [k for k, c in WANT.items() if c not in M.columns]
    print(f'{len(F)} shares -> {out}; flag counts:', F.drop(columns='asof').sum().to_dict())
    if missing:
        print('Ye column export mein nahi mile (flag 0 maana):', missing)


if __name__ == '__main__':
    main()
