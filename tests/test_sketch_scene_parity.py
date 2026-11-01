"""RW5d P2: both validators (spec_reader_show_me_figures_v1 §9.1).

The shared corpus is what the sidecar's validator finds, case by case;
``sketchScene.test.ts`` holds the desktop's validator to the same problems.
"""

from __future__ import annotations

import json

from tests import sketch_scene_corpus as SC


def test_the_shared_validator_corpus_is_what_the_sidecar_finds():
    stored = json.loads(SC.PATH.read_text(encoding="utf-8"))
    assert stored == json.loads(json.dumps(SC.build())), "regenerate with: uv run python -m tests.sketch_scene_corpus"


def test_the_corpus_has_valid_and_refused_cases():
    stored = json.loads(SC.PATH.read_text(encoding="utf-8"))
    valid = [case for case in stored["scenes"] if not case["problems"]]
    refused = [case for case in stored["scenes"] if case["problems"]]
    assert len(valid) == 2 and len(refused) >= 20
