"""Reader RW6b part 1: round 8, the re-valuation freshness guard (Sol verify
job ``20261031-211907-zauFg9``), reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Round 8").

Re-valuation now has the whole-row freshness guard publication has: one
digest's decisions (retirements, prunings, re-ask markers, the queue
revision) are computed from one snapshot and committed only if the row is
still that snapshot inside the commit transaction; otherwise all are
discarded and recomputed from the fresh row, a bounded number of times, then
left for the next pass. A scalar ``licensing`` is malformed (unreadable),
never a crash.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from tests.recap_fixtures import at, iso
from tests.test_reader_followups import NOW_MIN, _now
from tests.test_reader_followups_round4 import QD, QR, A, _check, _due
from tests.test_reader_followups_round5 import _shared
from tests.test_reader_followups_round7 import B, _dropped_retention


def _discrimination_stops_retention_needs_it(question, item_id):
    if question["intent"] == "retention":
        return {"problems": [{"verdict": "act", "reason": "positive_robust_net_value", "checks": [{"ref": item_id}]}]}
    return {"problems": [{"verdict": "stop", "reason": "lcb_value_below_minutes_cost", "checks": []}]}


def _stop(*_a):
    return {"problems": [{"verdict": "stop", "reason": "lcb_value_below_minutes_cost", "checks": []}]}


def _stored(repo, row):
    with repo.connection() as connection:
        return RDG.digest(connection, row["id"])


def test_round8_sols_interleaving_keeps_the_shared_check_live(tmp_path, monkeypatch):
    """B carries [D, R]; the first snapshot's receipt has only D; during D's
    valuation a publication restores R; D says stop. Round 7 retired B as
    below the stop; now the pass is discarded and recomputed with R."""

    vault, repo, row, commitment_id, retention_entry = _dropped_retention(tmp_path, monkeypatch)
    calls = []

    def valuer(question, item_id):
        calls.append(question["intent"])
        if len(calls) == 1:
            with repo.connection() as connection:
                current = RDG.digest(connection, row["id"])
                valuation = dict(current["valuation"])
                valuation["questions"] = [*valuation["questions"], retention_entry]
                RDG.update_digest(connection, row["id"], valuation_json=valuation)
                connection.commit()
        return _discrimination_stops_retention_needs_it(question, item_id)

    report = RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 90), valuer=valuer, clock=at(NOW_MIN + 90))
    assert report["retired"] == [] and report["deferred"] == []
    assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"
    [kept] = report["kept"]
    assert kept["kept_because"] == ["clears_the_stop"]
    stored = _stored(repo, row)
    [line] = stored["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD, QR]
    assert {entry["key"] for entry in stored["valuation"]["questions"]} == {QD, QR}
    assert stored["revaluation"]["lines"] == report["kept"] and stored["revalued_on"]
    assert calls == ["discriminate", "discriminate", "retention"]  # the stale pass, then the recomputed one
    due, _minutes = _due(row)
    assert B in _check(vault, repo, commitment_id, due).eligible


def test_round8_a_changed_row_is_recomputed_and_the_second_pass_commits(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    calls = []

    def valuer(question, item_id):
        calls.append(question["intent"])
        if len(calls) == 1:
            with repo.connection() as connection:  # any write to the row, here only its stamp
                RDG.update_digest(connection, row["id"], updated_at=iso(NOW_MIN + 5))
                connection.commit()
        return _stop()

    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=valuer, clock=at(600))
    assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_BELOW_STOP]
    assert C.resolve_disposition(repo, commitment_id) == "stopped"
    assert calls == ["retention", "discriminate", "retention", "discriminate"]  # recomputed once
    assert _stored(repo, row)["revaluation"]["lines"][0]["reason"] == RF.RETIRE_BELOW_STOP


def test_round8_a_row_that_keeps_changing_is_left_for_the_next_pass(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    stamps = iter(range(1, 100))

    def valuer(question, item_id):
        with repo.connection() as connection:
            RDG.update_digest(connection, row["id"], updated_at=iso(NOW_MIN + next(stamps)))
            connection.commit()
        return _stop()

    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=valuer, clock=at(600))
    assert report["deferred"] == [row["id"]] and report["retired"] == [] and report["kept"] == []
    assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"
    stored = _stored(repo, row)
    assert stored["revaluation"] is None and stored["revalued_on"] is None  # the next pass re-values it
    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_stop, clock=at(600))
    assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_BELOW_STOP]


def test_round8_a_scalar_licensing_is_unreadable_not_a_crash(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    valuation = dict(row["valuation"])
    valuation["chosen"] = [{**valuation["chosen"][0], "licensing": 7}]
    with repo.connection() as connection:
        RDG.update_digest(connection, row["id"], valuation_json=valuation)
        connection.commit()
    due, _minutes = _due(row)
    assert dict(_check(vault, repo, commitment_id, due).gated)[A]["reasons"] == ["licensing_unreadable"]
    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_stop, clock=at(600))
    assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_UNREADABLE]
    assert C.resolve_disposition(repo, commitment_id) == "stopped"
