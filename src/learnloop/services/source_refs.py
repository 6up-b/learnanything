"""Human-facing labels and metadata for durable source references.

``SourceRef.ref_id`` deliberately remains a stable machine identity.  Display
surfaces should resolve that identity through the ingest source library (or a
legacy canonical-source note) instead of asking learners to recognize a hash or
ULID.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Mapping
from urllib.parse import unquote, urlparse


_SPAN_LOCATOR = re.compile(r"^span:([^/]+)/")
_FILE_KINDS = {"audio", "pdf", "textfile"}
_KIND_ALIASES = {
    "arxiv": "arxiv_html",
    "web": "website_page",
    "youtube": "youtube_video",
}


@dataclass(frozen=True)
class SourceRefPresentation:
    """Resolved source identity suitable for UI and CLI presentation."""

    display_name: str
    kind: str | None
    canonical_uri: str | None
    original_uri: str | None
    note: Any | None


def source_ref_presentation(vault, repository, ref) -> SourceRefPresentation:
    """Resolve one ref without changing its persisted provenance identity."""

    revision = _revision_for_ref(repository, ref)
    source_id = _text_field(ref, "source_id")
    if revision is not None:
        source_id = _clean_text(revision.get("source_id")) or source_id

    artifact = (
        _repo_call(repository, "get_source_artifact", source_id)
        if source_id
        else None
    )
    if artifact is None:
        ref_id = _text_field(ref, "ref_id")
        artifact = (
            _repo_call(repository, "get_source_artifact", ref_id)
            if ref_id
            else None
        )
    if artifact is not None and revision is None:
        current_revision_id = _clean_text(artifact.get("current_revision_id"))
        if current_revision_id:
            revision = _repo_call(repository, "get_source_revision", current_revision_id)
        if revision is None:
            revisions = (
                _repo_call(repository, "source_revisions_for", artifact.get("id"))
                or []
            )
            revision = revisions[-1] if revisions else None

    note = _note_for_ref(vault, ref, revision)
    canonical = _canonical_metadata(note)
    artifact_kind = (
        _clean_text(artifact.get("acquisition_kind"))
        if artifact is not None
        else None
    )
    kind = _clean_text(canonical.get("kind")) or _KIND_ALIASES.get(
        artifact_kind or "", artifact_kind
    )
    canonical_uri = (
        _clean_text(artifact.get("canonical_uri")) if artifact is not None else None
    ) or _clean_text(canonical.get("canonical_uri"))
    original_uri = (
        _clean_text(revision.get("original_uri")) if revision is not None else None
    ) or _clean_text(canonical.get("original_uri"))

    display_title = (
        _clean_text(artifact.get("display_title"))
        if artifact is not None
        else None
    )
    canonical_title = _clean_text(canonical.get("title"))
    note_heading = (
        _first_heading(getattr(note, "body", "")) if note is not None else None
    )
    uri = original_uri or canonical_uri

    if _is_file_source(artifact_kind, uri):
        display_name = _file_name(uri) or display_title or canonical_title or note_heading
    elif kind == "youtube_video":
        display_name = display_title or canonical_title or note_heading
    else:
        display_name = display_title or canonical_title or note_heading

    if not display_name:
        display_name = _uri_label(uri)
    if not display_name:
        display_name = _text_field(ref, "ref_id") or "source"

    return SourceRefPresentation(
        display_name=display_name,
        kind=kind,
        canonical_uri=canonical_uri,
        original_uri=original_uri,
        note=note,
    )


def source_ref_display_dto(vault, repository, ref) -> dict[str, Any]:
    """Return a source-ref payload augmented with its human-facing name."""

    if hasattr(ref, "model_dump"):
        raw = ref.model_dump(mode="json")
    elif isinstance(ref, Mapping):
        raw = dict(ref)
    else:
        raise TypeError(f"Unsupported source ref: {type(ref)!r}")
    display_name = source_ref_presentation(vault, repository, ref).display_name
    # Put the human label before the durable id in terminal output while
    # preserving every source-ref field for API consumers.
    return {
        "display_name": display_name,
        **{key: value for key, value in raw.items() if key != "display_name"},
    }


def _revision_for_ref(repository, ref) -> dict[str, Any] | None:
    revision_id = _text_field(ref, "revision_id")
    if revision_id:
        revision = _repo_call(repository, "get_source_revision", revision_id)
        if revision is not None:
            return revision

    extraction_id = _text_field(ref, "extraction_id")
    if not extraction_id:
        locator = _text_field(ref, "locator")
        match = _SPAN_LOCATOR.match(locator or "")
        extraction_id = match.group(1) if match else None
    if extraction_id:
        extraction = _repo_call(repository, "get_extraction_run", extraction_id)
        if extraction is not None:
            revision_id = _clean_text(extraction.get("revision_id"))
            if revision_id:
                return _repo_call(repository, "get_source_revision", revision_id)
    return None


def _note_for_ref(vault, ref, revision: Mapping[str, Any] | None):
    notes = getattr(vault, "notes", {}) or {}
    ref_id = _text_field(ref, "ref_id")
    note = notes.get(ref_id) if ref_id else None
    if note is None and revision is not None:
        note_id = _clean_text(revision.get("note_id"))
        note = notes.get(note_id) if note_id else None
    if note is not None:
        return note

    ref_path = _text_field(ref, "path")
    if ref_path:
        return next((candidate for candidate in notes.values() if candidate.path == ref_path), None)
    return None


def _canonical_metadata(note) -> dict[str, Any]:
    if note is None:
        return {}
    metadata = getattr(note, "model_extra", {}) or {}
    canonical = metadata.get("canonical_source")
    return canonical if isinstance(canonical, dict) else {}


def _is_file_source(kind: str | None, uri: str | None) -> bool:
    if kind in _FILE_KINDS:
        return True
    if not uri:
        return False
    parsed = urlparse(uri)
    return parsed.scheme == "file" or (
        not parsed.scheme and bool(PurePosixPath(parsed.path).suffix)
    )


def _file_name(uri: str | None) -> str | None:
    if not uri:
        return None
    path = unquote(urlparse(uri).path or uri)
    name = PurePosixPath(path.replace("\\", "/")).name
    return name or None


def _uri_label(uri: str | None) -> str | None:
    if not uri:
        return None
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return _file_name(uri)
    if parsed.netloc:
        path = unquote(parsed.path).rstrip("/")
        return f"{parsed.netloc}{path}" if path else parsed.netloc
    return _file_name(uri) or uri


def _first_heading(body: str) -> str | None:
    for line in body.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1)
    return None


def _text_field(value: Any, field: str) -> str | None:
    if isinstance(value, Mapping):
        return _clean_text(value.get(field))
    return _clean_text(getattr(value, field, None))


def _clean_text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    return cleaned or None


def _repo_call(repository, method: str, *args):
    if repository is None:
        return None
    callback = getattr(repository, method, None)
    if callback is None:
        return None
    return callback(*args)
