"""RO5 §9 item 6 (owner decision, Nov 4): testing misconception picks.

A pick that today resolves its factor (a concrete candidate the trace does not contradict) keeps doing so by
default. A small seeded share (``pick_open_share``, 0.1, a declared price for information) stays open instead: the
report is recorded and passed on as the learner's attributed opinion, no provisional belief opens, and the factor
stays open. The assignment is drawn from the factor's own seed (never the clock or the session), inserted in the
same transaction as the report, and an existing assignment for the factor is reused, so a retried report draws the
same arm.

**What it identifies**: the effect of leaving a pick open, repair targeting included. Agreement between picks and
probes is **conditional on being probed** (open factors are probe targets only under further restrictions, and the
VOI gate may decline), and agreement against delayed performance is reported for all picks, **labelled
self-selected**. :func:`section` (``learnloop data-capture report``) records assignment, eligibility, gate reasons,
administration, completion and intervening instruction separately. FG1c's marks stay separate (their own section).

A leaf over the vault's tables and the router's uniform.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from typing import Any

from learnloop.router import mixture as mx
from learnloop.router_objective import assignments as A

VERSION = "ro5_open_pick_v1"
OPEN = "open"
RESOLVE = "resolve"
AGREEMENT_LABEL = "conditional on being probed: open factors are probe targets only under further restrictions"
DELAYED_LABEL = "self-selected: picks are the learner's own, and what follows them is not randomized"


def seed_for(factor_id: str) -> str:
    return hashlib.sha256(f"{A.PICK}|{factor_id}".encode("utf-8")).hexdigest()


def assign(connection: Any, *, factor_id: str, share: float, report_id: str, at: str,
           eligibility: Mapping[str, Any]) -> dict[str, Any]:
    """The pick's arm: an existing assignment for the factor (a retry), else a fresh one on the factor's seed,
    written on ``connection`` (the report's transaction). Returns the row's arm, probability and id."""

    existing = A.by_unit(connection, A.PICK, factor_id)
    if existing is not None:
        return {"variant": existing["variant"], "propensity": float(existing["propensity"]), "id": existing["id"],
                "reused": True}
    seed = seed_for(factor_id)
    u = mx.uniform(seed, "open_pick")
    variant = OPEN if u < float(share) else RESOLVE
    propensity = float(share) if variant == OPEN else 1.0 - float(share)
    assignment_id = A.insert(connection, experiment_id=A.PICK, unit_id=factor_id, variant=variant,
                             propensity=propensity, seed=seed, draw=u, candidate_refs=[OPEN, RESOLVE],
                             detail={"version": VERSION, "share": float(share), "report_id": report_id,
                                     "eligibility": dict(eligibility)}, at=at)
    return {"variant": variant, "propensity": propensity, "id": assignment_id, "reused": False}


def _present(connection: Any, table: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone() \
        is not None


def section(connection: Any) -> dict[str, Any]:
    """``learnloop data-capture report``'s open-picks section (module docstring), read-only."""

    rows = A.rows(connection, A.PICK)
    if not rows and not _present(connection, "causal_attribution_reports"):
        return {"available": False, "reason": "no_reports_table"}
    by_variant = Counter(str(row["variant"]) for row in rows)
    assigned = {str(row["unit_id"]): row for row in rows}
    picks = []
    if _present(connection, "causal_attribution_reports"):
        picks = [dict(row) for row in connection.execute(
            "SELECT id, factor_id, attempt_id, response, created_at FROM causal_attribution_reports "
            "WHERE response = 'believed_candidate' ORDER BY created_at, id")]
    eligibility = Counter("assigned" if str(pick["factor_id"]) in assigned else "not_assigned:ineligible_or_off"
                          for pick in picks)
    observations = {}
    if _present(connection, "causal_discriminating_observations"):
        for row in connection.execute(
                "SELECT factor_id, outcome, probe_attempt_id, created_at, classified_as_json FROM "
                "causal_discriminating_observations ORDER BY created_at, id"):
            observations.setdefault(str(row[0]), {"outcome": row[1], "probe_attempt_id": row[2], "at": row[3],
                                                  "classified": set(json.loads(row[4] or "[]"))})
    gates: dict[str, Counter] = {OPEN: Counter(), RESOLVE: Counter()}
    if _present(connection, "causal_probe_decision_receipts"):
        for factor_id, decision, reason in connection.execute(
                "SELECT factor_id, decision, reason FROM causal_probe_decision_receipts ORDER BY created_at, id"):
            row = assigned.get(str(factor_id))
            if row is not None:
                gates[str(row["variant"])][f"{decision}:{reason}"] += 1
    administered = {OPEN: 0, RESOLVE: 0}
    completed = {OPEN: 0, RESOLVE: 0}
    agreement = {OPEN: [0, 0], RESOLVE: [0, 0]}
    instruction = {OPEN: 0, RESOLVE: 0}
    delayed: dict[str, list[float]] = {OPEN: [], RESOLVE: []}
    for factor_id, row in assigned.items():
        variant = str(row["variant"])
        observation = observations.get(factor_id)
        report_at = str(row["created_at"])
        attempt = connection.execute(
            "SELECT learning_object_id FROM practice_attempts WHERE id = (SELECT attempt_id FROM "
            "unresolved_cause_factors WHERE id = ?)", (factor_id,)).fetchone() if _present(
            connection, "unresolved_cause_factors") else None
        lo = str(attempt[0]) if attempt is not None and attempt[0] else None
        if observation is not None:
            administered[variant] += 1
            if observation.get("probe_attempt_id"):
                completed[variant] += 1
                picked = ((row.get("detail") or {}).get("eligibility") or {}).get("hypothesis_id")
                if picked:
                    supported = str(picked) in observation["classified"]
                    agreement[variant][0 if supported else 1] += 1
        if lo is not None:
            until = (observation or {}).get("at") or "9999"
            instruction[variant] += int(connection.execute(
                "SELECT COUNT(*) FROM reveal_events WHERE learning_object_id = ? AND created_at > ? AND created_at < ?",
                (lo, report_at, until)).fetchone()[0]) if _present(connection, "reveal_events") else 0
            later = connection.execute(
                "SELECT correctness FROM practice_attempts WHERE learning_object_id = ? AND created_at > ? AND "
                "correctness IS NOT NULL AND COALESCE(hints_used, 0) = 0 ORDER BY created_at, id LIMIT 1",
                (lo, report_at)).fetchone()
            if later is not None:
                delayed[variant].append(float(later[0]))
    return {
        "available": True, "version": VERSION, "assignments": dict(by_variant), "picks": len(picks),
        "eligibility": dict(eligibility),
        "gate_reasons": {variant: dict(counter) for variant, counter in gates.items()},
        "administered": administered, "completed": completed,
        "intervening_instruction_reveals": instruction,
        "pick_probe_agreement": {"label": AGREEMENT_LABEL, **{
            variant: {"agree": a, "disagree": d, "agreement": round(a / (a + d), 4) if a + d else None}
            for variant, (a, d) in agreement.items()}},
        "delayed_performance": {"label": DELAYED_LABEL, **{
            variant: {"n": len(values), "mean": round(sum(values) / len(values), 4) if values else None}
            for variant, values in delayed.items()}},
        "note": "FG1c's marks are reported apart (hypothesis_marks) and resolve nothing",
    }


__all__ = ["AGREEMENT_LABEL", "DELAYED_LABEL", "OPEN", "RESOLVE", "VERSION", "assign", "section", "seed_for"]
