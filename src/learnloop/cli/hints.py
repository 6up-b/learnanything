"""`learnloop hints report`: hint use and what follows (adaptive hints H0; spec §6.3).

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

hints_app = typer.Typer(no_args_is_help=True, help="Hints (H0: the hint-use report).")

_RELATIVE = re.compile(r"^(\d+)([dh])$")
_SURFACES = ("practice", "workbench", "guided_redo", "tutor")


def _since(value: str | None, now: datetime) -> str | None:
    if value is None:
        return None
    match = _RELATIVE.match(value.strip())
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        return (now - (timedelta(days=amount) if unit == "d" else timedelta(hours=amount))).isoformat()
    return value


@hints_app.command("report")
def hints_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only hints shown at or after this ISO time, or a span such as 7d or 24h."),
    ] = None,
    surface: Annotated[
        str | None,
        typer.Option("--surface", help="Only one surface: practice, workbench, guided_redo or tutor."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Hints by surface, kind and level (authored hints are the baseline): shown, items,
    sessions, timing, more help, the attempt's outcome and later independent success."""

    from learnloop.hints.report import build_hints_report

    now = datetime.now(UTC)
    try:
        if surface is not None and surface not in _SURFACES:
            raise ValueError(f"--surface must be one of {', '.join(_SURFACES)}")
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        report = build_hints_report(path, since=_since(since, now), surface=surface, now=now)
        report["hints"] = loaded.config.hints.model_dump(mode="json")
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
