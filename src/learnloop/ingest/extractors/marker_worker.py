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
directory) on a private directory holding the PDF. The request (Marker's
options, which can carry an API key) goes to the worker through its stdin,
never a file or the command line, so nothing a killed process leaves on disk
holds a credential. The worker writes its answer to a file in the directory;
Marker's own output (progress bars, warnings, anything it prints) goes to a
log there, never to the sidecar's stdout, which carries JSON-RPC. The worker
loads Marker's models for each reading and frees them when it ends.

A worker that crashes, or runs out of time, stops there: the reading fails
with ``MarkerWorkerError`` naming it in ``health_flag``, and under ``engine =
"auto"`` the import falls back to pypdf as it did for any Marker failure
(``extract_with_fallback`` records the flag). A cancelled import stops the
worker (``interrupt``, checked while it reads), and so does the end of the
process that started it: the worker watches its stdin, whose other end only
that process holds, and removes its directory's files before it goes.

The worker can start processes of its own (pdftext's pool, with
``pdftext_workers`` above 1), and none outlives its reading. On POSIX the
worker leads a process group of its own: when a reading ends, however it
ends, the whole group is killed, and an orphaned worker kills its group
itself. On Windows the worker puts itself in a job object that kills every
process in it once the worker's handle closes, that is when the worker
exits, is killed or crashes.
"""

from __future__ import annotations

import io
import json
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, NoReturn

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
# What the worker writes in its directory: all an orphaned worker removes.
_SOURCE = "source.pdf"
_ANSWER = "answer.json"
_PARTIAL = "answer.json.partial"
_LOG = "worker.log"


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
    request = json.dumps({"task": task, "options": dict(options), "extractor_version": extractor_version})
    with tempfile.TemporaryDirectory(prefix="learnloop-marker-") as tmp:
        directory = Path(tmp)
        (directory / _SOURCE).write_bytes(raw)
        log_path = directory / _LOG
        with open(log_path, "wb") as log:
            try:
                worker = subprocess.Popen(
                    [sys.executable, "-P", "-c", _WORKER, str(directory)],
                    stdin=subprocess.PIPE, stdout=log, stderr=log, env=env, **_own_process_group(),
                )
            except OSError as exc:
                raise MarkerWorkerError(
                    f"Marker's worker could not start ({type(exc).__name__})", health_flag=WORKER_CRASHED
                ) from None
            sender = _send(worker, (request + "\n").encode("utf-8"))
            try:
                _wait(worker, timeout, interrupt)
            finally:
                returncode = _stop(worker, sender)
        answer = _answer(directory / _ANSWER)
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


def _own_process_group() -> dict[str, Any]:
    """POSIX: the worker leads a new session, so its process group is it and
    everything it starts. Windows: no console window (its job object is the
    worker's own, ``_contain_descendants``)."""

    if os.name == "posix":
        return {"start_new_session": True}
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


def _send(worker: subprocess.Popen, request: bytes) -> threading.Thread:
    """Write the request to the worker's stdin and keep stdin open (its end
    is how the worker knows this process is alive). A thread writes it, so a
    worker that never reads cannot hold this one past its time limit."""

    def send() -> None:
        if worker.stdin is None:
            return
        try:
            worker.stdin.write(request)
            worker.stdin.flush()
        except (OSError, ValueError):  # the worker is gone: its missing answer says so
            pass

    sender = threading.Thread(target=send, name="marker-worker-request", daemon=True)
    sender.start()
    return sender


def _wait(worker: subprocess.Popen, timeout: float, interrupt: Callable[[], None] | None) -> None:
    deadline = time.monotonic() + timeout
    while True:
        if _exited(worker, max(0.0, min(_POLL_SECONDS, deadline - time.monotonic()))):
            return
        if interrupt is not None:
            interrupt()
        if time.monotonic() >= deadline:
            limit = f"{timeout / 60:.0f} minutes" if timeout >= 120 else f"{timeout:.0f} seconds"
            raise MarkerWorkerError(
                f"Marker did not finish reading the PDF within {limit}", health_flag=WORKER_TIMED_OUT
            )


def _exited(worker: subprocess.Popen, seconds: float) -> bool:
    """Whether the worker exits within ``seconds``. Where ``os.waitid`` exists
    (Linux) an exited worker is left unreaped, so its pid, which is its
    process group's id, cannot be reused before ``_stop`` kills the group."""

    if not hasattr(os, "waitid"):
        try:
            worker.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            return False
        return True
    end = time.monotonic() + seconds
    delay = 0.0005
    while True:
        try:
            if os.waitid(os.P_PID, worker.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None:
                return True
        except ChildProcessError:  # already reaped
            return True
        remaining = end - time.monotonic()
        if remaining <= 0:
            return False
        delay = min(delay * 2, remaining, 0.05)
        time.sleep(delay)


def _stop(worker: subprocess.Popen, sender: threading.Thread | None = None) -> int:
    """End the reading's processes, the worker and everything it started,
    whether it answered, crashed, ran out of time or was cancelled; reap the
    worker and close its stdin. Returns the worker's exit status."""

    if os.name == "posix":
        # The group outlives its leader while any process it started runs.
        try:
            os.killpg(worker.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    elif worker.poll() is None:
        worker.kill()  # its job object then kills what it started
    returncode = worker.wait()
    if sender is not None:
        sender.join(timeout=5.0)
    if worker.stdin is not None:
        try:
            worker.stdin.close()
        except OSError:  # a request it never read
            pass
    return returncode


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
    """The private directory in ``sys.argv[1]``: the request on stdin (one
    JSON line), ``source.pdf`` in, ``answer.json`` (``{"result": ...}`` or
    ``{"error": ...}``) out."""

    directory = Path(sys.argv[1])
    _contain_descendants()
    request_line = _read_request()
    if request_line is None:  # the process that started it is already gone
        _orphaned(directory)
    _exit_with_parent(directory)
    try:
        request = json.loads(request_line)
        answer: dict[str, Any] = {"result": _read(request, directory / _SOURCE)}
    except Exception as exc:  # noqa: BLE001 - reported to the caller, which decides
        answer = {"error": f"{type(exc).__name__}: {exc}"[:_LOG_TAIL]}
    partial = directory / _PARTIAL
    partial.write_text(json.dumps(answer), encoding="utf-8")
    os.replace(partial, directory / _ANSWER)
    # The answer is written: leave now. An interpreter shutdown would tear
    # down torch and wait on whatever threads Marker's libraries left behind.
    # The caller then ends whatever processes this one started.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.flush()
        except Exception:  # noqa: BLE001 - only a log
            pass
    os._exit(0)


def _read_request() -> bytes | None:
    """The request's line from stdin (read from the descriptor, as the
    watcher does), or None when stdin ends first."""

    data = bytearray()
    while not data.endswith(b"\n"):
        try:
            chunk = os.read(0, 65536)
        except OSError:
            return None
        if not chunk:
            return None
        data += chunk
    return bytes(data)


def _exit_with_parent(directory: Path) -> None:
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
        _orphaned(directory)

    threading.Thread(target=watch, name="marker-worker-parent", daemon=True).start()


def _orphaned(directory: Path) -> NoReturn:
    """The process that started this one is gone, and with it the cleanup of
    the private directory: remove this worker's own files there (only those,
    and the directory if that empties it), then end this process and every
    process it started."""

    for name in (_SOURCE, _PARTIAL, _ANSWER, _LOG):
        try:
            (directory / name).unlink()
        except OSError:
            pass
    try:
        directory.rmdir()
    except OSError:  # something else is in it, or it is already gone
        pass
    if os.name == "posix" and os.getpgrp() == os.getpid():
        # This process leads its group (started by run_marker): the group is
        # it and what it started. Never a group this process merely joined.
        try:
            os.killpg(os.getpgrp(), signal.SIGKILL)
        except OSError:
            pass
    os._exit(_ORPHANED)


def _contain_descendants() -> None:
    """Windows: put this process in a job object that kills every process in
    it when its last handle closes. The handle is this process's alone (never
    inherited) and is never closed here, so the job ends with this process,
    however that ends, and takes what it started with it. POSIX does this
    with the process group run_marker starts the worker in."""

    if os.name != "nt":
        return
    try:
        _assign_to_kill_on_close_job()
    except Exception as exc:  # noqa: BLE001 - containment is best effort; the reading goes on
        print(f"marker worker: no job object ({type(exc).__name__}: {exc})", file=sys.stderr, flush=True)


def _job_limit_information() -> Any:
    """``JOBOBJECT_EXTENDED_LIMIT_INFORMATION`` (144 bytes on 64-bit Windows)."""

    import ctypes

    class _Basic(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_uint64)
            for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
            )
        ]

    class _Extended(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _Basic),
            ("IoInfo", _IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    return _Extended


def _assign_to_kill_on_close_job() -> None:  # pragma: no cover - Windows only
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    job_object_extended_limit_information = 9
    job_object_limit_kill_on_job_close = 0x2000

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
    info = _job_limit_information()()
    info.BasicLimitInformation.LimitFlags = job_object_limit_kill_on_job_close
    if not kernel32.SetInformationJobObject(
        job, job_object_extended_limit_information, ctypes.byref(info), ctypes.sizeof(info)
    ):
        raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]
    if not kernel32.AssignProcessToJobObject(job, kernel32.GetCurrentProcess()):
        raise ctypes.WinError(ctypes.get_last_error())  # type: ignore[attr-defined]


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
