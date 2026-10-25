"""`learnloop curriculum cover`: section coverage for a whole book now
(deliverable curriculum C0a; spec_deliverable_curriculum_v1 §6.2).

Owner-run, never on a hot path: no RPC reaches it.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

curriculum_app = typer.Typer(no_args_is_help=True,
                             help="The deliverable curriculum (C0a: section coverage across your books).")


@curriculum_app.command("cover")
def curriculum_cover(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    source: Annotated[str, typer.Option("--source", help="The source (or extraction) whose sections to judge.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="List the learning objects, their candidates and each call's estimated "
                                             "tokens and dollars against the cap; call and write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Judge where your books treat the topics a book's sections suggest (C0a).

    For each learning object whose candidates include a section of this book
    (its provenance, one search per source in the library, your own links),
    one listwise call through ai.routing.section_coverage_judge judges every
    candidate section across the library: introduces, develops, applies,
    mentions or not about it. Exam and held-out material is never a
    candidate. A judgment already stored for the current state is not paid
    for again. curriculum.cover_max_cost_usd caps a metered run, checked
    before each call. Run --dry-run first: it calls nothing and writes
    nothing (its candidates are read by keyword only)."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.source_retrieval.section_coverage import CoverageError, cover_source, enabled
    from learnloop.practice_index.paid import planning_repository

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        if not enabled(loaded):
            raise ValueError("section coverage is off (curriculum.enabled = false)")
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        extraction_id = resolve_extraction_id(repository, source)
        if extraction_id is None:
            raise ValueError(f"no extraction resolves for {source!r}")
        result = cover_source(loaded, repository, extraction_id, dry_run=dry_run)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error, CoverageError) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
