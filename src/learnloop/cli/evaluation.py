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
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="Conservative combined input/output-token USD rate for paid preparation.")] = None,
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
