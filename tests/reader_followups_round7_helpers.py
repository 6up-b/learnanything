"""What other test files use from ``tests/test_reader_followups_round7.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from learnloop.instructional import reader_followups as RF

from tests.recap_fixtures import EXT
from tests.reader_followups_helpers import NOW_MIN, _candidate, _plan, _seeded
from tests.reader_followups_round4_helpers import QD, QR, _ByIntent


B = "pi_svd_define_003"


def _dropped_retention(tmp_path, monkeypatch):
    """Round 6's F18 state: B licensed by [D, R], R no longer in the receipt."""

    vault, repo, session = _seeded(tmp_path)
    asked = [RF.Question(key=QD, purpose=RF.PURPOSE_DISCRIMINATING, learning_object_ids=["lo_svd_definition"]),
             RF.Question(key=QR, purpose=RF.PURPOSE_RETENTION, learning_object_ids=["lo_svd_definition"],
                         facet_ids=["recall"], attempt_ids=["att_book"])]
    monkeypatch.setattr(RF, "open_questions", lambda *_a, **_k: (list(asked), []))
    monkeypatch.setattr(RF, "_exposure_scope", lambda *_a, **_k: ["ext_we", EXT])
    search = _ByIntent({"discriminate": [[_candidate(B, 1.0, 0.0, 3.0)]],
                        "retention": [[_candidate(B, 1.0, 0.0, 3.0)], [_candidate(B, 1.0, 0.0, 3.0)]]})
    first = _plan(vault, repo, session, search)
    retention_entry = next(entry for entry in first["valuation"]["questions"] if entry["key"] == QR)
    asked[:] = asked[:1]
    row = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    [commitment_id] = row["followup_commitment_ids"]
    assert [entry["key"] for entry in row["valuation"]["questions"]] == [QD]
    return vault, repo, row, commitment_id, retention_entry
