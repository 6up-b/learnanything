"""Reader CA6b fix round 5 (structural): the passage-identity guard.

Every persisting RPC that names passages (span ids, a raw selection's nodes, a
region, a preset's subject, an exchange, library pins) together with a reading
(and often its source and revision) refuses, with the typed error
``span_extraction_mismatch``, when the passages are not that reading's, and
writes nothing. A request whose passages are the reading's own is unchanged.

Two books with disjoint span ids: ``ext_a`` (src_a / rev_a: a0, a1, a2) and
``ext_b`` (src_b / rev_b: b0, b1). Every model is a fake; nothing leaves the
machine.
"""
from __future__ import annotations

from typing import Any

import pytest

from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.ingest.ir import DocumentBlock, DocumentIR, DocumentUnit, ExtractionHealth
from learnloop.reader import reader_dialogue as RD
from learnloop.reader import source_identity as SI
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from tests.helpers import NOW, append_config_toml, create_basic_vault
from tests.reading_path_fixtures import call, context, table_counts
from tests.test_source_inventory import _persist, _register_revision

MISMATCH = "span_extraction_mismatch"
_CLOCK = FrozenClock(NOW)

#: Every switch the guarded handlers sit behind (the guard runs right after them).
_SWITCHES = """
[tutor_qa]
reader_enabled = true
[reader_inquiry]
enabled = true
[reader_intent]
enabled = true
[reader_active_reading]
enabled = true
[workbench]
enabled = true
[figures]
enabled = true
show_me_enabled = true
offers_enabled = true
[library_ask]
enabled = true
[source_service]
enabled = true
[reader_compare]
enabled = true
"""


def _ir(prefix: str, count: int) -> DocumentIR:
    spans = [f"{prefix}{index}" for index in range(count)]
    blocks = [
        DocumentBlock.build(span_id=span, block_type="Text", text=f"Passage {span} about symmetric matrices.",
                            ordinal=index, page=1, bbox=[10.0, 10.0 + 40 * index, 200.0, 40.0 + 40 * index],
                            section_path=["Ch1"])
        for index, span in enumerate(spans)
    ]
    unit = DocumentUnit(unit_id=f"u_{prefix}", label=f"Section {prefix}", ordinal=0, semantic_hash=f"sha256:{prefix}",
                        page_start=1, page_end=1, span_ids=spans)
    return DocumentIR(extractor="marker", extractor_version="1", units=[unit], blocks=blocks, assets=[],
                      health=ExtractionHealth())


@pytest.fixture
def books(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    append_config_toml(paths.root, _SWITCHES)
    repository = Repository(paths.sqlite_path)
    _register_revision(repository, source_id="src_a", revision_id="rev_a")
    _persist(repository, _ir("a", 3), revision_id="rev_a", extraction_id="ext_a")
    _register_revision(repository, source_id="src_b", revision_id="rev_b")
    _persist(repository, _ir("b", 2), revision_id="rev_b", extraction_id="ext_b")
    return paths, repository


def _refused(ctx, repository, method: str, params: dict[str, Any]) -> SidecarError:
    """The call is refused with the typed mismatch, and nothing is written."""

    before = table_counts(repository)
    with pytest.raises(SidecarError) as raised:
        call(ctx, method, params)
    assert raised.value.code == MISMATCH, (method, raised.value.code, raised.value.message)
    assert table_counts(repository) == before, method
    return raised.value


def _exchange(paths, repository, extraction_id: str, span_id: str) -> str:
    """One Reader exchange asked in ``extraction_id`` (the stub tutor)."""

    vault = load_vault(paths.root)
    result = RD.ask(vault, repository, RD.StubReaderClient(), extraction_id=extraction_id, span_id=span_id,
                    question_md="Why?", clock=_CLOCK)
    return str(result["reader_answer_event_id"] if "reader_answer_event_id" in result else result["event_id"])


B_NODE = {"nodes": [{"spanId": "b0", "quote": "Passage b0"}]}


# -- the helper ---------------------------------------------------------------------------------------


def test_the_helper_passes_a_readings_own_passages_and_refuses_anothers(books):
    _paths, repository = books
    SI.require_source_identity(repository, extraction_id="ext_a", span_ids=["a0", "a2"], source_id="src_a",
                               revision_id="rev_a")
    SI.require_source_identity(repository, extraction_id="ext_a")  # names no passage: nothing to check
    for kwargs, reason in (
        ({"span_ids": ["a0", "b1"]}, "span"),
        ({"span_ids": ["a0"], "source_id": "src_b"}, "source"),
        ({"span_ids": ["a0"], "revision_id": "rev_b"}, "revision"),
    ):
        with pytest.raises(SI.SpanExtractionMismatch) as raised:
            SI.require_source_identity(repository, extraction_id="ext_a", **kwargs)
        assert raised.value.reason == reason
        assert raised.value.code == MISMATCH
    with pytest.raises(SI.SpanExtractionMismatch) as raised:
        SI.require_source_identity(repository, extraction_id="ext_missing", span_ids=["a0"])
    assert raised.value.reason == "unknown_extraction"
    SI.require_span_keys(repository, ["ext_a:a1", "ext_b:b0"])
    with pytest.raises(SI.SpanExtractionMismatch):
        SI.require_span_keys(repository, ["ext_a:a1", "ext_b:a2"])
    assert SI.selection_span_ids({"nodes": [{"spanId": "a0"}, {"span_id": "a1"}, {"displayNodeId": "n"}],
                                  "region": {"spanId": "a2"}}) == ["a0", "a1", "a2"]
    with pytest.raises(SI.SpanExtractionMismatch):
        SI.subject_span_id("span:ext_b/b0", "ext_a")


# -- each guarded RPC refuses another reading's passages and writes nothing -----------------------------


def test_capture_and_create_annotation(books):
    paths, repository = books
    ctx = context(paths.root)
    base = {"sourceId": "src_a", "revisionId": "rev_a", "extractionId": "ext_a", "clientIdempotencyKey": "k1"}
    _refused(ctx, repository, "reader.capture", {**base, "action": "highlight", "rawSelection": B_NODE})
    # The reading named is not the source's (the passages are the reading's own).
    _refused(ctx, repository, "reader.capture", {**base, "sourceId": "src_b", "action": "highlight",
                                                  "rawSelection": {"nodes": [{"spanId": "a0", "quote": "Passage a0"}]}})
    _refused(ctx, repository, "reader.create_annotation", {
        "sourceId": "src_a", "revisionId": "rev_a", "extractionId": "ext_a", "annotationType": "highlight",
        "rawSelection": B_NODE,
    })


def test_capture_of_the_readings_own_passage_is_unchanged(books):
    paths, repository = books
    receipt = call(context(paths.root), "reader.capture", {
        "sourceId": "src_a", "revisionId": "rev_a", "extractionId": "ext_a", "clientIdempotencyKey": "k_ok",
        "action": "highlight", "rawSelection": {"nodes": [{"spanId": "a1", "quote": "Passage a1"}]},
    })
    assert receipt["annotation_id"] if "annotation_id" in receipt else receipt["annotationId"]


def test_invoke_preset_commitments_and_requests(books):
    paths, repository = books
    ctx = context(paths.root)
    base = {"sourceId": "src_a", "revisionId": "rev_a", "extractionId": "ext_a", "clientIdempotencyKey": "k2"}
    # "revisit once" / "make it something I can do" from an inquiry: the commitment's passage.
    for preset in ("test_me_later", "help_me_remember"):
        _refused(ctx, repository, "reader.invoke_preset", {**base, "preset": preset, "rawSelection": B_NODE})
        _refused(ctx, repository, "reader.invoke_preset", {
            **base, "preset": preset, "rawSelection": {"nodes": [{"spanId": "a0", "quote": "Passage a0"}]},
            "subjectId": "b1",
        })
    _refused(ctx, repository, "reader.enqueue_request", {**base, "spanId": "b0", "preset": "explain"})


def test_import_exercise(books):
    paths, repository = books
    _refused(context(paths.root), repository, "reader.import_exercise", {
        "extractionId": "ext_a", "sourceId": "src_a", "revisionId": "rev_a", "rawSelection": B_NODE,
    })
    _refused(context(paths.root), repository, "reader.import_exercise", {
        "extractionId": "ext_a", "sourceId": "src_b", "rawSelection": {"nodes": [{"spanId": "a0", "quote": "x"}]},
    })


def test_manual_anchor(books):
    paths, repository = books
    _refused(context(paths.root), repository, "reader.manual_anchor", {
        "annotationId": "ann_any", "extractionId": "ext_a", "rawSelection": B_NODE,
    })


def test_ask_and_answer_mode(books):
    paths, repository = books
    ctx = context(paths.root)
    _refused(ctx, repository, "reader.ask", {"extractionId": "ext_a", "spanId": "b0", "question": "Why?"})
    _refused(ctx, repository, "reader.ask", {"extractionId": "ext_a", "spanId": "a0", "question": "Why?",
                                              "selectionSpanIds": ["a0", "b1"]})
    other = _exchange(paths, repository, "ext_b", "b0")
    _refused(ctx, repository, "reader.ask", {"extractionId": "ext_a", "spanId": "a0", "question": "And?",
                                              "parentExchangeId": other})
    _refused(ctx, repository, "reader.set_answer_mode", {"extractionId": "ext_a", "spanId": "b0",
                                                          "answerMode": "answer_directly"})


def test_inquiry_status_reconnect_and_quick_check(books):
    paths, repository = books
    ctx = context(paths.root)
    other = _exchange(paths, repository, "ext_b", "b0")
    _refused(ctx, repository, "reader.set_inquiry_status", {"extractionId": "ext_a", "exchangeId": other,
                                                             "resolution": "resolved"})
    for answer in ("yes", "quick_check"):
        _refused(ctx, repository, "reader.reconnect_answer", {"extractionId": "ext_a", "exchangeId": other,
                                                               "answer": answer})
    _refused(ctx, repository, "reader.inquiry_question", {"extractionId": "ext_a", "exchangeId": other})
    # Named with its own reading, the same exchange's status is set as before.
    result = call(ctx, "reader.set_inquiry_status", {"extractionId": "ext_b", "exchangeId": other,
                                                      "resolution": "resolved"})
    assert result["resolution"] == "resolved"


def test_route_intent_and_active_question(books):
    paths, repository = books
    ctx = context(paths.root)
    _refused(ctx, repository, "reader.route_intent", {"extractionId": "ext_a", "spanIds": ["a0", "b0"],
                                                       "text": "why", "quote": "x"})
    _refused(ctx, repository, "reader.active_question", {"extractionId": "ext_a", "spanIds": ["b0"],
                                                          "style": "next_step"})


def test_workbench_open(books):
    paths, repository = books
    ctx = context(paths.root)
    base = {"origin": "reader", "entry": "work_through", "stemMd": "Prove it.", "clientIdempotencyKey": "w1"}
    # The problem's passages are another reading's (finding 2: B's reading with A's passage ids).
    _refused(ctx, repository, "workbench.open", {**base, "extractionId": "ext_a", "spanIds": ["b0"],
                                                  "importRequest": {"extractionId": "ext_a", "sourceId": "src_a",
                                                                    "revisionId": "rev_a", "rawSelection": B_NODE}})
    # The import is a selection of another reading than the problem's.
    _refused(ctx, repository, "workbench.open", {**base, "extractionId": "ext_a", "spanIds": ["a0"],
                                                  "importRequest": {"extractionId": "ext_b", "sourceId": "src_b",
                                                                    "revisionId": "rev_b", "rawSelection": B_NODE}})
    # The import names a source its reading is not of.
    _refused(ctx, repository, "workbench.open", {**base, "extractionId": "ext_a", "spanIds": ["a0"],
                                                  "importRequest": {"extractionId": "ext_a", "sourceId": "src_b",
                                                                    "rawSelection": {"nodes": [{"spanId": "a0"}]}}})
    # A check (an item) at another reading's passage.
    _refused(ctx, repository, "workbench.open", {**base, "entry": "check_me", "practiceItemId": "pi_any",
                                                  "extractionId": "ext_a", "spanIds": ["b1"]})


def test_figure_requests(books):
    paths, repository = books
    ctx = context(paths.root)
    _refused(ctx, repository, "reader.figure_request", {"extractionId": "ext_a", "spanIds": ["b0"]})
    _refused(ctx, repository, "reader.figure_request", {"extractionId": "ext_a", "spanIds": [],
                                                         "region": {"spanId": "b1", "bbox": [0, 0, 1, 1]}})
    _refused(ctx, repository, "figure.request", {"goalText": "draw it", "origin": "show_me",
                                                  "anchor": {"extractionId": "ext_a", "spanIds": ["b0"]}})
    _refused(ctx, repository, "figure.request", {"goalText": "draw it", "origin": "show_me",
                                                  "readingAt": {"extractionId": "ext_a", "spanId": "b0"}})


def test_library_ask_compare_and_tutor_pins(books):
    paths, repository = books
    ctx = context(paths.root)
    _refused(ctx, repository, "reader.library_ask", {"query": "symmetric", "entry": "where_else_explained",
                                                      "extractionId": "ext_a", "spanIds": ["b0"]})
    # An anchored door: another reading's passage, or a leading source the reading is not of.
    _refused(ctx, repository, "reader.library_compare", {"door": "selection", "question": "how?",
                                                          "extractionId": "ext_a", "anchorSpanIds": ["b0"],
                                                          "openSourceId": "src_a"})
    _refused(ctx, repository, "reader.library_compare", {"door": "selection", "question": "how?",
                                                          "extractionId": "ext_a", "anchorSpanIds": ["a0"],
                                                          "openSourceId": "src_b"})
    # A pin whose key names a reading its passage is not in.
    _refused(ctx, repository, "reader.library_compare", {"askId": "la_any", "pinnedSpanKeys": ["ext_a:a0", "ext_a:b1"]})
    _refused(ctx, repository, "reader.library_ask_tutor", {"askId": "la_any", "pinnedSpanKeys": ["ext_b:a1"],
                                                            "question": "why?"})
