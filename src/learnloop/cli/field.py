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


def _load_for_step(vault: Path, *, paid: bool):
    """Replay and dry runs read only the vault TOML; a paid step loads like
    `learnloop embeddings backfill`, so the app reads its keys and per-machine
    Codex checkout itself. Neither changes the route settings a cache keys on.
    (T8's success-head paid steps and `field classify-questions` share this.)
    """
    if not paid:
        return _load_offline(vault)
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml; use a backup-API copy.")
    return load_vault(vault)


def _emit(report: dict, json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2))


LEGACY_SECTIONS = frozenset({"predictions", "coverage", "gates", "retention", "propensity"})
FIELD_SECTION = "field"
_LEGACY_FALLBACK_HELP = (
    "Revision policy for attempts without a verified graded snapshot: exclude "
    "(default), or explicit, labelled current_content reconstruction. Defaults to "
    "the vault's field.legacy_fallback."
)


_PROBABILITY_ARM_HELP = (
    "Prepare or load the llm_probability V1-V3 arms: all, v1|v2|v3, decider|llm, or "
    "v<n>/<judge>; repeatable. Needs --llm-cache and field.enabled + "
    "field.llm_probability_enabled. Caps apply per judge."
)
#: Owner decision 2026-10-12: Phase 2's numeric llm_probability arm (route
#: ai.routing.field_llm_probability) is retired; --llm-cache and --prepare-llm
#: now serve only the V1-V3 arms.
_NUMERIC_ARM_RETIRED = (
    "Phase 2's numeric llm_probability arm is retired: pass --probability-arm "
    "(all, v1|v2|v3, decider|llm or v<n>/<judge>) with --llm-cache"
)


def _sections(section: str) -> set[str]:
    """``all`` is the legacy calibration report; ``field`` is opt-in."""
    requested = {part.strip() for part in section.split(",") if part.strip()}
    if "all" in requested:
        requested = (requested - {"all"}) | LEGACY_SECTIONS
    return requested


@field_app.command("data-check")
def field_data_check(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy to inspect.")],
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Count evidence, revision exclusions and independence without model calls."""
    from learnloop.field.outcomes import data_check

    try:
        loaded = _load_offline(vault)
        with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
            # All reads in this report see one ledger snapshot.
            connection.execute("BEGIN")
            report = data_check(connection, loaded, legacy_fallback=legacy_fallback)
        report["vault_validation_issues"] = len(loaded.issues)
        _emit(report, json_output)
    except (ValueError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc


def _replay_inputs(loaded, *, legacy_fallback):
    """One read-only snapshot: rows, signals, frozen priors and the FSRS fit.

    Every report reads the same canonical outcome view; arms never see a store.
    """
    from learnloop.field.outcomes import borrowed_repository, data_check, load_effective_replay_rows
    from learnloop.field.priors import load_frozen_priors
    from learnloop.params.fitted_params import fitted_fsrs_provenance, resolve_fsrs_weights

    with closing(connect(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)) as connection:
        connection.execute("BEGIN")
        # The same leak-aware rows the family-memory projection folds.
        attempts, facets, signals = load_effective_replay_rows(
            connection, loaded, legacy_fallback=legacy_fallback,
        )
        counts = data_check(connection, loaded, legacy_fallback=legacy_fallback)
        general_means, lo_priors, prior_report = load_frozen_priors(connection, attempts, loaded.config)
        repository = borrowed_repository(connection)
        fsrs_fit_id = fitted_fsrs_provenance(repository)
        fsrs_weights = resolve_fsrs_weights(repository) if fsrs_fit_id is not None else None
    return {
        "attempts": attempts,
        "facets": facets,
        "signals": signals, "data_check": counts,
        "general_means": general_means, "lo_priors": lo_priors, "claim_priors": prior_report,
        "fsrs_weights": fsrs_weights, "fsrs_fit_id": fsrs_fit_id,
    }


def _replay(loaded, inputs, *, arms, bootstrap_samples, seed, fast_track_q, extra_arms=(), pairwise=()):
    from learnloop.field.evaluation import evaluate

    if extra_arms:
        from learnloop.field.predictors import registered_predictors

        arms = (*(arms or registered_predictors(include_sweeps=True)), *extra_arms)
    report = evaluate(
        (*inputs["attempts"], *inputs["facets"], *inputs["signals"]),
        arms=arms, bootstrap_samples=bootstrap_samples, seed=seed, fast_track_q=fast_track_q,
        general_means=inputs["general_means"], lo_priors=inputs["lo_priors"],
        config=loaded.config.model_dump(mode="json"),
        fsrs_weights=inputs["fsrs_weights"], fsrs_fit_id=inputs["fsrs_fit_id"],
        pairwise=pairwise,
    )
    report["data_check"] = inputs["data_check"]
    report["claim_priors"] = inputs["claim_priors"]
    report["vault_validation_issues"] = len(loaded.issues)
    return report


def field_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")],
    section: Annotated[str, typer.Option("--section", help="all (legacy calibration: predictions|coverage|gates|retention|propensity), field (reports 1-2), or a comma list such as all,field")] = "all",
    bins: Annotated[int, typer.Option("--bins", min=1, help="Legacy decision-calibration bin count.")] = 10,
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    arm: Annotated[list[str] | None, typer.Option("--arm", help="Repeat to select registered arms; default includes fixed sweeps.")] = None,
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1)] = 1000,
    seed: Annotated[int, typer.Option("--seed")] = 0,
    fast_track_q: Annotated[float, typer.Option("--fast-track-q", min=0.5, max=1.0, help="Frozen simulation threshold; conservative 0.9 until report 2 supports 0.8.")] = 0.9,
    llm_cache: Annotated[Path | None, typer.Option("--llm-cache", help="The --probability-arm cache outside the vault; replay makes zero model calls.")] = None,
    prepare_llm: Annotated[bool, typer.Option("--prepare-llm", help="Explicit paid preparation of the --probability-arm arms before replay; requires --llm-cache and opt-in config.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate optional paid preparation without requests or report writes.")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Conservative combined input/output-token USD rate for paid preparation. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.")] = None,
    output_tokens: Annotated[int, typer.Option("--output-tokens", min=1)] = 256,
    json_output: Annotated[bool, typer.Option("--json")] = False,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Probability arms only: counted retries per judge (a 429, 5xx or failed turn).")] = 2,
    probability_arm: Annotated[list[str] | None, typer.Option("--probability-arm", help=_PROBABILITY_ARM_HELP)] = None,
) -> None:
    """Legacy calibration report by default; `--section field` adds reports 1-2."""
    try:
        valid_sections = LEGACY_SECTIONS | {FIELD_SECTION}
        sections = _sections(section)
        if not sections or sections - valid_sections:
            typer.echo("Unknown evaluation section; use " + "|".join(sorted(valid_sections)) + "|all", err=True)
            raise typer.Exit(code=2)
        if prepare_llm and llm_cache is None:
            raise ValueError("--prepare-llm requires --llm-cache outside the vault")
        if (llm_cache is not None or prepare_llm) and not probability_arm:
            raise ValueError(_NUMERIC_ARM_RETIRED)
        if probability_arm and FIELD_SECTION not in sections:
            raise ValueError("--probability-arm needs --section field")
        loaded = _load_offline(vault)
        legacy_report = None
        if sections - {FIELD_SECTION}:
            from learnloop.db.repositories import Repository
            from learnloop.scheduling.evaluation import build_eval_report

            legacy_report = build_eval_report(
                loaded,
                Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True),
                sections=sections - {FIELD_SECTION}, bins=bins,
            )
        if FIELD_SECTION not in sections:
            if json_output:
                _emit({"version": 1, "eval": legacy_report.as_dict()}, True)
            else:
                typer.echo(legacy_report.format_text())
            return
        inputs = _replay_inputs(loaded, legacy_fallback=legacy_fallback)
        arms = tuple(arm) if arm else None
        spend_report = None
        extra_arms = ()
        pairwise = ()
        if probability_arm:
            from learnloop.ai.spend import SpendCaps
            from learnloop.cli.embeddings import _cancellation
            from learnloop.cli.probability_arms import (
                pairwise_comparisons, prepare_or_load_probability_arms,
            )
            from learnloop.field.probability_arms import parse_arm_selection

            if llm_cache is None:
                raise ValueError("--probability-arm requires --llm-cache outside the vault")
            selection = parse_arm_selection(probability_arm)
            with _cancellation() as stop:
                probability_arms, spend_report = prepare_or_load_probability_arms(
                    loaded, inputs, cache_dir=llm_cache, selection=selection,
                    prepare=prepare_llm, dry_run=dry_run,
                    caps=SpendCaps(
                        max_candidates=max_candidates, max_calls=max_calls, max_pairs=0,
                        max_retries=max_retries, max_total_tokens=max_tokens,
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
            if not probability_arms:
                _emit(spend_report, json_output)
                raise typer.Exit(code=130 if spend_report["status"] == "cancelled" else 1)
            extra_arms = tuple(probability_arms)
            pairwise = tuple(pairwise_comparisons(selection))
        elif dry_run:
            _emit({"status": "dry_run", "calls": 0, "data_check": inputs["data_check"]}, json_output)
            return
        report = _replay(loaded, inputs, arms=arms, bootstrap_samples=bootstrap_samples,
                         seed=seed, fast_track_q=fast_track_q, extra_arms=extra_arms,
                         pairwise=pairwise)
        if spend_report is not None:
            report["offline_preparation"] = spend_report
        from learnloop.field.evaluation import write_reports

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


def families_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
    arm: Annotated[list[str] | None, typer.Option("--arm", help="Repeat to select arms; default is the families arm set.")] = None,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1)] = 1000,
    seed: Annotated[int, typer.Option("--seed")] = 0,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """PF-a report on the shared harness: memory per item/family/LO and idea_hier.

    The same rows, revision policy and replay loop as `--section field`, with
    the families arm set (incumbent, lo_general, idea_hier and the twelve
    memory arms). No model calls; report files are content-addressed.
    """
    from learnloop.field.evaluation import family_arms, report_digest, write_reports

    try:
        loaded = _load_offline(vault)
        inputs = _replay_inputs(loaded, legacy_fallback=legacy_fallback)
        report = _replay(loaded, inputs, arms=tuple(arm) if arm else family_arms(),
                         bootstrap_samples=bootstrap_samples, seed=seed, fast_track_q=0.9)
        files = write_reports(report, output_dir, stem="pf-a-" + report_digest(report)[:16],
                              title="PF-a families replay (research only)")
        if json_output:
            _emit({"version": 1, "status": "complete", "reports": files, "evaluation": report}, True)
        else:
            typer.echo("\n".join((files["json"], files["markdown"])))
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
