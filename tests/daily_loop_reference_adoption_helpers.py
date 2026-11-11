"""What other test files use from ``tests/test_daily_loop_reference_adoption.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.vault.loader import load_vault
from learnloop.vault.yaml_io import read_yaml, write_yaml

from tests.daily_loop_reader_authored_practice_helpers import LO_ID, QUESTION


def _cite_passage(paths, *, status: str = "active") -> None:
    lo_path = paths.learning_object_path("linear-algebra", LO_ID)
    lo = read_yaml(lo_path)
    lo["provenance"]["source_refs"] = [{
        "ref_type": "canonical_source", "ref_id": "src1", "locator": "span:ext1/s1",
        "source_id": "src1", "extraction_id": "ext1",
    }]
    lo["status"] = status
    write_yaml(lo_path, lo)


def _learner_cards(paths) -> list:
    return [item for item in load_vault(paths.root).practice_items.values() if item.prompt == QUESTION]
