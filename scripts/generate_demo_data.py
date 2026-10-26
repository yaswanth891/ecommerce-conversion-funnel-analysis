"""Create deterministic SYNTHETIC Retailrocket-shaped product events."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]

def generate(n_visitors=22000, seed=42):
    rng = np.random.default_rng(seed)
    rows = []
    origin = pd.Timestamp('2025-01-01',tz='UTC').value // 10**6
    for visitor in range(1, n_visitors + 1):
        first = origin + int(rng.integers(0, 180*86400000))
        item = int(rng.integers(1000, 9000))
        rows.append((first, visitor, 'view', item, ''))
        if rng.random() < 0.65:
            rows.append((first + int(rng.integers(12000, 600000)), visitor, 'view', item, ''))
        if rng.random() < .32:
            added = first + int(rng.integers(600001, 2400000))
            rows.append((added, visitor, 'addtocart', item, ''))
            if rng.random() < .45:
                rows.append((added + int(rng.integers(60000, 1200000)), visitor,'transaction',item,f'T{visitor}'))
        # In a real log some pre-view and misc signals do occur.
        if rng.random() < .07:
            rows.append((first + 4000, visitor, 'view', int(rng.integers(1000,9000)),''))
    frame = pd.DataFrame(rows,columns=['timestamp','visitorid','event','itemid','transactionid'])
    return frame.sample(frac=1,random_state=seed).reset_index(drop=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--visitors',type=int,default=22000)
    args=parser.parse_args()
    out=BASE/'data/raw/events.csv'
    generate(args.visitors).to_csv(out,index=False)
    print(f'SYNTHETIC demo events: {len(pd.read_csv(out)):,} rows -> {out}')
