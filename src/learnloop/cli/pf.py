"""`learnloop pf`: PF-b generate -> verify -> select -> publish (Slice 2 §5.3-§5.4).

Every paid command estimates first with ``--dry-run`` and runs under explicit
caps. Generation and publication are gated by ``pf.generation_enabled`` (off in
the template). Reports are aggregate-only: counts, models and costs, never
item or learner text.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.embeddings import _cancellation
from learnloop.vault.loader import load_vault

pf_app = typer.Typer(no_args_is_help=True, help="Generate, verify, select and publish practice-family items.")


def _emit(report: dict, json_output: bool, ok: set[str] = frozenset({"dry_run", "complete"})) -> None:
    typer.echo(json.dumps(report, sort_keys=True, default=str, indent=None if json_output else 2))
    if report.get("status") == "cancelled":
        raise typer.Exit(130)
    if report.get("status") not in ok:
        raise typer.Exit(1)


def _loaded(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")
    loaded = load_vault(vault)
    if loaded.issues:
        raise ValueError(f"Vault has {len(loaded.issues)} validation issues; run doctor first")
    return loaded


@pf_app.command("generate")
def pf_generate(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; rehearse on a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate calls, tokens and cost; no client, migration or data change.")] = False,
    path: Annotated[str, typer.Option("--path", help="generator | ensemble | single_shot (pilot baseline, never published) | auto (family source_kind, else pf.default_path).")] = "auto",
    relation: Annotated[str, typer.Option("--relation", help="Declared variant relation for ensemble proposals; programs draw isomorphs.")] = "isomorph",
    family: Annotated[list[str] | None, typer.Option("--family", help="Activity family id; repeatable. Default: every family with an active member.")] = None,
    learning_object_id: Annotated[str | None, typer.Option("--lo")] = None,
    seed_item: Annotated[list[str] | None, typer.Option("--seed-item", help="Create an owner-authored single-item family for this unfamilied item; repeatable.")] = None,
    count: Annotated[int | None, typer.Option("--count", min=1, max=60, help="Candidates per family (default pf.candidates_per_family).")] = None,
    select: Annotated[int | None, typer.Option("--select", min=1, help="Survivors to select per family (default pf.select_per_family).")] = None,
    round_id: Annotated[str | None, typer.Option("--round", help="Job round; reruns of a round resume. Default: today's UTC date.")] = None,
    tier: Annotated[str | None, typer.Option("--tier", help="Scaling check: run generator and judge roles on pf.scaling.cheap or .frontier.")] = None,
    publish: Annotated[bool, typer.Option("--publish/--no-publish", help="Publish selected survivors under today's cap.")] = True,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 60,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0)] = 2000,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 400,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 4_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 2.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive owner price bound (USD per million tokens, at least the higher input/output rate). Unknown prices fail closed on metered routes; Codex routes run on the subscription and only estimate cost.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Over-generate, verify, filter, select and publish verified items per family.

    Rerun the same --round to resume: finished paid calls are checkpointed and
    never repaid. SIGINT/SIGTERM stops before the next request.
    """
    from learnloop.ops.pf_generation import GenerationOptions, generate_practice

    try:
        loaded = _loaded(vault)
        options = GenerationOptions(
            path=path, relation=relation, count=count, select=select, round=round_id, tier=tier,
            publish=publish, family_ids=tuple(family or ()), learning_object_id=learning_object_id,
            seed_items=tuple(seed_item or ()),
        )
        caps = SpendCaps(max_candidates=max_candidates, max_pairs=max_pairs, max_calls=max_calls,
                         max_retries=max_retries, max_total_tokens=max_tokens,
                         max_estimated_usd=max_cost_usd)
        with _cancellation() as stop:
            report = generate_practice(loaded, caps=caps, options=options, dry_run=dry_run,
                                       price_per_million=price_per_million, cancelled=stop.is_set)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)


@pf_app.command("publish")
def pf_publish(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Publish selected, verified candidates left over by a capped day. No model calls."""
    from learnloop.ops.pf_generation import publish_backlog

    try:
        report = publish_backlog(_loaded(vault))
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)


@pf_app.command("status")
def pf_status_command(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Candidate counts by path and status, and today's remaining publish slots."""
    from learnloop.ops.pf_generation import pf_status

    try:
        report = {"status": "complete", **pf_status(_loaded(vault))}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
