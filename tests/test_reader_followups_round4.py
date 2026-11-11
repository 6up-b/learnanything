"""Reader RW6b part 1: Codex verify round 4 (F16), reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Round 4 (F16)").

F16: a check a discriminating question chose and a retention question shared
was judged for exposure on the first question's intent only, so a worked
example judged ``related`` (an exclusion for retention, only a label for
discrimination) let it be served cold and re-valuation kept it. Now the
serve-time gate and re-valuation's exposure step apply the STRICTEST rule
across the open licensing questions, and the exposure retirement re-asks every
licensing question. With one licensing question the rule is unchanged.

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from tests.recap_fixtures import at
from tests.reader_followups_helpers import NOW_MIN, _candidate, _plan, _seeded
from tests.reader_followups_round4_helpers import (
    A,
    QD,
    QR,
    _ByIntent,
    _check,
    _due,
    _questions,
    _studied_related_example,
)

def test_f16_a_shared_check_is_held_and_retired_by_retentions_rule(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)
    _questions(monkeypatch)
    # (1) retention's search stops on its budget before choosing; (2) discrimination chooses A;
    # (3) retention resumes and selects A too: shared.
    search = _ByIntent({"retention": [[], [_candidate(A, 1.0, 0.0, 3.0)]],
                        "discriminate": [[_candidate(A, 1.0, 0.0, 3.0)]]})
    first = _plan(vault, repo, session, search)
    assert first["status"] == "incomplete"
    [commitment_id] = first["followup_commitment_ids"]
    row = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert row["status"] == "planned" and row["followup_commitment_ids"] == [commitment_id]
    [line] = row["valuation"]["chosen"]
    assert [entry["question"] for entry in line["licensing"]] == [QD, QR]  # discrimination first: its provenance
    due, minutes_due = _due(row)
    assert A in _check(vault, repo, commitment_id, due).eligible  # cold before any exposure
    # (4) the learner studies a worked example judged related to A.
    _studied_related_example(repo, minutes_due - 60)
    # (5) the serve-time gate holds it by retention's rule (round 3 served it: discrimination's only).
    check = _check(vault, repo, commitment_id, due)
    assert A not in check.eligible and A in check.held
    assert dict(check.gated)[A]["reasons"] == ["related_worked_example"]
    # Re-valuation retires it as exposed and re-asks both licensing questions.
    report = RF.revalue_pending(vault, repo, now=due, valuer=lambda *_a: {"problems": []}, clock=at(minutes_due))
    [retired] = report["retired"]
    assert retired["reason"] == RF.RETIRE_EXPOSED and retired["detail"]["reasons"] == ["related_worked_example"]
    assert C.resolve_disposition(repo, commitment_id) == "stopped"
    with repo.connection() as connection:
        digest = RDG.digest(connection, row["id"])
    assert digest["status"] == "incomplete"
    entries = {entry["key"]: entry for entry in digest["valuation"]["questions"]}
    for key in (QD, QR):
        assert entries[key]["incomplete"] is True and entries[key]["reason"] == RF.RETIRE_EXPOSED


def test_f16_one_licensing_question_keeps_its_own_rule(tmp_path, monkeypatch):
    for retention, reasons in ((False, None), (True, ["related_worked_example"])):
        vault, repo, session = _seeded(tmp_path / f"r{int(retention)}")
        _questions(monkeypatch, retention=retention, discriminate=not retention)
        intent = "retention" if retention else "discriminate"
        row = _plan(vault, repo, session, _ByIntent({intent: [[_candidate(A, 1.0, 0.0, 3.0)]]}))
        [commitment_id] = row["followup_commitment_ids"]
        due, minutes_due = _due(row)
        _studied_related_example(repo, minutes_due - 60)
        check = _check(vault, repo, commitment_id, due)
        if reasons is None:
            assert A in check.eligible  # a label for a discriminating check, as before
        else:
            assert dict(check.gated)[A]["reasons"] == reasons
