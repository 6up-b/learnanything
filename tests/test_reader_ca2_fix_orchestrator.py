"""Reader CA2, one Ask: the orchestrator's fix round after the final Codex verify
(docs/reviews/reader-ca2-one-ask-codex-review.md, "Fix round (orchestrator)").

One component model for an attempt's help, each component counted once:
the answer box's authored reveals (the client's count, which the workbench
carries as ``carried_hints``), the book left open, an earlier attempt's help
opened before Submit (its own component, ``workbench_sessions.earlier_opened_at``
once the draft moves into steps), and the questions the server folds.

* F15: carrying an earlier opening into steps never raises the authored-hint
  count the answer box restores (which would reveal an authored hint the
  learner never asked for).
* F1: resuming a workbench that already carried authored hints keeps a new
  earlier opening as a distinct event (2 events -> 2).
* F12: a stored withheld answer (a row written before the take step was
  stored) reaches the question queue only as its take step.

Every scenario runs on real state through the RPCs; every model is a fake.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
from learnloop.tutor.tutor_qa import WITHHELD_ANSWER_MD
from tests.ro1_availability_helpers import RO1_ALTERED_TABLES
from tests.te3a_migration_helpers import TE3A_ALTERED_TABLES
from tests.hint_fakes import ITEM as CDF_ITEM, WORK
from tests.hint_h2b_review_helpers import grader  # noqa: F401 - the blind grader fixture
from tests.reader_ca2_codex_rereview_helpers import _attempt, _draft, _steps_sidecar
from tests.reader_ca2_codex_review_helpers import (  # noqa: F401 - the sidecar fixture
    ITEM,
    FakeTutor,
    _call,
    sidecar,
)
from tests.learner_claim_superseded_migration_helpers import SUPERSEDED_ALTERED_TABLES
from tests.deliverable_curriculum_migration_helpers import C0B_ADDED_OBJECTS
from tests.learner_notes_migration_helpers import C2_ADDED_OBJECTS
# TE1's 234 and TE1b's 236 follow on the way to head (composed in tests/test_teacher_te1b_migration.py).
from tests.teacher_te1b_migration_helpers import TE1_AND_TE1B_ADDED_OBJECTS as TE1_ADDED_OBJECTS
from tests.teacher_te1b_migration_helpers import TE1_AND_TE1B_ALTERED_TABLES as TE1_ALTERED_TABLES
from tests.figure_prefetch_migration_helpers import P5_ADDED_OBJECTS
from tests.data_capture_migration_helpers import DATA_CAPTURE_ADDED_OBJECTS
from tests.followup_migration_helpers import FOLLOWUP_ADDED_OBJECTS
from tests.hypothesis_marks_migration_helpers import MARKS_ADDED_OBJECTS
from tests.router_objective_migration_helpers import RO0_ADDED_OBJECTS
from tests.ro2_history_migration_helpers import RO2_ADDED_OBJECTS
from tests.ro4_traces_migration_helpers import RO4_ADDED_OBJECTS
from tests.teacher_te2log_migration_helpers import TE2LOG_ADDED_OBJECTS
from tests.ih3_migration_helpers import IH3_ADDED_OBJECTS
from tests.decision_records_migration_helpers import B1_ADDED_OBJECTS, B1_ALTERED_TABLES
from tests.apply_intents_conflicted_migration_helpers import K35_ALTERED_TABLES
from tests.mobile_jobs_migration_helpers import M2A_ADDED_OBJECTS
from tests.rw5c_migration_helpers import RW5C_ADDED_OBJECTS
from tests.helpers import MIGRATION_HEAD_FIXTURE, migration_head
from tests.reader_ca2_fix_orchestrator_helpers import CA2_ALTERED_TABLES, _open, _row, _step


def _answer_box_submit(ctx, session: str, *, hints: int, key: str) -> str:
    return _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": CDF_ITEM, "answerMd": WORK, "attemptType": "independent_attempt",
        "hintsUsed": hints, "authoredHints": hints,
        "selfGrade": {"criterionPoints": {"cdf": 2, "value": 0}, "confidence": 3}, "submissionId": key,
    })["attemptId"]


# -- F15: the earlier opening is never an authored reveal ---------------------------------------------


def test_f15_an_earlier_opening_carried_into_steps_is_not_an_authored_hint(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    view = _open(ctx, session)
    # What the answer box restores on the way back is its authored reveals
    # only (none here); the opening is its own component on the problem.
    assert view["carriedHints"] == 0
    assert view["earlierOpened"] is True
    assert _row(paths, view["sessionId"])["earlier_opened_at"]
    _step(ctx, view["sessionId"])
    attempt = _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 1


def test_f15_the_help_record_still_counts_a_carried_opening_after_another_items_draft(tmp_path, grader):
    _paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    _open(ctx, session)
    _draft(ctx, session, "pi_svd_define_001", "kB")
    _draft(ctx, session, CDF_ITEM, "kA")
    record = _call(ctx, "get_tutor_transcript", {"context": "practice", "practiceItemId": CDF_ITEM,
                                                 "sessionId": session, "submissionId": "kA"})["helpRecord"]
    assert record["earlierOpened"] is True and record["counted"] == 1
    assert [entry["kind"] for entry in record["items"]] == ["earlier"]


def test_f15_authored_reveals_and_the_opening_are_carried_apart(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    view = _open(ctx, session, carried=1)
    assert view["carriedHints"] == 1 and view["earlierOpened"] is True
    _step(ctx, view["sessionId"])
    attempt = _call(ctx, "workbench.submit", {"sessionId": view["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_f15_after_steps_the_answer_box_submit_counts_the_reveals_and_the_opening(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    view = _open(ctx, session, carried=1)
    # Back on the answer box the screen restores its one authored reveal and
    # reveals one more; the opening is the server's to add, once.
    attempt = _answer_box_submit(ctx, session, hints=2, key="kA")
    assert _attempt(paths, attempt)["hints_used"] == 3
    assert view["carriedHints"] == 1


def test_f15_an_abandoned_problem_never_takes_the_opening_with_it(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    view = _open(ctx, session)
    # The learner sets the steps aside and submits from the answer box: the
    # draft's opening still counts once (the problem no longer holds it).
    _call(ctx, "workbench.abandon", {"sessionId": view["sessionId"]})
    attempt = _answer_box_submit(ctx, session, hints=0, key="kA")
    assert _attempt(paths, attempt)["hints_used"] == 1


# -- F1: a resume keeps a new opening as its own event ------------------------------------------------


def test_f1_a_resume_after_carried_reveals_counts_a_new_opening_too(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    # Item A's workbench carries one authored hint from an earlier draft.
    _draft(ctx, session, CDF_ITEM, "kA")
    first = _open(ctx, session, carried=1)
    _step(ctx, first["sessionId"])
    # A fresh draft (no reveals) opens an earlier attempt's help, then resumes A.
    _draft(ctx, session, CDF_ITEM, "kB", earlierOpened=True)
    resumed = _open(ctx, session, carried=0, resume=first["sessionId"])
    assert resumed["carriedHints"] == 1 and resumed["earlierOpened"] is True
    attempt = _call(ctx, "workbench.submit", {"sessionId": first["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


def test_f1_the_opening_counts_once_however_often_the_problem_resumes(tmp_path, grader):
    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    first = _open(ctx, session, carried=1)
    _step(ctx, first["sessionId"])
    for _ in range(2):
        _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
        view = _open(ctx, session, carried=1, resume=first["sessionId"])
        assert view["carriedHints"] == 1 and view["earlierOpened"] is True
    record = view["record"]
    assert record["hints"] == 2
    attempt = _call(ctx, "workbench.submit", {"sessionId": first["sessionId"], "practiceSessionId": session})["attempt"]
    assert _attempt(paths, attempt["attemptId"])["hints_used"] == 2


# -- F12: every learner-facing read applies the delivered-answer policy ------------------------------


def test_f12_a_stored_withheld_answer_reaches_the_queue_only_as_its_take_step(sidecar):
    paths, ctx, _tutor = sidecar(tutor=FakeTutor(question_type="mechanism"))
    answer = _call(ctx, "ask_tutor_question", {"context": "practice", "practiceItemId": ITEM, "sessionId": "sess_1",
                                               "submissionId": "k1", "question": "Why orthogonal?"})
    secret = "The final answer is U Sigma V^T with sigma_1 = 3."
    # A row as a build before the take step was stored wrote it: the raw
    # answer kept beside the withheld marker.
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        context = json.loads(connection.execute("SELECT source_context_json FROM question_events WHERE id = ?",
                                                (answer["eventId"],)).fetchone()[0] or "{}")
        context["withheld"] = {"reason": "worked_help", "leaks": ["final_answer"], "take_levels": [4, 5]}
        connection.execute("UPDATE question_events SET answer_md = ?, source_context_json = ? WHERE id = ?",
                           (secret, json.dumps(context), answer["eventId"]))
        connection.commit()
    for resolution in (None, "open"):
        queue = _call(ctx, "list_question_queue", {"resolution": resolution})
        assert secret not in json.dumps(queue, ensure_ascii=False)
        rows = [row for row in queue["questions"] if row["id"] == answer["eventId"]]
        assert rows and rows[0]["answerMd"] == WITHHELD_ANSWER_MD


# -- Migration 223 (221 on the branch): the opening's own column ----------------------------------

def test_223_adds_only_the_earlier_opening_column(tmp_path):
    # Numbered 221 on reader/ca2-one-ask; the batch landing renumbered it 223
    # after main's 221 (LP claim fixes) and 222 (curriculum C0a). Reader
    # RW5d P1's 224 follows on the way to head.

    from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations
    from learnloop.db.migrate import upgrade_allowance
    from tests.figure_requests_migration_helpers import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
    from tests.session_ownership_migration_helpers import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES
    from tests.learner_note_source_kind_migration_helpers import C5_ALTERED_TABLES
    from tests.learner_gap_unlinked_migration_helpers import UNLINKED_ALTERED_TABLES
    from tests.help_assist_work_md_migration_helpers import DR2_ALTERED_TABLES
    from tests.help_assist_figures_migration_helpers import P3_ADDED_OBJECTS, P3_ALTERED_TABLES
    from tests.reader_session_digests_migration_helpers import RW6B_ADDED_OBJECTS

    through = tmp_path / "through_222"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 222:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)

    def schema() -> dict[str, str]:
        with closing(sqlite3.connect(database)) as connection:
            return {name: sql or "" for name, sql in connection.execute("SELECT name, sql FROM sqlite_master")}

    before = schema()
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("INSERT INTO workbench_sessions(id, stem_md, origin, entry, practice_item_id, "
                           "created_at, updated_at) VALUES ('wb_old', 'x', 'practice', 'practice_screen', 'pi', "
                           "'2026-10-01T00:00:00Z', '2026-10-01T00:00:00Z')")
        connection.commit()
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == list(range(223, migration_head() + 1))
    after = schema()
    assert set(after) - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS - RW6B_ADDED_OBJECTS - C0B_ADDED_OBJECTS - C2_ADDED_OBJECTS - P3_ADDED_OBJECTS - TE1_ADDED_OBJECTS - P5_ADDED_OBJECTS - RW5C_ADDED_OBJECTS - M2A_ADDED_OBJECTS - DATA_CAPTURE_ADDED_OBJECTS - FOLLOWUP_ADDED_OBJECTS - MARKS_ADDED_OBJECTS - RO0_ADDED_OBJECTS - RO2_ADDED_OBJECTS - RO4_ADDED_OBJECTS - TE2LOG_ADDED_OBJECTS - IH3_ADDED_OBJECTS - B1_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == (
        CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES | SUPERSEDED_ALTERED_TABLES | PR4_ALTERED_TABLES | DR2_ALTERED_TABLES | C5_ALTERED_TABLES | P3_ALTERED_TABLES | UNLINKED_ALTERED_TABLES | (TE1_ALTERED_TABLES | (B1_ALTERED_TABLES | K35_ALTERED_TABLES) | RO1_ALTERED_TABLES | TE3A_ALTERED_TABLES)
    )
    with closing(sqlite3.connect(database)) as connection:
        # A problem from before 223 reads as no opening carried.
        assert connection.execute("SELECT earlier_opened_at FROM workbench_sessions").fetchone() == (None,)
    head = MIGRATION_HEAD_FIXTURE / "state.sqlite"
    assert 223 in applied_versions(head)
    assert head.read_bytes()[18:20] == b"\x01\x01"
    with closing(sqlite3.connect(f"file:{head}?mode=ro", uri=True)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(workbench_sessions)")}
    assert "earlier_opened_at" in columns


def test_f16_the_session_view_reads_the_problems_own_opening_by_default(tmp_path, grader):
    from learnloop.reader import workbench as WB
    from learnloop.db.repositories import Repository

    paths, ctx, session = _steps_sidecar(tmp_path)
    _draft(ctx, session, CDF_ITEM, "kA", earlierOpened=True)
    view = _open(ctx, session)
    plain = WB.session_view(Repository(paths.sqlite_path), view["sessionId"])
    assert plain["earlier_opened"] is True and plain["record"]["earlier_hints"] == 1
