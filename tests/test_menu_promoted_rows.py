"""The split menu's promoted rows (spec §9.1, §0 item 7; RD5's acceptance "promoted rows differ by passage").

Cheap rows come at once from the union read of the object's passages; judged rows (correspondents, search) come
through a polled, cancellable job whose finders here are fakes. The order is the orchestrator's default (option A):
the learner's history most recent first, then the rest by their own judge's rank, checked before unchecked, one row of
each kind before a second, ties by row id, dismissed or "not this" rows left out, at most four.
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import pytest

from learnloop.db.repositories import Repository
from learnloop.passage_union import promoted as P
from learnloop.substrate.passage_spans import project_gap, project_question_event
from learnloop.vault.loader import load_vault
from tests.desk_helpers import (
    Batches,
    T0,
    seed_authored_question,
    seed_gap,
    seed_reader_exchange,
    seed_reading,
)
from tests.helpers import create_basic_vault
from tests.reading_path_fixtures import call, context

BOOK = "ext_book"
SPANS = ["s_exchange", "s_gap", "s_check", "s_pad", "s_carried", "s_nothing"]


@pytest.fixture
def menu(tmp_path, monkeypatch):
    """A reading whose six passages know different things, a sidecar on it, and the judged finders as fakes that
    find nothing (each test that wants judged rows sets them)."""

    from learnloop.passage_union import elsewhere as E

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository(paths.sqlite_path)
    vault = load_vault(paths.root)
    seed_reading(repository, source_id="src_book", revision_id="rev_book", extraction_id=BOOK, spans=SPANS)
    with repository.connection() as connection:
        seed_reader_exchange(connection, question_event_id="qe_1", extraction_id=BOOK, anchor="s_exchange",
                             created_at="2026-05-19T10:00:00Z")
        seed_authored_question(connection, question_id="raq_1", extraction_id=BOOK, spans=["s_gap"])
        seed_gap(connection, gap_id="g_1", source_kind="reader_formative", source_id="raq_1", kind="misconception")
        project_question_event(connection, vault, "qe_1")
        project_gap(connection, vault, "g_1")
        connection.commit()
    Batches(repository).pad("p1", {"op": "create_pad", "kind": "named"},
                            {"op": "insert_block", "block_id": "b1", "kind": "text", "provenance": "learner",
                             "position_key": "a0", "body_md": "why does this hold?"},
                            {"op": "link_anchor", "block_id": "b1", "extraction_id": BOOK, "span_id": "s_pad",
                             "expected_anchor_head": None})
    ctx = context(paths.root)
    ctx.post_attempt_worker.autostart = False
    call(ctx, "carried.carry", {"carriedId": "cq_1", "text": "is this always true?", "originKind": "selection",
                                "anchor": {"extractionId": BOOK, "spanId": "s_carried"}})
    finders = SimpleNamespace(correspondents=[], search=[])
    monkeypatch.setattr(E.SC, "correspondents", lambda *_a, **_k: {"learning_objects": [], "search": None})
    monkeypatch.setattr(E, "by_search", lambda *_a, **_k: list(finders.search))
    yield SimpleNamespace(ctx=ctx, repository=repository, vault=vault, finders=finders, paths=paths)
    ctx.close()


def _rows(reply):
    return [(row["kind"], row["label"]) for row in reply["rows"]]


def _job(ctx, job_id):
    for _ in range(200):
        state = call(ctx, "passage.promoted_job", {"jobId": job_id})
        if state["done"]:
            return state
        time.sleep(0.02)
    raise AssertionError("the menu's job did not finish")


@pytest.mark.parametrize(("span", "kinds"), [
    ("s_exchange", ["question"]),
    ("s_gap", ["gap"]),
    ("s_pad", ["your_words"]),
    ("s_carried", ["carried"]),
    # A passage with a due check, or with nothing, promotes nothing: a check must show nothing before it opens.
    ("s_check", []),
    ("s_nothing", []),
])
def test_promoted_rows_differ_by_passage(menu, span, kinds):
    reply = call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK, "spanId": span})
    assert reply["version"] == 1 and reply["cap"] == 4
    assert [row["kind"] for row in reply["rows"]] == kinds
    for row in reply["rows"]:
        assert row["reason"] and row["action"]["verb"] and row["rowId"].startswith("pr_")
    assert _job(menu.ctx, reply["pendingJob"]["jobId"])["status"] == "done"


def test_each_row_says_why_and_opens_what_it_names(menu):
    by_span = {span: call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK,
                                                          "spanId": span})["rows"]
               for span in ("s_exchange", "s_pad", "s_carried")}
    [question] = by_span["s_exchange"]
    assert question["reason"] == "you asked the tutor about this on 2026-05-19"
    assert question["action"] == {"verb": "open", "ref": {"kind": "thread", "rootExchangeId": "qe_1"}}
    [words] = by_span["s_pad"]
    assert words["action"] == {"verb": "open", "ref": {"kind": "pad", "padId": "p1"}, "target": {"blockId": "b1"}}
    [carried] = by_span["s_carried"]
    assert carried["label"] == "you carried: is this always true?" and carried["action"]["carriedId"] == "cq_1"


def test_a_due_check_is_never_a_row():
    entry = {"checks_due": [{"commitment_id": "c1"}]}
    assert P.cheap_rows("passage:e:s", [("e", "s", entry)]) == []


def test_judged_rows_arrive_through_the_job_checked_before_unchecked(menu):
    from learnloop.passage_union.elsewhere import Finding

    menu.finders.search = [
        Finding("search", "ext_other", "o2", "src_other", "Another book", False, 0, "found by search, not checked"),
        Finding("search", "ext_other", "o1", "src_other", "Another book", True, 1, "says this in other words"),
    ]
    reply = call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_nothing"})
    assert reply["rows"] == []
    done = _job(menu.ctx, reply["pendingJob"]["jobId"])
    assert [(row["kind"], row["checked"], row["action"]["target"]["spanId"]) for row in done["rows"]] == [
        ("elsewhere", True, "o1"), ("elsewhere", False, "o2")]
    assert done["rows"][1]["reason"] == "found by search, not checked"


def test_a_dismissed_or_wrong_row_is_left_out_on_that_object(menu):
    reply = call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_exchange"})
    row_id = reply["rows"][0]["rowId"]
    call(menu.ctx, "proposal.label", {"labelId": "l1", "proposalKind": "promoted_row", "proposalId": row_id,
                                      "label": "not_this"})
    again = call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_exchange"})
    assert again["rows"] == []
    # The same exchange from another object is another row: the label was for this object.
    other = P.row_id(P.object_key("passage", extraction_id=BOOK, span_id="s_gap"), "question", "qe_1")
    assert other != row_id


def test_a_cancelled_menu_delivers_nothing(menu):
    reply = call(menu.ctx, "passage.promoted", {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_exchange"})
    cancelled = call(menu.ctx, "passage.promoted_cancel", {"jobId": reply["pendingJob"]["jobId"]})
    final = _job(menu.ctx, reply["pendingJob"]["jobId"]) if not cancelled["done"] else cancelled
    assert final["status"] in ("cancelled", "done")
    if final["status"] == "cancelled":
        assert final["rows"] == []


def _row(kind, rid, *, at=None, checked=None, rank=0):
    return P.Row(rid, kind, "?", kind, "why", {"verb": "open"}, learner_at=at, checked=checked, judge_rank=rank)


def test_the_order_learners_history_first_then_judges_rank_one_of_a_kind_first_at_most_four():
    rows = [
        _row("question", "pr_q_old", at="2026-05-01T00:00:00Z"),
        _row("question", "pr_q_new", at="2026-05-03T00:00:00Z"),
        _row("carried", "pr_c", at="2026-05-02T00:00:00Z"),
        _row("next_step", "pr_n", checked=True, rank=0),
        _row("elsewhere", "pr_e_unchecked", checked=False, rank=0),
        _row("elsewhere", "pr_e_checked", checked=True, rank=3),
    ]
    ordered = [row.row_id for row in P.rank(rows)]
    # Newest act first; then judged, checked before unchecked; a second question only after one of each kind.
    assert ordered == ["pr_q_new", "pr_c", "pr_n", "pr_e_checked"]
    assert [row.row_id for row in P.rank(rows, cap=10)] == [
        "pr_q_new", "pr_c", "pr_n", "pr_e_checked", "pr_q_old", "pr_e_unchecked"]
    assert [row.row_id for row in P.rank(rows, dismissed={"pr_q_new"})][:2] == ["pr_c", "pr_q_old"]
    # A tie on the time goes to the smaller id.
    tied = [_row("note", "pr_b", at=T0), _row("gap", "pr_a", at=T0)]
    assert [row.row_id for row in P.rank(tied)] == ["pr_a", "pr_b"]


def test_a_cue_by_time_and_a_pad_line_by_its_passages(menu):
    seed_reading(menu.repository, source_id="src_talk", revision_id="rev_talk", extraction_id="ext_talk",
                 spans=["c1", "c2"], timed=True)
    cue = call(menu.ctx, "passage.promoted", {"objectKind": "cue", "extractionId": "ext_talk", "t": 12})
    assert cue["objectKey"] == "cue:ext_talk:c2"
    line = call(menu.ctx, "passage.promoted", {"objectKind": "pad_line", "blockId": "b1"})
    # The pad line is linked to s_pad: the union read there names the line itself.
    assert [row["kind"] for row in line["rows"]] == ["your_words"]


def test_what_this_knows_is_one_read_of_the_objects_passages(menu):
    knows = call(menu.ctx, "passage.knows", {"objectKind": "passage", "extractionId": BOOK, "spanId": "s_exchange"})
    [place] = knows["places"]
    assert (place["extractionId"], place["spanId"], knows["sourceIds"]) == (BOOK, "s_exchange", ["src_book"])
    assert [(e["questionEventId"], e["quality"]) for e in place["knows"]["exchanges"]] == [("qe_1", "exact_selection")]
    assert "role" in place
    line = call(menu.ctx, "passage.knows", {"objectKind": "pad_line", "blockId": "b1"})
    assert [(p["spanId"], [b["blockId"] for b in p["knows"]["padBlocks"]]) for p in line["places"]] == [
        ("s_pad", ["b1"])]


@pytest.mark.parametrize("name", ["passage.promoted", "passage.knows", "passage.promoted_job",
                                  "passage.promoted_cancel"])
def test_the_menu_rpcs_refuse_an_extra_field_and_are_desktop_only(name):
    from pydantic import ValidationError

    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.registry import METHOD_REGISTRY

    params = {"jobId": "j"} if name.endswith(("_job", "_cancel")) else {
        "objectKind": "passage", "extractionId": BOOK, "spanId": "s1"}
    model = METHOD_REGISTRY[name].params_model
    model.model_validate(params)
    with pytest.raises(ValidationError):
        model.model_validate({**params, "unexpected": True})
    assert name not in ALLOWLIST


def test_an_object_names_what_it_needs():
    from pydantic import ValidationError

    from learnloop_sidecar.registry import METHOD_REGISTRY

    model = METHOD_REGISTRY["passage.promoted"].params_model
    for params in ({"objectKind": "pad_line"}, {"objectKind": "passage", "extractionId": BOOK},
                   {"objectKind": "highlight", "extractionId": BOOK, "spanId": "s1"}):
        with pytest.raises(ValidationError):
            model.model_validate(params)
    model.model_validate({"objectKind": "cue", "extractionId": BOOK, "t": 3})
