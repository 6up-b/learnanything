"""Reader follow-ups (Nov 1), item 2: extraction-qualified span keys for the
reading-only Reader RPCs. Closes CA6b's landing open item 1
(``docs/reviews/reader-ca6b-second-pane-intent.md``): "Extraction-qualified span
keys for the reading-only RPCs, where the reading id is the only provenance on
the wire: ``workbench.open`` (problem spans, source exercise), ``reader.ask``,
``set_answer_mode``, ``route_intent``, ``active_question``, both figure
requests, ``reader.library_ask`` and ``enqueue_request``."

Production extractors number every book ``s0``, ``s1``, ...: a span id another
book also has passed the membership check on these RPCs. Each now takes the
passages as ``extraction:span`` keys (``spanKeys``), formed where the passage was
taken, and the one guard (``source_identity.require_identity``) refuses a key
naming another reading (``span_key_reading``) and a bare id sent without its key
(``span_key_missing``), writing nothing. A request whose keys name its own
reading passes the guard; a request with no keys is checked as before.

Two books with the same span ids (``ext_x`` / ``ext_y``: s0, s1, s2; the CA6b
round-6 ``twins``). Every model is a fake; nothing leaves the machine.
"""
from __future__ import annotations

from typing import Any

import pytest

from learnloop.reader import source_identity as SI
from learnloop_sidecar.errors import SidecarError
from tests.reading_path_fixtures import call, context
from tests.reader_source_identity_guard_helpers import MISMATCH, _refused, twins  # noqa: F401 - the fixture

X = {"sourceId": "src_x", "revisionId": "rev_x", "extractionId": "ext_x"}

#: One request per reading-only RPC, naming book x's reading and the passage ``s1``
#: (``{keys}``: where the request's ``spanKeys`` go; ``{spans}``: its bare ids).
REQUESTS: list[tuple[str, Any]] = [
    ("reader.ask", lambda keys: {"extractionId": "ext_x", "spanId": "s1", "question": "Why?",
                                 "selectionSpanIds": ["s1"], "spanKeys": keys}),
    ("reader.set_answer_mode", lambda keys: {"extractionId": "ext_x", "spanId": "s1",
                                             "answerMode": "answer_directly", "spanKeys": keys}),
    ("reader.enqueue_request", lambda keys: {**X, "spanId": "s1", "preset": "explain", "spanKeys": keys,
                                             "clientIdempotencyKey": "q1"}),
    ("reader.route_intent", lambda keys: {"extractionId": "ext_x", "spanIds": ["s1"], "text": "why", "quote": "x",
                                          "spanKeys": keys}),
    ("reader.active_question", lambda keys: {"extractionId": "ext_x", "spanIds": ["s1"], "style": "next_step",
                                             "spanKeys": keys}),
    ("reader.figure_request", lambda keys: {"extractionId": "ext_x", "spanIds": ["s1"], "spanKeys": keys}),
    ("figure.request", lambda keys: {"goalText": "draw it", "origin": "show_me",
                                     "anchor": {"extractionId": "ext_x", "spanIds": ["s1"], "spanKeys": keys}}),
    ("reader.library_ask", lambda keys: {"query": "symmetric", "entry": "where_else_explained",
                                         "extractionId": "ext_x", "spanIds": ["s1"], "spanKeys": keys}),
    ("workbench.open", lambda keys: {"origin": "reader", "entry": "work_through", "stemMd": "Prove it.",
                                     "clientIdempotencyKey": "w1", "extractionId": "ext_x", "spanIds": ["s1"],
                                     "spanKeys": keys}),
    ("workbench.open", lambda keys: {"origin": "reader", "entry": "work_through", "stemMd": "Prove it.",
                                     "clientIdempotencyKey": "w2",
                                     "sourceExercise": {"proposalId": "pp_any", "extractionId": "ext_x",
                                                        "spanIds": ["s1"], "spanKeys": keys}}),
]
IDS = [f"{method}:{index}" for index, (method, _build) in enumerate(REQUESTS)]


def test_ca6b_open1_the_helper_refuses_another_readings_key_and_an_unkeyed_id(twins):
    _paths, repository = twins
    SI.require_reading_span_keys(repository, extraction_id="ext_x", span_keys=["ext_x:s1"], span_ids=["s1"])
    SI.require_reading_span_keys(repository, extraction_id="ext_x", span_keys=None, span_ids=["s1"])  # not sent
    for keys, spans, reason in (
        (["ext_y:s1"], ["s1"], "span_key_reading"),   # book y's s1, which book x also has
        (["ext_x:s0"], ["s1"], "span_key_missing"),   # an id sent without its key
        (["s1"], ["s1"], "span_key"),                 # a key that names no reading
        (["ext_x:s9"], [], "span"),                   # a keyed passage the reading does not have
    ):
        with pytest.raises(SI.SpanExtractionMismatch) as raised:
            SI.require_reading_span_keys(repository, extraction_id="ext_x", span_keys=keys, span_ids=spans)
        assert raised.value.reason == reason and raised.value.code == MISMATCH


@pytest.mark.parametrize(("method", "build"), REQUESTS, ids=IDS)
def test_ca6b_open1_a_colliding_span_id_keyed_to_another_book_is_refused(twins, method, build):
    paths, repository = twins
    error = _refused(context(paths.root), repository, method, build(["ext_y:s1"]))
    assert error.details["reason"] == "span_key_reading"


@pytest.mark.parametrize(("method", "build"), REQUESTS, ids=IDS)
def test_ca6b_open1_a_bare_id_without_its_key_is_refused(twins, method, build):
    paths, repository = twins
    error = _refused(context(paths.root), repository, method, build([]))
    assert error.details["reason"] == "span_key_missing"


@pytest.mark.parametrize(("method", "build"), REQUESTS, ids=IDS)
def test_ca6b_open1_keys_naming_the_requests_own_reading_pass_the_guard(twins, method, build):
    paths, _repository = twins
    for keys in (["ext_x:s1"], None):  # keyed by the app, or a caller that sends no keys (as before)
        params = build(keys)
        try:
            call(context(paths.root), method, params)
        except SidecarError as exc:  # the handler may refuse later for its own reasons, never the guard
            assert exc.code != MISMATCH, (method, keys, exc.message)
