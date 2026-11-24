"""Exam and held-out material in the split menu's promoted rows and the scratchpads' gutter proposals (spec §9.1,
§10.6; the protection matrix, ``docs/reviews/exam-protection.md``).

The one predicate (``content.sources.exam_material.exam_withheld``, which ``passage.union_range`` and
``passage.content`` read) decides, at read time: a protected passage's words reach no search and no judge, and a
protected passage elsewhere (or its stored quote) reaches no row, reason or proposal, even when it was linked or
proposed before it was marked. Every search and judge here is a spy: no model call.
"""

from __future__ import annotations

import json
import time
from types import SimpleNamespace

import pytest

from learnloop.content.synthesis.source_unit_selection import save_unit_selection
from learnloop.db.repositories import Repository
from learnloop.source_retrieval.search import SpanHit, SpanSearch
from learnloop.source_retrieval.verify import Verification
from tests.desk_helpers import _ledger, seed_reading
from tests.helpers import create_basic_vault
from tests.reading_path_fixtures import call, context
from tests.source_service_fakes import set_config

BOOK, OTHER = "ext_book", "ext_other"
HELD_WORDS = "Exam problem: invert the secret matrix [[2,1],[1,1]]."
OPEN_WORDS = "Kernels are subspaces of the domain."
FAR_QUOTE = "There, applied to a secret example."


def _hit(extraction_id, span_id, source_id="src_other", title="Another book"):
    return SpanHit(extraction_id=extraction_id, span_id=span_id, source_id=source_id, source_title=title, text="t",
                   block_type="Text", section_path=[], page=3, ordinal=1)


@pytest.fixture
def protected(tmp_path, monkeypatch):
    """A book with an open section (s_open, s1, s2) and a section later held out (s_held, s3); another book (o1, o2).
    The cue judge tied s1, s3 and s2 to one misconception (s3 the best other passage) and s_held to another with o1.
    A pad whose note sits under a quote linked to s1. Search, the judge and the coverage judge are spies."""

    from learnloop.ai import model_use
    from learnloop.passage_union import elsewhere as E

    paths = create_basic_vault(tmp_path / "vault")
    set_config(paths, "source_retrieval", enabled=True)
    set_config(paths, "source_service", enabled=True, compare=True)
    set_config(paths, "library_ask", enabled=True)
    set_config(paths, "reader_compare", enabled=True)
    set_config(paths, "teacher", enabled=True)
    repository = Repository(paths.sqlite_path)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id=BOOK,
                 spans=["s_open", "s1", "s2", "s_held", "s3"],
                 texts={"s_open": OPEN_WORDS, "s_held": HELD_WORDS, "s3": "The far passage."},
                 sections=[("u_open", ["s_open", "s1", "s2"]), ("u_held", ["s_held", "s3"])])
    seed_reading(repository, source_id="src_other", revision_id="rev_other", extraction_id=OTHER, spans=["o1", "o2"])
    with repository.connection() as connection:
        for link_id, extraction_id, span, target, rank, relation, quote in (
                ("pl_here", BOOK, "s1", "m_1", 1, "clarifies_distinction", "Here."),
                ("pl_far", BOOK, "s3", "m_1", 2, "new_application", FAR_QUOTE),
                ("pl_worse", BOOK, "s2", "m_1", 3, "try_first", "Elsewhere."),
                ("pl_exam", BOOK, "s_held", "m_2", 1, "clarifies_distinction", "The exam's own words."),
                ("pl_other", OTHER, "o1", "m_2", 2, "new_application", "In the other book.")):
            connection.execute(
                "INSERT INTO passage_links (id, extraction_id, span_id, target_kind, target_id, relation, quote, "
                "pick_rank, ledger_id, state_key, model, prompt_version, created_at) VALUES (?, ?, ?, "
                "'misconception', ?, ?, ?, ?, ?, 'k', 'm', 'p', '2026-05-19T09:00:00Z')",
                (link_id, extraction_id, span, target, relation, quote, rank, _ledger(connection, f"jl_{link_id}")))
        connection.commit()
    spy = SimpleNamespace(queries=[], scopes=[], judged=[], judge_pools=[], hits=[_hit(OTHER, "o1")])

    def search(_vault, _repository, words, scope, **_kwargs):
        spy.queries.append(words)
        spy.scopes.append(scope)
        return SpanSearch(query=words, hits=list(spy.hits))

    def verify(_vault, _repository, *, question, pool, **_kwargs):
        spy.judged.append(question)
        spy.judge_pools.append([hit.key for hit in pool])
        return Verification("verified", picks=list(pool[:1]))

    monkeypatch.setattr(E, "search_spans", search)
    monkeypatch.setattr(E, "verify_spans", verify)
    monkeypatch.setattr(E.SC, "correspondents", lambda *_a, **_k: {"learning_objects": [], "search": None})
    monkeypatch.setattr(model_use, "waiting", lambda _root: False)
    ctx = context(paths.root)
    ctx.post_attempt_worker.autostart = False
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "pad_1", "ops": [
        {"op": "create_pad", "kind": "running"},
        {"op": "insert_block", "blockId": "q1", "kind": "source_quote", "provenance": "source", "positionKey": "a0",
         "bodyMd": "The passage s1."},
        {"op": "link_anchor", "blockId": "q1", "extractionId": BOOK, "spanId": "s1", "expectedAnchorHead": None},
        {"op": "insert_block", "blockId": "n1", "versionId": "v1", "kind": "note", "provenance": "learner",
         "positionKey": "a1", "bodyMd": "so this is where I mix them up", "payload": {"parent_block_id": "q1"}}]})
    yield SimpleNamespace(ctx=ctx, repository=repository, spy=spy, paths=paths)
    ctx.close()


def _hold_out(repository, unit="u_held"):
    save_unit_selection(repository, BOOK, ["u_open", "u_held"], exam_use_modes={unit: "held_out_evaluation"})


def _job(ctx, job_id):
    for _ in range(300):
        state = call(ctx, "passage.promoted_job", {"jobId": job_id})
        if state["done"]:
            return state
        time.sleep(0.02)
    raise AssertionError("the menu's job did not finish")


def _menu(ctx, params):
    reply = call(ctx, "passage.promoted", params)
    return reply, _job(ctx, reply["pendingJob"]["jobId"])


def test_a_menu_on_held_out_material_sends_its_words_to_no_search_and_no_judge(protected):
    _hold_out(protected.repository)
    call(protected.ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "blockId": "h1", "kind": "text", "provenance": "learner", "positionKey": "a2",
         "bodyMd": "my words on inverting the secret matrix"},
        {"op": "link_anchor", "blockId": "h1", "extractionId": BOOK, "spanId": "s_held", "expectedAnchorHead": None}]})
    for params in ({"objectKind": "passage", "extractionId": BOOK, "spanId": "s_held"},
                   {"objectKind": "cue", "extractionId": BOOK, "spanId": "s_held"},
                   {"objectKind": "highlight", "extractionId": BOOK, "spanId": "s3", "annotationId": "ann_1"},
                   # A pad line linked there: its words follow the passage they were written about.
                   {"objectKind": "pad_line", "blockId": "h1"}):
        reply, done = _menu(protected.ctx, params)
        assert (protected.spy.queries, protected.spy.judged, done["status"]) == ([], [], "done"), params
        assert reply["withheld"] is True
        assert (reply["paid"]["searchedByMeaning"], reply["paid"]["verified"]) == (False, False)
    # The guard is per passage: the open passage of the same reading is searched by its own words.
    reply, _done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_open"})
    assert reply["withheld"] is False
    assert protected.spy.queries == [OPEN_WORDS] and protected.spy.judged == [OPEN_WORDS]


def test_search_elsewhere_never_finds_or_judges_protected_material(protected):
    from learnloop.passage_union import elsewhere as E
    from learnloop.vault.loader import load_vault

    _hold_out(protected.repository)
    # Even a search that returned a protected passage: it is never judged and never a finding.
    protected.spy.hits = [_hit(BOOK, "s3", "src_book", "The book"), _hit(OTHER, "o1")]
    found = E.by_search(load_vault(protected.paths.root), protected.repository, "the far passage", deep=True,
                        verify=True, pick_at_most=4)
    [scope] = protected.spy.scopes
    assert not scope.allows(BOOK, "s3") and not scope.allows(BOOK, "s_held") and scope.allows(BOOK, "s1")
    assert protected.spy.judge_pools == [[(OTHER, "o1")]]
    assert [(f.extraction_id, f.span_id) for f in found] == [(OTHER, "o1")]


def test_a_passage_held_out_after_it_was_linked_yields_no_row_and_no_proposal(protected):
    before = call(protected.ctx, "pad.proposals", {"padId": "pad_1"})["proposals"]
    assert [(p["blockId"], p["target"]["target"]["span_id"], p["quote"]) for p in before] == [("n1", "s3", FAR_QUOTE)]
    rows = call(protected.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK,
                                                     "spanId": "s1"})["rows"]
    assert {row["action"]["target"]["spanId"] for row in rows if row["kind"] == "next_step"} == {"s2", "s3"}

    _hold_out(protected.repository)
    after = call(protected.ctx, "pad.proposals", {"padId": "pad_1"})
    # The stored proposal is read again: nothing of the protected passage, its target or its quote, is shown.
    assert after["proposals"] == [] and FAR_QUOTE not in json.dumps(after)
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s1"})
    for rows in (reply["rows"], done["rows"]):
        assert [row["action"]["target"]["spanId"] for row in rows if row["kind"] == "next_step"] == ["s2"]
        assert FAR_QUOTE not in json.dumps(rows)
    # A note committed now gets the next passage that is not protected.
    call(protected.ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "blockId": "n2", "versionId": "v2", "kind": "note", "provenance": "learner",
         "positionKey": "a2", "bodyMd": "and here too", "payload": {"parent_block_id": "q1"}}]})
    shown = call(protected.ctx, "pad.proposals", {"padId": "pad_1"})["proposals"]
    assert [(p["blockId"], p["target"]["target"]["span_id"]) for p in shown] == [("n2", "s2")]


def test_a_held_out_passage_promotes_no_passage_elsewhere(protected):
    reply, _done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_held"})
    assert [row["action"]["target"]["spanId"] for row in reply["rows"] if row["kind"] == "next_step"] == ["o1"]
    _hold_out(protected.repository)
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_held"})
    for rows in (reply["rows"], done["rows"]):
        assert [row for row in rows if row["kind"] in ("next_step", "elsewhere", "correspondent")] == []


def test_a_whole_exam_reading_is_protected_the_same_way(protected):
    save_unit_selection(protected.repository, BOOK, ["u_open", "u_held"], role_override="exam")
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_open"})
    assert reply["withheld"] is True and protected.spy.queries == []
    assert call(protected.ctx, "pad.proposals", {"padId": "pad_1"})["proposals"] == []


def test_selection_verdict_includes_the_neighbor(protected):
    _hold_out(protected.repository)
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK,
                                        "spanId": "s2", "spanIds": ["s2", "s_held"]})
    assert reply["withheld"] and protected.spy.queries == [] and protected.spy.judged == []
    assert all(row["kind"] not in {"elsewhere", "next_step", "correspondent"} for row in done["rows"])


@pytest.mark.parametrize("unit", ["u_open", "u_held"])
def test_finished_menu_rechecks_origin_and_targets_at_each_poll(protected, unit):
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s1"})
    assert FAR_QUOTE in json.dumps(done["rows"])
    _hold_out(protected.repository, unit)
    again = call(protected.ctx, "passage.promoted_job", {"jobId": reply["pendingJob"]["jobId"]})
    assert FAR_QUOTE not in json.dumps(again)
    if unit == "u_open":
        assert again["rows"] == []
    else:
        assert again["rows"] == [row for row in done["rows"] if row["action"].get("target", {}).get("spanId") != "s3"]


@pytest.mark.parametrize("rpc,params", [
    ("carried.carry", {"carriedId": "mixed", "originKind": "selection", "text": HELD_WORDS,
                       "anchor": {"extractionId": BOOK, "spanId": "s2", "spanIds": ["s2", "s_held"]}}),
    ("pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "kind": "source_quote", "provenance": "source", "positionKey": "a2",
         "blockId": "mix", "bodyMd": HELD_WORDS, "payload": {"extraction_id": BOOK, "span_id": "s2"}},
        {"op": "link_anchor", "blockId": "mix", "extractionId": BOOK, "spanId": "s_held", "expectedAnchorHead": None}]}),
    ("pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "kind": "source_piece", "provenance": "source", "positionKey": "a2",
         "blockId": "mix", "bodyMd": HELD_WORDS, "payload": {"extraction_id": BOOK, "span_id": "s_held"}}]}),
    ("reader.capture", {"sourceId": "src_book", "revisionId": "rev_book", "extractionId": BOOK, "action": "annotate",
                        "clientIdempotencyKey": "mixed", "learnerText": "note", "rawSelection": {
                            "nodes": [{"spanId": "s2"}, {"spanId": "s_held", "quote": HELD_WORDS}]}}),
    ("reader.import_exercise", {"extractionId": BOOK, "rawSelection": {"nodes": [{"spanId": "s2"}, {"spanId": "s_held"}]}}),
    ("reader.author_section_question", {"extractionId": BOOK, "sectionId": "u_open", "spanIds": ["s2", "s_held"]}),
    ("figure.request", {"goalText": HELD_WORDS, "anchor": {"extractionId": BOOK, "spanIds": ["s2", "s_held"]}}),
    ("companion.ask", {"requestId": "mixed", "surface": "reader", "extractionId": BOOK, "spanId": "s2",
                       "selectionSpanIds": ["s2", "s_held"], "question": "Why?", "selectionQuote": HELD_WORDS}),
    ("desk.apply", {"clientId": "compare", "seq": 1, "ops": [
        {"op": "open_window", "deskId": "desk", "windowId": "cmp", "content": {"kind": "compare", "query": HELD_WORDS},
         "view": {"compareAnchor": {"extractionId": BOOK, "spanIds": ["s2", "s_held"]}}}]}),
    ("reader.library_compare", {"door": "selection", "question": HELD_WORDS, "extractionId": BOOK,
                                "anchorSpanIds": ["s2", "s_held"]}),
    ("reader.library_ask", {"query": HELD_WORDS, "extractionId": BOOK, "spanIds": ["s2", "s_held"]}),
    ("lesson.turn", {"action": "open", "entry": "reader_selection",
                     "selection": {"extractionId": BOOK, "spanIds": ["s2", "s_held"]}}),
    ("search.everything", {"query": HELD_WORDS, "selection": {"extractionId": BOOK, "spanIds": ["s2", "s_held"]}}),
])
def test_destination_refuses_mixed_selection_without_menu(protected, rpc, params):
    from learnloop_sidecar.errors import SidecarError

    _hold_out(protected.repository)
    with pytest.raises(SidecarError) as refused:
        call(protected.ctx, rpc, params)
    assert refused.value.code == "exam_material"
    assert HELD_WORDS not in json.dumps(call(protected.ctx, "pad.get", {"padId": "pad_1"}))
    assert HELD_WORDS not in json.dumps(call(protected.ctx, "carried.list", {}))


def test_pad_selection_follows_every_lines_payload_and_links(protected):
    from learnloop_sidecar.errors import SidecarError

    ctx = protected.ctx
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "blockId": "piece", "kind": "source_piece", "provenance": "source",
         "positionKey": "a2", "bodyMd": HELD_WORDS, "payload": {"extraction_id": BOOK, "span_id": "s_held"}}]})
    ids = ["n1", "piece"]
    _hold_out(protected.repository)
    menu, done = _menu(ctx, {"objectKind": "pad_line", "blockId": "n1", "blockIds": ids})
    assert menu["withheld"] and done["withheld"] and protected.spy.queries == []
    for rpc, params in [
        ("search.everything", {"query": HELD_WORDS, "blockIds": ids}),
        ("carried.carry", {"carriedId": "from-pad", "originKind": "block", "originRef": "n1",
                           "blockIds": ids, "text": HELD_WORDS}),
        ("companion.ask", {"requestId": "mixed", "surface": "desk", "question": HELD_WORDS,
                           "extractionId": BOOK, "spanId": "s2", "padBlockIds": ids}),
        ("figure.request", {"goalText": HELD_WORDS, "anchor": {"extractionId": BOOK, "spanIds": ["s2"]},
                            "blockIds": ids}),
        ("author_practice_item", {"learningObjectId": "lo", "prompt": HELD_WORDS, "expectedAnswer": "a",
                                  "blockIds": ids}),
        ("lesson.turn", {"action": "open", "entry": "reader_selection",
                         "selection": {"extractionId": BOOK, "spanIds": ["s2"], "blockIds": ids}}),
    ]:
        with pytest.raises(SidecarError) as refused:
            call(ctx, rpc, params)
        assert refused.value.code == "exam_material", rpc


def test_finished_judged_row_loses_a_newly_marked_target(protected):
    reply, done = _menu(protected.ctx, {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_open"})
    assert [row["kind"] for row in done["rows"]] == ["elsewhere"]
    save_unit_selection(protected.repository, OTHER, [], role_override="exam")
    after = call(protected.ctx, "passage.promoted_job", {"jobId": reply["pendingJob"]["jobId"]})
    assert after["rows"] == [] and after["withheld"] is False


def test_carried_words_on_an_open_passage_follow_the_entire_saved_anchor(protected):
    ctx = protected.ctx
    call(ctx, "carried.carry", {"carriedId": "both", "originKind": "selection", "text": HELD_WORDS,
                                "anchor": {"extractionId": BOOK, "spanId": "s_open", "spanIds": ["s_open", "s_held"]}})
    obj = {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_open"}
    reply, done = _menu(ctx, obj)
    assert HELD_WORDS in json.dumps(done["rows"])
    _hold_out(protected.repository)
    assert HELD_WORDS not in json.dumps(call(ctx, "passage.promoted_job", {"jobId": reply["pendingJob"]["jobId"]}))
    assert HELD_WORDS not in json.dumps(_menu(ctx, obj))
    assert HELD_WORDS not in json.dumps(call(ctx, "passage.knows", obj))


def test_unplaced_legacy_pad_quote_needs_new_clearance_after_a_mark(protected):
    from learnloop_sidecar.errors import SidecarError

    ctx = protected.ctx
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "blockId": "old", "kind": "source_quote", "provenance": "source",
         "positionKey": "a2", "bodyMd": HELD_WORDS}]})
    obj = {"objectKind": "pad_line", "blockId": "old"}
    reply, done = _menu(ctx, obj)
    assert not reply["withheld"] and not done["withheld"]
    _hold_out(protected.repository)
    assert call(ctx, "passage.promoted_job", {"jobId": reply["pendingJob"]["jobId"]})["withheld"]
    with pytest.raises(SidecarError) as error:
        call(ctx, "carried.carry", {"carriedId": "from-old", "originKind": "block", "originRef": "old",
                                    "text": HELD_WORDS})
    assert error.value.code == "exam_material"


def test_the_learners_own_unplaced_quote_stays_usable_when_the_vault_has_held_material(protected):
    """An unplaced legacy quote is refused only when its words repeat protected text: one in the learner's own words
    can still be copied into a pad and carried while other material is held out (proportionate protection)."""
    ctx = protected.ctx
    _hold_out(protected.repository)
    own = "my own summary: a kernel is everything the map sends to zero, which I keep forgetting"
    call(ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
        {"op": "insert_block", "blockId": "mine", "kind": "source_quote", "provenance": "source",
         "positionKey": "a2", "bodyMd": own}]})
    carried = call(ctx, "carried.carry", {"carriedId": "from-mine", "originKind": "block", "originRef": "mine",
                                          "text": own})
    assert carried["created"] is True
    reply, done = _menu(ctx, {"objectKind": "pad_line", "blockId": "mine"})
    assert not reply["withheld"] and not done["withheld"]


def test_an_unplaced_quote_that_repeats_held_words_is_still_refused(protected):
    from learnloop_sidecar.errors import SidecarError

    _hold_out(protected.repository)
    with pytest.raises(SidecarError) as error:
        call(protected.ctx, "pad.apply", {"clientId": "c", "seq": 2, "padId": "pad_1", "ops": [
            {"op": "insert_block", "blockId": "copied", "kind": "source_quote", "provenance": "source",
             "positionKey": "a2", "bodyMd": f"as the book says, {HELD_WORDS.lower()} and more"}]})
    assert error.value.code == "exam_material"


def test_the_union_read_withholds_stored_quotes_and_questions_on_a_passage_held_out_since(protected):
    """passage.union_range applies the menu's withholding: a passage link's stored quote on a passage held out after
    it was linked is not returned (its row goes), while the open passage's link stays."""
    ctx = protected.ctx
    union = call(ctx, "passage.union_range", {"extractionId": BOOK, "fromSpanId": "s_open", "toSpanId": "s3"})
    assert FAR_QUOTE in json.dumps(union)
    _hold_out(protected.repository)
    union = call(ctx, "passage.union_range", {"extractionId": BOOK, "fromSpanId": "s_open", "toSpanId": "s3"})
    assert FAR_QUOTE not in json.dumps(union) and "The exam's own words." not in json.dumps(union)
    s1 = next(span for span in union["spans"] if span["spanId"] == "s1")
    assert [link["quote"] for link in s1["passageLinks"]] == ["Here."]
