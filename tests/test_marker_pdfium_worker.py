"""Marker reads PDFs in a worker process, never in the sidecar's (docs/reviews/marker-pdfium-worker.md).

pdfium is not thread-safe, and the Reader renders PDF pages with it in the
sidecar's own process while an import reads on the ingest drain's thread.
Marker enters pdfium all through a reading (its PdfProvider, pdftext, page
images for the models), so it runs in a worker process of its own, as
GLM-OCR's text layer does; the Reader's own renders take one lock.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid

import pytest

from tests.marker_fakes import fake_marker  # noqa: F401 - fixture
from tests.test_glm_ocr import _drain_beside_the_reader
from tests.test_source_ingestion_adapters import _make_pdf_bytes

LINES = ["Eigenvalues are scalars.", "Every square matrix has a characteristic polynomial."]


def _context(**kwargs):
    from learnloop.ingest.extractors import ExtractionContext

    return ExtractionContext(revision_id="rev_1", **kwargs)


def _alive(pid: int) -> bool:
    """Running: a process that was killed but not yet reaped (a zombie,
    waiting on whoever inherited it) has stopped."""

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # pragma: no cover - someone else's process took the pid
        return False
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as handle:
            state = handle.read().rsplit(")", 1)[1].split()[0]
    except FileNotFoundError:
        return False
    except OSError:  # pragma: no cover - no /proc: kill(pid, 0) is all there is
        return True
    return state not in ("Z", "X")


def _gone(pid: int, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.05)
    return False


def _kill_leftovers(fake_marker) -> None:
    """A failing test never leaves its processes asleep for ten minutes."""

    for entry in [*fake_marker.calls(), *fake_marker.descendants()]:
        if _alive(entry["pid"]):
            try:
                os.kill(entry["pid"], signal.SIGKILL)
            except OSError:
                pass


def _wait_for(condition, seconds: float = 60.0) -> None:
    deadline = time.monotonic() + seconds
    while not condition() and time.monotonic() < deadline:
        time.sleep(0.05)


def _start_reading_in_a_parent(tmp_path, options):
    """A process that reads a PDF with Marker's worker, as the sidecar does:
    the test kills it mid-reading. Its temporary directories go under
    ``tmp_path / "temp"``, where the test can see what a killed process left."""

    pdf = tmp_path / "book.pdf"
    pdf.write_bytes(_make_pdf_bytes(LINES))
    temp = tmp_path / "temp"
    temp.mkdir()
    parent = subprocess.Popen(
        [sys.executable, "-c",
         "import json, sys; from pathlib import Path; from learnloop.ingest.extractors import marker_worker; "
         "marker_worker.run_marker('markdown', Path(sys.argv[1]).read_bytes(), json.loads(sys.argv[2]))",
         str(pdf), json.dumps(options)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        env={**os.environ, "TMPDIR": str(temp), "TEMP": str(temp), "TMP": str(temp)},
    )
    return parent, temp


def _files_holding(root, needle: str) -> list[str]:
    found = []
    for path in root.rglob("*"):
        try:
            if path.is_file() and needle.encode() in path.read_bytes():
                found.append(str(path.relative_to(root)))
        except OSError:
            continue
    return found


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


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups")
@pytest.mark.parametrize("ending", ["timeout", "cancel", "crash", "error", "answer"])
def test_every_process_the_marker_worker_started_ends_with_its_reading(fake_marker, monkeypatch, ending):
    """With ``pdftext_workers`` above 1, pdftext starts a pool of processes
    under the worker. However the reading ends (out of time, cancelled, the
    worker crashed, Marker raised, or it answered), none of them is left
    running (Codex review F1)."""

    from learnloop.ai.spend import SpendCancelled
    from learnloop.ingest.extractors import MarkerDocumentExtractor, extract_with_fallback, marker_worker

    mode = {"timeout": "hang", "cancel": "hang", "crash": "crash", "error": "raise", "answer": "ok"}[ending]
    monkeypatch.setenv("FAKE_MARKER_MODE", mode)
    if ending == "timeout":
        monkeypatch.setattr(marker_worker, "_WORKER_MIN_SECONDS", 1.0)
        monkeypatch.setattr(marker_worker, "_WORKER_SECONDS_PER_PAGE", 0.0)

    def interrupt():
        if ending == "timeout":  # the time limit runs out only once the pool is up
            _wait_for(lambda: len(fake_marker.descendants()) >= 2)
        if ending == "cancel" and len(fake_marker.descendants()) >= 2:
            raise SpendCancelled("The import was cancelled")

    extractor = MarkerDocumentExtractor(config={"pdftext_workers": 2})
    try:
        if ending == "cancel":
            with pytest.raises(SpendCancelled):
                extract_with_fallback(_make_pdf_bytes(LINES), extractor, {"engine": "auto"},
                                      _context(interrupt=interrupt))
        else:
            ir = extract_with_fallback(_make_pdf_bytes(LINES), extractor, {"engine": "auto"},
                                       _context(interrupt=interrupt))
            if ending == "answer":
                assert ir.extractor == "marker" and [b.text for b in ir.blocks] == [" ".join(LINES)]
            else:
                assert ir.extractor == "pypdf"
                flag = {"timeout": "marker_worker_timed_out", "crash": "marker_worker_crashed"}.get(ending)
                assert flag is None or flag in ir.health.flags
        (call,) = fake_marker.calls()
        pool = fake_marker.descendants()
        assert len(pool) == 2 and {entry["parent"] for entry in pool} == {call["pid"]}
        assert _gone(call["pid"])
        left = [entry["pid"] for entry in pool if not _gone(entry["pid"])]
        assert left == [], f"the worker's pool outlived its reading: {left}"
    finally:
        _kill_leftovers(fake_marker)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_a_marker_worker_and_its_pool_stop_when_the_process_that_started_it_dies(fake_marker, monkeypatch, tmp_path):
    """The sidecar quitting (or killed) never leaves Marker reading on its
    own, nor any process Marker started (Codex review F1)."""

    monkeypatch.setenv("FAKE_MARKER_MODE", "hang")
    parent, temp = _start_reading_in_a_parent(tmp_path, {"output_format": "markdown", "pdftext_workers": 2})
    try:
        _wait_for(lambda: len(fake_marker.descendants()) >= 2)
        (call,) = fake_marker.calls()
        pool = fake_marker.descendants()
        assert _alive(call["pid"]) and len(pool) == 2 and all(_alive(entry["pid"]) for entry in pool)
        parent.send_signal(signal.SIGKILL)
        parent.wait()
        assert _gone(call["pid"]), "the worker outlived the process that started it"
        left = [entry["pid"] for entry in pool if not _gone(entry["pid"])]
        assert left == [], f"the worker's pool outlived the process that started it: {left}"
        assert list(temp.iterdir()) == [], "the worker left its private directory behind"
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()
        _kill_leftovers(fake_marker)


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX signals")
def test_a_marker_readings_api_key_never_reaches_the_disk_even_when_its_parent_dies(
    fake_marker, monkeypatch, tmp_path
):
    """The legacy path's ``use_llm`` puts an API key in Marker's options: the
    worker gets them through its stdin, never a file, so a sidecar killed
    mid-reading leaves no credential behind (Codex review F2)."""

    secret = f"sk-synthetic-{uuid.uuid4().hex}"
    monkeypatch.setenv("FAKE_MARKER_MODE", "hang")
    options = {"output_format": "markdown", "use_llm": True, "openai_api_key": secret}
    parent, temp = _start_reading_in_a_parent(tmp_path, options)
    try:
        _wait_for(lambda: bool(fake_marker.calls()))
        (call,) = fake_marker.calls()
        assert call["config"]["openai_api_key"] == secret  # the worker has it
        assert [path.name.startswith("learnloop-marker-") for path in temp.iterdir()] == [True]  # mid-reading
        assert _files_holding(temp, secret) == []
        parent.send_signal(signal.SIGKILL)
        parent.wait()
        assert _gone(call["pid"])
        assert _files_holding(temp, secret) == [], "a killed reading left its API key on disk"
    finally:
        if parent.poll() is None:
            parent.kill()
            parent.wait()
        _kill_leftovers(fake_marker)


def test_the_windows_job_limit_structure_has_its_documented_layout():
    """The job object that contains a Windows worker's processes is set
    through ``JOBOBJECT_EXTENDED_LIMIT_INFORMATION``; Windows only checks its
    size, so a wrong field shifts the kill-on-close flag silently."""

    import ctypes

    from learnloop.ingest.extractors import marker_worker

    if ctypes.sizeof(ctypes.c_void_p) != 8:  # pragma: no cover - 32-bit
        pytest.skip("the documented sizes are for 64-bit Windows")
    extended = marker_worker._job_limit_information()
    assert ctypes.sizeof(extended) == 144
    assert extended.IoInfo.offset == 64
    assert extended.BasicLimitInformation.offset == 0
    basic = extended._fields_[0][1]
    assert basic.LimitFlags.offset == 16 and ctypes.sizeof(basic) == 64


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
