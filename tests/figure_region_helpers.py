"""What other test files use from ``tests/test_figure_region.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import base64
import json

import pytest

import learnloop.reader.span_view as SV


PAGE_RENDERS: list[object] = []


@pytest.fixture
def crops(monkeypatch):
    """The PDF crop as a recorder: each crop's bytes name its box; a whole
    page render is recorded too (it must never be sent)."""

    made: list[list[float]] = []

    def crop(path, page, bbox):
        made.append([float(value) for value in bbox])
        data = ("CROP:" + json.dumps([round(float(value), 2) for value in bbox])).encode()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii"), [612.0, 792.0]

    def page_render(path, page):
        PAGE_RENDERS.append((path, page))
        return "data:image/png;base64," + base64.b64encode(b"WHOLE PAGE").decode("ascii"), [612.0, 792.0]

    monkeypatch.setattr(SV, "_original_pdf_for", lambda repo, extraction_id: "book.pdf")
    monkeypatch.setattr(SV, "_original_pdf_path", lambda repo, revision, uri: "book.pdf")
    monkeypatch.setattr(SV, "_local_pdf_block_crop", crop)
    monkeypatch.setattr(SV, "_local_pdf_page_render", page_render)
    PAGE_RENDERS.clear()
    return made


REGION = {"spanId": "p4", "bbox": [150.0, 120.0, 260.0, 220.0]}
