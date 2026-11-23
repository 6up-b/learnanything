"""``companion.ask`` as a polled job (spec_reader_workbench_v2 §3.4, §8.6; review F8): the model call runs
outside the sidecar's serial loop, the request id makes it idempotent, polling and cancellation are honest,
the exchange's context is recorded and its passages are written through as a rebuild writes them, and
``reader.ask`` answers from the same core."""

from __future__ import annotations

import io
import json
import os
import queue
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, closing, contextmanager
from typing import Any

import pytest
from pydantic import ValidationError

from learnloop.db.connection import connect
from learnloop.substrate.passage_spans import rebuild_question_event_spans
from learnloop_sidecar.errors import SidecarError
from tests.companion_rd3a_helpers import WAIT, HeldTutor, ask_params, seed_desk, seed_pad, wait_job, workbench_contexts
from tests.reading_path_fixtures import call

COMPANION_ASK_RPCS = ("companion.ask", "companion.ask_job", "companion.ask_cancel")



@pytest.fixture
def workbench(tmp_path, monkeypatch):
    with workbench_contexts(tmp_path, monkeypatch) as make:
        yield make

def _rows(repository: Any, sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        return [tuple(row) for row in connection.execute(sql, params).fetchall()]


def _question_count(repository: Any) -> int:
    return _rows(repository, "SELECT COUNT(*) FROM question_events")[0][0]


def test_the_rpcs_are_registered_desktop_only_and_refuse_extra_fields():
    from learnloop.companion.asks import ASK_SURFACES
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_sidecar.handlers.companion_ask import COMPANION_ASK_RPCS as REGISTERED
    from learnloop_sidecar.handlers.companion_ask import CompanionAskInput
    from learnloop_sidecar.registry import METHOD_REGISTRY

    assert REGISTERED == COMPANION_ASK_RPCS
    assert all(name in METHOD_REGISTRY and name not in ALLOWLIST for name in COMPANION_ASK_RPCS)
    for name, minimal in (("companion.ask", ask_params()), ("companion.ask_job", {"requestId": "r"}),
                          ("companion.ask_cancel", {"requestId": "r"})):
        model = METHOD_REGISTRY[name].params_model
        model.model_validate(minimal)
        with pytest.raises(ValidationError):
            model.model_validate({**minimal, "unexpected": True})
    # The surfaces the params accept are the ones the context reader knows.
    assert set(CompanionAskInput.model_fields["surface"].annotation.__args__) == set(ASK_SURFACES)
    with pytest.raises(ValidationError):
        CompanionAskInput.model_validate(ask_params(surface="phone"))


class _Lines:
    """The serial loop's stdout, read line by line on a thread so a test can wait with a timeout."""

    def __init__(self, stream: Any) -> None:
        self.lines: queue.Queue[str] = queue.Queue()
        self.pump = threading.Thread(target=self._pump, args=(stream,), daemon=True)
        self.pump.start()

    def _pump(self, stream: Any) -> None:
        for line in stream:
            self.lines.put(line)

    def next(self, timeout: float) -> dict[str, Any]:
        return json.loads(self.lines.get(timeout=timeout))


@contextmanager
def _serial_loop() -> Iterator[tuple[Callable[[int, str, dict[str, Any]], None], _Lines]]:
    """``server.serve`` on a pair of pipes: yields a sender and the replies; at exit the input ends (EOF) and the
    loop is joined."""

    from learnloop_sidecar.server import serve

    in_read, in_write = os.pipe()
    out_read, out_write = os.pipe()
    with ExitStack() as files:
        # Closed in reverse: the loop's stdout first, so the reply pump reads its end before its pipe is closed
        # (closing a reader another thread is blocked in waits on that reader's lock).
        replies = _Lines(files.enter_context(io.open(out_read, "r", encoding="utf-8")))
        stdin = files.enter_context(io.open(in_read, "r", encoding="utf-8"))
        writer = files.enter_context(io.open(in_write, "w", encoding="utf-8"))
        stdout = files.enter_context(io.open(out_write, "w", encoding="utf-8"))
        loop = threading.Thread(target=serve, args=(stdin, stdout), daemon=True)
        loop.start()

        def send(request_id: int, method: str, params: dict[str, Any]) -> None:
            writer.write(json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}) + "\n")
            writer.flush()

        try:
            yield send, replies
        finally:
            writer.close()
            loop.join(WAIT)
        assert not loop.is_alive()
    # The loop's stdout is closed: the pump reads its end and returns.
    replies.pump.join(WAIT)
    assert not replies.pump.is_alive()


def test_a_second_rpc_is_served_while_a_generation_is_held(workbench, monkeypatch):
    """The mutex proof: the real serial loop (``server.serve``) answers ``companion.ask`` with its job, then
    serves ``desk.state`` and a poll, all while the tutor's model request is held inside ``complete``."""

    tutor = HeldTutor()
    paths, _ctx, _repository, _spans = workbench(tutor)
    with _serial_loop() as (send, replies):
        try:
            send(1, "initialize", {"vaultPath": str(paths.root)})
            assert "result" in replies.next(WAIT)
            send(2, "companion.ask", ask_params("req_held"))
            started = replies.next(5.0)["result"]
            assert started["status"] in ("queued", "running") and started["done"] is False
            assert tutor.entered.wait(WAIT)  # the model request is in flight
            send(3, "desk.state", {})
            state = replies.next(5.0)
            assert "result" in state and tutor.inside.is_set(), "desk.state waited for the held generation"
            send(4, "companion.ask_job", {"requestId": "req_held"})
            polled = replies.next(5.0)["result"]
            assert tutor.inside.is_set()
            assert (polled["status"], polled["done"], polled["partialMd"], polled["citations"]) == (
                "running", False, "", [])
        finally:
            tutor.release.set()
        deadline, polled, number = time.monotonic() + WAIT, {}, 5
        while time.monotonic() < deadline:
            send(number, "companion.ask_job", {"requestId": "req_held"})
            polled = replies.next(5.0)["result"]
            number += 1
            if polled["done"]:
                break
            time.sleep(0.05)
        assert polled["status"] == "done" and polled["partialMd"] == tutor.answer_md
        assert polled["citations"] == polled["answer"]["citations"] and polled["questionEventId"]


def test_the_job_answers_with_the_reader_asks_reply_and_reader_ask_still_answers(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    started = call(ctx, "companion.ask", ask_params("req_core"))
    assert started["requestId"] == "req_core" and started["version"] == 1
    done = wait_job(ctx, "req_core")
    reader = call(ctx, "reader.ask", {key: value for key, value in ask_params().items()
                                      if key not in ("requestId", "surface")})
    # One core: the job's answer is reader.ask's reply, key for key.
    assert set(done["answer"]) == set(reader) - {"version"}
    assert done["answer"]["answerMd"] == reader["answerMd"] == tutor.answer_md
    assert done["questionEventId"] == done["answer"]["eventId"] and done["kept"] is False
    assert _question_count(repository) == 2 and len(tutor.prompts) == 2


def test_a_repeated_request_id_answers_the_same_job_and_asks_once(workbench, monkeypatch):
    tutor = HeldTutor()
    _paths, ctx, repository, _spans = workbench(tutor)
    first = call(ctx, "companion.ask", ask_params("req_once"))
    assert tutor.entered.wait(WAIT)
    again = call(ctx, "companion.ask", ask_params("req_once"))
    assert again["requestId"] == first["requestId"] and again["status"] == "running"
    with pytest.raises(SidecarError) as reused:
        call(ctx, "companion.ask", ask_params("req_once", question="something else entirely?"))
    assert reused.value.code == "request_reused"
    tutor.release.set()
    done = wait_job(ctx, "req_once")
    after = call(ctx, "companion.ask", ask_params("req_once"))
    assert after == done and len(tutor.prompts) == 1 and _question_count(repository) == 1


def test_a_finished_job_dropped_from_memory_is_answered_as_expired_never_asked_again(workbench):
    from learnloop_sidecar import polled_jobs as PJ

    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    ctx.companion_ask_jobs = PJ.PolledJobs(kept=1)
    call(ctx, "companion.ask", ask_params("req_a"))
    first = wait_job(ctx, "req_a")
    call(ctx, "companion.ask", ask_params("req_b", question="and why is the determinant multiplicative?"))
    wait_job(ctx, "req_b")
    assert ctx.companion_ask_jobs.get("req_a") is None
    expired = call(ctx, "companion.ask", ask_params("req_a"))
    assert (expired["status"], expired["done"], expired["questionEventId"]) == (
        "expired", True, first["questionEventId"])
    assert call(ctx, "companion.ask_job", {"requestId": "req_a"}) == expired
    assert len(tutor.prompts) == 2 and _question_count(repository) == 2


def test_a_failed_generation_is_reported_and_an_unknown_job_is_said_to_be_gone(workbench, monkeypatch):
    tutor = HeldTutor(hold=False, fail=TimeoutError("offline"))
    _paths, ctx, _repository, _spans = workbench(tutor)
    call(ctx, "companion.ask", ask_params("req_fail"))
    failed = wait_job(ctx, "req_fail")
    assert (failed["status"], failed["done"], failed["answer"], failed["partialMd"]) == ("failed", True, None, "")
    assert failed["error"]["code"] == "provider_unavailable" and failed["error"]["retryable"] is True

    tutor.fail = RuntimeError("a defect")
    call(ctx, "companion.ask", ask_params("req_crash", question="and the trace?"))
    crashed = wait_job(ctx, "req_crash")
    assert crashed["status"] == "failed" and crashed["error"]["code"] == "internal"
    with pytest.raises(SidecarError) as gone:
        call(ctx, "companion.ask_job", {"requestId": "never_asked"})
    assert gone.value.code == "job_not_found" and "history" in gone.value.message


def _hold_before_the_tutor(monkeypatch) -> tuple[threading.Event, threading.Event]:
    """Hold the job after its context is read and before the tutor's request is admitted."""

    from learnloop.reader import reader_dialogue as RD

    reached, release = threading.Event(), threading.Event()
    original = RD.build_reader_manifest

    def held(*args: Any, **kwargs: Any) -> Any:
        reached.set()
        assert release.wait(WAIT)
        return original(*args, **kwargs)

    monkeypatch.setattr(RD, "build_reader_manifest", held)
    return reached, release


def test_a_job_cancelled_before_its_request_is_sent_sends_nothing(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    reached, release = _hold_before_the_tutor(monkeypatch)
    call(ctx, "companion.ask", ask_params("req_cancel"))
    assert reached.wait(WAIT)
    cancelled = call(ctx, "companion.ask_cancel", {"requestId": "req_cancel"})
    assert cancelled["status"] == "cancelled" and cancelled["done"] is False  # its thread is still running
    release.set()
    final = wait_job(ctx, "req_cancel")
    assert (final["status"], final["done"], final["answer"], final["kept"]) == ("cancelled", True, None, False)
    assert tutor.prompts == [] and not tutor.entered.is_set()
    # The question the Ask recorded before its call is marked failed, as any unsent answer is.
    assert _rows(repository, "SELECT answer_status FROM question_events") in ([], [("failed",)])


def test_a_job_cancelled_after_its_request_was_sent_keeps_the_exchange(workbench, monkeypatch):
    tutor = HeldTutor()
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    call(ctx, "companion.ask", ask_params("req_late", surface="desk", deskId="d1"))
    assert tutor.entered.wait(WAIT)
    assert call(ctx, "companion.ask_cancel", {"requestId": "req_late"})["status"] == "cancelled"
    tutor.release.set()
    final = wait_job(ctx, "req_late")
    assert (final["status"], final["done"], final["answer"], final["kept"]) == ("cancelled", True, None, True)
    history = call(ctx, "companion.history", {"deskId": "d1"})
    exchanges = [exchange for day in history["days"] for desk in day["desks"] for exchange in desk["exchanges"]]
    assert [exchange["questionEventId"] for exchange in exchanges] == [final["questionEventId"]]
    # Cancelling a finished job changes nothing.
    assert call(ctx, "companion.ask_cancel", {"requestId": "req_late"}) == final


def test_closing_the_context_interrupts_a_job_honestly(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, _repository, _spans = workbench(tutor)
    reached, release = _hold_before_the_tutor(monkeypatch)
    call(ctx, "companion.ask", ask_params("req_closed"))
    assert reached.wait(WAIT)
    ctx.background_jobs.cancel()  # a vault switch or a close ends the epoch the job started in
    release.set()
    final = wait_job(ctx, "req_closed")
    assert (final["status"], final["error"]["code"], final["error"]["retryable"]) == ("failed", "interrupted", True)
    assert tutor.prompts == []


def test_the_exchange_context_is_recorded_and_its_passages_equal_a_rebuild(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    seed_pad(ctx, blocks={"b1": "why does swapping flip the sign?"}, desk_id="d1", seq=3)
    call(ctx, "companion.ask", ask_params("req_ctx", surface="desk", deskId="d1", padBlockIds=["b1"]))
    done = wait_job(ctx, "req_ctx")
    question_event_id = done["questionEventId"]
    rows = _rows(repository, "SELECT desk_id, surface, window_spec_json, pad_block_ids_json, goal_id, origin "
                             "FROM companion_exchange_context WHERE question_event_id = ?", (question_event_id,))
    assert len(rows) == 1
    desk_id, surface, window_spec, pad_blocks, goal_id, origin = rows[0]
    assert (desk_id, surface, json.loads(pad_blocks), goal_id, origin) == ("d1", "desk", ["b1"], None, "live")
    assert json.loads(window_spec) == {"window_id": "d1_w1", "kind": "source", "content": {
        "kind": "source", "source_id": "src_text", "extraction_id": "ext_text", "view": "render"}}
    history = call(ctx, "companion.history", {"deskId": "d1"})
    exchange = history["days"][0]["desks"][0]["exchanges"][0]
    assert (exchange["where"], exchange["origin"], exchange["padBlockIds"]) == ("on a desk", "live", ["b1"])

    spans_sql = ("SELECT question_event_id, extraction_id, span_id, role, quality FROM question_event_spans "
                 "ORDER BY question_event_id, extraction_id, span_id, role")
    live = _rows(repository, spans_sql)
    assert any(row[0] == question_event_id and row[3] == "selection" for row in live)
    vault, _ = ctx.require_vault()
    rebuild_question_event_spans(vault, repository)
    assert _rows(repository, spans_sql) == live


def test_refusals_come_back_on_the_request_and_start_no_job(workbench, monkeypatch):
    tutor = HeldTutor(hold=False)
    _paths, ctx, repository, _spans = workbench(tutor)
    seed_desk(ctx)
    seed_pad(ctx, blocks={"b1": "kept"}, seq=3)
    call(ctx, "pad.apply", {"clientId": "c", "seq": 4, "padId": "p1", "ops": [
        {"op": "remove_block", "blockId": "b1", "expectedHead": call(ctx, "pad.get", {"padId": "p1"})[
            "blocks"][0]["headVersionId"]}]})
    cases = [
        (ask_params("r1", surface="desk"), "validation_error"),
        (ask_params("r2", surface="desk", deskId="nope"), "desk_not_found"),
        (ask_params("r3", surface="notebook"), "validation_error"),
        (ask_params("r4", padBlockIds=["b1"]), "block_not_found"),
        (ask_params("r5", padBlockIds=["missing"]), "block_not_found"),
        (ask_params("r6", spanId="not_a_span", selectionSpanIds=["not_a_span"]), None),
    ]
    for params, code in cases:
        with pytest.raises(SidecarError) as refused:
            call(ctx, "companion.ask", params)
        if code is not None:
            assert refused.value.code == code, params
        jobs = getattr(ctx, "companion_ask_jobs", None)
        assert jobs is None or jobs.get(params["requestId"]) is None
    assert tutor.prompts == [] and _question_count(repository) == 0
