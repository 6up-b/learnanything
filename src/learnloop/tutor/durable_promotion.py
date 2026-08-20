"""Durable-promotion arms (c) and (d) — the late-evidence path (§5.6).

``spec_causal_attribution_v1.md`` §5.6 lists four conditions for promoting a
provisional belief to a durable misconception:

    (a) a valid probe reproduces the blind pre-registered signature;
    (b) recurrence on a fingerprint-distinct independent evidence group;
    (c) deterministic proof the response necessarily instantiates the rule
        + learner confirmation;
    (d) human adjudication.

``misconceptions._promotion_reason`` implements (a) and (b) and nothing else,
because both are decidable *at normalization time* from the attempt in hand.
(c) and (d) are not: a learner confirmation arrives after the feedback screen
renders, and a human verdict arrives days later through
``learnloop diagnosis adjudicate``. They are LATE evidence, so they need a
re-driver rather than another branch inside the normalization loop — a branch
there would be permanently dead.

This module is that re-driver. It is deliberately the *only* place the two late
arms are decided, and it reaches durable state through exactly one door:
``misconceptions.promote_candidate``.

Why this is safe to re-run, and why replay reproduces it
--------------------------------------------------------
Both arms read append-only stores (``diagnosis_adjudications``,
``causal_hypotheses``, ``causal_attribution_reports``) and neither writes any
state of its own beyond the promotion itself. Idempotency is structural rather
than guarded by a flag:

* ``update_misconception_candidate(..., status='promoted')`` on a projected
  causal candidate appends a hypothesis version with ``status='validated'``
  (``repositories.py``), and ``_projected_causal_candidates`` projects only
  ``candidate`` heads. So a promoted belief STOPS being a candidate and the
  second call finds nothing to promote.
* Withdrawals check the belief's existing disposition stream first, so a verdict
  already narrated is never narrated twice.
* ``reset_learning_object_derived_state`` deletes neither ``misconceptions`` nor
  the causal chain, and the P1 receipt is explicitly preserved as an immutable
  decision record — so a rebuild neither loses nor duplicates a promotion.

What the two arms deliberately do NOT do
----------------------------------------
Neither arm overrides the §5.6 trace-consistency veto. That veto fires only when
a *deterministic* postdictive claim ("if H, criterion C must fail") is
contradicted by full credit on a criterion that actually elicited the rule —
a fact about the persisted grade ledger, not an absence of information. §5.6
calls it hard, and a human verdict is a judgement: if the ledger proves H false,
promoting H would write permanent facet damage and an authored correction for a
belief the learner demonstrably does not hold. Adjudication outranks the
system's *uncertainty*, never its *evidence*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from learnloop.clock import Clock
from learnloop.db.repositories import Repository
from learnloop.vault.models import LoadedVault


#: ``misconceptions.promotion_reason`` values minted by this module. The column
#: is free text and nothing branches on it, but these are the audit trail for
#: "why does this vault hold a durable belief about me", so they name the arm.
PROMOTION_REASON_ADJUDICATED = "human_adjudication"
PROMOTION_REASON_PROVED_AND_CONFIRMED = "deterministic_proof_and_learner_confirmation"

#: The one verdict that affirms the diagnosis the system actually asserted.
#:
#: `correct` is the only value asserting BOTH that the anchor was right and that
#: the repair was right — `diagnosis_adjudication._finalize` uses exactly this
#: verdict as the `repair_class_match_rate` numerator. Durable promotion is the
#: strongest authority in the system (it unlocks facet locks and permanent
#: authored corrections), so it takes the unambiguous verdict and nothing weaker.
AFFIRMING_VERDICTS = frozenset({"correct"})

#: Verdicts that say the system was wrong about a cause it NAMED. These are the
#: first real producer of an A6 withdrawal
#: (``learnloop.learner.surfaced_beliefs``).
#:
#: * `wrong_anchor` — the diagnosis pointed at the wrong place, so the belief it
#:   asserted is not the belief the trace supports.
#: * `should_have_abstained` — the system named a cause where the vocabulary
#:   could not name one. This is the harmful write `harmful_write_rate` (§3 B5)
#:   exists to count, and leaving it standing is the exact trust defect A6
#:   describes.
OVERTURNING_VERDICTS = frozenset({"wrong_anchor", "should_have_abstained"})

#: Verdicts that neither promote nor withdraw, and why each one is here:
#:
#: * `wrong_repair` — `ANCHOR_CORRECT_VERDICTS` includes it: the adjudicator
#:   said "right place, wrong fix". Withdrawing would tell the learner the
#:   diagnosis of their belief was wrong when the verdict says the opposite;
#:   promoting would launder a verdict that explicitly refused the repair, and
#:   `promote_candidate` freezes an authored correction at promotion time.
#: * `correctly_abstained` / `should_not_have_abstained` — both are recordable
#:   ONLY against an abstention (CHECK-enforced in migration 126). The system
#:   asserted no cause, so there is no belief to promote and none to withdraw.
#:   `should_not_have_abstained` is the sharpest case: the adjudicator supplies
#:   an anchor the system never formed a hypothesis for, and minting a durable
#:   belief from it would invent a claim about the learner that no diagnosis
#:   ever made.
NEUTRAL_VERDICTS = frozenset(
    {"wrong_repair", "correctly_abstained", "should_not_have_abstained"}
)

#: Every status a durable belief can be found under, INCLUDING the append-only
#: lifecycle dispositions. `misconceptions_for_learning_object` filters on
#: ``COALESCE(disposition, status)``, so the default three-status read cannot see
#: a belief that has already been demoted — and a lookup that cannot see a
#: retracted belief reports "there was none", which is a different and much worse
#: answer than "it is already retracted".
ANY_BELIEF_STATUS = ("active", "resolving", "resolved", "demoted", "superseded")


@dataclass(frozen=True)
class BeliefEffect:
    """What one late-evidence arm did to durable belief state.

    ``declined`` carries typed reasons rather than being dropped: an arm that
    silently does nothing is indistinguishable from an unwired one, which is the
    failure mode this whole plan item exists to fix.
    """

    arm: str
    attempt_id: str
    verdict: str | None = None
    promoted: tuple[str, ...] = ()
    withdrawn: tuple[str, ...] = ()
    declined: tuple[str, ...] = ()

    @property
    def changed(self) -> bool:
        return bool(self.promoted or self.withdrawn)

    def as_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "attempt_id": self.attempt_id,
            "verdict": self.verdict,
            "promoted": list(self.promoted),
            "withdrawn": list(self.withdrawn),
            "declined": list(self.declined),
        }


# ---------------------------------------------------------------------------
# Shared resolution: from an attempt's asserted causes to promotable candidates
# ---------------------------------------------------------------------------


def _asserted_hypotheses(
    repository: Repository, adjudication: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """The concrete causes the adjudicated diagnosis actually asserted.

    Read from the verdict's OWN frozen snapshot rather than from the live
    receipt: ``system_snapshot.plausible_hypothesis_ids`` is what the
    adjudicator was looking at, and migration 126 exists precisely so a verdict
    cannot change meaning when the receipt is rebuilt.

    The open-set arm (``H_OTHER``) is dropped — an open-world arm names no cause,
    so there is nothing to promote or retract.
    """

    from learnloop.diagnosis.causal_attribution import OPEN_SET_CAUSE_ID

    snapshot = adjudication.get("system_snapshot") or {}
    hypotheses: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in snapshot.get("plausible_hypothesis_ids") or []:
        hypothesis_id = str(raw)
        if not hypothesis_id or hypothesis_id == OPEN_SET_CAUSE_ID:
            continue
        hypothesis = repository.causal_hypothesis(hypothesis_id)
        if hypothesis is None or hypothesis.get("status") == "open_set":
            continue
        # A chain may have advanced past the version the receipt named; the
        # normalized statement is stable across versions of one episode, so it
        # is the join key rather than the id.
        key = str(hypothesis.get("statement_normalized") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        hypotheses.append(hypothesis)
    return hypotheses


def _promote_hypothesis(
    vault: LoadedVault,
    repository: Repository,
    hypothesis: Mapping[str, Any],
    *,
    reason: str,
    attempt_id: str,
    clock: Clock | None,
) -> tuple[str | None, str | None]:
    """Promote the holding-pen candidate behind ``hypothesis``. Returns (id, declined).

    Every gate here is a real refusal, named in the returned reason so an arm
    that declines is auditable instead of silent.
    """

    from learnloop.diagnosis.causal_attribution import trace_consistent
    from learnloop.diagnosis.misconceptions import normalize_text, promote_candidate

    learning_object_id = str(hypothesis.get("learning_object_id") or "")
    learning_object = vault.learning_objects.get(learning_object_id)
    if learning_object is None:
        return None, f"learning_object_absent:{learning_object_id}"

    normalized = str(hypothesis.get("statement_normalized") or "") or normalize_text(
        str(hypothesis.get("statement") or "")
    )
    if not normalized:
        return None, "statement_empty"

    # Already durable? Then this arm has nothing to add. Covers both a prior run
    # of this arm and a belief promoted earlier by arm (a)/(b).
    #
    # A belief that was WITHDRAWN is refused separately and deliberately: silently
    # re-promoting a statement the system has already apologised for would
    # re-assert the retracted claim with no second correction to explain it, which
    # is the "quietly re-state it" failure A6 forbids. Re-asserting it has to be a
    # conscious act with its own evidence, not a side effect of a re-drive.
    for record in repository.misconceptions_for_learning_object(
        learning_object_id, statuses=ANY_BELIEF_STATUS
    ):
        if normalize_text(record.statement) != normalized:
            continue
        if record.lifecycle_disposition in {"demoted", "superseded"}:
            return None, f"previously_withdrawn:{record.lifecycle_disposition}"
        return None, "already_durable"

    candidate = repository.misconception_candidate_by_normalized(
        learning_object_id, normalized
    )
    if candidate is None:
        # A projected causal candidate disappears once promoted (its head flips
        # to `validated`), so "no candidate" is also the idempotency answer.
        return None, "no_promotable_candidate"
    if str(candidate.get("status") or "") != "candidate":
        return None, f"candidate_status:{candidate.get('status')}"

    # §5.6's hard veto, scoped to THIS hypothesis: a rival's contradicted claim
    # says nothing about this one. Neither late arm may override it — see the
    # module docstring.
    if not trace_consistent(
        vault, repository, attempt_id, hypothesis_id=str(hypothesis.get("id") or "") or None
    ):
        return None, "trace_consistency_veto"

    misconception_id = promote_candidate(
        vault,
        repository,
        candidate,
        learning_object=learning_object,
        reason=reason,
        clock=clock,
    )
    # Deliberately NOT calling `set_error_event_misconception` the way the
    # normalization loop does. That loop is iterating the attempt's events and
    # links the one it just consumed; a late arm is not, and back-linking events
    # from an arbitrary later moment would make the link depend on when the sweep
    # ran (`misconceptions.py`'s note: events left as candidates keep
    # `misconception_id` NULL so replay reproduces durable rows statelessly).
    # The durable row still records `source_error_event_ids`, and the posterior is
    # unaffected: a fire only counts where a discrimination row exists, and a
    # freshly promoted belief has none, so `misconception_posterior` holds at the
    # severity prior rather than being resolved away on the next sweep.
    return misconception_id, None


def _withdraw_hypothesis(
    repository: Repository,
    hypothesis: Mapping[str, Any],
    *,
    clock: Clock | None,
) -> tuple[str | None, str | None]:
    """Retract the durable belief this hypothesis was promoted into.

    The disposition is recorded unconditionally; whether the learner is TOLD is
    A6's decision (`learner_review_feed` narrates only beliefs a
    `surfaced_to_learner` presentation proves they saw). Recording it for an
    unsurfaced belief is the lifecycle fact; narrating it would be noise.
    """

    from learnloop.diagnosis.misconceptions import normalize_text
    from learnloop.learner.surfaced_beliefs import record_belief_withdrawal

    learning_object_id = str(hypothesis.get("learning_object_id") or "")
    normalized = str(hypothesis.get("statement_normalized") or "")
    if not normalized:
        return None, "statement_empty"
    for record in repository.misconceptions_for_learning_object(
        learning_object_id, statuses=ANY_BELIEF_STATUS
    ):
        if normalize_text(record.statement) != normalized:
            continue
        # One adjudicated withdrawal per belief. A re-adjudication that lands a
        # second overturning verdict finds the belief already retracted, and
        # re-narrating it would be the "told twice" noise A6 forbids.
        if any(
            str(event.get("reason") or "") == "adjudicated"
            for event in repository.misconception_dispositions(record.id)
        ):
            return None, "already_withdrawn"
        record_belief_withdrawal(
            repository, belief_id=record.id, reason="adjudicated", clock=clock
        )
        return record.id, None
    return None, "no_durable_belief"


# ---------------------------------------------------------------------------
# Arm (d): human adjudication
# ---------------------------------------------------------------------------


def apply_adjudicated_belief_effects(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> BeliefEffect:
    """§5.6 arm (d): route the active verdict on ``attempt_id`` into belief state.

    Only the head of the supersession chain acts. That is what makes a second
    opinion replace the first rather than compound with it, and it is why this
    can run on every read without accumulating effects.
    """

    adjudication = repository.active_diagnosis_adjudication(attempt_id)
    if adjudication is None:
        return BeliefEffect(arm="adjudication", attempt_id=attempt_id, declined=("no_verdict",))
    verdict = str(adjudication.get("verdict") or "")

    if verdict in NEUTRAL_VERDICTS:
        return BeliefEffect(
            arm="adjudication",
            attempt_id=attempt_id,
            verdict=verdict,
            declined=(f"neutral_verdict:{verdict}",),
        )

    hypotheses = _asserted_hypotheses(repository, adjudication)
    if not hypotheses:
        return BeliefEffect(
            arm="adjudication",
            attempt_id=attempt_id,
            verdict=verdict,
            declined=("no_asserted_cause",),
        )

    if verdict in OVERTURNING_VERDICTS:
        withdrawn: list[str] = []
        declined: list[str] = []
        for hypothesis in hypotheses:
            belief_id, reason = _withdraw_hypothesis(
                repository, hypothesis, clock=clock
            )
            if belief_id is not None:
                withdrawn.append(belief_id)
            elif reason is not None:
                declined.append(reason)
        return BeliefEffect(
            arm="adjudication",
            attempt_id=attempt_id,
            verdict=verdict,
            withdrawn=tuple(withdrawn),
            declined=tuple(declined),
        )

    # Affirming verdict. A verdict on an episode that asserted SEVERAL concrete
    # causes does not say which one the learner holds: `correct` rules on the
    # anchor and the repair, not on a choice among rival beliefs. Minting a
    # durable belief for each would turn one verdict into N permanent claims
    # about the learner, so an ambiguous set promotes nothing and says so.
    #
    # This is also what makes it safe for arm (d) to proceed while an unresolved
    # cause factor is still open — the case the block exists for (the system
    # cannot discriminate) is exactly the case this refuses.
    if len(hypotheses) > 1:
        return BeliefEffect(
            arm="adjudication",
            attempt_id=attempt_id,
            verdict=verdict,
            declined=(f"ambiguous_cause_set:{len(hypotheses)}",),
        )

    misconception_id, reason = _promote_hypothesis(
        vault,
        repository,
        hypotheses[0],
        reason=PROMOTION_REASON_ADJUDICATED,
        attempt_id=attempt_id,
        clock=clock,
    )
    return BeliefEffect(
        arm="adjudication",
        attempt_id=attempt_id,
        verdict=verdict,
        promoted=(misconception_id,) if misconception_id else (),
        declined=(reason,) if reason else (),
    )


# ---------------------------------------------------------------------------
# Arm (c): deterministic proof + learner confirmation
# ---------------------------------------------------------------------------


def _verified_repair_class_ids(repository: Repository, attempt_id: str) -> set[str]:
    """Repair classes this attempt's diagnosis DETERMINISTICALLY proved.

    "Deterministic proof the response necessarily instantiates the rule" is what
    a `verified` repair validation asserts: applying the named repair to the
    learner's own answer yields the authored expected answer, symbolically or
    exactly (`SympyVerifierAdapter` / the `exact_match` branch). The learner's
    response therefore differs from correct by precisely the rule the hypothesis
    names — no model judgement anywhere in the chain.

    Two gates, both deliberate:

    * ``verification.status == 'verified'`` is the only proving value; the other
      four (`contradicted`, `unsupported`, `parse_failed`, `assumption_missing`)
      are all "no proof", and `unsupported` is the overwhelmingly common one
      because it means no verifier was even requested.
    * ``repair_validation.status == 'valid'`` as well. A candidate that also
      failed a structural check (an unverifiable checkpoint claim, a protected
      ref) is not a proof of anything, even with a CAS equality in hand.

    Returned as repair-class ids because that is the ONLY structural bridge from
    a verification (which is attached to a repair suggestion) to a belief:
    ``causal_hypotheses.repair_class_id``. A verification that cannot name the
    belief it proves may not promote one, so this fails closed — no receipt, no
    repair class, no proof.

    Only the SELECTED repair is inspectable, and that is not a limitation to work
    around: ``select_minimal_repair`` records rejected candidates as
    ``{repair_class_id, reasons}`` with no suggestion attached, and a repair the
    verifier *contradicted* is rejected by construction. So "the selected
    repair's verification" is the whole of the deterministic evidence the episode
    retained.
    """

    from learnloop.diagnosis.causal_attribution import causal_episode_for_attempt

    episode = causal_episode_for_attempt(repository, attempt_id)
    receipt = (episode or {}).get("receipt")
    if not isinstance(receipt, Mapping):
        return set()
    selection = receipt.get("repair_selection")
    selection = selection if isinstance(selection, Mapping) else {}
    selected = selection.get("selected")
    if not isinstance(selected, Mapping):
        return set()
    suggestion = selected.get("suggestion")
    suggestion = suggestion if isinstance(suggestion, Mapping) else {}
    validation = suggestion.get("repair_validation")
    validation = validation if isinstance(validation, Mapping) else {}
    verification = validation.get("verification")
    verification = verification if isinstance(verification, Mapping) else {}
    if str(verification.get("status") or "") != "verified":
        return set()
    if str(validation.get("status") or "") != "valid":
        return set()
    repair_class = selected.get("repair_class")
    repair_class = repair_class if isinstance(repair_class, Mapping) else {}
    class_id = str(repair_class.get("id") or "")
    return {class_id} if class_id else set()


def _confirmed_hypotheses(
    repository: Repository, attempt_id: str
) -> list[dict[str, Any]]:
    """Hypotheses the learner said "I believed this" about, on this attempt.

    The durable record of a §5.6 confirmation is not the report row — that is
    keyed on a factor with an integer ``candidate_index`` — but the hypothesis
    version ``record_unresolved_cause_self_report`` appends carrying
    ``evidence.learner_confirmation``. Reading the chain means the confirmation
    survives re-materialization and names exactly one belief.

    ``latest_only=False`` is load-bearing. Recording a confirmation re-materializes
    the episode, and ``materialize_causal_episode`` rebuilds each hypothesis's
    evidence dict from the grader plan — so the HEAD after confirmation may not
    carry the marker. A confirmation is a historical fact about a version, not a
    property of whatever version is current, so the whole chain is scanned.
    """

    confirmed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hypothesis in repository.causal_hypotheses_for_attempt(
        attempt_id, latest_only=False
    ):
        evidence = hypothesis.get("evidence")
        if not isinstance(evidence, Mapping):
            continue
        confirmation = evidence.get("learner_confirmation")
        if not isinstance(confirmation, Mapping):
            continue
        if str(confirmation.get("response") or "") != "believed_candidate":
            continue
        key = str(hypothesis.get("statement_normalized") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        confirmed.append(hypothesis)
    return confirmed


def apply_proved_and_confirmed_promotion(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> BeliefEffect:
    """§5.6 arm (c): deterministic proof AND learner confirmation, conjunctively.

    Neither half promotes alone, and the conjunction is not "both happened on
    this attempt" — the two must be about the SAME belief. The join is
    ``causal_hypotheses.repair_class_id``: the confirmed hypothesis must carry
    the repair class whose repair the verifier proved. A confirmation with no
    repair mapping declines (that is `incomplete_repair_mapping`, itself an
    adjudication queue reason), and a proof about some other belief's repair
    grants this one nothing.

    This deliberately does NOT route through ``SUPPORT_BASIS_AUTHORITY``. That
    table governs the other lane — which channels may move *diagnosis support
    scores* on a triage route — and it grants `learner_confirmation` the
    `learner_confirmed` authority on its own. Durable promotion is a stronger
    write than support movement (facet locks, permanent authored corrections), and
    §5.6 arm (c) is a conjunction precisely because a bounded-trust self-report
    must not reach it alone. The validator-owned half is what carries the
    authority here; the confirmation is what makes it a belief about the learner
    rather than a fact about the answer.
    """

    confirmed = _confirmed_hypotheses(repository, attempt_id)
    if not confirmed:
        return BeliefEffect(
            arm="proof_and_confirmation",
            attempt_id=attempt_id,
            declined=("no_learner_confirmation",),
        )
    verified_classes = _verified_repair_class_ids(repository, attempt_id)
    if not verified_classes:
        return BeliefEffect(
            arm="proof_and_confirmation",
            attempt_id=attempt_id,
            declined=("no_deterministic_proof",),
        )

    promoted: list[str] = []
    declined: list[str] = []
    for hypothesis in confirmed:
        repair_class_id = str(hypothesis.get("repair_class_id") or "")
        if not repair_class_id:
            declined.append("confirmed_belief_has_no_repair_class")
            continue
        if repair_class_id not in verified_classes:
            declined.append("proof_is_for_a_different_repair")
            continue
        misconception_id, reason = _promote_hypothesis(
            vault,
            repository,
            hypothesis,
            reason=PROMOTION_REASON_PROVED_AND_CONFIRMED,
            attempt_id=attempt_id,
            clock=clock,
        )
        if misconception_id is not None:
            promoted.append(misconception_id)
        elif reason is not None:
            declined.append(reason)
    return BeliefEffect(
        arm="proof_and_confirmation",
        attempt_id=attempt_id,
        promoted=tuple(promoted),
        declined=tuple(declined),
    )


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------


def apply_late_promotion_evidence(
    vault: LoadedVault,
    repository: Repository,
    *,
    attempt_id: str,
    clock: Clock | None = None,
) -> list[BeliefEffect]:
    """Run both late arms for one attempt. Idempotent; safe on a read path.

    Arm (c) runs first, and the order is deliberate: when both apply, the belief
    should record the evidence that is stronger and older. A deterministic proof
    plus the learner's own confirmation is a better answer to "why does this vault
    hold a durable belief about me" than a verdict that arrived later, and
    ``promotion_reason`` is written once, at promotion.
    """

    return [
        apply_proved_and_confirmed_promotion(
            vault, repository, attempt_id=attempt_id, clock=clock
        ),
        apply_adjudicated_belief_effects(
            vault, repository, attempt_id=attempt_id, clock=clock
        ),
    ]


def sweep_late_promotion_evidence(
    vault: LoadedVault,
    repository: Repository,
    *,
    learning_object_id: str,
    clock: Clock | None = None,
) -> list[BeliefEffect]:
    """Catch up on late evidence for one learning object.

    Arm (d) fires at the moment a verdict is recorded when the caller supplies a
    vault, and arm (c) fires when the learner confirms. This sweep is the
    backstop for the callers that cannot: it makes the next attempt on the LO
    pick up a verdict recorded in between, so an adjudication is never silently
    inert just because it arrived through a surface with no vault in hand.

    Bounded by the adjudicated/confirmed sets rather than by all attempts, and
    both sets come from ONE query each. This runs on the feedback path for every
    attempt, so a per-attempt probe would put a fresh SQLite connection (and its
    schema parse) between the learner and their result for every attempt in the
    LO's history.
    """

    attempt_ids = {
        str(attempt["id"])
        for attempt in repository.list_attempts_by_learning_object(learning_object_id)
    }
    if not attempt_ids:
        return []
    interesting = attempt_ids & repository.adjudicated_attempt_ids()
    # Confirmations, in one pass over the LO's whole hypothesis chain. A confirmed
    # version keeps `status='candidate'`, and `latest_only=False` is required for
    # the same reason `_confirmed_hypotheses` needs it: re-materialization can
    # append a newer version that does not carry the marker.
    for hypothesis in repository.causal_hypotheses_for_learning_object(
        learning_object_id, statuses=("candidate",), latest_only=False
    ):
        evidence = hypothesis.get("evidence")
        if not isinstance(evidence, Mapping):
            continue
        confirmation = evidence.get("learner_confirmation")
        if not isinstance(confirmation, Mapping):
            continue
        if str(confirmation.get("response") or "") != "believed_candidate":
            continue
        attempt_id = str(hypothesis.get("attempt_id") or "")
        if attempt_id in attempt_ids:
            interesting.add(attempt_id)
    effects: list[BeliefEffect] = []
    for attempt_id in sorted(interesting):
        effects.extend(
            apply_late_promotion_evidence(
                vault, repository, attempt_id=attempt_id, clock=clock
            )
        )
    return [effect for effect in effects if effect.changed]
