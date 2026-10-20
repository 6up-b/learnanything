"""`learnloop plan show` and `learnloop plan report` (daily-loop DL1).

Both are read-only: they open the database read-only, never migrate it, never
build a queue or a plan, and never call a model. ``report`` is the owner's
two-week checkpoint (days active, plan starts and completions, estimated vs
actual minutes, keep-going rate, open-to-first-item time).
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

plan_app = typer.Typer(no_args_is_help=True, help="The finite daily plan (daily-loop DL1).")


def _load(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")
    return load_vault(vault, load_environment=False)


def _emit(payload: dict, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2))


@plan_app.command("show")
def plan_show_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    date: Annotated[str | None, typer.Option("--date", help="Local date YYYY-MM-DD (default: today).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Today's plans as stored: split, blocks, items and their states."""

    from learnloop.daily_plan.engine import load_records_from_connection, local_date, plan_active
    from learnloop.daily_plan.report import plan_show

    try:
        loaded = _load(vault)
        day = date or local_date()
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            records = load_records_from_connection(connection, local_date_value=day)
        _emit(
            {
                "active": plan_active(loaded),
                "algorithm_version": loaded.config.algorithms.algorithm_version,
                "local_date": day,
                "plans": [plan_show(record, loaded) for record in records],
            },
            json_output,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


@plan_app.command("report")
def plan_report_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Aggregates over every stored plan (the DL1 owner checkpoint)."""

    from learnloop.daily_plan.engine import load_records_from_connection, plan_active
    from learnloop.daily_plan.report import plan_report
    from learnloop.intent.report import intent_report

    try:
        loaded = _load(vault)
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            records = load_records_from_connection(connection)
            # DL2: what is committed, and the recall-target fallbacks (§5.3).
            intent = intent_report(loaded, connection)
        _emit(
            {
                "active": plan_active(loaded),
                "algorithm_version": loaded.config.algorithms.algorithm_version,
                **plan_report(records),
                "intent": intent,
            },
            json_output,
        )
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
