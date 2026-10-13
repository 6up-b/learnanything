"""The outcome join for retrieval interventions (spec_source_practice_and_probes_v1 §11.2; S5).

DERIVED, rebuilt by exactly one replayer (``retrieval_intervention_outcomes``
in :mod:`learnloop.substrate.rebuild_orchestrator`): zero model calls, persisted
rows only, deterministic (the reference time is the newest persisted attempt or
intervention, never the clock). Per intervention:

* ``R_next``: the next attempt on the targeted items or facets within the
  session (or, without one, the UTC day), its correctness and whether it was
  assisted;
* ``R_cold``: the next independent attempt at least the cold retrieval delay
  later, as one of the decision-value spec's outcome states (§4.3). Pending
  outcomes stay right-censored, never failures;
* the observed outcome bucket of a valued check beside its predicted P(E), and
  the actual minutes beside the predicted;
* the learner's taps and their text on the proposal.

Associations, not causes: nothing reads these rows to serve.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta, timezone
import json
from typing import Any

from learnloop.db.repositories import Repository
from learnloop.db.stores.source_service import interventions, replace_outcomes
from learnloop.vault.models import LoadedVault

OUTCOME_VERSION = "retrieval_outcomes.v1"
#: The cold retrieval delay (``diagnosis.remediation.COLD_RETRIEVAL_DELAY``, 1 day).
COLD_DELAY = timedelta(days=1)
#: Past this, an intervention with no independent attempt is expired, not pending.
CENSOR_HORIZON = timedelta(days=30)
#: A report threshold, not a learning decision: a graded attempt at or above it
#: counts as a success in the association report.
SUCCESS_CORRECTNESS = 0.5
COLD_STATES = ("cold_success", "cold_failure", "right_censored_pending", "right_censored_expired",
               "learner_declined", "unmeasurable_no_targets", "contaminated_or_assisted", "missing_duration")
USAGE_TASK = "practice_usage"


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _attempts(connection: Any) -> list[dict[str, Any]]:
    rows = connection.execute(
        "SELECT id, practice_item_id, created_at, session_id, correctness, rubric_score, error_type, attempt_type, "
        "hints_used, primed, latency_seconds, declared_dont_know, evidence_facets_json FROM practice_attempts "
        "ORDER BY created_at, id").fetchall()
    attempts = []
    for row in rows:
        value = dict(row)
        try:
            value["facets"] = set(json.loads(value.pop("evidence_facets_json") or "[]"))
        except (TypeError, ValueError):
            value["facets"] = set()
        attempts.append(value)
    return attempts


def _assisted(attempt: Mapping[str, Any]) -> bool:
    return (attempt.get("attempt_type") != "independent_attempt" or bool(attempt.get("hints_used"))
            or bool(attempt.get("primed")))


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
                as_of: datetime, signals: list[dict[str, Any]]) -> dict[str, Any]:
    created = _parse(intervention["created_at"])
    items, facets = _targets(intervention, vault)
    valuation = intervention.get("valuation") or {}
    predicted = valuation.get("predicted_outcomes")
    row: dict[str, Any] = {
        "intervention_id": intervention["id"], "as_of": as_of.isoformat(), "outcome_version": OUTCOME_VERSION,
        "predicted_outcomes": predicted, "predicted_minutes": valuation.get("expected_minutes"),
        "learner_signals": signals,
        "hypothesis_movement": {"status": "not_computed",
                                "reason": "v1 keeps references (state_ref); the evsi/calibration track reads "
                                          "posteriors before and after from replayed state"},
        "action_before": valuation.get("action_before"), "action_after": valuation.get("action_after"),
    }
    if row["action_before"] is not None and row["action_after"] is not None:
        row["action_flipped"] = int(row["action_before"] != row["action_after"])
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
            row.update(next_attempt_id=attempt["id"], next_correctness=attempt.get("correctness"),
                       next_assisted=int(_assisted(attempt)), next_window="session" if same_session else "day")
            if valuation and attempt["practice_item_id"] in items:
                row["observed_bucket"] = _bucket(attempt, predicted)
                if attempt.get("latency_seconds") is not None:
                    row["actual_minutes"] = round(float(attempt["latency_seconds"]) / 60.0, 4)
            break
    cold = next((attempt for attempt in targeted if _parse(attempt["created_at"]) >= created + COLD_DELAY), None)
    if cold is None:
        row["cold_outcome_state"] = ("right_censored_expired" if as_of - created > CENSOR_HORIZON
                                     else "right_censored_pending")
        return row
    row["cold_attempt_id"] = cold["id"]
    row["cold_correctness"] = cold.get("correctness")
    if cold.get("declared_dont_know") or cold.get("attempt_type") == "dont_know":
        row["cold_outcome_state"] = "learner_declined"
    elif _assisted(cold):
        row["cold_outcome_state"] = "contaminated_or_assisted"
    elif cold.get("correctness") is None:
        row["cold_outcome_state"] = "right_censored_pending"
    elif cold.get("latency_seconds") is None:
        row["cold_outcome_state"] = "missing_duration"
    else:
        row["cold_outcome_state"] = ("cold_success" if float(cold["correctness"]) >= SUCCESS_CORRECTNESS
                                     else "cold_failure")
    return row


def rebuild_intervention_outcomes(vault: LoadedVault, repository: Repository) -> dict[str, Any]:
    """The single DERIVED replayer: pure recomputation inside the caller's transaction."""

    with repository.connection() as connection:
        records = interventions(connection)
        attempts = _attempts(connection)
        stamps = [_parse(attempt["created_at"]) for attempt in attempts]
        stamps += [_parse(record["created_at"]) for record in records]
        as_of = max(stamps) if stamps else datetime(1970, 1, 1, tzinfo=timezone.utc)
        rows = [outcome_for(record, attempts, vault, as_of=as_of, signals=_signals(connection, record.get("proposal_id")))
                for record in records]
        cleared, written = replace_outcomes(connection, rows)
    return {"cleared": cleared, "written": written, "as_of": as_of.isoformat()}


__all__ = ["COLD_STATES", "OUTCOME_VERSION", "SUCCESS_CORRECTNESS", "outcome_for", "rebuild_intervention_outcomes"]
