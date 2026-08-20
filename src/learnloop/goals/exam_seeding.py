"""Exam seeding: import a past practice exam's per-question outcomes.

Two halves:

1. ``exam_ingest_instructions`` builds the exam-specific canonical-ingestor
   instructions used by ``learnloop ingest-exam`` (a thin wrapper over
   ``ingest_canonical_source``): one practice item per exam question, tagged
   ``exam_q:<n>`` + ``exam_question``.
2. ``seed_exam_attempts`` turns a learner-supplied outcomes file into
   backdated, discounted ``exam_evidence`` attempts through the normal
   deterministic belief pipeline (``apply_attempt`` with a ``FrozenClock``),
   then replays the affected learning objects so FSRS/mastery are recomputed
   in ``created_at`` order.

Design notes:

- Grading path: ``complete_self_graded_attempt`` maps learner confidence 1-5
  onto grader_confidence {0.2, 0.4, 0.6, 0.8, 1.0}, which cannot represent the
  configured ``exam_seeding.grader_confidence`` (default 0.7). Seeding
  therefore synthesizes a ``ResolvedGrade`` directly and calls
  ``apply_attempt`` — the same shared step used by live recording and replay.
  No ``attempt_feedback_metadata`` row is written (that table's
  ``grading_source`` CHECK only knows codex|ai|self and the row is a
  presentation concern, not part of the belief pipeline).
- Rounding: each rubric criterion is awarded ``score * criterion.points``
  rounded to 2 decimals, so total/max matches the reported score fraction to
  within 0.005 per criterion. The integer ``rubric_score`` then follows the
  standard ``int(round(sum))`` rule shared with self-grading, so LO-level
  correctness is quantized to the rubric scale while facet evidence keeps the
  exact fraction.
- Idempotency key: (practice item, exam date) — an item is skipped when it
  already has an ``exam_evidence`` attempt whose ``created_at`` date equals
  the exam date.
- Timestamps: seeded attempts are stamped at 12:00:00 UTC on the exam date
  plus ``index`` seconds in ascending question order, so created_at ordering
  is stable and deterministic across runs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any, Mapping

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.attempts.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    ResolvedGrade,
    calculate_rubric_score,
    apply_attempt,
)
from learnloop.attempts.grading import resolved_rubric
from learnloop.substrate.replay import RebuildResult, rebuild_derived_state
from learnloop.vault.models import LoadedVault, PracticeItem

EXAM_ATTEMPT_TYPE = "exam_evidence"
EXAM_QUESTION_TAG = "exam_question"
EXAM_QUESTION_TAG_PREFIX = "exam_q:"

# Seeded attempts land at noon UTC on the exam date, one second apart per
# question, so replay order is deterministic and unambiguous.
_EXAM_SEED_HOUR_UTC = 12


class ExamSeedingError(ValueError):
    pass


def exam_ingest_instructions(extra_instructions: str | None = None) -> str:
    """Canonical-ingestor instructions for ingesting a past practice exam."""

    base = (
        "This source is a past practice exam. Treat every exam question as one "
        "assessable unit:\n"
        "- Produce exactly one practice_item per exam question, in the order the "
        "questions appear in the source. Do not merge, split, or invent questions.\n"
        f"- Tag each practice_item with '{EXAM_QUESTION_TAG_PREFIX}<n>' where <n> is the "
        "question number as printed on the exam (1, 2, 3, ...), plus the tag "
        f"'{EXAM_QUESTION_TAG}'.\n"
        "- Give every practice_item a grading_rubric (criteria with points that sum to "
        "max_points), evidence_facets, and evidence_weights reflecting what the "
        "question actually tests.\n"
        "- Link each practice_item to an existing learning_object when one matches; "
        "otherwise propose the learning_object (and concept if needed) alongside it.\n"
        "- Set attempt_types_allowed to the live modes a learner would use to retry the "
        "question (for example independent_attempt, dont_know); the exam-import "
        "attempt type is added by the system, not by you.\n"
        "- Keep the question's own wording as the prompt and the model solution (or "
        "marking guide) as the expected_answer."
    )
    if extra_instructions and extra_instructions.strip():
        return f"{base}\n\nAdditional instructions from the learner:\n{extra_instructions.strip()}"
    return base


@dataclass(frozen=True)
class ExamOutcome:
    question: str
    score: float
    answer_md: str | None = None
    confidence: int | None = None


@dataclass(frozen=True)
class ExamOutcomesFile:
    exam_date: date
    outcomes: dict[str, ExamOutcome]


@dataclass(frozen=True)
class ExamSeedEntry:
    question: str
    practice_item_id: str
    status: str  # "seeded" | "skipped_existing" | "no_outcome" | "would_seed"
    attempt_id: str | None = None
    learning_object_id: str | None = None
    score: float | None = None
    rubric_score: int | None = None
    correctness: float | None = None
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "practice_item_id": self.practice_item_id,
            "status": self.status,
            "attempt_id": self.attempt_id,
            "learning_object_id": self.learning_object_id,
            "score": self.score,
            "rubric_score": self.rubric_score,
            "correctness": self.correctness,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ExamSeedingResult:
    exam_date: str
    dry_run: bool
    entries: list[ExamSeedEntry]
    seeded_count: int
    skipped_existing_count: int
    no_outcome_count: int
    rebuild: RebuildResult | None = None
    rebuilt_learning_object_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "exam_date": self.exam_date,
            "dry_run": self.dry_run,
            "entries": [entry.as_dict() for entry in self.entries],
            "seeded_count": self.seeded_count,
            "skipped_existing_count": self.skipped_existing_count,
            "no_outcome_count": self.no_outcome_count,
            "rebuild": self.rebuild.as_dict() if self.rebuild is not None else None,
            "rebuilt_learning_object_ids": self.rebuilt_learning_object_ids,
        }


def parse_exam_outcomes(
    payload: Mapping[str, Any],
    *,
    exam_date_override: str | None = None,
) -> ExamOutcomesFile:
    """Parse an outcomes file payload.

    Accepts either the canonical shape ``{"exam_date": "YYYY-MM-DD",
    "outcomes": {"1": {"score": 0.5, ...}, ...}}`` or, for convenience, a flat
    top-level mapping of question -> outcome. Outcome values may be a mapping
    with ``score`` (required, fraction 0..1), optional ``answer_md`` and
    ``confidence`` (1-5), or a bare number treated as the score.
    """

    raw_outcomes: Mapping[str, Any]
    raw_date: Any = exam_date_override
    if "outcomes" in payload and isinstance(payload.get("outcomes"), Mapping):
        raw_outcomes = payload["outcomes"]
        if raw_date is None:
            raw_date = payload.get("exam_date")
    else:
        unexpected = payload.get("exam_date")
        raw_outcomes = {key: value for key, value in payload.items() if key != "exam_date"}
        if raw_date is None:
            raw_date = unexpected
    if raw_date is None:
        raise ExamSeedingError(
            "exam date is required: provide \"exam_date\" in the outcomes file or pass --exam-date"
        )
    try:
        exam_date = date.fromisoformat(str(raw_date))
    except ValueError as exc:
        raise ExamSeedingError(f"invalid exam date {raw_date!r}: expected YYYY-MM-DD") from exc
    if not raw_outcomes:
        raise ExamSeedingError("outcomes file contains no question outcomes")
    outcomes: dict[str, ExamOutcome] = {}
    for question, value in raw_outcomes.items():
        key = str(question).strip()
        if not key:
            raise ExamSeedingError("outcome keys must be non-empty question numbers")
        if isinstance(value, Mapping):
            if "score" not in value:
                raise ExamSeedingError(f"outcome for question {key} is missing \"score\"")
            score = _validated_score(key, value["score"])
            answer_md = value.get("answer_md")
            confidence = value.get("confidence")
            if confidence is not None:
                confidence = int(confidence)
                if not 1 <= confidence <= 5:
                    raise ExamSeedingError(f"confidence for question {key} must be between 1 and 5")
            outcomes[key] = ExamOutcome(
                question=key,
                score=score,
                answer_md=str(answer_md) if answer_md is not None else None,
                confidence=confidence,
            )
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            outcomes[key] = ExamOutcome(question=key, score=_validated_score(key, value))
        else:
            raise ExamSeedingError(
                f"outcome for question {key} must be a mapping with \"score\" or a bare number"
            )
    return ExamOutcomesFile(exam_date=exam_date, outcomes=outcomes)


def _validated_score(question: str, value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError) as exc:
        raise ExamSeedingError(f"score for question {question} must be numeric") from exc
    if not 0.0 <= score <= 1.0:
        raise ExamSeedingError(f"score for question {question} must be a fraction between 0 and 1")
    return score


def exam_question_from_tags(item: PracticeItem) -> str | None:
    for tag in item.tags:
        if tag.startswith(EXAM_QUESTION_TAG_PREFIX):
            question = tag[len(EXAM_QUESTION_TAG_PREFIX):].strip()
            if question:
                return question
    return None


def find_exam_items(vault: LoadedVault, *, subject: str | None = None) -> dict[str, PracticeItem]:
    """Map exam question number -> practice item (tagged ``exam_q:<n>``)."""

    items: dict[str, PracticeItem] = {}
    for item in sorted(vault.practice_items.values(), key=lambda entry: entry.id):
        question = exam_question_from_tags(item)
        if question is None:
            continue
        if subject is not None and subject not in vault.subjects_for_item(item):
            continue
        existing = items.get(question)
        if existing is not None:
            raise ExamSeedingError(
                f"multiple practice items tagged {EXAM_QUESTION_TAG_PREFIX}{question}: "
                f"{existing.id}, {item.id}"
            )
        items[question] = item
    return items


def _question_sort_key(question: str) -> tuple[int, float | str, str]:
    match = re.match(r"^(\d+)", question)
    if match:
        return (0, int(match.group(1)), question)
    return (1, question, question)


def _has_exam_attempt_on_date(repository: Repository, practice_item_id: str, exam_date: date) -> bool:
    prefix = exam_date.isoformat()
    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1000)
    return any(
        attempt.get("attempt_type") == EXAM_ATTEMPT_TYPE
        and str(attempt.get("created_at") or "").startswith(prefix)
        for attempt in attempts
    )


def seed_exam_attempts(
    vault: LoadedVault,
    repository: Repository,
    *,
    outcomes: ExamOutcomesFile,
    subject: str | None = None,
    dry_run: bool = False,
) -> ExamSeedingResult:
    """Seed backdated ``exam_evidence`` attempts from per-question outcomes.

    Raises :class:`ExamSeedingError` when an outcome key does not match any
    ``exam_q:<n>``-tagged practice item. Exam items with no outcome are
    reported as warnings and skipped.
    """

    exam_items = find_exam_items(vault, subject=subject)
    if not exam_items:
        scope = f" in subject {subject}" if subject else ""
        raise ExamSeedingError(
            f"no practice items tagged {EXAM_QUESTION_TAG_PREFIX}<n> found{scope}; "
            "run `learnloop ingest-exam` and accept the proposal first"
        )
    unmatched = sorted(set(outcomes.outcomes) - set(exam_items), key=_question_sort_key)
    if unmatched:
        raise ExamSeedingError(
            "outcome keys with no matching exam item (expected practice items tagged "
            f"{EXAM_QUESTION_TAG_PREFIX}<n>): {', '.join(unmatched)}"
        )

    config = vault.config.exam_seeding
    base_instant = datetime(
        outcomes.exam_date.year,
        outcomes.exam_date.month,
        outcomes.exam_date.day,
        _EXAM_SEED_HOUR_UTC,
        0,
        0,
        tzinfo=UTC,
    )
    entries: list[ExamSeedEntry] = []
    affected_learning_objects: list[str] = []
    seeded = skipped = missing = 0
    for index, question in enumerate(sorted(exam_items, key=_question_sort_key)):
        item = exam_items[question]
        outcome = outcomes.outcomes.get(question)
        if outcome is None:
            missing += 1
            entries.append(
                ExamSeedEntry(
                    question=question,
                    practice_item_id=item.id,
                    status="no_outcome",
                    detail="exam item has no outcome in the outcomes file; skipped",
                )
            )
            continue
        if _has_exam_attempt_on_date(repository, item.id, outcomes.exam_date):
            skipped += 1
            entries.append(
                ExamSeedEntry(
                    question=question,
                    practice_item_id=item.id,
                    status="skipped_existing",
                    score=outcome.score,
                    detail=(
                        f"already has an {EXAM_ATTEMPT_TYPE} attempt dated "
                        f"{outcomes.exam_date.isoformat()}"
                    ),
                )
            )
            continue
        rubric = resolved_rubric(vault, item)
        criterion_points = {
            criterion.id: round(outcome.score * float(criterion.points), 2)
            for criterion in rubric.criteria
        }
        rubric_score = calculate_rubric_score(rubric, criterion_points, [])
        if dry_run:
            seeded += 1
            entries.append(
                ExamSeedEntry(
                    question=question,
                    practice_item_id=item.id,
                    status="would_seed",
                    learning_object_id=item.learning_object_id,
                    score=outcome.score,
                    rubric_score=rubric_score,
                )
            )
            continue
        clock = FrozenClock(base_instant + timedelta(seconds=index))
        now_iso = clock.now().replace(microsecond=0).isoformat().replace("+00:00", "Z")
        attempt_id = new_ulid()
        confidence = outcome.confidence if outcome.confidence is not None else config.default_learner_confidence
        answer_md = outcome.answer_md or f"[imported exam outcome: score {outcome.score:.2f}]"
        evidence_rows = [
            {
                "id": new_ulid(),
                "criterion_id": criterion.id,
                "points_awarded": criterion_points[criterion.id],
                "evidence": (
                    f"Imported exam outcome ({outcomes.exam_date.isoformat()}): "
                    f"{criterion_points[criterion.id]:g}/{criterion.points:g} "
                    f"(score {outcome.score:.2f})."
                ),
                "notes": None,
                "local_grader_id": "exam_import",
                "grader_tier": 1,
                "learner_confidence": "hedged" if confidence <= 2 else "confident",
                "created_at": now_iso,
            }
            for criterion in rubric.criteria
        ]
        grade = ResolvedGrade(
            rubric_score=rubric_score,
            criterion_points=criterion_points,
            evidence_rows=evidence_rows,
            error_attributions=[],
            grader_confidence=config.grader_confidence,
            confidence=confidence,
            manual_review_reason=None,
        )
        draft = AttemptDraft(
            practice_item_id=item.id,
            learner_answer_md=answer_md,
            attempt_type=EXAM_ATTEMPT_TYPE,
            hints_used=0,
        )
        result = apply_attempt(
            vault,
            repository,
            ApplyAttemptInput(draft=draft, attempt_id=attempt_id, grade=grade),
            clock=clock,
        )
        seeded += 1
        if result.learning_object_id not in affected_learning_objects:
            affected_learning_objects.append(result.learning_object_id)
        entries.append(
            ExamSeedEntry(
                question=question,
                practice_item_id=item.id,
                status="seeded",
                attempt_id=result.attempt_id,
                learning_object_id=result.learning_object_id,
                score=outcome.score,
                rubric_score=result.rubric_score,
                correctness=result.correctness,
            )
        )

    rebuild: RebuildResult | None = None
    if not dry_run and affected_learning_objects:
        # Seeded attempts are backdated, so FSRS elapsed-days and mastery drift
        # must be recomputed by replaying every attempt in created_at order.
        rebuild = rebuild_derived_state(
            vault,
            repository,
            learning_object_ids=affected_learning_objects,
        )
    return ExamSeedingResult(
        exam_date=outcomes.exam_date.isoformat(),
        dry_run=dry_run,
        entries=entries,
        seeded_count=seeded,
        skipped_existing_count=skipped,
        no_outcome_count=missing,
        rebuild=rebuild,
        rebuilt_learning_object_ids=list(affected_learning_objects),
    )
