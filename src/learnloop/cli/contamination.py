"""Slice 2 T4 shadow contamination flags: embed, then report. Nothing is executed."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from learnloop.ai.spend import SpendCaps
from learnloop.cli.embeddings import _cancellation
from learnloop.vault.loader import load_vault


contamination_app = typer.Typer(
    no_args_is_help=True,
    help="Shadow contamination flags (Slice 2 T4): embed the record kinds, then report. "
         "Flags only propose; the lexical floor keeps every live decision.",
)


def _emit(report: dict, json_output: bool) -> None:
    typer.echo(json.dumps(report, sort_keys=True, indent=None if json_output else 2, default=str))
    if report["status"] == "cancelled":
        raise typer.Exit(130)
    if report["status"] not in {"dry_run", "complete"}:
        raise typer.Exit(1)


def _load(vault: Path):
    if not (vault / "learnloop.toml").is_file():
        raise ValueError("--vault must contain learnloop.toml")
    loaded = load_vault(vault)
    if loaded.issues:
        raise ValueError(f"Vault has {len(loaded.issues)} validation issues; run doctor first")
    return loaded


@contamination_app.command("embed")
def contamination_embed(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Estimate calls, tokens and cost; no client, migration or data changes.")] = False,
    record_kind: Annotated[list[str] | None, typer.Option(
        "--record-kind",
        help="A record kind or recipe (item/stem, item/expected_answer, question_event/answer, "
             "surface/statement, exam_span/text); repeatable. Default: all.",
    )] = None,
    batch_size: Annotated[int, typer.Option("--batch-size", min=1, max=256)] = 32,
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0, help="Records to embed.")] = 2000,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0, help="Embedding uses no pairs.")] = 0,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 200,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 2_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive USD input-token estimate for an unknown/changed model price; still subject to cost cap.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Embed the texts the contamination report compares; reruns skip saved hashes.

    Uses the Phase 1 backfill (embedding route, caps, receipts, lock): both
    embedding switches must be enabled for paid work. The default backfill
    never embeds these record kinds. Reports carry counts, never text.
    """
    from learnloop.ops.contamination.recipes import CONTAMINATION_RECIPES
    from learnloop.ops.embedding_backfill import backfill_embeddings

    try:
        caps = SpendCaps(
            max_candidates=max_candidates, max_pairs=max_pairs, max_retries=max_retries,
            max_calls=max_calls, max_total_tokens=max_tokens, max_estimated_usd=max_cost_usd,
        )
        loaded = _load(vault)
        with _cancellation() as stop:
            report = backfill_embeddings(
                loaded, caps=caps, dry_run=dry_run,
                recipes=tuple(record_kind) if record_kind else None,
                batch_size=batch_size, price_per_million=price_per_million,
                cancelled=stop.is_set, registry=CONTAMINATION_RECIPES,
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)


@contamination_app.command("report")
def contamination_report_command(
    vault: Annotated[Path, typer.Option("--vault", help="Explicit vault root; use a fixtures-local copy.")],
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Scan and estimate the judge; no client, lock or data change.")] = False,
    no_judge: Annotated[bool, typer.Option("--no-judge", help="No paid calls: report the floor, the symbolic check and stored vectors.")] = False,
    detector: Annotated[list[str] | None, typer.Option(
        "--detector", help="exam_leakage, tutor_answer_leak or reader_reveal; repeatable. Default: all.",
    )] = None,
    top_k: Annotated[int, typer.Option("--top-k", min=1, max=50, help="Embedding shortlist rank; no score cutoff.")] = 3,
    sample: Annotated[int, typer.Option("--sample", min=0, max=100, help="Audited samples per category.")] = 5,
    repeat_sample: Annotated[int, typer.Option(
        "--repeat-sample", min=0, max=50,
        help="Noise floor: pairs per detector judged a second time under identical settings "
             "(planned in --dry-run; 0 turns it off).",
    )] = 5,
    judge_revision: Annotated[str, typer.Option(
        "--judge-revision", help="Checkpoint revision; change it to re-judge under a retargeted model alias.",
    )] = "1",
    max_candidates: Annotated[int, typer.Option("--max-candidates", min=0, help="Distinct subjects judged.")] = 500,
    max_pairs: Annotated[int, typer.Option("--max-pairs", min=0)] = 500,
    max_calls: Annotated[int, typer.Option("--max-calls", min=0)] = 500,
    max_retries: Annotated[int, typer.Option("--max-retries", min=0)] = 2,
    max_tokens: Annotated[int, typer.Option("--max-tokens", min=0)] = 2_000_000,
    max_cost_usd: Annotated[float, typer.Option("--max-cost-usd", min=0)] = 1.0,
    price_per_million: Annotated[float | None, typer.Option(
        "--price-per-million", min=0,
        help="Positive owner price bound (USD per million tokens). Unknown prices fail closed on "
             "metered routes; a Codex route runs on the subscription and only estimates cost.",
    )] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Shadow flag rates, floor agreement, proposals and audited samples (Slice 2 §13).

    Reads stored vectors only (no embedding call); missing vectors degrade to
    the lexical floor. Every item-bound tutor answer is judged. The noise floor
    re-judges a few pairs per detector. Proposals (burn_reserve,
    review_assessment, reveal_debit, review_item) are never executed. Rerun to
    resume: saved verdicts are never paid for again.
    """
    from learnloop.ops.contamination.detectors import DETECTORS
    from learnloop.ops.contamination.report import contamination_report

    try:
        loaded = _load(vault)
        with _cancellation() as stop:
            report = contamination_report(
                loaded, dry_run=dry_run, judge=not no_judge,
                detectors=tuple(detector) if detector else DETECTORS,
                top_k=top_k, sample_size=sample, repeat_sample=repeat_sample, judge_revision=judge_revision,
                price_per_million=price_per_million, cancelled=stop.is_set,
                caps=SpendCaps(
                    max_candidates=max_candidates, max_pairs=max_pairs, max_calls=max_calls,
                    max_retries=max_retries, max_total_tokens=max_tokens,
                    max_estimated_usd=max_cost_usd,
                ),
            )
    except ValueError as exc:
        report = {"status": "invalid", "reason": str(exc)}
    _emit(report, json_output)
