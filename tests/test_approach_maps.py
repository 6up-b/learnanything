"""Adaptive hints H1: approach maps (spec_adaptive_hints_v1 §4.3, §4.3.1, §7.2-7.3, §9;
G-H1's maps clause, G-H9, G-H11, G-H13).

* Seeds: the reference solution, rubric and authored hints; the trace
  contract's recipes; PF's skeletons; the learner's own textbook worked
  examples through T6 (item-bound exclusions); the learner's own correct
  solutions to the item and its family (graded correct or PF-c valid). A
  seed an item lacks is absent.
* The validator in code, every rule; a failing map is re-asked once, then not
  stored, each validation in the ledger by reason.
* Triggers: build on serve (background, de-duplicated, never blocking,
  failing or changing a serve); the inline build H2 will call; the lazy
  learner-route merge; the owner's backfill and its dry run (writes nothing).
* Revision keys and supersession; family templates; the daily money cap and
  route fallback; the kill switch (nothing built or read; practice RPCs
  byte-identical).

Fakes only (``tests/approach_map_fakes.MapFake``, a ``StructuredClientFake``).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

import learnloop.clock as clock_module
import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores import approach_maps as store
from learnloop.hints import map_builder as MB
from learnloop.hints import map_seeds as MS
from learnloop.hints.maps import ApproachMapV1, MapContext, validate_map
from learnloop.vault.hashes import practice_item_hash
from learnloop.vault.loader import load_vault
from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.registry import METHOD_REGISTRY
from tests.approach_map_fakes import (
    EXPECTED,
    HINTS,
    ITEM,
    PROMPT,
    TRACE_CONTRACT,
    MapFake,
    add_attempt,
    add_skeleton,
    edge,
    good_map,
    ledger,
    map_vault,
    merge_as_new_route,
    node,
    receipts,
    rows,
    write_item,
)
from tests.helpers import append_config_toml

FROZEN = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)
MAPS_OFF = "[hints.maps]\nenabled = false\n"
METERED = "[hints]\nprice_per_million = 5.0\n"


def _call(ctx, name: str, params: dict):
    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def _repo(paths) -> Repository:
    return Repository.attach(paths.sqlite_path)


def _build(paths, client, *, item: str = ITEM, trigger: str = "cli", **options):
    return MB.build_map(load_vault(paths.root), _repo(paths), item, trigger=trigger, client=client, **options)


def _context(paths, item: str = ITEM, **seeds_options) -> tuple[MapContext, MS.MapSeeds]:
    vault = load_vault(paths.root)
    seeds = MS.assemble_seeds(vault, _repo(paths), vault.practice_items[item], retrieve=False, **seeds_options)
    return MB.map_context(vault, seeds), seeds


def _validate(paths, payload: dict, **seeds_options):
    context, _seeds = _context(paths, **seeds_options)
    return validate_map(ApproachMapV1.model_validate(payload), context)


@pytest.fixture
def frozen(monkeypatch):
    monkeypatch.setattr(clock_module.SystemClock, "now", lambda _self: FROZEN)
    return FROZEN


@pytest.fixture
def paths(tmp_path):
    return map_vault(tmp_path, trace_contract=TRACE_CONTRACT)


@pytest.fixture(autouse=True)
def _joined_background_builds():
    yield
    assert MB.wait_for_background_builds(30), "a background map build did not finish"


# -- seeds (§4.3 items 1-3) -------------------------------------------------------------


def test_seeds_carry_the_trace_contract_skeleton_rubric_and_authored_hints(paths):
    add_skeleton(paths.sqlite_path)
    context, seeds = _context(paths)
    assert [recipe["id"] for recipe in seeds.trace_contract["recipes"]] == ["cdf_route", "direct_route"]
    assert [skeleton["id"] for skeleton in seeds.skeletons] == ["sk_1"]
    assert seeds.authored_hints == HINTS
    assert [criterion["id"] for criterion in seeds.rubric] == ["cdf", "value"]
    assert seeds.checkpoint_ids == {"cdf", "value", "sk_cdf", "sk_value"}
    assert context.recipe_ids == {"cdf_route", "direct_route"}
    fake = MapFake()
    assert _build(paths, fake).status == "built"
    sent = fake.requests[0][1]
    assert sent["reference_solution"] == EXPECTED and sent["question"] == PROMPT
    assert sent["authored_hints"] == HINTS
    assert [recipe["id"] for recipe in sent["trace_contract"]["recipes"]] == ["cdf_route", "direct_route"]
    assert sent["solution_skeletons"][0]["techniques"] == ["integrate", "evaluate"]
    assert [criterion["id"] for criterion in sent["rubric"]] == ["cdf", "value"]
    [row] = rows(paths.sqlite_path)
    record = json.loads(row["seeds_json"])
    assert record["trace_contract"] == {"status": "available", "recipes": ["cdf_route", "direct_route"]}
    assert record["skeletons"] == [{"id": "sk_1", "model_id": "fake-skeleton-model", "prompt_version": "pf_skeleton.v1"}]
    assert record["authored_hints"] == 2
    # Which seeds, never their texts.
    assert "Integrate the density, then" not in row["seeds_json"] and HINTS[0] not in row["seeds_json"]


def test_a_seed_the_item_lacks_is_simply_absent(tmp_path):
    paths = map_vault(tmp_path, hints=[])
    _context_, seeds = _context(paths)
    assert seeds.trace_contract is None and seeds.skeletons == [] and seeds.attempts == []
    assert seeds.authored_hints == [] and seeds.template is None
    fake = MapFake()
    assert _build(paths, fake).status == "built"
    sent = fake.requests[0][1]
    for absent in ("trace_contract", "solution_skeletons", "worked_examples", "learner_solutions",
                   "family_template"):
        assert absent not in sent
    record = json.loads(rows(paths.sqlite_path)[0]["seeds_json"])
    assert record["trace_contract"] is None and record["skeletons"] == [] and record["spans"] == []
    assert record["retrieval"]["policy"] == "assisted_practice"


def test_worked_examples_come_from_t6_under_the_item_bound_policy(tmp_path):
    from learnloop.source_retrieval.find_sources import find_sources_for_caller
    from tests.source_service_fakes import build_textbook_vault

    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    vault = load_vault(paths.root)
    item = vault.practice_items["pi_eigen_1"]
    seen: list[dict] = []

    def spy(*args, **kwargs):
        seen.append(kwargs)
        return find_sources_for_caller(*args, **kwargs)

    found, meta = MS.source_worked_examples(vault, repository, item, find=spy)
    [call] = seen
    caller = call["caller"]
    assert (caller.kind, caller.context, caller.item_id) == ("code", "practice", item.id)
    assert call["roles"] == ("worked_example",) and call["verify"] is False and call["rewrite"] is False
    assert meta["policy"] == "assisted_practice"
    keys = {span.span_id for span in found}
    assert keys and keys <= set(spans["worked"])
    assert not keys & (set(spans["exercises"]) | set(spans["solutions"]))
    assert all(span.role == "worked_example" for span in found)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts").fetchone()[0] == 0
    # In a build the passages are seeds the builder reads and the row names.
    answer = good_map(goal_answer="")
    answer["edges"][0]["facet_ids"] = []
    fake = MapFake([answer])
    outcome = MB.build_map(vault, repository, "pi_eigen_1", trigger="cli", client=fake)
    assert outcome.status == "built", outcome
    sent = fake.requests[0][1]
    assert [example["ref"] for example in sent.get("worked_examples", [])]
    record = json.loads(rows(paths.sqlite_path)[0]["seeds_json"])
    assert {entry["span_id"] for entry in record["spans"]} <= set(spans["worked"])


def test_only_the_learners_own_correct_or_pfc_valid_solutions_in_the_family_are_seeds(tmp_path, monkeypatch):
    paths = map_vault(tmp_path, family_id="fam_cdf")
    write_item(paths, "pi_cdf_2", prompt="X has density f(x) = 3x^2 on [0, 1]. Find P(X ≤ 1/2).",
               expected="F(x) = x^3. Therefore P(X ≤ 1/2) = 1/8.", family_id="fam_cdf")
    write_item(paths, "pi_other", prompt="Unrelated.", expected="42")
    db = paths.sqlite_path
    add_attempt(db, "a_correct", created_at="2026-10-17T09:00:00+00:00")
    add_attempt(db, "a_sibling", item_id="pi_cdf_2", created_at="2026-10-17T09:05:00+00:00")
    add_attempt(db, "a_partial", correctness=0.5, created_at="2026-10-17T09:06:00+00:00")
    add_attempt(db, "a_wrong", correctness=0.0, created_at="2026-10-17T09:07:00+00:00")
    add_attempt(db, "a_pfc", correctness=0.75, created_at="2026-10-17T09:08:00+00:00")
    add_attempt(db, "a_dont_know", attempt_type="dont_know", created_at="2026-10-17T09:09:00+00:00")
    add_attempt(db, "a_empty", answer="  ", created_at="2026-10-17T09:10:00+00:00")
    add_attempt(db, "a_held", created_at="2026-10-17T09:11:00+00:00")
    add_attempt(db, "a_other", item_id="pi_other", created_at="2026-10-17T09:12:00+00:00")
    add_attempt(db, "a_ungraded", correctness=None, created_at="2026-10-17T09:13:00+00:00")
    monkeypatch.setattr(MS, "pfc_unverified_attempt_ids", lambda connection: frozenset({"a_pfc"}))
    monkeypatch.setattr(MS, "held_for_review_attempts", lambda connection, ids: frozenset({"a_held"}))
    _context_, seeds = _context(paths)
    assert [(attempt.attempt_id, attempt.basis) for attempt in seeds.attempts] == [
        ("a_pfc", "pfc_valid"), ("a_sibling", "correct"), ("a_correct", "correct")]
    assert [attempt.ref for attempt in seeds.attempts] == ["a1", "a2", "a3"]
    fake = MapFake()
    assert _build(paths, fake).status == "built"
    sent = fake.requests[0][1]
    assert [solution["ref"] for solution in sent["learner_solutions"]] == ["a1", "a2", "a3"]
    stored = json.loads(rows(db)[0]["map_json"])
    # The builder's refs are stored as the attempts' ids.
    assert stored["routes"][0]["learner_attempt_ids"] == ["a_pfc", "a_sibling", "a_correct"]


# -- the validator (§4.3 "Validation in code"; G-H9) -------------------------------------


def test_a_valid_map_passes_and_code_marks_the_leaks(paths):
    payload = good_map()
    payload["nodes"].insert(2, node("half", "step", "Plug in the point", "F(1/2) = 1/4"))
    payload["edges"] = [edge("g", "cdf", facets=("recall",)), edge("cdf", "half"), edge("half", "goal")]
    payload["routes"][0]["path"] = ["g", "cdf", "half", "goal"]
    result = _validate(paths, payload)
    assert result.valid, result.details
    assert result.verified_goal and result.goal_basis == "exact_key"
    # The goal always, and a step whose state gives the answer away.
    assert set(result.leak_marked_by_code) == {"goal", "half"}
    assert {item.id: item.leak for item in result.normalized.nodes} == {
        "g": False, "cdf": False, "half": True, "goal": True}


def _mutate(name: str) -> dict:
    payload = good_map()
    if name == "cycle":
        payload["edges"].append(edge("goal", "cdf"))
    elif name == "route_starts_at_a_step":
        payload["routes"][0]["path"] = ["cdf", "goal"]
    elif name == "route_skips_an_edge":
        payload["routes"][0]["path"] = ["g", "goal"]
    elif name == "route_stops_short":
        payload["routes"][0]["path"] = ["g", "cdf"]
    elif name == "foreign_facet":
        payload["edges"][0]["facet_ids"] = ["someone_elses_facet"]
    elif name == "empty_label":
        payload["nodes"][1]["label"] = "   "
    elif name == "label_leaks_a_leak_nodes_expression":
        payload["nodes"][1]["label"] = "Reach P = 1/4"
    elif name == "label_leaks_a_marked_leak_state":
        payload["nodes"][1]["leak"] = True
        payload["nodes"][0]["label"] = "Aim for F(x)=x^2"
    elif name == "unknown_checkpoint":
        payload["nodes"][1]["checkpoint_id"] = "not_a_checkpoint"
    elif name == "unknown_source_origin":
        payload["routes"].append({**payload["routes"][0], "id": "r_src", "origin": "source:s9"})
    elif name == "unknown_learner_origin":
        payload["routes"][0]["learner_attempt_ids"] = ["a7"]
    elif name == "unknown_recipe":
        payload["routes"].append({**payload["routes"][0], "id": "r_tc", "origin": "trace_contract:nope"})
    elif name == "no_reference_route":
        payload["routes"][0]["origin"] = "model"
    elif name == "no_route":
        payload["routes"] = []
    elif name == "goal_mismatch":
        payload["goal_answer"] = "1/3"
    elif name == "two_goals":
        payload["nodes"][1]["role"] = "goal"
    elif name == "dangling_edge":
        payload["edges"].append(edge("cdf", "nowhere"))
    return payload


@pytest.mark.parametrize(("case", "reason"), [
    ("cycle", "cycle"),
    ("route_starts_at_a_step", "route_not_given_to_goal"),
    ("route_skips_an_edge", "route_not_given_to_goal"),
    ("route_stops_short", "route_not_given_to_goal"),
    ("foreign_facet", "foreign_facet"),
    ("empty_label", "empty_label"),
    ("label_leaks_a_leak_nodes_expression", "label_leak"),
    ("label_leaks_a_marked_leak_state", "label_leak"),
    ("unknown_checkpoint", "unknown_checkpoint"),
    ("unknown_source_origin", "unknown_origin"),
    ("unknown_learner_origin", "unknown_origin"),
    ("unknown_recipe", "unknown_origin"),
    ("no_reference_route", "no_reference_route"),
    ("no_route", "no_route"),
    ("goal_mismatch", "goal_mismatch"),
    ("two_goals", "malformed"),
    ("dangling_edge", "malformed"),
])
def test_every_validation_rule_rejects_its_case(paths, case, reason):
    result = _validate(paths, _mutate(case))
    assert not result.valid and reason in result.reasons, (case, result.reasons)
    assert result.normalized is None


def test_links_to_existing_checkpoints_recipes_and_question_values_pass(paths):
    add_skeleton(paths.sqlite_path)
    payload = good_map()
    payload["nodes"][1]["checkpoint_id"] = "cdf"  # a trace-contract checkpoint
    payload["nodes"][2]["checkpoint_id"] = "sk_value"  # a skeleton checkpoint
    payload["routes"].append({**payload["routes"][0], "id": "r_tc", "origin": "trace_contract:direct_route"})
    # The question states 1/2: a label may name it.
    payload["nodes"][2]["label"] = "Evaluate the CDF at 1/2"
    result = _validate(paths, payload)
    assert result.valid, result.details


def test_a_goal_without_an_exact_key_is_stored_unverified(tmp_path):
    paths = map_vault(tmp_path, expected="Because U and V are orthogonal, the factorization exists; this proves it.")
    payload = good_map(goal_answer="")
    result = _validate(paths, payload)
    assert result.valid and not result.verified_goal and result.goal_basis == "no_exact_key"
    assert _build(paths, MapFake([payload])).status == "built"
    assert rows(paths.sqlite_path)[0]["verified_goal"] == 0


# -- the builder: one call, re-asked once, then not stored -----------------------------------


def test_a_build_stores_one_validated_version_with_its_receipt_and_verdict(paths, frozen):
    fake = MapFake()
    outcome = _build(paths, fake)
    assert outcome.status == "built" and outcome.version == 1 and outcome.rounds == 1
    assert outcome.billing == "subscription" and outcome.routes == {"reference": 1}
    [row] = rows(paths.sqlite_path)
    item = load_vault(paths.root).practice_items[ITEM]
    assert row["id"] == outcome.map_id and row["version"] == 1 and row["supersedes_id"] is None
    assert row["practice_item_hash"] == practice_item_hash(item) and row["trigger"] == "cli"
    assert row["model"] == "fake-map-model" and row["prompt_version"] == MB.PROMPT_VERSION
    assert row["verified_goal"] == 1 and json.loads(row["validation_json"])["valid"] is True
    assert ApproachMapV1.model_validate_json(row["map_json"]).goal_node_id == "goal"
    [receipt] = receipts(paths.sqlite_path)
    declared = json.loads(receipt["budget_json"])
    assert declared["cost_basis"] == "estimated_only" and declared["practice_index"]["task"] == "approach_map"
    [verdict] = ledger(paths.sqlite_path)
    assert (verdict["judge"], verdict["verdict"], verdict["left_id"]) == ("verifier", "valid", ITEM)
    # The same revision is current now: no second call.
    assert _build(paths, fake).status == "current" and fake.calls == 1
    assert MB.current_map(load_vault(paths.root), _repo(paths), ITEM)["id"] == row["id"]


def test_a_failing_map_is_reasked_once_with_its_reasons_then_not_stored(paths):
    bad = _mutate("cycle")
    fake = MapFake([bad, _mutate("foreign_facet")])
    outcome = _build(paths, fake)
    assert outcome.status == "not_stored" and outcome.rounds == 2 and fake.calls == 2
    assert outcome.reasons == ["foreign_facet"]
    assert rows(paths.sqlite_path) == []
    second = fake.requests[1][1]
    assert second["previous_answer_problems"]["reasons"] == ["cycle"]
    assert second["previous_answer_problems"]["previous_answer"]["edges"][-1]["to_node"] == "cdf"
    verdicts = [(row["verdict"], json.loads(row["rationale"])["reasons"]) for row in ledger(paths.sqlite_path)]
    assert verdicts == [("invalid_reasked", ["cycle"]), ("invalid_not_stored", ["foreign_facet"])]
    # A rerun recovers both paid answers from their checkpoints: nothing is paid again.
    again = _build(paths, fake)
    assert again.status == "not_stored" and fake.calls == 2
    # A serve does not retry a revision whose build was not stored; the owner's CLI does.
    assert _build(paths, fake, trigger="serve").status == "failed_before"


def test_a_map_failing_once_is_stored_from_the_reask(paths):
    fake = MapFake([_mutate("label_leaks_a_leak_nodes_expression"), good_map()])
    outcome = _build(paths, fake)
    assert outcome.status == "built" and outcome.rounds == 2
    assert [row["verdict"] for row in ledger(paths.sqlite_path)] == ["invalid_reasked", "valid"]


def test_a_failed_call_stores_nothing_and_says_so(paths):
    outcome = _build(paths, MapFake(fail=True))
    assert outcome.status == "failed" and "fake failure" in outcome.reason
    assert rows(paths.sqlite_path) == []


# -- revision keys, supersession, family templates ----------------------------------------


def test_a_revised_item_or_changed_seeds_gets_a_new_row_never_an_update(paths):
    fake = MapFake()
    first = _build(paths, fake)
    # The trace contract changes; practice_item_hash does not cover it.
    write_item(paths, trace_contract={"status": "available", "recipes": [TRACE_CONTRACT["recipes"][0]]})
    assert MB.current_map(load_vault(paths.root), _repo(paths), ITEM) is None
    second = _build(paths, fake)
    # The item is revised.
    write_item(paths, prompt="X has density f(x) = 2x on [0, 1]. Find P(X ≤ 1/2) exactly.",
               trace_contract={"status": "available", "recipes": [TRACE_CONTRACT["recipes"][0]]})
    third = _build(paths, fake)
    assert (first.version, second.version, third.version) == (1, 2, 3) and fake.calls == 3
    stored = rows(paths.sqlite_path)
    assert [row["supersedes_id"] for row in stored] == [None, first.map_id, second.map_id]
    assert stored[0]["practice_item_hash"] == stored[1]["practice_item_hash"] != stored[2]["practice_item_hash"]
    assert stored[0]["structure_hash"] != stored[1]["structure_hash"]
    with closing(connect(paths.sqlite_path)) as connection:
        for statement in ("UPDATE approach_maps SET map_json = '{}'", "DELETE FROM approach_maps"):
            with pytest.raises(sqlite3.IntegrityError, match="approach_maps"):
                connection.execute(statement)
        # One row per item revision and seeds, even for a racing builder.
        with pytest.raises(sqlite3.IntegrityError):
            store.insert_map(connection, {**{key: stored[2][key] for key in store.COLUMNS}, "id": "am_dup",
                                          "version": 4})
    assert rows(paths.sqlite_path)[0]["map_json"] == stored[0]["map_json"]


def test_a_siblings_builder_receives_the_familys_map_as_its_template(tmp_path):
    paths = map_vault(tmp_path, family_id="fam_cdf")
    write_item(paths, "pi_cdf_2", prompt="X has density f(x) = 3x^2 on [0, 1]. Find P(X ≤ 1/2).",
               expected="F(x) = x^3 on [0, 1]. Therefore P(X ≤ 1/2) = 1/8.", family_id="fam_cdf")
    fake = MapFake([good_map(), good_map(goal_answer="1/8", nodes=[
        node("g", "given", "Read the density", "f(x) = 3x^2 on [0, 1]"),
        node("cdf", "step", "Find the CDF on the support", "$F(x) = x^3$ on [0, 1]"),
        node("goal", "goal", "Evaluate the CDF at the point", "P(X ≤ 1/2) = 1/8")])])
    first = _build(paths, fake)
    assert "family_template" not in fake.requests[0][1]
    second = _build(paths, fake, item="pi_cdf_2")
    assert second.status == "built", second
    template = fake.requests[1][1]["family_template"]
    assert template == json.loads(rows(paths.sqlite_path)[0]["map_json"])
    stored = {row["practice_item_id"]: row for row in rows(paths.sqlite_path)}
    assert json.loads(stored["pi_cdf_2"]["seeds_json"])["family_template"] == {
        "map_id": first.map_id, "practice_item_id": ITEM}
    assert stored[ITEM]["family_id"] == stored["pi_cdf_2"]["family_id"] == "fam_cdf"
    # Each item keeps its own values and leak marks.
    assert json.loads(stored["pi_cdf_2"]["map_json"])["goal_answer"] == "1/8"


# -- the inline build (H2's entry; wired to no RPC) ---------------------------------------


def test_the_inline_build_builds_now_and_stores(paths):
    outcome = MB.build_map_inline(load_vault(paths.root), _repo(paths), ITEM, client=MapFake(),
                                  deadline=time.monotonic() + 30)
    assert outcome.status == "built" and rows(paths.sqlite_path)[0]["trigger"] == "inline"


def test_the_inline_build_waits_for_a_build_in_flight_and_never_builds_twice(paths):
    gate = threading.Event()
    slow = MapFake(gate=gate)
    vault = load_vault(paths.root)
    thread = MB.schedule_build_on_serve(vault, paths.sqlite_path, ITEM, client=slow)
    assert thread is not None and slow.started.wait(10)
    second = MapFake()
    results: list = []
    waiter = threading.Thread(target=lambda: results.append(MB.build_map_inline(
        vault, _repo(paths), ITEM, client=second, deadline=time.monotonic() + 30)))
    waiter.start()
    time.sleep(0.2)
    assert not results  # waiting on the serve's build
    gate.set()
    waiter.join(30)
    assert results[0].status == "current" and second.calls == 0 and slow.calls == 1
    assert [row["trigger"] for row in rows(paths.sqlite_path)] == ["serve"]


def test_no_rpc_reaches_the_inline_build_or_the_merge():
    import ast

    sidecar = Path(__file__).resolve().parents[1] / "src" / "learnloop_sidecar"
    imported: set[str] = set()
    for path in sidecar.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node_ in ast.walk(tree):
            if isinstance(node_, ast.ImportFrom) and (node_.module or "").startswith("learnloop.hints.map"):
                imported.update(alias.name for alias in node_.names)
            if isinstance(node_, ast.Attribute) and node_.attr in ("build_map_inline", "merge_learner_routes"):
                raise AssertionError(f"{path} reaches {node_.attr} (H2 wires it)")
    # The serve's background build is the only map entry any RPC reaches.
    assert imported == {"schedule_build_on_serve"}


# -- build on serve (§4.3.1 row 1) --------------------------------------------------------


def _sidecar(root: Path, client=None):
    ctx = SidecarContext()
    ctx.load(root)
    ctx.grading_provider_override = "manual"
    if client is not None:
        ctx.approach_map_client = client
    session = _call(ctx, "start_session", {"energy": "medium"})
    return ctx, session["sessionId"]


def _serve(ctx, session_id: str | None, item: str = ITEM):
    params = {"practiceItemId": item}
    if session_id is not None:
        params["sessionId"] = session_id
    return _call(ctx, "get_practice_item", params)


def test_a_serve_starts_one_background_build_and_never_waits_for_it(paths, frozen):
    gate = threading.Event()
    fake = MapFake(gate=gate)
    ctx, session_id = _sidecar(paths.root, fake)
    first = _serve(ctx, session_id)
    assert fake.started.wait(10)
    # The model is still answering, and the serve has already returned.
    assert rows(paths.sqlite_path) == []
    again = _serve(ctx, session_id)
    assert again == first
    gate.set()
    assert MB.wait_for_background_builds(30)
    assert fake.calls == 1, "concurrent serves start one build"
    [row] = rows(paths.sqlite_path)
    assert row["trigger"] == "serve"
    # Built once per revision: a later serve builds nothing.
    assert _serve(ctx, session_id) == first
    assert MB.wait_for_background_builds(30) and fake.calls == 1


def test_a_read_only_open_builds_nothing(paths):
    fake = MapFake()
    ctx, _session = _sidecar(paths.root, fake)
    _serve(ctx, None)
    assert MB.wait_for_background_builds(30) and fake.calls == 0


def test_a_failing_or_raising_build_never_reaches_the_serve(paths, frozen, monkeypatch):
    ctx, session_id = _sidecar(paths.root, MapFake(fail=True))
    baseline = _serve(ctx, session_id)
    assert MB.wait_for_background_builds(30) and rows(paths.sqlite_path) == []

    def broken(*args, **kwargs):
        raise RuntimeError("no threads today")

    monkeypatch.setattr(MB.threading, "Thread", broken)
    assert _serve(ctx, session_id) == baseline
    monkeypatch.setattr(MB, "schedule_build_on_serve", broken)
    import learnloop_sidecar.handlers.practice as practice

    monkeypatch.setattr(practice, "schedule_build_on_serve", broken)
    assert _serve(ctx, session_id) == baseline


def test_without_an_injected_client_the_test_guard_starts_no_build(paths, monkeypatch):
    called: list = []
    monkeypatch.setattr(MB, "_route_client", lambda *args: called.append(args) or (None, "no"))
    vault = load_vault(paths.root)
    assert MB.schedule_build_on_serve(vault, paths.sqlite_path, ITEM) is None
    monkeypatch.delenv(MB.BUILDS_ENV)
    thread = MB.schedule_build_on_serve(vault, paths.sqlite_path, ITEM)
    assert thread is not None and MB.wait_for_background_builds(30)
    assert called and rows(paths.sqlite_path) == []


# -- the lazy learner-route merge (§4.3 "approach mining", §4.3.1 row 3) --------------------


def test_new_correct_answers_gain_a_matching_route_or_open_a_learner_route(paths):
    fake = MapFake()
    first = _build(paths, fake)
    vault = load_vault(paths.root)
    assert MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake).status == "up_to_date"
    add_attempt(paths.sqlite_path, "a_one", created_at="2026-10-18T08:00:00+00:00")
    add_attempt(paths.sqlite_path, "a_wrong", correctness=0.0, created_at="2026-10-18T08:01:00+00:00")
    assert [attempt.attempt_id for attempt in MB.new_learner_attempts(vault, _repo(paths), ITEM)] == ["a_one"]
    matched = MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake)
    assert matched.status == "merged" and matched.version == 2
    assert fake.requests[-1][0] == "approach_map_merge"
    assert [solution["ref"] for solution in fake.requests[-1][1]["new_learner_solutions"]] == ["n1"]
    stored = rows(paths.sqlite_path)
    assert stored[1]["supersedes_id"] == first.map_id and stored[1]["trigger"] == "merge"
    assert json.loads(stored[1]["map_json"])["routes"][0]["learner_attempt_ids"] == ["a_one"]
    assert [entry["id"] for entry in json.loads(stored[1]["seeds_json"])["attempts"]] == ["a_one"]
    assert MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake).status == "up_to_date"
    add_attempt(paths.sqlite_path, "a_two", answer="P(X > 1/2) = 3/4, so P = 1/4.",
                created_at="2026-10-18T08:02:00+00:00")
    fake.answers.append(merge_as_new_route)
    opened = MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake)
    assert opened.status == "merged" and opened.version == 3 and opened.routes == {"reference": 1, "learner": 1}
    routes = {route["id"]: route for route in json.loads(rows(paths.sqlite_path)[2]["map_json"])["routes"]}
    assert routes["r_learner"]["origin"] == "learner:a_two"
    assert routes["r_learner"]["learner_attempt_ids"] == ["a_two"]
    assert routes["r_ref"]["learner_attempt_ids"] == ["a_one"]
    # The map the serve and the hint read is the newest version.
    assert MB.current_map(vault, _repo(paths), ITEM)["version"] == 3


def test_a_merge_that_misplaces_an_answer_is_reasked_then_not_stored(paths):
    fake = MapFake()
    _build(paths, fake)
    add_attempt(paths.sqlite_path, "a_one", created_at="2026-10-18T08:00:00+00:00")
    unknown = {"matches": [{"attempt_ref": "n9", "route_id": "r_ref"}], "new_routes": []}
    unplaced = {"matches": [], "new_routes": []}
    fake.answers.extend([unknown, unplaced])
    outcome = MB.merge_learner_routes(load_vault(paths.root), _repo(paths), ITEM, client=fake)
    assert outcome.status == "not_stored" and "merge_unplaced_attempt" in outcome.reasons
    assert len(rows(paths.sqlite_path)) == 1
    merges = [row for row in ledger(paths.sqlite_path) if row["right_kind"] == "approach_map_merge"]
    assert [row["verdict"] for row in merges] == ["invalid_reasked", "invalid_not_stored"]
    assert "merge_unknown_attempt" in json.loads(merges[0]["rationale"])["reasons"]


def test_a_merge_needs_a_map(paths):
    add_attempt(paths.sqlite_path, "a_one")
    assert MB.merge_learner_routes(load_vault(paths.root), _repo(paths), ITEM, client=MapFake()).status == "no_map"


# -- the owner's backfill and its dry run (G-H11) ------------------------------------------


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_the_dry_run_prints_the_estimate_and_writes_nothing(paths, monkeypatch):
    from learnloop.cli import app

    def no_client(*args, **kwargs):
        raise AssertionError("a dry run resolves no client")

    def no_retrieval(*args, **kwargs):
        raise AssertionError("a dry run retrieves nothing")

    monkeypatch.setattr(MB, "_route_client", no_client)
    monkeypatch.setattr("learnloop.source_retrieval.find_sources.find_sources_for_caller", no_retrieval)
    write_item(paths, "pi_cdf_b", prompt="Find P(X ≤ 1/3) for f(x) = 2x on [0, 1].", expected="P = 1/9")
    def files() -> dict[str, str]:
        # A WAL reader's -shm index (and an empty -wal) are SQLite's, not writes.
        return {str(path.relative_to(paths.root)): _digest(path) for path in paths.root.rglob("*")
                if path.is_file() and not path.name.endswith(("-wal", "-shm"))}

    before = files()
    result = CliRunner().invoke(app, ["hints", "maps", "build", "--vault", str(paths.root), "--dry-run", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["status"] == "planned" and payload["dry_run"] is True
    assert payload["estimate"]["builds_due"] == payload["selected"] >= 2
    assert payload["estimate"]["cost_basis"] == "estimated_only"
    planned = {entry["practice_item_id"]: entry for entry in payload["items"]}
    assert planned[ITEM]["estimate"]["calls"] == 1 and planned[ITEM]["estimate"]["estimated_tokens"] > 0
    assert planned[ITEM]["estimate"]["worst_case_with_reask"]["calls"] == 2
    assert files() == before
    wal = Path(str(paths.sqlite_path) + "-wal")
    assert not wal.exists() or wal.stat().st_size == 0
    assert not Path(str(paths.sqlite_path) + "-journal").exists()


def test_the_backfill_builds_selected_items_and_skips_current_ones(paths):
    write_item(paths, "pi_cdf_b", prompt="Find P(X ≤ 1/3) for f(x) = 2x on [0, 1].", expected="P = 1/9")
    vault = load_vault(paths.root)
    fake = MapFake([good_map(), good_map(goal_answer="1/9", nodes=[
        node("g", "given", "Read the density", "f(x) = 2x on [0, 1]"),
        node("cdf", "step", "Find the CDF on the support", "$F(x) = x^2$ on [0, 1]"),
        node("goal", "goal", "Evaluate the CDF at the point", "P = 1/9")])])
    result = MB.backfill(vault, _repo(paths), MB.select_items(vault, learning_object_id="lo_svd_definition"),
                         dry_run=False, client=fake)
    # The basic vault's own item is on the same learning object: three builds.
    assert result["counts"] == {"built": 3} and result["status"] == "ok"
    assert result["spend_today"]["estimated_only"]["requests"] == 3
    again = MB.backfill(vault, _repo(paths), MB.select_items(vault, item_id=ITEM), dry_run=False, client=fake)
    assert again["counts"] == {"current": 1} and fake.calls == 3
    limited = MB.backfill(vault, _repo(paths), [vault.practice_items[ITEM]], dry_run=False, client=fake, limit=1)
    assert limited["counts"] == {"current": 1}
    with pytest.raises(ValueError, match="at most one"):
        MB.select_items(vault, item_id=ITEM, family_id="fam")


# -- spend (§7.3; G-H11) ----------------------------------------------------------------


def test_a_metered_route_without_a_price_is_refused_before_sending(paths):
    fake = MapFake(provider_type="openai_chat")
    retrieved: list = []
    outcome = _build(paths, fake, find=lambda *args, **kwargs: retrieved.append(kwargs))
    assert outcome.status == "unpriced" and fake.calls == 0 and rows(paths.sqlite_path) == []
    assert retrieved == [], "nothing is retrieved for a call that cannot be made"


def test_the_daily_cap_holds_on_metered_routes_and_says_so(tmp_path, frozen):
    paths = map_vault(tmp_path, config=METERED + "[hints.maps]\nmax_daily_cost_usd = 0.0\n")
    write_item(paths, "pi_cdf_b", prompt="Find P(X ≤ 1/3) for f(x) = 2x on [0, 1].", expected="P = 1/9")
    fake = MapFake(provider_type="openai_chat")
    vault = load_vault(paths.root)
    retrieved: list = []
    result = MB.backfill(vault, _repo(paths), MB.select_items(vault), dry_run=False, client=fake,
                         find=lambda *args, **kwargs: retrieved.append(kwargs))
    assert result["status"] == "capped" and "max_daily_cost_usd" in result["message"]
    assert fake.calls == 0 and rows(paths.sqlite_path) == [] and retrieved == []
    statuses = {entry["practice_item_id"]: entry["status"] for entry in result["items"]}
    assert set(statuses.values()) == {"capped"}


def test_a_metered_build_under_the_cap_reserves_and_settles_its_spend(tmp_path, frozen):
    paths = map_vault(tmp_path, config=METERED + "[hints.maps]\nmax_daily_cost_usd = 5.0\n")
    fake = MapFake(provider_type="openai_chat")
    outcome = _build(paths, fake)
    assert outcome.status == "built" and outcome.billing == "metered"
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        spend = MB.maps_spend_today(vault, connection)
    assert spend["metered_usd"] > 0 and spend["remaining_usd"] < 5.0 and spend["cap_usd"] == 5.0
    [receipt] = receipts(paths.sqlite_path)
    assert json.loads(receipt["budget_json"])["practice_index"]["cost_basis"] == "metered_estimate"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        states = connection.execute(
            "SELECT envelope, state FROM source_service_spend WHERE envelope = ?", (MB.ENVELOPE,)).fetchall()
    assert states and all(state == "settled" for _envelope, state in states)


def test_codex_is_estimated_only_and_never_capped(tmp_path):
    paths = map_vault(tmp_path, config="[hints.maps]\nmax_daily_cost_usd = 0.0\n")
    outcome = _build(paths, MapFake(provider_type="codex_sdk"))
    assert outcome.status == "built" and outcome.billing == "subscription"


def test_the_route_falls_back_to_the_active_provider_and_an_override_keeps_the_cap(tmp_path, monkeypatch):
    from learnloop.practice_index.paid import plan_route

    paths = map_vault(tmp_path)
    vault = load_vault(paths.root)
    assert plan_route(vault, "approach_map").provider == vault.config.ai.active_provider
    config_path = paths.root / "learnloop.toml"
    config_path.write_text(config_path.read_text(encoding="utf-8").replace(
        "[ai.routing]\n", '[ai.routing]\napproach_map = "codex_low"\n', 1), encoding="utf-8")
    assert plan_route(load_vault(paths.root), "approach_map").provider == "codex_low"
    # LEARNLOOP_AI_PROVIDER moves the route to a metered profile: the cap still applies.
    capped = map_vault(tmp_path, name="capped", config=METERED + "[hints.maps]\nmax_daily_cost_usd = 0.0\n"
                       + '[ai.providers.metered_chat]\ntype = "openrouter"\nmodel = "m"\n'
                       + 'api_key_env = "NO_SUCH_KEY"\n')
    monkeypatch.setenv("LEARNLOOP_AI_PROVIDER", "metered_chat")
    vault = load_vault(capped.root)
    route = plan_route(vault, "approach_map")
    assert route.provider == "metered_chat" and route.billing == "metered"
    fake = MapFake(provider_type="openrouter")
    monkeypatch.setattr(MB, "_route_client", lambda *args: (fake, None))
    outcome = MB.build_map(vault, _repo(capped), ITEM, trigger="cli")
    assert outcome.status == "capped" and fake.calls == 0


# -- the kill switch (G-H1's maps clause) ---------------------------------------------------


def test_the_kill_switch_builds_nothing_and_reads_nothing(paths):
    fake = MapFake()
    _build(paths, fake)
    add_attempt(paths.sqlite_path, "a_one")
    append_config_toml(paths.root, MAPS_OFF)
    vault = load_vault(paths.root)
    assert MB.current_map(vault, _repo(paths), ITEM) is None
    assert MB.build_map(vault, _repo(paths), ITEM, trigger="cli", client=fake).status == "disabled"
    assert MB.build_map_inline(vault, _repo(paths), ITEM, client=fake).status == "disabled"
    assert MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake).status == "disabled"
    assert MB.schedule_build_on_serve(vault, paths.sqlite_path, ITEM, client=fake) is None
    assert MB.backfill(vault, _repo(paths), MB.select_items(vault), dry_run=False, client=fake)["status"] == "disabled"
    assert fake.calls == 1 and len(rows(paths.sqlite_path)) == 1


def _normalized(value) -> str:
    text = json.dumps(value, sort_keys=True, default=str)
    return re.sub(r"\b[0-9A-HJKMNP-TV-Z]{26}\b|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                  "<id>", text)


def _practice_run(root: Path, client) -> list[str]:
    ctx, session_id = _sidecar(root, client)
    served = _serve(ctx, session_id)
    MB.wait_for_background_builds(30)
    submitted = _call(ctx, "submit_attempt", {
        "sessionId": session_id, "practiceItemId": ITEM, "answerMd": "F(x) = x^2, so P(X ≤ 1/2) = 1/4.",
        "attemptType": "independent_attempt", "hintsUsed": 0, "submissionId": "k1",
        "selfGrade": {"criterionPoints": {"cdf": 2, "value": 2}, "confidence": 4}})
    MB.wait_for_background_builds(30)
    return [_normalized(served), _normalized(submitted)]


def test_practice_rpcs_are_byte_identical_with_maps_on_or_off(tmp_path, frozen):
    on = map_vault(tmp_path, name="on", trace_contract=TRACE_CONTRACT)
    off = map_vault(tmp_path, name="off", trace_contract=TRACE_CONTRACT, config=MAPS_OFF)
    fake = MapFake()
    assert _practice_run(on.root, fake) == _practice_run(off.root, MapFake())
    assert fake.calls == 1 and len(rows(on.sqlite_path)) == 1 and rows(off.sqlite_path) == []
    with closing(sqlite3.connect(off.sqlite_path)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM model_call_receipts WHERE owner_kind = 'approach_map'"
                                  ).fetchone()[0] == 0


# -- the soft reference and the report ----------------------------------------------------


def test_help_assists_map_id_is_a_soft_reference_checked_in_code(paths):
    outcome = _build(paths, MapFake())
    with closing(connect(paths.sqlite_path)) as connection:
        assert store.map_exists(connection, outcome.map_id)
        assert not store.map_exists(connection, "am_missing") and not store.map_exists(connection, None)
        fks = connection.execute("PRAGMA foreign_key_list(help_assists)").fetchall()
    assert "approach_maps" not in {row[2] for row in fks}


def test_the_hints_report_shows_maps_failures_routes_and_spend(paths):
    from learnloop.cli import app

    fake = MapFake([_mutate("cycle"), good_map()])
    _build(paths, fake)
    write_item(paths, "pi_cdf_b", prompt="Find P(X ≤ 1/3) for f(x) = 2x on [0, 1].", expected="P = 1/9")
    _build(paths, MapFake([_mutate("foreign_facet"), _mutate("foreign_facet")]), item="pi_cdf_b")
    add_attempt(paths.sqlite_path, "a_one")
    add_attempt(paths.sqlite_path, "a_b", item_id="pi_cdf_b")
    result = CliRunner().invoke(app, ["hints", "report", "--vault", str(paths.root), "--json"])
    assert result.exit_code == 0, result.output
    maps = json.loads(result.output)["maps"]
    assert maps["enabled"] is True and maps["build_on_serve"] is True and maps["max_daily_cost_usd"] == 0.5
    assert maps["versions_stored"] == 1 and maps["current_maps"] == 1
    assert maps["served_items"] == {"basis": "active items with at least one practice attempt", "count": 2,
                                    "with_current_map": 1, "without_map": 1}
    assert maps["validation"]["failures_by_reason"] == {"cycle": 1, "foreign_facet": 2, "goal_mismatch": 2}
    assert maps["validation"]["not_stored"] == {"build": 1}
    assert maps["validation"]["verdicts"] == {"build:invalid_not_stored": 1, "build:invalid_reasked": 2,
                                              "build:valid": 1}
    assert maps["routes_by_origin"] == {"reference": 1}
    assert maps["versions_by_trigger"] == {"cli": 1}
    assert maps["model_calls"]["calls"] == 4
    assert maps["spend_today"]["envelope"] == MB.ENVELOPE
    assert maps["spend_today"]["estimated_only"]["requests"] == 4


# -- Codex review of H1 (job 20261018-023953-U3XWgU) -----------------------------------------

from learnloop.hints import maps as M  # noqa: E402
from tests.approach_map_fakes import child_build, write_default_rubric  # noqa: E402

COUNT_PROMPT = "A drawer holds two pairs of socks. How many socks are in the drawer?"


def _count_map(*, step_state: str, step_label: str, goal_state: str = "There are 4 socks",
               goal_answer: str = "4") -> dict:
    return {
        "nodes": [node("g", "given", "Read the drawer", "two pairs of socks"),
                  node("count", "step", step_label, step_state),
                  node("goal", "goal", "Report the total", goal_state)],
        "edges": [edge("g", "count"), edge("count", "goal")],
        "routes": [{"id": "r_ref", "name": "Count route", "path": ["g", "count", "goal"], "origin": "reference",
                    "learner_attempt_ids": []}],
        "goal_node_id": "goal", "goal_answer": goal_answer,
    }


def _count_context() -> MapContext:
    return MapContext(expected_answer="4", facet_ids=frozenset(), public_text=COUNT_PROMPT)


def test_f1_a_single_digit_answer_marks_its_node_and_fails_a_label_that_states_it():
    """A lone-digit answer, independent of the fractional CDF fake: the span
    check ignores one-character tokens, so the exact key is matched as a
    number of its own."""

    leaking_label = validate_map(ApproachMapV1.model_validate(
        _count_map(step_state="4", step_label="The count is 4")), _count_context())
    assert not leaking_label.valid and "label_leak" in leaking_label.reasons
    marked = validate_map(ApproachMapV1.model_validate(
        _count_map(step_state="4", step_label="Count the socks")), _count_context())
    assert marked.valid, marked.details
    assert {item.id: item.leak for item in marked.normalized.nodes} == {"g": False, "count": True, "goal": True}
    assert "count" in marked.leak_marked_by_code
    # The digit inside another number, a fraction, a decimal, a subscript or a power is not the answer.
    for text in ("14 socks", "3/4 of them", "4.5 pairs", "x_4", "2^4", "four"):
        assert not M.gives_away(text, "4", "4"), text
    for text in ("4", "$x = 4$", "There are 4 socks.", "total: 4"):
        assert M.gives_away(text, "4", "4"), text
    # A multi-digit or fractional key keeps the span check's behaviour.
    assert M.gives_away("so P = 1/4", "1/4", "1/4") and not M.gives_away("so P = 1/4", "1/8", "1/8")


def test_f1_a_single_digit_vault_item_builds_with_its_leaks_marked(tmp_path):
    paths = map_vault(tmp_path, prompt=COUNT_PROMPT, expected="4", trace_contract=None)
    leaky = _count_map(step_state="4", step_label="The count is 4")
    fixed = _count_map(step_state="4", step_label="Count the socks")
    outcome = _build(paths, MapFake([leaky, fixed]))
    assert outcome.status == "built" and outcome.rounds == 2 and outcome.verified_goal is True
    stored = json.loads(rows(paths.sqlite_path)[0]["map_json"])
    assert {item["id"]: item["leak"] for item in stored["nodes"]} == {"g": False, "count": True, "goal": True}
    assert [json.loads(row["rationale"])["reasons"] for row in ledger(paths.sqlite_path)][0] == ["label_leak"]


@pytest.mark.parametrize("goal_answer", ["1/4", ""])
def test_f2_a_goal_state_that_contradicts_the_answer_is_a_mismatch(paths, goal_answer):
    """Only the goal node's state is wrong: a correct declaration does not
    verify it, and an empty one does not let it through unverified."""

    payload = good_map(goal_answer=goal_answer)
    payload["nodes"][2]["state"] = "Therefore P = 3/4"
    result = _validate(paths, payload)
    assert not result.valid and "goal_mismatch" in result.reasons and not result.verified_goal
    assert any(detail.get("basis") == "goal_state" for detail in result.details if detail["reason"] == "goal_mismatch")


def test_f2_the_goal_verifies_from_an_agreeing_state_or_declaration(paths):
    for goal_answer, state in (("", "Therefore P = 1/4"), ("1/4", "P(X ≤ 1/2) = 1/4"),
                               ("1/4", "The probability at the point")):
        payload = good_map(goal_answer=goal_answer)
        payload["nodes"][2]["state"] = state
        result = _validate(paths, payload)
        assert result.valid and result.verified_goal and result.goal_basis == "exact_key", (goal_answer, state)
    # A wrong declaration with an agreeing state is still a mismatch.
    payload = good_map(goal_answer="3/4")
    assert "goal_mismatch" in _validate(paths, payload).reasons


def test_f4_every_seeded_solution_needs_exactly_one_route(paths):
    add_attempt(paths.sqlite_path, "a_one")
    reference_only = good_map()  # no learner_attempt_ids: the seeded solution is on no route
    result = _validate(paths, reference_only)
    assert not result.valid and "unplaced_attempt" in result.reasons
    twice = good_map(routes=[
        {"id": "r_ref", "name": "CDF route", "path": ["g", "cdf", "goal"], "origin": "reference",
         "learner_attempt_ids": ["a1"]},
        {"id": "r_model", "name": "Same", "path": ["g", "cdf", "goal"], "origin": "model",
         "learner_attempt_ids": ["a1"]}])
    assert "unplaced_attempt" in _validate(paths, twice).reasons
    # The builder that omits it is re-asked; the placed answer is stored.
    fake = MapFake([reference_only])  # then the fake's default places every solution
    outcome = _build(paths, fake)
    assert outcome.status == "built" and outcome.rounds == 2
    stored = json.loads(rows(paths.sqlite_path)[0]["map_json"])
    assert stored["routes"][0]["learner_attempt_ids"] == ["a_one"]
    assert MB.new_learner_attempts(load_vault(paths.root), _repo(paths), ITEM) == []


def test_f4_only_a_route_assignment_counts_as_mined():
    """A seeded attempt no route took (a row stored before the rule) is not
    mined: the next merge places it."""

    current = {"seeds": {"attempts": [{"id": "a_seeded"}, {"id": "a_placed"}]},
               "map": {"routes": [{"learner_attempt_ids": ["a_placed"]}]}}
    assert MB._known_attempts(current) == {"a_placed"}


def test_f4_a_seeded_but_unrouted_attempt_is_merged_later(paths):
    fake = MapFake()
    first = _build(paths, fake)
    add_attempt(paths.sqlite_path, "a_one")
    row = rows(paths.sqlite_path)[0]
    # A version whose seeds list a_one but whose routes do not (the shape F4 found accepted).
    with closing(connect(paths.sqlite_path)) as connection:
        seeds = {**json.loads(row["seeds_json"]), "attempts": [{"id": "a_one", "practice_item_id": ITEM,
                                                                "basis": "correct"}]}
        store.insert_map(connection, {**{key: row[key] for key in store.COLUMNS}, "id": "am_legacy", "version": 2,
                                      "seeds_json": json.dumps(seeds), "seeds_hash": "legacy",
                                      "supersedes_id": first.map_id})
        connection.commit()
    vault = load_vault(paths.root)
    assert [attempt.attempt_id for attempt in MB.new_learner_attempts(vault, _repo(paths), ITEM)] == ["a_one"]
    merged = MB.merge_learner_routes(vault, _repo(paths), ITEM, client=fake)
    assert merged.status == "merged" and merged.version == 3
    stored = rows(paths.sqlite_path)[2]
    assert json.loads(stored["map_json"])["routes"][0]["learner_attempt_ids"] == ["a_one"]
    assert [entry["id"] for entry in json.loads(stored["seeds_json"])["attempts"]] == ["a_one"]


def test_f5_an_inherited_rubric_change_is_a_new_revision(tmp_path):
    paths = map_vault(tmp_path, trace_contract=TRACE_CONTRACT, rubric=None)
    write_default_rubric(paths, [{"id": "cdf", "points": 2, "description": "Finds the CDF on the support."},
                                 {"id": "value", "points": 2, "description": "Evaluates the probability."}])
    vault = load_vault(paths.root)
    assert vault.practice_items[ITEM].grading_rubric is None
    fake = MapFake()
    first = _build(paths, fake)
    assert first.status == "built"
    assert [criterion["id"] for criterion in fake.requests[0][1]["rubric"]] == ["cdf", "value"]
    _context_before, seeds_before = _context(paths)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        revision_before = MS.item_revision(vault, connection, vault.practice_items[ITEM])
    # The default rubric changes; the item file does not.
    write_default_rubric(paths, [{"id": "value", "points": 4, "description": "States the probability with its units."}])
    vault = load_vault(paths.root)
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        revision_after = MS.item_revision(vault, connection, vault.practice_items[ITEM])
    _context_after, seeds_after = _context(paths)
    assert revision_before[0] == revision_after[0]  # practice_item_hash cannot see it
    assert revision_before[1] != revision_after[1] and seeds_before.seeds_hash != seeds_after.seeds_hash
    assert seeds_after.structure_hash == revision_after[1]
    assert MB.current_map(vault, _repo(paths), ITEM) is None
    second = _build(paths, fake)
    assert second.status == "built" and second.version == 2 and fake.calls == 2
    assert [criterion["id"] for criterion in fake.requests[1][1]["rubric"]] == ["value"]
    assert rows(paths.sqlite_path)[1]["supersedes_id"] == first.map_id
    assert MB.backfill(vault, _repo(paths), MB.select_items(vault, item_id=ITEM), dry_run=True)["counts"] == {"current": 1}


def _two_processes(monkeypatch, *, claims: bool) -> None:
    """Simulate a second process in this one: each call gets its own
    in-process lock; ``claims=False`` also takes the durable claim away, to
    show the commit's own fence."""

    monkeypatch.setattr(MB, "_item_lock", lambda _path, _item: threading.Lock())
    if not claims:
        from contextlib import contextmanager

        @contextmanager
        def no_claim(_repository, item_id, _until):
            yield MB._Claim(MB.claim_key(item_id), "nobody", 0)

        monkeypatch.setattr(MB, "_claimed", no_claim)
        monkeypatch.setattr(MB, "holds_claim", lambda *_args, **_kwargs: True)


def _gated_merge(paths, gate: threading.Event, results: list) -> tuple[MapFake, threading.Thread]:
    slow = MapFake(gate=gate)
    worker = threading.Thread(target=lambda: results.append(MB.merge_learner_routes(
        load_vault(paths.root), _repo(paths), ITEM, client=slow)))
    worker.start()
    assert slow.started.wait(10)
    return slow, worker


def test_f3_a_stale_merge_never_supersedes_a_newer_map(paths, monkeypatch):
    """Codex's completion order with the claim taken away: A merges a1 from
    v1 and is slow; B merges a1 and a2 from v1 and commits v2; A's commit is
    fenced out (its base is no longer the newest row), so v2 keeps a2."""

    _two_processes(monkeypatch, claims=False)
    first = _build(paths, MapFake())
    add_attempt(paths.sqlite_path, "a1", created_at="2026-10-18T08:00:00+00:00")
    gate, results = threading.Event(), []
    slow, worker = _gated_merge(paths, gate, results)
    add_attempt(paths.sqlite_path, "a2", created_at="2026-10-18T08:01:00+00:00")
    fast = MB.merge_learner_routes(load_vault(paths.root), _repo(paths), ITEM, client=MapFake())
    assert fast.status == "merged" and fast.version == 2
    gate.set()
    worker.join(30)
    assert results[0].status == "stale" and slow.calls == 1
    stored = rows(paths.sqlite_path)
    assert [row["version"] for row in stored] == [1, 2] and stored[1]["supersedes_id"] == first.map_id
    current = MB.current_map(load_vault(paths.root), _repo(paths), ITEM)
    assert current["id"] == fast.map_id
    assert sorted(current["map"]["routes"][0]["learner_attempt_ids"]) == ["a1", "a2"]
    assert MB.merge_learner_routes(load_vault(paths.root), _repo(paths), ITEM, client=MapFake()).status == "up_to_date"


def test_f3_a_slower_initial_build_with_other_seeds_does_not_land_a_second_map(paths, monkeypatch):
    """Two initial builds of one revision with different seeds (so the UNIQUE
    seeds key cannot catch them): the slower one finds the map and stores
    nothing."""

    _two_processes(monkeypatch, claims=False)
    gate, results = threading.Event(), []
    slow = MapFake(gate=gate)
    worker = threading.Thread(target=lambda: results.append(_build(paths, slow)))
    worker.start()
    assert slow.started.wait(10)
    add_attempt(paths.sqlite_path, "a1")
    fast = _build(paths, MapFake())
    assert fast.status == "built"
    gate.set()
    worker.join(30)
    assert results[0].status == "current" and results[0].map_id == fast.map_id
    assert len(rows(paths.sqlite_path)) == 1


def test_f3_the_durable_claim_keeps_a_second_worker_from_paying(paths, monkeypatch):
    """With only the durable claim between them (no shared in-process lock),
    a second worker answers busy instead of paying for the same item, and
    the claim is free again once the first worker ends."""

    _two_processes(monkeypatch, claims=True)
    gate, results = threading.Event(), []
    slow = MapFake(gate=gate)
    worker = threading.Thread(target=lambda: results.append(_build(paths, slow)))
    worker.start()
    assert slow.started.wait(10)
    second = MapFake()
    assert _build(paths, second, trigger="serve").status == "busy" and second.calls == 0
    _build_one = _build(paths, MapFake())  # wait_seconds=0 by default
    assert _build_one.status == "busy"
    gate.set()
    worker.join(30)
    assert results[0].status == "built" and slow.calls == 1
    with closing(connect(paths.sqlite_path, read_only=True)) as connection:
        state = connection.execute("SELECT state FROM judgment_work_claims WHERE claim_key = ?",
                                   (MB.claim_key(ITEM),)).fetchone()[0]
    assert state == "released"
    # A merge takes the same claim.
    add_attempt(paths.sqlite_path, "a1")
    gate2, merges = threading.Event(), []
    _slow_merge, merging = _gated_merge(paths, gate2, merges)
    blocked = MB.merge_learner_routes(load_vault(paths.root), _repo(paths), ITEM, client=MapFake(),
                                      deadline=time.monotonic() + 0.3)
    assert blocked.status == "busy"
    gate2.set()
    merging.join(30)
    assert merges[0].status == "merged"


def test_f3_a_lapsed_claim_of_a_dead_process_is_taken_over_and_fences_its_commit(paths, monkeypatch):
    from learnloop.db.stores.judgment_claims import claim_work

    repository = _repo(paths)
    # A dead process's lease, already lapsed.
    with repository.atomic():
        claim_work(repository.connection(), claim_key=MB.claim_key(ITEM), task=MB.CLAIM_TASK,
                   producer=MB.OWNER_KIND, prompt_version=None, input_hash="", owner="proc_dead:1",
                   now="2026-01-01T00:00:00+00:00", lease_seconds=1)
    fake = MapFake()
    assert _build(paths, fake, trigger="serve").status == "built" and fake.calls == 1
    # A worker whose claim was taken over stores nothing.
    stale = MB._Claim(MB.claim_key(ITEM), "proc_dead:1", 1)
    vault = load_vault(paths.root)
    context, seeds = _context(paths)
    validation = validate_map(ApproachMapV1.model_validate(good_map()), context)
    stored = MB._store(repository, item=vault.practice_items[ITEM], item_hash="other", structure="other",
                       seeds_hash="other", seeds_record={}, validated=validation.normalized,
                       validation=validation, trigger="cli", model=None, prompt_version=MB.PROMPT_VERSION,
                       prompt="p", clock=None, claim=stale)
    assert stored.status == "stale" and len(rows(paths.sqlite_path)) == 1


@pytest.mark.durability
def test_f3_a_second_os_process_never_pays_for_an_item_in_flight(tmp_path):
    """Two OS processes: this one builds with a model still answering; a
    child's serve build answers busy without a call, and a child's CLI build
    waits on the claim, then finds the map and pays nothing."""

    import multiprocessing

    paths = map_vault(tmp_path, trace_contract=TRACE_CONTRACT)
    gate, results = threading.Event(), []
    slow = MapFake(gate=gate)
    worker = threading.Thread(target=lambda: results.append(_build(paths, slow, wait_seconds=None)))
    worker.start()
    assert slow.started.wait(30)
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    children = []
    try:
        ready = context.Event()
        serve = context.Process(target=child_build, args=(str(paths.root), str(paths.sqlite_path), "serve", 0.0,
                                                          ready, queue))
        children.append(serve)
        serve.start()
        assert queue.get(timeout=120) == ("busy", 0)
        serve.join(60)
        assert serve.exitcode == 0
        ready = context.Event()
        cli = context.Process(target=child_build, args=(str(paths.root), str(paths.sqlite_path), "cli", None,
                                                        ready, queue))
        children.append(cli)
        cli.start()
        assert ready.wait(120)
        time.sleep(1.0)  # the child is now polling the claim
        assert cli.is_alive() and queue.empty()
        gate.set()
        worker.join(60)
        assert results[0].status == "built"
        assert queue.get(timeout=120) == ("current", 0)
        cli.join(60)
        assert cli.exitcode == 0
    finally:
        gate.set()
        for child in children:
            if child.is_alive():
                child.kill()
                child.join(10)
    assert len(rows(paths.sqlite_path)) == 1 and len(receipts(paths.sqlite_path)) == 1 and slow.calls == 1
