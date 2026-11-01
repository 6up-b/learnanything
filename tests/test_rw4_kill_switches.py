"""RW4a's kill switches (spec_reader_workbench_v1 §7.7, §12; G20).

With ``library_ask.enabled`` off (or the sources service, or RW1a's inquiry):
the prompt contract has no ``libraryAsk`` key and the intent palette has no
library actions (the contract is RW1b's, byte for byte); every RW4a RPC
refuses and writes nothing; T6's library search and the Reader's tutor spans
are unchanged. ``library_ask.expand_graph`` off makes no expansion call;
``reader_compare.enabled`` off removes compare.
"""
from __future__ import annotations

import copy

import pytest

from learnloop.reader import reader_intent as RI
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import ask_rows, build_library_vault, call, context, set_config, table_counts
from tests.source_service_fakes import tool_tutor

QUESTION = "eigenvalues characteristic polynomial determinant"
RPCS = {
    "reader.library_ask": {"query": QUESTION, "extractionId": "ext_text", "spanIds": ["t2"]},
    "reader.library_ask_notes": {"askId": "la_x"},
    "reader.library_compare": {"askId": "la_x", "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]},
    "reader.library_ask_tutor": {"askId": "la_x", "pinnedSpanKeys": ["ext_text:t2"]},
}
OFF = [("library_ask", {"enabled": False}), ("source_service", {"enabled": False}),
       ("reader_inquiry", {"enabled": False})]


@pytest.fixture
def make(tmp_path):
    def build(section: str | None = None, values: dict | None = None):
        root = tmp_path / f"vault_{section or 'on'}_{len(list(tmp_path.iterdir()))}"
        paths, repository, _spans = build_library_vault(root)
        if section:
            set_config(paths, section, **values)
        return paths, context(paths.root)
    return build


def _without_library(contract: dict) -> dict:
    out = copy.deepcopy(contract)
    out.pop("libraryAsk", None)
    # RW4b's exercises live inside the library answer: off with it.
    out.pop("libraryExercises", None)
    # RW4d's keep: the library's keep and perspectives go with the library
    # answer; the tutor's comparison can still be kept.
    if "compareKeep" in out:
        out["compareKeep"] = {**out["compareKeep"], "library": False, "perspectives": False}
    intent = out.get("intent")
    if intent:
        for name in ("palette", "notesPalette"):
            groups = []
            for group in intent[name]:
                # Reader CA3's "how do my other books treat this?" builds on the library answer too.
                actions = [a for a in group["actions"] if a["effect"]["kind"] not in ("library_ask", "compare")]
                if actions:
                    groups.append({**group, "actions": actions})
            intent[name] = groups
    return out


def test_the_switch_restores_rw1bs_contract_byte_for_byte(make):
    _on_paths, on = make()
    contract_on = call(on, "reader.prompt_contract", {})
    # Reader CA3 (reader_compare.scope_enabled, on by default) adds compareScope,
    # and Reader CA4 (reader_compare.by_point, on by default) compareByPoint.
    assert contract_on["libraryAsk"] == {"expandGraph": True, "personalizedDefault": True, "compare": True,
                                         "compareScope": True, "compareByPoint": True}
    groups = {group["group"] for group in contract_on["intent"]["palette"]}
    assert "orient" in groups
    _off_paths, off = make("library_ask", {"enabled": False})
    contract_off = call(off, "reader.prompt_contract", {})
    assert "libraryAsk" not in contract_off
    assert contract_off == _without_library(contract_on)
    # Orient keeps only RW7a's "what matters here?" (its own switch; no library ask).
    assert [a["id"] for g in contract_off["intent"]["palette"] if g["group"] == "orient" for a in g["actions"]] == [
        "what_matters_here"]
    # The notes pane (the learner's own notes) never offered them.
    assert contract_off["intent"]["notesPalette"] == contract_on["intent"]["notesPalette"]


@pytest.mark.parametrize("section,values", OFF)
def test_every_rw4a_rpc_refuses_and_writes_nothing(make, section, values):
    _paths, ctx = make(section, values)
    vault, repository = ctx.require_vault()
    before = table_counts(repository, ["library_asks", "source_exposure_events", "judgment_ledger",
                                       "interaction_events", "question_events"])
    for name, params in RPCS.items():
        with pytest.raises(SidecarError) as caught:
            call(ctx, name, params)
        assert caught.value.code == "library_ask_disabled", name
    assert table_counts(repository, ["library_asks", "source_exposure_events", "judgment_ledger",
                                     "interaction_events", "question_events"]) == before
    assert not {a.id for a in RI.available_actions(RI.Availability.from_config(vault.config))} & {
        "what_do_i_need_first", "where_else_explained", "where_is_this_used"}


def _without_timings(value):
    """Wall times differ run to run; everything else must match."""

    if isinstance(value, dict):
        return {key: _without_timings(item) for key, item in value.items() if key not in ("timingsMs", "timings_ms")}
    if isinstance(value, list):
        return [_without_timings(item) for item in value]
    return value


def test_t6s_library_search_is_unchanged(make):
    _p, on = make()
    _q, off = make("library_ask", {"enabled": False})
    for deep in (False, True):
        params = {"query": QUESTION, "deep": deep}
        assert _without_timings(call(on, "reader.search_sources", params)) == _without_timings(
            call(off, "reader.search_sources", params))


def test_the_readers_tutor_spans_are_unchanged(make, monkeypatch):
    import learnloop_sidecar.handlers.reader as reader_handler

    prompts = {}
    for label, args in (("on", ()), ("off", ("library_ask", {"enabled": False}))):
        _paths, ctx = make(*args)
        tutor = tool_tutor()

        class Ready:
            ready = True

        monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault, t=tutor: ("fake", Ready(), t))
        call(ctx, "reader.ask", {"extractionId": "ext_text", "spanId": "t2", "question": "why is it a root?"})
        prompts[label] = tutor.prompts[0]
    assert prompts["on"] == prompts["off"]


def test_expand_graph_off_makes_no_expansion_call(make):
    _paths, ctx = make("library_ask", {"expand_graph": False})
    assert call(ctx, "reader.prompt_contract", {})["libraryAsk"]["expandGraph"] is False
    result = call(ctx, "reader.library_ask", {**RPCS["reader.library_ask"], "learningObjectIds": ["lo_matrices"]})
    _vault, repository = ctx.require_vault()
    import json

    manifest = json.loads(ask_rows(repository)[0]["manifest_json"])
    assert manifest["expansions"] == [] and manifest["expansions_skipped"] == "library_ask.expand_graph is off"
    assert not any(hit["expansion"] for hit in result["hits"])


def test_reader_compare_off_removes_compare_only(make):
    _paths, ctx = make("reader_compare", {"enabled": False})
    assert call(ctx, "reader.prompt_contract", {})["libraryAsk"]["compare"] is False
    asked = call(ctx, "reader.library_ask", RPCS["reader.library_ask"])
    assert asked["hits"]
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.library_compare", {"askId": asked["askId"], "pinnedSpanKeys": ["ext_text:t2", "ext_book:s2"]})
    assert caught.value.code == "reader_compare_disabled"
