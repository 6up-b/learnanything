"""Carry repair context into delayed cold retries and record their outcomes.

The cold check verifies the selected repair on an independent, unassisted
retry after the primed source attempt, using the context stored on its task.
Terminal refusals and measured outcomes also receive final coldness receipts.
The queue marks a retry expired when its serving window ends; the expiry
sweep records censoring for a genuine serving opportunity, or structural
unmeasurability when an independent surface was unavailable or unservable.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_probe_coherence import candidate_has_current_blind_input_contract
from learnloop.diagnosis.causal_reads import (
    CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    _case_repair_class_id,
    _receipt_repair_class_id,
    diagnosis_receipt,
    open_factors_for_hypothesis,
)
from learnloop.vault.models import LoadedVault


def cold_verification_context(
    vault: LoadedVault | None,
    repository: Repository,
    *,
    episode: Mapping[str, Any],
    source_attempt: Mapping[str, Any],
) -> dict[str, Any]:
    """Everything ``record_delayed_cold_verification`` will need, resolved NOW.

    §6.2: carry the source attempt, causal factor, hypothesis set, repair class
    and avoided affordances THROUGH the follow-up task record.  Resolving them
    days later, from a consumed task and a bare item id, is the "future caller
    reconstructs it" assumption that leaves the cold channel unwired.

    ``vault`` is optional because this runs inside ``apply_attempt``'s
    remediation hook, which has no vault handle; without it the source surface
    family is simply not named among the avoided affordances.
    """

    from learnloop.substrate.canonical_projection import surface_group_id

    case_ref = str(episode.get("case_ref") or "")
    hypothesis = (
        repository.causal_hypothesis(case_ref)
        if episode.get("case_kind") == "diagnosis"
        else None
    )
    factor_id: str | None = None
    hypothesis_set_id: str | None = None
    repair_class_id: str | None = None
    hypothesis_ids: list[str] = []
    if hypothesis is not None:
        hypothesis_ids = [str(hypothesis["id"])]
        # Same resolution the G14 episode gate uses (`_case_repair_class_id`):
        # the hypothesis's own mapping, then its DIAGNOSING attempt's receipt.
        # The primed source attempt's receipt (the generic fallback below) is
        # empty for a clean primed redo, so without this the gate and the
        # carried context could disagree about measurability.
        repair_class_id = _case_repair_class_id(repository, hypothesis)
        factors = open_factors_for_hypothesis(repository, case_ref)
        if factors:
            factor_id = str(factors[0]["id"])
            hypothesis_ids = sorted(
                {
                    str(value.get("hypothesis_id"))
                    for value in factors[0].get("candidate_causes") or []
                    if isinstance(value, Mapping) and value.get("hypothesis_id")
                }
                | set(hypothesis_ids)
            )
            candidates = repository.causal_probe_candidates_for_factor(factor_id)
            candidates = [
                value
                for value in candidates
                if candidate_has_current_blind_input_contract(value)
            ]
            if candidates:
                hypothesis_set_id = str(candidates[0]["hypothesis_set_id"])
    if repair_class_id is None:
        repair_class_id = _receipt_repair_class_id(
            diagnosis_receipt(
                repository, str(source_attempt.get("id") or "") or None
            )
        )
    if repair_class_id is None and episode.get("case_kind") == "misconception":
        # Case-level fallback: a clean primed attempt materializes no causal
        # episode and therefore has no diagnosis receipt of its own. The repair
        # class the cold retry verifies was selected when the misconception was
        # DIAGNOSED, so read it off the newest diagnosing attempt's receipt.
        misconception = repository.misconception(case_ref)
        source_event_ids = (
            list(misconception.source_error_event_ids)
            if misconception is not None
            else []
        )
        for attempt_id in repository.attempt_ids_for_misconception(
            case_ref, event_ids=source_event_ids
        ):
            repair_class_id = _receipt_repair_class_id(
                diagnosis_receipt(repository, attempt_id)
            )
            if repair_class_id is not None:
                break

    # The affordances the primed source attempt had and the cold retry avoids.
    avoided: list[str] = ["primed_repair_context"]
    if int(source_attempt.get("hints_used") or 0) > 0:
        avoided.append("hints")
    primed_item = (
        vault.practice_items.get(str(source_attempt.get("practice_item_id") or ""))
        if vault is not None
        else None
    )
    if primed_item is not None:
        avoided.append(f"surface_family:{surface_group_id(primed_item)}")
    if episode.get("passages_shown"):
        avoided.append("remediation_passages")

    return {
        "kind": "causal_cold_verification",
        "formula_version": CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
        "source_attempt_id": str(source_attempt.get("id") or ""),
        "causal_factor_id": factor_id,
        "hypothesis_set_id": hypothesis_set_id,
        "hypothesis_ids": hypothesis_ids,
        "repair_class_id": repair_class_id,
        "avoided_affordances": sorted(set(avoided)),
    }


def record_cold_verification_from_task(
    vault: LoadedVault,
    repository: Repository,
    *,
    task: Mapping[str, Any],
    cold_attempt_id: str,
    clock: Clock | None = None,
) -> dict[str, Any] | None:
    """Fire the delayed cold verification when a scheduled retry completes.

    Returns the receipt, or None when the carried context is incomplete or the
    pair does not satisfy the §6.2 preconditions (same surface family, assisted
    retry, non-monotone chronology).  This runs inside ``apply_attempt``, so it
    must never raise on the hot path — but "does not apply" is a terminal
    disposition, not silence: every path below lands a typed §4.3 row
    (migration 145), because expiry, decline, contamination and same-surface
    reuse being indistinguishable from "no row" is exactly how the repair
    lane's cold corpus stayed empty.

    Migration 149: every terminal path — measured verification or refusal —
    also lands a FINAL coldness receipt (``coldness_receipts``), so "cold" is
    positive recorded evidence rather than an inference from ``hints_used ==
    0``.  Two receipt findings hard-fail (typed ``contaminated_or_assisted``
    disposition instead of a verification): the cold item's own answer was
    revealed post-primed, or a hard same-surface exposure landed post-primed.
    Everything else (co-interventions, indeterminate telemetry, unknown
    blinding) records as evidence without blocking, so the lane is never
    starved by its own receipts.
    """

    from learnloop.diagnosis.causal_probe_coherence import (
        ColdVerificationPrecondition,
        record_causal_cold_outcome,
        record_delayed_cold_verification,
    )
    from learnloop.attempts.coldness_receipt import (
        evaluate_final_coldness,
        record_final_receipt,
    )

    evaluation = evaluate_final_coldness(
        vault, repository, task=task, cold_attempt_id=cold_attempt_id, clock=clock
    )

    def _final_receipt(outcome: str, *, cold_verification_id: str | None = None) -> None:
        try:
            record_final_receipt(
                repository,
                task=task,
                evaluation=evaluation,
                outcome=outcome,
                cold_attempt_id=cold_attempt_id,
                cold_verification_id=cold_verification_id,
                clock=clock,
            )
        except Exception:  # pragma: no cover - receipts must not fail an attempt
            logging.getLogger(__name__).warning(
                "coldness final receipt failed for task %s",
                task.get("id"),
                exc_info=True,
            )

    def _disposition(
        outcome: str,
        *,
        cold_verification_id: str | None = None,
        detail: Mapping[str, Any] | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        record_causal_cold_outcome(
            repository,
            outcome=outcome,
            followup_task_id=str(task.get("id") or "") or None,
            remediation_episode_id=(
                str(task.get("remediation_episode_id") or "") or None
            ),
            case_kind=str(task.get("case_kind") or "") or None,
            case_ref=str(task.get("case_ref") or "") or None,
            source_attempt_id=(
                str((context or {}).get("source_attempt_id") or "")
                or (str(task.get("source_attempt_id") or "") or None)
            ),
            cold_attempt_id=cold_attempt_id,
            repair_class_id=(
                str((context or {}).get("repair_class_id") or "") or None
            ),
            hypothesis_ids=[
                str(value) for value in (context or {}).get("hypothesis_ids") or []
            ],
            cold_verification_id=cold_verification_id,
            # The task was served and consumed, so the opportunity was genuine.
            servable_opportunity=True,
            detail=detail,
            scheduled_not_before=str(task.get("not_before") or "") or None,
            scheduled_expires_at=str(task.get("expires_at") or "") or None,
            clock=clock,
        )

    context = task.get("context")
    if not isinstance(context, Mapping) or context.get("kind") != "causal_cold_verification":
        _disposition(
            "missing_chain",
            detail={"reason": "no_causal_cold_verification_context"},
        )
        _final_receipt("missing_chain")
        return None
    repair_class_id = context.get("repair_class_id")
    source_attempt_id = context.get("source_attempt_id")
    if not repair_class_id or not source_attempt_id:
        # No repair class means there is no repair-effect claim to make.  The
        # chain is incomplete, and that fact is the record.
        _disposition(
            "missing_chain",
            detail={
                "reason": "no_repair_class"
                if not repair_class_id
                else "no_source_attempt"
            },
            context=context,
        )
        _final_receipt("missing_chain")
        return None
    # Migration 149 hard-fail set — the ONLY receipt findings that block: the
    # cold item's own answer revealed post-primed, or a hard same-surface
    # exposure post-primed.  Checked only for an otherwise-clean attempt so an
    # assisted retry still lands the assistance-shaped detail below.
    cold_attempt = repository.fetch_practice_attempt(cold_attempt_id)
    attempt_clean = (
        cold_attempt is not None
        and not cold_attempt.get("primed")
        and not int(cold_attempt.get("hints_used") or 0)
    )
    if evaluation.hard_contamination is not None and attempt_clean:
        _disposition(
            "contaminated_or_assisted",
            detail={
                "reason": evaluation.hard_contamination["reason"],
                "exposure_event_ids": list(
                    evaluation.hard_contamination.get("event_ids") or []
                ),
            },
            context=context,
        )
        _final_receipt("contaminated_or_assisted")
        return None
    try:
        receipt = record_delayed_cold_verification(
            vault,
            repository,
            source_attempt_id=str(source_attempt_id),
            cold_attempt_id=cold_attempt_id,
            repair_class_id=str(repair_class_id),
            hypothesis_ids=[
                str(value) for value in context.get("hypothesis_ids") or []
            ],
            avoided_affordances=[
                str(value) for value in context.get("avoided_affordances") or []
            ],
            clock=clock,
        )
    except ColdVerificationPrecondition as exc:
        _disposition(exc.reason, detail={"message": str(exc), **exc.detail}, context=context)
        _final_receipt(exc.reason)
        return None
    except ValueError as exc:
        # A caller-contract violation with no §4.3 disposition of its own.
        _disposition("missing_chain", detail={"message": str(exc)}, context=context)
        _final_receipt("missing_chain")
        return None
    outcome = "cold_success" if receipt.get("success") else "cold_failure"
    _disposition(
        outcome,
        cold_verification_id=str(receipt["id"]),
        context=context,
    )
    _final_receipt(outcome, cold_verification_id=str(receipt["id"]))
    return receipt


def sweep_expired_cold_retries(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Turn silent cold-retry expiries into typed §4.3 dispositions.

    The queue's expiry UPDATE (``due_followup_tasks``) is a status transition,
    not a label.  Spec §4.3: only a task that had a genuine independent serving
    opportunity may become ordinary right-censoring — an expired task whose
    surface was never servable, or whose pair never had an independent surface,
    records structural unmeasurability instead.
    """

    from learnloop.substrate.canonical_projection import surface_group_id
    from learnloop.diagnosis.causal_probe_coherence import record_causal_cold_outcome
    from learnloop.attempts.coldness_receipt import (
        evaluate_final_coldness,
        record_final_receipt,
    )
    from learnloop.substrate.instrument_serving import unservable_reason

    recorded: list[dict[str, Any]] = []
    for task in repository.expired_cold_retry_tasks_without_outcome():
        context = task.get("context")
        context = context if isinstance(context, Mapping) else {}
        outcome = "right_censored_expired"
        servable = True
        detail: dict[str, Any] = {"stage": "expiry"}

        cold_item = vault.practice_items.get(str(task.get("selected_item_id") or ""))
        if cold_item is None:
            outcome, servable = "unmeasurable_unservable_surface", False
            detail["reason"] = "selected_item_missing"
        elif unservable_reason(cold_item) is not None:
            outcome, servable = "unmeasurable_unservable_surface", False
            detail["reason"] = unservable_reason(cold_item)
        else:
            state = repository.practice_item_state(cold_item.id)
            if state is not None and not state.active:
                outcome, servable = "unmeasurable_unservable_surface", False
                detail["reason"] = "selected_item_inactive"
            else:
                source_attempt_id = str(
                    context.get("source_attempt_id")
                    or task.get("source_attempt_id")
                    or ""
                )
                source_attempt = (
                    repository.fetch_practice_attempt(source_attempt_id)
                    if source_attempt_id
                    else None
                )
                source_item = (
                    vault.practice_items.get(
                        str(source_attempt.get("practice_item_id") or "")
                    )
                    if source_attempt is not None
                    else None
                )
                if source_item is not None and surface_group_id(
                    source_item
                ) == surface_group_id(cold_item):
                    outcome, servable = "unmeasurable_no_held_out_surface", False
                    detail["reason"] = "no_independent_surface"

        row = record_causal_cold_outcome(
            repository,
            outcome=outcome,
            followup_task_id=str(task["id"]),
            remediation_episode_id=(
                str(task.get("remediation_episode_id") or "") or None
            ),
            case_kind=str(task.get("case_kind") or "") or None,
            case_ref=str(task.get("case_ref") or "") or None,
            source_attempt_id=(
                str(context.get("source_attempt_id") or "")
                or (str(task.get("source_attempt_id") or "") or None)
            ),
            repair_class_id=str(context.get("repair_class_id") or "") or None,
            hypothesis_ids=[
                str(value) for value in context.get("hypothesis_ids") or []
            ],
            servable_opportunity=servable,
            detail=detail,
            scheduled_not_before=str(task.get("not_before") or "") or None,
            scheduled_expires_at=str(task.get("expires_at") or "") or None,
            clock=clock,
        )
        if row is not None:
            recorded.append(row)
            # Migration 149: an expiry is a terminal disposition too, so it
            # gets a final receipt with partial evidence — notably whether an
            # administration snapshot exists (the task was OPENED but never
            # answered) versus no snapshot at all (never served).
            try:
                record_final_receipt(
                    repository,
                    task=task,
                    evaluation=evaluate_final_coldness(
                        vault,
                        repository,
                        task=task,
                        cold_attempt_id=None,
                        clock=clock,
                    ),
                    outcome=outcome,
                    clock=clock,
                )
            except Exception:  # pragma: no cover - receipts must not fail sweeps
                logging.getLogger(__name__).warning(
                    "coldness final receipt failed for expired task %s",
                    task.get("id"),
                    exc_info=True,
                )
    return recorded
