"""Reader follow-ups (Nov 1), item 1: whole-comparison provenance on the S3/S4
surfaces. Closes the RW4d record's queued follow-up "whole-comparison
provenance for ``compare_sources`` and tutor tool runs (RW4a/S3/RW1c
surfaces)" (``docs/reviews/reader-workbench-RW4d.md``, open items).

Before, the direct ``compare_sources`` RPC and the tutor tool run's comparison
view (``instructional/tools.py`` ``_comparison_view``) withheld only the
displayed passages. Now both apply RW4d's rule through its own helper
(``reader.source_objects.withheld_comparisons``): a comparison any of whose
contributing passages (its sources, counterparts, dropped pins, the tutor
question it was asked for) is exam or held out now is refused whole
(``comparison_withheld``). A comparison with nothing protected is unchanged.

Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from contextlib import closing

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.connection import connect
from learnloop_sidecar.errors import SidecarError
from tests.library_ask_fixtures import build_library_vault, call, context, table_counts
from tests.source_service_fakes import FakeServiceLLM

QUESTION = "why does the determinant change sign when two rows are swapped"
PINS = ["ext_book:s6", "ext_text:t3"]


def _fake_service(monkeypatch, llm=None):
    import learnloop.instructional.sources as service

    real = service.propose_comparison
    llm = llm or FakeServiceLLM()
    monkeypatch.setattr(service, "propose_comparison", lambda *a, **k: real(*a, client=llm, verify_client=llm, **k))
    return llm


def _exam_span(repository) -> str:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        (span,) = connection.execute(
            "SELECT span_id FROM source_document_blocks WHERE extraction_id = 'ext_exam' AND text != '' "
            "ORDER BY ordinal LIMIT 1").fetchone()
    return str(span)


def _hold_out_chapter(repository, spans) -> None:
    # ext_text's chapter 5 (t1-t3; the tutor's question passage t3 among them) held out for an exam.
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    _fake_service(monkeypatch)
    return paths, context(paths.root), repository, spans


def _compare(ctx, pins):
    return call(ctx, "compare_sources", {"query": QUESTION, "pinnedSpanKeys": pins,
                                         "caller": {"kind": "reader", "ref": "ext_text"}})


# -- the direct compare_sources RPC ---------------------------------------------------------------


def test_rw4d_followup_the_direct_rpc_refuses_a_comparison_whose_dropped_pin_is_exam_material(library):
    _paths, ctx, repository, _spans = library
    exam = f"ext_exam:{_exam_span(repository)}"
    with pytest.raises(SidecarError) as caught:
        _compare(ctx, [*PINS, exam])
    assert caught.value.code == "comparison_withheld"
    # The comparison was made (and paid for) and stays in the ledger; nothing of it went out.
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 1}
    assert exam.split(":", 1)[1] not in str(caught.value.__dict__)


def test_rw4d_followup_the_direct_rpc_refuses_a_comparison_pinning_held_out_material(library):
    _paths, ctx, repository, spans = library
    _hold_out_chapter(repository, spans)
    with pytest.raises(SidecarError) as caught:
        _compare(ctx, PINS)
    assert caught.value.code == "comparison_withheld"


def test_rw4d_followup_the_direct_rpc_is_unchanged_with_nothing_protected(library):
    _paths, ctx, _repository, _spans = library
    response = _compare(ctx, PINS)
    assert response["status"] == "ok" and response["comparisonId"] and len(response["sources"]) >= 2
    assert "ext_text:t3" in {f"{s['extractionId']}:{s['spanId']}" for s in response["sources"]}


def test_rw4d_followup_the_rule_fails_closed_on_the_direct_rpc(library, monkeypatch):
    from learnloop.reader import source_objects as SO

    _paths, ctx, _repository, _spans = library

    def unresolvable(*_args, **_kwargs):
        raise LookupError("provenance unreadable")

    # RW4d's helper itself: a comparison whose provenance cannot be read is withheld.
    monkeypatch.setattr(SO, "comparison_passages", unresolvable)
    with pytest.raises(SidecarError) as caught:
        _compare(ctx, PINS)
    assert caught.value.code == "comparison_withheld"


# -- the tutor's tool run ---------------------------------------------------------------------------


def _tutor(tmp_path, monkeypatch):
    import learnloop.instructional.tools as tools
    from tests.reader_tutor_fakes import LookupTutor, ask, reader_ctx

    tutor = LookupTutor(tool_requests=[{"tool": "compare_sources", "query": "determinant sign when rows are swapped",
                                        "reason": "How do your books treat this?", "facet_ids": []}],
                        cite=lambda context: [("ext_text", "t3")])
    _paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor)
    verifier = ctx.reader_tutor_rerank_client
    real = tools.run_requested_tool
    monkeypatch.setattr(tools, "run_requested_tool", lambda vault, repo, request_id, **kw: real(
        vault, repo, request_id, **{**kw, "clients": {"source_rerank": verifier, "source_compare": FakeServiceLLM()}}))
    answer = ask(ctx)
    (request,) = [r for r in answer["toolRequests"] if r["tool"] == "compare_sources"]
    return ctx, repository, spans, request


def test_rw4d_followup_a_tutor_run_whose_question_passage_is_held_out_is_refused_whole(tmp_path, monkeypatch):
    ctx, repository, spans, request = _tutor(tmp_path, monkeypatch)
    # Held out between the answer and the press: the tutor question the comparison is for
    # (ext_text:t3) contributes to it, so the whole comparison is withheld, even though its
    # other book's passages are each readable.
    _hold_out_chapter(repository, spans)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    assert caught.value.code == "comparison_withheld"
    with repository.connection() as connection:
        run = connection.execute("SELECT status, result_keys_json, cost_json FROM source_tool_calls "
                                 "WHERE row_kind = 'run'").fetchone()
    # The run is recorded failed with the refusal's code, naming no passage.
    assert run["status"] == "failed" and "comparison_withheld" in run["cost_json"]
    assert run["result_keys_json"] in (None, "[]")


def test_rw4d_followup_a_tutor_run_with_nothing_protected_is_unchanged(tmp_path, monkeypatch):
    ctx, _repository, _spans, request = _tutor(tmp_path, monkeypatch)
    pressed = call(ctx, "run_source_tool", {"toolCallId": request["toolCallId"]})
    assert pressed["result"]["comparisonId"] and len(pressed["result"]["sources"]) >= 2


# -- find_sources(intent="compare"): the comparison rides on its manifest -----------------------------


def test_rw4d_followup_find_sources_compare_intent_applies_the_rule(library, monkeypatch):
    from learnloop.reader import source_objects as SO

    _paths, ctx, _repository, _spans = library
    params = {"query": QUESTION, "intent": "compare", "caller": {"kind": "reader", "ref": "ext_text"}}
    import learnloop.instructional.sources as service

    real = service.find_sources_for_caller
    llm = FakeServiceLLM()
    monkeypatch.setattr(service, "find_sources_for_caller",
                        lambda *a, **k: real(*a, **{**k, "compare_client": llm, "rerank_client": llm}))
    shown = call(ctx, "find_sources", params)
    assert shown["manifest"]["delegatedTo"] == "compare_sources" and shown["manifest"]["comparisonId"]

    def unresolvable(*_args, **_kwargs):
        raise LookupError("provenance unreadable")

    monkeypatch.setattr(SO, "comparison_passages", unresolvable)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "find_sources", params)
    assert caught.value.code == "comparison_withheld"


def test_rw4d_followup_an_agent_callers_comparison_is_not_withheld_as_unresolvable(tmp_path):
    """Gate finding: RW4d's helper read every non-tutor caller's ref as a reading,
    so an agent's ("cli") comparison was "unresolvable" and refused whole. Only a
    Reader caller's ref is a reading; any other names no passage."""

    from learnloop.instructional.policy import caller_for
    from learnloop.instructional.tools import run_tool
    from learnloop.reader import source_objects as SO
    from tests.source_service_fakes import build_textbook_vault, loaded

    paths, repository, _spans = build_textbook_vault(tmp_path / "vault")
    vault = loaded(paths)
    llm = FakeServiceLLM()
    agent = caller_for(repository, "agent", "cli")
    out = run_tool(vault, repository, "compare_sources", {"query": "what happens to a determinant when rows are swapped"},
                   caller=agent, clients={"source_rerank": llm, "source_compare": llm})
    assert out["result"]["comparison_id"] and out["result"]["sources"]
    assert not SO.withheld_comparisons(vault, repository, [(out["result"]["comparison_id"], None)])
