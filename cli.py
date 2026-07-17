"""ledger-sentinel CLI — screen an expense/AP ledger for fraud patterns.

Usage:
    python cli.py                                    # bundled sample ledger
    python cli.py --csv my_ledger.csv --threshold 500
    python cli.py --explain                          # add LLM plain-English layer
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from ledgersentinel.report import findings_frame, screen_ledger

app = typer.Typer(add_completion=False)
console = Console()
EX = Path(__file__).parent / "examples"


@app.command()
def run(csv: Path = typer.Option(EX / "sample_ledger.csv"),
        threshold: float = typer.Option(500.0, help="Approval limit to test"),
        explain: bool = typer.Option(False, help="LLM plain-English layer")) -> None:
    df = pd.read_csv(csv)
    console.print(f"[bold]ledger-sentinel[/bold] — {len(df)} transactions, "
                  f"{df['entity'].nunique()} entities")
    findings = screen_ledger(df, approval_threshold=threshold)

    t = Table(title=f"{len(findings)} findings (math decides, LLM only explains)")
    for col in ("severity", "kind", "entity", "detail"):
        t.add_column(col, overflow="fold")
    for f in findings:
        style = "red" if f.severity == "high" else "yellow"
        t.add_row(f"[{style}]{f.severity}[/{style}]", f.kind, f.entity, f.detail)
    console.print(t)

    if explain:
        from ledgersentinel.explain import explain as llm_explain
        console.print("\n[bold]Plain-English explanations:[/bold]")
        console.print(llm_explain(findings))


if __name__ == "__main__":
    app()
