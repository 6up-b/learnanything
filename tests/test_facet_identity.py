"""Facet identity (handoff §4): grouping, the judge, the ledger, dedupe, the regression set.

Every judge here is a fake (tests/facet_identity_fakes.py); nothing reaches a
network. The regression set is the facet-duplicate judging study's 39 facets
and labels (tests/facet_identity_regression.json).
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.content.facet_identity.actions import list_actions, normalized_entry, undo_action
from learnloop.content.facet_identity.dedupe import plan_dedupe, run_dedupe
from learnloop.content.facet_identity.grouping import FacetNode, neighbourhood_groups
from learnloop.content.facet_identity.judge import (
    DeciderGroupJudge,
    FacetPartitionVerdict,
    FacetSetVerdict,
    LLMGroupJudge,
    Member,
    PROMPT_VERSION,
    TASK,
    build_request,
    partition_from_pairs,
    pricing_for,
    validate_partition,
)
from learnloop.content.facet_identity.plan import build_plan
from learnloop.content.facet_identity.views import judge_view, union_payload
from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, SynthFacet
from learnloop.db.repositories import Repository
from learnloop.vault.loader import add_subject, init_vault, load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.facet_identity_fakes import FakeDecider, FakeFacetJudge, clusters_from_pairs, regression_data
from tests.helpers import append_config_toml

_CLOCK = FrozenClock(datetime(2026, 10, 12, 12, 0, 0, tzinfo=UTC))
_NOW = "2026-10-12T12:00:00Z"


# --- helpers ------------------------------------------------------------------


def _regression_vault(root: Path) -> tuple[Path, Repository, dict]:
    """A fresh vault holding the study's 39 facets, their concepts and graph."""

    data = regression_data()
    init_vault(root, clock=_CLOCK)
    add_subject(root, "vector-spaces", "Vector Spaces", clock=_CLOCK)
    vault = load_vault(root)
    paths = VaultPaths(vault.root, vault.config)
    write_yaml(paths.concepts_path, {"schema_version": 1, "concepts": {
        concept["id"]: {"title": concept["title"], "type": concept["type"], "aliases": [], "description": None,
                        "tags": [], "created_at": _NOW, "updated_at": _NOW}
        for concept in data["concepts"]
    }})
    write_yaml(paths.relations_path, {"schema_version": 1, "edges": [
        {"id": f"edge_{index}", "relation_type": edge["relation_type"], "source": edge["source"],
         "target": edge["target"], "strength": 1.0, "rationale": None, "created_at": _NOW, "updated_at": _NOW}
        for index, edge in enumerate(data["edges"])
    ]})
    write_yaml(paths.facets_path, {"schema_version": 2, "facets": [
        {**facet, "aliases": [], "status": "reviewed", "version": 1,
         "provenance": {"origin": "sourceset_synthesis", "source_refs": []}}
        for facet in data["facets"]
    ]})
    loaded = load_vault(root)
    assert loaded.issues == []
    return root, Repository(VaultPaths(loaded.root, loaded.config).sqlite_path), data


def _study_judge(data: dict, **kwargs) -> FakeFacetJudge:
    """A fake judge that merges exactly the study's merge-worthy clusters."""

    claim_of = {facet["id"]: judge_view(facet)["claim"] for facet in data["facets"]}
    clusters = [[claim_of[facet_id] for facet_id in cluster] for cluster in clusters_from_pairs(data["must_merge"])]
    return FakeFacetJudge(clusters=clusters, **kwargs)


def _ledger(sqlite_path: Path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute("SELECT * FROM judgment_ledger WHERE task = ?", (TASK,)).fetchall()
    finally:
        connection.close()


def _caps(**overrides) -> SpendCaps:
    return SpendCaps(**{"max_pairs": 10_000, "max_candidates": 1_000, **overrides})


def _members(*facets: dict, existing: bool = True, kind: str = "facet") -> list[Member]:
    return [Member(label="", key=facet["id"], subject_kind=kind, subject_id=facet["id"], existing=existing,
                   view=judge_view(facet)) for facet in facets]


# --- payload union -------------------------------------------------------------


def test_merge_unions_lists_and_sources_and_absorb_adds_the_claim():
    survivor = {"id": "f_a", "claim": "A", "preconditions": ["p1"], "positive_examples": ["e1"], "aliases": ["a"],
                "provenance": {"origin": "sourceset_synthesis", "source_refs": [{"ref_id": "s", "locator": "1"}]}}
    retired = {"id": "f_b", "claim": "B", "preconditions": ["P1 ", "p2"], "positive_examples": ["e2"],
               "aliases": ["b"], "provenance": {"origin": "sourceset_synthesis",
                                                "source_refs": [{"ref_id": "s", "locator": "1"}, {"ref_id": "s", "locator": "2"}]}}
    merged = union_payload(survivor, [retired], action="merge", alias_ids=["f_b"])
    assert merged["claim"] == "A"
    assert merged["preconditions"] == ["p1", "p2"]  # exact repeats (case/space) dropped
    assert merged["positive_examples"] == ["e1", "e2"]
    assert merged["aliases"] == ["a", "f_b", "b"]
    assert [ref["locator"] for ref in merged["provenance"]["source_refs"]] == ["1", "2"]
    assert survivor["preconditions"] == ["p1"]  # inputs untouched

    absorbed = union_payload(survivor, [retired], action="absorb", absorb_as="example")
    assert absorbed["positive_examples"] == ["e1", "B", "e2"]
    as_precondition = union_payload(survivor, [retired], action="absorb", absorb_as="precondition")
    assert as_precondition["preconditions"][:3] == ["p1", "B", "p2"]


# --- grouping ---------------------------------------------------------------------


def test_neighbourhoods_link_concepts_graph_lexical_and_the_embedding_shortlist():
    nodes = [
        FacetNode("a", {"claim": "alpha beta gamma"}, concept="c1"),
        FacetNode("b", {"claim": "delta"}, concept="c1"),
        FacetNode("c", {"claim": "epsilon"}, concept="c2"),
        FacetNode("d", {"claim": "zeta eta theta"}, concept="c9"),
        FacetNode("e", {"claim": "zeta eta theta"}, concept="c8"),
        FacetNode("f", {"claim": "lonely"}, concept="c7"),
    ]
    grouping = neighbourhood_groups(nodes, concept_edges=[("c1", "c2")])
    assert grouping.groups == [["a", "b", "c"], ["d", "e"]]
    assert grouping.links == {"same_concept": 1, "concept_graph": 1, "lexical": 1}
    # The embedding shortlist links "f" to its nearest neighbour.
    vectors = {key: np.eye(6)[index] for index, key in enumerate("abcdef")}
    vectors["f"] = vectors["d"] * 0.9 + 0.1
    grouping = neighbourhood_groups(nodes, concept_edges=[("c1", "c2")], vectors=vectors, top_k=1)
    assert grouping.shortlist == "embedding" and grouping.links.get("embedding", 0) >= 1
    assert "f" in {key for group in grouping.groups for key in group}


def test_an_oversized_neighbourhood_is_split_and_every_facet_lands_once():
    nodes = [FacetNode(f"f{index:02d}", {"claim": f"claim {index}"}, concept=f"c{index % 5}") for index in range(23)]
    edges = [("c0", "c1"), ("c1", "c2"), ("c2", "c3"), ("c3", "c4")]
    by_concept = neighbourhood_groups(nodes, concept_edges=edges, max_group_size=6)
    assert by_concept.split_components == 1
    members = [key for group in by_concept.groups for key in group]
    assert len(members) == len(set(members))
    assert all(len(group) <= 6 for group in by_concept.groups)
    rng = np.random.default_rng(7)
    vectors = {node.key: rng.normal(size=8) for node in nodes}
    by_vectors = neighbourhood_groups(nodes, concept_edges=edges, vectors=vectors, max_group_size=6,
                                      shortlist_edges=False)
    members = [key for group in by_vectors.groups for key in group]
    assert len(members) == len(set(members)) and all(len(group) <= 6 for group in by_vectors.groups)
    assert by_vectors.shortlist == "none"


def test_the_regression_neighbourhood_holds_every_merge_worthy_pair():
    data = regression_data()
    nodes = [FacetNode(facet["id"], facet, concept=facet["concept_id"]) for facet in data["facets"]]
    grouping = neighbourhood_groups(nodes, concept_edges=[(e["source"], e["target"]) for e in data["edges"]])
    group_of = {key: index for index, group in enumerate(grouping.groups) for key in group}
    for left, right in data["must_merge"]:
        assert group_of[left] == group_of[right], (left, right)


# --- the partition ------------------------------------------------------------------


def test_partition_validation_is_conservative():
    facets = [{"id": f"f_{name}", "claim": name} for name in "abcd"]
    request = build_request(_members(*facets), mode="consolidate")
    label = {member.key: member.label for member in request.members}
    verdict = FacetPartitionVerdict(sets=[
        FacetSetVerdict(members=[label["f_a"], label["f_b"], "F99"], action="merge", canonical="F99"),
        FacetSetVerdict(members=[label["f_b"], label["f_c"]], action="absorb", canonical=label["f_c"]),
        FacetSetVerdict(members=[label["f_c"], label["f_d"]], action="keep_distinct"),
    ])
    sets, notes = validate_partition(request, verdict)
    assert [(s.action, s.survivor, s.retired) for s in sets] == [("merge", "f_a", ["f_b"])]
    assert any("unknown label" in note for note in notes)
    assert any("already placed" in note for note in notes)


def test_attach_keeps_registered_facets_apart_and_makes_one_survive():
    registered = [{"id": "facet_x", "claim": "x"}, {"id": "facet_y", "claim": "y"}]
    candidate = {"id": "cand", "claim": "x again"}
    members = _members(*registered) + _members(candidate, existing=False, kind="facet_candidate")
    request = build_request(members, mode="attach")
    labels = {member.key: member.label for member in request.members}
    assert labels == {"facet_x": "E1", "facet_y": "E2", "cand": "N1"}
    assert len(request.pairs()) == 2  # registered pairs are never asked
    verdict = FacetPartitionVerdict(sets=[FacetSetVerdict(members=["N1", "E1", "E2"], action="merge", canonical="N1")])
    sets, notes = validate_partition(request, verdict)
    assert [(s.survivor, s.retired) for s in sets] == [("facet_x", ["cand"])]
    assert any("not merged at ingest" in note for note in notes)


def test_the_decider_partition_never_chains_against_a_distinct_verdict():
    facets = [{"id": f"f_{name}", "claim": name} for name in "abc"]
    request = build_request(_members(*facets), mode="consolidate")
    choices = {
        ("f_a", "f_b"): ("same_skill", {"same_skill": 0.9}),
        ("f_b", "f_c"): ("same_skill", {"same_skill": 0.8}),
        ("f_a", "f_c"): ("distinct", {"distinct": 0.9}),
    }
    sets = partition_from_pairs(request, choices)
    assert [(s.action, s.survivor, s.retired) for s in sets] == [("merge", "f_a", ["f_b"])]
    absorb = partition_from_pairs(request, {("f_a", "f_b"): ("first_special_case", {"first_special_case": 0.9})})
    assert [(s.action, s.survivor, s.retired) for s in absorb] == [("absorb", "f_b", ["f_a"])]


# --- the judge, the ledger and spend ---------------------------------------------------


@pytest.fixture
def vault_repo(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    return root, repository, data


def test_judge_writes_one_ledger_row_per_pair_and_never_pays_twice(vault_repo):
    root, repository, data = vault_repo
    vault = load_vault(root)
    requests, _summary = plan_dedupe(vault)
    assert len(requests) == 1 and len(requests[0].members) == 39
    judge_client = _study_judge(data)
    judge = LLMGroupJudge(client=judge_client, provider="codex_luna", model="fake-judge-1",
                          caps=_caps(), pricing=pricing_for(None), repository=repository, owner_id="run1")
    outcomes = judge.run(requests)
    assert outcomes[0].status == "judged" and len(judge_client.requests) == 1
    rows = _ledger(repository.sqlite_path)
    assert len(rows) == 741  # every pair of the 39 facets: same or different
    assert {row["judge"] for row in rows} == {"llm"}
    assert {row["judge_model"] for row in rows} == {"fake-judge-1"}
    assert {row["prompt_version"] for row in rows} == {PROMPT_VERSION}
    assert {row["left_kind"] for row in rows} == {"facet"}
    same = {frozenset((row["left_id"], row["right_id"])) for row in rows if row["verdict"] == "same"}
    for left, right in data["must_merge"]:
        assert frozenset((left, right)) in same
    for left, right in data["must_stay_distinct"]:
        assert frozenset((left, right)) not in same
    # A rerun reuses the checkpoint and the ledger rows: no call, no new row.
    again = LLMGroupJudge(client=judge_client, provider="codex_luna", model="fake-judge-1",
                          caps=_caps(), pricing=pricing_for(None), repository=repository, owner_id="run2")
    reused = again.run(plan_dedupe(load_vault(root))[0])
    assert reused[0].status == "reused" and len(judge_client.requests) == 1
    assert len(_ledger(repository.sqlite_path)) == 741
    assert reused[0].judgment_ids == outcomes[0].judgment_ids


def test_spend_caps_stop_the_judge_before_a_call(vault_repo):
    root, repository, data = vault_repo
    judge_client = _study_judge(data)
    judge = LLMGroupJudge(client=judge_client, provider="codex_luna", model="fake-judge-1",
                          caps=SpendCaps(max_calls=0), pricing=pricing_for(None), repository=repository,
                          owner_id="run1")
    outcomes = judge.run(plan_dedupe(load_vault(root))[0])
    assert outcomes[0].status == "not_run" and outcomes[0].error == "SpendLimitExceeded"
    assert judge_client.requests == [] and _ledger(repository.sqlite_path) == []


def test_a_failing_judge_is_retried_within_the_cap_then_gives_up(vault_repo):
    root, repository, data = vault_repo
    flaky = _study_judge(data, fail=1)
    judge = LLMGroupJudge(client=flaky, provider="codex_luna", model="fake-judge-1",
                          caps=_caps(max_retries=2), pricing=pricing_for(None), repository=repository,
                          owner_id="run1")
    assert judge.run(plan_dedupe(load_vault(root))[0])[0].status == "judged"
    assert len(flaky.requests) == 2
    down = _study_judge(data, fail=5)
    judge = LLMGroupJudge(client=down, provider="codex_luna", model="fake-judge-2",
                          caps=_caps(max_retries=1), pricing=pricing_for(None), repository=repository,
                          owner_id="run2")
    outcome = judge.run(plan_dedupe(load_vault(root))[0])[0]
    assert outcome.status == "failed" and outcome.error == "AIProviderUnavailable"
    assert len(down.requests) == 2


def _ledger_accepts_decider(sqlite_path: Path) -> bool:
    connection = sqlite3.connect(sqlite_path)
    try:
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='judgment_ledger'"
        ).fetchone()[0]
    finally:
        connection.close()
    return "'decider'" in schema


def test_the_decider_answers_per_pair_choices_and_partitions(vault_repo):
    root, repository, data = vault_repo
    facets = [facet for facet in data["facets"] if "zero_vector" in facet["id"] or "symbol_0" in facet["id"]]
    request = build_request(_members(*facets), mode="consolidate")
    decider = FakeDecider(choose=lambda first, second: "same_skill")
    if not _ledger_accepts_decider(repository.sqlite_path):
        pytest.skip("judge='decider' needs router R0's judgment_ledger CHECK (not merged on this branch)")
    judge = DeciderGroupJudge(client=decider, model=decider.model, caps=_caps(), pricing=pricing_for(decider.model),
                              repository=repository, owner_id="run1")
    outcome = judge.run([request])[0]
    assert outcome.status == "judged" and len(outcome.sets) == 1
    assert {row["judge"] for row in _ledger(repository.sqlite_path)} == {"decider"}


def test_the_decider_asks_one_choice_question_per_pair():
    data = regression_data()
    facets = [facet for facet in data["facets"] if "zero_vector" in facet["id"] or "symbol_0" in facet["id"]]
    request = build_request(_members(*facets), mode="consolidate")
    decider = FakeDecider(choose=lambda first, second: "distinct")

    class _NoLedger:
        def atomic(self):
            from contextlib import nullcontext
            return nullcontext()

        def connection(self):
            class _Connection:
                def execute(self, *args, **kwargs):
                    return None
            return _Connection()

    judge = DeciderGroupJudge(client=decider, model=decider.model, caps=SpendCaps(),
                              pricing=pricing_for(decider.model), repository=_NoLedger(), owner_id="run1")
    outcome = judge.run([request])[0]
    assert outcome.status == "judged" and outcome.sets == []
    assert len(decider.calls) == 1
    assert len(decider.calls[0]["questions"]) == len(request.pairs()) == 3


# --- dedupe ------------------------------------------------------------------------------


def test_dedupe_dry_run_plans_calls_and_cost_with_no_client_or_change(vault_repo):
    root, repository, data = vault_repo
    before = (root / "facets.yaml").read_text(encoding="utf-8")
    exploding = _study_judge(data, fail=99)
    report = run_dedupe(root, dry_run=True, client=exploding)
    assert report["status"] == "dry_run"
    assert report["estimate"]["calls"] == 1 and report["estimate"]["pairs"] == 741
    assert report["billing"] == "subscription" and report["route"]["model"] == "fake-judge-1"
    assert exploding.requests == []
    assert (root / "facets.yaml").read_text(encoding="utf-8") == before
    assert _ledger(repository.sqlite_path) == [] and list_actions(repository) == []


def test_dedupe_regression_set_merges_the_agreed_pairs_and_keeps_the_distinct_ones(vault_repo):
    root, repository, data = vault_repo
    original = {facet["id"]: normalized_entry(entry) for facet, entry in zip(
        data["facets"], read_yaml(root / "facets.yaml")["facets"])}
    report = run_dedupe(root, client=_study_judge(data), clock=_CLOCK)
    assert report["status"] == "complete", report
    assert len(report["actions"]) == 5 and report["refused"] == []
    vault = load_vault(root)
    assert len(vault.evidence_facets) == 39 - 10
    for left, right in data["must_merge"]:
        assert vault.canonical_facet_id(left) == vault.canonical_facet_id(right), (left, right)
    for left, right in data["must_stay_distinct"]:
        assert vault.canonical_facet_id(left) != vault.canonical_facet_id(right), (left, right)
    merges = dict(sqlite3.connect(repository.sqlite_path).execute(
        "SELECT retired_facet_id, surviving_facet_id FROM facet_merges").fetchall())
    assert len(merges) == 10
    # Undo every action: facets.yaml returns to exactly what it held.
    for action in list_actions(repository):
        undo_action(root, repository, action["id"], clock=_CLOCK)
    restored = {entry["id"]: normalized_entry(entry) for entry in read_yaml(root / "facets.yaml")["facets"]}
    assert restored == original
    assert [entry["id"] for entry in read_yaml(root / "facets.yaml")["facets"]] == [f["id"] for f in data["facets"]]
    assert sqlite3.connect(repository.sqlite_path).execute("SELECT COUNT(*) FROM facet_merges").fetchone()[0] == 0
    assert {action["status"] for action in list_actions(repository)} == {"undone"}


def test_dedupe_kill_switch_refuses(vault_repo):
    root, _repository, data = vault_repo
    append_config_toml(root, "[facet_identity]\nenabled = false")
    judge = _study_judge(data)
    assert run_dedupe(root, client=judge)["status"] == "disabled"
    assert judge.requests == []


# --- the in-run plan on the regression set ---------------------------------------------


def test_in_run_consolidation_of_the_regression_set(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    # The run's candidates are the 39 facets; nothing is registered yet.
    write_yaml(root / "facets.yaml", {"schema_version": 2, "facets": []})
    candidate = SourceSetSynthesis(facets=[
        SynthFacet(client_item_id=facet["id"], concept_id=facet["concept_id"], kind=facet["kind"],
                   claim=facet["claim"], preconditions=facet["preconditions"] or [],
                   positive_examples=facet["positive_examples"] or [],
                   negative_examples=facet["negative_examples"] or [], non_goals=facet["non_goals"] or [],
                   applicability=facet["applicability"] or [])
        for facet in data["facets"]
    ])
    judge = _study_judge(data)
    plan = build_plan(candidate, vault=load_vault(root), repository=repository, run_id="run1", judge_client=judge)
    assert plan is not None and plan.status == "judged"
    assert len(plan.retirements) == 10 and {r.scope for r in plan.retirements.values()} == {"in_run"}

    def survivor(key: str) -> str:
        retirement = plan.retirements.get(key)
        return str(retirement.survivor_client) if retirement else key

    for left, right in data["must_merge"]:
        assert survivor(left) == survivor(right), (left, right)
    for left, right in data["must_stay_distinct"]:
        assert survivor(left) != survivor(right), (left, right)
    rows = _ledger(repository.sqlite_path)
    assert len(rows) == 741 and {row["left_kind"] for row in rows} == {"facet_candidate"}
    # The plan is data: it round-trips through the synthesis run record.
    from learnloop.content.facet_identity.plan import FacetIdentityPlan

    assert FacetIdentityPlan.from_dict(plan.as_dict()).as_dict() == plan.as_dict()


def test_the_plan_is_off_with_the_kill_switch(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    append_config_toml(root, "[facet_identity]\nenabled = false")
    judge = _study_judge(data)
    candidate = SourceSetSynthesis(facets=[SynthFacet(client_item_id="a", claim="x"), SynthFacet(client_item_id="b", claim="x")])
    assert build_plan(candidate, vault=load_vault(root), repository=repository, run_id="r", judge_client=judge) is None
    assert judge.requests == []
