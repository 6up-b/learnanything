"""§5.6 durable-promotion arms (c) and (d) — the late-evidence path.

``spec_causal_attribution_v1.md`` §5.6 names four promotion conditions.
``misconceptions._promotion_reason`` implements (a) probe-signature reproduction
and (b) independent-surface recurrence. This file covers the two that arrive
*after* the attempt has been normalized, and therefore could not be branches
there:

  (c) deterministic proof the response necessarily instantiates the rule
      + learner confirmation — CONJUNCTIVELY, and about the same belief;
  (d) human adjudication — and its converse, which is the first real producer of
      an A6 withdrawal (`spec_diagnostic_augmentation_v1.md` §2 A6).

Nothing here hand-builds a receipt, a cause set, or a verification result. Every
input goes through `apply_attempt`, `record_unresolved_cause_self_report`, or
`append_diagnosis_adjudication` — hand-built dicts are exactly how the original
dead code in this area passed review, and a test that authors its own receipt
cannot tell a wired arm from an inert one.

All deterministic under FrozenClock.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.attempts import (
    ApplyAttemptInput,
    AttemptDraft,
    GradeAttribution,
    ResolvedGrade,
    apply_attempt,
)
from learnloop.services.causal_attribution import record_unresolved_cause_self_report
from learnloop.services.diagnosis_adjudication import append_diagnosis_adjudication
from learnloop.services.durable_promotion import (
    PROMOTION_REASON_ADJUDICATED,
    PROMOTION_REASON_PROVED_AND_CONFIRMED,
    apply_adjudicated_belief_effects,
    apply_proved_and_confirmed_promotion,
    sweep_late_promotion_evidence,
)
from learnloop.services.learner_review_feed import build_learner_review_feed
from learnloop.services.misconceptions import _normalize_text
from learnloop.services.state_sync import sync_vault_state
from learnloop.services.surfaced_beliefs import mark_belief_surfaced
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, NOW_ISO
from tests.test_km2_write_path import SHARED, build_mvp07_vault


CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"
#: One criterion, one measurement target -> a failure names exactly ONE cause and
#: opens no unresolved-cause factor. This is the shape arm (d) can act on.
SINGLE_ITEM = "pi_svd_define_001"
#: One whole-item criterion over TWO measurement targets -> the cause set stays
#: open, a factor opens, and the learner can confirm one arm of it. This is the
#: only shape arm (c) can act on, because a confirmation needs an open factor.
AMBIGUOUS_ITEM = "pi_svd_ambiguous_001"

STATEMENT = "The learner treats Sigma as the eigenvalue matrix of A."
REF = {"kind": "facet_capability", "facet_id": SHARED, "capability": "retrieval"}


def _vault(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    return vault, repository, paths


def _verified_repair() -> dict:
    """A repair the deterministic verifier can PROVE.

    `expected_answer` on every `build_mvp07_vault` item is the literal
    ``"An answer."``, so an `exact_match` request against a repaired answer of
    the same string is a genuine `verified` — the CAS/exact-match adapter decides
    it, not this fixture.
    """

    return {
        "practice_mode": "targeted_review",
        "operator": "restate_definition",
        "rationale": "Name Sigma as singular values.",
        "target_refs": [REF],
        "expected_minutes": 2.0,
        "answer_reveal_budget": 0.4,
        "verification_request": {"kind": "exact_match"},
        "repaired_trace": {
            "learner_work_prefix": "Sigma holds ",
            "repair_insertion_point": {
                "anchor_kind": "span",
                "criterion_id": "correctness",
                "quote": "eigenvalues",
            },
            "minimal_edit": "singular values",
            "regenerated_work": "",
            "repaired_answer_md": "An answer.",
            "changed_latent_claims": ["Sigma holds singular values"],
            "changed_checkpoint_ids": [],
        },
    }


def _unverified_repair() -> dict:
    """The same repair with no verification requested — the common case.

    `validate_repair_candidate` returns `unsupported` ("no deterministic
    verification was requested"), which is a proof of nothing.
    """

    repair = _verified_repair()
    repair.pop("verification_request")
    return repair


def _failure(
    vault,
    repository,
    *,
    attempt_id: str,
    item_id: str = SINGLE_ITEM,
    criterion: str = "correctness",
    points: float = 0.0,
    rubric_score: int = 0,
    repairs: list[dict] | None = None,
    postdictive_claims: list[dict] | None = None,
    abstain: bool = False,
):
    """One real graded miss, diagnosed as a learner-state cause (or abstained)."""

    attribution = GradeAttribution(
        error_type="wrong_method",
        severity=0.7,
        evidence="Sigma is not the eigenvalue matrix of A.",
        is_misconception=not abstain,
        misconception_statement=None if abstain else STATEMENT,
        resolution_status="abstained" if abstain else "unresolved",
        abstention_reason=(
            "no facet in the vocabulary names this confusion" if abstain else None
        ),
        cause_scope="unknown" if abstain else "learner_state",
        operation=None if abstain else "wrong_method",
        first_divergence=(
            None
            if abstain
            else {
                "anchor_kind": "span",
                "criterion_id": criterion,
                "quote": "eigenvalues",
            }
        ),
        candidate_causes=(
            []
            if abstain
            else [
                {
                    "statement": STATEMENT,
                    "cause_scope": "learner_state",
                    "target_ref": REF,
                }
            ]
        ),
        postdictive_claims=list(postdictive_claims or []),
    )
    return apply_attempt(
        vault,
        repository,
        ApplyAttemptInput(
            draft=AttemptDraft(
                practice_item_id=item_id,
                learner_answer_md="Sigma holds eigenvalues.",
            ),
            attempt_id=attempt_id,
            grade=ResolvedGrade(
                rubric_score=rubric_score,
                criterion_points={criterion: points},
                evidence_rows=[
                    {
                        "id": f"ge_{attempt_id}",
                        "criterion_id": criterion,
                        "points_awarded": float(points),
                        "evidence": "Sigma was called the eigenvalue matrix.",
                        "notes": None,
                        "local_grader_id": "test",
                        "grader_tier": 1,
                        "created_at": NOW_ISO,
                    }
                ],
                error_attributions=[attribution],
                grader_confidence=0.9,
                confidence=4,
                manual_review_reason=None,
                feedback_md="Sigma holds singular values.",
                repair_suggestions=list(
                    repairs if repairs is not None else [_verified_repair()]
                ),
            ),
        ),
        clock=CLOCK,
    )


def _durable(repository, statuses=("active", "resolving", "resolved")):
    return repository.misconceptions_for_learning_object(LO_ID, statuses=statuses)


def _confirm(vault, repository, attempt_id: str, *, statement: str = STATEMENT):
    """Learner taps "I believed one of these" on the named arm."""

    factor = repository.unresolved_cause_factors_for_attempt(attempt_id)[0]
    index = next(
        position
        for position, cause in enumerate(factor["candidate_causes"])
        if str(cause.get("statement")) == statement
    )
    return record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor["id"],
        response="believed_candidate",
        candidate_index=index,
        clock=CLOCK,
    )


def _withdrawal_entries(vault, repository) -> list[dict]:
    return [
        entry
        for entry in build_learner_review_feed(vault, repository)["changelog"]
        if entry["kind"] == "belief_withdrawn"
    ]


# ── The verdict vocabulary is partitioned, exhaustively ────────────────────


def test_every_verdict_has_a_promotion_decision(tmp_path):
    """A seventh verdict must not default into silence.

    The three sets partition `VERDICTS` exactly: adding a value to the store
    without deciding whether it promotes, retracts, or does neither fails here
    rather than quietly doing nothing to belief state.
    """

    from learnloop.services.diagnosis_adjudication import VERDICTS
    from learnloop.services.durable_promotion import (
        AFFIRMING_VERDICTS,
        NEUTRAL_VERDICTS,
        OVERTURNING_VERDICTS,
    )

    assert AFFIRMING_VERDICTS | OVERTURNING_VERDICTS | NEUTRAL_VERDICTS == set(VERDICTS)
    assert not AFFIRMING_VERDICTS & OVERTURNING_VERDICTS
    assert not AFFIRMING_VERDICTS & NEUTRAL_VERDICTS
    assert not OVERTURNING_VERDICTS & NEUTRAL_VERDICTS
    # Neither abstention verdict may promote or retract: the system asserted no
    # cause, so there is no belief to act on.
    from learnloop.services.diagnosis_adjudication import ABSTENTION_VERDICTS

    assert ABSTENTION_VERDICTS <= NEUTRAL_VERDICTS


# ── Arm (d): human adjudication ────────────────────────────────────────────


def test_correct_verdict_promotes_the_cause_the_system_asserted(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_d")
    # The attempt alone promotes nothing: one surface, no probe, so neither
    # arm (a) nor arm (b) fires. That is the precondition the arm is tested on.
    assert _durable(repository) == []

    record = append_diagnosis_adjudication(
        repository, attempt_id="att_d", verdict="correct", vault=vault, clock=CLOCK
    )
    assert record["verdict"] == "correct"

    durable = _durable(repository)
    assert len(durable) == 1
    assert _normalize_text(durable[0].statement) == _normalize_text(STATEMENT)
    assert durable[0].promotion_reason == PROMOTION_REASON_ADJUDICATED
    # A promoted belief carries the frozen authored correction, which is exactly
    # the permanent write durable status unlocks.
    assert durable[0].status == "active"


def test_adjudicated_promotion_is_idempotent(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_idem")
    append_diagnosis_adjudication(
        repository, attempt_id="att_idem", verdict="correct", vault=vault, clock=CLOCK
    )
    first = _durable(repository)
    assert len(first) == 1

    # Re-driving the arm — which every normalization sweep does — must not mint a
    # second durable belief. The guard is structural: a promoted candidate stops
    # being projected as a candidate at all.
    for _ in range(3):
        effect = apply_adjudicated_belief_effects(
            vault, repository, attempt_id="att_idem", clock=CLOCK
        )
        assert effect.promoted == ()
        assert "already_durable" in effect.declined
    assert [row.id for row in _durable(repository)] == [first[0].id]


@pytest.mark.parametrize("verdict", ["correctly_abstained", "should_not_have_abstained"])
def test_a_verdict_against_an_abstention_never_promotes(tmp_path, verdict):
    """There is no belief to promote: the system named no cause.

    `should_not_have_abstained` is the sharp case — the adjudicator supplies an
    anchor the system never formed a hypothesis for, and minting a durable belief
    from it would invent a claim about the learner that no diagnosis ever made.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_abstain", abstain=True)

    record = append_diagnosis_adjudication(
        repository,
        attempt_id="att_abstain",
        verdict=verdict,
        adjudicated_anchor={
            "anchor_kind": "whole_answer",
            "criterion_id": "correctness",
        },
        vault=vault,
        clock=CLOCK,
    )
    assert record["system_abstained"] is True
    assert _durable(repository) == []
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_abstain", clock=CLOCK
    )
    assert effect.promoted == ()
    assert effect.withdrawn == ()
    assert effect.declined == (f"neutral_verdict:{verdict}",)


def test_wrong_repair_is_neutral_because_the_anchor_was_ruled_correct(tmp_path):
    """`ANCHOR_CORRECT_VERDICTS` includes it: "right place, wrong fix".

    Withdrawing would tell the learner the diagnosis of their belief was wrong
    when the verdict says the opposite; promoting would launder a verdict that
    explicitly refused the repair whose copy promotion freezes.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_wr")

    append_diagnosis_adjudication(
        repository,
        attempt_id="att_wr",
        verdict="wrong_repair",
        adjudicated_repair_md="Contrast Sigma with the eigenvalue matrix directly.",
        vault=vault,
        clock=CLOCK,
    )
    assert _durable(repository) == []
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_wr", clock=CLOCK
    )
    assert effect.declined == ("neutral_verdict:wrong_repair",)


def test_an_ambiguous_cause_set_promotes_nothing(tmp_path):
    """`correct` rules on the anchor and repair, not among rival beliefs.

    Minting one durable belief per plausible cause would turn a single verdict
    into N permanent claims about the learner. This is also what makes it safe
    for the arm to run while an unresolved-cause factor is still open: the case
    the open-factor block exists for is exactly the case refused here.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_amb",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    assert len(repository.unresolved_cause_factors_for_attempt("att_amb")) == 1

    append_diagnosis_adjudication(
        repository, attempt_id="att_amb", verdict="correct", vault=vault, clock=CLOCK
    )
    assert _durable(repository) == []
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_amb", clock=CLOCK
    )
    assert effect.promoted == ()
    assert any(reason.startswith("ambiguous_cause_set:") for reason in effect.declined)


def test_the_trace_consistency_veto_outranks_a_human_verdict(tmp_path):
    """§5.6 calls the deterministic postdictive veto hard, and it stays hard.

    A verdict is a judgement; a contradicted deterministic claim is a fact about
    the persisted grade ledger. If the hypothesis asserted "if H, this criterion
    must not get full credit" and the criterion got full credit, H is false —
    promoting it would write permanent facet damage and an authored correction
    for a belief the learner demonstrably does not hold. Adjudication outranks
    the system's uncertainty, never its evidence.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_veto",
        points=4.0,
        rubric_score=4,
        postdictive_claims=[
            {"criterion_id": "correctness", "must": "not_full_credit"}
        ],
    )

    append_diagnosis_adjudication(
        repository, attempt_id="att_veto", verdict="correct", vault=vault, clock=CLOCK
    )
    assert _durable(repository) == []
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_veto", clock=CLOCK
    )
    assert effect.promoted == ()
    assert "trace_consistency_veto" in effect.declined


# ── Arm (d)'s converse: the first real producer of an A6 withdrawal ────────


@pytest.mark.parametrize("verdict", ["wrong_anchor", "should_have_abstained"])
def test_an_overturning_verdict_withdraws_a_surfaced_belief_once(tmp_path, verdict):
    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_over")
    head = append_diagnosis_adjudication(
        repository, attempt_id="att_over", verdict="correct", vault=vault, clock=CLOCK
    )
    belief = _durable(repository)[0]

    # The learner is actually shown the claim — otherwise A6's scope guard makes
    # the retraction housekeeping rather than a correction.
    mark_belief_surfaced(
        repository,
        belief_id=belief.id,
        claim_text=belief.statement,
        surface="feedback",
        clock=CLOCK,
    )

    append_diagnosis_adjudication(
        repository,
        attempt_id="att_over",
        verdict=verdict,
        adjudicated_anchor={
            "anchor_kind": "whole_answer",
            "criterion_id": "correctness",
        },
        supersedes_id=head["id"],
        vault=vault,
        clock=CLOCK,
    )

    dispositions = repository.misconception_dispositions(belief.id)
    assert [event["reason"] for event in dispositions] == ["adjudicated"]
    assert [event["disposition"] for event in dispositions] == ["demoted"]

    entries = _withdrawal_entries(vault, repository)
    assert len(entries) == 1
    assert entries[0]["belief_id"] == belief.id
    assert entries[0]["withdrawal_reason"] == "adjudicated"
    assert entries[0]["withdrawn_claim_text"] == belief.statement
    assert "withdrawn" in entries[0]["statement"]

    # Re-driving must not retract twice, and the feed must not re-narrate.
    for _ in range(3):
        effect = apply_adjudicated_belief_effects(
            vault, repository, attempt_id="att_over", clock=CLOCK
        )
        assert effect.withdrawn == ()
        assert "already_withdrawn" in effect.declined
    assert len(_withdrawal_entries(vault, repository)) == 1
    # The belief itself is out of the standing set, not merely annotated.
    assert _durable(repository) == []


def test_an_overturned_belief_the_learner_never_saw_is_retracted_but_not_narrated(
    tmp_path,
):
    """A6's scope guard: the disposition is the lifecycle fact, the entry is not.

    Recording the retraction is unconditional — it is what removes the belief
    from the standing set. Narrating it would be noise for a claim nobody read.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_quiet")
    head = append_diagnosis_adjudication(
        repository, attempt_id="att_quiet", verdict="correct", vault=vault, clock=CLOCK
    )
    belief = _durable(repository)[0]

    append_diagnosis_adjudication(
        repository,
        attempt_id="att_quiet",
        verdict="wrong_anchor",
        adjudicated_anchor={
            "anchor_kind": "whole_answer",
            "criterion_id": "correctness",
        },
        supersedes_id=head["id"],
        vault=vault,
        clock=CLOCK,
    )

    assert [
        event["reason"] for event in repository.misconception_dispositions(belief.id)
    ] == ["adjudicated"]
    assert _withdrawal_entries(vault, repository) == []


def test_a_withdrawn_belief_is_not_quietly_re_promoted(tmp_path):
    """A third verdict flipping back to `correct` must not silently re-assert it.

    Re-promoting a statement the system has already apologised for would restore
    the retracted claim with no second correction to explain it — the "quietly
    re-state it" failure A6 forbids. Re-asserting has to be a conscious act with
    its own evidence, not a side effect of a re-drive.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_flip")
    first = append_diagnosis_adjudication(
        repository, attempt_id="att_flip", verdict="correct", vault=vault, clock=CLOCK
    )
    belief = _durable(repository)[0]
    second = append_diagnosis_adjudication(
        repository,
        attempt_id="att_flip",
        verdict="wrong_anchor",
        adjudicated_anchor={
            "anchor_kind": "whole_answer",
            "criterion_id": "correctness",
        },
        supersedes_id=first["id"],
        vault=vault,
        clock=CLOCK,
    )
    assert _durable(repository) == []

    append_diagnosis_adjudication(
        repository,
        attempt_id="att_flip",
        verdict="correct",
        supersedes_id=second["id"],
        vault=vault,
        clock=CLOCK,
    )
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_flip", clock=CLOCK
    )
    assert effect.promoted == ()
    assert effect.declined == ("previously_withdrawn:demoted",)
    assert _durable(repository) == []
    # ...and the retraction the learner was given still stands, unduplicated.
    assert [
        event["reason"] for event in repository.misconception_dispositions(belief.id)
    ] == ["adjudicated"]


# ── Arm (c): deterministic proof AND learner confirmation ──────────────────


def test_proof_plus_confirmation_promotes(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_c",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    assert _durable(repository) == []

    result = _confirm(vault, repository, "att_c")
    # Confirming resolves the factor, so the open-factor block is satisfied by
    # the confirmation itself rather than being overridden.
    assert result["resolved"] is True

    effect = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_c", clock=CLOCK
    )
    assert len(effect.promoted) == 1
    durable = _durable(repository)
    assert len(durable) == 1
    assert durable[0].promotion_reason == PROMOTION_REASON_PROVED_AND_CONFIRMED
    assert _normalize_text(durable[0].statement) == _normalize_text(STATEMENT)

    # Idempotent on re-drive.
    again = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_c", clock=CLOCK
    )
    assert again.promoted == ()
    assert "already_durable" in again.declined


def test_confirmation_without_a_deterministic_proof_does_not_promote(tmp_path):
    """Half of arm (c) is not arm (c). A self-report is a §2 confirmation
    channel, never an override — §5.6 is explicit that it is "evidence toward
    resolution, never an override"."""

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_c_only",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
        repairs=[_unverified_repair()],
    )
    _confirm(vault, repository, "att_c_only")

    effect = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_c_only", clock=CLOCK
    )
    assert effect.promoted == ()
    assert effect.declined == ("no_deterministic_proof",)
    assert _durable(repository) == []


def test_a_deterministic_proof_without_confirmation_does_not_promote(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_p_only",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    # A verified repair is on the receipt; nobody confirmed anything.
    effect = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_p_only", clock=CLOCK
    )
    assert effect.promoted == ()
    assert effect.declined == ("no_learner_confirmation",)
    assert _durable(repository) == []


def test_the_proof_must_be_about_the_confirmed_belief(tmp_path):
    """The conjunction is not "both happened on this attempt".

    The synthesized open-world arm for the item's OTHER measurement target
    carries no repair class, so the verifier's proof — which is bound to a repair
    class — says nothing about it. Confirming that arm promotes nothing even
    though a verified repair exists on the same attempt.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_other",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    factor = repository.unresolved_cause_factors_for_attempt("att_other")[0]
    other = next(
        position
        for position, cause in enumerate(factor["candidate_causes"])
        if not cause.get("open_set") and str(cause.get("statement")) != STATEMENT
    )
    record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor["id"],
        response="believed_candidate",
        candidate_index=other,
        clock=CLOCK,
    )

    effect = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_other", clock=CLOCK
    )
    assert effect.promoted == ()
    assert "confirmed_belief_has_no_repair_class" in effect.declined
    assert _durable(repository) == []


def test_a_contest_is_not_a_confirmation(tmp_path):
    """Only `believed_candidate` confirms; the other five typed reasons contest."""

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_contest",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    factor = repository.unresolved_cause_factors_for_attempt("att_contest")[0]
    record_unresolved_cause_self_report(
        vault,
        repository,
        factor_id=factor["id"],
        response="diagnosis_wrong",
        clock=CLOCK,
    )

    effect = apply_proved_and_confirmed_promotion(
        vault, repository, attempt_id="att_contest", clock=CLOCK
    )
    assert effect.declined == ("no_learner_confirmation",)
    assert _durable(repository) == []


# ── Wiring: no verdict is ever silently inert ─────────────────────────────


def test_a_verdict_recorded_without_a_vault_is_picked_up_by_the_sweep(tmp_path):
    """The CLI records verdicts with no vault in hand (`learnloop diagnosis
    adjudicate` passes only the repository). The verdict must still reach belief
    state, so the LO sweep is the backstop."""

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_sweep")
    # Exactly the CLI call shape: no vault.
    append_diagnosis_adjudication(
        repository, attempt_id="att_sweep", verdict="correct", clock=CLOCK
    )
    assert _durable(repository) == []

    effects = sweep_late_promotion_evidence(
        vault, repository, learning_object_id=LO_ID, clock=CLOCK
    )
    assert [effect.arm for effect in effects] == ["adjudication"]
    durable = _durable(repository)
    assert len(durable) == 1
    assert durable[0].promotion_reason == PROMOTION_REASON_ADJUDICATED

    # ...and the sweep is itself idempotent: nothing changed means nothing
    # reported, so a later attempt does not re-promote.
    assert sweep_late_promotion_evidence(
        vault, repository, learning_object_id=LO_ID, clock=CLOCK
    ) == []


def test_the_sweep_also_finds_a_confirmation_on_a_superseded_version(tmp_path):
    """The sweep's confirmation scan must see the whole chain, not just heads.

    Recording a confirmation re-materializes the episode, and
    `materialize_causal_episode` rebuilds each hypothesis's evidence from the
    grader plan — so the marker ends up on a version that is no longer current.
    A head-only scan finds nothing and arm (c) goes quiet.
    """

    vault, repository, _paths = _vault(tmp_path)
    _failure(
        vault,
        repository,
        attempt_id="att_c_sweep",
        item_id=AMBIGUOUS_ITEM,
        criterion="whole_item",
    )
    _confirm(vault, repository, "att_c_sweep")
    # The marker is genuinely NOT on the head — that is the condition under test.
    heads = repository.causal_hypotheses_for_attempt("att_c_sweep")
    assert not any(
        (hypothesis.get("evidence") or {}).get("learner_confirmation")
        for hypothesis in heads
    )

    effects = sweep_late_promotion_evidence(
        vault, repository, learning_object_id=LO_ID, clock=CLOCK
    )
    assert [effect.arm for effect in effects] == ["proof_and_confirmation"]
    durable = _durable(repository)
    assert len(durable) == 1
    assert durable[0].promotion_reason == PROMOTION_REASON_PROVED_AND_CONFIRMED


def test_the_sweep_reports_nothing_when_there_is_no_late_evidence(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_none")
    assert (
        sweep_late_promotion_evidence(
            vault, repository, learning_object_id=LO_ID, clock=CLOCK
        )
        == []
    )
    assert _durable(repository) == []


def test_replay_reproduces_the_same_belief_state(tmp_path):
    """A rebuild neither loses nor duplicates an adjudicated promotion.

    `reset_learning_object_derived_state` deletes error events but keeps
    `misconceptions`, the causal chain, and the P1 receipt (an immutable decision
    record). Promotion therefore has to be a fact that survives, not derived
    state that gets recomputed into a second row.
    """

    from learnloop.services.replay import rebuild_derived_state

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_replay")
    append_diagnosis_adjudication(
        repository, attempt_id="att_replay", verdict="correct", vault=vault, clock=CLOCK
    )
    before = _durable(repository)
    assert len(before) == 1

    rebuild_derived_state(vault, repository, clock=CLOCK)

    after = _durable(repository)
    assert [row.id for row in after] == [row.id for row in before]
    assert after[0].promotion_reason == PROMOTION_REASON_ADJUDICATED
    # The verdict is still the active head and still resolves to the same effect.
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_replay", clock=CLOCK
    )
    assert effect.promoted == ()
    assert "already_durable" in effect.declined


def test_a_promoted_belief_is_not_resolved_away_by_the_next_posterior_pass(tmp_path):
    """The late arms do not back-link error events, and that must be harmless.

    `normalize_and_resolve_attempt` runs the sweep and THEN the §7 posterior
    resolver. A promoted belief whose source events carry no `misconception_id`
    registers no "fire" — so if the posterior counted absence as evidence against
    it, arm (c)/(d) would promote a belief and resolve it in the same breath. It
    does not: a fire only counts where a discrimination row exists, and a fresh
    belief has none, so the posterior holds at the severity prior.
    """

    from learnloop.services.misconceptions import (
        misconception_posterior,
        update_misconception_posteriors_and_resolve,
    )

    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_post")
    append_diagnosis_adjudication(
        repository, attempt_id="att_post", verdict="correct", vault=vault, clock=CLOCK
    )
    belief = _durable(repository)[0]
    tau = vault.config.misconceptions.tau_misconception_resolved
    assert misconception_posterior(vault, repository, belief) >= tau

    update_misconception_posteriors_and_resolve(
        vault, repository, learning_object_id=LO_ID, clock=CLOCK
    )
    still = _durable(repository)
    assert [row.id for row in still] == [belief.id]
    assert still[0].status == "active"


def test_no_verdict_is_a_declined_arm_not_a_crash(tmp_path):
    vault, repository, _paths = _vault(tmp_path)
    _failure(vault, repository, attempt_id="att_bare")
    effect = apply_adjudicated_belief_effects(
        vault, repository, attempt_id="att_bare", clock=CLOCK
    )
    assert effect.declined == ("no_verdict",)
    assert effect.changed is False
