"""`learnloop eval`: one read-only offline evaluation harness.

The group callback keeps `learnloop eval --vault ...` as the legacy decision
calibration report; `--section field` adds learner-field reports 1-2. The
`families` subcommand is the PF-a arm set over the same harness. None of these
initialize or migrate a vault, and replay never calls a model.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from learnloop.cli.field import (
    _LEGACY_FALLBACK_HELP, _PROBABILITY_ARM_HELP, families_eval, field_eval,
)
from learnloop.cli.runtime import _root

eval_app = typer.Typer(
    invoke_without_command=True,
    help="Read-only calibration report and the offline predictor harness.",
)


@eval_app.callback()
def evaluate_existing(
    ctx: typer.Context,
    vault: Annotated[Path | None, typer.Option("--vault", help="Vault root (use a copy); replay never calls a model.")] = None,
    section: Annotated[str, typer.Option("--section", help="all (legacy calibration: predictions|coverage|gates|retention|propensity), field (reports 1-2), or a comma list such as all,field")] = "all",
    bins: Annotated[int, typer.Option("--bins", min=1, help="Legacy decision-calibration bin count.")] = 10,
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    arm: Annotated[list[str] | None, typer.Option("--arm", help="Repeat to select registered arms; default includes fixed sweeps.")] = None,
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
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
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Conservative combined input/output-token USD rate for paid preparation. Unknown prices fail closed on metered routes; a Codex route runs on the subscription and only estimates cost.")] = None,
    output_tokens: Annotated[int, typer.Option("--output-tokens", min=1)] = 256,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Probability arms only: counted retries per judge (a 429, 5xx or failed turn).")] = 2,
    probability_arm: Annotated[list[str] | None, typer.Option("--probability-arm", help=_PROBABILITY_ARM_HELP)] = None,
) -> None:
    """Calibration report by default; `--section field` writes reports 1-2."""
    if ctx.invoked_subcommand is not None:
        return
    field_eval(
        vault=_root(vault), section=section, bins=bins, output_dir=output_dir, arm=arm,
        legacy_fallback=legacy_fallback, bootstrap_samples=bootstrap_samples, seed=seed,
        fast_track_q=fast_track_q, llm_cache=llm_cache, prepare_llm=prepare_llm,
        dry_run=dry_run, max_candidates=max_candidates, max_calls=max_calls,
        max_tokens=max_tokens, max_cost_usd=max_cost_usd,
        price_per_million=price_per_million, output_tokens=output_tokens,
        json_output=json_output, max_retries=max_retries, probability_arm=probability_arm,
    )


eval_app.command("families")(families_eval)


@eval_app.command("judges")
def judges(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (use a copy for --live-decider).")],
    probe: Annotated[bool, typer.Option("--probe", help="Free reachability check: OpenRouter's public listing for the Decider. No key, no learner text, no cost.")] = False,
    live_decider: Annotated[bool, typer.Option("--live-decider", help="One paid, spend-capped Decider call (under $0.001) with no learner data, to confirm the endpoint and typed answers.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="With --live-decider: resolve the call and print its token and cost estimate; no key is loaded, nothing is sent or written.")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """The judgment routes: resolution, readiness and privacy disclosures (router spec §6.2)."""
    import json
    import sqlite3

    from learnloop.ai.errors import AIProviderUnavailable
    from learnloop.ai.spend import SpendLimitExceeded
    from learnloop.cli.probability_arms import judge_readiness, live_decider_check, live_decider_estimate
    from learnloop.vault.loader import load_vault

    def emit(payload: dict) -> None:
        typer.echo(json.dumps(payload, sort_keys=True, indent=None if json_output else 2))

    try:
        root = _root(vault)
        if not (root / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        # Readiness reads key presence the way the app does; values never print.
        # A dry run loads nothing: no vault .env, no machine settings or
        # overlays, so its key presence is the process environment's alone.
        loaded = load_vault(root, load_environment=not dry_run)
        report = judge_readiness(loaded, probe=probe)
        report["environment_loaded"] = not dry_run
        if live_decider:
            report["live_decider"] = live_decider_estimate(loaded) if dry_run else live_decider_check(loaded)
        elif dry_run:
            raise ValueError("--dry-run applies to --live-decider (readiness alone sends nothing)")
        emit(report)
        if live_decider and dry_run and report["live_decider"]["status"] != "dry_run":
            raise typer.Exit(code=1)
    except (AIProviderUnavailable, SpendLimitExceeded) as exc:
        emit({"status": "unavailable", "error_type": type(exc).__name__, "reason": str(exc)[:300]})
        raise typer.Exit(code=1) from exc
    except (ValueError, OSError, sqlite3.Error) as exc:
        emit({"status": "invalid", "reason": str(exc)})
        raise typer.Exit(code=1) from exc
