"""``search.everything`` and ``search.job`` (spec_reader_workbench_v2 §3.4, §9.3): the groups found by the
learner's words come back at once, bounded; the search by meaning runs as a job where the vault can search
by meaning and says why not where it cannot; a newer search from the same desk supersedes an older one."""

from __future__ import annotations

import threading
from typing import Any

import pytest
from pydantic import ValidationError

from learnloop.db.repositories import Repository
from learnloop_sidecar.errors import SidecarError
from tests.companion_rd3a_helpers import WAIT, HeldTutor, ask_params, seed_desk, seed_pad, settle_gap_readings, wait_job, workbench_contexts
from tests.desk_helpers import seed_gap, seed_reading
from tests.reading_path_fixtures import call

SEARCH_RPCS = ("search.everything", "search.job")
GROUPS = ["sources", "passages", "notes", "pads", "threads", "exchanges"]



@pytest.fixture
def workbench(tmp_path, monkeypatch):
    with workbench_contexts(tmp_path, monkeypatch) as make:
        yield make

def _groups(reply: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["group"]: entry for entry in reply["groups"]}


@pytest.fixture
def searchable(workbench, monkeypatch):
    """The library vault with one answered Reader exchange, a desk on the text, a pad and a gap reading."""

    tutor = HeldTutor(hold=False, answer_md="Swapping two rows flips the sign of the determinant.")
    paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    call(ctx, "companion.ask", ask_params("req_seed", surface="desk", deskId="d1"))
    exchange = wait_job(ctx, "req_seed")
    seed_pad(ctx, blocks={"b1": "My note: the determinant is multiplicative.", "b2": "unrelated"}, desk_id="d1",
             seq=3)
    # The answer queued its question's gap reading: wait for it first, so the tests read a vault nothing writes to
    # and a gap seeded here never races the pipeline's own row for the same question.
    settle_gap_readings(ctx)
    with repository.connection() as connection:
        seed_gap(connection, gap_id="gap_1", source_kind="stuck_answer", source_id="att_1")
        if connection.execute("SELECT 1 FROM learner_text_gaps WHERE source_kind = 'tutor_question'").fetchone() is None:
            seed_gap(connection, gap_id="gap_2", source_kind="tutor_question", source_id=exchange["questionEventId"])
        connection.commit()
    return ctx, repository, exchange


def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.search import SEARCH_RPCS as REGISTERED
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert REGISTERED == SEARCH_RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in SEARCH_RPCS)
    for name, minimal in (("search.everything", {"query": "det"}), ("search.job", {"jobId": "j"})):
        model = METHOD_REGISTRY[name].params_model
        model.model_validate(minimal)
        with pytest.raises(ValidationError):
            model.model_validate({**minimal, "unexpected": True})
    model = METHOD_REGISTRY["search.everything"].params_model
    with pytest.raises(ValidationError):
        model.model_validate({"query": "det", "scopes": ["everything"]})
    with pytest.raises(ValidationError):
        model.model_validate({"query": "x" * 201})


def test_the_word_groups_come_back_at_once_each_naming_what_to_open(searchable):
    ctx, repository, exchange = searchable
    reply = call(ctx, "search.everything", {"query": "determinant", "deskId": "d1"})
    assert reply["version"] == 1 and reply["query"] == "determinant"
    groups = _groups(reply)
    assert list(groups) == GROUPS and all(entry["basis"] == "words" for entry in reply["groups"])

    passages = groups["passages"]["rows"]
    assert passages and all(row["ref"]["kind"] == "source" and row["target"]["spanId"] == row["spanId"]
                            for row in passages)
    pad = groups["pads"]["rows"]
    assert [(row["blockId"], row["onThisDesk"], row["handwriting"]) for row in pad] == [("b1", True, False)]
    assert pad[0]["ref"] == {"kind": "pad", "padId": "p1"} and pad[0]["target"] == {"blockId": "b1"}

    answer_event = exchange["answer"]["readerAnswerEventId"]
    threads = groups["threads"]["rows"]
    assert [(row["questionEventId"], row["exchangeId"], row["rootExchangeId"]) for row in threads] == [
        (exchange["questionEventId"], answer_event, answer_event)]
    assert threads[0]["ref"] == {"kind": "thread", "rootExchangeId": answer_event}
    assert threads[0]["target"] == {"spanId": "t3"}
    past = groups["exchanges"]["rows"]
    assert [(row["questionEventId"], row["deskId"], row["where"]) for row in past] == [
        (exchange["questionEventId"], "d1", "on a desk")]

    # A gap reading of the learner's words shows in the notes group only when no other group shows them.
    assert all(row.get("sourceKind") != "tutor_question" for row in groups["notes"]["rows"])
    assert groups["sources"]["rows"] == [] and groups["sources"]["more"] is False


def test_sources_by_title_say_which_desks_they_are_open_on(searchable):
    ctx, _repository, _exchange = searchable
    sources = _groups(call(ctx, "search.everything", {"query": "matrix theory", "deskId": "d1"}))["sources"]["rows"]
    assert [(row["sourceId"], row["openOnDeskIds"], row["onThisDesk"]) for row in sources] == [
        ("src_text", ["d1"], True)]
    assert sources[0]["ref"] == {"kind": "source", "sourceId": "src_text", "extractionId": "ext_text"}


def test_the_notes_group_holds_the_gap_readings_of_the_learners_own_words(searchable):
    ctx, _repository, _exchange = searchable
    notes = _groups(call(ctx, "search.everything", {"query": "the inverse", "scopes": ["notes"]}))["notes"]
    assert [(row["noteKind"], row["gapId"], row["sourceKind"]) for row in notes["rows"]] == [
        ("gap_reading", "gap_1", "stuck_answer")]


def test_a_video_passage_opens_at_its_cue(searchable):
    ctx, repository, _exchange = searchable
    seed_reading(repository, source_id="src_video", revision_id="rev_video", extraction_id="ext_video",
                 spans=["c1", "c2"], texts={"c2": "Here the eigenvalue appears on screen."}, timed=True)
    rows = _groups(call(ctx, "search.everything", {"query": "eigenvalue appears", "scopes": ["passages"]}))[
        "passages"]["rows"]
    video = [row for row in rows if row["extractionId"] == "ext_video"]
    assert [(row["ref"], row["target"]) for row in video] == [
        ({"kind": "video", "sourceId": "src_video", "extractionId": "ext_video", "t": 10.0},
         {"spanId": "c2", "t": 10.0})]


def test_every_group_is_bounded_and_says_there_is_more(searchable):
    ctx, _repository, _exchange = searchable
    seed_pad(ctx, pad_id="p2", blocks={f"x{index}": f"eigen line {index}" for index in range(15)}, seq=4)
    pads = _groups(call(ctx, "search.everything", {"query": "eigen line", "scopes": ["pads"]}))["pads"]
    assert len(pads["rows"]) == 12 and pads["more"] is True


def test_with_embeddings_off_nothing_runs_by_meaning_and_each_group_says_why(searchable):
    ctx, _repository, _exchange = searchable
    reply = call(ctx, "search.everything", {"query": "determinant", "deskId": "d1"})
    meaning = reply["meaning"]
    assert meaning["status"] == "unavailable" and meaning["jobId"] is None
    reasons = {entry["group"]: entry["reason"] for entry in meaning["unavailable"]}
    assert set(reasons) == {"passages", "notes", "pads", "threads", "exchanges"}
    assert reasons["passages"] == "Similar-passage search is unavailable. Word search is available."
    assert reasons["pads"] == "Pads are searched by word matches."
    assert getattr(ctx, "search_jobs", None) is None or not ctx.search_jobs._jobs


def test_a_query_too_short_searches_nothing(searchable):
    ctx, _repository, _exchange = searchable
    reply = call(ctx, "search.everything", {"query": " d "})
    assert reply["groups"] == [] and reply["meaning"]["status"] == "unavailable"


def test_an_unknown_desk_is_refused(searchable):
    ctx, _repository, _exchange = searchable
    with pytest.raises(SidecarError) as refused:
        call(ctx, "search.everything", {"query": "determinant", "deskId": "nope"})
    assert refused.value.code == "desk_not_found"
    with pytest.raises(SidecarError) as gone:
        call(ctx, "search.job", {"jobId": "srch_never"})
    assert gone.value.code == "job_not_found"


class _MeaningLibrary:
    """The library search's deep pass as a double: a passage the words found again plus one only meaning
    found; held on the first deep call while ``hold`` is set. The words' pass is the real search."""

    def __init__(self, real: Any, *, hold: bool = False) -> None:
        self.real = real
        self.hold = hold
        self.entered = threading.Event()
        self.release = threading.Event()
        self.deep_calls = 0

    def __call__(self, vault: Any, repository: Any, *, query: str, limit: int = 40, deep: bool = False,
                 **kwargs: Any) -> dict[str, Any]:
        if not deep:
            return self.real(vault, repository, query=query, limit=limit, deep=False, **kwargs)
        self.deep_calls += 1
        if self.hold and self.deep_calls == 1:
            self.entered.set()
            assert self.release.wait(WAIT)
        words = self.real(vault, repository, query=query, limit=limit, deep=False)["hits"]
        again = {**words[0], "matched_by": ["keyword", "meaning"]}
        found = {"source_id": "src_text", "source_title": "Matrix Theory", "extraction_id": "ext_text",
                 "span_id": "t1", "section": None, "page": 1, "snippet": "by meaning", "matched_by": ["meaning"]}
        return {"hits": [again, found], "basis": "keyword+meaning"}


def _meaning_ready(monkeypatch, double: _MeaningLibrary) -> None:
    import learnloop.source_retrieval.library as library

    monkeypatch.setattr(library, "search_library", double)
    monkeypatch.setattr(library, "meaning_search_state", lambda *args, **kwargs: {
        "status": "ready", "reason": None, "sources": 2, "sources_covered": 2, "blocks": 1, "blocks_covered": 1})


def test_the_meaning_job_adds_only_what_the_words_did_not_find(searchable, monkeypatch):
    import learnloop.source_retrieval.library as library

    ctx, _repository, _exchange = searchable
    double = _MeaningLibrary(library.search_library)
    _meaning_ready(monkeypatch, double)
    reply = call(ctx, "search.everything", {"query": "determinant", "deskId": "d1", "scopes": ["passages", "pads"]})
    assert reply["meaning"]["status"] == "pending" and reply["meaning"]["groups"] == ["passages"]
    assert [entry["group"] for entry in reply["meaning"]["unavailable"]] == ["pads"]
    done = wait_job(ctx, reply["meaning"]["jobId"], method="search.job")
    assert done["status"] == "done" and done["done"] is True
    [passages] = done["groups"]
    assert passages["basis"] == "meaning" and passages["retrievalBasis"] == "keyword+meaning"
    assert [(row["spanId"], row["byMeaning"]) for row in passages["rows"]] == [("t1", True)]


def test_a_newer_search_from_the_desk_supersedes_the_older_job(searchable, monkeypatch):
    import learnloop.source_retrieval.library as library

    ctx, _repository, _exchange = searchable
    double = _MeaningLibrary(library.search_library, hold=True)
    _meaning_ready(monkeypatch, double)
    first = call(ctx, "search.everything", {"query": "determinant", "deskId": "d1", "scopes": ["passages"]})
    assert double.entered.wait(WAIT)
    second = call(ctx, "search.everything", {"query": "determinants", "deskId": "d1", "scopes": ["passages"]})
    older = call(ctx, "search.job", {"jobId": first["meaning"]["jobId"]})
    assert older["status"] == "cancelled" and older["groups"] == []
    double.release.set()
    assert wait_job(ctx, first["meaning"]["jobId"], method="search.job")["groups"] == []
    newer = wait_job(ctx, second["meaning"]["jobId"], method="search.job")
    assert newer["status"] == "done" and newer["groups"][0]["rows"]


def test_waiting_for_the_ok_to_use_ai_runs_nothing_by_meaning(searchable, monkeypatch):
    import learnloop.ai.model_use as model_use
    import learnloop.source_retrieval.library as library

    ctx, _repository, _exchange = searchable
    double = _MeaningLibrary(library.search_library)
    _meaning_ready(monkeypatch, double)
    monkeypatch.setattr(model_use, "waiting", lambda *args, **kwargs: True)
    reply = call(ctx, "search.everything", {"query": "determinant", "scopes": ["passages"]})
    assert reply["meaning"]["status"] == "unavailable" and double.deep_calls == 0
    assert {"group": "passages", "reason": "waiting for your OK to use AI"} in reply["meaning"]["unavailable"]
    assert _groups(reply)["passages"]["rows"]  # the words still answer


def test_searching_by_words_writes_nothing(searchable):
    from tests.reading_path_fixtures import table_counts

    ctx, repository, _exchange = searchable
    before = table_counts(Repository.attach(repository.sqlite_path))
    call(ctx, "search.everything", {"query": "determinant", "deskId": "d1"})
    assert table_counts(Repository.attach(repository.sqlite_path)) == before
