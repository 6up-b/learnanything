"""The ``DiagnosisProposal`` contract and the diagnoser prompt (Slice 1 §5.3).

The diagnoser explains a blind-graded failure across time. It proposes level-4
hypotheses only: causes, cross-attempt patterns, prerequisite gaps, registry
matches and instructional repairs. It never grades and never writes evidence.

Generation order is part of the contract. In ``exact`` mode ``analysis_md``
comes first. Every other mode recites ``evidence_attempt_ids`` FIRST (§5.2's
recite-first rule), which partly offsets long-context degradation and makes
references to history that does not exist countable. The two orders are two
wire models with identical fields; :func:`as_diagnosis_proposal` normalizes
either to :class:`DiagnosisProposal`.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from learnloop.ai.schemas import AttributionTargetRef, CandidateCause, WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation
from learnloop.attempts.ai_contracts import (
    ELICITING_REVEAL_BUDGET_DEFAULT,
    PostdictiveClaim,
    RepairVerificationRequest,
)
from learnloop.diagnosis.split.context import AssembledContext
from learnloop.diagnosis.split.settings import DIAGNOSIS_PROMPT_VERSION
from learnloop.diagnosis.split.workbench_trace import SUFFIX as WORKBENCH_TRACE_SUFFIX

CAUSAL_CLASSES = ("learner_state", "transient_execution", "unknown")
PATTERN_RELATIONS = ("same_mechanism", "same_prerequisite_gap", "disconfirming")
#: ``pattern_claims[].hypothesis_ref`` names a proposed cause as
#: ``cause:<event_index>:<cause_index>``; anything else is a prior hypothesis id.
CAUSE_REF_PREFIX = "cause:"


class RegistryMatch(WireModel):
    """Replaces the ``misconception_match`` call (§5.3, §7.3)."""

    kind: Literal["durable", "candidate", "new", "abstain"]
    id: str | None = Field(
        default=None,
        description="REQUIRED for durable/candidate: an id from registry_candidates.",
    )
    statement: str | None = Field(
        default=None,
        description="REQUIRED for new: the belief in learner-model terms.",
    )


class HistoryChangedCause(WireModel):
    changed: bool
    note: str = Field(
        default="",
        description="Why a prior hypothesis does not explain this trace, when changed=true.",
    )


class EventDiagnosis(WireModel):
    """One per blind-grade error attribution, keyed by its index."""

    event_index: int = Field(ge=0)
    first_divergence_quote: str | None = None
    causal_class: Literal["learner_state", "transient_execution", "unknown"]
    candidate_causes: list[CandidateCause] = Field(default_factory=list)
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    operation: str | None = Field(
        default=None,
        pattern=r"^[a-z][a-z0-9_]*$",
        # Live M2 runs: without this the model wrote a phrase here and every
        # diagnosis paid a JSON-repair turn.
        description="A snake_case identifier for the failed operation (e.g. apply_basis_coordinates), never a phrase; null if none.",
    )
    causal_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    postdictive_claims: list[PostdictiveClaim] = Field(default_factory=list)
    soft_postdictive_claims: list[str] = Field(default_factory=list)
    registry_match: RegistryMatch
    prior_hypothesis_id: str | None = Field(
        default=None,
        description="The prior_hypotheses id this event's primary cause continues, if any.",
    )
    history_changed_cause: HistoryChangedCause


class DiagnosisRepairSuggestion(WireModel):
    """The instructional repair fields the grader no longer owns (§4.2)."""

    repaired_trace_id: str | None = Field(
        default=None,
        description="The blind grade's repaired trace this repair builds on, if any.",
    )
    practice_mode: str
    rationale: str
    learning_object_id: str | None = None
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)
    operator: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    target_refs: list[AttributionTargetRef] = Field(default_factory=list)
    preserve_refs: list[AttributionTargetRef] = Field(default_factory=list)
    expected_minutes: float | None = Field(default=None, ge=0.0)
    answer_reveal_budget: float = Field(default=0.0, ge=0.0, le=1.0)
    eliciting_question: str | None = None
    expected_response_contract: str | None = None
    verification_request: RepairVerificationRequest | None = None

    @model_validator(mode="after")
    def validate_eliciting(self) -> "DiagnosisRepairSuggestion":
        if (self.operator or "").startswith("elicit_"):
            if not (self.eliciting_question or "").strip():
                raise ValueError("an elicit_* repair operator requires a non-empty eliciting_question")
            if "answer_reveal_budget" not in self.model_fields_set:
                self.answer_reveal_budget = ELICITING_REVEAL_BUDGET_DEFAULT
                self.__pydantic_fields_set__.add("answer_reveal_budget")
        return self


class Citation(WireModel):
    attempt_id: str
    quote: str = Field(description="VERBATIM text copied from that attempt's learner answer.")


class PatternClaim(WireModel):
    """A cross-attempt claim; shadow in S1 (§8)."""

    hypothesis_ref: str
    relation: Literal["same_mechanism", "same_prerequisite_gap", "disconfirming"]
    cited: list[Citation] = Field(default_factory=list)
    counterevidence_attempt_ids: list[str] = Field(default_factory=list)


class PrerequisiteGapHypothesis(WireModel):
    prerequisite_ref: str = Field(description="A learning object or facet id from the neighborhood.")
    cited_attempt_ids: list[str] = Field(default_factory=list)
    demonstrated_counterevidence_ids: list[str] = Field(default_factory=list)
    suggested_discriminator_md: str


class Abstention(WireModel):
    scope: str = Field(description="What you abstain on, e.g. 'event:0', 'pattern', 'prerequisite'.")
    reason: str


class DiagnosisProposal(WireModel):
    """``exact`` order: the analysis first."""

    analysis_md: str
    evidence_attempt_ids: list[str] = Field(default_factory=list)
    event_diagnoses: list[EventDiagnosis] = Field(default_factory=list)
    repair_suggestions: list[DiagnosisRepairSuggestion] = Field(default_factory=list)
    pattern_claims: list[PatternClaim] = Field(default_factory=list)
    prerequisite_gap_hypotheses: list[PrerequisiteGapHypothesis] = Field(default_factory=list)
    abstentions: list[Abstention] = Field(default_factory=list)


class RecitingDiagnosisProposal(WireModel):
    """``full`` / ``snapshot`` / ``hybrid`` order: recite the evidence first."""

    evidence_attempt_ids: list[str] = Field(default_factory=list)
    analysis_md: str
    event_diagnoses: list[EventDiagnosis] = Field(default_factory=list)
    repair_suggestions: list[DiagnosisRepairSuggestion] = Field(default_factory=list)
    pattern_claims: list[PatternClaim] = Field(default_factory=list)
    prerequisite_gap_hypotheses: list[PrerequisiteGapHypothesis] = Field(default_factory=list)
    abstentions: list[Abstention] = Field(default_factory=list)


def proposal_model_for(mode: str) -> type[DiagnosisProposal] | type[RecitingDiagnosisProposal]:
    return DiagnosisProposal if mode == "exact" else RecitingDiagnosisProposal


def as_diagnosis_proposal(value: DiagnosisProposal | RecitingDiagnosisProposal) -> DiagnosisProposal:
    if isinstance(value, DiagnosisProposal):
        return value
    return DiagnosisProposal.model_validate(value.model_dump(mode="json", exclude_unset=False))


_TASK = (
    "You are LearnLoop's DIAGNOSTICIAN. The current answer has already been graded "
    "BLIND by a separate grader (`current_attempt.blind_grade`); you never re-grade "
    "it, and nothing you write changes the grade or counts as evidence. Explain WHY "
    "this answer went wrong, across time when history helps. Explain this trace "
    "first; history can support or contradict a hypothesis, never replace evidence "
    "in this trace. A prior cause may have changed. "
    "Write one `event_diagnoses` entry per blind-grade error attribution, with "
    "`event_index` equal to that attribution's index and its first-divergence quote. "
    "`causal_class` is learner_state (a durable state of knowledge or belief), "
    "transient_execution (a slip or lapse on this occasion), or unknown. Assign a "
    "class other than unknown ONLY to events whose `validity_scope` is "
    "valid_measurement; for any other scope set unknown and add an abstention. "
    "Draft `candidate_causes` as a SET in ONE pass: the roughly 3-5 genuinely "
    "distinct explanations of this trace together, each with a `prior_weight` (your "
    "verbalized relative plausibility, any non-negative scale, never a calibrated "
    "probability) and `discriminating_predictions` of the form \"if this cause is "
    "true, we'd observe X on Y\". Two candidates that predict the same observations "
    "are the same candidate: merge them. Fewer than three is correct when the trace "
    "underdetermines less. Write each `statement` as plain prose about what the "
    "learner did or believed; `mechanism` is optional. When the cause is a durable "
    "belief, state `misconception_statement` in learner-model terms (what the "
    "learner thinks is true), not a description of the wrong answer, and fill "
    "`misconception_consistent_answer` when you can. Postdictive claims are "
    "deterministic implications only. `causal_confidence` is a model-reported "
    "proposal, never used as a probability. "
    "`registry_match`: when the belief is the same as one in `registry_candidates`, "
    "set kind to that entry's kind (durable or candidate) and give its id; when it "
    "is a belief none of them states, set kind=new with the statement; otherwise "
    "abstain. Never pick the closest entry when none fits. `prior_hypothesis_id`: "
    "the id from `prior_hypotheses` your primary cause continues, or null. "
    "`history_changed_cause`: set changed=true with a note when a prior hypothesis "
    "for this learning object does NOT explain this trace. Prior hypotheses are "
    "typed claims with a status; do not revive a refuted or withdrawn one without "
    "new evidence in THIS trace. You see prior GRADES, never prior diagnosis prose. "
    "`repair_suggestions`: instructional repairs. When the mechanism is a durable "
    "wrong belief, DEFAULT to an eliciting repair (an `operator` beginning elicit_, "
    "ONE `eliciting_question` the learner can answer unaided, an "
    "`expected_response_contract`, `answer_reveal_budget` near zero); for a slip or "
    "local execution error, build on the blind grade's repaired trace by citing its "
    "id in `repaired_trace_id`. Target only failed criteria or genuinely implicated "
    "facets; passing evidence for a facet is evidence FOR it, never a repair target. "
    "`pattern_claims`: cross-attempt claims. `hypothesis_ref` is "
    "\"cause:<event_index>:<cause_index>\" for one of your candidate causes, or a "
    "prior hypothesis id. Each `cited` entry names a PRIOR attempt id and a quote "
    "copied VERBATIM, character-for-character, from that attempt's learner answer "
    "or first-divergence quote. Cite only attempts whose blind grade shows a "
    "non-pass on a target overlapping the hypothesis; list in "
    "`counterevidence_attempt_ids` the prior passes the claim must explain away. "
    "`prerequisite_gap_hypotheses`: only for prerequisites listed in "
    "`neighborhood`, citing the failures that suggest the gap and the "
    "demonstrations that argue against it, with one cheap probe that would test it. "
    "Use `abstentions` when the evidence underdetermines a claim. "
    "CLOSED WORLD: every attempt, hypothesis, registry, learning-object, facet and "
    "repaired-trace id you write must appear in the material you were given. Never "
    "invent an id, a date, or an attempt; an unknown id is counted against you. "
    "`evidence_attempt_ids` lists the prior attempts your analysis relies on."
)

_RECITE_FIRST = (
    "RECITE FIRST: write `evidence_attempt_ids` BEFORE `analysis_md` - list the prior "
    "attempts you will rely on, then write the analysis from them. The history is "
    "long; read it all, and prefer an attempt you can cite over a general impression."
)
_ANALYSIS_FIRST = "Write `analysis_md` first, then the structured fields."
_SNAPSHOT_RULES = (
    "READ-ONLY WORKSPACE: your working directory is an as-of export of this "
    "learner's typed history up to (not including) the current attempt: INDEX.md, "
    "attempts/, hypotheses/, registry/, graph/learning_objects.md and repairs/. "
    "Explore it with ordinary file reading (list, search, open) as much as helps, "
    "especially across learning objects and surface families the inline context "
    "does not show. You cannot write files or reach the network. Ids found in "
    "those files count as known; nothing else does."
)


def diagnosis_task(mode: str) -> str:
    rules = [_TASK, _ANALYSIS_FIRST if mode == "exact" else _RECITE_FIRST]
    if mode == "snapshot":
        rules.append(_SNAPSHOT_RULES)
    return " ".join(rules)


def diagnosis_prompt_version(assembled: AssembledContext) -> str:
    """The prompt version; ``+workbench-v1`` only when the current attempt
    carries a workbench step trace (RW2b, spec §5.4)."""

    if isinstance(assembled.current, Mapping) and assembled.current.get("workbench_trace"):
        return f"{DIAGNOSIS_PROMPT_VERSION}{WORKBENCH_TRACE_SUFFIX}"
    return DIAGNOSIS_PROMPT_VERSION


def diagnosis_prompt(assembled: AssembledContext) -> str:
    """The stable instructions first, then the cache-ordered context (§5.2)."""

    header = (
        "learnloop diagnosis proposal\n"
        f"prompt_version: {diagnosis_prompt_version(assembled)}\n"
        f"history_mode: {assembled.mode}\n\n"
        "Return only JSON that matches the provided output schema. Do not include "
        "Markdown fences or explanatory prose.\n\n"
    )
    return (
        header
        + "{"
        + f"{json.dumps('task')}: {json.dumps(diagnosis_task(assembled.mode), ensure_ascii=False)}, "
        + f"{json.dumps('context')}: {assembled.rendered()}"
        + "}"
    )


def request_diagnosis_proposal(
    client: OperationClient,
    assembled: AssembledContext,
    *,
    workspace: Path | None = None,
) -> DiagnosisProposal:
    """Run the diagnoser. ``workspace`` is the snapshot export (§5.6).

    Always an isolated turn: a non-snapshot diagnosis sees exactly its
    assembled context, a snapshot diagnosis its context plus the export.
    """

    result = execute_structured_operation(
        client,
        purpose="diagnosis",
        prompt=diagnosis_prompt(assembled),
        result_model=proposal_model_for(assembled.mode),
        workspace=workspace,
        isolated=True,
    )
    return as_diagnosis_proposal(result)


__all__ = [
    "CAUSAL_CLASSES",
    "CAUSE_REF_PREFIX",
    "PATTERN_RELATIONS",
    "Abstention",
    "Citation",
    "DiagnosisProposal",
    "DiagnosisRepairSuggestion",
    "EventDiagnosis",
    "HistoryChangedCause",
    "PatternClaim",
    "PrerequisiteGapHypothesis",
    "RecitingDiagnosisProposal",
    "RegistryMatch",
    "as_diagnosis_proposal",
    "diagnosis_prompt",
    "diagnosis_task",
    "proposal_model_for",
    "request_diagnosis_proposal",
]
