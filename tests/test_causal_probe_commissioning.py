"""Stage 2.1: the probe-administration lane gets a producer.

Before this, `create_probe_candidate` / `transition_probe_candidate` /
`generate_blind_prediction_bundle` had no production caller, so
`causal_probe_candidates` was always empty, `instrument_available` was
permanently False, and `causal_discriminating_observations` (migration 130) could
never be written. These tests pin the producer and, just as importantly, the
typed reasons it declines.
"""

from __future__ import annotations

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.causal_probe_coherence import transition_probe_candidate
from learnloop.services.causal_probe_commissioning import (
    COMMISSIONING_OUTCOMES,
    commission_probe_instrument,
    make_target_generator,
    measurement_contract_for_item,
    sweep_probe_commissioning,
    targeted_criteria,
)
from learnloop.vault.loader import load_vault

from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault

PASSING_REVIEW = {
    "contract_consistent": True,
    "measurement_target_independence": True,
    "undeclared_differences": [],
}


def _write_probe_item(
    paths, item_id: str, *, criteria: list[str], extra: dict | None = None
) -> None:
    """A diagnostic item for the same learning object, with its own rubric."""

    write_yaml(
        paths.practice_item_path("linear-algebra", item_id),
        {
            **(extra or {}),
            "schema_version": 1,
            "id": item_id,
            "learning_object_id": "lo_svd_definition",
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


def _seed_divergent_factor(
    repository: Repository,
    *,
    first_claims: list[dict] | None = None,
    second_claims: list[dict] | None = None,
    first_repair: str = "repair:recall",
    second_repair: str = "repair:method",
    first_target: str = "criterion_recall",
    second_target: str = "criterion_method",
) -> tuple[str, str, str]:
    """Two concrete causes needing different repairs, plus the open-set arm."""

    common = {
        "attempt_id": "att_commission",
        "learning_object_id": "lo_svd_definition",
        "cause_scope": "learner_state",
        "applicability": {"practice_item_id": "pi_svd_define_001"},
        "evidence": {"trace_consistent": True},
        "status": "candidate",
        "clock": FrozenClock(NOW),
    }
    first = repository.append_causal_hypothesis(
        **common,
        episode_key="att_commission:first",
        statement="The transpose rule was not available.",
        statement_normalized="the transpose rule was not available",
        operation="recall_omission",
        target_ref={"kind": "criterion", "criterion_id": first_target},
        repair_class_id=first_repair,
        postdictive_claims=(
            first_claims
            if first_claims is not None
            else [{"criterion_id": "criterion_recall", "must": "fail"}]
        ),
    )
    second = repository.append_causal_hypothesis(
        **common,
        episode_key="att_commission:second",
        statement="The learner selected the wrong factorization convention.",
        statement_normalized="the learner selected the wrong factorization convention",
        operation="method_selection",
        target_ref={"kind": "criterion", "criterion_id": second_target},
        repair_class_id=second_repair,
        postdictive_claims=(
            second_claims
            if second_claims is not None
            else [{"criterion_id": "criterion_method", "must": "fail"}]
        ),
    )
    factor_id = repository.insert_unresolved_cause_factor(
        attempt_id="att_commission",
        candidate_causes=[
            {"hypothesis_id": first["id"], "version": first["version"]},
            {"hypothesis_id": second["id"], "version": second["version"]},
            {"hypothesis_id": "H_OTHER", "open_set": True},
        ],
        algorithm_version="causal_attribution_p2",
        clock=FrozenClock(NOW),
    )
    return factor_id, str(first["id"]), str(second["id"])


def test_commissioning_lights_the_lane_end_to_end(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, first_id, second_id = _seed_divergent_factor(repository)

    # Nothing served this factor before.
    assert repository.causal_probe_candidates_for_factor(factor_id) == []

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )

    assert result["outcome"] == "commissioned"
    assert result["status"] == "registered"
    assert result["practice_item_id"] == "pi_svd_probe_001"
    assert len(result["bundle_ids"]) == 2
    # Model-free and observation-blind: predictions map typed hypothesis targets
    # onto the fresh item's authored criteria.
    assert result["prediction_basis"] == "hypothesis_target_frame_v2_uniform_keys"
    assert result["discrimination"]["distinguishable"]

    stored = repository.causal_probe_candidates_for_factor(factor_id)
    assert [value["status"] for value in stored] == ["registered"]
    assert (
        stored[0]["blind_input_contract_version"]
        == "observation_free_hypothesis_target_v2"
    )

    # A registered candidate is NOT servable: only `active` is, and reaching it
    # needs a reviewer. The producer must not activate its own instrument.
    assert not any(value["status"] == "active" for value in stored)
    with pytest.raises(ValueError, match="requires a reviewer"):
        transition_probe_candidate(
            repository,
            result["candidate_id"],
            to_status="reviewed",
            clock=FrozenClock(NOW),
        )
    reviewed = transition_probe_candidate(
        repository,
        result["candidate_id"],
        to_status="reviewed",
        reviewer="human_owner",
        clock=FrozenClock(NOW),
    )
    assert reviewed["status"] == "reviewed"
    activated = transition_probe_candidate(
        repository,
        result["candidate_id"],
        to_status="active",
        reviewer="human_owner",
        clock=FrozenClock(NOW),
    )
    assert activated["status"] == "active"


def test_obsolete_observation_exposed_candidate_cannot_advance(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)
    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    with repository.connection() as connection:
        connection.execute(
            """
            UPDATE causal_probe_candidates
               SET blind_input_contract_version = NULL
             WHERE id = ?
            """,
            (result["candidate_id"],),
        )
        connection.commit()

    with pytest.raises(ValueError, match="observation-exposed"):
        transition_probe_candidate(
            repository,
            result["candidate_id"],
            to_status="reviewed",
            reviewer="human_owner",
            clock=FrozenClock(NOW),
        )
    withdrawn = transition_probe_candidate(
        repository,
        result["candidate_id"],
        to_status="rejected",
        reviewer="system:blind_input_contract_v2",
        reason="obsolete blind input",
        clock=FrozenClock(NOW),
    )
    assert withdrawn["status"] == "rejected"


def test_commissioning_makes_the_orchestrator_see_an_instrument(tmp_path):
    """The point of the producer: `instrument_available` can finally be True."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    candidate_id = result["candidate_id"]
    for status in ("reviewed", "active"):
        transition_probe_candidate(
            repository,
            candidate_id,
            to_status=status,
            reviewer="human_owner",
            clock=FrozenClock(NOW),
        )

    candidates = repository.causal_probe_candidates_for_factor(factor_id)
    active = [value for value in candidates if value.get("status") == "active"]
    assert active, "the orchestrator's instrument_available reads exactly this"
    assert active[0]["blind_bundle_ids"] == result["bundle_ids"]

    # A pre-correction active candidate remains auditable but is withdrawn
    # before availability is decided.
    current = active[0]
    repository.insert_causal_probe_candidate(
        candidate_id="cpc_observation_exposed_legacy",
        factor_id=factor_id,
        practice_item_id=current["practice_item_id"],
        hypothesis_set_id=current["hypothesis_set_id"],
        manipulation_audit_id=current["manipulation_audit_id"],
        measurement_contract=current["measurement_contract"],
        blind_bundle_ids=current["blind_bundle_ids"],
        discrimination=current["discrimination"],
        blind_input_contract_version=None,
        status="active",
        clock=FrozenClock(NOW),
    )

    # Re-commissioning is a no-op once an instrument serves the factor.
    again = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    assert again["outcome"] == "already_available"
    legacy = repository.causal_probe_candidate(
        "cpc_observation_exposed_legacy"
    )
    assert legacy["status"] == "rejected"
    events = repository.causal_probe_candidate_events(
        "cpc_observation_exposed_legacy"
    )
    assert events[-1]["actor"] == "system:blind_input_contract_v2"


def test_pending_adversarial_review_is_a_state_not_a_failure(tmp_path):
    """Causal §5.8 rule 2 / §7: the structural half ships without the
    adversarial half, and says so rather than minting an unaudited instrument."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, clock=FrozenClock(NOW)
    )
    assert result["outcome"] == "pending_adversarial_review"
    assert result["manipulation_audit_id"]
    assert repository.causal_probe_candidates_for_factor(factor_id) == []


def test_self_reviewed_manipulation_is_rejected(tmp_path):
    """The reviewer may not be the generator — a model grading its own homework
    is not an independent audit."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="same_agent",
        reviewer_agent_run_id="same_agent",
        clock=FrozenClock(NOW),
    )
    assert result["outcome"] == "manipulation_audit_rejected"
    assert repository.causal_probe_candidates_for_factor(factor_id) == []


def test_causes_predicting_the_same_observation_do_not_discriminate(tmp_path):
    """Two causes committing to the same observables are indiscriminable, and the
    outcome names the remedy (author a manipulation) instead of pretending."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(paths, "pi_svd_probe_001", criteria=["criterion_recall"])
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(
        repository,
        first_target="criterion_recall",
        second_target="criterion_recall",
    )

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    assert result["outcome"] == "bundles_do_not_discriminate"
    assert repository.causal_probe_candidates_for_factor(factor_id) == []


def test_claims_the_item_cannot_observe_yield_no_derivable_predictions(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(paths, "pi_svd_probe_001", criteria=["criterion_unrelated"])
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    result = commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    assert result["outcome"] == "no_derivable_predictions"
    assert result["bundle_ids"] == []


def test_no_candidate_item_is_an_authoring_obligation(tmp_path):
    """The instrument-pool bottleneck, stated per factor."""

    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, clock=FrozenClock(NOW)
    )
    assert result["outcome"] == "no_candidate_item"
    assert result["learning_object_id"] == "lo_svd_definition"


def test_action_equivalent_causes_buy_nothing(tmp_path):
    """Divergence is the entire warrant for spending on discrimination."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(
        repository, first_repair="repair:same", second_repair="repair:same"
    )

    result = commission_probe_instrument(
        vault, repository, factor_id=factor_id, clock=FrozenClock(NOW)
    )
    assert result["outcome"] == "not_divergent"
    assert result["repair_class_ids"] == ["repair:same"]


def test_frame_generator_declares_targets_and_marks_the_complement(tmp_path):
    """The complement declaration is an added commitment; it must be visible."""

    generate = make_target_generator(["criterion_recall", "criterion_method"])
    payload = {
        "hypothesis": {
            "target_ref": {"kind": "criterion", "criterion_id": "criterion_recall"},
            # Observation-conditioned claims must be ignored by the bundle lane.
            "postdictive_claims": [
                {"criterion_id": "criterion_method", "must": "fail"}
            ]
        },
        "rubric": {
            "criteria": [
                {"id": "criterion_recall"},
                {"id": "criterion_method"},
                {"id": "criterion_extra"},
            ]
        },
    }
    predictions = generate(payload)

    assert predictions["prediction_basis"] == "hypothesis_target_frame_v2_uniform_keys"
    assert predictions["targeted_criteria"] == ["criterion_recall"]
    assert predictions["complement_criteria"] == ["criterion_method"]
    row = predictions["feature_rows"][0]
    # §6.2 arm B: every in-frame criterion declares BOTH keys, so all
    # hypotheses in the frame share one key schema and the bundles partition.
    assert row["values"] == {
        "criterion:criterion_method:full_credit": True,
        "criterion:criterion_method:passed": True,
        "criterion:criterion_recall:full_credit": False,
        "criterion:criterion_recall:passed": False,
    }
    assert predictions["open_set_disposition"]["disposition"] == (
        "excluded_no_declared_emission"
    )
    # A criterion outside the frame is never declared, even though the item
    # measures it: the frame is what the RIVALS put in play.
    assert "criterion:criterion_extra:full_credit" not in row["values"]

    # A hypothesis with no target inside the frame predicts nothing here, and must
    # not be handed a bundle asserting that everything passes.
    assert generate({**payload, "hypothesis": {"target_ref": None}}) == {}


def test_target_mapping_never_falls_back_to_postdictive_claims():
    rubric = {"criteria": [{"id": "c"}]}
    assert targeted_criteria(
        {
            "target_ref": None,
            "postdictive_claims": [{"criterion_id": "c", "must": "fail"}],
        },
        rubric,
    ) == []


def test_measurement_contract_is_the_items_own(tmp_path):
    """A1/§7: probe measurement targets are recompiled, never inherited."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    contract = measurement_contract_for_item(
        vault, vault.practice_items["pi_svd_probe_001"]
    )
    assert contract["independently_compiled"] is True
    assert contract["inherited_parent_facet_weights"] is False
    assert [value["criterion_id"] for value in contract["criteria"]] == [
        "criterion_recall",
        "criterion_method",
    ]
    assert contract["measurement_status"] == "item_local"


def test_sweep_machine_checks_queues_the_instrument_debt(tmp_path):
    """A divergent factor with no instrument owes one, and the debt is queued so
    it is drainable instead of re-derived and forgotten on every attempt."""

    from learnloop.services.causal_orchestrator import (
        MACHINE_CHECK_INSTRUMENT_COMMISSIONING,
        pending_machine_checks_for_factor,
        sweep_machine_checks,
    )

    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    sweep_machine_checks(
        vault, repository, "lo_svd_definition", clock=FrozenClock(NOW)
    )
    queued = [
        check
        for check in repository.causal_machine_checks(status="pending")
        if str(check["kind"]) == MACHINE_CHECK_INSTRUMENT_COMMISSIONING
    ]
    assert len(queued) == 1
    assert queued[0]["factor_id"] == factor_id
    assert queued[0]["payload"]["learner_actionable"] is False
    assert len(queued[0]["payload"]["repair_class_ids"]) == 2

    # It is machine-side debt, but it must NOT read as `defer_machine_checks`:
    # commissioning does not resolve the uncertainty, it builds the instrument.
    # The honest learner-facing state stays `no_discriminating_instrument`.
    assert (
        pending_machine_checks_for_factor(
            repository, factor_id=factor_id, learning_object_id="lo_svd_definition"
        )
        == []
    )

    # Idempotent on the obligation's content hash.
    sweep_machine_checks(
        vault, repository, "lo_svd_definition", clock=FrozenClock(NOW)
    )
    assert len(
        [
            check
            for check in repository.causal_machine_checks(status="pending")
            if str(check["kind"]) == MACHINE_CHECK_INSTRUMENT_COMMISSIONING
        ]
    ) == 1

    # Once an instrument is commissioned the obligation stops being emitted, and
    # the sweep closes it rather than leaving a permanent pending check.
    commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    sweep_machine_checks(
        vault, repository, "lo_svd_definition", clock=FrozenClock(NOW)
    )
    assert [
        check
        for check in repository.causal_machine_checks(status="pending")
        if str(check["kind"]) == MACHINE_CHECK_INSTRUMENT_COMMISSIONING
    ] == []


def test_sweep_commissions_open_factors_and_reports_each_outcome(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _seed_divergent_factor(repository)

    results = sweep_probe_commissioning(
        vault,
        repository,
        learning_object_id="lo_svd_definition",
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
    )
    assert [value["outcome"] for value in results] == ["commissioned"]
    assert all(value["outcome"] in COMMISSIONING_OUTCOMES for value in results)


# ---------------------------------------------------------------------------
# v3 multiplicity: one candidate per instrument CLASS, at most two per factor
# (EVSI-1 -- v2's one-candidate cap made the 2+ ranking arm unreachable).
# ---------------------------------------------------------------------------


def _commission(vault, repository, factor_id, **kwargs):
    return commission_probe_instrument(
        vault,
        repository,
        factor_id=factor_id,
        adversarial_review=PASSING_REVIEW,
        generation_agent_run_id="agent_generate",
        reviewer_agent_run_id="agent_review",
        clock=FrozenClock(NOW),
        **kwargs,
    )


def test_second_candidate_in_a_new_instrument_class_is_commissioned(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    _write_probe_item(
        paths,
        "pi_svd_probe_pair",
        criteria=["criterion_recall", "criterion_method"],
        extra={"contrast_of": "pi_svd_probe_001"},
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    first = _commission(vault, repository, factor_id)
    assert first["outcome"] == "commissioned"
    assert first["practice_item_id"] == "pi_svd_probe_001"

    second = _commission(vault, repository, factor_id)
    assert second["outcome"] == "commissioned"
    # The second mint is the DIFFERENT-class member (contrast pair), never a
    # same-class twin of the constructed diagnostic already pending.
    assert second["practice_item_id"] == "pi_svd_probe_pair"

    stored = repository.causal_probe_candidates_for_factor(factor_id)
    assert sorted(str(value["status"]) for value in stored) == [
        "registered",
        "registered",
    ]


def test_a_same_class_pool_keeps_the_single_candidate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    _write_probe_item(
        paths, "pi_svd_probe_002", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    assert _commission(vault, repository, factor_id)["outcome"] == "commissioned"
    # Both remaining items are the same constructed-diagnostic class: a twin
    # adds no class diversity, so the factor keeps its single pending candidate.
    result = _commission(vault, repository, factor_id)
    assert result["outcome"] == "already_pending_review"
    assert len(repository.causal_probe_candidates_for_factor(factor_id)) == 1


def test_explicit_same_class_item_is_refused_as_a_typed_duplicate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    _write_probe_item(
        paths, "pi_svd_probe_002", criteria=["criterion_recall", "criterion_method"]
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    assert _commission(vault, repository, factor_id)["outcome"] == "commissioned"
    result = _commission(
        vault, repository, factor_id,
        candidate_practice_item_id="pi_svd_probe_002",
    )
    assert result["outcome"] == "duplicate_instrument_class"
    assert result["instrument_class"] == "constructed_diagnostic"


def test_the_cap_is_two_candidates_per_factor(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_probe_item(
        paths, "pi_svd_probe_001", criteria=["criterion_recall", "criterion_method"]
    )
    _write_probe_item(
        paths,
        "pi_svd_probe_pair",
        criteria=["criterion_recall", "criterion_method"],
        extra={"contrast_of": "pi_svd_probe_001"},
    )
    _write_probe_item(
        paths,
        "pi_svd_probe_pair_b",
        criteria=["criterion_recall", "criterion_method"],
        extra={"contrast_of": "pi_svd_probe_001"},
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    factor_id, _first, _second = _seed_divergent_factor(repository)

    assert _commission(vault, repository, factor_id)["outcome"] == "commissioned"
    assert _commission(vault, repository, factor_id)["outcome"] == "commissioned"
    third = _commission(vault, repository, factor_id)
    assert third["outcome"] == "already_pending_review"
    assert len(repository.causal_probe_candidates_for_factor(factor_id)) == 2
