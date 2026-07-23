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
from dataclasses import asdict, dataclass, field, replace as dataclass_replace
from typing import Any, Mapping

from learnloop.clock import Clock, utc_now_iso
from learnloop.codex.client import TeachBackQuestionContext
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

STATE_VERSION = 1

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
                    content_md=str(turn.get("content_md") or ""),
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

    uncertain_core = [entry for entry in core if is_uncertain(entry[1])]
    solid_core = [entry for entry in core if not is_uncertain(entry[1])]
    ordered = [*uncertain_core, *transfer, *solid_core]

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
    state.turns.append(
        TeachBackTurn(role="ai", content_md=question.question_md, criterion_id=criterion.id)
    )
    state.asked_count += 1
    return state, {
        "question_md": question.question_md,
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
        lines.extend([f"**Student asked:** {turn.content_md.strip()}", ""])
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
    clock: Clock | None = None,
) -> tuple[str, bool]:
    """Find or mint the LO's teach-back card (learner opt-in path).

    Teach-back is the highest-mass conversational evidence in the system
    (evidence_mass 0.8), but a learner could only reach it if generation
    happened to author a teach_back item. This makes it an explicit learner
    choice: reuse the LO's active teach_back card if one exists, else mint one
    deterministically — prompt from the LO title, one core criterion per
    required facet (uncertainty-ranked, capped at 4) so ``plan_followups`` has
    real facet targets to interrogate, plus one transfer criterion on the top
    facet so the plan's guaranteed transfer slot has something to escalate to.
    Returns (practice_item_id, created).
    """

    from learnloop.services.facet_diagnostics import required_facets
    from learnloop.vault.writer import upsert_practice_item

    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        raise TeachBackError(f"Learning object {learning_object_id} was not found.")
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
    chosen = sorted(facet_ids, key=lambda f: (-uncertainty.get(f, 0.0), f))[:4]

    def _facet_line(facet_id: str) -> str:
        facet = vault.evidence_facets.get(facet_id)
        label = (facet.title or facet.description) if facet is not None else None
        return label or facet_id.removeprefix("facet_").replace("_", " ")

    # Core criteria split 3 of the 4 rubric points; the transfer criterion
    # takes the last one so total points stay within max_points.
    points = round(3.0 / len(chosen), 2)
    criteria = [
        {
            "id": f"criterion_teach_{index}",
            "points": points,
            "tier": "core",
            "description": f"Explains: {_facet_line(facet_id)}.",
        }
        for index, facet_id in enumerate(chosen, start=1)
    ]
    transfer_facet = chosen[0]
    criteria.append(
        {
            "id": "criterion_teach_transfer",
            "points": 1.0,
            "tier": "transfer",
            "description": (
                "Handles an edge case, changed assumption, or transfer scenario for: "
                f"{_facet_line(transfer_facet)}."
            ),
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
                "criterion_teach_transfer": {transfer_facet: 1.0},
            },
            "prompt": (
                f"Teach this to a curious student: {learning_object.title}. "
                "Explain it in your own words — the student will ask follow-up questions."
            ),
            "expected_answer": "A full explanation covering: "
            + "; ".join(_facet_line(facet_id) for facet_id in chosen)
            + ".",
            "difficulty": 0.6,
            "difficulty_source": "author",
            "tags": ["teach_back", "learner_requested"],
            "grading_rubric": {"max_points": 4, "criteria": criteria, "fatal_errors": []},
            "provenance": {"origin": "human"},  # learner-requested; no agent involved
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
