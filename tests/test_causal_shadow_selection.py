"""Causal valuation helpers and the retired shadow's write boundary."""

from __future__ import annotations

from learnloop.diagnosis import causal_diagnostic_selector as CDS
from learnloop.diagnosis.causal_orchestrator import causal_repair_status
from learnloop.diagnosis.causal_probe_commissioning import commission_probe_instrument

from tests.causal_shadow_selection_helpers import CLOCK, PASSING_REVIEW, _seed_factor, _vault


def test_no_action_mapping_is_a_typed_abstention_not_a_fabricated_route(tmp_path):
    _vault_obj, repository = _vault(tmp_path)

    table, meta = CDS.build_causal_loss_table(
        repository,
        repair_class_by_hypothesis={"h1": "repair:recall", "h2": None},
    )
    assert table is None
    assert meta["reason"] == "no_action_mapping"
    assert meta["unmapped_hypothesis_ids"] == ["h2"]


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


def test_causal_probe_decision_writes_no_retired_shadow_receipts(tmp_path):
    vault, repository = _vault(tmp_path, probe_item=True)
    factor_id, first_id, _second = _seed_factor(repository, with_targets=True)
    commissioned = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=CLOCK,
    )
    assert commissioned["outcome"] == "commissioned"

    status = causal_repair_status(
        vault, repository, misconception_id=first_id, clock=CLOCK
    )

    live = repository.causal_probe_decision_receipts(factor_id=factor_id)
    assert len(live) == 1
    assert live[0]["id"] == status.decision_receipt_id
    with repository.connection() as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM causal_shadow_selection_receipts"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT COUNT(*) FROM voi_forecasts WHERE site = ?",
            ("causal_shadow_selection",),
        ).fetchone()[0] == 0
