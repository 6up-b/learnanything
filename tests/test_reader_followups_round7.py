"""Reader RW6b part 1: round 7 (F19, F20; Sol verify job
``20261031-200207-4SHZVh``), reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Round 7 (F19, F20)").

* F19: re-valuation's licensing pruning is computed inside its transaction
  from the freshly read row, so a publication that restored a question
  between the first read and the write is never undone.
* F20: a chosen line without a valid ``licensing`` list is malformed (no
  fallback to a single question; RW6b never landed): held as
  ``licensing_unreadable``, and re-valuation retires and re-asks it.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from tests.recap_fixtures import at
from tests.reader_followups_helpers import NOW_MIN, _now
from tests.reader_followups_round4_helpers import QD, QR, A, _check, _due, _studied_related_example
from tests.reader_followups_round5_helpers import _discrimination_still_needs_it, _shared
from tests.reader_followups_round7_helpers import B, _dropped_retention

def test_f19_a_publication_between_the_read_and_the_write_keeps_the_restored_license(tmp_path, monkeypatch):
    vault, repo, row, commitment_id, retention_entry = _dropped_retention(tmp_path, monkeypatch)
    restored = []

    def valuer_with_an_interleaved_publication(question, item_id):
        if not restored:
            # Another process publishes meanwhile: retention is back in the receipt.
            with repo.connection() as connection:
                current = RDG.digest(connection, row["id"])
                valuation = dict(current["valuation"])
                valuation["questions"] = [*valuation["questions"], retention_entry]
                RDG.update_digest(connection, row["id"], valuation_json=valuation)
                connection.commit()
            restored.append(True)
        return _discrimination_still_needs_it(question, item_id)

    RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 90), valuer=valuer_with_an_interleaved_publication,
                       clock=at(NOW_MIN + 90))
    assert restored
    with repo.connection() as connection:
        stored = RDG.digest(connection, row["id"])
    assert {entry["key"] for entry in stored["valuation"]["questions"]} == {QD, QR}
    [line] = stored["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD, QR]  # round 6 pruned R here
    # So retention's rule still applies at serve: a related worked example holds B.
    due, minutes_due = _due(row)
    _studied_related_example(repo, minutes_due - 60, item_id=B)
    check = _check(vault, repo, commitment_id, due)
    assert B not in check.eligible and dict(check.gated)[B]["reasons"] == ["related_worked_example"]


def test_f19_a_question_still_absent_from_the_fresh_receipt_is_pruned(tmp_path, monkeypatch):
    vault, repo, row, commitment_id, _entry = _dropped_retention(tmp_path, monkeypatch)
    RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 90), valuer=_discrimination_still_needs_it,
                       clock=at(NOW_MIN + 90))
    with repo.connection() as connection:
        [line] = RDG.digest(connection, row["id"])["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD]
    assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"


def test_f20_a_line_without_a_licensing_list_is_held_and_retired_as_unreadable(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    valuation = dict(row["valuation"])
    legacy = {key: value for key, value in valuation["chosen"][0].items() if key != "licensing"}
    valuation["chosen"] = [legacy]
    with repo.connection() as connection:
        RDG.update_digest(connection, row["id"], valuation_json=valuation)
        connection.commit()
    due, _minutes = _due(row)
    check = _check(vault, repo, commitment_id, due)
    assert A not in check.eligible and dict(check.gated)[A]["reasons"] == ["licensing_unreadable"]
    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_discrimination_still_needs_it, clock=at(600))
    [retired] = report["retired"]
    assert retired["reason"] == RF.RETIRE_UNREADABLE
    with repo.connection() as connection:
        digest = RDG.digest(connection, row["id"])
    assert digest["status"] == "incomplete"
    assert next(e for e in digest["valuation"]["questions"] if e["key"] == QR)["incomplete"] is True
