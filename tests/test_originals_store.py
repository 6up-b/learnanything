"""Managed originals store (canonical-sources/raw/) — retention + backfill."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.hashing import asset_hash
from learnloop.ingest.originals import (
    backfill_original,
    is_pdf_file,
    resolve_original_file,
    store_original_bytes,
    stored_original_path,
)
from learnloop.ingest.source_library import register_source_revision
from learnloop.vault.paths import canonical_source_raw_path

_CLOCK = FrozenClock(datetime(2026, 7, 21, 0, 0, 0, tzinfo=UTC))


def test_register_with_vault_root_retains_bytes(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    raw = b"%PDF-1.7 fake"
    registered = register_source_revision(
        repo,
        acquisition_kind="pdf",
        canonical_uri="https://ex/book.pdf",
        raw_bytes=raw,
        vault_root=tmp_path,
        clock=_CLOCK,
    )
    stored = stored_original_path(tmp_path, registered.asset_hash)
    assert stored is not None
    assert stored.read_bytes() == raw
    assert is_pdf_file(stored)


def test_register_reuse_backfills_missing_store_copy(tmp_path):
    repo = Repository(tmp_path / "state.sqlite")
    raw = b"%PDF-1.7 fake"
    first = register_source_revision(
        repo, acquisition_kind="pdf", canonical_uri="https://ex/book.pdf", raw_bytes=raw, clock=_CLOCK
    )
    assert stored_original_path(tmp_path, first.asset_hash) is None
    second = register_source_revision(
        repo,
        acquisition_kind="pdf",
        canonical_uri="https://ex/book.pdf",
        raw_bytes=raw,
        vault_root=tmp_path,
        clock=_CLOCK,
    )
    assert second.reused_revision is True
    assert stored_original_path(tmp_path, second.asset_hash) is not None


def test_resolve_prefers_store_then_original_uri(tmp_path):
    raw = b"%PDF-1.7 fake"
    digest = asset_hash(raw)
    local = tmp_path / "book.pdf"
    local.write_bytes(raw)
    # Store missing → falls back to the original_uri file.
    resolved = resolve_original_file(tmp_path, digest=digest, original_uri=local.as_uri())
    assert resolved == local
    # Store present → wins even if the original file disappears.
    store_original_bytes(tmp_path, digest, raw)
    local.unlink()
    resolved = resolve_original_file(tmp_path, digest=digest, original_uri=local.as_uri())
    assert resolved == canonical_source_raw_path(tmp_path, digest)
    # Remote-only original with no store copy → nothing.
    assert resolve_original_file(tmp_path, digest="sha256:0", original_uri="https://ex/a.pdf") is None


def test_backfill_statuses(tmp_path):
    raw = b"%PDF-1.7 fake"
    digest = asset_hash(raw)
    local = tmp_path / "book.pdf"
    local.write_bytes(raw)

    status, path = backfill_original(tmp_path, digest=digest, original_uri=local.as_uri())
    assert status == "stored" and path is not None and path.read_bytes() == raw
    status, _ = backfill_original(tmp_path, digest=digest, original_uri=local.as_uri())
    assert status == "already_stored"

    other = tmp_path / "changed.pdf"
    other.write_bytes(b"%PDF-1.7 different bytes")
    status, path = backfill_original(tmp_path, digest=digest[:-4] + "beef", original_uri=other.as_uri())
    assert status == "hash_mismatch" and path is None

    status, path = backfill_original(tmp_path, digest="sha256:feed", original_uri="https://ex/gone.pdf")
    assert status == "missing" and path is None
