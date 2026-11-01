"""One guard for every persisting Reader request that names passages
(Reader CA6b fix round 5, structural).

A request that writes something about passages names them twice: by their
ids (span ids, a raw selection's nodes, a region's span, an exchange) and by
the reading they are in (an extraction, and often its source and revision).
The two must agree. If the passages are another reading's -- the other book
of side by side, or an older reading of the same book -- the write would
attach one book's passages to another book's record. The guard refuses such
a request before anything is written (fail closed). It changes no valid
call: a request whose ids all belong to the reading it names passes
unchanged.

``SpanExtractionMismatch`` carries the stable code ``span_extraction_mismatch``.
The sidecar handlers turn it into that typed error, and the Reader shows it as
"that passage belongs to another reading; reopen it".

Deliberately cross-reading flows do not go through this guard. They name both
readings explicitly: ``reader.reanchor`` (an annotation moved to
``new_extraction_id``), ``reader.saved_place`` (``to_extraction_id``), and
library pins, whose ``extraction:span`` keys each name their own reading and
are checked key by key here.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

MISMATCH_CODE = "span_extraction_mismatch"


class SpanExtractionMismatch(ValueError):
    """The passages named are not the named reading's (or the reading is not
    the named source's or revision's). Nothing was written."""

    code = MISMATCH_CODE

    def __init__(self, message: str, *, extraction_id: str | None, reason: str,
                 span_ids: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.extraction_id = extraction_id
        self.reason = reason
        self.span_ids = list(span_ids)

    def details(self) -> dict[str, Any]:
        return {"extraction_id": self.extraction_id, "reason": self.reason, "span_ids": self.span_ids}


def selection_span_ids(raw_selection: Mapping[str, Any] | None) -> list[str]:
    """The span ids a raw display selection names (its nodes, and a region's
    span). Nodes that name only a display node are resolved through the render
    view's own crosswalk (which belongs to the reading), so they are not listed."""

    if not raw_selection:
        return []
    spans: list[str] = []
    for node in raw_selection.get("nodes") or []:
        if isinstance(node, Mapping):
            span = node.get("span_id", node.get("spanId"))
            if span:
                spans.append(str(span))
    region = raw_selection.get("region")
    if isinstance(region, Mapping):
        span = region.get("span_id", region.get("spanId"))
        if span:
            spans.append(str(span))
    return spans


def subject_span_id(subject_id: str | None, extraction_id: str) -> list[str]:
    """A preset's subject: a bare span id of the reading, or a
    ``span:{extraction}/{span}`` locator (one naming another reading is a
    mismatch on its own)."""

    if not subject_id:
        return []
    if not subject_id.startswith("span:"):
        return [subject_id]
    reading, _, span = subject_id[len("span:"):].partition("/")
    if reading != extraction_id:
        raise SpanExtractionMismatch(
            f"The subject {subject_id!r} is a passage of another reading than {extraction_id!r}.",
            extraction_id=extraction_id, reason="subject_reading", span_ids=[span] if span else [],
        )
    return [span] if span else []


def require_source_identity(
    repository: Any,
    *,
    extraction_id: str,
    span_ids: Iterable[str | None] = (),
    source_id: str | None = None,
    revision_id: str | None = None,
) -> None:
    """Refuse (``SpanExtractionMismatch``) unless every span id is a block of
    ``extraction_id``, and the reading is ``revision_id``'s and ``source_id``'s
    when they are named. With no span id, source or revision named, nothing is
    checked (the request names no passage)."""

    wanted = list(dict.fromkeys(str(span) for span in span_ids if span))
    if not wanted and source_id is None and revision_id is None:
        return
    run = repository.get_extraction_run(extraction_id)
    if run is None:
        raise SpanExtractionMismatch(
            f"No reading {extraction_id!r} to check these passages against.",
            extraction_id=extraction_id, reason="unknown_extraction", span_ids=wanted,
        )
    run_revision = str(run.get("revision_id") or "")
    if revision_id is not None and revision_id != run_revision:
        raise SpanExtractionMismatch(
            f"The reading {extraction_id!r} is not of revision {revision_id!r}.",
            extraction_id=extraction_id, reason="revision", span_ids=wanted,
        )
    if source_id is not None:
        revision = repository.get_source_revision(run_revision) if run_revision else None
        if revision is None or str(revision.get("source_id") or "") != source_id:
            raise SpanExtractionMismatch(
                f"The reading {extraction_id!r} is not of source {source_id!r}.",
                extraction_id=extraction_id, reason="source", span_ids=wanted,
            )
    if not wanted:
        return
    present = {block.span_id for block in repository.document_blocks(extraction_id, wanted)}
    missing = [span for span in wanted if span not in present]
    if missing:
        raise SpanExtractionMismatch(
            f"The passage(s) {', '.join(missing)} are not in the reading {extraction_id!r}.",
            extraction_id=extraction_id, reason="span", span_ids=missing,
        )


def require_span_keys(repository: Any, keys: Iterable[str]) -> None:
    """Library pins: each ``extraction:span`` key's span is a block of the
    reading the key names."""

    by_reading: dict[str, list[str]] = {}
    for key in keys:
        reading, sep, span = str(key).rpartition(":")
        if not sep or not reading or not span:
            continue
        by_reading.setdefault(reading, []).append(span)
    for reading, spans in by_reading.items():
        require_source_identity(repository, extraction_id=reading, span_ids=spans)


def require_exchange_in_extraction(repository: Any, *, extraction_id: str, exchange_id: str | None) -> None:
    """A Reader exchange named with a reading must have been asked in it. An
    exchange of another reading is a mismatch. One that does not exist at all
    is left to the handler, which says so in its own words."""

    if not exchange_id:
        return
    for event in repository.reader_interaction_events(kind="reader_answer_submitted"):
        if str(event.get("id")) != exchange_id:
            continue
        payload = event.get("payload") or {}
        asked_in = str(payload.get("extraction_id") or "")
        if not asked_in:
            subject = str(event.get("subject_id") or "")
            asked_in = subject[len("span:"):].partition("/")[0] if subject.startswith("span:") else ""
        if asked_in and asked_in != extraction_id:
            raise SpanExtractionMismatch(
                f"The exchange {exchange_id!r} was asked in another reading than {extraction_id!r}.",
                extraction_id=extraction_id, reason="exchange", span_ids=[],
            )
        return


__all__ = [
    "MISMATCH_CODE",
    "SpanExtractionMismatch",
    "require_exchange_in_extraction",
    "require_source_identity",
    "require_span_keys",
    "selection_span_ids",
    "subject_span_id",
]
