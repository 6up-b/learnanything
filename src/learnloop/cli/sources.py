"""`learnloop sources`: the canonical-sources service (spec_source_practice_and_probes_v1).

Owner-run batch work over textbook exercises (``exercises harvest``,
``exercises verify``), the typed tools for external agents (``tools``,
``tool``) and the intervention report (``outcomes``). Every paid command has
``--dry-run`` (no client is built, nothing is sent or written) and a money cap.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from learnloop.cli.runtime import _repository, _root
from learnloop.vault.loader import load_vault

sources_app = typer.Typer(no_args_is_help=True,
                          help="Canonical sources: textbook exercises, typed tools and intervention outcomes.")
exercises_app = typer.Typer(no_args_is_help=True,
                            help="Textbook exercises as practice: harvest thin facets, verify answer keys.")
sources_app.add_typer(exercises_app, name="exercises")


def _emit(report: dict[str, Any], json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, default=str) if json_output
               else json.dumps(report, indent=2, sort_keys=True, default=str))


def _exit_for(report: dict[str, Any], ok: set[str]) -> None:
    if report.get("status") not in ok:
        raise typer.Exit(code=1)


@exercises_app.command("harvest")
def exercises_harvest(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    learning_object: Annotated[list[str] | None, typer.Option("--lo", help="Only facets of these LOs.")] = None,
    facet: Annotated[list[str] | None, typer.Option("--facet", help="Only these facets.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: no client, nothing written.")] = False,
    max_cost_usd: Annotated[float | None, typer.Option("--max-cost-usd", min=0.0,
                                                       help="Stop once metered spend reaches this.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Import judged textbook exercises for thin facets, each key checked before writing."""
    from learnloop.instructional.harvest import harvest

    root = _root(vault)
    try:
        report = harvest(load_vault(root), _repository(root), dry_run=dry_run, max_cost_usd=max_cost_usd,
                         learning_object_ids=tuple(learning_object or ()), facet_ids=tuple(facet or ()),
                         on_progress=None if json_output else typer.echo)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete", "over_budget"})


@exercises_app.command("verify")
def exercises_verify(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    item: Annotated[list[str] | None, typer.Option("--item", help="Only these practice items.")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: no client, nothing written.")] = False,
    max_cost_usd: Annotated[float | None, typer.Option("--max-cost-usd", min=0.0,
                                                       help="Stop once metered spend reaches this.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Check imported exercises' answer keys whose current content is not verified."""
    from learnloop.instructional.harvest import verify

    root = _root(vault)
    try:
        report = verify(load_vault(root), _repository(root), dry_run=dry_run, max_cost_usd=max_cost_usd,
                        item_ids=tuple(item or ()))
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete", "over_budget"})


__all__ = ["sources_app"]
