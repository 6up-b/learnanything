"""What other test files use from ``tests/test_reader_followups_round5.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from tests.reader_followups_helpers import _candidate, _plan, _seeded
from tests.reader_followups_round4_helpers import QD, QR, A, _ByIntent, _questions


def _shared(tmp_path, monkeypatch):
    """Retention creates A (its provenance), discrimination shares it."""

    vault, repo, session = _seeded(tmp_path)
    _questions(monkeypatch)
    row = _plan(vault, repo, session, _ByIntent({"retention": [[_candidate(A, 1.0, 0.0, 3.0)]],
                                                 "discriminate": [[_candidate(A, 1.0, 0.0, 3.0)]]}))
    [commitment_id] = row["followup_commitment_ids"]
    assert [entry["question"] for entry in row["valuation"]["chosen"][0]["licensing"]] == [QR, QD]
    return vault, repo, row, commitment_id


def _discrimination_still_needs_it(question, item_id):
    if question["intent"] == "discriminate":
        return {"problems": [{"verdict": "act", "reason": "positive_robust_net_value", "checks": [{"ref": item_id}]}]}
    return {"problems": [{"verdict": "stop", "reason": "lcb_value_below_minutes_cost", "checks": []}]}
