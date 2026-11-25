"""Review round 3, FR3-6 (class 3: a rebuild writes raw evidence), by the owner's decision (option b).

An ordinary grade commits even when its grade-channel write fails. That answer then has no observation (the identity
mint failed) or an observation without a raw grade (the grading step failed after it). A rebuild derives: it leaves the
answer as it is, with every raw row identical, and reports it; ``learnloop doctor`` names it with a plain-words issue,
and only its explicit repair (``doctor --fix-state``) records it. The failure is logged where it happens. History from
before the activity substrate is still backfilled once (``tests/test_replay_writes_no_ledger.py``).
"""

from __future__ import annotations

import logging

import pytest

from learnloop.attempts import grade_resolution
from learnloop.ops.doctor import run_doctor
from learnloop.substrate.compat.activity_backfill import answers_without_grade_record
from learnloop.substrate.rebuild_orchestrator import rebuild_all_derived_state
from learnloop.substrate.replay import replay_learning_object

from tests.grade_application_golden_helpers import _apply, _day, build_graded_vault

#: The grade record's raw rows: what a rebuild must leave exactly as it found them.
EVIDENCE = ("activity_administrations", "activity_exposure_events", "activity_observations", "raw_grade_events",
            "grade_interpretations", "measurement_events")
CODE = "answers:grade_record_missing"


def _ids(repository) -> dict[str, frozenset[str]]:
    with repository.connection() as connection:
        return {table: frozenset(row[0] for row in connection.execute(f"SELECT id FROM {table}")) for table in EVIDENCE}


def _fails(*_args, **_kwargs):
    raise RuntimeError("the grade channel is down")


def _degraded_grade(vault, repository, monkeypatch, caplog, failure: str):
    target = "ensure_administration_identity" if failure == "observation" else "resolve_grade"
    with monkeypatch.context() as patch, caplog.at_level(logging.WARNING):
        patch.setattr(grade_resolution, target, _fails)
        _apply(vault, repository, {"setup": 2, "result": 1}, attempt_id="att_degraded", when=_day(2))
    # Visible where it happens: the log names the answer and the repair.
    assert any("att_degraded" in record.getMessage() and "doctor" in record.getMessage()
               for record in caplog.records), caplog.text


@pytest.mark.parametrize("failure", ["observation", "grade"])
def test_a_rebuild_leaves_a_degraded_grade_unrecorded_and_doctor_repairs_it(failure, tmp_path, monkeypatch, caplog):
    paths, vault, repository = build_graded_vault(tmp_path)
    _apply(vault, repository, {"setup": 2, "result": 2}, attempt_id="att_recorded", when=_day(1))
    _degraded_grade(vault, repository, monkeypatch, caplog, failure)
    learning_object_id = repository.fetch_practice_attempt("att_degraded")["learning_object_id"]
    missing = [{"attempt_id": "att_degraded", "learning_object_id": learning_object_id, "missing": failure}]
    assert answers_without_grade_record(vault, repository) == missing

    # A whole-vault rebuild and a per-LO replay leave every raw row as it was, and the rebuild reports the answer.
    before = _ids(repository)
    result = rebuild_all_derived_state(vault, repository)
    replay_learning_object(vault, repository, learning_object_id)
    assert _ids(repository) == before
    details = {replayer.name: replayer.details for replayer in result.replayers}
    assert any(detail.get("answers_without_grade_record") == missing for detail in details.values())

    # Doctor names it in plain words; its repair records it, and nothing is left to report or to reconcile.
    issues = [issue for issue in run_doctor(paths.root).issues if issue.code == CODE]
    assert [issue.details for issue in issues] == [{"answers": missing}]
    assert "--fix-state" in issues[0].message
    repaired = run_doctor(paths.root, fix_state=True)
    assert not [issue for issue in repaired.issues if issue.code == CODE]
    assert answers_without_grade_record(vault, repository) == []
    observation = repository.observation_by_attempt("att_degraded")
    assert observation is not None and repository.raw_grade_events_for_observation(str(observation["id"]))
    after_repair = _ids(repository)
    rebuild_all_derived_state(vault, repository)
    assert _ids(repository) == after_repair


def test_a_regrade_is_an_explicit_revision_and_records_the_missing_grade(tmp_path, monkeypatch, caplog):
    """A regrade of the degraded answer applies a new grade: the grade revision writes its record (it is not a
    rebuild), so nothing is left to report."""

    from tests.regrade_contract_replay_helpers import _regrade

    _paths, vault, repository = build_graded_vault(tmp_path)
    _degraded_grade(vault, repository, monkeypatch, caplog, "observation")
    _regrade(vault, repository, "att_degraded", {"setup": 2, "result": 2}, when=_day(3))
    assert answers_without_grade_record(vault, repository) == []


# -- Review round 4, R4-S3: the repair writes the live grade, or leaves the answer visible --------------------------

#: The raw grade event's columns a repair must reproduce as the live write made them (ids and stamps aside).
LIVE_COLUMNS = ("role", "grader_provider", "grading_prompt_version", "grader_output_schema_version",
                "grader_identity_hash", "observed_class", "model_confidence", "confidence_bucket",
                "criterion_observed_classes_json", "raw_output_json")


def _blind_graded(vault, repository, attempt_id, when, *, run: bool = True):
    """A grade outside the practice door as teach-back writes it: a blind grading run, the vault grader's blind
    calibration identity and no blind record; a fatal error with a full score (what the live classification reads)."""

    from learnloop.attempts.grading import vault_grading_calibration_identity

    run_id = None
    if run:
        run_id = repository.insert_agent_run({"id": f"run_{attempt_id}", "purpose": "teach_back_grading",
                                              "output_schema": "BlindGradingProposal", "status": "completed",
                                              "started_at": when.isoformat()})
    fatal = ["conceptual_slip"]  # with a full score, the classification reads it (not a success)
    _apply(vault, repository, {"setup": 2, "result": 2}, attempt_id=attempt_id, when=when, source="codex",
           grade={"fatal_errors": fatal},
           apply={"grading_agent_run_id": run_id, "grader_identity": vault_grading_calibration_identity()})
    return fatal


def _raw(repository, attempt_id):
    """The answer's first raw grade event (the live write's; the repair's for a repaired answer)."""

    with repository.connection() as connection:
        row = connection.execute("SELECT * FROM raw_grade_events WHERE attempt_id = ? ORDER BY rowid",
                                 (attempt_id,)).fetchone()
    return dict(row) if row is not None else None


def test_a_repaired_blind_grade_is_the_one_the_live_write_makes(tmp_path, monkeypatch, caplog):
    paths, vault, repository = build_graded_vault(tmp_path)
    fatal = _blind_graded(vault, repository, "att_live", _day(1))
    with monkeypatch.context() as patch, caplog.at_level(logging.WARNING):
        patch.setattr(grade_resolution, "resolve_grade", _fails)
        _blind_graded(vault, repository, "att_degraded", _day(2))
    assert [entry["attempt_id"] for entry in answers_without_grade_record(vault, repository)] == ["att_degraded"]

    run_doctor(paths.root, fix_state=True)
    live, repaired = _raw(repository, "att_live"), _raw(repository, "att_degraded")
    assert repaired is not None
    # Failed before: the repair fell back to the joint grader's identity, named no run and read no fatal error.
    assert {c: repaired[c] for c in LIVE_COLUMNS} == {c: live[c] for c in LIVE_COLUMNS}
    assert repaired["agent_run_id"] == "run_att_degraded" and live["agent_run_id"] == "run_att_live"
    assert fatal and live["observed_class"] != "success"
    assert answers_without_grade_record(vault, repository) == []


def test_a_repair_whose_grading_run_is_gone_keeps_the_answer_visible(tmp_path, monkeypatch, caplog):
    paths, vault, repository = build_graded_vault(tmp_path)
    with monkeypatch.context() as patch, caplog.at_level(logging.WARNING):
        patch.setattr(grade_resolution, "resolve_grade", _fails)
        _blind_graded(vault, repository, "att_degraded", _day(2), run=False)

    report = run_doctor(paths.root, fix_state=True)
    # Failed before: the repair wrote a joint grade with no run and the issue cleared.
    assert _raw(repository, "att_degraded") is None
    issue = next(issue for issue in report.issues if issue.code == CODE)
    [entry] = issue.details["answers"]
    assert entry["attempt_id"] == "att_degraded" and entry["unrecoverable"] == "grading_run_missing"


def test_a_sitting_answer_whose_own_grade_record_failed_stays_visible(tmp_path, monkeypatch, caplog):
    """FR3-6's residue: a once-graded exam sitting answer is recorded by the sitting's own write; when that write
    failed it was left out of doctor's check (as an import, which records none, is). It is reported now, and the
    repair (which records through the practice channel) leaves it visible rather than writing another grade."""

    from pathlib import Path

    from learnloop.clock import FrozenClock
    from learnloop.goals.exam_session import finish_exam, record_exam_answer

    from tests.exam_session_helpers import _grade, _reserved_and_started
    from tests.helpers import NOW

    vault, repository, session = _reserved_and_started(tmp_path)
    session_id = session["session_id"]
    record_exam_answer(vault, repository, session_id, "pi_exam_a", answer_md="A", resolved_grade=_grade(4))
    with monkeypatch.context() as patch:
        patch.setattr(grade_resolution, "resolve_grade", _fails)
        finish_exam(vault, repository, session_id, clock=FrozenClock(NOW))
    [answer] = repository.exam_answers(session_id)
    missing = answers_without_grade_record(vault, repository)
    assert [entry["attempt_id"] for entry in missing] == [answer["attempt_id"]]  # failed before: []
    root = next(p for p in Path(repository.sqlite_path).resolve().parents if (p / "learnloop.toml").exists())
    report = run_doctor(root, fix_state=True)
    issue = next(issue for issue in report.issues if issue.code == CODE)
    assert [entry["unrecoverable"] for entry in issue.details["answers"]] == ["exam_sitting_channel"]
    assert _raw(repository, answer["attempt_id"]) is None
