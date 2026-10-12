"""`learnloop sources`: Slice 2 T6 source retrieval from the command line.

``search`` is the library search the reader runs (keyword while typing; with
``--deep`` also meaning and, for a conceptual question, the LLM rewrite, each a
capped live call). ``suggest-lo`` shows a span's provenance-linked learning
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


def _open(vault: Path):
    from learnloop.db.repositories import Repository
    from learnloop.vault.paths import VaultPaths

    if not (vault / "learnloop.toml").is_file():
        raise typer.BadParameter("--vault must name a vault containing learnloop.toml")
    loaded = load_vault(vault)
    return loaded, Repository(VaultPaths(loaded.root, loaded.config).sqlite_path)


@sources_app.command("search")
def sources_search(
    query: Annotated[str, typer.Argument(help="What to find in the source library.")],
    vault: Annotated[Path, typer.Option("--vault", help="Vault root; use a fixtures-local copy for experiments.")],
    deep: Annotated[bool, typer.Option("--deep", help="Also search by meaning (stored source-block vectors; one cached, capped query embedding) and rewrite a conceptual question (route source_query_rewrite).")] = False,
    limit: Annotated[int, typer.Option("--limit", min=1, max=200)] = 20,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Search every reader-enabled source, as the reader's library search does."""

    from learnloop.source_retrieval.library import search_library

    loaded, repository = _open(vault)
    report = search_library(loaded, repository, query=query, limit=limit, deep=deep)
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
