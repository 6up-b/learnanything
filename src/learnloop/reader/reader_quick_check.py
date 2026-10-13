"""Reader quick-check producer: AI-authored section-boundary questions.

The producer half of the mnemonic-medium boundary prompt: as the learner
approaches the end of a section while reading closely, a durable
``reader_quick_check`` job authors ONE span-grounded comprehension question for
that section (codex ``run_reading_quick_check``, getattr-discovered), validated
in code against the section's own spans and persisted as a
``reader_authored_questions`` row.  The guide plan surfaces it only where no
owner-reviewed placement exists (``placement: auto_authored``).

Evidence honesty: an authored question has no practice item, surface, or
administration.  Answering it is a formative self-check recorded on the row
(never attempts/mastery).  The learner may escalate it into a real
PracticeItem — the Matuschak reader-control act of collecting a prompt — which
mints a learner-authority card with ``codex_proposal`` provenance and
``span:<extraction_id>/<span_id>`` source refs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.ai.transport import StructuredTransport, execute_structured_operation
from learnloop.reader.ai_contracts import (
    READING_PASSAGE_CHECK_PROMPT_VERSION,
    ReadingQuickCheck,
    ReadingQuickCheckContext,
    reading_passage_check_prompt,
    reading_quick_check_prompt,
)
from learnloop.clock import Clock, utc_now_iso
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ingest.locators import BLOCK_SPAN_V1, format_block_span
from learnloop.reader.reader_guidance import extraction_sections
from learnloop.vault.loader import load_vault
from learnloop.vault.writer import upsert_practice_item

# Keep the authoring context bounded: a pathological "section" (e.g. the
# whole-source fallback unit) is truncated, never silently expanded.
MAX_SECTION_BLOCKS = 60
MAX_SECTION_CHARS = 24_000

QUESTION_ACTIONS = ("answered", "dismissed")

# RW1a: the reconnect line's passage-scoped check (spec_reader_workbench_v1 §4.1).
# The passage is the inquiry's anchor plus a little context on each side,
# inside the anchor's section (the producer never reads past it).
INQUIRY_PROMPT_VERSION = READING_PASSAGE_CHECK_PROMPT_VERSION
PASSAGE_BLOCKS_BEFORE = 1
PASSAGE_BLOCKS_AFTER = 2
MAX_PASSAGE_CHARS = 8_000
INQUIRY_ACTIONS = ("answered", "self_checked", "dismissed")
SELF_CHECKS = ("matches", "partly", "no")


class ReaderQuickCheckError(ValueError):
    """Domain error for the reader quick-check producer."""


def request_reading_quick_check(
    client: StructuredTransport, context: ReadingQuickCheckContext
) -> ReadingQuickCheck:
    """Author one section quick check through the shared transport."""

    return execute_structured_operation(
        client,
        purpose="reading_quick_check",
        prompt=reading_quick_check_prompt(context),
        result_model=ReadingQuickCheck,
    )


def request_passage_check(
    client: StructuredTransport, context: ReadingQuickCheckContext
) -> ReadingQuickCheck:
    """Author one passage-scoped quick check (RW1a) through the shared transport.

    The same operation and contract as the section check, so the producer's
    route and caps apply unchanged; only the prompt says "passage"."""

    return execute_structured_operation(
        client,
        purpose="reading_quick_check",
        prompt=reading_passage_check_prompt(context),
        result_model=ReadingQuickCheck,
    )


def section_view(repository: Repository, *, extraction_id: str, section_id: str) -> dict[str, Any]:
    """The bounded, readable view of ONE guide section: {section_id, label,
    blocks:[{span_id, kind, text}]}. Uses the same section derivation as the
    guide plan so producer and consumer agree on boundaries."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderQuickCheckError(f"extraction has no IR: {extraction_id!r}")
    section_rows, block_by_span, _span_to_section = extraction_sections(ir)
    section = next((row for row in section_rows if row["id"] == section_id), None)
    if section is None:
        raise ReaderQuickCheckError(f"unknown section: {section_id!r}")

    blocks: list[dict[str, str]] = []
    total_chars = 0
    for span_id in section["span_ids"][:MAX_SECTION_BLOCKS]:
        block = block_by_span[span_id]
        text = " ".join((block.text or "").split())
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_SECTION_CHARS:
            break
        blocks.append({"span_id": span_id, "kind": str(block.block_type or ""), "text": text})
    if not blocks:
        raise ReaderQuickCheckError(f"section has no readable text: {section_id!r}")
    return {"section_id": section["id"], "label": section["label"], "blocks": blocks}


def author_quick_check(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    section_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author + persist one quick check for a section (idempotent).

    Any existing row for the section is reused — a ``dismissed`` newest row is
    the learner's durable "don't bring this back" and suppresses re-authoring.
    The model output is candidate-only: span citations are validated against
    the section's provided spans before anything is persisted."""

    existing = repository.latest_reader_authored_question(
        extraction_id=extraction_id, section_id=section_id
    )
    if existing is not None:
        return existing

    view = section_view(repository, extraction_id=extraction_id, section_id=section_id)

    from learnloop.reader.ai_contracts import READING_QUICK_CHECK_PROMPT_VERSION

    result = request_reading_quick_check(
        client,
        ReadingQuickCheckContext(extraction_id=extraction_id, section=view)
    )
    question_md = (result.question_md or "").strip()
    expected_answer_md = (result.expected_answer_md or "").strip()
    if not question_md or not expected_answer_md:
        raise ReaderQuickCheckError("the model returned an empty question or answer")
    valid_spans = {block["span_id"] for block in view["blocks"]}
    span_ids = [span_id for span_id in result.span_ids if span_id in valid_spans]
    if not span_ids:
        raise ReaderQuickCheckError(
            f"the model cited no valid section spans: {list(result.span_ids)!r}"
        )

    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    question_id = repository.insert_reader_authored_question(
        fields={
            "extraction_id": extraction_id,
            "section_id": section_id,
            "source_id": revision.get("source_id"),
            "question_md": question_md,
            "expected_answer_md": expected_answer_md,
            "span_ids": span_ids,
            "prompt_version": READING_QUICK_CHECK_PROMPT_VERSION,
            "provider": getattr(getattr(client, "config", None), "provider", None)
            or getattr(client, "provider_name", None),
            "model": getattr(getattr(client, "config", None), "model", None)
            or getattr(client, "model", None),
        },
        clock=clock,
    )
    row = repository.get_reader_authored_question(question_id)
    assert row is not None
    return row


def passage_view(
    repository: Repository, *, extraction_id: str, anchor_span_ids: list[str] | tuple[str, ...]
) -> dict[str, Any]:
    """The bounded view of one inquiry's root passage (RW1a): its anchor spans
    and up to ``PASSAGE_BLOCKS_BEFORE``/``AFTER`` neighbours, inside the anchor's
    guide section (the same section derivation as the guide plan).

    ``{section_id, label, scope: "passage", anchor_span_ids, blocks}``."""

    ir = repository.load_document_ir(extraction_id)
    if ir is None:
        raise ReaderQuickCheckError(f"extraction has no IR: {extraction_id!r}")
    section_rows, block_by_span, span_to_section = extraction_sections(ir)
    anchors = [span_id for span_id in dict.fromkeys(anchor_span_ids) if span_id in span_to_section]
    if not anchors:
        raise ReaderQuickCheckError(f"the passage has no readable anchor: {list(anchor_span_ids)!r}")
    section_id = span_to_section[anchors[0]]
    section = next(row for row in section_rows if row["id"] == section_id)
    order = list(section["span_ids"])
    anchors = [span_id for span_id in anchors if span_id in order]
    positions = [order.index(span_id) for span_id in anchors]
    window = order[max(0, min(positions) - PASSAGE_BLOCKS_BEFORE):max(positions) + 1 + PASSAGE_BLOCKS_AFTER]
    blocks: list[dict[str, str]] = []
    total_chars = 0
    for span_id in window:
        block = block_by_span[span_id]
        text = " ".join((block.text or "").split())
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_PASSAGE_CHARS and span_id not in anchors:
            continue
        blocks.append({"span_id": span_id, "kind": str(block.block_type or ""), "text": text})
    if not any(block["span_id"] in anchors for block in blocks):
        raise ReaderQuickCheckError("the passage has no readable text")
    return {
        "section_id": section_id,
        "label": section["label"],
        "scope": "passage",
        "anchor_span_ids": anchors,
        "blocks": blocks,
    }


def author_inquiry_quick_check(
    repository: Repository,
    client: Any,
    *,
    extraction_id: str,
    inquiry_root_event_id: str,
    anchor_span_ids: list[str] | tuple[str, ...],
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Author + persist the reconnect line's quick check for one inquiry (RW1a).

    Idempotent per (``inquiry_root_event_id``, prompt version): any existing
    row is reused, a dismissed one included. Formative only (W1 tier 2): the
    row is the record, answering it writes no attempt. Span citations are
    validated against the passage before anything is persisted."""

    existing = repository.inquiry_reader_authored_question(
        inquiry_root_event_id=inquiry_root_event_id, prompt_version=INQUIRY_PROMPT_VERSION
    )
    if existing is not None:
        return existing

    view = passage_view(repository, extraction_id=extraction_id, anchor_span_ids=anchor_span_ids)
    result = request_passage_check(
        client, ReadingQuickCheckContext(extraction_id=extraction_id, section=view)
    )
    question_md = (result.question_md or "").strip()
    expected_answer_md = (result.expected_answer_md or "").strip()
    if not question_md or not expected_answer_md:
        raise ReaderQuickCheckError("the model returned an empty question or answer")
    valid_spans = {block["span_id"] for block in view["blocks"]}
    span_ids = [span_id for span_id in result.span_ids if span_id in valid_spans]
    if not span_ids:
        raise ReaderQuickCheckError(
            f"the model cited no valid passage spans: {list(result.span_ids)!r}"
        )

    run = repository.get_extraction_run(extraction_id) or {}
    revision = repository.get_source_revision(str(run.get("revision_id") or "")) or {}
    question_id = repository.insert_reader_authored_question(
        fields={
            "extraction_id": extraction_id,
            "section_id": view["section_id"],
            "source_id": revision.get("source_id"),
            "question_md": question_md,
            "expected_answer_md": expected_answer_md,
            "span_ids": span_ids,
            "prompt_version": INQUIRY_PROMPT_VERSION,
            "provider": getattr(getattr(client, "config", None), "provider", None)
            or getattr(client, "provider_name", None),
            "model": getattr(getattr(client, "config", None), "model", None)
            or getattr(client, "model", None),
            "scope_kind": "inquiry",
            "question_style": "recall",
            "anchor_span_ids": view["anchor_span_ids"],
            "inquiry_root_event_id": inquiry_root_event_id,
        },
        clock=clock,
    )
    row = repository.get_reader_authored_question(question_id)
    assert row is not None
    return row


def record_inquiry_action(
    repository: Repository,
    *,
    question_id: str,
    action: str,
    response_md: str | None = None,
    self_check: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's act on an inquiry-scoped quick check (RW1a).

    ``answered`` stamps their response (the expected answer is then shown
    beside it); ``self_checked`` records their own verdict -- matches, partly
    or no -- in ``self_check``; ``dismissed`` is the durable "don't bring this
    back". Formative only: the row is updated in place and nothing else is
    written (no attempt, observation, mastery or FSRS row). A "partly" or "no"
    becomes reader_formative learner text in RW1b, not here."""

    if action not in INQUIRY_ACTIONS:
        raise ReaderQuickCheckError(f"unknown question action: {action!r}")
    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row.get("scope_kind") != "inquiry":
        raise ReaderQuickCheckError("not an inquiry quick check")
    if row["status"] == "escalated":
        raise ReaderQuickCheckError("this question was already added to practice")
    if action == "self_checked":
        if self_check not in SELF_CHECKS:
            raise ReaderQuickCheckError(f"unknown self-check: {self_check!r}")
        if row["status"] != "answered":
            raise ReaderQuickCheckError("answer the question before comparing")
        repository.transition_reader_authored_question(
            question_id=question_id, status="answered", self_check=self_check, clock=clock
        )
    elif action == "answered":
        response = (response_md or "").strip()
        if not response:
            raise ReaderQuickCheckError("an answer is needed to compare with the source")
        repository.transition_reader_authored_question(
            question_id=question_id, status="answered", response_md=response, clock=clock
        )
    else:
        repository.transition_reader_authored_question(
            question_id=question_id, status="dismissed", clock=clock
        )
    refreshed = repository.get_reader_authored_question(question_id)
    assert refreshed is not None
    return refreshed


def record_action(
    repository: Repository,
    *,
    question_id: str,
    action: str,
    response_md: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Record the learner's self-check outcome on the row (salience-only):
    ``answered`` stamps their response; ``dismissed`` is the durable
    "don't bring this back"."""

    if action not in QUESTION_ACTIONS:
        raise ReaderQuickCheckError(f"unknown question action: {action!r}")
    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row["status"] == "escalated":
        raise ReaderQuickCheckError("this question was already added to practice")
    repository.transition_reader_authored_question(
        question_id=question_id,
        status=action,
        response_md=(response_md or "").strip() or None,
        clock=clock,
    )
    refreshed = repository.get_reader_authored_question(question_id)
    assert refreshed is not None
    return refreshed


def escalate(
    root: Path,
    repository: Repository,
    *,
    question_id: str,
    learning_object_id: str,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Escalate an authored quick check into a real PracticeItem.

    A learner-authority write (no review gate — the learner collecting a
    prompt is the authority, per the Matuschak reader-control slice), but the
    provenance stays honest: ``origin="codex_proposal"`` with the question's
    span refs, so the card never masquerades as human-authored."""

    row = repository.get_reader_authored_question(question_id)
    if row is None:
        raise ReaderQuickCheckError(f"unknown authored question: {question_id!r}")
    if row["status"] == "escalated":
        return {"practice_item_id": row["practice_item_id"], "question": row}
    if row["status"] == "dismissed":
        raise ReaderQuickCheckError("a dismissed question cannot be added to practice")

    vault = load_vault(root)
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise ReaderQuickCheckError(f"unknown learning object {learning_object_id!r}")

    try:
        span_ids = json.loads(row.get("span_ids_json") or "[]")
    except (TypeError, json.JSONDecodeError):
        span_ids = []
    source_refs = [
        {
            "ref_type": "canonical_source",
            "ref_id": str(row.get("source_id") or row["extraction_id"]),
            "locator": format_block_span(row["extraction_id"], str(span_id)),
            "locator_scheme": BLOCK_SPAN_V1,
        }
        for span_id in span_ids
        if isinstance(span_id, str)
    ]
    now = utc_now_iso(clock)
    item_id = f"pi_reader_{new_ulid().lower()}"
    payload: dict[str, Any] = {
        "id": item_id,
        "learning_object_id": learning_object_id,
        "practice_mode": "short_answer",
        "attempt_types_allowed": ["independent_attempt"],
        "evidence_facets": [],
        "prompt": str(row["question_md"]),
        "expected_answer": str(row["expected_answer_md"]),
        "hints": [],
        # A card must always be gradable: same plain correctness rubric as
        # learner-authored cards, so grading never depends on a vault default.
        "grading_rubric": {
            "max_points": 4,
            "criteria": [
                {
                    "id": "correctness",
                    "points": 4,
                    "description": "Answer matches the expected answer in substance.",
                }
            ],
        },
        "provenance": {"origin": "codex_proposal", "source_refs": source_refs},
        "created_at": now,
        "updated_at": now,
    }
    upsert_practice_item(root, payload, clock=clock)
    repository.transition_reader_authored_question(
        question_id=question_id, status="escalated", practice_item_id=item_id, clock=clock
    )
    try:
        repository.append_interaction_event(
            kind="learner_item_authored",
            origin="learner",
            subject_type="practice_item",
            subject_id=item_id,
            payload_json=json.dumps(
                {
                    "learning_object_id": learning_object_id,
                    "escalated_from": question_id,
                    "mechanism": "reader_quick_check_escalation",
                },
                sort_keys=True,
            ),
            clock=clock,
        )
    except Exception:  # noqa: BLE001 - provenance trail is best-effort
        pass
    refreshed = repository.get_reader_authored_question(question_id)
    return {"practice_item_id": item_id, "question": refreshed or row}
