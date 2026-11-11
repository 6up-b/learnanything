"""Reader RW6b part 1: round 6, the simplified gate (Sol verify job
``20261031-194450-KFaejV``: F17 reopened, F18), reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Round 6 (simplified gate)").

Cached answer and licensing state for shared checks kept producing findings,
so the design was simplified instead of patched:

* the serve-time gate never reads answered state: it applies the STRICTEST
  exposure rule over ALL the check's licensing questions, answered or not
  (F17: no insert order, timestamp or regrade can relax it);
* the gate is self-contained: the check's own ``chosen`` line carries its
  licensing list (question, intent and what the gate reads), written at
  publication; nothing is looked up in the receipt's question entries, so
  normal re-planning that drops a question from the receipt never makes a
  healthy check unreadable (F18). Re-valuation prunes such a question from
  the line's list;
* only a missing digest row or chosen line is damage (held, fail closed).

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from tests.recap_fixtures import EXT, at
from tests.reader_followups_helpers import NOW_MIN, _attempt, _candidate, _now, _plan, _seeded
from tests.reader_followups_round4_helpers import (
    QD,
    QR,
    A,
    _ByIntent,
    _check,
    _due,
    _studied_related_example,
)
from tests.reader_followups_round5_helpers import _discrimination_still_needs_it, _shared

B = "pi_svd_define_003"


def _answered_then(tmp_path, monkeypatch, variant):
    """A shared check (retention its provenance, discrimination sharing it);
    an unaided success answers retention; re-valuation keeps it for
    discrimination; then ``variant`` changes the answer state."""

    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    _attempt(repo, "att_own", minutes=500, hints=0, item="pi_svd_define_003")
    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_discrimination_still_needs_it, clock=at(600))
    [kept] = report["kept"]
    assert kept["answered_for"] == [QR]
    variant(repo)
    return vault, repo, row, commitment_id


def _same_second_assisted(repo):
    _attempt(repo, "att_same", minutes=600, hints=1, item="pi_svd_define_004")  # stamped at revalued_at


def _earlier_stamped_late_insert(repo):
    _attempt(repo, "att_late", minutes=550, hints=1, item="pi_svd_define_004")  # inserted now, stamped before


def _regrade_of_the_unaided_success(repo):
    with repo.connection() as connection:
        connection.execute("UPDATE practice_attempts SET correctness = 0.0, rubric_score = 0 WHERE id = 'att_own'")
        connection.commit()


def _nothing(_repo):
    pass


def test_f17_no_answer_state_change_can_relax_the_gate_on_a_shared_check(tmp_path, monkeypatch):
    for name, variant in (("same_second", _same_second_assisted), ("earlier_stamped", _earlier_stamped_late_insert),
                          ("regrade", _regrade_of_the_unaided_success), ("still_answered", _nothing)):
        vault, repo, row, commitment_id = _answered_then(tmp_path / name, monkeypatch, variant)
        due, minutes_due = _due(row)
        _studied_related_example(repo, minutes_due - 60)
        check = _check(vault, repo, commitment_id, due)
        assert A not in check.eligible and A in check.held, name
        assert dict(check.gated)[A]["reasons"] == ["related_worked_example"], name
        # Re-valuation judges it on the same input: retired as exposed, both questions re-asked.
        report = RF.revalue_pending(vault, repo, now=due, valuer=_discrimination_still_needs_it,
                                    clock=at(minutes_due), force=True)
        assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_EXPOSED], name


# -- F18: normal re-planning drops a question; the healthy shared check stays live and served -------------


def test_f18_re_planning_that_drops_a_question_keeps_the_shared_check_live_and_served(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)
    # Discrimination is asked first, so B's provenance is its; retention is the secondary licensing question.
    asked = [RF.Question(key=QD, purpose=RF.PURPOSE_DISCRIMINATING, learning_object_ids=["lo_svd_definition"]),
             RF.Question(key=QR, purpose=RF.PURPOSE_RETENTION, learning_object_ids=["lo_svd_definition"],
                         facet_ids=["recall"], attempt_ids=["att_book"])]
    monkeypatch.setattr(RF, "open_questions", lambda *_a, **_k: (list(asked), []))
    monkeypatch.setattr(RF, "_exposure_scope", lambda *_a, **_k: ["ext_we", EXT])
    # Discrimination chooses B (done); retention chooses B too and stops on its budget (shared, incomplete).
    search = _ByIntent({"retention": [[_candidate(B, 1.0, 0.0, 3.0)], [_candidate(B, 1.0, 0.0, 3.0)]],
                        "discriminate": [[_candidate(B, 1.0, 0.0, 3.0)]]})
    first = _plan(vault, repo, session, search)
    assert first["status"] == "incomplete"
    [commitment_id] = first["followup_commitment_ids"]
    # Retention is answered meanwhile: the next plan no longer asks it, and its entry leaves the receipt.
    asked[:] = asked[:1]
    row = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert row["status"] == "planned" and [entry["key"] for entry in row["valuation"]["questions"]] == [QD]
    due, _minutes = _due(row)
    check = _check(vault, repo, commitment_id, due)
    assert B in check.eligible, f"held: {dict(check.gated).get(B)}"  # round 5: licensing_unreadable
    [line] = row["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD, QR]  # the line's own list, intact
    # Re-valuation prunes the dropped question from the line's list and keeps B for discrimination.
    report = RF.revalue_pending(vault, repo, now=_now(NOW_MIN + 90), valuer=_discrimination_still_needs_it,
                                clock=at(NOW_MIN + 90))
    assert report["retired"] == [] and [k["kept_because"] for k in report["kept"]] == [["clears_the_stop"]]
    assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"
    with repo.connection() as connection:
        stored = RDG.digest(connection, row["id"])
    [line] = stored["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD]
    assert B in _check(vault, repo, commitment_id, due).eligible


def test_the_gate_reads_no_receipt_entry_and_no_answered_state():
    import inspect

    from learnloop.scheduling.intent import followup_gate as G

    source = inspect.getsource(G)
    for gone in ("answered_for", "revalued_at", "_active_since", '"questions"'):
        assert gone not in source, gone


def test_a_malformed_licensing_list_is_held_as_unreadable(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    valuation = dict(row["valuation"])
    valuation["chosen"] = [{**valuation["chosen"][0], "licensing": [{"question": QR}]}]  # no intent
    with repo.connection() as connection:
        RDG.update_digest(connection, row["id"], valuation_json=valuation)
        connection.commit()
    due, _minutes = _due(row)
    check = _check(vault, repo, commitment_id, due)
    assert dict(check.gated)[A]["reasons"] == ["licensing_unreadable"]

