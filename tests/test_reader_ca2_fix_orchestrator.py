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
from tests.hint_fakes import ITEM as CDF_ITEM, WORK
from tests.test_hint_h2b_review import grader  # noqa: F401 - the blind grader fixture
from tests.test_reader_ca2_codex_rereview import _attempt, _draft, _steps_sidecar
from tests.test_reader_ca2_codex_review import (  # noqa: F401 - the sidecar fixture
    ITEM,
    FakeTutor,
    _call,
    sidecar,
)
from tests.workbench_help_fakes import STEP_1
from tests.test_learner_claim_superseded_migration import SUPERSEDED_ALTERED_TABLES


def _row(paths, workbench_id: str) -> dict:
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        connection.row_factory = sqlite3.Row
        return dict(connection.execute("SELECT * FROM workbench_sessions WHERE id = ?", (workbench_id,)).fetchone())


def _open(ctx, session: str, *, carried: int = 0, resume: str | None = None) -> dict:
    params = {"origin": "practice", "entry": "practice_screen", "carriedHints": carried, "practiceSessionId": session}
    if resume:
        params["sessionId"] = resume
    else:
        params.update({"practiceItemId": CDF_ITEM, "stemMd": "Find P(X <= 1/2)."})
    return _call(ctx, "workbench.open", params)["session"]


def _step(ctx, workbench_id: str, key: str = "s0") -> None:
    _call(ctx, "workbench.save_step", {"sessionId": workbench_id, "clientIdempotencyKey": key, "op": "add",
                                       "bodyMd": STEP_1})


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

#: The table 223 alters: the earlier migrations' "nothing else changed" diffs on the way to head read it.
CA2_ALTERED_TABLES = frozenset({"workbench_sessions"})


def test_223_adds_only_the_earlier_opening_column(tmp_path):
    # Numbered 221 on reader/ca2-one-ask; the batch landing renumbered it 223
    # after main's 221 (LP claim fixes) and 222 (curriculum C0a). Reader
    # RW5d P1's 224 follows on the way to head.
    from pathlib import Path

    from learnloop.db.migrate import UPGRADE_TEST_HELPER, applied_versions, apply_migrations, discover_migrations
    from learnloop.db.migrate import upgrade_allowance
    from tests.test_figure_requests_migration import RW5D_ADDED_OBJECTS, RW5D_ALTERED_TABLES
    from tests.test_session_ownership_migration import PR4_ADDED_OBJECTS, PR4_ALTERED_TABLES

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
        assert [migration.version for migration in apply_migrations(database)] == [223, 224, 225, 226]
    after = schema()
    assert set(after) - RW5D_ADDED_OBJECTS - PR4_ADDED_OBJECTS == set(before)
    assert {name for name in before if before[name] != after[name]} == (
        CA2_ALTERED_TABLES | RW5D_ALTERED_TABLES | SUPERSEDED_ALTERED_TABLES | PR4_ALTERED_TABLES
    )
    with closing(sqlite3.connect(database)) as connection:
        # A problem from before 223 reads as no opening carried.
        assert connection.execute("SELECT earlier_opened_at FROM workbench_sessions").fetchone() == (None,)
    head = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_226" / "state.sqlite"
    assert max(applied_versions(head)) == max(m.version for m in discover_migrations()) == 226
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
