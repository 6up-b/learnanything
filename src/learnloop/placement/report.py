"""Report 3: the assumption report (learner field §7.3, after F2).

Read-only and aggregate-only: counts and rates per source, never learner text
and never per-LO identities. The first review's outcome is joined from
``practice_attempts`` exactly as serving resolves it (``placement.state``).
"""
from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from statistics import median
from typing import Any

from learnloop.algorithm_versions import PLACEMENT_VERSIONS
from learnloop.clock import utc_now_iso
from learnloop.placement.rules import RULES_VERSION
from learnloop.placement.state import (
    INTENT_ASSUMED,
    INTENT_MAINTENANCE,
    diagnosis_can_arrive,
    load_placement_state_from_connection,
    placement_tables_present,
)

REPORT_VERSION = "placement-report-3-v3"
#: How each learning obligation (an untouched item on a decided LO) ended up.
OBLIGATION_OUTCOMES = (
    "items_avoided",
    "items_deferred_pending_check",
    "items_deferred_then_returned",
    "items_deferred_then_learned",
    "items_used_as_checks",
)
SOURCES = ("self_report", "fast_track", "predictor", "quick_check")
#: The daily-loop spec's flat per-item bound when no duration is known.
DEFAULT_MINUTES_PER_ITEM = 3.0

CONFOUNDS = (
    "Learning and forgetting between the decision and the first review: a miss can mean the "
    "learner forgot, a pass can mean they learned the topic elsewhere in the meantime.",
    "Learner-requested practice and follow-up lanes in that window can show the LO's items "
    "before its scheduled check: early clean answers are recorded as early practice and never "
    "pass the check, but an early miss the diagnosis attributes to a knowledge gap returns the LO "
    "to learning (resolved early).",
    "Diagnoser error: the first review and lapses in maintenance are decided by the diagnosis, so "
    "a diagnoser that calls a knowledge gap a slip (or an item-contract problem) keeps an LO in "
    "maintenance it should leave, and the reverse; kept outcomes are counted by reason.",
    "A first review is one answer on one item: the miss rate has wide intervals until many "
    "assumptions have resolved.",
    "Grader error: a grader that accepts a wrong answer can fast-track an LO or pass its check "
    "(Slice 1 E1 measures it).",
    "Minutes are estimated from the learner's own answer latencies (or 3 minutes per item), not "
    "measured study time.",
)


def _wilson(failures: int, n: int) -> list[float] | None:
    if not n:
        return None
    p, z = failures / n, 1.959963984540054
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, center - half), min(1.0, center + half)]


def _minutes_per_item(connection: Any) -> tuple[float, str]:
    values = [
        float(row[0]) / 60.0
        for row in connection.execute(
            "SELECT latency_seconds FROM practice_attempts WHERE latency_seconds IS NOT NULL AND latency_seconds > 0"
        ).fetchall()
    ]
    if len(values) >= 5:
        return round(median(values), 3), "median_answer_latency"
    return DEFAULT_MINUTES_PER_ITEM, "flat_3_minutes"


def placement_report(connection: Any, vault: Any, *, now_iso: str | None = None) -> dict[str, Any]:
    """Report 3 over one read-only snapshot, as of ``now_iso`` (default: now)."""

    version = vault.config.algorithms.algorithm_version
    manifest = {
        "report_version": REPORT_VERSION,
        "rules_version": RULES_VERSION,
        "algorithm_version": version,
        "placement_version": version in PLACEMENT_VERSIONS,
        "placement_config_hash": sha256(json.dumps(
            vault.config.placement.model_dump(mode="json"), sort_keys=True
        ).encode()).hexdigest(),
        "active_predictor": vault.config.field.active_predictor,
    }
    if not placement_tables_present(connection):
        return {"manifest": manifest, "status": "no_placement_tables", "sources": {}, "counts": {}}
    state = load_placement_state_from_connection(
        connection, active=False, diagnosis_live=diagnosis_can_arrive(vault), now_iso=now_iso or utc_now_iso(),
    )
    returns = connection.execute(
        "SELECT assumption_id FROM assumption_returns ORDER BY created_at, id"
    ).fetchall()
    minutes_per_item, minutes_basis = _minutes_per_item(connection)

    active_items: dict[str, list[str]] = defaultdict(list)
    for item in vault.practice_items.values():
        if item.status == "active" and item.learning_object_id:
            active_items[str(item.learning_object_id)].append(item.id)
    # Each item's first answer in the durable (created_at, id) order that the
    # placement state uses, so a same-second tie sorts as it was written.
    attempted_items: dict[tuple[str, str], tuple[str, str]] = {}
    for row in connection.execute(
        "SELECT learning_object_id, practice_item_id, created_at, id FROM practice_attempts "
        "WHERE attempt_type NOT IN ('skip','guided_walkthrough') ORDER BY created_at, id"
    ).fetchall():
        attempted_items.setdefault((str(row[0]), str(row[1])), (str(row[2]), str(row[3])))

    # Learning obligations, each counted once (unique items, never per
    # decision): an active item on a decided LO that was not practised before
    # the LO's first decision. Its outcome is read from the LO's CURRENT intent
    # and the item's attempts, and attributed to the LO's latest decision.
    first_decision: dict[str, tuple[str, str]] = {}
    latest_source: dict[str, str] = {}
    for assumption in state.assumptions:  # ordered by (created_at, id)
        first_decision.setdefault(assumption.learning_object_id, (assumption.created_at, assumption.id))
        latest_source[assumption.learning_object_id] = assumption.source
    check_attempts = {a.resolving_attempt_id for a in state.assumptions if a.resolving_attempt_id}
    check_items = {
        str(row[0]) for row in connection.execute(
            "SELECT DISTINCT practice_item_id FROM practice_attempts WHERE id IN "
            f"({','.join('?' for _ in check_attempts)})",
            tuple(sorted(check_attempts)),
        ).fetchall()
    } if check_attempts else set()
    obligations: dict[str, Counter[str]] = defaultdict(Counter)
    obligation_items: set[str] = set()
    for lo, decided_at in first_decision.items():
        intent = state.intent_by_lo.get(lo)
        for item_id in active_items.get(lo, ()):
            first = attempted_items.get((lo, item_id))
            if first is not None and first <= decided_at:
                continue  # practised before any assumption: not an obligation
            obligation_items.add(item_id)
            if first is not None:
                outcome = "items_used_as_checks" if item_id in check_items else "items_deferred_then_learned"
            elif intent is not None and intent.intent == INTENT_MAINTENANCE:
                outcome = "items_avoided"
            elif intent is not None and intent.intent == INTENT_ASSUMED:
                outcome = "items_deferred_pending_check"
            else:
                outcome = "items_deferred_then_returned"
            obligations[latest_source[lo]][outcome] += 1

    sources: dict[str, dict[str, Any]] = {}
    for source in SOURCES:
        rows = [a for a in state.assumptions if a.source == source]
        statuses = Counter(a.status for a in rows)
        resolved = statuses["passed"] + statuses["failed"]
        on_schedule = [a for a in rows if a.status in ("passed", "failed") and a.resolved_at >= a.first_review_due]
        early = [a for a in rows if a.status in ("passed", "failed") and a.resolved_at < a.first_review_due]
        counted = obligations.get(source, Counter())
        sources[source] = {
            "decisions": len(rows),
            "open": statuses["open"],
            "passed": statuses["passed"],
            "failed": statuses["failed"],
            "returned_by_learner": statuses["returned"],
            "first_review_miss_rate": round(statuses["failed"] / resolved, 6) if resolved else None,
            "first_review_miss_rate_wilson_ci95": _wilson(statuses["failed"], resolved),
            # The raw rate before the diagnosis decides (Phase 6's original
            # miss): any first review short of clean full marks, kept or not.
            "first_review_full_marks_misses": _full_marks_misses(rows),
            "first_review_full_marks_miss_rate": (
                round(_full_marks_misses(rows) / resolved, 6) if resolved else None
            ),
            "first_review_full_marks_miss_rate_wilson_ci95": _wilson(_full_marks_misses(rows), resolved),
            "resolved_on_schedule": len(on_schedule),
            "resolved_early": len(early),
            "on_schedule_miss_rate": (
                round(sum(a.status == "failed" for a in on_schedule) / len(on_schedule), 6)
                if on_schedule else None
            ),
            "early_practice_answers": sum(a.early_answers for a in rows),
            "ineligible_check_answers": sum(a.ineligible_answers for a in rows),
            # Owner decision 2026-10-12: the first review is decided by the
            # diagnosis. ``passed`` = into maintenance, clean or kept.
            "passed_clean": sum(a.status == "passed" and a.resolution_reason == "clean" for a in rows),
            "kept_by_diagnosis": sum(
                a.status == "passed" and a.resolution_reason not in (None, "clean") for a in rows
            ),
            "awaiting_diagnosis": sum(a.is_open and a.awaiting_diagnosis_attempt_id is not None for a in rows),
            "outcomes_by_reason": dict(sorted(Counter(
                f"{a.status}:{a.resolution_reason}" for a in rows if a.status != "open"
            ).items())),
            "fallbacks_by_reason": dict(sorted(Counter(
                a.resolution.fallback for a in rows
                if a.status == "failed" and a.resolution is not None and a.resolution.fallback
            ).items())),
            "kept_early_misses_by_reason": dict(sorted(Counter(
                reason for a in rows for _attempt, reason in a.kept_answers
            ).items())),
            **{outcome: counted[outcome] for outcome in OBLIGATION_OUTCOMES},
            "learning_minutes_saved_estimate": round(counted["items_avoided"] * minutes_per_item, 2),
            "learning_minutes_provisional_estimate": round(
                counted["items_deferred_pending_check"] * minutes_per_item, 2,
            ),
        }

    # Every LO that started as new material: no answer before placement began.
    placement_started = min((a.created_at for a in state.assumptions), default=None)
    rebuild = connection.execute(
        "SELECT MIN(created_at) FROM derived_state_rebuilds WHERE algorithm_version IN "
        f"({','.join('?' for _ in PLACEMENT_VERSIONS)})",
        tuple(sorted(PLACEMENT_VERSIONS)),
    ).fetchone() if connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='derived_state_rebuilds'"
    ).fetchone() else None
    if rebuild is not None and rebuild[0] is not None:
        placement_started = min(filter(None, (placement_started, str(rebuild[0]))))
    first_answer_by_lo: dict[str, str] = {}
    for (lo, _item), (first, _attempt_id) in attempted_items.items():
        if lo not in first_answer_by_lo or first < first_answer_by_lo[lo]:
            first_answer_by_lo[lo] = first
    new_los = [
        lo for lo, learning_object in vault.learning_objects.items()
        if learning_object.status == "active"
        and (lo not in first_answer_by_lo or (placement_started is not None and first_answer_by_lo[lo] >= placement_started))
    ]
    new_items = sum(len(active_items.get(lo, ())) for lo in new_los)
    # The baseline every saving is a subset of: each unique item once, whether
    # it sits on a new LO or is an obligation an assumption deferred.
    baseline_items = {item_id for lo in new_los for item_id in active_items.get(lo, ())} | obligation_items
    saved = sum(values["items_avoided"] for values in sources.values())
    provisional = sum(values["items_deferred_pending_check"] for values in sources.values())
    all_resolved = sum(values["passed"] + values["failed"] for values in sources.values())
    all_failed = sum(values["failed"] for values in sources.values())
    all_full_marks_misses = sum(values["first_review_full_marks_misses"] for values in sources.values())
    return {
        "manifest": manifest,
        "status": "complete",
        "sources": sources,
        "overall": {
            "decisions": len(state.assumptions),
            "open": sum(values["open"] for values in sources.values()),
            "first_review_miss_rate": round(all_failed / all_resolved, 6) if all_resolved else None,
            "first_review_miss_rate_wilson_ci95": _wilson(all_failed, all_resolved),
            "first_review_full_marks_miss_rate": (
                round(all_full_marks_misses / all_resolved, 6) if all_resolved else None
            ),
            "first_review_full_marks_miss_rate_wilson_ci95": _wilson(all_full_marks_misses, all_resolved),
        },
        "maintenance": _maintenance_outcomes(state),
        "returns_to_learning": {
            "failed_first_reviews": all_failed,
            "i_dont_know_this": len(returns),
            "i_dont_know_this_on_assumed": sum(1 for row in returns if row[0] is not None),
        },
        "learning_minutes": {
            "minutes_per_item": minutes_per_item,
            "minutes_basis": minutes_basis,
            # Avoided learning: untouched items on LOs whose check passed and
            # that are still in maintenance.
            "saved_estimate": round(saved * minutes_per_item, 2),
            # Temporary deferral: untouched items on LOs still assumed, whose
            # check has not happened yet. Not a saving until it passes.
            "provisional_estimate": round(provisional * minutes_per_item, 2),
            "learning_every_new_lo_estimate": round(new_items * minutes_per_item, 2),
            "learning_obligations_estimate": round(len(baseline_items) * minutes_per_item, 2),
            "new_learning_objects": len(new_los),
            "new_material_items": new_items,
            "learning_obligation_items": len(baseline_items),
            "placement_started_at": placement_started,
        },
        "counts": {
            "assumption_decisions": len(state.assumptions),
            "assumption_returns": len(returns),
        },
        "confounds": list(CONFOUNDS),
        "definitions": {
            "first_review": "The first recorded answer on the LO from first_review_due on (an earlier miss "
                            "can resolve it early).",
            "miss": "A first review that returned the LO to learning (first_review_miss_rate): a miss the "
                    "diagnosis attributed to a knowledge gap (causal_class learner_state on a valid_measurement "
                    "attribution) or that left any part of it without a non-gap reading (no_gap_attributed), "
                    "learner-side help (hints, priming, \"don't know\", assistance), or, when no diagnosis decided "
                    "it (none landed within the wait, or the split's kill switch held it), any answer short of "
                    "clean full marks (today's rule, reason no_diagnosis).",
            "full_marks_miss": "A first review short of clean full marks, whatever the diagnosis decided "
                               "(first_review_full_marks_miss_rate, the rate before the owner's 2026-10-12 "
                               "decision): returned to learning, or kept by the diagnosis. An unassessed (PF-c) "
                               "answer is no failure evidence and is not one.",
            "kept_by_diagnosis": "A first review short of clean full marks that kept the LO in maintenance: a "
                                 "slip, an item-contract or grader-interpretation problem, the interaction "
                                 "rather than knowledge, or an unassessed (PF-c) criterion.",
            "awaiting_diagnosis": "An open assumption whose miss waits on its diagnosis (the decision waits, at "
                                  "most placement.rules.DIAGNOSIS_WAIT_DAYS from the miss's first diagnose job).",
            "returned_by_learner": "\"I don't know this\" before any answer on the LO.",
            "on_schedule": "Resolved at or after the decision's first_review_due.",
            "early_practice": "A clean answer before first_review_due (explicit practice): recorded, never the check.",
            "ineligible_check_answer": "A clean answer the independence rule rejected: neither pass nor miss.",
            "learning_obligation": "An active item on a decided LO not practised before its first decision, "
                                   "counted once whatever the number of decisions.",
            "items_avoided": "Obligations never practised on an LO now in maintenance (its check passed).",
            "items_deferred_pending_check": "Obligations never practised on an LO still assumed (provisional).",
            "items_deferred_then_returned": "Obligations on an LO back to learning: deferred, not saved.",
            "items_deferred_then_learned": "Obligations practised after the decision: learned anyway.",
            "items_used_as_checks": "Items whose answer resolved an assumption's check.",
        },
    }


def _full_marks_misses(rows: Any) -> int:
    """Resolved first reviews whose answer fell short of clean full marks:
    returned to learning, or kept by the diagnosis (an unassessed PF-c answer
    is no failure evidence, so it is not one)."""

    return sum(
        a.status == "failed"
        or (a.status == "passed" and a.resolution_reason not in (None, "clean", "unassessed"))
        for a in rows
    )


def _maintenance_outcomes(state: Any) -> dict[str, Any]:
    """Misses on LOs in maintenance, by how the diagnosis decided them."""

    kept: Counter[str] = Counter()
    lapses: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    awaiting = 0
    for intent in state.intent_by_lo.values():
        kept.update(reason for _attempt, reason in intent.kept_misses)
        if intent.reason == "missed_in_maintenance":
            lapses[str(intent.outcome_reason)] += 1
            if intent.resolution is not None and intent.resolution.fallback:
                fallbacks[intent.resolution.fallback] += 1
        if intent.intent == INTENT_MAINTENANCE and intent.awaiting_diagnosis_attempt_id is not None:
            awaiting += 1
    return {
        "kept_misses_by_reason": dict(sorted(kept.items())),
        "lapses_by_reason": dict(sorted(lapses.items())),
        "lapse_fallbacks_by_reason": dict(sorted(fallbacks.items())),
        "awaiting_diagnosis": awaiting,
    }


def write_placement_report(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
    digest = sha256(payload.encode()).hexdigest()[:16]
    json_path = directory / f"placement-report-3-{digest}.json"
    markdown_path = directory / f"placement-report-3-{digest}.md"
    json_path.write_text(payload + "\n", encoding="utf-8")
    lines = [
        "# Report 3: assumed known, checked in the first review", "",
        "Aggregates only. No learner text, no per-LO identities.", "",
        "| Source | Decisions | Open | Passed | Failed | Returned | Miss rate | 95% Wilson CI "
        "| Minutes saved (est.) | Minutes deferred, pending check |",
        "|---|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for source, values in report.get("sources", {}).items():
        lines.append(
            f"| {source} | {values['decisions']} | {values['open']} | {values['passed']} | "
            f"{values['failed']} | {values['returned_by_learner']} | {values['first_review_miss_rate']} | "
            f"{values['first_review_miss_rate_wilson_ci95']} | {values['learning_minutes_saved_estimate']} | "
            f"{values['learning_minutes_provisional_estimate']} |"
        )
    lines.extend(["", "## First reviews by reason (decided by the diagnosis)", ""])
    for source, values in report.get("sources", {}).items():
        if values.get("outcomes_by_reason") or values.get("awaiting_diagnosis"):
            lines.append(
                f"- {source}: {values.get('outcomes_by_reason')}, awaiting a diagnosis: "
                f"{values.get('awaiting_diagnosis')}, fallbacks: {values.get('fallbacks_by_reason')}"
            )
    maintenance = report.get("maintenance") or {}
    lines.append(
        f"- maintenance: kept {maintenance.get('kept_misses_by_reason')}, lapses "
        f"{maintenance.get('lapses_by_reason')}, awaiting a diagnosis: {maintenance.get('awaiting_diagnosis')}"
    )
    minutes = report.get("learning_minutes", {})
    lines.extend([
        "",
        f"Learning minutes saved (estimate): {minutes.get('saved_estimate')} of "
        f"{minutes.get('learning_obligations_estimate')} minutes of learning obligations "
        f"({minutes.get('learning_every_new_lo_estimate')} for learning every new LO); "
        f"{minutes.get('provisional_estimate')} more deferred pending a check "
        f"({minutes.get('minutes_per_item')} min/item, {minutes.get('minutes_basis')}).",
        "",
        "## Named confounds", "",
        *(f"- {value}" for value in report.get("confounds", ())),
        "", "## Full aggregate report", "", "```json", payload, "```", "",
    ])
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}
