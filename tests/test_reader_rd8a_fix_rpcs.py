"""RD8a's fix round, the sidecar half: a retry after a cancel waits for the cancelled request rather than paying
for the same strokes again, and a reading finishing after its context moved on wakes no worker. Every model is a
fake."""

from __future__ import annotations

import threading
import time

import pytest

from learnloop.pads import ink
from learnloop.pads import ink_transcribe as reading
from learnloop_sidecar.handlers import ink as ink_handler
from tests.helpers import create_basic_vault
from tests.ink_helpers import STROKES, WAIT, close_and_wait, glm_local, ink_jobs, ink_pad, wait_reading
from tests.reader_rd4_helpers import PAD, edit, rows, vault
from tests.reading_path_fixtures import call, context


class _Watched(threading.Event):
    """A job's done event that says when another thread starts waiting on it."""

    def __init__(self) -> None:
        super().__init__()
        self.waited = threading.Event()

    def wait(self, timeout=None):
        self.waited.set()
        return super().wait(timeout)


@pytest.fixture
def held_context(tmp_path, monkeypatch):
    root = create_basic_vault(tmp_path / "vault").root
    held = glm_local(monkeypatch, root, "$x$", hold=True)
    ctx = context(root)
    yield ctx, held
    held.release.set()
    close_and_wait(ctx)


def test_a_retry_after_a_cancel_waits_for_the_cancelled_request_instead_of_paying_again(held_context):
    ctx, held = held_context
    call(ctx, "pad.apply", {"clientId": "c", "seq": 1, "padId": "p", "ops": [
        {"op": "create_pad", "kind": "ink"},
        {"op": "insert_block", "blockId": "b1", "kind": "ink", "provenance": "ink_transcription", "positionKey": "a0"}]})
    call(ctx, "ink.save", {"clientId": "c", "seq": 2, "owner": {"blockId": "b1"}, "inkId": "ink_1",
                           "strokes": [{"strokeId": s["stroke_id"], "points": s["points"]} for s in STROKES],
                           "pointerMeta": {"pointerType": "pen", "devicePixelRatio": 1}})
    first = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert held.inside.wait(WAIT)
    cancelled = next(job for job in ink_jobs(ctx) if job.job_id == first["jobId"])
    cancelled.done = _Watched()
    assert call(ctx, "ink.transcribe_cancel", {"jobId": first["jobId"]})["status"] == "cancelled"
    second = call(ctx, "ink.transcribe", {"inkId": "ink_1"})
    assert second["jobId"] not in (None, first["jobId"]) and not second["done"]
    # The retry either waits on the cancelled job or reaches the model itself: whichever happens first.
    deadline = time.monotonic() + WAIT
    while not (cancelled.done.waited.is_set() or held.reached == 2) and time.monotonic() < deadline:
        cancelled.done.waited.wait(0.01)
    held.release.set()
    done = wait_reading(ctx, second["jobId"])
    assert (done["status"], done["result"]["latexMd"]) == ("done", "$x$")
    assert held.reached == 1


class _Worker:
    def __init__(self) -> None:
        self.woken = 0

    def notify(self) -> None:
        self.woken += 1


class _Context:
    def __init__(self) -> None:
        self.post_attempt_worker = _Worker()


def test_a_reading_finishing_after_its_context_moved_on_keeps_its_facts_but_wakes_no_worker(tmp_path, monkeypatch):
    paths, repository, _batches, client = ink_pad(tmp_path)
    glm_local(monkeypatch, paths.root, "a + b")
    client.save("ink_1", STROKES, block_id="b1")
    result = reading.transcribe(vault(paths), repository, reading.prepare(repository, "ink_1"))
    stale = _Context()
    ink_handler._after_reading(stale, vault(paths), repository, result, lambda: False)
    assert stale.post_attempt_worker.woken == 0
    assert rows(repository, "SELECT source_id FROM learner_text_gap_jobs WHERE state = 'queued'") == [(result["head_version_id"],)]


def test_the_listed_reading_beside_the_learners_correction_says_why_it_is_not_the_words(tmp_path, monkeypatch):
    paths, repository, batches, client = ink_pad(tmp_path)
    ocr = glm_local(monkeypatch, paths.root, "a")
    client.save("ink_1", STROKES[:2], block_id="b1")
    first = reading.transcribe(vault(paths), repository, reading.prepare(repository, "ink_1"))
    [listed] = ink.ink_for_pad(repository, PAD)
    assert (listed["transcription"]["applied"], listed["transcription"]["reason"]) == (True, None)
    batches.pad(PAD, edit("b1", first["head_version_id"], "mine", "v_fix"))
    client.save("ink_2", STROKES[2:], block_id="b1")
    ocr.text = "b"
    reading.transcribe(vault(paths), repository, reading.prepare(repository, "ink_2"))
    [listed] = ink.ink_for_pad(repository, PAD)
    assert listed["transcription"]["latex_md"] == "b"
    assert (listed["transcription"]["current"], listed["transcription"]["applied"], listed["transcription"]["reason"]) == (
        True, False, "kept_your_correction")
