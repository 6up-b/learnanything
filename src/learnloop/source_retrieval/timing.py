"""How long the tutor's source retrieval takes, from the questions' receipts.

The owner chose (2026-10-12) not to cancel the tutor's retrieval at a deadline
yet, but to log its time: every tutor question records each step's wall time
(``source_context.source_retrieval.timings_ms``: rewrite, query embedding,
retrieval, verification, total). This report reads them back and gives each
step's p50 and p90, and how often a step went over the soft deadline
(``source_retrieval.retrieval_timeout_seconds``, 15 s by default). It also
counts the LLM answers that were cut off by their output budget (receipts with
status ``truncated``), by purpose and model. Read-only; no model call.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
import math
import statistics
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.source_retrieval.tutor import TIMED_STEPS


def _percentile(ordered: Sequence[float], q: float) -> float:
    """Nearest-rank percentile of an ascending list."""

    return ordered[min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))]


def step_stats(values: Sequence[float], *, soft_deadline_ms: float) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return {"n": 0, "p50_ms": None, "p90_ms": None, "max_ms": None, "over_soft_deadline": 0}
    return {"n": len(ordered), "p50_ms": statistics.median(ordered), "p90_ms": _percentile(ordered, 0.9),
            "max_ms": ordered[-1], "over_soft_deadline": sum(1 for value in ordered if value > soft_deadline_ms)}


def truncated_answers(repository: Repository) -> list[dict[str, Any]]:
    """Root receipts whose answer stopped for length, by purpose and model."""

    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        rows = connection.execute(
            "SELECT purpose, COALESCE(model, '') AS model, COUNT(*) AS n FROM model_call_receipts "
            "WHERE status = 'truncated' AND parent_call_id IS NULL GROUP BY purpose, model "
            "ORDER BY n DESC, purpose, model").fetchall()
    return [{"purpose": row[0], "model": row[1] or None, "truncated": int(row[2])} for row in rows]


def tutor_timing_report(repository: Repository, *, soft_deadline_seconds: float,
                        cancels_at_deadline: bool = False, since: str | None = None) -> dict[str, Any]:
    """Per-step p50/p90 over every tutor question whose receipt timed its retrieval."""

    timings: dict[str, list[float]] = {step: [] for step in TIMED_STEPS}
    bases: dict[str, int] = {}
    verification: dict[str, int] = {}
    pools: dict[str, int] = {}
    over: dict[str, int] = {}
    questions = 0
    for event in repository.question_events(since=since):
        context = event.get("source_context")
        manifest = context.get("source_retrieval") if isinstance(context, Mapping) else None
        if not isinstance(manifest, Mapping):
            continue
        recorded = manifest.get("timings_ms")
        if not isinstance(recorded, Mapping):
            continue
        questions += 1
        for step in TIMED_STEPS:
            value = recorded.get(step)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                timings[step].append(float(value))
        basis = str(manifest.get("basis") or "unknown")
        bases[basis] = bases.get(basis, 0) + 1
        status = (manifest.get("verification") or {}).get("status") if isinstance(
            manifest.get("verification"), Mapping) else None
        if status:
            verification[str(status)] = verification.get(str(status), 0) + 1
        mode = (manifest.get("pool") or {}).get("mode") if isinstance(manifest.get("pool"), Mapping) else None
        if mode:
            pools[str(mode)] = pools.get(str(mode), 0) + 1
        for step in manifest.get("over_soft_deadline") or []:
            over[str(step)] = over.get(str(step), 0) + 1
    soft_ms = soft_deadline_seconds * 1000
    steps = {step: step_stats(values, soft_deadline_ms=soft_ms) for step, values in timings.items()}
    return {
        "questions": questions,
        "soft_deadline_seconds": soft_deadline_seconds,
        "cancels_at_deadline": cancels_at_deadline,
        "steps": steps,
        "over_soft_deadline": {step: entry["over_soft_deadline"] for step, entry in steps.items()
                               if entry["over_soft_deadline"]},
        "flagged_on_receipts": dict(sorted(over.items())),
        "basis": dict(sorted(bases.items())),
        "verification": dict(sorted(verification.items())),
        "pool": dict(sorted(pools.items())),
        "truncated_answers": truncated_answers(repository),
    }


__all__ = ["step_stats", "truncated_answers", "tutor_timing_report"]
