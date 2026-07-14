"""Vault-level source library registration (spec_source_ingestion_v2 §4.1/§13).

New canonical sources live at vault level (``sources/``). Legacy subject-scoped
source notes stay readable in place forever; this module indexes them into
``SourceArtifact``/``SourceRevision`` rows **without moving or rewriting user
files** (§13). Registration is idempotent on artifact identity + ``asset_hash``:
- same artifact identity + same bytes reuse the revision;
- same artifact identity + new bytes create a linked new revision
  (``supersedes_revision_id``).
"""

from __future__ import annotations

from dataclasses import dataclass

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.hashing import asset_hash


@dataclass(frozen=True)
class RegisteredRevision:
    source_id: str
    revision_id: str
    asset_hash: str
    reused_revision: bool
    reused_artifact: bool


def register_source_revision(
    repo: Repository,
    *,
    acquisition_kind: str,
    canonical_uri: str | None,
    raw_bytes: bytes,
    note_id: str | None = None,
    original_uri: str | None = None,
    retrieved_at: str | None = None,
    work_id: str | None = None,
    display_title: str | None = None,
    clock: Clock | None = None,
) -> RegisteredRevision:
    """Register (or reuse) the artifact/revision rows for one acquisition.

    Idempotent: identical artifact identity + identical bytes reuse the same
    revision; changed bytes link a new revision to the same artifact.

    ``display_title`` is a human-readable label captured at fetch time (e.g. a
    YouTube video's "<title> — <author>"). It is stored on first registration of
    an artifact and, being COALESCE-merged, never overwritten by a later re-import
    that omits it. Sources without knowable metadata pass ``None`` and fall back
    to the URL as before.
    """

    digest = asset_hash(raw_bytes)

    artifact = (
        repo.source_artifact_by_uri(acquisition_kind, canonical_uri)
        if canonical_uri is not None
        else None
    )
    reused_artifact = artifact is not None
    if artifact is None:
        source_id = f"src_{new_ulid()}"
        repo.upsert_source_artifact(
            id=source_id,
            acquisition_kind=acquisition_kind,
            canonical_uri=canonical_uri,
            work_id=work_id,
            display_title=display_title,
            clock=clock,
        )
    else:
        source_id = artifact["id"]

    existing = repo.source_revision_by_asset_hash(source_id, digest)
    if existing is not None:
        return RegisteredRevision(
            source_id=source_id,
            revision_id=existing["id"],
            asset_hash=digest,
            reused_revision=True,
            reused_artifact=reused_artifact,
        )

    # A newer byte sequence for the same artifact links via supersedes_revision_id.
    prior_revisions = repo.source_revisions_for(source_id)
    supersedes = prior_revisions[-1]["id"] if prior_revisions else None
    revision_id = f"rev_{new_ulid()}"
    repo.insert_source_revision(
        id=revision_id,
        source_id=source_id,
        asset_hash=digest,
        note_id=note_id,
        original_uri=original_uri or canonical_uri,
        retrieved_at=retrieved_at,
        supersedes_revision_id=supersedes,
        clock=clock,
    )
    repo.set_source_current_revision(source_id, revision_id, clock=clock)
    return RegisteredRevision(
        source_id=source_id,
        revision_id=revision_id,
        asset_hash=digest,
        reused_revision=False,
        reused_artifact=reused_artifact,
    )


def index_legacy_note(
    repo: Repository,
    *,
    note_id: str,
    acquisition_kind: str,
    canonical_uri: str | None,
    raw_bytes: bytes,
    note_path: str | None = None,
    retrieved_at: str | None = None,
    clock: Clock | None = None,
) -> RegisteredRevision:
    """Index one legacy subject-scoped source note into artifact/revision rows.

    Does NOT move or rewrite the note file (§13); it only records identity rows so
    the library can reference the source. ``note_path`` is retained as
    ``original_uri`` when no canonical URI exists.
    """

    return register_source_revision(
        repo,
        acquisition_kind=acquisition_kind,
        canonical_uri=canonical_uri,
        raw_bytes=raw_bytes,
        note_id=note_id,
        original_uri=canonical_uri or note_path,
        retrieved_at=retrieved_at,
        clock=clock,
    )
