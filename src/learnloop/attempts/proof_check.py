"""The valid-alternative gate for proofs and explanations (successor ``mvp-0.17``).

PF-c's gate (:mod:`learnloop.attempts.grading_support`) protects a learner's
different route only when a deterministic check verifies the final answer.
"Prove", "show that", "justify", "derive" and "explain why" items have no such
check, and LLM judges wrongly reject 13-91% of valid alternative proof steps
and wrongly accept 7-71% of wrong ones; the error is mostly a property of the
model, and showing the reference did not help (arXiv 2605.16207). This module
adds the smallest sound path for those items (owner decision 2026-10-13):

* **Which items.** An LLM reads the item's prompt, rubric and metadata (never
  a keyword list) and says what it asks for and whether its rubric credits
  the validity of the learner's own reasoning. ``proof_like`` follows that
  judgment (proofs, derivations, justifications, explanations, and
  computations whose rubric credits the working); recall and labelling items
  are never checked. The reading is cached per item
  content in ``judgment_ledger`` (task :data:`ITEM_KIND_TASK`), so each item
  version is classified once.
* **An independent re-derivation.** On a proof-like item every blind grade is
  followed by one isolated call on a route that is NOT the grader's model
  where one is configured (:func:`proof_check_route`). It sees the item, the
  rubric and the answer, never the grader's verdict or the reference, and
  checks each criterion on the learner's own terms: ``established``,
  ``not_established`` (quoting the first failing step verbatim) or
  ``cannot_tell``. Its agreement or disagreement with the grader goes to
  ``judgment_ledger`` (task :data:`ROUTE_CHECK_TASK`).
* **The gate** (:func:`apply_proof_route_gate`, deterministic, server side),
  per criterion, following PF-c's outcome types and its rule that a criterion
  may be marked down only where a concrete error is located in the learner's
  words:

  - grader below full points, checker ``established``, the grader located no
    step in the answer -> **restored** (full points, assessed);
  - grader below full points, checker ``established``, the grader quoted a
    concrete step -> **disputed**: unverified, which PF-c's rule makes
    unassessed (no credit, no failure), and provisional: a clarification
    question goes to the learner only when the checker says the dispute turns
    on what the learner meant (principle 8: a disagreement between two models
    about a written step is machine-resident and never costs the learner);
  - grader at full points, checker ``not_established`` with the failing step
    quoted verbatim -> **flagged**: the grade stands, never silently: a review
    reason and a note on the criterion;
  - grader below full points on a route the grader itself reads as divergent
    from the reference, no error located verbatim by either judge (the check
    abstains, or refutes without a quote) -> **unlocated**: unverified, so
    unassessed (P1's rule: marked down only on a located, quoted error;
    review F1). When nothing is then left assessed and nothing validated the
    answer, the grade is also **held for review** (re-review F9): it is the
    grader's own grade, provisional, never the full marks PF-c gives a
    verified answer; the attempt writes no evidence, applies no FSRS review
    (the item's memory and due date stay as they were), is no prediction
    error and inserts no follow-up, until a regrade or an adjudication
    assesses a criterion. The blind record carries the hold, so replay and
    the regrade reproduce it;
  - everything else (agreement, a located error, ``cannot_tell`` off a
    divergent route) leaves the grade as the grader gave it, recorded.

  Once the gate overrides a mark-down (restores or unassesses it), an
  attribution that names no criterion and locates no step in the learner's
  words is the grader's interpretation, as PF-c rescopes it: it never keeps
  the attempt a measured failure on its own (re-review F1).

  The deterministic final-answer check outranks the checker: a conclusion
  that ``differs_from_reference`` is never restored, disputed or left
  unassessed (P1 excludes it; review F2). A grade with fatal errors is never
  restored and keeps its mark-downs; a checker that disputes it is a flag.

Kill switch: ``proof_check.enabled = false`` grades exactly as ``mvp-0.16``
for new answers. The algorithm version gates it; replay never reads either
(the blind record, the evidence rows and the ledger are what an attempt was).
Any failure to classify or check leaves the grader's grade in force and is
recorded on the blind record (``status = unavailable``): a bonus check never
fails a grade.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
import logging
import re
from typing import Any, Callable, Literal, Mapping, Sequence

from pydantic import Field

from learnloop.ai.errors import AIInterrupted
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendLimitExceeded
from learnloop.ai.transport import OperationClient, execute_structured_operation, render_structured_prompt
from learnloop.algorithm_versions import PROOF_ROUTE_CHECK_VERSIONS
from learnloop.attempts.grading_admission import admit_grading_call, estimated_prompt_tokens
from learnloop.substrate.canonical_projection import (
    UNASSESSED_INTERPRETATION,
    UNVERIFIED_INTERPRETATION_KEY,
)
from learnloop.vault.models import LoadedVault, PracticeItem, Rubric

LOGGER = logging.getLogger(__name__)

#: v2 (review F1/F2): P1's located-error rule on a divergent route, and the
#: final-answer check outranks the checker. v3 (re-review F1/F9): an unlocated
#: attribution naming no criterion is the grader's interpretation once the gate
#: overrides a mark-down, and a grade held for review keeps the grader's own
#: score (not the verified-answer full marks) and applies no FSRS review.
PROOF_CHECK_VERSION = "proof-route-check-v3"
#: Gate versions whose records predate the hold (re-review F9).
_PRE_HOLD_VERSIONS = frozenset({"proof-route-check-v1", "proof-route-check-v2"})
ITEM_KIND_PROMPT_VERSION = "proof-like-item-v1"
ROUTE_CHECK_PROMPT_VERSION = "proof-route-check-v1"
#: ``judgment_ledger.task`` of the item classification (left = the item, the
#: input hash its content) and of one attempt's route check (left = the attempt).
ITEM_KIND_TASK = "proof_like_item"
ROUTE_CHECK_TASK = "proof_route_check"
#: The attempt's review reason when the check flags a step the grader accepted
#: (or disputes a grade carrying fatal errors). A real review concern: the
#: grade is in doubt, so it is not a non-blocking log like PF-c's.
PROOF_ROUTE_REVIEW_REASON = "proof_route_check_flag"
#: ``grading_clarifications.trigger`` of a question licensed by a dispute that
#: turns on the learner's meaning (migration 185).
CLARIFICATION_TRIGGER = "route_check_disagreement"
#: How a restored criterion is shown (beside PF-c's "not assessed" label).
RESTORED_CRITERION_LABEL = "restored: an independent check found your route valid"
#: Support key on the blind record.
SUPPORT_KEY = "proof_route_check"
#: The typed suppression the post-attempt pipeline records when a grade held
#: for review would otherwise insert follow-up work (re-review F9).
HELD_FOR_REVIEW_SUPPRESSION = "grade_held_for_review"
#: The spend route a command admits the reading and the check on (review F3):
#: the checker's own client, which may bill differently from the grader's.
SPEND_ROUTE = "proof_check"
#: Kinds whose credit can never rest on the learner's reasoning; any other kind
#: whose rubric credits the reasoning is checked (a computation whose rubric
#: credits the working included: its final-answer check rarely verifies a
#: different route).
NEVER_CHECKED_KINDS = frozenset({"recall", "classification"})
#: Clarification reasons that are learner-resident (A8): what the learner
#: meant, not whether a written step is valid.
_LEARNER_RESIDENT_REASONS = frozenset({"ambiguous_notation", "skipped_step", "method_ambiguity"})


def proof_check_active(vault: Any) -> bool:
    """Does this vault run the route check on NEW blind grades?

    The algorithm version gates it; ``proof_check.enabled`` is its kill
    switch. Read only when an answer is graded or regraded.
    """

    config = vault.config
    if config.algorithms.algorithm_version not in PROOF_ROUTE_CHECK_VERSIONS:
        return False
    section = getattr(config, "proof_check", None)
    return bool(getattr(section, "enabled", True))


# -- wire models -------------------------------------------------------------------------


class ItemKindReading(WireModel):
    """What one item asks for, read from its prompt, rubric and metadata."""

    response_kind: Literal[
        "proof", "derivation", "justification", "explanation",
        "computation", "recall", "classification", "other",
    ]
    reasoning_is_graded: bool = Field(
        description=(
            "True when the rubric credits the validity of the learner's own reasoning "
            "steps, not only a final result."
        ),
    )
    rationale: str = ""

    @property
    def proof_like(self) -> bool:
        return self.reasoning_is_graded and self.response_kind not in NEVER_CHECKED_KINDS


class CriterionRouteVerdict(WireModel):
    criterion_id: str
    verdict: Literal["established", "not_established", "cannot_tell"]
    invalid_step_quote: str | None = Field(
        default=None,
        description=(
            "not_established: the learner's text of the first step that fails, copied "
            "verbatim. For a missing step, the sentence whose conclusion relies on it."
        ),
    )
    error_kind: Literal["invalid_step", "unjustified_step", "missing_step", "false_claim"] | None = None
    reason_md: str = ""


class ProofRouteCheck(WireModel):
    """One independent re-derivation of the learner's own route."""

    route_md: str = Field(description="The learner's route, restated step by step in their order.")
    step_checks_md: str = Field(description="Each step checked on its own terms: valid, invalid or unjustified, and why.")
    criteria: list[CriterionRouteVerdict] = Field(default_factory=list)
    clarification_question_md: str | None = None
    clarification_reason: Literal[
        "ambiguous_notation", "skipped_step", "method_ambiguity", "not_learner_resident"
    ] = "not_learner_resident"


ITEM_KIND_RULES = (
    "Decide what this practice item asks the learner to produce, from its prompt, rubric "
    "criteria and metadata (the learner's answer is not shown). response_kind: proof (prove "
    "or show that a statement holds), derivation (derive a formula or result step by step), "
    "justification (justify or argue that a claim or choice is right), explanation (explain "
    "why or how something holds), computation (calculate a value; working may be shown but "
    "the result is what is assessed), recall (state a definition, fact or formula), "
    "classification (pick or label), other. reasoning_is_graded: true when the rubric gives "
    "credit for the validity of the learner's own reasoning steps (an argument, derivation "
    "or explanation), false when it grades only results, recall or labels. Judge what the "
    "rubric rewards, not the words the prompt happens to use."
)

ROUTE_CHECK_RULES = (
    "You are an independent checker of ONE learner's answer to a proof, derivation, "
    "justification or explanation item. No reference solution is given on purpose: check "
    "the learner's OWN route. First restate the route step by step (route_md), then check "
    "each step on its own terms (step_checks_md). For EVERY rubric criterion return one "
    "verdict. established: the learner's steps, each valid on its own terms, establish what "
    "the criterion is for. A criterion phrased in terms of one method is established by any "
    "valid method that establishes the same fact; an unusual, terse or differently ordered "
    "route is not an error when each step is valid and its justification is standard. "
    "not_established: a step the criterion depends on is invalid, unjustified, missing, or "
    "a stated claim is false; copy into invalid_step_quote the learner's text of the FIRST "
    "such step VERBATIM (for a missing step, the sentence whose conclusion relies on it). "
    "Never accept a step because its conclusion happens to be true. cannot_tell: you cannot "
    "decide from the answer. Ask clarification_question_md only when one short question to "
    "the learner would settle a disputed or undecidable step that turns on what THEY meant "
    "(ambiguous notation, a step they may have skipped as obvious, which method they "
    "intended), and set clarification_reason accordingly; never ask about whether a written "
    "step is valid (that is your job), and never reveal or hint at the answer."
)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _rubric_payload(rubric: Rubric) -> list[dict[str, Any]]:
    return [
        {"id": criterion.id, "description": criterion.description, "points": criterion.points}
        for criterion in rubric.criteria
    ]


def item_kind_payload(item: PracticeItem, rubric: Rubric) -> dict[str, Any]:
    """What the classifier reads: item-side only, no answer, no reference."""

    return {
        "prompt": item.prompt,
        "rubric_criteria": _rubric_payload(rubric),
        "metadata": {
            "practice_mode": item.practice_mode,
            "capability": item.capability,
            "has_trace_contract": item.trace_contract is not None,
            "attempt_types_allowed": list(item.attempt_types_allowed),
        },
    }


def item_kind_input_hash(item: PracticeItem, rubric: Rubric) -> str:
    return _digest({"version": ITEM_KIND_PROMPT_VERSION, "item": item_kind_payload(item, rubric)})


def item_kind_prompt(item: PracticeItem, rubric: Rubric) -> str:
    return render_structured_prompt(
        "learnloop practice item kind",
        ITEM_KIND_PROMPT_VERSION,
        {"task": ITEM_KIND_RULES, "context": item_kind_payload(item, rubric)},
    )


def route_check_payload(
    item: PracticeItem,
    rubric: Rubric,
    learner_answer_md: str,
    *,
    clarification_exchange: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": item.prompt,
        "rubric_criteria": _rubric_payload(rubric),
        "learner_answer_md": learner_answer_md,
    }
    if clarification_exchange:
        payload["clarification_exchange"] = dict(clarification_exchange)
    return payload


def route_check_prompt(
    item: PracticeItem,
    rubric: Rubric,
    learner_answer_md: str,
    *,
    clarification_exchange: Mapping[str, str] | None = None,
) -> str:
    return render_structured_prompt(
        "learnloop proof route check",
        ROUTE_CHECK_PROMPT_VERSION,
        {
            "task": ROUTE_CHECK_RULES,
            "context": route_check_payload(
                item, rubric, learner_answer_md, clarification_exchange=clarification_exchange,
            ),
        },
        context_tail_fields=("learner_answer_md",),
    )


# -- the deterministic gate ------------------------------------------------------------

_WS = re.compile(r"\s+")


def _squash(text: str | None) -> str:
    return _WS.sub(" ", text or "").strip().casefold()


def _in_answer(quote: str | None, answer: str) -> bool:
    squashed = _squash(quote)
    return bool(squashed) and squashed in _squash(answer)


def _criteria_of(attribution: Any) -> set[str]:
    criteria = {str(value) for value in (attribution.target_criterion_ids or [])}
    ref = attribution.target_ref
    if ref is not None and getattr(ref, "kind", None) == "criterion":
        criteria.add(str(getattr(ref, "criterion_id", "")))
    divergence = attribution.first_divergence
    if divergence is not None and getattr(divergence, "criterion_id", None):
        criteria.add(str(divergence.criterion_id))
    return criteria


def _grader_located(attribution: Any, answer: str) -> bool:
    """A concrete error in the learner's words, still in force (PF-c's rule)."""

    if attribution.validity_scope == "grader_interpretation":
        return False
    divergence = attribution.first_divergence
    return _in_answer(getattr(divergence, "quote", None) if divergence is not None else None, answer)


#: ``final_answer_check`` statuses (``attempts.answer_check``). A conclusion
#: that demonstrably differs from the reference is never restored or left
#: unassessed by this gate (P1 excludes it; review F2).
DIFFERS_FROM_REFERENCE = "differs_from_reference"
MATCHES_REFERENCE = "matches_reference"


@dataclass(frozen=True)
class ProofGateOutcome:
    proposal: Any
    outcomes: dict[str, str]
    restored: tuple[str, ...] = ()
    #: Every unverified criterion after both gates (PF-c's that stayed, plus
    #: ``disputed`` and ``unlocated``, the ones this gate added).
    unverified: tuple[str, ...] = ()
    disputed: tuple[str, ...] = ()
    #: P1 (review F1): marked down on a divergent route with no error located
    #: in the learner's words by either judge, and not validated either.
    unlocated: tuple[str, ...] = ()
    flagged: tuple[str, ...] = ()
    disputed_fatal: bool = False
    #: Nothing is left assessed and nothing validated the answer (no verified
    #: final answer, no criterion the check established): the grade is held
    #: for review instead of resting on nothing.
    held_for_review: bool = False
    clarification: dict[str, Any] | None = None
    assessed_shortfall: bool = True
    withdrawn_attributions: tuple[dict[str, Any], ...] = ()
    #: Per-criterion agreement between the grader (full points or not) and the
    #: check's verdict: ``agree`` | ``disagree`` | ``cannot_tell``.
    agreement: dict[str, str] = field(default_factory=dict)

    @property
    def applied(self) -> bool:
        """Did this gate change anything (PF-c's own outcome alone is not this gate's)."""
        return bool(
            self.restored or self.disputed or self.unlocated or self.flagged or self.disputed_fatal
            or self.clarification
        )


def apply_proof_route_gate(
    proposal: Any,
    *,
    rubric: Rubric,
    learner_answer_md: str,
    check: ProofRouteCheck,
    unverified_before: Sequence[str] = (),
    grader_review_recommended: bool = False,
    checker_model: str | None = None,
    clarification_allowed: bool = True,
    final_answer_status: str | None = None,
    divergent_route: bool = False,
) -> ProofGateOutcome:
    """Combine the blind grade with the independent check (see the module doc).

    ``proposal`` is the blind proposal after PF-c's gate; ``unverified_before``
    the criteria PF-c already recorded unverified. ``grader_review_recommended``
    is the grader's OWN review flag (before PF-c forced one), so a gate that
    resolves everything leaves no forced review behind.

    ``final_answer_status`` is the deterministic ``final_answer_check`` status
    of this answer: when the conclusion ``differs_from_reference`` nothing is
    restored, disputed or left unassessed (review F2); a flag still stands.
    ``divergent_route`` is the grader's own ``route_check.divergent_route``:
    on a divergent route whose conclusion is not shown to differ (P1), a
    criterion stays marked down only where an error is located verbatim in the
    learner's words, by the grader's attribution or the check's quote;
    otherwise it is ``unlocated``, which is unverified (unassessed), whether
    the check abstained or refuted it without a quote (review F1). A grade with
    fatal errors keeps its mark-downs (the fatal error is the grader's whole-
    answer finding).
    """

    maxima = {criterion.id: float(criterion.points) for criterion in rubric.criteria}
    awarded = {row.criterion_id: float(row.points_awarded) for row in proposal.criterion_evidence}
    below = {cid for cid, maximum in maxima.items() if awarded.get(cid, maximum) + 1e-9 < maximum}
    located: set[str] = set()
    for attribution in proposal.error_attributions:
        if _grader_located(attribution, learner_answer_md):
            located.update(_criteria_of(attribution))
    verdicts = {row.criterion_id: row for row in check.criteria if row.criterion_id in maxima}
    previously_unverified = {str(value) for value in unverified_before}
    fatal = bool(proposal.fatal_errors)
    answer_differs = final_answer_status == DIFFERS_FROM_REFERENCE
    # P1's trigger: a divergent route whose conclusion is not shown to differ.
    p1_eligible = bool(divergent_route) and not answer_differs and not fatal

    outcomes: dict[str, str] = {}
    agreement: dict[str, str] = {}
    restored: list[str] = []
    disputed: list[str] = []
    unlocated: list[str] = []
    flagged: list[str] = []
    disputed_fatal = False
    for cid in maxima:
        row = verdicts.get(cid)
        verdict = row.verdict if row is not None else "cannot_tell"
        quoted = row is not None and _in_answer(row.invalid_step_quote, learner_answer_md)
        if verdict == "cannot_tell":
            agreement[cid] = "cannot_tell"
        elif (cid in below) == (verdict == "not_established"):
            agreement[cid] = "agree"
        else:
            agreement[cid] = "disagree"
        if cid in below:
            if verdict == "established":
                if answer_differs:
                    # The machine check outranks the checker's validation.
                    outcomes[cid] = "answer_differs"
                elif fatal:
                    outcomes[cid] = "disputed_fatal"
                    disputed_fatal = True
                elif cid in located:
                    outcomes[cid] = "disputed"
                    disputed.append(cid)
                else:
                    outcomes[cid] = "restored"
                    restored.append(cid)
            elif cid in located or (verdict == "not_established" and quoted):
                outcomes[cid] = "agree_shortfall" if verdict == "not_established" else "cannot_tell"
            elif p1_eligible and cid not in previously_unverified:
                outcomes[cid] = "unlocated"
                unlocated.append(cid)
            else:
                outcomes[cid] = "agree_shortfall" if verdict == "not_established" else "cannot_tell"
        else:
            if verdict == "not_established" and quoted:
                outcomes[cid] = "flagged"
                flagged.append(cid)
            elif verdict == "not_established":
                outcomes[cid] = "questioned_unlocated"
            elif verdict == "established":
                outcomes[cid] = "agree_full"
            else:
                outcomes[cid] = "cannot_tell"

    restored_set = set(restored)
    unverified = (previously_unverified - restored_set) | set(disputed) | set(unlocated)
    # PF-c's "nothing assessed schedules as correct" rests on a verified final
    # answer; a dispute rests on the check's affirmative validation. With
    # neither, an all-unlocated grade is held for review, never silent.
    held_for_review = bool(
        unlocated and not (set(maxima) - unverified) and not disputed
        and final_answer_status != MATCHES_REFERENCE
    )
    # Rows: a restored criterion gets full points; flagged, disputed and
    # unlocated criteria carry a note naming what the check found.
    evidence = []
    for row in proposal.criterion_evidence:
        cid = row.criterion_id
        verdict = verdicts.get(cid)
        reason = (verdict.reason_md or "").strip() if verdict is not None else ""
        model = checker_model or "an independent model"
        if cid in restored_set:
            row = row.model_copy(update={
                "points_awarded": maxima[cid],
                "evidence": (
                    f"{RESTORED_CRITERION_LABEL[0].upper()}{RESTORED_CRITERION_LABEL[1:]} ({model}): "
                    f"{reason or 'each step it depends on is valid on its own terms.'}"
                ),
                "notes": f"Grader's mark-down, which named no step in the answer: {row.evidence}",
            })
        elif cid in flagged:
            quote = (verdict.invalid_step_quote or "").strip() if verdict is not None else ""
            row = row.model_copy(update={
                "notes": (
                    f"An independent check ({model}) questioned this step: “{quote}”. "
                    f"{reason}".strip() + " The grade stands until it is reviewed."
                ),
            })
        elif cid in disputed:
            row = row.model_copy(update={
                "notes": (
                    f"An independent check ({model}) found this step valid: {reason}".strip()
                    + " Not assessed while the two checks disagree."
                ),
            })
        elif cid in unlocated:
            row = row.model_copy(update={
                "notes": (
                    f"Not assessed: neither the grader nor an independent check ({model}) located "
                    "an error in your own route here."
                    + (" Held for review." if held_for_review else "")
                ),
            })
        evidence.append(row)

    # Attributions on a restored criterion are refuted by the restore: they
    # leave the grade (kept on the record); on an unverified one they are the
    # grader's interpretation, as PF-c rescopes them. Once the gate has
    # overridden a mark-down (restored or unassessed it), an attribution that
    # names no criterion and locates no step in the learner's words is the
    # grader's interpretation too: P1 marks down only on a located error, so
    # an unlocated whole-answer claim never keeps the grade a measured failure
    # on its own (PF-c's rule for untargeted attributions; re-review F1).
    overridden = bool(unverified or restored_set)
    attributions = []
    withdrawn: list[dict[str, Any]] = []
    attribution_in_force = False
    for attribution in proposal.error_attributions:
        criteria = _criteria_of(attribution)
        if criteria and criteria <= restored_set:
            withdrawn.append(attribution.model_dump(mode="json"))
            continue
        rescoped = (
            (criteria and criteria & unverified and not criteria - unverified - restored_set)
            or (not criteria and overridden and not _grader_located(attribution, learner_answer_md))
        )
        if rescoped:
            if attribution.validity_scope != "grader_interpretation":
                attribution = attribution.model_copy(update={"validity_scope": "grader_interpretation"})
        elif attribution.validity_scope != "grader_interpretation":
            attribution_in_force = True
        attributions.append(attribution)

    score_points = {row.criterion_id: float(row.points_awarded) for row in evidence}
    still_below = {
        cid for cid, maximum in maxima.items() if score_points.get(cid, maximum) + 1e-9 < maximum
    }
    assessed_shortfall = bool(still_below - unverified) or attribution_in_force or fatal

    clarification = None
    if (
        clarification_allowed
        and disputed
        and (check.clarification_question_md or "").strip()
        and check.clarification_reason in _LEARNER_RESIDENT_REASONS
    ):
        clarification = {
            "question_md": check.clarification_question_md.strip(),
            "reason": check.clarification_reason,
            "criterion_id": disputed[0],
            "trigger": CLARIFICATION_TRIGGER,
        }
    review = bool(
        grader_review_recommended or unverified or flagged or disputed_fatal or clarification
        or held_for_review
    )
    gated = proposal.model_copy(update={
        "criterion_evidence": evidence,
        "error_attributions": attributions,
        "rubric_score": int(round(sum(score_points.values()))) if restored else proposal.rubric_score,
        "manual_review_recommended": review,
    })
    return ProofGateOutcome(
        proposal=gated,
        outcomes=outcomes,
        restored=tuple(restored),
        unverified=tuple(sorted(unverified)),
        disputed=tuple(disputed),
        unlocated=tuple(unlocated),
        flagged=tuple(flagged),
        disputed_fatal=disputed_fatal,
        held_for_review=held_for_review,
        clarification=clarification,
        assessed_shortfall=assessed_shortfall,
        withdrawn_attributions=tuple(withdrawn),
        agreement=agreement,
    )


# -- routes ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class CheckerRoute:
    provider: str | None
    model: str | None
    independent: bool
    reason: str


def _profile_model(vault: LoadedVault, provider: str) -> str | None:
    profile = vault.config.ai.providers.get(provider)
    return getattr(profile, "model", None) if profile is not None else None


def proof_check_route(vault: LoadedVault, *, grader_model: str | None) -> CheckerRoute:
    """The route the check runs on: NOT the grader's model where possible.

    ``ai.routing.proof_check`` when set (the owner's choice, independent or
    not). Otherwise the first route the vault already sends learner text to
    (diagnosis, same-cause judge, diagnosis judge, tutor, the active and
    fallback providers) whose configured model differs from the grader's; if
    none differs, the grading route itself, recorded as not independent.
    Learner text never goes to a provider the vault does not already use.
    """

    from learnloop.ai.routing import is_generation_profile, provider_for_task

    config = vault.config
    explicit = (getattr(config.ai.routing, "proof_check", None) or "").strip()
    if explicit:
        model = _profile_model(vault, explicit)
        return CheckerRoute(
            explicit, model, bool(model and grader_model and model != grader_model),
            "ai.routing.proof_check",
        )
    candidates: list[tuple[str, str]] = []
    for task in ("diagnosis", "same_cause_judge", "diagnosis_judge", "tutor_qa"):
        name = provider_for_task(config, task, allow_env=False).provider_name  # type: ignore[arg-type]
        candidates.append((name, f"ai.routing.{task}"))
    candidates.append((config.ai.active_provider, "ai.active_provider"))
    candidates.append(((config.ai.fallback_provider or "").strip(), "ai.fallback_provider"))
    for name, source in candidates:
        if not name or name not in config.ai.providers or not is_generation_profile(config, name):
            continue
        model = _profile_model(vault, name)
        if model and grader_model and model != grader_model:
            return CheckerRoute(name, model, True, source)
    grading = provider_for_task(config, "grading", allow_env=False).provider_name
    return CheckerRoute(
        grading or None, _profile_model(vault, grading) if grading else None, False,
        "no configured route with a different model: the grading route",
    )


def resolve_check_client(vault: LoadedVault, route: CheckerRoute) -> Any | None:
    """A ready client for the route, or None (tests replace this)."""

    from learnloop.ai.routing import ready_client_for_task

    if not route.provider:
        return None
    resolved = ready_client_for_task(vault.root, vault.config, "proof_check", explicit=route.provider)
    return resolved.client if resolved.ready else None


# -- one check ---------------------------------------------------------------------------------


@dataclass
class ProofCheckResult:
    support: dict[str, Any]
    gate: ProofGateOutcome | None = None
    #: The per-attempt verdict for ``judgment_ledger`` (written by the caller in
    #: the grading transaction), or None when nothing was checked.
    judgment: dict[str, Any] | None = None
    clarification: dict[str, Any] | None = None


def _current_judgment(connection: Any, *, task: str, left_kind: str, left_id: str,
                      input_hash: str | None = None) -> Any:
    sql = (
        "SELECT j.id, j.verdict, j.judge_model, j.input_hash FROM judgment_ledger j "
        "WHERE j.task = ? AND j.left_kind = ? AND j.left_id = ? AND j.right_kind IS NULL "
        "AND NOT EXISTS (SELECT 1 FROM judgment_ledger s WHERE s.supersedes_id = j.id)"
    )
    params: list[Any] = [task, left_kind, left_id]
    if input_hash is not None:
        sql += " AND j.input_hash = ?"
        params.append(input_hash)
    return connection.execute(sql + " ORDER BY j.created_at DESC, j.id DESC LIMIT 1", params).fetchone()


def _cached_reading(repository: Any, item: PracticeItem, rubric: Rubric) -> tuple[ItemKindReading, Any] | None:
    """The item's current reading for its present content, with its ledger row."""

    with repository.connection() as connection:
        cached = _current_judgment(
            connection, task=ITEM_KIND_TASK, left_kind="practice_item", left_id=item.id,
            input_hash=item_kind_input_hash(item, rubric),
        )
    if cached is None:
        return None
    try:
        stored = json.loads(cached[1])
        # The verdict also records the derived ``proof_like`` for readers.
        reading = ItemKindReading.model_validate(
            {key: value for key, value in stored.items() if key in ItemKindReading.model_fields}
        )
    except (ValueError, AttributeError):
        return None
    return reading, cached


def classify_item(
    repository: Any,
    item: PracticeItem,
    rubric: Rubric,
    client: OperationClient | None,
    *,
    created_at: str,
) -> tuple[ItemKindReading | None, dict[str, Any]]:
    """The item's cached kind, or one classification call recorded in the ledger."""

    from learnloop.db.stores.judgments import append_judgment

    input_hash = item_kind_input_hash(item, rubric)
    cached = _cached_reading(repository, item, rubric)
    if cached is not None:
        reading, row = cached
        return reading, {"cached": True, "judgment_id": str(row[0]), "model": row[2]}
    if client is None:
        return None, {"cached": False, "error": "no ready client for the item classification"}
    prompt = item_kind_prompt(item, rubric)
    # Admitted on the check's spend route when a command installed a guard
    # (review F3); a no-op on every other door.
    with admit_grading_call("proof_item_classification", prompt, route=SPEND_ROUTE, client=client):
        reading = execute_structured_operation(
            client, purpose="proof_item_classification", prompt=prompt,
            result_model=ItemKindReading, isolated=True,
        )
    model = getattr(client, "model", None) or "unknown"
    with repository.connection() as connection:
        previous = _current_judgment(connection, task=ITEM_KIND_TASK, left_kind="practice_item", left_id=item.id)
        judgment_id = append_judgment(
            connection, task=ITEM_KIND_TASK, left_kind="practice_item", left_id=item.id,
            judge="llm", judge_model=str(model), prompt_version=ITEM_KIND_PROMPT_VERSION,
            input_hash=input_hash,
            verdict=_canonical({**reading.model_dump(mode="json"), "proof_like": reading.proof_like}),
            rationale=reading.rationale or reading.response_kind,
            supersedes_id=str(previous[0]) if previous is not None else None,
            created_at=created_at,
        )
        connection.commit()
    return reading, {"cached": False, "judgment_id": judgment_id, "model": model}


def run_proof_route_check(
    vault: LoadedVault,
    repository: Any,
    *,
    item: PracticeItem,
    rubric: Rubric,
    learner_answer_md: str,
    proposal: Any,
    unverified_before: Sequence[str],
    grader_review_recommended: bool,
    grader_model: str | None,
    created_at: str,
    clarification_exchange: Mapping[str, str] | None = None,
    client_resolver: Callable[[LoadedVault, CheckerRoute], Any] | None = None,
    final_answer_status: str | None = None,
    divergent_route: bool = False,
) -> ProofCheckResult:
    """Classify the item (cached), check the route, apply the gate.

    Never raises for a model or provider failure: anything that stops the
    check leaves the grader's grade in force, with ``status = unavailable``
    and the error type recorded. A spend refusal or cancellation from the
    command's admission guard is not a model failure and propagates.
    """

    support: dict[str, Any] = {
        "version": PROOF_CHECK_VERSION, "status": "unavailable", "applied": False,
        # The gate's deterministic inputs (P1's trigger, review F1/F2).
        "final_answer_status": final_answer_status, "divergent_route": bool(divergent_route),
    }
    resolver = client_resolver or resolve_check_client
    try:
        route = proof_check_route(vault, grader_model=grader_model)
        support["checker"] = {
            "provider": route.provider, "model": route.model, "independent": route.independent,
            "route": route.reason, "grader_model": grader_model,
        }
        client = resolver(vault, route)
        if client is not None:
            resolved_model = getattr(client, "model", None)
            if resolved_model:
                support["checker"]["model"] = resolved_model
                support["checker"]["independent"] = bool(grader_model and resolved_model != grader_model)
        reading, provenance = classify_item(repository, item, rubric, client, created_at=created_at)
        if reading is None:
            support["error"] = provenance.get("error", "item kind unavailable")
            return ProofCheckResult(support)
        support["item_kind"] = {
            "response_kind": reading.response_kind,
            "reasoning_is_graded": reading.reasoning_is_graded,
            "proof_like": reading.proof_like,
            **provenance,
        }
        if not reading.proof_like:
            support["status"] = "not_proof_like"
            return ProofCheckResult(support)
        if client is None:
            support["error"] = "no ready client for the route check"
            return ProofCheckResult(support)
        prompt = route_check_prompt(
            item, rubric, learner_answer_md, clarification_exchange=clarification_exchange,
        )
        with admit_grading_call("proof_route_check", prompt, route=SPEND_ROUTE, client=client):
            check = execute_structured_operation(
                client, purpose="proof_route_check", prompt=prompt, result_model=ProofRouteCheck,
                isolated=True,
            )
        checker_model = support["checker"]["model"]
        gate = apply_proof_route_gate(
            proposal, rubric=rubric, learner_answer_md=learner_answer_md, check=check,
            unverified_before=unverified_before, grader_review_recommended=grader_review_recommended,
            checker_model=checker_model,
            # One question per attempt: an answered exchange is never re-asked.
            clarification_allowed=not clarification_exchange,
            final_answer_status=final_answer_status, divergent_route=divergent_route,
        )
    except (SpendLimitExceeded, AIInterrupted):
        # The command's caps refused the call, or the learner cancelled: the
        # whole grade stops, as a refused grading sample does (review F3).
        raise
    except Exception as exc:  # a bonus check never fails a grade
        LOGGER.warning("proof route check unavailable for item %s", item.id, exc_info=True)
        support["error"] = f"{type(exc).__name__}: {exc}"[:500]
        return ProofCheckResult(support)

    verdicts = {
        row.criterion_id: {
            "verdict": row.verdict,
            "error_kind": row.error_kind,
            "quote_located": _in_answer(row.invalid_step_quote, learner_answer_md),
        }
        for row in check.criteria if row.criterion_id in {c.id for c in rubric.criteria}
    }
    agreement = {
        key: sum(value == key for value in gate.agreement.values())
        for key in ("agree", "disagree", "cannot_tell")
    }
    support.update(
        status="checked",
        applied=gate.applied,
        prompt_version=ROUTE_CHECK_PROMPT_VERSION,
        verdicts=verdicts,
        outcomes=dict(gate.outcomes),
        agreement=agreement,
        restored_criterion_ids=list(gate.restored),
        disputed_criterion_ids=list(gate.disputed),
        unlocated_criterion_ids=list(gate.unlocated),
        unverified_criterion_ids=list(gate.unverified),
        flagged_criterion_ids=list(gate.flagged),
        disputed_fatal=gate.disputed_fatal,
        held_for_review=gate.held_for_review,
        clarification=gate.clarification,
        assessed_shortfall=gate.assessed_shortfall,
        withdrawn_attributions=list(gate.withdrawn_attributions),
        route_md=check.route_md,
        step_checks_md=check.step_checks_md,
    )
    judgment = {
        "verdict": _canonical({
            "outcomes": gate.outcomes, "verdicts": verdicts, "agreement": agreement,
            "checker": support["checker"],
        }),
        "judge_model": str(checker_model or "unknown"),
        "input_hash": _digest({"prompt": prompt}),
        "rationale": (
            f"route check: {agreement['agree']} agree, {agreement['disagree']} disagree, "
            f"{agreement['cannot_tell']} cannot tell"
        ),
        "score": (
            agreement["agree"] / (agreement["agree"] + agreement["disagree"])
            if agreement["agree"] + agreement["disagree"] else None
        ),
    }
    return ProofCheckResult(support, gate=gate, judgment=judgment, clarification=gate.clarification)


def record_route_check_judgment(connection: Any, *, attempt_id: str, judgment: Mapping[str, Any],
                                created_at: str) -> str:
    """Append the attempt's route-check verdict (a regrade supersedes it).

    Called inside the transaction that records the grade.
    """

    from learnloop.db.stores.judgments import append_judgment

    current = _current_judgment(connection, task=ROUTE_CHECK_TASK, left_kind="attempt", left_id=attempt_id)
    return append_judgment(
        connection, task=ROUTE_CHECK_TASK, left_kind="attempt", left_id=attempt_id,
        judge="llm", judge_model=str(judgment["judge_model"]), prompt_version=ROUTE_CHECK_PROMPT_VERSION,
        input_hash=str(judgment["input_hash"]), verdict=str(judgment["verdict"]),
        score=judgment.get("score"), rationale=str(judgment["rationale"]),
        supersedes_id=str(current[0]) if current is not None else None, created_at=created_at,
    )


def gate_inputs(
    grading_support: Mapping[str, Any], *, item: PracticeItem, learner_answer_md: str,
) -> tuple[str | None, bool]:
    """(final-answer status, divergent route) for the gate, from the blind run.

    The status is the deterministic check PF-c recorded in its reference
    policy, or the same check computed here when the policy is off
    (``diagnosis.grading_support = false``), so a demonstrably different
    conclusion is never restored either way (review F2). ``divergent_route``
    is the grader's own ``route_check`` reading; without the policy there is
    none, and P1's unlocated rule does not apply.
    """

    from learnloop.attempts.answer_check import final_answer_check

    policy = grading_support.get("reference_policy") or {}
    check = policy.get("final_answer_check") or final_answer_check(learner_answer_md, item.expected_answer)
    route = grading_support.get("route_check") or {}
    return (str(check.get("status")) if check.get("status") else None), bool(route.get("divergent_route"))


@dataclass(frozen=True)
class ProofCheckPlan:
    """What the route check would send for one answer (read-only; review F3).

    ``calls`` is an upper bound: an item not read yet costs one reading and,
    only if it reads as proof-like, one check.
    """

    calls: int
    estimated_input_tokens: int
    route: CheckerRoute | None
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "calls": self.calls,
            "estimated_input_tokens": self.estimated_input_tokens,
            "provider": self.route.provider if self.route is not None else None,
            "model": self.route.model if self.route is not None else None,
            "independent": self.route.independent if self.route is not None else None,
            "reason": self.reason,
        }


def plan_proof_check(
    vault: LoadedVault,
    repository: Any,
    *,
    item: PracticeItem,
    rubric: Rubric,
    learner_answer_md: str,
    grader_model: str | None,
) -> ProofCheckPlan:
    """The calls a new blind grade of this answer adds (no call, no write)."""

    if not proof_check_active(vault):
        return ProofCheckPlan(0, 0, None, "inactive: below mvp-0.17 or proof_check.enabled = false")
    route = proof_check_route(vault, grader_model=grader_model)
    if not route.provider:
        return ProofCheckPlan(0, 0, route, "no route for the check")
    check_tokens = estimated_prompt_tokens(route_check_prompt(item, rubric, learner_answer_md))
    cached = _cached_reading(repository, item, rubric)
    if cached is not None:
        if not cached[0].proof_like:
            return ProofCheckPlan(0, 0, route, "the item's cached reading is not proof-like: no check")
        return ProofCheckPlan(1, check_tokens, route, "proof-like item (cached reading): one route check")
    kind_tokens = estimated_prompt_tokens(item_kind_prompt(item, rubric))
    return ProofCheckPlan(
        2, kind_tokens + check_tokens, route,
        "the item is read once, then checked only if proof-like (upper bound)",
    )


def is_held_for_review(grading_support: Mapping[str, Any] | None) -> bool:
    """Did the route check leave this grade held for review (re-review F9)?

    Nothing assessed and nothing validated the answer: the grade is the
    grader's own, provisional, and the attempt applies no FSRS review on it.
    Read from the blind run's ``grading_support`` (live, regrade) or from the
    blind record that persists it (replay and the post-attempt pipeline), so
    every door reads one recorded fact, never today's config.
    """

    proof = (grading_support or {}).get(SUPPORT_KEY) or {}
    return (
        proof.get("status") == "checked"
        and bool(proof.get("held_for_review"))
        # A record written before the hold (v2 scheduled it as correct, with
        # PF-c's full marks) replays as it was written.
        and proof.get("version") not in _PRE_HOLD_VERSIONS
    )


def record_held_for_review(blind_record: Mapping[str, Any] | None) -> bool:
    """:func:`is_held_for_review` of a persisted blind grade record row."""

    record = (blind_record or {}).get("record") or {}
    return is_held_for_review(record.get("grading_support"))


def checked_calibration_prompt_version(base: str, grading_support: Mapping[str, Any] | None) -> str:
    """The calibration identity of one blind grade (S1 §4.3; P1's identity bump).

    A grade the route check ran on (``status = checked``) comes from a
    different measurement process than the grader alone: the gate may have
    restored, unassessed or flagged it. Its identity names the gate version,
    the checker's prompt version and the checker's model (review F4), so
    calibration never pools it with grades the grader produced alone
    (predecessors, the kill switch, a non-proof-like item, an unavailable
    check) or with checks by another model. It is persisted on the blind
    record, which is where replay reads it.
    """

    proof = (grading_support or {}).get(SUPPORT_KEY) or {}
    if proof.get("status") != "checked":
        return base
    checker = (proof.get("checker") or {}).get("model") or "unknown"
    gate = proof.get("version") or PROOF_CHECK_VERSION
    prompt = proof.get("prompt_version") or ROUTE_CHECK_PROMPT_VERSION
    return f"{base}+{gate}:{prompt}@{checker}"


def checked_run(
    run: Any,
    vault: LoadedVault,
    repository: Any,
    *,
    item: PracticeItem,
    rubric: Rubric,
    learner_answer_md: str,
    grader_model: str | None,
    created_at: str,
    clarification_exchange: Mapping[str, str] | None = None,
) -> Any:
    """The blind run with the route check applied (unchanged when inactive).

    The run's ``grading_support`` gains :data:`SUPPORT_KEY`; when the gate
    applied, PF-c's own keys are rewritten over both gates, so every reader of
    ``unverified_criterion_ids``, ``valid_alternative_gate_applied`` and
    ``assessed_shortfall`` (the attempt step, diagnosis, placement, the field)
    treats a route-check outcome exactly as a PF-c one.
    """

    if not proof_check_active(vault):
        return run
    support = dict(run.grading_support)
    unverified_before = [str(value) for value in support.get("unverified_criterion_ids") or ()]
    own_review = bool(getattr(run.ungated_proposal or run.proposal, "manual_review_recommended", False))
    final_status, divergent = gate_inputs(support, item=item, learner_answer_md=learner_answer_md)
    result = run_proof_route_check(
        vault, repository, item=item, rubric=rubric, learner_answer_md=learner_answer_md,
        proposal=run.proposal, unverified_before=unverified_before,
        grader_review_recommended=own_review, grader_model=grader_model, created_at=created_at,
        clarification_exchange=clarification_exchange,
        final_answer_status=final_status, divergent_route=divergent,
    )
    support[SUPPORT_KEY] = result.support
    proposal = run.proposal
    if result.gate is not None and result.gate.applied:
        gate = result.gate
        proposal = gate.proposal
        pfc_applied = bool(support.get("valid_alternative_gate_applied"))
        support.update(
            unverified_criterion_ids=list(gate.unverified),
            valid_alternative_gate_applied=True,
            valid_alternative_gate={"final_answer": pfc_applied, "proof_route": True},
            assessed_shortfall=gate.assessed_shortfall,
        )
        if gate.unverified:
            support[UNVERIFIED_INTERPRETATION_KEY] = UNASSESSED_INTERPRETATION
    return replace(run, proposal=proposal, grading_support=support, proof_check=result)


__all__ = [
    "CLARIFICATION_TRIGGER",
    "CheckerRoute",
    "CriterionRouteVerdict",
    "HELD_FOR_REVIEW_SUPPRESSION",
    "ITEM_KIND_TASK",
    "ItemKindReading",
    "PROOF_CHECK_VERSION",
    "PROOF_ROUTE_REVIEW_REASON",
    "ProofCheckPlan",
    "ProofCheckResult",
    "ProofGateOutcome",
    "ProofRouteCheck",
    "RESTORED_CRITERION_LABEL",
    "ROUTE_CHECK_TASK",
    "SPEND_ROUTE",
    "SUPPORT_KEY",
    "apply_proof_route_gate",
    "checked_calibration_prompt_version",
    "checked_run",
    "classify_item",
    "gate_inputs",
    "is_held_for_review",
    "item_kind_prompt",
    "plan_proof_check",
    "proof_check_active",
    "proof_check_route",
    "record_held_for_review",
    "record_route_check_judgment",
    "resolve_check_client",
    "route_check_prompt",
    "run_proof_route_check",
]
