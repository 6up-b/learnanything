"""`learnloop teacher report`: the learned lesson-check weight's report lines (teacher TE1,
spec_teacher_v1 §12.1 "Kill switch and monitoring"; TE2 adds the lesson rows).

Read-only, no model call: prior-to-posterior contraction, prior sensitivity, the prequential
log loss of the learned mass beside the fixed 0.5, the pool weight per forecaster and the
tap/hedge recalibration. Nothing switches on any of them.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

teacher_app = typer.Typer(no_args_is_help=True,
                          help="Lessons (teacher TE1): the learned lesson-check weight's report.")


@teacher_app.command("report")
def teacher_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """How far the lesson-check weight, the forecast pool and the tap/hedge recalibration have moved
    off their seeded priors (read-only; no model call)."""

    from learnloop.teacher.report import report
    from learnloop.vault.repository import open_vault_repository

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        repository = open_vault_repository(loaded.root, VaultPaths(loaded.root, loaded.config).sqlite_path)
        result = report(loaded, repository)
        if json_output:
            typer.echo(json.dumps(result, sort_keys=True, default=str))
        else:
            for line in result["lines"]:
                typer.echo(line)
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
