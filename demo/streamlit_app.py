"""ledger-sentinel LIVE DEMO — Streamlit Community Cloud entrypoint.

Design contract for all Aixcel live demos:
- input -> output, no process: upload a CSV (or one click for sample data),
  get findings. Nobody needs to read code to feel the value.
- zero API keys required: detection is deterministic math (Benford,
  threshold clustering, duplicates, Isolation Forest).
- optional LLM narrative activates ONLY if the host has a GROQ_API_KEY
  secret configured in the Streamlit dashboard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import streamlit as st

from ledgersentinel.benford import EXPECTED_F1, benford_first_digit, first_digits
from ledgersentinel.report import findings_frame, screen_ledger

st.set_page_config(page_title="ledger-sentinel — fraud screening demo",
                   page_icon="🔎", layout="wide")

st.title("🔎 ledger-sentinel")
st.markdown(
    "**Upload an expense/AP ledger → get fraud-pattern findings in seconds.** "
    "Detection is deterministic forensic-accounting math — Benford's Law, "
    "approval-limit clustering, duplicate payments, Isolation Forest — "
    "so this demo needs no API keys and sends your data nowhere. "
    "[Code & paper trail](https://github.com/syedahmad0786/ledger-sentinel)")

left, right = st.columns([1, 2], gap="large")

with left:
    st.subheader("1 · Your ledger")
    up = st.file_uploader("CSV with columns: date, entity, amount",
                          type=["csv"])
    use_sample = st.button("…or try the sample ledger (4 planted schemes)",
                           type="primary", use_container_width=True)
    threshold = st.number_input("Approval limit to test (e.g. expenses "
                                "need a manager sign-off above this)",
                                min_value=0.0, value=500.0, step=50.0)

if "df" not in st.session_state:
    st.session_state.df = None
if up is not None:
    st.session_state.df = pd.read_csv(up)
elif use_sample:
    st.session_state.df = pd.read_csv(ROOT / "examples" / "sample_ledger.csv")

df = st.session_state.df
if df is None:
    with right:
        st.info("⬅ Upload a ledger or click the sample to see it work. "
                "The sample hides 4 real fraud schemes — see if it finds them.")
    st.stop()

missing = {"date", "entity", "amount"} - set(df.columns)
if missing:
    st.error(f"CSV is missing columns: {missing}")
    st.stop()

with left:
    st.metric("Transactions", f"{len(df):,}")
    st.metric("Entities (vendors/employees)", df["entity"].nunique())
    st.metric("Total amount", f"{df['amount'].sum():,.0f}")

with right:
    st.subheader("2 · Findings")
    findings = screen_ledger(df, approval_threshold=threshold or None)
    if not findings:
        st.success("No fraud patterns flagged. (Screens, not verdicts — "
                   "clean flags ≠ clean books.)")
    else:
        high = sum(1 for f in findings if f.severity == "high")
        st.markdown(f"**{len(findings)} findings — {high} high severity**")
        frame = findings_frame(findings)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        st.download_button("Download findings CSV",
                           frame.to_csv(index=False).encode(),
                           "ledger_findings.csv", "text/csv")

    st.subheader("3 · Why: Benford's Law, visually")
    ent = st.selectbox("First-digit distribution for…",
                       ["whole ledger"] + sorted(df["entity"].unique().tolist()))
    series = df["amount"] if ent == "whole ledger" else df[df["entity"] == ent]["amount"]
    r = benford_first_digit(series)
    if r is None:
        st.caption(f"Not enough rows for a digit test (needs ≥80, has {len(series)}) "
                   "— honesty over noise.")
    else:
        chart = pd.DataFrame({"digit": list(range(1, 10)),
                              "observed": r.observed,
                              "expected (Benford)": r.expected}).set_index("digit")
        st.bar_chart(chart)
        st.caption(f"MAD {r.mad} → **{r.verdict}** (n={r.n}). "
                   "Fabricated numbers drift toward uniform digits; "
                   "real multi-magnitude spend follows the curve.")

# Optional LLM narrative — only if the host configured a key.
if os.getenv("GROQ_API_KEY") or "GROQ_API_KEY" in st.secrets:
    os.environ.setdefault("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
    if findings and st.button("Explain these findings in plain English (LLM)"):
        from ledgersentinel.explain import explain
        with st.spinner("Writing the narrative…"):
            st.markdown(explain(findings))

st.divider()
st.caption("Built by [Ahmad Bukhari](https://github.com/syedahmad0786) — "
           "math detects, LLM explains. Why not LLM detection? FinFraud-LLM "
           "(IEEE 2026) measured ~35% recall for LLMs vs tree baselines on "
           "fraud — so the LLM is kept where it's strong: explanation.")
