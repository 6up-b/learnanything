"""Shared by the companion-ask and search-in-context tests (spec_reader_workbench_v2 §3.4, §8, §9.3): a tutor
fake that can hold its answer, the job waits, and the desk and pad seeding through the write protocol."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from tests.reader_tutor_fakes import ROOT_QUESTION, LookupTutor, reader_ctx
from tests.reading_path_fixtures import call

#: How long a test waits on a job or a held fake before it fails (never reached when the code is right).
WAIT = 20.0


class HeldTutor(LookupTutor):
    """``LookupTutor`` that, while ``hold`` is set, waits inside its model request until ``release``.

    ``entered`` is set once a request is inside ``complete`` (the request was admitted and sent), so a
    test knows generation is in progress while it serves another RPC."""

    def __init__(self, *, hold: bool = True, fail: BaseException | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.hold = hold
        self.fail = fail
        self.entered = threading.Event()
        self.release = threading.Event()
        self.inside = threading.Event()

    def complete(self, request):
        from learnloop.ai.execution import model_call

        # One physical request, as a provider makes it: admitted through the context's request gate first
        # (a cancelled or closed job's request is refused here, before anything is sent).
        with model_call(self, purpose=f"{request.purpose}:fake_turn", prompt=request.prompt):
            self.entered.set()
            if self.hold:
                self.inside.set()
                released = self.release.wait(WAIT)
                self.inside.clear()
                if not released:
                    raise TimeoutError("the test never released the held answer")
            if self.fail is not None:
                raise self.fail
            return super().complete(request)


def settle_gap_readings(ctx: Any) -> None:
    """Wait for the learner-text gap readings an answer queued (the reply queues one per exchange and wakes the
    post-attempt worker), then stop that worker, so nothing it would write lands after this returns."""

    from contextlib import closing

    from learnloop.db.connection import connect

    _vault, repository = ctx.require_vault()

    def pending() -> list[str]:
        with closing(connect(repository.sqlite_path, read_only=True)) as connection:
            return [str(row[0]) for row in connection.execute(
                "SELECT id FROM learner_text_gap_jobs WHERE state IN ('queued', 'leased')")]

    left, _waited = ctx.post_attempt_worker.wait_for(pending, WAIT)
    assert not left, f"gap readings still pending: {left}"
    ctx.post_attempt_worker.shutdown(timeout=WAIT)
    assert not ctx.post_attempt_worker.running


def close_and_wait(ctx: Any) -> None:
    """End a context as the sidecar does (``SidecarContext.close``: every owner told to stop and joined, bounded),
    then wait for every polled job's thread and every background job, so nothing a test started outlives it.
    A thread still alive after the bound fails the test, naming it."""

    ctx.close()
    deadline = time.monotonic() + WAIT
    threads = [*ctx.background_jobs.running]
    for name in ("companion_ask_jobs", "search_jobs"):
        registry = getattr(ctx, name, None)
        if registry is not None:
            threads += [job.thread for job in list(registry._jobs.values()) if job.thread is not None]
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    alive = [thread.name for thread in threads if thread.is_alive()]
    assert not alive, f"threads still running after the context closed: {alive}"


@contextmanager
def workbench_contexts(tmp_path: Any, monkeypatch: Any) -> Iterator[Callable[..., tuple[Any, Any, Any, Any]]]:
    """Makes ``reader_ctx`` contexts (the library vault with the tutor fake); each is closed and waited for at the
    end (a test file's ``workbench`` fixture wraps this, so every job a test starts ends inside that test)."""

    made: list[tuple[Any, LookupTutor]] = []

    def make(tutor: LookupTutor, **kwargs: Any) -> tuple[Any, Any, Any, Any]:
        paths, ctx, repository, spans = reader_ctx(tmp_path, monkeypatch, tutor, **kwargs)
        made.append((ctx, tutor))
        return paths, ctx, repository, spans

    yield make
    for ctx, tutor in made:
        if isinstance(tutor, HeldTutor):
            tutor.release.set()  # a test that failed while holding never leaves its job waiting
        close_and_wait(ctx)


def ask_params(request_id: str = "req_1", question: str = ROOT_QUESTION, **extra: Any) -> dict[str, Any]:
    """``companion.ask``'s input on the library vault's text passage (the old Reader's surface by default)."""

    return {"requestId": request_id, "surface": "reader", "extractionId": "ext_text", "spanId": "t3",
            "question": question, "selectionSpanIds": ["t3"], "selectionQuote": "the determinant changes sign",
            **extra}


def wait_job(ctx: Any, request_id: str, *, method: str = "companion.ask_job") -> dict[str, Any]:
    """Wait on the job itself (a poll never waits), then poll it once."""

    registry = ctx.companion_ask_jobs if method.startswith("companion") else ctx.search_jobs
    job = registry.get(request_id)
    assert job is not None and job.done.wait(WAIT), f"job {request_id} did not finish"
    deadline = time.monotonic() + WAIT
    while job.thread is not None and job.thread.is_alive() and time.monotonic() < deadline:
        job.thread.join(0.05)
    key = "requestId" if method.startswith("companion") else "jobId"
    return call(ctx, method, {key: request_id})


def seed_desk(ctx: Any, *, desk_id: str = "d1", source_id: str = "src_text", extraction_id: str = "ext_text",
              goal_id: str | None = None, client_id: str = "c", seq: int = 1) -> dict[str, Any]:
    """A desk with one source window, focused (two batches through ``desk.apply``)."""

    call(ctx, "desk.apply", {"clientId": client_id, "seq": seq, "ops": [
        {"op": "create_desk", "deskId": desk_id, "title": "determinants", "position": "a0",
         **({"goalId": goal_id} if goal_id else {})},
        {"op": "open_window", "deskId": desk_id, "windowId": f"{desk_id}_w1", "expectedVersion": 1,
         "content": {"kind": "source", "sourceId": source_id, "extractionId": extraction_id}}]})
    return call(ctx, "desk.apply", {"clientId": client_id, "seq": seq + 1, "ops": [
        {"op": "set_focus", "deskId": desk_id, "windowId": f"{desk_id}_w1", "expectedVersion": 2}]})


def seed_pad(ctx: Any, *, pad_id: str = "p1", blocks: dict[str, str], desk_id: str | None = None,
             client_id: str = "c", seq: int = 1, provenance: str = "learner") -> dict[str, Any]:
    """A named pad with learner text blocks (``{block_id: text}``)."""

    ops: list[dict[str, Any]] = [{"op": "create_pad", "kind": "named", "title": "scratch",
                                  **({"homeDeskId": desk_id} if desk_id else {})}]
    for index, (block_id, text) in enumerate(blocks.items()):
        ops.append({"op": "insert_block", "blockId": block_id, "kind": "text", "provenance": provenance,
                    "positionKey": f"a{index}", "bodyMd": text})
    return call(ctx, "pad.apply", {"clientId": client_id, "seq": seq, "padId": pad_id, "ops": ops})
