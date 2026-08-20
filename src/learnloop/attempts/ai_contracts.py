"""Feature-owned structured grading contract."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import Field, model_validator

from learnloop.ai.schemas import AttributionTargetRef, CandidateCause, WireModel
from learnloop.ai.transport import render_structured_prompt

class CriterionEvidence(WireModel):
    criterion_id: str
    points_awarded: float
    evidence: str
    notes: str | None = None
    learner_confidence: Literal["confident", "hedged", "absent", "unknown"] | None = None




class FirstDivergence(WireModel):
    anchor_kind: Literal["span", "between_spans", "missing_required_step", "whole_answer"]
    criterion_id: str
    checkpoint_id: str | None = None
    quote: str | None = None
    quote_hash: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    normalized_quote: str | None = None

    @model_validator(mode="after")
    def validate_offsets(self) -> "FirstDivergence":
        if self.anchor_kind == "missing_required_step" and not self.checkpoint_id:
            raise ValueError(
                "missing_required_step first divergence requires checkpoint_id"
            )
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("first-divergence offsets must be supplied together")
        if (
            self.char_start is not None
            and self.char_end is not None
            and self.char_end < self.char_start
        ):
            raise ValueError("first-divergence char_end must be >= char_start")
        return self


class FacetContrast(WireModel):
    target_facet: str
    confused_with_facet: str
    justification: str

    @model_validator(mode="after")
    def validate_contrast(self) -> "FacetContrast":
        if self.target_facet == self.confused_with_facet:
            raise ValueError("facet contrast requires two distinct facets")
        if not self.justification.strip():
            raise ValueError("facet contrast justification must cite the trace")
        return self




class PostdictiveClaim(WireModel):
    criterion_id: str
    must: Literal["fail", "not_full_credit"]


class RepairedTrace(WireModel):
    """A minimal, auditable edit of the learner's displayed reasoning."""

    learner_work_prefix: str = ""
    repair_insertion_point: FirstDivergence | None = None
    minimal_edit: str
    regenerated_work: str = ""
    repaired_answer_md: str
    changed_latent_claims: list[str] = Field(default_factory=list)
    changed_checkpoint_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_minimal_edit(self) -> "RepairedTrace":
        if not self.minimal_edit.strip():
            raise ValueError("repaired trace requires a non-empty minimal_edit")
        if not self.repaired_answer_md.strip():
            raise ValueError("repaired trace requires repaired_answer_md")
        return self


class RepairVerificationRequest(WireModel):
    """A request for a backend verifier, never a model-supplied verdict.

    ``test_execution`` is requestable but carries no result field: the outcome
    reaches ``validate_repair_candidate`` through its ``execution_result``
    parameter, from a trusted caller. A model that could attach its own
    ``returncode`` would be issuing itself a deterministic verdict.
    """

    kind: Literal["symbolic_equality", "exact_match", "test_execution"]
    assumptions: list[str] = Field(default_factory=list)
    required_assumptions: list[str] = Field(default_factory=list)


class ErrorAttribution(WireModel):
    # Aug C1: checkable artifact before causal structure.  The top-level
    # GradingProposal also places repair_suggestions immediately after prose;
    # within the suggestion this field therefore precedes every causal label.
    # (ErrorAttribution itself contains no repair artifact.)
    error_type: str
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str
    is_misconception: bool = False
    # spec §2.1 (G1): required when is_misconception=True, but not enforced here so
    # legacy providers that omit it still validate — the belief in learner-model
    # terms, and what a holder of the belief would answer on this item.
    misconception_statement: str | None = None
    misconception_consistent_answer: str | None = None
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)
    resolution_status: Literal["resolved", "unresolved", "abstained"] | None = None
    abstention_reason: str | None = None
    cause_scope: Literal[
        "learner_state",
        "transient_execution",
        "interaction_context",
        "item_contract",
        "grader_interpretation",
        "unknown",
    ] | None = None
    target_ref: AttributionTargetRef | None = Field(default=None, discriminator="kind")
    operation: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    first_divergence: FirstDivergence | None = None
    localization_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    causal_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    facet_contrast: FacetContrast | None = None
    candidate_causes: list[CandidateCause] = Field(default_factory=list)
    postdictive_claims: list[PostdictiveClaim] = Field(default_factory=list)
    soft_postdictive_claims: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_abstention(self) -> "ErrorAttribution":
        if self.resolution_status == "abstained" and not (self.abstention_reason or "").strip():
            raise ValueError("abstention_reason is required when resolution_status is abstained")
        return self


#: An eliciting repair shows the learner a divergence anchor and one question.
#: It is not zero — naming where the reasoning first went wrong is itself a
#: partial reveal — but it is an order of magnitude below a spliced solution.
ELICITING_REVEAL_BUDGET_DEFAULT = 0.05


class RepairSuggestion(WireModel):
    # Aug C1 field order is causal under autoregressive decoding: emit the
    # checkable edit before inventing the causal story that explains it.
    repaired_trace: RepairedTrace | None = None
    verification_request: RepairVerificationRequest | None = None
    practice_mode: str
    learning_object_id: str | None = None
    rationale: str
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)
    # P1 structural repair fields. They remain nullable so older/self grading
    # can keep producing the P0 shape without fabricating structure.
    operator: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    target_refs: list[AttributionTargetRef] = Field(default_factory=list)
    preserve_refs: list[AttributionTargetRef] = Field(default_factory=list)
    expected_minutes: float | None = Field(default=None, ge=0.0)
    answer_reveal_budget: float = Field(default=0.0, ge=0.0, le=1.0)
    #: Eliciting repair (misconception-class default). Instead of splicing a
    #: regenerated solution onto the learner's prefix — which hands over the
    #: very production the next attempt is supposed to measure — an eliciting
    #: suggestion names the divergence and asks ONE targeted question the
    #: learner answers unaided.
    eliciting_question: str | None = None
    #: What a correct UNAIDED response to ``eliciting_question`` would
    #: demonstrate. Free text; it is the contract the response is read against,
    #: not a rubric and not a grade.
    expected_response_contract: str | None = None

    @model_validator(mode="after")
    def validate_eliciting(self) -> "RepairSuggestion":
        """Structural only.

        The prompt states WHEN an eliciting suggestion is the right default
        (misconception-class mechanisms) and the grader may override it freely;
        no validator enforces that mapping. What is enforced here is only that
        an ``elicit_*`` operator actually carries the question it promises, and
        that such a suggestion declares the near-zero reveal budget it implies
        when the model left the budget unstated.
        """

        if (self.operator or "").startswith("elicit_"):
            if not (self.eliciting_question or "").strip():
                raise ValueError(
                    "an elicit_* repair operator requires a non-empty eliciting_question"
                )
            if "answer_reveal_budget" not in self.model_fields_set:
                self.answer_reveal_budget = ELICITING_REVEAL_BUDGET_DEFAULT
                # Mark it as set so the grading validator keeps it: the default
                # is a property of the operator, not an unfilled field.
                self.__pydantic_fields_set__.add("answer_reveal_budget")
        return self


class ExercisedFacetObservation(WireModel):
    """One facet the grader saw *exercised* in the trace (Meas §3.A6).

    The most bitter-lesson-aligned field in the grading contract: the model
    observes, the harness decides what the observation is worth. Three bounds,
    and none of them is expressible as a field the model fills in — they are
    enforced by what this schema omits.

    * **Positive only.** There is no polarity. Opportunistic evidence may credit
      a facet; it may never indict one. Indicting a facet the item did not
      intend to measure is exactly the smearing causal §1 principle 5 forbids,
      and there is no criterion to appeal to.
    * **Supporting at most.** There is no ``role``. Everything from this channel
      lands as embedded credit under A1's cap.
    * **No capability.** Standing constraint 8: the rung an observation counts
      at is a deterministic property of the criterion's authored target, never a
      model-reported one.

    ``evidence`` is required. An observation with no citation from the trace is
    an assertion, and this channel exists precisely because the model is
    reporting rather than deciding.
    """

    facet: str
    evidence: str
    criterion_id: str | None = None


class ClarificationRequest(WireModel):
    """One question to the learner that would resolve a hedged grade (Meas §3.A8).

    Bounded below by the schema and above by the validator. The schema forbids
    the shapes that would make it an interrogation:

    * there is no ``answer`` and no ``expected_answer`` — the grader is asking,
      not proposing what it expects to hear, which is the difference between a
      question and a leading one;
    * there is no ``points`` or ``grade`` — an answer never grades itself, it
      triggers a re-grade through the ordinary regrade path;
    * ``reason`` is closed to the three uncertainty shapes §3.A8 names plus a
      method-ambiguity arm and an explicit ``other``.

    The validator then drops any request against a *confident* grade
    (``grading._validated_clarification``): the whole channel is licensed by the
    grader having already said it is unsure.
    """

    question_md: str
    reason: Literal[
        "ambiguous_notation",
        "skipped_step",
        "correct_answer_possibly_invalid_reasoning",
        "method_ambiguity",
        "other",
    ] = "other"
    criterion_id: str | None = None


class DiscriminationProfileMatch(WireModel):
    """Which authored candidate profile the trace matches -- or none (Meas §3.A5).

    THE REJECTION ARM IS THE POINT. §3.A5: a profile is "a candidate set the
    diagnostician may match against and **must be free to reject**, with
    ``no_profile_applies`` a first-class outcome carrying the same weight as any
    named match." So the two arms are siblings in one closed vocabulary rather
    than a nullable ``profile_id`` -- a null would make rejection
    indistinguishable from a model that simply did not answer, and the revert
    criterion ("``no_profile_applies`` rate collapses toward zero") would be
    computed over a denominator that silently absorbed both.

    There is no confidence and no ranking. A profile is a PRIOR over causes
    (causal §1 principle 4), and a scored match would be a posterior the item's
    author wrote before the learner arrived.
    """

    outcome: Literal["matched", "no_profile_applies"]
    profile_id: str | None = Field(
        default=None,
        description="REQUIRED on `matched`; must be one of the item's authored profile ids.",
    )
    evidence: str = Field(
        default="",
        description=(
            "The part of the learner's trace that shows the match. Required on "
            "`matched`: a match with no citation is an assertion."
        ),
    )

    @model_validator(mode="after")
    def validate_match(self) -> "DiscriminationProfileMatch":
        if self.outcome == "matched" and not (self.profile_id or "").strip():
            raise ValueError("a matched discrimination profile requires a profile_id")
        return self


class ReportedError(WireModel):
    """One error the learner claims to have found in an A3 worked solution.

    ``repair_md`` is separate from ``claim_md`` because §3.A3 requires the
    REPAIR, not the flag: "Flagging is recognition; repairing is construction."
    A report with a claim and no repair is recorded as flagged-not-repaired and
    earns no facet credit, which is what keeps A3 on the right side of §11's
    no-recognition-items non-goal.
    """

    location: str = Field(
        default="",
        description="Where in the worked solution the learner says the error is.",
    )
    claim_md: str = Field(description="What the learner says is wrong there.")
    repair_md: str = Field(
        default="",
        description=(
            "The corrected work the learner produced. EMPTY when they only flagged "
            "the error without repairing it."
        ),
    )
    matches_planted_error_id: str | None = Field(
        default=None,
        description=(
            "The item's planted-error id this report corresponds to, or null when "
            "it corresponds to none. Null on a CLEAN solution is the informative "
            "case, not an error."
        ),
    )


class ErrorHuntReport(WireModel):
    """What the learner found and repaired in an A3 item (Meas §3.A3).

    Reported as observations, never as a score. The harness decides what each
    report is worth -- in particular whether a report matching no plant is noise
    (on a seeded solution) or a misconception handed over directly (on a clean
    one), which is a fact about the ITEM the grader is not told and cannot infer.
    """

    reported_errors: list[ReportedError] = Field(default_factory=list)


@dataclass(frozen=True)
class GradingContext:
    attempt_id: str
    practice_item_id: str
    prompt: str
    expected_answer: str
    learner_answer_md: str
    rubric: dict
    evidence_facets: list[str] = field(default_factory=list)
    evidence_weights: dict[str, float] = field(default_factory=dict)
    criterion_facet_weights: dict[str, dict[str, float]] = field(default_factory=dict)
    trace_contract: dict[str, Any] | None = None
    error_taxonomy: dict[str, Any] = field(default_factory=dict)
    facet_registry: list[dict[str, str]] = field(default_factory=list)
    discrimination_profiles: list[dict[str, Any]] = field(default_factory=list)
    clarification_exchange: dict[str, str] | None = None
    error_hunt_solution: str | None = None
    verifier_observations: list[dict[str, Any]] = field(default_factory=list)
    diagnostic_history: list[dict[str, Any]] = field(default_factory=list)


class GradingProposal(WireModel):
    diagnosis_md: str | None = None
    repair_suggestions: list[RepairSuggestion] = Field(default_factory=list)
    attempt_id: str
    practice_item_id: str
    rubric_score: int = Field(ge=0)
    criterion_evidence: list[CriterionEvidence] = Field(default_factory=list)
    fatal_errors: list[str] = Field(default_factory=list)
    error_attributions: list[ErrorAttribution] = Field(default_factory=list)
    grader_confidence: float = Field(ge=0.0, le=1.0)
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    exercised_facets: list[ExercisedFacetObservation] = Field(default_factory=list)
    clarification_request: ClarificationRequest | None = None
    discrimination_profile_match: DiscriminationProfileMatch | None = None
    error_hunt_report: ErrorHuntReport | None = None


GRADING_PROMPT_VERSION = (
    "mvp-1.5-joint-candidate-causes-verbalized-weights-eliciting-repair"
)


def grading_prompt(context: GradingContext) -> str:
    """Render the grading request owned by the attempts domain."""

    return render_structured_prompt(
        "learnloop grading proposal",
        GRADING_PROMPT_VERSION,
        {
            "task": (
                "Grade the learner answer against the prompt, expected answer, and "
                "rubric. Return a LearnLoop GradingProposal as schema-valid JSON only. "
                "Write `diagnosis_md` FIRST, before filling any structured field. "
                "Next construct the smallest `repaired_trace` that preserves the "
                "learner's valid prefix. Only AFTER that checkable repair, fill the "
                "structured causal fields as explanations of the edit. Diagnose the "
                "displayed work in ordinary prose without trying to fit it to the "
                "supplied facet vocabulary; structure only claims that the prose and "
                "repair actually establish. Treat `verifier_observations` as typed "
                "instruments: verified/contradicted may localize a failure, while "
                "parse_failed/unsupported/assumption_missing confer NO support and "
                "must not attract the anchor merely because another part parsed. "
                "`diagnostic_history` contains raw prior traces only. Use it to test "
                "recurrence, but re-diagnose the current trace independently; a prior "
                "cause may have changed. A first_divergence span quote must "
                "be copied VERBATIM from the learner answer — character-for-character, "
                "including whitespace and notation. Leave char_start/char_end null: "
                "offsets are recomputed server-side from the quote, so never count "
                "characters yourself. Locate the EARLIEST incorrect or unsupported "
                "claim, not merely the learner's later admission of uncertainty; do "
                "not preserve an earlier false count, equation, or premise in the "
                "repair prefix. Every named facet must also "
                "appear in diagnosis_md. A missing_required_step divergence must name "
                "a checkpoint_id from the item's trace contract. "
                "For each error_attribution's `error_type`, pick the id from "
                "`error_taxonomy.canonical_error_types` whose `use_when` fits the "
                "observed failure and whose `avoid_when` does not — use ONLY those "
                "ids for ordinary errors. Use existing rubric fatal "
                "error ids or vault-specific taxonomy ids only when they apply more "
                "precisely. Use the retrieval-failure taxonomy id only when the trace "
                "locally supports a failure to access previously learned, "
                "task-relevant knowledge. An expression such as 'I don't know how' "
                "or 'I'm not sure,' or an inability to continue, does not by itself "
                "establish failed retrieval. If the evidence instead identifies a "
                "misunderstanding, unsuitable selection or organization, incorrect "
                "execution or application, transfer or context mismatch, "
                "representation difficulty, or a local omission or slip, classify "
                "that more specific observed mechanism. For each failed rubric "
                "line or facet, add an "
                "error_attribution unless another attribution already covers the same "
                "failure. Set the orthogonal `resolution_status`, `cause_scope`, and "
                "typed `target_ref` axes independently. A facet may be named only "
                "when the failed step exercises that facet's claim; prefer a failed "
                "criterion, item step, answer span, or a reasoned abstention over the "
                "nearest listed facet. `target_evidence_families` may be empty. "
                "Passing evidence for a facet is evidence FOR it, never a repair "
                "target. Set facet_contrast only when the trace explicitly demonstrates "
                "a contract swap, with a trace-citing justification. "
                "When resolution_status is abstained, give a concrete abstention_reason. "
                "When unresolved, draft `candidate_causes` as a SET in ONE pass, "
                "not one at a time: generate the roughly 3-5 genuinely distinct "
                "explanations of this trace TOGETHER, and give each a "
                "`prior_weight` — your verbalized relative plausibility across "
                "that set, any non-negative scale, higher means more likely. "
                "Weights are a prior you are stating out loud, not a "
                "measurement; the system normalizes them and never reads them "
                "as calibrated probabilities. Write each `statement` as plain "
                "prose about what the learner did or believed. There is no "
                "vocabulary to fit, no category to span, and no label you must "
                "produce: a candidate is never wrong for its wording. For each "
                "candidate give `discriminating_predictions` — free-text "
                "falsifiable expectations of the form \"if this cause is true, "
                "we'd observe X on Y\". Those predictions are what make two "
                "candidates DIFFERENT: if two candidates predict the same "
                "observations, they are the same candidate said twice, so MERGE "
                "them. Returning fewer than three candidates is the correct "
                "answer when the trace genuinely underdetermines less; padding "
                "the set with restatements is worse than a short list. "
                "`mechanism` is optional — fill it only when an obvious "
                "mechanism label applies, and leave it null rather than "
                "reaching for the nearest one. The system adds the open-set "
                "H_OTHER arm itself. `localization_confidence` and "
                "`causal_confidence` are separate model-reported proposals, not outcome "
                "confidence or posteriors. `operation` is nullable free snake_case. "
                "For each repair_suggestion, target only failed criterion ids and/or "
                "genuinely implicated evidence facets; both target lists may be empty. "
                "When a safe local repair is supported, structure it with a snake_case "
                "`operator`, typed `target_refs`, `preserve_refs` for demonstrated "
                "work, `expected_minutes`, and the fraction-like "
                "`answer_reveal_budget`. "
                "Choose the repair SHAPE from what went wrong. When the "
                "mechanism is a durable wrong belief — a conceptual or schema "
                "error, a representation/notation confusion, a wrong selection "
                "or plan, a missed condition or assumption, a transfer or "
                "context mismatch — DEFAULT to an ELICITING repair rather than "
                "a spliced solution: use an `operator` beginning `elicit_`, "
                "name the divergence anchor in `target_refs`, ask exactly ONE "
                "targeted `eliciting_question` the learner can answer unaided, "
                "state in `expected_response_contract` what a correct unaided "
                "response would demonstrate, and keep `answer_reveal_budget` "
                "near zero. Showing a believer the corrected work teaches them "
                "to recognize it, not to stop believing what they believe; the "
                "question is what makes their belief speak again. When the "
                "mechanism is instead a slip, a local execution error, or a "
                "retrieval lapse, keep the spliced `repaired_trace` — there is "
                "no belief to elicit and the edit is the whole lesson. This is "
                "a default, not a rule: override it when the trace warrants, "
                "and nothing rejects your choice. "
                "Emit `repaired_trace` only when you can keep "
                "the learner's displayed work verbatim through a supported insertion "
                "point: copy `learner_work_prefix`, state one `minimal_edit`, regenerate "
                "only downstream work in the learner's notation, and enumerate changed "
                "latent claims and authored checkpoint ids. Do not fabricate trace "
                "structure when the item has no reliable decomposition. Request "
                "`symbolic_equality` verification only when the full repaired answer "
                "and authored expected answer are parseable mathematical expressions; "
                "request `exact_match` only when exact text equality is the authored "
                "contract. Never propose a verification verdict. "
                "When an error_attribution sets `is_misconception=true`, "
                "`misconception_statement` is REQUIRED: state the learner's belief "
                "in learner-model terms (what the learner thinks is true), NOT a "
                "description of the wrong answer — e.g. \"believes Q maps standard "
                "vectors to eigenbasis coefficients (reverses Q / Q^T)\", not "
                "\"used Q instead of Q^T\". Also fill "
                "`misconception_consistent_answer` when you can: the answer a holder "
                "of that belief would give on this specific item. "
                "Postdictive claims are deterministic implications only: if the "
                "cause were true, the named criterion must fail or lose full credit. "
                "Use the supplied `error_taxonomy.selection_policy` and "
                "`error_taxonomy.targeting_policy` exactly. Set `rubric_score` to "
                "the rounded sum of awarded criterion points after any fatal-error "
                "cap. The rubric criterion total is the maximum; never normalize or "
                "clamp the score to four. "
                "LAST, fill `exercised_facets`: facets from "
                "`context.facet_registry` that the learner's written work "
                "actually EXERCISES, whether or not this item declares them. "
                "Quote the part of the trace that shows it in `evidence` — an "
                "observation with no citation is not one. This channel is "
                "positive only: it says a facet was used, never that it was "
                "used wrongly, and a facet that appears only in the item's "
                "prompt rather than in the learner's own work was not "
                "exercised. Report at most a handful, and leave it empty when "
                "the work shows nothing beyond the criteria you already "
                "graded; an empty list is the common and correct answer on a "
                "short response. "
                "`clarification_request`: leave it null unless you are "
                "genuinely unsure what the LEARNER did and one question would "
                "settle it - ambiguous notation, a skipped step that is either "
                "fluency or a gap, a correct answer possibly reached by invalid "
                "reasoning, or which of two methods they believed they were "
                "using. Ask at most one, only against a criterion you marked "
                "`learner_confidence='hedged'` or an attribution you marked "
                "`abstained`. NEVER ask about something you could settle "
                "yourself from the item, the expected answer, or the trace - "
                "that is the system's debt, not the learner's. If "
                "`context.clarification_exchange` is present, the learner has "
                "already answered a question about this attempt: grade with "
                "their answer in hand, do not ask again, and if it still does "
                "not settle the matter, abstain rather than guess. "
                "`discrimination_profile_match`: when "
                "`context.discrimination_profiles` is non-empty, the item's "
                "author has written down, per candidate hypothesis, what a "
                "holder of it visibly produces. Treat that list as a PRIOR - a "
                "set of candidates to check the trace against - never as a menu "
                "you must choose from. Set outcome='matched' with the profile_id "
                "and a quote from the learner's work ONLY when the work really "
                "shows that hypothesis; otherwise set "
                "outcome='no_profile_applies', which is a full answer and not a "
                "failure to answer. Picking the closest profile when none fits "
                "is worse than rejecting them all: it replaces what the learner "
                "did with what the author guessed. Leave the field null when "
                "the item lists no profiles. "
                "`error_hunt_report`: when `context.error_hunt_solution` is "
                "present the learner was shown that worked solution and asked "
                "to find and REPAIR whatever is wrong with it. Report each "
                "error they claimed, with where they say it is, what they say "
                "is wrong, and the corrected work they produced - `repair_md` "
                "empty when they only pointed at it without fixing it. You are "
                "NOT told how many errors were planted or where; do not guess "
                "at `matches_planted_error_id` unless the item names the plant "
                "to you. The solution may contain no errors at all, and "
                "reporting that the learner found one in correct work is the "
                "informative outcome, not a mistake to smooth over."
            ),
            "context": asdict(context),
        },
    )


__all__ = ["GRADING_PROMPT_VERSION", "GradingContext", "GradingProposal", "grading_prompt"]
