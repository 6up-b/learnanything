"""Delete an imported source and everything derived from it (§4.1).

The source library is append-only everywhere else in the pipeline: an import
registers an artifact/revision/extraction chain, and every later stage only adds
rows that point back at it. Removing a source is therefore the one operation
that has to reason about the whole graph at once, so it runs in two steps:

``plan_source_deletion`` reports the impact without touching anything — what
disappears, what it costs (study-map citations, collection memberships), and
what makes deletion unsafe right now (a worker still writing rows for it).
``delete_source`` performs it: the SQLite cascade
(:meth:`Repository.delete_source_artifact`), the collection memberships in
``sources/source_sets.yaml``, and the stored original bytes.

Deletion is never partial-on-error: the database cascade is one transaction, and
the vault-side cleanup runs only after it commits.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import canonical_source_raw_path
from learnloop.vault.writer import upsert_source_set


class SourceDeletionError(ValueError):
    """Deletion refused. ``code`` is the typed reason for the RPC layer."""

    def __init__(self, code: str, message: str, *, details: dict[str, Any] | None = None) -> None:
        self.code = code
        self.details = details or {}
        super().__init__(message)


@dataclass
class CollectionImpact:
    source_set_id: str
    title: str
    subject_id: str
    # True when this source is the collection's only member, so the collection
    # is left empty (kept, not deleted — an empty collection is the learner's to
    # remove, and silently deleting one would lose its brief and title).
    leaves_empty: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_set_id": self.source_set_id,
            "title": self.title,
            "subject_id": self.subject_id,
            "leaves_empty": self.leaves_empty,
        }


@dataclass
class SourceDeletionPlan:
    source_id: str
    title: str
    canonical_uri: str | None
    revision_count: int
    extraction_count: int
    unit_count: int
    block_count: int
    # Provenance links from study-map entities into this source. These are the
    # real cost of the delete: the entities survive, their citation does not.
    citation_count: int
    cited_entities: list[dict[str, str]] = field(default_factory=list)
    collections: list[CollectionImpact] = field(default_factory=list)
    annotation_count: int = 0
    # Non-empty means deletion is refused right now; each entry is human-facing.
    blockers: list[str] = field(default_factory=list)
    # True when the stored original bytes go too (no surviving revision of any
    # other source shares the asset hash).
    removes_stored_original: bool = False

    @property
    def deletable(self) -> bool:
        return not self.blockers

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "canonical_uri": self.canonical_uri,
            "revision_count": self.revision_count,
            "extraction_count": self.extraction_count,
            "unit_count": self.unit_count,
            "block_count": self.block_count,
            "citation_count": self.citation_count,
            "cited_entities": [dict(entity) for entity in self.cited_entities],
            "collections": [collection.as_dict() for collection in self.collections],
            "annotation_count": self.annotation_count,
            "blockers": list(self.blockers),
            "deletable": self.deletable,
            "removes_stored_original": self.removes_stored_original,
        }


@dataclass
class SourceDeletionResult:
    source_id: str
    title: str
    deleted_rows: dict[str, int]
    collections_updated: list[str]
    removed_original: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "title": self.title,
            "deleted_rows": dict(self.deleted_rows),
            "collections_updated": list(self.collections_updated),
            "removed_original": self.removed_original,
        }


# The entity_source_links relations that represent a real citation from applied
# study-map content. Everything else in that table is bookkeeping.
_CITED_ENTITY_LIMIT = 12


def _artifact_or_error(repo: Repository, source_id: str) -> dict[str, Any]:
    artifact = repo.get_source_artifact(source_id)
    if artifact is None:
        raise SourceDeletionError("source_not_found", f"Source '{source_id}' does not exist.")
    return artifact


def _display_title(artifact: dict[str, Any], revisions: list[dict[str, Any]]) -> str:
    """Same fallback chain the Source library uses, so the confirmation dialog
    names the source exactly as the row the learner clicked."""

    title = str(artifact.get("display_title") or "").strip()
    if title:
        return title
    for revision in reversed(revisions):
        original_uri = str(revision.get("original_uri") or "").strip()
        if original_uri:
            return original_uri
    return str(artifact.get("canonical_uri") or artifact["id"])


def _active_job_blockers(
    repo: Repository, *, canonical_uri: str | None, revision_ids: set[str], extraction_ids: set[str]
) -> list[str]:
    """Jobs still running against this source, matched on their payload.

    A payload references a source by URI (import), extraction id (inventory), or
    revision id (repair/append). Serializing it and looking for any of those ids
    catches every shape without teaching this module each job type's schema."""

    needles = {value for value in (canonical_uri, *revision_ids, *extraction_ids) if value}
    if not needles:
        return []
    blockers: list[str] = []
    for job in repo.active_ingest_jobs():
        payload = json.dumps(job.get("payload") or {})
        if any(needle in payload for needle in needles):
            blockers.append(
                f"ingest job {job['id']} ({job['job_type']}) is {job['status']} for this source — "
                "cancel or let it finish first"
            )
    return blockers


def _collections_for_source(vault, source_id: str) -> list[CollectionImpact]:
    impacts: list[CollectionImpact] = []
    for source_set in getattr(vault, "source_sets", []) or []:
        members = list(source_set.members)
        remaining = [member for member in members if member.source_id != source_id]
        if len(remaining) == len(members):
            continue
        impacts.append(
            CollectionImpact(
                source_set_id=source_set.id,
                title=source_set.title,
                subject_id=source_set.subject_id,
                leaves_empty=not remaining,
            )
        )
    return impacts


def _shared_asset_hashes(repo: Repository, source_id: str, revisions: list[dict[str, Any]]) -> set[str]:
    """Asset hashes of this source's revisions that another source also stores.

    The original-bytes store is content-addressed, so two artifacts importing the
    same file share one file on disk. Deleting it for one would blank the reader
    for the other."""

    hashes = {str(rev.get("asset_hash") or "") for rev in revisions if rev.get("asset_hash")}
    if not hashes:
        return set()
    shared: set[str] = set()
    for artifact in repo.all_source_artifacts():
        if artifact["id"] == source_id:
            continue
        for other in repo.source_revisions_for(artifact["id"]):
            digest = str(other.get("asset_hash") or "")
            if digest in hashes:
                shared.add(digest)
    return shared


def plan_source_deletion(vault, repo: Repository, source_id: str) -> SourceDeletionPlan:
    """Report what deleting ``source_id`` would remove, cost, and currently block."""

    artifact = _artifact_or_error(repo, source_id)
    revisions = repo.source_revisions_for(source_id)
    revision_ids = {str(revision["id"]) for revision in revisions}

    extraction_ids: set[str] = set()
    unit_count = 0
    block_count = 0
    for revision_id in revision_ids:
        for run in repo.extraction_runs_for_revision(revision_id):
            extraction_ids.add(str(run["id"]))
            counts = repo.document_ir_counts(run["id"])
            unit_count += int(counts.get("unit_count", 0))
            block_count += int(counts.get("block_count", 0))

    links = repo.entity_source_links_for_sources([source_id])
    cited: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for link in links:
        key = (str(link.get("entity_type") or ""), str(link.get("entity_id") or ""))
        if key in seen:
            continue
        seen.add(key)
        if len(cited) < _CITED_ENTITY_LIMIT:
            cited.append({"entity_type": key[0], "entity_id": key[1], "relation": str(link.get("relation") or "")})

    asset_hashes = {str(rev.get("asset_hash") or "") for rev in revisions if rev.get("asset_hash")}
    shared = _shared_asset_hashes(repo, source_id, revisions)

    return SourceDeletionPlan(
        source_id=source_id,
        title=_display_title(artifact, revisions),
        canonical_uri=artifact.get("canonical_uri"),
        revision_count=len(revisions),
        extraction_count=len(extraction_ids),
        unit_count=unit_count,
        block_count=block_count,
        citation_count=len(links),
        cited_entities=cited,
        collections=_collections_for_source(vault, source_id),
        annotation_count=len(repo.annotations_for_source(source_id)),
        blockers=_active_job_blockers(
            repo,
            canonical_uri=artifact.get("canonical_uri"),
            revision_ids=revision_ids,
            extraction_ids=extraction_ids,
        ),
        removes_stored_original=bool(asset_hashes - shared),
    )


def delete_source(
    vault,
    repo: Repository,
    source_id: str,
    *,
    vault_root: Path | None = None,
    clock: Clock | None = None,
) -> SourceDeletionResult:
    """Delete the source: SQLite cascade, collection membership, stored bytes.

    Raises :class:`SourceDeletionError` when the plan reports a blocker, so a
    caller that skipped the preview still cannot delete out from under a running
    worker."""

    plan = plan_source_deletion(vault, repo, source_id)
    if plan.blockers:
        raise SourceDeletionError(
            "source_delete_blocked",
            plan.blockers[0],
            details={"blockers": plan.blockers},
        )

    root = Path(vault_root) if vault_root is not None else Path(vault.root)
    revisions = repo.source_revisions_for(source_id)
    asset_hashes = {str(rev.get("asset_hash") or "") for rev in revisions if rev.get("asset_hash")}
    removable = asset_hashes - _shared_asset_hashes(repo, source_id, revisions)

    deleted_rows = repo.delete_source_artifact(source_id)

    # Vault-side cleanup runs only after the cascade commits: a collection that
    # still listed a deleted revision would fail its next build with a confusing
    # extraction_not_found instead of simply no longer containing the source.
    updated: list[str] = []
    for impact in plan.collections:
        source_set = next((s for s in vault.source_sets if s.id == impact.source_set_id), None)
        if source_set is None:
            continue
        members = [
            member.model_dump(mode="json")
            for member in source_set.members
            if member.source_id != source_id
        ]
        upsert_source_set(
            root,
            {
                "id": source_set.id,
                "subject_id": source_set.subject_id,
                "title": source_set.title,
                "members": members,
            },
            clock=clock,
        )
        updated.append(source_set.id)

    removed_original = False
    for digest in removable:
        path = canonical_source_raw_path(root, digest)
        try:
            path.unlink()
            removed_original = True
        except FileNotFoundError:
            continue
        except OSError:
            # The rows are already gone; a byte file we cannot unlink is orphaned
            # storage, not a failed delete. Report it as "not removed".
            continue

    return SourceDeletionResult(
        source_id=source_id,
        title=plan.title,
        deleted_rows=deleted_rows,
        collections_updated=updated,
        removed_original=removed_original,
    )
