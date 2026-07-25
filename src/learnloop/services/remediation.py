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


class RemediationBlocked(RemediationError):
    """A repair that the causal state holds back, with its typed status.

    Carries the full :class:`~learnloop.services.causal_orchestrator.RepairStatus`
    so a caller can render the §6 learner copy and actions instead of a bare
    string. ``str(exc)`` is the learner-facing message.
    """

    def __init__(self, status: Any) -> None:
        super().__init__(status.message)
        self.repair_status = status

    @property
    def status(self) -> str:
        return str(self.repair_status.status)


def start_remediation_episode(
    repository: Repository,
    misconception_id: str,
    *,
    vault: LoadedVault | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Start the repair episode, or raise the typed causal hold.

    Thin adapter over ``causal_orchestrator.causal_repair_status`` (§6): the
    orchestrator owns the decision, records the probe-decision receipt, and
    creates the episode when the causal state permits it. Callers that want the
    learner offer (message + "Take the quick check" / "Teach me now" /
    "Not now") should call ``causal_repair_status`` directly.
    """

    from learnloop.services.causal_orchestrator import (
        CausalRepairError,
        causal_repair_status,
    )

    try:
        status = causal_repair_status(
            vault,
            repository,
            misconception_id=misconception_id,
            session_id=session_id,
            clock=clock,
        )
    except CausalRepairError as exc:
        raise RemediationError(str(exc)) from exc
    if status.episode is None:
        raise RemediationBlocked(status)
    return status.episode


def _episode_case(repository: Repository, episode: dict[str, Any]) -> Any | None:
    if episode.get("case_kind") == "misconception":
        return repository.misconception(str(episode["case_ref"]))
    return repository.misconception_candidate_by_id(str(episode["case_ref"]))


def _case_value(case: Any, key: str, default: Any = None) -> Any:
    if isinstance(case, dict):
        return case.get(key, default)
    return getattr(case, key, default)


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
    misconception = _episode_case(repository, episode)
    if misconception is None:
        raise RemediationError("remediation case no longer exists")

    passages: list[dict[str, Any]] = []
    for role, facet_id in (
        ("target", _case_value(misconception, "target_facet")),
        ("confused_with", _case_value(misconception, "confused_with_facet")),
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
                    entity_id=str(_case_value(misconception, "id", episode["case_ref"])),
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
        for facet in (
            _case_value(misconception, "target_facet"),
            _case_value(misconception, "confused_with_facet"),
        )
        if facet
    }
    ranked = []
    for item in vault.practice_items.values():
        if item.learning_object_id != _case_value(misconception, "learning_object_id"):
            continue
        state = repository.practice_item_state(item.id)
        if state is not None and not state.active:
            continue
        overlap = len(
            target_facets
            & {vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets}
        )
        # A seeded-but-never-attempted item has a state row whose
        # `last_attempt_at` is NULL; comparing that against another item's
        # timestamp raised TypeError and crashed the whole prescription. Treat
        # "never attempted" as the earliest possible time, which is also the
        # ordering this rank wants (least recently practiced first).
        last_attempt_at = (state.last_attempt_at or "") if state else ""
        ranked.append((-overlap, last_attempt_at, item.id, item))
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
    misconception = _episode_case(repository, episode)
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
        # §6.2: resolve the cold-verification inputs NOW and carry them on the
        # task. When the retry lands days later, the factor may have closed and
        # the receipt may be stale; reconstructing them then is exactly the
        # "future caller" assumption that left this channel unwired.
        from learnloop.services.causal_orchestrator import cold_verification_context

        context = cold_verification_context(
            None, repository, episode=episode, source_attempt=attempt
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
            context=context,
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
