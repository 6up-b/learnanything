"""Reader RW6b part 1: the Codex RE-review's findings, each reproduced first
(docs/reviews/reader-rw6b-p1-followups-codex-review.md, "Re-review").

* F1 (reopened): the serve-time gate reads an imported exercise's book
  solution spans, and a ``related`` worked example (a label for a
  discriminating check) never masks another studied example nobody judged.
* F3 (reopened): two resumptions of an incomplete digest publishing in the
  same second never overwrite each other's commitments (the whole captured
  row is compared, not a second-resolution stamp).
* F13: an exposure retirement and its re-ask marker commit together; a
  failure between them loses neither the check nor the replacement search.
* F14: a resumed search over a check it published earlier (carried, with a
  cheaper one with the same information found) keeps the earlier one and adds
  nothing (round 3: the live check seeds the greedy conditional selection;
  round 2's retirement by reconciliation is gone).

Fakes only; no model call anywhere.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from learnloop.curriculum import commitments as C
from learnloop.db.stores import reader_digests as RDG
from learnloop.instructional import reader_followups as RF
from learnloop.scheduling.intent.followup_gate import followup_gate
from tests.recap_fixtures import EXT, at, iso
from tests.test_reader_followups import FakeSearch, NOW_MIN, _candidate, _now, _plan, _seeded

ITEM = "pi_svd_define_002"
OTHER = "pi_svd_define_003"
THIRD = "pi_svd_define_004"


def _provenance(intent="discriminate", purpose="discriminating", scope=None):
    return {"via": RF.VIA, "purpose": purpose, "question": {"intent": intent, "facet_ids": [],
                                                            "learning_object_ids": ["lo_svd_definition"]},
            "attempt_ids": [], **({"exposure_scope_extraction_ids": scope} if scope is not None else {})}


# -- F1: the gate applies the whole exposure rule ------------------------------------------------------


def test_f1_reading_the_imported_exercises_book_solution_since_valuation_holds_the_check(tmp_path):
    _vault, repo, _session = _seeded(tmp_path)
    item = SimpleNamespace(id=ITEM, family_id=None, learning_object_id="lo_svd_definition", evidence_facets=(),
                           canonical_exercise=SimpleNamespace(extraction_id="ext_book", span_ids=("x1",)))
    vault = SimpleNamespace(practice_items={ITEM: item}, canonical_facet_id=lambda facet: facet)
    with repo.connection() as connection:
        connection.execute(
            "INSERT INTO source_exercise_imports (id, extraction_id, span_ids_json, practice_item_id, "
            "verification_json, status, caller, created_at, updated_at) VALUES "
            "('imp_1', 'ext_book', '[\"x1\"]', ?, '{\"book_solution\": {\"span_ids\": [\"sol1\"]}}', 'written', "
            "'reader', ?, ?)", (ITEM, iso(100), iso(100)))
        connection.commit()
    valued_at, now = iso(NOW_MIN), _now(NOW_MIN + 600)
    assert followup_gate(vault, repo, item_id=ITEM, provenance=_provenance(), valued_at=valued_at, now=now) is None
    # The learner opens the exercise's printed solution after the check was valued.
    repo.insert_source_exposure_event({"context": "library", "extraction_id": "ext_book", "span_id": "sol1",
                                       "created_at": iso(NOW_MIN + 500)})
    verdict = followup_gate(vault, repo, item_id=ITEM, provenance=_provenance(), valued_at=valued_at, now=now)
    assert verdict is not None and verdict["reasons"] == ["source_exposed"]


WORKED_UNITS = {
    "worked": ("Worked examples", [
        ("Example 2.1 Find the singular values of A = [[3,0],[0,4]]. They are 4 and 3.", 4),
        ("Example 2.2 Write the SVD of a rank-one matrix u v^T and read off its singular value.", 4),
    ]),
}


def _two_studied_examples(repo):
    from learnloop.db.stores.source_service import WORKED_EXAMPLE_LEDGER_TASK
    from tests.source_service_fakes import seed_textbook

    spans = seed_textbook(repo, source_id="src_we", revision_id="rev_we", extraction_id="ext_we",
                          units=WORKED_UNITS)["worked"][1:]
    with repo.connection() as connection:
        roles = {row[0]: row[1] for row in connection.execute(
            "SELECT span_id, role_hint FROM source_document_blocks WHERE extraction_id='ext_we'")}
    assert all(roles[span] == "worked_example" for span in spans), roles
    for span in spans:
        repo.insert_source_exposure_event({"context": "library", "extraction_id": "ext_we", "span_id": span,
                                           "created_at": iso(NOW_MIN + 500)})

    def judge(span, verdict):
        with repo.connection() as connection:
            connection.execute(
                "INSERT INTO judgment_ledger (id, created_at, task, left_kind, left_id, right_kind, right_id, judge, "
                "judge_model, prompt_version, input_hash, verdict, rationale) "
                "VALUES (?, ?, ?, 'item', ?, 'span', ?, 'llm', 'fake', 'v1', 'h', ?, 'r')",
                (f"jl_{span}", iso(NOW_MIN + 510), WORKED_EXAMPLE_LEDGER_TASK, ITEM, f"ext_we:{span}", verdict))
            connection.commit()

    return spans, judge


def test_f1_a_related_example_does_not_mask_another_unjudged_one_for_a_discriminating_check(tmp_path):
    vault, repo, _session = _seeded(tmp_path)
    (related, unjudged), judge = _two_studied_examples(repo)
    judge(related, "related")
    valued_at, now = iso(NOW_MIN), _now(NOW_MIN + 600)
    verdict = followup_gate(vault, repo, item_id=ITEM, provenance=_provenance(), valued_at=valued_at, now=now)
    assert verdict is not None and verdict["reasons"] == ["worked_example_unjudged"]
    # Once the second example is judged related too, the related label stands alone: no exclusion.
    judge(unjudged, "related")
    assert followup_gate(vault, repo, item_id=ITEM, provenance=_provenance(), valued_at=valued_at, now=now) is None
    # A retention check is excluded by a related example (the valuation's own rule).
    retention = _provenance(intent="retention", purpose="retention")
    verdict = followup_gate(vault, repo, item_id=ITEM, provenance=retention, valued_at=valued_at, now=now)
    assert verdict is not None and verdict["reasons"] == ["related_worked_example"]


# -- F3: concurrent resumptions within one second --------------------------------------------------------


class _Budget(FakeSearch):
    """Stops on its budget (a cursor left) after valuing its candidates."""

    def __call__(self, query, constraints, *, caller, **kwargs):
        result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
        result["paging"] = {"outcome": "budget", "cursor": {"judged_items": []}}
        return result


def _live(repo, row):
    with repo.connection() as connection:
        ids = [r[0] for r in connection.execute("SELECT id FROM commitments")]
    return {cid for cid in ids if C.resolve_disposition(repo, cid) == "one_check_pending"}


def test_f3_two_resumptions_publishing_in_the_same_second_never_orphan_a_commitment(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    first = _plan(vault, repo, session, _Budget([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    assert first["status"] == "incomplete" and len(first["followup_commitment_ids"]) == 1
    minutes = NOW_MIN  # every publication stamps the same second

    class OtherResumptionFirst(_Budget):
        def __call__(self, query, constraints, *, caller, **kwargs):
            result = super().__call__(query, constraints, caller=caller, **kwargs)
            if len(self.calls) == 1:
                # Another sidecar resumes the same digest and publishes within the same second.
                _plan(vault, repo, session, _Budget([_candidate(ITEM, 0.99, 0.01, 1.0),
                                                     _candidate(OTHER, 0.98, 0.3, 0.05)]), minutes=minutes)
            return result

    final = _plan(vault, repo, session, OtherResumptionFirst([_candidate(ITEM, 0.99, 0.01, 1.0),
                                                               _candidate(THIRD, 0.97, 0.3, 0.05)]),
                  minutes=minutes)
    with repo.connection() as connection:
        stored = RDG.digest(connection, final["id"])
    assert _live(repo, stored) <= set(stored["followup_commitment_ids"])
    refs = {entry["ref"] for entry in stored["valuation"]["chosen"] if entry.get("commitment_id")}
    assert THIRD not in refs  # the stale resumption published nothing


# -- F13: an interrupted exposure retirement -------------------------------------------------------------


def _impression(repo, item_id, minutes):
    from learnloop.db.stores.source_service import insert_impression

    with repo.connection() as connection:
        insert_impression(connection, id=f"imp_{minutes}", created_at=iso(minutes), surface="reader",
                          caller_kind="reader", caller_ref="elsewhere", proposal_id="pp_elsewhere",
                          candidate_kind="item", practice_item_id=item_id, extraction_id=None, span_ids=[],
                          shown_fields={}, session_id=None)
        connection.commit()


def test_f13_a_failure_after_the_exposure_retirement_loses_neither_the_check_nor_the_re_ask(tmp_path, monkeypatch):
    vault, repo, session = _seeded(tmp_path)
    row = _plan(vault, repo, session, FakeSearch([_candidate(ITEM, 0.99, 0.01, 1.0)]))
    [commitment_id] = row["followup_commitment_ids"]
    _impression(repo, ITEM, NOW_MIN + 30)
    real = RDG.update_digest

    def die(*_a, **_k):
        raise RuntimeError("the process died before the re-ask marker")

    monkeypatch.setattr(RDG, "update_digest", die)
    with pytest.raises(RuntimeError):
        RF.revalue_pending(vault, repo, now=_now(400), valuer=lambda *_a: {"problems": []}, clock=at(400))
    monkeypatch.setattr(RDG, "update_digest", real)
    # Nothing half-done: the check is still pending, so the next re-valuation sees it.
    assert C.resolve_disposition(repo, commitment_id) == "one_check_pending"
    report = RF.revalue_pending(vault, repo, now=_now(410), valuer=lambda *_a: {"problems": []}, clock=at(410))
    assert [line["reason"] for line in report["retired"]] == [RF.RETIRE_EXPOSED]
    with repo.connection() as connection:
        digest = RDG.digest(connection, row["id"])
    assert digest["status"] == "incomplete"
    assert digest["valuation"]["questions"][0]["reason"] == RF.RETIRE_EXPOSED
    assert [s.session_id for s in RF.sessions_to_plan(vault, repo, now=_now(410))] == [session.session_id]


# -- F14: a resumed search conditions on the live check (round 3) ---------------------------------------


class _PerCall(FakeSearch):
    """Call ``n`` values ``rounds[n]``; every call but the last stops on its budget.
    Perfect-information tables: a second check with the same information adds none."""

    def __init__(self, rounds):
        super().__init__([])
        self.rounds = rounds

    def __call__(self, query, constraints, *, caller, **kwargs):
        self.candidates = self.rounds[min(len(self.calls), len(self.rounds) - 1)]
        result = dict(super().__call__(query, constraints, caller=caller, **kwargs))
        if len(self.calls) < len(self.rounds):
            result["paging"] = {"outcome": "budget", "cursor": {"judged_items": []}}
        return result


def test_f14_a_resumed_search_conditions_on_the_live_check_and_retires_nothing(tmp_path):
    """Round 3 replaced round 2's reconciliation (which retired the earlier
    check): the live check seeds the greedy selection, so a cheaper check with
    the same information adds nothing and nothing is retired."""

    vault, repo, session = _seeded(tmp_path)
    search = _PerCall([[_candidate(ITEM, 1.0, 0.0, 1.0)],
                       # Resumed: the earlier pick is carried; a cheaper check with the same information is found.
                       [_candidate(ITEM, 1.0, 0.0, 1.0), _candidate(OTHER, 1.0, 0.0, 0.2)]])
    first = _plan(vault, repo, session, search)
    assert first["status"] == "incomplete"
    [earlier] = first["followup_commitment_ids"]
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert again["status"] == "planned"
    assert len(search.calls) == 2 and search.calls[1]["continue_from"] == "pp_fake_1"
    assert search.calls[1]["already_chosen"] == [ITEM]
    assert again["followup_commitment_ids"] == [earlier]
    assert C.resolve_disposition(repo, earlier) == "one_check_pending"
    timeline = RF.coming_up(vault, repo, extraction_id=EXT, now=_now(NOW_MIN + 60))
    assert [line["commitment_id"] for line in timeline["next"]] == [earlier] and timeline["retired"] == []


def test_f14_a_resumed_search_that_still_selects_the_earlier_check_keeps_it(tmp_path):
    vault, repo, session = _seeded(tmp_path)
    search = _PerCall([[_candidate(ITEM, 1.0, 0.0, 0.2)],
                       [_candidate(ITEM, 1.0, 0.0, 0.2), _candidate(OTHER, 1.0, 0.0, 1.0)]])
    first = _plan(vault, repo, session, search)
    [earlier] = first["followup_commitment_ids"]
    again = _plan(vault, repo, session, search, minutes=NOW_MIN + 60)
    assert C.resolve_disposition(repo, earlier) == "one_check_pending"
    assert [C.resolve_disposition(repo, cid) for cid in again["followup_commitment_ids"]] == ["one_check_pending"]
