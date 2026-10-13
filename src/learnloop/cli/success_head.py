"""`learnloop eval success-head`: the T8 replay report (offline research only).

Read-only over one snapshot of a vault copy. The embedding arms read vectors
already stored by `learnloop embeddings backfill`. The zero-data LLM arm is
router R0's ``llm_probability/v2/llm`` arm (owner decision 2026-10-12): one
implementation, reported here under T8's pre-registered names. It reads R0's
cache outside the vault, filled only by the explicit, spend-capped
`--prepare-llm` step (or by `learnloop eval --section field --probability-arm
v2/llm --prepare-llm`; either reuses the other's paid verdicts). Reports are
aggregates; nothing is activated.
"""
from __future__ import annotations

from contextlib import closing
import math
from pathlib import Path
import sqlite3
from typing import Annotated

import typer

from learnloop.ai.errors import AIProviderUnavailable
from learnloop.ai.spend import SpendCaps
from learnloop.cli.field import _LEGACY_FALLBACK_HELP, _emit, _load_for_step, _replay_inputs
from learnloop.db.connection import connect
from learnloop.field.probability_arms import arm_name
from learnloop.field.success_head import LLM_ARMS
from learnloop.vault.paths import VaultPaths


#: T8's descriptive LLM arms, each the R0 arm it reports (owner decision
#: 2026-10-12: they are comparable and paid for once). T8's arm lacked V2's
#: difficulty prior; the pre-registration (its names, window and
#: recalibration) is unchanged, and the report records the alias.
LLM_ARM_ALIASES: dict[str, str] = dict(zip(
    LLM_ARMS, (arm_name("v2", "llm"), arm_name("v2", "llm", recalibrated=True)), strict=True,
))
LLM_ALIAS_NOTE = (
    "llm_zero_data is router R0's llm_probability/v2/llm arm (owner decision 2026-10-12), "
    "reported under T8's pre-registered names. Against the registered T8 arm: the state "
    "adds V2's difficulty prior (the harness's b and a, and an authored or empirical 0-1 "
    "difficulty when present), the stem is capped at 1,500 characters (registered 6,000), "
    "and the right/wrong window of 25 names earlier items by an excerpt instead of an "
    "opaque reference and shows only interactions before a provable start (none when the "
    "start is unknown). Every scored attempt is predicted. Recalibration is the same "
    "one-intercept MAP under N(0, 1) on past predictions; raw values are clipped to "
    "[0.001, 0.999]."
)


def _load(vault: Path, *, paid: bool):
    return _load_for_step(vault, paid=paid)


def prepare_or_load_zero_data(
    loaded, inputs, *, cache_dir, prepare=False, dry_run=False, caps: SpendCaps,
    price_per_million=None, output_tokens=None, cancelled=lambda: False, routes=None,
):
    """Return ``(aliased arms or None, aggregate report)``; cache-only reads build no client.

    Preparation, cache and ledger are router R0's for ``v2/llm``: a verdict
    already paid for (here or by the field section) is reused, never bought
    again. Both field switches are required (D8).
    """
    from learnloop.cli.probability_arms import prepare_or_load_probability_arms

    if price_per_million is not None and (
        isinstance(price_per_million, bool)
        or not math.isfinite(price_per_million) or price_per_million <= 0
    ):
        raise ValueError("--price-per-million must be finite and positive")
    if output_tokens is not None and (type(output_tokens) is not int or output_tokens <= 0):
        raise ValueError("--output-tokens must be a positive integer")
    arms, report = prepare_or_load_probability_arms(
        loaded, inputs, cache_dir=Path(cache_dir), selection=(("v2", "llm"),), prepare=prepare,
        dry_run=dry_run, caps=caps, price_per_million=price_per_million,
        output_tokens=output_tokens, cancelled=cancelled, routes=routes,
    )
    report["aliases"] = dict(LLM_ARM_ALIASES)
    report["alias_note"] = LLM_ALIAS_NOTE
    if not arms:
        return None, report
    by_name = {arm.name: arm for arm in arms}
    return tuple(by_name[target].aliased(alias) for alias, target in LLM_ARM_ALIASES.items()), report


def success_head_eval(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault copy; replay never calls a model.")],
    output_dir: Annotated[Path, typer.Option("--output", "--output-dir", help="Aggregate-only report destination.")] = Path("fixtures-local/reports"),
    legacy_fallback: Annotated[str | None, typer.Option("--legacy-fallback", help=_LEGACY_FALLBACK_HELP)] = None,
    bootstrap_samples: Annotated[int, typer.Option("--bootstrap-samples", min=1, help="Pre-registered: 1000.")] = 1000,
    seed: Annotated[int, typer.Option("--seed", help="Pre-registered: 0.")] = 0,
    llm_cache: Annotated[Path | None, typer.Option("--llm-cache", help="The llm_probability cache outside the vault (the field section's --llm-cache); its llm_probability/v2/llm arm is T8's zero-data arm. Replay makes zero calls.")] = None,
    prepare_llm: Annotated[bool, typer.Option("--prepare-llm", help="Explicit paid preparation of llm_probability/v2/llm (T8's zero-data arm); requires --llm-cache and both field switches. Verdicts already paid for are reused.")] = False,
    backfill_seen_stems: Annotated[bool, typer.Option("--backfill-seen-stems", help="Explicit paid step: embed (item/stem recipe, ai.routing.embedding) the exact stem each scored attempt showed, retired items and earlier wordings included. Needs both embedding switches; run alone, --dry-run first.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Plan only: coverage, and the spend estimate with --prepare-llm or --backfill-seen-stems. No calls, no writes.")] = False,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0)] = 100,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 100,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0, help="Embedding batch retries (--backfill-seen-stems only); T8's LLM preparation never retries.")] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 100_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option("--price-per-million", min=0, help="USD per million tokens for this invocation's paid step: combined input/output for --prepare-llm (the ai.routing.llm_probability_llm route), input for --backfill-seen-stems. Unknown prices fail closed on metered routes; a Codex route only estimates cost.")] = None,
    output_tokens: Annotated[int | None, typer.Option("--output-tokens", min=1, help="Output-token budget of each LLM-arm request; default: the shared policy (ai.output_tokens or the route's override).")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit stable JSON.")] = False,
) -> None:
    """T8 learner success head replay: emb_ridge's kill rule, gated heads, zero-data LLM.

    Pre-registered in docs/reviews/slice-2-t8.md. Run --dry-run first. The
    embedding arms read stored item/stem vectors for the text each attempt
    showed (--backfill-seen-stems embeds them); the LLM arms are router R0's
    llm_probability/v2/llm under T8's names and need --llm-cache (prepared
    with --prepare-llm here or by the field section). Arms without inputs are
    reported as unavailable. Each paid step runs in its own invocation.
    """
    from learnloop.config import MasteryConfig
    from learnloop.field.evaluation import evaluate, report_digest, write_reports
    from learnloop.field.item_content import load_content_index, seen_stem_records
    from learnloop.field.success_head import PREREGISTRATION, preregistration_hash, success_head_arms
    from learnloop.field.success_head_analysis import make_t8_analysis, summary_lines

    try:
        if prepare_llm and llm_cache is None:
            raise ValueError("--prepare-llm requires --llm-cache outside the vault")
        if prepare_llm and backfill_seen_stems:
            raise ValueError("Run --backfill-seen-stems and --prepare-llm as separate invocations")
        loaded = _load(vault, paid=(backfill_seen_stems or prepare_llm) and not dry_run)
        inputs = _replay_inputs(loaded, legacy_fallback=legacy_fallback)
        sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
        if backfill_seen_stems:
            from learnloop.cli.embeddings import _cancellation
            from learnloop.ops.embedding_backfill import backfill_embeddings

            with closing(connect(sqlite_path, read_only=True)) as connection:
                connection.execute("BEGIN")
                records = seen_stem_records(connection, loaded, inputs["attempts"])
            with _cancellation() as stop:
                backfill = backfill_embeddings(
                    loaded, dry_run=dry_run, recipes=("item/stem",), records=records,
                    caps=SpendCaps(max_candidates=max_candidates, max_calls=max_calls, max_pairs=0,
                                   max_retries=max_retries, max_total_tokens=max_tokens,
                                   max_estimated_usd=max_cost_usd),
                    price_per_million=price_per_million, cancelled=stop.is_set,
                )
            _emit({"status": backfill["status"], "backfill": backfill}, json_output)
            if backfill["status"] not in {"dry_run", "complete"}:
                raise typer.Exit(code=130 if backfill["status"] == "cancelled" else 1)
            return
        with closing(connect(sqlite_path, read_only=True)) as connection:
            connection.execute("BEGIN")
            content, coverage = load_content_index(connection, loaded, inputs["attempts"])
        unavailable = {}
        if not coverage["difficulty"]["solver_panel"]:
            unavailable["success_head+difficulty"] = "no solver_panel difficulty (Phase 5a)"
        llm_arms, llm_report = (), None
        if llm_cache is None:
            for name in LLM_ARMS:
                unavailable[name] = "not run: pass --llm-cache (prepared with --prepare-llm)"
        else:
            from learnloop.cli.embeddings import _cancellation

            with _cancellation() as stop:
                arms, llm_report = prepare_or_load_zero_data(
                    loaded, inputs, cache_dir=llm_cache, prepare=prepare_llm,
                    dry_run=dry_run,
                    caps=SpendCaps(max_candidates=max_candidates, max_calls=max_calls, max_pairs=0,
                                   max_retries=0, max_total_tokens=max_tokens,
                                   max_estimated_usd=max_cost_usd),
                    price_per_million=price_per_million, output_tokens=output_tokens,
                    cancelled=stop.is_set,
                )
            if arms is None and not dry_run:
                _emit({"status": llm_report["status"], "llm": llm_report}, json_output)
                raise typer.Exit(code=130 if llm_report["status"] == "cancelled" else 1)
            llm_arms = arms or ()
        if dry_run:
            plan = {
                "status": "dry_run", "calls": 0, "writes": 0,
                "preregistration": {"version": PREREGISTRATION["version"], "hash": preregistration_hash()},
                "data_check": inputs["data_check"], "content": coverage,
                "unavailable": unavailable, "llm": llm_report,
            }
            _emit(plan, json_output)
            if llm_report is not None and llm_report["status"] not in {"dry_run", "complete", "disabled"}:
                raise typer.Exit(code=1)
            return
        config = loaded.config.model_dump(mode="json")
        mastery = MasteryConfig.model_validate(config["mastery"])
        t8_arms = success_head_arms(
            content, config=mastery, lo_priors=inputs["lo_priors"],
            include_difficulty="success_head+difficulty" not in unavailable,
        )
        report = evaluate(
            (*inputs["attempts"], *inputs["facets"], *inputs["signals"]),
            arms=("base_rate_lo", "mastery_ekf", "lo_general", *t8_arms, *llm_arms),
            bootstrap_samples=bootstrap_samples, seed=seed, fast_track_q=0.9,
            general_means=inputs["general_means"], lo_priors=inputs["lo_priors"], config=config,
            fsrs_weights=inputs["fsrs_weights"], fsrs_fit_id=inputs["fsrs_fit_id"],
            analyses={"t8": make_t8_analysis(unavailable=unavailable)}, bootstrap_unit="item",
        )
        report["manifest"]["embedding_model"] = coverage["embedding_model"]
        report["manifest"]["kernel"] = "bayesian_logistic_linear_blocks"
        report["manifest"]["t8"] = {
            "preregistration_hash": preregistration_hash(), "content_digest": content.digest,
            "views": coverage["views"], "dimensions": coverage["dimensions"],
            # The delta in force, so the owner can monitor whether it needs changing.
            "smallest_worthwhile_gain_nats_per_attempt": PREREGISTRATION[
                "smallest_worthwhile_gain_nats_per_attempt"],
            "margin_nats_per_attempt": PREREGISTRATION["margin_nats_per_attempt"],
            "decision_interval": PREREGISTRATION["decision_interval"]["method"],
        }
        report["data_check"] = inputs["data_check"]
        report["claim_priors"] = inputs["claim_priors"]
        report["t8_inputs"] = {"content": coverage, "unavailable": unavailable,
                               "llm_aliases": dict(LLM_ARM_ALIASES), "llm_alias_note": LLM_ALIAS_NOTE}
        if llm_report is not None:
            report["offline_preparation"] = llm_report
        report["vault_validation_issues"] = len(loaded.issues)
        files = write_reports(
            report, output_dir, stem="t8-success-head-" + report_digest(report)[:16],
            title="T8 learner success head replay (research only)",
            preamble=summary_lines(report["analyses"]["t8"]),
        )
        if json_output:
            _emit({"version": 1, "status": "complete", "reports": files, "evaluation": report}, True)
        else:
            typer.echo("\n".join((files["json"], files["markdown"])))
    except AIProviderUnavailable as exc:
        _emit({"status": "unavailable", "error_type": type(exc).__name__}, json_output)
        raise typer.Exit(code=1) from exc
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        _emit({"status": "invalid", "reason": str(exc)}, json_output)
        raise typer.Exit(code=1) from exc
