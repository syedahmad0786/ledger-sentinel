"""Generate a realistic 14-month SMB expense ledger with four planted schemes.

Legitimate spend is log-normal (naturally Benford-conforming). Planted:
1. 'Apex Supplies' — fabricated invoice amounts (uniform digits, breaks Benford)
2. 'j.doe' — expenses clustered just under the $500 approval limit
3. Two duplicate vendor payments within days of each other
4. One large weekend wire — a statistical outlier

Ground truth is written next to the ledger so the demo can show
detected-vs-planted honestly.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
HERE = Path(__file__).parent


def make(n_legit: int = 900) -> pd.DataFrame:
    rows = []
    vendors = ["OfficeMart", "CloudServe", "FleetFuel", "CaterCo", "AdWorks",
               "j.smith", "m.khan", "s.lee"]
    start = pd.Timestamp("2025-05-01")
    # legitimate: log-normal spans magnitudes -> Benford-conforming
    for _ in range(n_legit):
        amt = float(np.round(rng.lognormal(mean=4.2, sigma=1.4), 2))
        amt = max(3.50, min(amt, 20000))
        d = start + pd.Timedelta(days=int(rng.integers(0, 420)))
        if d.weekday() >= 5:                      # businesses mostly pay weekdays
            d -= pd.Timedelta(days=2)
        rows.append({"date": d.date(), "entity": str(rng.choice(vendors)),
                     "amount": amt, "memo": "regular"})

    # scheme 1: fabricated Apex invoices (humans pick uniform-ish digits)
    for _ in range(140):
        first = rng.integers(1, 10)               # uniform first digit
        rest = rng.integers(0, 100)
        amt = float(f"{first}{rng.integers(0,10)}{rng.integers(0,10)}.{rest:02d}")
        d = start + pd.Timedelta(days=int(rng.integers(0, 420)))
        rows.append({"date": d.date(), "entity": "Apex Supplies",
                     "amount": amt, "memo": "invoice"})

    # scheme 2: j.doe splits expenses under the 500 approval limit
    for _ in range(26):
        amt = float(np.round(rng.uniform(478, 499.99), 2))
        d = start + pd.Timedelta(days=int(rng.integers(0, 420)))
        rows.append({"date": d.date(), "entity": "j.doe",
                     "amount": amt, "memo": "expense claim"})
    for _ in range(30):                           # normal-looking cover traffic
        amt = float(np.round(rng.lognormal(3.4, 0.9), 2))
        d = start + pd.Timedelta(days=int(rng.integers(0, 420)))
        rows.append({"date": d.date(), "entity": "j.doe",
                     "amount": amt, "memo": "expense claim"})

    # scheme 3: duplicate payments
    for date_a, date_b in [("2025-09-03", "2025-09-11"), ("2026-02-17", "2026-02-20")]:
        rows.append({"date": pd.Timestamp(date_a).date(), "entity": "CaterCo",
                     "amount": 1240.00, "memo": "event catering"})
        rows.append({"date": pd.Timestamp(date_b).date(), "entity": "CaterCo",
                     "amount": 1240.00, "memo": "event catering"})

    # scheme 4: weekend wire outlier
    rows.append({"date": pd.Timestamp("2026-03-08").date(),   # a Sunday
                 "entity": "m.khan", "amount": 9875.00, "memo": "wire"})

    df = pd.DataFrame(rows).sample(frac=1, random_state=7).reset_index(drop=True)
    return df


if __name__ == "__main__":
    df = make()
    df.to_csv(HERE / "sample_ledger.csv", index=False)
    truth = {
        "benford": ["Apex Supplies"],
        "threshold": ["j.doe"],
        "duplicate": ["CaterCo"],
        "anomaly": ["m.khan weekend wire 9875.00"],
    }
    (HERE / "ground_truth.json").write_text(json.dumps(truth, indent=2))
    print(f"wrote {len(df)} rows -> sample_ledger.csv (+ ground_truth.json)")
