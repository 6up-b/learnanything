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
- **Hint equivalence.** Substantive questions (prerequisite, mechanism,
  strategy) about a bound practice item are hint-equivalents; clarification,
  verification, and other are free. This follows the ITEM, not the surface —
  a feedback-screen question counts for the next attempt exactly as a
  mid-attempt one does. The sidecar submit path counts hint-equivalent
  question events for the (practice item, session) newer than the previous
  attempt on the item and adds them to the UI hint count, flowing through the
  existing hint dampening / FSRS rating caps.
- **Reveal accounting.** Every answer about a bound item is scored for how
  much of the expected answer it exposed (``answer_leak_overlap``) and, when
  that is non-zero, debited to the cross-channel ``reveal_events`` ledger
  (migration 154). The submit path sums the ledger since the last attempt and
  auto-primes an attempt whose answer was substantially given away, so a
  revealed item cannot be re-recorded as clean unassisted evidence.
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
import logging
import re
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.ai.transport import OperationClient, execute_structured_operation
from learnloop.tutor.ai_contracts import (
    TUTOR_QA_PROMPT_VERSION,
    TutorAnswer,
    TutorQAContext,
    tutor_qa_prompt,
)
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ai.runs import finish_agent_run
from learnloop.learner.facet_diagnostics import required_facets
from learnloop.attempts.reveal_ledger import record_reveal, reveal_episode_id
from learnloop.vault.loader import add_note
from learnloop.vault.models import LoadedVault, PracticeItem

logger = logging.getLogger(__name__)

QUESTION_CONTEXTS = ("library", "practice", "feedback", "reader")

# U-033 (§7.6): per-ask reader answer modes. answer_directly is the launch default.
READER_ANSWER_MODES = ("answer_directly", "help_me_reason", "ask_me_first")
READER_ANSWER_MODE_DEFAULT = "answer_directly"


def request_tutor_answer(
    client: OperationClient,
    context: TutorQAContext,
) -> TutorAnswer:
    """Run the feature-owned tutor-Q&A operation."""

    return execute_structured_operation(
        client,
        purpose="tutor_qa",
        prompt=tutor_qa_prompt(context),
        result_model=TutorAnswer,
        legacy_capability="tutor_qa",
        legacy_context=context,
    )


def reader_span_key(extraction_id: str, span_id: str) -> str:
    """The persistence/budget key for a reader exchange: one source block span.

    Reader Ask anchors to source block ids from the ingest structure (§7.6), so a
    reader exchange is keyed by its span rather than a vault note. The key is
    stored in ``question_events.note_id`` (a distinct ``reader`` context, so it
    never collides with library note ids) which gives per-span budgeting and
    per-span exchange history for free through the existing store."""

    return f"span:{extraction_id}/{span_id}"

# question_type → counts as a hint. Substantive content help is a hint;
# clarifying the prompt, asking "am I right?" (which the tutor deflects), or
# off-topic chatter is not.
HINT_EQUIVALENT_TYPES = frozenset({"prerequisite", "mechanism", "strategy"})

_LEAK_MIN_TOKENS = 3
_LEAK_OVERLAP_THRESHOLD = 0.8

# ING M8 (§9.2): total source-span citations offered to one tutor turn. Bounded so
# the grading/tutor context does not grow with source count (KM §12.9).
_MAX_CITATION_SPANS = 4
# A multi-block reader selection may legitimately cover more blocks than the
# neighbour-window citation cap — bounded separately so a selected exercise
# list arrives whole without unbounding the manifest.
_MAX_SELECTION_SPANS = 8


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
    if context == "reader":
        # Per source span (note_id carries the reader_span_key) per UTC day.
        now = parse_utc(utc_now_iso(clock))
        day_start = now.strftime("%Y-%m-%dT00:00:00Z")
        used = repository.count_question_events(
            context="reader", note_id=note_id, since=day_start, answer_status="answered"
        )
        return used, config.max_questions_reader
    raise TutorQAError(f"Unknown question context {context!r}")


def _record_dialogue_causal_signals(
    vault: LoadedVault,
    repository: Repository,
    *,
    answer: Any,
    attempt_id: str | None,
    practice_item_id: str | None,
    question_event_id: str,
    remediation_episode_id: str | None,
    leak_overlap: float,
    model: str | None = None,
    clock: Clock | None = None,
) -> None:
    """Fold what the learner's question revealed back into the causal record.

    Fires only for a question stamped with a remediation episode: outside a
    repair there is no open causal question for the answer to bear on, and
    minting hypotheses off ordinary library browsing would fill the substrate
    with claims nothing will ever test.

    Two signals, and they are admitted on opposite grounds:

    * ``embedded_prediction`` is a falsifiable expectation the learner's own
      question asserted. It is admissible however much has been revealed — the
      question predates the answer to it, and exposure cannot reach backwards
      into a sentence already typed.
    * ``new_candidate_cause`` is a hypothesis, and the tutor has just been
      talking. It is recorded with ``post_reveal`` stamped from the measured
      leak so a reader can weigh it; the constraint that keeps it honest (only
      causes grounded in what the LEARNER said) lives in the prompt, where the
      generation actually happens.

    Best-effort: bookkeeping never fails the learner's answer.
    """

    if not remediation_episode_id or attempt_id is None:
        return
    prediction = str(getattr(answer, "embedded_prediction", None) or "").strip()
    candidate = getattr(answer, "new_candidate_cause", None)
    if not prediction and candidate is None:
        return

    if prediction:
        try:
            from learnloop.diagnosis.causal_orchestrator import (
                record_learner_embedded_prediction,
            )

            factors = repository.unresolved_cause_factors_for_attempt(
                attempt_id, status="open"
            )
            if factors:
                record_learner_embedded_prediction(
                    repository,
                    factor_id=str(factors[0]["id"]),
                    prediction=prediction,
                    question_event_id=question_event_id,
                    attempt_id=attempt_id,
                    practice_item_id=practice_item_id,
                    remediation_episode_id=remediation_episode_id,
                    clock=clock,
                )
        except Exception:  # pragma: no cover - bookkeeping is best-effort
            logger.warning(
                "failed to record embedded prediction for question %s",
                question_event_id,
                exc_info=True,
            )

    if candidate is not None:
        try:
            from learnloop.diagnosis.causal_attribution import (
                append_dialogue_candidate,
            )

            append_dialogue_candidate(
                vault,
                repository,
                attempt_id=attempt_id,
                candidate=candidate.model_dump(mode="json", exclude_none=True)
                if hasattr(candidate, "model_dump")
                else dict(candidate),
                question_event_id=question_event_id,
                remediation_episode_id=remediation_episode_id,
                post_reveal=leak_overlap > 0.0,
                model=model,
                clock=clock,
            )
        except Exception:  # pragma: no cover - bookkeeping is best-effort
            logger.warning(
                "failed to append dialogue candidate for question %s",
                question_event_id,
                exc_info=True,
            )


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
    extraction_id: str | None = None,
    span_id: str | None = None,
    answer_mode: str | None = None,
    selection_span_ids: Sequence[str] = (),
    selection_quote_md: str | None = None,
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
        # Feedback questions are now hint-equivalent for the NEXT attempt on the
        # item, and that window is session-scoped. A client that omits the
        # session would otherwise write an unattributable row that no submit
        # path counts, so inherit the graded attempt's session.
        session_id = session_id or attempt.get("session_id")
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
    if context == "reader":
        # Reader Ask (§7.6) anchors to a source block span, never a practice item
        # or vault note. The span key is stored in note_id so the existing
        # per-context budget/thread store carries per-span history.
        if not extraction_id or not span_id:
            raise TutorQAError("Reader questions require extraction_id and span_id.")
        if answer_mode is None:
            answer_mode = READER_ANSWER_MODE_DEFAULT
        if answer_mode not in READER_ANSWER_MODES:
            raise TutorQAError(f"Unknown reader answer mode {answer_mode!r}.")
        note_id = reader_span_key(extraction_id, span_id)

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
        extraction_id=extraction_id,
        span_id=span_id,
        answer_mode=answer_mode,
        selection_span_ids=selection_span_ids,
        selection_quote_md=selection_quote_md,
    )

    # Two-phase write: the question row lands BEFORE the provider call. The
    # learner asking is elicitation evidence about their knowledge state
    # regardless of whether the tutor manages to answer, so a provider failure
    # must not erase it (classification arrives with the answer, or never).
    qc = dict(question_context or {})
    source_context: dict[str, Any] | None = None
    if context == "reader" and extraction_id and span_id:
        from learnloop.reader.reader_progression import learning_objects_for_span

        source_context = {
            "extraction_id": extraction_id,
            "span_id": span_id,
            "candidate_learning_object_ids": learning_objects_for_span(
                vault,
                repository,
                extraction_id=extraction_id,
                span_id=span_id,
            ),
            "source_spans": list(ai_context.source_spans),
        }
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
            "source_context": source_context,
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
        answer = request_tutor_answer(client, ai_context)
    except Exception as exc:
        finish_agent_run(
            repository, agent_run_id, client,
            status="failed", error_message=str(exc), clock=clock,
        )
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
    finish_agent_run(repository, agent_run_id, client, clock=clock)

    facets = sorted(
        {vault.canonical_facet_id(str(facet)) for facet in answer.facets}
        & set(candidates)
    )
    citations = _validated_citations(answer, ai_context.source_spans)
    if citations:
        source_context = dict(source_context or {})
        # Persist the model-selected citation only after it has passed the
        # provided-span allowlist. Today can then link this exact discussion
        # instead of guessing from the broader learning-object source set.
        source_context["citations"] = citations
    # Hint equivalence and leak accounting follow the ITEM, not the surface. A
    # mechanism question asked from the feedback screen — where the graded
    # solution is already on display — helps the next attempt on that item at
    # least as much as the same question asked mid-attempt; scoring it only in
    # the practice context let a fully revealed answer be re-recorded as clean
    # unassisted evidence. Reader/library asks stay exempt: no item is bound,
    # so there is nothing to contaminate.
    hint_equivalent = item is not None and answer.question_type in HINT_EQUIVALENT_TYPES
    leak_overlap = (
        answer_leak_overlap(answer.answer_md, item.expected_answer)
        if item is not None
        else 0.0
    )
    leak_suspected = leak_overlap >= _LEAK_OVERLAP_THRESHOLD
    episode = reveal_episode_id(repository, practice_item_id) if item is not None else None
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
        source_context=source_context,
        leak_overlap=leak_overlap if item is not None else None,
        remediation_episode_id=episode,
    )
    if item is not None:
        record_reveal(
            repository,
            practice_item_id=item.id,
            learning_object_id=item.learning_object_id,
            remediation_episode_id=episode,
            source_kind="tutor_answer",
            amount=leak_overlap,
            basis=f"tutor_qa:{context}",
            question_event_id=event_id,
            attempt_id=attempt_id,
            clock=clock,
        )

    # The question join. A question asked INSIDE a repair episode is causal
    # evidence in its own right, and until now it was only ever a hint debit.
    # Best-effort like every other post-answer bookkeeping step: a failure here
    # is logged, never raised, and never costs the learner their answer.
    _record_dialogue_causal_signals(
        vault,
        repository,
        answer=answer,
        attempt_id=attempt_id,
        practice_item_id=practice_item_id,
        question_event_id=event_id,
        remediation_episode_id=episode,
        leak_overlap=leak_overlap,
        model=getattr(client, "model", None),
        clock=clock,
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
        "leak_overlap": leak_overlap,
        "remediation_episode_id": episode,
        "citations": citations,
        "remaining": max(0, limit - used - 1),
    }


def _validated_citations(answer: Any, source_spans: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only citations naming a span actually provided in context (§9.2).

    Never model-invented: a citation whose (extraction_id, span_id) was not in
    ``source_spans`` is dropped. Labels are taken from the provided span so the UI
    chip is trustworthy regardless of what the model echoed."""

    provided = {
        (str(span.get("extraction_id")), str(span.get("span_id"))): span
        for span in source_spans
    }
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for citation in getattr(answer, "citations", None) or []:
        key = (str(citation.extraction_id), str(citation.span_id))
        if key not in provided or key in seen:
            continue
        seen.add(key)
        span = provided[key]
        out.append(
            {
                "extraction_id": key[0],
                "span_id": key[1],
                "label": span.get("label") or citation.label,
            }
        )
    return out


def build_tutor_opening(
    vault: LoadedVault,
    repository: Repository,
    client: Any,
    *,
    practice_item_id: str,
) -> str | None:
    """A proactive tutor opening for a just-closed diagnostic block (§12.1).

    Ephemeral: unlike ``ask_question`` this never inserts a question_event —
    an unprompted opening isn't elicitation evidence and must not consume the
    Q&A budget or count as a hint. Returns None when there is no persisted
    decision to open with (block still measuring, never routed to tutoring,
    or unknown item) so the caller falls back to the ordinary learner-speaks-
    first overlay.
    """

    item = vault.practice_items.get(practice_item_id)
    if item is None:
        return None
    if _diagnostic_decision_for(repository, item, "practice") is None:
        return None
    candidates = _candidate_facets(vault, repository, "practice", item=item, note=None)
    ai_context = _build_context(
        vault,
        repository,
        context="practice",
        question_md="",
        candidates=candidates,
        thread=[],
        item=item,
        attempt=None,
        note=None,
        note_id=None,
    )
    answer = request_tutor_answer(client, ai_context)
    return answer.answer_md


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
    into that attempt's evidence). Practice- and feedback-context questions
    both count: the window explicitly spans the feedback screen shown between
    attempt N and attempt N+1."""

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


def answer_leak_overlap(answer_md: str, expected_answer: str | dict[str, Any]) -> float:
    """How much of the expected answer the tutor's answer exposed (0..1).

    The quantity behind ``answer_leaks_expected``. A normalized-substring hit
    is a full reveal (1.0); otherwise the fraction of the expected answer's
    content tokens that appear in the tutor's answer. 0.0 when the comparison
    cannot be made at all (empty text, or too few content tokens to distinguish
    a real overlap from incidental vocabulary).

    A quantity rather than a flag because reveals *accumulate*: two partial
    answers across two turns can hand over as much as one leak, and the submit
    path thresholds a sum. Heuristic and lexical — it measures surface overlap,
    not semantic equivalence, so it under-reports a paraphrased solution."""

    expected_text = (
        expected_answer if isinstance(expected_answer, str) else json.dumps(expected_answer, sort_keys=True)
    )
    answer_norm = _normalize(answer_md)
    expected_norm = _normalize(expected_text)
    if not expected_norm or not answer_norm:
        return 0.0
    if len(expected_norm) >= 12 and expected_norm in answer_norm:
        return 1.0
    expected_tokens = {token for token in expected_norm.split() if len(token) > 2}
    if len(expected_tokens) < _LEAK_MIN_TOKENS:
        return 0.0
    answer_tokens = {token for token in answer_norm.split() if len(token) > 2}
    return len(expected_tokens & answer_tokens) / len(expected_tokens)


def answer_leaks_expected(answer_md: str, expected_answer: str | dict[str, Any]) -> bool:
    """Heuristic answer-leak telemetry: did the tutor give the answer away?

    Kept as the boolean face of ``answer_leak_overlap`` (same threshold as
    before). Flags, never blocks."""

    return answer_leak_overlap(answer_md, expected_answer) >= _LEAK_OVERLAP_THRESHOLD


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
    related_lo_ids: list[str] | None = None,
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

    related_los: list[str] = list(related_lo_ids or [])
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
    elif context == "reader":
        # Prior reader exchanges on the SAME span only (note_id is the span key);
        # never the practice/feedback history, never cold attempt content (§7.6).
        events = repository.question_events(
            context="reader", note_id=note_id, answer_status="answered"
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
    extraction_id: str | None = None,
    span_id: str | None = None,
    answer_mode: str | None = None,
    selection_span_ids: Sequence[str] = (),
    selection_quote_md: str | None = None,
) -> TutorQAContext:
    if context == "reader":
        # The reader_context_manifest_v1 (design A.2): the exact span(s) in view
        # (the learner's selection + neighbours) + the question + the chosen
        # mode. It MUST NOT carry the learner ability estimate, any
        # assessment-reserved surface's statement/rubric, or any cold in-flight
        # response -- so no note body, no rubric, no expected answer, no
        # diagnostic decision, no candidate facets.
        return TutorQAContext(
            context="reader",
            question_md=question_md,
            candidate_facets=[],
            thread=thread,
            source_spans=_reader_source_spans(
                repository,
                extraction_id,
                span_id,
                selection_span_ids=selection_span_ids,
                selection_quote_md=selection_quote_md,
            ),
            answer_mode=answer_mode or READER_ANSWER_MODE_DEFAULT,
        )

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

    source_spans = _source_spans(vault, repository, lo_ids)

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
        source_spans=source_spans,
    )


def _source_spans(
    vault: LoadedVault, repository: Repository, lo_ids: list[str]
) -> list[dict[str, Any]]:
    """Bounded semantic-authority source spans for the LO(s) in tutor context (§9.2).

    Reuses the cross-source span builder (semantic authority first, alternates for
    variety, held-out excluded) and caps the TOTAL across LOs so the context does
    not grow with source count (KM §12.9). Degrades to [] when no links exist."""

    from learnloop.content.authoring.practice_leakage import build_cross_source_spans

    spans: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for lo_id in lo_ids:
        for span in build_cross_source_spans(
            vault, repository, lo_id, max_spans_per_item=_MAX_CITATION_SPANS
        ):
            key = (span.extraction_id, span.span_id)
            if key in seen:
                continue
            seen.add(key)
            spans.append(span.as_dict())
            if len(spans) >= _MAX_CITATION_SPANS:
                return spans
    return spans


def _reader_source_spans(
    repository: Repository,
    extraction_id: str | None,
    span_id: str | None,
    *,
    selection_span_ids: Sequence[str] = (),
    selection_quote_md: str | None = None,
) -> list[dict[str, Any]]:
    """Block-level span views for the reader manifest (§7.6): the learner's
    selection (exact quote first, then every covered block), plus the primary
    block's immediate neighbours, as citable {extraction_id, span_id, label,
    text} spans. NOT the P3 annotation layer -- just ``span_view`` geometry. The
    tutor may cite ONLY these. Degrades to [] when the span cannot be resolved."""

    if not extraction_id or not span_id:
        return []
    from learnloop.reader.span_view import SpanViewError, build_span_view

    try:
        view = build_span_view(repository, extraction_id, span_id, record=False)
    except SpanViewError:
        return []
    spans: list[dict[str, Any]] = []

    def _label(text: str | None) -> str:
        text = " ".join((text or "").split())
        return text[:59].rstrip() + "…" if len(text) > 60 else text

    # The exact selected passage leads: it tells the tutor which PART of the
    # in-view blocks the question is about (a multi-block selection is joined
    # client-side in reading order). Anchored to the primary block, so the
    # citation contract (extraction_id/span_id pairs from this list) holds.
    if selection_quote_md and selection_quote_md.strip():
        spans.append(
            {
                "extraction_id": extraction_id,
                "span_id": span_id,
                "label": "learner selection",
                "text": selection_quote_md,
                "relation": "selected_text",
            }
        )
    spans.append(
        {
            "extraction_id": extraction_id,
            "span_id": span_id,
            "label": _label(view.get("text")),
            "text": view.get("text"),
            "relation": "in_view",
        }
    )
    # Every other block the selection covers is in view too (bounded).
    for extra_id in list(dict.fromkeys(selection_span_ids))[:_MAX_SELECTION_SPANS]:
        if extra_id == span_id:
            continue
        try:
            extra = build_span_view(repository, extraction_id, extra_id, record=False)
        except SpanViewError:
            continue
        spans.append(
            {
                "extraction_id": extraction_id,
                "span_id": extra_id,
                "label": _label(extra.get("text")),
                "text": extra.get("text"),
                "relation": "in_view",
            }
        )
    max_spans = max(_MAX_CITATION_SPANS, len(spans) + 2)
    for neighbour in (view.get("previous_spans") or []) + (view.get("next_spans") or []):
        nid = neighbour.get("span_id")
        if nid is None:
            continue
        spans.append(
            {
                "extraction_id": extraction_id,
                "span_id": nid,
                "label": _label(neighbour.get("text")),
                "text": neighbour.get("text"),
                "relation": "surrounding",
            }
        )
        if len(spans) >= max_spans:
            break
    return spans


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
