"""Reader RW5d P1: the Codex review's findings, each reproduced (docs/reviews/reader-rw5d-p1-show-me-codex-review.md).

F1 grounding's physical calls are admitted by the build's live figures gate;
F2 every supplied question-event reference determines the caller, whatever the origin;
F3 a reused goal lands where the current request was made, and lists at every placement;
F4 a goal-only figure's home is rechecked for held-out material after it was built;
F5 a missed prediction on a goal-only figure is read with its grounding passages;
F6 the tutor's figure goal has its judgment_ledger row, and the press is checked against it;
F7 a reused figure's request row is required: a storage failure fails the request, retryably;
F9 the grounding cap is registered (the parameter audit's module inventory).

Fakes only: the author, the retrieval and every model are injected; no model is reached.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import pytest

from learnloop.ai.execution import model_call
from learnloop.db.stores import figures as figure_store
from learnloop.figures import service as FS
from learnloop.vault.loader import load_vault
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import figures as FH
from tests.figure_fixtures import EXTRACTION, AuthorFake, build, call, flagship, rows, set_config
from tests.source_service_fakes import insert_question
from tests.test_figures_codex_review import _HeldSpans
from tests.test_figures_show_me import GOAL, READING_AT, FindFake, _ctx, _requests, _vault, show_me


def _hold(monkeypatch, *keys: tuple[str, str]) -> None:
    from learnloop.content.sources import exam_material as EM

    monkeypatch.setattr(EM, "exam_material", lambda _vault, _repository: _HeldSpans(set(keys)))


# ---------------------------------------------------------------------------
# F1: grounding is inside the build's gate
# ---------------------------------------------------------------------------

class _PhysicalCalls:
    """A model client the grounding fake asks through ``model_call`` (as the
    sources service's rewrite, embedding and verification calls are made)."""

    provider_name = "fake_grounding"
    model = "fake-grounding-model"


class GatedFind(FindFake):
    """The grounding retrieval making ``calls`` physical requests, flipping
    the configuration after the ``after``-th was admitted."""

    def __init__(self, hits, *, calls: int, after: int, flip) -> None:
        super().__init__(hits)
        self.physical, self.after, self.flip = calls, after, flip
        self.admitted = 0

    def __call__(self, vault: Any, repository: Any, query: str, **kwargs: Any):
        for index in range(self.physical):
            with model_call(_PhysicalCalls(), purpose=f"source_rerank:{index}", prompt=query):
                self.admitted += 1
            if self.admitted == self.after:
                self.flip()
        return super().__call__(vault, repository, query, **kwargs)


FLIPS = {
    "show_me": lambda paths: set_config(paths, "figures", show_me_enabled=False),
    "figures": lambda paths: set_config(paths, "figures", enabled=False),
}


@pytest.mark.parametrize("flip", sorted(FLIPS))
@pytest.mark.parametrize("after", [1, 2])
def test_f1_switching_off_during_grounding_stops_its_calls_and_the_author(tmp_path, flip, after):
    paths, repository = _vault(tmp_path)
    find = GatedFind([("ext_book", "s2")], calls=2, after=after, flip=lambda: FLIPS[flip](paths))
    author = AuthorFake([flagship(kind="illustrative")])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=[], origin="show_me", goal_text=GOAL,
                               goal_author="learner", reading_at={"extraction_id": EXTRACTION, "span_id": "p2"})
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(load_vault(paths.root), repository, request, author_client=author, find=find)
    assert caught.value.code == "figures_changed"
    # Switched off after the first call: the second is never admitted. After
    # the last: grounding's result is never used (no author call).
    assert find.admitted == after and author.calls == 0
    assert rows(repository, "interactive_figures") == [] and _requests(repository) == []


def test_f1_the_control_admits_every_grounding_call(tmp_path):
    paths, repository = _vault(tmp_path)
    find = GatedFind([("ext_book", "s2")], calls=2, after=99, flip=lambda: None)
    author = AuthorFake([flagship(kind="illustrative")])
    request = FS.FigureRequest(extraction_id=EXTRACTION, span_ids=[], origin="show_me", goal_text=GOAL,
                               goal_author="learner", reading_at={"extraction_id": EXTRACTION, "span_id": "p2"})
    outcome = FS.build_figure(load_vault(paths.root), repository, request, author_client=author, find=find)
    assert find.admitted == 2 and author.calls == 1 and outcome.view["grounding"] == "retrieved"


def test_f1_a_reuse_after_show_me_is_switched_off_is_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    find = FindFake([("ext_book", "s2")])
    author = AuthorFake([flagship(kind="illustrative")])
    request = lambda: FS.FigureRequest(extraction_id=EXTRACTION, span_ids=[], origin="show_me", goal_text=GOAL,  # noqa: E731
                                       goal_author="learner", reading_at={"extraction_id": EXTRACTION, "span_id": "p2"})
    FS.build_figure(load_vault(paths.root), repository, request(), author_client=author, find=find)
    flipping = GatedFind([("ext_book", "s2")], calls=1, after=1,
                         flip=lambda: set_config(paths, "figures", show_me_enabled=False))
    with pytest.raises(FS.FigureRefused) as caught:
        FS.build_figure(load_vault(paths.root), repository, request(), author_client=author, find=flipping)
    assert caught.value.code == "figures_changed"
    assert len(_requests(repository)) == 1 and author.calls == 1


# ---------------------------------------------------------------------------
# F2: a supplied question event's restriction is the request's
# ---------------------------------------------------------------------------

def _event(repository, *, context: str = "reader", restriction: dict[str, Any] | None = None) -> str:
    return insert_question(repository, context=context, question="why is it p?",
                           source_context={"reader_caller": restriction} if restriction else None)


@pytest.mark.parametrize(("restriction", "context_name", "code"), [
    ({"cold": True}, "reader", "cold_check"),
    ({"policy": "cold_attempt"}, "reader", "cold_check"),
    ({"item_id": "pi_bound"}, "reader", "validation_error"),
    (None, "practice", "validation_error"),
    (None, "feedback", "validation_error"),
], ids=["cold", "cold policy", "bound to an item", "practice question", "feedback question"])
def test_f2_a_restricted_question_event_refuses_a_show_me_request(tmp_path, restriction, context_name, code):
    paths, repository = _vault(tmp_path)
    author, find = AuthorFake(), FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    event_id = _event(repository, context=context_name, restriction=restriction)
    for origin, extra in (("show_me", {"readingAt": READING_AT}),
                          ("selection", {"anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}})):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", {"goalText": GOAL, "origin": origin, "hostRef": {"questionEventId": event_id},
                                         **extra})
        assert caught.value.code == code, (origin, caught.value.code)
    assert author.calls == 0 and find.calls == [] and _requests(repository) == []


def test_f2_an_open_reader_question_event_derives_a_reader_caller_from_it(tmp_path):
    paths, repository = _vault(tmp_path)
    find = FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=find)
    event_id = _event(repository)
    show_me(ctx, hostRef={"questionEventId": event_id})
    (asked,) = find.calls
    assert asked["caller"].kind == "reader" and asked["caller"].ref == event_id
    (request,) = _requests(repository)
    assert (request["caller_kind"], request["policy"]) == ("reader", "reading")
    assert json.loads(request["host_ref_json"]) == {"question_event_id": event_id}


def test_f2_two_different_answers_named_at_once_are_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake(), find=FindFake([]))
    first, second = _event(repository), _event(repository)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL, "origin": "tutor", "offerRef": first,
                                     "hostRef": {"questionEventId": second}, "readingAt": READING_AT})
    assert caught.value.code in ("not_offered", "validation_error")


# ---------------------------------------------------------------------------
# F3: placement follows the request
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("hits", [[("ext_book", "s2")], []], ids=["grounded", "nothing found"])
def test_f3_a_reused_goal_lands_at_the_current_requests_home(tmp_path, hits):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = _ctx(paths, author=author, find=FindFake(hits))
    first = show_me(ctx)
    assert first["figure"]["anchorSpanId"] == "p2"
    again = show_me(ctx, readingAt={"extractionId": EXTRACTION, "spanId": "p5"})
    assert again["reused"] is True and again["figure"]["figureId"] == first["figure"]["figureId"]
    assert again["figure"]["anchorSpanId"] == "p5" and author.calls == 1
    homes = [json.loads(row["reading_at_json"])["span_id"] for row in _requests(repository)]
    assert homes == ["p2", "p5"]
    # Both placements are kept: the figure is listed under each.
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert sorted((item["figureId"], item["anchorSpanId"]) for item in listed) == [
        (first["figure"]["figureId"], "p2"), (first["figure"]["figureId"], "p5")]
    # Asked again at a placement it already has: still two placements.
    show_me(ctx, readingAt={"extractionId": EXTRACTION, "spanId": "p5"})
    assert len(call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]) == 2


def test_f3_an_anchored_figure_is_listed_once_at_its_anchor(tmp_path):
    paths, _repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([]))
    joint = {"goalText": "but with p near 1", "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]},
             "origin": "show_me"}
    build(ctx, joint, rpc="figure.request")
    build(ctx, joint, rpc="figure.request")
    (listed,) = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert listed["anchorSpanId"] == "p3"


# ---------------------------------------------------------------------------
# F4: a goal-only figure's home, held out later
# ---------------------------------------------------------------------------

def test_f4_a_home_held_out_after_construction_withholds_the_figure(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps.sources import figure_prediction_row, figure_prediction_withheld

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([("ext_book", "s2")]))
    result = show_me(ctx)
    figure = result["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "falls"})
    vault = load_vault(paths.root)
    row = figure_prediction_row(repository, found["predictionId"])
    assert figure_prediction_withheld(vault, repository, row) is None
    # Only the home (never sent to the author) is held out now.
    _hold(monkeypatch, (EXTRACTION, "p2"))
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []
    assert FH.deliver_figure(ctx, result) == {"figure": None, "reused": False, "withheld": True}
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 1, "answer": "rises"})
    assert caught.value.code == "exam_material"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "slower"})
    assert caught.value.code == "exam_material"
    assert figure_prediction_withheld(vault, repository, row) is not None


def test_f4_a_later_placement_held_out_withholds_the_figure_too(tmp_path, monkeypatch):
    paths, _repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([("ext_book", "s2")]))
    show_me(ctx)
    show_me(ctx, readingAt={"extractionId": EXTRACTION, "spanId": "p5"})
    _hold(monkeypatch, (EXTRACTION, "p5"))
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []


def test_f4_an_unreadable_home_fails_closed(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([]))
    show_me(ctx)
    with repository.connection() as connection:
        connection.execute("DROP TRIGGER IF EXISTS figure_requests_append_only_update")
        names = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'figure_requests'")]
        for name in names:
            connection.execute(f'DROP TRIGGER "{name}"')
        connection.execute("UPDATE figure_requests SET reading_at_json = '[1]'")
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []


# ---------------------------------------------------------------------------
# F5: the formative reading of a goal-only figure's prediction
# ---------------------------------------------------------------------------

def test_f5_a_goal_only_figures_prediction_is_read_with_its_grounding_passages(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import sources as gap_sources

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]),
               find=FindFake([("ext_book", "s2"), ("ext_text", "t2")]))
    figure = show_me(ctx)["figure"]
    asked: list[tuple[str, str]] = []

    def learning_objects(_vault, _repository, *, extraction_id, span_id):
        asked.append((extraction_id, span_id))
        return ["lo_matrices"] if (extraction_id, span_id) == ("ext_book", "s2") else []

    monkeypatch.setattr(gap_sources, "learning_objects_for_span", learning_objects)
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "falls"})
    vault = load_vault(paths.root)
    text = gap_sources.figure_prediction_text(vault, repository, found["predictionId"])
    assert text is not None
    # The kept passages (not their neighbours), across both books.
    assert asked == [("ext_book", "s2"), ("ext_text", "t2")]
    passage = text.context["passage"]
    book = repository.load_document_ir("ext_book")
    s2 = " ".join(next(block.text for block in book.blocks if block.span_id == "s2").split())
    assert s2 in passage
    assert text.anchor_learning_object_ids == ("lo_matrices",)
    assert text.subject_id == vault.learning_objects["lo_matrices"].subjects[0]
    assert text.context["learning_objects"] == [vault.learning_objects["lo_matrices"].title]


def test_f5_the_gap_reader_is_sent_the_grounding_passage(tmp_path, monkeypatch):
    from learnloop.diagnosis.text_gaps import sources as gap_sources
    from learnloop.diagnosis.text_gaps.jobs import process_next_gap_job
    from tests.test_figures_codex_review import _clients

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([("ext_book", "s2")]))
    monkeypatch.setattr(gap_sources, "learning_objects_for_span",
                        lambda _v, _r, *, extraction_id, span_id: ["lo_matrices"] if extraction_id == "ext_book" else [])
    figure = show_me(ctx)["figure"]
    call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "falls"})
    llm, clients = _clients()
    outcome = process_next_gap_job(paths.root, repository, owner="t", clients=clients)
    assert outcome.state == "done"
    book = repository.load_document_ir("ext_book")
    s2 = " ".join(next(block.text for block in book.blocks if block.span_id == "s2").split())
    sent = json.dumps([payload for _purpose, payload in llm.calls])
    assert s2 in sent
    with repository.connection() as connection:
        (anchor,) = connection.execute("SELECT anchor_learning_object_id FROM learner_text_gaps").fetchone()
    assert anchor == "lo_matrices"


def test_f5_an_anchored_figures_text_is_unchanged(tmp_path):
    from learnloop.diagnosis.text_gaps import sources as gap_sources

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]))
    figure = build(ctx)["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "falls"})
    row = gap_sources.figure_prediction_row(repository, found["predictionId"])
    assert gap_sources.figure_grounding_keys(repository, row) == []
    text = gap_sources.figure_prediction_text(load_vault(paths.root), repository, found["predictionId"])
    assert text.context["passage"] == gap_sources._span_texts(repository, EXTRACTION, ["p3"])


# ---------------------------------------------------------------------------
# F6: the tutor's figure goal is a ledger judgment
# ---------------------------------------------------------------------------

def test_f6_the_tutors_goal_has_one_ledger_row_and_the_press_reads_it(tmp_path, monkeypatch):
    from learnloop.figure_admission import (
        TUTOR_FIGURE_GOAL_TASK,
        figure_goal_digest,
        tutor_figure_goal_judgment_id,
    )
    from tests.test_figures_show_me import _tutor_ask

    goal = "vary p and watch the mass left of zero follow it"
    _paths, repository, ctx, tutor, author, _find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=goal)
    event_id = answer["eventId"]
    with repository.connection() as connection:
        ledger = [dict(row) for row in connection.execute(
            "SELECT * FROM judgment_ledger WHERE task = ?", (TUTOR_FIGURE_GOAL_TASK,))]
    (row,) = ledger
    assert row["id"] == tutor_figure_goal_judgment_id(event_id) and row["left_id"] == event_id
    assert row["judge"] == "llm" and row["judge_model"] and "show-me" in row["prompt_version"]
    assert row["verdict"] == "offered" and row["right_id"] == figure_goal_digest(goal, [[EXTRACTION, "p6"]])
    assert json.loads(row["rationale"]) == {"figure_goal": goal, "span_keys": [[EXTRACTION, "p6"]]}
    press = {"origin": "tutor", "goalText": goal, "offerRef": event_id,
             "readingAt": {"extractionId": EXTRACTION, "spanId": "p6"}}
    # The stored view edited to another goal or other grounding: refused.
    stored = repository.question_event(event_id)["source_context"]
    for edited in ({"text": "a goal the tutor never offered", "span_keys": [[EXTRACTION, "p6"]]},
                   {"text": goal, "span_keys": [["ext_book", "s2"]]}):
        _set_view_goal(repository, event_id, stored, edited)
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", {**press, "goalText": edited["text"]})
        assert caught.value.code == "not_offered"
    _set_view_goal(repository, event_id, stored, {"text": goal, "span_keys": [[EXTRACTION, "p6"]]})
    assert author.calls == 0
    figure = build(ctx, press, rpc="figure.request")["figure"]
    assert figure["goalAuthor"] == "tutor" and author.calls == 1


def test_f6_a_goal_in_the_view_with_no_ledger_row_is_refused(tmp_path, monkeypatch):
    from learnloop.figure_admission import TUTOR_FIGURE_GOAL_TASK
    from tests.test_figures_show_me import _tutor_ask

    goal = "vary p and watch the mass left of zero follow it"
    _paths, repository, ctx, _tutor, author, _find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=goal)
    with repository.connection() as connection:
        connection.execute("DROP TRIGGER IF EXISTS judgment_ledger_no_delete")
        triggers = [row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'trigger' AND tbl_name = 'judgment_ledger'")]
        for name in triggers:
            connection.execute(f'DROP TRIGGER "{name}"')
        connection.execute("DELETE FROM judgment_ledger WHERE task = ?", (TUTOR_FIGURE_GOAL_TASK,))
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"origin": "tutor", "goalText": goal, "offerRef": answer["eventId"],
                                     "readingAt": {"extractionId": EXTRACTION, "spanId": "p6"}})
    assert caught.value.code == "not_offered" and author.calls == 0


def test_f6_no_goal_writes_no_goal_row(tmp_path, monkeypatch):
    from learnloop.figure_admission import TUTOR_FIGURE_GOAL_TASK
    from tests.test_figures_show_me import _tutor_ask

    _paths, repository, *_rest = _tutor_ask(tmp_path, monkeypatch, figure_goal=None)
    with repository.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM judgment_ledger WHERE task = ?",
                                  (TUTOR_FIGURE_GOAL_TASK,)).fetchone()[0] == 0


def _set_view_goal(repository, event_id: str, source_context: dict[str, Any], goal: dict[str, Any]) -> None:
    edited = json.loads(json.dumps(source_context))
    edited["reader_tutor"]["figure_goal"] = goal
    with repository.connection() as connection:
        connection.execute("UPDATE question_events SET source_context_json = ? WHERE id = ?",
                           (json.dumps(edited), event_id))


# ---------------------------------------------------------------------------
# F7: a reuse's request row is required
# ---------------------------------------------------------------------------

def test_f7_a_reuse_whose_request_cannot_be_recorded_fails_retryably_and_the_retry_reuses(tmp_path, monkeypatch):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = _ctx(paths, author=author, find=FindFake([("ext_book", "s2")]))
    first = show_me(ctx)
    real = figure_store.insert_request
    failing = {"left": 1}

    def insert_request(connection, row):
        if failing["left"]:
            failing["left"] -= 1
            raise sqlite3.OperationalError("database is locked")
        return real(connection, row)

    monkeypatch.setattr(figure_store, "insert_request", insert_request)
    with pytest.raises(SidecarError) as caught:
        show_me(ctx)
    # Never a success without its ledger row.
    assert caught.value.code == FS.STORAGE_BUSY and caught.value.retryable
    assert len(_requests(repository)) == 1
    again = show_me(ctx)
    assert again["reused"] is True and again["figure"]["figureId"] == first["figure"]["figureId"]
    assert author.calls == 1 and len(_requests(repository)) == 2


# ---------------------------------------------------------------------------
# F9: the grounding cap is registered
# ---------------------------------------------------------------------------

def test_f9_the_grounding_cap_is_registered_and_audited():
    from learnloop.params import parameter_registry as PR

    assert PR.MODULE_INVENTORY["figure_admission"] == "src/learnloop/figure_admission.py"
    assert "figure_admission:GROUNDING_PASSAGES" in PR.module_numeric_constants()
    spec = PR.REGISTRY["figure_admission:GROUNDING_PASSAGES"]
    assert spec.kind == "structural" and spec.rationale.startswith("keep:")


# ---------------------------------------------------------------------------
# F8 (server side): a cited passage names its source, so its chip can open it
# ---------------------------------------------------------------------------

def test_f8_every_cited_passage_names_its_source(tmp_path, monkeypatch):
    from tests.test_figures_show_me import _tutor_ask

    paths, _repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([("ext_book", "s2")]))
    retrieved = show_me(ctx)["figure"]
    assert [(p["sourceId"], p["sourceTitle"]) for p in retrieved["passages"]] == [("src_book", "Book ext_book")]
    # A tutor goal's cited passages (fixed keys, no retrieval hit to copy from).
    goal = "vary p and watch the mass left of zero follow it"
    _paths, _repo, tutor_ctx, *_rest, answer = _tutor_ask(tmp_path / "tutor", monkeypatch, figure_goal=goal)
    figure = build(tutor_ctx, {"origin": "tutor", "goalText": goal, "offerRef": answer["eventId"],
                               "readingAt": {"extractionId": EXTRACTION, "spanId": "p6"}}, rpc="figure.request")["figure"]
    assert [(p["extractionId"], p["sourceId"], p["sourceTitle"]) for p in figure["passages"]] == [
        (EXTRACTION, "src_prob", "Introduction to Probability")]
