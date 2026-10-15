"""A stand-in ``marker`` package written to disk, for tests that need Marker.

Marker reads a PDF in a worker process (``learnloop.ingest.extractors.marker_worker``),
so a fake held in this process's ``sys.modules`` would never reach it. The
``fake_marker`` fixture writes a small ``marker`` package to a temporary
directory, puts it on ``sys.path`` (so ``marker_available()`` sees it here)
and on ``PYTHONPATH`` (so the worker, which inherits the environment, imports
it). Like Marker's ``PdfProvider``, its converter opens the PDF with pypdfium2,
reads every page's text layer and renders every page, then answers as the
``markdown`` or ``chunks`` renderer does.

Its behaviour is set through the environment, which the worker inherits:
``FAKE_MARKER_MODE`` (``ok``, ``crash`` - a native abort, ``hang``, ``raise``,
``chatty`` - prints to stdout first) and ``FAKE_MARKER_MARKDOWN`` (the
markdown to answer with). Each conversion appends what it saw (process,
thread, file, config, ``TORCH_DEVICE``) to a JSON-lines file:
``fake_marker.calls()``.

With ``pdftext_workers`` above 1 it starts that many worker processes, as
pdftext does (a ``ProcessPoolExecutor`` of forked processes reading the text
layer): each records its pid (``fake_marker.descendants()``) before the
converter goes on, and outside ``ok`` and ``chatty`` they sleep, so a crash,
a hang, an error or a cancel finds them alive.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_CONVERTER = '''
import json
import multiprocessing
import os
import sys
import threading
import time
from concurrent.futures import ProcessPoolExecutor


def _record(entry, variable="FAKE_MARKER_CAPTURE"):
    path = os.environ.get(variable)
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\\n")


def _pool_started():
    _record({"pid": os.getpid(), "parent": os.getppid()}, "FAKE_MARKER_DESCENDANTS")


def _pool_read(mode, filepath, indices):
    if mode not in ("ok", "chatty"):
        time.sleep(600)
    return _read_pages(filepath, indices)


def _read_pages(filepath, indices):
    # As Marker's PdfProvider does: pdfium opens the file, reads each
    # page's text layer (pdftext) and renders each page for the models.
    import pypdfium2 as pdfium

    document = pdfium.PdfDocument(filepath)
    pages = []
    try:
        for index in indices if indices is not None else range(len(document)):
            page = document[index]
            try:
                textpage = page.get_textpage()
                try:
                    text = " ".join(textpage.get_text_range().split())
                finally:
                    textpage.close()
                page.render(scale=1.0).close()
            finally:
                page.close()
            pages.append((index, text))
    finally:
        document.close()
    return pages


def _start_pool(workers, mode, filepath, indices):
    """pdftext's pool: forked workers, each with a share of the pages."""

    if indices is None:
        import pypdfium2 as pdfium

        document = pdfium.PdfDocument(filepath)
        try:
            indices = list(range(len(document)))
        finally:
            document.close()
    shares = [indices[start::workers] for start in range(workers)]
    pool = ProcessPoolExecutor(
        max_workers=workers, mp_context=multiprocessing.get_context("fork"), initializer=_pool_started
    )
    futures = [pool.submit(_pool_read, mode, filepath, share) for share in shares]
    deadline = time.monotonic() + 60
    path = os.environ.get("FAKE_MARKER_DESCENDANTS")
    while time.monotonic() < deadline:  # every pool worker is up before the converter goes on
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as handle:
                if sum(1 for line in handle if line.strip()) >= workers:
                    break
        time.sleep(0.02)
    return pool, futures


class _Rendered:
    def __init__(self, markdown):
        self.markdown = markdown


class _Chunks:
    def __init__(self, pages):
        self.blocks = [
            {
                "id": f"/page/{index}/Text/0",
                "block_type": "Text",
                "html": f"<p>{text}</p>",
                "page": index,
                "polygon": [[72.0, 72.0], [540.0, 72.0], [540.0, 100.0], [72.0, 100.0]],
                "bbox": [72.0, 72.0, 540.0, 100.0],
                "section_hierarchy": None,
                "images": {},
            }
            for index, text in pages
        ]
        self.metadata = {
            "table_of_contents": [],
            "page_stats": [
                {"page_id": index, "text_extraction_method": "pdftext", "block_counts": [["Text", 1]]}
                for index, _ in pages
            ],
        }
        self.page_info = {}


class PdfConverter:
    def __init__(self, config, artifact_dict, processor_list, renderer, llm_service):
        self.config = dict(config)
        self.llm_service = llm_service

    def __call__(self, filepath):
        mode = os.environ.get("FAKE_MARKER_MODE", "ok")
        _record({
            "pid": os.getpid(),
            "thread": threading.current_thread().name,
            "filepath": filepath,
            "config": self.config,
            "llm_service": self.llm_service,
            "torch_device": os.environ.get("TORCH_DEVICE"),
        })
        wanted = self.config.get("page_range")
        indices = [int(page) for page in str(wanted).split(",")] if wanted else None
        workers = int(self.config.get("pdftext_workers") or 1)
        pool = futures = None
        if workers > 1:
            pool, futures = _start_pool(workers, mode, filepath, indices)
        if mode == "crash":
            os.abort()
        if mode == "hang":
            time.sleep(600)
        if mode == "raise":
            raise RuntimeError("the fake marker could not read it")
        if mode == "chatty":
            print("marker progress on stdout")
            sys.stdout.flush()
        if pool is not None:
            pages = sorted(page for future in futures for page in future.result())
            pool.shutdown()
        else:
            pages = _read_pages(filepath, indices)
        if self.config.get("output_format") == "chunks":
            return _Chunks(pages)
        return _Rendered(os.environ.get("FAKE_MARKER_MARKDOWN") or "\\n\\n".join(text for _, text in pages))
'''

_PARSER = '''
class ConfigParser:
    def __init__(self, options):
        self.options = dict(options)

    def generate_config_dict(self):
        return dict(self.options)

    def get_processors(self):
        return []

    def get_renderer(self):
        return self.options.get("output_format", "markdown") + "-renderer"

    def get_llm_service(self):
        return self.options.get("llm_service")
'''

_FILES = {
    "marker/__init__.py": "",
    "marker/config/__init__.py": "",
    "marker/config/parser.py": _PARSER,
    "marker/converters/__init__.py": "",
    "marker/converters/pdf.py": _CONVERTER,
    "marker/models.py": "def create_model_dict():\n    return {'models': 'loaded'}\n",
    "marker/output.py": "def text_from_rendered(rendered):\n    return rendered.markdown, 'md', {}\n",
}


class FakeMarker:
    def __init__(self, root: Path, capture: Path, descendants: Path):
        self.root = root
        self.capture = capture
        self.descendants_capture = descendants

    def calls(self) -> list[dict]:
        return _lines(self.capture)

    def descendants(self) -> list[dict]:
        """The pool workers the converter started (``pdftext_workers`` > 1)."""

        return _lines(self.descendants_capture)


def _lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture
def fake_marker(tmp_path_factory, monkeypatch):
    root = tmp_path_factory.mktemp("fake-marker")
    for relative, source in _FILES.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
    capture = root / "calls.jsonl"
    descendants = root / "descendants.jsonl"
    before = {name for name in sys.modules if name == "marker" or name.startswith("marker.")}
    monkeypatch.syspath_prepend(str(root))
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(filter(None, [str(root), os.environ.get("PYTHONPATH")])))
    monkeypatch.setenv("FAKE_MARKER_CAPTURE", str(capture))
    monkeypatch.setenv("FAKE_MARKER_DESCENDANTS", str(descendants))
    monkeypatch.delenv("FAKE_MARKER_MODE", raising=False)
    monkeypatch.delenv("FAKE_MARKER_MARKDOWN", raising=False)
    yield FakeMarker(root, capture, descendants)
    # Never leave the fake importable for a later test (find_spec reads sys.modules).
    for name in [name for name in sys.modules if (name == "marker" or name.startswith("marker.")) and name not in before]:
        del sys.modules[name]
