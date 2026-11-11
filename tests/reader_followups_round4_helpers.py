"""What other test files use from ``tests/test_reader_followups_round4.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import date, datetime, UTC

from learnloop.instructional import reader_followups as RF
from learnloop.vault.loader import load_vault

from tests.recap_fixtures import EXT, T0, iso
from tests.reader_followups_helpers import FakeSearch


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


def _studied_related_example(repo, minutes, item_id=A):
    """The learner studies a worked example (in scope) that the judge called ``related`` to the item (A)."""

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
            (f"jl_{span}", iso(minutes + 1), WORKED_EXAMPLE_LEDGER_TASK, item_id, f"ext_we:{span}"))
        connection.commit()


def _check(vault, repo, commitment_id, now):
    from learnloop.scheduling.intent.serving import intent_serving

    return intent_serving(load_vault(vault.root), repo, now=now, force=True).checks[commitment_id]
