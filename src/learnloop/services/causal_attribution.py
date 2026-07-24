"""P0 causal-attribution learner report and trace-consistency helpers."""

from __future__ import annotations

import re
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault

SELF_REPORT_REASONS = frozenset(
    {
        "slipped",
        "believed_candidate",
        "item_unclear",
        "other_valid_approach",
        "diagnosis_wrong",
    }
)

_NORMALIZE_RE = re.compile(r"\W+")


def _normalized(value: str) -> str:
    return _NORMALIZE_RE.sub(" ", value.casefold()).strip()


def _trace_consistent(
    vault: LoadedVault,
    repository: Repository,
    attempt_id: str,
) -> bool:
    """Hard-veto deterministic postdictive claims contradicted by full credit."""

    attempt = repository.fetch_practice_attempt(attempt_id)
    if attempt is None:
        return False
    item = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
    if item is None:
        return False
    rubric = vault.rubric_for_item(item)
    if rubric is None:
        return False
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    awarded = {
        row.criterion_id: float(row.points_awarded)
        for row in repository.fetch_grading_evidence(attempt_id)
    }
    for event in repository.error_events_for_attempt(attempt_id):
        plan = event.get("repair_plan")
        if not isinstance(plan, dict):
            continue
        for claim in plan.get("postdictive_claims") or []:
            if not isinstance(claim, dict):
                continue
            criterion_id = str(claim.get("criterion_id") or "")
            maximum = maxima.get(criterion_id)
            if maximum is None or criterion_id not in awarded:
                continue
            if awarded[criterion_id] >= maximum - 1e-9:
                return False
    return True


def record_unresolved_cause_self_report(
    vault: LoadedVault,
    repository: Repository,
    *,
    factor_id: str,
    response: str,
    candidate_index: int | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the one-tap report; confirmation may open a provisional belief."""

    if response not in SELF_REPORT_REASONS:
        raise ValueError(f"unknown unresolved-cause self-report reason {response!r}")
    factor = repository.unresolved_cause_factor(factor_id)
    if factor is None or factor.get("status") != "open":
        raise ValueError("unresolved-cause factor is not open")
    presented_factor = next(
        (
            row
            for row in repository.unresolved_cause_factors_for_attempt(
                str(factor["attempt_id"])
            )
            if row["id"] == factor_id
        ),
        None,
    )
    if presented_factor is not None and presented_factor.get("self_report") is not None:
        raise ValueError("unresolved-cause factor already has a learner report")
    candidates = list(factor.get("candidate_causes") or [])
    selected: dict[str, Any] | None = None
    if response == "believed_candidate":
        if candidate_index is None or not 0 <= candidate_index < len(candidates):
            raise ValueError("believed_candidate requires a valid candidate_index")
        raw = candidates[candidate_index]
        if not isinstance(raw, dict) or raw.get("hypothesis_id") == "H_OTHER":
            raise ValueError("believed_candidate must select a concrete hypothesis")
        selected = raw

    report_id = new_ulid()
    observation_id = f"learner_report:{report_id}"
    attempt_id = str(factor["attempt_id"])
    repository.insert_causal_attribution_report(
        report_id=report_id,
        factor_id=factor_id,
        attempt_id=attempt_id,
        response=response,
        candidate_index=candidate_index,
        payload={"observation_id": observation_id},
        clock=clock,
    )

    provisional_belief_id: str | None = None
    resolved = False
    if selected is not None and _trace_consistent(vault, repository, attempt_id):
        attempt = repository.fetch_practice_attempt(attempt_id) or {}
        learning_object_id = str(attempt.get("learning_object_id") or "")
        learning_object = vault.learning_objects.get(learning_object_id)
        statement = str(selected.get("statement") or "").strip()
        if statement and learning_object is not None:
            item = vault.practice_items.get(
                str(attempt.get("practice_item_id") or "")
            )
            error_events = repository.error_events_for_attempt(attempt_id)
            surface_families: list[str] = []
            if item is not None:
                from learnloop.services.canonical_projection import surface_group_id

                surface_families = [surface_group_id(item)]
            existing = repository.misconception_candidate_by_normalized(
                learning_object_id, _normalized(statement)
            )
            if existing is None:
                target_ref = selected.get("target_ref")
                target_ref = target_ref if isinstance(target_ref, dict) else {}
                facet = (
                    target_ref.get("facet_id")
                    if target_ref.get("kind") == "facet_capability"
                    else selected.get("facet")
                )
                provisional_belief_id = repository.insert_misconception_candidate(
                    learning_object_id=learning_object_id,
                    statement=statement,
                    statement_normalized=_normalized(statement),
                    concept_id=learning_object.concept,
                    target_facet=str(facet) if facet else None,
                    facet_ids=[str(facet)] if facet else [],
                    source_error_event_ids=[
                        str(event["id"]) for event in error_events
                    ],
                    surface_families=surface_families,
                    item_ids=[str(attempt.get("practice_item_id") or "")],
                    occurrence_count=1,
                    severity=max(
                        (float(event.get("severity") or 0.0) for event in error_events),
                        default=0.7,
                    ),
                    clock=clock,
                )
            else:
                provisional_belief_id = str(existing["id"])
                repository.update_misconception_candidate(
                    provisional_belief_id,
                    occurrence_count=int(existing.get("occurrence_count") or 0) + 1,
                    severity=max(
                        float(existing.get("severity") or 0.0),
                        max(
                            (
                                float(event.get("severity") or 0.0)
                                for event in error_events
                            ),
                            default=0.7,
                        ),
                    ),
                    append_source_error_event_ids=[
                        str(event["id"]) for event in error_events
                    ],
                    add_surface_families=surface_families,
                    add_item_ids=[str(attempt.get("practice_item_id") or "")],
                    clock=clock,
                )
            resolved = repository.resolve_unresolved_cause_factor(
                factor_id,
                resolution_observation_ids=[observation_id],
                clock=clock,
            )
    return {
        "factor_id": factor_id,
        "response": response,
        "resolved": resolved,
        "provisional_belief_id": provisional_belief_id,
        "observation_id": observation_id,
    }
