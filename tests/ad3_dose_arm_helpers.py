"""What other test files use from ``tests/test_ad3_dose_arm.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from contextlib import closing
from typing import Any

from learnloop.adaptive_difficulty import dose as D
from learnloop.db.connection import connect
from learnloop.db.stores import ad_serving
from learnloop.vault.loader import load_vault

from tests.ad1_reading_opportunities_helpers import FakeMap, _setup


QUIET = "[adaptive_difficulty]\noutside_forecasters = []\nfeature_audit = false\n"


def _arm(tmp_path, *, config: str = "") -> tuple[Any, Any, Any]:
    paths, _vault, repo = _setup(tmp_path, config=QUIET + config)
    return paths, load_vault(paths.root), repo


def _boundary(visit: str = "visit1", section: str = "u1", **flags: Any) -> D.Boundary:
    return D.Boundary(visit_id=visit, extraction_id="ext1", section_id=section, **flags)


def _draws(paths) -> list[dict[str, Any]]:
    with closing(connect(paths.sqlite_path)) as connection:
        return [row for row in ad_serving.dose_rows(connection) if row["row_kind"] == "draw"]


def _mapping(**changes: Any) -> FakeMap:
    mapping = FakeMap()
    # A second worked example cited by the LO and not in section u1 (the extra example's source).
    mapping.examples["ext1"] = {"we1", "we2"}
    mapping.spans[("ext1", "we2")] = ["lo_svd_definition"]
    for key, value in changes.items():
        setattr(mapping, key, value)
    return mapping
