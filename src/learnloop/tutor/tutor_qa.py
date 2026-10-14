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
  revealed item cannot be re-recorded as clean unassisted evidence. Source
  spans chosen by retrieval (Slice 2 T6) are a second channel: the learner can
  open a cited span, so a cited span's overlap with the expected answer
  (``span_answer_overlap``, which also measures short answers) is debited too.
- **Guardrails.** The practice prompt forbids stating the answer, completing
  the derivation, or confirming/denying the learner's approach; verification
  questions are deflected with a guiding question. A post-hoc leak check flags
  (never blocks) answers that overlap the expected answer.
- **Two-phase persistence.** The question row is inserted with
  ``answer_status='pending'`` before the provider call (and, outside the
  reader, before any source retrieval) and updated to
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
import time
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any, Callable, Mapping, Sequence

from learnloop.clock import Clock, parse_utc, utc_now_iso
from learnloop.ai.transport import OperationClient, execute_structured_operation
from learnloop.tutor.ai_contracts import (
    TUTOR_QA_PROMPT_VERSION,
    TUTOR_QA_TOOLS_PROMPT_VERSION,
    TutorAnswer,
    TutorAnswerWithTools,
    TutorQAContext,
    tutor_qa_prompt,
)
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ai.runs import finish_agent_run
from learnloop.learner.facet_diagnostics import required_facets, scope_facets
from learnloop.attempts.reveal_ledger import record_reveal, reveal_episode_id
from learnloop.vault.loader import add_note
from learnloop.vault.models import LoadedVault, PracticeItem
from learnloop.vault.required_method import presented_prompt

logger = logging.getLogger(__name__)

QUESTION_CONTEXTS = ("library", "practice", "feedback", "reader")

# Slice 2 T6 injection seams (the adapter supplies learnloop.source_retrieval's).
# A span provider returns (spans or None to keep the linked spans, a manifest or
# None); a suggester returns labelled LO suggestions for a reader span.
SourceSpanProvider = Callable[..., tuple[list[dict[str, Any]] | None, dict[str, Any] | None]]
LearningObjectSuggester = Callable[..., list[dict[str, Any]]]

# U-033 (§7.6): per-ask reader answer modes. answer_directly is the launch default.
READER_ANSWER_MODES = ("answer_directly", "help_me_reason", "ask_me_first")
READER_ANSWER_MODE_DEFAULT = "answer_directly"


def request_tutor_answer(
    client: OperationClient,
    context: TutorQAContext,
    *,
    tools: bool = False,
) -> TutorAnswer:
    """Run the feature-owned tutor-Q&A operation (``tools``: S4's request field)."""

    return execute_structured_operation(
        client,
        purpose="tutor_qa",
        prompt=tutor_qa_prompt(context, tools=tools),
        result_model=TutorAnswerWithTools if tools else TutorAnswer,
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
    question_event_id: str | None = None,
    source_span_provider: SourceSpanProvider | None = None,
    learning_object_suggester: LearningObjectSuggester | None = None,
    reader_thread: Sequence[Mapping[str, Any]] | None = None,
    tool_request_handler: Callable[..., list[dict[str, Any]]] | None = None,
    learner_draft_md: str | None = None,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """``question_context`` carries the §13.4 generating-process fields
    (preceding_tutor_move, scaffold_level, warning_state, learner_mode,
    question_opportunity, hints_used_before, direct_explanation_request,
    attempt_progress). They are persisted verbatim for later contextual
    likelihood calibration; unknown keys are ignored.

    Slice 2 T6, injected by the adapter (this package never imports the
    retrieval package): ``source_span_provider`` chooses the practice, feedback
    and library contexts' source spans from the question (None keeps the
    learning object's linked spans), and ``learning_object_suggester`` records a
    labelled nearest-LO suggestion for a reader span without provenance. Neither
    changes the facet -> LO mapping, the candidate LOs or any evidence.

    Canonical sources S4, injected by the adapter: ``tool_request_handler``
    turns on the answer's ``tool_requests`` field (prompt and contract) and
    validates the requests after the answer is stored; None keeps S0's tutor
    byte for byte. ``learner_draft_md`` passes the learner's current draft as
    context ("Explain this with my work")."""

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
    # Reader branches (RW1a) resolve a follow-up's durable ancestors server-side
    # in the reader dialogue: an explicit empty sequence starts a new root, and
    # None (the kill switch off, or a direct caller) keeps the same-span thread.
    thread = (
        [dict(turn) for turn in reader_thread]
        if context == "reader" and reader_thread is not None
        else _thread(
            repository,
            context=context,
            practice_item_id=practice_item_id,
            attempt_id=attempt_id,
            note_id=note_id,
            session_id=session_id,
        )
    )
    # Two-phase write: the question row lands BEFORE the provider call. The
    # learner asking is elicitation evidence about their knowledge state
    # regardless of whether the tutor manages to answer, so a provider failure
    # must not erase it (classification arrives with the answer, or never).
    # Outside the reader the row also lands before source retrieval (Slice 2
    # T6), so a slow or interrupted retrieval cannot lose the question either.
    qc = dict(question_context or {})
    question_row = {
        "id": question_event_id,
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
    }
    source_context: dict[str, Any] | None = None
    provided_spans: list[dict[str, Any]] | None = None

    def build_context() -> TutorQAContext:
        return _build_context(
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
            provided_source_spans=provided_spans,
            learner_draft_md=learner_draft_md,
        )

    if context == "reader":
        ai_context = build_context()
        if extraction_id and span_id:
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
            if not source_context["candidate_learning_object_ids"] and learning_object_suggester is not None:
                suggestions = _suggested_learning_objects(
                    vault, repository, learning_object_suggester,
                    extraction_id=extraction_id, span_id=span_id,
                )
                if suggestions:
                    # Labelled suggestions, never candidates: promotion, the learner
                    # field and filing read only candidate_learning_object_ids.
                    source_context["suggested_learning_objects"] = suggestions
        event_id = repository.insert_question_event(
            {**question_row, "source_context": source_context}, clock=clock,
        )
    else:
        event_id = repository.insert_question_event(
            {**question_row, "source_context": None}, clock=clock,
        )
        try:
            if source_span_provider is not None:
                provided_spans, retrieval_manifest = _provided_source_spans(
                    vault, repository, source_span_provider, context=context,
                    question_md=question_md, learning_object_ids=_context_learning_objects(item, note),
                    item=item,
                )
                if retrieval_manifest is not None:
                    source_context = {"source_retrieval": retrieval_manifest}
            ai_context = build_context()
        except Exception as exc:
            repository.update_question_event_answer(
                event_id,
                answer_md=None,
                question_type=None,
                facets=None,
                hint_equivalent=False,
                leak_suspected=False,
                answer_status="failed",
                source_context=source_context,
            )
            logger.warning("tutor context failed before the provider call: %s", type(exc).__name__)
            raise
    tools = tool_request_handler is not None
    agent_run_id = repository.insert_agent_run(
        {
            "id": new_ulid(),
            "purpose": "tutor_qa",
            "provider": getattr(client, "provider_name", None) or "codex",
            "provider_type": getattr(client, "provider_type", None),
            "model": getattr(client, "model", None),
            "prompt_template": "tutor_qa",
            "prompt_version": TUTOR_QA_TOOLS_PROMPT_VERSION if tools else TUTOR_QA_PROMPT_VERSION,
            "input_context_hash": _tutor_context_hash(ai_context),
            "output_schema": "TutorAnswerWithTools" if tools else "TutorAnswer",
            "started_at": utc_now_iso(clock),
            "status": "running",
        }
    )
    try:
        answer = request_tutor_answer(client, ai_context, tools=tools)
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
            source_context=source_context,
        )
        raise
    finish_agent_run(repository, agent_run_id, client, clock=clock)

    facets = sorted(
        {vault.canonical_facet_id(str(facet)) for facet in answer.facets}
        & set(candidates)
    )
    if facets:
        # The facet -> LO mapping as of this question, persisted so the learner
        # field never re-derives history from today's mutable membership. It is
        # grounded in what this question is about (its item's LO or its note's
        # LOs; for a prerequisite question, their declared prerequisites), never
        # in vault-wide facet membership. An unresolved or ambiguous facet is
        # left to the opt-in classifier. Each target keeps its own subject.
        source_context = dict(source_context or {})
        source_context.update(_grounded_facet_targets(
            vault, repository, facets,
            question_type=answer.question_type, item=item, note=note,
        ))
    citations = _validated_citations(answer, ai_context.source_spans)
    if citations:
        source_context = dict(source_context or {})
        # Persist the model-selected citation only after it has passed the
        # provided-span allowlist. Today can then link this exact discussion
        # instead of guessing from the broader learning-object source set.
        source_context["citations"] = citations
    learner_gap = _learner_gap_reading(answer, model=getattr(client, "model", None))
    if learner_gap is not None:
        source_context = dict(source_context or {})
        # Learner-text gaps: the tutor's reading of the question, persisted
        # with the answer (a paid output; the gap pipeline matches it to a
        # target later and never asks again).
        source_context["learner_gap"] = learner_gap
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
        if provided_spans is not None and citations:
            # Slice 2 T6: a cited retrieved span opens in the Ask overlay, so
            # what it exposes of the expected answer is a reveal of its own
            # (the tutor's prose is scored above). Spans that reproduce the
            # answer never reach the tutor; partial overlap is debited here.
            span_overlap = _cited_span_overlap(citations, ai_context.source_spans, item.expected_answer)
            record_reveal(
                repository,
                practice_item_id=item.id,
                learning_object_id=item.learning_object_id,
                remediation_episode_id=episode,
                source_kind="source_review",
                amount=span_overlap,
                basis=f"tutor_qa:{context}:cited_source_span",
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

    result = {
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
        "learner_gap": learner_gap,
        "remaining": max(0, limit - used - 1),
    }
    if tool_request_handler is not None:
        # Canonical sources S4: validated before anything is shown; a failure
        # here never costs the learner their answer.
        try:
            result["tool_requests"] = tool_request_handler(
                vault, repository, event_id=event_id,
                requests=list(getattr(answer, "tool_requests", None) or []),
                model=getattr(client, "model", None), prompt_version=TUTOR_QA_TOOLS_PROMPT_VERSION, clock=clock,
            )
        except Exception as exc:  # noqa: BLE001 - offers are optional
            logger.warning("tutor tool requests failed: %s", type(exc).__name__)
            result["tool_requests"] = []
    suggested = (source_context or {}).get("suggested_learning_objects")
    if suggested:
        # Slice 2 T6: labelled suggestions for a reader span without provenance
        # (absent when there are none, so the kill switch changes nothing).
        result["suggested_learning_objects"] = list(suggested)
    return result


def _learner_gap_reading(answer: Any, *, model: Any = None) -> dict[str, Any] | None:
    """The tutor's named gap, trimmed, with the prompt it was read under.

    None when the tutor gave none. A name the kind does not use is kept: the
    gap pipeline's chooser may be the Decider, which names nothing.
    """

    gap = getattr(answer, "learner_gap", None)
    if gap is None:
        return None
    data = gap.model_dump(mode="json") if hasattr(gap, "model_dump") else dict(gap)
    reading: dict[str, Any] = {"kind": str(data.get("kind") or "none")}
    for key in ("prerequisite_name", "prerequisite_line", "belief_statement"):
        value = " ".join(str(data.get(key) or "").split())[:500]
        reading[key] = value or None
    reading["prompt_version"] = TUTOR_QA_PROMPT_VERSION
    reading["model"] = str(model) if model else None
    return reading


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
    if _diagnostic_decision_for(vault, repository, item, "practice") is None:
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


#: A short expected answer (fewer than ``_LEAK_MIN_TOKENS`` content tokens) is
#: matched as a token sequence in a source span when it has at most this many
#: tokens. A lone token must contain a digit and be at least two characters
#: ("154"), since a single short word or digit appears in passages by accident.
_SHORT_ANSWER_MAX_TOKENS = 8


def span_answer_overlap(text: str, expected_answer: str | dict[str, Any]) -> float:
    """How much of the expected answer a source span exposes (0..1).

    ``answer_leak_overlap`` measures long answers. A short answer, which it
    cannot measure (``2/13``, ``0.154``, ``2 and 3``), counts as fully exposed
    when its normalized tokens appear in order and adjacent in the span: a
    passage that states the number is the solution as far as the learner is
    concerned. Used to withhold retrieved spans before the tutor sees them and
    to debit cited ones, so it errs towards exposure."""

    overlap = answer_leak_overlap(text, expected_answer)
    if overlap >= 1.0:
        return overlap
    expected_text = (
        expected_answer if isinstance(expected_answer, str) else json.dumps(expected_answer, sort_keys=True)
    )
    expected_tokens = _normalize(expected_text).split()
    content = [token for token in expected_tokens if len(token) > 2]
    if not expected_tokens or len(expected_tokens) > _SHORT_ANSWER_MAX_TOKENS or len(content) >= _LEAK_MIN_TOKENS:
        return overlap
    if len(expected_tokens) == 1:
        token = expected_tokens[0]
        if len(token) < 2 or not any(character.isdigit() for character in token):
            return overlap
    span_tokens = _normalize(text).split()
    width = len(expected_tokens)
    for start in range(len(span_tokens) - width + 1):
        if span_tokens[start:start + width] == expected_tokens:
            return 1.0
    return overlap


def span_leaks_expected(text: str, expected_answer: str | dict[str, Any]) -> bool:
    """A source span that gives the expected answer away (withheld from the tutor)."""

    return span_answer_overlap(text, expected_answer) >= _LEAK_OVERLAP_THRESHOLD


def _cited_span_overlap(
    citations: Sequence[Mapping[str, Any]],
    source_spans: Sequence[Mapping[str, Any]],
    expected_answer: str | dict[str, Any],
) -> float:
    """The largest expected-answer overlap among the cited source spans."""

    texts = {
        (str(span.get("extraction_id")), str(span.get("span_id"))): str(span.get("text") or "")
        for span in source_spans
    }
    return max(
        (span_answer_overlap(texts.get((str(c.get("extraction_id")), str(c.get("span_id"))), ""), expected_answer)
         for c in citations),
        default=0.0,
    )


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


def _prerequisite_learning_objects(vault: LoadedVault, anchors: Sequence[str]) -> set[str]:
    """LOs on the concepts the anchor LOs declare as prerequisites.

    Declared by the LO's own ``prerequisites`` (concept ids) or by a
    ``prerequisite`` relation edge into its concept. The anchors are excluded:
    a prerequisite question points below the item, never at it."""

    concepts: set[str] = set()
    for lo_id in anchors:
        learning_object = vault.learning_objects.get(lo_id)
        if learning_object is None:
            continue
        concepts.update(learning_object.prerequisites)
        concepts.update(
            edge.source for edge in vault.edges
            if edge.relation_type == "prerequisite" and edge.target == learning_object.concept
        )
    return {
        learning_object.id for learning_object in vault.learning_objects.values()
        if learning_object.concept in concepts
    } - set(anchors)


def _grounded_facet_targets(
    vault: LoadedVault,
    repository: Repository,
    facets: Sequence[str],
    *,
    question_type: str,
    item: PracticeItem | None,
    note: Any,
) -> dict[str, Any]:
    """The question-time facet -> LO mapping, grounded in the question's context.

    A facet two LOs both measure is not a relationship between them: a generic
    facet such as ``recall`` is shared across unrelated subjects. Targets are
    therefore drawn only from the LOs this question is about:

    - an item question (practice or feedback) targets its item's LO, and a note
      question (library) the note's related LOs;
    - a ``prerequisite`` question points below those, to the LOs their declared
      prerequisites name (``_prerequisite_learning_objects``).

    A facet resolves only when exactly one grounded LO is responsible for it
    (``scope_facets``). None or several leaves it unresolved, for the opt-in
    classifier. Each target's subject is recorded as of now: the item's own
    subject for its LO, else the target LO's primary subject.
    """

    if item is not None:
        anchors = [item.learning_object_id]
    elif note is not None:
        anchors = sorted({lo for lo in note.related_los if lo in vault.learning_objects})
    else:
        anchors = []
    if question_type == "prerequisite":
        scope = sorted(_prerequisite_learning_objects(vault, anchors))
    else:
        scope = anchors
    responsible = {
        lo_id: {vault.canonical_facet_id(f) for f in scope_facets(vault, lo_id, repository)}
        for lo_id in scope
    }
    if item is not None and item.learning_object_id in responsible:
        # The item's own facets are the item's LO's, whatever its scope says.
        responsible[item.learning_object_id] |= {
            vault.canonical_facet_id(str(f)) for f in item.evidence_facets
        }
    mapping: dict[str, list[str]] = {}
    for facet in sorted(facets):
        owners = [lo_id for lo_id in scope if facet in responsible[lo_id]]
        if len(owners) == 1:
            mapping[facet] = owners
    subjects: dict[str, str] = {}
    for lo_id in sorted({lo for owners in mapping.values() for lo in owners}):
        if item is not None and lo_id == item.learning_object_id:
            candidates = vault.subjects_for_item(item)
        else:
            candidates = vault.learning_objects[lo_id].subjects
        if candidates:
            subjects[lo_id] = candidates[0]
    return {"facet_learning_object_ids": mapping, "learning_object_subject_ids": subjects}


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
    provided_source_spans: list[dict[str, Any]] | None = None,
    learner_draft_md: str | None = None,
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

    # ING M8 §9.2: provided spans obey the same total bound as linked ones.
    source_spans = (
        list(provided_source_spans)[:_MAX_CITATION_SPANS] if provided_source_spans is not None
        else _source_spans(vault, repository, lo_ids)
    )

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

    if learner_answer is None and learner_draft_md and learner_draft_md.strip():
        # S4's "Explain this with my work": the learner's current draft.
        learner_answer = learner_draft_md
    return TutorQAContext(
        context=context,
        question_md=question_md,
        candidate_facets=candidates,
        thread=thread,
        # The question as the learner was shown it (round 3: a required
        # method's instruction is rendered after the statement).
        practice_item_prompt=presented_prompt(item.prompt, item.required_method) if item is not None else None,
        expected_answer=expected,
        rubric=rubric.model_dump() if rubric is not None else None,
        learner_answer_md=learner_answer,
        grading_feedback=grading_feedback,
        note_title=note_id,
        note_body=note.body if note is not None else None,
        learning_object_summaries=lo_summaries,
        diagnostic_decision=_diagnostic_decision_for(vault, repository, item, context),
        source_spans=source_spans,
    )


def _context_learning_objects(item: PracticeItem | None, note: Any) -> list[str]:
    """The LOs a non-reader question is about: its item's, or its note's related LOs."""

    if item is not None:
        return [item.learning_object_id]
    if note is not None:
        return list(note.related_los)
    return []


def _provided_source_spans(
    vault: LoadedVault,
    repository: Repository,
    provider: SourceSpanProvider,
    *,
    context: str,
    question_md: str,
    learning_object_ids: list[str],
    item: PracticeItem | None,
) -> tuple[list[dict[str, Any]] | None, dict[str, Any] | None]:
    """The injected span provider's choice; any failure keeps the linked spans.

    The receipt records the provider's wall time (``timings_ms.total``) on
    every path, failures included, unless the provider timed its own steps.
    """

    started = time.monotonic()
    try:
        spans, manifest = provider(
            vault, repository, context=context, question_md=question_md,
            learning_object_ids=learning_object_ids, item=item,
        )
    except Exception as exc:  # noqa: BLE001 - retrieval is context; never lose the question
        logger.warning("tutor source retrieval failed: %s", type(exc).__name__)
        return None, {"basis": "lo_provenance", "reason": f"retrieval failed ({type(exc).__name__})",
                      "timings_ms": {"total": int(round((time.monotonic() - started) * 1000))}}
    if spans is not None:
        spans = [dict(span) for span in spans]
    if manifest is None:
        return spans, None
    manifest = dict(manifest)
    manifest.setdefault("timings_ms", {"total": int(round((time.monotonic() - started) * 1000))})
    return spans, manifest


def _suggested_learning_objects(
    vault: LoadedVault,
    repository: Repository,
    suggester: LearningObjectSuggester,
    *,
    extraction_id: str,
    span_id: str,
) -> list[dict[str, Any]]:
    try:
        return [dict(entry) for entry in suggester(vault, repository, extraction_id=extraction_id,
                                                   span_id=span_id)]
    except Exception as exc:  # noqa: BLE001 - a suggestion is optional
        logger.warning("learning-object suggestion failed: %s", type(exc).__name__)
        return []


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
    vault: LoadedVault, repository: Repository, item: PracticeItem | None, context: str
) -> dict[str, Any] | None:
    """The §12.1 typed transition decision steering post-diagnosis tutoring.

    Attached only when the item's LO has no open episode (measurement has
    ended — attaching it mid-measurement would lift the no-reveal guardrail
    while a block is still measuring) and the latest closed episode persisted
    a decision on its way into tutoring. An unanswered opening episode
    placement ignores is not measuring anything (owner decision 2026-10-12).

    Only a typed transition counts (Codex re-review F2). ``target_decision``
    also records how an episode was opened or relocked, as ``{"kind": ...}``
    (an opening episode a door adopted, the causal quick check), until a block
    routes it into tutoring and overwrites it with the typed decision, which
    has no ``kind``. An episode that completed without a gap keeps that stamp;
    it is no decision, so it neither opens the tutor nor reaches the model.
    """

    if item is None or context not in ("practice", "feedback"):
        return None
    lo_id = item.learning_object_id
    from learnloop.placement.state import servable_open_episode

    if servable_open_episode(vault, repository, lo_id) is not None:
        return None
    for episode in reversed(repository.probe_episodes_for_learning_object(lo_id)):
        decision = episode.target_decision
        if (
            episode.status in ("complete", "converted_to_tutoring")
            and isinstance(decision, Mapping)
            and decision
            and "kind" not in decision
        ):
            return dict(decision)
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
