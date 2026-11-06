"""Teacher TE2-log, part 6: ``learnloop teacher report``'s new lines (spec_teacher_v1 §11.10), on a synthetic lesson.

Read-only: the pool weight's trajectory per forecaster (λ̂ and its sd from the seeded prior through each update),
the lessons (opened, closed by reason, active and elapsed minutes apart, missing intervals, delayed checks), the
episodes, the probe and placement forecasts (natural and randomized outcomes apart, each labelled) and the coverage
of item 5's fields.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from typer.testing import CliRunner

from learnloop.clock import FrozenClock
from learnloop.teacher import service as S
from learnloop.teacher.report import COVERAGE_FIELDS, report
from learnloop.vault.loader import load_vault
from tests.teacher_fakes import TeacherFake, build_teacher_vault, check_turn, clients, landed_turn, plan_turn
from tests.test_teacher_te2log_receipt import T0, _iso, _run


def _cold(paths, repository, item, days, right=True):
    from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt

    return complete_self_graded_attempt(
        load_vault(paths.root), repository,
        AttemptDraft(practice_item_id=item, learner_answer_md="cold answer", attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4 if right else 0}, confidence=4),
        clock=FrozenClock(T0 + timedelta(days=days)))


def test_the_report_on_a_synthetic_lesson(tmp_path, capsys):
    intervals = [{"screen_session": "s", "seq": 1, "started_at": _iso(0), "ended_at": _iso(4), "foreground": True},
                 {"screen_session": "s", "seq": 3, "started_at": _iso(6), "ended_at": _iso(8), "foreground": False}]
    repository, lesson_id, receipt = _run(tmp_path, intervals=intervals)
    paths = type("P", (), {"root": tmp_path / "vault"})()
    _cold(paths, repository, "pi_det_1", 2)  # resolves the two lo_det placement forecasts (n0, both plan versions)
    out = report(load_vault(paths.root), repository, today=(T0 + timedelta(days=30)).date().isoformat())
    lines = out["lines"]
    print("\n".join(lines))
    text = "\n".join(lines)
    assert "lessons: 1 opened, 0 open; closed: goal_reached 1" in text
    assert ("lesson minutes: active 4.0 (over 1 lesson(s) with intervals; 0 with none, active unknown) · elapsed 10.0"
            " · 1 interval(s) missing") in text
    delayed = receipt["delayed_checks"]
    committed = sum(1 for entry in delayed if entry.get("commitment_id"))
    assert out["lessons"]["delayed_checks"]["committed"] == committed and out["lessons"]["delayed_checks"]["due"] == committed
    assert "episodes: probe 0, detour 2, gap 0, goal_lo 0" in text
    assert "detours by repair: reteach 1, unlogged 1 (1 unlogged)" in text
    assert "probes: 0 generated, 0 refused, 0 retired unused, 0 answered" in text
    # Placement forecasts: natural (self-selected) apart from randomized.
    held = out["forecasts"]["lesson_node_held"]
    assert held["receipts"] == 4 and held["natural"]["n"] == 2 and held["natural"]["label"] == "self-selected"
    assert held["natural"]["rate"] == 1.0 and held["natural"]["mean_p"] == 0.8
    assert held["randomized"]["n"] == 0 and held["randomized"]["label"] == "randomized"
    assert "against RO5's randomized checks (randomized): none scored yet" in text
    assert "probe forecasts (lesson_probe_correct) against their grades: none scored yet" in text
    # Coverage of item 5's fields: two detours, one noted (with a hypothesis and p), one unlogged.
    fields = out["coverage"]["fields"]
    assert out["coverage"]["episodes"] == 2 and set(fields) == set(COVERAGE_FIELDS)
    assert (fields["hypothesis"], fields["repair_class"], fields["teacher_p"], fields["origin"]) == (1, 2, 1, 2)
    assert fields["elapsed_minutes"] == 2 and fields["active_minutes"] == 2 and fields["objective_trace"] == 0
    assert "coverage of item 5's fields over 2 episode(s): hypothesis 1/2, repair_class 2/2" in text


def test_the_pool_weights_trajectory_per_forecaster(tmp_path):
    paths, repository = build_teacher_vault(tmp_path / "vault")
    fake = TeacherFake([plan_turn, landed_turn(p=0.3), check_turn()])
    view = S.open_lesson(load_vault(paths.root), repository, entry="learning_object", learning_object_ids=["lo_eigen"],
                         clients=clients(fake), clock=FrozenClock(T0))
    for minute, (action, payload) in enumerate((("reply", {"text": "go"}), ("reply", {"text": "and?"}),
                                                 ("answer_check", {"answer": "det(A - tI) = 0", "tap": 5})), start=1):
        S.take_turn(load_vault(paths.root), repository, lesson_id=view["lesson_id"], action=action, payload=payload,
                    clients=clients(fake), clock=FrozenClock(T0 + timedelta(minutes=minute)))
    _cold(paths, repository, "pi_eig_2", 3)
    out = report(load_vault(paths.root), repository)
    family = f"{S.DOCTRINE_VERSION}+teacher_episodes_v1:fake-teacher-model"
    points = out["pool_trajectory"][family]
    assert points[0]["at"] is None and points[0]["updates"] == 0
    assert len(points) >= 2 and points[-1]["updates"] == len(points) - 1
    assert points[-1]["lambda"] == round(out["pool"][family]["lambda"], 6)
    assert 0.0 < points[-1]["sd"] <= points[0]["sd"] + 1e-6
    assert any(line.startswith(f"pool weight trajectory {family}: prior λ̂") for line in out["lines"])


def test_randomized_checks_are_scored_apart_with_their_r(tmp_path, monkeypatch):
    from learnloop.router_objective import checks as RC

    repository, _lesson_id, _receipt = _run(tmp_path)
    paths = type("P", (), {"root": tmp_path / "vault"})()
    attempt = _cold(paths, repository, "pi_det_1", 2, right=False)
    attempt_id = getattr(attempt, "attempt_id", None) or getattr(attempt, "id", None) or attempt["attempt_id"]
    slot = RC.Resolved(assignment_id="pa_1", local_date="2026-11-07", topic="lo_det", r=0.25, status="completed",
                       outcome=0.0, attempt_id=str(attempt_id), item_id="pi_det_1")
    monkeypatch.setattr(RC, "resolve", lambda connection, **kwargs: [slot])
    out = report(load_vault(paths.root), repository)
    held = out["forecasts"]["lesson_node_held"]
    # The same outcome, read once as natural (self-selected) and once as the randomized check it was, apart.
    assert held["randomized"]["n"] == 2 and held["randomized"]["r"] == [0.25, 0.25]
    assert held["randomized"]["rate"] == 0.0 and held["natural"]["rate"] == 0.0
    assert any("randomized, r 0.250, 0.250" in line for line in out["lines"])


def test_the_cli_prints_the_new_lines(tmp_path):
    from learnloop.cli.teacher import teacher_app

    _repository, _lesson_id, _receipt = _run(tmp_path)
    result = CliRunner().invoke(teacher_app, ["--vault", str(tmp_path / "vault"), "--json"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["episodes"]["by_kind"]["detour"] == 2 and "coverage" in data and "pool_trajectory" in data
