"""Durable misconception-repair episode lifecycle and cold retries."""

from __future__ import annotations

from datetime import UTC, timedelta
from typing import Any

from learnloop.clock import Clock, SystemClock, parse_utc
from learnloop.db.repositories import Repository
from learnloop.ingest.locators import parse_block_span
from learnloop.services.provenance import get_entity_provenance
from learnloop.services.span_view import SpanViewError, build_span_view
from learnloop.vault.models import LoadedVault


class RemediationError(ValueError):
    pass


def start_remediation_episode(
    repository: Repository,
    misconception_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    misconception = repository.misconception(misconception_id)
    if misconception is None or misconception.status not in {"active", "resolving"}:
        raise RemediationError("repair requires an active durable misconception")
    return repository.create_remediation_episode(
        case_kind="misconception", case_ref=misconception_id, clock=clock
    )


def prescribe_remediation(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    episode = repository.remediation_episode(episode_id)
    if episode is None:
        raise RemediationError("remediation episode does not exist")
    misconception = repository.misconception(episode["case_ref"])
    if misconception is None:
        raise RemediationError("remediation case no longer exists")

    passages: list[dict[str, Any]] = []
    for role, facet_id in (
        ("target", misconception.target_facet),
        ("confused_with", misconception.confused_with_facet),
    ):
        if not facet_id:
            continue
        provenance = get_entity_provenance(repository, "facet", facet_id)
        links = provenance.get("semantic_sources") or []
        for link in links:
            parsed = parse_block_span(str(link.get("locator") or ""))
            if parsed is None:
                continue
            extraction_id, span_id = parsed
            try:
                view = build_span_view(
                    repository,
                    extraction_id,
                    span_id,
                    context="remediation",
                    entity_type="misconception",
                    entity_id=misconception.id,
                    record=False,
                    clock=clock,
                )
            except SpanViewError:
                continue
            passages.append({"role": role, "facet_id": facet_id, "span_view": view})
            break
    return repository.update_remediation_episode(
        episode_id, state="prescribed", passages_shown=passages, clock=clock
    ) or episode


def _rank_items(vault: LoadedVault, repository: Repository, misconception) -> list[Any]:
    target_facets = {
        vault.canonical_facet_id(facet)
        for facet in (misconception.target_facet, misconception.confused_with_facet)
        if facet
    }
    ranked = []
    for item in vault.practice_items.values():
        if item.learning_object_id != misconception.learning_object_id:
            continue
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        overlap = len(
            target_facets
            & {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
        )
        ranked.append((-overlap, state.last_attempt_at if state else "", item.id, item))
    return [entry[3] for entry in sorted(ranked)]


def start_remediation_treatment(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
) -> dict[str, Any]:
    episode = repository.remediation_episode(episode_id)
    if episode is None:
        raise RemediationError("remediation episode does not exist")
    misconception = repository.misconception(episode["case_ref"])
    if misconception is None:
        raise RemediationError("remediation case no longer exists")
    ranked = _rank_items(vault, repository, misconception)
    if not ranked:
        raise RemediationError("no practice item is available for this repair")
    primed = ranked[0]
    cold = ranked[1] if len(ranked) > 1 else ranked[0]
    updated = repository.update_remediation_episode(
        episode_id,
        state="treatment",
        primed_item_id=primed.id,
        cold_item_id=cold.id,
        clock=clock,
    )
    assert updated is not None
    return {"episode": updated, "primed_item_id": primed.id, "cold_item_id": cold.id}


def record_remediation_attempt(
    repository: Repository,
    attempt: dict[str, Any],
    *,
    clock: Clock | None = None,
) -> None:
    """Link treatment attempts and consume delayed tasks exactly once."""

    if attempt.get("primed"):
        episode = repository.open_remediation_episode_for_primed_item(
            str(attempt["practice_item_id"])
        )
        if episode is None:
            return
        created = parse_utc(attempt.get("created_at")) or (clock or SystemClock()).now()
        not_before = (created.astimezone(UTC) + timedelta(days=1)).replace(microsecond=0)
        expires = not_before + timedelta(days=30)
        repository.update_remediation_episode(
            episode["id"], state="cold_scheduled", primed_attempt_id=attempt["id"], clock=clock
        )
        repository.create_followup_task(
            kind="cold_retry",
            case_kind=episode["case_kind"],
            case_ref=episode["case_ref"],
            source_attempt_id=attempt["id"],
            remediation_episode_id=episode["id"],
            not_before=not_before.isoformat().replace("+00:00", "Z"),
            expires_at=expires.isoformat().replace("+00:00", "Z"),
            selected_item_id=episode.get("cold_item_id"),
            clock=clock,
        )
        return

    task = repository.active_followup_task_for_item(
        str(attempt["practice_item_id"]), at=str(attempt.get("created_at") or "")
    )
    if task is None or task.get("kind") != "cold_retry":
        return
    consumed = repository.consume_followup_task(task["id"], attempt["id"], clock=clock)
    if consumed is None or consumed.get("status") != "consumed":
        return
    episode_id = task.get("remediation_episode_id")
    if episode_id:
        completed_at = str(attempt.get("created_at") or "")
        repository.update_remediation_episode(
            episode_id,
            state="completed",
            cold_attempt_id=attempt["id"],
            completed_at=completed_at,
            clock=clock,
        )


def misconception_status_history(repository: Repository, misconception_id: str) -> list[dict[str, Any]]:
    history = []
    for event in repository.misconception_transition_events(misconception_id):
        label = event["to_status"]
        if event.get("from_status") == "resolved" and event["to_status"] in {"active", "resolving"}:
            label = "returned"
        history.append(dict(event) | {"label": label})
    return history
