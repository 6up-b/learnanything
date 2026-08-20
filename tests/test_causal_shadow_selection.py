"""EVSI-2 — shadow selection receipts, the §6.2 likelihood arms, and the firewall.

The shadow selector rides every live probe decision (§6.6) with ZERO live
authority (§3 invariant 2). These tests drive the REAL path — seeded factors
through ``causal_repair_status`` and the commissioning producer — plus direct
adapter calls for the arms integration cannot cheaply reach (skewed
support-weighted priors, EVPI skip licensing).
"""

from __future__ import annotations

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.diagnosis import causal_diagnostic_selector as CDS
from learnloop.diagnosis import causal_orchestrator as CO
from learnloop.diagnosis.causal_orchestrator import causal_repair_status
from learnloop.diagnosis.causal_probe_coherence import lock_causal_hypothesis_set
from learnloop.diagnosis.causal_probe_commissioning import (
    commission_probe_instrument,
)
from learnloop.diagnosis.causal_selection_audit import causal_selection_readiness
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault

CLOCK = FrozenClock(NOW)
LO_ID = "lo_svd_definition"

PASSING_REVIEW = {
    "contract_consistent": True,
    "measurement_target_independence": True,
    "undeclared_differences": [],
}


def _write_probe_item(paths, item_id: str, *, criteria: list[str]) -> None:
    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": LO_ID,
            "subjects": None,
            "practice_mode": "diagnostic_probe",
            "attempt_types_allowed": ["diagnostic_probe"],
            "evidence_facets": [],
            "prompt": "Which factor makes the product valid?",
            "expected_answer": "The transposed one.",
            "difficulty": 0.4,
            "tags": [],
            "grading_rubric": {
                "max_points": len(criteria),
                "criteria": [
                    {
                        "id": criterion,
                        "points": 1,
                        "description": f"Checks {criterion}.",
                        "measurement_status": "item_local",
                    }
                    for criterion in criteria
                ],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )


def _seed_factor(
    repository: Repository,
    *,
    first_repair: str | None = "repair:recall",
    second_repair: str | None = "repair:method",
    attempt_id: str = "att_shadow",
    with_targets: bool = False,
) -> tuple[str, str, str]:
    common = {
        "attempt_id": attempt_id,
        "learning_object_id": LO_ID,
        "cause_scope": "learner_state",
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "evidence": {"trace_consistent": True},
        "status": "candidate",
        "postdictive_claims": [],
        "clock": CLOCK,
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        target_ref=(
            {"kind": "criterion", "criterion_id": "criterion_recall"}
            if with_targets
            else {"kind": "criterion", "criterion_id": "correctness"}
        ),
        repair_class_id=first_repair,
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key=f"{attempt_id}:second",
        statement="The learner selected the wrong convention.",
        statement_normalized="the learner selected the wrong convention",
        operation="method_selection",
        target_ref=(
            {"kind": "criterion", "criterion_id": "criterion_method"}
            if with_targets
            else {"kind": "criterion", "criterion_id": "correctness"}
        ),
        repair_class_id=second_repair,
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id=attempt_id,
        candidate_causes=[
            {"hypothesis_id": first["id"], "version": first["version"]},
            {"hypothesis_id": second["id"], "version": second["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=CLOCK,
    )
    return factor_id, str(first["id"]), str(second["id"])


def _vault(tmp_path, *, probe_item: bool = False):
    paths = create_basic_vault(tmp_path / "vault")
    if probe_item:
        _write_probe_item(
            paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
        )
    vault = load_vault(paths.root)
    return vault, Repository(paths.sqlite_path)


# ---------------------------------------------------------------------------
# The shadow rides every live decision, typed-unavailable when inputs are absent.
# ---------------------------------------------------------------------------


def test_shadow_receipt_rides_the_live_decision_with_typed_arms(tmp_path):
    vault, repository = _vault(tmp_path)
    factor_id, first_id, _second = _seed_factor(repository)

    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)

    live = repository.causal_probe_decision_receipts(factor_id=factor_id)
    shadows = repository.causal_shadow_selection_receipts(factor_id=factor_id)
    assert len(live) == 1 and len(shadows) == 1
    shadow = shadows[0]
    assert shadow["decision_receipt_id"] == live[0]["id"]
    assert shadow["incumbent_decision"] == live[0]["decision"]
    # No instrument exists: the honest early state is typed unavailability,
    # never a fabricated value and never a confident stop.
    assert shadow["likelihood_regime"] == "none"
    assert shadow["shadow_verdict"] == "unavailable"
    baselines = shadow["baselines"]
    assert set(baselines) == {
        "p2_incumbent",
        "formal_evsi",
        "equal_cost_modal_route",
        "evpi_skip_bound",
        "no_measure_common_repair",
    }
    assert baselines["p2_incumbent"]["available"] is True
    assert baselines["formal_evsi"]["available"] is False
    assert baselines["equal_cost_modal_route"]["available"] is False
    assert baselines["evpi_skip_bound"]["available"] is False
    assert shadow["would_change_measure_vs_repair"] is None


def test_no_action_mapping_is_a_typed_abstention_not_a_fabricated_route(tmp_path):
    vault, repository = _vault(tmp_path)
    factor_id, first_id, second_id = _seed_factor(repository, second_repair=None)

    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)

    shadow = repository.causal_shadow_selection_receipts(factor_id=factor_id)[0]
    loss = shadow["body"]["loss_table"]
    assert loss["available"] is False
    assert loss["reason"] == "no_action_mapping"
    assert second_id in loss["unmapped_hypothesis_ids"]

    table, meta = CDS.build_causal_loss_table(
        repository,
        repair_class_by_hypothesis={"h1": "repair:recall", "h2": None},
    )
    assert table is None
    assert meta["reason"] == "no_action_mapping"
    assert meta["unmapped_hypothesis_ids"] == ["h2"]


# ---------------------------------------------------------------------------
# §6.2 arms.
# ---------------------------------------------------------------------------


def test_commissioned_v2_bundles_reach_arm_b_and_the_prior_refusal_passes_through(
    tmp_path,
):
    vault, repository = _vault(tmp_path, probe_item=True)
    factor_id, first_id, _second = _seed_factor(repository, with_targets=True)

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=CLOCK,
    )
    assert result["outcome"] == "commissioned"
    assert result["prediction_basis"] == "hypothesis_target_frame_v2_uniform_keys"

    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)

    shadow = repository.causal_shadow_selection_receipts(factor_id=factor_id)[-1]
    assert shadow["likelihood_regime"] == "arm_b_noiseless_partition"
    formal = shadow["baselines"]["formal_evsi"]
    assert formal["available"] is True
    assert formal["noiseless_upper_bound"] is True
    # The open-set arm is excluded FORMALLY, with its mass on the receipt.
    excluded = formal["conditional_scope"]["excluded"]["other_or_unknown"]
    assert excluded > 0.0
    # No support score existed, so the locked prior is `uniform_fallback` — a
    # legal record, a fabricated distribution as a live-value input. EVSI-1's
    # exclusion passes through as the rank's typed refusal, and the verdict is
    # an abstention, never a live-value claim.
    assert shadow["prior_basis"] == "uniform_fallback"
    rank = formal["rank"]
    assert rank["verdict"] == "abstain"
    assert rank["reason"] == "no_evaluable_candidate"
    assert [entry["reason"] for entry in rank["excluded"]] == [
        "uniform_fallback_prior"
    ]

    # Full-loss and equal-cost are computed from ONE duration estimate today,
    # so they are provably identical — the readiness report's expectations
    # note, demonstrated rather than assumed.
    equal = shadow["baselines"]["equal_cost_modal_route"]
    assert equal["available"] is True

    readiness = causal_selection_readiness(vault, repository)
    assert readiness["shadow_conversions"]["available"] is True
    assert readiness["shadow_conversions"]["full_vs_equal_cost_diverged"] == 0
    assert readiness["likelihood_regimes"]["counts"].get(
        "arm_b_noiseless_partition"
    ) == 1
    assert "provably identical" in readiness["expectations_note"]


def test_v1_style_bundles_stay_arm_c_and_never_license_measure(tmp_path):
    vault, repository = _vault(tmp_path, probe_item=True)
    factor_id, first_id, _second = _seed_factor(repository, with_targets=True)

    def v1_generator(payload):
        hypothesis = payload.get("hypothesis") or {}
        target = ((hypothesis.get("target_ref") or {}).get("criterion_id")) or ""
        if not target:
            return {}
        # The literal v1 emission: both keys for the OWN target, full_credit
        # only for the complement — separable (conflicting full_credit values)
        # but the key schema differs by target set, and no H_OTHER disposition.
        frame = ["criterion_recall", "criterion_method"]
        values = {}
        for criterion in frame:
            if criterion == target:
                values[f"criterion:{criterion}:passed"] = False
                values[f"criterion:{criterion}:full_credit"] = False
            else:
                values[f"criterion:{criterion}:full_credit"] = True
        return {"predicted_features": values}

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        blind_generator=v1_generator,
        model_revision="model-r1",
        clock=CLOCK,
    )
    assert result["outcome"] == "commissioned"

    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)

    shadow = repository.causal_shadow_selection_receipts(factor_id=factor_id)[-1]
    assert shadow["likelihood_regime"] == "arm_c_structural"
    assert shadow["baselines"]["formal_evsi"]["available"] is False
    assert (
        shadow["baselines"]["formal_evsi"]["reason"] == "incomplete_likelihoods"
    )
    # Arm C's only licensed verdict is a bound-based stop; it can never measure.
    assert shadow["shadow_verdict"] in ("stop", "unavailable")


def test_stripping_the_h_other_disposition_demotes_arm_b(tmp_path):
    vault, repository = _vault(tmp_path, probe_item=True)
    factor_id, first_id, second_id = _seed_factor(repository, with_targets=True)

    def undisposed_generator(payload):
        hypothesis = payload.get("hypothesis") or {}
        target = ((hypothesis.get("target_ref") or {}).get("criterion_id")) or ""
        if not target:
            return {}
        keys = {
            "criterion:criterion_recall:passed": target != "criterion_recall",
            "criterion:criterion_method:passed": target != "criterion_method",
        }
        return {"feature_rows": [{"keys": sorted(keys), "values": keys}]}

    commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        blind_generator=undisposed_generator,
        model_revision="model-r1",
        clock=CLOCK,
    )
    candidate = repository.causal_probe_candidates_for_factor(factor_id)[0]
    regime, detail, member = CDS.likelihood_regime_for_candidate(
        repository,
        candidate,
        concrete_hypothesis_ids=[first_id, second_id],
    )
    # Uniform keys, one row each — but the open-set arm was excluded by
    # omission, which is exactly what arm B refuses to accept.
    assert regime == "arm_c_structural"
    assert "no_h_other_disposition" in detail["reason"]
    assert member is None


# ---------------------------------------------------------------------------
# EVPI skip bound + would_change flags (direct call, skewed live-value prior).
# ---------------------------------------------------------------------------


def test_evpi_skip_bound_licenses_stop_under_a_skewed_supported_prior(tmp_path):
    vault, repository = _vault(tmp_path)
    factor_id, first_id, second_id = _seed_factor(repository)
    locked = lock_causal_hypothesis_set(
        repository,
        factor_id,
        probe_phase_id="phase_shadow",
        algorithm_version="test",
        support_scores={first_id: 0.9, second_id: 0.1},
        clock=CLOCK,
    )

    decision_receipt = {
        "id": "receipt_direct_evpi",
        "factor_id": factor_id,
        "decision": "probe_now",
        "reason": "test",
        "inputs": {"probe_burden_minutes": 1.5, "common_repair_covers": False},
        "repair_class_ids": ["repair:recall", "repair:method"],
        "learning_object_id": LO_ID,
        "attempt_id": "att_shadow",
    }
    shadow = CDS.record_shadow_selection(
        repository,
        decision_receipt=decision_receipt,
        candidates=(),
        chosen_candidate={
            "id": "cand_direct",
            "hypothesis_set_id": locked.id,
            "practice_item_id": "pi_without_bundles",
        },
        repair_class_by_hypothesis={
            first_id: "repair:recall",
            second_id: "repair:method",
        },
        common_repair_class_id="repair:recall",
        clock=CLOCK,
    )
    assert shadow is not None
    assert shadow["prior_basis"] == "support_weighted"
    evpi = shadow["baselines"]["evpi_skip_bound"]
    assert evpi["available"] is True
    # Prior ~0.9/0.1 over two routes at the 3.0-minute heuristic default:
    # current expected loss = 0.1 * 6.0 = 0.6 <= 1.5 burden. Even PERFECT
    # information is worth less than the question costs — skip licensed with
    # no likelihood model anywhere in sight.
    assert evpi["skip_licensed"] is True
    assert evpi["current_action"] == "repair:recall"
    assert shadow["shadow_verdict"] == "stop"
    # The incumbent said probe_now; the bound says stop: a conversion.
    assert shadow["would_change_measure_vs_repair"] is True
    # The bound's optimal action agrees with the live common repair.
    assert shadow["would_change_repair"] is False
    # Idempotent per live receipt: a second shadow for the same decision is
    # refused by the UNIQUE constraint, not duplicated.
    again = CDS.record_shadow_selection(
        repository,
        decision_receipt=decision_receipt,
        candidates=(),
        chosen_candidate=None,
        repair_class_by_hypothesis={},
        clock=CLOCK,
    )
    assert again is None


def test_duration_estimates_carry_honest_provenance(tmp_path):
    _vault_obj, repository = _vault(tmp_path)
    repository.record_causal_repair_class_definitions(
        [
            {
                "repair_class_id": "repair:authored",
                "repair_equivalence_id": "eq:authored",
                "episode_id": "ep1",
                "operator": "reteach",
                "repair_policy_version": "test",
                "expected_minutes": 7.5,
            }
        ],
        clock=CLOCK,
    )
    estimates = CDS.duration_estimates_for_repair_classes(
        repository, ["repair:authored", "repair:unknown"]
    )
    assert estimates["repair:authored"]["source"] == "authored_prior"
    assert estimates["repair:authored"]["minutes"] == 7.5
    # No latency has been captured in this vault: the fallback is the pinned
    # heuristic, labeled as such — never a fabricated empirical number.
    assert estimates["repair:unknown"]["source"] == "heuristic_default"


# ---------------------------------------------------------------------------
# The firewall: shadow output is structurally incapable of touching the live path.
# ---------------------------------------------------------------------------


def test_shadow_failure_and_corruption_cannot_alter_the_live_decision(
    tmp_path, monkeypatch
):
    vault, repository = _vault(tmp_path)
    factor_id, first_id, _second = _seed_factor(
        repository, first_repair="repair:recall", second_repair="repair:recall"
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("shadow computation corrupted")

    monkeypatch.setattr(CO.shadow_selector, "record_shadow_selection", _boom)
    raising = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    monkeypatch.setattr(
        CO.shadow_selector,
        "record_shadow_selection",
        lambda *a, **k: {"shadow_verdict": "measure", "garbage": True},
    )
    corrupted = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )
    monkeypatch.undo()
    clean = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )

    # Byte-identical live behavior across a raising shadow, a corrupted
    # shadow, and the real one — receipt ids differ by construction, nothing
    # else may.
    def _comparable(status):
        payload = status.as_dict()
        payload.pop("decision_receipt_id")
        return payload

    assert _comparable(raising) == _comparable(corrupted) == _comparable(clean)
    # The raising and corrupted passes persisted NO shadow rows; the clean
    # pass persisted exactly one for its own receipt.
    shadows = repository.causal_shadow_selection_receipts(factor_id=factor_id)
    assert len(shadows) == 1
    assert shadows[0]["decision_receipt_id"] == clean.decision_receipt_id
    live = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert len(live) == 3


# ---------------------------------------------------------------------------
# Readiness report typed arms.
# ---------------------------------------------------------------------------


def test_readiness_report_types_every_empty_denominator(tmp_path):
    vault, repository = _vault(tmp_path)
    report = causal_selection_readiness(vault, repository)
    assert report["factors"] == {"total": 0, "open": 0}
    assert report["candidate_multiplicity"] == {
        "available": False,
        "reason": "no_open_factors",
    }
    assert report["likelihood_regimes"]["available"] is False
    assert report["duration_sources"]["available"] is False
    assert report["shadow_conversions"] == {
        "available": False,
        "reason": "no_shadow_receipts",
    }
    assert report["cold_outcomes"] == {
        "available": False,
        "reason": "no_cold_outcomes",
    }
    assert report["findings"][0]["parameter"] == (
        "causal_probe_commissioning:MAX_CANDIDATES_PER_FACTOR"
    )


def test_readiness_report_counts_multiplicity_and_regimes(tmp_path):
    vault, repository = _vault(tmp_path, probe_item=True)
    factor_id, first_id, _second = _seed_factor(repository, with_targets=True)
    commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=CLOCK,
    )
    bare_factor_id, bare_first, _bare_second = _seed_factor(
        repository, attempt_id="att_shadow_bare"
    )
    causal_repair_status(vault, repository, misconception_id=first_id, clock=CLOCK)
    causal_repair_status(vault, repository, misconception_id=bare_first, clock=CLOCK)

    report = causal_selection_readiness(vault, repository)
    counts = report["candidate_multiplicity"]["counts"]
    assert counts == {"0": 1, "1": 1, "2+": 0}
    regimes = report["likelihood_regimes"]["counts"]
    assert regimes.get("arm_b_noiseless_partition") == 1
    assert regimes.get("none") == 1
    shadows = report["shadow_conversions"]
    assert shadows["receipts"] == 2
    assert shadows["formal_arm_available"] == 1
