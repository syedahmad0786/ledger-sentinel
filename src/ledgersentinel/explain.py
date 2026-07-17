"""Optional LLM layer: explain flags in plain English for a non-accountant.

Strictly explanation-only by design — FinFraud-LLM (2026) measured LLM
recall at ~35% on fraud detection. Detection stays deterministic
(benford.py, anomaly.py); this module never adds or removes flags.
Runs only when an LLM is configured; everything else works without one.
"""

from __future__ import annotations

import os

from .report import Finding


def get_llm(temperature: float = 0.2):
    if os.getenv("GROQ_API_KEY"):
        from langchain_groq import ChatGroq

        return ChatGroq(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                        temperature=temperature)
    from langchain_ollama import ChatOllama

    return ChatOllama(model=os.getenv("OLLAMA_MODEL", "llama3.1"),
                      temperature=temperature,
                      num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "8192")))


SYSTEM = (
    "You are a forensic-accounting assistant. You receive statistical flags "
    "produced by deterministic screens (Benford's Law, threshold clustering, "
    "duplicate detection, Isolation Forest). For each flag, explain to a "
    "business owner in 2-3 plain sentences: what the pattern is, why it can "
    "indicate fraud or error, and what to check first. Never claim fraud is "
    "proven — these are screens, not verdicts."
)


def explain(findings: list[Finding]) -> str:
    llm = get_llm()
    from langchain_core.messages import HumanMessage, SystemMessage

    bullet = "\n".join(f"- [{f.severity}] {f.kind} / {f.entity}: {f.detail}"
                       for f in findings)
    reply = llm.invoke([SystemMessage(content=SYSTEM),
                        HumanMessage(content=f"Flags:\n{bullet}")])
    return reply.content
