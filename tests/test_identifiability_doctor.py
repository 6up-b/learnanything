"""KM5 §11.3 assessment identifiability doctor.

Unit coverage of the seven warnings plus the pre-first-practice registry check:
the doctor runs over a subject whose registry changed since the last check
(watermark-gated), emits warnings (never false facet-specific precision), and
schedules discriminating-probe needs.
"""

from __future__ import annotations

from pathlib import Path

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ops.doctor import run_doctor
from learnloop.learner.identifiability import (
    ProposalView,
    analyze_identifiability,
    build_registry_view,
    graph_identifiability_report,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.test_km2_write_path import _item, _rubric


def test_seven_identifiability_warnings():
    """A crafted neighborhood trips all seven §11.3 warnings, one to seven."""

    view = ProposalView(
        facet_repairs={"fa": ("r",), "fb": ("r",), "fx": ("rx",)},
        criterion_targets=[
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fa", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c1", "correlation_group": "g1", "facet": "fb", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c2", "correlation_group": "g2", "facet": "fx", "capability": "retrieval", "role": "primary"},
            {"criterion_id": "c2", "correlation_group": "g2", "facet": "fx", "capability": "method_selection", "role": "primary"},
            {"criterion_id": "c3", "correlation_group": "g3", "facet": "fc", "capability": "procedure_execution", "role": "primary"},
        ],
        recipe_components=[
            {"facet": "fmissing", "capability": "coordination"},
            {"facet": "fc", "capability": "procedure_execution", "blueprint_id": "bp1", "recipe_id": "r1", "integration": False},
        ],
        recipes=[
            {"blueprint_id": "bp2", "recipe_id": "ra"},
            {"blueprint_id": "bp2", "recipe_id": "rb"},
            {"blueprint_id": "bp1", "recipe_id": "r1", "integration_facet": "fint", "integration_capability": "coordination"},
        ],
        planted_profiles=[
            {"id": "p1", "facets": ("fa",), "outcome_signature": ["s1", "s2"]},
            {"id": "p2", "facets": ("fb",), "outcome_signature": ["s1", "s2"]},
        ],
        criterion_fingerprints={"c1": "rep1", "c2": "rep1"},
    )
    findings = analyze_identifiability(view)
    fired = {f.check for f in findings}
    assert fired == {1, 2, 3, 4, 5, 6, 7}


def _build_registry_vault(root: Path) -> Path:
    """mvp-0.7 vault whose LO blueprint requires a facet-capability no criterion
    observes (§11.3 check 2 missing anchor)."""

    paths = create_basic_vault(root)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [
            {"id": "facet_def", "kind": "definition", "claim": "A definition."},
            {"id": "facet_pick", "kind": "applicability_condition", "claim": "When to pick."},
        ],
    )
    # LO with a blueprint requiring facet_pick@method_selection, but the only
    # rubric criterion observes facet_def@retrieval -> facet_pick has no anchor.
    lo = {
        "schema_version": 1,
        "id": "lo_svd_definition",
        "title": "SVD definition",
        "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition",
        "knowledge_type": "definition",
        "status": "active",
        "contradicts": None,
        "summary": "Define SVD.",
        "prerequisites": [],
        "confusables": [],
        "blueprints": [
            {
                "id": "bp_main",
                "weight": 1.0,
                "recipes": [
                    {
                        "id": "recipe_main",
                        "composition": "conjunctive",
                        "all_of": [
                            {"facet": "facet_def", "capability": "retrieval", "modality": "hard"},
                            {"facet": "facet_pick", "capability": "method_selection", "modality": "hard"},
                        ],
                    }
                ],
            }
        ],
        "difficulty_prior": 0.5,
        "tags": [],
        "provenance": {"origin": "human", "source_refs": []},
        "created_at": NOW_ISO,
        "updated_at": NOW_ISO,
    }
    write_yaml(paths.learning_object_path("linear-algebra", "lo_svd_definition"), lo)
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_define_001"),
        _item(
            "pi_svd_define_001",
            "lo_svd_definition",
            evidence_facets=["facet_def"],
            rubric=_rubric(
                "correctness",
                [{"facet": "facet_def", "capability": "retrieval", "role": "primary"}],
                correlation_group="def_group",
            ),
            fingerprint={"source_family": "chapter3"},
        ),
    )
    set_algorithm_version(paths, "mvp-0.7")
    return paths


def test_registry_view_flags_missing_anchor():
    import tempfile

    paths = _build_registry_vault(Path(tempfile.mkdtemp()) / "vault")
    vault = load_vault(paths.root)
    view = build_registry_view(vault, "linear-algebra")
    findings = analyze_identifiability(view)
    assert any(f.detail == "missing_anchor" and f.capability == "method_selection" for f in findings)


def test_graph_identifiability_report_and_probe_scheduling(tmp_path):
    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    report = graph_identifiability_report(vault, repository, subject_id="linear-algebra", schedule_probes=True)
    assert report["totals"]["findings"] >= 1
    assert report["totals"]["scheduled_probes"] >= 1
    subject = report["subjects"][0]
    assert subject["unresolved_bundles"]
    # the discriminating-probe need was persisted through the generation machinery.
    needs = repository.synthesis_generation_needs(subject_id="linear-algebra")
    assert any(n["need_kind"] == "generate_discriminator" for n in needs)


def test_pre_first_practice_doctor_watermark(tmp_path):
    paths = _build_registry_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))

    # First doctor pass (fix_state) surfaces the warning and advances the watermark.
    report = run_doctor(paths.root, fix_state=True)
    ident_warnings = [i for i in report.issues if i.code.startswith("identifiability:")]
    assert ident_warnings
    assert all(i.severity == "warning" for i in ident_warnings)
    watermark = repository.identifiability_watermark("linear-algebra")
    assert watermark is not None and watermark["finding_count"] >= 1

    # Second pass over the unchanged registry is gated by the watermark: no repeat.
    report2 = run_doctor(paths.root, fix_state=True)
    assert not [i for i in report2.issues if i.code.startswith("identifiability:")]
