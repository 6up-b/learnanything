from contextlib import closing
import sqlite3

import pytest

from learnloop.db.connection import connect
from learnloop.db.migrate import apply_migrations
from learnloop.db.stores.judgments import append_judgment


@pytest.fixture
def connection(tmp_path):
    path = tmp_path / "state.sqlite"
    apply_migrations(path)
    with closing(connect(path)) as connection:
        yield connection


def judgment(**changes):
    return dict(task="same_target", left_kind="item", left_id="a", right_kind="item",
                right_id="b", judge="llm", judge_model="fake", prompt_version="v1",
                input_hash="h", verdict="same") | changes


def test_append_and_validated_supersession(connection):
    first = append_judgment(connection, **judgment())
    second = append_judgment(connection, **judgment(
        judge="owner", verdict="different", input_hash="new", supersedes_id=first))
    assert first != second
    assert connection.execute("SELECT count(*) FROM judgment_ledger").fetchone()[0] == 2
    for change in ({"left_id": "c"}, {"task": "isomorph"}, {"right_id": "c"},
                   {"right_kind": None, "right_id": None}, {"supersedes_id": "missing"}):
        with pytest.raises(sqlite3.IntegrityError, match="same question"):
            append_judgment(connection, **judgment(supersedes_id=first) | change)


@pytest.mark.parametrize("sql", [
    "UPDATE judgment_ledger SET verdict='different'",
    "DELETE FROM judgment_ledger",
    "INSERT OR REPLACE INTO judgment_ledger SELECT * FROM judgment_ledger",
])
def test_database_protects_history(connection, sql):
    append_judgment(connection, **judgment())
    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        connection.execute(sql)
    assert connection.execute("SELECT verdict FROM judgment_ledger").fetchone()[0] == "same"


def test_unary_verdict_and_validation(connection):
    append_judgment(connection, **judgment(right_kind=None, right_id=None))
    with pytest.raises(sqlite3.IntegrityError):
        append_judgment(connection, **judgment(right_kind=None))
    with pytest.raises(sqlite3.IntegrityError):
        append_judgment(connection, **judgment(judge="unknown"))
    with pytest.raises(ValueError, match="finite"):
        append_judgment(connection, **judgment(score=float("nan")))


@pytest.mark.parametrize("judge", ["llm", "diagnoser"])
@pytest.mark.parametrize("field", ["judge_model", "prompt_version"])
@pytest.mark.parametrize("missing", [None, ""])
def test_model_judges_require_provenance_in_api_and_sql(connection, judge, field, missing):
    values = judgment(judge=judge) | {field: missing}
    with pytest.raises(ValueError, match="nonempty judge_model and prompt_version"):
        append_judgment(connection, **values)
    columns = ["id", "created_at", "rationale", *values]
    parameters = ["invalid", "2026-01-01", "", *values.values()]
    with pytest.raises(sqlite3.IntegrityError, match="nonempty judge_model and prompt_version"):
        connection.execute(
            f"INSERT INTO judgment_ledger ({','.join(columns)}) "
            f"VALUES ({','.join('?' for _ in columns)})", parameters,
        )
    assert connection.execute("SELECT count(*) FROM judgment_ledger").fetchone()[0] == 0


@pytest.mark.parametrize("judge", ["llm", "diagnoser"])
def test_model_judges_accept_complete_provenance(connection, judge):
    append_judgment(connection, **judgment(judge=judge))
    assert tuple(connection.execute(
        "SELECT judge, judge_model, prompt_version FROM judgment_ledger"
    ).fetchone()) == (judge, "fake", "v1")


@pytest.mark.parametrize("judge", ["owner", "verifier", "exact_key", "learner_card"])
def test_other_judges_keep_optional_provenance(connection, judge):
    append_judgment(connection, **judgment(judge=judge, judge_model=None, prompt_version=None))
    assert connection.execute("SELECT count(*) FROM judgment_ledger").fetchone()[0] == 1
