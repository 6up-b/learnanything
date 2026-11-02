"""Learner data-relax 2: migration 230 keeps the learner's draft on a help_assists row.

``help_assists`` (RAW_LEDGER, migration 210) gains one nullable column,
``work_md``: the learner's draft when the help was asked for, bounded by its
writer (``db.stores.help_assists.WORK_MD_CHARS``). Every earlier row keeps its
values (``work_md`` NULL); the append-only and fixed-identity triggers are
unchanged. No new table, so no role or replayer; ``help_assists`` is not an
AD-readable table (``protected_tables``), so no column class. The practice
screen's writers store the draft (an authored reveal, a served hint, a
discriminating answer's question's draft); the grader still never sees it.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from learnloop.adaptive_difficulty import protected_tables as PT
from learnloop.db.migrate import applied_versions, discover_migrations
from learnloop.db.stores import help_assists as store
from learnloop.db.table_roles import TableRole, role_for_table
from tests.test_learner_note_source_kind_migration import C5_ALTERED_TABLES
from tests.test_learner_gap_unlinked_migration import UNLINKED_ALTERED_TABLES
from tests.test_learner_notes_vault_origin_migration import C2B_ALTERED_TABLES
from tests.test_teacher_te1_migration import TE1_ADDED_OBJECTS, TE1_ALTERED_TABLES

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"
HEAD = Path(__file__).resolve().parents[1] / "fixtures" / "migration_head_236" / "state.sqlite"
#: The table 230 alters (it adds no object): the earlier migrations' "nothing
#: else changed" diffs on the way to head read this.
DR2_ALTERED_TABLES = frozenset({"help_assists"})
DR2_ADDED_OBJECTS: frozenset[str] = frozenset()


def _later():
    # RW5d P3's migration 232 and teacher TE1's 234 also apply on the way to head (C2b's 233 is composed below).
    from tests.test_help_assist_figures_migration import P3_ADDED_OBJECTS, P3_ALTERED_TABLES

    from tests.test_figure_prefetch_migration import P5_ADDED_OBJECTS

    # _schema reads objects with SQL only: TE1's (and RW5d P5's 236's) autoindexes are not among them.
    te1_added = {name for name in TE1_ADDED_OBJECTS | P5_ADDED_OBJECTS if not name.startswith("sqlite_autoindex")}
    return P3_ADDED_OBJECTS | te1_added, P3_ALTERED_TABLES | TE1_ALTERED_TABLES


def test_230_is_the_work_md_migration_and_help_assists_stays_a_raw_ledger():
    names = {migration.version: migration.path.name for migration in discover_migrations()}
    assert names[230] == "230_help_assist_work_md.sql"
    assert names[229] == "229_learner_notes.sql"
    assert role_for_table("help_assists") == TableRole.RAW_LEDGER
    # Not a table an AD operation reads (so no column class is needed).
    assert "help_assists" not in PT.ROLES


def _at_229(tmp_path: Path) -> Path:
    from learnloop.db.migrate import apply_migrations

    through = tmp_path / "through_229"
    through.mkdir()
    for migration in discover_migrations():
        if migration.version <= 229:
            (through / migration.path.name).write_text(migration.path.read_text(encoding="utf-8"), encoding="utf-8")
    database = tmp_path / "state.sqlite"
    apply_migrations(database, migrations_dir=through)
    assert max(applied_versions(database)) == 229
    return database


def _schema(database: Path) -> dict[str, str]:
    with closing(sqlite3.connect(database)) as connection:
        return {name: sql for name, sql in connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL")}


def test_230_adds_only_the_nullable_column_and_keeps_every_row(tmp_path):
    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance

    database = _at_229(tmp_path)
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "INSERT INTO help_assists (id, surface, assist_kind, chooser, shown, requested_at, work_hash, work_chars) "
            "VALUES ('ha_old', 'practice', 'hint', 'none', 1, '2026-10-01T00:00:00Z', 'h', 12)")
        connection.commit()
        before_row = connection.execute("SELECT * FROM help_assists").fetchone()
    before = _schema(database)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        # Curriculum C5's 231 (the two gap tables' source kinds), RW5d P3's 232, curriculum C2b's
        # 233 (learner_notes' vault origin) and teacher TE1's 234 follow on the way to head.
        # Follow-ups Nov 2's 235 (learner_text_gap_reversals, not read here) follows too.
        assert [migration.version for migration in apply_migrations(database)] == [230, 231, 232, 233, 234, 235, 236]
    after = _schema(database)
    later_added, later_altered = _later()
    assert set(after) - set(before) == set(DR2_ADDED_OBJECTS) | set(later_added)
    assert {name for name in before if before[name] != after.get(name)} == set(DR2_ALTERED_TABLES) | set(C5_ALTERED_TABLES) | set(later_altered) | set(C2B_ALTERED_TABLES) | set(UNLINKED_ALTERED_TABLES)
    with closing(sqlite3.connect(database)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(help_assists)")]
        assert columns[-2] == "work_md" and tuple(columns) == store.COLUMNS
        info = {row[1]: row for row in connection.execute("PRAGMA table_info(help_assists)")}
        assert info["work_md"][2] == "TEXT" and info["work_md"][3] == 0 and info["work_md"][4] is None
        row = connection.execute("SELECT * FROM help_assists").fetchone()
        assert tuple(row)[:-2] == tuple(before_row) and row[-2] is None and row[-1] is None
        # The ledger's triggers are unchanged: still append-only, identity fixed.
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            connection.execute("DELETE FROM help_assists")
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_the_head_fixture_holds_230_in_rollback_mode():
    assert HEAD.read_bytes()[18:20] == b"\x01\x01"
    # The head is 235 (follow-ups Nov 2, rebuilt from TE1's 234 head with only 235 applied); it holds 230,
    # 231, 232 and 233.
    assert {230, 231, 232, 233} <= set(applied_versions(HEAD))
    assert max(applied_versions(HEAD)) == max(m.version for m in discover_migrations()) == 236
    with closing(sqlite3.connect(f"file:{HEAD}?mode=ro", uri=True)) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(help_assists)")]
        assert "work_md" in columns
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert connection.execute("SELECT COUNT(*) FROM help_assists WHERE work_md IS NOT NULL").fetchone()[0] == 0


@pytest.mark.durability
def test_230_on_the_durability_lane(tmp_path):
    from learnloop.db.migrate import UPGRADE_TEST_HELPER, apply_migrations, upgrade_allowance

    database = _at_229(tmp_path)
    with upgrade_allowance(UPGRADE_TEST_HELPER):
        assert [migration.version for migration in apply_migrations(database)] == [230, 231, 232, 233, 234, 235, 236]
    with closing(sqlite3.connect(database)) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        store.insert_assist(connection, {"id": "ha_d", "surface": "practice", "assist_kind": "hint",
                                         "chooser": "none", "shown": 1, "requested_at": "t",
                                         "work_md": store.kept_draft("my draft")})
        connection.commit()
        assert connection.execute("SELECT work_md FROM help_assists").fetchone()[0] == "my draft"


def test_the_kept_draft_is_bounded_and_empty_is_none():
    assert store.kept_draft(None) is None and store.kept_draft("   \n") is None
    assert store.kept_draft("x = 1") == "x = 1"
    long = "a" * (store.WORK_MD_CHARS + 50)
    assert store.kept_draft(long) == "a" * store.WORK_MD_CHARS


# ---------------------------------------------------------------------------
# The writers store the draft
# ---------------------------------------------------------------------------

def test_an_authored_reveal_keeps_the_draft(tmp_path):
    from learnloop.db.repositories import Repository
    from learnloop.hints.telemetry import record_authored_reveal
    from learnloop.vault.loader import load_vault
    from tests.hint_fakes import ITEM, hint_vault

    paths = hint_vault(tmp_path)
    vault = load_vault(paths.root)
    repository = Repository.attach(paths.sqlite_path)
    draft = "F(x) = x^2 so P(X <= 1/2) = 1/4 ZEBRADRAFT"
    record = record_authored_reveal(repository, item=vault.practice_items[ITEM], session_id="s1", submission_id="k1",
                                    authored_index=0, work_md=draft)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        work_md, chars = connection.execute("SELECT work_md, work_chars FROM help_assists WHERE id = ?",
                                            (record.assist_id,)).fetchone()
    assert work_md == draft and chars == len(draft)


def _ctx(paths):
    from learnloop_sidecar.context import SidecarContext

    ctx = SidecarContext()
    ctx.load(paths.root)
    ctx.grading_provider_override = "manual"
    ctx.hints_inline = True
    return ctx


def _call(ctx, name, params):
    import learnloop_sidecar.handlers  # noqa: F401 - registers the RPCs
    from learnloop_sidecar.registry import METHOD_REGISTRY

    spec = METHOD_REGISTRY[name]
    return spec.handler(ctx, spec.params_model.model_validate(params))


def test_a_served_hint_keeps_the_draft_it_answered_and_the_grader_never_sees_it(tmp_path):
    """Record stores the draft; the blind grader's prompt for the submitted
    answer is the one a vault where no hint was served gets (its inputs are
    unchanged), and the draft never reaches it."""

    from learnloop.attempts.blind_grading import blind_grading_context, blind_grading_prompt
    from learnloop.vault.loader import load_vault
    from tests.hint_fakes import ITEM, ChooserFake, WriterFake, assists, good_answer, hint_vault, prefer

    paths = hint_vault(tmp_path, config='[hints]\nchoice_policy = "argmax"\n')
    ctx = _ctx(paths)
    session = _call(ctx, "start_session", {"energy": "medium"})["sessionId"]
    draft = "F(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) + 1 ZEBRADRAFT"
    ctx.hint_writer_client = WriterFake([good_answer])
    ctx.hint_chooser_client = ChooserFake(prefer("next_step@L3", 0.9))
    _call(ctx, "practice.request_hint", {"sessionId": session, "practiceItemId": ITEM, "submissionId": "k1",
                                         "answerMd": draft})
    rows = assists(paths.sqlite_path)
    assert len(rows) == 1 and rows[0]["work_md"] == draft and rows[0]["work_chars"] == len(draft)
    final = "F(x) = x^2 on [0, 1]\nso P(X <= 1/2) = F(1/2) = 1/4"
    result = _call(ctx, "submit_attempt", {
        "sessionId": session, "practiceItemId": ITEM, "answerMd": final, "attemptType": "independent_attempt",
        "hintsUsed": 0, "selfGrade": {"criterionPoints": {"cdf": 2, "value": 2}, "confidence": 3},
        "submissionId": "k1"})
    vault = load_vault(paths.root)
    prompt = blind_grading_prompt(blind_grading_context(vault, vault.practice_items[ITEM],
                                                        attempt_id=result["attemptId"], learner_answer_md=final))
    assert "ZEBRADRAFT" not in prompt
    clean = hint_vault(tmp_path, name="clean")
    clean_vault = load_vault(clean.root)
    assert prompt == blind_grading_prompt(blind_grading_context(
        clean_vault, clean_vault.practice_items[ITEM], attempt_id=result["attemptId"], learner_answer_md=final))
    # The hint report gains a count only: never the draft's words.
    import json

    from learnloop.hints.report import build_hints_report

    report = build_hints_report(paths.sqlite_path)
    kept = [row["drafts_kept"] for row in report["kinds"]]
    assert [(entry["count"], entry["of"]) for entry in kept] == [(1, 1)]
    assert "ZEBRADRAFT" not in json.dumps(report)
