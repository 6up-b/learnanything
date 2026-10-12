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


def _accept_decider(sqlite_path: Path) -> None:
    """Router R0's judgment_ledger rebuild, simulated: the CHECK accepts 'decider'.

    R0 (migration 174 on its branch) merges before this stage; until then the
    Decider's ledger rows need this rebuild in the test database.
    """

    if _ledger_accepts_decider(sqlite_path):
        return
    connection = sqlite3.connect(sqlite_path)
    try:
        objects = connection.execute(
            "SELECT type, sql FROM sqlite_master WHERE tbl_name = 'judgment_ledger' AND sql IS NOT NULL"
        ).fetchall()
        table = next(sql for kind, sql in objects if kind == "table")
        rebuilt = table.replace("'exact_key')", "'exact_key', 'decider')")
        assert rebuilt != table
        connection.executescript(
            "PRAGMA foreign_keys = OFF; BEGIN;"
            "ALTER TABLE judgment_ledger RENAME TO judgment_ledger_before_r0;"
            f"{rebuilt};"
            "INSERT INTO judgment_ledger SELECT * FROM judgment_ledger_before_r0;"
            "DROP TABLE judgment_ledger_before_r0;"
            + "".join(f"{sql};" for kind, sql in objects if kind in ("index", "trigger"))
            + "COMMIT;"
        )
    finally:
        connection.close()


def test_the_decider_answers_per_pair_choices_and_partitions(vault_repo):
    root, repository, data = vault_repo
    _accept_decider(repository.sqlite_path)
    facets = [facet for facet in data["facets"] if "zero_vector" in facet["id"] or "symbol_0" in facet["id"]]
    request = build_request(_members(*facets), mode="consolidate")
    decider = FakeDecider(choose=lambda first, second: "same_skill")
    judge = DeciderGroupJudge(client=decider, model=decider.model, caps=_caps(), pricing=pricing_for(decider.model),
                              repository=repository, owner_id="run1")
    outcome = judge.run([request])[0]
    assert outcome.status == "judged" and len(outcome.sets) == 1
    assert {row["judge"] for row in _ledger(repository.sqlite_path)} == {"decider"}


def test_the_decider_asks_one_choice_question_per_pair(vault_repo):
    _root, repository, data = vault_repo
    _accept_decider(repository.sqlite_path)
    facets = [facet for facet in data["facets"] if "zero_vector" in facet["id"] or "symbol_0" in facet["id"]]
    request = build_request(_members(*facets), mode="consolidate")
    decider = FakeDecider(choose=lambda first, second: "distinct")
    judge = DeciderGroupJudge(client=decider, model=decider.model, caps=SpendCaps(),
                              pricing=pricing_for(decider.model), repository=repository, owner_id="run1")
    outcome = judge.run([request])[0]
    assert outcome.status == "judged" and outcome.sets == []
    assert len(decider.calls) == 1
    assert len(decider.calls[0]["questions"]) == len(request.pairs()) == 3


# --- review F8: the ledger says what the judge said ------------------------------------


def test_a_rerun_of_the_decider_reuses_its_answers_and_ledger_rows(vault_repo):
    _root, repository, data = vault_repo
    _accept_decider(repository.sqlite_path)
    facets = [facet for facet in data["facets"] if "zero_vector" in facet["id"] or "symbol_0" in facet["id"]]
    request = build_request(_members(*facets), mode="consolidate")
    decider = FakeDecider(choose=lambda first, second: "same_skill")

    def judge(owner):
        return DeciderGroupJudge(client=decider, model=decider.model, caps=_caps(),
                                 pricing=pricing_for(decider.model), repository=repository, owner_id=owner)

    first = judge("run1").run([request])[0]
    rows = len(_ledger(repository.sqlite_path))
    again = judge("run2").run([request])[0]
    assert again.status == "reused" and len(decider.calls) == 1  # paid once
    assert len(_ledger(repository.sqlite_path)) == rows  # no duplicate rows
    assert again.judgment_ids == first.judgment_ids
    assert [(s.survivor, s.retired) for s in again.sets] == [(s.survivor, s.retired) for s in first.sets]


def test_the_ledger_keeps_the_judges_verdict_and_marks_repaired_and_omitted_pairs(vault_repo):
    import json

    _root, repository, _data = vault_repo
    registered = [{"id": "facet_x", "claim": "x"}, {"id": "facet_y", "claim": "y"}]
    candidates = [{"id": "cand", "claim": "x again"}, {"id": "cand_z", "claim": "z"}]
    request = build_request(
        _members(*registered) + _members(*candidates, existing=False, kind="facet_candidate"), mode="attach",
    )
    # The judge joins one candidate with BOTH registered facets; validation keeps
    # one registered facet, and "z" is never listed (kept distinct by the rule).
    client = FakeFacetJudge(clusters=[["x", "x again", "y"]])
    judge = LLMGroupJudge(client=client, provider="codex_luna", model="fake-judge-1", caps=_caps(),
                          pricing=pricing_for(None), repository=repository, owner_id="run1")
    outcome = judge.run([request])[0]
    assert [(s.survivor, s.retired) for s in outcome.sets] == [("facet_x", ["cand"])]
    rows = {frozenset((row["left_id"], row["right_id"])): (row["verdict"], json.loads(row["rationale"]))
            for row in _ledger(repository.sqlite_path)}
    verdict, detail = rows[frozenset(("facet_x", "cand"))]
    assert verdict == "same" and detail["applied"] is True and "repaired" not in detail
    verdict, detail = rows[frozenset(("facet_y", "cand"))]
    assert verdict == "same" and detail["applied"] is False  # the judge's verdict, not the repair
    assert "not merged at ingest" in detail["repaired"]
    assert set(detail["raw_set"]["members"]) == {"E1", "E2", "N1"}
    verdict, detail = rows[frozenset(("facet_x", "cand_z"))]
    assert verdict == "different" and detail["basis"] == "omitted" and detail["applied"] is False


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


# --- review F3: an undo is the owner's verdict, and it sticks ----------------------------


def test_an_undone_merge_is_an_owner_verdict_and_dedupe_never_reapplies_it(vault_repo):
    root, repository, data = vault_repo
    report = run_dedupe(root, client=_study_judge(data), clock=_CLOCK)
    assert report["status"] == "complete"
    first = list_actions(repository)[-1]
    survivor, retired = first["survivor_facet_id"], first["retired_facet_ids"]
    undone = undo_action(root, repository, first["id"], clock=_CLOCK)
    assert undone["owner_judgment_ids"]

    rows = _ledger(repository.sqlite_path)
    owner = [row for row in rows if row["judge"] == "owner"]
    members = {survivor, *retired}
    pairs = {frozenset((row["left_id"], row["right_id"])) for row in owner}
    assert pairs == {frozenset((a, b)) for a in members for b in members if a < b}
    assert {row["verdict"] for row in owner} == {"different"}
    superseded = {row["supersedes_id"] for row in owner}
    llm_same = {row["id"] for row in rows if row["judge"] == "llm" and row["verdict"] == "same"
                and frozenset((row["left_id"], row["right_id"])) in pairs}
    assert llm_same and llm_same <= superseded

    # A second pass (open question 2) with the same judge: the undone set stays apart.
    judge = _study_judge(data)
    again = run_dedupe(root, client=judge, clock=_CLOCK)
    assert again["status"] == "complete"
    vault = load_vault(root)
    for facet_id in retired:
        assert vault.canonical_facet_id(facet_id) == facet_id, "undone merge was re-applied"
    notes = [note for group in again["judged_groups"] for note in group["notes"]]
    assert any(note.startswith("owner verdict:") for note in notes)


def test_an_undone_in_run_merge_stays_apart_when_the_run_is_planned_again(tmp_path):
    from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis
    from learnloop.content.synthesis.source_set_synthesis import create_study_map

    from tests.test_facet_identity_ingest import DEF_CLAIM, DUP_CLAIM, DUP_ID, _with_duplicate
    from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

    root, repo = _setup(tmp_path, with_exam=False)
    judge = FakeFacetJudge(clusters=[[DEF_CLAIM, DUP_CLAIM]])
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(builder=_with_duplicate), repository=repo,
                              clock=_CLOCK, apply=True, facet_identity_client=judge)
    (action,) = result.facet_identity["actions"]
    undo_action(root, repo, action["id"], clock=_CLOCK)
    owner = [row for row in _ledger(repo.sqlite_path) if row["judge"] == "owner"]
    assert {(row["left_kind"], row["verdict"]) for row in owner} == {("facet_candidate", "different"),
                                                                    ("facet", "different")}
    assert any(row["supersedes_id"] for row in owner if row["left_kind"] == "facet_candidate")
    assert any({row["left_id"], row["right_id"]} == {"facet_symmetry_definition", DUP_ID}
               for row in owner if row["left_kind"] == "facet")

    # The same candidates planned again (a resynthesis, or a revalidation of
    # its candidate): the judge still says "same", the owner's verdict decides.
    candidate = SourceSetSynthesis.model_validate(repo.synthesis_run(result.synthesis_run_id)["candidate_output"])
    plan = build_plan(candidate, vault=load_vault(root), repository=repo, run_id="again", judge_client=judge)
    assert plan is not None
    retired_where = {key: (r.scope, r.survivor_client or r.survivor_facet) for key, r in plan.retirements.items()}
    dup_client = next(key for key in candidate_keys(candidate) if key.endswith("f_def_dup"))
    def_client = next(key for key in candidate_keys(candidate) if key.endswith("f_def"))
    # The restatement never rejoins the definition, as a candidate or as a vault facet...
    assert retired_where.get(dup_client) is None, retired_where
    # ...while the definition's own candidate is the registered definition it was minted as.
    assert retired_where.get(def_client) == ("attach", "facet_symmetry_definition")
    notes = [note for group in plan.groups for note in group["notes"]]
    assert any(note.startswith("owner verdict:") for note in notes)

    # Alone with the registered definition, the restatement's candidate is
    # still bound by the owner's verdict on the vault facet it restates.
    alone = SourceSetSynthesis.model_validate({**candidate.model_dump(mode="json"), "facets": [
        facet.model_dump(mode="json") for facet in candidate.facets if facet.client_item_id.endswith("f_def_dup")]})
    plan = build_plan(alone, vault=load_vault(root), repository=repo, run_id="alone", judge_client=judge)
    assert plan is not None and plan.retirements == {}, plan.retirements


def candidate_keys(candidate):
    return [str(facet.client_item_id) for facet in candidate.facets]


# --- review F11: splitting a large neighbourhood stays fast --------------------------------


def _reference_agglomerate(members, unit, cap):
    """The stage's original average-link split (recomputes every link each step)."""

    clusters = [[key] for key in sorted(members)]
    similarity = {(a, b): float(unit[a] @ unit[b]) for a in members for b in members if a < b}

    def link(left, right):
        return sum(similarity[(a, b) if a < b else (b, a)] for a in left for b in right) / (len(left) * len(right))

    while True:
        best = None
        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                if len(clusters[i]) + len(clusters[j]) > cap:
                    continue
                score = link(clusters[i], clusters[j])
                if best is None or score > best[0]:
                    best = (score, i, j)
        if best is None:
            return sorted(clusters)
        _score, i, j = best
        clusters[i] = sorted(clusters[i] + clusters[j])
        del clusters[j]


@pytest.mark.parametrize("seed,count,cap", [(1, 23, 6), (2, 40, 7), (3, 31, 40), (4, 12, 2)])
def test_the_heap_split_matches_the_reference_average_link(seed, count, cap):
    from learnloop.content.facet_identity.grouping import _agglomerate, centred_unit

    rng = np.random.default_rng(seed)
    unit = centred_unit({f"f{index:03d}": rng.normal(size=8) for index in range(count)})
    assert _agglomerate(list(unit), unit, cap) == _reference_agglomerate(list(unit), unit, cap)


def test_a_neighbourhood_of_hundreds_of_facets_splits_in_seconds():
    import time

    rng = np.random.default_rng(11)
    nodes = [FacetNode(f"f{index:04d}", {"claim": f"claim {index}"}, concept="c0") for index in range(600)]
    vectors = {node.key: rng.normal(size=32) for node in nodes}
    started = time.monotonic()
    grouping = neighbourhood_groups(nodes, vectors=vectors, max_group_size=40, shortlist_edges=False)
    elapsed = time.monotonic() - started
    members = [key for group in grouping.groups for key in group]
    assert len(members) == len(set(members)) and all(len(group) <= 40 for group in grouping.groups)
    assert elapsed < 30, elapsed
