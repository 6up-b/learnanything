"""The attempt chain's decision records after the grade (refactor B7, ADR-017).

The grade's records are ``attempts.grade_records``; the queue hop is
``db.stores.provenance.record_job_enqueued``. This module holds the rest, each a
pure builder and a writer that never raises:

* ``diagnosis``: one per persisted diagnosis row, its status and why, in the
  row's own transaction (``split.jobs._persist``), child of the job's
  ``job_enqueued``;
* ``diagnosis_step``: a post-diagnosis step that failed to a log line before
  (the machine-check sweep, the common-repair consultation, the escalation
  receipt, the learner-text enqueue, the causal shadow selector);
* ``followup_value``: each follow-up value decision, beside its receipt
  (``followup_value_decisions``), so the follow-up's later router decision is
  reached through the trace (break 6);
* ``voi_forecast``: a forecast writer that failed (it logged only);
* ``probe_value``: an opened item value rejected as the episode's next
  observation (it left no row);
* ``probe_offer``: every acceptance of a causal probe offer, with the id that
  decided it (the learner lane's causal receipt, or FG1's router decision), so a
  learner-lane probe has a row at acceptance (break 5).

Every value is an id, a number or a code; prose (an analysis, a statement, an
error message) is counted or dropped, never copied.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from learnloop import provenance
from learnloop.db.stores import provenance as decision_store

LOG = logging.getLogger(__name__)

DIAGNOSIS = "diagnosis"
DIAGNOSIS_STEP = "diagnosis_step"
FOLLOWUP_VALUE = "followup_value"
VOI_FORECAST = "voi_forecast"
PROBE_VALUE = "probe_value"
PROBE_OFFER = "probe_offer"

#: Alternatives and ids kept per record (the receipts keep the rest).
ALTERNATIVES_KEPT = 10

#: A diagnosis row's status -> the record's status.
_DIAGNOSIS_STATUS = {"completed": "chosen", "validation_rejected": "discarded", "failed": "failed"}
#: A skipped diagnosis's reason -> the record's status (``budget`` was refused by the cap; ``not_needed`` excluded).
_SKIP_STATUS = {"budget": "refused", "not_needed": "excluded"}


def _code(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if provenance.is_code(text) else "unnamed"


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _ids(values: Iterable[Any]) -> list[str]:
    return sorted({str(value) for value in values if value is not None and provenance.is_code(str(value))})[
        :ALTERNATIVES_KEPT]


def _write(repository: Any, kind: str, build: Any) -> str | None:
    """Build and write one record through the repository's connection (joining its transaction); never raises."""

    try:
        record = build()
    except Exception as exc:  # noqa: BLE001 - a record never changes the decision it describes
        LOG.warning("decision record %r not written (trace %s): %s", kind, provenance.current_trace(),
                    type(exc).__name__)
        return None
    return decision_store.write_decision(repository, record)


# -- diagnosis --------------------------------------------------------------------------------------------------


def diagnosis_record(*, diagnosis_id: str, job_id: str | None, values: Mapping[str, Any]) -> provenance.DecisionRecord:
    """One persisted diagnosis (pure). ``rule`` is the error or skip code (``completed`` when it ran clean);
    ``alternatives`` are the candidate causes per event, by index and prior weight, never their statements."""

    status_word = str(values.get("status") or "failed")
    report = values.get("validation_report") or {}
    skip = _get(report, "skip_reason")
    error = values.get("error")
    if status_word == "skipped":
        status = _SKIP_STATUS.get(str(skip or error or ""), "excluded")
    else:
        status = _DIAGNOSIS_STATUS.get(status_word, "failed")
    proposal = values.get("proposal")
    events = list(_get(proposal, "event_diagnoses", []) or []) if proposal is not None else []
    alternatives: list[dict[str, Any]] = []
    for event in events:
        index = _get(event, "event_index", 0)
        for position, cause in enumerate(_get(event, "candidate_causes", []) or []):
            alternatives.append({"ref": f"event:{int(index)}:cause:{position}",
                                 "p": _number(_get(cause, "prior_weight")),
                                 "lost_by": _code(_get(event, "causal_class"))})
    counts = {
        f"{name}_n": len(list(_get(proposal, name, []) or [])) if proposal is not None else 0
        for name in ("event_diagnoses", "repair_suggestions", "pattern_claims", "prerequisite_gap_hypotheses",
                     "abstentions")
    }
    attempt_id = str(values.get("attempt_id") or "")
    return provenance.DecisionRecord(
        kind=DIAGNOSIS, status=status, subject_kind="attempt", subject_id=attempt_id or None,
        chosen_ref=diagnosis_id if status == "chosen" else None, decided_by="diagnoser",
        rule=_code(skip or error) or status_word,
        alternatives=tuple(alternatives[:provenance.MAX_ALTERNATIVES]),
        facts={"status": _code(status_word), "mode": _code(values.get("mode")),
               "history_mode": _code(values.get("history_mode")), "job_id": _code(job_id),
               "blind_grade_record_id": _code(values.get("blind_grade_record_id")),
               "supersedes_id": _code(values.get("supersedes_id")), "agent_run_id": _code(values.get("agent_run_id")),
               "latency_seconds": _number(values.get("latency_seconds")),
               "evidence_attempt_ids": _ids(_get(proposal, "evidence_attempt_ids", []) or [])
               if proposal is not None else [],
               **counts},
        versions={"diagnosis_prompt_version": _code(values.get("diagnosis_prompt_version")),
                  "provider": _code(values.get("provider")), "model": _code(values.get("model"))},
        detail_table="attempt_diagnoses", detail_id=diagnosis_id, parent_id=provenance.current_cause(),
    )


def record_diagnosis(repository: Any, *, diagnosis_id: str, job_id: str | None,
                     values: Mapping[str, Any]) -> str | None:
    return _write(repository, DIAGNOSIS,
                  lambda: diagnosis_record(diagnosis_id=diagnosis_id, job_id=job_id, values=values))


def step_failed_record(*, step: str, exc: BaseException, attempt_id: str | None = None,
                       subject: tuple[str, str] | None = None,
                       facts: Mapping[str, Any] | None = None) -> provenance.DecisionRecord:
    """A diagnosis step that failed and was skipped (pure): the step as ``rule``, the exception's class and where it
    was raised; the message stays in the log (at the caller's WARNING, with the trace)."""

    subject_kind, subject_id = subject if subject is not None else ("attempt", attempt_id)
    return provenance.DecisionRecord(
        kind=DIAGNOSIS_STEP, status="failed", subject_kind=subject_kind, subject_id=subject_id,
        decided_by="diagnosis_pipeline", rule=step,
        facts={"attempt_id": _code(attempt_id),
               **{key: (_code(value) if isinstance(value, str) else value)
                  for key, value in dict(facts or {}).items()}},
        error_type=type(exc).__name__, error_where=_code(provenance.where(exc)),
        parent_id=provenance.current_cause(),
    )


def record_step_failed(repository: Any, *, step: str, exc: BaseException, attempt_id: str | None = None,
                       subject: tuple[str, str] | None = None, facts: Mapping[str, Any] | None = None) -> str | None:
    return _write(repository, DIAGNOSIS_STEP, lambda: step_failed_record(step=step, exc=exc, attempt_id=attempt_id,
                                                                         subject=subject, facts=facts))


# -- value of information -------------------------------------------------------------------------------------


def _candidate_alternatives(body: Mapping[str, Any] | None, chosen: str | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for candidate in list(_get(body, "candidates", []) or [])[:ALTERNATIVES_KEPT] if body else []:
        ref = _get(candidate, "ref")
        if ref is None or str(ref) == chosen:
            continue
        out.append({"ref": _code(ref), "score": _number(_get(candidate, "evsi_robust_minutes")),
                    "cost": _number(_get(candidate, "cost_minutes")), "lost_by": _code(_get(candidate, "reason"))})
    return out


def _value_facts(body: Mapping[str, Any] | None) -> dict[str, Any]:
    if not body:
        return {}
    best = _get(body, "best") or {}
    return {"site": _code(_get(body, "site")), "decision": _code(_get(body, "decision")),
            "recommended_ref": _code(_get(body, "recommended_ref")), "served_ref": _code(_get(body, "served_ref")),
            "candidate_count": _number(_get(body, "candidate_count")),
            "cap_comparison": _code(_get(body, "cap_comparison")),
            "best_evsi_robust_minutes": _number(_get(best, "evsi_robust_minutes")),
            "best_cost_minutes": _number(_get(best, "cost_minutes"))}


def followup_value_record(*, receipt_id: str, attempt_id: str, learning_object_id: str | None,
                          session_id: str | None, outcome: str, decision: Mapping[str, Any] | None,
                          manual_override: bool, need_id: str | None,
                          algorithm_version: str | None) -> provenance.DecisionRecord:
    """One follow-up value decision (pure), beside its receipt row. The router decision that serves the follow-up
    later names no receipt (break 6); it is reached through this record's trace, which the follow-up's jobs continue."""

    body = dict(decision) if decision is not None else None
    chosen = _get(body, "served_ref") or _get(body, "recommended_ref") if body else None
    verdict = _get(body, "decision") if body else None
    return provenance.DecisionRecord(
        kind=FOLLOWUP_VALUE, status="chosen" if chosen else "excluded", subject_kind="attempt", subject_id=attempt_id,
        chosen_ref=_code(chosen), decided_by="voi_followup_value", rule=_code(outcome),
        alternatives=tuple(_candidate_alternatives(body, str(chosen) if chosen else None)),
        facts={"verdict": _code(verdict), "manual_override": bool(manual_override), "need_id": _code(need_id),
               "learning_object_id": _code(learning_object_id), "session_id": _code(session_id),
               "reason": _code(_get(body, "reason")) if body else None, **_value_facts(body)},
        versions={"algorithm_version": _code(algorithm_version),
                  "forecast_version": _code(_get(body, "forecast_version")) if body else None},
        detail_table="followup_value_decisions", detail_id=receipt_id, parent_id=provenance.current_cause(),
    )


def record_followup_value(repository: Any, **values: Any) -> str | None:
    return _write(repository, FOLLOWUP_VALUE, lambda: followup_value_record(**values))


def forecast_failed_record(*, site: str, exc: BaseException, decision_ref: str | None = None,
                           receipt_key: str | None = None) -> provenance.DecisionRecord:
    """A value-of-information forecast that could not be logged (pure): the decision it describes stands."""

    return provenance.DecisionRecord(
        kind=VOI_FORECAST, status="failed", subject_kind="decision" if decision_ref else None,
        subject_id=_code(decision_ref) if decision_ref else None, decided_by="voi_forecasting",
        rule="forecast_not_recorded", facts={"site": _code(site), "receipt_key": _code(receipt_key)},
        error_type=type(exc).__name__, error_where=_code(provenance.where(exc)),
        parent_id=provenance.current_cause(),
    )


def record_forecast_failed(repository: Any, *, site: str, exc: BaseException, decision_ref: str | None = None,
                           receipt_key: str | None = None) -> str | None:
    return _write(repository, VOI_FORECAST, lambda: forecast_failed_record(
        site=site, exc=exc, decision_ref=decision_ref, receipt_key=receipt_key))


def probe_value_record(*, practice_item_id: str, episode_id: str | None, reason: str,
                       decision: Mapping[str, Any] | None) -> provenance.DecisionRecord:
    """An opened item rejected as its episode's next observation (pure): its value did not pay for its minutes, so
    it is ordinary practice. The other candidates value considered are the alternatives."""

    body = dict(decision) if decision is not None else None
    subject_value = _get(body, "subject") or {} if body else {}
    return provenance.DecisionRecord(
        kind=PROBE_VALUE, status="excluded", subject_kind="item", subject_id=_code(practice_item_id),
        chosen_ref=_code(_get(body, "recommended_ref")) if body else None, decided_by="voi_probe_episode",
        rule=_code(reason), alternatives=tuple(_candidate_alternatives(body, None)),
        facts={"episode_id": _code(episode_id),
               "item_evsi_robust_minutes": _number(_get(subject_value, "evsi_robust_minutes")),
               "item_cost_minutes": _number(_get(subject_value, "cost_minutes")), **_value_facts(body)},
        versions={"forecast_version": _code(_get(body, "forecast_version")) if body else None},
        detail_table="probe_episodes" if episode_id else None, detail_id=_code(episode_id) if episode_id else None,
        parent_id=provenance.current_cause(),
    )


def record_probe_value(repository: Any, *, practice_item_id: str, episode_id: str | None, reason: str,
                       decision: Mapping[str, Any] | None) -> str | None:
    return _write(repository, PROBE_VALUE, lambda: probe_value_record(
        practice_item_id=practice_item_id, episode_id=episode_id, reason=reason, decision=decision))


# -- the causal probe offer ------------------------------------------------------------------------------------


def probe_offer_record(*, offer: Any, decision_receipt_id: str | None, router_decision_id: str | None,
                       followup_workflow_id: str | None) -> provenance.DecisionRecord:
    """One acceptance of a causal probe offer (pure): accepted (pinned, or already pinned) or refused with its code.
    ``decided_by`` says which lane decided the offer: the learner's tap on a causal receipt, or FG1's router."""

    accepted = bool(_get(offer, "accepted"))
    lane = "router" if router_decision_id else "learner_lane"
    return provenance.DecisionRecord(
        kind=PROBE_OFFER, status="chosen" if accepted else "refused", subject_kind="factor",
        subject_id=_code(_get(offer, "factor_id")), chosen_ref=_code(_get(offer, "practice_item_id")),
        decided_by=lane, rule=_code(_get(offer, "reason")),
        facts={"causal_receipt_id": _code(decision_receipt_id), "router_decision_id": _code(router_decision_id),
               "followup_workflow_id": _code(followup_workflow_id), "episode_id": _code(_get(offer, "episode_id")),
               "presentation_id": _code(_get(offer, "presentation_id")),
               "candidate_id": _code(_get(offer, "candidate_id")),
               "hypothesis_set_id": _code(_get(offer, "hypothesis_set_id")),
               "blind_bundle_ids": _ids(_get(offer, "blind_bundle_ids", ()) or ())},
        detail_table="probe_presentations" if _get(offer, "presentation_id") else None,
        detail_id=_code(_get(offer, "presentation_id")), parent_id=provenance.current_cause(),
    )


def record_probe_offer(repository: Any, *, offer: Any, decision_receipt_id: str | None,
                       router_decision_id: str | None, followup_workflow_id: str | None) -> str | None:
    return _write(repository, PROBE_OFFER, lambda: probe_offer_record(
        offer=offer, decision_receipt_id=decision_receipt_id, router_decision_id=router_decision_id,
        followup_workflow_id=followup_workflow_id))
