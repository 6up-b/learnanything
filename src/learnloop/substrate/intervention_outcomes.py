"""The outcome join for retrieval interventions (spec_source_practice_and_probes_v1 §11.2; S5).

DERIVED, rebuilt by exactly one replayer (``retrieval_intervention_outcomes``
in :mod:`learnloop.substrate.rebuild_orchestrator`): zero model calls, persisted
rows only, deterministic (the reference time is the newest persisted attempt or
intervention, never the clock). Per intervention:

* ``R_next``: the next attempt on the targeted items or facets within the
  session (or, without one, the UTC day), its correctness and whether it was
  assisted;
* ``R_cold``: the next independent attempt at least the cold retrieval delay
  later, as one of the decision-value spec's outcome states (§4.3). The
  search skips assisted attempts and attempts contaminated by an exposure in
  the cold delay before them (a reveal on the item or its LO, the passage or
  the exercise's own source text shown, another retrieval intervention on the
  same targets, a failed coldness receipt), so neither masks a later
  independent attempt. A submitted "don't know" is an unaided answer
  (``cold_dont_know``, counted as a failure); declining the proposal
  (a ``skipped`` tap) with no attempt is ``learner_declined``. Pending
  outcomes stay right-censored, never failures;
* the observed outcome bucket of a valued check beside its predicted P(E), and
  the actual minutes beside the predicted;
* what that observation implies, from the record's own persisted prior,
  member-0 likelihood and per-outcome actions: the posterior movement on the
  target hypotheses (Bayes over the model's table, labelled
  ``bayes_update_member0``) and the decision's action before and after it;
* the learner's taps and their text on the proposal.

A grade held for review (mvp-0.17's route check; THE predicate,
``held_grades.held_for_review_attempts``) is no evidence here either (merge
onto main, held-grade-evidence): a held next attempt has no correctness,
bucket or posterior movement, and a held cold attempt is
``grade_held_for_review`` (unmeasured, with no correctness), never a success
or failure. It still occupies its place in the search, as main's dataset
labels do: the attempt happened, so a later one is not the next cold one.

Associations, not causes: nothing reads these rows to serve.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import interventions, replace_outcomes
from learnloop.held_grades import held_for_review_attempts
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW, HELD_ROW_KEY
from learnloop.vault.models import LoadedVault

#: v4 (the merge onto main): a held grade is no outcome (held-grade-evidence).
OUTCOME_VERSION = "retrieval_outcomes.v4"
#: The cold retrieval delay (``diagnosis.remediation.COLD_RETRIEVAL_DELAY``, 1 day).
COLD_DELAY = timedelta(days=1)
#: Past this, an intervention with no independent attempt is expired, not pending.
CENSOR_HORIZON = timedelta(days=30)
#: A report threshold, not a learning decision: a graded attempt at or above it
#: counts as a success in the association report.
SUCCESS_CORRECTNESS = 0.5
COLD_STATES = ("cold_success", "cold_failure", "cold_dont_know", "right_censored_pending", "right_censored_expired",
               "learner_declined", "unmeasurable_no_targets", "contaminated_or_assisted", "missing_duration",
               GRADE_HELD_FOR_REVIEW)
#: Measured cold outcomes (a submitted "don't know" is a measured failure).
MEASURED_COLD_STATES = ("cold_success", "cold_failure", "cold_dont_know")
#: Coldness-receipt dimensions whose failure makes an attempt not independent.
COLDNESS_DIMENSIONS = ("unassisted", "answer_leakage", "exposure_isolation")
USAGE_TASK = "practice_usage"


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _attempts(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT id, practice_item_id, learning_object_id, created_at, session_id, correctness, rubric_score, "
        "error_type, attempt_type, hints_used, primed, latency_seconds, declared_dont_know, evidence_facets_json "
        "FROM practice_attempts ORDER BY created_at, id").fetchall()
    # THE held predicate (held-grade-evidence): a held grade's score is the
    # grader's provisional one, never read as an outcome below.
    held = held_for_review_attempts(connection)
    attempts = []
    for row in rows:
        value = dict(row)
        value[HELD_ROW_KEY] = value["id"] in held
        try:
            value["facets"] = set(json.loads(value.pop("evidence_facets_json") or "[]"))
        except (TypeError, ValueError):
            value["facets"] = set()
        attempts.append(value)
    return attempts


#: Attempt types that are unaided productions (the learner field's graded
#: retrieval types, ``field.outcomes.GRADED_RETRIEVAL_TYPES``): a submitted
#: "don't know" is an unaided answer, not assistance.
UNAIDED_TYPES = frozenset({"independent_attempt", "dont_know", "exam_attempt"})


def is_assisted(attempt: Mapping[str, Any]) -> bool:
    """Not an unaided attempt: another attempt type, a hint used, or primed."""

    return (attempt.get("attempt_type") not in UNAIDED_TYPES or bool(attempt.get("hints_used"))
            or bool(attempt.get("primed")))


_assisted = is_assisted


def _table(connection: Any, name: str) -> bool:
    return connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() \
        is not None


def exposure_evidence(connection: Any) -> dict[str, Any]:
    """The persisted exposure and coldness records the cold search reads."""

    evidence: dict[str, Any] = {"reveals": [], "source_exposures": [], "coldness_failures": {}}
    if _table(connection, "reveal_events"):
        evidence["reveals"] = [dict(row) for row in connection.execute(
            "SELECT id, practice_item_id, learning_object_id, created_at FROM reveal_events ORDER BY created_at, id")]
    if _table(connection, "source_exposure_events"):
        evidence["source_exposures"] = [dict(row) for row in connection.execute(
            "SELECT id, extraction_id, span_id, entity_type, entity_id, created_at FROM source_exposure_events "
            "ORDER BY created_at, id")]
    if _table(connection, "coldness_receipts"):
        for row in connection.execute(
                "SELECT cold_attempt_id, dimensions_json FROM coldness_receipts WHERE stage='final' "
                "AND cold_attempt_id IS NOT NULL ORDER BY id"):
            try:
                dimensions = json.loads(row[1] or "{}")
            except (TypeError, ValueError):
                dimensions = {}
            failed = [name for name in COLDNESS_DIMENSIONS
                      if (dimensions.get(name) or {}).get("status") == "fail"]
            if failed:
                evidence["coldness_failures"][str(row[0])] = failed
    return evidence


def _contamination(attempt: Mapping[str, Any], intervention: Mapping[str, Any],
                   interventions_on_targets: Sequence[Mapping[str, Any]], evidence: Mapping[str, Any],
                   vault: LoadedVault) -> list[str]:
    """Why ``attempt`` is not independent of exposure (empty: it is), from
    persisted rows only: anything in the cold delay before it."""

    at = _parse(attempt["created_at"])
    start = at - COLD_DELAY

    def inside(value: str) -> bool:
        moment = _parse(value)
        return start < moment <= at

    reasons: list[str] = []
    item_id = str(attempt.get("practice_item_id") or "")
    lo_id = attempt.get("learning_object_id")
    if any(inside(row["created_at"]) and (row["practice_item_id"] == item_id
                                          or (lo_id and row.get("learning_object_id") == lo_id))
           for row in evidence.get("reveals") or ()):
        reasons.append("revealed")
    spans = {str(key) for key in (intervention.get("assets") or {}).get("span_keys") or ()}
    item = vault.practice_items.get(item_id)
    canonical = getattr(item, "canonical_exercise", None) if item is not None else None
    if canonical is not None:
        spans |= {f"{canonical.extraction_id}:{span}" for span in canonical.span_ids}
    if any(inside(row["created_at"]) and (f"{row['extraction_id']}:{row['span_id']}" in spans
                                          or (row.get("entity_type") == "practice_item"
                                              and row.get("entity_id") == item_id))
           for row in evidence.get("source_exposures") or ()):
        reasons.append("source_exposed")
    if any(other["id"] != intervention["id"] and inside(other["created_at"]) for other in interventions_on_targets):
        reasons.append("another_intervention")
    if evidence.get("coldness_failures", {}).get(str(attempt.get("id"))):
        reasons.append("coldness_receipt_failed")
    return reasons


def _targets(intervention: Mapping[str, Any], vault: LoadedVault) -> tuple[set[str], set[str]]:
    assets, targets = intervention.get("assets") or {}, intervention.get("targets") or {}
    items = {str(item) for item in assets.get("practice_item_ids") or ()}
    facets = {str(facet) for facet in targets.get("facets") or ()}
    for item_id in items:
        item = vault.practice_items.get(item_id)
        if item is not None and not facets:
            facets |= set(item.evidence_facets)
    return items, facets


def _bucket(attempt: Mapping[str, Any], predicted: Mapping[str, float] | None) -> str | None:
    correctness = attempt.get("correctness")
    if correctness is None:
        return None
    if predicted and any("|" in key for key in predicted):
        score = attempt.get("rubric_score")
        normalized = 4.0 * float(score) / 4 if score is not None else 4.0 * float(correctness)
        bucket = "low" if normalized <= 1 else "mid" if normalized <= 3 else "high"
        return f"{bucket}|{attempt.get('error_type') or 'none'}"
    if predicted:
        correct = next((key for key in predicted if "correct" in key and "incorrect" not in key), None)
        if float(correctness) >= 0.999 and correct is not None:
            return correct
        return "incorrect (class split unknown)"
    return "correct" if float(correctness) >= 0.999 else "partial" if float(correctness) > 0 else "incorrect"


def _signals(connection: Any, proposal_id: str | None) -> list[dict[str, Any]]:
    if not proposal_id:
        return []
    rows = connection.execute(
        "SELECT verdict, right_id, rationale FROM judgment_ledger WHERE task=? AND left_id=? ORDER BY created_at, id",
        (USAGE_TASK, proposal_id)).fetchall()
    signals = []
    for row in rows:
        text = None
        try:
            text = json.loads(row["rationale"]).get("learner_text")
        except (TypeError, ValueError, AttributeError):
            text = None
        signals.append({"signal": row["verdict"], "ref": row["right_id"], **({"text": text} if text else {})})
    return signals


def outcome_for(intervention: Mapping[str, Any], attempts: Sequence[Mapping[str, Any]], vault: LoadedVault, *,
                as_of: datetime, signals: list[dict[str, Any]], evidence: Mapping[str, Any] | None = None,
                interventions_seen: Sequence[Mapping[str, Any]] = ()) -> dict[str, Any]:
    created = _parse(intervention["created_at"])
    items, facets = _targets(intervention, vault)
    valuation = intervention.get("valuation") or {}
    predicted = valuation.get("predicted_outcomes")
    likelihood = valuation.get("likelihood") or None
    alphabet = predicted or ({emission: None for row in likelihood.values() for emission in row}
                             if likelihood else None)
    row: dict[str, Any] = {
        "intervention_id": intervention["id"], "as_of": as_of.isoformat(), "outcome_version": OUTCOME_VERSION,
        "predicted_outcomes": predicted, "predicted_minutes": valuation.get("expected_minutes"),
        "learner_signals": signals,
        "hypothesis_movement": ({"status": "pending", "reason": "no observation on the check yet"}
                                if valuation.get("prior") and likelihood else
                                {"status": "not_valued", "reason": "the record has no prior and likelihood"}),
        "action_before": valuation.get("action_before"), "action_after": None,
    }
    if not items and not facets:
        row["cold_outcome_state"] = "unmeasurable_no_targets"
        return row
    targeted = [attempt for attempt in attempts if _parse(attempt["created_at"]) >= created
                and (attempt["practice_item_id"] in items or attempt["facets"] & facets)]
    session = intervention.get("session_id")
    for attempt in targeted:
        same_session = session is not None and attempt.get("session_id") == session
        same_day = _parse(attempt["created_at"]).date() == created.date()
        if same_session or (session is None and same_day):
            held = bool(attempt.get(HELD_ROW_KEY))
            row.update(next_attempt_id=attempt["id"], next_correctness=None if held else attempt.get("correctness"),
                       next_assisted=int(_assisted(attempt)), next_window="session" if same_session else "day")
            if held:
                # Held for review: no observation (the minutes are time only).
                if attempt["practice_item_id"] in items and attempt.get("latency_seconds") is not None:
                    row["actual_minutes"] = round(float(attempt["latency_seconds"]) / 60.0, 4)
                if valuation.get("prior") and likelihood:
                    row["hypothesis_movement"] = {"status": GRADE_HELD_FOR_REVIEW,
                                                  "reason": "the check's grade is held for review"}
            elif valuation and attempt["practice_item_id"] in items:
                row["observed_bucket"] = _bucket(attempt, alphabet)
                if attempt.get("latency_seconds") is not None:
                    row["actual_minutes"] = round(float(attempt["latency_seconds"]) / 60.0, 4)
                _observation(row, valuation, likelihood)
            break
    # The next INDEPENDENT attempt (§11.2): assisted attempts and attempts
    # contaminated by an exposure in the cold delay before them are skipped,
    # never allowed to mask a later independent one.
    on_targets = [other for other in interventions_seen
                  if other.get("id") != intervention.get("id") and _overlaps(other, items, facets, vault)]
    masked: dict[str, Any] | None = None
    cold = None
    for attempt in targeted:
        if _parse(attempt["created_at"]) < created + COLD_DELAY:
            continue
        if _assisted(attempt) or _contamination(attempt, intervention, on_targets, evidence or {}, vault):
            masked = masked or attempt
            continue
        cold = attempt
        break
    if cold is None:
        if masked is not None:
            row["cold_attempt_id"] = masked["id"]
            row["cold_correctness"] = None if masked.get(HELD_ROW_KEY) else masked.get("correctness")
            row["cold_outcome_state"] = "contaminated_or_assisted"
        elif any(signal.get("signal") == "skipped" for signal in signals):
            row["cold_outcome_state"] = "learner_declined"  # declined the proposal itself
        else:
            row["cold_outcome_state"] = ("right_censored_expired" if as_of - created > CENSOR_HORIZON
                                         else "right_censored_pending")
        return row
    row["cold_attempt_id"] = cold["id"]
    if cold.get(HELD_ROW_KEY):
        # Held for review: the cold check happened, its grade is no outcome.
        row["cold_correctness"] = None
        row["cold_outcome_state"] = GRADE_HELD_FOR_REVIEW
        return row
    row["cold_correctness"] = cold.get("correctness")
    if _dont_know(cold):
        row["cold_outcome_state"] = "cold_dont_know"
    elif cold.get("correctness") is None:
        row["cold_outcome_state"] = "right_censored_pending"
    elif cold.get("latency_seconds") is None:
        row["cold_outcome_state"] = "missing_duration"
    else:
        row["cold_outcome_state"] = ("cold_success" if float(cold["correctness"]) >= SUCCESS_CORRECTNESS
                                     else "cold_failure")
    return row


def _entropy(distribution: Mapping[str, float]) -> float:
    return -sum(p * math.log(p) for p in distribution.values() if p > 0)


def _observation(row: dict[str, Any], valuation: Mapping[str, Any],
                 likelihood: Mapping[str, Mapping[str, float]] | None) -> None:
    """What the observed bucket implies, from persisted rows only (§11.4 items
    2 and 3; Codex re-review F11): the posterior on the target hypotheses by
    Bayes' rule over the check's own member-0 likelihood (the model's implied
    movement, labelled so; calibration compares it with the predicted EIG),
    and the decision's action after the observation from the persisted
    per-outcome actions."""

    bucket = row.get("observed_bucket")
    by_outcome = valuation.get("action_by_outcome") or {}
    if row.get("action_before") is not None and bucket in by_outcome:
        row["action_after"] = by_outcome[bucket]
        row["action_flipped"] = int(row["action_before"] != row["action_after"])
    prior = {str(h): float(p) for h, p in (valuation.get("prior") or {}).items()}
    if not prior or not likelihood:
        return
    if bucket is None or not any(bucket in (likelihood.get(h) or {}) for h in prior):
        row["hypothesis_movement"] = {"status": "bucket_not_in_alphabet", "observed_bucket": bucket,
                                      "basis": "bayes_update_member0"}
        return
    joint = {h: p * float((likelihood.get(h) or {}).get(bucket, 0.0)) for h, p in prior.items()}
    total = sum(joint.values())
    if total <= 0:
        row["hypothesis_movement"] = {"status": "impossible_under_model", "observed_bucket": bucket,
                                      "basis": "bayes_update_member0"}
        return
    posterior = {h: round(value / total, 6) for h, value in joint.items()}
    before, after = _entropy(prior), _entropy(posterior)
    row["hypothesis_movement"] = {
        "status": "computed", "basis": "bayes_update_member0", "observed_bucket": bucket,
        "prior": {h: round(p, 6) for h, p in prior.items()}, "posterior": posterior,
        "entropy_before_nats": round(before, 6), "entropy_after_nats": round(after, 6),
        "information_gained_nats": round(before - after, 6),
        "predicted_eig_nats": valuation.get("point_eig_nats"), "state_hash": valuation.get("state_hash")}


def _dont_know(attempt: Mapping[str, Any]) -> bool:
    return bool(attempt.get("declared_dont_know")) or attempt.get("attempt_type") == "dont_know"


def _overlaps(other: Mapping[str, Any], items: set[str], facets: set[str], vault: LoadedVault) -> bool:
    other_items, other_facets = _targets(other, vault)
    return bool(other_items & items or other_facets & facets)


def rebuild_intervention_outcomes(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """The single DERIVED replayer: pure recomputation inside the caller's transaction."""

    with repository.connection() as connection:
        records = interventions(connection)
        attempts = _attempts(connection)
        stamps = [_parse(attempt["created_at"]) for attempt in attempts]
        stamps += [_parse(record["created_at"]) for record in records]
        as_of = max(stamps) if stamps else datetime(1970, 1, 1, tzinfo=timezone.utc)
        evidence = exposure_evidence(connection)
        rows = [outcome_for(record, attempts, vault, as_of=as_of, signals=_signals(connection, record.get("proposal_id")),
                            evidence=evidence, interventions_seen=records)
                for record in records]
        cleared, written = replace_outcomes(connection, rows)
    return {"cleared": cleared, "written": written, "as_of": as_of.isoformat()}


__all__ = ["COLD_STATES", "MEASURED_COLD_STATES", "OUTCOME_VERSION", "SUCCESS_CORRECTNESS", "exposure_evidence",
           "is_assisted", "outcome_for", "rebuild_intervention_outcomes"]
