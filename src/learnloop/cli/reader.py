"""`learnloop reader report`: the Reader's workflow funnel (reader workbench RW1a).

Read-only: the database is opened read-only, never migrated, and no model is
called. The report carries ids, counts, shares and timings, never learner text.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

reader_app = typer.Typer(no_args_is_help=True, help="The Reader (RW1a: the workflow funnel report).")

_RELATIVE = re.compile(r"^(\d+)([dh])$")


def _since(value: str | None, now: datetime) -> str | None:
    if value is None:
        return None
    match = _RELATIVE.match(value.strip())
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        return (now - (timedelta(days=amount) if unit == "d" else timedelta(hours=amount))).isoformat()
    return value


@reader_app.command("report")
def reader_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only activity at or after this ISO time, or a span such as 7d or 24h."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Workflows with denominators: selection -> action -> result -> back to reading,
    inquiries, detours (return rate, cost), proactive load, waiting behaviour, visits."""

    from learnloop.reader.reader_report import build_reader_report

    now = datetime.now(UTC)
    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        report = build_reader_report(path, since=_since(since, now), now=now)
        report["reader_inquiry"] = loaded.config.reader_inquiry.model_dump(mode="json")
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
