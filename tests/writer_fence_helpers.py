"""What the writer fence's tests share (``tests/test_writer_fence.py``, ``tests/test_writer_fence_scopes.py``): the
small vault at a tag with two graded answers, counts read past every fence, an older binary's connection, and the
refusal predicate (the fence's own exception, or the trigger's text on a connection this code did not open)."""

from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from datetime import timedelta

import pytest

from learnloop import activation_journal
from learnloop.algorithm_versions import LESSON_WEIGHT_CURVES_ALGORITHM_VERSION
from learnloop.attempts.attempts import AttemptDraft, SelfGradeInput, complete_self_graded_attempt
from learnloop.clock import FrozenClock
from learnloop.db import writer_fence
from learnloop.db.repositories import Repository
from learnloop.ops import upgrades
from learnloop.ops.upgrades import UPGRADES
from learnloop.substrate.state_sync import sync_vault_state
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version

#: The re-review's link: mvp-0.71 (the label retired) to mvp-0.72 (the grade curves).
CURVES = next(link for link in UPGRADES if link.tag == LESSON_WEIGHT_CURVES_ALGORITHM_VERSION)
PREDECESSOR, TARGET = CURVES.predecessor, CURVES.tag
#: The link before it, so a vault can be fenced (one fence-aware activation behind it) before the curves' upgrade.
BEFORE = next(link for link in UPGRADES if link.tag == PREDECESSOR)
ITEM_ID = "pi_svd_define_001"


@pytest.fixture
def cli_process():
    """This process as the CLI is: the table's completion is installed (and removed after)."""

    previous = activation_journal._COMPLETER
    activation_journal.install_completer(upgrades.complete_interrupted_activation)
    yield
    activation_journal.install_completer(previous)


def grade(vault, repository, *, minutes: int, answer: str = "SVD factors a matrix as U Sigma V transpose."):
    return complete_self_graded_attempt(
        vault, repository, AttemptDraft(ITEM_ID, answer, attempt_type="independent_attempt"),
        SelfGradeInput(criterion_points={"correctness": 4}, confidence=5),
        clock=FrozenClock(NOW + timedelta(minutes=minutes)),
    )


def vault_at(tmp_path, tag, name="vault"):
    """The small vault at ``tag`` with two graded answers (``tests/test_upgrades.py``'s)."""

    paths = create_basic_vault(tmp_path / name)
    set_algorithm_version(paths, tag)
    vault = load_vault(paths.root)
    repository = Repository(paths.sqlite_path)
    sync_vault_state(vault, repository, clock=FrozenClock(NOW))
    grade(vault, repository, minutes=0, answer="I do not know")
    grade(vault, repository, minutes=1)
    return paths


def count(paths, table: str) -> int:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def recorded(paths) -> str | None:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return writer_fence.recorded_tag(connection)


def surprise_without_curve(paths) -> int:
    with closing(sqlite3.connect(f"file:{paths.sqlite_path}?mode=ro", uri=True)) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM attempt_surprise AS s WHERE NOT EXISTS "
            "(SELECT 1 FROM attempt_grade_curves AS c WHERE c.attempt_id = s.attempt_id)"
        ).fetchone()[0]


def copy_last_row(connection, table: str, key: str, value: str) -> None:
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


def refused(error: BaseException) -> bool:
    """The fence refused the write: its own exception on a connection this code opened, the trigger's text on any
    other (an older binary's, a plain sqlite3 one)."""

    return writer_fence.is_refusal(error)
