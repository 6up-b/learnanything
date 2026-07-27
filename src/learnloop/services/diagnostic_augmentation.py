"""Stage 7 diagnostic evaluation and Phase-C diagnosis augmentation.

Two invariants organize this module:

* planted traces are scored in memory and may only enter migration 144's eval
  ledger; they never become attempts or learner evidence;
* model agreement is diagnostic support, not durable causal authority.  It may
  populate a provisional support score and an unresolved cause set, but it does
  not license promotion by itself.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from typing import Any, Mapping, Sequence

from learnloop.clock import Clock
from learnloop.codex.client import GradingContext
from learnloop.codex.prompts import GRADING_PROMPT_VERSION
from learnloop.codex.schemas import CandidateCause, GradingProposal
from learnloop.db.repositories import Repository
from learnloop.services.causal_attribution import (
    SympyVerifierAdapter,
    repair_equivalence_id,
)
from learnloop.services.diagnosis_adjudication import anchor_key
from learnloop.services.grading import build_grading_context, resolved_rubric
from learnloop.services.persona_realism import (
    latest_realism_license,
    match_persona_realism,
    trace_corpus_hash,
)
from learnloop.ids import new_ulid
from learnloop.vault.models import LoadedVault, PracticeItem


DIAGNOSTIC_EVAL_HARNESS_VERSION = "blind_planted_diagnostician_v1"
PHASE_C_VERSION = "diagnostic_augmentation_c1_c4_v1"
DEFAULT_DIAGNOSIS_SAMPLES = 3
DEFAULT_HISTORY_LIMIT = 4

REGRESSION_SHAPES: tuple[str, ...] = (
    "exhibit",
    "genuine_facet_failure",
    "multiplication_failure",
    "addition_multiplication_confusion",
    "notation_typo_valid_reasoning",
    "missing_required_step",
    "alternate_valid_path",
    "item_contract_fault",
    "grader_interpretation_fault",
    "composite_supporting_pass",
    "correct_answer_invalid_reasoning",
    "unparseable_notation",
    "open_vocabulary_abstention",
    "cause_change_mid_history",
)
PLANTED_CASE_SOURCES: frozenset[str] = frozenset(
    {"discrimination_profile", "authored_fixture", "adjudicated_overlap"}
)

PHASE_C_HYPOTHESES: dict[str, str] = {
    "c1": "repair-class match rises while anchor accuracy holds or rises",
    "c2": "anchor accuracy rises on deterministically verifiable domains",
    "c3": "sample agreement correlates with adjudicated correctness and improves probe action change",
    "c4": "same-facet recurrence is detected sooner without anchoring after a cause change",
}

PHASE_C_REVERT_CRITERIA: dict[str, str] = {
    "c1": "revert if planted abstention recall collapses",
    "c2": "revert if parseability anchors the diagnosis and abstention precision falls",
    "c3": "revert if tokens per resolved episode rise without probe action-change gain",
    "c4": "revert if the cause-change-mid-history control repeats the prior diagnosis",
}

_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def normalize_semantic_key(value: Any) -> str:
    return _NORMALIZE_RE.sub(" ", str(value or "").casefold()).strip()


def model_family(provider: str | None, model: str | None) -> str:
    """Conservative B3 family identity.

    Different revisions of GPT, Claude, Gemini, DeepSeek, or Llama remain one
    family.  Unknown models key on their first stable name component rather than
    pretending two spelling variants are independent.
    """

    provider_key = normalize_semantic_key(provider) or "unknown_provider"
    model_key = normalize_semantic_key(model) or "unknown_model"
    aliases = (
        ("gpt", "gpt"),
        ("o1", "openai_reasoning"),
        ("o3", "openai_reasoning"),
        ("o4", "openai_reasoning"),
        ("claude", "claude"),
        ("gemini", "gemini"),
        ("deepseek", "deepseek"),
        ("qwen", "qwen"),
        ("llama", "llama"),
        ("mistral", "mistral"),
        ("grok", "grok"),
    )
    family = next((family for marker, family in aliases if marker in model_key), None)
    if family is not None:
        # Provider aliases do not create independence. The same GPT family
        # routed through two gateways is still the same family for B3.
        return family
    family = model_key.split(" ", 1)[0]
    return f"{provider_key}:{family}"


@dataclass(frozen=True)
class PlantedDiagnosticCase:
    case_key: str
    regression_shape: str
    practice_item_id: str
    learner_trace_md: str
    should_abstain: bool
    planted_anchor: dict[str, Any] | None = None
    planted_cause_key: str | None = None
    planted_repair_class_id: str | None = None
    planted_repair_equivalence_id: str | None = None
    source: str = "authored_fixture"
    profile_id: str | None = None
    attempt_id: str | None = None
    history: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not self.case_key.strip():
            raise ValueError("a planted diagnostic case needs a case_key")
        if self.regression_shape not in REGRESSION_SHAPES:
            raise ValueError(
                f"unknown diagnostic regression shape {self.regression_shape!r}"
            )
        if not self.practice_item_id.strip():
            raise ValueError("a planted diagnostic case needs a practice_item_id")
        if self.source not in PLANTED_CASE_SOURCES:
            raise ValueError(f"unknown planted case source {self.source!r}")
        if not self.learner_trace_md.strip():
            raise ValueError("a planted diagnostic trace cannot be empty")


@dataclass(frozen=True)
class DiagnosisSample:
    index: int
    fingerprint: str
    anchor_key: str
    repair_equivalence_id: str | None
    cause_key: str | None
    proposal: GradingProposal


@dataclass(frozen=True)
class DiagnosisConsensus:
    proposal: GradingProposal
    sample_count: int
    agreement_support: float
    winner_fingerprint: str
    samples: tuple[DiagnosisSample, ...]
    disagreement_causes: tuple[dict[str, Any], ...] = ()

    @property
    def disagreed(self) -> bool:
        return len({sample.fingerprint for sample in self.samples}) > 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": PHASE_C_VERSION,
            "sample_count": self.sample_count,
            "agreement_support": self.agreement_support,
            "winner_fingerprint": self.winner_fingerprint,
            "disagreed": self.disagreed,
            "disagreement_causes": list(self.disagreement_causes),
            "samples": [
                {
                    "index": sample.index,
                    "fingerprint": sample.fingerprint,
                    "anchor_key": sample.anchor_key,
                    "repair_equivalence_id": sample.repair_equivalence_id,
                    "cause_key": sample.cause_key,
                }
                for sample in self.samples
            ],
        }


@dataclass(frozen=True)
class DiagnosticEvalReport:
    run_id: str
    status: str
    licensed: bool
    generator_family: str
    diagnostician_family: str
    persona_realism_run_id: str | None
    metrics: dict[str, Any]
    cases: tuple[dict[str, Any], ...] = ()
    missing_regression_shapes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "harness_version": DIAGNOSTIC_EVAL_HARNESS_VERSION,
            "run_id": self.run_id,
            "status": self.status,
            "licensed": self.licensed,
            "generator_family": self.generator_family,
            "diagnostician_family": self.diagnostician_family,
            "persona_realism_run_id": self.persona_realism_run_id,
            "metrics": self.metrics,
            "cases": list(self.cases),
            "missing_regression_shapes": list(self.missing_regression_shapes),
        }


def diagnostic_verifier_observations(
    learner_answer_md: str,
    expected_answer: str,
) -> list[dict[str, Any]]:
    """C2 verifier instrument over the submitted answer.

    The whole answer is the only expression whose contract is authored here.
    ``parse_failed`` and ``unsupported`` are returned but explicitly carry
    ``confers_support=False``; callers must never turn parseability into causal
    evidence.
    """

    result = SympyVerifierAdapter().verify(learner_answer_md, expected_answer)
    body = result.as_dict()
    body.update(
        {
            "instrument": "symbolic_equality",
            "scope": "whole_answer",
            "confers_support": result.status in {"verified", "contradicted"},
        }
    )
    return [body]


def diagnostic_history_context(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    *,
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> list[dict[str, Any]]:
    """C4 raw prior traces on the same facet and surface family.

    Prior diagnoses are deliberately omitted.  The grader gets evidence of
    recurrence, not the system's old answer to copy.
    """

    wanted_facets = {
        vault.canonical_facet_id(str(facet)) for facet in item.evidence_facets
    }
    wanted_surface = item.surface_family or item.id
    history: list[dict[str, Any]] = []
    for attempt in repository.list_recent_attempts_by_learning_object(
        item.learning_object_id, limit=max(limit * 5, limit)
    ):
        previous = vault.practice_items.get(str(attempt.get("practice_item_id") or ""))
        if previous is None:
            continue
        previous_facets = {
            vault.canonical_facet_id(str(facet))
            for facet in previous.evidence_facets
        }
        previous_surface = previous.surface_family or previous.id
        if not (wanted_facets & previous_facets):
            continue
        if previous_surface != wanted_surface:
            continue
        trace = str(attempt.get("learner_answer_md") or "").strip()
        if not trace:
            continue
        history.append(
            {
                "attempt_id": str(attempt["id"]),
                "learner_trace_md": trace,
                "created_at": attempt.get("created_at"),
                "surface_family": previous_surface,
                "shared_facets": sorted(wanted_facets & previous_facets),
            }
        )
        if len(history) >= limit:
            break
    history.reverse()
    return history


def augment_grading_context(
    vault: LoadedVault,
    repository: Repository,
    item: PracticeItem,
    context: GradingContext,
    *,
    history_limit: int = DEFAULT_HISTORY_LIMIT,
) -> GradingContext:
    """Attach C2/C4 evidence before the model call."""

    return replace(
        context,
        verifier_observations=diagnostic_verifier_observations(
            context.learner_answer_md, context.expected_answer
        ),
        diagnostic_history=diagnostic_history_context(
            vault, repository, item, limit=history_limit
        ),
    )


def _primary_attribution(proposal: GradingProposal) -> Any | None:
    if not proposal.error_attributions:
        return None
    return max(
        proposal.error_attributions,
        key=lambda attribution: (
            float(attribution.severity or 0.0),
            bool(attribution.first_divergence),
        ),
    )


def _repair_equivalence(proposal: GradingProposal) -> str | None:
    if not proposal.repair_suggestions:
        return None
    suggestion = proposal.repair_suggestions[0]
    payload = suggestion.model_dump(mode="json", exclude_none=True)
    if not payload.get("operator") and not payload.get("practice_mode"):
        return None
    return repair_equivalence_id(payload)


def _proposal_keys(
    proposal: GradingProposal,
) -> tuple[str, str | None, str | None]:
    attribution = _primary_attribution(proposal)
    anchor = (
        attribution.first_divergence.model_dump(mode="json", exclude_none=True)
        if attribution is not None and attribution.first_divergence is not None
        else None
    )
    cause = None
    if attribution is not None:
        cause = normalize_semantic_key(
            attribution.misconception_statement
            or attribution.operation
            or attribution.evidence
        )
    return anchor_key(anchor), _repair_equivalence(proposal), cause or None


def _sample(proposal: GradingProposal, index: int) -> DiagnosisSample:
    anchor, repair, cause = _proposal_keys(proposal)
    identity = {
        "abstained": _system_abstained(proposal),
        "anchor": anchor,
        "repair": repair,
    }
    fingerprint = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]
    return DiagnosisSample(
        index=index,
        fingerprint=fingerprint,
        anchor_key=anchor,
        repair_equivalence_id=repair,
        cause_key=cause,
        proposal=proposal,
    )


def run_diagnosis_samples(
    client: Any,
    context: GradingContext,
    *,
    sample_count: int = DEFAULT_DIAGNOSIS_SAMPLES,
) -> DiagnosisConsensus:
    """C3 k independent calls, modal answer, and a disagreement cause set."""

    if sample_count < 1:
        raise ValueError("diagnostic sample_count must be >= 1")
    samples = tuple(
        _sample(client.run_grading_proposal(context), index)
        for index in range(sample_count)
    )
    counts = Counter(sample.fingerprint for sample in samples)
    winner_fingerprint, winner_count = max(
        counts.items(),
        key=lambda pair: (pair[1], -next(
            sample.index for sample in samples if sample.fingerprint == pair[0]
        )),
    )
    winner = next(
        sample for sample in samples if sample.fingerprint == winner_fingerprint
    )
    distinct: dict[str, DiagnosisSample] = {}
    for sample in samples:
        distinct.setdefault(sample.fingerprint, sample)
    disagreement_causes = tuple(
        {
            "statement": (
                sample.cause_key
                or f"diagnostic sample anchored at {sample.anchor_key}"
            ),
            "cause_scope": (
                str(getattr(_primary_attribution(sample.proposal), "cause_scope", None))
                if _primary_attribution(sample.proposal) is not None
                else "unknown"
            )
            or "unknown",
            "target_ref": (
                _primary_attribution(sample.proposal).target_ref.model_dump(
                    mode="json", exclude_none=True
                )
                if _primary_attribution(sample.proposal) is not None
                and _primary_attribution(sample.proposal).target_ref is not None
                else {"kind": "none"}
            ),
            "anchor_key": sample.anchor_key,
            "repair_equivalence_id": sample.repair_equivalence_id,
            "sample_votes": counts[sample.fingerprint],
        }
        for sample in distinct.values()
    )
    proposal = winner.proposal
    if len(distinct) > 1 and proposal.error_attributions:
        primary = _primary_attribution(proposal)
        assert primary is not None
        candidates = [
            CandidateCause(
                statement=str(cause["statement"]),
                cause_scope=(
                    cause["cause_scope"]
                    if cause["cause_scope"]
                    in {
                        "learner_state",
                        "transient_execution",
                        "interaction_context",
                        "item_contract",
                        "grader_interpretation",
                        "unknown",
                    }
                    else "unknown"
                ),
                target_ref=cause["target_ref"],
            )
            for cause in disagreement_causes
        ]
        updated = primary.model_copy(
            update={
                "resolution_status": "unresolved",
                "candidate_causes": candidates,
                "causal_confidence": winner_count / sample_count,
            }
        )
        proposal = proposal.model_copy(
            update={
                "error_attributions": [
                    updated if attribution is primary else attribution
                    for attribution in proposal.error_attributions
                ]
            }
        )
    return DiagnosisConsensus(
        proposal=proposal,
        sample_count=sample_count,
        agreement_support=winner_count / sample_count,
        winner_fingerprint=winner_fingerprint,
        samples=samples,
        disagreement_causes=(
            disagreement_causes if len(distinct) > 1 else ()
        ),
    )


def _system_abstained(proposal: GradingProposal) -> bool:
    if not proposal.error_attributions:
        return True
    statuses = [
        attribution.resolution_status for attribution in proposal.error_attributions
    ]
    return bool(statuses) and all(status == "abstained" for status in statuses)


def cases_from_discrimination_profiles(
    vault: LoadedVault,
) -> list[PlantedDiagnosticCase]:
    """Turn A5 profiles into authored ground truth, without a model labeler."""

    cases: list[PlantedDiagnosticCase] = []
    for item in vault.practice_items.values():
        rubric = resolved_rubric(vault, item)
        default_criterion = rubric.criteria[0].id if rubric.criteria else "whole_answer"
        for profile in item.discrimination_profiles or ():
            source_shape = str(profile.source or "")
            shape = (
                source_shape
                if source_shape in REGRESSION_SHAPES
                else "genuine_facet_failure"
            )
            criterion = (
                profile.fails_criteria[0]
                if profile.fails_criteria
                else default_criterion
            )
            anchor = {
                "anchor_kind": "whole_answer",
                "criterion_id": criterion,
            }
            case_key = f"{item.id}:{profile.id}"
            cases.append(
                PlantedDiagnosticCase(
                    case_key=case_key,
                    regression_shape=shape,
                    practice_item_id=item.id,
                    learner_trace_md=profile.observable_signature,
                    should_abstain=False,
                    planted_anchor=anchor,
                    planted_cause_key=normalize_semantic_key(profile.hypothesis),
                    source="discrimination_profile",
                    profile_id=profile.id,
                )
            )
    return cases


def planted_cases_from_manifest(payload: Any) -> list[PlantedDiagnosticCase]:
    """Parse the explicit JSON boundary used by the commissioning CLI.

    A fixed manifest is the reproducible way to carry authored abstention and
    cause-change controls that cannot be inferred from a discrimination profile.
    Unknown fields fail closed so a misspelled oracle label cannot silently
    disappear from an evaluation.
    """

    rows = payload.get("cases") if isinstance(payload, Mapping) else payload
    if not isinstance(rows, list):
        raise ValueError("diagnostic case manifest must be a list or {'cases': [...]}")
    allowed = {
        "case_key",
        "regression_shape",
        "practice_item_id",
        "learner_trace_md",
        "should_abstain",
        "planted_anchor",
        "planted_cause_key",
        "planted_repair_class_id",
        "planted_repair_equivalence_id",
        "source",
        "profile_id",
        "attempt_id",
        "history",
    }
    cases: list[PlantedDiagnosticCase] = []
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise ValueError(f"diagnostic case {index} must be an object")
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(
                f"diagnostic case {index} has unknown field(s): {', '.join(unknown)}"
            )
        if not isinstance(raw.get("should_abstain"), bool):
            raise ValueError(
                f"diagnostic case {index} should_abstain must be boolean"
            )
        anchor = raw.get("planted_anchor")
        if anchor is not None and not isinstance(anchor, Mapping):
            raise ValueError(
                f"diagnostic case {index} planted_anchor must be an object or null"
            )
        raw_history = raw.get("history") or []
        if not isinstance(raw_history, list) or not all(
            isinstance(row, Mapping) for row in raw_history
        ):
            raise ValueError(
                f"diagnostic case {index} history must be a list of objects"
            )
        cases.append(
            PlantedDiagnosticCase(
                case_key=str(raw.get("case_key") or ""),
                regression_shape=str(raw.get("regression_shape") or ""),
                practice_item_id=str(raw.get("practice_item_id") or ""),
                learner_trace_md=str(raw.get("learner_trace_md") or ""),
                should_abstain=raw["should_abstain"],
                planted_anchor=dict(anchor) if anchor is not None else None,
                planted_cause_key=(
                    str(raw["planted_cause_key"])
                    if raw.get("planted_cause_key") is not None
                    else None
                ),
                planted_repair_class_id=(
                    str(raw["planted_repair_class_id"])
                    if raw.get("planted_repair_class_id") is not None
                    else None
                ),
                planted_repair_equivalence_id=(
                    str(raw["planted_repair_equivalence_id"])
                    if raw.get("planted_repair_equivalence_id") is not None
                    else None
                ),
                source=str(raw.get("source") or "authored_fixture"),
                profile_id=(
                    str(raw["profile_id"])
                    if raw.get("profile_id") is not None
                    else None
                ),
                attempt_id=(
                    str(raw["attempt_id"])
                    if raw.get("attempt_id") is not None
                    else None
                ),
                history=tuple(dict(row) for row in raw_history),
            )
        )
    return cases


def _generated_trace(
    generator_client: Any,
    case: PlantedDiagnosticCase,
    item: PracticeItem,
) -> str:
    """Use the generator model when available; never ask it to label the cause."""

    generate = getattr(generator_client, "run_diagnostic_trials", None)
    if not callable(generate) or case.should_abstain:
        return case.learner_trace_md
    trials = generate(
        {
            "n_trials": 1,
            "max_answer_words": 120,
            "item_prompt": item.prompt,
            "expected_answer": (
                item.expected_answer
                if isinstance(item.expected_answer, str)
                else json.dumps(item.expected_answer, sort_keys=True)
            ),
            "misconception_statement": case.planted_cause_key or "",
            "misconception_consistent_answer": case.learner_trace_md,
            "keyed_fatal_errors": [],
        }
    )
    planted = list(getattr(trials, "planted", None) or [])
    answer = str(getattr(planted[0], "answer", "") or "").strip() if planted else ""
    return answer or case.learner_trace_md


def _case_result(
    case: PlantedDiagnosticCase,
    proposal: GradingProposal,
    consensus: DiagnosisConsensus,
) -> dict[str, Any]:
    system_anchor, system_repair, system_cause = _proposal_keys(proposal)
    planted_anchor = anchor_key(case.planted_anchor)
    system_abstained = _system_abstained(proposal)
    repair_correct: bool | None = None
    if case.planted_repair_equivalence_id is not None:
        repair_correct = (
            system_repair == case.planted_repair_equivalence_id
        )
    cause_correct: bool | None = None
    if case.planted_cause_key is not None:
        planted_cause = normalize_semantic_key(case.planted_cause_key)
        diagnosed_cause = normalize_semantic_key(system_cause)
        cause_correct = bool(
            planted_cause
            and diagnosed_cause
            and (
                planted_cause == diagnosed_cause
                or planted_cause in diagnosed_cause
                or diagnosed_cause in planted_cause
            )
        )
        if repair_correct is True:
            cause_correct = True
    return {
        "case_key": case.case_key,
        "attempt_id": case.attempt_id,
        "regression_shape": case.regression_shape,
        "source": case.source,
        "practice_item_id": case.practice_item_id,
        "profile_id": case.profile_id,
        "learner_trace_md": case.learner_trace_md,
        "planted_should_abstain": case.should_abstain,
        "planted_anchor": case.planted_anchor,
        "planted_anchor_key": planted_anchor,
        "planted_cause_key": case.planted_cause_key,
        "planted_repair_class_id": case.planted_repair_class_id,
        "planted_repair_equivalence_id": case.planted_repair_equivalence_id,
        "system_snapshot": {
            "diagnosis_md": proposal.diagnosis_md,
            "proposal": proposal.model_dump(mode="json", exclude_none=True),
            "consensus": consensus.as_dict(),
        },
        "system_abstained": system_abstained,
        "system_anchor_key": system_anchor,
        "system_cause_key": system_cause,
        "system_repair_class_id": None,
        "system_repair_equivalence_id": system_repair,
        "anchor_correct": (
            system_anchor == planted_anchor
            if not case.should_abstain and planted_anchor != "none"
            else system_abstained
        ),
        "cause_correct": cause_correct,
        "repair_correct": repair_correct,
        "abstention_correct": system_abstained == case.should_abstain,
    }


def _rate(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Any]:
    scored = [row for row in rows if row.get(key) is not None]
    numerator = sum(bool(row[key]) for row in scored)
    return {
        "value": round(numerator / len(scored), 6) if scored else None,
        "numerator": numerator,
        "denominator": len(scored),
    }


def _eval_metrics(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    def score(group: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        predicted_abstain = [row for row in group if row["system_abstained"]]
        should_abstain = [row for row in group if row["planted_should_abstain"]]
        true_abstain = sum(
            row["system_abstained"] and row["planted_should_abstain"]
            for row in group
        )
        return {
            "first_divergence_anchor_accuracy": _rate(group, "anchor_correct"),
            "cause_equivalence_rate": _rate(group, "cause_correct"),
            "repair_class_match_rate": _rate(group, "repair_correct"),
            "abstention_precision": {
                "value": (
                    round(true_abstain / len(predicted_abstain), 6)
                    if predicted_abstain
                    else None
                ),
                "numerator": true_abstain,
                "denominator": len(predicted_abstain),
            },
            "abstention_recall": {
                "value": (
                    round(true_abstain / len(should_abstain), 6)
                    if should_abstain
                    else None
                ),
                "numerator": true_abstain,
                "denominator": len(should_abstain),
            },
        }

    metrics = score(rows)
    metrics["cases_by_shape"] = dict(
        sorted(Counter(str(row["regression_shape"]) for row in rows).items())
    )
    metrics["by_regression_shape"] = {
        shape: score(
            [row for row in rows if row["regression_shape"] == shape]
        )
        for shape in REGRESSION_SHAPES
        if any(row["regression_shape"] == shape for row in rows)
    }
    return metrics


def run_planted_diagnostic_evaluation(
    vault: LoadedVault,
    repository: Repository,
    *,
    generator_client: Any,
    diagnostician_client: Any,
    cases: Sequence[PlantedDiagnosticCase] | None = None,
    sample_count: int = DEFAULT_DIAGNOSIS_SAMPLES,
    personas_pre_generated: bool = False,
    clock: Clock | None = None,
) -> DiagnosticEvalReport:
    """B1/B3 live-path evaluation, blind to the planted cause.

    The grading context removes discrimination profiles and receives no planted
    labels.  Only the outer harness sees them.
    """

    generator_provider = getattr(generator_client, "provider_name", None)
    generator_model = getattr(generator_client, "model", None)
    diagnostician_provider = getattr(diagnostician_client, "provider_name", None)
    diagnostician_model = getattr(diagnostician_client, "model", None)
    generator_family = model_family(generator_provider, generator_model)
    diagnostician_family = model_family(
        diagnostician_provider, diagnostician_model
    )
    separated = generator_family != diagnostician_family
    selected_cases = list(cases) if cases is not None else cases_from_discrimination_profiles(vault)
    evaluated_cases: list[PlantedDiagnosticCase] = []
    if separated:
        for case in selected_cases:
            item = vault.practice_items.get(case.practice_item_id)
            if item is None:
                raise ValueError(
                    f"planted case {case.case_key} names unknown item "
                    f"{case.practice_item_id}"
                )
            trace = (
                case.learner_trace_md
                if personas_pre_generated
                else _generated_trace(generator_client, case, item)
            )
            evaluated_cases.append(replace(case, learner_trace_md=trace))
    realism = (
        latest_realism_license(
            repository,
            generator_family=generator_family,
            persona_source="generated_regression_matrix",
            persona_corpus_hash=trace_corpus_hash(
                case.learner_trace_md for case in evaluated_cases
            ),
        )
        if separated
        else None
    )
    realism_licensed = bool(
        realism and realism.get("verdict") == "indistinguishable"
    )
    results: list[dict[str, Any]] = []
    status = (
        "invalid_same_model_family"
        if not separated
        else ("licensed" if realism_licensed else "unlicensed_realism")
    )

    if separated:
        for case in evaluated_cases:
            item = vault.practice_items[case.practice_item_id]
            trace = case.learner_trace_md
            synthetic_id = f"eval_{new_ulid()}"
            base = build_grading_context(
                vault,
                item,
                attempt_id=synthetic_id,
                learner_answer_md=trace,
                rubric=resolved_rubric(vault, item),
            )
            # Blind means the authored profile supplying the oracle is removed.
            # The ordinary rubric/expected answer remain: that is the live
            # diagnostician's legitimate item contract.
            context = replace(
                base,
                discrimination_profiles=[],
                diagnostic_history=list(case.history),
                verifier_observations=diagnostic_verifier_observations(
                    trace, base.expected_answer
                ),
            )
            consensus = run_diagnosis_samples(
                diagnostician_client, context, sample_count=sample_count
            )
            results.append(
                _case_result(case, consensus.proposal, consensus)
            )

    metrics = _eval_metrics(results)
    metrics["counts_for_decisions"] = status == "licensed"
    metrics["license_reason"] = {
        "licensed": "cross-model separation and B2 realism both passed",
        "unlicensed_realism": "B2 has not licensed this generator family",
        "invalid_same_model_family": (
            "persona generator and diagnostician share a model family"
        ),
    }[status]
    missing = tuple(
        shape
        for shape in REGRESSION_SHAPES
        if not any(row["regression_shape"] == shape for row in results)
    )
    matrix_violations: list[str] = []
    if missing:
        matrix_violations.append("missing_required_shapes")
    if not any(
        case.regression_shape == "open_vocabulary_abstention"
        and case.should_abstain
        for case in selected_cases
    ):
        matrix_violations.append("missing_open_vocabulary_abstention_case")
    if not any(case.should_abstain for case in selected_cases):
        matrix_violations.append("no_abstention_case")
    if not any(
        case.regression_shape == "cause_change_mid_history"
        and len(case.history) >= 2
        for case in selected_cases
    ):
        matrix_violations.append("missing_mid_history_cause_change_control")
    if status == "licensed" and matrix_violations:
        status = "incomplete_regression_matrix"
        metrics["counts_for_decisions"] = False
        metrics["license_reason"] = (
            "B2/B3 passed, but the required regression matrix is incomplete"
        )
    metrics["regression_matrix_complete"] = not matrix_violations
    metrics["missing_regression_shapes"] = list(missing)
    metrics["regression_matrix_violations"] = matrix_violations
    run_id = repository.insert_diagnostic_eval_run(
        {
            "harness_version": DIAGNOSTIC_EVAL_HARNESS_VERSION,
            "grading_prompt_version": GRADING_PROMPT_VERSION,
            "generator_provider": generator_provider,
            "generator_model": generator_model,
            "generator_family": generator_family,
            "diagnostician_provider": diagnostician_provider,
            "diagnostician_model": diagnostician_model,
            "diagnostician_family": diagnostician_family,
            "cross_model_separated": separated,
            "persona_realism_run_id": realism.get("id") if realism else None,
            "realism_licensed": realism_licensed,
            "status": status,
            "case_count": len(results),
            "metrics": metrics,
        },
        clock=clock,
    )
    persisted: list[dict[str, Any]] = []
    for row in results:
        persisted_row = {**row, "run_id": run_id}
        repository.insert_diagnostic_eval_case(persisted_row, clock=clock)
        # Reports never echo full learner traces; the eval ledger owns them.
        persisted.append(
            {
                key: value
                for key, value in persisted_row.items()
                if key not in {"learner_trace_md", "system_snapshot"}
            }
        )
    return DiagnosticEvalReport(
        run_id=run_id,
        status=status,
        licensed=status == "licensed",
        generator_family=generator_family,
        diagnostician_family=diagnostician_family,
        persona_realism_run_id=realism.get("id") if realism else None,
        metrics=metrics,
        cases=tuple(persisted),
        missing_regression_shapes=missing,
    )


def commission_planted_diagnostic_evaluation(
    vault: LoadedVault,
    repository: Repository,
    *,
    generator_client: Any,
    diagnostician_client: Any,
    cases: Sequence[PlantedDiagnosticCase] | None = None,
    real_traces: Sequence[str] | None = None,
    sample_count: int = DEFAULT_DIAGNOSIS_SAMPLES,
    separation_threshold: float = 0.70,
    clock: Clock | None = None,
) -> dict[str, Any]:
    """Generate once, run B2 on those exact traces, then score them in B1.

    This is the commissioning entry point.  Keeping generation outside B1
    would permit the matcher to license corpus A while the diagnostician was
    scored on a fresh corpus B; generating twice is enough distribution drift
    to make B2 ceremonial.
    """

    selected = (
        list(cases)
        if cases is not None
        else cases_from_discrimination_profiles(vault)
    )
    generator_provider = getattr(generator_client, "provider_name", None)
    generator_model = getattr(generator_client, "model", None)
    generator_family = model_family(generator_provider, generator_model)
    diagnostician_family = model_family(
        getattr(diagnostician_client, "provider_name", None),
        getattr(diagnostician_client, "model", None),
    )
    if generator_family == diagnostician_family:
        evaluation = run_planted_diagnostic_evaluation(
            vault,
            repository,
            generator_client=generator_client,
            diagnostician_client=diagnostician_client,
            cases=selected,
            sample_count=sample_count,
            personas_pre_generated=True,
            clock=clock,
        )
        return {
            "persona_realism": None,
            "evaluation": evaluation.as_dict(),
        }

    generated: list[PlantedDiagnosticCase] = []
    for case in selected:
        item = vault.practice_items.get(case.practice_item_id)
        if item is None:
            raise ValueError(
                f"planted case {case.case_key} names unknown item "
                f"{case.practice_item_id}"
            )
        generated.append(
            replace(
                case,
                learner_trace_md=_generated_trace(
                    generator_client, case, item
                ),
            )
        )
    realism = match_persona_realism(
        repository,
        [case.learner_trace_md for case in generated],
        real_traces=real_traces,
        persona_source="generated_regression_matrix",
        generator_provider=generator_provider,
        generator_model=generator_model,
        generator_family=generator_family,
        separation_threshold=separation_threshold,
        clock=clock,
    )
    evaluation = run_planted_diagnostic_evaluation(
        vault,
        repository,
        generator_client=generator_client,
        diagnostician_client=diagnostician_client,
        cases=generated,
        sample_count=sample_count,
        personas_pre_generated=True,
        clock=clock,
    )
    return {
        "persona_realism": realism.as_dict(),
        "evaluation": evaluation.as_dict(),
    }


def record_phase_c_receipt(
    repository: Repository,
    *,
    attempt_id: str,
    context: GradingContext,
    consensus: DiagnosisConsensus,
    grader_provider: str | None,
    grader_model: str | None,
    clock: Clock | None = None,
) -> str | None:
    """Append the hypothesis/revert manifest for one live augmented diagnosis."""

    return repository.insert_diagnostic_augmentation_receipt(
        {
            "attempt_id": attempt_id,
            "grading_prompt_version": GRADING_PROMPT_VERSION,
            "grader_provider": grader_provider,
            "grader_model": grader_model,
            "c1_repair_before_structure": True,
            "c2_verifier_observations": context.verifier_observations,
            "c3_sample_count": consensus.sample_count,
            "c3_agreement_support": consensus.agreement_support,
            "c3_disagreement_causes": list(consensus.disagreement_causes),
            "c4_history_attempt_ids": [
                row["attempt_id"]
                for row in context.diagnostic_history
                if row.get("attempt_id")
            ],
            "hypotheses": PHASE_C_HYPOTHESES,
            "revert_criteria": PHASE_C_REVERT_CRITERIA,
        },
        clock=clock,
    )


def diagnostic_augmentation_report(repository: Repository) -> dict[str, Any]:
    """Read-only Stage-7 report, grouped by the version pins persisted at source."""

    realism = repository.persona_realism_run_rows()
    runs = repository.diagnostic_eval_run_rows()
    cases = repository.diagnostic_eval_case_rows()
    receipts = repository.diagnostic_augmentation_receipt_rows()
    return {
        "harness_version": DIAGNOSTIC_EVAL_HARNESS_VERSION,
        "phase_c_version": PHASE_C_VERSION,
        "regression_shapes": list(REGRESSION_SHAPES),
        "phase_c": {
            "hypotheses": dict(PHASE_C_HYPOTHESES),
            "revert_criteria": dict(PHASE_C_REVERT_CRITERIA),
            "live_receipts": len(receipts),
            "by_prompt_and_model": dict(
                sorted(
                    Counter(
                        "prompt="
                        + str(row.get("grading_prompt_version") or "unknown")
                        + "|model="
                        + str(row.get("grader_model") or "unknown")
                        for row in receipts
                    ).items()
                )
            ),
        },
        "persona_realism": {
            "runs": len(realism),
            "latest": realism[-1] if realism else None,
        },
        "planted_evaluation": {
            "runs": len(runs),
            "licensed_runs": sum(row["status"] == "licensed" for row in runs),
            "cases": len(cases),
            "latest": runs[-1] if runs else None,
        },
    }
