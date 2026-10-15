"""Marker reads PDFs in a worker process, never in the sidecar's (docs/reviews/marker-pdfium-worker.md).

pdfium is not thread-safe, and the Reader renders PDF pages with it in the
sidecar's own process while an import reads on the ingest drain's thread.
Marker enters pdfium all through a reading (its PdfProvider, pdftext, page
images for the models), so it runs in a worker process of its own, as
GLM-OCR's text layer does; the Reader's own renders take one lock.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time

import pytest

from tests.marker_fakes import fake_marker  # noqa: F401 - fixture
from tests.test_glm_ocr import _drain_beside_the_reader
from tests.test_source_ingestion_adapters import _make_pdf_bytes

LINES = ["Eigenvalues are scalars.", "Every square matrix has a characteristic polynomial."]


def _context(**kwargs):
    from learnloop.ingest.extractors import ExtractionContext

    return ExtractionContext(revision_id="rev_1", **kwargs)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # pragma: no cover - someone else's process took the pid
        return False
    return True


def _gone(pid: int, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.05)
    return False


def test_marker_never_enters_pdfium_in_this_process_while_the_reader_renders(fake_marker, monkeypatch, tmp_path):
    """The import's Marker reading (the durable extractor and the legacy
    one-shot path) beside the Reader rendering: only the Reader enters
    pdfium in this process, and Marker's own pdfium reading still happens,
    in the worker."""

    pdfium = pytest.importorskip("pypdfium2")
    from learnloop.config import PdfIngestConfig
    from learnloop.content.sources.pdf_extraction import extract_pdf_markdown
    from learnloop.ingest.extractors import MarkerDocumentExtractor

    raw = _make_pdf_bytes(LINES)
    path = tmp_path / "book.pdf"
    path.write_bytes(raw)
    entered = []
    opened = pdfium.PdfDocument

    def watched(*args, **kwargs):
        entered.append(threading.current_thread().name)
        return opened(*args, **kwargs)

    monkeypatch.setattr(pdfium, "PdfDocument", watched)
    ir, renders = _drain_beside_the_reader(lambda: MarkerDocumentExtractor().extract(raw, _context()), path)

    assert renders >= 1
    assert set(entered) == {threading.current_thread().name}  # only the Reader entered pdfium here
    assert ir.extractor == "marker" and [b.text for b in ir.blocks] == [" ".join(LINES)]  # pdfium read it, there
    (call,) = fake_marker.calls()
    assert call["pid"] != os.getpid() and call["config"]["output_format"] == "chunks"

    entered.clear()
    extraction, _ = _drain_beside_the_reader(
        lambda: extract_pdf_markdown(raw, config=PdfIngestConfig(engine="marker")), path
    )
    assert extraction.engine == "marker" and "Eigenvalues are scalars." in extraction.markdown
    assert set(entered) == {threading.current_thread().name}
    assert fake_marker.calls()[-1]["pid"] != os.getpid()


def test_a_marker_worker_that_crashes_or_hangs_is_recorded_and_the_import_falls_back(fake_marker, monkeypatch):
    from learnloop.ingest.extractors import MarkerDocumentExtractor, extract_with_fallback, marker_worker

    raw = _make_pdf_bytes(LINES)

    monkeypatch.setenv("FAKE_MARKER_MODE", "crash")  # a native crash, as a segfault would be
    crashed = extract_with_fallback(raw, MarkerDocumentExtractor(), {"engine": "auto"}, _context())
    assert crashed.extractor == "pypdf" and "Eigenvalues are scalars." in crashed.blocks[0].text
    assert {"marker_failed_pypdf_fallback", "marker_worker_crashed"} <= set(crashed.health.flags)
    with pytest.raises(marker_worker.MarkerWorkerError, match="stopped") as stopped:
        extract_with_fallback(raw, MarkerDocumentExtractor(), {"engine": "marker"}, _context())  # fails as itself
    assert stopped.value.health_flag == "marker_worker_crashed"

    monkeypatch.setenv("FAKE_MARKER_MODE", "raise")  # Marker's own error: a plain fallback, as before
    failed = extract_with_fallback(raw, MarkerDocumentExtractor(), {"engine": "auto"}, _context())
    assert "marker_failed_pypdf_fallback" in failed.health.flags
    assert not {"marker_worker_crashed", "marker_worker_timed_out"} & set(failed.health.flags)
    with pytest.raises(marker_worker.MarkerWorkerError, match="the fake marker could not read it"):
        MarkerDocumentExtractor().extract(raw, _context())

    monkeypatch.setenv("FAKE_MARKER_MODE", "hang")
    monkeypatch.setattr(marker_worker, "_WORKER_MIN_SECONDS", 2.0)
    monkeypatch.setattr(marker_worker, "_WORKER_SECONDS_PER_PAGE", 0.0)
    workers = []
    popen = subprocess.Popen

    def started(*args, **kwargs):
        workers.append(popen(*args, **kwargs))
        return workers[-1]

    monkeypatch.setattr(subprocess, "Popen", started)
    hung = extract_with_fallback(raw, MarkerDocumentExtractor(), {"engine": "auto"}, _context())
    assert hung.extractor == "pypdf"
    assert {"marker_failed_pypdf_fallback", "marker_worker_timed_out"} <= set(hung.health.flags)
    assert len(workers) == 1 and workers[0].poll() is not None  # stopped, not left running


def test_the_legacy_one_shot_path_reports_a_marker_worker_crash_as_its_error(fake_marker, monkeypatch):
    from learnloop.config import PdfIngestConfig
    from learnloop.content.sources.pdf_extraction import PdfExtractionError, extract_pdf_markdown

    monkeypatch.setenv("FAKE_MARKER_MODE", "crash")
    with pytest.raises(PdfExtractionError, match="marker failed to convert PDF"):
        extract_pdf_markdown(_make_pdf_bytes(LINES), config=PdfIngestConfig(engine="marker"))


def test_a_cancelled_import_stops_the_marker_worker(fake_marker, monkeypatch):
    from learnloop.ai.spend import SpendCancelled
    from learnloop.ingest.extractors import MarkerDocumentExtractor, extract_with_fallback

    monkeypatch.setenv("FAKE_MARKER_MODE", "hang")
    started = time.monotonic()

    def interrupt():
        if fake_marker.calls():  # the worker is reading: the learner cancels
            raise SpendCancelled("The import was cancelled")

    with pytest.raises(SpendCancelled):  # never a fallback
        extract_with_fallback(_make_pdf_bytes(LINES), MarkerDocumentExtractor(), {"engine": "auto"},
                              _context(interrupt=interrupt))
    assert time.monotonic() - started < 60
    assert _gone(fake_marker.calls()[-1]["pid"])


def test_marker_output_never_reaches_this_process_stdout(fake_marker, monkeypatch, capfd):
    """The sidecar's stdout carries JSON-RPC: whatever Marker prints stays
    in the worker's log."""

    from learnloop.ingest.extractors import MarkerDocumentExtractor

    monkeypatch.setenv("FAKE_MARKER_MODE", "chatty")
    ir = MarkerDocumentExtractor().extract(_make_pdf_bytes(LINES), _context())
    assert [b.text for b in ir.blocks] == [" ".join(LINES)]
    out, err = capfd.readouterr()
    assert "marker progress" not in out and "marker progress" not in err


def test_a_worker_that_answered_exits_at_once_and_cleanly(fake_marker, monkeypatch):
    """Its stdin watcher never holds the interpreter's stdin lock (that
    aborted the worker at shutdown, about ten seconds after every answer)."""

    from learnloop.ingest.extractors import MarkerDocumentExtractor

    workers = []
    popen = subprocess.Popen

    def started(*args, **kwargs):
        workers.append(popen(*args, **kwargs))
        return workers[-1]

    monkeypatch.setattr(subprocess, "Popen", started)
    MarkerDocumentExtractor().extract(_make_pdf_bytes(LINES), _context())
    assert [worker.returncode for worker in workers] == [0]


def test_the_worker_carries_the_page_selection_and_torch_device_without_touching_this_process(
    fake_marker, monkeypatch
):
    from learnloop.ingest.extractors import MarkerDocumentExtractor

    monkeypatch.delenv("TORCH_DEVICE", raising=False)
    raw = _make_pdf_bytes(LINES)
    ir = MarkerDocumentExtractor(config={"torch_device": "cuda:1"}).extract(raw, _context(page_selection=(0,)))
    assert [b.page for b in ir.blocks] == [0]
    (call,) = fake_marker.calls()
    assert call["torch_device"] == "cuda:1" and "TORCH_DEVICE" not in os.environ
    assert call["config"]["page_range"] == "0" and call["config"]["pdftext_workers"] == 1
    assert "torch_device" not in call["config"]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_a_marker_worker_stops_when_the_process_that_started_it_dies(fake_marker, monkeypatch, tmp_path):
    """The sidecar quitting (or killed) never leaves Marker reading on its own."""

    import signal

    monkeypatch.setenv("FAKE_MARKER_MODE", "hang")
    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(_make_pdf_bytes(LINES))
    parent = subprocess.Popen(
        [sys.executable, "-c",
         "import sys; from pathlib import Path; from learnloop.ingest.extractors import marker_worker; "
         "marker_worker.run_marker('markdown', Path(sys.argv[1]).read_bytes(), {'output_format': 'markdown'})",
         str(pdf)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        # A killed process never removes its temporary directory: keep it here.
        env={**os.environ, "TMPDIR": str(tmp_path), "TEMP": str(tmp_path), "TMP": str(tmp_path)},
    )
    try:
        deadline = time.monotonic() + 60
        while not fake_marker.calls() and time.monotonic() < deadline:
            time.sleep(0.05)
        (call,) = fake_marker.calls()
        assert _alive(call["pid"])
        parent.send_signal(signal.SIGKILL)
        parent.wait()
        assert _gone(call["pid"]), "the worker outlived the process that started it"
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()
        for call in fake_marker.calls():
            if _alive(call["pid"]):
                os.kill(call["pid"], 9)


def test_the_readers_own_renders_enter_pdfium_one_at_a_time(monkeypatch, tmp_path):
    """The Reader is the one pdfium user left in the sidecar's process; two
    of its renders (a request and a background view) never overlap in it."""

    pdfium = pytest.importorskip("pypdfium2")
    from learnloop.reader import span_view

    path = tmp_path / "book.pdf"
    path.write_bytes(_make_pdf_bytes(LINES))
    inside, peak, held = [0], [0], []
    guard = threading.Lock()
    opened = pdfium.PdfDocument

    def watched(*args, **kwargs):
        lock = getattr(span_view, "_PDFIUM_LOCK", None)
        held.append(lock is not None and lock.locked())
        with guard:
            inside[0] += 1
            peak[0] = max(peak[0], inside[0])
        time.sleep(0.005)
        with guard:
            inside[0] -= 1
        return opened(*args, **kwargs)

    monkeypatch.setattr(pdfium, "PdfDocument", watched)
    failures = []

    def render(crop: bool):
        for _ in range(15):
            if crop:
                image, _ = span_view._local_pdf_block_crop(path, 0, [72.0, 80.0, 300.0, 120.0])
            else:
                image, _ = span_view._local_pdf_page_render(path, 0)
            if not (image or "").startswith("data:image/png;base64,"):
                failures.append(crop)

    threads = [threading.Thread(target=render, args=(index % 2 == 1,)) for index in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert failures == []
    assert peak[0] == 1  # never two renders inside pdfium at once
    assert held and all(held)
