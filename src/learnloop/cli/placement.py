"""`learnloop placement status` and `learnloop eval placement` (report 3).

Both are read-only: they open the database read-only, never migrate it and
never call a model. Run them on a backup-API copy of a vault.
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

placement_app = typer.Typer(no_args_is_help=True, help="Starting new material without ceremony (learner field F2).")


def _load(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")
    return load_vault(vault, load_environment=False)


def _emit(payload: dict, json_output: bool) -> None:
    typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2))


@placement_app.command("status")
def placement_status(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Whether placement serves, and every open assumed-known LO with its check date."""

    from learnloop.placement.state import (
        assumption_summary,
        load_placement_state_from_connection,
        placement_active,
    )

    try:
        loaded = _load(vault)
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            state = load_placement_state_from_connection(connection, active=placement_active(loaded))
        payload = {
            "algorithm_version": loaded.config.algorithms.algorithm_version,
            "placement": loaded.config.placement.model_dump(mode="json"),
            **assumption_summary(state),
            "resolved": {
                status: sum(1 for a in state.assumptions if a.status == status)
                for status in ("passed", "failed", "returned")
            },
        }
        _emit(payload, json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


def placement_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; read-only, no model calls.")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Report 3: first-review miss rate by source, returns to learning, minutes saved.

    Aggregates only (no learner text, no per-LO identities); files are
    content-addressed under the output directory.
    """

    from learnloop.placement.report import placement_report, write_placement_report

    try:
        loaded = _load(vault)
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            report = placement_report(connection, loaded)
        files = write_placement_report(report, output_dir)
        if json_output:
            _emit({"version": 1, "status": "complete", "reports": files, "report": report}, True)
        else:
            typer.echo("\n".join((files["json"], files["markdown"])))
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
