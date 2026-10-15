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
* **Own-route rules (mvp-0.20, route-check-in-grader).** The grader is told to
  grade every criterion on the learner's own route (a criterion phrased in
  one method is met by any valid method that establishes the same fact), to
  mark a criterion down only by quoting the failing step verbatim, and to say
  so rather than mark down a route it cannot verify (``ROUTE_RULES``, on the
  reference policy as ``route_rules``). One deterministic rule then reads
  only the grader's output (:func:`apply_route_rule`). On a route the grader
  reads as divergent (``route_check.divergent_route``) these are unverified,
  so unassessed (P1: marked down only on a located error): a mark-down with
  no verbatim quote in the learner's words (the answer, or the learner's
  clarification reply), an omitted criterion, and a mark-down the grader
  itself declared it could not verify. With nothing then assessed and
  nothing validated the answer (no verified final answer), the grade is held
  for review (``outcome_contract.grade_is_held``). A conclusion that
  ``differs_from_reference`` is never unassessed, and fatal errors keep their
  mark-downs. Each ruled grade's route verdict is appended to
  ``judgment_ledger`` (task ``own_route_rule``; a regrade supersedes it, as
  ``not_checked`` when the rule did not run over the new grade). It
  replaced mvp-0.17's separate item reading, re-derivation call and gate
  (owner decision 2026-10-13): one grading call.
* **Required methods (method-explicit successor, ``own-route-v2``).** Owner
  rule 2026-10-13: criteria name facts, and an item whose target IS a method
  records it as ``PracticeItem.required_method`` and is presented with the
  instruction rendered from that field ("Use {method} in your answer.", after
  the statement, on every surface and in the grader's question; round 3). The policy then carries the
  ``required_method`` (name and criterion ids) the answer's assessment
  contract froze when the item was presented (review F1: a method added or
  changed later never reaches that answer, at grading or at a regrade), only
  when the prompt the learner answered requires it, and the prompt adds
  :data:`REQUIRED_METHOD_RULES`: a criterion tied to the required method is
  graded on USE of that method. On a route the grader reads as divergent, a
  mark-down of such a criterion stays assessed with no quoted wrong step (the
  route is the evidence): neither PF-c's gate nor the unlocated rule
  unassesses it (the grader's own "cannot verify" still does). Every other
  criterion keeps the own-route rules. Kill switch ``required_method.enabled``
  (off: mvp-0.20's grading exactly).
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
    BlindErrorAttribution,
    BlindGradingContext,
    BlindGradingProposal,
    BlindRepairedTrace,
    StuckBlindGradingProposal,
    blind_grading_prompt,
    blind_prompt_version,
    validate_blind_grading_proposal,
)
from learnloop.attempts.grading_admission import admit_grading_call
from learnloop.attempts.stuck import StuckReading
from learnloop.attempts.answer_check import final_answer_check
from learnloop.algorithm_versions import METHOD_EXPLICIT_VERSIONS, ROUTE_RULES_VERSIONS
from learnloop.outcome_contract import GRADE_HELD_FOR_REVIEW
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

#: mvp-0.20 (route-check-in-grader): the own-route rules' identity. It is the
#: reference policy's ``route_rules`` value, and its suffix names both the
#: prompt (``mvp-2.1-blind-reference-policy+own-route-v1``) and the
#: calibration identity, so calibration never pools these grades with the
#: rules-free grader's (S1 section 4.3).
ROUTE_RULES_VERSION = "own-route-v1"
ROUTE_RULES_SUFFIX = f"+{ROUTE_RULES_VERSION}"
ROUTE_RULES = (
    "OWN ROUTE (`context.reference_policy.route_rules` is set). Grade EVERY "
    "criterion on the learner's OWN route, whatever `final_answer_check` says. "
    "A criterion phrased in terms of one method is met by ANY valid method "
    "that establishes the same fact; an unusual, terse or differently ordered "
    "route is not an error when each step is valid and its justification is "
    "standard. When the route differs from the reference's, set "
    "`route_check.divergent_route`, restate the learner's route step by step "
    "in `route_check.rederivation_md` and check each step on its own terms; "
    "never accept a step because its conclusion happens to be true. Mark a "
    "criterion below full points ONLY by quoting the step that fails it: an "
    "error_attribution naming that criterion whose first_divergence quote is "
    "copied VERBATIM from the learner's answer (for a missing step, the "
    "sentence whose conclusion relies on it). When you cannot verify a step of "
    "a different route, say so instead of marking the criterion down for it: "
    "explain why in its evidence and list it in `unverified_criterion_ids`. A "
    "mark-down on a divergent route that quotes nothing from the answer is "
    "recorded as not assessed."
)
#: The method-explicit successor's rules (owner rule 2026-10-13): the own-route
#: rules plus :data:`REQUIRED_METHOD_RULES`. Its suffix names the prompt
#: (``...+own-route-v2``) and the calibration identity, whether or not the
#: graded item has a required method (the prompt's rules are the same).
METHOD_ROUTE_RULES_VERSION = "own-route-v2"
METHOD_ROUTE_RULES_SUFFIX = f"+{METHOD_ROUTE_RULES_VERSION}"
REQUIRED_METHOD_RULES = (
    "REQUIRED METHOD (`context.reference_policy.required_method`, when set): the "
    "item's own statement requires the learner to use the method "
    "`required_method.name`. Each criterion listed in "
    "`required_method.criterion_ids` is graded on USE of that method: an answer "
    "that reaches the result by another route FAILS that criterion even when every "
    "step of its own route is valid. Set `route_check.divergent_route`, name the "
    "method the learner used instead in that criterion's evidence, and mark it down "
    "without needing to quote a wrong step: the route itself is the evidence. Do "
    "not list such a criterion in `unverified_criterion_ids` merely because the "
    "route differs; list it only when you genuinely cannot tell whether the method "
    "was used. Grade every OTHER criterion by the OWN ROUTE rules above: by the fact "
    "it establishes, on the learner's own route, whatever method they used."
)
ROUTE_RULES_V2 = f"{ROUTE_RULES} {REQUIRED_METHOD_RULES}"
#: The prompt text of each own-route rules version.
ROUTE_RULES_TEXT: dict[str, str] = {
    ROUTE_RULES_VERSION: ROUTE_RULES,
    METHOD_ROUTE_RULES_VERSION: ROUTE_RULES_V2,
}


def route_rules_text(version: str) -> str:
    """The prompt text of an own-route rules version (``own-route-v1``/``-v2``)."""

    return ROUTE_RULES_TEXT[version]


def route_rules_suffix(version: str) -> str:
    """The prompt and calibration identity suffix of a rules version."""

    return f"+{version}"


#: The record the server-side rule writes on the blind record, under the key
#: the held-grade predicate reads (``outcome_contract.grade_held_for_review``;
#: mvp-0.17's route-check records use the same key, and their gate versions
#: ``proof-route-check-v1``..``v3`` keep their meaning). ``status = checked``
#: says the rule ran over this grade.
ROUTE_RULE_SUPPORT_KEY = "proof_route_check"
ROUTE_RULE_RECORD_VERSION = "route-rules-in-grader-v1"
#: The attempt's review reason when the rule holds the grade for review (a
#: real review: nothing assessed and nothing validated).
HELD_REVIEW_REASON = GRADE_HELD_FOR_REVIEW
#: ``final_answer_check`` statuses the rule reads.
DIFFERS_FROM_REFERENCE = "differs_from_reference"
MATCHES_REFERENCE = "matches_reference"


def route_rules_active(vault: LoadedVault) -> bool:
    """Does this vault grade NEW blind answers under the own-route rules?

    The algorithm version gates them (``ROUTE_RULES_VERSIONS``);
    ``proof_check.enabled`` is the kill switch (off: new answers grade as
    mvp-0.19 now does, whose grading is mvp-0.16's). Read only when an answer is graded
    or regraded: the reference policy then carries ``route_rules`` and the
    blind record carries the rule's outcome, which is what replay reads.
    """

    config = vault.config
    if config.algorithms.algorithm_version not in ROUTE_RULES_VERSIONS:
        return False
    return bool(getattr(getattr(config, "proof_check", None), "enabled", True))


def method_rules_active(vault: LoadedVault) -> bool:
    """Does this vault grade NEW blind answers under the required-method rules?

    The method-explicit successor (``METHOD_EXPLICIT_VERSIONS``) on top of the
    own-route rules (:func:`route_rules_active`); ``required_method.enabled``
    is its kill switch (off: mvp-0.20's grading exactly).
    """

    if not route_rules_active(vault):
        return False
    if vault.config.algorithms.algorithm_version not in METHOD_EXPLICIT_VERSIONS:
        return False
    return bool(getattr(getattr(vault.config, "required_method", None), "enabled", True))


def route_rules_version(vault: LoadedVault) -> str | None:
    """The own-route rules version new blind answers are graded under, if any."""

    if method_rules_active(vault):
        return METHOD_ROUTE_RULES_VERSION
    if route_rules_active(vault):
        return ROUTE_RULES_VERSION
    return None


class _ItemRequiredMethod:
    """:func:`reference_policy`'s default source: the item's current required method."""

    def __repr__(self) -> str:
        return "ITEM_REQUIRED_METHOD"


#: Read the required method from the item as it is now (the gold-set harness
#: and callers that grade the item as currently stated). The live doors pass
#: the method frozen with the answer's assessment contract instead (review F1).
ITEM_REQUIRED_METHOD: Any = _ItemRequiredMethod()


def required_method_policy(
    item: PracticeItem,
    rubric_criterion_ids: Sequence[str] | None = None,
    *,
    required_method: Mapping[str, Any] | None | Any = ITEM_REQUIRED_METHOD,
) -> dict[str, Any] | None:
    """The required method as the grader's policy shows it, or None.

    ``required_method`` is the method the answer is graded under: the one its
    assessment contract froze when the item was presented (``None``: the
    presented item required none, and an answer never acquires one from
    content changed later; review F1), or, by default, the item's current one.
    Only criteria of the rubric being graded are listed (an unknown id is
    doctor's ``required_method:unknown_criterion``, never graded).

    The field is the ONE authority (redesign 2026-10-14): nothing here reads
    the prompt. Whether the statement requires the method was settled when
    the field was written (a one-time, ledgered judgment on a source
    statement), and the contract froze the result with the statement the
    learner answered; the instruction the learner and the grader were shown
    is rendered from it (``learnloop.vault.required_method.presented_prompt``).
    """

    if required_method is ITEM_REQUIRED_METHOD:
        current = getattr(item, "required_method", None)
        method = (
            {"name": current.name, "criterion_ids": list(current.criterion_ids)} if current is not None else None
        )
    else:
        method = dict(required_method) if isinstance(required_method, Mapping) else None
    if method is None or not str(method.get("name") or "").strip():
        return None
    name = str(method["name"])
    known = set(rubric_criterion_ids) if rubric_criterion_ids is not None else None
    criterion_ids = [str(cid) for cid in method.get("criterion_ids") or () if known is None or str(cid) in known]
    return {"name": name, "criterion_ids": criterion_ids}


def policy_method_criteria(policy: Mapping[str, Any] | None) -> tuple[str, ...]:
    """The criterion ids a policy's required method grades on use of the method."""

    method = (policy or {}).get("required_method")
    if not isinstance(method, Mapping):
        return ()
    return tuple(str(value) for value in method.get("criterion_ids") or ())


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
            exclude={
                "solve_first_answer_md",
                "route_check",
                "unverified_criterion_ids",
                "stuck_reading",
            },
        )
        return BlindGradingProposal.model_validate(payload)


class StuckReferencePolicyBlindGradingProposal(ReferencePolicyBlindGradingProposal):
    """mvp-2.1 for a stuck answer (``mvp-0.13``): the reading comes LAST."""

    stuck_reading: StuckReading


def blind_result_model(context: BlindGradingContext) -> type[WireModel]:
    """The wire model one blind grading call returns for this context."""

    if context.reference_policy is not None:
        if context.answer_prompt is not None:
            return StuckReferencePolicyBlindGradingProposal
        return ReferencePolicyBlindGradingProposal
    if context.answer_prompt is not None:
        return StuckBlindGradingProposal
    return BlindGradingProposal


def reference_policy(
    item: PracticeItem,
    learner_answer_md: str,
    *,
    route_rules: bool | str = False,
    rubric_criterion_ids: Sequence[str] | None = None,
    required_method: Mapping[str, Any] | None | Any = ITEM_REQUIRED_METHOD,
) -> dict[str, Any]:
    """The PF-c policy block for one answer (item-side + this answer only).

    ``route_rules`` (mvp-0.20) adds the own-route rules' identity: the prompt
    then carries :data:`ROUTE_RULES` and the server applies
    :func:`apply_route_rule`. ``True`` is ``own-route-v1``; a version string
    names the rules (``own-route-v2``, the method-explicit successor, also
    shows the ``required_method`` the answer is graded under: the one its
    contract froze, by default the item's, its criteria limited to
    ``rubric_criterion_ids``; :func:`required_method_policy`, which never
    reads the prompt). Without it the block is exactly mvp-2.1's.
    """

    expected = item.expected_answer
    text = expected if isinstance(expected, str) else json.dumps(expected, sort_keys=True)
    has_reference = bool((text or "").strip())
    policy = {
        "version": GRADING_SUPPORT_VERSION,
        "reference_status": "authored" if has_reference else "absent",
        "final_answer_check": final_answer_check(learner_answer_md, expected),
    }
    if route_rules:
        version = ROUTE_RULES_VERSION if route_rules is True else str(route_rules)
        if version not in ROUTE_RULES_TEXT:
            raise ValueError(f"unknown own-route rules version {version!r}")
        policy["route_rules"] = version
        if version == METHOD_ROUTE_RULES_VERSION:
            method = required_method_policy(item, rubric_criterion_ids, required_method=required_method)
            if method is not None:
                policy["required_method"] = method
    return policy


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
    method_criterion_ids: Sequence[str] = (),
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

    ``method_criterion_ids`` (the method-explicit successor) are the item's
    required-method criteria on a route the grader reads as divergent: the
    route is their evidence, so an unlocated mark-down of one stays assessed
    (only the grader's own declaration unverifies it).
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
    exempt = {str(value) for value in method_criterion_ids}
    unverified = {cid for cid in below if cid not in located and cid not in exempt}
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


# -- the own-route rule (mvp-0.20) ---------------------------------------------------


def _named_criteria(attribution: BlindErrorAttribution, rubric_ids: Sequence[str] | set[str]) -> set[str]:
    """The rubric criteria an attribution names (held-grade-evidence F1).

    Only ids of this rubric count: a blank or unknown id (``[""]``, a
    criterion ``target_ref`` with no id) names no criterion. Validation drops
    such ids after the rule, so the rule reads the attribution as validation
    will keep it: untargeted, and so rescoped like any whole-answer claim
    when it locates nothing.
    """

    named = {value for value in _attribution_criteria(attribution) if value.strip()}
    return named & set(rubric_ids)


def _located_in_force(attribution: BlindErrorAttribution, texts: Sequence[str]) -> bool:
    """A concrete error in the learner's words, still in force (P1).

    ``texts`` are the learner's own words this grade read: the answer and,
    on a clarification regrade, the learner's reply (never the question).
    """

    return attribution.validity_scope != "grader_interpretation" and any(
        _located(attribution, text) for text in texts if text
    )


#: Why the rule left a criterion unassessed (its evidence row's note).
_UNLOCATED_NOTE = "Not assessed: no error was located in your own route here."
_DECLARED_NOTE = "Not assessed: the grader could not verify this step of your own route."


@dataclass(frozen=True)
class RouteRuleOutcome:
    proposal: BlindGradingProposal
    #: Marked down on a divergent route with no verbatim quote in the
    #: learner's words (an omitted criterion scores 0, so it counts: review F1).
    unlocated: tuple[str, ...] = ()
    #: Marked down on a divergent route although the grader itself declared
    #: it could not verify the criterion (``unverified_criterion_ids``,
    #: review F2): its quote, if any, does not make the mark-down a located
    #: error.
    declared: tuple[str, ...] = ()
    #: Every unverified criterion after PF-c's gate and this rule.
    unverified: tuple[str, ...] = ()
    #: Marked-down criteria that stay assessed only because a quote occurs in
    #: the learner's clarification reply (review F3), not in the answer.
    clarification_located: tuple[str, ...] = ()
    #: The item's required-method criteria marked down on the divergent route
    #: with no located quote: they stay assessed, the route is the evidence
    #: (the method-explicit successor; empty below it).
    method_route: tuple[str, ...] = ()
    #: Nothing assessed and nothing validated the answer.
    held_for_review: bool = False
    assessed_shortfall: bool = True

    @property
    def applied(self) -> bool:
        return bool(self.unlocated or self.declared)


def apply_route_rule(
    proposal: BlindGradingProposal,
    *,
    rubric: Rubric,
    learner_answer_md: str,
    final_answer_status: str | None,
    divergent_route: bool,
    unverified_before: Sequence[str] = (),
    declared_unverified: Sequence[str] = (),
    clarification_answer_md: str | None = None,
    method_criterion_ids: Sequence[str] = (),
) -> RouteRuleOutcome:
    """P1 on the grader's own output: no located error, no mark-down.

    ``proposal`` is the blind proposal after PF-c's gate and
    ``unverified_before`` the criteria PF-c recorded unverified. On a route
    the grader reads as divergent (``divergent_route``), whose conclusion is
    not shown to differ from the reference and whose grade carries no fatal
    error, every criterion below full points is unverified, so unassessed (no
    credit, no failure), when either

    * no attribution in force locates it with a quote that occurs verbatim in
      the learner's words (**unlocated**). The learner's words are the answer
      and, on a clarification regrade, the learner's reply
      (``clarification_answer_md``, review F3; never the machine's question).
      A fabricated quote locates nothing. A criterion the grader omitted
      scores 0 in validation (the grade is the sum of the rows present), so
      it is below full points like any other mark-down (review F1); or
    * the grader itself declared it could not verify it
      (``declared_unverified``, the grader's ``unverified_criterion_ids``,
      review F2), quote or not (**declared**). PF-c reads that declaration
      only on a verified final answer; this rule reads it on a divergent
      route.

    When nothing is then assessed and the final answer was not verified, the
    grade is **held for review**: the grader's own score, provisional
    (``outcome_contract.grade_is_held``).

    Once the rule unassesses a mark-down, attributions on unverified criteria
    and attributions that name no criterion and locate nothing are the
    grader's interpretation (PF-c's rescoping), so an unlocated claim never
    keeps the attempt a measured failure on its own. Points are left as the
    grader awarded them; the evidence rows of unassessed criteria say why
    they are not assessed. Anything else leaves the proposal unchanged.

    ``method_criterion_ids`` (the method-explicit successor, ``own-route-v2``)
    are the item's required-method criteria. They are graded on USE of the
    method, so on a divergent route a mark-down of one needs no located
    quote: it is never unlocated (the route is the evidence) and stays
    assessed (``method_route``). The grader's own declaration that it cannot
    verify one still unassesses it. Every other criterion keeps the rule.
    """

    previously = {str(value) for value in unverified_before}
    unchanged = RouteRuleOutcome(proposal, unverified=tuple(sorted(previously)))
    if not divergent_route or final_answer_status == DIFFERS_FROM_REFERENCE or proposal.fatal_errors:
        return unchanged
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    awarded = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
    # Review F1: an omitted criterion is worth what validation scores it, 0.
    below = {cid for cid, maximum in maxima.items() if awarded.get(cid, 0.0) + 1e-9 < maximum}
    reply = (clarification_answer_md or "").strip()
    texts = (learner_answer_md, reply)
    in_answer: set[str] = set()
    in_reply: set[str] = set()
    for attribution in proposal.error_attributions:
        if _located_in_force(attribution, (learner_answer_md,)):
            in_answer.update(_named_criteria(attribution, maxima))
        elif reply and _located_in_force(attribution, (reply,)):
            in_reply.update(_named_criteria(attribution, maxima))
    located = in_answer | in_reply
    declared_ids = {str(value) for value in declared_unverified}
    method_ids = {str(value) for value in method_criterion_ids} & set(maxima)
    declared = [cid for cid in maxima if cid in below and cid in declared_ids and cid not in previously]
    unlocated = [
        cid for cid in maxima
        if cid in below and cid not in located and cid not in previously and cid not in declared_ids
        and cid not in method_ids
    ]
    unverified = previously | set(unlocated) | set(declared)
    method_route = tuple(
        cid for cid in maxima if cid in method_ids and cid in below and cid not in located and cid not in unverified
    )
    from_reply = tuple(
        cid for cid in maxima if cid in below and cid in in_reply and cid not in in_answer and cid not in unverified
    )
    if not (unlocated or declared):
        return RouteRuleOutcome(
            proposal, unverified=tuple(sorted(previously)), clarification_located=from_reply,
            method_route=method_route,
        )
    # PF-c's "nothing assessed schedules as correct" rests on a verified final
    # answer; without one an all-unassessed grade rests on nothing.
    held = not (set(maxima) - unverified) and final_answer_status != MATCHES_REFERENCE
    evidence = []
    for row in proposal.criterion_evidence:
        if row.criterion_id in unlocated or row.criterion_id in declared:
            note = _DECLARED_NOTE if row.criterion_id in declared else _UNLOCATED_NOTE
            if held:
                note += " Held for review."
            row = row.model_copy(update={"notes": note})
        evidence.append(row)
    attributions = []
    attribution_in_force = False
    for attribution in proposal.error_attributions:
        criteria = _named_criteria(attribution, maxima)
        rescoped = (criteria and criteria <= unverified) or (
            not criteria and not _located_in_force(attribution, texts)
        )
        if rescoped:
            if attribution.validity_scope != "grader_interpretation":
                attribution = attribution.model_copy(update={"validity_scope": "grader_interpretation"})
        elif attribution.validity_scope != "grader_interpretation":
            attribution_in_force = True
        attributions.append(attribution)
    gated = proposal.model_copy(update={
        "criterion_evidence": evidence,
        "error_attributions": attributions,
        "manual_review_recommended": True,
    })
    return RouteRuleOutcome(
        gated,
        unlocated=tuple(unlocated),
        declared=tuple(declared),
        unverified=tuple(sorted(unverified)),
        clarification_located=from_reply,
        method_route=method_route,
        held_for_review=held,
        assessed_shortfall=bool(below - unverified) or attribution_in_force,
    )


#: ``judgment_ledger.task`` of one attempt's own-route verdict (review F4):
#: the grader's route reading and what the rule made of it, appended in the
#: transaction that records the grade (standard rule 6). Left = the attempt;
#: a regrade's verdict supersedes the attempt's current one. It replaces the
#: ledger rows mvp-0.17's separate check wrote (task ``proof_route_check``)
#: and needs no model call of its own.
ROUTE_RULE_JUDGMENT_TASK = "own_route_rule"
#: mvp-0.17's per-attempt verdict task. Nothing writes a checked one any
#: more; a grade that replaces the one it described supersedes it as not
#: checked (review F5).
LEGACY_ROUTE_CHECK_JUDGMENT_TASK = "proof_route_check"
#: The verdict a grade the rule did not run over writes when it replaces a
#: grade that has a current route verdict (review F5): the attempt's current
#: verdict then describes its current grade.
NOT_CHECKED_VERDICT = {"status": "not_checked"}


def _current_route_judgment(connection: Any, task: str, attempt_id: str) -> Any:
    return connection.execute(
        "SELECT j.id FROM judgment_ledger j "
        "WHERE j.task = ? AND j.left_kind = 'attempt' AND j.left_id = ? AND j.right_kind IS NULL "
        "AND NOT EXISTS (SELECT 1 FROM judgment_ledger s WHERE s.supersedes_id = j.id) "
        "ORDER BY j.created_at DESC, j.id DESC LIMIT 1",
        (task, attempt_id),
    ).fetchone()


def record_route_rule_judgment(
    connection: Any,
    *,
    attempt_id: str,
    grading_support: Mapping[str, Any],
    judge_model: str | None,
    prompt_version: str,
    input_hash: str,
    created_at: str,
) -> str | None:
    """Append the grade's own-route verdict to ``judgment_ledger`` (review F4).

    Called inside the transaction that records a grade and (for a blind
    grade) its blind record, live and on every regrade, blind or joint, so
    the verdict and the measurement commit together. ``prompt_version`` and
    ``input_hash`` are the grading run's (the blind grading context hash on a
    blind grade). Replay never writes one.

    * The rule ran over this grade (``status = checked`` on its record): its
      verdict is appended and supersedes the attempt's current one.
    * It did not (the kill switch, a version without the rules, PF-c off, a
      joint grade): when the attempt has a current verdict, a ``not_checked``
      verdict supersedes it (review F5), so the ledger never keeps a verdict
      current for a grade that was replaced. Nothing otherwise.

    mvp-0.17's verdict (task ``proof_route_check``) is superseded as not
    checked by any grade that replaces it. Returns the own-route row id, or
    None when none was written.
    """

    from learnloop.db.stores.judgments import append_judgment

    def append(task: str, verdict: Mapping[str, Any], rationale: str, current: Any) -> str:
        return append_judgment(
            connection,
            task=task,
            left_kind="attempt",
            left_id=attempt_id,
            judge="llm",
            judge_model=str(judge_model or "unknown"),
            prompt_version=prompt_version,
            input_hash=input_hash,
            verdict=json.dumps(verdict, sort_keys=True),
            rationale=rationale,
            supersedes_id=str(current[0]) if current is not None else None,
            created_at=created_at,
        )

    legacy = _current_route_judgment(connection, LEGACY_ROUTE_CHECK_JUDGMENT_TASK, attempt_id)
    if legacy is not None:
        append(
            LEGACY_ROUTE_CHECK_JUDGMENT_TASK, NOT_CHECKED_VERDICT,
            "route check: not checked; the grade this verdict described was replaced", legacy,
        )
    current = _current_route_judgment(connection, ROUTE_RULE_JUDGMENT_TASK, attempt_id)
    rule = grading_support.get(ROUTE_RULE_SUPPORT_KEY) or {}
    if not (
        isinstance(rule, Mapping)
        and rule.get("version") == ROUTE_RULE_RECORD_VERSION
        and rule.get("status") == "checked"
    ):
        if current is None:
            return None
        return append(
            ROUTE_RULE_JUDGMENT_TASK, NOT_CHECKED_VERDICT,
            "own route: not checked; the rule did not run over the grade that replaced this verdict's",
            current,
        )
    route = grading_support.get("route_check") or {}
    verdict = {
        **dict(rule),
        "grader_unverified_criterion_ids": list(grading_support.get("grader_unverified_criterion_ids") or []),
        "concrete_error_located": bool(route.get("concrete_error_located")) if isinstance(route, Mapping) else False,
    }
    if not rule.get("divergent_route"):
        rationale = "own route: the grader read the route as the reference's; the rule did not apply"
    elif not rule.get("applied"):
        rationale = "own route: divergent; no mark-down left unassessed"
    else:
        parts = []
        if rule.get("unlocated_criterion_ids"):
            parts.append("unlocated " + ", ".join(rule["unlocated_criterion_ids"]))
        if rule.get("declared_unverified_criterion_ids"):
            parts.append("declared unverifiable " + ", ".join(rule["declared_unverified_criterion_ids"]))
        rationale = "own route: divergent; " + "; ".join(parts)
        if rule.get("held_for_review"):
            rationale += "; held for review"
    return append(ROUTE_RULE_JUDGMENT_TASK, verdict, rationale, current)


def revalidated_support(
    grading_support: Mapping[str, Any], record: Mapping[str, Any], rubric: Rubric,
) -> dict[str, Any]:
    """``assessed_shortfall`` recomputed over the VALIDATED grade
    (held-grade-evidence F1).

    The rule runs on the raw proposal; validation then drops what it cannot
    keep (an unknown or blank criterion id, an attribution it rejects). When
    the route rule applied, the support's ``assessed_shortfall`` (what queues
    a diagnosis, what placement and the field read) is recomputed from the
    persisted record exactly as the rule computes it: a criterion still below
    full points that is not unverified, an attribution still in force (not
    the grader's interpretation), or a fatal error. Unchanged otherwise.
    """

    support = dict(grading_support)
    rule = support.get(ROUTE_RULE_SUPPORT_KEY) or {}
    if not (isinstance(rule, Mapping) and rule.get("status") == "checked" and rule.get("applied")):
        return support
    unverified = {str(value) for value in support.get("unverified_criterion_ids") or ()}
    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    points = {
        str(row.get("criterion_id")): float(row.get("points_awarded") or 0.0)
        for row in record.get("criteria") or ()
    }
    # An omitted criterion is worth what validation scored it, 0 (review F1).
    still_below = {cid for cid, maximum in maxima.items() if points.get(cid, 0.0) + 1e-9 < maximum}
    in_force = any(
        str(attribution.get("validity_scope") or "valid_measurement") != "grader_interpretation"
        for attribution in record.get("error_attributions") or ()
    )
    shortfall = bool(still_below - unverified) or in_force or bool(record.get("fatal_errors"))
    if support.get("assessed_shortfall") != shortfall:
        support["assessed_shortfall"] = shortfall
        support[ROUTE_RULE_SUPPORT_KEY] = {**rule, "assessed_shortfall": shortfall}
    return support


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
    #: ``mvp-0.13``: the winning sample's reading of a stuck answer (None for
    #: an ordinary answer). The caller verifies and records it.
    stuck_reading: StuckReading | None = None


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
    if own is not None:
        return own
    # mvp-0.20: a grade the own-route rule held for review (nothing assessed,
    # nothing validated) is a real review; an unverified criterion alone is
    # PF-c's non-blocking log.
    rule = run.grading_support.get(ROUTE_RULE_SUPPORT_KEY) or {}
    if rule.get("applied") and rule.get("held_for_review"):
        return HELD_REVIEW_REASON
    return UNVERIFIED_REVIEW_REASON


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
    result_model = blind_result_model(context)
    raw: list[BlindGradingProposal] = []
    declared: list[list[str]] = []
    extras: list[dict[str, Any]] = []
    readings: list[StuckReading | None] = []
    for _ in range(sample_count):
        # Each sample is one logical call: admitted against a command's caps
        # when one installed a guard (review F5); a no-op otherwise.
        with admit_grading_call("blind_grading", prompt):
            result = execute_structured_operation(
                client,
                purpose="blind_grading",
                prompt=prompt,
                result_model=result_model,
                isolated=True,
            )
        readings.append(getattr(result, "stuck_reading", None))
        if policy is not None:
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
                result.as_blind_proposal()
                if isinstance(result, StuckBlindGradingProposal)
                else result
            )
            declared.append([])
            extras.append({})
    winner, sampling = modal_sample(raw, rubric) if len(raw) > 1 else (0, {"sample_count": 1})
    ungated = proposal = raw[winner]
    support: dict[str, Any] = {"version": GRADING_SUPPORT_VERSION, "sampling": sampling}
    if policy is not None:
        divergent = bool((extras[winner].get("route_check") or {}).get("divergent_route"))
        # The method-explicit successor: on a divergent route the item's
        # required-method criteria are graded on use of the method, so neither
        # gate unassesses an unlocated mark-down of one.
        method_ids = policy_method_criteria(policy) if policy.get("route_rules") else ()
        route_method_ids = method_ids if divergent else ()
        gate = apply_valid_alternative_gate(
            proposal,
            rubric=rubric,
            learner_answer_md=context.learner_answer_md,
            policy=policy,
            declared_unverified=declared[winner],
            method_criterion_ids=route_method_ids,
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
        if policy.get("route_rules"):
            # mvp-0.20: the own-route rule over the grader's own output.
            final_status = (policy.get("final_answer_check") or {}).get("status")
            rule = apply_route_rule(
                proposal,
                rubric=rubric,
                learner_answer_md=context.learner_answer_md,
                final_answer_status=final_status,
                divergent_route=divergent,
                unverified_before=gate.unverified_criterion_ids,
                # Review F2: the grader's own "cannot verify" reaches the rule.
                declared_unverified=declared[winner],
                # Review F3: the learner's clarification reply is the
                # learner's words too; the machine's question is not.
                clarification_answer_md=(context.clarification_exchange or {}).get("answer_md"),
                method_criterion_ids=method_ids,
            )
            support[ROUTE_RULE_SUPPORT_KEY] = {
                "version": ROUTE_RULE_RECORD_VERSION,
                "rules": policy["route_rules"],
                "status": "checked",
                "applied": rule.applied,
                "final_answer_status": final_status,
                "divergent_route": divergent,
                "unlocated_criterion_ids": list(rule.unlocated),
                "declared_unverified_criterion_ids": list(rule.declared),
                "clarification_located_criterion_ids": list(rule.clarification_located),
                "unverified_criterion_ids": list(rule.unverified),
                "held_for_review": rule.held_for_review,
                "assessed_shortfall": rule.assessed_shortfall if rule.applied else None,
            }
            if isinstance(policy.get("required_method"), Mapping):
                # The method-explicit successor's record: the item's required
                # method, and its criteria marked down on the divergent route
                # that stayed assessed with no located quote.
                support[ROUTE_RULE_SUPPORT_KEY].update(
                    required_method=dict(policy["required_method"]),
                    method_route_criterion_ids=list(rule.method_route),
                )
            if rule.applied:
                proposal = rule.proposal
                # PF-c's keys over both rules, so every reader of
                # ``unverified_criterion_ids``, ``valid_alternative_gate_applied``
                # and ``assessed_shortfall`` treats this outcome as PF-c's.
                support.update(
                    unverified_criterion_ids=list(rule.unverified),
                    valid_alternative_gate_applied=True,
                    valid_alternative_gate={"final_answer": gate.applied, "proof_route": True},
                    assessed_shortfall=rule.assessed_shortfall,
                )
                support[UNVERIFIED_INTERPRETATION_KEY] = UNASSESSED_INTERPRETATION
    return BlindGradingRun(
        proposal=proposal,
        prompt_version=blind_prompt_version(context),
        grading_support=support,
        samples=len(raw),
        ungated_proposal=ungated,
        stuck_reading=readings[winner],
    )


__all__ = [
    "BlindGradingRun",
    "GRADING_SUPPORT_VERSION",
    "GateOutcome",
    "HELD_REVIEW_REASON",
    "ITEM_REQUIRED_METHOD",
    "LEGACY_ROUTE_CHECK_JUDGMENT_TASK",
    "METHOD_ROUTE_RULES_SUFFIX",
    "METHOD_ROUTE_RULES_VERSION",
    "NOT_CHECKED_VERDICT",
    "REFERENCE_POLICY_CALIBRATION_PROMPT_VERSION",
    "REFERENCE_POLICY_PROMPT_VERSION",
    "REFERENCE_POLICY_RULES",
    "REQUIRED_METHOD_RULES",
    "ROUTE_RULES",
    "ROUTE_RULES_TEXT",
    "ROUTE_RULES_V2",
    "ROUTE_RULES_SUFFIX",
    "ROUTE_RULES_VERSION",
    "ROUTE_RULE_JUDGMENT_TASK",
    "ROUTE_RULE_RECORD_VERSION",
    "ROUTE_RULE_SUPPORT_KEY",
    "ReferencePolicyBlindGradingProposal",
    "RouteCheck",
    "RouteRuleOutcome",
    "StuckReferencePolicyBlindGradingProposal",
    "UNASSESSED_CRITERION_LABEL",
    "UNVERIFIED_REVIEW_REASON",
    "apply_route_rule",
    "apply_valid_alternative_gate",
    "blind_result_model",
    "criterion_outcomes",
    "family_key",
    "gated_review_reason",
    "grade_uncertainty_signal",
    "method_rules_active",
    "modal_sample",
    "policy_method_criteria",
    "record_route_rule_judgment",
    "reference_policy",
    "request_blind_grading_run",
    "required_method_policy",
    "revalidated_support",
    "route_rules_active",
    "route_rules_suffix",
    "route_rules_text",
    "route_rules_version",
    "sample_fingerprint",
]
