"""`learnloop decider`: evidence on the Decider's Tier-1 judgments (owner decision 2026-10-13).

* ``agreement``: per ``judgment_ledger`` task, the real pairs where both the
  Decider and an LLM judged the same input, their agreement and confusion
  counts, the Decider's fallbacks, and its calibration where owner or
  verifier labels exist. Read-only: no model call, no migration, no write.
"""

from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.ai.agreement import agreement_report, ledger_rows
from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

decider_app = typer.Typer(
    no_args_is_help=True,
    help="The Decider's Tier-1 judgments: agreement with the LLM judges (no model call).",
)

#: A review run's scratch ledger (``learnloop diagnose review``), where its link judgments live.
REVIEW_SCRATCH = "scratch.sqlite"


@decider_app.command("agreement")
def agreement(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")] = Path("."),
    review_runs: Annotated[
        list[Path] | None,
        typer.Option("--review-run", help="Also read this `learnloop diagnose review` run's ledger (repeatable)."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="One line of JSON.")] = False,
) -> None:
    """Agreement, confusion and calibration of the Decider against the LLM, from real pairs only.

    A pair is one input both judges answered in the ordinary course (the
    learner-text gap judges before mvp-0.20, an LLM fallback beside the
    Decider's failure, a review run's link batch); no shadow call is ever
    made. Labels are the owner's confirms, keeps and undos and verifier
    verdicts. The pattern-link judgments of a review run live in its own
    ledger: name the run with `--review-run` to include them (each row is
    counted once, though the run's ledger copies the vault's).
    """

    loaded = load_vault(vault, load_environment=False)
    paths = [VaultPaths(loaded.root, loaded.config).sqlite_path]
    paths += [Path(run) / REVIEW_SCRATCH for run in review_runs or []]
    rows = []
    for path in paths:
        if not path.exists():
            raise typer.BadParameter(f"no ledger at {path}")
        with closing(connect(path, read_only=True)) as connection:
            rows += ledger_rows(connection)
    report = {**agreement_report(rows), "ledgers": [str(path) for path in paths]}
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
