"""Benford's Law digit screening (Nigrini's forensic-accounting playbook).

Naturally occurring amounts that span magnitudes follow
P(first digit = d) = log10(1 + 1/d). Fabricated numbers usually don't —
humans over-pick middle digits and cluster below approval thresholds.

Honesty notes baked into the API:
- digit tests need sample size (we refuse < MIN_N with a warning, not a score)
- Benford does NOT apply to assigned/bounded numbers (invoice IDs, prices
  from a fixed catalog); callers screen free-form amounts only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MIN_N = 80                      # below this, digit tests are noise
EXPECTED_F1 = np.array([math.log10(1 + 1 / d) for d in range(1, 10)])

# Nigrini's Mean Absolute Deviation conformity bands (first digit).
# IMPORTANT (found by our own benchmark): these bands assume LARGE samples
# (thousands). At n~100, sampling noise alone breaches 0.015 and every
# honest vendor gets flagged. So the verdict below is gated on chi-square,
# which accounts for n; MAD stays as the effect-size descriptor.
MAD_BANDS = [
    (0.006, "close conformity"),
    (0.012, "acceptable conformity"),
    (0.015, "marginal conformity"),
    (float("inf"), "nonconforming shape"),
]
CHI2_CRIT_P001 = 26.12          # chi-square df=8, p=0.001


@dataclass
class BenfordResult:
    n: int
    observed: list[float]           # observed first-digit proportions, d=1..9
    expected: list[float]
    mad: float
    verdict: str
    chi2: float
    suspicious_digits: list[int] = field(default_factory=list)

    @property
    def nonconforming(self) -> bool:
        """Flag only when BOTH hold: the deviation is statistically real at
        this sample size (chi2, p<0.001) AND the effect size is material
        (MAD past Nigrini's acceptable band)."""
        return self.chi2 >= CHI2_CRIT_P001 and self.mad > 0.012


def first_digits(amounts: pd.Series) -> pd.Series:
    a = amounts.abs()
    a = a[a > 0]
    return a.map(lambda x: int(str(f"{x:.10e}")[0]))


def benford_first_digit(amounts: pd.Series) -> BenfordResult | None:
    """None = not enough data to say anything (never fake a verdict)."""
    fd = first_digits(amounts)
    n = len(fd)
    if n < MIN_N:
        return None
    obs = np.array([(fd == d).mean() for d in range(1, 10)])
    mad = float(np.abs(obs - EXPECTED_F1).mean())
    verdict = next(label for cutoff, label in MAD_BANDS if mad <= cutoff)
    chi2 = float((n * (obs - EXPECTED_F1) ** 2 / EXPECTED_F1).sum())
    suspicious = [d + 1 for d in range(9)
                  if obs[d] - EXPECTED_F1[d] > max(0.03, 2 * math.sqrt(EXPECTED_F1[d] * (1 - EXPECTED_F1[d]) / n))]
    return BenfordResult(n=n, observed=obs.round(4).tolist(),
                         expected=EXPECTED_F1.round(4).tolist(),
                         mad=round(mad, 4), verdict=verdict,
                         chi2=round(chi2, 1), suspicious_digits=suspicious)


def threshold_clustering(amounts: pd.Series, threshold: float,
                         band: float = 0.05) -> dict | None:
    """Nigrini's near-threshold test: fraudsters cluster just UNDER approval
    limits. Measures the share of amounts in [threshold*(1-band), threshold)
    against the share just above — a legitimate ledger is roughly symmetric."""
    a = amounts.abs()
    lo, hi = threshold * (1 - band), threshold * (1 + band)
    below = int(((a >= lo) & (a < threshold)).sum())
    above = int(((a >= threshold) & (a <= hi)).sum())
    n = len(a)
    if n == 0 or below + above < 8:
        return None
    ratio = below / max(above, 1)
    return {"threshold": threshold, "just_below": below, "just_above": above,
            "ratio": round(ratio, 2), "suspicious": ratio >= 3.0 and below >= 8}


def duplicate_payments(df: pd.DataFrame, entity_col: str, amount_col: str,
                       date_col: str, window_days: int = 14,
                       min_amount: float = 500.0) -> pd.DataFrame:
    """Same entity + same amount within a short window = possible double
    payment. Materiality floor (min_amount) because small legit amounts
    collide by chance, and recurring subscriptions are exact by design —
    both false-positive sources our benchmark actually produced."""
    d = df[[entity_col, amount_col, date_col]].copy()
    d = d[d[amount_col].abs() >= min_amount]
    d[date_col] = pd.to_datetime(d[date_col])
    d = d.sort_values([entity_col, amount_col, date_col])
    gap = d.groupby([entity_col, amount_col])[date_col].diff().dt.days
    dup_mask = gap.notna() & (gap <= window_days)
    pairs = d[dup_mask | dup_mask.shift(-1, fill_value=False)]
    return pairs
