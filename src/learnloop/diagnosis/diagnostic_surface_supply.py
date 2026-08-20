"""Replenish diagnostic-probe surface supply after consumption.

Owner design intent: a probe must be an entirely fresh, never-before-seen
problem, so a vault-authored ``practice_mode: diagnostic_probe`` item is a
single-use surface — its one administration consumes it (attempt recording
deactivates the item; the scheduler refuses administered probes defensively).
Consumption therefore leaves a hole nothing used to fill: the learning object
has one fewer fresh diagnostic surface for its facets/misconception pairs.

This module is the reconciliation seam. It DERIVES needs from attempts + item
state rather than hooking attempt recording, for two reasons:

* replay safety — ``rebuild-derived-state`` replays attempts into
  ``practice_item_states``; a sweep over that derived state reproduces the
  same needs regardless of ordering, and the table's UNIQUE key on the
  consumed item id makes re-running a no-op;
* ownership — attempt recording is a shared compute path; a sweep called from
  the scheduler build (the next thing that always runs after an attempt) needs
  no coordination with it.

The needs land in ``diagnostic_surface_generation_needs`` (migration 147),
following the ``probe_generation_needs`` / ``synthesis_generation_needs``
status lifecycle (``pending`` → ``resolved``/``declined``). The sweep also
self-heals: a pending need whose learning object has since gained a fresh
(never-administered, active) diagnostic surface covering the same facet
signature is resolved, so the queue of needs always reflects the actual gap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault, PracticeItem, discriminates

#: Capability string stamped on every replenishment need. One value, so the
#: consumer (diagnostic proposal generation) can select this need class.
DIAGNOSTIC_SURFACE_CAPABILITY = "diagnostic_probe_surface"

#: Maintenance-notice type raised when the eligible pool behind an open probe
#: episode or a pending diagnostic replenishment need is EMPTY. Registered in
#: ``maintenance_feed.NOTICE_TYPES`` (aging ``auto_resolution``, severity
#: ``action_needed``) and swept from ``reconcile_empty_probe_pools`` so the
#: notice exists the moment the pool empties, not only when the feed
#: regenerates. One open notice per learning object (``dedup_key`` = LO id).
PROBE_POOL_EMPTY_NOTICE_TYPE = "probe_pool_empty"

#: Why the pool is empty. The two arms the owner asked to keep apart:
#: ``excluded_as_seen`` — surfaces exist but every one has already carried an
#: administration (the lifetime never-before-seen gate excludes them all);
#: ``never_existed`` — the learning object has no probe-capable surface at all.
EMPTY_POOL_REASONS = ("excluded_as_seen", "never_existed")


def _facet_target_key(item: PracticeItem) -> str:
    facets = sorted(str(facet) for facet in item.evidence_facets)
    return "|".join(facets) if facets else f"item:{item.id}"


def _misconception_ids(vault: LoadedVault, item: PracticeItem) -> list[str]:
    rubric = vault.rubric_for_item(item)
    return sorted(discriminates(item, rubric))


def reconcile_diagnostic_surface_needs(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> dict[str, list[str]]:
    """Enqueue needs for consumed diagnostic surfaces; resolve satisfied ones.

    Idempotent: needs are a pure function of (vault items, derived item state,
    existing needs), deduplicated by the consumed item id. Returns the need ids
    it touched, keyed by action (``enqueued`` includes pre-existing dedup hits).
    """

    item_states = repository.practice_item_states()

    consumed: list[PracticeItem] = []
    fresh_target_keys_by_lo: dict[str, set[str]] = {}
    for item in vault.practice_items.values():
        if item.practice_mode != "diagnostic_probe":
            continue
        state = item_states.get(item.id)
        administered = state is not None and state.last_attempt_at is not None
        if administered:
            if item.status == "active":
                consumed.append(item)
            continue
        active = item.status == "active" and (state is None or state.active)
        if active:
            fresh_target_keys_by_lo.setdefault(item.learning_object_id, set()).add(
                _facet_target_key(item)
            )

    enqueued: list[str] = []
    for item in sorted(consumed, key=lambda entry: entry.id):
        enqueued.append(
            repository.upsert_diagnostic_surface_generation_need(
                learning_object_id=item.learning_object_id,
                consumed_practice_item_id=item.id,
                target_key=_facet_target_key(item),
                missing_capability=DIAGNOSTIC_SURFACE_CAPABILITY,
                facet_ids=sorted(str(facet) for facet in item.evidence_facets),
                misconception_ids=_misconception_ids(vault, item),
                clock=clock,
            )
        )

    resolved: list[str] = []
    for need in repository.diagnostic_surface_generation_needs(status="pending"):
        fresh_keys = fresh_target_keys_by_lo.get(str(need["learning_object_id"]), set())
        if str(need["target_key"]) in fresh_keys:
            repository.resolve_diagnostic_surface_generation_need(
                str(need["id"]), clock=clock
            )
            resolved.append(str(need["id"]))

    return {"enqueued": enqueued, "resolved": resolved}


# --- Empty-pool detection + urgent notice (owner decision) --------------------------
#
# The lifetime never-before-seen gate (`administered_surface_exclusions`) can
# leave an open probe episode with NOTHING to serve on a small vault, and a
# pending replenishment need with nothing to point at. Neither may be silent:
# when the eligible pool is empty the system (1) queues generation through the
# existing needs→commissioning path when an AI provider is routed for the
# authoring workflow, and (2) always raises one deduplicated, urgent
# maintenance notice per learning object, self-resolving when a fresh surface
# appears (mirroring the need sweep above).


@dataclass(frozen=True)
class EmptyPoolCondition:
    """One learning object whose diagnostic surface pool is currently empty."""

    learning_object_id: str
    #: One of :data:`EMPTY_POOL_REASONS`.
    reason: str
    #: The open probe episode starved by the empty pool, when there is one.
    episode_id: str | None = None
    episode_status: str | None = None
    #: Pending ``diagnostic_surface_generation_needs`` ids for the LO.
    pending_need_ids: tuple[str, ...] = ()
    #: Probe-capable surfaces that exist for the LO (any administration state).
    total_surfaces: int = 0
    #: ...of which the learner has never seen (id nor surface group).
    fresh_surfaces: int = 0


def probe_pool_empty_conditions(
    vault: LoadedVault, repository: Repository
) -> list[EmptyPoolCondition]:
    """Learning objects whose eligible diagnostic pool is empty right now.

    Derived, not recorded: a pure function of (vault items, derived item state,
    attempt history, open episodes, pending needs), so the sweep and the
    maintenance feed regenerate identical conditions and the notice
    self-resolves the moment a fresh surface appears.

    A condition exists when:

    * an OPEN probe episode's LO has zero fresh probe-capable surfaces — the
      never-before-seen gate leaves ``eligible_instruments`` nothing to admit
      (a ``pending_items`` episode whose LO still has fresh surfaces is NOT a
      condition: that is the ordinary §10 missing-instrument-binding state,
      already parked with its own generation need); or
    * a pending diagnostic replenishment need's LO has zero fresh active
      ``diagnostic_probe`` surfaces — the need has nothing to resolve against.

    ``reason`` separates 'every surface was already administered'
    (``excluded_as_seen``) from 'no surface was ever authored'
    (``never_existed``) because the remedies differ: the first needs fresh
    generation, the second may also need family/card authoring.
    """

    from learnloop.substrate.canonical_projection import surface_group_id
    from learnloop.substrate.instrument_serving import unservable_reason
    from learnloop.diagnosis.probe_episodes import administered_surface_exclusions

    item_states = repository.practice_item_states()
    attempted_ids, attempted_surfaces = administered_surface_exclusions(vault, repository)

    total_by_lo: dict[str, int] = {}
    fresh_by_lo: dict[str, int] = {}
    diag_total_by_lo: dict[str, int] = {}
    diag_fresh_by_lo: dict[str, int] = {}
    for item in vault.practice_items.values():
        if item.status != "active":
            continue
        if item.practice_mode == "diagnostic_microprobe":
            continue
        if unservable_reason(item) is not None:
            continue
        lo_id = item.learning_object_id
        total_by_lo[lo_id] = total_by_lo.get(lo_id, 0) + 1
        is_diag = item.practice_mode == "diagnostic_probe"
        if is_diag:
            diag_total_by_lo[lo_id] = diag_total_by_lo.get(lo_id, 0) + 1
        state = item_states.get(item.id)
        if state is not None and not state.active:
            continue
        fresh = (
            item.id not in attempted_ids
            and surface_group_id(item) not in attempted_surfaces
        )
        if fresh:
            fresh_by_lo[lo_id] = fresh_by_lo.get(lo_id, 0) + 1
            if is_diag:
                diag_fresh_by_lo[lo_id] = diag_fresh_by_lo.get(lo_id, 0) + 1

    pending_needs_by_lo: dict[str, list[str]] = {}
    for need in repository.diagnostic_surface_generation_needs(status="pending"):
        pending_needs_by_lo.setdefault(str(need["learning_object_id"]), []).append(
            str(need["id"])
        )

    conditions: dict[str, EmptyPoolCondition] = {}

    for lo_id, episode in sorted(repository.open_probe_episodes().items()):
        if lo_id not in vault.learning_objects:
            continue
        if fresh_by_lo.get(lo_id, 0) > 0:
            continue
        reason = "excluded_as_seen" if total_by_lo.get(lo_id, 0) > 0 else "never_existed"
        conditions[lo_id] = EmptyPoolCondition(
            learning_object_id=lo_id,
            reason=reason,
            episode_id=episode.id,
            episode_status=episode.status,
            pending_need_ids=tuple(pending_needs_by_lo.get(lo_id, [])),
            total_surfaces=total_by_lo.get(lo_id, 0),
            fresh_surfaces=0,
        )

    for lo_id, need_ids in sorted(pending_needs_by_lo.items()):
        if lo_id in conditions or lo_id not in vault.learning_objects:
            continue
        if diag_fresh_by_lo.get(lo_id, 0) > 0:
            continue
        reason = (
            "excluded_as_seen" if diag_total_by_lo.get(lo_id, 0) > 0 else "never_existed"
        )
        conditions[lo_id] = EmptyPoolCondition(
            learning_object_id=lo_id,
            reason=reason,
            pending_need_ids=tuple(need_ids),
            total_surfaces=total_by_lo.get(lo_id, 0),
            fresh_surfaces=fresh_by_lo.get(lo_id, 0),
        )

    return [conditions[lo_id] for lo_id in sorted(conditions)]


def probe_pool_empty_notice_payload(
    vault: LoadedVault, condition: EmptyPoolCondition
) -> dict[str, Any]:
    """The one notice shape both writers use (sweep upsert + feed collector).

    Single-sourced so the two paths cannot drift into flapping (`upsert` is
    idempotent on ``(notice_type, dedup_key)``; a differing title would still
    churn the row on every writer alternation).
    """

    learning_object = vault.learning_objects.get(condition.learning_object_id)
    title_name = (
        learning_object.title if learning_object is not None else condition.learning_object_id
    )
    reason_text = (
        "every surface was already administered"
        if condition.reason == "excluded_as_seen"
        else "no probe-capable surface exists"
    )
    return {
        "notice_type": PROBE_POOL_EMPTY_NOTICE_TYPE,
        "dedup_key": condition.learning_object_id,
        "title": f"Probe pool empty for '{title_name}' — {reason_text}",
        "subject_id": (
            learning_object.subjects[0]
            if learning_object is not None and learning_object.subjects
            else None
        ),
        "entity_type": "learning_object",
        "entity_id": condition.learning_object_id,
        "action": {
            "action": "generate_diagnostic_surfaces",
            "label": "Generate fresh diagnostic surfaces",
            "learning_object_id": condition.learning_object_id,
        },
        "detail": {
            "reason": condition.reason,
            "probe_episode_id": condition.episode_id,
            "probe_episode_status": condition.episode_status,
            "pending_diagnostic_need_ids": list(condition.pending_need_ids),
            "total_surfaces": condition.total_surfaces,
            "fresh_surfaces": condition.fresh_surfaces,
        },
    }


def authoring_provider_available(vault: LoadedVault) -> str | None:
    """The routed authoring provider when its runtime is ready, else None.

    Respects ``[ai.routing]`` (workflow ``authoring``) and the vault's provider
    profiles; the readiness check is config/filesystem only (no network), the
    same check ``doctor`` and the ingest runner use. AI stays optional: with no
    ready provider the empty-pool sweep still raises the notice and skips
    queueing.
    """

    from learnloop.ai.routing import ready_client_for_task

    try:
        resolved = ready_client_for_task(vault.root, vault.config, "authoring")
    except Exception:  # pragma: no cover - a broken runtime probe means "not ready"
        return None
    return resolved.provider_name if resolved.ready else None


def reconcile_empty_probe_pools(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
    provider_available: bool | None = None,
    ai_client: object | None = None,
) -> dict[str, Any]:
    """Detect empty pools; queue generation (provider-gated); raise/clear notices.

    Runs from the scheduler build right after
    :func:`reconcile_diagnostic_surface_needs`. Idempotent: notices upsert on
    ``(notice_type, learning_object_id)``, generation needs dedup on
    ``(episode, target_key)``, and a condition that has cleared resolves its
    notice on the next sweep (the maintenance feed's ``auto_resolution`` aging
    does the same through the registered collector).

    ``provider_available`` overrides runtime detection (tests); ``ai_client``
    optionally lets a caller that already holds a provider client mint a fresh
    single-use surface immediately (see
    ``probe_instance_generation.mint_single_use_probe_surface``) instead of
    only queueing the need.
    """

    conditions = probe_pool_empty_conditions(vault, repository)
    if provider_available is None:
        provider_available = (
            bool(conditions) and authoring_provider_available(vault) is not None
        )

    queued_need_ids: list[str] = []
    minted_item_ids: list[str] = []
    notice_ids: list[str] = []
    for condition in conditions:
        auto_queued_need_id: str | None = None
        if provider_available and condition.episode_id is not None:
            auto_queued_need_id = _queue_episode_generation_need(
                vault, repository, condition.episode_id, clock=clock
            )
            if auto_queued_need_id is not None:
                queued_need_ids.append(auto_queued_need_id)
            if ai_client is not None:
                from learnloop.diagnosis.probe_instance_generation import (
                    mint_single_use_probe_surface,
                )

                minted = mint_single_use_probe_surface(
                    repository,
                    vault,
                    condition.episode_id,
                    ai_client=ai_client,
                    clock=clock,
                )
                if minted is not None:
                    minted_item_ids.append(minted.practice_item_id)
        payload = probe_pool_empty_notice_payload(vault, condition)
        payload["detail"]["provider_available"] = bool(provider_available)
        payload["detail"]["auto_queued_need_id"] = auto_queued_need_id
        notice_ids.append(
            repository.upsert_maintenance_notice(
                notice_type=payload["notice_type"],
                dedup_key=payload["dedup_key"],
                title=payload["title"],
                action=payload["action"],
                aging_policy="auto_resolution",
                severity="action_needed",
                subject_id=payload["subject_id"],
                entity_type=payload["entity_type"],
                entity_id=payload["entity_id"],
                detail=payload["detail"],
                clock=clock,
            )
        )

    # Self-resolution: a live empty-pool notice whose LO regained a fresh
    # surface (or closed its episode/needs) clears here, mirroring the need
    # sweep — the feed's auto_resolution aging is the second, slower path.
    live_los = {condition.learning_object_id for condition in conditions}
    resolved_notice_ids: list[str] = []
    for notice in repository.maintenance_notices(include_hidden=True):
        if notice["notice_type"] != PROBE_POOL_EMPTY_NOTICE_TYPE:
            continue
        if notice["status"] not in ("active", "snoozed"):
            continue
        if notice["dedup_key"] in live_los:
            continue
        repository.set_maintenance_notice_status(
            notice["id"], status="resolved", clock=clock
        )
        resolved_notice_ids.append(str(notice["id"]))

    return {
        "conditions": conditions,
        "notice_ids": notice_ids,
        "resolved_notice_ids": resolved_notice_ids,
        "queued_need_ids": queued_need_ids,
        "minted_item_ids": minted_item_ids,
        "provider_available": bool(provider_available),
    }


def _queue_episode_generation_need(
    vault: LoadedVault,
    repository: Repository,
    episode_id: str,
    *,
    clock: Clock | None = None,
) -> str | None:
    """Ensure the starved episode has one pending generation need.

    Reuses the exact §10 needs→commissioning path (``probe_generation_needs``
    consumed and resolved by ``generate_instances_for_episode``); the upsert is
    deduplicated per (episode, target_key), so re-sweeping never multiplies
    queue entries. Returns the pending need id, or None when the episode has no
    locked hypothesis set to derive a target from.
    """

    from learnloop.diagnosis.probe_episodes import (
        _record_generation_need,
        episode_hypothesis_set,
    )

    episode = repository.probe_episode(episode_id)
    if episode is None or episode.status not in ("pending_items", "in_progress"):
        return None
    hypothesis_set = episode_hypothesis_set(repository, episode)
    if hypothesis_set is None:
        return None
    _record_generation_need(vault, repository, episode, hypothesis_set, clock=clock)
    pending = repository.probe_generation_needs(
        probe_episode_id=episode.id, status="pending"
    )
    return str(pending[-1].id) if pending else None
