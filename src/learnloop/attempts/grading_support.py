"""PF-c grading support for the learner-blind grader (Slice 2 §5.5, at S1.1).

The blind grader is still the measurement; this module changes what it is
asked and adds deterministic guards around what it returns. It never gives the
grader learner history (S1): every input here is item-side or the current
answer.

* **Verified reference first.** The reference policy tells the grader whether
  an authored reference exists. The vault has no verified-reference store yet
  (PF-b builds it); authored references are labelled ``authored`` honestly.
* **Valid-alternative path.** A deterministic check of the answer's concluding
  line against the reference (``final_answer_check``) is computed before the
  call. When the final answer verifies, the grader re-derives the learner's own
  route instead of diffing it against the reference, and a criterion may be
  marked down only where that re-derivation locates a concrete error in the
  learner's words. Otherwise the criterion is recorded ``unverified``: its
  attributions carry ``validity_scope = grader_interpretation``. The gate is
  server-side and deterministic; the grader's own ``unverified_criterion_ids``
  only add to it. Each unverified criterion is also persisted as such: its
  grading-evidence row carries the ``negative_evidence_blocked`` attribution
  ``valid_alternative_unverified`` (live grades and regrades alike).
  Owner decision 2026-10-12: an unverified criterion is UNASSESSED
  everywhere - no credit and no failure. Each record names the rule it was
  written under (the row block's and the support's
  ``unverified_interpretation``), so a record from before the rule replays as
  written; a regrade rewrites it under the rule. It leaves the attempt's
  grade (``attempts.assessed_rubric_score``), so the FSRS rating too; it has
  no facet mass or outcome in the attempt step, the canonical projection, the
  evidence timeline or the learner field; and it alone never queues a
  diagnosis (``assessed_shortfall``). ``manual_review_recommended`` and the
  reason stay as a non-blocking log: nothing waits on a review. The reason is
  the attempt's only when it is the grade's sole review concern
  (``gated_review_reason``, review F7): a concern the grade carries without
  the gate stays its reason, and blocking.
* **Solve-first without a reference.** The grader writes its own expected
  answer before reading the learner's, and scores claims, not prose.
* **One pass.** No voting. Where k-sampling is configured, the modal
  fingerprint is over (abstained, anchor, criterion outcomes) only, and a
  shadow log records how often the asymmetric rule ("negative evidence only
  when every sample agrees") would differ from it.
* **Grade-uncertainty signal (shadow).** The new grade is compared with prior
  blind grades on the same family's variants plus the grader's verbal
  confidence. It is recorded on the blind record and read by nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.schemas import WireModel
from learnloop.ai.transport import OperationClient, execute_structured_operation
from learnloop.attempts.ai_contracts import (
    ClarificationRequest,
    CriterionEvidence,
    DiscriminationProfileMatch,
    ErrorHuntReport,
    ExercisedFacetObservation,
)
from learnloop.attempts.blind_grading import (
    BLIND_GRADING_PROMPT_VERSION,
    BlindErrorAttribution,
    BlindGradingContext,
    BlindGradingProposal,
    BlindRepairedTrace,
    blind_grading_prompt,
    validate_blind_grading_proposal,
)
from learnloop.attempts.answer_check import final_answer_check
from learnloop.substrate.canonical_projection import (
    UNASSESSED_INTERPRETATION,
    UNVERIFIED_CRITERION_BLOCK,
    UNVERIFIED_INTERPRETATION_KEY,
    surface_group_id,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

#: PF-c prompt identity (Slice 2 §5.5) and its calibration identity (§4.3), so
#: calibration never pools the mvp-2.0 and mvp-2.1 blind graders.
REFERENCE_POLICY_PROMPT_VERSION = "mvp-2.1-blind-reference-policy"
REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION = "grading_prompt_v2_1_blind_reference_policy"
GRADING_SUPPORT_VERSION = "pf-c-grading-support-v1"
#: The manual-review reason, and the per-criterion block reason persisted in
#: ``grading_evidence.attribution_json`` (one value, read by the projection).
#: As a review reason it is a non-blocking log (owner decision 2026-10-12),
#: recorded only when it is the grade's sole review concern (review F7).
UNVERIFIED_REVIEW_REASON = UNVERIFIED_CRITERION_BLOCK
#: How every learner-facing surface shows an unverified criterion: not
#: assessed, never as lost points.
UNASSESSED_CRITERION_LABEL = "not assessed (a different route)"

REFERENCE_POLICY_RULES = (
    "REFERENCE POLICY (`context.reference_policy`). `reference_status` says "
    "whether the expected answer is an authored reference (`authored`) or "
    "absent (`absent`). `final_answer_check` is a deterministic, server-side "
    "comparison of the learner's concluding line with the reference; never "
    "re-litigate it. "
    "SOLVE FIRST when `reference_status` is `absent`: before reading the "
    "learner's answer, write your own expected answer from the item in "
    "`solve_first_answer_md`, then grade the learner's CLAIMS against it, not "
    "their prose, fluency or length. Otherwise leave `solve_first_answer_md` "
    "null. "
    "VALID ALTERNATIVES: a correct derivation can differ from the reference. "
    "Set `route_check.divergent_route` when the learner's route differs from "
    "the reference's. When it does and `final_answer_check.status` is "
    "`matches_reference`, do NOT diff the trace against the reference: "
    "re-derive the learner's own route step by step in "
    "`route_check.rederivation_md`. Mark a criterion below full points only "
    "where that re-derivation locates a CONCRETE error, and cite it as an "
    "error_attribution whose first_divergence quote is copied verbatim from the "
    "learner's answer. A criterion you cannot verify either way goes in "
    "`unverified_criterion_ids` - it is recorded unverified, not failed. "
    "Grade in ONE careful pass."
)


class RouteCheck(WireModel):
    divergent_route: bool = False
    rederivation_md: str = ""
    concrete_error_located: bool = False


class ReferencePolicyBlindGradingProposal(WireModel):
    """The mvp-2.1 wire model: PF-c fields in generation order around the
    shared blind fields (solve-first BEFORE the analysis; the route check
    right after it)."""

    solve_first_answer_md: str | None = None
    local_analysis_md: str
    route_check: RouteCheck = Field(default_factory=RouteCheck)
    repaired_traces: list[BlindRepairedTrace] = Field(default_factory=list)
    attempt_id: str
    practice_item_id: str
    criterion_evidence: list[CriterionEvidence] = Field(default_factory=list)
    rubric_score: int = Field(ge=0)
    fatal_errors: list[str] = Field(default_factory=list)
    error_attributions: list[BlindErrorAttribution] = Field(default_factory=list)
    unverified_criterion_ids: list[str] = Field(default_factory=list)
    grader_confidence: float = Field(ge=0.0, le=1.0)
    manual_review_recommended: bool = False
    feedback_md: str | None = None
    clarification_request: ClarificationRequest | None = None
    discrimination_profile_match: DiscriminationProfileMatch | None = None
    error_hunt_report: ErrorHuntReport | None = None
    exercised_facets: list[ExercisedFacetObservation] = Field(default_factory=list)

    def as_blind_proposal(self) -> BlindGradingProposal:
        payload = self.model_dump(
            mode="json",
            exclude={"solve_first_answer_md", "route_check", "unverified_criterion_ids"},
        )
        return BlindGradingProposal.model_validate(payload)


def reference_policy(item: PracticeItem, learner_answer_md: str) -> dict[str, Any]:
    """The PF-c policy block for one answer (item-side + this answer only)."""

    expected = item.expected_answer
    text = expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True)
    has_reference = bool((text or "").strip())
    return {
        "version": GRADING_SUPPORT_VERSION,
        "reference_status": "authored" if has_reference else "absent",
        "final_answer_check": final_answer_check(learner_answer_md, expected),
    }


# -- the deterministic valid-alternative gate ---------------------------------

_WS = re.compile(r"\s+")


def _squash(text: str) -> str:
    return _WS.sub(" ", text or "").strip().casefold()


def _attribution_criteria(attribution: BlindErrorAttribution) -> set[str]:
    criteria = {str(value) for value in attribution.target_criterion_ids}
    ref = attribution.target_ref
    if ref is not None and getattr(ref, "kind", None) == "criterion":
        criteria.add(str(getattr(ref, "criterion_id", "")))
    divergence = attribution.first_divergence
    if divergence is not None and getattr(divergence, "criterion_id", None):
        criteria.add(str(divergence.criterion_id))
    return criteria


def _located(attribution: BlindErrorAttribution, answer: str) -> bool:
    divergence = attribution.first_divergence
    quote = getattr(divergence, "quote", None) if divergence is not None else None
    return bool(quote and _squash(quote) and _squash(quote) in _squash(answer))


@dataclass(frozen=True)
class GateOutcome:
    proposal: BlindGradingProposal
    unverified_criterion_ids: tuple[str, ...] = ()
    applied: bool = False
    reason: str | None = None
    #: When the gate applied: whether anything ASSESSED fell short - a
    #: criterion below full points that is not unverified, or an attribution
    #: the gate left in force. False means every shortfall is unassessed.
    assessed_shortfall: bool = True


def apply_valid_alternative_gate(
    proposal: BlindGradingProposal,
    *,
    rubric: Rubric,
    learner_answer_md: str,
    policy: Mapping[str, Any] | None,
    declared_unverified: Sequence[str] = (),
) -> GateOutcome:
    """Record unlocated failures on a verifying answer as unverified.

    Fires only when the deterministic final-answer check says the concluding
    line equals the reference. Every criterion below full points that no
    attribution locates verbatim in the learner's answer (plus any the grader
    itself declared unverified) is unverified: attributions on it are rescoped
    to ``grader_interpretation`` and ``manual_review_recommended`` is set (a
    non-blocking log). The proposal's points are left as the grader awarded
    them; the attempt step treats an unverified criterion as unassessed (no
    credit, no failure, out of the grade).
    """

    check = (policy or {}).get("final_answer_check") or {}
    if check.get("status") != "matches_reference":
        return GateOutcome(proposal)
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    awarded = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
    below = {cid for cid, maximum in maxima.items() if awarded.get(cid, maximum) + 1e-9 < maximum}
    located: set[str] = set()
    for attribution in proposal.error_attributions:
        if _located(attribution, learner_answer_md):
            located.update(_attribution_criteria(attribution))
    unverified = {cid for cid in below if cid not in located}
    unverified.update(str(cid) for cid in declared_unverified if str(cid) in below)
    if not unverified:
        return GateOutcome(proposal)
    attributions = []
    attribution_in_force = False
    for attribution in proposal.error_attributions:
        criteria = _attribution_criteria(attribution)
        untargeted = not criteria
        if (criteria & unverified) or (untargeted and not _located(attribution, learner_answer_md)):
            attribution = attribution.model_copy(update={"validity_scope": "grader_interpretation"})
        else:
            attribution_in_force = True
        attributions.append(attribution)
    gated = proposal.model_copy(
        update={"error_attributions": attributions, "manual_review_recommended": True}
    )
    return GateOutcome(
        gated,
        unverified_criterion_ids=tuple(sorted(unverified)),
        applied=True,
        reason=UNVERIFIED_REVIEW_REASON,
        assessed_shortfall=bool(below - unverified) or attribution_in_force,
    )


# -- blind k-sampling ------------------------------------------------------------

def _anchor_key(proposal: BlindGradingProposal) -> str | None:
    rows = proposal.error_attributions
    if not rows:
        return None
    primary = max(rows, key=lambda row: (float(row.severity or 0.0), bool(row.first_divergence)))
    divergence = primary.first_divergence
    if divergence is None:
        return None
    return json.dumps(
        {
            "criterion_id": getattr(divergence, "criterion_id", None),
            "quote": _squash(getattr(divergence, "quote", "") or ""),
        },
        sort_keys=True,
    )


def _abstained(proposal: BlindGradingProposal) -> bool:
    rows = proposal.error_attributions
    return bool(rows) and all(row.resolution_status == "abstained" for row in rows)


def criterion_outcomes(proposal: BlindGradingProposal, rubric: Rubric) -> dict[str, str]:
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    out: dict[str, str] = {}
    for row in proposal.criterion_evidence:
        maximum = maxima.get(row.criterion_id)
        if maximum is None:
            continue
        out[row.criterion_id] = "pass" if float(row.points_awarded) + 1e-9 >= maximum else "fail"
    return dict(sorted(out.items()))


def sample_fingerprint(proposal: BlindGradingProposal, rubric: Rubric) -> str:
    """§4.4 split-mode fingerprint: (abstained, anchor, criterion outcomes)."""

    identity = {
        "abstained": _abstained(proposal),
        "anchor": _anchor_key(proposal),
        "criteria": criterion_outcomes(proposal, rubric),
    }
    return hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:24]


def modal_sample(
    proposals: Sequence[BlindGradingProposal], rubric: Rubric
) -> tuple[int, dict[str, Any]]:
    """(index of the modal sample, the shadow sampling log)."""

    fingerprints = [sample_fingerprint(proposal, rubric) for proposal in proposals]
    counts = Counter(fingerprints)
    winner_fingerprint, winner_votes = max(
        counts.items(), key=lambda pair: (pair[1], -fingerprints.index(pair[0]))
    )
    winner = fingerprints.index(winner_fingerprint)
    log: dict[str, Any] = {
        "sample_count": len(proposals),
        "winner_votes": winner_votes,
        "distinct_fingerprints": len(counts),
    }
    if len(proposals) > 1:
        outcomes = [criterion_outcomes(proposal, rubric) for proposal in proposals]
        modal = outcomes[winner]
        unanimous_fail = {
            cid for cid in modal if all(row.get(cid) == "fail" for row in outcomes)
        }
        modal_fail = {cid for cid, outcome in modal.items() if outcome == "fail"}
        differs = sorted(modal_fail - unanimous_fail)
        log["asymmetric_rule"] = {
            "rule": "negative evidence only when every sample agrees",
            "would_differ": bool(differs),
            "criteria_modal_fails_not_unanimous": differs,
        }
    return winner, log


# -- grade-uncertainty signal (shadow) -----------------------------------------

def family_key(vault: LoadedVault, item: PracticeItem) -> str:
    """The family a variant belongs to: PF-a's ``family_id`` once it exists,
    else the independent-surface group (one code path, augmentation §8)."""

    family = getattr(item, "family_id", None)
    if family:
        return f"family:{family}"
    return f"surface:{surface_group_id(item)}"


def grade_uncertainty_signal(
    *,
    score_fraction: float,
    grader_confidence: float,
    prior_fractions: Sequence[float],
    family: str,
) -> dict[str, Any]:
    """Shadow only: never an input to the grader, never read by routing."""

    signal: dict[str, Any] = {
        "family": family,
        "prior_blind_grades": len(prior_fractions),
        "grader_confidence": round(float(grader_confidence), 4),
        "shadow": True,
    }
    if not prior_fractions:
        signal.update(disagreement=None, would_suggest=[])
        return signal
    mean = sum(prior_fractions) / len(prior_fractions)
    disagreement = abs(float(score_fraction) - mean)
    suggest: list[str] = []
    if len(prior_fractions) >= 2 and disagreement >= 0.5 and grader_confidence < 0.7:
        suggest = ["manual_review", "clarification", "regrade"]
    elif disagreement >= 0.5 and grader_confidence < 0.5:
        suggest = ["manual_review"]
    signal.update(
        prior_mean_fraction=round(mean, 4),
        disagreement=round(disagreement, 4),
        would_suggest=suggest,
    )
    return signal


# -- one blind grading run -----------------------------------------------------------

@dataclass
class BlindGradingRun:
    proposal: BlindGradingProposal
    prompt_version: str
    grading_support: dict[str, Any] = field(default_factory=dict)
    samples: int = 1
    #: The modal proposal as the grader returned it, before the PF-c gate
    #: forced its review flag and rescoped its attributions (review F7).
    ungated_proposal: BlindGradingProposal | None = None


def gated_review_reason(
    run: BlindGradingRun,
    *,
    attempt_id: str,
    item: PracticeItem,
    vault: LoadedVault,
    learner_answer_md: str,
    rubric: Rubric,
) -> str | None:
    """The attempt's manual-review reason when the PF-c gate applied, else None.

    The gate's reason is informational, so it is the attempt's reason only when
    it is the grade's SOLE review concern (review F7). The gated proposal cannot
    say whether it is: the gate forces ``manual_review_recommended`` and
    rescopes attributions, so its validated reason is always the gate's. The
    grade's own concerns are read from the grader's proposal as returned,
    validated the same way. Any reason found there (the grader's own
    recommendation, low confidence, an unknown target, a pending
    clarification...) stays the attempt's reason: a blocking review, which
    retention reads as an unresolved grade. The PF-c state itself is on the
    evidence rows and the blind record, whichever reason is recorded.
    """

    if not run.grading_support.get("valid_alternative_gate_applied"):
        return None
    own = None
    if run.ungated_proposal is not None:
        own = validate_blind_grading_proposal(
            run.ungated_proposal,
            attempt_id=attempt_id,
            item=item,
            vault=vault,
            learner_answer_md=learner_answer_md,
            rubric=rubric,
        ).grade.manual_review_reason
    return own if own is not None else UNVERIFIED_REVIEW_REASON


def request_blind_grading_run(
    client: OperationClient,
    context: BlindGradingContext,
    *,
    rubric: Rubric,
    sample_count: int = 1,
) -> BlindGradingRun:
    """k isolated blind grading calls (k=1 by default), modal choice, PF-c gate."""

    if sample_count < 1:
        raise ValueError("sample_count must be at least 1")
    policy = context.reference_policy
    prompt = blind_grading_prompt(context)
    raw: list[BlindGradingProposal] = []
    declared: list[list[str]] = []
    extras: list[dict[str, Any]] = []
    for _ in range(sample_count):
        if policy is not None:
            result = execute_structured_operation(
                client,
                purpose="blind_grading",
                prompt=prompt,
                result_model=ReferencePolicyBlindGradingProposal,
                isolated=True,
            )
            raw.append(result.as_blind_proposal())
            declared.append(list(result.unverified_criterion_ids))
            extras.append(
                {
                    "solve_first_written": bool((result.solve_first_answer_md or "").strip()),
                    "route_check": result.route_check.model_dump(mode="json"),
                }
            )
        else:
            raw.append(
                execute_structured_operation(
                    client,
                    purpose="blind_grading",
                    prompt=prompt,
                    result_model=BlindGradingProposal,
                    isolated=True,
                )
            )
            declared.append([])
            extras.append({})
    winner, sampling = modal_sample(raw, rubric) if len(raw) > 1 else (0, {"sample_count": 1})
    ungated = proposal = raw[winner]
    support: dict[str, Any] = {"version": GRADING_SUPPORT_VERSION, "sampling": sampling}
    if policy is not None:
        gate = apply_valid_alternative_gate(
            proposal,
            rubric=rubric,
            learner_answer_md=context.learner_answer_md,
            policy=policy,
            declared_unverified=declared[winner],
        )
        proposal = gate.proposal
        support.update(
            reference_policy=dict(policy),
            route_check=extras[winner].get("route_check"),
            solve_first_written=extras[winner].get("solve_first_written", False),
            grader_unverified_criterion_ids=sorted(declared[winner]),
            unverified_criterion_ids=list(gate.unverified_criterion_ids),
            valid_alternative_gate_applied=gate.applied,
        )
        if gate.applied:
            support["assessed_shortfall"] = gate.assessed_shortfall
            # The interpretation its unverified criteria are recorded under
            # (review F5): a record without it predates the unassessed rule.
            support[UNVERIFIED_INTERPRETATION_KEY] = UNASSESSED_INTERPRETATION
    return BlindGradingRun(
        proposal=proposal,
        prompt_version=(
            REFERENCE_POLICY_PROMPT_VERSION if policy is not None else BLIND_GRADING_PROMPT_VERSION
        ),
        grading_support=support,
        samples=len(raw),
        ungated_proposal=ungated,
    )


__all__ = [
    "BlindGradingRun",
    "GRADING_SUPPORT_VERSION",
    "GateOutcome",
    "REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION",
    "REFERENCE_POLICY_PROMPT_VERSION",
    "REFERENCE_POLICY_RULES",
    "ReferencePolicyBlindGradingProposal",
    "RouteCheck",
    "UNASSESSED_CRITERION_LABEL",
    "UNVERIFIED_REVIEW_REASON",
    "apply_valid_alternative_gate",
    "criterion_outcomes",
    "family_key",
    "gated_review_reason",
    "grade_uncertainty_signal",
    "modal_sample",
    "reference_policy",
    "request_blind_grading_run",
    "sample_fingerprint",
]
