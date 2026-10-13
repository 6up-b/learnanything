"""`learnloop sources`: Slice 2 T6 source retrieval from the command line.

``report`` reads the tutor questions' receipts back: each retrieval step's p50
and p90 wall time and how often it went over the soft deadline (the owner
logs the tutor's retrieval time rather than cancelling it, 2026-10-12), plus
the LLM answers cut off by their output budget. ``search`` is the library search the reader runs (keyword while typing; with
``--deep`` also meaning and, for a conceptual question, the LLM rewrite: paid
calls under one budget, ``--max-calls`` / ``--max-tokens`` / ``--max-cost-usd``,
planned without any call by ``--dry-run``). ``suggest-lo`` shows a span's provenance-linked learning
objects or, when it has none, the labelled nearest-LO suggestions. Neither
writes anything except receipts, cached query vectors and checkpoints of the
calls a deep search makes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault

sources_app = typer.Typer(no_args_is_help=True, help="Slice 2 T6 source retrieval: search and span -> LO suggestions.")


def _open(vault: Path, *, migrate: bool = True):
    from learnloop.practice_index.paid import planning_repository
    from learnloop.vault.paths import VaultPaths

    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    try:
        # A dry run attaches read-only and never migrates.
        return loaded, planning_repository(sqlite_path, dry_run=not migrate)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@sources_app.command("search")
def sources_search(
    query: Annotated[str, typer.Argument(help="What to find in the source library.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for experiments.")],
    deep: Annotated[bool, typer.Option("--deep", help="Also search by meaning (stored source-block vectors; one cached, capped query embedding) and rewrite a conceptual question (route source_query_rewrite). Paid: dry-run first.")] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=200)] = 20,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the planned paid calls and their estimated cost; call and write nothing.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0, help="Cap on the deep search's paid requests (rewrite, its retry, query embedding).")] = 3,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Cap on the deep search's estimated tokens (a rewrite reserves its full output budget, a truncation retry twice that).")] = 120_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0.0, help="Cap on the deep search's estimated metered cost (USD).")] = 0.25,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search every reader-enabled source, as the reader's library search does."""

    from learnloop.ai.spend import SpendBudget
    from learnloop.source_retrieval.library import deep_search_caps, plan_library_search, search_library

    loaded, repository = _open(vault, migrate=not dry_run)
    caps = deep_search_caps(max_calls=max_calls, max_tokens=max_tokens, max_cost_usd=max_cost_usd)
    if dry_run:
        plan = plan_library_search(loaded, repository, query=query, deep=deep, caps=caps)
        if json_output:
            typer.echo(json.dumps(plan, sort_keys=True, default=str))
            return
        typer.echo(f"dry run: {plan['status']}; {plan['calls']} paid call(s) at most; "
                   f"estimated ${plan['estimated_usd']}" if plan.get("estimated_usd") is not None
                   else f"dry run: {plan['status']}; {plan['calls']} paid call(s) at most; cost unknown")
        for step in ("rewrite", "query_embedding"):
            if step in plan:
                entry = plan[step]
                typer.echo(f"  {step}: {entry.get('status')} ({entry.get('calls', 0)} call(s))"
                           + (f": {entry['reason']}" if entry.get("reason") else ""))
        meaning = plan.get("meaning_search") or {}
        if meaning:
            typer.echo(f"  meaning search: {meaning.get('status')}"
                       + (f" ({meaning['reason']})" if meaning.get("reason") else ""))
        return
    report = search_library(loaded, repository, query=query, limit=limit, deep=deep,
                            budget=SpendBudget(caps) if deep else None)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True, default=str))
        return
    typer.echo(f"{len(report['hits'])} hits across {report['searched_sources']} sources; "
               f"basis: {report.get('basis', 'substring')}")
    for note in (report.get("retrieval") or {}).get("notes", []):
        typer.echo(f"  note: {note}")
    for rank, hit in enumerate(report["hits"], start=1):
        where = " · ".join(str(part) for part in (hit.get("section"), f"p.{hit['page']}" if hit.get("page") is not None else None) if part)
        typer.echo(f"{rank:>3}. {hit['source_title']}{(' · ' + where) if where else ''}  "
                   f"[{hit['extraction_id']}/{hit['span_id']}] {','.join(hit.get('matched_by', []))}")
        typer.echo(f"     {hit['snippet']}")


@sources_app.command("suggest-lo")
def sources_suggest_lo(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    extraction_id: Annotated[str, typer.Option("--extraction", help="Extraction id of the span.")],
    span_id: Annotated[str, typer.Option("--span", help="Span id.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Provenance-linked LOs for a span, else labelled nearest-LO suggestions (no calls)."""

    from learnloop.source_retrieval.suggest import suggest_learning_objects

    loaded, repository = _open(vault)
    report = suggest_learning_objects(loaded, repository, extraction_id=extraction_id, span_id=span_id)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
        return
    typer.echo(f"status: {report['status']}")
    for lo_id in report["provenance"]:
        typer.echo(f"  provenance: {lo_id}")
    for entry in report["suggestions"]:
        typer.echo(f"  suggestion (not a provenance link): {entry['learning_object_id']} "
                   f"{entry['title']} [{', '.join(entry['basis'])}]")


@sources_app.command("report")
def sources_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    since: Annotated[str | None, typer.Option("--since", help="Only questions asked at or after this ISO time.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Tutor-span retrieval timing per step (p50/p90, over the soft deadline) and truncated answers."""

    from learnloop.source_retrieval.timing import tutor_timing_report

    loaded, repository = _open(vault, migrate=False)
    config = loaded.config.source_retrieval
    report = tutor_timing_report(repository, soft_deadline_seconds=config.retrieval_timeout_seconds,
                                 cancels_at_deadline=config.tutor_deadline_cancels, since=since)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True))
        return
    deadline = report["soft_deadline_seconds"]
    typer.echo(f"{report['questions']} tutor question(s) with timed retrieval; soft deadline {deadline:g} s "
               f"({'cancels' if report['cancels_at_deadline'] else 'logged, never cancelled'})")
    typer.echo(f"{'step':<16}{'n':>5}{'p50 ms':>10}{'p90 ms':>10}{'max ms':>10}{'> deadline':>12}")
    for step, entry in report["steps"].items():
        def cell(value):
            return "-" if value is None else f"{value:.0f}"
        typer.echo(f"{step:<16}{entry['n']:>5}{cell(entry['p50_ms']):>10}{cell(entry['p90_ms']):>10}"
                   f"{cell(entry['max_ms']):>10}{entry['over_soft_deadline']:>12}")
    for step, count in report["over_soft_deadline"].items():
        typer.echo(f"  note: {step} exceeded the {deadline:g} s soft deadline on {count} question(s)")
    if report["basis"]:
        typer.echo("basis: " + ", ".join(f"{name} {count}" for name, count in report["basis"].items()))
    if report["pool"]:
        typer.echo("pool: " + ", ".join(f"{name} {count}" for name, count in report["pool"].items()))
    truncated = report["truncated_answers"]
    if truncated:
        typer.echo("truncated LLM answers (each retried once at double the budget):")
        for entry in truncated:
            typer.echo(f"  {entry['purpose']} {entry['model'] or '?'}: {entry['truncated']}")
    else:
        typer.echo("truncated LLM answers: none")
