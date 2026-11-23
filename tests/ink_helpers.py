"""Shared doubles and builders for the pen-and-ink tests (``tests/test_reader_rd8a_*.py``) and the paid-call image
identity test: a model that reads images (a structured transport double that records each request) and the
synthetic strokes the renderer and the transcription are tested on."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from learnloop.ai.transport import IMAGE_INPUT, ISOLATED_TURN, STRUCTURED_COMPLETION


class ImageReader:
    """A ChatGPT-plan-typed structured client that reads images (``reads_images=False``: one that cannot), records
    every request it is sent and answers with ``answer(request)``."""

    provider_type = "chatgpt_plan"

    def __init__(self, answer: Callable[[Any], Any], *, reads_images: bool = True, provider_name: str = "plan",
                 model: str = "pin-vision") -> None:
        self.answer = answer
        self.reads_images = reads_images
        self.provider_name = provider_name
        self.model = model
        self.requests: list[Any] = []

    def supports(self, capability: str) -> bool:
        if capability == IMAGE_INPUT:
            return self.reads_images
        return capability in {STRUCTURED_COMPLETION, ISOLATED_TURN, "complete", "structured"}

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import model_call

        # One physical request, as a provider makes it: admitted through the request gate first (a cancelled or
        # closed job's request is refused there, before anything is sent).
        with model_call(self, purpose=f"{request.purpose}:fake_turn", prompt=request.prompt):
            self.requests.append(request)
            return self.answer(request)


def stroke(stroke_id: str, *points: tuple[float, float], pressure: float = 0.5) -> dict[str, Any]:
    """A synthetic stroke through ``points`` (CSS pixels), at a fixed pressure and no tilt, 8 ms apart."""

    return {"stroke_id": stroke_id, "points": [[x, y, 8.0 * index, pressure, 0.0, 0.0]
                                               for index, (x, y) in enumerate(points)]}


#: A tick and a bar: two strokes of a handwritten "√" and one dot, the synthetic ink most tests read.
STROKES = [stroke("s1", (10, 30), (16, 40), (30, 8)), stroke("s2", (30, 8), (70, 8)), stroke("s3", (80, 40))]
PEN = {"pointer_type": "pen", "device_pixel_ratio": 1.0}


class InkClient:
    """Saves strokes the way the client does: one ``ink.save`` per flush, numbered in the client's one sequence
    with its pad batches (``tests.desk_helpers.Batches``)."""

    def __init__(self, batches: Any) -> None:
        self.batches = batches

    def save(self, ink_id: str, strokes: list[dict[str, Any]], *, block_id: str | None = None,
             annotation_id: str | None = None, pointer: dict[str, Any] | None = None) -> dict[str, Any]:
        from learnloop.pads import ink

        owner = ink.InkOwner(block_id=block_id, annotation_id=annotation_id)
        self.batches.seq += 1
        return ink.save_ink(self.batches.repository, client_id=self.batches.client_id, seq=self.batches.seq,
                            owner=owner, ink_id=ink_id,
                            strokes=[ink.InkStroke.model_validate(value) for value in strokes],
                            pointer_meta=ink.PointerMeta.model_validate(pointer or PEN))


def ink_pad(tmp_path: Any, *, kind: str = "ink") -> tuple[Any, Any, Any, InkClient]:
    """A basic vault with pad ``pad_1`` holding one empty ink block ``b1`` (provenance ``ink_transcription``, as the
    client inserts a fresh ink line)."""

    from tests.reader_rd4_helpers import PAD, create_pad, insert, pad_vault

    paths, repository, batches = pad_vault(tmp_path)
    create_pad(batches, kind=kind)
    batches.pad(PAD, insert("b1", "", kind="ink", provenance="ink_transcription", version_id="v0"))
    return paths, repository, batches, InkClient(batches)


def reads_as(text: str) -> Callable[[Any], Any]:
    """An answer for :class:`ImageReader`: the reading ``text``, whatever the image."""

    from learnloop.pads.ink_transcribe import InkTranscriptionV1

    return lambda request: InkTranscriptionV1(latex_md=text)


#: How long a test waits on a job or a held fake before it fails (never reached when the code is right).
WAIT = 20.0


class HeldReader(ImageReader):
    """An :class:`ImageReader` that holds inside its one model request until ``release`` (admitted through the
    context's request gate first, as a provider's request is: a cancelled job's request is refused there)."""

    def __init__(self, answer: Callable[[Any], Any], **kwargs: Any) -> None:
        import threading

        super().__init__(answer, **kwargs)
        self.inside = threading.Event()
        self.release = threading.Event()

    def complete(self, request: Any) -> Any:
        from learnloop.ai.execution import model_call

        with model_call(self, purpose=f"{request.purpose}:fake_turn:held", prompt=request.prompt):
            self.inside.set()
            if not self.release.wait(WAIT):
                raise TimeoutError("the test never released the held reading")
        self.requests.append(request)
        return self.answer(request)


def ink_jobs(ctx: Any) -> list[Any]:
    """Every reading job of every vault a context ran."""

    registry = getattr(ctx, "ink_transcribe_jobs", None)
    return [] if registry is None else list(registry._jobs.values())


def wait_reading(ctx: Any, job_id: str) -> dict[str, Any]:
    """Wait on the job itself (a poll never waits), then poll it once."""

    import time

    from tests.reading_path_fixtures import call

    job = next(job for job in ink_jobs(ctx) if job.job_id == job_id)
    assert job.done.wait(WAIT), f"reading {job_id} did not finish"
    deadline = time.monotonic() + WAIT
    while job.thread is not None and job.thread.is_alive() and time.monotonic() < deadline:
        job.thread.join(0.05)
    return call(ctx, "ink.transcribe_job", {"jobId": job_id})


def close_and_wait(ctx: Any) -> None:
    """End a context as the sidecar does, then join every reading job and background job (a thread still alive
    fails the test, naming it)."""

    import time

    ctx.close()
    deadline = time.monotonic() + WAIT
    threads = [*ctx.background_jobs.running, *(job.thread for job in ink_jobs(ctx) if job.thread is not None)]
    for thread in threads:
        thread.join(max(0.0, deadline - time.monotonic()))
    while ctx.post_attempt_worker.running and time.monotonic() < deadline:
        ctx.post_attempt_worker.shutdown(timeout=0.5)
    alive = [thread.name for thread in threads if thread.is_alive()]
    assert not alive, f"threads still running after the context closed: {alive}"
