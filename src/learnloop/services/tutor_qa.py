"""Tutor Q&A ("ask"): classified learner questions in three contexts.

Design decisions (agreed spec):

- **Uncertainty is read-side.** Questions never write facet_uncertainty rows or
  touch mastery means. Because ``question_events`` persist, the effect is
  derivable at read time: ``mastery_diagnostic_view`` folds recent unresolved
  questions about a facet into that facet's displayed uncertainty/state as a
  bounded bump (see ``facet_diagnostics.unresolved_question_facet_counts``).
  This is simpler than a write-side update, cannot drift from a
  rebuild-derived-state replay, and reaches every consumer of the diagnostic
  view (facet radar, diagnostics) without new plumbing.
- **Hint equivalence.** Substantive mid-attempt questions (prerequisite,
  mechanism, strategy) are hint-equivalents; clarification, verification, and
  other are free. The sidecar submit path counts hint-equivalent question
  events for the (practice item, session) newer than the previous attempt on
  the item and adds them to the UI hint count, flowing through the existing
  hint dampening / FSRS rating caps.
- **Guardrails.** The practice prompt forbids stating the answer, completing
  the derivation, or confirming/denying the learner's approach; verification
  questions are deflected with a guiding question. A post-hoc leak check flags
  (never blocks) answers that overlap the expected answer.
- **Two-phase persistence.** The question row is inserted with
  ``answer_status='pending'`` before the provider call and updated to
  ``answered`` (with classification) or ``failed`` after. Asking is
  elicitation evidence about the learner's knowledge state, so a tutor outage
  must not erase the question. Only ``answered`` turns consume the Q&A budget
  or appear in transcripts/threads; each turn records a ``tutor_qa``
  agent_run for observability.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any, Mapping

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.codex.client import TutorQAContext
from learnloop.codex.prompts import TUTOR_QA_PROMPT_VERSION
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.facet_diagnostics import required_facets
from learnloop.vault.loader import add_note
from learnloop.vault.models import LoadedVault, PracticeItem

QUESTION_CONTEXTS = ("library", "practice", "feedback")

# question_type → counts as a hint. Substantive content help is a hint;
# clarifying the prompt, asking "am I right?" (which the tutor deflects), or
# off-topic chatter is not.
HINT_EQUIVALENT_TYPES = frozenset({"prerequisite", "mechanism", "strategy"})

_LEAK_MIN_TOKENS = 3
_LEAK_OVERLAP_THRESHOLD = 0.8


class TutorQAError(ValueError):
    pass


@dataclass(frozen=True)
class QuestionLimitReached(Exception):
    context: str
    limit: int
    used: int

    def __str__(self) -> str:
        return (
            f"Question limit reached for this {self.context} context "
            f"({self.used}/{self.limit})."
        )


def question_usage(
    vault: LoadedVault,
    repository: Repository,
    *,
    context: str,
    practice_item_id: str | None = None,
    attempt_id: str | None = None,
    note_id: str | None = None,
    session_id: str | None = None,
    clock: Clock | None = None,
) -> tuple[int, int]:
    """(used, limit) for one Q&A budget window.

    practice: per (practice item, session); feedback: per attempt; library:
    per note per UTC day."""

    config = vault.config.tutor_qa
    # Only answered turns consume budget: a provider failure (answer_status
    # 'failed'/'pending') keeps the question on record without charging for it.
    if context == "practice":
        used = repository.count_question_events(
            context="practice",
            practice_item_id=practice_item_id,
            session_id=session_id,
            answer_status="answered",
        )
        return used, config.max_questions_practice
    if context == "feedback":
        used = repository.count_question_events(
            context="feedback", attempt_id=attempt_id, answer_status="answered"
        )
        return used, config.max_questions_feedback
    if context == "library":
        now = parse_utc(utc_now_iso(clock))
        day_start = now.strftime("%Y-%m-%dT00:00:00Z")
        used = repository.count_question_events(
            context="library", note_id=note_id, since=day_start, answer_status="answered"
        )
        return used, config.max_questions_library
    raise TutorQAError(f"Unknown question context {context!r}")


def ask_question(
    vault: LoadedVault,
    repository: Repository,
    client: Any,
    *,
    context: str,
    question_md: str,
    practice_item_id: str | None = None,
    attempt_id: str | None = None,
    note_id: str | None = None,
    session_id: str | None = None,
    seconds_into_attempt: float | None = None,
    question_context: Mapping[str, Any] | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """``question_context`` carries the §13.4 generating-process fields
    (preceding_tutor_move, scaffold_level, warning_state, learner_mode,
    question_opportunity, hints_used_before, direct_explanation_request,
    attempt_progress). They are persisted verbatim for later contextual
    likelihood calibration; unknown keys are ignored."""

    if context not in QUESTION_CONTEXTS:
        raise TutorQAError(f"Unknown question context {context!r}")
    if not question_md.strip():
        raise TutorQAError("Question must not be empty.")

    item: PracticeItem | None = None
    attempt: dict[str, Any] | None = None
    note = None

    if context == "feedback":
        if attempt_id is None:
            raise TutorQAError("Feedback questions require attempt_id.")
        attempt = repository.fetch_practice_attempt(attempt_id)
        if attempt is None:
            raise TutorQAError(f"Attempt {attempt_id} was not found.")
        practice_item_id = practice_item_id or attempt["practice_item_id"]
    if context in {"practice", "feedback"}:
        if practice_item_id is None:
            raise TutorQAError(f"{context} questions require practice_item_id.")
        item = vault.practice_items.get(practice_item_id)
        if item is None:
            raise TutorQAError(f"Practice item {practice_item_id} was not found.")
    if context == "library":
        if note_id is None:
            raise TutorQAError("Library questions require note_id.")
        note = vault.notes.get(note_id)
        if note is None:
            raise TutorQAError(f"Note {note_id} was not found.")

    used, limit = question_usage(
        vault,
        repository,
        context=context,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        note_id=note_id,
        session_id=session_id,
        clock=clock,
    )
    if used >= limit:
        raise QuestionLimitReached(context=context, limit=limit, used=used)

    candidates = _candidate_facets(vault, repository, context, item=item, note=note)
    thread = _thread(
        repository,
        context=context,
        practice_item_id=practice_item_id,
        attempt_id=attempt_id,
        note_id=note_id,
        session_id=session_id,
    )
    ai_context = _build_context(
        vault,
        repository,
        context=context,
        question_md=question_md,
        candidates=candidates,
        thread=thread,
        item=item,
        attempt=attempt,
        note=note,
        note_id=note_id,
    )

    # Two-phase write: the question row lands BEFORE the provider call. The
    # learner asking is elicitation evidence about their knowledge state
    # regardless of whether the tutor manages to answer, so a provider failure
    # must not erase it (classification arrives with the answer, or never).
    qc = dict(question_context or {})
    event_id = repository.insert_question_event(
        {
            "context": context,
            "note_id": note_id,
            "practice_item_id": practice_item_id,
            "attempt_id": attempt_id,
            "session_id": session_id,
            "question_md": question_md,
            "answer_status": "pending",
            "seconds_into_attempt": seconds_into_attempt,
            "provider": getattr(client, "provider_name", None),
            # §13.4 generating-process context, persisted for later contextual
            # likelihood calibration.
            "preceding_tutor_move": qc.get("preceding_tutor_move"),
            "scaffold_level": qc.get("scaffold_level"),
            "warning_state": qc.get("warning_state"),
            "learner_mode": qc.get("learner_mode"),
            "question_opportunity": qc.get("question_opportunity"),
            "hints_used_before": qc.get("hints_used_before"),
            "direct_explanation_request": bool(qc.get("direct_explanation_request")),
            "attempt_progress": qc.get("attempt_progress"),
        },
        clock=clock,
    )
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "tutor_qa",
            "provider": getattr(client, "provider_name", None) or "codex",
            "provider_type": getattr(client, "provider_type", None),
            "model": getattr(client, "model", None),
            "prompt_template": "tutor_qa",
            "prompt_version": TUTOR_QA_PROMPT_VERSION,
            "input_context_hash": _tutor_context_hash(ai_context),
            "output_schema": "TutorAnswer",
            "started_at": utc_now_iso(clock),
            "status": "running",
        }
    )
    try:
        answer = client.run_tutor_qa(ai_context)
    except Exception as exc:
        repository.complete_agent_run(agent_run_id, status="failed", error_message=str(exc), clock=clock)
        repository.update_question_event_answer(
            event_id,
            answer_md=None,
            question_type=None,
            facets=None,
            hint_equivalent=False,
            leak_suspected=False,
            answer_status="failed",
        )
        raise
    repository.complete_agent_run(agent_run_id, status="completed", clock=clock)

    facets = sorted(
        {vault.canonical_facet_id(str(facet)) for facet in answer.facets}
        & set(candidates)
    )
    hint_equivalent = context == "practice" and answer.question_type in HINT_EQUIVALENT_TYPES
    leak_suspected = (
        context == "practice"
        and item is not None
        and answer_leaks_expected(answer.answer_md, item.expected_answer)
    )
    # §13.4 channel: an explicit direct-explanation request is
    # interaction-preference by construction, whatever the classifier said.
    signal_channel = (
        "interaction_preference"
        if qc.get("direct_explanation_request")
        else getattr(answer, "question_channel", None) or "epistemic"
    )

    repository.update_question_event_answer(
        event_id,
        answer_md=answer.answer_md,
        question_type=answer.question_type,
        facets=facets,
        hint_equivalent=hint_equivalent,
        leak_suspected=leak_suspected,
        answer_status="answered",
        signal_channel=signal_channel,
    )

    # Feedback wiring: a post-grade question about facet X is a signal the
    # existing intervention need (if any) should also target X.
    if context == "feedback" and facets and attempt_id is not None:
        need = repository.intervention_need_for_attempt(attempt_id)
        if need is not None and need.get("status") == "pending":
            repository.append_intervention_need_target_facets(need["id"], facets, clock=clock)

    return {
        "event_id": event_id,
        "answer_md": answer.answer_md,
        "question_type": answer.question_type,
        "signal_channel": signal_channel,
        "facets": facets,
        "hint_equivalent": hint_equivalent,
        "leak_suspected": leak_suspected,
        "remaining": max(0, limit - used - 1),
    }


def hint_equivalents_for_submission(
    repository: Repository,
    practice_item_id: str,
    session_id: str | None,
    *,
    until: str | None = None,
) -> int:
    """Hint-equivalent questions since the item was last attempted.

    Window start = created_at of the most recent prior attempt on the item
    (questions asked before an already-graded attempt were already dampened
    into that attempt's evidence)."""

    attempts = repository.list_recent_attempts_by_practice_item(practice_item_id, limit=1)
    since = attempts[0]["created_at"] if attempts else None
    return repository.count_hint_equivalent_question_events(
        practice_item_id, session_id, since=since, until=until
    )


def hint_equivalents_for_attempt(repository: Repository, attempt: dict[str, Any]) -> int:
    """Reconstruct a graded attempt's question-hint count from persisted rows.

    Same window as ``hint_equivalents_for_submission``, evaluated post hoc:
    questions on (item, session) after the previous attempt on the item and at
    or before this attempt."""

    prior = [
        row
        for row in repository.list_recent_attempts_by_practice_item(
            attempt["practice_item_id"], limit=50
        )
        if (row["created_at"], row.get("id", "")) < (attempt["created_at"], attempt.get("id", ""))
    ]
    since = max((row["created_at"] for row in prior), default=None)
    return repository.count_hint_equivalent_question_events(
        attempt["practice_item_id"],
        attempt.get("session_id"),
        since=since,
        until=attempt["created_at"],
    )


def answer_leaks_expected(answer_md: str, expected_answer: str | dict[str, Any]) -> bool:
    """Heuristic answer-leak telemetry for the practice context.

    Normalized-substring or high token overlap between the tutor's answer and
    the item's expected answer. Flags, never blocks."""

    expected_text = (
        expected_answer if isinstance(expected_answer, str) else json.dumps(expected_answer, sort_keys=True)
    )
    answer_norm = _normalize(answer_md)
    expected_norm = _normalize(expected_text)
    if not expected_norm or not answer_norm:
        return False
    if len(expected_norm) >= 12 and expected_norm in answer_norm:
        return True
    expected_tokens = {token for token in expected_norm.split() if len(token) > 2}
    if len(expected_tokens) < _LEAK_MIN_TOKENS:
        return False
    answer_tokens = {token for token in answer_norm.split() if len(token) > 2}
    overlap = len(expected_tokens & answer_tokens) / len(expected_tokens)
    return overlap >= _LEAK_OVERLAP_THRESHOLD


def tutor_qa_note_title(question_md: str) -> str:
    text = " ".join(question_md.split())
    if len(text) <= 60:
        return text
    return text[:59].rstrip() + "…"


def build_tutor_qa_note(
    vault: LoadedVault,
    repository: Repository,
    event: Mapping[str, Any],
    *,
    subject_id: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Materialize a tutor Q&A turn as a vault note and persist the back-link.

    Shared by the ``save_tutor_answer_note`` handler and the promotion
    pipeline's grounding step (spec_tutor_promotion.md §3 Step 1). Idempotent:
    if the event already carries a ``saved_note_id`` the existing note is
    returned unchanged (``reused=True``) without writing a duplicate;
    otherwise the note is written, the ``question_events.saved_note_id``
    back-link is persisted via ``set_question_event_saved_note``, and the
    created note is returned (``reused=False``).

    The note body carries the full turn (learner question + tutor answer, which
    contains the socratic question) and its ``related_los``/subject are resolved
    from the event's practice item or source note. The caller is responsible for
    reloading the vault so a newly created note becomes visible. Raises
    ``TutorQAError`` when no subject can be resolved to file the note under.
    """

    existing_note_id = event.get("saved_note_id")
    if existing_note_id:
        return {"note_id": existing_note_id, "path": None, "reused": True}

    related_los: list[str] = []
    subjects: list[str] = []
    item_id = event.get("practice_item_id")
    if item_id is not None:
        item = vault.practice_items.get(item_id)
        if item is not None:
            related_los.append(item.learning_object_id)
            subjects = vault.subjects_for_item(item)
    source_note_id = event.get("note_id")
    if source_note_id is not None:
        source_note = vault.notes.get(source_note_id)
        if source_note is not None:
            related_los.extend(source_note.related_los)
            subjects = subjects or list(source_note.subjects)

    resolved_subject = subject_id or (subjects[0] if subjects else None)
    if resolved_subject is None and vault.subjects:
        resolved_subject = sorted(vault.subjects)[0]
    if resolved_subject is None:
        raise TutorQAError("No subject available to file the note under.")

    title = tutor_qa_note_title(event["question_md"])
    body = (
        f"**Q ({event['context']}):** {event['question_md'].strip()}\n\n"
        f"**A:** {(event.get('answer_md') or '').strip()}\n"
    )
    path = add_note(
        vault.root,
        resolved_subject,
        f"tutor_qa_{new_ulid().lower()}",
        title,
        body,
        related_los=sorted(set(related_los)),
        clock=clock,
    )
    note_id = path.stem
    repository.set_question_event_saved_note(str(event["id"]), note_id)
    return {"note_id": note_id, "path": str(path), "reused": False}


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def _candidate_facets(
    vault: LoadedVault,
    repository: Repository,
    context: str,
    *,
    item: PracticeItem | None,
    note,
) -> list[str]:
    facets: set[str] = set()
    if item is not None:
        facets.update(str(facet) for facet in item.evidence_facets)
        facets.update(required_facets(vault, item.learning_object_id, repository))
    if context == "library" and note is not None:
        for lo_id in note.related_los:
            facets.update(required_facets(vault, lo_id, repository))
    return sorted({vault.canonical_facet_id(facet) for facet in facets})


def _thread(
    repository: Repository,
    *,
    context: str,
    practice_item_id: str | None,
    attempt_id: str | None,
    note_id: str | None,
    session_id: str | None,
) -> list[dict[str, Any]]:
    if context == "practice":
        events = repository.question_events(
            context="practice",
            practice_item_id=practice_item_id,
            session_id=session_id,
            answer_status="answered",
        )
    elif context == "feedback":
        events = repository.question_events(
            context="feedback", attempt_id=attempt_id, answer_status="answered"
        )
    else:
        events = repository.question_events(
            context="library", note_id=note_id, answer_status="answered"
        )
    return [
        {
            "question_md": event["question_md"],
            "answer_md": event["answer_md"],
            "question_type": event["question_type"],
        }
        for event in events
    ]


def _tutor_context_hash(context: TutorQAContext) -> str:
    payload = json.dumps(asdict(context), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _build_context(
    vault: LoadedVault,
    repository: Repository,
    *,
    context: str,
    question_md: str,
    candidates: list[str],
    thread: list[dict[str, Any]],
    item: PracticeItem | None,
    attempt: dict[str, Any] | None,
    note,
    note_id: str | None,
) -> TutorQAContext:
    lo_summaries: list[dict[str, Any]] = []
    lo_ids: list[str] = []
    if item is not None:
        lo_ids = [item.learning_object_id]
    elif note is not None:
        lo_ids = list(note.related_los)
    for lo_id in lo_ids:
        lo = vault.learning_objects.get(lo_id)
        if lo is not None:
            lo_summaries.append({"id": lo.id, "title": lo.title, "summary": lo.summary})

    rubric = vault.rubric_for_item(item) if item is not None else None
    expected = None
    if item is not None:
        expected = (
            item.expected_answer
            if isinstance(item.expected_answer, str)
            else json.dumps(item.expected_answer, sort_keys=True)
        )

    learner_answer = None
    grading_feedback = None
    if context == "feedback" and attempt is not None:
        learner_answer = attempt.get("learner_answer_md")
        metadata = repository.fetch_attempt_feedback_metadata(attempt["id"]) or {}
        grading_feedback = {
            "rubric_score": attempt.get("rubric_score"),
            "correctness": attempt.get("correctness"),
            "feedback_md": metadata.get("feedback_md"),
            "fatal_errors": metadata.get("fatal_errors") or [],
            "criterion_evidence": [
                {
                    "criterion_id": row.get("criterion_id"),
                    "points_awarded": row.get("points_awarded"),
                    "evidence": row.get("evidence"),
                }
                for row in _grading_evidence_rows(repository, attempt["id"])
            ],
        }

    return TutorQAContext(
        context=context,
        question_md=question_md,
        candidate_facets=candidates,
        thread=thread,
        practice_item_prompt=item.prompt if item is not None else None,
        expected_answer=expected,
        rubric=rubric.model_dump() if rubric is not None else None,
        learner_answer_md=learner_answer,
        grading_feedback=grading_feedback,
        note_title=note_id,
        note_body=note.body if note is not None else None,
        learning_object_summaries=lo_summaries,
        diagnostic_decision=_diagnostic_decision_for(repository, item, context),
    )


def _diagnostic_decision_for(
    repository: Repository, item: PracticeItem | None, context: str
) -> dict[str, Any] | None:
    """The §12.1 typed transition decision steering post-diagnosis tutoring.

    Attached only when the item's LO has no open episode (measurement has
    ended — attaching it mid-measurement would lift the no-reveal guardrail
    while a block is still measuring) and the latest closed episode persisted
    a decision on its way into tutoring.
    """

    if item is None or context not in ("practice", "feedback"):
        return None
    lo_id = item.learning_object_id
    if repository.open_probe_episode(lo_id) is not None:
        return None
    for episode in reversed(repository.probe_episodes_for_learning_object(lo_id)):
        if episode.status in ("complete", "converted_to_tutoring") and episode.target_decision:
            return dict(episode.target_decision)
    return None


def _grading_evidence_rows(repository: Repository, attempt_id: str) -> list[dict[str, Any]]:
    rows = repository.fetch_grading_evidence(attempt_id)
    normalized: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            normalized.append(row)
        else:
            normalized.append(
                {
                    "criterion_id": getattr(row, "criterion_id", None),
                    "points_awarded": getattr(row, "points_awarded", None),
                    "evidence": getattr(row, "evidence", None),
                }
            )
    return normalized
