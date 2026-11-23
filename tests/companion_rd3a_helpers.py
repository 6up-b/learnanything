"""Shared by the companion-ask and search-in-context tests (spec_reader_workbench_v2 §3.4, §8, §9.3): a tutor
fake that can hold its answer, the job waits, and the desk and pad seeding through the write protocol."""

from __future__ import annotations

import threading
import time
from typing import Any

from tests.reader_tutor_fakes import ROOT_QUESTION, LookupTutor
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
