"""Plan 8.1: static cells-converted precheck before building B1 or B3."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.learner.inference_precheck import analyze_inference_precheck
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW_ISO, create_basic_vault


UPSTREAM_CONCEPT = "singular_value_decomposition"
DOWNSTREAM_CONCEPT = "downstream_application"
UPSTREAM_LO = "lo_svd_definition"
DOWNSTREAM_LO = "lo_downstream_application"


def _precheck_vault(tmp_path, *, modality: str | None):
    paths = create_basic_vault(tmp_path / "vault")

    concepts = read_yaml(paths.concepts_path)
    concepts["concepts"][DOWNSTREAM_CONCEPT] = {
        "title": "Downstream application",
        "type": "skill",
        "aliases": [],
        "description": "Uses the prerequisite.",
        "tags": [],
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.concepts_path, concepts)

    upstream_path = paths.learning_object_path("linear-algebra", UPSTREAM_LO)
    upstream = read_yaml(upstream_path)
    upstream["blueprints"] = [
        {
            "id": "bp_upstream",
            "recipes": [
                {
                    "id": "r_upstream",
                    "composition": "conjunctive",
                    "all_of": [
                        {
                            # The existing item observes recall at
                            # schema_interpretation: B1 can carry it down.
                            "facet": "recall",
                            "capability": "retrieval",
                            "modality": "hard",
                        },
                        {
                            # No instrument observes this; only B3 can move it.
                            "facet": "unobserved_upstream",
                            "capability": "procedure_execution",
                            "modality": "hard",
                        },
                    ],
                }
            ],
        }
    ]
    write_yaml(upstream_path, upstream)

    write_yaml(
        paths.learning_object_path("linear-algebra", DOWNSTREAM_LO),
        {
            "schema_version": 1,
            "id": DOWNSTREAM_LO,
            "title": "Downstream application",
            "subjects": ["linear-algebra"],
            "concept": DOWNSTREAM_CONCEPT,
            "knowledge_type": "procedure",
            "status": "active",
            "contradicts": None,
            "summary": "Apply the prerequisite downstream.",
            "prerequisites": [UPSTREAM_CONCEPT],
            "confusables": [],
            "blueprints": [
                {
                    "id": "bp_downstream",
                    "recipes": [
                        {
                            "id": "r_downstream",
                            "composition": "conjunctive",
                            "all_of": [
                                {
                                    "facet": "downstream_execution",
                                    "capability": "procedure_execution",
                                    "modality": "hard",
                                }
                            ],
                        }
                    ],
                }
            ],
            "tags": [],
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_downstream"),
        {
            "schema_version": 1,
            "id": "pi_downstream",
            "learning_object_id": DOWNSTREAM_LO,
            "subjects": None,
            "practice_mode": "worked_problem",
            "capability": "procedure_execution",
            "attempt_types_allowed": ["independent_attempt"],
            "evidence_facets": ["downstream_execution"],
            "evidence_weights": {"downstream_execution": 1.0},
            "prompt": "Apply it.",
            "expected_answer": "A valid downstream application.",
            "difficulty": 0.5,
            "status": "active",
            "tags": [],
            "hints": [],
            "grading_rubric": {
                "max_points": 1,
                "criteria": [
                    {
                        "id": "apply",
                        "points": 1,
                        "description": "Applies correctly.",
                        "targets": [
                            {
                                "facet": "downstream_execution",
                                "capability": "procedure_execution",
                                "role": "primary",
                            }
                        ],
                    }
                ],
                "fatal_errors": [],
            },
            "provenance": {"origin": "human", "source_refs": []},
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
        },
    )

    edge = {
        "id": "edge_upstream_downstream",
        "relation_type": "prerequisite",
        "source": UPSTREAM_CONCEPT,
        "target": DOWNSTREAM_CONCEPT,
        "strength": 0.9,
        "rationale": "Required by the downstream application.",
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    if modality is not None:
        edge["modality"] = modality
    write_yaml(paths.relations_path, {"schema_version": 1, "edges": [edge]})
    return paths


def test_b1_counts_exactly_mismatch_above_and_combined_union_deduplicates(tmp_path):
    paths = _precheck_vault(tmp_path, modality="hard")
    report = analyze_inference_precheck(load_vault(paths.root))
    summary = report.summary()

    assert summary["baseline"]["counts"]["MISMATCH_ABOVE"] == 1
    assert summary["capability_dominance"]["cells_converted"] == 1
    assert summary["capability_dominance"]["moves_count"] is True
    assert report.dominance[0].cell.key == (UPSTREAM_LO, "recall", "retrieval")
    assert report.dominance[0].source_capabilities == ("schema_interpretation",)
    assert report.dominance[0].source_instrument_ids == ("pi_svd_define_001",)

    # B3 can move both upstream gaps, but the recall cell overlaps B1. The
    # combined answer is a set union, never 1 + 2.
    assert summary["prerequisite_entailment"]["cells_converted"] == 2
    assert summary["combined"]["cells_converted"] == 2


def test_untyped_and_instructional_edges_convert_nothing(tmp_path):
    untyped = analyze_inference_precheck(
        load_vault(_precheck_vault(tmp_path / "untyped", modality=None).root)
    )
    instructional = analyze_inference_precheck(
        load_vault(
            _precheck_vault(
                tmp_path / "instructional", modality="instructional_order"
            ).root
        )
    )

    assert untyped.summary()["prerequisite_entailment"]["cells_converted"] == 0
    assert untyped.summary()["prerequisite_entailment"]["disposition_counts"] == {
        "UNTYPED": 1
    }
    assert instructional.summary()["prerequisite_entailment"]["cells_converted"] == 0
    assert instructional.summary()["prerequisite_entailment"]["disposition_counts"] == {
        "INSTRUCTIONAL_ORDER": 1
    }


def test_path_specific_is_conditional_not_a_guaranteed_conversion(tmp_path):
    paths = _precheck_vault(tmp_path, modality="path_specific")
    report = analyze_inference_precheck(load_vault(paths.root))
    b3 = report.summary()["prerequisite_entailment"]

    assert b3["cells_converted"] == 0
    assert b3["conditional_cells"] == 2
    assert b3["maximum_cells_converted"] == 2
    assert all(row.conditional_only for row in report.entailment)
    assert b3["disposition_counts"] == {"CONDITIONAL_ON_PATH": 1}


def test_b3_requires_a_directly_reachable_downstream_anchor(tmp_path):
    paths = _precheck_vault(tmp_path, modality="hard")
    item_path = paths.practice_item_path("linear-algebra", "pi_downstream")
    item = read_yaml(item_path)
    item["status"] = "retired"
    write_yaml(item_path, item)

    report = analyze_inference_precheck(load_vault(paths.root))
    b3 = report.summary()["prerequisite_entailment"]

    assert b3["cells_converted"] == 0
    assert b3["disposition_counts"] == {"NO_DOWNSTREAM_DIRECT_ANCHOR": 1}


def test_report_is_static_deterministic_and_empty_contracts_are_not_perfect(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    first = analyze_inference_precheck(vault).as_dict()
    second = analyze_inference_precheck(vault).as_dict()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
    assert first["summary"]["baseline"]["cell_count"] == 0
    assert first["summary"]["capability_dominance"]["share_of_all_cells"] is None
    assert first["summary"]["prerequisite_entailment"]["share_of_all_cells"] is None
    assert first["summary"]["combined"]["moves_count"] is False


def test_cli_exposes_stable_machine_and_human_precheck(tmp_path):
    paths = _precheck_vault(tmp_path, modality="hard")
    runner = CliRunner()

    machine = runner.invoke(
        app, ["inference-precheck", "--vault", str(paths.root), "--json"]
    )
    assert machine.exit_code == 0, machine.stdout
    payload = json.loads(machine.stdout)
    assert payload["version"] == 1
    assert payload["summary"]["capability_dominance"]["cells_converted"] == 1
    assert payload["summary"]["prerequisite_entailment"]["cells_converted"] == 2
    assert payload["summary"]["combined"]["cells_converted"] == 2

    human = runner.invoke(app, ["inference-precheck", "--vault", str(paths.root)])
    assert human.exit_code == 0, human.stdout
    assert "B1 capability dominance: 1 cell(s) converted" in human.stdout
    assert "B3 prerequisite entailment: 2 hard-edge cell(s) converted" in human.stdout
    assert "Combined, deduplicated: 2 guaranteed" in human.stdout
