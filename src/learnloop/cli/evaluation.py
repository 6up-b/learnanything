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

from learnloop.cli.field import _LEGACY_FALLBACK_HELP, families_eval, field_eval
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
        json_output=json_output,
    )


eval_app.command("families")(families_eval)


def _pf_report(kind: str, vault: Path, round_id: str, output_dir: Path, judge: bool, dry_run: bool,
               max_calls: int, max_retries: int, max_tokens: int, max_cost_usd: float,
               price_per_million: float | None, json_output: bool) -> None:
    import json

    from learnloop.ai.spend import SpendCaps
    from learnloop.cli.embeddings import _cancellation
    from learnloop.ops.pf_reports import pilot_report, scaling_report
    from learnloop.vault.loader import load_vault

    try:
        if not (vault / "learnloop.toml").is_file():
            raise ValueError("--vault must contain learnloop.toml")
        loaded = load_vault(vault)
        caps = SpendCaps(max_calls=max_calls, max_retries=max_retries, max_total_tokens=max_tokens,
                         max_estimated_usd=max_cost_usd)
        runner = pilot_report if kind == "pilot" else scaling_report
        with _cancellation() as stop:
            report = runner(loaded, round_id=round_id, output_dir=output_dir, judge=judge, dry_run=dry_run,
                            caps=caps, price_per_million=price_per_million, cancelled=stop.is_set)
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    typer.echo(json.dumps(report, sort_keys=True, default=str, indent=None if json_output else 2))
    if report["status"] == "cancelled":
        raise typer.Exit(130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(1)


@eval_app.command("pf-pilot")
def pf_pilot_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (use a copy).")],
    round_id: Annotated[str, typer.Option("--round", help="The `learnloop pf generate --round` to report.")],
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Aggregate-only report destination.")] = Path("fixtures-local/reports/pf"),
    judge: Annotated[bool, typer.Option("--judge", help="Run the paid blind pairwise LLM comparison (15 survivors vs 15 single-shot items, two passes).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate the judge; no requests or report files.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Owner price bound for a metered judge route; Codex estimates only.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """PF pilot: survival per filter and per generation path, panel disagreement, cost, usage signals."""
    _pf_report("pilot", vault, round_id, output_dir, judge, dry_run, max_calls, max_retries, max_tokens,
               max_cost_usd, price_per_million, json_output)


@eval_app.command("pf-scaling")
def pf_scaling_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Vault root (use a copy).")],
    round_id: Annotated[str, typer.Option("--round", help="The round generated with --tier cheap and --tier frontier.")],
    output_dir: Annotated[Path, typer.Option("--output-dir", "--output", help="Aggregate-only report destination.")] = Path("fixtures-local/reports/pf"),
    judge: Annotated[bool, typer.Option("--judge", help="Run the paid blind pairwise rating (10 survivors per tier, two passes).")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate the judge; no requests or report files.")] = False,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 1_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Owner price bound for a metered judge route; Codex estimates only.")] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Scaling check: does quality rise with the model? Per tier and per component."""
    _pf_report("scaling", vault, round_id, output_dir, judge, dry_run, max_calls, max_retries, max_tokens,
               max_cost_usd, price_per_million, json_output)
