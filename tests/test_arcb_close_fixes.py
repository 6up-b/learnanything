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


# -- 1. a spend refusal stays a refusal while a reader holds a snapshot -------------------------------------------


class _MeteredClient:
    provider_name = "openrouter_decider"
    provider_type = "decider"
    model = "m"

    def __init__(self, usd: float) -> None:
        self.usd = usd
        self.sent = 0

    def estimated_cost(self, input_tokens):
        return self.usd

    def send(self):
        from learnloop.ai.execution import model_call, report_call_usage

        with model_call(self, purpose="router_decision", prompt="x"):
            self.sent += 1
            report_call_usage({"cost": self.usd})


def test_a_refused_router_request_is_refused_at_once_while_a_reader_holds_a_snapshot(tmp_path: Path):
    """Before the fix the guard committed its record before raising, and in rollback-journal mode that commit waited
    out the 5 s busy timeout behind the reader, then raised ``database is locked``: the component reported ``failed``
    (or stayed pending past the router's deadline) instead of ``spend``."""

    import sqlite3
    import time

    from learnloop.daily_plan.router_runtime import RouterSpend, SpendRefused
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()),
                      toml="[router]\nmax_daily_cost_usd = 0.30\n")
    with connect(env.repository.sqlite_path, read_only=True) as probe:
        assert str(probe.execute("PRAGMA journal_mode").fetchone()[0]).lower() != "wal"
    late = _MeteredClient(0.45)
    reader = sqlite3.connect(env.repository.sqlite_path)
    reader.execute("BEGIN")
    reader.execute("SELECT COUNT(*) FROM practice_attempts").fetchone()  # holds the snapshot (a SHARED lock)
    started = time.monotonic()
    try:
        with provenance.trace_scope("TRACE_SNAPSHOT"), pytest.raises(SpendRefused) as caught, \
                RouterSpend().metered(env.repository, env.vault.config, owner_kind="router_decision",
                                      owner_id="key_snapshot"):
            late.send()
    finally:
        reader.rollback()
        reader.close()
    assert time.monotonic() - started < 2.0
    assert late.sent == 0 and caught.value.rule == "router_daily_cap"
    assert _count(env.repository.sqlite_path, "SELECT COUNT(*) FROM model_call_receipts WHERE owner_id = 'key_snapshot'") == 0


def test_a_refused_router_request_still_leaves_its_record_when_nothing_holds_a_lock(tmp_path: Path):
    from learnloop.daily_plan.router_runtime import RouterSpend, SpendRefused
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM()),
                      toml="[router]\nmax_daily_cost_usd = 0.30\n")
    with provenance.trace_scope("TRACE_FREE"), pytest.raises(SpendRefused), RouterSpend().metered(
            env.repository, env.vault.config, owner_kind="router_decision", owner_id="key_free"):
        _MeteredClient(0.45).send()
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        [record] = provenance.read(connection, "TRACE_FREE", kind="spend_admission")
    assert (record.status, record.rule) == ("refused", "router_daily_cap")
    assert record.facts["spent_usd"] == 0.0 and record.facts["request_usd"] == pytest.approx(0.45)


# -- 3. records draw their ids from a stream of their own ---------------------------------------------------------


def _seeded_day(tmp_path: Path, name: str, *, drop_records: bool) -> tuple[list[tuple], int]:
    import random

    from learnloop import ids
    from tests.router_mixture_helpers import join_carried_valuations, mixture_env, rows, run
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    with pytest.MonkeyPatch.context() as patch:
        join_carried_valuations(patch)
        patch.setattr(ids, "_wall_clock_ms", lambda: 1_760_000_000_000)  # every id in one millisecond
        patch.setattr(ids, "_last_timestamp_ms", -1)
        patch.setattr(ids, "_last_randomness", 0)
        patch.setattr(ids.secrets, "randbits", random.Random(7).getrandbits)
        if drop_records:
            patch.setattr(provenance, "write", lambda *_a, **_k: None)
        env = mixture_env(tmp_path / name, fake_runtime(decider=FakeDecider(), llm=FakeLLM()))
        with provenance.trace_scope("TRACE_SEEDED"):
            run(env, steps=4)
        decided = [(row["id"], row["seed"], row["chosen_ref"], row["propensity"]) for row in rows(env)]
    return decided, _count(env.repository.sqlite_path, "SELECT COUNT(*) FROM decision_records")


def test_a_decisions_id_and_seed_are_the_same_whether_records_are_written_or_not(tmp_path: Path):
    """Under a frozen clock every id of a process falls in one millisecond, so each id drawn from the shared stream
    moves the next one. Before the fix every record (and every record a check refused) drew its id from that
    stream, and so moved the next router decision's id, which seeds its draw."""

    recorded, written = _seeded_day(tmp_path, "recorded", drop_records=False)
    dropped, none = _seeded_day(tmp_path, "dropped", drop_records=True)
    assert written > 0 and none == 0 and recorded
    assert recorded == dropped


def test_the_record_stream_is_monotonic_and_apart_from_the_shared_one(monkeypatch):
    from learnloop import ids

    monkeypatch.setattr(ids, "_wall_clock_ms", lambda: 1_760_000_000_000)
    first = ids.new_ulid()
    minted = [provenance.new_record_id() for _ in range(5)] + [provenance.new_trace_id()]
    assert minted == sorted(minted) and len(set(minted)) == len(minted)
    second = ids.new_ulid()
    assert ids._decode_ulid(second)[1] == ids._decode_ulid(first)[1] + 1  # the shared stream moved by one only


# -- 9. a lesson's budget close is found by the lesson ------------------------------------------------------------


def _why(root: Path, target: str, *extra: str) -> dict:
    import json

    from typer.testing import CliRunner

    from learnloop.cli import app

    result = CliRunner().invoke(app, ["why", target, "--json", "--vault", str(root), *extra])
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_why_lesson_finds_the_record_the_real_lesson_budget_builder_writes(tmp_path: Path):
    from learnloop.ai.spend import SpendLimitExceeded
    from tests.helpers import create_basic_vault

    paths = create_basic_vault(tmp_path / "vault")
    repository = Repository.attach(paths.sqlite_path)
    with provenance.trace_scope("TRACE_LESSON"):
        assert refusal_records.write(repository, refusal_records.SPEND_ADMISSION,
                                     lambda: refusal_records.lesson_budget_record(
                                         lesson_id="lesson_42", exc=SpendLimitExceeded("x", rule="max_calls"),
                                         refusal={"purpose": "teacher_turn", "limit_usd": 1.0}))
    [record] = [item for item in _why(paths.root, "lesson:lesson_42")["records"] if item["kind"] == "spend_admission"]
    assert (record["subject_kind"], record["subject_id"]) == ("lesson", "lesson_42")
    assert (record["status"], record["decided_by"], record["rule"]) == ("refused", "lesson_envelope", "max_calls")


# -- 5. the trigger attempt is the one the chooser captured -------------------------------------------------------


def test_a_plan_block_names_the_attempt_its_chooser_saw_not_one_committed_while_it_waited(tmp_path: Path):
    """Attempt B commits while the chooser waits on its models (after it captured ``as_of`` = A, before the block's
    transaction): before the fix the record re-read the newest attempt there and named B, with B's record as parent."""

    from datetime import timedelta

    from learnloop.daily_plan.engine import advance
    from tests.daily_plan_fakes import record_attempt
    from tests.router_mixture_helpers import mixture_env
    from tests.router_model_fakes import FakeDecider, FakeLLM, fake_runtime

    armed: dict[str, object] = {}

    def answer(request):
        if armed.pop("step", None) is not None and "first" in armed:
            step = armed["first"]
            armed["b"] = record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"],
                                        env.clock.now() + timedelta(minutes=1), session_id=env.session_id)
        return FakeLLM.default_answer(request)

    env = mixture_env(tmp_path, fake_runtime(decider=FakeDecider(), llm=FakeLLM(answer=answer)))
    last_attempt = None
    for index in range(12):
        armed.update(step=True)
        with provenance.trace_scope(f"TRACE_AS_OF_{index}"):
            _record, step = advance(env, serve=True)
        if "b" in armed:
            break
        assert step is not None and step["kind"] == "item"
        armed["first"] = step
        env.clock.advance(2)
        last_attempt = record_attempt(env.repository, step["practice_item_id"], step["learning_object_id"],
                                      env.clock.now(), session_id=env.session_id)
    assert armed.get("b") and last_attempt, "the models were never asked while an attempt existed"
    with connect(env.repository.sqlite_path, read_only=True) as connection:
        blocks = provenance.read(connection, f"TRACE_AS_OF_{index}", kind="plan_block")
    assert blocks and all(block.facts.get("trigger_attempt") == last_attempt for block in blocks), \
        [block.facts.get("trigger_attempt") for block in blocks]
