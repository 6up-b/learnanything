from __future__ import annotations

import sqlite3
from datetime import timedelta

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis.causal_probe_coherence import (
    BundleFeatureRow,
    audit_manipulation_contract,
    blind_bundle_discrimination,
    build_causal_hypothesis_set,
    classify_against_blind_bundles,
    create_probe_candidate,
    decide_probe,
    generate_blind_prediction_bundle,
    lock_causal_hypothesis_set,
    parse_bundle_feature_rows,
    record_delayed_cold_verification,
    repair_class_need_for_factor,
    rows_are_separable,
    rung_divergence_gate,
    transition_probe_candidate,
)
from learnloop.diagnosis import failure_triage as FT
from learnloop.diagnosis.remediation import (
    RemediationBlocked,
    RemediationError,
    start_remediation_episode,
)
from learnloop.attempts.attempts import (
    AttemptDraft,
    SelfGradeInput,
    complete_self_graded_attempt,
)
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, add_followup_item, create_basic_vault


def _seed_factor(repository: Repository) -> tuple[str, str, str]:
    common = {
        "attempt_id": "att_p2_factor",
        "learning_object_id": "lo_svd_definition",
        "cause_scope": "learner_state",
        "target_ref": {"kind": "criterion", "criterion_id": "correctness"},
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "postdictive_claims": [],
        "evidence": {"trace_consistent": True},
        "status": "candidate",
        "clock": FrozenClock(NOW),
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key="att_p2_factor:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        repair_class_id="repair:recall",
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key="att_p2_factor:second",
        statement="The learner selected the wrong factorization convention.",
        statement_normalized=(
            "the learner selected the wrong factorization convention"
        ),
        operation="method_selection",
        repair_class_id="repair:method",
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id="att_p2_factor",
        candidate_causes=[
            {
                "hypothesis_id": first["id"],
                "version": first["version"],
            },
            {
                "hypothesis_id": second["id"],
                "version": second["version"],
            },
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=FrozenClock(NOW),
    )
    return factor_id, str(first["id"]), str(second["id"])


def test_evsi_rule_is_action_relative_and_budgeted():
    same = decide_probe(
        repair_class_ids=["repair:a", "repair:a"],
        common_repair_covers=False,
        expected_information_gain=1.0,
        probability_information_changes_repair=1.0,
        probe_burden_minutes=1,
        avoided_overteaching_minutes=20,
    )
    assert same.decision == "skip_action_equivalent"

    pending = decide_probe(
        repair_class_ids=["repair:a", "repair:b"],
        common_repair_covers=False,
        expected_information_gain=1.0,
        probability_information_changes_repair=1.0,
        probe_burden_minutes=1,
        avoided_overteaching_minutes=20,
        pending_machine_checks=["regrade"],
    )
    assert pending.decision == "defer_machine_checks"

    worth_it = decide_probe(
        repair_class_ids=["repair:a", "repair:b"],
        common_repair_covers=False,
        expected_information_gain=0.8,
        probability_information_changes_repair=0.75,
        probe_burden_minutes=2,
        avoided_overteaching_minutes=10,
    )
    assert worth_it.decision == "probe_now"
    # What a divergent factor holds is the BRANCH-SPECIFIC repair inside it, not
    # "unrelated remediation" elsewhere (the field was renamed with the copy).
    assert worth_it.blocks_branch_specific_repair
    # The EVSI knobs are resolved parameters, and the receipt carries the
    # manifest that produced the decision.
    manifest = worth_it.parameters
    assert manifest["scope"] == "causal_probe_policy"
    assert manifest["lifecycle"] == "heuristic_default"
    assert manifest["values"]["recent_diagnostic_limit"] == 2.0
    assert worth_it.decision_policy_version == "causal_p2_v1"


def test_triage_signature_authority_is_an_and_gate_not_a_replacement():
    """Causal support VETOES freely but PROMOTES only under an approved authority.

    The previous contract encoded here ("a receipt replaces the legacy route") made
    tier one unreachable in production: single-attempt receipts carry all-``None``
    support scores by design, so the causal arm never fired and the legacy arm was
    skipped."""

    # A production single-attempt receipt: no validator-owned support, no falsifiable
    # claims. It must NOT silently downgrade an otherwise-decisive legacy route.
    single_attempt_receipt = {
        "support_authority": "unavailable_single_attempt",
        "hypotheses": [
            {
                "hypothesis_id": "h_method",
                "triage_reason": "method_selection",
                "support_score": None,
                "trace_consistency": "no_deterministic_claims",
            }
        ],
    }
    reason, basis = FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.99},
        {},
        causal_support=single_attempt_receipt,
        causal_support_available=True,
    )
    assert (reason, basis) == ("method_selection", FT.TIER_ONE_BASIS_LEGACY)

    # A contradicted deterministic claim on the routed reason vetoes it.
    contradicted = FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.99},
        {},
        causal_support={
            "support_authority": "unavailable_single_attempt",
            "hypotheses": [
                {
                    "hypothesis_id": "h_method",
                    "triage_reason": "method_selection",
                    "support_score": None,
                    "trace_consistency": "contradicted",
                }
            ],
        },
        causal_support_available=True,
    )
    assert contradicted == (None, None)

    # Approved, complete, dominant, trace-consistent support promotes on its own --
    # grader confidence is irrelevant to the causal arm.
    promoted = FT._decisive_route(
        {"error_signature": "wrong_method", "grader_confidence": 0.1},
        {},
        causal_support={
            "support_authority": "validator_owned",
            "hypotheses": [
                {
                    "hypothesis_id": "h_method",
                    "triage_reason": "method_selection",
                    "support_score": 0.9,
                    "trace_consistency": "consistent_with_claims",
                },
                {
                    "hypothesis_id": "h_execution",
                    "triage_reason": "procedure_execution",
                    "support_score": 0.1,
                    "trace_consistency": "consistent_with_claims",
                },
            ],
        },
        causal_support_available=True,
    )
    assert promoted == ("method_selection", FT.TIER_ONE_BASIS_CAUSAL)


def test_repair_class_divergence_locks_existing_hypothesis_set_with_other(
    tmp_path,
):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)

    need = repair_class_need_for_factor(repository, factor_id)
    assert need["repair_class_ids"] == ["repair:method", "repair:recall"]
    assert need["high_priority_diagnostic_need"]
    # Wave 2: the raw block is now the typed `causal_repair_status` union. The
    # divergent factor has no reviewed-active discriminating instrument, so the
    # branch-specific repair is held pending review rather than served blind.
    with pytest.raises(RemediationBlocked) as blocked:
        start_remediation_episode(
            repository, first_id, clock=FrozenClock(NOW)
        )
    assert blocked.value.status == "blocked_pending_review"
    assert isinstance(blocked.value, RemediationError)

    unlocked = build_causal_hypothesis_set(repository, factor_id)
    assert [value.label for value in unlocked.hypotheses] == [
        first_id,
        second_id,
        "other_or_unknown",
    ]
    # With no support score on any arm -- which is every set produced today --
    # the uniform prior is an AUTHORED fallback and must say so.
    assert unlocked.prior_basis == "uniform_fallback"
    weighted = build_causal_hypothesis_set(
        repository, factor_id, support_scores={first_id: 0.9, second_id: 0.1}
    )
    assert weighted.prior_basis == "support_weighted"
    assert weighted.prior[first_id] > weighted.prior[second_id]

    locked = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id="phase_p2",
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )
    stored = repository.fetch_hypothesis_set(str(locked.id))
    assert stored["hypotheses"][-1]["label"] == "other_or_unknown"
    assert stored["prior_basis"] == "uniform_fallback"
    # The locked set pins the hypothesis VERSION classification must replay at.
    assert stored["hypotheses"][0]["causal_hypothesis_version"] == 1


def test_blind_bundles_diff_audit_and_review_ladder(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id="phase_review",
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )
    source = {
        "id": "pi_source",
        "prompt": "State the SVD.",
        "expected_answer": "U Sigma V^T",
        "practice_mode": "short_answer",
        "difficulty": 0.5,
        "evidence_facets": ["recall"],
        "evidence_weights": {"recall": 1.0},
        "grading_rubric": {"criteria": [{"id": "correctness"}]},
        "task_features": {"transfer_distance": "near"},
    }
    candidate = {
        **source,
        "id": "pi_causal_probe",
        "prompt": "Choose which final factor makes the product valid.",
        "variant_contract": {
            "variant_kind": "rung_shift",
            "intended_manipulations": [
                {"axis": "surface_wording", "direction": "increase"}
            ],
            "incidental_changes": [],
            "held_constant": [
                "answer_contract",
                "rubric",
                "measurement_targets",
            ],
        },
    }

    seen_inputs = []

    def first_generator(safe_input):
        seen_inputs.append(safe_input)
        return {"predicted_features": {"uses_transpose": False}}

    first_bundle = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=first_id,
        item=candidate,
        rubric=candidate["grading_rubric"],
        trace_contract=None,
        generator=first_generator,
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=FrozenClock(NOW),
    )
    second_bundle = generate_blind_prediction_bundle(
        repository,
        hypothesis_id=second_id,
        item=candidate,
        rubric=candidate["grading_rubric"],
        trace_contract=None,
        generator=lambda _safe: {
            "predicted_features": {"uses_transpose": True}
        },
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=FrozenClock(NOW),
    )
    assert seen_inputs
    assert "learner_answer" not in str(seen_inputs[0])
    assert "postdictive_claims" not in str(seen_inputs[0])
    assert seen_inputs[0]["hypothesis"]["target_ref"] is not None
    assert first_bundle["generated_without_observation"]
    classified = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=[first_bundle["id"], second_bundle["id"]],
        observed_features={"uses_transpose": False},
    )
    assert classified["classified_as"] == [first_id]
    assert classified["outcome"] == "matched_single"
    assert classified["basis"] == "blind_prediction_bundles_only"
    assert classified["cohort"] == {
        "model_revision": "model-r1",
        "outcome_schema_version": "probe-outcome-v1",
    }
    # A pinned id that does not resolve is an error, never a silent fallback to
    # "whatever bundle is newest".
    with pytest.raises(ValueError, match="does not resolve"):
        classify_against_blind_bundles(
            repository,
            hypothesis_set_id=str(locked.id),
            practice_item_id="pi_causal_probe",
            blind_bundle_ids=["bpb_missing"],
            observed_features={"uses_transpose": False},
        )

    audit = audit_manipulation_contract(
        repository,
        source_item=source,
        candidate_item=candidate,
        source_kind="causal_probe",
        adversarial_review={
            "contract_consistent": True,
            "measurement_target_independence": True,
            "undeclared_differences": [],
        },
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    assert audit["status"] == "passed"
    self_review = audit_manipulation_contract(
        repository,
        source_item=source,
        candidate_item=candidate,
        source_kind="causal_probe",
        adversarial_review={
            "contract_consistent": True,
            "measurement_target_independence": True,
            "undeclared_differences": [],
        },
        generation_agent_run_id="same_agent",
        reviewer_agent_run_id="same_agent",
        clock=FrozenClock(NOW),
    )
    assert self_review["status"] == "rejected"

    probe = create_probe_candidate(
        repository,
        factor_id=factor_id,
        practice_item_id="pi_causal_probe",
        hypothesis_set_id=str(locked.id),
        manipulation_audit_id=audit["id"],
        measurement_contract={
            "independently_compiled": True,
            "inherited_parent_facet_weights": False,
            "criteria": [
                {
                    "criterion_id": "correctness",
                    "target_ref": {
                        "kind": "criterion",
                        "criterion_id": "correctness",
                    },
                }
            ],
        },
        clock=FrozenClock(NOW),
    )
    assert set(probe["blind_bundle_ids"]) == {
        first_bundle["id"],
        second_bundle["id"],
    }
    for status, reviewer in (
        ("registered", None),
        ("reviewed", "owner"),
        ("active", None),
    ):
        probe = transition_probe_candidate(
            repository,
            probe["id"],
            to_status=status,
            reviewer=reviewer,
            clock=FrozenClock(NOW),
        )
    assert probe["status"] == "active"
    assert [
        value["to_status"]
        for value in repository.causal_probe_candidate_events(probe["id"])
    ] == ["candidate", "registered", "reviewed", "active"]

    with repository.connection() as connection:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute(
                """
                UPDATE causal_blind_prediction_bundles
                   SET model_revision = 'rewritten'
                 WHERE id = ?
                """,
                (first_bundle["id"],),
            )


def test_cold_success_updates_repair_effect_not_diagnosis(tmp_path):
    root = tmp_path / "vault"
    paths = create_basic_vault(root)
    add_followup_item(root)
    vault = load_vault(root)
    repository = Repository(paths.sqlite_path)
    source = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_001",
            learner_answer_md="U Sigma Q",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 0}, confidence=4
        ),
        clock=FrozenClock(NOW),
    )
    cold = complete_self_graded_attempt(
        vault,
        repository,
        AttemptDraft(
            practice_item_id="pi_svd_define_002",
            learner_answer_md="U Sigma V^T",
        ),
        SelfGradeInput(
            criterion_points={"correctness": 4}, confidence=5
        ),
        clock=FrozenClock(NOW + timedelta(days=2)),
    )

    receipt = record_delayed_cold_verification(
        vault,
        repository,
        source_attempt_id=source.attempt_id,
        cold_attempt_id=cold.attempt_id,
        repair_class_id="repair:transpose",
        hypothesis_ids=["hypothesis:transpose"],
        avoided_affordances=["single-letter-q-notation"],
        clock=FrozenClock(NOW + timedelta(days=2)),
    )

    assert receipt["success"]
    assert receipt["repair_effect_support"]["success"] is True
    # The success cut is a resolved fitted-store parameter, not a literal.
    assert receipt["repair_effect_support"]["success_threshold"] == 0.8
    assert (
        receipt["repair_effect_support"]["parameters"]["lifecycle"]
        == "heuristic_default"
    )
    assert receipt["diagnosis_support_update"]["delta"] == 0.0
    activity = repository.causal_activity_classification(cold.attempt_id)
    assert activity["contamination_class"] == "verification"
    assert activity["eligible_for_certification"] is True

    # A "delayed" verification that is not later than its source is a wiring or
    # replay-ordering bug, never evidence of durable transfer.
    with pytest.raises(ValueError, match="chronologically later"):
        record_delayed_cold_verification(
            vault,
            repository,
            source_attempt_id=cold.attempt_id,
            cold_attempt_id=source.attempt_id,
            repair_class_id="repair:transpose",
            hypothesis_ids=["hypothesis:transpose"],
            avoided_affordances=["single-letter-q-notation"],
            clock=FrozenClock(NOW + timedelta(days=2)),
        )


# --- P2 blind-bundle coherence (contract §3) --------------------------------


def _bundle(
    repository,
    hypothesis_id,
    predictions,
    *,
    item_id="pi_causal_probe",
    model_revision="model-r1",
    outcome_schema_version="probe-outcome-v1",
    clock=None,
):
    return generate_blind_prediction_bundle(
        repository,
        hypothesis_id=hypothesis_id,
        item={"id": item_id, "prompt": "Choose the valid final factor."},
        rubric={"criteria": [{"id": "correctness"}]},
        trace_contract=None,
        generator=lambda _safe: predictions,
        model_revision=model_revision,
        outcome_schema_version=outcome_schema_version,
        clock=clock or FrozenClock(NOW),
    )


def _locked_set(repository, factor_id, phase):
    return lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id=phase,
        algorithm_version="test",
        clock=FrozenClock(NOW),
    )


def test_empty_feature_row_is_rejected_at_generation_and_skipped_at_read(
    tmp_path,
):
    """An empty declared key set matches every observation vacuously."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = _locked_set(repository, factor_id, "phase_empty_row")

    with pytest.raises(ValueError, match="empty feature row"):
        _bundle(repository, first_id, {"predicted_features": {}})

    # A row that carries no declared keys is skipped with a typed reason at
    # read time rather than matching everything.
    hand_written = repository.insert_causal_blind_prediction_bundle(
        bundle_id="bpb_hand_written_empty",
        hypothesis_id=first_id,
        hypothesis_version=1,
        practice_item_id="pi_causal_probe",
        input_hash="hash_hand_written",
        predictions={"predicted_features": {}, "prose": "looks plausible"},
        model_revision="model-r1",
        outcome_schema_version="probe-outcome-v1",
        clock=FrozenClock(NOW),
    )
    other = _bundle(repository, second_id, {"predicted_features": {"x": 1}})
    result = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=[hand_written["id"], other["id"]],
        observed_features={"anything": "at all"},
    )
    empty_detail = next(
        value
        for value in result["details"]
        if value["hypothesis_id"] == first_id
    )
    assert empty_detail["matched"] is False
    assert empty_detail["reason"] == "no_declared_feature_rows"
    assert empty_detail["skipped_feature_rows"] == ["empty_feature_row"]
    assert result["evaluable_hypothesis_ids"] == [second_id]
    assert parse_bundle_feature_rows({"predicted_features": {}}) == []


def test_subset_rows_without_a_conflicting_shared_key_are_inseparable(
    tmp_path,
):
    """Full-payload JSON distinctness is not separability under the matcher."""

    subset = BundleFeatureRow(keys=("x",), values={"x": 1})
    superset = BundleFeatureRow(keys=("x", "y"), values={"x": 1, "y": 2})
    disjoint = BundleFeatureRow(keys=("y",), values={"y": 2})
    conflicting = BundleFeatureRow(keys=("x",), values={"x": 2})
    assert not rows_are_separable([subset], [superset])
    assert not rows_are_separable([subset], [disjoint])
    assert rows_are_separable([subset], [conflicting])
    # "Some pair of rows conflicts" is not enough: here (A.x=1, B.x=2) conflicts
    # yet no observation matches exactly one side.
    assert not rows_are_separable([subset, conflicting], [subset, conflicting])
    # Exact matching over the declared key set -- a declared key missing from
    # the observation is not a match.
    assert superset.matches({"x": 1, "y": 2, "z": 9})
    assert not superset.matches({"x": 1})

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    _factor_id, first_id, second_id = _seed_factor(repository)
    _bundle(
        repository,
        first_id,
        {"predicted_features": {"uses_transpose": False}},
    )
    _bundle(
        repository,
        second_id,
        {
            "predicted_features": {"uses_transpose": False, "slow": True},
            "rationale": "a different story, the same discriminating features",
        },
    )
    discrimination = blind_bundle_discrimination(
        repository,
        hypothesis_ids=[first_id, second_id],
        practice_item_id="pi_causal_probe",
    )
    assert discrimination["distinguishable"] is False
    assert discrimination["reason"] == "inseparable_hypothesis_pairs"
    assert discrimination["inseparable_pairs"] == [
        sorted([first_id, second_id])
    ]
    assert discrimination["separable_pairs"] == []


def test_bundles_from_different_cohorts_never_compare(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = _locked_set(repository, factor_id, "phase_cohort")
    first = _bundle(
        repository,
        first_id,
        {"predicted_features": {"uses_transpose": False}},
        model_revision="model-r1",
    )
    second = _bundle(
        repository,
        second_id,
        {"predicted_features": {"uses_transpose": True}},
        model_revision="model-r2",
    )
    discrimination = blind_bundle_discrimination(
        repository,
        hypothesis_ids=[first_id, second_id],
        practice_item_id="pi_causal_probe",
    )
    assert discrimination["distinguishable"] is False
    assert discrimination["reason"] == "cohort_mismatch"
    assert discrimination["cohort"] is None
    assert [value["model_revision"] for value in discrimination["cohorts"]] == [
        "model-r1",
        "model-r2",
    ]

    classified = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=[first["id"], second["id"]],
        observed_features={"uses_transpose": False},
    )
    assert classified["outcome"] == "cohort_mismatch"
    assert classified["classified_as"] == []
    assert classified["supports_open_set"] is False


def test_classification_is_pinned_and_survives_a_newer_bundle(tmp_path):
    """A later bundle must not rewrite an earlier replay (append-only substrate)."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = _locked_set(repository, factor_id, "phase_pinned")
    first = _bundle(
        repository,
        first_id,
        {"predicted_features": {"uses_transpose": False}},
    )
    second = _bundle(
        repository,
        second_id,
        {"predicted_features": {"uses_transpose": True}},
    )
    pinned = [first["id"], second["id"]]
    before = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=pinned,
        observed_features={"uses_transpose": False},
    )
    assert before["classified_as"] == [first_id]

    # A newer bundle for the same hypothesis that would flip the answer.
    newer = _bundle(
        repository,
        first_id,
        {"predicted_features": {"uses_transpose": True}},
        clock=FrozenClock(NOW + timedelta(days=1)),
    )
    assert newer["id"] != first["id"]
    latest = repository.causal_blind_prediction_bundles(
        practice_item_id="pi_causal_probe", hypothesis_ids=[first_id]
    )[-1]
    assert latest["id"] == newer["id"]

    after = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=pinned,
        observed_features={"uses_transpose": False},
    )
    assert after["classified_as"] == before["classified_as"]
    assert after["outcome"] == before["outcome"] == "matched_single"

    # Pinning the newer bundle is a different instrument and may differ.
    repinned = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=[newer["id"], second["id"]],
        observed_features={"uses_transpose": False},
    )
    assert repinned["outcome"] == "no_bundle_matched"


def test_all_bundles_matched_is_not_open_set_evidence(tmp_path):
    """An undiscriminating instrument is not evidence for H_OTHER."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = _locked_set(repository, factor_id, "phase_h_other")
    first = _bundle(
        repository,
        first_id,
        {"predicted_features": {"uses_transpose": False}},
    )
    second = _bundle(
        repository,
        second_id,
        {"predicted_features": {"order_reversed": True}},
    )
    pinned = [first["id"], second["id"]]

    both = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=pinned,
        observed_features={"uses_transpose": False, "order_reversed": True},
    )
    assert both["outcome"] == "all_bundles_matched"
    assert both["ambiguous"] is True
    assert both["supports_open_set"] is False
    assert both["open_set"] is False
    assert sorted(both["classified_as"]) == sorted([first_id, second_id])

    neither = classify_against_blind_bundles(
        repository,
        hypothesis_set_id=str(locked.id),
        practice_item_id="pi_causal_probe",
        blind_bundle_ids=pinned,
        observed_features={"uses_transpose": True, "order_reversed": False},
    )
    assert neither["outcome"] == "no_bundle_matched"
    assert neither["supports_open_set"] is True
    assert neither["classified_as"] == ["other_or_unknown"]


def test_rung_divergence_gate_defers_instead_of_buying_learner_effort(
    tmp_path,
):
    """Missing machine-side mapping routes to backfill, never to a probe."""

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    empty = rung_divergence_gate(repository, [])
    assert empty["state"] == "insufficient_mapping"
    assert empty["probe_worthy"] is False
    assert empty["repair_class_divergence"] is False
    assert empty["common_repair_cover"] is False
    assert empty["requires_repair_mapping_backfill"] is True

    unmapped = rung_divergence_gate(
        repository,
        [
            {"hypothesis_id": "h_mapped", "repair_class_id": "repair:a"},
            {"hypothesis_id": "h_unmapped"},
        ],
    )
    assert unmapped["state"] == "insufficient_mapping"
    assert unmapped["probe_worthy"] is False
    assert unmapped["unresolved_hypothesis_ids"] == ["h_unmapped"]

    divergent = rung_divergence_gate(
        repository,
        [
            {"hypothesis_id": "h_a", "repair_class_id": "repair:a"},
            {"hypothesis_id": "h_b", "repair_class_id": "repair:b"},
        ],
    )
    assert divergent["state"] == "divergent"
    assert divergent["probe_worthy"] is True

    cover = rung_divergence_gate(
        repository,
        [
            {"hypothesis_id": "h_a", "repair_class_id": "repair:a"},
            {"hypothesis_id": "h_b", "repair_class_id": "repair:a"},
        ],
    )
    assert cover["state"] == "common_cover"
    assert cover["probe_worthy"] is False
    assert cover["common_repair_cover"] is True
