"""Typed learner-facing claim dispatch and local response telemetry.

This module is deliberately presentation-only: responses never mutate evidence,
canonical content, grading, or learner belief state.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Iterable, Mapping

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository


CLAIM_CLASSES = {"estimate", "diagnosis", "policy", "ledger_fact"}
TEMPERATURES = {"hot", "cold"}
PRIORITY = {
    "misconception": 0,
    "regrade": 1,
    "forecast": 2,
    "ready_estimate": 3,
    "schedule_choice": 4,
    "session_delta": 5,
}


class HypothesisClaimError(ValueError):
    pass


def canonical_claim_ref(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _validate_candidate(candidate: Mapping[str, Any]) -> None:
    if candidate.get("claim_class") not in CLAIM_CLASSES:
        raise HypothesisClaimError("unknown claim_class")
    if not str(candidate.get("claim_type") or "").strip():
        raise HypothesisClaimError("claim_type is required")
    if candidate.get("temperature") not in TEMPERATURES:
        raise HypothesisClaimError("temperature must be hot or cold")
    if not str(candidate.get("claim_version") or "").strip():
        raise HypothesisClaimError("claim_version is required")
    if not str(candidate.get("producer_version") or "").strip():
        raise HypothesisClaimError("producer_version is required")


def _cooldown_active(
    repository: Repository,
    *,
    claim_ref: str,
    claim_version: str,
    cooldown_days: int,
    clock: Clock,
) -> bool:
    responded_at = parse_utc(repository.last_hypothesis_response_at(claim_ref, claim_version))
    if responded_at is None:
        return False
    return clock.now() < responded_at + timedelta(days=max(cooldown_days, 0))


def present_claims(
    repository: Repository,
    candidates: Iterable[Mapping[str, Any]],
    *,
    session_id: str | None = None,
    visit_id: str | None = None,
    session_card_budget: int = 2,
    claim_cooldown_days: int = 7,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Dispatch claims under the attention budget and persist presentations.

    Repeating the exact claim/surface/session-or-visit returns the existing row;
    supplying ``visible_at`` on that repeat patches actual viewport exposure.
    """

    if session_id is None and visit_id is None:
        raise HypothesisClaimError("session_id or visit_id is required")
    clock = clock or SystemClock()
    ordered = [dict(candidate) for candidate in candidates]
    for candidate in ordered:
        _validate_candidate(candidate)
    ordered.sort(
        key=lambda c: (
            0 if c["temperature"] == "hot" else 1,
            PRIORITY.get(str(c["claim_type"]), 99),
            canonical_claim_ref(c.get("claim_ref")),
        )
    )

    results: list[dict[str, Any]] = []
    soliciting_count = repository.soliciting_hypothesis_count(
        session_id=session_id, visit_id=visit_id
    )
    cold_count = repository.cold_hypothesis_count_for_visit(visit_id) if visit_id else 0

    for candidate in ordered:
        claim_ref = canonical_claim_ref(candidate.get("claim_ref"))
        claim_version = str(candidate["claim_version"])
        existing = repository.find_hypothesis_presentation(
            claim_ref=claim_ref,
            claim_version=claim_version,
            surface=str(candidate["surface"]),
            session_id=session_id,
            visit_id=visit_id,
        )
        visible_at = candidate.get("visible_at")
        if existing is not None:
            if visible_at:
                existing = repository.mark_hypothesis_visible(existing["id"], str(visible_at)) or existing
            results.append(_presentation_result(candidate, existing, debounced=True))
            continue

        suppression_reason: str | None = None
        is_cold_reask = bool(candidate.get("cold_reask"))
        if (
            _cooldown_active(
                repository,
                claim_ref=claim_ref,
                claim_version=claim_version,
                cooldown_days=claim_cooldown_days,
                clock=clock,
            )
            and not is_cold_reask
        ):
            suppression_reason = "claim_cooldown"
        elif is_cold_reask and visit_id is not None and cold_count >= 1:
            suppression_reason = "cold_reask_visit_limit"
        else:
            budget = max(session_card_budget, 0)
            # Reserve one slot for a hot Feedback claim. Cold surfaces can use
            # at most budget-1; a hot surface may use the full configured cap.
            available = budget if candidate["temperature"] == "hot" else max(budget - 1, 0)
            if soliciting_count >= available:
                suppression_reason = "session_card_budget"

        event = repository.insert_hypothesis_event(
            event_type="presented",
            claim_class=str(candidate["claim_class"]),
            claim_type=str(candidate["claim_type"]),
            claim_ref=claim_ref,
            claim_version=claim_version,
            producer_version=str(candidate["producer_version"]),
            surface=str(candidate["surface"]),
            temperature=str(candidate["temperature"]),
            visible_at=str(visible_at) if visible_at else None,
            suppression_reason=suppression_reason,
            session_id=session_id,
            visit_id=visit_id,
            clock=clock,
        )
        if suppression_reason is None:
            soliciting_count += 1
            if candidate["temperature"] == "cold" and visit_id is not None:
                cold_count += 1
        results.append(_presentation_result(candidate, event, debounced=False))
    return results


def _presentation_result(
    candidate: Mapping[str, Any], event: Mapping[str, Any], *, debounced: bool
) -> dict[str, Any]:
    result = dict(candidate)
    result.update(
        {
            "presentation_id": event["id"],
            "affordances_enabled": event.get("suppression_reason") is None,
            "suppression_reason": event.get("suppression_reason"),
            "visible_at": event.get("visible_at"),
            "debounced": debounced,
        }
    )
    return result


def _presentation_or_raise(repository: Repository, presentation_id: str) -> dict[str, Any]:
    presentation = repository.hypothesis_event(presentation_id)
    if presentation is None or presentation.get("event_type") != "presented":
        raise HypothesisClaimError("presentation does not exist")
    if presentation.get("suppression_reason") is not None:
        raise HypothesisClaimError("suppressed claims have no response affordance")
    return presentation


def record_response(
    repository: Repository,
    presentation_id: str,
    payload: Mapping[str, Any],
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    presentation = _presentation_or_raise(repository, presentation_id)
    if any(
        event["event_type"] == "responded" and event["presentation_id"] == presentation_id
        for event in repository.list_hypothesis_events()
    ):
        raise HypothesisClaimError("presentation already has a response")
    if not payload:
        raise HypothesisClaimError("response payload is required")
    return repository.insert_hypothesis_event(
        event_type="responded",
        presentation_id=presentation_id,
        claim_class=presentation["claim_class"],
        claim_type=presentation["claim_type"],
        claim_ref=presentation["claim_ref"],
        claim_version=presentation["claim_version"],
        producer_version=presentation["producer_version"],
        surface=presentation["surface"],
        temperature=presentation["temperature"],
        response_payload=payload,
        session_id=presentation.get("session_id"),
        visit_id=presentation.get("visit_id"),
        clock=clock,
    )


def dismiss_claim(
    repository: Repository, presentation_id: str, *, clock: Clock | None = None
) -> dict[str, Any]:
    presentation = _presentation_or_raise(repository, presentation_id)
    return repository.insert_hypothesis_event(
        event_type="dismissed",
        presentation_id=presentation_id,
        claim_class=presentation["claim_class"],
        claim_type=presentation["claim_type"],
        claim_ref=presentation["claim_ref"],
        claim_version=presentation["claim_version"],
        producer_version=presentation["producer_version"],
        surface=presentation["surface"],
        temperature=presentation["temperature"],
        session_id=presentation.get("session_id"),
        visit_id=presentation.get("visit_id"),
        clock=clock,
    )


def export_claim_events(repository: Repository) -> list[dict[str, Any]]:
    return repository.list_hypothesis_events()


def purge_claim_events(repository: Repository) -> int:
    return repository.purge_hypothesis_events()
