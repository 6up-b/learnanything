"""Explicit, read-only offline evaluation; does not initialize or migrate a vault."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.cli.field import field_eval
from learnloop.cli.runtime import _root
from learnloop.db.repositories import Repository
from learnloop.evaluation.report import evaluate, write_report
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

eval_app = typer.Typer(invoke_without_command=True, help="Read-only calibration and offline predictor evaluation.")


@eval_app.callback()
def evaluate_existing(
    ctx: typer.Context,
    vault: Annotated[Path | None, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")] = None,
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
    """Preserve `learnloop eval --vault ...`; `--section field` writes reports 1-2."""
    if ctx.invoked_subcommand is not None:
        return
    field_eval(
        vault=_root(vault), section=section, bins=bins, output_dir=output_dir, arm=arm,
        bootstrap_samples=bootstrap_samples, seed=seed, fast_track_q=fast_track_q,
        llm_cache=llm_cache, prepare_llm=prepare_llm, dry_run=dry_run,
        max_candidates=max_candidates, max_calls=max_calls, max_tokens=max_tokens,
        max_cost_usd=max_cost_usd, price_per_million=price_per_million,
        output_tokens=output_tokens, json_output=json_output,
    )


@eval_app.command("families")
def eval_families(
    vault: Annotated[Path, typer.Option("--vault")],
    output: Annotated[Path, typer.Option("--output")] = Path("fixtures-local/reports"),
    legacy_fallback: Annotated[str, typer.Option("--legacy-fallback",
        help="exclude (default), or explicit current_content reconstruction.")] = "exclude",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Replay memory per item/family/LO and idea_hier without any model calls."""
    loaded = load_vault(vault)
    repository = Repository.attach(VaultPaths(loaded.root, loaded.config).sqlite_path, read_only=True)
    try:
        report = evaluate(loaded, repository, legacy_fallback=legacy_fallback)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    paths = write_report(report, output)
    typer.echo(json.dumps(report, sort_keys=True) if json_output else
               "\n".join(str(path) for path in paths))
