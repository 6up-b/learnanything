"""L4-2's review fix round (``docs/reviews/algorithm-mvp-0.71.md``, "Review fix round"): the lesson-weight fit's
reads. Each test failed before its fix.

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
