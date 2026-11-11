"""What other test files use from ``tests/test_ad_guard_offer_receipts.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing


ITEM = "pi_e1"
AT = "2026-10-01T09:00:00Z"


def seed_learner_pick(paths, attempt_id: str, item_id: str = ITEM, *, offered: bool = True,
                      components: dict | None = None, tag: str = "") -> str:
    """Bind ``attempt_id`` to a scheduler slate candidate the learner picked from a published offer
    (the shape the owner's probability vault holds): a slate, its candidate (no forced follow-up
    component unless ``components`` says so), the offer receipt (when ``offered``), the submission
    intent naming the candidate, and the attempt's own receipts."""

    slate, candidate, submission = f"slate{tag}", f"cand-{attempt_id}", f"sub-{attempt_id}"
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.execute("INSERT OR IGNORE INTO sessions(id, started_at) VALUES ('s1', ?)", (AT,))
        connection.execute(
            "INSERT OR IGNORE INTO scheduler_slates(id, generated_at, selection_policy, session_context_json, "
            "config_snapshot_json, algorithm_version, created_at, updated_at) "
            "VALUES (?, ?, 'policy', '{}', '{}', 'test', ?, ?)", (slate, AT, AT, AT))
        connection.execute(
            "INSERT INTO scheduler_slate_candidates(id, slate_id, practice_item_id, rank, selected_mode, priority, "
            "components_json, algorithm_version, created_at, selection_propensity, was_returned, returned_rank) "
            "VALUES (?, ?, ?, 1, 'practice', 1, ?, 'test', ?, .25, 1, 1)",
            (candidate, slate, item_id, json.dumps(components or {}), AT))
        if offered:
            connection.execute(
                "INSERT INTO scheduler_offer_receipts VALUES (?, ?, 'desktop_queue', 'learnloop-events-v1', ?)",
                (slate, json.dumps([candidate]), AT))
        connection.execute(
            "INSERT INTO submission_intents(submission_id, session_id, practice_item_id, scheduler_candidate_id, "
            "entry_surface, created_at) VALUES (?, 's1', ?, ?, 'desktop_practice', ?)",
            (submission, item_id, candidate, AT))
        connection.execute(
            "UPDATE practice_attempts SET submission_id = ?, scheduler_candidate_id = ?, scheduler_slate_id = ?, "
            "collection_version = 'learnloop-events-v1' WHERE id = ?", (submission, candidate, slate, attempt_id))
        connection.commit()
    return candidate
