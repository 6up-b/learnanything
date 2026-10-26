"""Reader RW5d P1: "show me" (docs/specs/spec_reader_show_me_figures_v1.md §6.1-6.3, §7, §8; gates G-SM1-G-SM7).

* **The request.** ``figure.request`` takes ``FigureRequestV1``: a goal in the
  learner's words, an optional anchor, where the learner was reading and the
  host references; ``goal_author`` is the server's (G-SM5), a client never
  states its policy, a check on your own refuses, and P3/P4 hosts are refused.
* **Grounding** (§8.3). With no passage the goal is grounded through the
  sources service's verified retrieval (intent explain, verify on, at most
  three passages, exam material withheld and rechecked); nothing found is built
  anyway, an illustration that quotes nothing, labelled "not from your books"
  (G-SM3). A joint request uses the anchor's context and adds the goal.
* **Held-out material** (G-SM2): never sent, and a figure whose retrieved
  passage is held out later is neither listed nor delivered.
* **Reuse** (G-SM4): the key changes with the goal and the grounding, never
  with the origin; an RW5a/b request is hashed and prompted exactly as before.
* **The tutor's goal** (G-SM5, G-SM7): a stored ``figure_goal`` becomes a
  button whose press is checked against it; switched off, the tutor is RW5b's.
* **The ledger**: every request, built or reused, appends one
  ``figure_requests`` row (append-only; ``figure_id`` set once).

Fakes only: the author and the retrieval are injected; no model is reached.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import pytest

from learnloop.ai import plan_fallback as PF
from learnloop.ai.execution import content_key
from learnloop.figures import routes as R
from learnloop.figures import service as FS
from learnloop.figures import spec as S
from learnloop.source_retrieval.find_sources import SourceHits
from learnloop_sidecar.errors import SidecarError
from learnloop_sidecar.handlers import figures as FH
from tests.figure_fixtures import (
    EXTRACTION,
    AuthorFake,
    build,
    build_figure_vault,
    call,
    context,
    flagship,
    rows,
    set_config,
)

READING_AT = {"extractionId": EXTRACTION, "spanId": "p2"}
GOAL = "show how the mass left of zero moves as p changes"


class FindFake:
    """The grounding retrieval: records every call, answers with ``hits`` (keys) and ``status``."""

    def __init__(self, hits: list[tuple[str, str]] | None = None, *, status: str = "ok",
                 fail: BaseException | None = None) -> None:
        self.hits = list(hits or [])
        self.status = status
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def __call__(self, vault: Any, repository: Any, query: str, **kwargs: Any) -> SourceHits:
        self.calls.append({"query": query, **kwargs})
        if self.fail is not None:
            raise self.fail
        return SourceHits(intent="explain", policy="reading", status=self.status, manifest={"query_hash": "q"},
                          hits=[{"extraction_id": e, "span_id": s, "source_title": f"Book {e}", "section": "§1",
                                 "page": 1, "text": "..."} for e, s in self.hits])


def _vault(tmp_path):
    return build_figure_vault(tmp_path / "vault")


def _ctx(paths, *, author=None, find=None):
    ctx = context(paths.root, author=author or AuthorFake())
    if find is not None:
        ctx.figure_find_sources = find
    return ctx


def show_me(ctx, goal: str = GOAL, **params: Any) -> dict[str, Any]:
    return build(ctx, {"goalText": goal, "readingAt": READING_AT, "origin": "show_me", **params},
                 rpc="figure.request")


def _requests(repository) -> list[dict[str, Any]]:
    return rows(repository, "figure_requests")


# ---------------------------------------------------------------------------
# G-SM1: the switch and the minimum request
# ---------------------------------------------------------------------------

def test_a_goal_alone_is_refused_while_show_me_is_off(tmp_path):
    paths, repository = _vault(tmp_path)
    set_config(paths, "figures", show_me_enabled=False)
    author, find = AuthorFake(), FindFake()
    ctx = _ctx(paths, author=author, find=find)
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT})
    assert caught.value.code == "show_me_disabled"
    # A joint request too: the words are what is switched off.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL, "origin": "show_me",
                                     "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}})
    assert caught.value.code == "show_me_disabled"
    assert author.calls == 0 and find.calls == [] and _requests(repository) == []
    # Off, the contract has no show_me and an anchor-only request is RW5a's.
    assert "showMe" not in call(ctx, "reader.prompt_contract", {})["figures"]
    built = build(ctx, {"anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}, "origin": "selection"},
                  rpc="figure.request")
    assert built["figure"]["verification"] == "illustrative" and "goalText" not in built["figure"]


def test_neither_goal_nor_anchor_is_refused_and_show_me_needs_words(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake()
    ctx = _ctx(paths, author=author, find=FindFake())
    for params in ({"origin": "selection", "readingAt": READING_AT}, {"origin": "show_me", "readingAt": READING_AT},
                   {"goalText": "   ", "readingAt": READING_AT}):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", params)
        assert caught.value.code == "validation_error", params
    # A goal with no anchor needs a place to land.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL})
    assert caught.value.code == "validation_error"
    assert author.calls == 0 and _requests(repository) == []


def test_the_client_never_names_the_goals_author_its_policy_or_a_later_host(tmp_path):
    paths, _repository = _vault(tmp_path)
    author = AuthorFake()
    ctx = _ctx(paths, author=author, find=FindFake())
    for extra in ({"goalAuthor": "tutor"}, {"policy": "post_attempt"}, {"tiersAllowed": ["manim"]}):
        with pytest.raises(Exception):
            call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT, **extra})
    for origin in ("ask", "teacher", "prefetch"):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT, "origin": origin})
        assert caught.value.code == "validation_error"
    for ref in ({"itemId": "pi_1"}, {"workbenchSessionId": "wb_1"}, {"lessonId": "les_1", "nodeId": "n1"}):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT, "hostRef": ref})
        assert caught.value.code == "validation_error"
    # SM4: nothing during a check on your own (the take step is P3's).
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT, "coldActive": True})
    assert caught.value.code == "cold_check"
    assert author.calls == 0


# ---------------------------------------------------------------------------
# Grounding (§8.3) and G-SM3
# ---------------------------------------------------------------------------

def test_a_goal_alone_is_grounded_in_the_books_and_lands_where_the_learner_was(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative", source_claims=[
        {"span_id": "ext_book:s2", "quote": "not a quote from it"}])])
    find = FindFake([("ext_book", "s2"), ("ext_prob", "p6"), ("ext_book", "s2"), ("ext_book", "s3"),
                     ("ext_book", "s4")])
    ctx = _ctx(paths, author=author, find=find)
    result = show_me(ctx)
    figure = result["figure"]
    # The sources service's verified retrieval, intent explain, at most three passages.
    (asked,) = find.calls
    assert asked["query"] == GOAL and asked["intent"] == "explain" and asked["verify"] is True
    assert asked["limit"] == FS.GROUNDING_PASSAGES == 3 and asked["caller"].kind == "reader"
    sent = author.contexts[0]
    assert sent["learner_request"] == {"text": GOAL, "written_by": "learner"}
    assert sent["grounding"] == "retrieved"
    assert [block["span_id"] for block in sent["passage"]] == ["ext_book:s2", "ext_prob:p6", "ext_book:s3"]
    assert all(":" in block["span_id"] for block in sent["around"])
    assert author.prompts[0].count(R.SHOW_ME_SUFFIX) >= 1 and "learner_request" in author.prompts[0]
    # It lands under the passage the learner was reading, its home.
    assert figure["extractionId"] == EXTRACTION and figure["anchorSpanId"] == "p2" and figure["spanIds"] == []
    assert figure["goalText"] == GOAL and figure["goalAuthor"] == "learner" and figure["grounding"] == "retrieved"
    assert [(p["extractionId"], p["spanId"]) for p in figure["passages"]] == [
        ("ext_book", "s2"), ("ext_prob", "p6"), ("ext_book", "s3")]
    assert figure["label"] == FS.LABELS["illustrative"]
    (row,) = rows(repository, "interactive_figures")
    assert row["origin"] == "show_me" and row["grounding"] == "retrieved" and row["goal_text"] == GOAL
    assert json.loads(row["input_span_ids_json"]) == []
    keys = [tuple(key) for key in json.loads(row["input_span_keys_json"])]
    assert ("ext_book", "s2") in keys and ("ext_prob", "p6") in keys
    assert row["prompt_version"] == R.author_prompt_version(advanced=True, show_me=True)
    (request,) = _requests(repository)
    assert request["figure_id"] == row["id"] and row["request_id"] == request["id"]
    assert (request["origin"], request["goal_author"], request["policy"], request["caller_kind"]) == (
        "show_me", "learner", "reading", "reader")
    assert request["grounding"] == "retrieved" and request["anchor_json"] is None
    assert json.loads(request["reading_at_json"]) == {"extraction_id": EXTRACTION, "span_id": "p2"}
    assert (request["build_mode"], json.loads(request["tiers_allowed_json"])) == ("pressed", ["grammar"])
    assert json.loads(request["grounding_manifest_json"])["kept"] == [["ext_book", "s2"], ["ext_prob", "p6"],
                                                                     ["ext_book", "s3"]]
    # Listed on its home.
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [item["figureId"] for item in listed] == [figure["figureId"]]


@pytest.mark.parametrize("find", [FindFake([]), FindFake([("ext_book", "s2")], status="unverified: unavailable"),
                                  FindFake(fail=RuntimeError("no index"))],
                         ids=["nothing found", "unverified", "retrieval failed"])
def test_nothing_found_is_built_anyway_as_an_illustration_not_from_your_books(tmp_path, find):
    paths, repository = _vault(tmp_path)
    # The author writes a reconstruction with claims and quotes: code forces it.
    author = AuthorFake([flagship()])
    ctx = _ctx(paths, author=author, find=find)
    figure = show_me(ctx)["figure"]
    sent = author.contexts[0]
    assert sent["grounding"] == "none" and sent["passage"] == [] and sent["around"] == []
    assert "nothing in the learner's books was found" in author.prompts[0]
    assert figure["verification"] == "illustrative" and figure["kind"] == "illustrative"
    assert figure["grounding"] == "none" and figure["passages"] == []
    assert figure["label"] == FS.NOT_FROM_BOOKS_LABEL == "AI-built illustration · not from your books"
    spec = json.loads(figure["specJson"])
    assert spec["kind"] == "illustrative" and spec["source_claims"] == []
    assert all(not item.get("quote") for item in spec["assumptions"])
    assert all(item["kind"] != "equals_source" for item in spec["invariants"])
    assert all(item["quote"] is None for item in figure["assumptions"])
    (row,) = rows(repository, "interactive_figures")
    assert row["grounding"] == "none" and json.loads(row["input_span_keys_json"]) == []
    assert json.loads(row["verification_report_json"])["claims"] == []


def test_a_joint_request_uses_the_anchors_context_and_adds_the_goal(tmp_path):
    paths, repository = _vault(tmp_path)
    author, find = AuthorFake([flagship(kind="illustrative")]), FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    figure = build(ctx, {"goalText": "but with p near 1", "origin": "show_me",
                         "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}}, rpc="figure.request")["figure"]
    assert find.calls == []  # the learner chose the passage
    sent = author.contexts[0]
    assert [block["span_id"] for block in sent["passage"]] == ["p3"]
    assert [block["span_id"] for block in sent["around"]] == ["p1", "p2", "p4", "p5"]
    assert sent["learner_request"] == {"text": "but with p near 1", "written_by": "learner"}
    assert sent["grounding"] == "anchor"
    assert figure["anchorSpanId"] == "p3" and figure["grounding"] == "anchor" and figure["goalText"] == "but with p near 1"
    (row,) = rows(repository, "interactive_figures")
    assert json.loads(row["input_span_ids_json"]) == ["p3", "p1", "p2", "p4", "p5"]


# ---------------------------------------------------------------------------
# G-SM2: held-out material, at the request and later
# ---------------------------------------------------------------------------

def test_exam_passages_never_reach_the_author_and_an_exam_home_is_refused(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    find = FindFake([("ext_exam", "s1"), ("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    show_me(ctx)
    sent = author.contexts[0]
    assert not any(block["span_id"].startswith("ext_exam:") for block in sent["passage"] + sent["around"])
    # A figure never lands on held-out material.
    with pytest.raises(SidecarError) as caught:
        call(ctx, "figure.request", {"goalText": GOAL, "readingAt": {"extractionId": "ext_exam", "spanId": "s1"}})
    assert caught.value.code == "exam_material"
    assert author.calls == 1


def test_a_retrieved_passage_held_out_later_withholds_the_figure(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material as EM
    from tests.test_figures_codex_review import _HeldSpans

    paths, _repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = _ctx(paths, author=author, find=FindFake([("ext_book", "s2")]))
    result = show_me(ctx)
    figure = result["figure"]
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    # Another book's passage (the home is open) becomes held out.
    monkeypatch.setattr(EM, "exam_material", lambda _vault, _repository: _HeldSpans({("ext_book", "s2")}))
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []
    assert FH.deliver_figure(ctx, result) == {"figure": None, "reused": False, "withheld": True}
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0, "answer": "rises"})
    assert caught.value.code == "exam_material"
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "slower"})
    assert caught.value.code == "exam_material"
    # A neighbour of the retrieved passage counts too (it was sent).
    monkeypatch.setattr(EM, "exam_material", lambda _vault, _repository: _HeldSpans({("ext_book", "s3")}))
    assert call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"] == []


def test_a_missed_predictions_text_rechecks_the_retrieved_passages(tmp_path, monkeypatch):
    from learnloop.content.sources import exam_material as EM
    from learnloop.diagnosis.text_gaps.provenance import figure_prediction_record
    from learnloop.diagnosis.text_gaps.sources import figure_prediction_row, figure_prediction_withheld
    from learnloop.vault.loader import load_vault
    from tests.test_figures_codex_review import _HeldSpans

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([("ext_book", "s2")]))
    figure = show_me(ctx)["figure"]
    found = call(ctx, "reader.figure_predict", {"figureId": figure["figureId"], "predictionIndex": 0,
                                                 "answer": "falls"})
    with repository.connection() as connection:
        record = figure_prediction_record(connection, found["predictionId"])
    assert any(source["extraction_id"] == "ext_book" and "s2" in source["span_ids"]
               for source in record.inputs.sources)
    vault = load_vault(paths.root)
    row = figure_prediction_row(repository, found["predictionId"])
    assert figure_prediction_withheld(vault, repository, row) is None
    monkeypatch.setattr(EM, "exam_material", lambda _vault, _repository: _HeldSpans({("ext_book", "s2")}))
    assert figure_prediction_withheld(vault, repository, row) is not None


# ---------------------------------------------------------------------------
# G-SM4: the reuse key
# ---------------------------------------------------------------------------

def test_the_reuse_key_follows_the_goal_and_grounding_never_the_origin(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative") for _ in range(4)])
    find = FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    first = show_me(ctx)
    again = show_me(ctx, "  show how the mass left of zero   moves as p changes ")  # whitespace-normalized
    assert again["reused"] is True and again["figure"]["figureId"] == first["figure"]["figureId"]
    assert author.calls == 1
    other = show_me(ctx, "Show how the mass left of zero moves as p changes")  # case kept
    assert other["reused"] is False and author.calls == 2
    find.hits = [("ext_book", "s3")]
    regrounded = show_me(ctx)
    assert regrounded["reused"] is False and author.calls == 3
    # Origin stays out of the key: a joint request from the box with origin
    # selection or show_me is one figure.
    joint = {"goalText": "but with p near 1", "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}}
    built = build(ctx, {**joint, "origin": "show_me"}, rpc="figure.request")
    reused = build(ctx, {**joint, "origin": "selection"}, rpc="figure.request")
    assert reused["reused"] is True and reused["figure"]["figureId"] == built["figure"]["figureId"]
    assert author.calls == 4
    # Every request, built or reused, is on the ledger.
    assert len(_requests(repository)) == 6
    assert [row["figure_id"] is not None for row in _requests(repository)] == [True] * 6


def test_an_rw5ab_request_hashes_and_prompts_exactly_as_before(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative")])
    ctx = _ctx(paths, author=author)
    build(ctx)  # reader.figure_request, the selection p3
    (row,) = rows(repository, "interactive_figures")
    # The pre-224 key: no goal, grounding or show-me field, RW5b's prompt version.
    sent = author.contexts[0]
    old_key = content_key({
        "spec_version": S.SPEC_VERSION, "prompt_version": R.ADVANCED_PROMPT_VERSION, "extraction_id": EXTRACTION,
        "span_ids": ["p3"], "region": None, "origin": "selection", "passage": sent["passage"],
        "around": sent["around"], "image_sha256": None, "supersedes_id": None, "revision_note": None})
    assert row["input_hash"] == old_key and row["prompt_version"] == R.ADVANCED_PROMPT_VERSION
    assert "learner_request" not in sent and "grounding" not in sent
    assert R.SHOW_ME_SUFFIX not in author.prompts[0] and "learner_request" not in author.prompts[0]
    assert author.prompts[0] == R.author_prompt(sent, advanced=True)
    assert row["grounding"] == "anchor" and row["goal_text"] is None and row["tier"] == "grammar"
    # The new RPC with the same anchor is the same input.
    again = build(ctx, {"anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}, "origin": "selection"},
                  rpc="figure.request")
    assert again["reused"] is True and author.calls == 1


# ---------------------------------------------------------------------------
# Revisions, the switch going off, the job's origin
# ---------------------------------------------------------------------------

def test_not_right_on_a_show_me_figure_keeps_its_goal_home_and_grounding(tmp_path):
    paths, repository = _vault(tmp_path)
    author = AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative", demonstrates="better")])
    find = FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    figure = show_me(ctx)["figure"]
    job = call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "start p at 0.1"})
    revised = call(ctx, "reader.figure_job", {"jobId": job["jobId"]})["result"]["figure"]
    assert len(find.calls) == 1  # nothing is retrieved again
    sent = author.contexts[1]
    assert sent["learner_request"] == {"text": GOAL, "written_by": "learner"} and sent["grounding"] == "retrieved"
    assert sent["learner_note"] == "start p at 0.1"
    assert [block["span_id"] for block in sent["passage"]] == ["ext_book:s2"]
    assert revised["supersedesId"] == figure["figureId"] and revised["anchorSpanId"] == "p2"
    assert revised["goalText"] == GOAL and revised["grounding"] == "retrieved"


def test_show_me_off_lists_no_show_me_figure_and_the_view_is_rw5bs(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative")]),
               find=FindFake([("ext_book", "s2")]))
    goal_figure = show_me(ctx)["figure"]
    anchored = build(ctx)["figure"]
    set_config(paths, "figures", show_me_enabled=False)
    ctx = _ctx(paths, author=AuthorFake())
    listed = call(ctx, "reader.figures", {"extractionId": EXTRACTION})["figures"]
    assert [item["figureId"] for item in listed] == [anchored["figureId"]]
    assert not {"goalText", "goalAuthor", "grounding", "passages"} & set(listed[0])
    with pytest.raises(SidecarError) as caught:
        call(ctx, "reader.figure_predict", {"figureId": goal_figure["figureId"], "predictionIndex": 0,
                                            "answer": "rises"})
    assert caught.value.code == "show_me_disabled"


def test_the_build_job_belongs_to_figure_request_for_t1s_offer(tmp_path):
    """Redesign D: the offer is the grant, keyed by the origin RPC method. A
    figure.request job's units carry ``figure.request`` (the press), so a
    grant given on it covers its build and nothing else."""

    paths, _repository = _vault(tmp_path)
    seen: list[Any] = []

    def record(context):
        seen.append(PF._job_here())
        return flagship(kind="illustrative")

    ctx = _ctx(paths, author=AuthorFake([record]), find=FindFake([]))
    with PF.request(paths.root, "figure.request"):
        call(ctx, "figure.request", {"goalText": GOAL, "readingAt": READING_AT})
    assert seen and seen[0][0] == "figure.request"


# ---------------------------------------------------------------------------
# G-SM5 and G-SM7: the tutor's figure goal
# ---------------------------------------------------------------------------

def _tutor_ask(tmp_path, monkeypatch, *, figure_goal: str | None, show_me: bool = True):
    import learnloop_sidecar.handlers.reader as reader_handler
    from tests.reader_tutor_fakes import KeepContaining, LookupTutor, Ready

    paths, repository = _vault(tmp_path)
    if not show_me:
        set_config(paths, "figures", show_me_enabled=False)
    tutor = LookupTutor(answer_md="P(X <= 0) = p, whatever lambda is.", cite=lambda _c: [(EXTRACTION, "p6")])
    tutor.figure_goal = figure_goal
    author = AuthorFake([flagship(kind="illustrative")])
    find = FindFake([("ext_book", "s2")])
    ctx = _ctx(paths, author=author, find=find)
    ctx.reader_tutor_rerank_client = KeepContaining("whatever")
    monkeypatch.setattr(reader_handler, "ready_tutor_qa_provider", lambda vault: ("fake", Ready(), tutor))
    answer = call(ctx, "reader.ask", {"extractionId": EXTRACTION, "spanId": "p6", "question": "why is it p?",
                                      "selectionSpanIds": ["p6"], "selectionQuote": "P(X <= 0) = p"})
    return paths, repository, ctx, tutor, author, find, answer


def test_the_tutors_goal_is_a_button_and_its_press_builds_from_the_cited_passages(tmp_path, monkeypatch):
    goal = "vary p and watch the mass left of zero follow it"
    _paths, repository, ctx, tutor, author, find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=goal)
    assert tutor.result_models[-1].startswith("ReaderTutor") and "ShowMe" in tutor.result_models[-1]
    assert "figure_goal" in tutor.prompts[-1]
    buttons = (answer.get("tutorOffers") or {}).get("buttons") or []
    (button,) = [b for b in buttons if b["kind"] == "show_me"]
    assert button["label"] == goal and button["role"] == "figure_goal"
    stored = repository.question_event(answer["eventId"])["source_context"]["reader_tutor"]["figure_goal"]
    assert stored == {"text": goal, "span_keys": [[EXTRACTION, "p6"]]}
    # A forged goal, another event, or an anchor with it: refused before any call.
    for params in ({"goalText": "something the tutor never said", "offerRef": answer["eventId"]},
                   {"goalText": goal, "offerRef": answer["readerAnswerEventId"]},
                   {"goalText": goal, "offerRef": answer["eventId"],
                    "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}}):
        with pytest.raises(SidecarError) as caught:
            call(ctx, "figure.request", {"origin": "tutor", "readingAt": READING_AT, **params})
        assert caught.value.code == "not_offered", params
    # A learner's words never claim the tutor's voice: from the box it is the learner's goal.
    assert author.calls == 0
    figure = build(ctx, {"origin": "tutor", "goalText": goal, "offerRef": answer["eventId"],
                         "readingAt": {"extractionId": EXTRACTION, "spanId": "p6"}}, rpc="figure.request")["figure"]
    assert find.calls == []  # grounded in the answer's cited passages
    sent = author.contexts[0]
    assert sent["learner_request"] == {"text": goal, "written_by": "tutor"}
    assert [block["span_id"] for block in sent["passage"]] == [f"{EXTRACTION}:p6"]
    assert figure["goalAuthor"] == "tutor" and figure["origin"] == "tutor" and figure["grounding"] == "retrieved"
    (request,) = _requests(repository)
    assert request["goal_author"] == "tutor" and request["caller_kind"] == "tutor"
    assert json.loads(request["host_ref_json"]) == {"question_event_id": answer["eventId"]}


def test_no_goal_no_button_and_show_me_off_is_rw5bs_tutor(tmp_path, monkeypatch):
    *_, tutor, _author, _find, answer = _tutor_ask(tmp_path, monkeypatch, figure_goal=None)
    assert not [b for b in (answer.get("tutorOffers") or {}).get("buttons") or [] if b["kind"] == "show_me"]
    assert "figureGoal" not in (answer.get("tutor") or {})
    tutor_off = _tutor_ask(tmp_path / "off", monkeypatch, figure_goal="vary p", show_me=False)
    tutor, answer = tutor_off[3], tutor_off[6]
    # RW5b's model and prompt: no figure goal asked for, none read, no button.
    assert "ShowMe" not in tutor.result_models[-1] and "figure_goal" not in tutor.prompts[-1]
    assert "figureGoal" not in (answer.get("tutor") or {})
    assert not [b for b in (answer.get("tutorOffers") or {}).get("buttons") or [] if b["kind"] == "show_me"]


def test_the_show_me_tutor_prompt_is_rw5bs_plus_the_goal_clause():
    from learnloop.tutor import ai_contracts as C

    base = dict(context="reader", question_md="why?", candidate_facets=[], thread=[], source_spans=[],
                answer_mode="answer_directly", reader_tutor={"books_cover": True, "intent": "explain"})
    plain = C.tutor_qa_prompt(C.ReaderTutorQAContext(**base))
    goal = C.tutor_qa_prompt(C.ReaderTutorShowMeQAContext(**base))
    assert C.READER_TUTOR_PROMPT_VERSION in plain and C.READER_TUTOR_SHOW_ME_PROMPT_VERSION in goal
    assert "figure_goal" not in plain and "figure_goal" in goal
    explorable = C.tutor_qa_prompt(C.ReaderTutorExplorableShowMeQAContext(**base), tools=True)
    assert C.READER_TUTOR_EXPLORABLE_SHOW_ME_TOOLS_PROMPT_VERSION in explorable and "`explorable`" in explorable


# ---------------------------------------------------------------------------
# G-SM6 (server side): the intent box's one action
# ---------------------------------------------------------------------------

def test_the_intent_boxs_figure_action_is_show_me_while_on():
    from learnloop.config.schema import LearnLoopConfig
    from learnloop.reader import reader_intent as RI

    config = LearnLoopConfig()
    on = RI.Availability.from_config(config)
    actions = {action.id: action for action in RI.available_actions(on)}
    assert actions["make_explorable"].label == "show me…"
    assert actions["make_explorable"].describe.endswith(RI.SHOW_ME_CLAUSE)
    assert actions["make_explorable"].effect == {"kind": "figure"}
    assert RI.question_set_version(on) == RI.SHOW_ME_QUESTION_SET_VERSION
    config.figures.show_me_enabled = False
    off = RI.Availability.from_config(config)
    actions = {action.id: action for action in RI.available_actions(off)}
    assert actions["make_explorable"] == RI.ACTIONS_BY_ID["make_explorable"]
    assert RI.question_set_version(off) == RI.QUESTION_SET_VERSION
    # Routings hash as before while show me is off.
    assert RI.input_hash("x", "q", ["a"]) == RI.input_hash("x", "q", ["a"], question_set=RI.QUESTION_SET_VERSION)


# ---------------------------------------------------------------------------
# The ledger and the report
# ---------------------------------------------------------------------------

def test_figure_requests_is_append_only_with_the_figure_set_once(tmp_path):
    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative")]), find=FindFake([]))
    show_me(ctx)
    (request,) = _requests(repository)
    with repository.connection() as connection:
        for statement in ("UPDATE figure_requests SET goal_text = 'other'", "DELETE FROM figure_requests",
                          "UPDATE figure_requests SET figure_id = NULL", "UPDATE figure_requests SET policy = 'x'"):
            with pytest.raises(sqlite3.DatabaseError):
                connection.execute(statement)


def test_the_reader_report_counts_show_me_without_the_words(tmp_path):
    from learnloop.reader.reader_report import build_reader_report

    paths, repository = _vault(tmp_path)
    ctx = _ctx(paths, author=AuthorFake([flagship(kind="illustrative"), flagship(kind="illustrative"),
                                         ("unsupported", "3-D surface"), flagship(kind="illustrative")]),
               find=FindFake([("ext_book", "s2")]))
    figure = show_me(ctx)["figure"]
    ctx.figure_find_sources = FindFake([])
    show_me(ctx, "a different idea")
    build(ctx, {"goalText": "as a surface", "origin": "show_me",
                "anchor": {"extractionId": EXTRACTION, "spanIds": ["p3"]}}, rpc="figure.request")
    call(ctx, "reader.figure_revise", {"figureId": figure["figureId"], "note": "slower"})
    report = build_reader_report(repository.sqlite_path, figures_enabled=True, figure_offers_enabled=True,
                                 figure_show_me_enabled=True)
    block = report["figures"]["show_me"]
    assert block["requests"] == 4 and block["by_origin"] == {"show_me": 4} and block["joint"] == 1
    assert block["grounding"] == {"retrieved": 2, "none": 1, "anchor": 1} and block["abstentions"] == 1
    assert block["goal_by"] == {"learner": 4}
    assert block["built"] == {"illustrative": 2, "unsupported": 1}
    assert block["unsupported_by_kind"] == {"3-D surface": 1}
    assert block["not_right"] == 1 and block["not_right_rate"] == round(1 / 3, 4)
    assert GOAL not in json.dumps(report)
    off = build_reader_report(repository.sqlite_path, figures_enabled=True, figure_offers_enabled=True)
    assert "show_me" not in off["figures"]
