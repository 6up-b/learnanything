"""The RD3 adversarial review's backend findings (spec_reader_workbench_v2 §3.4, §8.6, §9.3), each held by a test:
jobs belong to one vault and one epoch; a closed epoch never wakes the context's workers; where a question was asked
is recorded as the question is and a failed write heals; request ids are remembered apart from results; running jobs
and kept results are bounded; nested receipts name their job; every search supersedes; note results open their note;
an unrun search by meaning says why."""

from __future__ import annotations

import json
import threading
from contextlib import closing
from typing import Any

import pytest

from learnloop.db.connection import connect
from learnloop_sidecar import polled_jobs as PJ
from learnloop_sidecar.errors import SidecarError
from tests.companion_rd3a_helpers import (WAIT, HeldTutor, ask_params, hold_before_the_tutor, job_of, seed_desk,
                                         wait_job, workbench_contexts)
from tests.desk_helpers import seed_annotation
from tests.reading_path_fixtures import call


@pytest.fixture
def workbench(tmp_path, monkeypatch):
    with workbench_contexts(tmp_path, monkeypatch) as make:
        yield make


def _rows(repository: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _context_row(repository: Any, question_event_id: str) -> tuple[Any, ...] | None:
    found = _rows(repository, "SELECT desk_id, surface, origin FROM companion_exchange_context "
                              "WHERE question_event_id = ?", (question_event_id,))
    return found[0] if found else None


# -- 1: one vault --------------------------------------------------------------------------------------------------


def test_a_job_is_found_only_in_the_vault_it_was_started_in(workbench):
    tutor = HeldTutor(hold=False)
    paths_a, ctx, _repository_a, _spans = workbench(tutor)
    paths_b, _ctx_b, _repository_b, _spans_b = workbench(tutor, name="vault_b")
    call(ctx, "companion.ask", ask_params("req_shared"))
    answered_in_a = wait_job(ctx, "req_shared")
    ctx.load(paths_b.root)
    with pytest.raises(SidecarError) as gone:
        call(ctx, "companion.ask_job", {"requestId": "req_shared"})
    assert gone.value.code == "job_not_found"
    with pytest.raises(SidecarError) as not_cancelled:
        call(ctx, "companion.ask_cancel", {"requestId": "req_shared"})
    assert not_cancelled.value.code == "job_not_found"
    # The same id with another question is this vault's own new request, not a reuse of vault A's.
    call(ctx, "companion.ask", ask_params("req_shared", question="what does a zero determinant mean?"))
    answered_in_b = wait_job(ctx, "req_shared")
    assert answered_in_b["questionEventId"] != answered_in_a["questionEventId"]
    ctx.load(paths_a.root)
    assert call(ctx, "companion.ask_job", {"requestId": "req_shared"})["questionEventId"] == \
        answered_in_a["questionEventId"]


def test_a_vault_switch_ends_the_jobs_epoch_before_its_request_is_sent(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths_a, ctx, _repository, _spans = workbench(tutor)
    paths_b, _ctx_b, _repository_b, _spans_b = workbench(tutor, name="vault_b")
    reached, release = hold_before_the_tutor(monkeypatch)
    call(ctx, "companion.ask", ask_params("req_switch"))
    assert reached.wait(WAIT)
    job = job_of(ctx, "req_switch")
    ctx.load(paths_b.root)
    release.set()
    assert job.done.wait(WAIT)
    job.thread.join(WAIT)
    state = job.state()
    assert (state["status"], state["error"].code) == ("failed", "interrupted")
    assert tutor.prompts == [] and not tutor.entered.is_set()


def _count_wakes(monkeypatch, ctx: Any) -> dict[str, int]:
    import learnloop_sidecar.prefetch_runtime as prefetch

    counts = {"worker": 0, "prefetch": 0}
    original_notify = ctx.post_attempt_worker.notify

    def worker_notify() -> None:
        counts["worker"] += 1
        original_notify()

    def offer(*_args: Any, **_kwargs: Any) -> bool:
        counts["prefetch"] += 1
        return False

    monkeypatch.setattr(ctx.post_attempt_worker, "notify", worker_notify)
    monkeypatch.setattr(prefetch, "notify_offer", offer)
    return counts


def test_a_stale_completion_after_a_vault_switch_touches_nothing_of_the_new_context(workbench, monkeypatch):
    tutor = HeldTutor()
    # Vault B first: each context replaces the tutor provider, and the one made last answers.
    paths_b, _ctx_b, repository_b, _spans_b = workbench(tutor, name="vault_b")
    _paths_a, ctx, repository_a, _spans = workbench(tutor)
    counts = _count_wakes(monkeypatch, ctx)
    call(ctx, "companion.ask", ask_params("req_stale"))
    assert tutor.entered.wait(WAIT)  # the request was sent before the switch: it finishes
    job = job_of(ctx, "req_stale")
    ctx.load(paths_b.root)
    tutor.release.set()
    assert job.done.wait(WAIT)
    job.thread.join(WAIT)
    question_event_id = job.state()["notes"]["question_event_id"]
    assert counts == {"worker": 0, "prefetch": 0}
    # The exchange and its gap reading stay in vault A; vault B gains nothing.
    assert _rows(repository_a, "SELECT COUNT(*) FROM learner_text_gap_jobs WHERE source_id = ?",
                 (question_event_id,)) == [(1,)]
    assert _rows(repository_b, "SELECT COUNT(*) FROM question_events") == [(0,)]


# -- 2: a closed epoch wakes nothing -------------------------------------------------------------------------------


def test_an_answer_finishing_after_the_close_restarts_no_worker(workbench, monkeypatch):
    tutor = HeldTutor()
    _paths, ctx, _repository, _spans = workbench(tutor)
    counts = _count_wakes(monkeypatch, ctx)
    call(ctx, "companion.ask", ask_params("req_closed"))
    assert tutor.entered.wait(WAIT)
    job = job_of(ctx, "req_closed")
    ctx.close()  # its bounded joins return while the answer is still held
    assert job.thread.is_alive()
    tutor.release.set()
    assert job.done.wait(WAIT)
    job.thread.join(WAIT)
    assert job.state()["status"] == "done"  # the exchange is kept
    assert counts == {"worker": 0, "prefetch": 0} and not ctx.post_attempt_worker.running


# -- 8: the context is written with the question -------------------------------------------------------------------


def test_a_failed_answer_keeps_where_its_question_was_asked(workbench):
    tutor = HeldTutor(hold=False, fail=TimeoutError("offline"))
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    call(ctx, "companion.ask", ask_params("req_failed", surface="desk", deskId="d1"))
    final = wait_job(ctx, "req_failed")
    assert final["status"] == "failed" and final["questionEventId"] and final["contextRecorded"] is True
    assert _context_row(repository, final["questionEventId"]) == ("d1", "desk", "live")
    history = call(ctx, "companion.history", {"deskId": "d1"})
    listed = [exchange for day in history["days"] for desk in day["desks"] for exchange in desk["exchanges"]]
    assert [(exchange["questionEventId"], exchange["origin"]) for exchange in listed] == [
        (final["questionEventId"], "live")]


def test_a_question_cancelled_before_sending_keeps_its_desk(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    from learnloop.tutor import tutor_qa

    asked = threading.Event()
    release = threading.Event()
    original = tutor_qa.request_tutor_answer

    def held(*args: Any, **kwargs: Any) -> Any:
        asked.set()
        assert release.wait(WAIT)
        return original(*args, **kwargs)

    monkeypatch.setattr(tutor_qa, "request_tutor_answer", held)
    call(ctx, "companion.ask", ask_params("req_unsent", surface="desk", deskId="d1"))
    assert asked.wait(WAIT)  # the question is recorded; its answer is not asked for yet
    cancelled = call(ctx, "companion.ask_cancel", {"requestId": "req_unsent"})
    assert cancelled["sent"] is False and cancelled["questionEventId"]
    assert _context_row(repository, cancelled["questionEventId"]) == ("d1", "desk", "live")
    release.set()
    final = wait_job(ctx, "req_unsent")
    assert (final["status"], final["sent"], final["kept"]) == ("cancelled", False, False)
    assert tutor.prompts == []


def test_a_context_write_that_failed_is_retried_and_reported_until_it_lands(workbench, monkeypatch):
    import learnloop_sidecar.handlers.companion_ask as handler

    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    original = handler.record_exchange_context
    failing = {"left": 4}

    def flaky(*args: Any, **kwargs: Any) -> bool:
        if failing["left"]:
            failing["left"] -= 1
            raise RuntimeError("disk full")
        return original(*args, **kwargs)

    monkeypatch.setattr(handler, "record_exchange_context", flaky)
    call(ctx, "companion.ask", ask_params("req_flaky", surface="desk", deskId="d1"))
    # The write as the question was recorded, the two at the job's end and this first poll's retry all fail.
    first = wait_job(ctx, "req_flaky")
    assert first["status"] == "done" and first["contextRecorded"] is False
    assert _context_row(repository, first["questionEventId"]) is None
    healed = call(ctx, "companion.ask_job", {"requestId": "req_flaky"})
    assert healed["contextRecorded"] is True
    assert _context_row(repository, first["questionEventId"]) == ("d1", "desk", "live")


# -- 9, 10: ids remembered apart from results; bounded work --------------------------------------------------------


def test_a_request_id_is_remembered_after_its_result_is_dropped(workbench):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    ctx.companion_ask_jobs = PJ.PolledJobs(kept=1, remember_ids=True)
    call(ctx, "companion.ask", ask_params("req_old"))
    wait_job(ctx, "req_old")
    for index in range(3):
        call(ctx, "companion.ask", ask_params(f"req_new_{index}", question=f"question number {index}?"))
        wait_job(ctx, f"req_new_{index}")
    assert job_of(ctx, "req_old") is None
    with pytest.raises(SidecarError) as reused:
        call(ctx, "companion.ask", ask_params("req_old", question="a different question?"))
    assert reused.value.code == "request_reused"
    assert call(ctx, "companion.ask", ask_params("req_old"))["status"] == "expired"
    assert len(tutor.prompts) == 4


def test_a_full_record_of_ids_refuses_a_new_id_rather_than_forget_one(workbench):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    ctx.companion_ask_jobs = PJ.PolledJobs(kept=1, remember_ids=True, remembered=2)
    for request_id in ("req_1", "req_2"):
        call(ctx, "companion.ask", ask_params(request_id, question=f"{request_id}?"))
        wait_job(ctx, request_id)
    with pytest.raises(SidecarError) as full:
        call(ctx, "companion.ask", ask_params("req_3"))
    assert full.value.code == "request_ids_full"
    assert call(ctx, "companion.ask", ask_params("req_1", question="req_1?"))["status"] == "expired"


def test_running_asks_are_bounded(workbench):
    tutor = HeldTutor()
    _paths, ctx, _repository, _spans = workbench(tutor)
    ctx.companion_ask_jobs = PJ.PolledJobs(running=1, remember_ids=True)
    call(ctx, "companion.ask", ask_params("req_running"))
    assert tutor.entered.wait(WAIT)
    with pytest.raises(SidecarError) as busy:
        call(ctx, "companion.ask", ask_params("req_waiting", question="another?"))
    assert (busy.value.code, busy.value.retryable) == ("jobs_busy", True)
    tutor.release.set()
    wait_job(ctx, "req_running")
    tutor.hold = False
    call(ctx, "companion.ask", ask_params("req_waiting", question="another?"))
    assert wait_job(ctx, "req_waiting")["status"] == "done"


def test_results_are_pruned_as_jobs_finish_not_only_when_the_next_starts(workbench):
    tutor = HeldTutor()
    _paths, ctx, _repository, _spans = workbench(tutor)
    ctx.companion_ask_jobs = PJ.PolledJobs(kept=1, running=2, remember_ids=True)
    call(ctx, "companion.ask", ask_params("req_one"))
    call(ctx, "companion.ask", ask_params("req_two", question="two?"))
    assert ctx.companion_ask_jobs.kept_count() == 2  # both running: neither is dropped
    jobs = [job_of(ctx, "req_one"), job_of(ctx, "req_two")]
    tutor.release.set()
    for job in jobs:
        assert job.done.wait(WAIT)
        job.thread.join(WAIT)
    # Both finished and no third job started: the older result went as the later one finished.
    assert ctx.companion_ask_jobs.kept_count() == 1


# -- 16: nested receipts name their job ----------------------------------------------------------------------------


class _Embedder:
    provider_name = "fake_embedder"
    provider_type = "fake"
    model = "fake-embedding"


def test_a_receipt_a_nested_recorder_owns_still_names_the_job(workbench, monkeypatch):
    import learnloop.source_retrieval.library as library
    from learnloop.ai.execution import model_call, record_model_calls

    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    real = library.search_library

    def deep_with_its_own_recorder(vault: Any, repo: Any, *, query: str, limit: int = 40, deep: bool = False,
                                   **kwargs: Any) -> dict[str, Any]:
        if deep:
            # As the query embedding does: its own recorder, replacing the job's for this call.
            with record_model_calls(repo, owner_kind="library_search", owner_id="library"), \
                    model_call(_Embedder(), purpose="query_embedding", prompt="q"):
                pass
            words = real(vault, repo, query=query, limit=limit, deep=False)["hits"]
            return {"hits": [{**hit, "matched_by": ["meaning"]} for hit in words], "basis": "meaning"}
        return real(vault, repo, query=query, limit=limit, deep=False, **kwargs)

    monkeypatch.setattr(library, "search_library", deep_with_its_own_recorder)
    monkeypatch.setattr(library, "meaning_search_state", lambda *args, **kwargs: {
        "status": "ready", "reason": None, "sources": 2, "sources_covered": 2, "blocks": 1, "blocks_covered": 1})
    reply = call(ctx, "search.everything", {"query": "determinant", "scopes": ["passages"]})
    job_id = reply["meaning"]["jobId"]
    wait_job(ctx, job_id, method="search.job")
    receipts = _rows(repository, "SELECT owner_kind, owner_id, budget_json FROM model_call_receipts "
                                 "WHERE purpose = 'query_embedding'")
    assert len(receipts) == 1  # one row, never a duplicate for the job
    owner_kind, owner_id, budget_json = receipts[0]
    assert (owner_kind, owner_id) == ("library_search", "library")
    assert json.loads(budget_json)["owning_job"] == f"search.meaning:{job_id}"


# -- 18, 19: supersede on every return; more before the cap --------------------------------------------------------


class _HeldDeep:
    def __init__(self, real: Any) -> None:
        self.real = real
        self.entered = threading.Event()
        self.release = threading.Event()

    def __call__(self, vault: Any, repository: Any, *, query: str, limit: int = 40, deep: bool = False,
                 **kwargs: Any) -> dict[str, Any]:
        if not deep:
            return self.real(vault, repository, query=query, limit=limit, deep=False, **kwargs)
        self.entered.set()
        assert self.release.wait(WAIT)
        hits = self.real(vault, repository, query=query, limit=limit, deep=False)["hits"]
        return {"hits": [{**hit, "matched_by": ["meaning"], "span_id": f"m_{hit['span_id']}"} for hit in hits],
                "basis": "meaning"}


@pytest.mark.parametrize("newer", [{"query": "determinant", "scopes": ["pads"]}, {"query": "d"}])
def test_every_newer_search_from_the_desk_supersedes_the_running_one(workbench, monkeypatch, newer):
    import learnloop.source_retrieval.library as library

    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    seed_desk(ctx)
    held = _HeldDeep(library.search_library)
    monkeypatch.setattr(library, "search_library", held)
    monkeypatch.setattr(library, "meaning_search_state", lambda *args, **kwargs: {
        "status": "ready", "reason": None, "sources": 2, "sources_covered": 2, "blocks": 1, "blocks_covered": 1})
    first = call(ctx, "search.everything", {"query": "determinant", "deskId": "d1", "scopes": ["passages"]})
    assert held.entered.wait(WAIT)
    call(ctx, "search.everything", {**newer, "deskId": "d1"})
    held.release.set()
    older = wait_job(ctx, first["meaning"]["jobId"], method="search.job")
    assert (older["status"], older["groups"]) == ("cancelled", [])


def _notes_double(monkeypatch, hits: list[dict[str, Any]], *, meaning: dict[str, Any] | None = None,
                  by_words: list[dict[str, Any]] | None = None) -> None:
    """The vault notes' search as a double: ``hits`` by meaning, and by words ``by_words`` (``hits`` when
    not given)."""

    import learnloop_sidecar.handlers.notes as notes

    def found(_ctx: Any, _vault: Any, _repository: Any, *, query: str, mode: str) -> dict[str, Any]:
        if mode == "words":
            return {"hits": hits if by_words is None else by_words, "basis": mode, "meaning": None}
        return {"hits": hits, "basis": mode, "meaning": meaning}

    monkeypatch.setattr(notes, "search_vault_notes", found)


def test_more_notes_than_the_group_shows_says_there_are_more(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    _notes_double(monkeypatch, [{"note_key": f"capture:c{index}", "title": "inbox", "heading": "", "snippet": "x",
                                 "captured_on": None, "extraction_id": None, "span_id": None} for index in range(20)])
    notes = {entry["group"]: entry for entry in call(ctx, "search.everything", {
        "query": "zzz unmatched words", "scopes": ["notes"]})["groups"]}["notes"]
    assert len(notes["rows"]) == 12 and notes["more"] is True


# -- 7: note results open their note -------------------------------------------------------------------------------


def test_a_reader_note_opens_at_its_passage_and_a_capture_note_names_itself(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_annotation(repository, annotation_id="ann_1", source_id="src_text", revision_id="rev_text",
                    extraction_id="ext_text", span_id="t3", text="my eigenspace remark")
    rows = {entry["group"]: entry for entry in call(ctx, "search.everything", {
        "query": "eigenspace remark", "scopes": ["notes"]})["groups"]}["notes"]["rows"]
    [note] = [row for row in rows if row.get("noteKey") == "annotation:ann_1"]
    assert note["ref"] == {"kind": "source", "sourceId": "src_text", "extractionId": "ext_text"}
    assert note["target"] == {"noteKey": "annotation:ann_1", "annotationId": "ann_1", "spanId": "t3"}

    _notes_double(monkeypatch, [{"note_key": "capture:cap_9", "title": "inbox", "heading": "", "snippet": "y",
                                 "captured_on": "2026-11-20", "extraction_id": None, "span_id": None}])
    [capture] = {entry["group"]: entry for entry in call(ctx, "search.everything", {
        "query": "anything", "scopes": ["notes"]})["groups"]}["notes"]["rows"]
    assert capture["ref"] == {"kind": "panel", "panel": "notes"}
    assert capture["target"] == {"noteKey": "capture:cap_9", "captureId": "cap_9"}


# -- 13: an unrun search by meaning says why -----------------------------------------------------------------------


def _meaning_on(monkeypatch, deep_pass: Any) -> None:
    import learnloop.source_retrieval.library as library
    import learnloop_sidecar.handlers.notes as notes

    real = library.search_library

    def library_search(vault: Any, repository: Any, *, query: str, limit: int = 40, deep: bool = False,
                       **kwargs: Any) -> dict[str, Any]:
        if not deep:
            return real(vault, repository, query=query, limit=limit, deep=False, **kwargs)
        return deep_pass(vault, repository, query)

    monkeypatch.setattr(library, "search_library", library_search)
    monkeypatch.setattr(library, "meaning_search_state", lambda *args, **kwargs: {
        "status": "ready", "reason": None, "sources": 2, "sources_covered": 2, "blocks": 1, "blocks_covered": 1})
    monkeypatch.setattr(notes, "notes_search_state", lambda vault: {"on": True, "meaning": True, "reason": None})


def test_an_unrun_search_by_meaning_is_said_per_group_never_shown_as_nothing_found(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    _meaning_on(monkeypatch, lambda *_args: {"hits": [], "basis": "keyword", "retrieval": {
        "query_embedding": {"status": "failed", "reason": "the embedding route is not ready"}}})
    _notes_double(monkeypatch, [], meaning={"status": "unavailable", "reason": "the query could not be embedded",
                                            "covered": 0, "total": 3})
    reply = call(ctx, "search.everything", {"query": "determinant", "scopes": ["passages", "notes", "pads"]})
    done = wait_job(ctx, reply["meaning"]["jobId"], method="search.job")
    groups = {entry["group"]: entry for entry in done["groups"]}
    assert (groups["passages"]["status"], groups["passages"]["reason"]) == (
        "unavailable", "Couldn’t search for similar passages. Try word matches.")
    assert (groups["notes"]["status"], groups["notes"]["reason"]) == ("unavailable", "Couldn’t search for similar notes. Try word matches.")
    # The groups that never had a meaning search still say why, on the job's poll too.
    assert [entry["group"] for entry in done["unavailable"]] == ["pads"]


def test_a_group_whose_search_by_meaning_fails_says_so_and_the_other_group_still_answers(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)

    def broken(*_args: Any) -> dict[str, Any]:
        raise RuntimeError("index file unreadable")

    _meaning_on(monkeypatch, broken)
    _notes_double(monkeypatch, [{"note_key": "capture:c1", "title": "inbox", "heading": "", "snippet": "z",
                                 "captured_on": None, "extraction_id": None, "span_id": None}],
                  meaning={"status": "ready", "reason": None, "covered": 1, "total": 1}, by_words=[])
    reply = call(ctx, "search.everything", {"query": "determinant zz", "scopes": ["passages", "notes"]})
    done = wait_job(ctx, reply["meaning"]["jobId"], method="search.job")
    groups = {entry["group"]: entry for entry in done["groups"]}
    assert done["status"] == "done" and groups["passages"]["status"] == "failed" and groups["passages"]["reason"]
    assert groups["notes"]["status"] == "ok" and [row["noteKey"] for row in groups["notes"]["rows"]] == ["capture:c1"]
