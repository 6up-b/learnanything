"""Marker, in a worker process of its own (docs/reviews/marker-pdfium-worker.md).

pdfium is not thread-safe (pypdfium2: "PDFium is inherently not
thread-safe"). The Reader renders PDF pages with it in the sidecar's own
process (reader/span_view.py) while an import reads on the ingest drain's
thread, and Marker is inside pdfium all through a reading: its PdfProvider
opens the file with pypdfium2, pdftext reads every page's text layer with it,
and its layout and OCR models look at pages pdfium rendered. Two threads in
pdfium at once crash the whole process with a segmentation fault or an
abort, which no Python handler contains (the GLM-OCR quality review's F1, and
this stage's own test). One lock shared with the Reader would hold the Reader
off for a whole reading (minutes to hours) and could not reach the calls
Marker and pdftext make into pdfium themselves. So a Marker reading runs in a
worker process, as GLM-OCR's text layer does (``glm_text_layer.pdfium_worker``),
and the sidecar's process keeps only the Reader in pdfium.

Each reading starts one worker (``sys.executable -P``, the same environment,
so the sidecar's ``PYTHONPATH`` still applies; ``-P`` only drops the working
directory) in a private directory holding the PDF and the request (which can
carry an API key, so never the command line). The worker writes its answer to
a file there; Marker's own output (progress bars, warnings, anything it
prints) goes to a log in that directory, never to the sidecar's stdout, which
carries JSON-RPC. The worker loads Marker's models for each reading and frees
them when it ends.

A worker that crashes, or runs out of time, stops there: the reading fails
with ``MarkerWorkerError`` naming it in ``health_flag``, and under ``engine =
"auto"`` the import falls back to pypdf as it did for any Marker failure
(``extract_with_fallback`` records the flag). A cancelled import stops the
worker (``interrupt``, checked while it reads), and so does the end of the
process that started it: the worker watches its stdin, whose other end only
that process holds.
"""

from __future__ import annotations

import io
import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)

WORKER_CRASHED = "marker_worker_crashed"
WORKER_TIMED_OUT = "marker_worker_timed_out"

_WORKER = "from learnloop.ingest.extractors.marker_worker import _worker_main; _worker_main()"
# Generous: the limit is there for a worker that hangs, never to cut a slow
# reading short. Loading the models (or downloading them on a first run) fits
# in the minimum; a page on a CPU with OCR takes seconds to a minute.
_WORKER_MIN_SECONDS = 1800.0
_WORKER_SECONDS_PER_PAGE = 120.0
# When the page count can't be read here, the time a long book would get.
_WORKER_UNKNOWN_PAGES = 1000
# How often a cancelled import is noticed while the worker reads.
_POLL_SECONDS = 0.5
_LOG_TAIL = 2000
# The worker's exit status when the process that started it is gone.
_ORPHANED = 70


class MarkerWorkerError(RuntimeError):
    """Marker's worker could not read the PDF: Marker failed in it, or the
    worker crashed (``health_flag`` = ``marker_worker_crashed``) or ran out
    of time (``marker_worker_timed_out``)."""

    def __init__(self, message: str, *, health_flag: str | None = None):
        super().__init__(message)
        self.health_flag = health_flag


def run_marker(
    task: str,
    raw: bytes,
    options: Mapping[str, Any],
    *,
    pages: int | None = None,
    torch_device: str | None = None,
    extractor_version: str | None = None,
    interrupt: Callable[[], None] | None = None,
) -> Any:
    """Read the PDF ``raw`` with Marker in a worker process.

    ``task``: ``"markdown"``, the markdown renderer's text; ``"chunks"``,
    the Document IR of the chunks renderer's answer (``chunk_output_to_ir``,
    with ``extractor_version``), as a JSON-ready dict. ``options``: Marker's
    config. ``pages``: how many pages it reads (its time limit), else counted
    here. ``torch_device`` is the worker's ``TORCH_DEVICE``; this process's
    environment is never changed. ``interrupt`` raises to stop the reading
    (a cancelled import): the worker is stopped and the exception goes on."""

    timeout = max(_WORKER_MIN_SECONDS, _WORKER_SECONDS_PER_PAGE * (pages if pages is not None else _page_count(raw)))
    env = dict(os.environ)
    if torch_device:
        env["TORCH_DEVICE"] = str(torch_device)
    with tempfile.TemporaryDirectory(prefix="learnloop-marker-") as tmp:
        directory = Path(tmp)
        (directory / "source.pdf").write_bytes(raw)
        request = {"task": task, "options": dict(options), "extractor_version": extractor_version}
        (directory / "request.json").write_text(json.dumps(request), encoding="utf-8")
        log_path = directory / "worker.log"
        with open(log_path, "wb") as log:
            try:
                worker = subprocess.Popen(
                    [sys.executable, "-P", "-c", _WORKER, str(directory)],
                    stdin=subprocess.PIPE, stdout=log, stderr=log, env=env,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except OSError as exc:
                raise MarkerWorkerError(
                    f"Marker's worker could not start ({type(exc).__name__})", health_flag=WORKER_CRASHED
                ) from None
            try:
                returncode = _wait(worker, timeout, interrupt)
            finally:
                if worker.poll() is None:
                    worker.kill()
                    worker.wait()
                if worker.stdin is not None:
                    worker.stdin.close()
        answer = _answer(directory / "answer.json")
        if answer is None:
            tail = _tail(log_path)
            LOG.warning("Marker's worker stopped (exit %s) before it answered; its log ends:\n%s", returncode, tail)
            raise MarkerWorkerError(
                f"Marker stopped before it finished reading the PDF (worker exit {returncode})",
                health_flag=WORKER_CRASHED,
            )
        if "result" in answer:
            return answer["result"]
        LOG.info("Marker could not read the PDF; its worker's log ends:\n%s", _tail(log_path))
        raise MarkerWorkerError(f"Marker could not read the PDF: {answer.get('error') or 'no answer'}")


def _wait(worker: subprocess.Popen, timeout: float, interrupt: Callable[[], None] | None) -> int:
    deadline = time.monotonic() + timeout
    while True:
        try:
            return worker.wait(timeout=max(0.0, min(_POLL_SECONDS, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        if interrupt is not None:
            interrupt()
        if time.monotonic() >= deadline:
            limit = f"{timeout / 60:.0f} minutes" if timeout >= 120 else f"{timeout:.0f} seconds"
            raise MarkerWorkerError(
                f"Marker did not finish reading the PDF within {limit}", health_flag=WORKER_TIMED_OUT
            )


def _page_count(raw: bytes) -> int:
    """The PDF's pages, read by pypdf (pure Python: never pdfium here)."""

    try:
        from pypdf import PdfReader

        return len(PdfReader(io.BytesIO(raw)).pages)
    except Exception:  # noqa: BLE001 - unreadable here: the time a long book gets
        return _WORKER_UNKNOWN_PAGES


def _answer(path: Path) -> dict[str, Any] | None:
    try:
        answer = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return answer if isinstance(answer, dict) and ("result" in answer or "error" in answer) else None


def _tail(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    return data[-_LOG_TAIL:].decode("utf-8", errors="replace")


# -- the worker's side ------------------------------------------------------------


def _worker_main() -> None:
    """The private directory in ``sys.argv[1]``: ``request.json`` and
    ``source.pdf`` in, ``answer.json`` (``{"result": ...}`` or
    ``{"error": ...}``) out."""

    _exit_with_parent()
    directory = Path(sys.argv[1])
    try:
        request = json.loads((directory / "request.json").read_text(encoding="utf-8"))
        answer: dict[str, Any] = {"result": _read(request, directory / "source.pdf")}
    except Exception as exc:  # noqa: BLE001 - reported to the caller, which decides
        answer = {"error": f"{type(exc).__name__}: {exc}"[:_LOG_TAIL]}
    partial = directory / "answer.json.partial"
    partial.write_text(json.dumps(answer), encoding="utf-8")
    os.replace(partial, directory / "answer.json")
    # The answer is written: leave now. An interpreter shutdown would tear
    # down torch and wait on whatever threads Marker's libraries left behind.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:  # noqa: BLE001 - only a log
            pass
    os._exit(0)


def _exit_with_parent() -> None:
    """Stop when the process that started this one is gone (the sidecar quit
    or was killed): only it holds the other end of stdin, so stdin ends.

    It reads the file descriptor itself: a thread blocked inside
    ``sys.stdin``'s buffered reader holds its lock, which aborts the
    interpreter at shutdown."""

    def watch() -> None:
        try:
            while os.read(0, 4096):
                pass
        except OSError:  # a broken stdin means the same
            pass
        os._exit(_ORPHANED)

    threading.Thread(target=watch, name="marker-worker-parent", daemon=True).start()


def _read(request: Mapping[str, Any], path: Path) -> Any:
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict

    parser = ConfigParser(dict(request["options"]))
    converter = PdfConverter(
        config=parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=parser.get_processors(),
        renderer=parser.get_renderer(),
        llm_service=parser.get_llm_service(),
    )
    rendered = converter(str(path))
    if request["task"] == "markdown":
        from marker.output import text_from_rendered

        text, _, _images = text_from_rendered(rendered)
        return text or ""
    if request["task"] == "chunks":
        from learnloop.ingest.extractors.marker import chunk_output_to_ir
        from learnloop.ingest.extractors.pypdf import read_embedded_outline

        ir = chunk_output_to_ir(
            blocks=list(getattr(rendered, "blocks", [])),
            metadata=dict(getattr(rendered, "metadata", {}) or {}),
            page_info=dict(getattr(rendered, "page_info", {}) or {}),
            extractor_version=str(request["extractor_version"]),
            embedded_outline=read_embedded_outline(path.read_bytes()),
        )
        return ir.model_dump(mode="json")
    raise ValueError(f"unknown task {request['task']!r}")


__all__ = ["MarkerWorkerError", "WORKER_CRASHED", "WORKER_TIMED_OUT", "run_marker"]
