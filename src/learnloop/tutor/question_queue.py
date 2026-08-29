"""The outstanding-question queue (spec_andymatusnotes: "a queue of outstanding
questions ... a natural place to put questions which came up but remained
unanswered").

Every captured tutor question (question_events) starts ``open`` and stays
visibly in the queue until the learner marks it ``resolved`` or ``dismissed``
(migration 102). Resolution belongs to the learner, not the tutor: a
tutor-``answered`` question may still leave the underlying confusion standing,
so ``answer_status`` (did the tutor answer?) and ``resolution`` (is the learner
done with it?) are independent axes. Promotion to practice material is a
separate, already-shipped action (question_promotions) surfaced here so the
queue shows what each question already became.
"""

from __future__ import annotations

from typing import Any

from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault

RESOLUTIONS = ("open", "resolved", "dismissed")


class QuestionQueueError(ValueError):
    """Invalid queue operation (unknown event id or resolution state)."""


def list_question_queue(
    repository: Repository,
    *,
    vault: LoadedVault | None = None,
    resolution: str | None = "open",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Queue rows, newest first, each carrying its promotion (if any).

    ``resolution=None`` lists every question regardless of state (the review
    ledger); the default lists only the open queue.
    """

    if resolution is not None and resolution not in RESOLUTIONS:
        raise QuestionQueueError(f"unknown resolution {resolution!r}")
    events = repository.question_events(resolution=resolution)
    events.reverse()  # repository order is oldest-first
    if limit is not None:
        events = events[: max(0, int(limit))]
    promotions = repository.question_promotions_for_events([e["id"] for e in events])
    promotion_requests = repository.question_promotion_requests_for_events(
        [e["id"] for e in events]
    )
    if vault is not None:
        from learnloop.tutor.promotions import promotion_target_ids

        targets = {
            event["id"]: promotion_target_ids(vault, repository, event)
            for event in events
        }
    else:
        targets = {event["id"]: [] for event in events}
    return [
        {
            "id": event["id"],
            "context": event["context"],
            "question_md": event["question_md"],
            "answer_md": event["answer_md"],
            "answer_status": event["answer_status"],
            "resolution": event["resolution"],
            "question_type": event.get("question_type"),
            "practice_item_id": event.get("practice_item_id"),
            "attempt_id": event.get("attempt_id"),
            "note_id": event.get("note_id"),
            "session_id": event.get("session_id"),
            "saved_note_id": event.get("saved_note_id"),
            "created_at": event["created_at"],
            "promotion": promotions.get(event["id"]),
            "promotion_request": promotion_requests.get(event["id"]),
            "promotion_target_ids": targets[event["id"]],
            "source_citation": _source_citation(
                repository, event, vault=vault
            ),
        }
        for event in events
    ]


def _source_citation(
    repository: Repository,
    event: dict[str, Any],
    *,
    vault: LoadedVault | None,
) -> dict[str, str | None] | None:
    """Best canonical teaching span for an outstanding question.

    Reader questions retain their exact in-view span in ``source_context``.
    Older practice/feedback/library turns predate that structured field, so
    they fall back to the same bounded semantic-authority span selection used
    to ground tutor answers.  Returning ``None`` is an honest absence: the
    Today surface never fabricates a source link from a note path or item id.
    """

    source_context = event.get("source_context")
    source_context = source_context if isinstance(source_context, dict) else {}
    extraction_id = source_context.get("extraction_id")
    span_id = source_context.get("span_id")
    source_spans = source_context.get("source_spans")
    source_spans = source_spans if isinstance(source_spans, list) else []
    citations = source_context.get("citations")
    citations = citations if isinstance(citations, list) else []

    # Reader dialogue continuity is keyed to the originally viewed span. A
    # tutor may cite an adjacent block in its answer, but reopening the thread
    # must not silently move the learner into a different per-span conversation.
    if event.get("context") == "reader" and extraction_id and span_id:
        matching = next(
            (
                span
                for span in source_spans
                if isinstance(span, dict)
                and str(span.get("extraction_id")) == str(extraction_id)
                and str(span.get("span_id")) == str(span_id)
            ),
            None,
        )
        return {
            "extraction_id": str(extraction_id),
            "span_id": str(span_id),
            "label": (
                str(matching.get("label"))
                if matching is not None and matching.get("label")
                else None
            ),
        }

    validated_citation = next(
        (
            citation
            for citation in citations
            if isinstance(citation, dict)
            and citation.get("extraction_id")
            and citation.get("span_id")
        ),
        None,
    )
    if validated_citation is not None:
        return {
            "extraction_id": str(validated_citation["extraction_id"]),
            "span_id": str(validated_citation["span_id"]),
            "label": (
                str(validated_citation["label"])
                if validated_citation.get("label")
                else None
            ),
        }

    if extraction_id and span_id:
        matching = next(
            (
                span
                for span in source_spans
                if isinstance(span, dict)
                and str(span.get("extraction_id")) == str(extraction_id)
                and str(span.get("span_id")) == str(span_id)
            ),
            None,
        )
        return {
            "extraction_id": str(extraction_id),
            "span_id": str(span_id),
            "label": (
                str(matching.get("label"))
                if matching is not None and matching.get("label")
                else None
            ),
        }

    if vault is None:
        return None

    learning_object_ids: list[str] = []
    practice_item_id = event.get("practice_item_id")
    if practice_item_id:
        item = vault.practice_items.get(str(practice_item_id))
        if item is not None:
            learning_object_ids.append(item.learning_object_id)
    elif event.get("context") == "library" and event.get("note_id"):
        note = vault.notes.get(str(event["note_id"]))
        if note is not None:
            learning_object_ids.extend(note.related_los)

    if not learning_object_ids:
        return None

    # Kept in tutor_qa as the single authority for bounded, semantic teaching
    # spans. Import lazily to avoid loading the tutor stack for queue counts.
    from learnloop.tutor.tutor_qa import _source_spans

    try:
        spans = _source_spans(vault, repository, learning_object_ids)
    except Exception:  # noqa: BLE001 - optional enrichment must never hide the queue
        return None
    if not spans:
        return None
    first = spans[0]
    if not first.get("extraction_id") or not first.get("span_id"):
        return None
    return {
        "extraction_id": str(first["extraction_id"]),
        "span_id": str(first["span_id"]),
        "label": str(first["label"]) if first.get("label") else None,
    }


def count_open_questions(repository: Repository) -> int:
    return repository.count_question_events(resolution="open")


def set_question_resolution(
    repository: Repository,
    *,
    question_event_id: str,
    resolution: str,
) -> dict[str, Any]:
    """Move one question to ``open``/``resolved``/``dismissed``; returns the row.

    Reopening is legitimate (the confusion came back) -- the queue is a working
    surface, not an append-only ledger, so this is a plain state flip.
    """

    if resolution not in RESOLUTIONS:
        raise QuestionQueueError(f"unknown resolution {resolution!r}")
    if repository.question_event(question_event_id) is None:
        raise QuestionQueueError(f"unknown question event {question_event_id!r}")
    repository.set_question_event_resolution(question_event_id, resolution=resolution)
    event = repository.question_event(question_event_id)
    assert event is not None
    return event
