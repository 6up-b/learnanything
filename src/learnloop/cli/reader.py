"""`learnloop reader report`: the Reader's workflow funnel (reader workbench RW1a).

Read-only: the database is opened read-only, never migrated, and no model is
called. The report carries ids, counts, shares and timings, never learner text.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated, Any

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

reader_app = typer.Typer(no_args_is_help=True, help="The Reader (RW1a: the workflow funnel report).")
cues_app = typer.Typer(no_args_is_help=True, help="Margin cues (RW3b): discovered links for a source.")
reader_app.add_typer(cues_app, name="cues")

_RELATIVE = re.compile(r"^(\d+)([dh])$")


def _since(value: str | None, now: datetime) -> str | None:
    if value is None:
        return None
    match = _RELATIVE.match(value.strip())
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        return (now - (timedelta(days=amount) if unit == "d" else timedelta(hours=amount))).isoformat()
    return value


@reader_app.command("report")
def reader_report(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only).")],
    since: Annotated[
        str | None,
        typer.Option("--since", help="Only activity at or after this ISO time, or a span such as 7d or 24h."),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Workflows with denominators: selection -> action -> result -> back to reading,
    inquiries, detours (return rate, cost), proactive load, waiting behaviour, visits."""

    from learnloop.reader.reader_report import build_reader_report

    now = datetime.now(UTC)
    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        skipped_section_los = None
        if loaded.config.reading_paths.enabled:
            # RW7b (§15's reading-path row): the skipped sections' LOs, read
            # through a read-only attach (the report's reader has no vault).
            from learnloop.db.repositories import Repository
            from learnloop.source_retrieval.reading_paths import skipped_section_learning_objects

            skipped_section_los = skipped_section_learning_objects(loaded, Repository.attach(path, read_only=True))
        report = build_reader_report(path, since=_since(since, now), now=now,
                                     reading_paths_enabled=loaded.config.reading_paths.enabled,
                                     figures_enabled=bool(loaded.config.figures.enabled),
                                     figure_offers_enabled=bool(loaded.config.figures.enabled
                                                                and loaded.config.figures.offers_enabled),
                                     figure_show_me_enabled=bool(loaded.config.figures.enabled
                                                                 and loaded.config.figures.show_me_enabled),
                                     figure_sketch_enabled=bool(loaded.config.figures.enabled
                                                                and loaded.config.figures.sketch_enabled),
                                     figure_rich_enabled=bool(loaded.config.figures.enabled
                                                              and loaded.config.figures.rich_tiers_enabled),
                                     skipped_section_los=skipped_section_los)
        if loaded.config.figures.enabled and loaded.config.figures.prefetch_enabled:
            # RW5d P5 (spec §10b.6): the prefetch block (absent with the switch off).
            from learnloop.figures.prefetch_ledger import add_report_block

            add_report_block(report, path, since=_since(since, now), plan_providers=_plan_providers(loaded), now=now)
        if loaded.config.figures.enabled and loaded.config.figures.checked_labels_enabled:
            # RW5c (spec §12): the source-check block (absent with the switch off: G23g).
            from learnloop.figures.source_check import add_report_block as add_source_checks

            add_source_checks(report, path, since=_since(since, now))
        report["reader_inquiry"] = loaded.config.reader_inquiry.model_dump(mode="json")
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@reader_app.command("figure-checks")
def figure_checks(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    recheck: Annotated[
        bool, typer.Option("--recheck", help="Recheck stored grammar figures by code (no model client): those with no "
                                             "check at the current certification version.")
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="With --recheck: look at every stored grammar figure and report by "
                                             "reason key; write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Reader RW5c: what "matches the book's equation (checked)" covers (spec §12). Without
    --recheck, each element carrying the claim, for your audit: the book's equation as
    LearnLoop read it, its page and the figure's definition. Never calls a model."""

    from learnloop.db.repositories import Repository
    from learnloop.figures import service as FS
    from learnloop.figures import source_check as SC

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        if dry_run and not recheck:
            raise ValueError("--dry-run goes with --recheck")
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        repository = Repository.attach(path, read_only=dry_run or not recheck)
        enabled = SC.enabled(loaded)
        payload: dict[str, object] = {"status": "ok", "enabled": enabled, "dry_run": dry_run}

        def withheld(row: Any) -> bool:
            return FS.row_withheld(loaded, repository, row) is not None

        if not recheck:
            payload.update(SC.audit(repository, withheld=withheld) if enabled else {})
        elif enabled:
            payload.update(SC.coverage(loaded, repository, dry_run=dry_run, withheld=withheld))
        typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


def _plan_providers(loaded: object) -> list[str]:
    """RW5d P5: the vault's plan profiles (the prefetch block reads the plan's load from their receipts)."""

    from learnloop.figures.prefetch_ledger import plan_providers

    return sorted(plan_providers(loaded))


@cues_app.command("discover")
def cues_discover(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    source: Annotated[str, typer.Option("--source", help="The source (or extraction) to discover cue links for.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="List the targets, their keyword shortlists and a spend plan; call and "
                                             "write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Find a source's discovered margin-cue links now (what opening it in the Reader
    does in the background): the open targets, each one's shortlist and one cue
    judgment each, under cues.max_calls_per_source_open (every request, a retry
    included) and cues.max_daily_cost_usd (query embeddings included). Run
    --dry-run first: it reads keyword matches only, names the targets already
    settled, and gives the spend plan (route, cost basis, estimated tokens and
    dollars, caps); it calls nothing."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.practice_index.paid import planning_repository
    from learnloop.source_retrieval.passage_cues import discover

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        extraction_id = resolve_extraction_id(repository, source)
        if extraction_id is None:
            raise ValueError(f"no extraction resolves for {source!r}")
        result = discover(loaded, repository, extraction_id, dry_run=dry_run)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@reader_app.command("label-roles")
def reader_label_roles(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    source: Annotated[str, typer.Option("--source", help="The source (or extraction) to label.")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Give the batch plan, its estimated tokens and dollars and the cap; "
                                             "call and write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Label a source's passages with instructional roles now (RW4e).

    Its blocks in reading order, without solutions, held-out or exam material,
    in listwise batches through ai.routing.role_labeller; each role is written
    as a source-object proposal (the model's label, used only to find passages,
    never to exclude). roles.batch_max_cost_usd caps the run, checked before
    each batch call. A rerun resumes after the passages already labelled. Run
    --dry-run first: it calls nothing and writes nothing."""

    from learnloop.content.sources.source_outline import resolve_extraction_id
    from learnloop.practice_index.paid import planning_repository
    from learnloop.source_retrieval.role_labeller import label_roles

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        extraction_id = resolve_extraction_id(repository, source)
        if extraction_id is None:
            raise ValueError(f"no extraction resolves for {source!r}")
        result = label_roles(loaded, repository, extraction_id, dry_run=dry_run)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
