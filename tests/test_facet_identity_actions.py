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
    """Merge DUP into SHARED. These fixtures' facets are probe-locked from the
    first sync (``can_apply``'s probe arm), so tests of the merge mechanics run
    under the owner's override; the lock-policy tests pass ``merge_locked=None``
    to use the configured policy."""

    kwargs.setdefault("merge_locked", True)
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

    # Probe episodes lock both facets: this is the owner's override
    # (merge_locked_facets), the only way a facet with history merges.
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


def _lock_shared(vault, repository):
    # Two distinct surface groups lock SHARED (knowledge model §3.4).
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_apply_001", {"uses_factorization": 4}, FrozenClock(NOW))


def test_the_default_lock_policy_refuses_and_the_owner_override_labels_the_lock(tmp_path):
    """Review F2: the knowledge model's single lock policy is the default."""

    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    assert load_vault(paths.root).config.facet_identity.merge_locked_facets is False
    before = paths.facets_path.read_text(encoding="utf-8")
    refused = _merge(paths, repository, merge_locked=None)
    assert refused["status"] == "refused" and refused["reason"] == "identity_locked"
    assert SHARED in refused["lock_reasons"]
    assert paths.facets_path.read_text(encoding="utf-8") == before and list_actions(repository) == []
    applied = _merge(paths, repository, merge_locked=True)
    assert applied["status"] == "applied" and applied["locked"] and SHARED in applied["lock_reasons"]
    assert list_actions(repository)[0]["detail"]["lock_reasons"][SHARED]


def test_dedupe_proposes_a_locked_set_and_applies_it_only_under_the_override(tmp_path):
    from learnloop.content.facet_identity.dedupe import run_dedupe

    from tests.facet_identity_fakes import FakeFacetJudge
    from tests.helpers import append_config_toml

    paths, vault, repository = _vault_with_duplicate(tmp_path)
    facets = read_yaml(paths.facets_path)
    for entry in facets["facets"]:
        entry["concept_id"] = "singular_value_decomposition"
    write_yaml(paths.facets_path, facets)
    _lock_shared(load_vault(paths.root), repository)
    judge = FakeFacetJudge(clusters=[["SVD factorizes into U, Sigma, V^T.",
                                      "Every matrix A can be written A = U Sigma V^T."]])
    before = paths.facets_path.read_text(encoding="utf-8")
    report = run_dedupe(paths.root, client=judge, clock=_CLOCK)
    assert report["status"] == "complete" and report["lock_policy"] == "refuse_locked"
    assert report["actions"] == [] and report["refused"] == []
    (proposal,) = report["locked_proposals"]
    assert proposal["status"] == "proposed_locked" and proposal["survivor"]["id"] == SHARED
    assert [facet["id"] for facet in proposal["retired"]] == [DUP] and SHARED in proposal["lock_reasons"]
    assert paths.facets_path.read_text(encoding="utf-8") == before and list_actions(repository) == []

    append_config_toml(paths.root, "[facet_identity]\nmerge_locked_facets = true")
    calls = len(judge.requests)
    applied = run_dedupe(paths.root, client=judge, clock=_CLOCK)
    assert len(judge.requests) == calls  # the judged group is reused
    assert [action["survivor"]["id"] for action in applied["actions"]] == [SHARED]
    assert applied["actions"][0]["locked"] and applied["locked_proposals"] == []


def test_undo_refuses_to_overwrite_a_later_change(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    first = _merge(paths, repository)
    second = merge_registered_facets(
        paths.root, repository, survivor=SHARED, retired=[SELECT], action="merge", absorb_as=None,
        origin="dedupe", run_id="run2", judge="llm", judge_model="fake", prompt_version="v1", clock=_CLOCK,
        merge_locked=True,
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


def test_a_merge_without_an_undo_says_so_and_refuses(tmp_path):
    from learnloop.content.facet_identity.actions import describe, record_proposed_actions

    paths, vault, repository = _vault_with_duplicate(tmp_path)
    (action_id,) = record_proposed_actions(repository, [{
        "scope": "in_run", "action": "merge", "survivor_facet_id": SHARED, "retired_facet_ids": ["facet_gone"],
        "before": {"facets": {SHARED: None, "facet_gone": {"id": "facet_gone"}}, "order": {}},
        "after": {"facets": {SHARED: None, "facet_gone": None}}, "judge": "llm", "judge_model": "fake",
        "prompt_version": "v1", "detail": {"undo": "unavailable: the survivor was aliased by the mint gate"},
    }], origin="ingest", run_id="run1", proposal_id=None, clock=_CLOCK)
    view = describe(list_actions(repository)[0], vault)
    assert view["undoable"] is False and "mint gate" in view["note"]
    with pytest.raises(FacetIdentityActionError) as exc:
        undo_action(paths.root, repository, action_id)
    assert exc.value.code == "no_undo"


# --- review F1: a criterion or recipe that names both merged facets ------------------


def _vault_targeting(root, targets, *, recipe_facets=()):
    paths = build_mvp07_vault(root)
    write_facets(paths, [
        {"id": SHARED, "kind": "definition", "claim": "SVD factorizes into U, Sigma, V^T."},
        {"id": SELECT, "kind": "applicability_condition", "claim": "When SVD applies."},
        {"id": "recall", "kind": "definition", "claim": "SVD recall."},
        {"id": DUP, "kind": "definition", "claim": "Every matrix A can be written A = U Sigma V^T."},
    ])
    write_yaml(paths.practice_item_path("linear-algebra", "pi_both_001"), _item(
        "pi_both_001", "lo_svd_application", evidence_facets=sorted({target[0] for target in targets}),
        rubric=_rubric("states", [{"facet": target[0], "capability": target[2] if len(target) > 2 else "retrieval",
                                   "role": target[1]} for target in targets],
                       correlation_group="both"),
        fingerprint={"source_family": "both"},
    ))
    if recipe_facets:
        lo_path = paths.learning_object_path("linear-algebra", "lo_svd_application")
        lo = read_yaml(lo_path)
        lo["blueprints"] = [{"id": "bp_apply", "weight": 1.0, "recipes": [{
            "id": "recipe_apply", "composition": "conjunctive",
            "all_of": [{"facet": facet, "capability": "retrieval", "modality": modality}
                       for facet, modality in recipe_facets],
            "any_of": [{"facet": facet, "capability": "retrieval", "modality": "hard"} for facet, _m in recipe_facets],
            "integration": None,
        }]}]
        write_yaml(lo_path, lo)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))
    return paths, repository


def _shared_row(repository):
    return [
        (state.capability_key, round(state.recall_alpha, 9), round(state.recall_beta, 9),
         round(state.independent_evidence_mass, 9))
        for state in repository.canonical_facet_recall_states()
        if state.facet_id == SHARED and not state.practice_item_id
    ]


@pytest.mark.parametrize("score", [4, 0])
def test_a_merge_of_two_facets_one_criterion_targets_counts_like_one_target(tmp_path, score):
    """Review F1: after the merge the criterion's targets resolve to one facet, once.

    Before the fix the loader kept ``[SHARED, SHARED]``: a correct answer split
    and discounted its mass, and a wrong one wrote no recall row at all.
    """

    merged_paths, merged = _vault_targeting(tmp_path / "merged", [(SHARED, "supporting"), (DUP, "primary")])
    assert _merge(merged_paths, merged)["status"] == "applied"
    _attempt(load_vault(merged_paths.root), merged, "pi_both_001", {"states": score}, FrozenClock(NOW))
    single_paths, single = _vault_targeting(tmp_path / "single", [(SHARED, "primary")])
    _attempt(load_vault(single_paths.root), single, "pi_both_001", {"states": score}, FrozenClock(NOW))

    targets = load_vault(merged_paths.root).practice_items["pi_both_001"].grading_rubric.criteria[0].targets
    assert [(target.facet, target.role) for target in targets] == [(SHARED, "primary")]  # strongest role kept
    assert _shared_row(single)
    assert _shared_row(merged) == _shared_row(single)


def test_a_recipe_naming_both_merged_facets_keeps_one_component(tmp_path):
    paths, repository = _vault_targeting(
        tmp_path / "vault", [(SHARED, "primary")], recipe_facets=[(SHARED, "facilitating"), (DUP, "hard")],
    )
    assert _merge(paths, repository)["status"] == "applied"
    recipe = load_vault(paths.root).learning_objects["lo_svd_application"].blueprints[0].recipes[0]
    assert [(c.facet, c.capability, c.modality) for c in recipe.all_of] == [(SHARED, "retrieval", "hard")]
    assert [(c.facet, c.capability) for c in recipe.any_of] == [(SHARED, "retrieval")]


def test_authored_duplicate_targets_without_an_alias_load_unchanged(tmp_path):
    """Only duplicates that alias resolution creates collapse (no-alias vaults load as before)."""

    paths, _repository = _vault_targeting(tmp_path / "vault", [(SHARED, "primary"), (SHARED, "supporting")])
    targets = load_vault(paths.root).practice_items["pi_both_001"].grading_rubric.criteria[0].targets
    assert [(target.facet, target.role) for target in targets] == [(SHARED, "primary"), (SHARED, "supporting")]


@pytest.mark.parametrize("score", [4, 0])
def test_a_criterion_graded_before_the_merge_keeps_its_two_facets_apart(tmp_path, score):
    """Re-review F1: history is replayed from its frozen contract, which still names both facets.

    Merging would resolve that criterion's targets to the survivor twice: a
    correct answer read alpha 1.625 / mass 0.5 (one target: 2.0 / 1.0), and a
    wrong one wrote no recall row (one target: beta 2.0). The merge now holds
    the retiree back, under either lock policy, and changes nothing.
    """

    paths, repository = _vault_targeting(tmp_path / "vault", [(SHARED, "primary"), (DUP, "primary")])
    _attempt(load_vault(paths.root), repository, "pi_both_001", {"states": score}, FrozenClock(NOW))
    before_belief = _belief(repository)
    before_file = paths.facets_path.read_text(encoding="utf-8")

    refused = _merge(paths, repository)  # the owner's override: the lock policy is not what refuses
    assert refused["status"] == "refused" and refused["reason"] == "shared_graded_criterion"
    (held,) = refused["held_back"]
    assert held["facet_id"] == DUP and held["with"] == [SHARED]
    assert [(hit["practice_item_id"], hit["criterion_id"], hit["capability"], hit["facets"])
            for hit in held["criteria"]] == [("pi_both_001", "states", "retrieval", sorted([SHARED, DUP]))]
    assert paths.facets_path.read_text(encoding="utf-8") == before_file
    assert list_actions(repository) == [] and _merge_rows(paths) == []
    assert _belief(repository) == before_belief


def test_a_held_back_retiree_stays_registered_while_the_rest_of_the_set_merges(tmp_path):
    paths, repository = _vault_targeting(tmp_path / "vault", [(SHARED, "primary"), (DUP, "primary")])
    _attempt(load_vault(paths.root), repository, "pi_both_001", {"states": 0}, FrozenClock(NOW))
    result = merge_registered_facets(
        paths.root, repository, survivor=SHARED, retired=[DUP, "recall"], action="merge", absorb_as=None,
        origin="dedupe", run_id="run1", judge="llm", judge_model="fake", prompt_version="v1", clock=_CLOCK,
        merge_locked=True,
    )
    assert result["status"] == "applied" and result["retired_facet_ids"] == ["recall"]
    assert [held["facet_id"] for held in result["held_back"]] == [DUP]
    vault = load_vault(paths.root)
    assert DUP in vault.evidence_facets and "recall" in vault.evidence_facets[SHARED].aliases
    (record,) = list_actions(repository)
    assert record["retired_facet_ids"] == ["recall"] and _merge_rows(paths) == [("recall", SHARED)]
    from learnloop.content.facet_identity.actions import describe

    assert describe(record, vault)["held_back"] == [DUP]


def test_a_criterion_naming_the_two_facets_at_different_capabilities_does_not_hold_back(tmp_path):
    paths, repository = _vault_targeting(
        tmp_path / "vault", [(SHARED, "primary", "retrieval"), (DUP, "primary", "method_selection")],
    )
    _attempt(load_vault(paths.root), repository, "pi_both_001", {"states": 4}, FrozenClock(NOW))
    result = _merge(paths, repository)
    assert result["status"] == "applied" and result["held_back"] == []


def test_dedupe_reports_a_held_back_retiree_as_refused(tmp_path):
    from learnloop.content.facet_identity.dedupe import run_dedupe

    from tests.facet_identity_fakes import FakeFacetJudge
    from tests.helpers import append_config_toml

    paths, repository = _vault_targeting(tmp_path / "vault", [(SHARED, "primary"), (DUP, "primary")])
    facets = read_yaml(paths.facets_path)
    for entry in facets["facets"]:
        entry["concept_id"] = "singular_value_decomposition"
    write_yaml(paths.facets_path, facets)
    _attempt(load_vault(paths.root), repository, "pi_both_001", {"states": 0}, FrozenClock(NOW))
    append_config_toml(paths.root, "[facet_identity]\nmerge_locked_facets = true")
    judge = FakeFacetJudge(clusters=[["SVD factorizes into U, Sigma, V^T.",
                                      "Every matrix A can be written A = U Sigma V^T."]])
    report = run_dedupe(paths.root, client=judge, clock=_CLOCK)
    assert report["status"] == "complete" and report["actions"] == [] and report["locked_proposals"] == []
    (refused,) = report["refused"]
    assert refused["reason"] == "shared_graded_criterion" and refused["retired"] == [DUP]
    assert refused["survivor"] in {SHARED, DUP} and refused["held_back"][0]["criteria"]
    assert list_actions(repository) == [] and DUP in load_vault(paths.root).evidence_facets


# --- review F4: merge and undo survive an interrupted process ------------------------


class _Killed(BaseException):
    """A process death: no ``except Exception`` compensation runs."""


def _kill_at(monkeypatch, name, *, after_calls=0):
    import learnloop.content.facet_identity.actions as actions_module

    real = getattr(actions_module, name)
    calls = {"n": 0}

    def killed(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] > after_calls:
            raise _Killed(name)
        return real(*args, **kwargs)

    monkeypatch.setattr(actions_module, name, killed)


def _merge_rows(paths):
    return sqlite3.connect(paths.sqlite_path).execute(
        "SELECT retired_facet_id, surviving_facet_id FROM facet_merges").fetchall()


@pytest.mark.parametrize("killed_at", ["_write_facets", "refresh_derived_state"])
def test_an_interrupted_merge_is_finished_by_recovery(tmp_path, monkeypatch, killed_at):
    from learnloop.content.facet_identity.actions import recover_interrupted_actions

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, killed_at)
        with pytest.raises(_Killed):
            _merge(paths, repository)
    (record,) = list_actions(repository)
    # The intent and its facet_merges rows committed together, before the file.
    assert record["status"] == "applying" and _merge_rows(paths) == [(DUP, SHARED)]
    recovered = recover_interrupted_actions(paths.root, repository, clock=_CLOCK)
    assert [(row["from"], row["to"]) for row in recovered] == [("applying", "applied")]
    vault = load_vault(paths.root)
    assert DUP not in vault.evidence_facets and DUP in vault.evidence_facets[SHARED].aliases
    assert list_actions(repository)[0]["status"] == "applied"
    undo_action(paths.root, repository, record["id"], clock=_CLOCK)
    assert DUP in load_vault(paths.root).evidence_facets and _merge_rows(paths) == []


@pytest.mark.parametrize("killed_at", ["_write_facets", "_delete_merge_rows", "refresh_derived_state"])
def test_an_interrupted_undo_is_finished_by_a_retry(tmp_path, monkeypatch, killed_at):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    before_file = {entry["id"]: normalized_entry(entry) for entry in read_yaml(paths.facets_path)["facets"]}
    applied = _merge(paths, repository)
    with monkeypatch.context() as patched:
        _kill_at(patched, killed_at)
        with pytest.raises(_Killed):
            undo_action(paths.root, repository, applied["action_id"], clock=_CLOCK)
    assert list_actions(repository)[0]["status"] == "undoing"
    # The retry the review found refused ("exist again" / "edited since") now finishes it.
    result = undo_action(paths.root, repository, applied["action_id"], clock=_CLOCK)
    assert result["status"] == "undone" and result.get("recovered") is True
    assert {entry["id"]: normalized_entry(entry) for entry in read_yaml(paths.facets_path)["facets"]} == before_file
    assert _merge_rows(paths) == [] and list_actions(repository)[0]["status"] == "undone"


def test_doctor_reports_an_interrupted_merge_and_fix_state_finishes_it(tmp_path, monkeypatch):
    from learnloop.ops.doctor import run_doctor

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, "_write_facets")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    report = run_doctor(paths.root)
    assert any(issue.code == "facet_identity:interrupted" for issue in report.issues)
    assert list_actions(repository)[0]["status"] == "applying"
    fixed = run_doctor(paths.root, fix_state=True)
    assert any(issue.code == "facet_identity:recovered" for issue in fixed.issues)
    assert list_actions(repository)[0]["status"] == "applied"
    assert DUP in load_vault(paths.root).evidence_facets[SHARED].aliases


def test_a_merge_intent_whose_file_changed_meanwhile_is_withdrawn(tmp_path, monkeypatch):
    from learnloop.content.facet_identity.actions import recover_interrupted_actions

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, "_write_facets")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    document = read_yaml(paths.facets_path)
    document["facets"] = [entry for entry in document["facets"] if entry["id"] != DUP]  # an edit meanwhile
    write_yaml(paths.facets_path, document)
    recovered = recover_interrupted_actions(paths.root, repository, clock=_CLOCK)
    assert [(row["from"], row["to"]) for row in recovered] == [("applying", "abandoned")]
    assert _merge_rows(paths) == [] and list_actions(repository)[0]["status"] == "abandoned"


# --- re-review F12: an interrupted merge or undo never leaves a half-merged vault ------


def _project(paths, repository):
    from learnloop.substrate.canonical_projection import project_canonical_facet_state

    project_canonical_facet_state(load_vault(paths.root), repository, clock=FrozenClock(NOW))


def _graded_duplicate(tmp_path):
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _attempt(vault, repository, "pi_svd_define_001", {"correctness": 4}, FrozenClock(NOW))
    _attempt(vault, repository, "pi_svd_restated_001", {"states_factorization": 0}, FrozenClock(NOW))
    before = _belief(repository)
    assert any(row[0] == DUP for row in before)
    return paths, repository, before


def test_a_merge_interrupted_before_its_file_write_keeps_the_facets_evidence_apart(tmp_path, monkeypatch):
    """While facets.yaml still lists the retired facet, its evidence stays its own."""

    paths, repository, before = _graded_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, "_write_facets")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    assert list_actions(repository)[0]["status"] == "applying" and DUP in load_vault(paths.root).evidence_facets
    _project(paths, repository)  # any later re-projection: a grade, a sync, a sidecar start
    assert _belief(repository) == before


def test_an_undo_interrupted_after_its_file_write_keeps_the_restored_facets_evidence_apart(tmp_path, monkeypatch):
    paths, repository, before = _graded_duplicate(tmp_path)
    applied = _merge(paths, repository)
    assert not any(row[0] == DUP for row in _belief(repository))
    with monkeypatch.context() as patched:
        _kill_at(patched, "_delete_merge_rows")
        with pytest.raises(_Killed):
            undo_action(paths.root, repository, applied["action_id"], clock=_CLOCK)
    assert list_actions(repository)[0]["status"] == "undoing" and _merge_rows(paths) == [(DUP, SHARED)]
    assert DUP in load_vault(paths.root).evidence_facets
    _project(paths, repository)
    assert _belief(repository) == before


def test_a_merge_interrupted_after_its_file_write_already_resolves_through_the_alias(tmp_path, monkeypatch):
    from learnloop.content.facet_identity.actions import recover_interrupted_actions

    paths, repository, _before = _graded_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, "refresh_derived_state")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    _project(paths, repository)
    during = _belief(repository)
    assert not any(row[0] == DUP for row in during)
    recover_interrupted_actions(paths.root, repository, clock=_CLOCK)
    assert list_actions(repository)[0]["status"] == "applied" and _belief(repository) == during


def test_the_sidecar_finishes_an_interrupted_merge_when_it_opens_the_vault(tmp_path, monkeypatch):
    from learnloop_sidecar.context import SidecarContext

    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    with monkeypatch.context() as patched:
        _kill_at(patched, "_write_facets")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    context = SidecarContext()
    context.load(paths.root, maintenance=False)
    assert list_actions(repository)[0]["status"] == "applied"
    assert DUP not in context.vault.evidence_facets and DUP in context.vault.evidence_facets[SHARED].aliases


def test_recovery_withdraws_a_merge_that_a_criterion_graded_meanwhile_names_both_facets(tmp_path, monkeypatch):
    """Graded while the intent waited, a criterion naming both facets would be counted twice (F1)."""

    from learnloop.content.facet_identity.actions import recover_interrupted_actions

    paths, repository = _vault_targeting(tmp_path / "vault", [(SHARED, "primary"), (DUP, "primary")])
    with monkeypatch.context() as patched:
        _kill_at(patched, "_write_facets")
        with pytest.raises(_Killed):
            _merge(paths, repository)
    _attempt(load_vault(paths.root), repository, "pi_both_001", {"states": 0}, FrozenClock(NOW))
    graded = _belief(repository)
    (row,) = recover_interrupted_actions(paths.root, repository, clock=_CLOCK)
    assert (row["from"], row["to"]) == ("applying", "abandoned")
    assert DUP in load_vault(paths.root).evidence_facets and _merge_rows(paths) == []
    assert list_actions(repository)[0]["status"] == "abandoned" and _belief(repository) == graded


def test_dataset_exports_keep_the_merge_history_an_undo_removes_from_facet_merges():
    from learnloop.db.table_roles import TABLE_ROLES, TableRole
    from learnloop.substrate.dataset import _CAPTURED_WORKFLOW_TABLES

    assert TABLE_ROLES["facet_merges"] is TableRole.RAW_LEDGER
    assert "facet_identity_actions" in _CAPTURED_WORKFLOW_TABLES
