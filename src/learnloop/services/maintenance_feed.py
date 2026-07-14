"""Maintenance feed (source-ingestion §11).

The core release ships the maintenance feed required to operate append safely. It
is generated DETERMINISTICALLY from existing tables — no LLM. Every notice:

- has ONE concrete action link,
- can be dismissed/snoozed WITHOUT changing source or curriculum state,
- declares an AGING POLICY per notice TYPE so the feed stays bounded and
  trustworthy instead of accumulating into review debt:
    * ``auto_resolution`` — clears automatically when the underlying condition
      clears (regeneration drops the notice);
    * ``auto_expiry`` — a purely-informational notice expires if unacted after a
      regeneration cycle no longer sees it;
    * ``escalation`` — severity rises after N snoozes so it cannot be buried.

``generate_maintenance_feed`` is idempotent: it upserts current notices on their
``(notice_type, dedup_key)`` and auto-resolves live notices whose condition no
longer holds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

ESCALATION_SNOOZE_THRESHOLD = 3


@dataclass(frozen=True)
class NoticeType:
    key: str
    aging_policy: str  # auto_resolution | auto_expiry | escalation
    default_severity: str


# The §11 notice catalogue with declared aging policies.
NOTICE_TYPES: dict[str, NoticeType] = {
    "update_available": NoticeType("update_available", "auto_resolution", "info"),
    "stale_links": NoticeType("stale_links", "auto_resolution", "warning"),
    "needs_reanchor_links": NoticeType("needs_reanchor_links", "auto_resolution", "warning"),
    "unit_needs_reinventory": NoticeType("unit_needs_reinventory", "auto_resolution", "warning"),
    "append_partially_complete": NoticeType("append_partially_complete", "escalation", "action_needed"),
    "open_conflict": NoticeType("open_conflict", "auto_resolution", "action_needed"),
    "missing_prerequisite_coverage": NoticeType("missing_prerequisite_coverage", "auto_expiry", "info"),
    "task_family_without_teaching": NoticeType("task_family_without_teaching", "auto_expiry", "info"),
    "taught_blueprint_without_assessment": NoticeType("taught_blueprint_without_assessment", "auto_expiry", "info"),
    "token_estimate_exceeded": NoticeType("token_estimate_exceeded", "auto_expiry", "info"),
    "lo_without_practice": NoticeType("lo_without_practice", "escalation", "warning"),
}


@dataclass
class _Notice:
    notice_type: str
    dedup_key: str
    title: str
    action: dict[str, Any]
    subject_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    detail: Any = None


def generate_maintenance_feed(
    vault: LoadedVault,
    repository: Repository,
    *,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Regenerate the feed deterministically; return the live notices (§11)."""

    notices = _collect(vault, repository)
    seen_keys = {(n.notice_type, n.dedup_key) for n in notices}

    for notice in notices:
        spec = NOTICE_TYPES[notice.notice_type]
        repository.upsert_maintenance_notice(
            notice_type=notice.notice_type,
            dedup_key=notice.dedup_key,
            title=notice.title,
            action=notice.action,
            aging_policy=spec.aging_policy,
            severity=spec.default_severity,
            subject_id=notice.subject_id,
            entity_type=notice.entity_type,
            entity_id=notice.entity_id,
            detail=notice.detail,
            clock=clock,
        )

    # Aging: auto-resolution / auto-expiry clear a live notice whose condition no
    # longer holds; escalation raises severity after N snoozes.
    for live in repository.maintenance_notices(include_hidden=True):
        key = (live["notice_type"], live["dedup_key"])
        spec = NOTICE_TYPES.get(live["notice_type"])
        if spec is None:
            continue
        if live["status"] in {"dismissed"}:
            continue
        if key not in seen_keys and live["status"] in {"active", "snoozed"}:
            if spec.aging_policy in {"auto_resolution", "auto_expiry"}:
                new_status = "resolved" if spec.aging_policy == "auto_resolution" else "expired"
                repository.set_maintenance_notice_status(live["id"], status=new_status, clock=clock)
        elif spec.aging_policy == "escalation" and live["snooze_count"] >= ESCALATION_SNOOZE_THRESHOLD:
            if live["severity"] != "action_needed":
                repository.upsert_maintenance_notice(
                    notice_type=live["notice_type"], dedup_key=live["dedup_key"],
                    title=live["title"], action=live["action"], aging_policy=spec.aging_policy,
                    severity="action_needed", subject_id=live.get("subject_id"),
                    entity_type=live.get("entity_type"), entity_id=live.get("entity_id"),
                    detail=live.get("detail"), clock=clock,
                )

    return repository.maintenance_notices()


# --- deterministic condition collectors -------------------------------------


def _collect(vault: LoadedVault, repository: Repository) -> list[_Notice]:
    notices: list[_Notice] = []
    for collector in _COLLECTORS:
        notices.extend(collector(vault, repository))
    return notices


def _stale_link_notices(vault, repository) -> list[_Notice]:
    stale = repository.stale_entity_source_links(("stale",))
    needs = repository.stale_entity_source_links(("needs_reanchor",))
    out: list[_Notice] = []
    if stale:
        out.append(
            _Notice(
                notice_type="stale_links", dedup_key="all",
                title=f"{len(stale)} source link(s) went stale after a revision change",
                action={"action": "review_stale_links", "label": "Review stale links"},
                detail={"count": len(stale), "link_ids": [l["id"] for l in stale][:50]},
            )
        )
    if needs:
        out.append(
            _Notice(
                notice_type="needs_reanchor_links", dedup_key="all",
                title=f"{len(needs)} source link(s) need re-anchoring",
                action={"action": "reanchor_links", "label": "Re-anchor links"},
                detail={"count": len(needs), "link_ids": [l["id"] for l in needs][:50]},
            )
        )
    return out


def _open_conflict_notices(vault, repository) -> list[_Notice]:
    out: list[_Notice] = []
    for conflict in repository.source_conflicts_by_status("open"):
        out.append(
            _Notice(
                notice_type="open_conflict", dedup_key=conflict["id"],
                title=f"Open conflict on {conflict['entity_type']} {conflict['entity_id']}",
                subject_id=conflict.get("subject_id"),
                entity_type=conflict["entity_type"], entity_id=conflict["entity_id"],
                action={"action": "resolve_conflict", "label": "Resolve conflict", "conflict_id": conflict["id"]},
                detail={"statement": conflict["statement"]},
            )
        )
    return out


def _partial_append_notices(vault, repository) -> list[_Notice]:
    out: list[_Notice] = []
    for intent in repository.pending_apply_intents():
        out.append(
            _Notice(
                notice_type="append_partially_complete", dedup_key=intent["id"],
                title="An append/apply is partially complete and awaiting recovery",
                action={"action": "recover_apply_intents", "label": "Complete pending apply"},
                detail={"intent_id": intent["id"]},
            )
        )
    return out


def _lo_without_practice_notices(vault, repository) -> list[_Notice]:
    have_practice: set[str] = set()
    for pi in vault.practice_items.values():
        if pi.learning_object_id:
            have_practice.add(pi.learning_object_id)
    out: list[_Notice] = []
    for lo_id, lo in sorted(vault.learning_objects.items()):
        if getattr(lo, "status", "active") == "dormant":
            continue
        if lo_id not in have_practice:
            subject = lo.subjects[0] if lo.subjects else None
            out.append(
                _Notice(
                    notice_type="lo_without_practice", dedup_key=lo_id,
                    title=f"Learning object '{lo.title}' has no practice material",
                    subject_id=subject, entity_type="learning_object", entity_id=lo_id,
                    action={"action": "generate_practice", "label": "Generate practice", "learning_object_id": lo_id},
                )
            )
    return out


def _taught_blueprint_without_assessment_notices(vault, repository) -> list[_Notice]:
    """A taught blueprint with no assessment_alignment provenance (§11)."""

    out: list[_Notice] = []
    for lo in vault.learning_objects.values():
        for bp in lo.blueprints or []:
            links = repository.entity_source_links("task_blueprint", bp.id)
            if not any(l["relation"] == "assessment_alignment" for l in links):
                out.append(
                    _Notice(
                        notice_type="taught_blueprint_without_assessment", dedup_key=bp.id,
                        title=f"Blueprint {bp.id} has no representative assessment",
                        entity_type="task_blueprint", entity_id=bp.id,
                        action={"action": "align_assessment", "label": "Add assessment source", "blueprint_id": bp.id},
                    )
                )
    return out


_COLLECTORS: tuple[Callable[[LoadedVault, Repository], list[_Notice]], ...] = (
    _stale_link_notices,
    _open_conflict_notices,
    _partial_append_notices,
    _lo_without_practice_notices,
    _taught_blueprint_without_assessment_notices,
)


# --- user actions (dismiss / snooze; never change source/curriculum state) --


def dismiss_notice(repository: Repository, notice_id: str, *, clock: Clock | None = None) -> None:
    repository.set_maintenance_notice_status(notice_id, status="dismissed", clock=clock)


def snooze_notice(
    repository: Repository, notice_id: str, *, until: str | None = None, clock: Clock | None = None
) -> dict[str, Any] | None:
    """Snooze a notice; escalation-policy notices raise severity after N snoozes."""

    repository.set_maintenance_notice_status(
        notice_id, status="snoozed", snoozed_until=until, bump_snooze=True, clock=clock
    )
    notice = repository.maintenance_notice(notice_id)
    if notice is None:
        return None
    spec = NOTICE_TYPES.get(notice["notice_type"])
    if spec and spec.aging_policy == "escalation" and notice["snooze_count"] >= ESCALATION_SNOOZE_THRESHOLD:
        repository.upsert_maintenance_notice(
            notice_type=notice["notice_type"], dedup_key=notice["dedup_key"],
            title=notice["title"], action=notice["action"], aging_policy=spec.aging_policy,
            severity="action_needed", subject_id=notice.get("subject_id"),
            entity_type=notice.get("entity_type"), entity_id=notice.get("entity_id"),
            detail=notice.get("detail"), clock=clock,
        )
        repository.set_maintenance_notice_status(
            notice_id, status="snoozed", snoozed_until=until, bump_snooze=False, clock=clock
        )
    return repository.maintenance_notice(notice_id)
