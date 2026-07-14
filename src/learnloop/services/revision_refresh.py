"""Revision refresh (source-ingestion §10.4).

Adopting a new source revision:

1. import/extraction first produces a deterministic old/new block diff (M1's
   ``reanchor_spans``);
2. unchanged / re-anchored spans keep their links (status stays ``current``);
3. changed/removed spans mark affected links ``needs_reanchor`` / ``stale`` and
   flag the affected entities for reconciliation (content events);
4. append runs with ``change_kind=source_revision_changed`` and the span diff;
5. pinned membership advances to the new revision ONLY on explicit confirmation;
6. a partially refreshed source stays usable, with unresolved stale links visible.

Nothing here silently deletes knowledge or migrates evidence (§10.4/§12).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.reanchor import EXACT_HASH, reanchor_spans
from learnloop.services.source_outline import resolve_extraction_id
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.writer import upsert_source_set


@dataclass
class RefreshResult:
    source_id: str
    old_revision_id: str
    new_revision_id: str
    membership_advanced: bool
    unchanged_links: list[str] = field(default_factory=list)
    reanchored_links: list[str] = field(default_factory=list)
    stale_links: list[str] = field(default_factory=list)
    needs_reanchor_links: list[str] = field(default_factory=list)
    affected_entities: list[dict[str, str]] = field(default_factory=list)
    append_result: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "old_revision_id": self.old_revision_id,
            "new_revision_id": self.new_revision_id,
            "membership_advanced": self.membership_advanced,
            "unchanged_links": list(self.unchanged_links),
            "reanchored_links": list(self.reanchored_links),
            "stale_links": list(self.stale_links),
            "needs_reanchor_links": list(self.needs_reanchor_links),
            "affected_entities": list(self.affected_entities),
            "append_result": self.append_result,
        }


def _span_id_from_locator(link: dict[str, Any]) -> str | None:
    locator = str(link.get("locator") or "")
    from learnloop.ingest.locators import parse_block_span

    parsed = parse_block_span(locator)
    if parsed is not None:
        return parsed[1]
    if locator.startswith("span:"):
        return locator.split(":", 1)[1]  # malformed early-v2 compatibility
    return None


def refresh_revision(
    root: Path,
    source_set_id: str,
    *,
    source_id: str,
    old_revision_id: str,
    new_revision_id: str,
    client: Any = None,
    new_extraction_id: str | None = None,
    confirm: bool = False,
    run_append: bool = True,
    repository: Repository | None = None,
    clock: Clock | None = None,
) -> RefreshResult:
    """Adopt ``new_revision_id`` for ``source_id`` in ``source_set_id`` (§10.4)."""

    vault = load_vault(root)
    if repository is None:
        # Repository opens a fresh sqlite connection per call; nothing to close.
        repository = Repository(VaultPaths(vault.root, vault.config).sqlite_path)
    return _refresh(
        root, vault, repository, source_set_id, source_id, old_revision_id, new_revision_id,
        client=client, new_extraction_id=new_extraction_id, confirm=confirm,
        run_append=run_append, clock=clock,
    )


def _refresh(root, vault, repository, source_set_id, source_id, old_revision_id, new_revision_id,
             *, client, new_extraction_id, confirm, run_append, clock):
    old_extraction = resolve_extraction_id(repository, old_revision_id)
    new_extraction = new_extraction_id or resolve_extraction_id(repository, new_revision_id)
    result = RefreshResult(
        source_id=source_id, old_revision_id=old_revision_id, new_revision_id=new_revision_id,
        membership_advanced=False,
    )

    old_ir = repository.load_document_ir(old_extraction) if old_extraction else None
    new_ir = repository.load_document_ir(new_extraction) if new_extraction else None
    # An EXACT content-hash re-anchor is safe (§2.4): the normalized text is
    # unchanged, so the link stays current. A geometry/fallback re-anchor means the
    # CONTENT changed at a stable position — the link is kept but flagged
    # needs_reanchor for reconciliation. A span with no match at all is stale/removed.
    exact_aliases: set[str] = set()
    geometry_aliases: set[str] = set()
    needs_reanchor: set[str] = set()
    if old_ir is not None and new_ir is not None:
        reanchor = reanchor_spans(old_ir, new_ir)
        for alias in reanchor.aliases:
            (exact_aliases if alias.match_kind == EXACT_HASH else geometry_aliases).add(alias.from_span_id)
        needs_reanchor = set(reanchor.needs_reanchor)

    now = utc_now_iso(clock)
    affected: dict[tuple[str, str], None] = {}
    for link in repository.entity_source_links_for_revision(old_revision_id):
        span_id = _span_id_from_locator(link)
        if span_id is None:
            # non-span locator: conservatively keep current (legacy locators resolve
            # forever per §13) — no staleness inference without a span.
            result.unchanged_links.append(link["id"])
            continue
        if span_id in exact_aliases:
            result.unchanged_links.append(link["id"])
            continue
        # changed (geometry re-anchor) or removed (no match): flag for reconciliation.
        status = "needs_reanchor" if span_id in geometry_aliases or span_id in needs_reanchor else "stale"
        repository.mark_entity_source_link_status(link["id"], status=status, clock=clock)
        (result.needs_reanchor_links if status == "needs_reanchor" else result.stale_links).append(link["id"])
        affected[(link["entity_type"], link["entity_id"])] = None
        _record_span_change_event(repository, link, status, now)

    result.affected_entities = [{"entity_type": et, "entity_id": eid} for (et, eid) in affected]

    # Pinned membership advances ONLY on explicit confirmation (§10.4/§14).
    if confirm:
        _advance_membership(root, vault, source_set_id, source_id, old_revision_id, new_revision_id, clock)
        result.membership_advanced = True

    # Append runs with change_kind=source_revision_changed over the new revision.
    if run_append and confirm and client is not None:
        from learnloop.services.source_append import append_source

        append = append_source(
            root, source_set_id, client=client, new_revision_ids=[new_revision_id],
            change_kind="source_revision_changed",
            revision_diff={
                "old_revision_id": old_revision_id, "new_revision_id": new_revision_id,
                "reanchored": result.reanchored_links, "stale": result.stale_links,
                "needs_reanchor": result.needs_reanchor_links,
            },
            repository=repository, clock=clock,
        )
        result.append_result = append.as_dict()
    return result


def _record_span_change_event(repository, link, status, now) -> None:
    event_type = "source_span_removed" if status == "stale" else "source_span_changed"
    repository.record_content_events(
        [
            {
                "id": new_ulid(),
                "event_type": event_type,
                "subject": None,
                "entity_type": link["entity_type"] if link["entity_type"] in _EVENTABLE else "learning_object",
                "entity_id": link["entity_id"],
                "origin": "system",
                "review_status": None,
                "summary": f"span {link.get('locator')} {status} after revision change",
                "created_at": now,
            }
        ]
    )


_EVENTABLE = frozenset(
    {"learning_object", "practice_item", "concept", "concept_edge", "rubric", "error_type",
     "facet", "task_blueprint", "provenance_link", "notation_mapping", "source_conflict"}
)


def _advance_membership(root, vault, source_set_id, source_id, old_revision_id, new_revision_id, clock) -> None:
    source_set = next((s for s in vault.source_sets if s.id == source_set_id), None)
    if source_set is None:
        return
    members: list[dict[str, Any]] = []
    for member in source_set.members:
        revision_id = new_revision_id if (member.source_id == source_id and member.revision_id == old_revision_id) else member.revision_id
        members.append(
            {
                "source_id": member.source_id,
                "revision_id": revision_id,
                "default_role": member.default_role,
                "scope": [{"unit_id": s.unit_id, **({"role_override": s.role_override} if s.role_override else {})} for s in member.scope],
                "priority": member.priority,
            }
        )
    upsert_source_set(
        root,
        {"id": source_set.id, "subject_id": source_set.subject_id, "title": source_set.title, "members": members},
        clock=clock,
    )
