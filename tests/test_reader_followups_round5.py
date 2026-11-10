"""Reader RW6b part 1: Codex verify round 5 (F17), reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Round 5 (F17)").

* A stale ``answered_for`` no longer hides a reopened question (round 6
  removed answered state from the gate altogether: every licensing question
  counts, answered or not).
* The digest lookup fails closed: a reader follow-up whose digest row or
  ``chosen`` line cannot be read is held, never served cold, and re-valuation
  retires it and re-asks what it can name. (A licensing question missing from
  the receipt is not damage since round 6: see test_reader_followups_round6.py.)

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from tests.recap_fixtures import at
from tests.test_reader_followups import _attempt, _candidate, _now, _plan, _seeded
from tests.test_reader_followups_round4 import (
    QD,
    QR,
    A,
    _ByIntent,
    _check,
    _due,
    _questions,
    _studied_related_example,
)

#: ``scheduling.intent.followup_gate.LICENSING_UNREADABLE`` (a literal, so the repro runs on the base).
LICENSING_UNREADABLE = "licensing_unreadable"


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


def test_f17_a_retention_question_reopened_since_the_revaluation_still_tightens_the_gate(tmp_path, monkeypatch):
    vault, repo, row, commitment_id = _shared(tmp_path, monkeypatch)
    # An unaided success answers retention; re-valuation records it and keeps A for discrimination.
    _attempt(repo, "att_own", minutes=500, hints=0, item="pi_svd_define_003")
    report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_discrimination_still_needs_it, clock=at(600))
    [kept] = report["kept"]
    assert kept["answered_for"] == [QR] and kept["kept_because"] == ["clears_the_stop"]
    # A later ASSISTED success reopens retention (answered_since's own rule) ...
    _attempt(repo, "att_help", minutes=700, hints=1, item="pi_svd_define_004")
    assert RF.answered_since(vault, repo, {"intent": "retention", "learning_object_ids": ["lo_svd_definition"],
                                           "facet_ids": ["recall"]}, since="") is None
    # ... and after a worked example judged related to A, serving holds A by retention's rule.
    due, minutes_due = _due(row)
    _studied_related_example(repo, minutes_due - 60)
    check = _check(vault, repo, commitment_id, due)
    assert A not in check.eligible and A in check.held
    assert dict(check.gated)[A]["reasons"] == ["related_worked_example"]


def _rewrite(repo, row, *, chosen=None, questions=None, delete=False):
    with repo.connection() as connection:
        if delete:
            connection.execute("DELETE FROM reader_session_digests WHERE id = ?", (row["id"],))
        else:
            valuation = dict(row["valuation"])
            if chosen is not None:
                valuation["chosen"] = chosen
            if questions is not None:
                valuation["questions"] = questions
            RDG.update_digest(connection, row["id"], valuation_json=valuation)
        connection.commit()


def _cases(row):
    keep_primary = [entry for entry in row["valuation"]["questions"] if entry["key"] == QR]
    return {"no_digest_row": {"delete": True}, "no_chosen_line": {"chosen": []},
            "no_licensing_entry": {"questions": keep_primary}}  # round 6: not damage (pruned, still served)


def test_f17_an_unreadable_digest_holds_the_check_in_each_missing_data_case(tmp_path, monkeypatch):
    for name in ("no_digest_row", "no_chosen_line"):
        vault, repo, row, commitment_id = _shared(tmp_path / name, monkeypatch)
        due, _minutes = _due(row)
        assert A in _check(vault, repo, commitment_id, due).eligible  # readable: served cold
        _rewrite(repo, row, **_cases(row)[name])
        check = _check(vault, repo, commitment_id, due)
        assert A not in check.eligible and A in check.held, name
        assert dict(check.gated)[A]["reasons"] == [LICENSING_UNREADABLE], name


def test_f17_revaluation_retires_an_unreadable_check_and_re_asks_what_it_can_name(tmp_path, monkeypatch):
    for name in ("no_chosen_line",):
        vault, repo, row, commitment_id = _shared(tmp_path / name, monkeypatch)
        _rewrite(repo, row, **_cases(row)[name])
        report = RF.revalue_pending(vault, repo, now=_now(600), valuer=_discrimination_still_needs_it,
                                    clock=at(600))
        [retired] = report["retired"]
        assert retired["reason"] == RF.RETIRE_UNREADABLE, name
        assert C.resolve_disposition(repo, commitment_id) == "stopped"
        with repo.connection() as connection:
            digest = RDG.digest(connection, row["id"])
        assert digest["status"] == "incomplete", name
        [entry] = [e for e in digest["valuation"]["questions"] if e["key"] == QR]
        assert entry["incomplete"] is True and entry["reason"] == RF.RETIRE_UNREADABLE
        assert RF.coming_up(vault, repo, extraction_id=row["extraction_id"],
                            now=_now(600))["retired"][0]["text"].startswith("Taken off the schedule")
