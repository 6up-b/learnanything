"""Every outcome lands with its judgment, or neither does (project-understanding F5, F6).

Faults are injected at the persistence boundary with a temporary trigger that
aborts any insert into ``judgments``: that is where a process that stops
between "outcome written" and "judgment written" would leave the store.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager

import pytest

from learnloop.ai.spend import SpendCaps
from learnloop.config import LearnLoopConfig
from learnloop.projects.ai_runtime import PaidCalls
from learnloop.projects.capture import enroll_repo, sweep
from learnloop.projects.experiment_store import ProjectStore
from learnloop.projects.probes import (
    contest_grade,
    generate_probes,
    grade_responses,
    record_response,
)
from tests.project_support import (
    ProjectFake,
    clock_at,
    fake_resolver,
    isolated_git,  # noqa: F401
    make_model_repo,
)

CAPS = SpendCaps(max_candidates=100, max_pairs=0, max_retries=2, max_calls=100, max_total_tokens=10**7, max_estimated_usd=100.0)


def _routes(fake):
    resolver = fake_resolver(fake)
    return {role: resolver(None, None, role) for role in ("authoring", "closed_book", "grading")}


@pytest.fixture
def captured(isolated_git, tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    repo = make_model_repo(tmp_path / "repo")
    config = LearnLoopConfig()
    enroll_repo(vault, config, repo.path, clock=clock_at(0))
    sweep(vault, config, clock=clock_at(0))
    store = ProjectStore.for_vault(vault)
    (diff,) = store.diffs()
    return vault, config, store, diff


@contextmanager
def judgment_writes_fail(store: ProjectStore):
    with store.connection() as connection:
        connection.execute(
            "CREATE TRIGGER fault_injection BEFORE INSERT ON judgments "
            "BEGIN SELECT RAISE(ABORT, 'injected stop before the judgment'); END"
        )
    try:
        yield
    finally:
        with store.connection() as connection:
            connection.execute("DROP TRIGGER fault_injection")


def _generate(vault, config, store, fake):
    paid = PaidCalls(store, caps=CAPS, run_id="run")
    return generate_probes(store, vault, config, paid, _routes(fake), store.diffs(probe_status="pending"), clock=clock_at(0))


def test_candidates_never_persist_without_their_validity_judgments(captured):
    vault, config, store, diff = captured
    with judgment_writes_fail(store):
        _generate(vault, config, store, ProjectFake())
    assert store.probes_for_diff(diff["id"]) == []
    assert store.judgments() == []
    _generate(vault, config, store, ProjectFake())
    probes = store.probes_for_diff(diff["id"])
    validity = store.judgments(task="project_probe_validity")
    assert len(probes) == 6 and sorted(row["left_id"] for row in validity) == sorted(p["id"] for p in probes)


def test_closed_book_verdicts_never_persist_without_their_judgments(captured):
    vault, config, store, diff = captured

    class StopAtClosedBookGrade(ProjectFake):
        armed = True

        def run_project_probe_grading(self, context):
            result = super().run_project_probe_grading(context)
            if self.armed:
                with store.connection() as connection:
                    connection.execute(
                        "CREATE TRIGGER fault_injection BEFORE INSERT ON judgments "
                        "BEGIN SELECT RAISE(ABORT, 'injected stop'); END"
                    )
            return result

    _generate(vault, config, store, StopAtClosedBookGrade())
    with store.connection() as connection:
        connection.execute("DROP TRIGGER fault_injection")
    statuses = {probe["status"] for probe in store.probes_for_diff(diff["id"])}
    assert statuses <= {"invalid", "pending_closed_book_grade"}  # no verdict without its judgment
    assert store.judgments(task="project_closed_book") == []
    resumed = ProjectFake()
    _generate(vault, config, store, resumed)
    assert resumed.calls == {"grading": 1}
    graded = [probe for probe in store.probes_for_diff(diff["id"]) if probe["status"] in {"survivor", "rejected_generic"}]
    assert len(store.judgments(task="project_closed_book")) == len(graded) == 4


def _answered(captured):
    vault, config, store, diff = captured
    _generate(vault, config, store, ProjectFake())
    selected = [probe for probe in store.probes_for_diff(diff["id"]) if probe["selected"]]
    response = record_response(store, selected[0]["id"], kind="answer", answer="It applies relu.", clock=clock_at(8))
    return store, selected, response


def test_a_grade_never_persists_without_its_judgment(captured):
    store, _selected, response = _answered(captured)
    route = _routes(ProjectFake())["grading"]
    with judgment_writes_fail(store), pytest.raises(sqlite3.DatabaseError):
        grade_responses(store, PaidCalls(store, caps=CAPS, run_id="g1"), route, clock=clock_at(8))
    assert store.response(response["id"])["grade_status"] == "pending"
    assert store.judgments(task="project_probe_grade") == []
    results = grade_responses(store, PaidCalls(store, caps=CAPS, run_id="g2"), route, clock=clock_at(8))
    assert [result["status"] for result in results] == ["graded"]
    (judgment,) = store.judgments(task="project_probe_grade", left_id=response["id"])
    assert judgment["score"] == store.response(response["id"])["score"]


def test_an_adjudication_never_persists_without_its_judgment(captured):
    store, _selected, response = _answered(captured)
    grade_responses(store, PaidCalls(store, caps=CAPS, run_id="g"), _routes(ProjectFake())["grading"], clock=clock_at(8))
    with judgment_writes_fail(store), pytest.raises(sqlite3.DatabaseError):
        contest_grade(store, response["id"], score=0.2, note="missed it", clock=clock_at(9))
    assert store.response(response["id"])["contested"] == 0
    contest_grade(store, response["id"], score=0.2, note="missed it", clock=clock_at(9))
    rows = store.judgments(task="project_probe_grade", left_id=response["id"])
    assert [row["judge"] for row in rows] == ["llm", "owner"]


def test_an_unfair_tap_never_persists_without_its_judgment(captured):
    store, selected, _response = _answered(captured)
    with judgment_writes_fail(store), pytest.raises(sqlite3.DatabaseError):
        record_response(store, selected[1]["id"], kind="unfair", clock=clock_at(8))
    assert store.response_for_probe(selected[1]["id"]) is None
    record_response(store, selected[1]["id"], kind="unfair", clock=clock_at(8))
    assert len(store.judgments(task="project_probe_unfair")) == 1


# --- concurrent graders (F6) ------------------------------------------------------------


def test_a_second_grader_waits_its_turn_instead_of_paying(captured):
    from learnloop.projects.probes import _exclusive

    store, _selected, response = _answered(captured)
    fake = ProjectFake()
    with _exclusive(store.path.parent, "grade.lock") as held:
        assert held
        results = grade_responses(store, PaidCalls(store, caps=CAPS, run_id="late"), _routes(fake)["grading"], clock=clock_at(8))
    assert [result["status"] for result in results] == ["busy"]
    assert fake.calls == {} and store.response(response["id"])["grade_status"] == "pending"


def test_interleaved_graders_leave_one_outcome_and_report_it(captured, monkeypatch):
    from contextlib import contextmanager as _cm

    from learnloop.projects import probes as probes_module

    @_cm
    def no_lock(*_args, **_kwargs):  # as if the lock could not help (e.g. another host)
        yield True

    monkeypatch.setattr(probes_module, "_exclusive", no_lock)
    store, _selected, response = _answered(captured)

    class FirstGrader(ProjectFake):
        def run_project_probe_grading(self, context):
            grades = super().run_project_probe_grading(context)
            return grades.model_copy(update={"grades": [g.model_copy(update={"score": 0.0, "verdict": "incorrect"}) for g in grades.grades]})

    class SlowGrader(ProjectFake):
        def run_project_probe_grading(self, context):
            # The first grader reads, pays and persists while this one is in flight.
            grade_responses(store, PaidCalls(store, caps=CAPS, run_id="first"), _routes(FirstGrader())["grading"], clock=clock_at(8))
            return super().run_project_probe_grading(context)

    results = grade_responses(store, PaidCalls(store, caps=CAPS, run_id="second"), _routes(SlowGrader())["grading"], clock=clock_at(8))
    stored = store.response(response["id"])
    assert stored["score"] == 0.0
    assert results == [{"response_id": response["id"], "status": "already_graded", "score": 0.0, "verdict": "incorrect"}]
    (judgment,) = store.judgments(task="project_probe_grade", left_id=response["id"])
    assert judgment["score"] == 0.0
