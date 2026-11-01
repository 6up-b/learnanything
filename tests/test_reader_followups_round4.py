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

from datetime import date, datetime, UTC

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from learnloop.vault.loader import load_vault
from tests.recap_fixtures import EXT, T0, at, iso
from tests.test_reader_followups import FakeSearch, NOW_MIN, _candidate, _plan, _seeded

A = "pi_svd_define_002"
QR = "retention:recall"
QD = "discriminate:lo_svd_definition"

WORKED_UNITS = {
    "worked": ("Worked examples", [
        ("Example 2.1 Find the singular values of A = [[3,0],[0,4]]. They are 4 and 3.", 4),
        ("Example 2.2 Write the SVD of a rank-one matrix u v^T and read off its singular value.", 4),
    ]),
}


def _questions(monkeypatch, *, retention=True, discriminate=True):
    found = []
    if retention:
        found.append(RF.Question(key=QR, purpose=RF.PURPOSE_RETENTION, learning_object_ids=["lo_svd_definition"],
                                 facet_ids=["recall"], attempt_ids=["att_book"]))
    if discriminate:
        found.append(RF.Question(key=QD, purpose=RF.PURPOSE_DISCRIMINATING,
                                 learning_object_ids=["lo_svd_definition"]))
    monkeypatch.setattr(RF, "open_questions", lambda *_a, **_k: (list(found), []))
    # The studied worked examples' extraction is in the checks' exposure scope.
    monkeypatch.setattr(RF, "_exposure_scope", lambda *_a, **_k: ["ext_we", EXT])


class _ByIntent(FakeSearch):
    """Per intent, call ``n`` values ``rounds[intent][n]``; every call but the
    intent's last stops on its budget with a cursor."""

    def __init__(self, rounds):
        super().__init__([])
        self.rounds = rounds
        self.seen: dict[str, int] = {}

    def __call__(self, query, constraints, *, caller, **kwargs):
        intent = constraints["intent"]
        n = self.seen.get(intent, 0)
        self.seen[intent] = n + 1
        rounds = self.rounds[intent]
        self.candidates = rounds[min(n, len(rounds) - 1)]
        result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
        if n + 1 < len(rounds):
            result["paging"] = {"outcome": "budget", "cursor": {"judged_items": []}}
        return result


def _due(row) -> tuple[datetime, float]:
    day = date.fromisoformat(row["valuation"]["chosen"][0]["due_hint"])
    moment = datetime(day.year, day.month, day.day, 12).astimezone().astimezone(UTC)
    return moment, (moment - T0).total_seconds() / 60.0


def _studied_related_example(repo, minutes):
    """The learner studies a worked example (in scope) that the judge called ``related`` to A."""

    from learnloop.db.stores.source_service import WORKED_EXAMPLE_LEDGER_TASK
    from tests.source_service_fakes import seed_textbook

    span = seed_textbook(repo, source_id="src_we", revision_id="rev_we", extraction_id="ext_we",
                         units=WORKED_UNITS)["worked"][1]
    repo.insert_source_exposure_event({"context": "library", "extraction_id": "ext_we", "span_id": span,
                                       "created_at": iso(minutes)})
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
            "judge_model, prompt_version, input_hash, verdict, rationale) "
            "VALUES (?, ?, ?, 'item', ?, 'span', ?, 'llm', 'fake', 'v1', 'h', 'related', 'r')",
            (f"jl_{span}", iso(minutes + 1), WORKED_EXAMPLE_LEDGER_TASK, A, f"ext_we:{span}"))
        connection.commit()


def _check(vault, repo, commitment_id, now):
    from learnloop.scheduling.intent.serving import intent_serving

    return intent_serving(load_vault(vault.root), repo, now=now, force=True).checks[commitment_id]


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
