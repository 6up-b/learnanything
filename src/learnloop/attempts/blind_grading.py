"""The learner-blind grading contract (Slice 1 §4).

The blind grader MEASURES one answer: score, criteria, where the work first
went wrong, the minimal repaired trace and the local error type. It never
explains why across time; that is the diagnoser's job, and the diagnoser may
read history precisely because every grade it reads was produced blind.

Blindness is structural (standing constraint S1). :class:`BlindGradingContext`
has no field that can hold a prior trace, grade, diagnosis, hypothesis,
registry entry or retrieval result, so no configuration value can put learner
history back into the grading prompt. Item-side material stays: prompt,
reference, rubric, trace contract, taxonomy, facet registry, discrimination
profiles, verifier observations and the current attempt's own clarification.

Validation reuses :func:`validate_codex_grading_proposal` through the §4.2
mapping (:func:`to_grading_proposal`), so the blind grade obeys exactly the
scoring, anchoring, repair-splice and passed-facet rules the joint grade does.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from pydantic import Field, model_validator

from learnloop.ai.schemas import AttributionTargetRef, WireModel
from learnloop.ai.transport import (
    OperationClient,
    execute_structured_operation,
    render_structured_prompt,
)
from learnloop.attempts.ai_contracts import (
    ClarificationRequest,
    CriterionEvidence,
    DiscriminationProfileMatch,
    ErrorAttribution,
    ErrorHuntReport,
    ExercisedFacetObservation,
    FacetContrast,
    FirstDivergence,
    GradingContext,
    GradingProposal,
    RepairedTrace,
    RepairSuggestion,
    RepairVerificationRequest,
)
from learnloop.attempts.grading import (
    GradingValidationError,
    ValidatedCodexGrade,
    build_grading_context,
    resolved_rubric,
    validate_codex_grading_proposal,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

#: §4.3. A new prompt identity: the task text carries no causal instruction.
BLIND_GRADING_PROMPT_VERSION = "mvp-2.0-blind-local-grader"
#: §4.3 calibration identity, so calibration never pools joint and blind graders
#: (``attempts/grader_calibration.py`` stamps its own pair into
#: ``raw_grade_events``; these are the blind values M2 stamps there).
BLIND_CALIBRATION_PROMPT_VERSION = "grading_prompt_v2_blind"
BLIND_GRADER_OUTPUT_SCHEMA_VERSION = "blind_grading_proposal_v1"
#: §10: the grader-mode label a blind grade's receipts carry.
GRADER_MODE_BLIND = "blind"

ValidityScope = Literal[
    "valid_measurement",
    "item_contract",
    "grader_interpretation",
    "interaction_context",
    "unknown",
]
VALIDITY_SCOPES: tuple[str, ...] = (
    "valid_measurement",
    "item_contract",
    "grader_interpretation",
    "interaction_context",
    "unknown",
)
#: Validity scopes that gate negative evidence and manual review, carried into
#: the joint vocabulary's ``cause_scope`` unchanged. ``valid_measurement``
#: asserts nothing causal, so it maps to the joint ``unknown`` (the diagnoser,
#: not the grader, owns ``causal_class``; §4.2).
_SCOPE_FOR_VALIDITY = {
    "valid_measurement": "unknown",
    "item_contract": "item_contract",
    "grader_interpretation": "grader_interpretation",
    "interaction_context": "interaction_context",
    "unknown": "unknown",
}
_BLIND_REPAIR_PRACTICE_MODE = "repaired_trace"


@dataclass(frozen=True)
class BlindGradingContext:
    """Today's grading context WITHOUT ``diagnostic_history`` (§4.1).

    A new type rather than an empty list: there is no field here that learner
    history could be written into, so S1 cannot be undone by configuration.
    """

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


class BlindRepairedTrace(WireModel):
    """A minimal edit of THIS answer, with an id the diagnoser's repairs cite."""

    id: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,40}$")
    learner_work_prefix: str = ""
    repair_insertion_point: FirstDivergence | None = None
    minimal_edit: str
    regenerated_work: str = ""
    repaired_answer_md: str
    changed_latent_claims: list[str] = Field(default_factory=list)
    changed_checkpoint_ids: list[str] = Field(default_factory=list)
    verification_request: RepairVerificationRequest | None = None

    @model_validator(mode="after")
    def validate_minimal_edit(self) -> "BlindRepairedTrace":
        if not self.minimal_edit.strip():
            raise ValueError("repaired trace requires a non-empty minimal_edit")
        if not self.repaired_answer_md.strip():
            raise ValueError("repaired trace requires repaired_answer_md")
        return self


class BlindErrorAttribution(WireModel):
    """Localization of one failure, without any causal claim (§4.2 "G" rows)."""

    error_type: str
    severity: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str
    first_divergence: FirstDivergence | None = None
    localization_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    target_evidence_families: list[str] = Field(default_factory=list)
    target_criterion_ids: list[str] = Field(default_factory=list)
    target_ref: AttributionTargetRef | None = Field(default=None, discriminator="kind")
    resolution_status: Literal["resolved", "unresolved", "abstained"] | None = None
    abstention_reason: str | None = None
    validity_scope: ValidityScope = "unknown"
    facet_contrast: FacetContrast | None = None
    repaired_trace_id: str | None = None

    @model_validator(mode="after")
    def validate_abstention(self) -> "BlindErrorAttribution":
        if self.resolution_status == "abstained" and not (self.abstention_reason or "").strip():
            raise ValueError("abstention_reason is required when resolution_status is abstained")
        return self


class BlindGradingProposal(WireModel):
    """§4.2 output. Field order is generation order (§4.3)."""

    local_analysis_md: str
    repaired_traces: list[BlindRepairedTrace] = Field(default_factory=list)
    attempt_id: str
    practice_item_id: str
    criterion_evidence: list[CriterionEvidence] = Field(default_factory=list)
    rubric_score: int = Field(ge=0)
    fatal_errors: list[str] = Field(default_factory=list)
    error_attributions: list[BlindErrorAttribution] = Field(default_factory=list)
    grader_confidence: float = Field(ge=0.0, le=1.0)
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    clarification_request: ClarificationRequest | None = None
    discrimination_profile_match: DiscriminationProfileMatch | None = None
    error_hunt_report: ErrorHuntReport | None = None
    exercised_facets: list[ExercisedFacetObservation] = Field(default_factory=list)


def blind_grading_context(
    vault: LoadedVault,
    item: PracticeItem,
    *,
    attempt_id: str,
    learner_answer_md: str,
    rubric: Rubric | None = None,
    assessment_contract: dict[str, Any] | None = None,
    verifier_observations: list[dict[str, Any]] | None = None,
    clarification_exchange: dict[str, str] | None = None,
) -> BlindGradingContext:
    """Build the blind context from the item contract and this answer only.

    ``verifier_observations`` are the C2 instruments over this answer, supplied
    by the caller (they are item-side: they read nothing but the answer and
    the reference).
    """

    joint = build_grading_context(
        vault,
        item,
        attempt_id=attempt_id,
        learner_answer_md=learner_answer_md,
        rubric=rubric,
        assessment_contract=assessment_contract,
    )
    return blind_context_from_grading_context(
        joint,
        verifier_observations=verifier_observations,
        clarification_exchange=clarification_exchange,
    )


def blind_context_from_grading_context(
    context: GradingContext,
    *,
    verifier_observations: list[dict[str, Any]] | None = None,
    clarification_exchange: dict[str, str] | None = None,
) -> BlindGradingContext:
    """Copy every item-side field; ``diagnostic_history`` has nowhere to go."""

    return BlindGradingContext(
        attempt_id=context.attempt_id,
        practice_item_id=context.practice_item_id,
        prompt=context.prompt,
        expected_answer=context.expected_answer,
        learner_answer_md=context.learner_answer_md,
        rubric=dict(context.rubric),
        evidence_facets=list(context.evidence_facets),
        evidence_weights=dict(context.evidence_weights),
        criterion_facet_weights={
            key: dict(value) for key, value in context.criterion_facet_weights.items()
        },
        trace_contract=context.trace_contract,
        error_taxonomy=dict(context.error_taxonomy),
        facet_registry=list(context.facet_registry),
        discrimination_profiles=list(context.discrimination_profiles),
        clarification_exchange=(
            clarification_exchange
            if clarification_exchange is not None
            else context.clarification_exchange
        ),
        error_hunt_solution=context.error_hunt_solution,
        verifier_observations=list(
            verifier_observations
            if verifier_observations is not None
            else context.verifier_observations
        ),
    )


def blind_grading_context_hash(context: BlindGradingContext) -> str:
    """Content address of exactly what the blind grader was shown."""

    payload = {"grader_mode": GRADER_MODE_BLIND, **asdict(context)}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


_BLIND_TASK = (
    "Grade the learner answer against the prompt, expected answer, and rubric. "
    "Return a LearnLoop BlindGradingProposal as schema-valid JSON only. You are a "
    "LEARNER-BLIND grader: you see this item and this one answer, nothing about "
    "the learner's past work, and you measure only what this answer shows. Do "
    "not speculate about the learner's beliefs, history, or recurring patterns, "
    "and do not propose causes, misconceptions, or teaching plans; a separate "
    "diagnostician explains causes later, using your grade. "
    "Write `local_analysis_md` FIRST, before filling any structured field: what "
    "is right and what is wrong IN THIS ANSWER, located in the learner's own "
    "work. Next construct `repaired_traces`: the smallest edit of this answer "
    "that preserves the learner's valid prefix, each with a short id such as "
    "rt1. Only AFTER that checkable repair, fill the localization fields as "
    "descriptions of where the work diverges. Treat `verifier_observations` as "
    "typed instruments: verified/contradicted may localize a failure, while "
    "parse_failed/unsupported/assumption_missing confer NO support and must not "
    "attract the anchor merely because another part parsed. A first_divergence "
    "span quote must be copied VERBATIM from the learner answer — "
    "character-for-character, including whitespace and notation. Leave "
    "char_start/char_end null: offsets are recomputed server-side from the "
    "quote, so never count characters yourself. Locate the EARLIEST incorrect "
    "or unsupported claim, not merely the learner's later admission of "
    "uncertainty; do not preserve an earlier false count, equation, or premise "
    "in the repair prefix. Every named facet must also appear in "
    "local_analysis_md. A missing_required_step divergence must name a "
    "checkpoint_id from the item's trace contract. "
    "For each error_attribution's `error_type`, pick the id from "
    "`error_taxonomy.canonical_error_types` whose `use_when` fits the observed "
    "failure and whose `avoid_when` does not — use ONLY those ids for ordinary "
    "errors. Use existing rubric fatal error ids or vault-specific taxonomy ids "
    "only when they apply more precisely. Use the retrieval-failure taxonomy id "
    "only when the trace locally supports a failure to access previously "
    "learned, task-relevant knowledge; 'I don't know how' or an inability to "
    "continue does not by itself establish failed retrieval. For each failed "
    "rubric line or facet, add an error_attribution unless another attribution "
    "already covers the same failure, and set `repaired_trace_id` to the "
    "repaired trace that fixes it when there is one. "
    "Set the orthogonal axes independently. `resolution_status` says whether "
    "you LOCALIZED the failure: resolved (located on a target), unresolved "
    "(failure seen but not located), or abstained (give a concrete "
    "abstention_reason). `validity_scope` says whether this answer is a fair "
    "measurement: valid_measurement when it is; item_contract when the item, "
    "rubric or expected answer is defective; grader_interpretation when the "
    "grade turns on an interpretation you cannot settle from the item; "
    "interaction_context when the presentation or interaction rather than the "
    "learner's knowledge plausibly produced the failure; unknown otherwise. "
    "`target_ref` is the typed location. A facet may be named only when the "
    "failed step exercises that facet's claim; prefer a failed criterion, item "
    "step, answer span, or a reasoned abstention over the nearest listed facet. "
    "`target_evidence_families` may be empty. Passing evidence for a facet is "
    "evidence FOR it, never a repair target. Set facet_contrast only when the "
    "trace explicitly demonstrates a contract swap, with a trace-citing "
    "justification. `localization_confidence` is a model-reported proposal, "
    "not outcome confidence. "
    "Emit a repaired trace only when you can keep the learner's displayed work "
    "verbatim through a supported insertion point: copy `learner_work_prefix`, "
    "state one `minimal_edit`, regenerate only downstream work in the "
    "learner's notation, and enumerate changed latent claims and authored "
    "checkpoint ids. Do not fabricate trace structure when the item has no "
    "reliable decomposition. Request `symbolic_equality` verification only "
    "when the full repaired answer and authored expected answer are parseable "
    "mathematical expressions; request `exact_match` only when exact text "
    "equality is the authored contract. Never propose a verification verdict. "
    "Set `rubric_score` to the rounded sum of awarded criterion points after "
    "any fatal-error cap. The rubric criterion total is the maximum; never "
    "normalize or clamp the score to four. `feedback_md` is answer-local "
    "feedback only and never refers to anything outside this answer. "
    "`clarification_request`: leave it null unless you are genuinely unsure "
    "what the LEARNER did and one question would settle it - ambiguous "
    "notation, a skipped step that is either fluency or a gap, a correct answer "
    "possibly reached by invalid reasoning, or which of two methods they "
    "believed they were using. Ask at most one, only against a criterion you "
    "marked `learner_confidence='hedged'` or an attribution you marked "
    "`abstained`. NEVER ask about something you could settle yourself from the "
    "item, the expected answer, or the trace. If "
    "`context.clarification_exchange` is present, grade with the learner's "
    "answer in hand, do not ask again, and abstain rather than guess if it "
    "still does not settle the matter. "
    "`discrimination_profile_match`: when `context.discrimination_profiles` is "
    "non-empty, the item's author has written down what a holder of each "
    "candidate visibly produces. Set outcome='matched' with the profile_id and "
    "a quote from the learner's work ONLY when the work really shows that "
    "signature; otherwise set outcome='no_profile_applies', which is a full "
    "answer. Leave the field null when the item lists no profiles. "
    "`error_hunt_report`: when `context.error_hunt_solution` is present the "
    "learner was shown that worked solution and asked to find and REPAIR "
    "whatever is wrong with it. Report each error they claimed, with where "
    "they say it is, what they say is wrong, and the corrected work they "
    "produced - `repair_md` empty when they only pointed at it. Do not guess at "
    "`matches_planted_error_id` unless the item names the plant to you. "
    "LAST, fill `exercised_facets`: facets from `context.facet_registry` that "
    "the learner's written work actually EXERCISES, with a quote from the "
    "trace in `evidence`. This channel is positive only; leave it empty when "
    "the work shows nothing beyond the criteria you already graded."
)


def blind_grading_prompt(context: BlindGradingContext) -> str:
    """Render the blind grading request (§4.3)."""

    return render_structured_prompt(
        "learnloop blind grading proposal",
        BLIND_GRADING_PROMPT_VERSION,
        {"task": _BLIND_TASK, "context": asdict(context)},
    )


def request_blind_grading_proposal(
    client: OperationClient,
    context: BlindGradingContext,
) -> BlindGradingProposal:
    """Run the blind grading operation on a structured provider.

    Always an isolated turn: structural blindness is meaningless if the
    grader can read prior grades and diagnoses from the vault, so a
    transport that cannot isolate the turn refuses it.
    """

    return execute_structured_operation(
        client,
        purpose="blind_grading",
        prompt=blind_grading_prompt(context),
        result_model=BlindGradingProposal,
        isolated=True,
    )


def _cause_scope_for(validity_scope: str) -> str:
    return _SCOPE_FOR_VALIDITY.get(validity_scope, "unknown")


def taxonomy_misconception_prior(vault: LoadedVault, error_type: str) -> bool:
    """O2: at grade time ``is_misconception`` is the taxonomy prior only."""

    taxonomy = vault.error_types.get(error_type)
    return bool(taxonomy.is_misconception) if taxonomy is not None else False


def to_grading_proposal(
    proposal: BlindGradingProposal,
    *,
    vault: LoadedVault | None = None,
) -> GradingProposal:
    """The §4.2 mapping onto the joint shape, with every causal field empty.

    ``local_analysis_md`` becomes ``diagnosis_md`` (so the facet-grounding
    check reads it), each repaired trace becomes a structural-only repair
    suggestion (so the splice, prefix and checkpoint rules validate it), and
    ``validity_scope`` becomes the joint ``cause_scope`` gate value.
    """

    suggestions = [
        RepairSuggestion(
            repaired_trace=RepairedTrace(
                learner_work_prefix=trace.learner_work_prefix,
                repair_insertion_point=trace.repair_insertion_point,
                minimal_edit=trace.minimal_edit,
                regenerated_work=trace.regenerated_work,
                repaired_answer_md=trace.repaired_answer_md,
                changed_latent_claims=list(trace.changed_latent_claims),
                changed_checkpoint_ids=list(trace.changed_checkpoint_ids),
            ),
            **(
                {"verification_request": trace.verification_request}
                if trace.verification_request is not None
                else {}
            ),
            practice_mode=_BLIND_REPAIR_PRACTICE_MODE,
            rationale=f"Minimal repair {trace.id} of this answer (blind grader).",
        )
        for trace in proposal.repaired_traces
    ]
    attributions = [
        ErrorAttribution(
            error_type=attribution.error_type,
            severity=attribution.severity,
            evidence=attribution.evidence,
            is_misconception=(
                taxonomy_misconception_prior(vault, attribution.error_type)
                if vault is not None
                else False
            ),
            target_evidence_families=list(attribution.target_evidence_families),
            target_criterion_ids=list(attribution.target_criterion_ids),
            resolution_status=attribution.resolution_status,
            abstention_reason=attribution.abstention_reason,
            cause_scope=_cause_scope_for(attribution.validity_scope),
            target_ref=attribution.target_ref,
            first_divergence=attribution.first_divergence,
            localization_confidence=attribution.localization_confidence,
            facet_contrast=attribution.facet_contrast,
        )
        for attribution in proposal.error_attributions
    ]
    return GradingProposal(
        diagnosis_md=proposal.local_analysis_md,
        repair_suggestions=suggestions,
        attempt_id=proposal.attempt_id,
        practice_item_id=proposal.practice_item_id,
        rubric_score=proposal.rubric_score,
        criterion_evidence=list(proposal.criterion_evidence),
        fatal_errors=list(proposal.fatal_errors),
        error_attributions=attributions,
        grader_confidence=proposal.grader_confidence,
        manual_review_recommended=proposal.manual_review_recommended,
        feedback_md=proposal.feedback_md,
        exercised_facets=list(proposal.exercised_facets),
        clarification_request=proposal.clarification_request,
        discrimination_profile_match=proposal.discrimination_profile_match,
        error_hunt_report=proposal.error_hunt_report,
    )


@dataclass(frozen=True)
class ValidatedBlindGrade:
    """A validated blind grade plus the blind-only fields the joint shape lacks.

    ``grade`` is the validated joint-shape grade (the measurement M2 applies);
    ``validity_scopes`` and ``repaired_trace_ids`` align with
    ``grade.error_attributions`` and ``repaired_traces`` by index.
    """

    grade: ValidatedCodexGrade
    local_analysis_md: str
    repaired_traces: tuple[dict[str, Any], ...]
    validity_scopes: tuple[str, ...]
    attribution_trace_ids: tuple[str | None, ...]
    max_points: float

    def attributions(self) -> list[dict[str, Any]]:
        """Grader-owned attribution fields only; no causal field exists here."""

        rows: list[dict[str, Any]] = []
        for index, attribution in enumerate(self.grade.error_attributions):
            rows.append(
                {
                    "index": index,
                    "error_type": attribution.error_type,
                    "severity": attribution.severity,
                    "evidence": attribution.evidence,
                    "is_misconception_prior": attribution.is_misconception,
                    "target_evidence_families": list(attribution.target_evidence_families or []),
                    "target_criterion_ids": list(attribution.target_criterion_ids or []),
                    "target_ref": attribution.target_ref,
                    "resolution_status": attribution.resolution_status,
                    "abstention_reason": attribution.abstention_reason,
                    "validity_scope": (
                        self.validity_scopes[index]
                        if index < len(self.validity_scopes)
                        else "unknown"
                    ),
                    "first_divergence": attribution.first_divergence,
                    "localization_confidence": attribution.model_reported_localization_confidence,
                    "facet_contrast": attribution.facet_contrast,
                    "facet_write_blocked": attribution.facet_write_blocked,
                    "repaired_trace_id": (
                        self.attribution_trace_ids[index]
                        if index < len(self.attribution_trace_ids)
                        else None
                    ),
                }
            )
        return rows

    def as_record(self) -> dict[str, Any]:
        """The persisted blind-grade record the diagnosis context reads."""

        grade = self.grade
        return {
            "grader_mode": GRADER_MODE_BLIND,
            "prompt_version": BLIND_GRADING_PROMPT_VERSION,
            "output_schema_version": BLIND_GRADER_OUTPUT_SCHEMA_VERSION,
            "rubric_score": grade.rubric_score,
            "max_points": self.max_points,
            "criteria": [
                {
                    "criterion_id": row.criterion_id,
                    "points_awarded": row.points_awarded,
                    "evidence": row.evidence,
                    "learner_confidence": row.learner_confidence,
                }
                for row in grade.criterion_evidence
            ],
            "fatal_errors": list(grade.fatal_errors),
            "local_analysis_md": self.local_analysis_md,
            "repaired_traces": [dict(trace) for trace in self.repaired_traces],
            "error_attributions": self.attributions(),
            "grader_confidence": grade.grader_confidence,
            "manual_review_reason": grade.manual_review_reason,
            "feedback_md": grade.feedback_md,
            "exercised_facets": [
                {"facet": row.facet, "evidence": row.evidence, "scope": row.observation_scope}
                for row in grade.exercised_facets or []
            ],
            "discrimination_profile_match": grade.discrimination_profile_match,
            "attribution_audit_events": list(grade.attribution_audit_events or []),
        }


def validate_blind_grading_proposal(
    proposal: BlindGradingProposal,
    *,
    attempt_id: str,
    item: PracticeItem,
    vault: LoadedVault,
    learner_answer_md: str | None = None,
    rubric: Rubric | None = None,
) -> ValidatedBlindGrade:
    """Validate through the joint validator, minus causal fields (§3).

    Raises :class:`~learnloop.attempts.grading.GradingValidationError` on the
    same conditions as a joint grade, plus a duplicate or dangling repaired
    trace id.
    """

    rubric = rubric or resolved_rubric(vault, item)
    trace_ids = [trace.id for trace in proposal.repaired_traces]
    if len(set(trace_ids)) != len(trace_ids):
        raise GradingValidationError("Duplicate repaired_trace id")
    known_ids = set(trace_ids)
    dangling = sorted(
        {
            str(attribution.repaired_trace_id)
            for attribution in proposal.error_attributions
            if attribution.repaired_trace_id is not None
            and attribution.repaired_trace_id not in known_ids
        }
    )
    grade = validate_codex_grading_proposal(
        to_grading_proposal(proposal, vault=vault),
        attempt_id=attempt_id,
        item=item,
        vault=vault,
        learner_answer_md=learner_answer_md,
        rubric=rubric,
    )
    validated_traces: list[dict[str, Any]] = []
    for index, suggestion in enumerate(grade.repair_suggestions or []):
        trace = suggestion.get("repaired_trace")
        if not isinstance(trace, dict):
            continue
        trace_id = trace_ids[index] if index < len(trace_ids) else f"rt{index + 1}"
        validated_traces.append(
            {
                "id": trace_id,
                **trace,
                **(
                    {"verification_request": suggestion["verification_request"]}
                    if suggestion.get("verification_request") is not None
                    else {}
                ),
                "repair_validation": suggestion.get("repair_validation"),
            }
        )
    surviving = {trace["id"] for trace in validated_traces}
    return ValidatedBlindGrade(
        grade=grade,
        local_analysis_md=proposal.local_analysis_md,
        repaired_traces=tuple(validated_traces),
        validity_scopes=tuple(
            attribution.validity_scope for attribution in proposal.error_attributions
        ),
        attribution_trace_ids=tuple(
            attribution.repaired_trace_id
            if attribution.repaired_trace_id in surviving and attribution.repaired_trace_id not in dangling
            else None
            for attribution in proposal.error_attributions
        ),
        max_points=float(rubric.max_points),
    )


__all__ = [
    "BLIND_CALIBRATION_PROMPT_VERSION",
    "BLIND_GRADER_OUTPUT_SCHEMA_VERSION",
    "BLIND_GRADING_PROMPT_VERSION",
    "GRADER_MODE_BLIND",
    "VALIDITY_SCOPES",
    "BlindErrorAttribution",
    "BlindGradingContext",
    "BlindGradingProposal",
    "BlindRepairedTrace",
    "ValidatedBlindGrade",
    "blind_context_from_grading_context",
    "blind_grading_context",
    "blind_grading_context_hash",
    "blind_grading_prompt",
    "request_blind_grading_proposal",
    "taxonomy_misconception_prior",
    "to_grading_proposal",
    "validate_blind_grading_proposal",
]
