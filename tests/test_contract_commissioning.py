"""Rung-correct generation + the contract-cell hit rate (plan item 5.1).

Step 0 (spec_measurement_efficiency_v1 §5.8.2) measured that 100% of attempts hit
a facet the contract requires and only 28% hit a required ``(facet, capability)``
cell — "72% hit no contract cell at all, *purely* because the item sits at the
wrong rung". These tests pin the mechanism (the waypoint used to be chosen from the
learner's mastery band, independently of the blueprint, and the rung gate then
hard-failed items authored at the contract's capability), the fix, and the metric
that makes item 5.1's hypothesis falsifiable.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.db.repositories import MasteryState, Repository
from learnloop.services.contract_commissioning import (
    CommissionDisposition,
    commission_plan,
    contract_cell_hit_rate,
    item_observed_cells,
)
from learnloop.services.contract_reachability import (
    ReachabilityVerdict,
    analyze_contract_reachability,
)
from learnloop.services.depth_rungs import capability_rung, select_rung, waypoint_slug_for_capability
from learnloop.services.practice_generation import (
    PracticeExpansionError,
    _RungGate,
    build_practice_expansion_plan,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault

# The basic vault's only item is `short_answer` on facet "recall", compiling to
# `schema_interpretation` (capability_mapping.MODE_CAPABILITY_DEFAULTS). Same
# anchor test_contract_reachability.py uses, so the ladder positions line up.
INSTRUMENT_FACET = "recall"
INSTRUMENT_CAPABILITY = "schema_interpretation"
LO_ID = "lo_svd_definition"


def _write_blueprint(paths, components, *, integration=None, recipe_id="r1"):
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    recipe = {
        "id": recipe_id,
        "composition": "conjunctive",
        "all_of": [
            {"facet": facet, "capability": capability, "modality": modality}
            for facet, capability, modality in components
        ],
    }
    if integration is not None:
        recipe["integration"] = {
            "facet": integration[0],
            "capability": integration[1],
            "modality": "hard",
        }
    data["blueprints"] = [{"id": "bp1", "weight": 1.0, "recipes": [recipe]}]
    write_yaml(lo_path, data)
    return paths


def _seed_cold_mastery(repository: Repository) -> None:
    """A learner the mastery band would park at the bottom rung.

    0.02 is well below `display_developing_threshold`, so `select_rung` picks
    `recall` / `retrieval` — the band-keyed choice that has nothing to do with what
    the blueprint asks for. This is the divergence the item exists to remove.
    """

    repository.upsert_mastery_state(
        MasteryState(
            learning_object_id=LO_ID,
            logit_mean=-4.0,
            logit_variance=0.2,
            evidence_count=12,
            last_evidence_at=NOW_ISO,
            algorithm_version="mvp-0.1",
            updated_at=NOW_ISO,
        )
    )


# -- the commissioning queue ---------------------------------------------------


def test_queue_order_is_3_1s_order_not_a_second_priority(tmp_path):
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [
            # MISMATCH_BELOW: the instrument sits below this requirement.
            (INSTRUMENT_FACET, "procedure_execution", "hard"),
            # NO_INSTRUMENT: nothing observes this facet at all.
            ("uninstrumented_facet", "method_selection", "hard"),
        ],
    )
    vault = load_vault(paths.root)
    plan = commission_plan(vault, Repository(paths.sqlite_path))

    # `_QUEUE_PRIORITY` puts the re-rung remedy ahead of the authoring backlog, and
    # commissioning preserves that rather than sorting by, say, capability depth.
    assert [str(cell.row.verdict) for cell in plan.commissioned] == [
        "MISMATCH_BELOW",
        "NO_INSTRUMENT",
    ]
    assert [cell.queue_rank for cell in plan.commissioned] == [0, 1]
    # Each commissioned cell carries the CONTRACT's capability and the waypoint
    # that authors at it — not the learner's band.
    assert [cell.capability for cell in plan.commissioned] == [
        "procedure_execution",
        "method_selection",
    ]
    assert [cell.rung.waypoint_slug for cell in plan.commissioned] == ["execute", "select_method"]


def test_coordination_cell_is_deferred_with_a_typed_reason(tmp_path):
    # §5.8.3 / D3 criterion 2: `coordination` is legitimate but observable "only
    # behind a reviewed depth envelope, because the default trajectory deliberately
    # refuses to generate whole-task work". So it is never quietly re-aimed one
    # rung lower — that would be a blueprint edit disguised as generation (5.2's
    # job) — and never authored off-trajectory.
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [(INSTRUMENT_FACET, "schema_interpretation", "hard")],
        integration=("assembly_facet", "coordination"),
    )
    plan = commission_plan(load_vault(paths.root), Repository(paths.sqlite_path))

    assert plan.commissioned == ()
    (deferred,) = plan.deferred
    assert deferred.disposition is CommissionDisposition.DEFER_DEPTH_ENVELOPE
    assert deferred.reason == "coordination_requires_reviewed_depth_envelope"
    assert deferred.rung is None
    assert deferred.row.cell.integration is True
    assert waypoint_slug_for_capability("coordination") is None


def test_integration_cell_at_an_authorable_rung_is_commissioned_normally(tmp_path):
    # §5.8.2 noted the one integration component that did NOT sit at coordination
    # ("proves the model was choosing"). An integration component at an authorable
    # rung is just a cell; its role does not change what a rung means.
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [(INSTRUMENT_FACET, "schema_interpretation", "hard")],
        integration=("assembly_facet", "method_selection"),
    )
    plan = commission_plan(load_vault(paths.root), Repository(paths.sqlite_path))

    (commissioned,) = plan.commissioned
    assert commissioned.row.cell.integration is True
    assert commissioned.capability == "method_selection"
    assert commissioned.rung.waypoint_slug == "select_method"


def test_mismatch_above_and_indeterminate_are_deferred_not_authored(tmp_path):
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [
            # instrument is ABOVE this requirement -> B1 dominance, not authoring
            (INSTRUMENT_FACET, "retrieval", "hard"),
            # unplaceable on the ladder -> the blueprint is what needs fixing
            (INSTRUMENT_FACET, "not_a_capability", "hard"),
        ],
    )
    plan = commission_plan(load_vault(paths.root), Repository(paths.sqlite_path))

    assert plan.commissioned == ()
    by_disposition = {cell.disposition: cell for cell in plan.deferred}
    assert set(by_disposition) == {
        CommissionDisposition.DEFER_DOMINANCE,
        CommissionDisposition.DEFER_BLUEPRINT_REPAIR,
    }
    assert (
        by_disposition[CommissionDisposition.DEFER_DOMINANCE].reason
        == "instrument_above_requirement_propagate_dominance"
    )
    assert (
        by_disposition[CommissionDisposition.DEFER_BLUEPRINT_REPAIR].reason
        == "required_capability_outside_vocabulary"
    )


def test_contract_capabilities_include_reachable_cells(tmp_path):
    # The gate's admission set is the whole contract, not just the backlog: an
    # extra item on an already-reachable cell is still on-contract.
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),  # REACHABLE
            (INSTRUMENT_FACET, "procedure_execution", "hard"),    # MISMATCH_BELOW
        ],
    )
    plan = commission_plan(load_vault(paths.root), Repository(paths.sqlite_path))

    # Ladder order, low -> high.
    assert plan.capabilities_for(LO_ID) == ("schema_interpretation", "procedure_execution")
    assert [cell.capability for cell in plan.commissioned] == ["procedure_execution"]


# -- generation targets the contract's capability -------------------------------


def test_plan_rung_follows_the_contract_not_the_mastery_band(tmp_path):
    """The mechanism, pinned.

    ``select_rung`` keys the waypoint to the learner's mastery band, so a cold
    learner is parked at ``recall`` / ``retrieval`` no matter what the blueprint
    asks for — and ``_RungGate`` then hard-fails any item authored at the
    contract's capability. Both halves are asserted here so a regression cannot
    quietly reintroduce either.
    """

    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [("uninstrumented_facet", "procedure_execution", "hard")],
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _seed_cold_mastery(repository)

    band_rung = select_rung(
        vault, repository, learning_object_id=LO_ID, mastery_mean=0.02, evidence_count=12
    )
    assert (band_rung.waypoint_slug, band_rung.capability) == ("recall", "retrieval")

    plan = build_practice_expansion_plan(
        vault, repository, learning_object_ids=[LO_ID], require_completed_probe=False
    )
    (target,) = plan.targets
    assert target.rung.capability == "procedure_execution"
    assert target.rung.waypoint_slug == "execute"
    assert [cell["capability"] for cell in target.commissioned_cells] == ["procedure_execution"]
    assert target.contract_capabilities == ["procedure_execution"]
    # The prompt payload carries the cells, so the model is told the requirement
    # rather than left to infer it from a flat facet list.
    payload = target.as_dict()
    assert payload["capability"] == "procedure_execution"
    assert payload["commissioned_cells"][0]["facet"] == "uninstrumented_facet"
    assert payload["commissioned_cells"][0]["target_task_features"]["span"] == "multi_step"


def test_legacy_learning_object_keeps_the_mastery_band_rung(tmp_path):
    # `fixtures/arxiv` has 0 contract cells over 15 LOs. A vault with no authored
    # blueprints must be byte-for-byte unaffected — this change is not a policy
    # that applies everywhere, it is honouring contracts where they exist.
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _seed_cold_mastery(repository)

    plan = build_practice_expansion_plan(
        vault, repository, learning_object_ids=[LO_ID], require_completed_probe=False
    )
    (target,) = plan.targets
    assert target.commissioned_cells == []
    assert target.contract_capabilities == []
    assert (target.rung.waypoint_slug, target.rung.capability) == ("recall", "retrieval")


def test_deferred_cells_ride_on_the_plan_not_the_prompt(tmp_path):
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [(INSTRUMENT_FACET, "procedure_execution", "hard")],
        integration=("assembly_facet", "coordination"),
    )
    plan = build_practice_expansion_plan(
        load_vault(paths.root),
        Repository(paths.sqlite_path),
        learning_object_ids=[LO_ID],
        require_completed_probe=False,
    )
    (target,) = plan.targets

    # Naming an unauthorable cell to the model would only invite a wrong-rung item;
    # dropping it entirely is how 18 uncertifiable objectives went unnoticed.
    assert "deferred_cells" not in target.as_dict()
    deferred = plan.as_dict()["deferred_contract_cells"]
    assert [row["reason"] for row in deferred] == [
        "coordination_requires_reviewed_depth_envelope"
    ]


def test_max_los_truncates_by_queue_priority(tmp_path):
    """The "prioritized" half of item 5.1.

    Two LOs, the alphabetically-later one holding the cheaper remedy. Truncating
    alphabetically would drop the cell the queue put first.
    """

    paths = create_basic_vault(tmp_path / "vault")
    # lo_svd_definition: NO_INSTRUMENT (authoring backlog, queue priority 2).
    _write_blueprint(paths, [("uninstrumented_facet", "procedure_execution", "hard")])
    # A second LO with a MISMATCH_BELOW cell (queue priority 1) and an id that
    # sorts AFTER lo_svd_definition.
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    data["id"] = "lo_zzz_second"
    data["blueprints"] = [
        {
            "id": "bp2",
            "weight": 1.0,
            "recipes": [
                {
                    "id": "r2",
                    "composition": "conjunctive",
                    "all_of": [
                        {
                            "facet": INSTRUMENT_FACET,
                            "capability": "procedure_execution",
                            "modality": "hard",
                        }
                    ],
                }
            ],
        }
    ]
    write_yaml(paths.learning_object_path("linear-algebra", "lo_zzz_second"), data)

    plan = build_practice_expansion_plan(
        load_vault(paths.root),
        Repository(paths.sqlite_path),
        require_completed_probe=False,
        max_los=1,
    )

    assert [target.learning_object_id for target in plan.targets] == ["lo_zzz_second"]


# -- the completed-probe gate ----------------------------------------------------


def test_contract_backed_lo_waives_the_completed_probe_gate(tmp_path):
    """A commissionable contract cell is an authoring obligation regardless of probes.

    With the gate unconditional, `fixtures/linear_algebra` yielded **0** expansion
    targets under the CLI default while 18 LOs held commissionable cells — every
    `lo_probe_state` row was absent and all probe episodes sat at pending_items.
    The contract already owns the waypoint (5.1); it owns this gate for the same
    reason: probe evidence is about the learner, a commissionable cell is about
    the instrument pool.
    """

    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [("uninstrumented_facet", "procedure_execution", "hard")],
    )
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)  # no probe state seeded anywhere

    # Default gate (require_completed_probe=True) — the CLI `generate-practice` path.
    plan = build_practice_expansion_plan(vault, repository)
    (target,) = plan.targets
    assert target.learning_object_id == LO_ID
    assert [cell["capability"] for cell in target.commissioned_cells] == ["procedure_execution"]

    # Naming the LO must agree with the loop rather than raising at validation.
    named = build_practice_expansion_plan(vault, repository, learning_object_ids=[LO_ID])
    assert [t.learning_object_id for t in named.targets] == [LO_ID]


def test_lo_without_contract_cells_keeps_the_completed_probe_gate(tmp_path):
    # No blueprint ⇒ nothing commissionable ⇒ the probe gate is byte-for-byte the
    # old behaviour, in both the loop and the named-LO validation.
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)

    assert build_practice_expansion_plan(vault, repository).targets == []
    with pytest.raises(PracticeExpansionError):
        build_practice_expansion_plan(vault, repository, learning_object_ids=[LO_ID])


def test_deferred_only_lo_keeps_the_completed_probe_gate(tmp_path):
    # Deferral is not commissioning: an LO whose only unreachable cell is deferred
    # (`coordination` behind the depth envelope) has nothing the planner can
    # author, so waiving the probe gate for it would produce a target with no
    # commissioned cells and a band-keyed rung — the pre-5.1 shape.
    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [(INSTRUMENT_FACET, "schema_interpretation", "hard")],  # REACHABLE
        integration=("assembly_facet", "coordination"),  # deferred, not commissioned
    )
    plan = build_practice_expansion_plan(load_vault(paths.root), Repository(paths.sqlite_path))
    assert plan.targets == []


# -- the gate -------------------------------------------------------------------


def _gate_row(capability: str, *, learning_object_id: str = LO_ID) -> dict:
    return {
        "item_type": "practice_item",
        "operation": "create",
        "client_item_id": "pi_new",
        "validation_status": "valid",
        "payload": {
            "learning_object_id": learning_object_id,
            "capability": capability,
            "task_features": {
                "complexity": 2,
                "transfer": "near",
                "response": "structured_steps",
                "scaffolding": "none",
                "span": "multi_step",
            },
        },
    }


def _gate_for(paths, *, contract):
    _write_blueprint(paths, contract)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _seed_cold_mastery(repository)
    plan = build_practice_expansion_plan(
        vault, repository, learning_object_ids=[LO_ID], require_completed_probe=False
    )
    return _RungGate(repository, plan)


def test_gate_admits_an_item_at_the_contracts_capability(tmp_path):
    # This is the inversion: with the mastery-band rung (recall/retrieval) this
    # exact row hard-failed "capability 'procedure_execution' does not match the
    # target waypoint capability 'retrieval'".
    gate = _gate_for(
        create_basic_vault(tmp_path / "vault"),
        contract=[("uninstrumented_facet", "procedure_execution", "hard")],
    )
    rows = [_gate_row("procedure_execution")]
    gate(rows)

    assert gate.violations == []
    assert rows[0].get("_auto_apply") is None
    assert rows[0]["payload"]["task_feature_schema"] == "p1_launch@1"


def test_gate_hard_fails_an_off_contract_capability(tmp_path):
    gate = _gate_for(
        create_basic_vault(tmp_path / "vault"),
        contract=[("uninstrumented_facet", "procedure_execution", "hard")],
    )
    rows = [_gate_row("retrieval")]
    gate(rows)

    assert len(gate.violations) == 1
    assert "not one this learning object's contract names" in gate.violations[0]
    assert rows[0]["_auto_apply"] is False
    assert any("rung_target:" in error for error in rows[0]["validation_errors"])


def test_gate_flags_a_coordination_item_for_review_rather_than_admitting_it(tmp_path):
    # The contract legitimately names coordination, so the item is not off-contract;
    # but no default-trajectory waypoint exists to validate it against, so it is
    # held for review with the obligation named (§5.8.3 "keeps and flags").
    paths = create_basic_vault(tmp_path / "vault")
    gate = _gate_for(paths, contract=[("uninstrumented_facet", "coordination", "hard")])
    whole_task = _gate_row("coordination")
    whole_task["payload"]["task_features"]["span"] = "whole_task"
    gate(rows := [whole_task])

    assert gate.violations == []
    assert len(gate.warnings) == 1
    assert "reviewed depth envelope" in gate.warnings[0]
    assert rows[0].get("_auto_apply") is None

    # The one structural rule about coordination still binds with no waypoint to
    # bound task features against: a coordination observation IS a whole-task one.
    gate = _gate_for(paths, contract=[("uninstrumented_facet", "coordination", "hard")])
    gate(rows := [_gate_row("coordination")])
    assert any("requires span=whole_task" in violation for violation in gate.violations)
    assert rows[0]["_auto_apply"] is False


def test_gate_keeps_single_rung_behaviour_on_a_legacy_learning_object(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    _seed_cold_mastery(repository)
    plan = build_practice_expansion_plan(
        vault, repository, learning_object_ids=[LO_ID], require_completed_probe=False
    )
    gate = _RungGate(repository, plan)
    rows = [_gate_row("procedure_execution")]
    gate(rows)

    # No contract => the mastery-band waypoint still rules, and overshooting it is
    # still a hard fail. Nothing about the legacy path changed.
    assert any("does not match the target waypoint capability" in v for v in gate.violations)


# -- end to end: authoring at the rung closes the cell -------------------------


def test_authoring_at_the_contract_capability_makes_the_cell_reachable(tmp_path):
    """The whole point, through 3.1's own report.

    A ``MISMATCH_BELOW`` cell becomes ``REACHABLE`` once an item is authored at the
    contract's capability — and would not have, at the mastery-band capability.
    """

    paths = _write_blueprint(
        create_basic_vault(tmp_path / "vault"),
        [(INSTRUMENT_FACET, "procedure_execution", "hard")],
    )
    before = analyze_contract_reachability(load_vault(paths.root))
    (row,) = before.cells
    assert row.verdict is ReachabilityVerdict.MISMATCH_BELOW

    commissioned = commission_plan(load_vault(paths.root), Repository(paths.sqlite_path)).commissioned
    assert len(commissioned) == 1
    cell = commissioned[0]

    # Author exactly what the commissioning row asks for.
    template = read_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_001"))
    template.update(
        {
            "id": "pi_svd_execute_001",
            "practice_mode": "constructed_response",
            "capability": cell.capability,
            "task_features": dict(cell.rung.task_features),
            "task_feature_schema": cell.rung.task_feature_schema_version_id,
            "evidence_facets": [cell.facet_id],
            "evidence_weights": {cell.facet_id: 1.0},
            "prompt": "Compute the SVD factors of the given matrix, showing each step.",
            "surface_family": "svd_compute_steps",
            "updated_at": NOW_ISO,
        }
    )
    write_yaml(paths.practice_item_path("linear-algebra", "pi_svd_execute_001"), template)

    after = analyze_contract_reachability(load_vault(paths.root))
    (row,) = after.cells
    assert row.verdict is ReachabilityVerdict.REACHABLE
    assert "pi_svd_execute_001" in row.matching_instrument_ids
    # And there is nothing left to commission for this LO.
    assert commission_plan(load_vault(paths.root), Repository(paths.sqlite_path)).commissioned == ()


def test_capability_rung_refuses_to_guess(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)

    assert capability_rung(repository, "method_selection").waypoint_slug == "select_method"
    # No nearest-neighbour fallback: authoring one rung off the contract silently
    # is the defect item 5.1 removes.
    assert capability_rung(repository, "coordination") is None
    assert capability_rung(repository, "not_a_capability") is None


# -- the metric -----------------------------------------------------------------


def _attempt(attempt_id: str, item_id: str, *, learning_object_id: str = LO_ID, created_at=NOW_ISO):
    return {
        "id": attempt_id,
        "practice_item_id": item_id,
        "learning_object_id": learning_object_id,
        "subject": "linear-algebra",
        "concept": "singular_value_decomposition",
        "practice_mode": "short_answer",
        "attempt_type": "independent_attempt",
        "learner_answer_md": "an answer",
        "evidence_facets": [INSTRUMENT_FACET],
        "evidence_weights": {INSTRUMENT_FACET: 1.0},
        "rubric_score": 4,
        "correctness": 1.0,
        "confidence": 4,
        "latency_seconds": 10,
        "hints_used": 0,
        "grader_confidence": 1.0,
        "created_at": created_at,
        "updated_at": created_at,
    }


def _author_item(paths, item_id: str, *, capability: str, facet: str, mode="constructed_response"):
    template = read_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_001"))
    template.update(
        {
            "id": item_id,
            "practice_mode": mode,
            "capability": capability,
            "evidence_facets": [facet],
            "evidence_weights": {facet: 1.0},
            "surface_family": item_id,
            "updated_at": NOW_ISO,
        }
    )
    write_yaml(paths.practice_item_path("linear-algebra", item_id), template)


def test_hit_rate_partitions_attempts_into_cell_rung_and_off_contract(tmp_path):
    """The three arms of §5.8.2's decomposition, one attempt each."""

    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [(INSTRUMENT_FACET, "procedure_execution", "hard")])
    _author_item(paths, "pi_on_cell", capability="procedure_execution", facet=INSTRUMENT_FACET)
    _author_item(paths, "pi_wrong_rung", capability="retrieval", facet=INSTRUMENT_FACET)
    _author_item(paths, "pi_off_topic", capability="procedure_execution", facet="other_facet")
    repository = Repository(paths.sqlite_path)
    repository.insert_practice_attempt(_attempt("a1", "pi_on_cell"))
    repository.insert_practice_attempt(_attempt("a2", "pi_wrong_rung"))
    repository.insert_practice_attempt(_attempt("a3", "pi_off_topic"))

    metric = contract_cell_hit_rate(load_vault(paths.root), repository)

    assert metric.attempts_scored == 3
    assert (metric.cell_hits, metric.facet_only_hits, metric.off_contract) == (1, 1, 1)
    assert metric.cell_hit_rate == 1 / 3
    # The middle arm is the only one rung-correct generation can move, so it stays
    # separate: right facet, wrong capability.
    assert metric.rung_loss_share == 1 / 3
    assert metric.facet_hit_rate == 2 / 3
    assert metric.by_learning_object[LO_ID] == (1, 3)


def test_hit_rate_excludes_attempts_with_no_contract_to_hit(tmp_path):
    # An LO that declares no cells has nothing to miss; folding it into the
    # denominator would make this a measure of blueprint coverage instead.
    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    repository.insert_practice_attempt(_attempt("a1", "pi_svd_define_001"))

    metric = contract_cell_hit_rate(load_vault(paths.root), repository)

    assert metric.attempts_total == 1
    assert metric.attempts_scored == 0
    assert metric.attempts_without_contract == 1
    # Never a fake 1.0 (3.1's discipline).
    assert metric.cell_hit_rate is None
    assert metric.facet_hit_rate is None


def test_hit_rate_since_window_scopes_to_new_attempts(tmp_path):
    # Item 5.1's hypothesis is about the hit rate of *new* attempts.
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [(INSTRUMENT_FACET, "procedure_execution", "hard")])
    _author_item(paths, "pi_on_cell", capability="procedure_execution", facet=INSTRUMENT_FACET)
    _author_item(paths, "pi_wrong_rung", capability="retrieval", facet=INSTRUMENT_FACET)
    repository = Repository(paths.sqlite_path)
    repository.insert_practice_attempt(
        _attempt("old", "pi_wrong_rung", created_at="2026-01-01T00:00:00Z")
    )
    repository.insert_practice_attempt(
        _attempt("new", "pi_on_cell", created_at="2026-06-01T00:00:00Z")
    )
    vault = load_vault(paths.root)

    everything = contract_cell_hit_rate(vault, repository)
    windowed = contract_cell_hit_rate(vault, repository, since="2026-05-01T00:00:00Z")

    assert everything.attempts_scored == 2
    assert everything.cell_hit_rate == 0.5
    assert windowed.attempts_scored == 1
    assert windowed.cell_hit_rate == 1.0


def test_unrubricked_item_is_not_scored_as_a_miss(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [(INSTRUMENT_FACET, "procedure_execution", "hard")])
    item_path = paths.practice_item_path("linear-algebra", "pi_svd_define_001")
    data = read_yaml(item_path)
    data["grading_rubric"] = None
    data["practice_mode"] = "mode_without_default_rubric"
    data["updated_at"] = NOW_ISO
    write_yaml(item_path, data)
    repository = Repository(paths.sqlite_path)
    repository.insert_practice_attempt(_attempt("a1", "pi_svd_define_001"))
    vault = load_vault(paths.root)

    assert item_observed_cells(vault, vault.practice_items["pi_svd_define_001"]) is None
    metric = contract_cell_hit_rate(vault, repository)
    assert metric.attempts_scored == 0
    assert metric.attempts_unrubricked == 1


def test_cli_contract_hit_rate(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [(INSTRUMENT_FACET, "procedure_execution", "hard")])
    _author_item(paths, "pi_wrong_rung", capability="retrieval", facet=INSTRUMENT_FACET)
    Repository(paths.sqlite_path).insert_practice_attempt(_attempt("a1", "pi_wrong_rung"))
    runner = CliRunner()

    result = runner.invoke(app, ["contract-hit-rate", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["cell_hit_rate"] == 0.0
    assert payload["rung_loss_share"] == 1.0

    human = runner.invoke(app, ["contract-hit-rate", "--vault", str(paths.root)])
    assert human.exit_code == 0
    assert "contract-cell hits" in human.output
    assert "rung loss" in human.output
