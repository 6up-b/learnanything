"""RW5d P2: one engine, two hosts (spec_reader_show_me_figures_v1 G-SM9).

The parity corpus is what the sidecar's wasmtime runner returns, text for
text; ``sketchParity.test.ts`` replays it in the desktop's engine host. Here:
the stored corpus is still exactly what the pinned engine gives.
"""

from __future__ import annotations

import json

from learnloop.figures.sketch_engine import ENGINE_SHA256
from tests import sketch_parity_corpus as PC


def test_the_parity_corpus_is_what_the_pinned_engine_returns():
    stored = json.loads(PC.PATH.read_text(encoding="utf-8"))
    assert stored["engine_sha256"] == ENGINE_SHA256
    assert stored == PC.build(), "regenerate with: uv run python -m tests.sketch_parity_corpus"


def test_the_corpus_covers_every_read_kind_and_a_clock():
    stored = json.loads(PC.PATH.read_text(encoding="utf-8"))
    ops = {call["op"] for case in stored["cases"] for call in case["calls"]}
    assert ops == {"init", "step", "view", "probes"}
    assert len(stored["cases"]) >= 5
