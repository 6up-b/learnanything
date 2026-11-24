"""L4-2's review fix round (``docs/reviews/algorithm-mvp-0.71.md``, "Review fix round"): the lesson-weight fit's
reads. Each test failed before its fix.

Two grades of one learning object applied within one second can carry ids in the opposite order from their
application; the fit orders the ledger as mastery applied it (``attempt_order_for``), for its window and for an item's
first use (L42-R6).

One learner runs several processes at once (the desktop sidecar, the phone host, a CLI): a regrade can commit while
the fit is reading. The fit reads the ledgers in one snapshot, so it never scores one epoch's answer with another
epoch's curve (L42-R5).
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta

import pytest

from learnloop.learner import lesson_weight as LW
from learnloop.vault.loader import load_vault

from tests.regrade_contract_replay_helpers import _regrade
from tests.teacher_fakes import build_teacher_vault
from tests.teacher_te1_review_fixes_helpers import _cold, _lesson_with_check

T = datetime(2026, 11, 1, 9, tzinfo=UTC)


#: Ids minted in this order (A before B) and applied in the other (B, then A).
A_ID, B_ID = "01ZZZZZZZZZZZZZZZZZZZZZZZA", "01ZZZZZZZZZZZZZZZZZZZZZZZB"


def _apply(paths, repository, item_id, points, *, attempt_id, when, primed=False):
    """A self-graded answer with a chosen id, through the shared attempt step."""

    from learnloop.attempts.attempts import (
        ApplyAttemptInput,
        AttemptDraft,
        ResolvedGrade,
        apply_attempt,
        calculate_rubric_score,
    )
    from learnloop.attempts.grading import resolved_rubric
    from learnloop.clock import FrozenClock

    vault = load_vault(paths.root)
    rubric = resolved_rubric(vault, vault.practice_items[item_id])
    criterion = {"correctness": float(points)}
    stamp = when.isoformat().replace("+00:00", "Z")
    return apply_attempt(vault, repository, ApplyAttemptInput(
        draft=AttemptDraft(practice_item_id=item_id, learner_answer_md="an answer", attempt_type="independent_attempt",
                           primed=primed),
        attempt_id=attempt_id,
        grade=ResolvedGrade(
            rubric_score=calculate_rubric_score(rubric, criterion, []), criterion_points=criterion,
            evidence_rows=[{"id": f"ge_{attempt_id}", "criterion_id": "correctness", "points_awarded": float(points),
                            "evidence": "self", "notes": None, "local_grader_id": "self", "grader_tier": 1,
                            "created_at": stamp}],
            error_attributions=[], grader_confidence=1.0, confidence=3, manual_review_reason=None,
            feedback_md="self-graded"),
        grading_source="self"), clock=FrozenClock(when))


def test_an_update_applied_before_the_outcome_in_its_second_is_in_the_window(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    when = T + timedelta(days=1)
    _apply(paths, repository, "pi_eig_1", 0, attempt_id=B_ID, when=when, primed=True)
    _apply(paths, repository, "pi_eig_2", 4, attempt_id=A_ID, when=when)
    vault = load_vault(paths.root)
    update = next(e for e in LW.replay_state(vault, repository).trace if e["kind"] == "weight_update")
    assert update["resolving_attempt_id"] == A_ID
    assert update["detail"]["likelihood"] == "recorded_trajectory"
    assert [step["attempt_id"] for step in update["detail"]["trajectory_inputs"]][-1] == B_ID
    assert update["detail"]["intervening"] == 1
    check = _checks(repository)[0]
    with repository.connection() as connection:
        trajectory = LW.recorded_trajectory(connection, vault, vault.config.mastery, check,
                                            {"id": A_ID, "created_at": connection.execute(
                                                "SELECT created_at FROM practice_attempts WHERE id = ?",
                                                (A_ID,)).fetchone()[0]})
    state = LW.trajectory_state(LW.CheckSensitivity.from_dict(check["inputs"]["sensitivity"]), trajectory,
                                mass=float(check["mass_applied"]), recorded_mass=float(check["mass_applied"]),
                                mastery_config=vault.config.mastery)
    recorded = repository.latest_attempt_surprise(A_ID)["posterior_delta"]
    assert (state.logit_mean, state.logit_variance) == pytest.approx((recorded["mu_before"], recorded["P_before"]))
    # The record's owner-copy window count follows the same order.
    with repository.atomic():
        LW.write_state(repository, LW.replay_state(vault, repository))
    counts = dict(zip(("fitted_checks", "attempts", "primed", "with_curve", "missing_curve"),
                      _rows(repository, _owner_copy_window_query())[0]))
    assert counts == {"fitted_checks": 1, "attempts": 3, "primed": 1, "with_curve": 3, "missing_curve": 0}


def _owner_copy_window_query() -> str:
    """The first query of the record's owner-copy procedure (the fitted windows' coverage)."""

    from pathlib import Path

    record = (Path(__file__).resolve().parents[1] / "docs/reviews/algorithm-mvp-0.71.md").read_text()
    body = record[record.index("PRAGMA query_only = ON;\n") + len("PRAGMA query_only = ON;\n"):]
    return body[:body.index("SELECT count(*) AS foreign_key_violations")]


def _rows(repository, sql):
    with repository.connection() as connection:
        return [tuple(row) for row in connection.execute(sql).fetchall()]


def test_an_items_first_use_is_the_attempt_applied_first_in_its_second(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    when = T + timedelta(days=1)
    _apply(paths, repository, "pi_eig_2", 4, attempt_id=B_ID, when=when)
    _apply(paths, repository, "pi_eig_2", 0, attempt_id=A_ID, when=when)
    update = next(e for e in LW.replay_state(load_vault(paths.root), repository).trace if e["kind"] == "weight_update")
    assert (update["resolving_attempt_id"], update["detail"]["y"]) == (B_ID, 1.0)


def _resolved(state):
    return [(entry["kind"], json.dumps(entry["detail"], sort_keys=True, default=float))
            for entry in state.trace if entry["kind"] in ("weight_update", "pool_update")]


@pytest.mark.durability
def test_a_regrade_committing_while_the_fit_reads_does_not_reach_it(tmp_path, monkeypatch):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T, retained=0.8)
    _cold(paths, repository, "pi_eig_1", T + timedelta(days=1), primed=True)
    outcome = _cold(paths, repository, "pi_eig_2", T + timedelta(days=2), points=4)
    vault = load_vault(paths.root)
    before = LW.replay_state(vault, repository)
    assert [kind for kind, _ in _resolved(before)] == ["weight_update", "pool_update"]

    real = LW.current_curve
    regraded = []

    def regrade_from_another_process(connection, attempt_id):
        # Another process's regrade of the resolving answer commits between the fit's first reads and this one.
        if not regraded:
            regraded.append(True)
            failures: list[BaseException] = []

            def regrade():
                try:
                    _regrade(load_vault(paths.root), repository, outcome.attempt_id, {"correctness": 0},
                             when=T + timedelta(days=3))
                except BaseException as exc:  # noqa: BLE001 - reported on the test's thread
                    failures.append(exc)

            worker = threading.Thread(target=regrade)
            worker.start()
            worker.join()
            assert not failures, failures
        return real(connection, attempt_id)

    monkeypatch.setattr(LW, "current_curve", regrade_from_another_process)
    during = LW.replay_state(vault, repository)
    assert regraded
    # The regrade committed, and the fit that was reading saw none of it.
    assert repository.fetch_practice_attempt(outcome.attempt_id)["correctness"] == 0.0
    assert _resolved(during) == _resolved(before)
    monkeypatch.setattr(LW, "current_curve", real)
    after = LW.replay_state(vault, repository)
    update = next(entry for entry in after.trace if entry["kind"] == "weight_update")
    assert update["detail"]["y"] == 0.0 and update["detail"]["resolving_input"]["epoch_key"] == "revision:1"


def test_a_grade_committing_while_a_check_is_weighed_waits_for_the_check(tmp_path, monkeypatch):
    """The check's mass, its recorded prior and the attempt step that applies it read one state: another process's
    grade on the same learning object commits wholly before the weighing or after the check is recorded."""

    from learnloop.teacher import checks as CK

    paths, repository = build_teacher_vault(tmp_path / "vault")
    real = CK.check_mass
    committed = threading.Event()
    failures: list[BaseException] = []
    workers: list[threading.Thread] = []

    def another_process_grades(*args, **kwargs):
        mass = real(*args, **kwargs)

        def grade():
            try:
                _cold(paths, repository, "pi_eig_3", T + timedelta(minutes=3), points=0)
                committed.set()
            except BaseException as exc:  # noqa: BLE001 - reported on the test's thread
                failures.append(exc)

        workers.append(threading.Thread(target=grade))
        workers[-1].start()
        # Before the fix the other grade commits here, between the weighing and the check's own application. After
        # it, the grade waits for the check's transaction: the wait only detects that it is blocked.
        committed.wait(timeout=2.0)
        return mass

    monkeypatch.setattr(CK, "check_mass", another_process_grades)
    _lesson_with_check(paths, repository, at=T)
    for worker in workers:
        worker.join()
    assert not failures, failures
    assert workers and committed.is_set()
    check = next(row for row in _checks(repository))
    recorded = repository.latest_attempt_surprise(check["attempt_id"])["posterior_delta"]
    sensitivity = check["inputs"]["sensitivity"]
    assert (sensitivity["mu"], sensitivity["variance"]) == (recorded["mu_before"], recorded["P_before"])


def _checks(repository):
    with repository.connection() as connection:
        return LW._checks(connection)


def test_a_regrade_leaves_the_lesson_weight_tables_as_a_rebuild_would(tmp_path):
    """L42-R11: the DERIVED tables describe the ledgers through the latest lesson check; a replacement grade of an
    answer inside that prefix refreshes them in its own transaction, so a rebuild right after it changes nothing."""

    from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state

    paths, repository = build_teacher_vault(tmp_path / "vault")
    _lesson_with_check(paths, repository, at=T)
    resolver = _cold(paths, repository, "pi_eig_2", T + timedelta(days=1), points=4)
    _lesson_with_check(paths, repository, at=T + timedelta(days=2))
    tables = ("SELECT * FROM lesson_weight_state ORDER BY family",
              "SELECT seq, kind, lesson_check_id, resolving_attempt_id, learning_object_id, at, detail_json "
              "FROM lesson_weight_trace ORDER BY seq",
              "SELECT * FROM confidence_calibration_state ORDER BY family")
    resolved = [row for row in _rows(repository, tables[1]) if row[1] == "weight_update"]
    assert [row[3] for row in resolved] == [resolver.attempt_id]
    _regrade(load_vault(paths.root), repository, resolver.attempt_id, {"correctness": 0},
             when=T + timedelta(days=3))
    after_regrade = [_rows(repository, sql) for sql in tables]
    assert '"y": 0.0' in next(row[-1] for row in after_regrade[1] if row[1] == "weight_update")
    rebuild_all_derived_state(load_vault(paths.root), repository)
    assert [_rows(repository, sql) for sql in tables] == after_regrade
