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
