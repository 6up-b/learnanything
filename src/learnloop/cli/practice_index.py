"""`learnloop practice-index`: facet dossiers, find_practice, coverage and the evaluation.

Paid commands (dossiers, eval) estimate first with ``--dry-run`` (no client,
migration or data changes), then run under explicit caps behind their own
switches. ``find`` proposes practice and never serves it.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.embeddings import _cancellation
from learnloop.cli.runtime import _repository, _root
from learnloop.vault.loader import load_vault


practice_index_app = typer.Typer(
    no_args_is_help=True,
    help="The practice index: facet dossiers, find_practice, coverage and its evaluation.",
)

_PRICE_HELP = (
    "USD per million tokens for a metered (non-Codex) LLM route; unknown prices fail closed. "
    "Codex routes run on the subscription and report an estimated_only cost."
)


def _emit(report: dict[str, Any], json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, default=str) if json_output
               else json.dumps(report, indent=2, sort_keys=True, default=str))


def _loaded(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    if loaded.issues:
        raise ValueError(f"Vault has {len(loaded.issues)} validation issues; run doctor first.")
    return loaded


def _exit_for(report: dict[str, Any], ok: set[str]) -> None:
    if report.get("status") == "cancelled":
        raise typer.Exit(code=130)
    if report.get("status") not in ok:
        raise typer.Exit(code=1)


@practice_index_app.command("dossiers")
def practice_index_dossiers(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate calls, tokens and cost; no client, migration or data changes.")] = False,
    facet: Annotated[list[str] | None, typer.Option("--facet", help="Only this facet id; repeatable. Default: every registered facet.")] = None,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0, help="Facets to write in this run.")] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Metered routes only.")] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Metered routes only.")] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help=_PRICE_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Write missing or stale facet dossiers (route ai.routing.practice_dossier).

    A dossier is regenerated only when its facet or its grounding sources change.
    Requires practice_index.dossiers_enabled for paid work. Reports are aggregate.
    """
    from learnloop.practice_index.dossiers import generate_dossiers

    try:
        if price_per_million is not None and price_per_million <= 0:
            raise ValueError("--price-per-million must be positive")
        caps = SpendCaps(max_candidates=max_candidates, max_pairs=0, max_retries=max_retries,
                         max_calls=max_calls, max_total_tokens=max_tokens,
                         max_estimated_usd=max_cost_usd)
        loaded = _loaded(vault)
        if not dry_run:
            _repository(_root(vault))
        with _cancellation() as stop:
            report = generate_dossiers(loaded, caps=caps, dry_run=dry_run,
                                       price_per_million=price_per_million,
                                       facet_ids=list(facet) if facet else None,
                                       cancelled=stop.is_set)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete"})


@practice_index_app.command("find")
def practice_index_find(
    query: Annotated[str, typer.Argument(help="What you want to practise.")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    limit: Annotated[int | None, typer.Option("--limit", min=1, max=20)] = None,
    learning_object: Annotated[list[str] | None, typer.Option("--learning-object", help="Repeatable.")] = None,
    facet: Annotated[list[str] | None, typer.Option("--facet", help="Repeatable.")] = None,
    mode: Annotated[list[str] | None, typer.Option("--mode", help="Practice mode; repeatable.")] = None,
    exclude: Annotated[list[str] | None, typer.Option("--exclude", help="Item id; repeatable.")] = None,
    rerank: Annotated[bool | None, typer.Option("--rerank/--no-rerank", help="Override practice_index.rerank_enabled.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Propose practice items for a request (the find_practice agent tool). Never serves."""
    from learnloop.practice_index.retrieval import PracticeConstraints, find_practice

    root = _root(vault)
    try:
        loaded = load_vault(root)
        repository = _repository(root)
        constraints = PracticeConstraints(
            limit=limit, learning_object_ids=tuple(learning_object or ()),
            facet_ids=tuple(facet or ()), practice_modes=tuple(mode or ()),
            exclude_item_ids=tuple(exclude or ()), rerank=rerank,
        )
        report = find_practice(loaded, repository, query, constraints, origin="cli")
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    if json_output:
        _emit(report, True)
    elif report.get("status") != "ok":
        typer.echo(report.get("reason") or report.get("status"), err=True)
    else:
        typer.echo(f"{report['path']} path ({report['path_reason']}); rerank: {report['rerank_status']}")
        for item in report["items"]:
            reason = f" - {item['rationale']}" if item.get("rationale") else ""
            typer.echo(f"{item['rank']}. {item['practice_item_id']} [{item['learning_object_title']}]{reason}")
        typer.echo(f"proposal {report['proposal_id']} (proposals only; the scheduler serves)")
    _exit_for(report, {"ok"})


@practice_index_app.command("coverage")
def practice_index_coverage(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    min_eligible: Annotated[int | None, typer.Option("--min-eligible", min=0, help="Default: practice_index.coverage_min_eligible.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Facets with few admissible items: the targets for generating more practice."""
    from learnloop.practice_index.coverage import coverage_report

    root = _root(vault)
    report = coverage_report(load_vault(root), _repository(root), min_eligible=min_eligible)
    _emit({"status": "ok", **report}, json_output)


@practice_index_app.command("status")
def practice_index_status(
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Dossier freshness, index completeness, the chosen path and usage counts."""
    from contextlib import closing

    from learnloop.db.connection import connect
    from learnloop.db.stores.practice_index import latest_evaluation
    from learnloop.practice_index.dossiers import dossier_status
    from learnloop.practice_index.retrieval import choose_path, load_snapshot
    from learnloop.practice_index.usage import usage_summary

    root = _root(vault)
    loaded = load_vault(root)
    repository = _repository(root)
    snapshot = load_snapshot(loaded, repository)
    path, reason = choose_path(loaded, repository, snapshot)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        evaluation = latest_evaluation(connection)
    _emit({
        "status": "ok", "dossiers": dossier_status(loaded, repository),
        "index": {**snapshot.manifest(), "dossier_available": snapshot.dossier_available,
                  "dossier_reason": snapshot.dossier_reason,
                  "embedding_reason": snapshot.embedding_reason},
        "path": path, "path_reason": reason,
        "latest_evaluation": None if evaluation is None else {
            key: evaluation[key] for key in ("id", "created_at", "winner", "reason", "manifest_hash")
        },
        "usage": usage_summary(repository),
    }, json_output)


@practice_index_app.command("usage")
def practice_index_usage(
    proposal: Annotated[str, typer.Option("--proposal", help="A find_practice proposal id.")],
    item: Annotated[str, typer.Option("--item", help="A proposed practice item id.")],
    signal: Annotated[str, typer.Option("--signal", help="practised | skipped | too_easy | not_what_i_asked")],
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Record a learner's usage signal on a proposed item (judgment_ledger)."""
    from learnloop.practice_index.usage import record_practice_usage

    root = _root(vault)
    try:
        report = {"status": "ok", **record_practice_usage(
            _repository(root), proposal_id=proposal, practice_item_id=item, signal=signal,
        )}
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"ok"})


def practice_index_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate calls, tokens and cost; no client, migration or data changes.")] = False,
    queries: Annotated[int, typer.Option("--queries", min=0, help="Target size of the LLM-written held-out query set.")] = 40,
    logged_queries: Annotated[int, typer.Option("--logged-queries", min=0, help="Real find_practice requests to include.")] = 20,
    seed: Annotated[int, typer.Option("--seed")] = 0,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1)] = 1000,
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 500,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0, help="Query-item label pairs.")] = 4000,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 400,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 4,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Metered routes only.")] = 4_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0, help="Metered routes only.")] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help=_PRICE_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Retrieval evaluation: dossier two-level search vs direct item search.

    LLM relevance labels in two passes (agreement reported), Recall@10 and
    nDCG@10 with bootstrap intervals, and the bar that decides find_practice's
    path. Requires practice_index.evaluation_enabled for paid work.
    """
    from learnloop.practice_index.evaluation import run_retrieval_evaluation

    try:
        if price_per_million is not None and price_per_million <= 0:
            raise ValueError("--price-per-million must be positive")
        caps = SpendCaps(max_candidates=max_candidates, max_pairs=max_pairs,
                         max_retries=max_retries, max_calls=max_calls,
                         max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd)
        loaded = _loaded(vault)
        if not dry_run:
            _repository(_root(vault))
        with _cancellation() as stop:
            report = run_retrieval_evaluation(
                loaded, caps=caps, dry_run=dry_run, queries=queries,
                logged_queries=logged_queries, seed=seed, bootstrap_samples=bootstrap_samples,
                price_per_million=price_per_million,
                output_dir=None if dry_run else output_dir, cancelled=stop.is_set,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
    _exit_for(report, {"dry_run", "complete"})


practice_index_app.command("eval")(practice_index_eval)


@practice_index_app.command("tool-spec")
def practice_index_tool_spec() -> None:
    """Print the find_practice agent-tool declaration (JSON schema)."""
    from learnloop.practice_index.tool import FIND_PRACTICE_TOOL

    typer.echo(json.dumps(FIND_PRACTICE_TOOL, indent=2, sort_keys=True))
