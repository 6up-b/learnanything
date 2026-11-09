"""Recognition and effort RE0 (docs/specs/spec_recognition_and_effort_v1.md §4): active seconds and the cue label.

Capture only: nothing here serves, scores, schedules or projects, and nothing in ``adaptive_difficulty`` reads either.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import sqlite3

import pytest

from learnloop.attempts.attempts import AttemptDraft, AttemptValidationError, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.stores import router_objective as receipts
from learnloop.db.table_roles import TABLE_ROLES, TableRole
from learnloop.vault.paths import VaultPaths
from learnloop.recognition import cue as C
from learnloop.recognition import ledger as L
from learnloop.recognition import report as R

from tests.test_exam_seeding import _exam_vault

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 5, 19, 15, 30, 7, tzinfo=UTC)
WINDOW_HOURS = 6.0
SESSION_GAP = 60.0


def _stamp(minutes: float) -> str:
    return (NOW + timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _attempt(identifier: str, minutes: float, *, session: str | None = "s1", lo: str = "lo_a", concept: str = "c_a",
             latency: int | None = None, kind: str = "independent_attempt", mode: str = "free_response") -> dict:
    return {"id": identifier, "session_id": session, "learning_object_id": lo, "concept": concept,
            "created_at": _stamp(minutes), "latency_seconds": latency, "attempt_type": kind, "practice_mode": mode,
            "practice_item_id": f"item_{identifier}"}


def _ledger(attempts, **more) -> C.CueLedger:
    more.setdefault("method_stated", {str(row["id"]): False for row in attempts})
    return C.CueLedger(attempts=attempts, window_hours=WINDOW_HOURS, session_gap_minutes=SESSION_GAP, **more)


# -- the cue label ---------------------------------------------------------------------------------------------------


def test_the_same_ledger_gives_the_same_label():
    attempts = [_attempt("a1", 0), _attempt("a2", 5), _attempt("a3", 9, lo="lo_b", concept="c_a")]
    exposures = [C.Exposure("lo_b", _stamp(-30), C.READING)]
    first = C.cues(attempts, _ledger(attempts, exposures=exposures))
    # A second ledger built from the same records, the attempts in another order, reads the same.
    again = C.cues(list(reversed(attempts)), _ledger(list(reversed(attempts)), exposures=list(exposures)))
    assert first == again
    assert first["a3"].same_concept_before and not first["a3"].same_lo_before and first["a3"].after_reading
    assert first["a2"].same_lo_before and first["a2"].same_concept_before
    # Reading an attempt twice, or in another order, changes nothing.
    ledger = _ledger(attempts, exposures=exposures)
    assert [C.attempt_cue_v1(row, ledger) for row in attempts] == [C.attempt_cue_v1(row, ledger) for row in attempts]


def test_a_synthetic_trace_with_no_cues_present_is_uncued():
    # Different topics in one session, no reading, no lesson, no method, no follow-up, no check, a long gap between.
    attempts = [_attempt("a1", 0, lo="lo_a", concept="c_a"), _attempt("a2", 5, lo="lo_b", concept="c_b"),
                _attempt("a3", 9, lo="lo_c", concept="c_c")]
    labels = C.cues(attempts, _ledger(attempts))
    for found in labels.values():
        assert found.label == C.UNCUED and found.present == () and found.unreadable == ()
        assert found.version == "attempt_cue_v1"


@pytest.mark.parametrize("name", C.FIELDS)
def test_each_cue_alone_makes_an_attempt_cued(name):
    attempts = [_attempt("a1", 0, lo="lo_a", concept="c_a"), _attempt("a2", 5, lo="lo_b", concept="c_b")]
    more: dict = {}
    if name == "same_lo_before":
        attempts[1] = _attempt("a2", 5, lo="lo_a", concept="c_b")
    elif name == "same_concept_before":
        attempts[1] = _attempt("a2", 5, lo="lo_b", concept="c_a")
    elif name == "after_reading":
        more["exposures"] = [C.Exposure("lo_b", _stamp(-60), C.READING)]
    elif name == "after_lesson":
        more["exposures"] = [C.Exposure("lo_b", _stamp(-60), C.LESSON)]
    elif name == "method_stated":
        more["method_stated"] = {"a1": False, "a2": True}
    elif name == "followup_of_miss":
        more["followups"] = frozenset({"a2"})
    elif name == "randomized_check":
        more["checks"] = frozenset({"a2"})
    found = C.attempt_cue_v1(attempts[1], _ledger(attempts, **more))
    assert found.label == C.CUED and found.present == (name,)


def test_the_cue_window_counts_what_happened_before_the_attempt_began_and_not_help_during_it():
    attempts = [_attempt("a1", 60, latency=600)]  # began at minute 50
    inside = [C.Exposure("lo_a", _stamp(50 - 60 * (WINDOW_HOURS - 1)), C.READING)]
    outside = [C.Exposure("lo_a", _stamp(50 - 60 * (WINDOW_HOURS + 1)), C.READING)]
    during = [C.Exposure("lo_a", _stamp(55), C.READING)]  # a reveal while answering is help, not a cue
    tied = [C.Exposure("lo_a", _stamp(40), C.READING, attempt_id="a1")]
    assert C.attempt_cue_v1(attempts[0], _ledger(attempts, exposures=inside)).after_reading
    for exposures in (outside, during, tied):
        assert not C.attempt_cue_v1(attempts[0], _ledger(attempts, exposures=exposures)).after_reading
    other_topic = [C.Exposure("lo_z", _stamp(40), C.READING)]
    assert not C.attempt_cue_v1(attempts[0], _ledger(attempts, exposures=other_topic)).after_reading


def test_the_previous_attempt_is_the_sessions_and_a_session_less_one_reads_the_routers_gap():
    attempts = [_attempt("a1", 0, session="s1"), _attempt("a2", 5, session="s2"),
                _attempt("n1", 10, session=None), _attempt("n2", 20, session=None), _attempt("n3", 200, session=None)]
    labels = C.cues(attempts, _ledger(attempts))
    assert not labels["a2"].same_lo_before            # the previous attempt of s2 is none
    assert not labels["n1"].same_lo_before            # a session-less attempt has no earlier one
    assert labels["n2"].same_lo_before                # ten minutes later, inside the gap
    assert not labels["n3"].same_lo_before            # 180 minutes later, a new session


def test_an_unreadable_field_is_listed_and_an_imported_answer_is_unlabelled_not_uncued():
    attempts = [_attempt("a1", 0), _attempt("e1", 1, lo="lo_b", concept="c_b", kind="exam_evidence"),
                _attempt("a2", 2, lo="lo_b", concept="c_b")]
    labels = C.cues(attempts, _ledger(attempts, method_stated={"a1": None, "a2": False}))
    # Not knowing a cue is not knowing there was none: unlabelled, never uncued; a known cue still makes it cued.
    assert labels["a1"].unreadable == ("method_stated",) and labels["a1"].label == C.UNLABELLED
    known = C.attempt_cue_v1(attempts[2], _ledger(attempts, method_stated={"a2": None}, followups=frozenset({"a2"})))
    assert known.unreadable == ("method_stated",) and known.label == C.CUED
    assert labels["e1"].label == C.UNLABELLED and labels["e1"].imported and labels["e1"].unreadable == C.FIELDS
    # An import is never anyone's previous attempt.
    assert not labels["a2"].same_lo_before and not labels["a2"].same_concept_before


# -- active_seconds --------------------------------------------------------------------------------------------------


def test_active_seconds_is_a_nullable_attempt_column_filled_after_the_row_and_never_blended_with_latency(tmp_path):
    _root, loaded, repository = _exam_vault(tmp_path)
    clock = FrozenClock(NOW)
    # A resumed problem: a day's wall-clock gap in the latency, thirty-five seconds of activity across both opens.
    resumed = complete_self_graded_attempt(
        loaded, repository, AttemptDraft(practice_item_id="pi_exam_q1", learner_answer_md="A", latency_seconds=86_400,
                                         active_seconds=35),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=clock)
    silent = complete_self_graded_attempt(
        loaded, repository, AttemptDraft(practice_item_id="pi_exam_q1", learner_answer_md="B", latency_seconds=60),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=clock)
    first = repository.fetch_practice_attempt(resumed.attempt_id)
    second = repository.fetch_practice_attempt(silent.attempt_id)
    assert (first["latency_seconds"], first["active_seconds"]) == (86_400, 35)
    assert (second["latency_seconds"], second["active_seconds"]) == (60, None)  # a null stays null: no imputation
    with pytest.raises(AttemptValidationError, match="active_seconds"):
        complete_self_graded_attempt(
            loaded, repository, AttemptDraft(practice_item_id="pi_exam_q1", learner_answer_md="C", active_seconds=-1),
            SelfGradeInput(criterion_points={"correctness": 4}, confidence=4), clock=clock)


def test_migration_252_adds_one_nullable_checked_column_to_a_ledger_table(tmp_path):
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[252] == "252_attempt_active_seconds.sql"
    assert TABLE_ROLES["practice_attempts"] is TableRole.RAW_LEDGER
    _root, loaded, repository = _exam_vault(tmp_path)
    with repository.connection() as connection:
        column = next(row for row in connection.execute("PRAGMA table_info(practice_attempts)") if row[1] == "active_seconds")
        assert column[2].upper() == "INTEGER" and column[3] == 0 and column[4] is None  # nullable, no default
        definition = connection.execute("SELECT sql FROM sqlite_master WHERE name = 'practice_attempts'").fetchone()[0]
        assert "active_seconds IS NULL OR active_seconds >= 0" in definition  # the CHECK that refuses a negative
    assert 252 in applied_versions(VaultPaths(loaded.root, loaded.config).sqlite_path)


def test_a_database_below_252_records_the_attempt_and_the_fill_is_a_no_op():
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE practice_attempts (id TEXT PRIMARY KEY, latency_seconds INTEGER)")
        connection.execute("INSERT INTO practice_attempts VALUES ('a1', 5)")
        assert receipts.fill_receipt(connection, "practice_attempts", "a1", {"active_seconds": 3}) is False
        assert connection.execute("SELECT latency_seconds FROM practice_attempts").fetchone()[0] == 5
        connection.execute("ALTER TABLE practice_attempts ADD COLUMN active_seconds INTEGER")
        assert receipts.fill_receipt(connection, "practice_attempts", "a1", {"active_seconds": 3}) is True
        assert receipts.fill_receipt(connection, "practice_attempts", "a1", {"active_seconds": None}) is False
        assert connection.execute("SELECT active_seconds FROM practice_attempts").fetchone()[0] == 3


# -- the report ------------------------------------------------------------------------------------------------------


def _pin_contract(connection, attempt_id: str, item: str = "pi_exam_q1", *, method: bool = False) -> None:
    """Grade the attempt under a frozen contract, so its required method is readable (as every live attempt's is)."""

    contract = {"required_method": {"name": "SVD", "criterion_ids": []}} if method else {}
    connection.execute(
        "INSERT OR IGNORE INTO assessment_contract_versions(id, practice_item_id, contract_hash, contract_json, "
        "schema_version, created_at) VALUES (?, ?, ?, ?, 1, ?)",
        (f"acv_{item}_{int(method)}", item, f"h{int(method)}", json.dumps(contract), _stamp(-1)))
    connection.execute(
        "INSERT INTO grading_evidence(id, attempt_id, criterion_id, points_awarded, grader_tier, created_at, "
        "assessment_contract_version_id) VALUES (?, ?, 'correctness', 1, 0, ?, ?)",
        (f"ge_{attempt_id}", attempt_id, _stamp(-1), f"acv_{item}_{int(method)}"))


def _insert(connection, row: dict, *, correctness: float | None, active: int | None, item: str = "pi_exam_q1") -> None:
    connection.execute(
        "INSERT INTO practice_attempts(id, practice_item_id, learning_object_id, subject, concept, practice_mode, "
        "attempt_type, learner_answer_md, evidence_facets_json, evidence_weights_json, correctness, latency_seconds, "
        "created_at, session_id, entry_surface, active_seconds) "
        "VALUES (?, ?, ?, 's', ?, ?, ?, 'x', '[]', '{}', ?, ?, ?, ?, 'desktop', ?)",
        (row["id"], item, row["learning_object_id"], row["concept"], row["practice_mode"], row["attempt_type"],
         correctness, row["latency_seconds"], row["created_at"], row["session_id"], active))


def test_the_report_splits_method_selection_by_cue_reports_missing_and_never_imputes(tmp_path):
    _root, loaded, repository = _exam_vault(tmp_path)
    with repository.connection() as connection:
        connection.execute("DELETE FROM practice_attempts")
        # Two topics in turn: the first attempt of each has no cue; the third repeats a topic (cued).
        rows = [
            (_attempt("u1", 0, lo="lo_svd_definition", concept="k1", mode="method_selection", latency=30), 1.0, 20),
            (_attempt("c1", 5, lo="lo_svd_definition", concept="k1", mode="method_selection", latency=40), 0.0, None),
            (_attempt("c2", 9, lo="lo_svd_definition", concept="k1", mode="free_response", latency=50), 1.0, 12),
        ]
        for row, correctness, active in rows:
            _insert(connection, row, correctness=correctness, active=active)
            _pin_contract(connection, row["id"])
        section = R.section(connection, loaded, repository, window_hours=WINDOW_HOURS)
    assert section["available"] and "observational" in section["label"]
    method = section["method_selection"]
    assert method["uncued"]["attempts"] == 1 and method["uncued"]["mean_correctness"] == 1.0
    assert method["cued"]["attempts"] == 1 and method["cued"]["mean_correctness"] == 0.0
    # The cued attempt sent no active seconds: missing, not latency, and the mean is over what was sent.
    assert method["cued"]["active_seconds_sent"] == 0 and method["cued"]["active_seconds_missing"] == 1
    assert method["cued"]["mean_active_seconds"] is None and method["cued"]["latency_sent"] == 1
    assert method["uncued"]["mean_active_seconds"] == 20.0
    pool = section["practice_pool"]
    assert pool["uncued"]["attempts"] == 1 and pool["cued"]["attempts"] == 2
    assert pool["cued"]["mean_active_seconds"] == 12.0 and pool["cued"]["active_seconds_missing"] == 1
    assert section["active_seconds_by_surface"]["desktop"] == {"sent": 2, "missing": 1}
    text = "\n".join(R.lines(section))
    assert "Recognition and effort (RE0" in text and "method_selection" in text and "missing" in text


def test_the_report_reads_imported_exam_answers_as_unlabelled_goal_date_reads(tmp_path):
    _root, loaded, repository = _exam_vault(tmp_path)
    with repository.connection() as connection:
        connection.execute("DELETE FROM practice_attempts")
        row = _attempt("e1", 0, lo="lo_svd_definition", session=None, kind="exam_evidence")
        _insert(connection, row, correctness=0.5, active=None)
        section = R.section(connection, loaded, repository, window_hours=WINDOW_HOURS)
    reads = section["goal_date_reads"]
    assert reads["unlabelled"]["attempts"] == 1 and reads["uncued"]["attempts"] == 0
    assert section["practice_attempts"] == 0


def test_the_capture_report_carries_the_section_and_stays_read_only(tmp_path):
    from learnloop.ops.capture_report import build_report, lines

    _root, loaded, repository = _exam_vault(tmp_path)
    with repository.connection() as connection:
        report = build_report(connection, loaded, repository, as_of=_stamp(0), success_correctness=0.8)
    assert report["recognition_and_effort"]["version"] == R.REPORT_VERSION
    assert any(line.startswith("Recognition and effort (RE0") for line in lines(report))


# -- nothing serving, scoring, scheduling or projecting reads it ------------------------------------------------------


def test_nothing_in_adaptive_difficulty_reads_active_seconds_or_the_cue():
    registry = {"column_classes.py", "protected_tables.py"}  # the schema's own column lists, which classify it
    offenders = []
    for path in sorted((ROOT / "src" / "learnloop" / "adaptive_difficulty").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name == "report.py":
            # The Reader visit's own payload field (``reader_view_closed``), a different record from the attempt column.
            text = text.replace('data.get("active_seconds")', "")
        for needle in ("active_seconds", "attempt_cue", "learnloop.recognition", "AttemptCue"):
            if needle in text and not (path.name in registry and needle == "active_seconds"):
                offenders.append((path.name, needle))
    assert offenders == []
    from learnloop.adaptive_difficulty import column_classes

    # Classified as content, so an AD operation can read it only through the rules, which never hand it out.
    assert "active_seconds" in column_classes._CLASSES["practice_attempts"][1].split()
    assert "active_seconds" not in column_classes._CLASSES["practice_attempts"][0].split()


def test_only_reports_read_the_new_modules():
    importers = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if "recognition" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        if "learnloop.recognition" in text:
            importers.append(str(path.relative_to(ROOT)))
    assert importers == ["src/learnloop/ops/capture_report.py"]


# -- the sidecar: each request that can carry it does -----------------------------------------------------------------


def test_the_sidecar_carries_active_seconds_into_the_attempt_beside_its_latency(tmp_path):
    from pydantic import ValidationError

    import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
    from learnloop_sidecar.context import SidecarContext
    from learnloop_sidecar.registry import METHOD_REGISTRY
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"

    def call(name: str, params: dict):
        spec = METHOD_REGISTRY[name]
        return spec.handler(ctx, spec.params_model.model_validate(params))

    session_id = call("start_session", {"availableMinutes": 25})["sessionId"]
    base = {"sessionId": session_id, "practiceItemId": "pi_svd_define_001"}
    # Two opens a day apart: the wall clock says 25 hours, the active clock thirty seconds.
    call("submit_dont_know", {**base, "latencySeconds": 90_000, "activeSeconds": 30, "submissionId": "sub_a"})
    # A surface that sends no clock (an older client, a lesson check) is stored as missing.
    call("submit_dont_know", {**base, "latencySeconds": 40, "submissionId": "sub_b"})
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        rows = {row[0]: row[1:] for row in connection.execute(
            "SELECT submission_id, latency_seconds, active_seconds FROM practice_attempts")}
    assert rows["sub_a"] == (90_000, 30) and rows["sub_b"] == (40, None)
    with pytest.raises(ValidationError):
        METHOD_REGISTRY["submit_dont_know"].params_model.model_validate({**base, "activeSeconds": -3})
    for name in ("submit_attempt", "submit_dont_know", "submit_teach_back_turn", "workbench.submit"):
        assert "active_seconds" in METHOD_REGISTRY[name].params_model.model_fields, name


def test_the_warmth_window_is_the_outcome_contracts_retention_minimum_not_a_new_constant():
    from learnloop.outcome_contract import RETENTION_MIN_DELAY_SECONDS

    assert R.warmth_window_hours() == RETENTION_MIN_DELAY_SECONDS / 3600.0 == 24.0


# -- review fixes ------------------------------------------------------------------------------------------------------

#: Hashes of these requests as main's code (before RE0, ``6c8962ce95``) computed them: the validated model dumped and
#: canonically hashed (``learnloop_mobile.adapter.canonical_hash``).
_PRE_RE0_REQUEST = {"sessionId": "s1", "practiceItemId": "i1", "answerMd": "My answer", "attemptType": "independent_attempt",
                    "submissionId": "k1", "latencySeconds": 42, "schedulerCandidateId": "cand_i1",
                    "assessmentContractVersionId": "acv", "hintsUsed": 0, "authoredHints": 0, "bookCounted": False}
_PRE_RE0_HASHES = {"submit_attempt": "4419a2a45eeacae4eb5130b3d65eef06ee38b9527adc1f83cd2c4418cae6096e",
                   "submit_dont_know": "d0e60a1daff5c860a4f5b3f1f96c6e8944c7a4968f770197c6b5d148601bf8a4"}


@pytest.mark.parametrize("name", ["submit_attempt", "submit_dont_know"])
def test_a_request_without_active_seconds_hashes_as_it_did_before_re0(name):
    from learnloop_mobile.adapter import canonical_hash
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_mobile.runtime import HostRuntime

    params = {k: v for k, v in _PRE_RE0_REQUEST.items() if name == "submit_attempt" or k not in ("answerMd", "attemptType")}
    runtime = HostRuntime.__new__(HostRuntime)
    runtime.ensure_started = lambda: None
    validated = runtime.validate(ALLOWLIST[name], params)
    assert "active_seconds" not in validated
    assert canonical_hash(validated) == _PRE_RE0_HASHES[name]
    # A request that sends it is a different request, and says so.
    sent = runtime.validate(ALLOWLIST[name], {**params, "activeSeconds": 30})
    assert sent["active_seconds"] == 30 and canonical_hash(sent) != _PRE_RE0_HASHES[name]


def test_an_unchanged_retry_accepted_before_re0_is_not_a_conflict(tmp_path):
    from learnloop.capture.jobs import accept_job
    from learnloop.db.repositories import Repository
    from learnloop_mobile.adapter import canonical_hash
    from learnloop_mobile.allowlist import ALLOWLIST
    from learnloop_mobile.runtime import HostRuntime
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    repo = Repository(paths.sqlite_path)
    runtime = HostRuntime.__new__(HostRuntime)
    runtime.ensure_started = lambda: None
    validated = runtime.validate(ALLOWLIST["submit_attempt"], _PRE_RE0_REQUEST)
    # The job as it was stored by a pre-RE0 host: the pre-RE0 hash.
    accept_job(repo, device_id="d1", request_id="k1", method="submit_attempt", params=validated,
               params_sha256=_PRE_RE0_HASHES["submit_attempt"], boot_id="b")
    job, enqueue = accept_job(repo, device_id="d1", request_id="k1", method="submit_attempt", params=validated,
                              params_sha256=canonical_hash(validated), boot_id="b")
    assert enqueue is False and job["request_id"] == "k1"


def test_an_attempt_with_an_unreadable_cue_stays_out_of_the_uncued_mean(tmp_path):
    _root, loaded, repository = _exam_vault(tmp_path)
    with repository.connection() as connection:
        connection.execute("DELETE FROM practice_attempts")
        # No grading evidence, so no pinned contract: method_stated is unknown for this correct first attempt.
        _insert(connection, _attempt("o1", 0, lo="lo_svd_definition", mode="method_selection"), correctness=1.0, active=10)
        section = R.section(connection, loaded, repository, window_hours=WINDOW_HOURS)
    method = section["method_selection"]
    assert method["uncued"]["attempts"] == 0 and method["uncued"]["scored"] == 0
    assert method["unlabelled"]["attempts"] == 1 and method["unlabelled"]["mean_correctness"] == 1.0
    assert section["unlabelled_for_an_unreadable_field"] == 1
