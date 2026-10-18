"""`learnloop ad`: adaptive difficulty AD1's owner-run commands (spec §14 AD1).

`ad data-check` is read-only: the database is opened read-only, never
migrated, and no model is called; it prints aggregates only. Run it on a
backup copy.

`ad backfill` is the owner's one-time pass: `--dry-run` opens the database
read-only, calls nothing, writes nothing and prints the plan with its
estimate; a real run audits (`--audit`), forecasts never-attempted items
(`--llm-v1`) and sweeps the reading history (`--reading`) under
`adaptive_difficulty.daily_spend_cap_usd`.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

ad_app = typer.Typer(no_args_is_help=True, help="Adaptive difficulty: AD1's data check and backfills.")


def _vault_root(vault: Path) -> None:
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")


@ad_app.command("data-check")
def data_check_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only; use a backup copy).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The spec's §3.3 tables, first-surface attempts per cell, coverage of latency, ratings
    and hint timing, exam units with and without a facet mapping, and historical attempts by
    revision status. Read-only, no model call."""

    from learnloop.adaptive_difficulty.data_check import data_check
    from learnloop.db.repositories import Repository

    try:
        _vault_root(vault)
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        report = data_check(loaded, path, repository=Repository.attach(path, read_only=True))
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@ad_app.command("backfill")
def backfill_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    audit: Annotated[bool, typer.Option("--audit", help="Audit every active and every held item revision.")] = False,
    llm_v1: Annotated[bool, typer.Option("--llm-v1", help="Forecast the never-attempted items (llm_v1:item).")] = False,
    reading: Annotated[bool, typer.Option("--reading", help="Sweep the reading history (no model call).")] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="At most this many audits / forecasts.")] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print the plan and the estimate; call and write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """AD1's one-time backfills (--audit, --llm-v1, --reading). Run --dry-run first."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.practice_index.paid import planning_repository

    try:
        _vault_root(vault)
        if not (audit or llm_v1 or reading):
            raise ValueError("name at least one of --audit, --llm-v1, --reading")
        loaded = load_vault(vault)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        result = backfill(loaded, repository, audit=audit, llm_v1=llm_v1, reading=reading, dry_run=dry_run,
                          limit=limit)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
