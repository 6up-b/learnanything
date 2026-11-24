"""Shared doubles and builders for the pen-and-ink tests (``tests/test_reader_rd8a_*.py``,
``tests/test_reader_ink_glm_ocr.py``): GLM-OCR faked at the extractor's own transport seam (``glm_ocr._open``, as
``tests/test_glm_ocr.py`` fakes it), the vault set up for its hosted or local backend, and the synthetic strokes
the renderer and the reading are tested on. No request leaves the machine."""

from __future__ import annotations

import io
import json
import threading
from types import SimpleNamespace
from typing import Any

from tests.glm_ocr_helpers import region

#: A z.ai key for the hosted backend's tests (never a real one).
GLM_KEY = "fake-zai-key-123456"


class FakeGlmOcr:
    """GLM-OCR's transport (``glm_ocr._open``, reached inside the extractor's admission and receipt): records each
    request it is sent and answers one page whose regions hold ``text`` (``regions``: those regions instead).
    ``hold``: it waits inside the request until ``release`` (a request already sent)."""

    def __init__(self, text: str = "", *, regions: list[dict] | None = None, hold: bool = False) -> None:
        self.text = text
        self.regions = regions
        self.hold = hold
        self.requests: list[Any] = []
        self.reached = 0
        self.inside = threading.Event()
        self.release = threading.Event()

    def install(self, monkeypatch: Any) -> FakeGlmOcr:
        from learnloop.ingest.extractors import glm_ocr

        monkeypatch.setattr(glm_ocr, "_open", self)
        return self

    def __call__(self, request: Any, timeout: float) -> Any:
        self.reached += 1
        body = json.loads(request.data)
        if self.hold:
            self.inside.set()
            if not self.release.wait(WAIT):
                raise RuntimeError("the test never released the held reading")
        self.requests.append(SimpleNamespace(url=request.full_url, headers=dict(request.header_items()), body=body))
        regions = self.regions if self.regions is not None else [region(0, "text", self.text, [10, 10, 400, 60])]
        answer = {"id": "task_ink", "model": "glm-ocr", "layout_details": [regions],
                  "data_info": {"num_pages": 1, "pages": [{"width": 1224, "height": 1584}]},
                  "usage": {"prompt_tokens": 900, "completion_tokens": 40, "total_tokens": 940}}
        return io.BytesIO(json.dumps(answer).encode())


def glm_local(monkeypatch: Any, vault_root: Any, text: str = "", **fake: Any) -> FakeGlmOcr:
    """The vault reads with the self-hosted GLM-OCR server (``backend = "local"``), which answers."""

    from learnloop.ingest.extractors import glm_ocr
    from learnloop.ops.settings_store import apply_config_updates

    apply_config_updates(vault_root / "learnloop.toml", {("ingest", "pdf", "glm_ocr", "backend"): "local"})
    monkeypatch.setattr(glm_ocr, "local_available", lambda config=None: True)
    return FakeGlmOcr(text, **fake).install(monkeypatch)


def glm_hosted(monkeypatch: Any, vault_root: Any, text: str = "", *, upload_ok: bool = True,
               model_use_ok: bool = True, **fake: Any) -> FakeGlmOcr:
    """The vault reads with z.ai's hosted GLM-OCR (a key set), with the learner's OKs as given."""

    from learnloop.ai.model_use import MODEL_USE_FLOW, MODEL_USE_KEY
    from learnloop.content.pipeline.add_source import FILE_UPLOAD_DATA_FLOW, GLM_OCR_UPLOAD_CONSENT
    from learnloop.ops.settings_store import apply_config_updates

    monkeypatch.setenv("ZAI_API_KEY", GLM_KEY)
    updates: dict[tuple[str, ...], Any] = {}
    if model_use_ok:
        updates[("ai", "consent", MODEL_USE_KEY, "granted_at")] = "2026-11-23T09:00:00Z"
        updates[("ai", "consent", MODEL_USE_KEY, "data_flow")] = MODEL_USE_FLOW
    if upload_ok:
        updates[("ai", "consent", GLM_OCR_UPLOAD_CONSENT, "granted_at")] = "2026-11-23T09:00:00Z"
        updates[("ai", "consent", GLM_OCR_UPLOAD_CONSENT, "data_flow")] = FILE_UPLOAD_DATA_FLOW
    if updates:
        apply_config_updates(vault_root / "learnloop.toml", updates)
    return FakeGlmOcr(text, **fake).install(monkeypatch)


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
             annotation_id: str | None = None, extraction_id: str | None = None,
             pointer: dict[str, Any] | None = None) -> dict[str, Any]:
        from learnloop.pads import ink

        owner = ink.InkOwner(block_id=block_id, annotation_id=annotation_id, extraction_id=extraction_id)
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


#: How long a test waits on a job or a held fake before it fails (never reached when the code is right).
WAIT = 20.0


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
