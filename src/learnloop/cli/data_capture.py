"""``learnloop data-capture``: is the long-horizon dataset being captured? (Read-only.)"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.clock import utc_now_iso
from learnloop.db.connection import connect
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

data_capture_app = typer.Typer(
    help="What later evaluation needs, recorded now: counts and coverage of each new record (read-only).",
    no_args_is_help=True,
)


@data_capture_app.command("report")
def data_capture_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Counts and coverage for each new record: prefilter receipts, frozen objectives and their measurement
    states by arm, outcomes by arm, the first-delayed-success proxy, the not_ready floor and the delayed
    picks, the marks on possible causes with the coverage of their exposures, and RO0's coverage per row with
    measured bytes per day (read-only; no model call; no effect is estimated)."""

    from learnloop.diagnosis.causal_probe_coherence import resolve_causal_probe_parameters
    from learnloop.db.repositories import Repository
    from learnloop.ops.capture_report import build_report, lines

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        repository = Repository.attach(path, read_only=True)
        threshold = float(resolve_causal_probe_parameters(repository)["cold_verification_success_correctness"])
        with closing(connect(path, read_only=True)) as connection:
            connection.execute("BEGIN")
            report = build_report(connection, loaded, repository, as_of=utc_now_iso(), success_correctness=threshold)
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True, default=str))
        return
    for line in lines(report):
        typer.echo(line)
