<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/papers-Benford/Nigrini_·_Isolation_Forest_2008_·_FinFraud--LLM_2026-blueviolet" alt="Papers"/>
  <img src="https://img.shields.io/badge/API_keys-none_required-7ee787" alt="No keys"/>
  <img src="https://img.shields.io/badge/demo-live_on_Streamlit-FF4B4B?logo=streamlit&logoColor=white" alt="Demo"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT"/>
</p>

# ledger-sentinel — forensic screening for SMB ledgers

Upload an expense/AP ledger. Get fraud-pattern findings in seconds:

```text
┌────────────────── 6 findings (math decides, LLM only explains) ──────────────────┐
│ high    benford    Apex Supplies  first-digit distribution nonconforming         │
│                                   (MAD 0.0313, n=140) — typical of fabricated…   │
│ high    threshold  j.doe          26 amounts just below the 500 approval limit   │
│                                   vs 0 just above — classic limit-avoidance      │
│ medium  duplicate  CaterCo        1240.00 paid 2x within 14 days                 │
│ medium  anomaly    m.khan         9875.00 on 2026-03-08 (a Sunday) — outlier     │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## The design bet: math detects, LLM explains

The 2026 literature settled this one. **FinFraud-LLM** (IEEE 2026) measured
LLMs on fraud detection at ~97% accuracy but **~35% recall** vs. tree-model
baselines; *Understanding Structured Financial Data with LLMs* (arXiv
2512.13040) reaches the same conclusion — LLMs narrow the gap and add
interpretability, but specialized classifiers still detect better. So:

| Layer | Technique | Year | Role |
|---|---|---|---|
| Digit forensics | Benford's Law + Nigrini's MAD bands | 1938/2012 | detect fabricated amounts |
| Limit gaming | near-threshold clustering | Nigrini | detect approval-limit avoidance |
| Double pay | windowed duplicate screen | — | detect duplicate invoices |
| Outliers | Isolation Forest | 2008 | surface review-worthy oddities |
| Narrative | any LLM (optional) | 2026 | explain each flag in plain English |

Everything above the last row is deterministic — **no API keys, data goes
nowhere**, results reproduce exactly.

## Try it live

**[→ live demo](https://ledger-sentinel.streamlit.app)** — upload a CSV
(`date, entity, amount`) or click the sample ledger, which hides 4 planted
schemes. Input → output; no setup, no keys.

Or locally:

```bash
pip install -r requirements.txt
python examples/make_sample.py     # 1,101-row ledger, 4 planted schemes
python cli.py                      # screen it
python cli.py --explain            # + plain-English narrative (Ollama/Groq)
streamlit run demo/streamlit_app.py
```

## Verified: the benchmark falsified v1 (twice)

Tested against a generated ledger with labeled ground truth (900 legitimate
log-normal transactions + 4 planted schemes). First version failed honestly:

1. **Every honest vendor flagged as Benford-nonconforming.** Nigrini's MAD
   bands assume thousands of records; at n≈110 sampling noise alone breaches
   the 0.015 cutoff. Fix: verdicts now require chi-square significance
   (p<0.001, which is sample-size aware) *and* material MAD — MAD stays as
   effect size, not gate.
2. **Duplicate screen tripped on small legit collisions.** Real ledgers
   collide by chance at small amounts and by design on subscriptions. Fix:
   materiality floor (≥500) + 14-day window.

Final result on ground truth: **4/4 planted schemes detected, 0 false
positives on the digit and duplicate screens** (Isolation Forest additionally
surfaces 2 legitimate-but-odd rows as review items, by design).

## Honest scope (v0.1)

Screens, not verdicts — output is "look here first", never "fraud proven."
Benford applies to naturally occurring, multi-magnitude amounts only (not
invoice IDs or fixed-catalog prices), and digit tests refuse to score groups
under 80 rows rather than guess. FinVerBench (arXiv 2605.29586) shows LLM
accuracy collapses 60–90% on hierarchical multi-document financials — one
more reason the LLM here only ever writes prose.

---

<p align="center">Built by <a href="https://github.com/syedahmad0786">Ahmad Bukhari</a> — AI &amp; Automation Architect · <i>agentic systems that run real businesses, not just demos</i></p>
