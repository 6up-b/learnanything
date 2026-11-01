"""Reader follow-ups (Nov 1), Codex review F1 [High]: cached comparisons omit
the current request's provenance.

``compare_sources`` reuses a stored comparison of the same question over the
same counterparts. RW4d's whole-comparison rule (``comparison_withheld``) read
only the stored row's provenance, so a contributor the REUSING call brought
(an exam-material pin it dropped, the tutor question it was asked for) was
never checked: the cached comparison was shown where the same request, made
fresh, is withheld whole. Now the rule reads the union of the stored
provenance and the current call's (its question, anchor, dropped pins and
unverified sources), and the reuse's dropped pins and unverified sources are
persisted on the stored comparison so later reads (the library's deliveries
and keeps) read them too.

Every regression warms the cache BEFORE the protected contributor appears.
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


def _compare(ctx, pins):
    return call(ctx, "compare_sources", {"query": QUESTION, "pinnedSpanKeys": pins,
                                         "caller": {"kind": "reader", "ref": "ext_text"}})


@pytest.fixture
def library(tmp_path, monkeypatch):
    paths, repository, spans = build_library_vault(tmp_path / "vault")
    _fake_service(monkeypatch)
    return paths, context(paths.root), repository, spans


# -- the direct compare_sources RPC: an exam pin the reusing call dropped --------------------------


def test_f1_a_reused_comparison_with_a_new_exam_pin_is_withheld_whole(library):
    _paths, ctx, repository, _spans = library
    warm = _compare(ctx, PINS)
    assert warm["status"] == "ok" and warm["comparisonId"]
    exam = f"ext_exam:{_exam_span(repository)}"
    with pytest.raises(SidecarError) as caught:
        _compare(ctx, [*PINS, exam])
    assert caught.value.code == "comparison_withheld"
    # The same comparison was reused (no second row, no second paid call), and refused whole.
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 1}


def test_f1_the_reuses_dropped_pin_is_persisted_for_later_reads(library):
    from learnloop.reader import source_objects as SO

    _paths, ctx, repository, _spans = library
    warm = _compare(ctx, PINS)
    vault, _ = ctx.require_vault()
    assert not SO.withheld_comparisons(vault, repository, [(warm["comparisonId"], None)])
    exam = f"ext_exam:{_exam_span(repository)}"
    with pytest.raises(SidecarError):
        _compare(ctx, [*PINS, exam])
    # Every later read of the comparison (the library's deliveries and keeps) reads the reuse's pin.
    assert SO.withheld_comparisons(vault, repository, [(warm["comparisonId"], None)])


def test_f1_a_reuse_with_nothing_new_protected_is_shown_and_writes_nothing(library):
    _paths, ctx, repository, _spans = library
    warm = _compare(ctx, PINS)
    with repository.connection() as connection:
        before = dict(connection.execute("SELECT * FROM source_comparisons").fetchone())
    again = _compare(ctx, PINS)
    assert again["status"] == "ok" and again["comparisonId"] == warm["comparisonId"]
    with repository.connection() as connection:
        assert dict(connection.execute("SELECT * FROM source_comparisons").fetchone()) == before


def test_f1_a_reuses_pin_naming_no_passage_is_not_persisted(library):
    """A pin that names no passage contributed nothing: it is not written onto
    the shared comparison (it would make every later read of it unresolvable)."""

    from learnloop.reader import source_objects as SO

    _paths, ctx, repository, _spans = library
    warm = _compare(ctx, PINS)
    try:
        _compare(ctx, [*PINS, "ext_book:no_such_span"])
    except SidecarError:
        pass  # the current call may refuse (fail closed); the stored comparison must stay readable
    vault, _ = ctx.require_vault()
    assert not SO.withheld_comparisons(vault, repository, [(warm["comparisonId"], None)])


# -- find_sources(intent="compare"): the comparison on its manifest, reused ---------------------------


def test_f1_find_sources_compare_reads_a_reuses_persisted_exam_pin(library, monkeypatch):
    """find_sources(compare) passes no pins. The direct RPC reuses its
    comparison with an exam pin, which is persisted on the shared row; the
    next find_sources(compare) reuses that row and is refused whole."""

    import learnloop.instructional.sources as service

    _paths, ctx, repository, _spans = library
    real = service.find_sources_for_caller
    llm = FakeServiceLLM()
    monkeypatch.setattr(service, "find_sources_for_caller",
                        lambda *a, **k: real(*a, **{**k, "compare_client": llm, "rerank_client": llm}))
    params = {"query": QUESTION, "intent": "compare", "caller": {"kind": "reader", "ref": "ext_text"}}
    shown = call(ctx, "find_sources", params)
    comparison_id = shown["manifest"]["comparisonId"]
    assert comparison_id
    with repository.connection() as connection:
        (counterparts,) = connection.execute("SELECT counterpart_keys_json FROM source_comparisons WHERE id = ?",
                                             (comparison_id,)).fetchone()
    import json

    pins = [f"{e}:{s}" for e, s in json.loads(counterparts)]
    exam = f"ext_exam:{_exam_span(repository)}"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "compare_sources", {"query": QUESTION, "pinnedSpanKeys": [*pins, exam],
                                      "caller": {"kind": "reader", "ref": "ext_text"}})
    assert caught.value.code == "comparison_withheld"
    # The direct call reused find_sources' comparison (one row): its exam pin is on that row now.
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 1}
    with pytest.raises(SidecarError) as again:
        call(ctx, "find_sources", params)
    assert again.value.code == "comparison_withheld"


# -- the tutor's tool run: the current question's protected passage -----------------------------------


def _tutor_flow(tmp_path, monkeypatch):
    import learnloop.instructional.tools as tools
    from tests.reader_tutor_fakes import LookupTutor, reader_ctx

    tutor = LookupTutor(tool_requests=[{"tool": "compare_sources", "query": "determinant sign when rows are swapped",
                                        "reason": "How do your books treat this?", "facet_ids": []}],
                        cite=lambda context: [(context["source_spans"][0]["extraction_id"],
                                               context["source_spans"][0]["span_id"])])
    _paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor)
    verifier = ctx.reader_tutor_rerank_client
    real = tools.run_requested_tool
    llm = FakeServiceLLM()
    monkeypatch.setattr(tools, "run_requested_tool", lambda vault, repo, request_id, **kw: real(
        vault, repo, request_id, **{**kw, "clients": {"source_rerank": verifier, "source_compare": llm}}))
    return ctx, repository, spans


def _ask_at(ctx, extraction_id, span_id):
    answer = call(ctx, "reader.ask", {"extractionId": extraction_id, "spanId": span_id,
                                      "question": "why does the determinant change sign when two rows are swapped?",
                                      "selectionSpanIds": [span_id], "selectionQuote": "the determinant"})
    (request,) = [r for r in answer["toolRequests"] if r["tool"] == "compare_sources"]
    return request


def test_f1_a_cached_tutor_comparison_checks_the_current_questions_passage(tmp_path, monkeypatch):
    ctx, repository, spans = _tutor_flow(tmp_path, monkeypatch)
    # Warm: a question asked in the other book (ext_book) runs the comparison; nothing is protected.
    first = _ask_at(ctx, "ext_book", "s7")
    warm = call(ctx, "run_source_tool", {"toolCallId": first["toolCallId"]})
    comparison_id = warm["result"]["comparisonId"]
    assert comparison_id
    from learnloop.reader import source_objects as SO

    chapter = {("ext_text", span) for span in spans["ch5"]}
    assert not (SO.comparison_passages(repository, comparison_id) & chapter), \
        "the warm comparison must not itself read the chapter held out below"
    # A second question, asked at ext_text's chapter 5 (t3); then that chapter is held out.
    second = _ask_at(ctx, "ext_text", "t3")
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})
    with pytest.raises(SidecarError) as caught:
        call(ctx, "run_source_tool", {"toolCallId": second["toolCallId"]})
    assert caught.value.code == "comparison_withheld"
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM source_comparisons").fetchone()[0] == 1


# -- Codex re-review F1: a direct tutor RPC's reuse persists its question --------------------------


def _question_of(repository, tool_call_id: str) -> str:
    from learnloop.db.stores.source_service import tool_call

    with repository.connection() as connection:
        return str(tool_call(connection, tool_call_id)["caller_ref"])


def test_f1_rereview_a_direct_tutor_reuse_persists_its_question_for_later_readers(tmp_path, monkeypatch):
    """Codex re-review F1: a direct ``compare_sources`` RPC for a tutor question
    reused a stored comparison while its question's passage was readable, and
    no row linked that question to the comparison (only a tool run writes
    one). Once the passage was held out, later readers still got the
    comparison. The reuse now persists the question on the stored comparison,
    so RW4d's rule reads it on every later read."""

    from learnloop.reader import source_objects as SO

    ctx, repository, spans = _tutor_flow(tmp_path, monkeypatch)
    _fake_service(monkeypatch)
    first = _ask_at(ctx, "ext_book", "s7")
    warm = call(ctx, "run_source_tool", {"toolCallId": first["toolCallId"]})
    comparison_id = warm["result"]["comparisonId"]
    chapter = {("ext_text", span) for span in spans["ch5"]}
    assert comparison_id and not (SO.comparison_passages(repository, comparison_id) & chapter)
    # A second question at ext_text's chapter 5, compared through the DIRECT RPC (no tool run): a reuse.
    question = _question_of(repository, _ask_at(ctx, "ext_text", "t3")["toolCallId"])
    shown = call(ctx, "compare_sources", {"query": first["arguments"]["query"],
                                          "caller": {"kind": "tutor", "ref": question}})
    assert shown["comparisonId"] == comparison_id  # reused while the chapter was readable: shown
    assert table_counts(repository, ["source_comparisons"]) == {"source_comparisons": 1}
    save_unit_selection(repository, "ext_text", list(spans), exam_use_modes={"ch5": "held_out_evaluation"})
    vault, _ = ctx.require_vault()
    # A later reader (no question of its own) reads the persisted question: withheld whole.
    assert SO.withheld_comparisons(vault, repository, [(comparison_id, None)])
    with pytest.raises(SidecarError) as caught:
        call(ctx, "run_source_tool", {"toolCallId": first["toolCallId"]})
    assert caught.value.code == "comparison_withheld"


def test_f1_rereview_a_reuse_for_an_unknown_question_is_not_persisted(tmp_path, monkeypatch):
    """A question that does not exist names no passage: it is not written onto
    the shared comparison (every later read of it would be unresolvable)."""

    from learnloop.reader import source_objects as SO
    from learnloop.source_retrieval.compare import compare_sources
    from learnloop.source_retrieval.policy import CallerContext

    ctx, repository, _spans = _tutor_flow(tmp_path, monkeypatch)
    first = _ask_at(ctx, "ext_book", "s7")
    warm = call(ctx, "run_source_tool", {"toolCallId": first["toolCallId"]})
    comparison_id = warm["result"]["comparisonId"]
    vault, _ = ctx.require_vault()
    llm = FakeServiceLLM()
    caller = CallerContext(kind="tutor", ref="qe_no_such_question")
    again = compare_sources(vault, repository, first["arguments"]["query"], caller=caller, client=llm,
                            verify_client=llm)
    assert again.comparison_id == comparison_id and again.reused
    assert not SO.withheld_comparisons(vault, repository, [(comparison_id, None)])
