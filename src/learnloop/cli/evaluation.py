"""Explicit, read-only offline evaluation; does not initialize or migrate a vault."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.cli.app import eval_command
from learnloop.db.repositories import Repository
from learnloop.evaluation.report import evaluate, write_report
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

eval_app = typer.Typer(invoke_without_command=True, help="Read-only calibration and offline predictor evaluation.")


@eval_app.callback()
def evaluate_existing(
    ctx: typer.Context,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    section: Annotated[str, typer.Option("--section", help="predictions|coverage|gates|retention|propensity|all")] = "all",
    bins: Annotated[int, typer.Option("--bins", help="Calibration bin count.")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """Preserve `learnloop eval --vault ...` while adding research arms."""
    if ctx.invoked_subcommand is None:
        eval_command(vault=vault, section=section, bins=bins, json_output=json_output)


@eval_app.command("families")
def eval_families(
    vault: Annotated[Path, typer.Option("--vault")],
    output: Annotated[Path, typer.Option("--output")] = Path("fixtures-local/reports"),
    legacy_fallback: Annotated[str, typer.Option("--legacy-fallback",
        help="exclude (default), or explicit current_content reconstruction.")] = "exclude",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Replay memory per item/family/LO and idea_hier without any model calls."""
    loaded = load_vault(vault)
    repository = Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)
    try:
        report = evaluate(loaded, repository, legacy_fallback=legacy_fallback)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    paths = write_report(report, output)
    typer.echo(json.dumps(report, sort_keys=True) if json_output else
               "\n".join(str(path) for path in paths))
