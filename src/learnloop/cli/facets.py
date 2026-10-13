"""Facet identity (handoff §4): dedupe an existing vault, list actions, undo one, decide a held reword."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.cli.embeddings import _cancellation


facets_app = typer.Typer(
    no_args_is_help=True,
    help="Facet identity: merge duplicate facets with a cheap judge (live, each with an undo).",
)


def _emit(report: dict, json_output: bool, *, ok: set[str]) -> None:
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2, default=str))
    if report.get("status") == "cancelled":
        raise typer.Exit(130)
    if report.get("status") not in ok:
        raise typer.Exit(1)


def _root(vault: Path) -> Path:
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")
    return vault


@facets_app.command("dedupe")
def facets_dedupe(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    dry_run: Annotated[bool, typer.Option(
        "--dry-run", help="Plan the groups, calls and estimated cost; no client, no call, no change.",
    )] = False,
    subject: Annotated[str | None, typer.Option("--subject", help="Only facets this subject uses.")] = None,
    max_calls: Annotated[int | None, typer.Option("--max-calls", min=0)] = None,
    max_facets: Annotated[int | None, typer.Option("--max-facets", min=0)] = None,
    max_pairs: Annotated[int | None, typer.Option("--max-pairs", min=0)] = None,
    max_retries: Annotated[int | None, typer.Option("--max-retries", min=0)] = None,
    max_tokens: Annotated[int | None, typer.Option("--max-tokens", min=0)] = None,
    max_cost_usd: Annotated[float | None, typer.Option("--max-cost-usd", min=0)] = None,
    price_input: Annotated[float | None, typer.Option(
        "--price-per-million-input", min=0,
        help="Owner price (USD per million input tokens) for a metered judge model without a known price.",
    )] = None,
    price_output: Annotated[float | None, typer.Option(
        "--price-per-million-output", min=0, help="Owner price per million output tokens (default: input price).",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Partition each concept neighbourhood's facets with the judge and apply merges.

    Route: ai.routing.facet_identity_judge (default: the Codex `codex_luna`
    profile, on the subscription; a decider profile is also accepted). Every
    merge or absorb applies live and is listed with its undo command, naming
    the facets whose evidence it re-keys. Merged and shortlisted pairs go to
    judgment_ledger (task same_facet); a rerun reuses judged groups.
    """
    from learnloop.content.facet_identity.dedupe import run_dedupe

    caps = {
        "max_calls": max_calls, "max_candidates": max_facets, "max_pairs": max_pairs,
        "max_retries": max_retries, "max_total_tokens": max_tokens, "max_estimated_usd": max_cost_usd,
    }
    try:
        with _cancellation() as stop:
            report = run_dedupe(
                _root(vault), subject_id=subject, dry_run=dry_run,
                caps_overrides={key: value for key, value in caps.items() if value is not None},
                price_per_million_input=price_input, price_per_million_output=price_output,
                cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, ok={"dry_run", "complete"})


@facets_app.command("actions")
def facets_actions(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    run_id: Annotated[str | None, typer.Option("--run", help="Only one synthesis or dedupe run.")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1, max=10_000)] = 50,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Facet merges, absorbs and rewords (facet versions), newest first, with their undo state.

    A reword waiting for your confirm is listed with status `proposed`
    (`learnloop facets confirm` or `learnloop facets keep`).
    """
    from learnloop.content.facet_identity.actions import describe, list_actions
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    try:
        loaded = load_vault(_root(vault))
        repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
        report = {"status": "complete", "actions": [
            describe(record, loaded) for record in list_actions(repository, run_id=run_id, limit=limit)
        ]}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, ok={"complete"})


@facets_app.command("undo")
def facets_undo(
    action_id: Annotated[str, typer.Argument(help="The action id from the result or `facets actions`.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Restore the facets one merge, absorb or reword replaced; re-fold their evidence.

    Rows graded while the merge stood (exercised facets, notes, error events)
    stay with the surviving facet; the result says so (not_restored).
    """
    from learnloop.content.facet_identity.actions import FacetIdentityActionError, undo_action
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    try:
        loaded = load_vault(_root(vault))
        repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
        report = undo_action(loaded.root, repository, action_id)
    except FacetIdentityActionError as exc:
        report = {"status": "refused", "code": exc.code, "reason": str(exc)}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, ok={"undone"})


def _decide_reword(action_id: str, vault: Path, json_output: bool, *, confirm: bool) -> None:
    from learnloop.content.facet_identity.actions import (
        FacetIdentityActionError,
        confirm_reword,
        keep_current_wording,
    )
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault
    from learnloop.vault.paths import VaultPaths

    try:
        loaded = load_vault(_root(vault))
        repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
        decide = confirm_reword if confirm else keep_current_wording
        report = decide(loaded.root, repository, action_id)
    except FacetIdentityActionError as exc:
        report = {"status": "refused", "code": exc.code, "reason": str(exc)}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output, ok={"applied" if confirm else "kept"})


@facets_app.command("confirm")
def facets_confirm(
    action_id: Annotated[str, typer.Argument(help="A reword waiting for your confirm (`facets actions`).")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Confirm a reword that had no explanatory source behind it: it applies, with an undo.

    The confirm is your verdict (judgment_ledger, judge owner) and writes the
    new wording as your own edit would. A reword whose support is exam
    material only, or whose facet changed since, is refused.
    """
    _decide_reword(action_id, vault, json_output, confirm=True)


@facets_app.command("keep")
def facets_keep(
    action_id: Annotated[str, typer.Argument(help="A reword waiting for your confirm (`facets actions`).")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Keep the facet's current wording: the held reword closes and nothing is written."""
    _decide_reword(action_id, vault, json_output, confirm=False)


__all__ = ["facets_app"]
