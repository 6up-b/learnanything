"""Teach-back conversations: the learner teaches, an AI naive student asks.

Flow (design decisions, agreed spec):

- The learner writes an opening explanation, then the AI — playing a curious
  NAIVE STUDENT (never corrects, never confirms/denies, never reveals) — asks
  up to ``config.teach_back.max_followups`` questions one at a time, each
  generated live against one planned rubric criterion. The whole transcript is
  graded at the end as ONE ``teach_back`` attempt through ``apply_attempt``.
- Follow-up planning is deterministic given DB state: the item's facets are
  ranked by diagnostic uncertainty via the ``mastery_diagnostic_view`` read
  path (which folds in the tutor-question uncertainty bump), core-tier rubric
  criteria are picked for the most uncertain facets first, and when nothing
  uncertain remains the plan ESCALATES to transfer-tier criteria that
  stress-test solid knowledge. When the rubric has transfer-tier criteria at
  all, one question is GUARANTEED to be one (the last slot is reserved), so
  edge-case/what-if probing can't be crowded out by uncertain core facets.
- Grading: only ASKED criteria produce evidence. The grading context rubric is
  restricted to the asked criteria, the rubric score is normalized over the
  asked criteria's points (unasked criteria are never zero-score failures),
  and the evidence-mass side is handled by
  ``scale_coverage_for_graded_criteria`` inside the shared attempt step
  (including the symmetric transfer-tier multiplier). "I don't know" answers
  are just low-scoring text — no special branch.
- Provider failure mid-conversation: ``finish_teach_back`` grades whatever was
  actually asked *and answered*; a question the learner never answered is not
  treated as asked. If no follow-up was answered at all, the opening
  explanation is graded against the core-tier criteria (the opening teaches
  the core surface), so a provider outage still yields one usable attempt.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field, replace as dataclass_replace
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import TeachBackAuthoringContext, TeachBackQuestionContext
from learnloop.codex.schemas import TeachBackAuthoring, TeachBackCriterionDraft
from learnloop.config import LearnLoopConfig
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    AttemptResult,
    AttemptValidationError,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.facet_diagnostics import mastery_diagnostic_view
from learnloop.services.grading import (
    GradingValidationError,
    build_grading_context,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.services.recall_coverage import criterion_facet_weights_for_item
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric, RubricCriterion

TEACH_BACK_ATTEMPT_TYPE = "teach_back"
TEACH_BACK_PRACTICE_MODE = "teach_back"
TEACH_BACK_COMPILER_VERSION = "source_item_v3"

STATE_VERSION = 1
LOG = logging.getLogger(__name__)

# Model-authored Markdown occasionally arrives with terminal rendering bytes
# (for example ``\x1b[1mR\x1b[22m`` instead of ``**R**``). Those bytes are not
# content: persisting them makes the transcript unstable across renderers and
# can break the grading repair contract's verbatim-prefix check. Preserve
# Markdown whitespace, but remove ANSI CSI/OSC sequences and other C0/C1
# controls from AI turns at the boundary.
_ANSI_SEQUENCE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))"
)
_UNSAFE_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


def _sanitize_ai_markdown(value: str) -> str:
    return _UNSAFE_CONTROL.sub("", _ANSI_SEQUENCE.sub("", value))


# Diagnostic-state ranking for follow-up planning: uncertain and unexamined
# facets are probed first; known gaps next (the gap is known but a probe still
# helps); solid facets last (core criteria on them are skipped in favor of
# transfer escalation).
_STATE_RANK = {"uncertain": 0, "unexamined": 1, "known_gap": 2, "solid": 3}


class TeachBackError(ValueError):
    pass


def _criterion_tier(criterion: RubricCriterion) -> str:
    return getattr(criterion, "tier", "core") or "core"


@dataclass
class TeachBackTurn:
    role: str  # "learner" | "ai"
    content_md: str
    criterion_id: str | None = None


@dataclass
class TeachBackState:
    """Serializable conversation state (JSON round-trippable).

    The sidecar stores ``to_dict()`` output verbatim in its session
    checkpoint; ``from_dict`` restores it. ``planned`` is the ordered
    follow-up plan (``plan_followups`` output); ``turns`` is the transcript
    oldest-first — the first turn is the learner's opening explanation;
    ``asked_count`` counts AI questions generated so far.
    """

    practice_item_id: str
    planned: list[dict[str, Any]] = field(default_factory=list)
    turns: list[TeachBackTurn] = field(default_factory=list)
    asked_count: int = 0
    version: int = STATE_VERSION
    # Stable id for the whole conversation, generated in ``begin_teach_back``.
    # Persisted on the recorded attempt's evidence rows so a retried finish can
    # find the already-recorded attempt instead of grading the transcript twice.
    # Optional for backward compatibility with checkpoints written before it
    # existed (those simply skip the dedup lookup).
    conversation_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "practice_item_id": self.practice_item_id,
            "planned": [dict(selection) for selection in self.planned],
            "turns": [asdict(turn) for turn in self.turns],
            "asked_count": self.asked_count,
            "conversation_id": self.conversation_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "TeachBackState":
        return cls(
            practice_item_id=str(payload["practice_item_id"]),
            planned=[dict(selection) for selection in payload.get("planned", [])],
            turns=[
                TeachBackTurn(
                    role=str(turn["role"]),
                    content_md=(
                        _sanitize_ai_markdown(str(turn.get("content_md") or ""))
                        if str(turn["role"]) == "ai"
                        else str(turn.get("content_md") or "")
                    ),
                    criterion_id=turn.get("criterion_id"),
                )
                for turn in payload.get("turns", [])
            ],
            asked_count=int(payload.get("asked_count") or 0),
            version=int(payload.get("version") or STATE_VERSION),
            conversation_id=payload.get("conversation_id"),
        )

    @classmethod
    def from_json(cls, text: str) -> "TeachBackState":
        return cls.from_dict(json.loads(text))


@dataclass(frozen=True)
class TeachBackFinishResult:
    attempt: AttemptResult
    transcript_md: str
    asked_criterion_ids: list[str]
    graded_criterion_ids: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt.as_dict(),
            "transcript_md": self.transcript_md,
            "asked_criterion_ids": self.asked_criterion_ids,
            "graded_criterion_ids": self.graded_criterion_ids,
        }


def plan_followups(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    config: LearnLoopConfig | None = None,
    clock: Clock | None = None,
) -> list[dict[str, Any]]:
    """Ordered follow-up plan: ``[{criterion_id, tier, facet_targets}]``.

    Deterministic given DB state. Core-tier criteria whose target facets are
    still uncertain/unexamined/known-gap come first (most uncertain facet
    first); when nothing uncertain remains the plan escalates to transfer-tier
    criteria; any leftover slots are filled with the remaining (solid-facet)
    core criteria. Capped at ``config.teach_back.max_followups``. When the
    rubric has transfer-tier criteria (and the cap allows at least two
    questions), the plan is guaranteed to contain one: uncertain core criteria
    can otherwise crowd out escalation entirely, so the last slot is swapped
    for the transfer criterion whose target facets are most solid — a transfer
    failure on a facet whose core is still uncertain is ambiguous evidence.
    """

    config = config or vault.config
    rubric = _teach_back_rubric(vault, item)
    mapping = criterion_facet_weights_for_item(item, rubric)
    facet_rank = _facet_ranks(vault, repository, item, clock=clock)

    def criterion_targets(criterion: RubricCriterion) -> list[str]:
        raw_map = mapping.get(criterion.id) or {}
        targets = [
            str(facet)
            for facet, weight in raw_map.items()
            if float(weight) > 0 and str(facet) in facet_rank
        ]
        if targets:
            return sorted(targets, key=lambda facet: facet_rank[facet])
        # P0b authoring honesty: a declared empty map is meaningful. In
        # particular, item-local source-procedure criteria must not silently
        # inherit every broad facet on the Learning Object.
        if getattr(criterion, "measurement_status", None) is not None:
            return []
        return [str(facet) for facet in item.evidence_facets]

    def criterion_key(criterion: RubricCriterion, index: int) -> tuple:
        targets = [facet for facet in criterion_targets(criterion) if facet in facet_rank]
        best = min((facet_rank[facet] for facet in targets), default=(len(_STATE_RANK), 0.0, ""))
        return (*best, index, criterion.id)

    core: list[tuple[tuple, RubricCriterion]] = []
    transfer: list[tuple[tuple, RubricCriterion]] = []
    for index, criterion in enumerate(rubric.criteria):
        tier = _criterion_tier(criterion)
        entry = (criterion_key(criterion, index), criterion)
        (transfer if tier == "transfer" else core).append(entry)
    core.sort(key=lambda entry: entry[0])
    transfer.sort(key=lambda entry: entry[0])

    def is_uncertain(criterion: RubricCriterion) -> bool:
        return any(
            facet in facet_rank and facet_rank[facet][0] < _STATE_RANK["solid"]
            for facet in criterion_targets(criterion)
        )

    targetless_core = [entry for entry in core if not criterion_targets(entry[1])]
    uncertain_core = [
        entry
        for entry in core
        if criterion_targets(entry[1]) and is_uncertain(entry[1])
    ]
    solid_core = [
        entry
        for entry in core
        if criterion_targets(entry[1]) and not is_uncertain(entry[1])
    ]
    # Targetless does not mean "solid": it means the criterion is deliberately
    # item-local or outside the canonical facet vocabulary. Probe it before
    # transfer, while retaining the reserved transfer slot below.
    ordered = [*uncertain_core, *targetless_core, *transfer, *solid_core]

    max_slots = config.teach_back.max_followups
    selected = [criterion for _key, criterion in ordered[:max_slots]]
    if (
        transfer
        and max_slots >= 2
        and not any(_criterion_tier(criterion) == "transfer" for criterion in selected)
    ):
        # Guaranteed transfer slot: transfer[-1] is the transfer criterion
        # whose target facets are most solid (the sort puts uncertain targets
        # first), keeping core/transfer attribution as clean as possible.
        selected[-1] = transfer[-1][1]

    plan: list[dict[str, Any]] = []
    for criterion in selected:
        plan.append(
            {
                "criterion_id": criterion.id,
                "tier": _criterion_tier(criterion),
                "facet_targets": criterion_targets(criterion),
            }
        )
    return plan


def begin_teach_back(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    opening_md: str,
    config: LearnLoopConfig | None = None,
    clock: Clock | None = None,
) -> TeachBackState:
    """Start a conversation: plan the follow-ups and record the opening turn."""

    if not opening_md.strip():
        raise TeachBackError("Opening explanation must not be empty.")
    planned = plan_followups(vault, repository, item, config=config, clock=clock)
    return TeachBackState(
        practice_item_id=item.id,
        planned=planned,
        turns=[TeachBackTurn(role="learner", content_md=opening_md)],
        conversation_id=new_ulid(),
    )


def next_question(
    vault: LoadedVault,
    state: TeachBackState,
    client: Any,
    *,
    config: LearnLoopConfig | None = None,
) -> tuple[TeachBackState, dict[str, Any] | None]:
    """Generate the next naive-student question via the AI provider.

    Returns ``(state, payload)`` where ``payload`` is ``{question_md,
    criterion_id, tier, facet_targets, question_number, remaining}`` — or
    ``(state, None)`` when the plan (or ``max_followups``) is exhausted. The
    question is appended to ``state.turns`` and ``asked_count`` advances.
    Provider errors propagate (``CodexUnavailable``); the caller may finish
    the conversation with the partial transcript.
    """

    config = config or vault.config
    if state.asked_count >= min(len(state.planned), config.teach_back.max_followups):
        return state, None
    item = vault.practice_items.get(state.practice_item_id)
    if item is None:
        raise TeachBackError(f"Practice item {state.practice_item_id} was not found.")
    selection = state.planned[state.asked_count]
    rubric = _teach_back_rubric(vault, item)
    criterion = next(
        (entry for entry in rubric.criteria if entry.id == selection["criterion_id"]),
        None,
    )
    if criterion is None:
        raise TeachBackError(
            f"Planned criterion {selection['criterion_id']} is not in the rubric for {item.id}."
        )
    learning_object = vault.learning_object_for_item(item)
    context = TeachBackQuestionContext(
        practice_item_id=item.id,
        practice_item_prompt=item.prompt,
        criterion_id=criterion.id,
        criterion_description=criterion.description,
        criterion_tier=str(selection.get("tier") or "core"),
        facet_targets=[str(facet) for facet in selection.get("facet_targets", [])],
        transcript=[{"role": turn.role, "content_md": turn.content_md} for turn in state.turns],
        question_number=state.asked_count + 1,
        max_followups=config.teach_back.max_followups,
        learning_object_title=learning_object.title if learning_object is not None else None,
        learning_object_summary=learning_object.summary if learning_object is not None else None,
    )
    question = client.run_teach_back_question(context)
    question_md = _sanitize_ai_markdown(question.question_md)
    state.turns.append(
        TeachBackTurn(role="ai", content_md=question_md, criterion_id=criterion.id)
    )
    state.asked_count += 1
    return state, {
        "question_md": question_md,
        "criterion_id": criterion.id,
        "tier": str(selection.get("tier") or "core"),
        "facet_targets": [str(facet) for facet in selection.get("facet_targets", [])],
        "question_number": state.asked_count,
        "remaining": min(len(state.planned), config.teach_back.max_followups) - state.asked_count,
    }


def record_answer(state: TeachBackState, answer_md: str) -> TeachBackState:
    """Append the learner's answer to the most recent AI question."""

    if not state.turns or state.turns[-1].role != "ai":
        raise TeachBackError("No open question to answer.")
    state.turns.append(
        TeachBackTurn(
            role="learner",
            content_md=answer_md,
            criterion_id=state.turns[-1].criterion_id,
        )
    )
    return state


def asked_criterion_ids(state: TeachBackState) -> list[str]:
    """Criteria whose question was asked AND answered, in ask order.

    A dangling question with no learner answer (session died mid-turn) is not
    "asked" for grading purposes: the learner never got to respond, so it must
    not score as a failure.
    """

    asked: list[str] = []
    for index, turn in enumerate(state.turns):
        if turn.role != "ai" or turn.criterion_id is None:
            continue
        answered = any(
            later.role == "learner" for later in state.turns[index + 1 :]
        )
        if answered and turn.criterion_id not in asked:
            asked.append(turn.criterion_id)
    return asked


def render_transcript_md(state: TeachBackState, item: PracticeItem) -> str:
    """Render the conversation to Markdown (the graded ``learner_answer_md``)."""

    lines: list[str] = ["# Teach-back transcript", ""]
    opening = next((turn for turn in state.turns if turn.role == "learner"), None)
    lines.extend(["## Opening explanation", "", (opening.content_md if opening else "").strip(), ""])
    question_number = 0
    turns = list(state.turns)
    for index, turn in enumerate(turns):
        if turn.role != "ai":
            continue
        question_number += 1
        criterion_note = f" (criterion: {turn.criterion_id})" if turn.criterion_id else ""
        lines.extend([f"## Follow-up {question_number}{criterion_note}", ""])
        lines.extend(
            [
                f"**Student asked:** {_sanitize_ai_markdown(turn.content_md).strip()}",
                "",
            ]
        )
        answer = next(
            (later for later in turns[index + 1 :] if later.role == "learner"),
            None,
        )
        if answer is not None:
            lines.extend([f"**Learner answered:** {answer.content_md.strip()}", ""])
        else:
            lines.extend(["*(no answer recorded)*", ""])
    return "\n".join(lines).strip() + "\n"


def finish_teach_back(
    vault: LoadedVault,
    repository: Repository,
    state: TeachBackState,
    client: Any,
    *,
    session_id: str | None = None,
    latency_seconds: int | None = None,
    agent_run_id: str | None = None,
    clock: Clock | None = None,
) -> TeachBackFinishResult:
    """Grade the whole transcript as ONE ``teach_back`` attempt.

    Uses the EXISTING grading path (``run_grading_proposal`` + proposal
    validation) with the grading-context rubric restricted to the asked
    criteria, then records the attempt through ``apply_attempt`` with
    ``attempt_type="teach_back"`` and ``hints_used=0``. Works with fewer
    questions asked than planned (provider failure mid-conversation); with no
    answered follow-up at all, the opening explanation is graded against the
    core-tier criteria.
    """

    item = vault.practice_items.get(state.practice_item_id)
    if item is None:
        raise TeachBackError(f"Practice item {state.practice_item_id} was not found.")
    rubric = _teach_back_rubric(vault, item)
    asked = asked_criterion_ids(state)
    if not asked:
        # Nothing was asked/answered: the opening explanation still teaches the
        # core surface, so grade it against the core-tier criteria.
        asked = [criterion.id for criterion in core_criteria(rubric)]
    asked_criteria = [criterion for criterion in rubric.criteria if criterion.id in asked]
    if not asked_criteria:
        raise TeachBackError(f"No gradable rubric criteria for {item.id}.")

    transcript_md = render_transcript_md(state, item)
    attempt_id = new_ulid()
    context = build_grading_context(
        vault, item, attempt_id=attempt_id, learner_answer_md=transcript_md
    )
    context = restrict_grading_context_to_criteria(context, item, rubric, asked_criteria)
    proposal = client.run_grading_proposal(context)
    try:
        validated = validate_codex_grading_proposal(
            proposal,
            attempt_id=attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=transcript_md,
        )
    except GradingValidationError as exc:
        raise AttemptValidationError(str(exc)) from exc

    now_iso = utc_now_iso(clock)
    asked_set = set(asked)
    graded_evidence = [
        evidence for evidence in validated.criterion_evidence if evidence.criterion_id in asked_set
    ]
    criterion_points = {evidence.criterion_id: evidence.points_awarded for evidence in graded_evidence}
    rubric_score = asked_rubric_score(rubric, asked_criteria, criterion_points, validated.fatal_errors)
    evidence_rows = [
        {
            "id": new_ulid(),
            "criterion_id": evidence.criterion_id,
            "points_awarded": evidence.points_awarded,
            "evidence": evidence.evidence,
            "notes": evidence.notes,
            "agent_run_id": agent_run_id,
            "local_grader_id": None,
            "grader_tier": 3,
            "learner_confidence": evidence.learner_confidence,
            "created_at": now_iso,
        }
        for evidence in graded_evidence
    ]
    grade = ResolvedGrade(
        rubric_score=rubric_score,
        criterion_points=criterion_points,
        evidence_rows=evidence_rows,
        error_attributions=[
            GradeAttribution(
                error_type=attribution.error_type,
                severity=attribution.severity,
                evidence=attribution.evidence,
                is_misconception=attribution.is_misconception,
                target_evidence_families=list(attribution.target_evidence_families or []),
                target_criterion_ids=list(attribution.target_criterion_ids or []),
            )
            for attribution in validated.error_attributions
        ],
        grader_confidence=validated.grader_confidence,
        confidence=None,
        manual_review_reason=validated.manual_review_reason,
        feedback_md=validated.feedback_md,
        repair_suggestions=list(validated.repair_suggestions or []),
        fatal_errors=list(validated.fatal_errors),
    )
    draft = AttemptDraft(
        practice_item_id=item.id,
        learner_answer_md=transcript_md,
        attempt_type=TEACH_BACK_ATTEMPT_TYPE,
        hints_used=0,
        latency_seconds=latency_seconds,
        session_id=session_id,
    )
    result = apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(draft=draft, attempt_id=attempt_id, grade=grade),
        clock=clock,
    )
    return TeachBackFinishResult(
        attempt=result,
        transcript_md=transcript_md,
        asked_criterion_ids=list(asked),
        graded_criterion_ids=sorted(criterion_points),
    )


def core_criteria(rubric: Rubric) -> list[RubricCriterion]:
    """Core-tier criteria of a rubric (the fallback graded set)."""

    return [criterion for criterion in rubric.criteria if _criterion_tier(criterion) == "core"]


def restrict_grading_context_to_criteria(
    context: Any,
    item: PracticeItem,
    rubric: Rubric,
    criteria: list[RubricCriterion],
) -> Any:
    """Restrict a grading context's rubric + facet weights to ``criteria``.

    Shared by ``finish_teach_back`` and the teach-back regrade path so both
    grade against exactly the asked/graded criterion subset — unasked criteria
    are never shown to the grader and never produce evidence.
    """

    restricted_rubric = Rubric(
        max_points=rubric.max_points,
        criteria=list(criteria),
        fatal_errors=rubric.fatal_errors,
    )
    criterion_ids = {criterion.id for criterion in criteria}
    full_weights = criterion_facet_weights_for_item(item, rubric)
    return dataclass_replace(
        context,
        rubric=restricted_rubric.model_dump(mode="json", exclude_none=False),
        criterion_facet_weights={
            criterion_id: weights
            for criterion_id, weights in full_weights.items()
            if criterion_id in criterion_ids
        },
    )


def asked_rubric_score(
    rubric: Rubric,
    asked_criteria: list[RubricCriterion],
    criterion_points: Mapping[str, float],
    fatal_errors: list[str],
) -> int:
    """Rubric score normalized over the asked criteria's points.

    Unasked criteria must not depress LO-level correctness, so the score
    fraction is computed over the asked subset and projected back onto the
    rubric's 0..max_points scale, then fatal-error caps apply as usual.
    """

    asked_max = sum(max(float(criterion.points), 0.0) for criterion in asked_criteria)
    awarded = sum(max(float(points), 0.0) for points in criterion_points.values())
    fraction = min(1.0, awarded / asked_max) if asked_max > 0 else 0.0
    score = int(round(fraction * float(rubric.max_points)))
    score = max(0, min(int(rubric.max_points), score, 4))
    fatal_by_id = {fatal_error.id: fatal_error for fatal_error in rubric.fatal_errors}
    for fatal_error_id in fatal_errors:
        fatal = fatal_by_id.get(fatal_error_id)
        if fatal is not None:
            score = min(score, fatal.max_grade)
    return max(0, min(score, 4))


def _teach_back_rubric(vault: LoadedVault, item: PracticeItem) -> Rubric:
    try:
        return resolved_rubric(vault, item)
    except GradingValidationError as exc:
        raise TeachBackError(str(exc)) from exc


def ensure_teach_back_item(
    root,
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    source_practice_item_id: str | None = None,
    authoring_client: Any | None = None,
    quest_sentence: str | None = None,
    clock: Clock | None = None,
) -> tuple[str, bool]:
    """Find or mint a learner-requested teach-back card.

    A request through ``source_practice_item_id`` is a transformation of that
    exact item, not an LO-wide singleton. The configured model authors the
    learner-facing prompt, criteria, honest facet links, and transfer scenario
    from a bounded source contract. The highest-priority relevant active goal
    supplies explicit learner intent or a narrower operational quest, which may
    shape only the transfer criterion. Invalid or unavailable model output
    falls back to a conservative source-specific contract whose criteria are
    item-local.

    Direct LO requests retain the legacy LO-wide behavior because they have no
    source task to preserve. Returns ``(practice_item_id, created)``.
    """

    from learnloop.vault.writer import upsert_practice_item

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise TeachBackError(f"Learning object {learning_object_id} was not found.")

    if source_practice_item_id is None:
        return _ensure_lo_wide_teach_back_item(
            root,
            vault,
            repository,
            learning_object_id,
            clock=clock,
        )

    source_item = vault.practice_items.get(source_practice_item_id)
    if source_item is None:
        raise TeachBackError(f"Practice item {source_practice_item_id} was not found.")
    if source_item.learning_object_id != learning_object_id:
        raise TeachBackError(
            f"Practice item {source_practice_item_id} does not belong to {learning_object_id}."
        )
    if source_item.practice_mode == TEACH_BACK_PRACTICE_MODE and source_item.status != "retired":
        return source_item.id, False

    quest_id = None
    quest_basis = "provided" if quest_sentence is not None else None
    if quest_sentence is None:
        quest_id, quest_sentence, quest_basis = _active_quest_for_learning_object(
            vault, repository, learning_object_id
        )
    for item in vault.practice_items.values():
        source_contract = getattr(item, "teach_back_source", None)
        if (
            item.practice_mode == TEACH_BACK_PRACTICE_MODE
            and item.status != "retired"
            and source_contract is not None
            and source_contract.source_practice_item_id == source_item.id
            and source_contract.source_updated_at == source_item.updated_at
            and source_contract.compiler_version == TEACH_BACK_COMPILER_VERSION
            and source_contract.quest_id == quest_id
            and source_contract.quest_sentence == quest_sentence
            and source_contract.quest_basis == quest_basis
        ):
            return item.id, False

    context, source_criteria = _teach_back_authoring_context(
        vault,
        source_item,
        learning_object,
        quest_sentence=quest_sentence,
    )
    authored = _run_teach_back_authoring(
        authoring_client,
        context,
        source_criteria=source_criteria,
        allowed_facet_ids=set(source_item.evidence_facets),
        learning_object_title=learning_object.title,
    )
    authoring_mode = "ai"
    if authored is None:
        authoring_mode = "deterministic_fallback"
        authored = _fallback_teach_back_authoring(
            source_item,
            source_criteria,
            quest_sentence=quest_sentence,
        )

    criteria, criterion_facet_weights = _compiled_teach_back_criteria(authored)
    trace_contract = source_item.trace_contract or authored.trace_contract
    item_id = f"pi_{learning_object_id.removeprefix('lo_')}_teach_back_{new_ulid().lower()[-6:]}"
    now = utc_now_iso(clock)
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": learning_object_id,
            "subjects": list(learning_object.subjects) or None,
            "practice_mode": TEACH_BACK_PRACTICE_MODE,
            "attempt_types_allowed": [TEACH_BACK_ATTEMPT_TYPE],
            "evidence_facets": list(source_item.evidence_facets),
            "evidence_weights": {
                facet_id: float(source_item.evidence_weights.get(facet_id, 1.0))
                for facet_id in source_item.evidence_facets
            },
            "criterion_facet_weights": criterion_facet_weights,
            "trace_contract": (
                trace_contract.model_dump(mode="json", exclude_none=True)
                if trace_contract is not None
                else None
            ),
            "teach_back_source": {
                "source_practice_item_id": source_item.id,
                "source_updated_at": source_item.updated_at,
                "compiler_version": TEACH_BACK_COMPILER_VERSION,
                "quest_id": quest_id,
                "quest_sentence": quest_sentence,
                "quest_basis": quest_basis,
                "quest_connection": authored.quest_connection,
                "authoring_mode": authoring_mode,
            },
            "prompt": authored.prompt_md.strip(),
            "expected_answer": authored.expected_answer_md.strip(),
            "difficulty": source_item.difficulty if source_item.difficulty is not None else 0.6,
            "difficulty_source": source_item.difficulty_source or "author",
            "tags": [
                "teach_back",
                "learner_requested",
                f"teach_back_compiler:{TEACH_BACK_COMPILER_VERSION}",
                f"quest_transfer:{authored.quest_connection}",
            ],
            "grading_rubric": {"max_points": 4, "criteria": criteria, "fatal_errors": []},
            "provenance": {
                "origin": "codex_proposal",
                "source_refs": [{"ref_type": "existing_entity", "ref_id": source_item.id}],
            },
            "created_at": now,
            "updated_at": now,
        },
        clock=clock,
    )
    return item_id, True


def _active_quest_for_learning_object(
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
) -> tuple[str | None, str | None, str | None]:
    """Highest-priority relevant active goal with a resolvable learner quest."""

    from learnloop.services.goal_intent import resolve_goal_quest
    from learnloop.services.goal_projection import resolve_goal_scope

    candidates = []
    for goal in vault.goals:
        if goal.status != "active":
            continue
        if learning_object_id in resolve_goal_scope(vault, goal, repository):
            quest = resolve_goal_quest(goal)
            if quest is not None:
                candidates.append((goal, quest))
    selected = max(
        candidates,
        key=lambda entry: (entry[0].priority, entry[0].id),
        default=None,
    )
    if selected is None:
        return None, None, None
    goal, quest = selected
    return goal.id, quest.sentence, quest.basis


def _teach_back_authoring_context(
    vault: LoadedVault,
    source_item: PracticeItem,
    learning_object,
    *,
    quest_sentence: str | None,
) -> tuple[TeachBackAuthoringContext, list[dict[str, Any]]]:
    rubric = _teach_back_rubric(vault, source_item)
    mapping = criterion_facet_weights_for_item(source_item, rubric)
    source_criteria = [
        {
            "id": criterion.id,
            "description": criterion.description,
            "measurement_status": criterion.measurement_status,
            "facet_ids": [
                str(facet_id)
                for facet_id, weight in (mapping.get(criterion.id) or {}).items()
                if float(weight) > 0
            ],
        }
        for criterion in rubric.criteria
    ]
    if not source_criteria:
        source_criteria = [
            {
                "id": "source_task",
                "description": "Explains the reasoning and method required by the source task.",
                "measurement_status": "item_local",
                "facet_ids": [],
            }
        ]

    allowed_facets = []
    for facet_id in source_item.evidence_facets:
        facet = vault.evidence_facets.get(str(facet_id))
        allowed_facets.append(
            {
                "id": str(facet_id),
                "title": getattr(facet, "title", None),
                "description": (
                    getattr(facet, "description", None)
                    or getattr(facet, "claim", None)
                ),
            }
        )
    context = TeachBackAuthoringContext(
        source_practice_item_id=source_item.id,
        source_prompt=source_item.prompt,
        source_expected_answer=source_item.expected_answer,
        source_criteria=source_criteria,
        source_trace_contract=(
            source_item.trace_contract.model_dump(mode="json", exclude_none=True)
            if source_item.trace_contract is not None
            else None
        ),
        allowed_facets=allowed_facets,
        learning_object_title=learning_object.title,
        learning_object_summary=learning_object.summary or "",
        quest_sentence=quest_sentence,
    )
    return context, source_criteria


def _run_teach_back_authoring(
    client: Any | None,
    context: TeachBackAuthoringContext,
    *,
    source_criteria: list[dict[str, Any]],
    allowed_facet_ids: set[str],
    learning_object_title: str,
) -> TeachBackAuthoring | None:
    run = getattr(client, "run_teach_back_authoring", None)
    if not callable(run):
        return None
    try:
        authored = TeachBackAuthoring.model_validate(run(context))
        _validate_teach_back_authoring(
            authored,
            source_criteria=source_criteria,
            allowed_facet_ids=allowed_facet_ids,
            quest_sentence=context.quest_sentence,
            learning_object_title=learning_object_title,
        )
        return authored
    except Exception as exc:  # noqa: BLE001 - invalid provider output degrades safely
        LOG.warning("teach-back authoring fell back for %s: %s", context.source_practice_item_id, exc)
        return None


def _validate_teach_back_authoring(
    authored: TeachBackAuthoring,
    *,
    source_criteria: list[dict[str, Any]],
    allowed_facet_ids: set[str],
    quest_sentence: str | None,
    learning_object_title: str,
) -> None:
    if not authored.prompt_md.strip() or not authored.expected_answer_md.strip():
        raise TeachBackError("AI-authored teach-back prompt and expected answer must be non-empty.")
    generic_prefix = f"teach this to a curious student: {learning_object_title}".casefold()
    if authored.prompt_md.strip().casefold().startswith(generic_prefix):
        raise TeachBackError("AI-authored teach-back collapsed to the broad Learning Object title.")
    if not 1 <= len(authored.core_criteria) <= 3:
        raise TeachBackError("AI-authored teach-back must contain one to three core criteria.")
    if authored.transfer_criterion is None or not authored.transfer_scenario.strip():
        raise TeachBackError("AI-authored teach-back must contain one concrete transfer scenario.")

    required_ids = {str(entry["id"]) for entry in source_criteria}
    core_ids = [
        criterion_id
        for criterion in authored.core_criteria
        for criterion_id in criterion.source_criterion_ids
    ]
    if set(core_ids) != required_ids or len(core_ids) != len(set(core_ids)):
        raise TeachBackError(
            "AI-authored core criteria must cover every source criterion exactly once."
        )
    transfer_ids = set(authored.transfer_criterion.source_criterion_ids)
    if not transfer_ids or not transfer_ids <= required_ids:
        raise TeachBackError("AI-authored transfer criterion has invalid source criterion ids.")

    for criterion in [*authored.core_criteria, authored.transfer_criterion]:
        if not criterion.description.strip():
            raise TeachBackError("AI-authored teach-back criterion description is empty.")
        facets = set(criterion.facet_ids)
        if not facets <= allowed_facet_ids:
            raise TeachBackError("AI-authored teach-back criterion invented a facet id.")
        if criterion.measurement_status in {"item_local", "no_canonical_facet"} and facets:
            raise TeachBackError("Item-local teach-back criteria must have empty facet mappings.")
        if criterion.measurement_status in {"direct", "supporting", "composite"} and not facets:
            raise TeachBackError("Facet-measuring teach-back criteria must name at least one facet.")

    if quest_sentence is None and authored.quest_connection != "no_quest":
        raise TeachBackError("Teach-back declared a quest connection when no quest was supplied.")
    if quest_sentence is not None and authored.quest_connection == "no_quest":
        raise TeachBackError("Teach-back ignored the supplied quest without declaring it irrelevant.")
    if quest_sentence is not None:
        quest_text = quest_sentence.strip().casefold()
        core_text = " ".join(
            [authored.prompt_md, *(criterion.description for criterion in authored.core_criteria)]
        ).casefold()
        if quest_text and quest_text in core_text:
            raise TeachBackError("The quest sentence may shape only the transfer criterion.")
    if (
        authored.transfer_criterion.facet_ids
        and authored.transfer_criterion.measurement_status != "supporting"
    ):
        raise TeachBackError("Quest/transfer facet mappings must be supporting evidence.")


def _fallback_teach_back_authoring(
    source_item: PracticeItem,
    source_criteria: list[dict[str, Any]],
    *,
    quest_sentence: str | None,
) -> TeachBackAuthoring:
    """Conservative source-specific fallback: useful wording, zero false facet links."""

    group_count = min(3, len(source_criteria))
    groups: list[list[dict[str, Any]]] = [[] for _ in range(group_count)]
    for index, criterion in enumerate(source_criteria):
        groups[min(index, group_count - 1)].append(criterion)
    core = [
        TeachBackCriterionDraft(
            description="Explains how and why the source solution "
            + " and ".join(str(entry["description"]).rstrip(".") for entry in group)
            + ".",
            source_criterion_ids=[str(entry["id"]) for entry in group],
            measurement_status="item_local",
            facet_ids=[],
        )
        for group in groups
    ]
    answer = (
        source_item.expected_answer
        if isinstance(source_item.expected_answer, str)
        else json.dumps(source_item.expected_answer, sort_keys=True, ensure_ascii=False)
    )
    return TeachBackAuthoring(
        prompt_md=(
            "Teach a curious student how to reason through this completed task:\n\n"
            f"{source_item.prompt}\n\n"
            "Explain the method, the important decisions, and why the result follows. "
            "The student will ask follow-up questions."
        ),
        expected_answer_md=(
            "A clear explanation of the reasoning and method behind the source answer:\n\n"
            + answer
        ),
        core_criteria=core,
        transfer_criterion=TeachBackCriterionDraft(
            description=(
                "Explains how the same reasoning would adapt to a nearby edge case "
                "or changed assumption in the source task."
            ),
            source_criterion_ids=[str(entry["id"]) for entry in source_criteria],
            measurement_status="item_local",
            facet_ids=[],
        ),
        transfer_scenario=(
            "Change one assumption or boundary condition in the source task and explain "
            "which parts of the method stay valid."
        ),
        quest_connection="not_relevant" if quest_sentence else "no_quest",
        trace_contract=None,
    )


def _compiled_teach_back_criteria(
    authored: TeachBackAuthoring,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, float]]]:
    core_points = 3.0 / len(authored.core_criteria)
    criteria: list[dict[str, Any]] = []
    mappings: dict[str, dict[str, float]] = {}
    for index, draft in enumerate(authored.core_criteria, start=1):
        criterion_id = f"criterion_teach_{index}"
        criteria.append(
            {
                "id": criterion_id,
                "points": core_points,
                "tier": "core",
                "description": draft.description.strip(),
                "measurement_status": draft.measurement_status,
            }
        )
        if draft.facet_ids:
            mappings[criterion_id] = {
                facet_id: 1.0 / len(draft.facet_ids) for facet_id in draft.facet_ids
            }

    transfer = authored.transfer_criterion
    assert transfer is not None  # validated or constructed by the fallback
    criteria.append(
        {
            "id": "criterion_teach_transfer",
            "points": 1.0,
            "tier": "transfer",
            "description": (
                transfer.description.strip()
                + "\n\nTransfer scenario: "
                + authored.transfer_scenario.strip()
            ),
            "measurement_status": transfer.measurement_status,
        }
    )
    if transfer.facet_ids:
        mappings["criterion_teach_transfer"] = {
            facet_id: 1.0 / len(transfer.facet_ids) for facet_id in transfer.facet_ids
        }
    return criteria, mappings


def _ensure_lo_wide_teach_back_item(
    root,
    vault: LoadedVault,
    repository: Repository,
    learning_object_id: str,
    *,
    clock: Clock | None,
) -> tuple[str, bool]:
    """Compatibility path for direct LO requests with no source item."""

    from learnloop.services.facet_diagnostics import required_facets
    from learnloop.vault.writer import upsert_practice_item

    learning_object = vault.learning_objects[learning_object_id]
    for item in vault.practice_items.values():
        if (
            item.learning_object_id == learning_object_id
            and item.practice_mode == TEACH_BACK_PRACTICE_MODE
            and item.status != "retired"
        ):
            return item.id, False

    facet_ids = sorted(required_facets(vault, learning_object_id, repository))
    if not facet_ids:
        raise TeachBackError(
            f"Learning object {learning_object_id} has no assessable facets to teach back."
        )
    view = mastery_diagnostic_view(vault, repository, learning_object_id, clock=clock)
    uncertainty = {
        str(entry["facet_id"]): float(entry.get("uncertainty") or 0.0)
        for entry in view["facets"]
    }
    chosen = sorted(facet_ids, key=lambda facet: (-uncertainty.get(facet, 0.0), facet))[:4]

    def facet_line(facet_id: str) -> str:
        facet = vault.evidence_facets.get(facet_id)
        label = (
            (getattr(facet, "title", None) or getattr(facet, "description", None))
            if facet is not None
            else None
        )
        return label or facet_id.removeprefix("facet_").replace("_", " ")

    points = 3.0 / len(chosen)
    criteria = [
        {
            "id": f"criterion_teach_{index}",
            "points": points,
            "tier": "core",
            "description": f"Explains: {facet_line(facet_id)}.",
            "measurement_status": "direct",
        }
        for index, facet_id in enumerate(chosen, start=1)
    ]
    criteria.append(
        {
            "id": "criterion_teach_transfer",
            "points": 1.0,
            "tier": "transfer",
            "description": (
                "Handles an edge case, changed assumption, or transfer scenario for: "
                f"{facet_line(chosen[0])}."
            ),
            "measurement_status": "direct",
        }
    )
    item_id = f"pi_{learning_object_id.removeprefix('lo_')}_teach_back_{new_ulid().lower()[-6:]}"
    now = utc_now_iso(clock)
    upsert_practice_item(
        root,
        {
            "id": item_id,
            "learning_object_id": learning_object_id,
            "subjects": list(learning_object.subjects) or None,
            "practice_mode": TEACH_BACK_PRACTICE_MODE,
            "attempt_types_allowed": [TEACH_BACK_ATTEMPT_TYPE],
            "evidence_facets": chosen,
            "evidence_weights": {facet_id: 1.0 for facet_id in chosen},
            "criterion_facet_weights": {
                **{
                    f"criterion_teach_{index}": {facet_id: 1.0}
                    for index, facet_id in enumerate(chosen, start=1)
                },
                "criterion_teach_transfer": {chosen[0]: 1.0},
            },
            "prompt": (
                f"Teach this to a curious student: {learning_object.title}. "
                "Explain it in your own words — the student will ask follow-up questions."
            ),
            "expected_answer": "A full explanation covering: "
            + "; ".join(facet_line(facet_id) for facet_id in chosen)
            + ".",
            "difficulty": 0.6,
            "difficulty_source": "author",
            "tags": ["teach_back", "learner_requested"],
            "grading_rubric": {"max_points": 4, "criteria": criteria, "fatal_errors": []},
            "provenance": {"origin": "human"},
            "created_at": now,
            "updated_at": now,
        },
        clock=clock,
    )
    return item_id, True


def _facet_ranks(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    clock: Clock | None,
) -> dict[str, tuple[int, float, str]]:
    """Uncertainty rank per item facet, from the diagnostic read path.

    ``mastery_diagnostic_view`` already folds recent unresolved tutor
    questions into displayed uncertainty (the tutor-question bump), so a
    facet the learner keeps asking about ranks as uncertain here too. Lower
    tuple sorts first (more uncertain).
    """

    view = mastery_diagnostic_view(vault, repository, item.learning_object_id, clock=clock)
    view_by_facet = {str(entry["facet_id"]): entry for entry in view["facets"]}
    ranks: dict[str, tuple[int, float, str]] = {}
    for facet in item.evidence_facets:
        facet_id = str(facet)
        entry = view_by_facet.get(facet_id) or view_by_facet.get(vault.canonical_facet_id(facet_id))
        state = str(entry["state"]) if entry is not None else "unexamined"
        uncertainty = float(entry.get("uncertainty") or 0.0) if entry is not None else 0.0
        ranks[facet_id] = (
            _STATE_RANK.get(state, _STATE_RANK["unexamined"]),
            -uncertainty,
            facet_id,
        )
    return ranks
