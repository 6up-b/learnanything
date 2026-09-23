"""Managed store for original source bytes (``canonical-sources/raw/``).

Revisions record ``asset_hash`` + ``original_uri``. Live-source viewers (the
embedded PDF reader) and resumed ingests need the original bytes even after
the user's file moves or a URL goes stale, so registration retains a
content-addressed copy at ``VaultPaths.canonical_source_raw_path``.
``original_uri`` remains the record of provenance; the store is a vault-owned
copy whose filename commits to the bytes (``sha256-<hex>``), so a stored file
can always be verified against its revision's ``asset_hash``.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from learnloop.ingest.hashing import asset_hash

PDF_MAGIC = b"%PDF-"


def canonical_source_raw_path(root: Path, asset_hash_value: str) -> Path:
    """Return the config-free managed-original path for one content hash."""

    return root / "canonical-sources" / "raw" / asset_hash_value.replace(":", "-")


def store_original_bytes(vault_root: Path, digest: str, raw_bytes: bytes) -> Path:
    """Write bytes into the content-addressed store (idempotent, atomic).

    Each writer uses its own temporary name, so concurrent imports of the same
    content never rename or remove a file another writer is still filling. The
    bytes are synced before the rename: a stored file is trusted by name alone,
    so a power loss must not leave a truncated file under the final name.
    """

    path = canonical_source_raw_path(vault_root, digest)
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        # 0o644 is filtered by the process umask, like any other vault file.
        descriptor = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw_bytes)
            handle.flush()
            os.fsync(handle.fileno())
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return path


def stored_original_path(vault_root: Path, digest: str | None) -> Path | None:
    if not digest:
        return None
    path = canonical_source_raw_path(vault_root, digest)
    return path if path.is_file() else None


def _local_uri_path(original_uri: str | None) -> Path | None:
    if not original_uri or original_uri.startswith(("http://", "https://")):
        return None
    candidate = original_uri[7:] if original_uri.startswith("file://") else original_uri
    path = Path(candidate).expanduser()
    return path if path.is_file() else None


def resolve_original_file(
    vault_root: Path, *, digest: str | None, original_uri: str | None
) -> Path | None:
    """Best available copy of a revision's original bytes: the managed store
    first, else ``original_uri`` when it still points at a local file."""

    return stored_original_path(vault_root, digest) or _local_uri_path(original_uri)


def is_pdf_file(path: Path) -> bool:
    """Header sniff — store files are extensionless (named by hash)."""

    try:
        with path.open("rb") as handle:
            return handle.read(len(PDF_MAGIC)) == PDF_MAGIC
    except OSError:
        return False


def backfill_original(
    vault_root: Path, *, digest: str, original_uri: str | None
) -> tuple[str, Path | None]:
    """Copy a pre-store revision's bytes into the store from ``original_uri``.

    Returns ``(status, stored_path)`` where status is one of ``stored``,
    ``already_stored``, ``missing`` (no resolvable local file), or
    ``hash_mismatch`` (the file at ``original_uri`` no longer matches the
    revision's ``asset_hash`` — never stored under that digest).
    """

    existing = stored_original_path(vault_root, digest)
    if existing is not None:
        return "already_stored", existing
    source = _local_uri_path(original_uri)
    if source is None:
        return "missing", None
    raw = source.read_bytes()
    if asset_hash(raw) != digest:
        return "hash_mismatch", None
    return "stored", store_original_bytes(vault_root, digest, raw)
