"""Generator of fixtures/mvp017_route_check_replay (runs only at e238fa07a).

Builds a vault graded under mvp-0.17's separate route check (the code that
route-check-in-grader deleted), with every outcome that check could write:
restored, disputed, a learner-meaning clarification (migration 186's
``route_check_disagreement`` trigger), flagged, P1 unlocated, held for review,
a hold a failed regrade check kept, an adjudicated (released) hold, a
not-proof-like reading, an unavailable checker and a wrong final answer the
final-answer check outranked. It rebuilds the derived state to its fixed
point and copies the vault with the backup API. Fakes only; no network.

Run once, at the base commit, with
``LEARNLOOP_GENERATE_MVP017_FIXTURE=<dir> uv run pytest tests/<this file>``.
"""

from __future__ import annotations

import json
import os
from datetime import timedelta
from pathlib import Path

import pytest

from learnloop.attempts.grade_resolution import append_adjudication_evidence_revision
from learnloop.attempts.regrade import regrade_attempt
from learnloop.clock import FrozenClock
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.held_grades import held_attempt_ids
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

from tests.diagnosis_fakes import ReviewFakeClient
from tests.split_live_helpers import ReadyRuntime, split_vault, submit
from tests.test_proof_route_check import (  # noqa: F401 - ``checker`` is a fixture
    ALTERNATIVE,
    CLOCK,
    VERSION,
    CheckerFake,
    DivergentUnlocatedGrader,
    FullCreditGrader,
    LocatedGrader,
    checker,
)

OUT = os.environ.get("LEARNLOOP_GENERATE_MVP017_FIXTURE")
ESTABLISHED = {"verdict": "established"}
HOLDING = {"setup": {"verdict": "cannot_tell"}, "result": {"verdict": "not_established"}}


@pytest.mark.skipif(not OUT, reason="fixture generator: set LEARNLOOP_GENERATE_MVP017_FIXTURE")
def test_generate_the_mvp017_replay_fixture(tmp_path, checker):
    assert VERSION == "mvp-0.17"
    paths, vault, repository = split_vault(tmp_path, version=VERSION)
    t0 = CLOCK.now()
    attempts: dict[str, str] = {}

    def at(days: float):
        return t0 + timedelta(days=days)

    checker(CheckerFake(verdicts={"setup": ESTABLISHED, "result": ESTABLISHED}))
    attempts["restored_both"] = submit(
        vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE, when=at(0)).attempt_id
    checker(CheckerFake(verdicts={"setup": ESTABLISHED, "result": ESTABLISHED}))
    attempts["restored_and_disputed"] = submit(
        vault, repository, LocatedGrader(), answer=ALTERNATIVE + " (2)", when=at(1)).attempt_id
    checker(CheckerFake(
        verdicts={"setup": {"verdict": "not_established"}, "result": ESTABLISHED},
        question="Does Sigma^{-1} mean the pseudo-inverse here?", reason="ambiguous_notation",
    ))
    attempts["clarification"] = submit(
        vault, repository, LocatedGrader(), answer=ALTERNATIVE + " (3)", when=at(2)).attempt_id
    checker(CheckerFake(verdicts={
        "setup": ESTABLISHED,
        "result": {"verdict": "not_established", "invalid_step_quote": "U = A V Sigma^{-1}",
                   "error_kind": "unjustified_step", "reason_md": "Sigma may be singular"},
    }))
    attempts["flagged"] = submit(
        vault, repository, FullCreditGrader(), answer=ALTERNATIVE + " (4)", when=at(3)).attempt_id
    checker(CheckerFake(verdicts={"setup": ESTABLISHED, "result": {"verdict": "cannot_tell"}}))
    attempts["unlocated_partial"] = submit(
        vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (5)", when=at(4)).attempt_id
    checker(CheckerFake(verdicts=HOLDING))
    attempts["held"] = submit(
        vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (6)", when=at(5)).attempt_id
    checker(CheckerFake(verdicts=HOLDING))
    attempts["held_kept_by_failed_regrade"] = submit(
        vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (7)", when=at(6)).attempt_id
    checker(CheckerFake(verdicts={"setup": ESTABLISHED, "result": ESTABLISHED},
                        fail_purposes=("proof_route_check",)))
    regrade_attempt(
        vault, repository, repository.fetch_practice_attempt(attempts["held_kept_by_failed_regrade"]),
        runtime=ReadyRuntime(), client=DivergentUnlocatedGrader(), grading_source="ai",
        clock=FrozenClock(at(7)),
    )
    checker(CheckerFake(verdicts=HOLDING))
    attempts["held_then_adjudicated"] = submit(
        vault, repository, DivergentUnlocatedGrader(), answer=ALTERNATIVE + " (8)", when=at(8)).attempt_id
    revision = append_adjudication_evidence_revision(
        repository, attempt_id=attempts["held_then_adjudicated"], resolved_fraction=1.0,
        adjudication_id="adj-mvp017-fixture", adjudicator_source="human_owner",
        rationale="the route is valid", vault=vault, clock=FrozenClock(at(9)),
    )
    assert revision["status"] == "revised"
    checker(CheckerFake(kind="computation", reasoning=False))
    attempts["not_proof_like"] = submit(
        vault, repository, ReviewFakeClient(), item_id="pi_svd_compute_002", answer="U Sigma V^T",
        when=at(10)).attempt_id
    checker(None)
    attempts["checker_unavailable"] = submit(
        vault, repository, ReviewFakeClient(), item_id="pi_eigen_001", answer="A = P D P^{-1}",
        when=at(11)).attempt_id

    class Unlocated(ReviewFakeClient):
        def _blind_grading(self, request, context):
            return super()._blind_grading(request, context).model_copy(update={"error_attributions": []})

    checker(CheckerFake(verdicts={"correctness": ESTABLISHED}))
    attempts["answer_differs"] = submit(
        vault, repository, Unlocated(), item_id="pi_unrelated_001",
        answer="Four is the smallest even square, so the answer is 4.", when=at(12)).attempt_id

    # The fixed point: the first rebuild may move a seeded schedule; from the
    # second on, rebuilds are idempotent.
    rebuild_all_derived_state(vault, repository, clock=CLOCK)
    rebuild_all_derived_state(vault, repository, clock=CLOCK)

    outcomes = {}
    held = held_attempt_ids(repository, attempts.values())
    for label, attempt_id in attempts.items():
        attempt = repository.fetch_practice_attempt(attempt_id)
        record = repository.latest_blind_grade_record(attempt_id)["record"]
        proof = (record.get("grading_support") or {}).get("proof_route_check") or {}
        outcomes[label] = {
            "attempt_id": attempt_id,
            "rubric_score": attempt["rubric_score"],
            "correctness": attempt["correctness"],
            "manual_review_reason": attempt["manual_review_reason"],
            "held": attempt_id in held,
            "calibration_prompt_version": record.get("calibration_prompt_version"),
            "proof_route_check": {
                key: proof.get(key)
                for key in ("version", "status", "applied", "held_for_review", "hold_kept_from",
                            "restored_criterion_ids", "unverified_criterion_ids", "flagged_criterion_ids",
                            "unlocated_criterion_ids", "disputed_criterion_ids")
                if key in proof
            },
        }
    with connect(paths.sqlite_path) as connection:
        triggers = sorted(row[0] for row in connection.execute(
            "SELECT trigger FROM grading_clarifications"))
        tasks = dict(connection.execute(
            "SELECT task, COUNT(*) FROM judgment_ledger WHERE task IN ('proof_like_item', 'proof_route_check') "
            "GROUP BY task").fetchall())
    assert "route_check_disagreement" in triggers
    out = Path(OUT)
    assert not out.exists()
    copy_tree_with_databases(paths.root, out)
    import sqlite3

    # A tracked fixture stays rollback-mode (CLAUDE.md).
    with sqlite3.connect(out / "state.sqlite") as copy:
        assert copy.execute("PRAGMA journal_mode=DELETE").fetchone()[0].lower() == "delete"
    (out / "expected.json").write_text(json.dumps({
        "generated_at_commit": "e238fa07a",
        "algorithm_version": VERSION,
        "rebuild_clock": CLOCK.now().isoformat(),
        "attempts": outcomes,
        "clarification_triggers": triggers,
        "judgment_tasks": tasks,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
