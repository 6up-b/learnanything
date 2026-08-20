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
from learnloop.diagnosis.probe_targeting import (
    CAUSE_SET_COMMON_COVER,
    CAUSE_SET_DIVERGENT,
    CAUSE_SET_INCOMPLETE_MAPPING,
    COHERENCE_GATE_STATE,
    classify_cause_set,
    integration_condition_target,
    open_cause_set_states_for_learning_object,
    open_cause_sets_for_learning_object,
    probe_priority,
    rank_discriminating_instruments,
    repair_mapping_backfills,
    select_discriminating_instrument,
    should_suppress_prerequisite_probe,
)
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import write_yaml

from tests.helpers import NOW, NOW_ISO, create_basic_vault, set_algorithm_version, write_facets
from tests.test_km2_write_path import SELECT, SHARED, _attempt, _item, _rubric, build_mvp07_vault


def _fake_instrument(
    item_id,
    target_facets,
    rate=0.1,
    eig=0.1,
    slot_map=None,
    instructional_actions=None,
):
    return SimpleNamespace(
        item=SimpleNamespace(id=item_id),
        instrument=SimpleNamespace(
            target_facets=tuple(target_facets),
            instructional_actions=dict(instructional_actions or {}),
        ),
        slot_map=dict(slot_map or {}),
        predictive_information_rate=rate,
        expected_information_gain=eig,
    )


def test_cause_set_diagnostic_selects_discriminating_instrument(tmp_path):
    # (a) A LEGACY (pre-P1, no hypothesis refs) cause set still uses the
    # distinct-facet rule: prefer the instrument covering BOTH candidate causes
    # over a single-facet one, even when the latter has higher raw EIG.
    causes = [{"facet": SHARED, "capability": "retrieval"}, {"facet": SELECT, "capability": "method_selection"}]
    non_discriminating = _fake_instrument("pi_single", [SHARED], rate=0.9, eig=0.9)
    discriminating = _fake_instrument("pi_contrast", [SHARED, SELECT], rate=0.2, eig=0.2)
    chosen = select_discriminating_instrument(causes, [non_discriminating, discriminating])
    assert chosen.item.id == "pi_contrast"
    # ... and the legacy basis is labelled, never silent.
    ranking = rank_discriminating_instruments(causes, [non_discriminating, discriminating])
    assert ranking.cause_set_state == CAUSE_SET_DIVERGENT
    assert ranking.basis == "legacy_facet_coverage"
    assert ranking.legacy_facet_fallback is True
    assert ranking.as_dict()["facet_coverage_status"] == "legacy_fallback"

    # (b) The real cause set is read from the observation ledger: an ambiguous
    # whole-item failure over two facets carries P1 hypothesis refs with NO
    # repair-class mapping. That is a machine-side backfill obligation, not a
    # probe target — the old facet fallback would have probed here.
    #
    # The mapping is unfilled here for a SPECIFIC, now-typed reason: a
    # self-graded attempt authors no repair suggestion, so there is nothing to
    # map to (`no_repair_authored`). An authored divergent episode does reach
    # `divergent` end to end — see
    # tests/test_causal_repair_mapping_p2.py::test_authored_divergent_repairs_
    # fill_repair_class_id_end_to_end. Do NOT "fix" this case by synthesizing a
    # repair class per target ref: one synthetic class per facet-capability
    # makes divergence equivalent to facet difference, which is the fallback
    # this test exists to keep buried.
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, FrozenClock(NOW))
    states = open_cause_set_states_for_learning_object(vault, repository, "lo_svd_definition")
    assert states
    targeting = states[0]
    assert {c["facet"] for c in targeting.causes if c.get("facet")} == {SHARED, SELECT}
    assert any(cause.get("hypothesis_id") == "H_OTHER" for cause in targeting.causes)
    # Distinct facets, yet NOT probe-worthy: repair classes are authoritative.
    assert targeting.state == CAUSE_SET_INCOMPLETE_MAPPING
    assert targeting.probe_worthy is False
    assert len(targeting.unmapped_hypothesis_ids) == 2
    # The gap is typed, not a bare null: it names the machine-side remedy owed.
    assert set(dict(targeting.unmapped_reasons).values()) == {"no_repair_authored"}
    assert open_cause_sets_for_learning_object(vault, repository, "lo_svd_definition") == []
    backfills = repair_mapping_backfills(vault, repository, "lo_svd_definition")
    assert [check["kind"] for check in backfills] == ["repair_class_mapping_backfill"]
    assert backfills[0]["coherence_gate_state"] == "insufficient_mapping"
    assert backfills[0]["learner_actionable"] is False
    assert set(backfills[0]["unmapped_reasons"]) == set(
        targeting.unmapped_hypothesis_ids
    )


def _p1_cause(hypothesis_id, facet, repair_class_id=None, **extra):
    cause = {
        "hypothesis_id": hypothesis_id,
        "statement": f"cause {hypothesis_id}",
        "facet": facet,
        "capability": "retrieval",
    }
    if repair_class_id is not None:
        cause["repair_class_id"] = repair_class_id
    cause.update(extra)
    return cause


_OPEN_SET_ARM = {"hypothesis_id": "H_OTHER", "open_set": True, "statement": "other"}


def test_p1_shared_repair_class_is_not_divergent_even_across_facets():
    # Two hypotheses, two DIFFERENT facets, one repair class: probing cannot
    # change the action, so this is a common cover, not a probe.
    causes = [
        _p1_cause("h_a", SHARED, "rc_retrieval_practice"),
        _p1_cause("h_b", SELECT, "rc_retrieval_practice"),
        _OPEN_SET_ARM,
    ]
    targeting = classify_cause_set(causes)
    assert targeting.state == CAUSE_SET_COMMON_COVER
    assert targeting.basis == "repair_class"
    assert targeting.probe_worthy is False
    assert targeting.repair_class_ids == ("rc_retrieval_practice",)
    # The pure ranking refuses to treat it as a discriminating context.
    ranking = rank_discriminating_instruments(
        causes,
        [_fake_instrument("pi_a", [SHARED, SELECT], rate=0.1), _fake_instrument("pi_b", [SHARED], rate=0.9)],
    )
    assert ranking.basis == "eig_order"
    assert ranking.selected.item.id == "pi_a"  # untouched incoming EIG order


def test_p1_unmapped_hypothesis_is_incomplete_not_a_facet_fallback():
    causes = [
        _p1_cause("h_a", SHARED, "rc_retrieval_practice"),
        _p1_cause("h_b", SELECT),  # no repair class anywhere
        _OPEN_SET_ARM,
    ]
    targeting = classify_cause_set(causes)
    assert targeting.state == CAUSE_SET_INCOMPLETE_MAPPING
    assert targeting.coherence_gate_state == "insufficient_mapping"
    assert targeting.unmapped_hypothesis_ids == ("h_b",)
    # Two distinct facets are present — the old rule would have called this
    # divergent and probed the learner for missing machine-side data.
    assert targeting.facets == tuple(sorted({SHARED, SELECT}))
    assert targeting.probe_worthy is False
    assert targeting.needs_machine_backfill is True


def test_legacy_pre_p1_cause_set_keeps_the_distinct_facet_rule():
    legacy = [
        {"facet": SHARED, "capability": "retrieval", "statement": "a"},
        {"facet": SELECT, "capability": "method_selection", "statement": "b"},
        {"open_set": True, "hypothesis_id": "H_OTHER", "statement": "other"},
    ]
    targeting = classify_cause_set(legacy)
    assert targeting.state == CAUSE_SET_DIVERGENT
    assert targeting.basis == "legacy_facet"
    assert targeting.probe_worthy is True
    assert targeting.unmapped_hypothesis_ids == ()

    single_facet = [legacy[0], legacy[2]]
    assert classify_cause_set(single_facet).state == CAUSE_SET_COMMON_COVER


def test_repair_class_is_resolved_from_the_stored_hypothesis_record(tmp_path):
    # The machine-side check runs BEFORE any probe: an inline-null repair class
    # that the hypothesis record does carry is resolved, not treated as missing.
    repository = Repository(tmp_path / "state.sqlite3")
    rows = [
        repository.append_causal_hypothesis(
            episode_key=f"ep_{index}",
            attempt_id="at_1",
            learning_object_id="lo_1",
            cause_scope="learner_state",
            statement=f"cause {index}",
            statement_normalized=f"cause {index}",
            repair_class_id=repair_class_id,
        )
        for index, repair_class_id in enumerate(("rc_one", "rc_two"))
    ]
    causes = [
        {"hypothesis_id": rows[0]["id"], "facet": SHARED},
        {"hypothesis_id": rows[1]["id"], "facet": SHARED},
        _OPEN_SET_ARM,
    ]
    targeting = classify_cause_set(causes, repository=repository)
    assert targeting.state == CAUSE_SET_DIVERGENT
    assert targeting.repair_class_ids == ("rc_one", "rc_two")
    # Same facet on both arms: the facet rule could never have found this.
    assert targeting.facets == (SHARED,)
    resolved = [c for c in targeting.causes if c.get("repair_class_id")]
    assert {c["repair_class_basis"] for c in resolved} == {"hypothesis_record"}


def test_instrument_ranking_prefers_discrimination_over_facet_coverage():
    causes = [
        _p1_cause("h_a", SHARED, "rc_retrieval_practice", probe_label="misconception:m_a"),
        _p1_cause("h_b", SELECT, "rc_method_selection", probe_label="misconception:m_b"),
        _OPEN_SET_ARM,
    ]
    # Higher facet coverage AND higher EIG, but both causes land on one row, so
    # it cannot tell them apart.
    coverage_only = _fake_instrument(
        "pi_coverage",
        [SHARED, SELECT],
        rate=0.9,
        eig=0.9,
        slot_map={"misconception:m_a": "other_or_unknown", "misconception:m_b": "other_or_unknown"},
    )
    discriminating = _fake_instrument(
        "pi_discriminating",
        [SHARED],
        rate=0.1,
        eig=0.1,
        slot_map={"misconception:m_a": "slot_a", "misconception:m_b": "slot_b"},
        instructional_actions={"slot_a": "drill_retrieval", "slot_b": "contrast_methods"},
    )
    ranking = rank_discriminating_instruments(causes, [coverage_only, discriminating])
    assert ranking.cause_set_state == CAUSE_SET_DIVERGENT
    assert ranking.selected.item.id == "pi_discriminating"
    assert ranking.basis == "repair_class_discrimination"
    assert ranking.legacy_facet_fallback is False
    top = ranking.as_dict()["ranked"][0]
    assert top["repair_class_pairs_separated"] == 1
    assert top["expected_action_change"] == 1
    assert select_discriminating_instrument(causes, [coverage_only, discriminating]) is discriminating


def test_incomplete_mapping_surfaces_as_a_machine_check_never_as_a_probe(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_ambiguous_001", {"whole_item": 0}, FrozenClock(NOW))

    priority = probe_priority(vault, repository, vault.learning_objects["lo_svd_definition"])
    kinds = {entry["kind"] for entry in priority["considered"]}
    assert CAUSE_SET_INCOMPLETE_MAPPING in kinds
    assert "cause_set_discrimination" not in kinds
    incomplete = next(
        entry for entry in priority["considered"] if entry["kind"] == CAUSE_SET_INCOMPLETE_MAPPING
    )
    assert incomplete["learner_actionable"] is False
    assert priority["machine_checks"] == [incomplete["machine_check"]]
    # Nothing learner-facing is selected off a missing machine-side mapping.
    assert priority["selected"] is None


def test_cause_set_state_vocabulary_matches_the_coherence_gate():
    # `causal_probe_coherence.rung_divergence_gate` publishes the same tri-state
    # under its own spelling; keep the bridge explicit so the two cannot drift.
    assert COHERENCE_GATE_STATE == {
        CAUSE_SET_COMMON_COVER: "common_cover",
        CAUSE_SET_DIVERGENT: "divergent",
        CAUSE_SET_INCOMPLETE_MAPPING: "insufficient_mapping",
    }


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
