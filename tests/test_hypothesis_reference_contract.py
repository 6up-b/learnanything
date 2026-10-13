"""Codex sources-build review F13: one hypothesis-reference contract for the
published tool schemas and the adapters, and the named-gap target mapping."""
from __future__ import annotations

import sys
import types

import pytest

from learnloop.instructional.sources import resolve_misconceptions
from learnloop.instructional.tools import run_tool, tool_schemas
from learnloop.instructional.valuation import HypothesisRef, NAMED_GAPS_MODULE, open_hypotheses
from learnloop.source_retrieval.policy import CallerContext
from tests.source_service_fakes import FakeServiceLLM, build_textbook_vault, loaded
from tests.test_discriminating_search import _valuer


@pytest.fixture
def textbook(tmp_path):
    paths, repository, spans = build_textbook_vault(tmp_path / "vault")
    misconception = repository.insert_misconception(
        learning_object_id="lo_matrices", statement="Swapping rows leaves the determinant unchanged",
        target_facet="facet_determinant", severity=0.8)
    return paths, repository, misconception


def _valuation(repository, proposal_id):
    import json

    with repository.connection() as connection:
        row = connection.execute("SELECT valuation_json FROM practice_index_proposals WHERE id=?",
                                 (proposal_id,)).fetchone()
    return json.loads(row[0])


def _published_kinds() -> set[str]:
    schema = next(entry for entry in tool_schemas() if entry["name"] == "find_practice")["input_schema"]
    defs = schema.get("$defs") or schema.get("definitions") or {}
    return set(defs["HypothesisRefArg"]["properties"]["kind"]["enum"])


def test_every_published_kind_parses_under_the_adapters_contract():
    kinds = _published_kinds()
    assert {"facet", "lo", "named_gap", "misconception", "learning_object", "facet_state"} <= kinds
    for kind in kinds:
        HypothesisRef.parse({"kind": kind, "id": "x"})  # never "a hypothesis ref needs kind in ..."


@pytest.mark.parametrize("ref", [{"kind": "facet", "id": "facet_determinant"}, {"kind": "lo", "id": "lo_matrices"},
                                 {"kind": "learning_object", "id": "lo_matrices"},
                                 {"kind": "facet_state", "id": "facet_determinant"}])
def test_schema_valid_references_run_through_the_tool(textbook, ref):
    paths, repository, _misconception = textbook
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = run_tool(vault, repository, "find_practice",
                      {"query": "determinant rows swapped sign", "intent": "discriminate",
                       "learning_object_ids": ["lo_matrices"], "target_hypotheses": [ref]},
                      caller=CallerContext(kind="agent"), clients={"practice_rerank": llm},
                      injections={"valuer": _valuer(llm)})
    valuation = _valuation(repository, result["result_ref"])
    assert valuation["problems"] or valuation["unavailable"]
    if ref["kind"] in ("lo", "learning_object"):
        assert "lo:lo_matrices" in {section["problem"]["key"] for section in valuation["problems"]}


# -- named gaps, through named_gaps_for_card() --------------------------------------------------


def _install_gaps(monkeypatch, repository, events):
    module = types.ModuleType(NAMED_GAPS_MODULE)
    module.named_gaps_for_card = lambda connection, **_kwargs: list(events)
    monkeypatch.setitem(sys.modules, NAMED_GAPS_MODULE, module)
    with repository.connection() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS learner_text_gaps (id TEXT PRIMARY KEY)")
        connection.commit()


def _gap(event_id, target, reversals=()):
    return {"event_id": event_id, "at": "2026-10-12T00:00:00Z", "source": "tutor_question", "kind": "misconception",
            "named": {}, "action": "belief_sighting", "target": target, "chooser": "decider",
            "context_kind": None, "decider_kind": None, "reversals": list(reversals)}


def test_named_gaps_map_to_their_targets_and_reversals_name_nothing(textbook, monkeypatch):
    paths, repository, misconception = textbook
    _install_gaps(monkeypatch, repository, [
        _gap("g_belief", {"kind": "durable", "id": misconception, "subject": "linear-algebra"}),
        _gap("g_prereq", {"kind": "learning_object", "id": "lo_matrices", "subject": "linear-algebra"}),
        _gap("g_reversed", {"kind": "durable", "id": misconception, "subject": "linear-algebra"},
             reversals=["not_this_belief"]),
        _gap("g_candidate", {"kind": "candidate", "id": "mcc_1", "subject": "linear-algebra"}),
        _gap("g_none", None),
    ])
    vault = loaded(paths)
    problems, unavailable = open_hypotheses(vault, repository, refs=[
        {"kind": "named_gap", "id": "g_belief"}, {"kind": "named_gap", "id": "g_reversed"},
        {"kind": "named_gap", "id": "g_candidate"}, {"kind": "named_gap", "id": "g_none"},
        {"kind": "named_gap", "id": "g_unknown"}])
    [problem] = problems
    assert problem.key == "lo:lo_matrices" and f"misconception:{misconception}" in problem.slots
    assert HypothesisRef("misconception", misconception) in problem.refs
    assert problem.context["named_gaps"][0]["ref"]["id"] == "g_belief"
    reasons = {entry["ref"]["id"]: entry["reason"] for entry in unavailable}
    assert reasons == {"g_reversed": "named_gap_reversed", "g_candidate": "unmapped_named_gap",
                       "g_none": "unmapped_named_gap", "g_unknown": "unknown_named_gap"}
    prerequisite, _ = open_hypotheses(vault, repository, refs=[{"kind": "named_gap", "id": "g_prereq"}])
    assert [entry.key for entry in prerequisite] == ["lo:lo_matrices"]
    # Remediation reads the belief a gap names.
    assert [record.id for record in resolve_misconceptions(
        repository, [{"kind": "named_gap", "id": "g_belief"}], item=None)] == [misconception]
    assert resolve_misconceptions(repository, [{"kind": "named_gap", "id": "g_reversed"}], item=None) == []


def test_a_named_gap_runs_through_the_tool_as_what_it_names(textbook, monkeypatch):
    paths, repository, misconception = textbook
    _install_gaps(monkeypatch, repository, [_gap("g_belief", {"kind": "durable", "id": misconception})])
    vault = loaded(paths)
    llm = FakeServiceLLM()
    result = run_tool(vault, repository, "find_practice",
                      {"query": "determinant rows swapped sign", "intent": "discriminate",
                       "target_hypotheses": [{"kind": "named_gap", "id": "g_belief"}]},
                      caller=CallerContext(kind="agent"), clients={"practice_rerank": llm},
                      injections={"valuer": _valuer(llm)})
    [section] = _valuation(repository, result["result_ref"])["problems"]
    assert {"kind": "misconception", "id": misconception} in section["problem"]["refs"]
