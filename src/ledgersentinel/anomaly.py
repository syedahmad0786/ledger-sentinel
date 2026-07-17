"""Isolation Forest anomaly screening (Liu et al., 2008).

Why a 2008 tree method and not an LLM? Because the 2026 literature says so:
FinFraud-LLM (IEEE 2026) measured LLMs at ~97% accuracy but ~35% RECALL on
fraud vs. XGBoost-class baselines. Deterministic models detect; the LLM's
job (explain.py) is to explain flags in plain English. Math decides.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def _features(df: pd.DataFrame, amount_col: str, date_col: str,
              entity_col: str) -> pd.DataFrame:
    f = pd.DataFrame(index=df.index)
    amt = df[amount_col].abs().astype(float)
    dates = pd.to_datetime(df[date_col])
    f["log_amount"] = np.log1p(amt)
    f["weekday"] = dates.dt.weekday
    f["is_weekend"] = (dates.dt.weekday >= 5).astype(int)
    f["is_round_hundred"] = ((amt % 100) == 0).astype(int)
    f["cents_99"] = ((amt * 100 % 100).round() == 99).astype(int)
    grp = amt.groupby(df[entity_col])
    f["entity_z"] = ((amt - grp.transform("mean")) /
                     grp.transform("std").replace(0, np.nan)).fillna(0.0)
    return f


def anomaly_scores(df: pd.DataFrame, amount_col: str = "amount",
                   date_col: str = "date", entity_col: str = "entity",
                   contamination: float = 0.02,
                   random_state: int = 7) -> pd.DataFrame:
    """Returns df + anomaly_score (higher = weirder) + is_anomaly."""
    feats = _features(df, amount_col, date_col, entity_col)
    iso = IsolationForest(n_estimators=200, contamination=contamination,
                          random_state=random_state)
    iso.fit(feats)
    out = df.copy()
    out["anomaly_score"] = (-iso.score_samples(feats)).round(4)
    out["is_anomaly"] = iso.predict(feats) == -1
    return out


def top_anomalies(scored: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    return scored.sort_values("anomaly_score", ascending=False).head(k)
