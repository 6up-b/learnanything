"""What other test files use from ``tests/test_reader_rw6b_p2_landing.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from learnloop.db.stores import reader_digests as RDG


DIGEST_ID = "rsd_landing_1"


def _digest(c1, *, los=("lo_eigen", "lo_det")) -> str:
    """An ended reader session's digest row on the C1 vault's book: part 1's "planned with no
    checks" row (so part 1 leaves it), waiting for its narrative."""

    moment = c1.clock.moment
    ended = (moment - timedelta(days=1)).isoformat()
    started = (moment - timedelta(days=1, minutes=40)).isoformat()
    summary = {
        "summary_version": "reader_session_summary_v1", "extraction_id": "ext_book", "activity": True,
        "learning_objects_touched": list(los), "facets_touched": [],
        "inquiries": {"opened": [{"root_exchange_id": "ex_landing", "question_event_id": "ev_landing",
                                  "span_ids": []}], "resolved": [], "still_open": []},
        "inquiry_exchanges": ["ex_landing"],
    }
    with c1.repository.connection() as connection:
        RDG.insert_digest(connection, {
            "id": DIGEST_ID, "extraction_id": "ext_book", "session_key": "v_landing", "visit_ids": ["v_landing"],
            "started_at": started, "ended_at": ended, "status": "planned", "summary": summary,
            "followup_commitment_ids": [], "valuation": {"questions": [], "chosen": [], "chosen_ids": []},
            "created_at": ended})
        connection.commit()
    return DIGEST_ID


def _digest_row(c1) -> dict[str, Any]:
    with c1.repository.connection() as connection:
        return RDG.digest(connection, DIGEST_ID)
