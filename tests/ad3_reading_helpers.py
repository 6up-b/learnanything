"""What other test files use from ``tests/test_ad3_reading.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from typing import Any

from learnloop.db.stores import ad_receipts

from tests.ad23_fakes import LO, SEEDED


def _opportunity(connection: Any, *, key: str, kind: str, subkind: str, source_table: str, at: str,
                 lo: str = LO, doses: dict[str, float] | None = None) -> None:
    ad_receipts.insert_reading_opportunity(connection, {
        "protection_epoch": SEEDED, "opportunity_key": key, "kind": kind, "subkind": subkind, "source_table": source_table,
        "source_id": key, "source_written_at": at, "learning_object_id": lo,
        "facet_doses": doses or {"recall": 1.0}, "dose_offer_id": None, "mapping_version": "ad_reading_map_v1",
        "sweep": "backfill", "sweep_ref": None, "swept_at": at})
