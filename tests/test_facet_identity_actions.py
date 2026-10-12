"""Facet identity: the vault-level merge, its evidence re-key, and the exact undo."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.facet_identity.actions import (
    FacetIdentityActionError,
    list_actions,
    merge_registered_facets,
    normalized_entry,
    undo_action,
)
from learnloop.db.repositories import Repository
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.models import learning_object_facet_union
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.helpers import NOW, write_facets
from tests.test_km2_write_path import SELECT, SHARED, _attempt, _item, _rubric, build_mvp07_vault

DUP = "facet_svd_factorization_restated"
_CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))


def _vault_with_duplicate(tmp_path):
    paths = build_mvp07_vault(tmp_path / "vault")
    write_facets(paths, [
        {"id": SHARED, "kind": "definition", "claim": "SVD factorizes into U, Sigma, V^T.",
         "positive_examples": ["A = U Sigma V^T for a 2x2 matrix"]},
        {"id": SELECT, "kind": "applicability_condition", "claim": "When SVD applies."},
        {"id": "recall", "kind": "definition", "claim": "SVD recall."},
        {"id": DUP, "kind": "definition", "claim": "Every matrix A can be written A = U Sigma V^T.",
         "preconditions": ["A is a real matrix"]},
    ])
    write_yaml(
        paths.practice_item_path("linear-algebra", "pi_svd_restated_001"),
        _item(
            "pi_svd_restated_001", "lo_svd_application", evidence_facets=[DUP],
            rubric=_rubric("states_factorization", [{"facet": DUP, "capability": "retrieval", "role": "primary"}],
                           correlation_group="svd_restated"),
            fingerprint={"source_family": "chapter9-restated"},
        ),
    )
    lo_path = paths.learning_object_path("linear-algebra", "lo_svd_application")
    lo = read_yaml(lo_path)
    lo["blueprints"] = [{"id": "bp_apply", "weight": 1.0, "recipes": [{
        "id": "recipe_apply", "composition": "conjunctive",
        "all_of": [{"facet": DUP, "capability": "retrieval", "modality": "hard"}], "any_of": [],
        "integration": None,
    }]}]
    write_yaml(lo_path, lo)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    return paths, load_vault(paths.root), repository


def _belief(repository: Repository) -> list[tuple]:
    return sorted(
        (state.facet_id, state.capability_key, state.practice_item_id or "", round(state.recall_alpha, 9),
         round(state.recall_beta, 9), round(state.independent_evidence_mass, 9))
        for state in repository.canonical_facet_recall_states()
    )


def _merge(paths, repository, **kwargs):
    return merge_registered_facets(
        paths.root, repository, survivor=SHARED, retired=[DUP], action=kwargs.pop("action", "merge"),
        absorb_as=kwargs.pop("absorb_as", None), origin="dedupe", run_id="run1", judge="llm",
        judge_model="fake-judge-1", prompt_version="v1", clock=_CLOCK, **kwargs,
    )


def test_a_merge_rekeys_evidence_and_undo_restores_facets_and_evidence_exactly(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_restated_001", {"states_factorization": 0}, FrozenClock(NOW))
    before_belief = _belief(repository)
    assert any(row[0] == DUP for row in before_belief)
    before_file = {entry["id"]: normalized_entry(entry) for entry in read_yaml(paths.facets_path)["facets"]}
    before_order = [entry["id"] for entry in read_yaml(paths.facets_path)["facets"]]
    item_file = paths.practice_item_path("linear-algebra", "pi_svd_restated_001").read_text(encoding="utf-8")

    result = _merge(paths, repository)
    assert result["status"] == "applied"
    merged = load_vault(paths.root)
    assert DUP not in merged.evidence_facets
    assert DUP in merged.evidence_facets[SHARED].aliases
    assert merged.evidence_facets[SHARED].preconditions == ["A is a real matrix"]
    # References keep their id on disk and resolve to the survivor at load.
    assert paths.practice_item_path("linear-algebra", "pi_svd_restated_001").read_text(encoding="utf-8") == item_file
    item = merged.practice_items["pi_svd_restated_001"]
    assert item.evidence_facets == [SHARED]
    assert item.grading_rubric.criteria[0].targets[0].facet == SHARED
    assert learning_object_facet_union(merged.learning_objects["lo_svd_application"]) == [SHARED]
    assert sqlite3.connect(paths.sqlite_path).execute(
        "SELECT retired_facet_id, surviving_facet_id FROM facet_merges").fetchall() == [(DUP, SHARED)]
    # Evidence is re-keyed: the retired facet's observations fold into the survivor.
    after_belief = _belief(repository)
    assert not any(row[0] == DUP for row in after_belief)
    shared = [row for row in after_belief if row[0] == SHARED and row[2] == ""]
    shared_before = [row for row in before_belief if row[0] == SHARED and row[2] == ""]
    assert shared[0][4] > shared_before[0][4]  # the failed restated attempt now counts against SHARED

    undone = undo_action(paths.root, repository, result["action_id"], clock=_CLOCK)
    assert undone["status"] == "undone" and undone["merge_rows_deleted"] == 1
    after_file = {entry["id"]: normalized_entry(entry) for entry in read_yaml(paths.facets_path)["facets"]}
    assert after_file == before_file
    assert [entry["id"] for entry in read_yaml(paths.facets_path)["facets"]] == before_order
    assert sqlite3.connect(paths.sqlite_path).execute("SELECT COUNT(*) FROM facet_merges").fetchone()[0] == 0
    assert _belief(repository) == before_belief
    assert load_vault(paths.root).practice_items["pi_svd_restated_001"].evidence_facets == [DUP]
    with pytest.raises(FacetIdentityActionError) as exc:
        undo_action(paths.root, repository, result["action_id"])
    assert exc.value.code == "already_undone"


def test_absorb_adds_the_special_case_as_an_example(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    _merge(paths, repository, action="absorb", absorb_as="example")
    shared = load_vault(paths.root).evidence_facets[SHARED]
    assert "Every matrix A can be written A = U Sigma V^T." in shared.positive_examples


def test_the_strict_lock_policy_refuses_and_the_default_labels_the_lock(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    # Two distinct surface groups lock SHARED (knowledge model §3.4).
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, FrozenClock(NOW))
    before = paths.facets_path.read_text(encoding="utf-8")
    refused = _merge(paths, repository, merge_locked=False)
    assert refused["status"] == "refused" and refused["reason"] == "identity_locked"
    assert SHARED in refused["lock_reasons"]
    assert paths.facets_path.read_text(encoding="utf-8") == before and list_actions(repository) == []
    applied = _merge(paths, repository)
    assert applied["status"] == "applied" and applied["locked"] and SHARED in applied["lock_reasons"]
    assert list_actions(repository)[0]["detail"]["lock_reasons"][SHARED]


def test_undo_refuses_to_overwrite_a_later_change(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    first = _merge(paths, repository)
    second = merge_registered_facets(
        paths.root, repository, survivor=SHARED, retired=[SELECT], action="merge", absorb_as=None,
        origin="dedupe", run_id="run2", judge="llm", judge_model="fake", prompt_version="v1", clock=_CLOCK,
    )
    assert second["status"] == "applied"
    with pytest.raises(FacetIdentityActionError) as exc:
        undo_action(paths.root, repository, first["action_id"])
    assert exc.value.code == "changed_since" and second["action_id"] in str(exc.value)
    undo_action(paths.root, repository, second["action_id"])
    undo_action(paths.root, repository, first["action_id"])
    assert {facet for facet in load_vault(paths.root).evidence_facets} >= {SHARED, SELECT, DUP}


def test_a_merge_leaves_the_vault_doctor_clean(tmp_path):
    from learnloop.ops.doctor import run_doctor

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    before = {issue.code for issue in run_doctor(paths.root).issues if issue.severity == "error"}
    _merge(paths, repository)
    after = {issue.code for issue in run_doctor(paths.root).issues if issue.severity == "error"}
    assert after <= before
    assert not any("unregistered" in code for code in after)
