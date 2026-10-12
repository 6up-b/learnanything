"""Slice 2 T1 §3.4: recurrence groups, the no-chaining rule and the key switch."""

from __future__ import annotations

import pytest

from learnloop.db.repositories import Repository
from learnloop.matching.union import UnionEdge, effective_verdicts, union_with_refusals
from learnloop.recurrence import is_group_key, recurrence_key
from learnloop.substrate.recurrence_groups import claim_for_citation, compute_groups, refresh_recurrence_groups
from learnloop.vault.loader import load_vault

from tests.diagnosis_split_helpers import at, build_diagnosis_vault, seed_attempt, transpose_error
from tests.helpers import set_algorithm_version
from tests.recurrence_fakes import record_verdict
from tests.split_live_helpers import append_config

V_SAME = "Believes V and V transpose are the same matrix."
V_REWORDED = "Thinks the last SVD factor never needs transposing."
OTHER = "Forgets that singular values are non-negative."


def _edge(left, right, verdict, authority=2, judge="llm", at_="2026-01-01", ref=None):
    return UnionEdge(left=left, right=right, verdict=verdict, authority=authority, judge=judge,
                     source="judgment", ref=ref or f"{left}-{right}-{verdict}-{at_}", occurred_at=at_)


# -- the pure union ------------------------------------------------------------------------


def test_no_chaining_a_b_b_c_with_a_not_c_never_makes_one_group():
    result = union_with_refusals(
        ["a", "b", "c"],
        [_edge("a", "b", "same", at_="1"), _edge("b", "c", "same", at_="2"), _edge("a", "c", "different", at_="0")],
        order={"a": 0, "b": 1, "c": 2},
    )
    roots = result.root_of
    assert roots["a"] == roots["b"] != roots["c"]
    assert len(result.refused) == 1
    assert result.refused[0].edge.pair() == frozenset({"b", "c"})
    assert result.refused[0].blocking.pair() == frozenset({"a", "c"})


def test_a_lower_authority_different_does_not_block_a_higher_same():
    result = union_with_refusals(
        ["a", "b", "c"],
        [_edge("a", "b", "same"), _edge("b", "c", "same", at_="2"), _edge("a", "c", "different", authority=1, judge="learner_card")],
        order={"a": 0, "b": 1, "c": 2},
    )
    assert len(set(result.root_of.values())) == 1 and not result.refused


def test_highest_authority_then_latest_verdict_wins_and_unsure_never_counts():
    effective, conflicts = effective_verdicts([
        _edge("a", "b", "same", authority=2, at_="1"),
        _edge("a", "b", "different", authority=4, judge="owner", at_="0"),
        _edge("b", "a", "unsure", authority=4, judge="owner", at_="5"),
        _edge("c", "d", "different", at_="1"),
        _edge("c", "d", "same", at_="2"),
        _edge("e", "e", "different", at_="3"),
    ])
    assert effective[frozenset({"a", "b"})].verdict == "different"
    assert effective[frozenset({"c", "d"})].verdict == "same"
    assert [edge.left for edge in conflicts] == ["e"]


def test_the_oldest_class_roots_its_group_and_each_member_records_its_join():
    result = union_with_refusals(["x", "y", "z"], [_edge("z", "y", "same"), _edge("y", "x", "same", at_="2")],
                                 order={"x": 0, "y": 1, "z": 2})
    assert set(result.root_of.values()) == {"x"}
    assert set(result.joined_by) == {"y", "z"}


# -- the builder on a seeded vault -------------------------------------------------------------


@pytest.fixture
def seeded(tmp_path):
    paths = build_diagnosis_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    for attempt_id, item_id, offset, statement in (
        ("att_a", "pi_svd_compute_001", 1, V_SAME),
        ("att_b", "pi_svd_compute_002", 2, V_REWORDED),
        ("att_c", "pi_svd_compute_001", 3, V_SAME),
        ("att_d", "pi_svd_compute_002", 4, OTHER),
    ):
        seed_attempt(
            vault, repository, attempt_id=attempt_id, item_id=item_id, answer=f"answer {attempt_id}",
            when=at(offset), points={"setup": 2, "result": 0}, error=transpose_error(statement, quote="answer"),
        )
    set_algorithm_version(paths, "mvp-0.11")
    return paths, load_vault(paths.root), repository


def _episode(repository, attempt_id):
    rows = [row for row in repository.causal_hypotheses_for_attempt(attempt_id) if row["status"] != "open_set"]
    assert rows, attempt_id
    return rows[0]


def test_no_merges_leave_every_key_exact_and_the_projection_empty(seeded):
    _paths, vault, repository = seeded
    before = repository._projected_causal_candidates("lo_svd_compute")
    report = refresh_recurrence_groups(vault, repository)
    assert report["active"] is True and report["member_count"] == 0
    assert repository.recurrence_group_map() == {}
    after = repository._projected_causal_candidates("lo_svd_compute")
    assert after == before
    head = _episode(repository, "att_a")
    assert recurrence_key(head, repository.recurrence_group_map()) == head["statement_normalized"]


def test_a_same_verdict_merges_two_classes_into_one_group_key(seeded):
    _paths, vault, repository = seeded
    a, b = _episode(repository, "att_a"), _episode(repository, "att_b")
    record_verdict(repository, left=b["episode_key"], right=a["episode_key"], verdict="same")
    refresh_recurrence_groups(vault, repository)
    groups = repository.recurrence_group_map()
    key_a, key_b = recurrence_key(a, groups), recurrence_key(b, groups)
    assert key_a == key_b and is_group_key(key_a)
    # The exact class of att_a (att_c repeats it) joins with it.
    assert recurrence_key(_episode(repository, "att_c"), groups) == key_a
    assert recurrence_key(_episode(repository, "att_d"), groups) == _episode(repository, "att_d")["statement_normalized"]
    projected = repository._projected_causal_candidates("lo_svd_compute")
    merged = [row for row in projected if row["statement_normalized"] == key_a]
    assert len(merged) == 1 and merged[0]["occurrence_count"] == 3
    assert set(merged[0]["item_ids"]) == {"pi_svd_compute_001", "pi_svd_compute_002"}
    # A raw statement of either class finds the group's candidate.
    assert repository.misconception_candidate_by_normalized("lo_svd_compute", b["statement_normalized"])["id"] == merged[0]["id"]
    members = {row["episode_key"]: row for row in repository.recurrence_groups()}
    assert members[a["episode_key"]]["joined_by"] == "root"
    assert members[b["episode_key"]]["joined_by"] == "judgment"
    assert members[_episode(repository, "att_c")["episode_key"]]["joined_by"] == "exact_key"


def test_an_owner_different_refuses_the_judge_merge_and_logs_it(seeded):
    _paths, vault, repository = seeded
    a, b = _episode(repository, "att_a"), _episode(repository, "att_b")
    record_verdict(repository, left=b["episode_key"], right=a["episode_key"], verdict="same")
    d = _episode(repository, "att_d")
    record_verdict(repository, left=d["episode_key"], right=b["episode_key"], verdict="same")
    record_verdict(repository, left=d["episode_key"], right=a["episode_key"], verdict="different", judge="owner")
    refresh_recurrence_groups(vault, repository)
    groups = repository.recurrence_group_map()
    assert recurrence_key(a, groups) == recurrence_key(b, groups)
    assert recurrence_key(d, groups) != recurrence_key(a, groups)
    refused = repository.recurrence_review("refused_union")
    assert len(refused) == 1 and refused[0]["detail"]["blocking_judge"] == "owner"


def test_a_different_verdict_inside_one_exact_class_is_a_review_case_not_a_split(seeded):
    _paths, vault, repository = seeded
    a, c = _episode(repository, "att_a"), _episode(repository, "att_c")
    record_verdict(repository, left=c["episode_key"], right=a["episode_key"], verdict="different", judge="owner")
    refresh_recurrence_groups(vault, repository)
    assert repository.recurrence_review("exact_key_conflict")
    assert recurrence_key(a, repository.recurrence_group_map()) == recurrence_key(c, repository.recurrence_group_map())


def test_the_successor_and_its_kill_switch_gate_the_projection(seeded):
    paths, vault, repository = seeded
    a, b = _episode(repository, "att_a"), _episode(repository, "att_b")
    record_verdict(repository, left=b["episode_key"], right=a["episode_key"], verdict="same")
    refresh_recurrence_groups(vault, repository)
    assert repository.recurrence_group_map()
    append_config(paths.root, "[recurrence]\nenabled = false")
    refresh_recurrence_groups(load_vault(paths.root), repository)
    assert repository.recurrence_group_map() == {} and repository.recurrence_state() is None
    set_algorithm_version(paths, "mvp-0.10")
    paths.root.joinpath("learnloop.toml").write_text(
        paths.root.joinpath("learnloop.toml").read_text(encoding="utf-8").replace("enabled = false", "enabled = true"),
        encoding="utf-8",
    )
    refresh_recurrence_groups(load_vault(paths.root), repository)
    assert repository.recurrence_group_map() == {}


def test_an_unchanged_fingerprint_skips_the_rebuild(seeded):
    _paths, vault, repository = seeded
    assert refresh_recurrence_groups(vault, repository)["rebuilt"] is True
    assert refresh_recurrence_groups(vault, repository)["rebuilt"] is False
    a, b = _episode(repository, "att_a"), _episode(repository, "att_b")
    record_verdict(repository, left=b["episode_key"], right=a["episode_key"], verdict="same")
    assert refresh_recurrence_groups(vault, repository)["rebuilt"] is True


def test_attempt_level_owner_verdicts_resolve_only_to_one_class_per_side(seeded):
    _paths, vault, repository = seeded
    record_verdict(repository, left="att_b", right="att_a", verdict="same", judge="owner", kind="attempt")
    refresh_recurrence_groups(vault, repository)
    groups = repository.recurrence_group_map()
    assert recurrence_key(_episode(repository, "att_a"), groups) == recurrence_key(_episode(repository, "att_b"), groups)
    # An attempt with no hypotheses cannot be resolved: a review case, no merge.
    record_verdict(repository, left="att_missing", right="att_a", verdict="same", judge="owner", kind="attempt")
    refresh_recurrence_groups(vault, repository)
    unresolved = repository.recurrence_review("unresolved_link")
    assert any(row["left_ref"] == "att_missing" for row in unresolved)


def test_planted_subjects_never_touch_vault_groups(seeded):
    _paths, vault, repository = seeded
    record_verdict(repository, left="builtin:x:a", right="builtin:x:b", verdict="same", kind="planted_hypothesis")
    refresh_recurrence_groups(vault, repository)
    assert repository.recurrence_group_map() == {}


def test_claim_lookup_survives_a_claim_dropped_by_validation():
    proposal = {
        "pattern_claims": [
            {"hypothesis_ref": "cause:0:0", "relation": "disconfirming", "cited": [{"attempt_id": "x", "quote": "q1"}]},
            {"hypothesis_ref": "cause:0:1", "relation": "same_mechanism", "cited": [{"attempt_id": "y", "quote": "q2"}]},
        ]
    }
    # claim_index 2: one malformed claim before it was dropped by validation.
    claim = claim_for_citation(proposal, {"claim_index": 2, "attempt_id": "y", "quote": "q2"})
    assert claim is not None and claim["relation"] == "same_mechanism"
    assert claim_for_citation(proposal, {"claim_index": 0, "attempt_id": "z", "quote": "q"}) is None


def test_compute_groups_is_a_pure_read(seeded):
    _paths, _vault, repository = seeded
    a, b = _episode(repository, "att_a"), _episode(repository, "att_b")
    record_verdict(repository, left=b["episode_key"], right=a["episode_key"], verdict="same")
    with repository.connection() as connection:
        first = compute_groups(connection)
        second = compute_groups(connection)
    assert first.members == second.members and first.group_count == 1
    assert repository.recurrence_groups() == []


def test_registry_disagreements_need_an_informative_ranking():
    """§3.5: log the diagnoser's registry match against the top-1 neighbour,
    only when the ranking covered at least two records."""

    from learnloop.substrate.recurrence_groups import EpisodeIndex, _Build, _source_registry_disagreements

    def diagnosis(universe, match):
        return {
            "id": f"d{universe}{match['kind']}",
            "attempt_id": "att",
            "created_at": "2026-01-01",
            "proposal": {"event_diagnoses": [{"event_index": 0, "registry_match": match}]},
            "retrieval": {"registry_retrieval": {
                "universe": universe, "model_id": "m",
                "matches": [{"kind": "durable", "registry_id": "r1", "rank": 1, "score": 0.4},
                            {"kind": "durable", "registry_id": "r2", "rank": 2, "score": 0.1}],
            }},
        }

    build = _Build(index=EpisodeIndex([]))
    _source_registry_disagreements(build, [
        diagnosis(1, {"kind": "new"}),
        diagnosis(2, {"kind": "durable", "id": "r1"}),
        diagnosis(3, {"kind": "durable", "id": "r2"}),
        diagnosis(4, {"kind": "abstain"}),
        diagnosis(5, {"kind": "new"}),
    ])
    cases = sorted((row["source_ref"], row["left_ref"]) for row in build.reviews.values())
    assert cases == [("diagnosis:d3durable", "durable:r2"), ("diagnosis:d5new", "new")]
