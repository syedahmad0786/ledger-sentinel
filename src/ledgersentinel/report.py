"""Combine the deterministic screens into one findings report."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .anomaly import anomaly_scores, top_anomalies
from .benford import benford_first_digit, duplicate_payments, threshold_clustering


@dataclass
class Finding:
    kind: str            # benford | threshold | duplicate | anomaly
    entity: str
    severity: str        # high | medium
    detail: str
    evidence: dict = field(default_factory=dict)


def screen_ledger(df: pd.DataFrame, amount_col: str = "amount",
                  date_col: str = "date", entity_col: str = "entity",
                  approval_threshold: float | None = None) -> list[Finding]:
    findings: list[Finding] = []

    # 1) Benford per entity (only entities with enough rows) + whole ledger
    for entity, grp in df.groupby(entity_col):
        r = benford_first_digit(grp[amount_col])
        if r and r.nonconforming:
            findings.append(Finding(
                kind="benford", entity=str(entity), severity="high",
                detail=(f"first-digit distribution nonconforming "
                        f"(MAD {r.mad}, n={r.n}; digits {r.suspicious_digits} "
                        f"over-represented) — pattern typical of fabricated amounts"),
                evidence={"mad": r.mad, "n": r.n, "observed": r.observed,
                          "expected": r.expected}))

    # 2) Near-threshold clustering per entity
    if approval_threshold:
        for entity, grp in df.groupby(entity_col):
            t = threshold_clustering(grp[amount_col], approval_threshold)
            if t and t["suspicious"]:
                findings.append(Finding(
                    kind="threshold", entity=str(entity), severity="high",
                    detail=(f"{t['just_below']} amounts just below the "
                            f"{approval_threshold:.0f} approval limit vs "
                            f"{t['just_above']} just above (ratio {t['ratio']}) "
                            f"— classic limit-avoidance pattern"),
                    evidence=t))

    # 3) Duplicate payments
    dups = duplicate_payments(df, entity_col, amount_col, date_col)
    for (entity, amount), grp in dups.groupby([entity_col, amount_col]):
        if len(grp) >= 2:
            dates = pd.to_datetime(grp[date_col]).dt.date.astype(str).tolist()
            findings.append(Finding(
                kind="duplicate", entity=str(entity), severity="medium",
                detail=f"{amount:.2f} paid {len(grp)}x within 14 days ({', '.join(dates)})",
                evidence={"amount": float(amount), "dates": dates}))

    # 4) Isolation Forest outliers
    scored = anomaly_scores(df, amount_col, date_col, entity_col)
    for _, row in top_anomalies(scored[scored["is_anomaly"]], k=3).iterrows():
        findings.append(Finding(
            kind="anomaly", entity=str(row[entity_col]), severity="medium",
            detail=(f"{row[amount_col]:.2f} on {row[date_col]} is a statistical "
                    f"outlier (score {row['anomaly_score']})"),
            evidence={"amount": float(row[amount_col]),
                      "score": float(row["anomaly_score"])}))

    order = {"high": 0, "medium": 1}
    findings.sort(key=lambda f: order[f.severity])
    return findings


def findings_frame(findings: list[Finding]) -> pd.DataFrame:
    return pd.DataFrame([{"severity": f.severity, "kind": f.kind,
                          "entity": f.entity, "detail": f.detail}
                         for f in findings])
