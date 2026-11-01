"""The sidecar's one call into the Reader's passage-identity guard (Reader
CA6b fix round 5): every persisting handler that takes passage ids with a
reading calls ``require_identity`` before it writes anything, and a mismatch
becomes the typed ``span_extraction_mismatch`` error (nothing written)."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from learnloop.reader import source_identity as SI
from learnloop_sidecar.errors import SidecarError


def require_identity(
    repository: Any,
    *,
    extraction_id: str | None,
    span_ids: Iterable[str | None] = (),
    raw_selection: Mapping[str, Any] | None = None,
    subject_id: str | None = None,
    source_id: str | None = None,
    revision_id: str | None = None,
    span_keys: Iterable[str] = (),
    exchange_id: str | None = None,
    render_view_id: str | None = None,
    annotation_id: str | None = None,
) -> None:
    """Refuse with ``span_extraction_mismatch`` unless the passages (span ids,
    a raw selection's nodes and region, a preset's subject), the source and
    revision named, an exchange, and each pin key all belong to the reading."""

    try:
        if extraction_id:
            spans = [*span_ids, *SI.selection_span_ids(raw_selection), *SI.subject_span_id(subject_id, extraction_id)]
            SI.require_source_identity(
                repository, extraction_id=extraction_id, span_ids=spans, source_id=source_id, revision_id=revision_id,
            )
            SI.require_exchange_in_extraction(repository, extraction_id=extraction_id, exchange_id=exchange_id)
            # Round 6: a selection's render view and its nodes' own readings,
            # and an annotation moved only within its own book.
            SI.require_selection_provenance(repository, extraction_id=extraction_id, raw_selection=raw_selection,
                                            render_view_id=render_view_id)
            SI.require_annotation_source(repository, annotation_id=annotation_id, extraction_id=extraction_id)
        SI.require_span_keys(repository, span_keys)
    except SI.SpanExtractionMismatch as exc:
        raise SidecarError(SI.MISMATCH_CODE, str(exc), details=exc.details()) from exc


__all__ = ["require_identity"]
