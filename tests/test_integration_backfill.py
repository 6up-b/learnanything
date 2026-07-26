"""D3's integration criterion applied to persisted blueprints (plan item 5.2).

D3 (spec_measurement_efficiency_v1 §6, sibling rule to D2) shipped at ingest;
§5.8.3 recorded that it "does not repair existing vaults" because blueprints are
vault content and no rebuild touches them. These tests pin the retroactive pass:
each arm of the criterion, the typed reason it produces, and the fact that the
write side is diff-first because it edits hand-authored files.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.services.contract_reachability import analyze_contract_reachability
from learnloop.services.integration_backfill import (
    DEEPEST_AUTHORABLE_CAPABILITY,
    IntegrationDisposition,
    IntegrationReason,
    apply_integration_backfill,
    coordination_is_observable,
    plan_integration_backfill,
)
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault

LO_ID = "lo_svd_definition"
INSTRUMENT_FACET = "recall"


def _write_recipe(paths, *, all_of, integration, any_of=(), recipe_id="r1"):
    """One blueprint recipe on ``lo_svd_definition``.

    ``all_of`` / ``any_of`` are ``(facet, capability, modality)`` triples;
    ``integration`` is ``(facet, capability)``.
    """

    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    data = read_yaml(lo_path)
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {
                    "id": recipe_id,
                    "composition": "conjunctive",
                    "all_of": [
                        {"facet": facet, "capability": capability, "modality": modality}
                        for facet, capability, modality in all_of
                    ],
                    "any_of": [
                        {"facet": facet, "capability": capability, "modality": modality}
                        for facet, capability, modality in any_of
                    ],
                    "integration": {
                        "facet": integration[0],
                        "capability": integration[1],
                        "modality": "hard",
                    },
                }
            ],
        }
    ]
    write_yaml(lo_path, data)
    return paths


def _judge_one(paths):
    report = plan_integration_backfill(load_vault(paths.root))
    (verdict,) = report.verdicts
    return verdict, report


# -- D3 criterion 1: is the assembly failure nameable? -------------------------


def test_drop_when_the_integration_facet_duplicates_a_component(tmp_path):
    """The dominant shape on the measured vault: 14 of 19 components.

    The integration names the SAME facet as one of the recipe's own components, one
    rung deeper. D3 requires the assembly failure to be "separately repairable" —
    repairing this one is repairing that component's facet, so there is no distinct
    obligation and "omission is the correct output, not a gap".
    """

    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "procedure_execution", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    verdict, _ = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.DROP
    assert verdict.reason is IntegrationReason.FACET_DUPLICATES_COMPONENT
    assert verdict.lowered_capability is None
    assert verdict.owed_capstone is False
    assert verdict.component_facets == (INSTRUMENT_FACET, "second_facet")


def test_drop_when_fewer_than_two_binding_components(tmp_path):
    # "A learner could hold every all_of component and still fail" presupposes at
    # least two parts to assemble. `facilitating` components never gate anything
    # (knowledge-model §8.2), so they do not count toward the two.
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("only_binding_facet", "schema_interpretation", "hard"),
            ("advisory_facet", "procedure_execution", "facilitating"),
        ],
        integration=("assembly_facet", "coordination"),
    )
    verdict, _ = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.DROP
    assert verdict.reason is IntegrationReason.NO_ASSEMBLY_TO_FAIL
    assert verdict.binding_component_count == 1


def test_criterion_one_is_capability_independent(tmp_path):
    # D3: "Absent (1), omit the component" — with no reference to the rung it
    # claimed. A duplicate-facet integration at an *observable* capability is still
    # dropped, which is why the pass reports the one `method_selection` integration
    # §5.8.3 highlighted rather than exempting it.
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "method_selection"),
    )
    verdict, _ = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.DROP
    assert verdict.reason is IntegrationReason.FACET_DUPLICATES_COMPONENT


# -- D3 criterion 2: is the capability observable? -----------------------------


def test_lower_when_coordination_is_unobservable_and_a_deeper_authorable_rung_exists(tmp_path):
    """§5.8.3's "lowered to an observable rung" arm.

    A real assembly (three distinct binding components, a fourth distinct facet as
    the integration), coordination unobservable, and the trajectory tip is still
    strictly deeper than every part — so the assembly claim survives at a rung an
    instrument can reach.
    """

    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "procedure_execution", "hard"),
            ("third_facet", "procedure_execution", "hard"),
        ],
        integration=("assembly_facet", "coordination"),
    )
    verdict, report = _judge_one(paths)

    assert report.coordination_observed is False
    assert verdict.disposition is IntegrationDisposition.LOWER
    assert verdict.reason is IntegrationReason.LOWERED_TO_DEEPEST_AUTHORABLE
    assert verdict.lowered_capability == DEEPEST_AUTHORABLE_CAPABILITY == "method_selection"
    assert verdict.deepest_component_capability == "procedure_execution"


def test_keep_and_flag_when_no_observable_rung_is_deeper_than_the_parts(tmp_path):
    """The "genuinely coordination" arm, owed an A1 capstone (plan item 6.1).

    A component already sits at the trajectory tip, so lowering the integration
    would put it at or below a part it assembles — no longer an assembly claim at
    all. §5.8.3 keeps these deliberately: the component "announces the obligation
    it creates rather than creating it silently".
    """

    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "method_selection", "hard"),
        ],
        integration=("assembly_facet", "coordination"),
    )
    verdict, report = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.KEEP
    assert verdict.reason is IntegrationReason.OWED_WHOLE_TASK_CAPSTONE
    assert verdict.owed_capstone is True
    assert report.owed_capstones == (verdict,)
    assert report.summary()["owed_capstones"] == [LO_ID]
    # Nothing to write.
    assert apply_integration_backfill(load_vault(paths.root), report.verdicts) == ()


def test_keep_when_the_capability_is_already_observable(tmp_path):
    # An integration at a default-trajectory capability is authorable by
    # definition, so criterion 2 is satisfied and D3 has no complaint.
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=("assembly_facet", "procedure_execution"),
    )
    verdict, _ = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.KEEP
    assert verdict.reason is IntegrationReason.CAPABILITY_OBSERVABLE


def test_coordination_becomes_keepable_once_an_instrument_observes_it(tmp_path):
    """Criterion 2 is measured, not assumed.

    §5.8.2: "Zero of 55 items observe ``coordination``". Once an A1 whole-task
    capstone exists the same code stops lowering, with no flag flipped — which is
    what makes this a criterion rather than a policy.
    """

    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "procedure_execution", "hard"),
        ],
        integration=("assembly_facet", "coordination"),
    )
    assert _judge_one(paths)[0].disposition is IntegrationDisposition.LOWER

    template = read_yaml(paths.practice_item_path("linear-algebra", "pi_svd_define_001"))
    template.update(
        {
            "id": "pi_svd_capstone",
            "practice_mode": "constructed_response",
            "capability": "coordination",
            "evidence_facets": ["assembly_facet"],
            "evidence_weights": {"assembly_facet": 1.0},
            "prompt": "Carry out the whole SVD workflow end to end and justify each choice.",
            "surface_family": "svd_whole_task",
            "updated_at": NOW_ISO,
        }
    )
    write_yaml(paths.practice_item_path("linear-algebra", "pi_svd_capstone"), template)

    assert coordination_is_observable(load_vault(paths.root)) is True
    verdict, _ = _judge_one(paths)
    assert verdict.disposition is IntegrationDisposition.KEEP
    assert verdict.reason is IntegrationReason.CAPABILITY_OBSERVABLE


def test_out_of_vocabulary_capability_abstains(tmp_path):
    # Unplaceable on the ladder: no lowering target is defined, and this is 3.1's
    # `repair_blueprint_capability`, not D3's business.
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "procedure_execution", "hard"),
        ],
        integration=("assembly_facet", "not_a_capability"),
    )
    verdict, _ = _judge_one(paths)

    assert verdict.disposition is IntegrationDisposition.KEEP
    assert verdict.reason is IntegrationReason.CAPABILITY_OUTSIDE_VOCABULARY
    assert verdict.lowered_capability is None


# -- scoping and the write side ------------------------------------------------


def test_capability_scope_keeps_the_plans_stated_batch_honest(tmp_path):
    # Item 5.2's scope is "the 18 persisted **coordination** integrations".
    # Sweeping in a `method_selection` integration would be a different decision.
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "method_selection"),
    )
    vault = load_vault(paths.root)

    assert plan_integration_backfill(vault, capabilities=["coordination"]).verdicts == ()
    assert len(plan_integration_backfill(vault).verdicts) == 1


def test_learning_object_scope_is_the_pilot_seam(tmp_path):
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    vault = load_vault(paths.root)

    assert plan_integration_backfill(vault, learning_object_ids=["lo_other"]).verdicts == ()
    assert len(plan_integration_backfill(vault, learning_object_ids=[LO_ID]).verdicts) == 1


def test_apply_is_diff_only_by_default(tmp_path):
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    before = lo_path.read_text(encoding="utf-8")
    vault = load_vault(paths.root)
    report = plan_integration_backfill(vault)

    (edit,) = apply_integration_backfill(vault, report.verdicts)

    assert lo_path.read_text(encoding="utf-8") == before
    assert edit.learning_object_id == LO_ID
    assert "-          capability: coordination" in edit.diff
    assert edit.applied_verdicts == report.verdicts


def test_apply_writes_a_drop_as_an_explicit_null(tmp_path):
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    vault = load_vault(paths.root)
    report = plan_integration_backfill(vault)

    apply_integration_backfill(vault, report.verdicts, dry_run=False)

    raw = read_yaml(paths.learning_object_path("linear-algebra", LO_ID))
    recipe = raw["blueprints"][0]["recipes"][0]
    # The key survives as a null, which is how a recipe with no integration
    # component is already persisted in the tree — the diff shows the decision.
    assert "integration" in recipe
    assert recipe["integration"] is None
    reloaded = load_vault(paths.root)
    assert reloaded.learning_objects[LO_ID].blueprints[0].recipes[0].integration is None
    # Idempotent: re-running finds nothing left to judge.
    assert plan_integration_backfill(reloaded).verdicts == ()


def test_apply_lowers_the_capability_in_place(tmp_path):
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            ("first_facet", "schema_interpretation", "hard"),
            ("second_facet", "procedure_execution", "hard"),
        ],
        integration=("assembly_facet", "coordination"),
    )
    vault = load_vault(paths.root)
    report = plan_integration_backfill(vault)
    apply_integration_backfill(vault, report.verdicts, dry_run=False)

    reloaded = load_vault(paths.root)
    integration = reloaded.learning_objects[LO_ID].blueprints[0].recipes[0].integration
    assert integration is not None
    assert integration.capability == "method_selection"
    assert integration.facet == "assembly_facet"
    # The cell survives (still one integration cell) but is now on the authorable
    # trajectory — §5.8.3: the fix "does not move the reachable-cell count at all".
    after = analyze_contract_reachability(reloaded)
    assert after.integration_cell_count == 1
    assert [row.cell.capability for row in after.cells if row.cell.integration] == [
        "method_selection"
    ]


def test_drop_removes_the_cell_without_moving_the_reachable_count(tmp_path):
    """§5.8.3's measured shape: "it removes a third of the contract cells outright
    — but it does not move the reachable-cell count at all"."""

    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    before = analyze_contract_reachability(load_vault(paths.root))
    vault = load_vault(paths.root)
    apply_integration_backfill(vault, plan_integration_backfill(vault).verdicts, dry_run=False)
    after = analyze_contract_reachability(load_vault(paths.root))

    assert (before.cell_count, before.reachable_count) == (3, 1)
    assert (after.cell_count, after.reachable_count) == (2, 1)
    assert after.integration_cell_count == 0
    assert before.reachable_share == 1 / 3
    assert after.reachable_share == 0.5


def test_cli_integration_backfill_diff_then_apply(tmp_path):
    paths = _write_recipe(
        create_basic_vault(tmp_path / "vault"),
        all_of=[
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            ("second_facet", "schema_interpretation", "hard"),
        ],
        integration=(INSTRUMENT_FACET, "coordination"),
    )
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    before = lo_path.read_text(encoding="utf-8")
    runner = CliRunner()

    dry = runner.invoke(app, ["integration-backfill", "--vault", str(paths.root), "--json"])
    assert dry.exit_code == 0
    payload = json.loads(dry.output)
    assert payload["applied"] is False
    assert payload["summary"]["dispositions"] == {"KEEP": 0, "LOWER": 0, "DROP": 1}
    assert payload["verdicts"][0]["reason"] == "facet_duplicates_component"
    assert lo_path.read_text(encoding="utf-8") == before

    applied = runner.invoke(
        app, ["integration-backfill", "--vault", str(paths.root), "--json", "--apply"]
    )
    assert applied.exit_code == 0
    assert json.loads(applied.output)["applied"] is True
    assert lo_path.read_text(encoding="utf-8") != before

    human = runner.invoke(app, ["integration-backfill", "--vault", str(paths.root)])
    assert human.exit_code == 0
    assert "0 file(s) would change" in human.output
