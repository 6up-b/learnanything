"""Saved diagnosis forecasts: what a diagnosis and a repair expect, frozen.

Two decisions state expectations about outcomes they cannot yet know; each
writes its forecast as a ``forecast_receipts`` row in its own transaction
(:mod:`learnloop.scheduling.forecast_receipts`), before the outcome exists:

* **A persisted diagnosis** (the split diagnoser's completed proposal,
  ``diagnosis.split.jobs._persist``): for each diagnosed error event whose
  cause the diagnoser classed (learner state or a transient slip; an
  ``unknown`` class states no expectation and writes nothing) and each facet
  the event targets (once per facet and error pattern), the diagnosis's
  posterior over the event's cause (its
  causal class and the diagnoser's own confidence) and what that posterior
  predicts for the NEXT qualifying observation of the facet: the facet
  passes, the same error pattern recurs, or another error shows (kind
  ``diagnosis_next_observation``, forecaster ``diagnoser_causal_class``).
  The likelihood is the system's own facet response model
  (``probes.facet_conditional_distribution`` under ``probe.irt``) for an
  item-agnostic check (a = 1, b = 0): the learner-state cause reads as the
  error's misconception label, the slip as the facet being solid.
* **A repair's scheduled cold verification** (``remediation.
  record_remediation_attempt``, the primed attempt's transaction): the
  probability that the repair class fixes it on the cold attempt the task
  binds (kind ``repair_cold_outcome``, forecaster ``repair_class_cold_rate``:
  the class's measured cold outcomes, read as their cold grades stand when
  the receipt is written, shrunk toward the pooled rate). A
  repair whose verification cannot be scheduled (no episode, no independent
  surface, no repair class) is censored at birth with that reason.

The probe and follow-up selections' predicted outcomes are already receipts
(``voi_forecasts``); the report reads them as the ``check_outcome`` kind.

Binding is exact (the EVSI calibration F3/F6 rule). A diagnosis forecast
resolves only on the first qualifying attempt on its facet that was NOT
visible when the receipt was written (the visible ones are listed in the
receipt), and only when that attempt answered a plan or probe presentation or
a scheduler offer (``practice_attempts.plan_presentation_id`` /
``probe_presentation_id`` / ``scheduler_candidate_id``) that the report
verifies exists, is of the answered item and was administered to it (Codex
review F4); an unbound one, or one whose reference establishes nothing,
censors it. Its facet is read under the contract its grade cites, and its
pattern only through errors attributed to that facet (F1, F2). A repair
forecast resolves only on its task's consumed attempt and terminal cold
outcome. Logging only: nothing here changes grading,
scoring, scheduling or what is served, and every function returns quietly on
any failure.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.diagnosis.probes import facet_conditional_distribution
from learnloop.scheduling import forecast_receipts as FR
from learnloop.scheduling import voi_forecasts as VF

logger = logging.getLogger(__name__)

# -- the diagnosis forecast ------------------------------------------------------------------

DIAGNOSER_FORECASTER = "diagnoser_causal_class"
#: v1: causal class posterior x the facet response model, item-agnostic.
DIAGNOSER_FORECASTER_VERSION = "diagnoser_causal_class_v1"
#: The frozen rule that names a diagnosis forecast's observation and its
#: emission. Among the attempts created at or after the diagnosed attempt
#: (not it) and not visible when the receipt was written
#: (``target.seen_attempt_ids``), the first, in (created_at, id) order, whose
#: recorded evidence facets include the facet and that tests it unaided (a
#: qualifying type, not primed, no hint); assisted, primed or non-test
#: attempts before it are kept as intervening. It must answer a plan or probe
#: presentation or a scheduler offer whose record verifies (exists, is of the
#: answered item, was administered to that attempt), else the forecast is
#: censored ``unbound_attempt``. v2 (Codex review 2026-10-15): the facet must
#: be assessed under the contract the grade cites before anything resolves,
#: and the pattern counts only through errors attributed to the facet (v1
#: counted any error on the attempt and accepted any nonempty reference).
NEXT_OBSERVATION_RULE = "next_unseen_qualifying_presented_attempt_on_facet_v2"
NEXT_OBSERVATION_ALPHABET = ("pass", "same_error", "other_error")
#: Attempt types that test a facet unaided (the field's graded retrievals and
#: the committed diagnostic probe).
QUALIFYING_ATTEMPT_TYPES = ("independent_attempt", "dont_know", "diagnostic_probe", "exam_attempt")
#: A blind attribution whose validity scope says the error was not the
#: learner's (the grader owns validity) carries no learner-state forecast.
NON_LEARNER_VALIDITY = frozenset({"item_contract", "grader_interpretation", "interaction_context"})
#: The classes a diagnosis states an expectation with.
LEARNER_STATE = "learner_state"
TRANSIENT = "transient_execution"
CLASSED = (LEARNER_STATE, TRANSIENT)
#: P(the named class) when the diagnoser names it without a confidence.
DEFAULT_CLASS_CONFIDENCE = 0.7
#: Each hypothesis's predicted distribution is mixed with uniform by this
#: much: a slip can still repeat the error, a gap can still pass.
FORECAST_FLOOR = 0.02
#: At most this many receipts per diagnosis (events x targeted facets).
MAX_RECEIPTS_PER_DIAGNOSIS = 12


def _class_posterior(causal_class: str, confidence: float | None) -> dict[str, float]:
    named = DEFAULT_CLASS_CONFIDENCE if confidence is None else min(max(float(confidence), 0.0), 1.0)
    p = named if causal_class == LEARNER_STATE else 1.0 - named
    return {LEARNER_STATE: p, TRANSIENT: 1.0 - p}


def _coarse(distribution: Mapping[tuple[str, str | None], float], error_type: str) -> dict[str, float]:
    """(bucket, error) -> pass / same_error / other_error, floored."""

    out = {"pass": 0.0, "same_error": 0.0, "other_error": 0.0}
    for (bucket, error), p in distribution.items():
        if error == error_type:
            out["same_error"] += float(p)
        elif bucket == "high" and error is None:
            out["pass"] += float(p)
        else:
            out["other_error"] += float(p)
    total = sum(out.values()) or 1.0
    uniform = 1.0 / len(out)
    return {e: (1.0 - FORECAST_FLOOR) * (p / total) + FORECAST_FLOOR * uniform for e, p in out.items()}


def next_observation_likelihood(vault: Any, *, facet_id: str, error_type: str) -> dict[str, dict[str, float]]:
    """The facet response model's prediction under each cause, item-agnostic."""

    irt = vault.config.probe.irt
    common = dict(
        facet_id=facet_id, candidate_facet_support={facet_id}, fatal_error_ids={error_type},
        known_error_types=[error_type], item_a=1.0, item_b=0.0, irt=irt,
    )
    return {
        LEARNER_STATE: _coarse(facet_conditional_distribution(f"misconception:{error_type}", **common), error_type),
        TRANSIENT: _coarse(facet_conditional_distribution(f"facet_solid:{facet_id}", **common), error_type),
    }


def _diagnoser_parameters(vault: Any) -> list[dict[str, Any]]:
    irt = vault.config.probe.irt
    return [
        VF.parameter("probe.irt", irt.model_dump(mode="json"), "heuristic", source="config",
                     note="theta/cuts/error fractions of the facet response model"),
        VF.parameter("item_irt", {"a": 1.0, "b": 0.0}, "structural", source="item_agnostic",
                     note="the next observation's item is unknown when the diagnosis is made"),
        VF.parameter("DEFAULT_CLASS_CONFIDENCE", DEFAULT_CLASS_CONFIDENCE, "heuristic", source="authored_prior",
                     note="P(the named class) when the diagnoser gives no confidence"),
        VF.parameter("FORECAST_FLOOR", FORECAST_FLOOR, "heuristic", source="authored_prior"),
        VF.parameter("causal_confidence", "per event", "heuristic", source="diagnoser_self_report",
                     note="the diagnoser's own confidence, scored here, never used by a decision"),
    ]


def _attributions(record: Mapping[str, Any] | None) -> dict[int, Mapping[str, Any]]:
    out: dict[int, Mapping[str, Any]] = {}
    for position, attribution in enumerate((record or {}).get("error_attributions") or []):
        if not isinstance(attribution, Mapping):
            continue
        index = attribution.get("index", position)
        try:
            out[int(index)] = attribution
        except (TypeError, ValueError):
            continue
    return out


def _canonical_facets(vault: Any, facets: Sequence[Any]) -> list[str]:
    seen: list[str] = []
    for facet in facets:
        canonical = vault.canonical_facet_id(str(facet)) if facet else ""
        if canonical and canonical not in seen:
            seen.append(canonical)
    return seen


def _candidate_causes(event: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The diagnoser's candidate causes with their verbalized weights normalized
    (a cause without a weight takes the mean of the others): recorded, not used."""

    causes = [c for c in event.get("candidate_causes") or [] if isinstance(c, Mapping)]
    weights: list[float | None] = []
    for cause in causes:
        try:
            weights.append(max(float(cause["prior_weight"]), 0.0) if cause.get("prior_weight") is not None else None)
        except (TypeError, ValueError):
            weights.append(None)
    known = [w for w in weights if w is not None]
    fill = (sum(known) / len(known)) if known else 1.0
    resolved = [fill if w is None else w for w in weights]
    total = sum(resolved) or 1.0
    return [
        {"cause_scope": c.get("cause_scope"), "prior_weight": round(w / total, 6),
         "statement": str(c.get("statement") or "")[:240]}
        for c, w in zip(causes, resolved)
    ]


def diagnosis_receipts(
    vault: Any,
    *,
    diagnosis_id: str,
    attempt: Mapping[str, Any],
    values: Mapping[str, Any],
    record: Mapping[str, Any] | None,
    seen_attempt_ids: Sequence[str] = (),
    inputs_as_of: str | None = None,
) -> list[FR.ForecastReceipt]:
    """The receipts one completed diagnosis states (pure; no database).

    ``seen_attempt_ids``: the attempts created at or after the diagnosed one
    that are visible to the receipt's transaction (never its observation).
    """

    proposal = values.get("proposal") or {}
    if values.get("status") != "completed" or not isinstance(proposal, Mapping):
        return []
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    item_facets = _canonical_facets(vault, list(getattr(item, "evidence_facets", None) or []))
    attributions = _attributions(record)
    context = values.get("receipt") or {}
    retrieval = context.get("retrieval") if isinstance(context.get("retrieval"), Mapping) else {}
    seen = sorted({str(value) for value in seen_attempt_ids if value})
    receipts: list[FR.ForecastReceipt] = []
    #: One forecast per (facet, pattern): two events of one pattern on one
    #: facet predict one observation once (the first event's statement).
    stated: set[tuple[str, str, str | None]] = set()
    parameters = _diagnoser_parameters(vault)
    for event in proposal.get("event_diagnoses") or []:
        if not isinstance(event, Mapping):
            continue
        causal_class = str(event.get("causal_class") or "unknown")
        if causal_class not in CLASSED:
            continue  # unknown: the diagnosis states no expectation
        try:
            index = int(event.get("event_index", -1))
        except (TypeError, ValueError):
            continue
        attribution = attributions.get(index)
        if attribution is None:
            continue
        error_type = str(attribution.get("error_type") or "")
        if not error_type or str(attribution.get("validity_scope") or "unknown") in NON_LEARNER_VALIDITY:
            continue
        facets = _canonical_facets(vault, list(attribution.get("target_evidence_families") or [])) or item_facets
        registry = event.get("registry_match") if isinstance(event.get("registry_match"), Mapping) else {}
        misconception_id = (
            str(registry.get("id")) if registry.get("kind") in ("durable", "candidate") and registry.get("id") else None
        )
        confidence = event.get("causal_confidence")
        posterior = _class_posterior(causal_class, confidence)
        candidate_causes = _candidate_causes(event)
        for facet in facets:
            if len(receipts) >= MAX_RECEIPTS_PER_DIAGNOSIS:
                break
            if (facet, error_type, misconception_id) in stated:
                continue
            stated.add((facet, error_type, misconception_id))
            likelihood = next_observation_likelihood(vault, facet_id=facet, error_type=error_type)
            body = FR.categorical_body(likelihood, posterior, alphabet=NEXT_OBSERVATION_ALPHABET)
            body.update({
                "target": {
                    "rule": NEXT_OBSERVATION_RULE,
                    "facet_id": facet,
                    "learning_object_id": attempt.get("learning_object_id"),
                    "after_attempt_id": attempt.get("id"),
                    "after_created_at": attempt.get("created_at"),
                    "seen_attempt_ids": seen,
                    "qualifying_attempt_types": list(QUALIFYING_ATTEMPT_TYPES),
                    "requires": "a verified plan_presentation | probe_presentation | scheduler_candidate",
                },
                "pattern": {"error_type": error_type, "misconception_id": misconception_id},
                "emissions": {
                    "same_error": "the facet is assessed and an error attributed to it shows the pattern "
                                  "(its error type or registry misconception)",
                    "pass": "otherwise, the facet's outcome on the observation reaches the high bucket",
                    "other_error": "otherwise",
                },
                "causal_class": causal_class,
                "causal_confidence": confidence,
                "candidate_causes": candidate_causes,
            })
            inputs = {
                "diagnosis_id": diagnosis_id,
                "attempt_id": attempt.get("id"),
                "blind_grade_record_id": values.get("blind_grade_record_id"),
                "event_index": index,
                "facet_id": facet,
                "error_type": error_type,
                "misconception_id": misconception_id,
                "causal_class": causal_class,
                "causal_confidence": confidence,
                "mode": values.get("mode"),
                "history_mode": values.get("history_mode"),
                "context_as_of_attempt_id": context.get("context_as_of_attempt_id"),
                "context_hash": retrieval.get("context_hash") or context.get("context_hash"),
            }
            receipts.append(FR.ForecastReceipt(
                receipt_key=f"{FR.DIAGNOSIS_NEXT_OBSERVATION}:{diagnosis_id}:{index}:{facet}:{DIAGNOSER_FORECASTER}",
                kind=FR.DIAGNOSIS_NEXT_OBSERVATION,
                forecaster=DIAGNOSER_FORECASTER,
                forecaster_version=DIAGNOSER_FORECASTER_VERSION,
                scope="next_observation",
                decision_kind="diagnosis",
                binding_kind=FR.PRESENTED_ATTEMPT_ON_FACET,
                event="next_observation_shape",
                forecast=body,
                inputs=inputs,
                parameters=parameters,
                versions={
                    "diagnosis_prompt_version": values.get("diagnosis_prompt_version"),
                    "mode": values.get("mode"),
                    "history_mode": values.get("history_mode"),
                    "provider": values.get("provider"),
                    "model": values.get("model"),
                    "next_observation_rule": NEXT_OBSERVATION_RULE,
                },
                inputs_as_of=inputs_as_of,
                p=float(body["predicted_outcomes"]["pass"]),
                columns={
                    "decision_ref": diagnosis_id,
                    "source_attempt_id": attempt.get("id"),
                    "learning_object_id": attempt.get("learning_object_id"),
                    "facet_id": facet,
                    "hypothesis_ref": misconception_id or f"error_type:{error_type}",
                },
            ))
    return receipts


def _seen_attempts(connection: Any, attempt: Mapping[str, Any]) -> list[str]:
    """The attempts created at or after ``attempt`` (not it) visible now."""

    rows = connection.execute(
        "SELECT id FROM practice_attempts WHERE created_at >= ? AND id != ? ORDER BY created_at, id",
        (str(attempt.get("created_at") or ""), str(attempt.get("id") or "")),
    ).fetchall()
    return [str(row[0]) for row in rows]


def record_diagnosis_forecasts(
    vault: Any,
    repository: Repository,
    *,
    diagnosis_id: str,
    attempt: Mapping[str, Any],
    values: Mapping[str, Any],
    record: Mapping[str, Any] | None,
    inputs_as_of: str | None = None,
    clock: Clock | None = None,
) -> list[str]:
    """Write a persisted diagnosis's receipts in ITS transaction. Never raises.

    Call it inside the diagnosis's ``repository.atomic()`` block, after its
    row: the visible attempts are read there, so the receipt names exactly
    the attempts it was written after.
    """

    try:
        if vault is None or not FR.receipts_enabled(vault):
            return []
        if values.get("status") != "completed":
            return []
        created_at = utc_now_iso(clock)
        with repository.connection() as connection:
            seen = _seen_attempts(connection, attempt)
        receipts = diagnosis_receipts(
            vault, diagnosis_id=diagnosis_id, attempt=attempt, values=values, record=record,
            seen_attempt_ids=seen, inputs_as_of=inputs_as_of,
        )
    except Exception:  # noqa: BLE001 - a receipt must never break its decision
        logger.warning("diagnosis forecast not built (diagnosis=%s)", diagnosis_id, exc_info=True)
        return []
    return FR.record_receipts(repository, receipts, vault=vault, clock=clock, created_at=created_at)


# -- the repair forecast ---------------------------------------------------------------------

REPAIR_FORECASTER = "repair_class_cold_rate"
#: v2 (Codex review F3): Beta-binomial: the class's measured cold outcomes AS
#: THEIR GRADES STAND when the receipt is written (:func:`effective_cold_outcome`:
#: a held or unassessed cold grade is no measurement, a regrade counts as
#: regraded), shrunk toward the pooled measured rate (itself
#: Laplace-smoothed) by REPAIR_PSEUDO_COUNT. v1 counted the verification's
#: immutable disposition.
REPAIR_FORECASTER_VERSION = "repair_class_cold_rate_v2"
REPAIR_ALPHABET = ("cold_success", "cold_failure")
REPAIR_PSEUDO_COUNT = 2.0
#: The cold verification's own rule for a success (``causal_probe_coherence.
#: record_delayed_cold_verification``): v1, correctness at or above the
#: frozen threshold on the task's consumed, assessed, unheld cold attempt.
REPAIR_OUTCOME_RULE = "followup_task_consumed_attempt_v1"
#: A measured disposition (the others are censored, never outcomes).
MEASURED_COLD_DISPOSITIONS = ("cold_success", "cold_failure")


def _has_table(connection: Any, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
    ).fetchone() is not None


def _assessed(connection: Any, attempt_id: str) -> bool:
    """Does the attempt's current grade assess anything? Its surviving rows,
    the last row of a criterion winning (as replay reads them), any of them
    not unassessed."""

    from learnloop.outcome_contract import unassessed_evidence_row

    if not _has_table(connection, "grading_evidence"):
        return False
    latest: dict[str, Any] = {}
    for row in connection.execute(
        "SELECT criterion_id, attribution_json FROM grading_evidence WHERE attempt_id = ? AND superseded_at IS NULL "
        "ORDER BY created_at, criterion_id, id",
        (attempt_id,),
    ):
        latest[str(row[0])] = row[1]
    return any(not unassessed_evidence_row(attribution) for attribution in latest.values())


def effective_cold_outcome(connection: Any, cold_attempt_id: str, *, threshold: float) -> tuple[str | None, str]:
    """A measured cold verification's outcome as the cold attempt's grade
    stands NOW: ``(cold_success | cold_failure, "realized")``, or ``(None,
    why not)``: the grade is held for review (THE held predicate), assesses
    nothing, or there is no correctness. The disposition row is immutable; a
    regrade or a hold since the verification is read here. The repair
    forecaster's measured sample (as of its receipt) and the report's
    resolution (as of the report) read outcomes through this one rule."""

    from learnloop.held_grades import held_for_review_attempts
    from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW

    cold_attempt_id = str(cold_attempt_id)
    if cold_attempt_id in held_for_review_attempts(connection, (cold_attempt_id,)):
        return None, GRADE_HELD_FOR_REVIEW
    if not _assessed(connection, cold_attempt_id):
        return None, "cold_attempt_unassessed"
    row = connection.execute("SELECT correctness FROM practice_attempts WHERE id = ?", (cold_attempt_id,)).fetchone()
    if row is None or row[0] is None:
        return None, "ungraded"
    return ("cold_success" if float(row[0]) >= float(threshold) else "cold_failure"), "realized"


def _measured_cold_outcomes(connection: Any, repair_class_id: str | None, *, threshold: float) -> dict[str, Any]:
    """The measured cold outcomes as their grades stand now (Codex review F3):
    every measured disposition's cold attempt read through
    :func:`effective_cold_outcome`; the ones that no longer measure anything
    are counted by reason, never in the sample."""

    pooled = {"successes": 0, "n": 0}
    own = {"successes": 0, "n": 0}
    excluded: dict[str, int] = {}
    if not _has_table(connection, "causal_cold_outcomes"):
        return {"pooled": pooled, "class": own, "excluded": excluded}
    marks = ",".join("?" for _ in MEASURED_COLD_DISPOSITIONS)
    for _outcome, row_class, cold_attempt_id in connection.execute(
        f"SELECT outcome, repair_class_id, cold_attempt_id FROM causal_cold_outcomes WHERE outcome IN ({marks}) "
        "ORDER BY created_at, id",
        MEASURED_COLD_DISPOSITIONS,
    ).fetchall():
        if not cold_attempt_id:
            excluded["missing_cold_attempt"] = excluded.get("missing_cold_attempt", 0) + 1
            continue
        emission, why = effective_cold_outcome(connection, str(cold_attempt_id), threshold=threshold)
        if emission is None:
            excluded[why] = excluded.get(why, 0) + 1
            continue
        success = 1 if emission == "cold_success" else 0
        pooled["n"] += 1
        pooled["successes"] += success
        if repair_class_id is not None and row_class == repair_class_id:
            own["n"] += 1
            own["successes"] += success
    return {"pooled": pooled, "class": own, "excluded": dict(sorted(excluded.items()))}


def repair_receipt(
    connection: Any,
    *,
    attempt: Mapping[str, Any],
    repair_class_id: str | None,
    hypothesis_ids: Sequence[str],
    episode: Mapping[str, Any] | None,
    task: Mapping[str, Any] | None,
    censor_reason: str | None,
    success_threshold: float,
) -> FR.ForecastReceipt:
    """The repair class's predicted cold outcome (reads the measured ledger)."""

    measured = _measured_cold_outcomes(connection, repair_class_id, threshold=success_threshold)
    pooled, own = measured["pooled"], measured["class"]
    pooled_mean = (pooled["successes"] + 1.0) / (pooled["n"] + 2.0)
    p = (own["successes"] + REPAIR_PSEUDO_COUNT * pooled_mean) / (own["n"] + REPAIR_PSEUDO_COUNT)
    hypothesis = f"repair_class:{repair_class_id or 'unmapped'}"
    body = FR.categorical_body({hypothesis: {"cold_success": p, "cold_failure": 1.0 - p}}, {hypothesis: 1.0},
                               alphabet=REPAIR_ALPHABET)
    body["measured"] = {"class": dict(own), "pooled": dict(pooled), "pooled_mean": round(pooled_mean, 8),
                        "excluded": dict(measured["excluded"])}
    task_id = (task or {}).get("id")
    episode_id = (episode or {}).get("id")
    cold_item_id = (task or {}).get("selected_item_id") or (episode or {}).get("cold_item_id")
    body["target"] = {
        "rule": REPAIR_OUTCOME_RULE,
        "followup_task_id": task_id,
        "cold_item_id": cold_item_id,
        "success_threshold": float(success_threshold),
        "primed_attempt_id": attempt.get("id"),
    }
    parameters = [
        VF.parameter("REPAIR_PSEUDO_COUNT", REPAIR_PSEUDO_COUNT, "heuristic", source="authored_prior"),
        VF.parameter("pooled_cold_success_rate", round(pooled_mean, 8),
                     "measured" if pooled["n"] else "population_prior",
                     source="causal_cold_outcomes" if pooled["n"] else "laplace_prior", sample_count=pooled["n"]),
        VF.parameter("class_cold_successes", own["successes"], "measured" if own["n"] else "heuristic",
                     source="causal_cold_outcomes", sample_count=own["n"],
                     note="measured dispositions read as their cold grades stand (held/unassessed excluded)"),
        VF.parameter("cold_verification_success_correctness", float(success_threshold), "heuristic",
                     source="causal_probe_parameters", note="what a cold success is"),
    ]
    subject = task_id or episode_id or attempt.get("id")
    columns: dict[str, Any] = {
        "decision_ref": subject,
        "source_attempt_id": attempt.get("id"),
        "learning_object_id": attempt.get("learning_object_id"),
        "hypothesis_ref": (episode or {}).get("case_ref") or (sorted(hypothesis_ids)[0] if hypothesis_ids else None),
        "practice_item_id": cold_item_id,
    }
    if task_id:
        columns["followup_task_id"] = task_id
        binding = FR.FOLLOWUP_TASK
    else:
        columns["censor_reason"] = censor_reason or "no_cold_task"
        binding = FR.NO_BINDING
    return FR.ForecastReceipt(
        receipt_key=f"{FR.REPAIR_COLD_OUTCOME}:{subject}:{REPAIR_FORECASTER}",
        kind=FR.REPAIR_COLD_OUTCOME,
        forecaster=REPAIR_FORECASTER,
        forecaster_version=REPAIR_FORECASTER_VERSION,
        scope="followup_task",
        decision_kind="cold_retry_schedule",
        binding_kind=binding,
        event="cold_success",
        forecast=body,
        inputs={
            "primed_attempt_id": attempt.get("id"),
            "remediation_episode_id": episode_id,
            "followup_task_id": task_id,
            "repair_class_id": repair_class_id,
            "hypothesis_ids": sorted({str(h) for h in hypothesis_ids if h}),
            "measured_cold_outcomes": pooled["n"],
        },
        parameters=parameters,
        versions={"repair_outcome_rule": REPAIR_OUTCOME_RULE},
        p=float(body["predicted_outcomes"]["cold_success"]),
        columns=columns,
    )


def record_repair_expectation(
    vault: Any,
    repository: Repository,
    *,
    attempt: Mapping[str, Any],
    repair_class_id: str | None,
    hypothesis_ids: Sequence[str] = (),
    episode: Mapping[str, Any] | None = None,
    task: Mapping[str, Any] | None = None,
    censor_reason: str | None = None,
    clock: Clock | None = None,
) -> list[str]:
    """Write a repair's predicted cold outcome in the primed attempt's
    transaction. ``vault`` None (replay or a regrade re-applying a recorded
    attempt) writes nothing. Never raises."""

    if vault is None:
        return []
    try:
        if not FR.receipts_enabled(vault):
            return []
        from learnloop.diagnosis.causal_probe_coherence import resolve_causal_probe_parameters

        threshold = float(resolve_causal_probe_parameters(repository)["cold_verification_success_correctness"])
        with repository.connection() as connection:
            receipt = repair_receipt(
                connection, attempt=attempt, repair_class_id=repair_class_id,
                hypothesis_ids=hypothesis_ids, episode=episode, task=task, censor_reason=censor_reason,
                success_threshold=threshold,
            )
    except Exception:  # noqa: BLE001 - a receipt must never break its decision
        logger.warning("repair forecast not built (attempt=%s)", attempt.get("id"), exc_info=True)
        return []
    return FR.record_receipts(repository, [receipt], vault=vault, clock=clock)


__all__ = [
    "DIAGNOSER_FORECASTER",
    "DIAGNOSER_FORECASTER_VERSION",
    "MEASURED_COLD_DISPOSITIONS",
    "NEXT_OBSERVATION_ALPHABET",
    "NEXT_OBSERVATION_RULE",
    "QUALIFYING_ATTEMPT_TYPES",
    "REPAIR_ALPHABET",
    "REPAIR_FORECASTER",
    "REPAIR_FORECASTER_VERSION",
    "REPAIR_OUTCOME_RULE",
    "diagnosis_receipts",
    "effective_cold_outcome",
    "next_observation_likelihood",
    "record_diagnosis_forecasts",
    "record_repair_expectation",
    "repair_receipt",
]
