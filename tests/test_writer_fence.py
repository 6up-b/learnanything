"""The writer fence (``learnloop.db.writer_fence``, migration 275; refactor bug ledger L42-R2): a tag-dependent write
commits only under the tag the vault's database is at.

The scenarios are the re-review's (``docs/reviews/refactor-writer-fence.md``): a binary that predates the fence keeps
grading (and regrading) after the activation of ``mvp-0.72`` it does not know; a writer of this code that loaded the
vault before the upgrade keeps writing under the predecessor's tag; a process dies between the database's activation
and the config's publication, or after the publication and before the commit; and, in the durability lane, a WAL
reader whose snapshot predates the activation tries to write after it. A "predecessor binary" here is a connection
that registers none of the fence's functions, which is exactly how code from before the fence (``a17cba6132``) or any
other SQLite client meets the database. Fakes only; no model call.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
import subprocess
import sys
from contextlib import closing, contextmanager
from datetime import timedelta

import pytest

from learnloop import activation_journal
from learnloop.algorithm_versions import LESSON_WEIGHT_CURVES_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db import writer_fence
from learnloop.db.connection import connect, reused_connections
from learnloop.db.repositories import Repository
from learnloop.ops import upgrades
from learnloop.ops.upgrades import UPGRADES, upgrade
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault
from learnloop.vault.repository import open_vault_repository

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

# Every connection here opens for real: a kept connection would carry the functions of an earlier open.
pytestmark = pytest.mark.fresh_connections

#: The re-review's link: mvp-0.71 (the label retired) to mvp-0.72 (the grade curves).
CURVES = next(link for link in UPGRADES if link.tag == LESSON_WEIGHT_CURVES_ALGORITHM_VERSION)
PREDECESSOR, TARGET = CURVES.predecessor, CURVES.tag
#: The link before it, so a vault can be fenced (one fence-aware activation behind it) before the curves' upgrade.
BEFORE = next(link for link in UPGRADES if link.tag == PREDECESSOR)
ITEM_ID = "pi_svd_define_001"


@pytest.fixture(autouse=True)
def _cli_process():
    """This process as the CLI is: the table's completion is installed (and removed after)."""

    previous = activation_journal._COMPLETER
    activation_journal.install_completer(upgrades.complete_interrupted_activation)
    yield
    activation_journal.install_completer(previous)


def _grade(vault, repository, *, minutes: int, answer: str = "SVD factors a matrix as U Sigma V transpose."):
    return complete_self_graded_attempt(
        vault, repository, AttemptDraft(ITEM_ID, answer, attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


def _vault_at(tmp_path, tag, name="vault"):
    """The small vault at ``tag`` with two graded answers (``tests/test_upgrades.py``'s)."""

    paths = create_basic_vault(tmp_path / name)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    _grade(vault, repository, minutes=0, answer="I do not know")
    _grade(vault, repository, minutes=1)
    return paths


def _count(paths, table: str) -> int:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _recorded(paths) -> str | None:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return writer_fence.recorded_tag(connection)


def _surprise_without_curve(paths) -> int:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM attempt_surprise AS s WHERE NOT EXISTS "
            "(SELECT 1 FROM attempt_grade_curves AS c WHERE c.attempt_id = s.attempt_id)"
        ).fetchone()[0]


def _copy_last_row(connection, table: str, key: str, value: str) -> None:
    """Insert a copy of ``table``'s newest row under a new ``key``: the shape of the write an older binary makes."""

    columns = [row[1] for row in connection.execute(f"PRAGMA table_info({table})")]
    selected = ", ".join("?" if column == key else column for column in columns)
    connection.execute(
        f"INSERT INTO {table}({', '.join(columns)}) SELECT {selected} FROM {table} ORDER BY rowid DESC LIMIT 1",
        (value,),
    )


@contextmanager
def predecessor_binary():
    """Connections opened inside are what code from before the fence opens: no fence function on them."""

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(writer_fence, "register", lambda connection, sqlite_path, tags: frozenset())
        # Nor the fence's own exception: an older binary meets the trigger's IntegrityError as it is.
        patch.setattr(writer_fence, "raise_refusal", lambda cursor, error: None)
        yield


def _refused(error: BaseException) -> bool:
    return writer_fence.is_refusal(error)


# -- the schema ------------------------------------------------------------------------------------------------------


def test_every_fenced_write_has_its_trigger_at_the_head(tmp_path):
    paths = create_basic_vault(tmp_path / "vault", fresh=True)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        found = set()
        for name, sql in connection.execute(
            "SELECT tbl_name, sql FROM sqlite_master WHERE type = 'trigger' AND name GLOB 'writer_fence_*'"
        ):
            if name == "writer_fence":
                continue
            assert writer_fence.REFUSAL in sql
            event = "INSERT" if " BEFORE INSERT ON " in sql else "UPDATE" if " BEFORE UPDATE ON " in sql else None
            found.add((name, event))
        assert found == set(writer_fence.GUARDED)
        # No row until a fence-aware activation: nothing is fenced, the config is the tag.
        assert writer_fence.recorded_tag(connection) is None


# -- a binary from before the fence ----------------------------------------------------------------------------------


def test_a_predecessor_binary_cannot_grade_or_regrade_after_the_activation(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    # The older process loaded the vault at the predecessor and grades as it always did, before the upgrade.
    old_vault = load_vault(paths.root)
    old_repository = Repository(paths.sqlite_path)
    with predecessor_binary():
        _grade(old_vault, old_repository, minutes=2)
    graded = _count(paths, "practice_attempts")

    assert upgrade(paths.root, to=TARGET).upgraded  # another process: the CLI
    assert _recorded(paths) == TARGET and _surprise_without_curve(paths) == 0
    before = {table: _count(paths, table) for table in (
        "practice_attempts", "grading_evidence", "attempt_surprise", "attempt_grade_curves")}
    assert before["practice_attempts"] == graded

    # Its next grade: refused at the database, nothing written (no surprise row without its curve).
    with predecessor_binary(), pytest.raises(sqlite3.IntegrityError) as refused:
        _grade(old_vault, old_repository, minutes=3)
    assert _refused(refused.value)
    # Its regrade's first write (new evidence for an answer) and a later write to a grade's surprise row.
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        with pytest.raises(sqlite3.IntegrityError) as regrade:
            _copy_last_row(connection, "grading_evidence", "id", "ge_old_binary_regrade")
        assert _refused(regrade.value)
        with pytest.raises(sqlite3.IntegrityError) as actions:
            connection.execute("UPDATE attempt_surprise SET triggered_actions_json = '[]'")
        assert _refused(actions.value)
        connection.rollback()
    assert {table: _count(paths, table) for table in before} == before
    assert _surprise_without_curve(paths) == 0


def test_after_a_fenced_activation_a_predecessor_binary_is_refused_whatever_tag_it_knows(tmp_path):
    """An older binary cannot say which tag it writes under, so it is refused at the vault's own tag too, and so is
    its own upgrade (its rebuild's receipt among its writes): the database's tag never falls behind the config."""

    paths = _vault_at(tmp_path, BEFORE.predecessor)
    assert upgrade(paths.root, to=PREDECESSOR).upgraded  # the first fence-aware activation writes the row
    assert _recorded(paths) == PREDECESSOR
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        for tag in (PREDECESSOR, TARGET):
            with pytest.raises(sqlite3.IntegrityError) as refused:
                connection.execute(
                    "INSERT INTO derived_state_rebuilds(id, scope, learning_object_ids_json, algorithm_version, "
                    "rebuilt_learning_objects, replayed_attempts, created_at) "
                    "VALUES (?, 'test', '[]', ?, 0, 0, '2026-05-16T12:00:00Z')", (f"dsr_old_{tag}", tag))
            assert _refused(refused.value)


def test_a_fenced_writer_bound_to_no_tag_is_not_refused(tmp_path):
    """A process that never loaded the vault computed nothing from its config (a scratch copy, a seeded row)."""

    paths = _vault_at(tmp_path, PREDECESSOR)
    assert upgrade(paths.root, to=TARGET).upgraded
    with writer_fence.writing_under(paths.sqlite_path):
        with closing(connect(paths.sqlite_path)) as connection:
            for table, _event in writer_fence.GUARDED:
                with pytest.raises(sqlite3.IntegrityError) as schema:
                    connection.execute(f"INSERT INTO {table} DEFAULT VALUES")
                assert not _refused(schema.value)  # past the fence, the row meets the table's own constraints


def test_a_vault_no_fence_aware_activation_touched_is_not_fenced(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    assert _recorded(paths) is None
    with predecessor_binary():  # an older binary writes as before
        _grade(load_vault(paths.root), Repository(paths.sqlite_path), minutes=2)
    assert _count(paths, "practice_attempts") == 3


# -- a writer of this code with a stale config -----------------------------------------------------------------------


def test_a_stale_writer_of_this_code_is_refused_and_proceeds_after_a_reload(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    stale = load_vault(paths.root)  # this process loaded the predecessor
    repository = Repository(paths.sqlite_path)
    # The upgrade runs in another process, as `learnloop upgrade` does beside an open desktop.
    upgraded = subprocess.run(
        [sys.executable, "-c",
         "import sys; from learnloop.ops.upgrades import upgrade; "
         "sys.exit(0 if upgrade(sys.argv[1], to=sys.argv[2]).upgraded else 3)",
         str(paths.root), TARGET],
        env=dict(os.environ), capture_output=True, text=True, timeout=300,
    )
    assert upgraded.returncode == 0, upgraded.stderr
    assert writer_fence.binding(paths.sqlite_path) == {PREDECESSOR}
    attempts = _count(paths, "practice_attempts")

    with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
        _grade(stale, repository, minutes=2)
    assert _refused(refused.value) and writer_fence.is_refusal(refused.value)
    assert _count(paths, "practice_attempts") == attempts and _surprise_without_curve(paths) == 0

    fresh = load_vault(paths.root)  # the reload: the process now writes under the vault's tag
    assert fresh.config.algorithms.algorithm_version == TARGET
    # The repository opened for the stale vault stays bound to it (WF-R1): the reload opens the vault's repository again.
    result = _grade(fresh, Repository(paths.sqlite_path), minutes=2)
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        curve = connection.execute(
            "SELECT algorithm_version, provenance FROM attempt_grade_curves WHERE attempt_id = ?", (result.attempt_id,)
        ).fetchone()
    assert curve == (TARGET, "graded")


# A fenced pair with a condition (a Reader section's first completion) has its own test in test_writer_fence_scopes.py.
@pytest.mark.parametrize(("table", "event"), [pair for pair in writer_fence.GUARDED if pair not in writer_fence.GUARD_CONDITIONS],
                         ids=lambda value: str(value))
def test_every_fenced_write_refuses_a_writer_bound_to_another_tag(tmp_path, table, event):
    paths = _vault_at(tmp_path, PREDECESSOR)
    assert upgrade(paths.root, to=TARGET).upgraded
    statement = f"INSERT INTO {table} DEFAULT VALUES" if event == "INSERT" else (
        f"UPDATE {table} SET rowid = rowid WHERE rowid = (SELECT MIN(rowid) FROM {table})")
    if event == "UPDATE":
        assert _count(paths, table) > 0
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        with closing(connect(paths.sqlite_path)) as connection:
            with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
                connection.execute(statement)
            assert _refused(refused.value)
    with writer_fence.writing_under(paths.sqlite_path, TARGET):
        with closing(connect(paths.sqlite_path)) as connection:
            try:
                connection.execute(statement)  # past the fence: an update applies, an empty insert meets the schema
            except sqlite3.IntegrityError as error:
                assert not _refused(error)
            connection.rollback()


def test_a_pool_never_hands_a_connection_to_another_binding(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    assert upgrade(paths.root, to=TARGET).upgraded
    with reused_connections():
        with writer_fence.writing_under(paths.sqlite_path, TARGET):
            current = connect(paths.sqlite_path)
            current.execute("SELECT 1").fetchone()
            current.close()
        with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
            stale = connect(paths.sqlite_path)
            with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
                stale.execute("INSERT INTO lesson_checks DEFAULT VALUES")
            assert _refused(refused.value)
            stale.close()


# -- deaths around the activation ------------------------------------------------------------------------------------


def _die(root, tag, before_publication):
    real = upgrades.publish_algorithm_version

    def publish_then_die(*args, **kwargs):
        if not before_publication:
            real(*args, **kwargs)
        os._exit(17)  # no handler runs: the transaction never commits

    upgrades.publish_algorithm_version = publish_then_die
    upgrade(root, to=tag)


def _crash(paths, tag, *, before_publication):
    process = multiprocessing.get_context("fork").Process(target=_die, args=(paths.root, tag, before_publication))
    process.start()
    process.join(120)
    assert process.exitcode == 17


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
def test_a_death_between_the_activation_and_the_publication_leaves_the_predecessor_in_force(tmp_path):
    paths = _vault_at(tmp_path, BEFORE.predecessor)
    assert upgrade(paths.root, to=PREDECESSOR).upgraded  # fenced at the predecessor
    _crash(paths, TARGET, before_publication=True)  # the database's tag moved inside the transaction; it never committed
    assert _recorded(paths) == PREDECESSOR
    assert load_vault(paths.root).config.algorithms.algorithm_version == PREDECESSOR
    # The predecessor's writers go on (they are the vault's tag); nothing of the successor's may write.
    repository = open_vault_repository(paths.root, paths.sqlite_path)
    _grade(load_vault(paths.root), repository, minutes=2)
    with writer_fence.writing_under(paths.sqlite_path, TARGET):
        with closing(connect(paths.sqlite_path)) as connection:
            with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
                connection.execute("INSERT INTO lesson_checks DEFAULT VALUES")
            assert _refused(refused.value)


@pytest.mark.filterwarnings("ignore:This process .* is multi-threaded:DeprecationWarning")
def test_a_death_after_the_publication_keeps_the_database_tag_until_the_completion(tmp_path):
    paths = _vault_at(tmp_path, BEFORE.predecessor)
    assert upgrade(paths.root, to=PREDECESSOR).upgraded
    stale = load_vault(paths.root)
    _crash(paths, TARGET, before_publication=False)
    # The config names the successor over the predecessor's database: the database's row is the truth.
    assert activation_journal.pending(paths.sqlite_path)
    assert upgrades.published_algorithm_version(paths.root / "learnloop.toml") == TARGET
    assert _recorded(paths) == PREDECESSOR
    # A writer of the successor would put successor rows into the predecessor's database: refused.
    with writer_fence.writing_under(paths.sqlite_path, TARGET):
        with closing(connect(paths.sqlite_path)) as connection:
            with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
                connection.execute("INSERT INTO lesson_checks DEFAULT VALUES")
            assert _refused(refused.value)
    # A predecessor's write in the window is predecessor history, and the completion freezes its curve with the rest.
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR), activation_journal.completing_activation():
        result = _grade(stale, Repository(paths.sqlite_path), minutes=2)
    open_vault_repository(paths.root, paths.sqlite_path)  # the next opener completes the activation
    assert not activation_journal.pending(paths.sqlite_path) and _recorded(paths) == TARGET
    with closing(sqlite3.connect(paths.sqlite_path)) as connection:
        curve = connection.execute(
            "SELECT algorithm_version FROM attempt_grade_curves WHERE attempt_id = ?", (result.attempt_id,)
        ).fetchone()
    assert curve == (PREDECESSOR,)
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
            _grade(stale, Repository(paths.sqlite_path), minutes=3)
    assert _refused(refused.value)


# -- the durability lane: WAL ----------------------------------------------------------------------------------------


@pytest.mark.durability
def test_a_wal_reader_from_before_the_activation_cannot_commit_after_it(tmp_path):
    paths = _vault_at(tmp_path, PREDECESSOR)
    with closing(sqlite3.connect(paths.sqlite_path)) as probe:
        assert probe.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    attempts = _count(paths, "practice_attempts")
    with writer_fence.writing_under(paths.sqlite_path, PREDECESSOR):
        snapshot = connect(paths.sqlite_path)  # a stale writer, its read snapshot taken before the activation
        lock_first = connect(paths.sqlite_path)  # a stale writer that takes the write lock after it
    try:
        snapshot.execute("BEGIN")
        assert snapshot.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()[0] == attempts
        assert upgrade(paths.root, to=TARGET).upgraded  # WAL: the open snapshot does not hold the commit back
        with pytest.raises(sqlite3.DatabaseError) as stale_snapshot:
            _copy_last_row(snapshot, "practice_attempts", "id", "pa_stale_snapshot")
        # Either SQLite refuses the snapshot's upgrade to a writer, or the trigger refuses the stale binding.
        assert "locked" in str(stale_snapshot.value) or _refused(stale_snapshot.value)
        snapshot.rollback()
        lock_first.execute("BEGIN IMMEDIATE")
        with pytest.raises(writer_fence.WriterFenceRefusal) as refused:
            _copy_last_row(lock_first, "practice_attempts", "id", "pa_stale_writer")
        assert _refused(refused.value)
        lock_first.rollback()
    finally:
        snapshot.close()
        lock_first.close()
    assert _count(paths, "practice_attempts") == attempts and _recorded(paths) == TARGET


#: Every link from the first the fence's re-review named through the head: 0.72 (the curves) to the newest tag.
CHAIN_FROM_CURVES = UPGRADES[UPGRADES.index(CURVES):]


@pytest.mark.parametrize("link", CHAIN_FROM_CURVES, ids=lambda link: link.tag)
def test_every_link_from_the_curves_moves_the_fence_and_a_reloaded_grade_writes_under_it(tmp_path, link):
    """Each activation through the head (0.74 and 0.75 among them) runs inside the fence's binding: the row moves to
    the link's tag, a writer without the fence is refused at either tag, and a grade by this code after the reload
    (its grade receipt, its surprise and the rest) writes on a connection bound to the new tag."""

    paths = _vault_at(tmp_path, link.predecessor)
    assert upgrade(paths.root, to=link.tag).upgraded
    assert _recorded(paths) == link.tag
    with predecessor_binary(), closing(sqlite3.connect(paths.sqlite_path)) as connection:
        for tag in (link.predecessor, link.tag):
            with pytest.raises(sqlite3.IntegrityError) as refused:
                connection.execute(
                    "INSERT INTO derived_state_rebuilds(id, scope, learning_object_ids_json, algorithm_version, "
                    "rebuilt_learning_objects, replayed_attempts, created_at) "
                    "VALUES (?, 'test', '[]', ?, 0, 0, '2026-05-16T12:00:00Z')", (f"dsr_old_{tag}", tag))
            assert _refused(refused.value)
    before = _count(paths, "attempt_surprise")
    vault = load_vault(paths.root)
    _grade(vault, Repository(paths.sqlite_path), minutes=30)
    assert _count(paths, "attempt_surprise") == before + 1
