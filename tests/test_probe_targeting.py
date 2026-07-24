"""KM5 §11.1 unresolved-cause-set probe targeting.

The diagnostic instrument-choice path: entering a diagnostic for a cause set
selects an instrument that discriminates the candidate causes; already-demonstrated
prerequisites are not re-probed; and a components-strong / integration-weak LO
probes coordination, not the components again.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.services.probe_targeting import (
    integration_condition_target,
    open_cause_sets_for_learning_object,
    probe_priority,
    select_discriminating_instrument,
    should_suppress_prerequisite_probe,
)
from learnloop.services.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.test_km2_write_path import SELECT, SHARED, _attempt, _item, _rubric, build_mvp07_vault


def _fake_instrument(item_id, target_facets, rate=0.1, eig=0.1):
    return SimpleNamespace(
        item=SimpleNamespace(id=item_id),
        instrument=SimpleNamespace(target_facets=tuple(target_facets)),
        predictive_information_rate=rate,
        expected_information_gain=eig,
    )


def test_cause_set_diagnostic_selects_discriminating_instrument(tmp_path):
    # (a) The pure selection prefers the instrument that covers BOTH candidate
    # causes (a contrast instrument) over a single-facet instrument, even when the
    # single-facet one has higher raw EIG.
    causes = [{"facet": SHARED, "capability": "retrieval"}, {"facet": SELECT, "capability": "method_selection"}]
    non_discriminating = _fake_instrument("pi_single", [SHARED], rate=0.9, eig=0.9)
    discriminating = _fake_instrument("pi_contrast", [SHARED, SELECT], rate=0.2, eig=0.2)
    chosen = select_discriminating_instrument(causes, [non_discriminating, discriminating])
    assert chosen.item.id == "pi_contrast"

    # (b) The real cause set is read from the observation ledger: an ambiguous
    # whole-item failure over two facets is an open, repair-divergent cause set.
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, FrozenClock(NOW))
    cause_sets = open_cause_sets_for_learning_object(vault, repository, "lo_svd_definition")
    assert cause_sets
    facets = {c["facet"] for c in cause_sets[0] if c.get("facet")}
    assert facets == {SHARED, SELECT}
    assert any(cause.get("hypothesis_id") == "H_OTHER" for cause in cause_sets[0])


def test_embedded_evidence_suppresses_redundant_probe(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    # Demonstrate SHARED@retrieval with two independent-surface correct attempts.
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, FrozenClock(NOW))

    # A prerequisite already demonstrated downstream must not be re-probed.
    assert should_suppress_prerequisite_probe(vault, repository, {"facet": SHARED, "capability": "retrieval"})
    # A capability with no certification credit is NOT suppressed.
    assert not should_suppress_prerequisite_probe(vault, repository, {"facet": SHARED, "capability": "method_selection"})


def _integration_vault(root: Path) -> Path:
    paths = create_basic_vault(root)
    write_yaml(paths.goals_path, {"schema_version": 2, "goals": []})
    write_facets(
        paths,
        [
            {"id": "facet_comp", "kind": "procedure_contract", "claim": "A component step."},
            {"id": "facet_integ", "kind": "procedure_contract", "claim": "Coordinating the steps."},
        ],
    )
    lo = {
        "schema_version": 1,
        "id": "lo_svd_definition",
        "title": "Composite task",
        "subjects": ["linear-algebra"],
        "concept": "singular_value_decomposition",
        "knowledge_type": "procedure",
        "status": "active",
        "contradicts": None,
        "summary": "A composite procedure with a coordination factor.",
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
                        "all_of": [{"facet": "facet_comp", "capability": "procedure_execution", "modality": "hard"}],
                        "integration": {"facet": "facet_integ", "capability": "coordination", "modality": "hard"},
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
            evidence_facets=["facet_comp"],
            rubric=_rubric(
                "component",
                [{"facet": "facet_comp", "capability": "procedure_execution", "role": "primary"}],
                correlation_group="comp_group",
            ),
            fingerprint={"source_family": "chapter3"},
        ),
    )
    set_algorithm_version(paths, "mvp-0.7")
    return paths


def test_integration_condition_probes_coordination_not_components(tmp_path):
    paths = _integration_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    # Demonstrate the component (procedure_execution) across two surface groups.
    _attempt(vault, repository, "pi_svd_define_001", {"component": 4}, FrozenClock(NOW))
    lo = vault.learning_objects["lo_svd_definition"]

    target = integration_condition_target(vault, repository, lo)
    assert target is not None
    assert target["capability"] == "coordination"
    assert target["facet"] == "facet_integ"  # the integration factor, NOT facet_comp

    priority = probe_priority(vault, repository, lo)
    selected = priority["selected"]
    assert selected is not None and selected["kind"] == "integration_condition"
    assert selected["target"]["facet"] == "facet_integ"
