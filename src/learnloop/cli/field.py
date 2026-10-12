"""Offline learner-field inspection and evaluation; never changes serving."""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.db.connection import connect
from learnloop.cli.field_classification import register_classification_command
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths


field_app = typer.Typer(no_args_is_help=True, help="Offline learner-field diagnostics.")
register_classification_command(field_app)


def _load_offline(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml; use a backup-API copy.")
    return load_vault(vault, load_environment=False)


def _emit(report: dict, json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))


@field_app.command("data-check")
def field_data_check(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy to inspect.")],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Count evidence, revision exclusions and independence without model calls."""
    from learnloop.field.outcomes import data_check

    try:
        loaded = _load_offline(vault)
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            # All reads in this report see one ledger snapshot.
            connection.execute("BEGIN")
            report = data_check(connection, loaded)
        report["vault_validation_issues"] = len(loaded.issues)
        _emit(report, json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


def field_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")],
    section: Annotated[str, typer.Option("--section", help="predictions|coverage|gates|retention|propensity|field|all")] = "all",
    bins: Annotated[int, typer.Option("--bins", min=1, help="Legacy decision-calibration bin count.")] = 10,
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    arm: Annotated[list[str] | None, typer.Option("--arm", help="Repeat to select registered arms; default includes fixed sweeps.")] = None,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1)] = 1000,
    seed: Annotated[int, typer.Option("--seed")] = 0,
    fast_track_q: Annotated[float, typer.Option("--fast-track-q", min=0.5, max=1.0, help="Frozen simulation threshold; conservative 0.9 until report 2 supports 0.8.")] = 0.9,
    llm_cache: Annotated[Path | None, typer.Option("--llm-cache", help="Optional prepared probability cache outside the vault; replay makes zero model calls.")] = None,
    prepare_llm: Annotated[bool, typer.Option("--prepare-llm", help="Explicit paid preparation step before replay; requires --llm-cache and opt-in config.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate optional paid preparation without requests or report writes.")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Conservative combined input/output-token USD rate for paid preparation.")] = None,
    output_tokens: Annotated[int, typer.Option("--output-tokens", min=1)] = 256,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Generate reports 1–2: prequential replay and historical fast-track simulation."""
    from learnloop.field.evaluation import evaluate, write_reports
    from learnloop.field.outcomes import data_check, load_attempt_rows, load_facet_rows
    from learnloop.field.signals import enrich_attempts, load_interaction_signals

    try:
        valid_sections = {"predictions", "coverage", "gates", "retention", "propensity", "field"}
        sections = valid_sections if section == "all" else {s.strip() for s in section.split(",") if s.strip()}
        if not sections or sections - valid_sections:
            typer.echo("Unknown evaluation section; use " + "|".join(sorted(valid_sections)) + "|all", err=True)
            raise typer.Exit(code=2)
        if prepare_llm and llm_cache is None:
            raise ValueError("--prepare-llm requires --llm-cache outside the vault")
        loaded = _load_offline(vault)
        legacy_report = None
        if sections - {"field"}:
            from learnloop.db.repositories import Repository
            from learnloop.scheduling.evaluation import build_eval_report

            legacy_report = build_eval_report(
                loaded,
                Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True),
                sections=sections - {"field"}, bins=bins,
            )
        if "field" not in sections:
            if json_output:
                _emit({"version": 1, "eval": legacy_report.as_dict()}, True)
            else:
                typer.echo(legacy_report.format_text())
            return
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            attempts = load_attempt_rows(connection, loaded)
            facets = load_facet_rows(connection, loaded)
            signals = load_interaction_signals(connection, loaded, attempts)
            counts = data_check(connection, loaded)
        attempts = enrich_attempts(attempts, signals)
        facets = enrich_attempts(facets, signals)
        arms = tuple(arm) if arm else None
        spend_report = None
        if llm_cache is not None:
            from learnloop.ai.spend import SpendCaps
            from learnloop.cli.embeddings import _cancellation
            from learnloop.cli.field_llm import prepare_or_load_llm
            from learnloop.field.predictors import registered_predictors

            with _cancellation() as stop:
                llm_arm, spend_report = prepare_or_load_llm(
                    loaded, attempts, cache_dir=llm_cache, prepare=prepare_llm,
                    dry_run=dry_run,
                    caps=SpendCaps(
                        max_candidates=max_candidates, max_calls=max_calls,
                        max_pairs=0, max_retries=0, max_total_tokens=max_tokens,
                        max_estimated_usd=max_cost_usd,
                    ),
                    price_per_million=price_per_million, output_tokens=output_tokens,
                    cancelled=stop.is_set,
                )
            if dry_run:
                _emit(spend_report, json_output)
                if spend_report["status"] != "dry_run":
                    raise typer.Exit(code=1)
                return
            if llm_arm is None:
                _emit(spend_report, json_output)
                raise typer.Exit(code=130 if spend_report["status"] == "cancelled" else 1)
            arms = (*(arms or registered_predictors(include_sweeps=True)), llm_arm)
        elif dry_run:
            _emit({"status": "dry_run", "calls": 0, "data_check": counts}, json_output)
            return
        report = evaluate(
            (*attempts, *facets, *signals),
            arms=arms,
            bootstrap_samples=bootstrap_samples,
            seed=seed,
            fast_track_q=fast_track_q,
            config=loaded.config.model_dump(mode="json"),
        )
        report["data_check"] = counts
        report["vault_validation_issues"] = len(loaded.issues)
        if spend_report is not None:
            report["offline_preparation"] = spend_report
        files = write_reports(report, output_dir)
        response = {"version": 1, "status": "complete", "reports": files, "evaluation": report}
        if legacy_report is not None:
            response["eval"] = legacy_report.as_dict()
            if not json_output:
                typer.echo(legacy_report.format_text())
        _emit(response, json_output)
    except AIProviderUnavailable as exc:
        _emit({"status": "unavailable", "error_type": type(exc).__name__}, json_output)
        raise typer.Exit(code=1) from exc
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
