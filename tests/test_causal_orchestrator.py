"""P2 causal repair orchestration (contract §6).

Every test here drives a REAL path — ``complete_self_graded_attempt``, the
orchestrator, ``enter_episode``, the follow-up task queue — rather than calling
a pure function with hand-built dicts. The original P2 code passed review while
being unreachable precisely because its tests never went through an integration
path.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.diagnosis.causal_orchestrator import (
    CAUSAL_ORCHESTRATOR_FORMULA_VERSION,
    EVSI_PROVENANCE,
    NEEDS_DISAMBIGUATION_MESSAGE,
    accept_probe_offer,
    causal_repair_status,
    classify_probe_response,
    cold_verification_context,
    defer_probe_offer,
    enqueue_backfill_obligation,
    learner_preference,
    pinned_causal_probe,
    request_teaching_now,
    sweep_machine_checks,
)
from learnloop.diagnosis.causal_probe_coherence import (
    generate_blind_prediction_bundle,
)
from learnloop.diagnosis.followups import evaluate_attempt_intervention_followup
from learnloop.diagnosis.probe_episodes import enter_episode, episode_posterior
from learnloop.diagnosis.remediation import (
    RemediationBlocked,
    prescribe_remediation,
    start_remediation_episode,
    start_remediation_treatment,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import (
    NOW,
    NOW_ISO,
    admit_probe_instrument_card,
)
from tests.causal_orchestrator_helpers import (
    CLOCK,
    LO_ID,
    PROBE_ITEM,
    _activate_probe_candidate,
    _seed_factor,
    _vault,
)

# --- the machine-check arm has a producer AND a consumer ---------------------


def test_live_attempt_queues_a_repair_mapping_backfill_that_self_closes(tmp_path):
    """The machine-check producer runs off a REAL attempt, from the live hook.

    On the live mvp-0.7 path P1 hypotheses are minted with ``repair_class_id``
    null, so every cause set is ``incomplete_repair_mapping``. Missing
    machine-side data must be bought with machine effort, never with a learner
    probe (principle 8) — and before wave 2 nothing consumed that typed
    obligation at all, so both the backfill and the ``deferred_machine_checks``
    arm were inert.
    """

    from tests.km2_write_path_helpers import build_mvp07_vault

    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=CLOCK)
    result = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_ambiguous_001",
            learner_answer_md="An answer.",
        ),
        SelfGradeInput(criterion_points={"whole_item": 0}, fatal_errors=[], confidence=4),
        clock=CLOCK,
    )
    factor = repository.unresolved_cause_factors_for_attempt(result.attempt_id)[0]
    concrete = [
        value for value in factor["candidate_causes"] if not value.get("open_set")
    ]
    assert concrete, "the live path must mint concrete P1 hypotheses"
    assert all(value.get("repair_class_id") is None for value in concrete)

    assert repository.causal_machine_checks(status="pending") == []
    evaluate_attempt_intervention_followup(
        vault, repository, result=result, clock=CLOCK
    )
    pending = repository.causal_machine_checks(status="pending")
    assert [check["kind"] for check in pending] == ["repair_class_mapping_backfill"]
    assert pending[0]["factor_id"] == factor["id"]
    assert pending[0]["payload"]["learner_actionable"] is False
    assert sorted(pending[0]["payload"]["hypothesis_ids"]) == sorted(
        str(value["hypothesis_id"]) for value in concrete
    )

    # The queue self-closes when the obligation goes away, so the arm can never
    # become a permanent block.
    repository.resolve_unresolved_cause_factor(
        factor["id"], resolution_observation_ids=[], clock=CLOCK
    )
    remaining = sweep_machine_checks(vault, repository, LO_ID, clock=CLOCK)
    assert remaining == []
    closed = repository.causal_machine_check(pending[0]["id"])
    assert closed["status"] == "resolved"
    assert closed["resolution"]["basis"] == "obligation_no_longer_present"


def test_unmapped_hypothesis_defers_the_repair_behind_a_machine_check(tmp_path):
    """`deferred_machine_checks` is reachable, blocking, and recorded."""

    vault, repository, _root = _vault(tmp_path)
    factor_id, first_id, second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair=None
    )

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status == "deferred_machine_checks"
    assert status.probe_decision == "defer_machine_checks"
    assert status.episode is None
    assert status.actions == ()
    assert status.pending_machine_check_ids

    pending = repository.causal_machine_checks(status="pending")
    assert [check["kind"] for check in pending] == ["repair_class_mapping_backfill"]
    assert pending[0]["payload"]["hypothesis_ids"] == [second_id]
    # A queue entry that cannot be routed is not a queue: carry the typed
    # unresolved reason (migration 125) with the obligation.
    assert set(pending[0]["payload"]["unresolved_reasons"]) == {second_id}

    # A negative decision, persisted rather than thrown away.
    receipts = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert [receipt["decision"] for receipt in receipts] == ["defer_machine_checks"]
    assert receipts[0]["repair_status"] == "deferred_machine_checks"
    assert receipts[0]["formula_version"] == CAUSAL_ORCHESTRATOR_FORMULA_VERSION
    assert receipts[0]["parameters"]["probe_policy"]["scope"] == "causal_probe_policy"
    assert receipts[0]["machine_check_ids"] == list(status.pending_machine_check_ids)

    # The hold surfaces through the legacy entrypoint as a typed status.
    with pytest.raises(RemediationBlocked) as blocked:
        start_remediation_episode(repository, first_id, vault=vault, clock=CLOCK)
    assert blocked.value.status == "deferred_machine_checks"

    # Re-asking is idempotent on the queue (content-hashed obligation) but still
    # appends a second decision record: frequency is the P4 signal.
    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)
    assert len(repository.causal_machine_checks(status="pending")) == 1
    decisions = repository.causal_probe_decision_receipts(factor_id=factor_id)
    # Three asks (status, start_remediation_episode, status) -> three records.
    assert len(decisions) == 3
    assert len({receipt["decision_fingerprint"] for receipt in decisions}) == 1


# --- negative decisions are the majority class and are all persisted --------


def test_a_common_repair_cover_serves_the_repair_and_records_the_skip(tmp_path):
    vault, repository, _root = _vault(tmp_path)
    factor_id, first_id, _second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status == "safe_common_repair_available"
    assert status.probe_decision == "skip_common_repair"
    assert status.common_repair_class_id == "repair:recall"
    assert status.episode is not None
    assert status.actions == ()

    receipts = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert [receipt["decision"] for receipt in receipts] == ["skip_common_repair"]
    assert receipts[0]["repair_class_ids"] == ["repair:recall"]
    # The repair episode really opened through the same call.
    episode = repository.remediation_episode(status.episode["id"])
    assert episode is not None and episode["case_ref"] == first_id


def test_a_stale_backfill_check_cannot_wedge_a_now_mapped_factor(tmp_path):
    """Once the mapping lands, the queue entry must not keep blocking."""

    vault, repository, _root = _vault(tmp_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    stale = enqueue_backfill_obligation(
        repository,
        {
            "kind": "repair_class_mapping_backfill",
            "factor_id": factor_id,
            "attempt_id": "att_orchestrator",
            "hypothesis_ids": [second_id],
            "learner_actionable": False,
        },
        learning_object_id=LO_ID,
        source="test_stale",
        clock=CLOCK,
    )
    assert stale["status"] == "pending"

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status != "deferred_machine_checks"
    closed = repository.causal_machine_check(stale["id"])
    assert closed["status"] == "resolved"
    assert closed["resolution"]["basis"] == "repair_mapping_resolved"


def test_a_status_read_records_the_decision_without_minting_an_episode(tmp_path):
    vault, repository, _root = _vault(tmp_path)
    factor_id, first_id, _second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )

    status = causal_repair_status(
        vault,
        repository,
        misconception_id=first_id,
        start_repair=False,
        clock=CLOCK,
    )
    assert status.status == "safe_common_repair_available"
    assert status.repair_permitted is True
    assert status.episode is None
    # The decision is still recorded — the negatives are the P4 training data.
    assert repository.causal_probe_decision_receipts(factor_id=factor_id)


def test_divergent_causes_without_a_reviewed_instrument_block_pending_review(
    tmp_path,
):
    vault, repository, _root = _vault(tmp_path)
    factor_id, first_id, _second_id = _seed_factor(repository)

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status == "blocked_pending_review"
    assert status.reason == "no_discriminating_instrument"
    assert status.episode is None
    # No instrument means no information at any price -- the decision says so.
    assert status.probe_decision == "skip_no_discrimination"
    receipts = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert receipts[0]["inputs"]["instrument_available"] is False


# --- the offer, the pin, and "Not now" --------------------------------------


def test_reviewed_active_candidate_produces_the_disambiguation_offer(tmp_path):
    vault, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    minted = _activate_probe_candidate(repository, factor_id, first_id, second_id)

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status == "needs_disambiguation"
    assert status.probe_decision == "probe_now"
    assert status.probe_offered is True
    assert status.message == NEEDS_DISAMBIGUATION_MESSAGE
    assert [action.id for action in status.actions] == [
        "take_quick_check",
        "teach_me_now",
        "not_now",
    ]
    assert status.candidate_id == minted["candidate"]["id"]
    assert set(status.blind_bundle_ids) == set(
        minted["candidate"]["blind_bundle_ids"]
    )
    assert status.episode is None
    # Real EVSI inputs, not placeholders: one separable pair across two
    # different repair classes.
    receipt = repository.causal_probe_decision_receipts(factor_id=factor_id)[0]
    assert receipt["inputs"]["expected_information_gain"] == 1.0
    assert receipt["inputs"]["probability_information_changes_repair"] == 1.0
    assert receipt["inputs"]["avoided_overteaching_minutes"] > 0.0


def test_evsi_inputs_are_computed_and_carry_their_provenance(tmp_path):
    """Standing constraint 4: deterministic quantities outrank model-reported ones.

    ``decide_probe`` takes the two information terms as caller-supplied floats,
    and the orchestrator is the caller. Both come from the recorded blind-bundle
    separability and the repair-class structure — never from a model. The one
    model-sourced number (`expected_minutes` off an authored repair suggestion)
    is labelled as such and can only ever multiply the deterministic terms.
    """

    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    provenance = status.evsi_provenance
    assert provenance["expected_information_gain"] == "deterministic"
    assert provenance["probability_information_changes_repair"] == "deterministic"
    assert provenance["learner_preference"] == "deterministic"
    assert provenance["recent_diagnostic_burden"] == "deterministic"
    # No repair-class `expected_minutes` was authored, so the teaching cost is
    # the pinned fallback -- said out loud, not passed off as computed.
    assert provenance["avoided_overteaching_minutes"] == "heuristic_default"
    # The instrument card declares its own expected seconds -- an authored
    # family-template constant. Reading it is deterministically reproducible,
    # but the receipt records the epistemic SOURCE (decision-value spec §4.1):
    # authored, not computed.
    assert provenance["probe_burden_minutes"] == "authored_prior"
    assert set(provenance.values()) <= set(EVSI_PROVENANCE)

    receipt = repository.causal_probe_decision_receipts(factor_id=factor_id)[0]
    assert receipt["inputs"]["evsi_provenance"] == provenance
    assert receipt["inputs"]["separable_pairs"] == 1
    assert receipt["inputs"]["inseparable_pairs"] == 0
    # §10.1 receipt contract: the decision states how the prior was formed,
    # whether likelihood coverage is complete, and which loss regime priced it.
    assert receipt["inputs"]["likelihood_completeness"]["complete"] is True
    assert receipt["inputs"]["loss_table_regime"] == "p2_pairwise_proxy_no_loss_table"
    assert "prior_basis" in receipt["inputs"]


def test_inseparable_bundles_yield_a_computed_zero_information_gain(tmp_path):
    """A provably inseparable instrument is worth nothing at any teaching cost."""

    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    minted = _activate_probe_candidate(repository, factor_id, first_id, second_id)

    # Re-point the ACTIVE candidate at a discrimination record whose pairs are
    # inseparable under the real matcher, exactly as `blind_bundle_discrimination`
    # would report for two bundles sharing every declared key.
    inseparable = dict(minted["candidate"]["discrimination"])
    inseparable["separable_pairs"] = []
    inseparable["inseparable_pairs"] = [sorted([first_id, second_id])]
    with repository.connection() as connection:
        connection.execute(
            "UPDATE causal_probe_candidates SET discrimination_json = ? WHERE id = ?",
            (__import__("json").dumps(inseparable), minted["candidate"]["id"]),
        )
        connection.commit()

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    receipt = repository.causal_probe_decision_receipts(factor_id=factor_id)[0]
    assert receipt["inputs"]["expected_information_gain"] == 0.0
    assert receipt["inputs"]["evsi_provenance"]["expected_information_gain"] == (
        "deterministic"
    )
    # ...and no probe is bought, however large the claimed avoided teaching.
    assert status.probe_decision == "skip_no_discrimination"
    assert status.status == "started"


def test_not_now_persists_and_the_next_call_does_not_reoffer(tmp_path):
    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    offered = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert offered.probe_offered is True

    defer_probe_offer(repository, factor_id=factor_id, clock=CLOCK)
    assert learner_preference(repository, factor_id=factor_id) == "decline"

    again = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    # The causes still diverge, but the OFFER is withdrawn -- that is what
    # "Not now" means. Before wave 2 `learner_preference` had no store at all,
    # so a decline re-offered itself on the very next attempt.
    assert again.status == "needs_disambiguation"
    assert again.probe_offered is False
    assert again.probe_decision == "defer_learner_preference"
    assert [action.id for action in again.actions] == ["teach_me_now"]

    decisions = [
        receipt["decision"]
        for receipt in repository.causal_probe_decision_receipts(factor_id=factor_id)
    ]
    assert decisions == ["probe_now", "defer_learner_preference"]


def test_teach_me_now_starts_the_repair_under_recorded_authorisation(tmp_path):
    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    status = request_teaching_now(
        vault,
        repository,
        misconception_id=first_id,
        factor_id=factor_id,
        clock=CLOCK,
    )
    assert status.status == "started"
    assert status.reason == "learner_requested_teaching_without_probe"
    assert status.episode is not None
    assert learner_preference(repository, factor_id=factor_id) == "teach_now"


def test_relocking_an_open_episode_does_not_inherit_its_evidence(tmp_path):
    """The precondition that makes the relock honest, pinned.

    An open episode with no observations is relocked onto the cause set rather
    than refusing the offer (otherwise the placement episode vault state sync
    opens for every LO makes the journey unreachable). What must NOT happen is
    the new set inheriting evidence gathered under the old one:
    `episode_posterior` scopes replay by `entered_at`, so a relock that left
    `entered_at` behind would replay the pre-relock attempts — including the one
    the cause hypotheses were derived from — as independent evidence FOR those
    hypotheses.
    """

    later = FrozenClock(NOW + timedelta(days=1))
    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    plain = enter_episode(vault, repository, LO_ID, trigger="initial", clock=CLOCK)
    assert plain.status == "in_progress"
    # Ordinary practice inside the open placement episode: incidental evidence
    # under ITS locked set. On the LO's ordinary item, NOT the probe item — an
    # administration of the probe surface itself would (correctly) trip the
    # never-before-seen probe gate and leave the relock with no instrument.
    complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(practice_item_id="pi_svd_define_001", learner_answer_md="U Sigma Q"),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=3),
        clock=CLOCK,
    )

    offer = accept_probe_offer(
        vault, repository, factor_id=factor_id, clock=later
    )
    assert offer.accepted, offer.reason
    assert offer.episode_id == plain.id

    relocked = repository.probe_episode(plain.id)
    assert relocked.entered_at != plain.entered_at
    posterior = episode_posterior(vault, repository, relocked)
    assert posterior.total_observations == 0
    # The causal set is still at its prior: nothing recorded under the previous
    # lock was replayed into it.
    assert posterior.posterior == pytest.approx(posterior.prior)


def test_accepting_the_offer_enters_a_factor_aware_episode_with_pinned_bundles(
    tmp_path,
):
    """`enter_episode(causal_factor_id=...)` had zero callers anywhere."""

    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    minted = _activate_probe_candidate(repository, factor_id, first_id, second_id)

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    offer = accept_probe_offer(
        vault,
        repository,
        factor_id=factor_id,
        decision_receipt_id=status.decision_receipt_id,
        clock=CLOCK,
    )
    assert offer.accepted, offer.reason
    episode = repository.probe_episode(offer.episode_id)
    assert episode is not None
    assert episode.origin == f"causal_factor:{factor_id}"
    # The episode locked the CAUSAL hypothesis set, open-set arm included.
    locked = repository.fetch_hypothesis_set(episode.hypothesis_set_id)
    labels = [value["label"] for value in locked["hypotheses"]]
    assert set(labels) == {first_id, second_id, "other_or_unknown"}

    pinned = pinned_causal_probe(repository, offer.presentation_id)
    assert pinned["causal_probe_candidate_id"] == minted["candidate"]["id"]
    assert set(pinned["blind_bundle_ids"]) == set(
        minted["candidate"]["blind_bundle_ids"]
    )
    assert pinned["decision_receipt_id"] == status.decision_receipt_id

    classified = classify_probe_response(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"uses_transpose": False},
    )
    assert classified["outcome"] == "matched_single"
    assert classified["classified_as"] == [first_id]
    assert classified["causal_factor_id"] == factor_id

    # A newer bundle for the same hypothesis must not rewrite this replay: the
    # presentation pinned the instrument when the probe was minted.
    newer = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=first_id,
        item={"id": PROBE_ITEM, "prompt": "Choose the valid final factor."},
        rubric={"criteria": [{"id": "correctness"}]},
        trace_contract=None,
        generator=lambda _safe: {"predicted_features": {"uses_transpose": True}},
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=FrozenClock(NOW + timedelta(days=1)),
    )
    assert newer["id"] not in pinned["blind_bundle_ids"]
    replayed = classify_probe_response(
        repository,
        presentation_id=offer.presentation_id,
        observed_features={"uses_transpose": False},
    )
    assert replayed["classified_as"] == classified["classified_as"]


def test_a_router_decided_pin_names_its_router_decision_not_a_causal_receipt(tmp_path):
    """Refactor B6 (break 4): FG1 passed its router decision as ``decision_receipt_id``, the learner lane's causal
    receipt. Each meaning has its own parameter and key now; the learner lane's pin is unchanged (above)."""

    vault, repository, _root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository)
    admit_probe_instrument_card(repository, items=(PROBE_ITEM,))
    _activate_probe_candidate(repository, factor_id, first_id, second_id)

    offer = accept_probe_offer(
        vault, repository, factor_id=factor_id, router_decision_id="RD_ROUTER_1",
        followup_workflow_id="WF_1", clock=CLOCK,
    )
    assert offer.accepted, offer.reason
    pinned = pinned_causal_probe(repository, offer.presentation_id)
    assert pinned["router_decision_id"] == "RD_ROUTER_1" and pinned["followup_workflow_id"] == "WF_1"
    assert "decision_receipt_id" not in pinned


# --- §6.2 cold verification rides the follow-up task ------------------------


def test_cold_verification_is_carried_through_the_followup_task(tmp_path):
    vault, repository, root = _vault(tmp_path, with_probe_item=True)
    factor_id, first_id, _second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )
    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    assert status.status == "safe_common_repair_available"
    episode_id = status.episode["id"]
    prescribe_remediation(vault, repository, episode_id, clock=CLOCK)
    treatment = start_remediation_treatment(
        vault, repository, episode_id, clock=CLOCK
    )
    assert treatment["primed_item_id"] != treatment["cold_item_id"]

    primed = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=treatment["primed_item_id"],
            learner_answer_md="U Sigma Q",
            primed=True,
        ),
        SelfGradeInput(criterion_points={"correctness": 0}, confidence=4),
        clock=CLOCK,
    )
    task = repository.active_followup_task_for_item(
        treatment["cold_item_id"], at=NOW_ISO
    )
    if task is None:
        task = next(
            value
            for value in repository.due_followup_tasks(
                clock=FrozenClock(NOW + timedelta(days=2))
            )
            if value["kind"] == "cold_retry"
        )
    # §6.2: the inputs travel WITH the task rather than being reconstructed.
    context = task["context"]
    assert context["kind"] == "causal_cold_verification"
    assert context["source_attempt_id"] == primed.attempt_id
    assert context["repair_class_id"] == "repair:recall"
    assert first_id in context["hypothesis_ids"]
    assert context["avoided_affordances"]

    cold = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id=treatment["cold_item_id"],
            learner_answer_md="U Sigma V^T",
        ),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    evaluate_attempt_intervention_followup(
        vault,
        repository,
        result=cold,
        clock=FrozenClock(NOW + timedelta(days=2)),
    )
    verification = repository.causal_cold_verification_for_attempt(cold.attempt_id)
    assert verification is not None
    assert verification["source_attempt_id"] == primed.attempt_id
    assert verification["repair_class_id"] == "repair:recall"
    assert verification["success"] is True
    # Repair success never moves the diagnosis (§6.2 / §7).
    assert verification["diagnosis_support_update"]["delta"] == 0.0


def test_cold_verification_context_names_the_avoided_affordances(tmp_path):
    vault, repository, _root = _vault(tmp_path)
    _factor_id, first_id, _second_id = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )
    episode = {
        "case_kind": "diagnosis",
        "case_ref": first_id,
        "passages_shown": [{"role": "target"}],
    }
    context = cold_verification_context(
        vault,
        repository,
        episode=episode,
        source_attempt={
            "id": "att_primed",
            "practice_item_id": "pi_svd_define_001",
            "hints_used": 2,
        },
    )
    assert context["repair_class_id"] == "repair:recall"
    assert "hints" in context["avoided_affordances"]
    assert "primed_repair_context" in context["avoided_affordances"]
    assert "remediation_passages" in context["avoided_affordances"]
    assert any(
        value.startswith("surface_family:")
        for value in context["avoided_affordances"]
    )
