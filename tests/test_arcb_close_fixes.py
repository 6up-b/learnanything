"""Arc B close, the fix round: the end-of-arc review's findings on the decision records (ADR-017), each staged.

What each group pins (each test failed before its fix):

* a record written through a repository whose connection the caller holds (a pin) joins the caller's transaction
  and never commits it;
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learnloop import provenance, refusal_records
from learnloop.db.connection import connect
from learnloop.db.copies import copy_tree_with_databases
from learnloop.db.repositories import Repository
from learnloop.provenance import DecisionRecord
from tests.helpers import MIGRATION_HEAD_FIXTURE


@pytest.fixture()
def head_db(tmp_path: Path) -> Path:
    root = tmp_path / "head"
    copy_tree_with_databases(MIGRATION_HEAD_FIXTURE, root, database_names=("state.sqlite",))
    return root / "state.sqlite"


def _count(path: Path, sql: str) -> int:
    with connect(path, read_only=True) as connection:
        return int(connection.execute(sql).fetchone()[0])


# -- 2. a borrowed connection's transaction is the caller's ------------------------------------------------------


@pytest.mark.parametrize("writer", ["store", "refusal_records"])
def test_a_record_written_under_a_pin_never_commits_the_callers_work(head_db: Path, writer: str):
    from learnloop.db.stores.provenance import write_decision

    repository = Repository.attach(head_db)
    with repository.connection() as connection:
        connection.execute("CREATE TABLE callers_work (x)")
    record = DecisionRecord(kind="slate", status="chosen", id="REC_PINNED")

    def write() -> str | None:
        if writer == "store":
            return write_decision(repository, record)
        return refusal_records.write(repository, "slate", lambda: record)

    with pytest.raises(RuntimeError, match="caller failed"), repository.pinned():
        with repository.connection() as connection:
            connection.execute("INSERT INTO callers_work VALUES (1)")
            assert write() == "REC_PINNED"
            raise RuntimeError("caller failed")
    # The record joined the caller's transaction, so both went with its rollback.
    assert _count(head_db, "SELECT COUNT(*) FROM callers_work") == 0
    assert _count(head_db, "SELECT COUNT(*) FROM decision_records WHERE id = 'REC_PINNED'") == 0


def test_a_record_under_a_pin_with_nothing_open_commits_alone(head_db: Path):
    from learnloop.db.stores.provenance import write_decision

    repository = Repository.attach(head_db)
    with repository.pinned():
        assert write_decision(repository, DecisionRecord(kind="slate", status="chosen", id="REC_ALONE"))
        with connect(head_db, read_only=True) as other:  # visible to another connection before the pin ends
            assert other.execute("SELECT COUNT(*) FROM decision_records WHERE id = 'REC_ALONE'").fetchone()[0] == 1
