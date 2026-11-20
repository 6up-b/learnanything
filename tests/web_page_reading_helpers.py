"""A web page as the code before UX-11 read it, for the test files that need a library holding one.

``tests/fixtures/ux11_extraction_before.json`` holds what that code's production Add path stored for the two
web samples (captured before the change, never regenerated). :func:`old_web_reading_services` is the import
seams of a runner that reads a page that way: the stored reading under its identity (``html`` version 2), so
a library built with it is one whose pages were read before, and the current code can then open it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.content.pipeline.runner import RunnerServices
from learnloop.ingest.ir import DocumentIR

from tests.ux_phase1_support import fake_services

BEFORE: dict[str, Any] = json.loads(
    (Path(__file__).resolve().parent / "fixtures" / "ux11_extraction_before.json").read_text(encoding="utf-8")
)
OLD_IDENTITY = {"extractor": "html", "extractor_version": "2", "model_versions": {}, "config": {}}


def old_web_reading_services(sample: str, **overrides: Any) -> RunnerServices:
    """Runner seams that read ``samples/<sample>`` as the code before UX-11 did."""

    old_ir = DocumentIR.model_validate(BEFORE["html"][sample]["ir"])
    return fake_services(
        extract=lambda fetched, category, job: old_ir.model_copy(deep=True),
        describe_extraction=lambda fetched, category, job: dict(OLD_IDENTITY),
        **overrides,
    )
