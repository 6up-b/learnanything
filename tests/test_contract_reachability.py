"""Contract-cell reachability (spec_measurement_efficiency_v1 §5.8.2, plan 3.1).

The check whose absence let 43 attempts land on contracts no authored item could
close. Everything here is static: no attempts, no learner state, no provider.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.learner.contract_reachability import (
    ReachabilityVerdict,
    analyze_contract_reachability,
    classify_cell,
)
from learnloop.ops.doctor import run_doctor
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


# The basic vault's only item is `short_answer` on facet "recall", which compiles
# to capability `schema_interpretation` (capability_mapping.MODE_CAPABILITY_DEFAULTS).
# Every cell below is positioned relative to that single instrument, so the four
# verdicts fall out of the ladder alone:
#   retrieval(0) < schema_interpretation(1) < procedure_execution(2)
#     < method_selection(3) < coordination(4)
INSTRUMENT_CAPABILITY = "schema_interpretation"
INSTRUMENT_FACET = "recall"
INSTRUMENT_ID = "pi_svd_define_001"


def _write_blueprint(paths, components, *, integration=None, recipe_id="r1"):
    """Give ``lo_svd_definition`` one blueprint with the given components.

    ``components`` are ``(facet, capability, modality)`` triples for ``all_of``;
    ``integration`` is an optional ``(facet, capability)`` pair.
    """

    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
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


def _four_verdict_vault(tmp_path):
    """One LO whose four contract cells realize the four §5.8.2 verdicts."""

    paths = create_basic_vault(tmp_path / "vault")
    return _write_blueprint(
        paths,
        [
            # observed at exactly this capability -> REACHABLE
            (INSTRUMENT_FACET, "schema_interpretation", "hard"),
            # the instrument sits one rung ABOVE this requirement -> MISMATCH_ABOVE
            (INSTRUMENT_FACET, "retrieval", "hard"),
            # the instrument sits below this requirement -> MISMATCH_BELOW
            (INSTRUMENT_FACET, "coordination", "hard"),
            # nothing observes this facet at all -> NO_INSTRUMENT
            ("uninstrumented_facet", "procedure_execution", "hard"),
        ],
    )


def _rows_by_cell(report):
    return {
        (row.cell.facet_id, row.cell.capability): row for row in report.cells
    }


def test_four_verdicts_on_purpose_built_vault(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    report = analyze_contract_reachability(load_vault(paths.root))
    rows = _rows_by_cell(report)

    reachable = rows[(INSTRUMENT_FACET, "schema_interpretation")]
    assert reachable.verdict is ReachabilityVerdict.REACHABLE
    assert reachable.matching_instrument_ids == (INSTRUMENT_ID,)
    assert reachable.observed_capabilities == (INSTRUMENT_CAPABILITY,)
    assert reachable.remedy == "none"

    above = rows[(INSTRUMENT_FACET, "retrieval")]
    assert above.verdict is ReachabilityVerdict.MISMATCH_ABOVE
    assert above.matching_instrument_ids == ()
    assert above.instrument_ids == (INSTRUMENT_ID,)
    assert above.nearest_above == "schema_interpretation"
    assert above.nearest_below is None
    assert above.remedy == "propagate_downward_dominance"

    below = rows[(INSTRUMENT_FACET, "coordination")]
    assert below.verdict is ReachabilityVerdict.MISMATCH_BELOW
    assert below.matching_instrument_ids == ()
    assert below.instrument_ids == (INSTRUMENT_ID,)
    assert below.nearest_below == "schema_interpretation"
    assert below.nearest_above is None
    assert below.remedy == "author_instrument_at_required_capability"

    missing = rows[("uninstrumented_facet", "procedure_execution")]
    assert missing.verdict is ReachabilityVerdict.NO_INSTRUMENT
    assert missing.observed_capabilities == ()
    assert missing.instrument_ids == ()
    assert missing.remedy == "author_instrument_for_facet"


def test_aggregate_counts_and_shares(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    report = analyze_contract_reachability(load_vault(paths.root))
    summary = report.summary()

    assert summary["cell_count"] == 4
    assert summary["counts"] == {
        "REACHABLE": 1,
        "MISMATCH_ABOVE": 1,
        "MISMATCH_BELOW": 1,
        "NO_INSTRUMENT": 1,
        "INDETERMINATE": 0,
    }
    assert summary["reachable_count"] == 1
    assert summary["unreachable_count"] == 3
    assert summary["reachable_share"] == 0.25
    assert summary["learning_object_count"] == 1
    assert summary["learning_objects_total"] == 1
    assert summary["instrument_count"] == 1
    assert summary["unrubricked_item_count"] == 0
    assert summary["integration_cell_count"] == 0
    assert summary["integration_reachable_share"] is None


def test_commissioning_queue_excludes_reachable_and_orders_cheapest_first(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    report = analyze_contract_reachability(load_vault(paths.root))

    queue = report.commissioning_queue()
    assert [str(row.verdict) for row in queue] == [
        "MISMATCH_ABOVE",
        "MISMATCH_BELOW",
        "NO_INSTRUMENT",
    ]
    # Every queue row carries the identity Stage 5.1 acts on without re-reading
    # the vault: the contract, the facet, the required capability, what is
    # available, and the remedy.
    payload = queue[0].as_dict()
    assert payload["learning_object_id"] == "lo_svd_definition"
    assert payload["facet_id"] == INSTRUMENT_FACET
    assert payload["required_capability"] == "retrieval"
    assert payload["observed_capabilities"] == [INSTRUMENT_CAPABILITY]
    assert payload["recipe_refs"] == ["bp1:r1"]
    assert payload["component_roles"] == ["all_of"]
    assert payload["verdict"] == "MISMATCH_ABOVE"


def test_mismatch_above_wins_when_observed_both_sides():
    # A facet observed above AND below the requirement is reported ABOVE: the
    # cheap remedy (propagate what exists) applies, and calling it a below-
    # shortfall would commission an instrument that is not needed.
    assert (
        classify_cell("procedure_execution", ["retrieval", "coordination"])
        is ReachabilityVerdict.MISMATCH_ABOVE
    )


def test_classify_cell_ladder_direction_and_abstention():
    # The ladder runs low -> high in CAPABILITY_VOCABULARY order.
    assert classify_cell("retrieval", ["coordination"]) is ReachabilityVerdict.MISMATCH_ABOVE
    assert classify_cell("coordination", ["retrieval"]) is ReachabilityVerdict.MISMATCH_BELOW
    assert classify_cell("retrieval", ["retrieval"]) is ReachabilityVerdict.REACHABLE
    assert classify_cell("retrieval", []) is ReachabilityVerdict.NO_INSTRUMENT
    # Explicit abstention arm: an out-of-vocabulary requirement cannot be placed
    # on the ladder, so no above/below claim is made and it is never reachable.
    verdict = classify_cell("not_a_capability", ["retrieval"])
    assert verdict is ReachabilityVerdict.INDETERMINATE
    assert verdict.reachable is False
    # Nothing comparable observes the facet -> the honest no-instrument arm.
    assert classify_cell("retrieval", ["not_a_capability"]) is ReachabilityVerdict.NO_INSTRUMENT


def test_indeterminate_capability_is_counted_but_never_reachable(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(paths, [(INSTRUMENT_FACET, "not_a_capability", "hard")])
    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.counts["INDETERMINATE"] == 1
    assert report.reachable_count == 0
    assert report.cells[0].remedy == "repair_blueprint_capability"


def test_advisory_modality_is_not_a_contract_cell(tmp_path):
    # knowledge-model §8.2: only hard / exercised path_specific requirements
    # materially bind. Counting facilitating components as contract cells is what
    # inflated the raw component count (68) above §5.8.2's 64 contract cells.
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(
        paths,
        [
            (INSTRUMENT_FACET, "coordination", "hard"),
            ("helper_facet", "coordination", "facilitating"),
            ("path_facet", "coordination", "path_specific"),
        ],
    )
    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.cell_count == 2
    assert report.advisory_component_count == 1
    assert {row.cell.facet_id for row in report.cells} == {INSTRUMENT_FACET, "path_facet"}


def test_integration_cell_is_tracked_separately(tmp_path):
    # §5.8.2/§5.8.3: 18 of 19 integration components sat at `coordination`, zero
    # instruments observed it, and that alone made 20 of 21 LOs uncertifiable.
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(
        paths,
        [(INSTRUMENT_FACET, "schema_interpretation", "hard")],
        integration=("assembly_facet", "coordination"),
    )
    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.cell_count == 2
    assert report.integration_cell_count == 1
    assert report.integration_counts["NO_INSTRUMENT"] == 1
    assert report.integration_reachable_share == 0.0
    integration_row = next(row for row in report.cells if row.cell.integration)
    assert integration_row.cell.component_roles == ("integration",)


def test_retired_items_are_not_instruments(tmp_path):
    # A retired item cannot be scheduled, so it cannot close a cell. (On
    # fixtures/linear_algebra this is the difference between 15 and 14
    # instrumented facets.)
    paths = _four_verdict_vault(tmp_path)
    item_path = paths.practice_item_path("linear-algebra", INSTRUMENT_ID)
    data = read_yaml(item_path)
    data["status"] = "retired"
    write_yaml(item_path, data)

    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.instrument_count == 0
    assert report.counts["NO_INSTRUMENT"] == 4
    assert report.reachable_count == 0
    # The seam still allows asking the counterfactual explicitly.
    revived = analyze_contract_reachability(
        load_vault(paths.root), statuses=("active", "retired")
    )
    assert revived.counts["REACHABLE"] == 1


def test_legacy_vault_without_contracts_reports_empty_not_perfect(tmp_path):
    # A vault whose LOs declare no blueprints has nothing to certify. The report
    # must be empty rather than crash or claim a fake 100%.
    paths = create_basic_vault(tmp_path / "vault")
    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.cells == ()
    assert report.cell_count == 0
    assert report.reachable_share is None
    assert report.integration_reachable_share is None
    assert report.learning_objects_total == 1
    assert report.learning_object_count == 0
    assert report.counts == {
        "REACHABLE": 0,
        "MISMATCH_ABOVE": 0,
        "MISMATCH_BELOW": 0,
        "NO_INSTRUMENT": 0,
        "INDETERMINATE": 0,
    }
    assert report.commissioning_queue() == ()

    doctor_report = run_doctor(paths.root, fix_state=True)
    assert doctor_report.contract_reachability is None
    assert not [
        issue for issue in doctor_report.issues if issue.code.startswith("contract_cell:")
    ]


def test_report_is_deterministic(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    vault = load_vault(paths.root)

    first = analyze_contract_reachability(vault).as_dict()
    second = analyze_contract_reachability(vault).as_dict()
    reloaded = analyze_contract_reachability(load_vault(paths.root)).as_dict()

    serialized = json.dumps(first, sort_keys=True)
    assert serialized == json.dumps(second, sort_keys=True)
    assert serialized == json.dumps(reloaded, sort_keys=True)
    # Cell order itself is pinned (LO, capability rank, capability, facet), not
    # just the set of cells.
    assert [(row["facet_id"], row["required_capability"]) for row in first["cells"]] == [
        ("recall", "retrieval"),
        ("recall", "schema_interpretation"),
        ("uninstrumented_facet", "procedure_execution"),
        ("recall", "coordination"),
    ]


def test_recipe_duplicate_cells_collapse_to_one_obligation(tmp_path):
    # The same (facet, capability) requirement repeated across recipes is one
    # commissioning obligation, not two.
    paths = create_basic_vault(tmp_path / "vault")
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_definition")
    data = read_yaml(lo_path)
    component = {"facet": INSTRUMENT_FACET, "capability": "coordination", "modality": "hard"}
    data["blueprints"] = [
        {
            "id": "bp1",
            "weight": 1.0,
            "recipes": [
                {"id": "r1", "composition": "conjunctive", "all_of": [component]},
                {"id": "r2", "composition": "conjunctive", "any_of": [component]},
            ],
        }
    ]
    write_yaml(lo_path, data)

    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.cell_count == 1
    cell = report.cells[0].cell
    assert cell.component_roles == ("all_of", "any_of")
    assert cell.recipe_refs == ("bp1:r1", "bp1:r2")


def test_doctor_reports_unreachable_cells_as_review_warnings(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    report = run_doctor(paths.root, fix_state=True)

    by_code = {
        issue.code: issue for issue in report.issues if issue.code.startswith("contract_cell:")
    }
    assert set(by_code) == {
        "contract_cell:mismatch_above",
        "contract_cell:mismatch_below",
        "contract_cell:no_instrument",
    }
    # Reportable, never fatal: an unreachable cell is valid content carrying an
    # authoring obligation, so it uses the same review severity as the
    # identifiability doctor (§11.3) rather than blocking the vault.
    assert {issue.severity for issue in by_code.values()} == {"warning"}
    assert report.error_count == 0

    no_instrument = by_code["contract_cell:no_instrument"]
    assert no_instrument.entity_id == "lo_svd_definition"
    assert no_instrument.details["cell_count"] == 1
    assert no_instrument.details["verdict"] == "NO_INSTRUMENT"
    assert no_instrument.details["cells"][0]["facet_id"] == "uninstrumented_facet"
    assert "Author an instrument" in no_instrument.details["suggested_action"]

    # The aggregate rides on the doctor report so `doctor --json` states §5.8's
    # proportions without a second pass.
    assert report.contract_reachability["cell_count"] == 4
    assert report.contract_reachability["reachable_share"] == 0.25
    assert report.as_dict()["contract_reachability"] == report.contract_reachability


def test_doctor_groups_cells_by_learning_object_and_verdict(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    _write_blueprint(
        paths,
        [
            (INSTRUMENT_FACET, "coordination", "hard"),
            (INSTRUMENT_FACET, "method_selection", "hard"),
        ],
    )
    report = run_doctor(paths.root, fix_state=True)

    grouped = [issue for issue in report.issues if issue.code == "contract_cell:mismatch_below"]
    assert len(grouped) == 1
    assert grouped[0].details["cell_count"] == 2


def test_cli_contract_reachability_json_and_exit_code(tmp_path):
    paths = _four_verdict_vault(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["contract-reachability", "--vault", str(paths.root), "--json"])

    # A report, not a gate: always exits 0 even with an uncloseable contract.
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["summary"]["counts"]["NO_INSTRUMENT"] == 1
    assert payload["summary"]["reachable_share"] == 0.25
    # Default JSON body is the commissioning queue (unreachable cells only).
    assert {row["verdict"] for row in payload["cells"]} == {
        "MISMATCH_ABOVE",
        "MISMATCH_BELOW",
        "NO_INSTRUMENT",
    }

    every = runner.invoke(
        app, ["contract-reachability", "--vault", str(paths.root), "--json", "--all"]
    )
    assert every.exit_code == 0
    assert len(json.loads(every.output)["cells"]) == 4

    human = runner.invoke(app, ["contract-reachability", "--vault", str(paths.root)])
    assert human.exit_code == 0
    assert "4 contract cell(s)" in human.output
    assert "reachable 1/4 (25%)" in human.output


def test_cli_contract_reachability_on_vault_without_contracts(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    runner = CliRunner()

    result = runner.invoke(app, ["contract-reachability", "--vault", str(paths.root)])

    assert result.exit_code == 0
    assert "No contract cells" in result.output
    assert "not a clean bill" in result.output


def test_unrubricked_items_are_counted_not_silently_dropped(tmp_path):
    # An item with no resolvable rubric cannot be graded, so it observes nothing;
    # the count makes that visible instead of reading as a facet nobody authored.
    paths = _four_verdict_vault(tmp_path)
    item_path = paths.practice_item_path("linear-algebra", INSTRUMENT_ID)
    data = read_yaml(item_path)
    data["grading_rubric"] = None
    data["practice_mode"] = "mode_without_default_rubric"
    data["updated_at"] = NOW_ISO
    write_yaml(item_path, data)

    report = analyze_contract_reachability(load_vault(paths.root))

    assert report.unrubricked_item_count == 1
    assert report.instrument_count == 0
    assert report.counts["NO_INSTRUMENT"] == 4
