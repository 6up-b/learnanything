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

RESOLUTIONS = ("open", "resolved", "dismissed")


class QuestionQueueError(ValueError):
    """Invalid queue operation (unknown event id or resolution state)."""


def list_question_queue(
    repository: Repository,
    *,
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
            "note_id": event.get("note_id"),
            "saved_note_id": event.get("saved_note_id"),
            "created_at": event["created_at"],
            "promotion": promotions.get(event["id"]),
        }
        for event in events
    ]


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
