"""Facet identity composed with main at its merge (merge/facet-identity).

Owner decisions (2026-10-12):

* ``merge_locked_facets`` defaulted to true: an identity-locked facet merged
  live like any other, with the one-tap undo. Facet locks were then removed
  altogether (facets/locks-and-depends-on); the key is a retired compatibility
  key and each action names the facets whose evidence it re-keyed instead.
* The judge is cheap and live, and router R0's Decider (``judge='decider'``)
  is accepted on the ``facet_identity_judge`` route, receipts included.
* The ledger records the merged pairs plus the shortlisted different pairs
  only (not every pair of a judged neighbourhood).

Composition: facet identity uses Slice 2 T1's matching maths (the shortlist's
mean-centred unit rows and the no-chaining union), and Slice 2 T5's
nominations and the D2 mint gate keep working with facet identity on.
"""

from __future__ import annotations

from datetime import UTC, datetime
import itertools
import json
import random
import re
import sqlite3

import numpy as np
import pytest

from learnloop.ai.execution import model_call
from learnloop.ai.spend import SpendCaps
from learnloop.clock import FrozenClock
from learnloop.content.facet_identity import grouping as grouping_module
from learnloop.content.facet_identity import judge as judge_module
from learnloop.content.facet_identity.actions import list_actions, undo_action
from learnloop.content.facet_identity.dedupe import run_dedupe
from learnloop.content.facet_identity.grouping import centred_unit, shortlist_pairs
from learnloop.content.facet_identity.judge import (
    DECIDER_QUESTION_SET_VERSION,
    PROMPT_VERSION,
    TASK,
    DeciderGroupJudge,
    DecidedSet,
    LLMGroupJudge,
    Member,
    build_judge,
    build_request,
    partition_from_pairs,
    pricing_for,
    resolve_route,
)
from learnloop.content.facet_identity.plan import build_plan, candidate_subject_id
from learnloop.content.facet_identity.views import judge_view
from learnloop.content.synthesis.ai_contracts import SourceSetSynthesis, SynthFacet
from learnloop.content.synthesis.graph_nomination import facet_query
from learnloop.content.synthesis.synthesis_gates import facet_tokens, jaccard
from learnloop.db.repositories import Repository
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.decider_fakes import fake_decisions
from tests.facet_identity_fakes import FakeFacetJudge
from tests.helpers import append_config_toml
from tests.test_facet_identity import _regression_vault, _study_judge
from tests.test_facet_identity_actions import DUP, SHARED, _lock_shared, _merge, _vault_with_duplicate

_CLOCK = FrozenClock(datetime(2026, 10, 13, 12, 0, 0, tzinfo=UTC))
SHARED_CLAIM = "SVD factorizes into U, Sigma, V^T."
DUP_CLAIM = "Every matrix A can be written A = U Sigma V^T."


def _ledger(sqlite_path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute("SELECT * FROM judgment_ledger WHERE task = ?", (TASK,)).fetchall()
    finally:
        connection.close()


def _receipts(sqlite_path) -> list[sqlite3.Row]:
    connection = sqlite3.connect(sqlite_path)
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            "SELECT * FROM model_call_receipts WHERE owner_kind = 'facet_identity' ORDER BY started_at"
        ).fetchall()
    finally:
        connection.close()


def _one_concept(paths) -> None:
    facets = read_yaml(paths.facets_path)
    for entry in facets["facets"]:
        entry["concept_id"] = "singular_value_decomposition"
    write_yaml(paths.facets_path, facets)


def _route(root, provider: str) -> None:
    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    assert "[ai.routing]\n" in text
    path.write_text(text.replace("[ai.routing]\n", f'[ai.routing]\nfacet_identity_judge = "{provider}"\n', 1),
                    encoding="utf-8")


# --- owner decision: facets with evidence merge (facet locks removed) -------------------


def test_facets_with_evidence_merge_whatever_the_retired_lock_key_says(tmp_path):
    from learnloop.config.schema import FacetIdentityConfig
    from tests.helpers import append_config_toml

    assert FacetIdentityConfig().merge_locked_facets is True  # kept, unread, for the snapshots
    paths, vault, repository = _vault_with_duplicate(tmp_path)
    _lock_shared(vault, repository)
    append_config_toml(paths.root, "[facet_identity]\nmerge_locked_facets = false")
    applied = _merge(paths, repository)
    assert applied["status"] == "applied" and SHARED in applied["evidence"]
    assert DUP in load_vault(paths.root).evidence_facets[SHARED].aliases
    (action,) = list_actions(repository)
    assert SHARED in action["detail"]["evidence"] and "lock_reasons" not in action["detail"]
    assert undo_action(paths.root, repository, applied["action_id"], clock=_CLOCK)["status"] == "undone"
    assert DUP in load_vault(paths.root).evidence_facets


def test_dedupe_applies_a_set_with_evidence(tmp_path):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    _one_concept(paths)
    _lock_shared(load_vault(paths.root), repository)
    report = run_dedupe(paths.root, client=FakeFacetJudge(clusters=[[SHARED_CLAIM, DUP_CLAIM]]), clock=_CLOCK)
    assert report["status"] == "complete" and "lock_policy" not in report
    (action,) = report["actions"]
    assert action["survivor"]["id"] == SHARED and SHARED in action["evidenced_facets"]
    assert load_vault(paths.root).canonical_facet_id(DUP) == SHARED


def test_an_absorb_into_a_registered_facet_grows_its_examples_whatever_its_history(tmp_path):
    from tests.test_facet_identity_ingest import _attach_absorb

    _root, repo, result, restated = _attach_absorb(tmp_path, absorb_as="example")
    (action,) = result.facet_identity["actions"]
    assert "locked" not in action and not action.get("contract_note")
    facet_rows = [row for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"]
    assert set(facet_rows[0]["payload"]) == {"id", "aliases", "positive_examples"}
    assert facet_rows[0]["payload"]["positive_examples"][-1] == restated


# --- owner decision: the Decider serves the facet_identity_judge route -------------------


def test_a_decider_profile_may_serve_the_facet_identity_judge_route_only():
    from learnloop.ai.routing import route_profile_mismatch
    from learnloop.config.schema import DEFAULT_DECIDER_PROVIDER, DEFAULT_EMBEDDING_PROVIDER, LearnLoopConfig

    config = LearnLoopConfig()
    assert route_profile_mismatch(config, DEFAULT_DECIDER_PROVIDER, "facet_identity_judge") is None
    assert route_profile_mismatch(config, "codex_luna", "facet_identity_judge") is None
    assert route_profile_mismatch(config, "openrouter_haiku", "facet_identity_judge") is None
    # Nothing else widens: a decider still serves no generation route, and an
    # embedding profile still serves no judge.
    assert route_profile_mismatch(config, DEFAULT_DECIDER_PROVIDER, "grading") is not None
    assert route_profile_mismatch(config, DEFAULT_DECIDER_PROVIDER, None) is not None
    assert route_profile_mismatch(config, DEFAULT_EMBEDDING_PROVIDER, "facet_identity_judge") is not None


def test_a_configured_decider_route_builds_the_decider_judge_without_a_call(tmp_path, monkeypatch):
    from learnloop.config.schema import DEFAULT_DECIDER_PROVIDER

    root, repository, _data = _regression_vault(tmp_path / "vault")
    _route(root, DEFAULT_DECIDER_PROVIDER)
    vault = load_vault(root)
    planned = resolve_route(vault.config)
    assert planned.decider and planned.problem is None and planned.pricing.known
    # Readiness is key presence only; constructing the client sends nothing.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-not-a-key")
    judge, route = build_judge(vault, repository, owner_id="run1", caps=SpendCaps())
    assert route.problem is None, route.problem
    assert isinstance(judge, DeciderGroupJudge) and route.decider
    assert route.as_dict()["judge"] == "decider"


def _decider_answers(pairs_same: set[frozenset[str]]):
    """A fake Decisions API reply: same_skill for the named claim pairs, else distinct."""

    def respond(body):
        by_label = {facet["label"]: facet for facet in body["state"]["facets"]}
        answers = {}
        for name, question in body["questions"].items():
            match = re.search(r"Compare facet (\S+) with facet (\S+?)\.", question["instructions"])
            assert match is not None
            claims = frozenset((by_label[match.group(1)]["claim"], by_label[match.group(2)]["claim"]))
            choice = "same_skill" if claims in pairs_same else "distinct"
            answers[name] = {"type": "choice", "choice": choice, "confidence": 0.9,
                             "probabilities": {option: (0.91 if option == choice else 0.03)
                                               for option in question["criteria"]}}
        payload = {"model": body["model"] + "-20261006", "answers": answers, "id": "gen-dec-facets",
                   "provider": "Perplexity", "usage": {"input_tokens": 120, "output_tokens": 3, "cost": 0.0000024}}
        return 200, payload, {}

    return respond


def test_dedupe_through_a_decider_route_merges_and_writes_labelled_receipts(tmp_path, monkeypatch):
    paths, _vault, repository = _vault_with_duplicate(tmp_path)
    _one_concept(paths)
    with fake_decisions(respond=_decider_answers({frozenset((SHARED_CLAIM, DUP_CLAIM))})) as server:
        monkeypatch.setenv("LEARNLOOP_TEST_DECIDER_KEY", server.key)
        append_config_toml(paths.root, f"""
            [ai.providers.test_decider]
            type = "decider"
            api = "openrouter"
            base_url = "{server.base_url}"
            api_key_env = "LEARNLOOP_TEST_DECIDER_KEY"
            model = "perplexity/pplx-decider-v1.1-27b"
        """)
        _route(paths.root, "test_decider")
        report = run_dedupe(paths.root, clock=_CLOCK)
    assert report["status"] == "complete", report
    assert report["route"]["judge"] == "decider" and report["route"]["provider"] == "test_decider"
    assert [action["survivor"]["id"] for action in report["actions"]] == [SHARED]
    assert load_vault(paths.root).canonical_facet_id(DUP) == SHARED
    assert len(server.requests) == 1  # one request: every pair of the group as typed questions
    rows = _ledger(repository.sqlite_path)
    assert rows and {row["judge"] for row in rows} == {"decider"}
    assert {row["prompt_version"] for row in rows} == {DECIDER_QUESTION_SET_VERSION}
    (receipt,) = _receipts(repository.sqlite_path)
    assert receipt["judge"] == "decider" and receipt["question_set_version"] == DECIDER_QUESTION_SET_VERSION
    assert receipt["purpose"] == "facet_identity_judgment" and receipt["status"] == "completed"
    assert receipt["provider"] == "test_decider"


class _ReceiptedJudge(FakeFacetJudge):
    """The fake structured judge, wrapped as a real transport records a call."""

    def complete(self, request):
        with model_call(self, purpose=request.purpose, prompt=request.prompt):
            return super().complete(request)


def test_the_structured_judge_labels_its_receipts_llm(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    report = run_dedupe(root, client=_ReceiptedJudge(clusters=_study_judge(data).clusters), clock=_CLOCK)
    assert report["status"] == "complete"
    receipts = _receipts(repository.sqlite_path)
    assert receipts and {row["purpose"] for row in receipts} == {"facet_identity_judgment"}
    assert {(row["judge"], row["question_set_version"]) for row in receipts} == {("llm", PROMPT_VERSION)}


# --- owner decision: merged pairs plus shortlisted different pairs ---------------------------


class _VectorNominator:
    """Deterministic definition vectors for the run's candidates (no model)."""

    def vectors(self, queries):
        out = {}
        for query in queries:
            if query is not None:
                seed = int(query.content_hash.split(":")[-1][:8], 16)
                out[query.content_hash] = np.random.default_rng(seed).normal(size=24)
        return out

    def nominate(self, recipe, queries, *, k):
        return {}


def test_the_ledger_records_merged_pairs_and_shortlisted_different_pairs_only(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    write_yaml(root / "facets.yaml", {"schema_version": 2, "facets": []})
    candidate = SourceSetSynthesis(facets=[
        SynthFacet(client_item_id=facet["id"], concept_id=facet["concept_id"], kind=facet["kind"],
                   claim=facet["claim"], preconditions=facet["preconditions"] or [],
                   positive_examples=facet["positive_examples"] or [],
                   negative_examples=facet["negative_examples"] or [], non_goals=facet["non_goals"] or [],
                   applicability=facet["applicability"] or [])
        for facet in data["facets"]
    ])
    nominator = _VectorNominator()
    plan = build_plan(candidate, vault=load_vault(root), repository=repository, run_id="run1",
                      judge_client=_study_judge(data), nominator=nominator)
    assert plan is not None and plan.status == "judged" and len(plan.retirements) == 10

    # The shortlist, computed independently: each candidate's top-4 by
    # mean-centred cosine over the run's definition vectors, and the lexical
    # near-duplicate pairs.
    payloads = {facet.client_item_id: facet.model_dump(mode="json") for facet in candidate.facets}
    queries = {key: facet_query(payload, record_id=key) for key, payload in payloads.items()}
    by_hash = nominator.vectors(list(queries.values()))
    unit = centred_unit({key: by_hash[query.content_hash] for key, query in queries.items()})
    shortlisted = {frozenset((left, right)) for left, right, _score, _rank in shortlist_pairs(unit, top_k=4)}
    tokens = {key: facet_tokens(payload) for key, payload in payloads.items()}
    shortlisted |= {frozenset(pair) for pair in itertools.combinations(sorted(payloads), 2)
                    if jaccard(tokens[pair[0]], tokens[pair[1]]) >= 0.85}
    survivor = {key: str(r.survivor_client) for key, r in plan.retirements.items()}
    clusters: dict[str, set[str]] = {}
    for key in payloads:
        clusters.setdefault(survivor.get(key, key), set()).add(key)
    merged = {frozenset(pair) for members in clusters.values() for pair in itertools.combinations(sorted(members), 2)}

    rows = _ledger(repository.sqlite_path)
    key_of = {candidate_subject_id(payload): key for key, payload in payloads.items()}
    recorded = {frozenset((key_of[row["left_id"]], key_of[row["right_id"]])): row for row in rows}
    assert len(rows) == len(recorded) < 741  # not every pair of the 39-facet neighbourhood
    assert {pair for pair, row in recorded.items() if row["verdict"] == "same"} == merged
    different = {pair for pair, row in recorded.items() if row["verdict"] == "different"}
    assert different == shortlisted - merged
    assert all(json.loads(row["rationale"])["shortlisted"] for pair, row in recorded.items() if pair in different)


def test_an_undo_still_supersedes_the_judges_merged_rows(tmp_path):
    root, repository, data = _regression_vault(tmp_path / "vault")
    assert run_dedupe(root, client=_study_judge(data), clock=_CLOCK)["status"] == "complete"
    action = list_actions(repository)[-1]
    undo_action(root, repository, action["id"], clock=_CLOCK)
    rows = _ledger(repository.sqlite_path)
    members = {action["survivor_facet_id"], *action["retired_facet_ids"]}
    llm_same = {row["id"] for row in rows if row["judge"] == "llm" and row["verdict"] == "same"
                and {row["left_id"], row["right_id"]} <= members}
    owner = [row for row in rows if row["judge"] == "owner"]
    assert llm_same and llm_same <= {row["supersedes_id"] for row in owner}


# --- composition: Slice 2 T1's matching maths ---------------------------------------------


def test_facet_grouping_centres_vectors_with_matchings_shortlist_maths(monkeypatch):
    from learnloop.matching import shortlist as matching_shortlist

    calls = []
    original = matching_shortlist.centred_unit

    def spy(vectors):
        calls.append(sorted(vectors))
        return original(vectors)

    monkeypatch.setattr(matching_shortlist, "centred_unit", spy)
    rng = np.random.default_rng(3)
    vectors = {key: rng.normal(size=6) for key in "abcd"}
    unit = grouping_module.centred_unit(vectors)
    assert calls == [["a", "b", "c", "d"]]
    expected = original(vectors)
    assert set(unit) == set(expected) and all(np.array_equal(unit[key], expected[key]) for key in unit)
    # Facet identity's own rule stays: vectors of mixed widths shortlist nothing.
    assert grouping_module.centred_unit({"a": np.ones(3), "b": np.ones(4)}) == {}


def _reference_partition(request, choices):
    """The branch's own no-chaining union, kept as the equivalence oracle."""

    keys = [member.key for member in request.members]
    parent = {key: key for key in keys}
    members_of = {key: {key} for key in keys}

    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key

    distinct = {frozenset(pair) for pair, (choice, _p) in choices.items() if choice == "distinct"}
    general_of: dict[str, int] = {}
    edges = sorted(((float(probs.get(choice, 0.0)), pair, choice) for pair, (choice, probs) in choices.items()
                    if choice != "distinct"), key=lambda row: (-row[0], row[1]))
    special = set()
    for _p, (first, second), choice in edges:
        if request.mode == "attach":
            a, b = request.by_key(first), request.by_key(second)
            if a is not None and b is not None and a.existing and b.existing:
                continue
        left, right = find(first), find(second)
        if left == right:
            continue
        if any(frozenset((x, y)) in distinct for x in members_of[left] for y in members_of[right]):
            continue
        if request.mode == "attach":
            existing = [k for k in (*members_of[left], *members_of[right]) if (m := request.by_key(k)) and m.existing]
            if len(existing) > 1:
                continue
        keep, drop = sorted((left, right))
        parent[drop] = keep
        members_of[keep] |= members_of.pop(drop)
        if choice == "first_special_case":
            general_of[second] = general_of.get(second, 0) + 1
            special.add(frozenset((first, second)))
        elif choice == "second_special_case":
            general_of[first] = general_of.get(first, 0) + 1
            special.add(frozenset((first, second)))
    sets = []
    for root in sorted(members_of):
        component = sorted(members_of[root])
        if len(component) < 2:
            continue
        existing = [key for key in component if (m := request.by_key(key)) and m.existing and request.mode == "attach"]
        survivor = existing[0] if existing else sorted(
            component, key=lambda key: (-general_of.get(key, 0), request.by_key(key).label))[0]
        absorb = any(frozenset((a, b)) in special for a in component for b in component if a < b)
        sets.append(DecidedSet(action="absorb" if absorb else "merge", survivor=survivor,
                               retired=[key for key in component if key != survivor],
                               absorb_as="example" if absorb else None,
                               rationale="decider: per-pair choices, no-chaining union"))
    return sets


def _random_request(rng: random.Random, mode: str):
    count = rng.randint(2, 7)
    members = [Member(label="", key=f"k{index}", subject_kind="facet", subject_id=f"k{index}",
                      existing=(mode == "attach" and rng.random() < 0.4), view={"claim": f"claim {index}"})
               for index in range(count)]
    if mode == "attach" and not any(m.existing for m in members):
        members[0] = Member(label="", key="k0", subject_kind="facet", subject_id="k0", existing=True,
                            view={"claim": "claim 0"})
    request = build_request(members, mode=mode)
    options = ["same_skill", "first_special_case", "second_special_case", "distinct", "distinct"]
    choices = {}
    for left, right in request.pairs():
        choice = rng.choice(options)
        p = rng.choice([0.4, 0.55, 0.7, 0.7, 0.9])
        choices[(left.key, right.key)] = (choice, {choice: p})
    return request, choices


def test_the_decider_partition_is_matchings_no_chaining_union(monkeypatch):
    from learnloop.matching import union as matching_union

    calls = []
    original = matching_union.union_with_refusals

    def spy(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(matching_union, "union_with_refusals", spy)
    rng = random.Random(20261013)
    for mode in ("consolidate", "attach"):
        for _ in range(150):
            request, choices = _random_request(rng, mode)
            got = partition_from_pairs(request, choices)
            assert [s.as_dict() for s in got] == [s.as_dict() for s in _reference_partition(request, choices)]
    assert len(calls) == 300


def test_the_head_schema_ledger_accepts_the_deciders_verdicts(tmp_path):
    root, repository, _data = _regression_vault(tmp_path / "vault")
    schema = sqlite3.connect(repository.sqlite_path).execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='judgment_ledger'").fetchone()[0]
    assert "'decider'" in schema


# --- composition: Slice 2 T5's nominations and the D2 mint gate ----------------------------


def _enable_t5(root) -> None:
    path = root / "learnloop.toml"
    text = path.read_text(encoding="utf-8")
    block = "[embedding]\nenabled = false\nbackfill_enabled = false\n"
    assert block in text
    text = text.replace(block, "[embedding]\nenabled = true\nbackfill_enabled = true\n")
    path.write_text(text.replace("dimensions = 4096", "dimensions = 64"), encoding="utf-8")
    append_config_toml(root, "[graph_nomination]\nenabled = true\ntop_k = 2")


def _t5_bootstrap(tmp_path, *, facet_identity: bool):
    from learnloop.content.synthesis.source_set_synthesis import create_study_map
    from learnloop.vault.writer import upsert_facet

    from tests.embedding_fakes import BagOfWordsEmbedder
    from tests.test_graph_nomination_ingest import _backfill
    from tests.test_source_set_synthesis import FakeSynthesisClient, _setup

    root, repo = _setup(tmp_path)
    upsert_facet(root, {
        "id": "facet_elimination", "kind": "procedure_contract",
        "claim": "Gaussian elimination reaches row echelon form",
        "instructional_repairs": ["practise one pivot at a time"],
    }, clock=_CLOCK)
    _enable_t5(root)
    if not facet_identity:
        append_config_toml(root, "[facet_identity]\nenabled = false")
    embedder = BagOfWordsEmbedder()
    _backfill(root, embedder, ("facet/definition",))
    judge = FakeFacetJudge(clusters=[])  # keeps every facet distinct
    result = create_study_map(root, "set_la", client=FakeSynthesisClient(), brief={"depth": "intro"},
                              repository=repo, clock=_CLOCK, embedding_client_factory=lambda: embedder,
                              facet_identity_client=judge)
    run = repo.synthesis_run(result.synthesis_run_id)
    facet_rows = sorted(
        (row["operation"], row["payload"]["id"], row["payload"].get("status"),
         tuple(row["payload"].get("aliases") or []))
        for row in repo.proposal_items(result.proposal_id) if row["item_type"] == "facet"
    )
    return run, facet_rows, judge


def test_t5_nominations_and_the_d2_gate_hold_with_facet_identity_on(tmp_path):
    on_run, on_rows, on_judge = _t5_bootstrap(tmp_path / "on", facet_identity=True)
    off_run, off_rows, off_judge = _t5_bootstrap(tmp_path / "off", facet_identity=False)
    # T5's nominations are recorded either way, each candidate with its
    # registered neighbours.
    for run in (on_run, off_run):
        record = run["coverage_decisions"]["graph_nomination"]
        assert record["summary"]["status"] == "active"
        assert record["candidates"] and all(c["embedding_neighbours"] for c in record["candidates"])
    assert [c["candidate_id"] for c in on_run["coverage_decisions"]["graph_nomination"]["candidates"]] == [
        c["candidate_id"] for c in off_run["coverage_decisions"]["graph_nomination"]["candidates"]]
    # The judge kept everything distinct, so D2 decided every candidate exactly
    # as without facet identity: the same facet rows, statuses and aliases.
    assert on_rows and on_rows == off_rows
    # With facet identity on the judge saw T5's registered nomination (an E*
    # member) for attach; off, it was never asked.
    plan = on_run["actual_usage"]["facet_identity"]
    assert plan["status"] == "judged" and plan["retirements"] == {}
    attach = [request["context"] for request in on_judge.requests if request["context"]["mode"] == "attach"]
    assert attach and any(view["label"].startswith("E") for context in attach for view in context["facets"])
    assert off_judge.requests == []
