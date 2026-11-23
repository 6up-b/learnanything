"""Where a completed Reader Ask was, read from its durable ``reader_answer_submitted`` payload.

Two readers share this: :func:`learnloop.reader.reader_dialogue.ask_provenance` (every passage an
exchange names, for the protection filter) and the workbench's passage projection
(``learnloop.passage_spans.projection``: the selection and the citations, each with its role). Pure: it
reads one payload and touches no store.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: The roles a place can have: the learner's anchor and selection, a citation of the answer, and a
#: passage the tutor was given (a neighbour, a retrieved or explorable passage, the excerpt).
SELECTION = "selection"
CITED = "cited"
GIVEN = "given"


def located(value: Any, extraction_id: str) -> tuple[str, str] | None:
    """The ``(reading, span)`` a citation-like value names, or None."""

    if not isinstance(value, dict):
        return None
    span = value.get("span_id")
    reading = value.get("extraction_id") or extraction_id
    locator = str(value.get("locator") or value.get("href") or "")
    if not span and locator.startswith("span:") and "/" in locator:
        reading, span = locator[len("span:"):].split("/", 1)
    return (str(reading), str(span)) if span else None


def exchange_places(payload: Mapping[str, Any], *, subject_id: str, extraction_id: str) -> list[tuple[str, str, str]]:
    """Every ``(reading, span, role)`` one exchange names, in the order ``ask_provenance`` lists them."""

    prefix = f"span:{extraction_id}/"
    manifest = payload.get("manifest") or {}
    selection = manifest.get("selection") or {}
    tutor = payload.get("tutor") if isinstance(payload.get("tutor"), dict) else {}
    anchor = payload.get("span_id") or (subject_id[len(prefix):] if subject_id.startswith(prefix) else None)
    places = [(extraction_id, str(span), SELECTION) for span in [anchor, *(selection.get("span_ids") or [])] if span]
    for value in payload.get("citations") or []:
        place = located(value, extraction_id)
        if place is not None:
            places.append((*place, CITED))
    for value in [tutor.get("excerpt"), *(tutor.get("explorable") or []), *(manifest.get("source_spans") or [])]:
        place = located(value, extraction_id)
        if place is not None:
            places.append((*place, GIVEN))
    for key in (tutor.get("retrieval") or {}).get("span_keys") or []:
        reading, _, span = str(key).partition(":")  # as ``reader_tutor.shown_span_keys`` reads them
        if reading and span:
            places.append((reading, span, GIVEN))
    return places


__all__ = ["CITED", "GIVEN", "SELECTION", "exchange_places", "located"]
