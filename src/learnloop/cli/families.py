"""Explicit family authoring; no background review queue or live retention key."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.embeddings import _cancellation
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


families_app = typer.Typer(no_args_is_help=True, help="Propose practice families and undo an applied decision.")


def _emit(report: dict, json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(1)


@families_app.command("propose")
def families_propose(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate only; no paid calls or data changes.")] = False,
    learning_object_id: Annotated[str | None, typer.Option("--lo")] = None,
    judge_revision: Annotated[str, typer.Option(
        "--judge-revision",
        help="Checkpoint revision; change this when re-evaluating a retargeted model alias.",
    )] = "1",
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 200,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive owner price bound (USD per million tokens, at least the higher input/output rate). Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Two independent passes must agree on every pair; ambiguous items stay unfamilied.

    Rerun to resume persisted verdicts. SIGINT/SIGTERM saves the current paid
    verdict, then stops. Accepted family/proposal IDs can be passed to undo.
    Large LOs require an existing complete item/stem embedding backfill.
    """
    from learnloop.ops.family_proposals import propose_families

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        if loaded.issues:
            raise ValueError(f"Vault has {len(loaded.issues)} validation issues; run doctor first")
        with _cancellation() as stop:
            report = propose_families(
                loaded, dry_run=dry_run, learning_object_id=learning_object_id,
                judge_revision=judge_revision,
                price_per_million=price_per_million, cancelled=stop.is_set,
                caps=SpendCaps(
                    max_candidates=max_candidates, max_pairs=max_pairs, max_calls=max_calls,
                    max_retries=max_retries, max_total_tokens=max_tokens,
                    max_estimated_usd=max_cost_usd,
                ),
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)


@families_app.command("undo")
def families_undo(
    decision: Annotated[str, typer.Argument(help="Applied family ID or proposal ID.")],
    vault: Annotated[Path, typer.Option("--vault")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Undo in one step, retaining historical verdicts and each item's card."""
    from learnloop.substrate.families import undo_family

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        repository = Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)
        with repository.connection() as connection:
            row = connection.execute(
                "SELECT left_id AS id FROM judgment_ledger "
                "WHERE task='family_decision' AND verdict='accept' "
                "AND (left_id=? OR json_extract(rationale,'$.plan.family.id')=?) "
                "ORDER BY created_at DESC,id DESC LIMIT 1",
                (decision, decision),
            ).fetchone()
        if row is None:
            raise ValueError("No applied family decision matches that ID")
        undo_family(loaded, repository, row["id"])
        report = {"status": "complete", "proposal_id": row["id"], "action": "undo"}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
