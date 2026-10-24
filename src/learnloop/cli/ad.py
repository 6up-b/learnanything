"""`learnloop ad`: adaptive difficulty AD1's owner-run commands (spec §14 AD1).

`ad data-check` is read-only: the database is opened read-only, never
migrated, and no model is called; it prints aggregates only. Run it on a
backup copy.

`ad backfill` is the owner's one-time pass: `--dry-run` opens the database
read-only, calls nothing, writes nothing and prints the plan with its
estimate; a real run audits (`--audit`), forecasts never-attempted items
(`--llm-v1`) and sweeps the reading history (`--reading`) under
`adaptive_difficulty.daily_spend_cap_usd`.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Annotated

import typer

from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

ad_app = typer.Typer(no_args_is_help=True, help="Adaptive difficulty: the data check, backfills, report, eval and relatedness.")


def _vault_root(vault: Path) -> None:
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")


@ad_app.command("data-check")
def data_check_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only; use a backup copy).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The spec's §3.3 tables, first-surface attempts per cell, coverage of latency, ratings
    and hint timing, exam units with and without a facet mapping, and historical attempts by
    revision status. Read-only, no model call."""

    from learnloop.adaptive_difficulty.data_check import data_check
    from learnloop.db.repositories import Repository

    try:
        _vault_root(vault)
        loaded = load_vault(vault, load_environment=False)
        path = VaultPaths(loaded.root, loaded.config).sqlite_path
        report = data_check(loaded, path, repository=Repository.attach(path, read_only=True))
        typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@ad_app.command("backfill")
def backfill_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    audit: Annotated[bool, typer.Option("--audit", help="Audit every active and every held item revision.")] = False,
    llm_v1: Annotated[bool, typer.Option("--llm-v1", help="Forecast the never-attempted items (llm_v1:item).")] = False,
    reading: Annotated[bool, typer.Option("--reading", help="Sweep the reading history (no model call).")] = False,
    limit: Annotated[int | None, typer.Option("--limit", min=1, help="At most this many audits / forecasts.")] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print the plan and the estimate; call and write nothing.")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """AD1's one-time backfills (--audit, --llm-v1, --reading). Run --dry-run first."""

    from learnloop.adaptive_difficulty.backfill import backfill
    from learnloop.practice_index.paid import planning_repository

    try:
        _vault_root(vault)
        if not (audit or llm_v1 or reading):
            raise ValueError("name at least one of --audit, --llm-v1, --reading")
        loaded = load_vault(vault)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run)
        result = backfill(loaded, repository, audit=audit, llm_v1=llm_v1, reading=reading, dry_run=dry_run,
                          limit=limit)
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


def _read_only(vault: Path) -> tuple:
    from learnloop.db.connection import connect
    from learnloop.db.repositories import Repository

    _vault_root(vault)
    loaded = load_vault(vault, load_environment=False)
    path = VaultPaths(loaded.root, loaded.config).sqlite_path
    return loaded, Repository.attach(path, read_only=True), connect(path, read_only=True)


@ad_app.command("report")
def report_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only; use a backup copy).")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print what the report would read; compute nothing.")] = False,
    sensitivity: Annotated[bool, typer.Option("--sensitivity/--no-sensitivity",
                                              help="Rerun with each feature-effect prior shifted ±1 sd.")] = True,
) -> None:
    """The AD2/AD3 report (spec §10.4): scores with the first-attempt split first, field's rule as a
    monitor, confidence sequences, auto-flags, the honest lines, identifiability, time to usable, the dose
    arm and the dose-and-burden analysis. Read-only; no model call."""

    from learnloop.adaptive_difficulty import replay as RP
    from learnloop.adaptive_difficulty.report import build, render_markdown

    try:
        loaded, repository, connection = _read_only(vault)
        try:
            if dry_run:
                events = RP.load_events(connection, loaded, repository)
                result = {"status": "dry_run", "inputs": events.summary, "model_calls": 0,
                          "writes": 0, "arms": "ad_threshold@subject, @subject_uniform, @lo and the §10.4 arms"}
                typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
                return
            report = build(loaded, repository, connection, sensitivity=sensitivity)
        finally:
            connection.close()
        if json_output:
            typer.echo(json.dumps(report, sort_keys=True, default=str))
        else:
            typer.echo(render_markdown(report))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@ad_app.command("eval")
def eval_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (read-only; use a backup copy).")],
    arms: Annotated[str | None, typer.Option("--arms", help="Comma-separated arms (default: every §10.4 arm).")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The §10.4 harness arms, scored prequentially (first-attempt split first). Read-only; no model call."""

    from learnloop.adaptive_difficulty import arms as A
    from learnloop.adaptive_difficulty.report import SPLITS, arm_scores

    try:
        loaded, repository, connection = _read_only(vault)
        try:
            selected = tuple(a.strip() for a in arms.split(",")) if arms else A.DEFAULT_ARMS
            log = A.prequential(loaded, repository, connection, arms=selected)
        finally:
            connection.close()
        names = sorted({name for record in log["records"] for name in record.p})
        result = {"arms": {name: {("all" if s is None else s): arm_scores(log["records"], name, s) for s in SPLITS}
                           for name in names}, "records": len(log["records"]), "field_coverage": log["field_coverage"]}
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc


@ad_app.command("relatedness")
def relatedness_command(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root.")],
    subject: Annotated[str | None, typer.Option("--subject", help="One subject (default: every subject).")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print the plan and the estimate; call and write nothing.")] = False,
    adopt: Annotated[bool, typer.Option("--adopt", help="Adopt the proposals in force as the next coupling version.")] = False,
    shadow: Annotated[bool, typer.Option("--shadow", help="Print what adopting a later version would change; write nothing.")] = False,
    confirm_reinterpretation: Annotated[bool, typer.Option(
        "--confirm-reinterpretation", help="Adopt a later coupling version after reading its --shadow report.")] = False,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """The relatedness proposal's backfill per subject (spec §5.10): one LLM call per subject on
    ai.routing.llm_probability_llm, reading only the subject's LO and facet text, the concept graph and
    item stems (never learner data or held-out text), inside adaptive_difficulty.daily_spend_cap_usd;
    later calls re-propose only the units that changed. --adopt then adopts the proposals in force as the
    subject's next coupling version: the first applies to the whole history by one rebuild; a later one is a
    reinterpretation, adopted only with --confirm-reinterpretation after its --shadow report."""

    from learnloop.adaptive_difficulty import relatedness as R
    from learnloop.practice_index.paid import planning_repository

    try:
        _vault_root(vault)
        loaded = load_vault(vault)
        repository = planning_repository(VaultPaths(loaded.root, loaded.config), dry_run=dry_run or shadow)
        chosen = [subject] if subject else R.subjects(loaded)
        if shadow:
            result = {"status": "shadow", "reports": [R.shadow_report(loaded, repository, name) for name in chosen],
                      "model_calls": 0, "writes": 0}
        elif dry_run:
            from contextlib import closing

            from learnloop.adaptive_difficulty.backfill import llm_plan
            from learnloop.db.connection import connect
            from learnloop.db.stores import ad_serving

            prompts = []
            units = {}
            for name in chosen:
                inputs = R.subject_inputs(loaded, repository, name)
                with closing(connect(repository.sqlite_path, read_only=True)) as connection:
                    runs = ad_serving.relatedness_runs(connection, subject_id=name)
                touched = R.touched_units(inputs, runs)
                if touched and inputs["payload"]["learning_objects"]:
                    prompts.append(R.prompt(R.focus(inputs, touched)))
                units[name] = {"learning_objects": len(inputs["payload"]["learning_objects"]),
                               "items": len(inputs["item_ids"]), "units_to_propose": len(touched),
                               "input_hash": inputs["input_hash"]}
            plan = llm_plan(loaded, R.ROUTE, prompts, R.RelatednessV1, role="ad_relatedness", retries=1)
            result = {"status": "dry_run", "subjects": units, "plan": plan, "model_calls": 0, "writes": 0,
                      "learned_coupling": R.coupling_on(loaded.config)}
        else:
            outcomes = [R.propose_subject(loaded, repository, name).as_dict() for name in chosen]
            adopted = [R.adopt(repository, name, adopted_by="owner_backfill",
                               confirm_reinterpretation=confirm_reinterpretation) for name in chosen] if adopt else []
            result = {"status": "ran", "proposals": outcomes, "adopted": adopted}
        typer.echo(json.dumps(result, sort_keys=True, indent=None if json_output else 2, default=str))
    except (ValueError, OSError, sqlite3.Error) as exc:
        typer.echo(json.dumps({"status": "invalid", "reason": str(exc)}, sort_keys=True))
        raise typer.Exit(code=1) from exc
