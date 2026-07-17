"""Aixcel brand layer for Streamlit demos — Ahmad Bukhari's palette.

Source of truth: the ahmad-card.svg profile card (GitHub-dark canvas with
terminal traffic-light accents). Import and call brand() right after
st.set_page_config; call footer() at the end.
"""

from __future__ import annotations

import streamlit as st

INK = "#0d1117"          # canvas
PANEL = "#161b22"        # cards
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#8b949e"
GREEN = "#7ee787"
AMBER = "#ffbd2e"
RED = "#ff5f56"
BLUE = "#79c0ff"
PURPLE = "#d2a8ff"

_CSS = f"""
<style>
.stApp {{ background: {INK}; color: {TEXT}; }}
section[data-testid="stSidebar"] {{ background: {PANEL}; }}
h1, h2, h3 {{ color: {TEXT} !important; font-family: 'Cascadia Code', Consolas, monospace; }}
.aixcel-bar {{
  height: 6px; border-radius: 3px; margin: 0 0 1.2rem 0;
  background: linear-gradient(90deg, {RED}, {AMBER}, {GREEN});
}}
.aixcel-chip {{
  display: inline-block; padding: 2px 10px; margin-right: 6px;
  border: 1px solid {BORDER}; border-radius: 999px;
  background: {PANEL}; color: {MUTED}; font-size: 0.78rem;
  font-family: Consolas, monospace;
}}
div[data-testid="stMetric"] {{
  background: {PANEL}; border: 1px solid {BORDER};
  border-radius: 10px; padding: 10px 14px;
}}
div[data-testid="stMetric"] label {{ color: {MUTED} !important; }}
.stDownloadButton button, .stButton button[kind="primary"] {{
  background: linear-gradient(90deg, {RED}, {AMBER}) !important;
  color: {INK} !important; border: none !important; font-weight: 700;
}}
.aixcel-footer {{
  margin-top: 2.5rem; padding-top: 0.8rem; border-top: 1px solid {BORDER};
  color: {MUTED}; font-size: 0.85rem; font-family: Consolas, monospace;
}}
.aixcel-footer a {{ color: {BLUE}; text-decoration: none; }}
</style>
"""


def brand(title: str, tagline: str, chips: list[str] | None = None) -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="aixcel-bar"></div>', unsafe_allow_html=True)
    st.title(title)
    if chips:
        st.markdown(" ".join(f'<span class="aixcel-chip">{c}</span>' for c in chips),
                    unsafe_allow_html=True)
    st.markdown(tagline)


def footer(extra: str = "") -> None:
    st.markdown(
        f'<div class="aixcel-footer">built by '
        f'<a href="https://github.com/syedahmad0786">Ahmad Bukhari</a> — '
        f'AI &amp; Automation Architect · agentic systems that run real '
        f'businesses, not just demos{(" · " + extra) if extra else ""}</div>',
        unsafe_allow_html=True)
