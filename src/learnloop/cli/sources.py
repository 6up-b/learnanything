"""`learnloop sources`: Slice 2 T6 source retrieval from the command line.

``search`` is the library search the reader runs (keyword while typing; with
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
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0, help="Cap on the deep search's estimated tokens.")] = 60_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0.0, help="Cap on the deep search's estimated metered cost (USD).")] = 0.02,
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


@sources_app.command("build-preview")
def sources_build_preview(
    source_id: Annotated[str, typer.Argument(help="The book's source id (src_...).")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for experiments.")],
    whole_book: Annotated[bool, typer.Option("--whole-book", help="Preview 'Build questions for the whole book'.")] = False,
    approved: Annotated[bool, typer.Option("--approved", help="Preview as if the learner pressed 'Build them'.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Dry run of an automatic question build for one book (UX Phase 1): what it
    would cover, the route, tokens, money and whether it would ask first or
    stop. Zero model calls; reads only (the database opens read-only)."""

    from learnloop.content.pipeline.add_source import preview_auto_build

    loaded, repository = _open(vault, migrate=False)
    report = preview_auto_build(loaded.root, repository, source_id, whole_book=whole_book, approved=approved)
    if json_output:
        typer.echo(json.dumps(report, sort_keys=True, default=str))
        return
    typer.echo(f"dry run: {report['status']}; 0 model calls")
    if "chapters" in report:
        typer.echo(f"  chapters: {', '.join(report['chapters'])}")
        typer.echo(f"  route: {report['provider']} ({report['cost_basis']}); tokens about {report['estimate_tokens']:,}")
        usd = report.get("estimate_usd")
        typer.echo(f"  money: {'unknown' if usd is None else f'about ${usd:,.2f}'}"
                   + (f"; allowed up to ${report['authorized_usd']:,.2f}" if report.get("authorized_usd") is not None else ""))
