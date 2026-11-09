"""Router speed stage 2, item 4: SQLite connections reused within one objective job (``db.connection.
reused_connections``, opened by ``objective_chooser._objective_job``).

* The pool: one connection per database and mode serves every ``connect()`` of the scope's thread; other threads open
  their own; a connection in use is never handed out twice; a connection given back is reset as a fresh one (no
  authorizer, its cursors finalized, any transaction its user left open rolled back) and the scope's end closes it;
  one on which anything but reads ran (a PRAGMA with an argument, a write, DDL, ATTACH) is closed at release (landing
  ruling R4). Inside an AD operation the connection carries that operation's guard and nothing after it.
* Under the durability lane (WAL, ``synchronous=FULL``): a writer commits with no busy wait while a pooled connection
  is idle, after a user left a write uncommitted, and a pooled reader sees every commit made since its previous user,
  even one whose cursor was left mid-read (no snapshot outlives its user).
* On a journey's prefetch jobs (both policies on fakes): every input build, the decision card and the combiner's fit
  are the same with the pool as read afresh without it, and the job opens a handful of connections.

Fakes only; no model call.
"""

from __future__ import annotations

from contextlib import closing
from dataclasses import fields, is_dataclass
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any

import pytest

from learnloop.db import connection as DBC
from learnloop.db.connection import connect, reused_connections

# These pin production's own pool, so production's connect path must run around it.
pytestmark = pytest.mark.fresh_connections

_PROBE = "rospeed2_probe"


def _vault_db(tmp_path) -> Path:
    from tests.helpers import create_basic_vault

    database = Path(create_basic_vault(tmp_path / "vault").sqlite_path)
    with closing(connect(database)) as connection:
        connection.execute(f"CREATE TABLE IF NOT EXISTS {_PROBE}(n INTEGER)")
        connection.executemany(f"INSERT INTO {_PROBE}(n) VALUES (?)", [(n,) for n in range(5)])
        connection.commit()
    return database


def _pool() -> DBC._ConnectionPool:
    pool = DBC._REUSED.get()
    assert pool is not None
    return pool


def test_one_connection_per_database_and_mode_serves_the_scopes_thread(tmp_path):
    database = _vault_db(tmp_path)
    with reused_connections():
        raws = set()
        for _ in range(20):
            with closing(connect(database, read_only=True)) as connection:
                assert connection.execute(f"SELECT COUNT(*) FROM {_PROBE}").fetchone()[0] == 5
                raws.add(id(connection._connection))
        for _ in range(5):
            with closing(connect(database)) as connection:
                connection.execute(f"SELECT COUNT(*) FROM {_PROBE}").fetchone()
        assert _pool().opened == 2 and _pool().handed == 25 and len(raws) == 1
        # In use, never handed out again: a nested user gets its own.
        outer = connect(database, read_only=True)
        inner = connect(database, read_only=True)
        assert outer._connection is not inner._connection
        inner.close()
        outer.close()
        # Another thread (a model call copies the job's context) opens its own, never the pool's.
        seen: dict[str, Any] = {}

        def other() -> None:
            connection = connect(database, read_only=True)
            seen["type"] = type(connection)
            connection.close()

        import contextvars

        context = contextvars.copy_context()
        thread = threading.Thread(target=context.run, args=(other,))
        thread.start()
        thread.join()
        assert seen["type"] is sqlite3.Connection
        idle = [raw for raws_ in _pool().idle.values() for raw in raws_]
    with pytest.raises(sqlite3.ProgrammingError):
        idle[0].execute("SELECT 1")  # the scope's end closed every idle connection
    assert type(connect(database, read_only=True)) is sqlite3.Connection  # outside the scope: as before


def test_a_connection_given_back_is_reset_as_a_fresh_one(tmp_path):
    database = _vault_db(tmp_path)
    with reused_connections():
        connection = connect(database)
        connection.row_factory = None
        connection.isolation_level = None
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("PRAGMA busy_timeout = 1")
        connection.set_authorizer(lambda *args: sqlite3.SQLITE_DENY)
        cursor = connection.cursor()
        connection.close()
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
        with pytest.raises(sqlite3.ProgrammingError):
            cursor.execute("SELECT 1")
        again = connect(database)
        assert again.row_factory is sqlite3.Row and again.isolation_level == ""
        assert again.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert again.execute("PRAGMA busy_timeout").fetchone()[0] == DBC.BUSY_TIMEOUT_MS
        assert again.execute("PRAGMA synchronous").fetchone()[0] in (2, 0)  # FULL (the tests' connect sets OFF)
        assert again.execute(f"SELECT COUNT(*) FROM {_PROBE}").fetchone()[0] == 5  # no authorizer left
        # A write left uncommitted is discarded when its user closes the connection, as a close discards it.
        again.execute(f"INSERT INTO {_PROBE}(n) VALUES (99)")
        assert again.in_transaction
        again.close()
        third = connect(database)
        assert not third.in_transaction
        assert third.execute(f"SELECT COUNT(*) FROM {_PROBE} WHERE n = 99").fetchone()[0] == 0
        third.close()


def test_inside_an_ad_operation_a_pooled_connection_carries_its_guard_and_nothing_after(tmp_path):
    from learnloop.adaptive_difficulty.operation import ad_operation
    from learnloop.db.repositories import Repository
    from learnloop.vault.loader import load_vault

    from learnloop.algorithm_versions import LESSON_OFFERS_ALGORITHM_VERSION

    from tests.helpers import create_basic_vault, set_algorithm_version

    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, LESSON_OFFERS_ALGORITHM_VERSION)
    vault = load_vault(paths.root)
    assert vault.config.adaptive_difficulty.enabled
    repository = Repository(paths.sqlite_path)
    with reused_connections():
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            connection.execute("SELECT COUNT(*) FROM grading_evidence").fetchone()  # no operation: read freely
        with pytest.raises(Exception):
            with ad_operation(vault, repository, read_only=True):
                with closing(connect(paths.sqlite_path, read_only=True)) as connection:
                    connection.execute("SELECT COUNT(*) FROM grading_evidence").fetchone()  # DENIED to AD
        with closing(connect(paths.sqlite_path, read_only=True)) as connection:
            assert connection.execute("SELECT COUNT(*) FROM grading_evidence").fetchone()[0] >= 0
        assert _pool().opened < _pool().handed  # the operation's own reads reused them too


# -- the durability lane: WAL, locks and snapshots ----------------------------------------------------------------


@pytest.mark.durability
def test_no_lock_and_no_stale_snapshot_under_wal(tmp_path):
    from learnloop.db.storage import header_journal_mode

    database = _vault_db(tmp_path)
    assert header_journal_mode(database) == "wal"
    writer = sqlite3.connect(database, isolation_level=None)
    writer.execute("PRAGMA busy_timeout = 0")  # a lock held by the pool fails at once, never waits

    def commit(n: int) -> None:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute(f"INSERT INTO {_PROBE}(n) VALUES (?)", (n,))
        writer.execute("COMMIT")

    try:
        with reused_connections():
            # A user leaves a write uncommitted and closes: no lock is kept.
            first = connect(database)
            first.execute(f"INSERT INTO {_PROBE}(n) VALUES (100)")
            first.close()
            commit(1)
            # A user reads one row of many and keeps the cursor: its snapshot ends with its use.
            reader = connect(database, read_only=True)
            cursor = reader.execute(f"SELECT n FROM {_PROBE}")
            cursor.fetchone()
            reader.close()
            commit(2)
            writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            again = connect(database, read_only=True)
            assert again._connection is reader._connection
            assert again.execute(f"SELECT COUNT(*) FROM {_PROBE}").fetchone()[0] == 7  # sees both commits
            assert again.execute(f"SELECT COUNT(*) FROM {_PROBE} WHERE n = 100").fetchone()[0] == 0
            again.close()
            commit(3)  # idle in the pool: no lock
        busy = writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        assert busy[0] == 0
    finally:
        writer.close()


# -- the journey: every value equal with and without the pool ------------------------------------------------------


def _canon(value: Any) -> Any:
    """A value as exact JSON (floats by their bits)."""

    import numpy as np

    if is_dataclass(value) and not isinstance(value, type):
        return {"__type": type(value).__name__, **{f.name: _canon(getattr(value, f.name)) for f in fields(value)}}
    if isinstance(value, dict):
        return {str(key): _canon(item) for key, item in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canon(item) for item in value]
    if isinstance(value, np.ndarray):
        return [_canon(item) for item in value.tolist()]
    if isinstance(value, (float, np.floating)):
        return float(value).hex()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (set, frozenset)):
        return sorted(_canon(item) for item in value)
    return value


def test_every_build_card_and_fit_of_the_jobs_is_the_same_with_the_pool(tmp_path, monkeypatch):
    """Each prefetch job's input builds, its decision card and its combiner fit, recomputed at once with the pool
    switched off for that call (fresh connections), are equal bit for bit; the job opens a handful of connections."""

    from learnloop.daily_plan import objective_card as OCARD
    from learnloop.daily_plan import objective_inputs as OI

    from tests.test_rospeed_join import _journey

    compared: dict[str, int] = {"build": 0, "card": 0, "fit": 0}

    def without_pool(call):
        token = DBC._REUSED.set(None)
        try:
            return call()
        finally:
            DBC._REUSED.reset(token)

    real_build = OI.build

    def build(*args, **kwargs):
        pooled = real_build(*args, **kwargs)
        if DBC._REUSED.get() is not None:
            fresh = without_pool(lambda: real_build(*args, **kwargs))
            assert json.dumps(_canon(pooled), sort_keys=True, default=str) == json.dumps(
                _canon(fresh), sort_keys=True, default=str)
            compared["build"] += 1
        return pooled

    real_card = OCARD.decision_card

    def card(*args, **kwargs):
        pooled = real_card(*args, **kwargs)
        if DBC._REUSED.get() is not None:
            fresh = without_pool(lambda: real_card(*args, **kwargs))
            assert json.dumps(_canon(pooled), sort_keys=True, default=str) == json.dumps(
                _canon(fresh), sort_keys=True, default=str)
            compared["card"] += 1
        return pooled

    real_fit = OI._combiner_read

    def fit(repository, now_iso, vault=None):
        pooled = real_fit(repository, now_iso, vault)
        if DBC._REUSED.get() is not None:
            fresh = without_pool(lambda: real_fit(repository, now_iso, vault))
            assert _canon(pooled) == _canon(fresh)
            compared["fit"] += 1
        return pooled

    monkeypatch.setattr(OI, "build", build)
    monkeypatch.setattr(OCARD, "decision_card", card)
    monkeypatch.setattr(OI, "_combiner_read", fit)
    _journey(tmp_path, steps=12)
    assert compared["build"] >= 4 and compared["card"] >= 2 and compared["fit"] >= 2, compared
    print("ROSPEED2_COMPARED", json.dumps(compared))


# -- Codex review F2: the pool is a serving change under the deadline, behind its own switch ------------------------


class _OpenCharged:
    """A deterministic clock: one unit per sigmoid element evaluated (the rollouts' work, as router speed's F1 clock)
    and ``per_open`` units per SQLite connection opened on the replay's own thread (what the pool saves)."""

    def __init__(self, per_open: int) -> None:
        self.spent = 0
        self.opens = 0
        self.per_open = per_open
        self.thread = threading.get_ident()

    def __call__(self) -> float:
        return float(self.spent)

    def install(self, patch) -> None:
        import numpy as np

        from learnloop.router_objective import memory as M
        from learnloop.router_objective import value as V

        real_sigmoid = M.sigmoid

        def charged(x):
            self.spent += int(np.size(x))
            return real_sigmoid(x)

        for module in (V, M):
            patch.setattr(module, "sigmoid", charged)
        for name in ("_open_read_only", "_open_writable"):
            real_open = getattr(DBC, name)

            def opened(*args, _real=real_open, **kwargs):
                if threading.get_ident() == self.thread:
                    self.opens += 1
                    self.spent += self.per_open
                return _real(*args, **kwargs)

            patch.setattr(DBC, name, opened)


def test_the_pool_completes_more_draws_by_one_deadline_and_switched_off_is_mains(tmp_path, monkeypatch):
    """Codex review F2. One prefetch job's numeric policy, replayed on its own inputs with the LLM still out (so the
    evaluation refines until the deadline): on a clock charged per sigmoid element and per connection opened, main's
    code (no pool, ``held_reading_map`` off) completes its first 8 draws by a deadline that admits no more, and the
    branch with both switches on completes more by the same deadline, so its choice can differ (the reason both are
    serving changes in RO6's generator payload and the prefetch key). At a fixed number of draws the two are equal
    bit for bit, and the job takes its pool from ``[router_objective] pooled_connections`` alone (``_pooled``)."""

    from learnloop.adaptive_difficulty import reading_cache
    from learnloop.daily_plan import objective_chooser as OC

    from tests.test_rospeed_join import _journey

    real = OC.run_numeric
    found: dict[str, Any] = {}

    def replay(vault, repository, kwargs, *, branch: bool, per_open: int, refine: bool,
               deadline_after: float | None = None) -> tuple[Any, _OpenCharged]:
        """The job's numeric policy on its own inputs: ``branch`` with both switches' code on (the pool, the held
        map), else main's (no pool, the map off); ``refine``: while the LLM is out (until the deadline or 64 draws),
        else the first batch alone (8 draws)."""

        with monkeypatch.context() as patch:
            clock = _OpenCharged(per_open)
            clock.install(patch)
            if not branch:
                patch.setattr(reading_cache, "held_on", lambda _config: False)
            token = DBC._REUSED.set(None)
            try:
                with reused_connections() if branch else OC._pooled(None):
                    start = clock()
                    policy = real(vault, repository, **{
                        **kwargs, "clock": clock, "keep_going": lambda: refine, "forecasts": None, "publish": None,
                        "defer_carried": None,
                        "deadline": None if deadline_after is None else start + deadline_after})
            finally:
                DBC._REUSED.reset(token)
        return policy, clock

    def numeric(vault, repository, **kwargs):
        if "runs" not in found:
            replay(vault, repository, kwargs, branch=False, per_open=0, refine=False)  # warm (the day's price)
            _policy, work = replay(vault, repository, kwargs, branch=False, per_open=0, refine=False)
            per_open = max(1, int(work.spent))  # one open priced as main's whole first batch of rollouts
            first, clock = replay(vault, repository, kwargs, branch=False, per_open=per_open, refine=False)
            again, clock_again = replay(vault, repository, kwargs, branch=False, per_open=per_open, refine=False)
            assert clock.spent == clock_again.spent and _canon(first.evaluation) == _canon(again.evaluation)
            budget = float(clock.spent)  # main's first batch fits by the deadline; its refinement does not
            main, main_clock = replay(vault, repository, kwargs, branch=False, per_open=per_open, refine=True,
                                      deadline_after=budget)
            branch, branch_clock = replay(vault, repository, kwargs, branch=True, per_open=per_open, refine=True,
                                          deadline_after=budget)
            fixed, _fixed_clock = replay(vault, repository, kwargs, branch=True, per_open=per_open, refine=False)
            found["runs"] = {
                "main": [main.evaluation.draws, main.evaluation.complete, main.choice, main_clock.opens],
                "branch": [branch.evaluation.draws, branch.evaluation.complete, branch.choice, branch_clock.opens],
                "fixed_draws_equal": _canon(fixed.evaluation.valued) == _canon(first.evaluation.valued),
                "choice_at_8": [first.choice, fixed.choice],
            }
        return real(vault, repository, **kwargs)

    monkeypatch.setattr(OC, "run_numeric", numeric)
    _journey(tmp_path, steps=2)
    runs = found["runs"]
    print("ROSPEED2_F2", json.dumps(runs, default=str))
    assert runs["main"][:2] == [8, True]
    assert runs["branch"][3] < runs["main"][3]  # the pool opens fewer connections ...
    assert runs["branch"][0] > runs["main"][0] and runs["branch"][1]  # ... so the same deadline admits more draws
    assert runs["fixed_draws_equal"] and runs["choice_at_8"][0] == runs["choice_at_8"][1]  # equal at fixed draws


def test_the_pool_and_the_held_map_follow_their_switches(tmp_path):
    """``[router_objective] pooled_connections`` and ``held_reading_map``: on at the follow-up batch's tag by default,
    off when switched off or below the tag; both in RO6's generator payload and the prefetch boundary key."""

    from contextlib import nullcontext

    from learnloop.adaptive_difficulty import reading_cache
    from learnloop.algorithm_versions import ROUTER_FOLLOWUPS_ALGORITHM_VERSION, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION
    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.router_objective_switches import (FOLLOWUP_GENERATOR_SWITCHES, FOLLOWUP_SWITCHES,
                                                     followup_generator_switches)
    from learnloop.vault.loader import load_vault

    from tests.helpers import append_config_toml, create_basic_vault, set_algorithm_version

    for key in ("held_reading_map", "pooled_connections"):
        assert key in FOLLOWUP_GENERATOR_SWITCHES and key in FOLLOWUP_SWITCHES
    paths = create_basic_vault(tmp_path / "vault")

    def state() -> tuple[bool, bool, dict | None]:
        config = load_vault(paths.root).config
        return (not isinstance(OC._pooled(config), nullcontext), reading_cache.held_on(config),
                followup_generator_switches(config))

    set_algorithm_version(paths, ROUTER_FOLLOWUPS_ALGORITHM_VERSION)
    pooled, held, switches = state()
    assert (pooled, held) == (True, True)
    assert switches["pooled_connections"] is True and switches["held_reading_map"] is True
    set_algorithm_version(paths, ROUTER_LEARNED_TAIL_ALGORITHM_VERSION)
    assert state() == (False, False, None)
    set_algorithm_version(paths, ROUTER_FOLLOWUPS_ALGORITHM_VERSION)
    append_config_toml(paths.root, "[router_objective]\npooled_connections = false\nheld_reading_map = false\n")
    pooled, held, switches = state()
    assert (pooled, held) == (False, False)
    assert switches["pooled_connections"] is False and switches["held_reading_map"] is False
    assert isinstance(OC._pooled(None), nullcontext)


def test_switched_off_the_job_opens_a_connection_at_every_connect(tmp_path, monkeypatch):
    """``pooled_connections = false``: no input build of any objective job runs inside a pool (main's job: a
    connection opened at every ``connect()``)."""

    from learnloop.daily_plan import objective_inputs as OI

    from tests.test_rospeed_join import _journey

    seen: list[bool] = []
    real_build = OI.build

    def build(*args, **kwargs):
        seen.append(DBC._REUSED.get() is None)
        return real_build(*args, **kwargs)

    monkeypatch.setattr(OI, "build", build)
    import tests.router_mixture_helpers as RMH

    real_env = RMH.mixture_env

    def switched_off(tmp_path, runtime, **kwargs):
        return real_env(tmp_path, runtime, **{**kwargs, "toml": "[router_objective]\npooled_connections = false\n"})

    monkeypatch.setattr(RMH, "mixture_env", switched_off)
    _journey(tmp_path, steps=2)
    assert seen and all(seen), seen


def test_the_job_opens_a_handful_of_connections(tmp_path, monkeypatch):
    from learnloop.daily_plan import objective_chooser as OC

    from tests.test_rospeed_join import _journey

    counter = {"n": 0}
    opens: list[int] = []
    real_connect = sqlite3.connect

    def counting(*args, **kwargs):
        counter["n"] += 1
        return real_connect(*args, **kwargs)

    real_job = OC._objective_job

    def job(*args, **kwargs):
        before = counter["n"]
        try:
            return real_job(*args, **kwargs)
        finally:
            opens.append(counter["n"] - before)

    monkeypatch.setattr(sqlite3, "connect", counting)
    monkeypatch.setattr(OC, "_objective_job", job)
    _journey(tmp_path)
    # Landing ruling R4: a checkout that ran a PRAGMA with an argument (the repositories' ``table_info`` column
    # checks) or a write (the job's model-call receipts) closes its connection, so a job opens about a dozen (5
    # before R4; main: hundreds).
    assert opens and max(opens) <= 12, opens
    print("ROSPEED2_JOB_OPENS", json.dumps(opens))


# -- landing ruling R4: a checkout that changed its connection's state never hands it out again --------------------


@pytest.mark.parametrize("read_only", [False, True], ids=["writable", "read_only"])
def test_r4_a_pragma_set_during_a_checkout_never_reaches_the_next_user(tmp_path, read_only):
    """Codex's verify, N1: checkout A sets ``query_only`` and ``reverse_unordered_selects`` and gives the connection
    back; checkout B must not inherit either (main's reset restored a list of settings, not these). Landing ruling R4:
    a connection on which a PRAGMA with an argument ran during a checkout (the authorizer's SQLITE_PRAGMA action) is
    closed at release, never pooled again."""

    database = _vault_db(tmp_path)
    with reused_connections():
        connection = connect(database, read_only=read_only)
        first = connection._connection
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA reverse_unordered_selects = ON")
        assert [row[0] for row in connection.execute(f"SELECT n FROM {_PROBE}")] == [4, 3, 2, 1, 0]
        connection.close()
        with closing(connect(database, read_only=read_only)) as again:
            assert again.execute("PRAGMA query_only").fetchone()[0] == 0
            assert again.execute("PRAGMA reverse_unordered_selects").fetchone()[0] == 0
            assert [row[0] for row in again.execute(f"SELECT n FROM {_PROBE}")] == [0, 1, 2, 3, 4]
            if not read_only:
                again.execute(f"INSERT INTO {_PROBE}(n) VALUES (99)")  # writable, as a fresh connection is
                again.rollback()
            assert again._connection is not first  # closed at release, not handed out
    with pytest.raises(sqlite3.ProgrammingError):
        first.execute("SELECT 1")  # closed


def test_r4_only_a_checkout_of_reads_is_pooled_again(tmp_path):
    """R4's other half: a checkout whose statements were all reads (a PRAGMA without an argument is a read) gives its
    connection back; a write, DDL or ATTACH (any statement other than reads and the pool's own resets) closes it."""

    database = _vault_db(tmp_path)

    def reused_after(statements: list[str], *, read_only: bool) -> bool:
        with reused_connections():
            connection = connect(database, read_only=read_only)
            first = connection._connection
            for sql in statements:
                connection.execute(sql).fetchall()
            connection.rollback()
            connection.close()
            with closing(connect(database, read_only=read_only)) as again:
                return again._connection is first

    assert reused_after([f"SELECT COUNT(*) FROM {_PROBE}", "PRAGMA data_version", "PRAGMA schema_version"],
                        read_only=True)
    assert reused_after([f"SELECT n FROM {_PROBE} WHERE n > 1"], read_only=False)
    assert not reused_after([f"INSERT INTO {_PROBE}(n) VALUES (7)"], read_only=False)
    assert not reused_after(["CREATE TEMP TABLE scratch(x)"], read_only=False)
    assert not reused_after([f"ATTACH DATABASE '{tmp_path / 'other.sqlite'}' AS other"], read_only=False)
    assert not reused_after(["PRAGMA cache_size = 10"], read_only=True)


# -- landing ruling R2: the numeric policy's seed excludes the two speed switches -----------------------------------

#: Main ccb6573987's FOLLOWUP_SWITCHES (the prefetch key's switch snapshot before this stage).
_MAIN_SWITCHES = ("combiner_trace_outcomes", "merged_sessions", "consistent_review_draw", "monotone_combiner",
                  "ad_predictive_link", "scope_extension", "held_ad_link", "carried_in_prefetch")


@pytest.mark.parametrize("switches", ["off", "on"])
def test_r2_the_numeric_seed_is_mains_whatever_the_speed_switches(tmp_path, monkeypatch, switches):
    """Codex's verify, F2: at the tag with both switches off, the boundary identity differs from main's only by the
    two switches' entries in its snapshot, and the numeric seed was derived from it, so at eight draws (no deadline)
    the real evaluator chose main ``a``, the branch ``b``. Landing ruling R2: both stay in the prefetch key, but the
    numeric policy's seed is derived from the identity without them (they change no value at a fixed draw count), so
    its draws are main's: here every job's seed is main's, and its eight-draw evaluation is main's bit for bit."""

    from learnloop.daily_plan import objective_chooser as OC
    from learnloop.router_objective_switches import FOLLOWUP_SWITCHES

    import tests.router_mixture_helpers as RMH
    from tests.test_rospeed_join import _journey

    assert tuple(key for key in FOLLOWUP_SWITCHES if key not in ("held_reading_map", "pooled_connections")) == \
        _MAIN_SWITCHES
    identities: list[dict[str, Any]] = []
    real_hash = OC._hash

    def recording(value):
        # The prefetch key's identity (its snapshot names every switch; the seed's own hash names fewer).
        if isinstance(value, dict) and value.get("kind") == "objective_block" and "held_reading_map" in (
                value.get("objective") or {}).get("followup_switches", {}):
            identities.append(value)
        return real_hash(value)

    def mains(identity: dict[str, Any]) -> dict[str, Any]:
        objective = dict(identity["objective"])
        objective["followup_switches"] = {key: value for key, value in objective["followup_switches"].items()
                                          if key in _MAIN_SWITCHES}
        return {**identity, "objective": objective}

    real = OC.run_numeric
    seen: list[dict[str, Any]] = []

    def numeric(vault, repository, **kwargs):
        identity = next(found for found in reversed(identities) if real_hash({"numeric": real_hash(found)}) ==
                        kwargs["seed"] or real_hash({"numeric": real_hash(mains(found))}) == kwargs["seed"])
        main_seed = real_hash({"numeric": real_hash(mains(identity))})
        old_seed = real_hash({"numeric": real_hash(identity)})
        fixed = {**kwargs, "keep_going": lambda: False, "forecasts": None, "publish": None, "defer_carried": None,
                 "deadline": None}
        at_main = real(vault, repository, **{**fixed, "seed": main_seed})
        at_served = real(vault, repository, **fixed)
        at_old = real(vault, repository, **{**fixed, "seed": old_seed})
        seen.append({"seed_is_mains": kwargs["seed"] == main_seed, "old_differs": old_seed != main_seed,
                     "draws": [at_main.evaluation.draws, at_served.evaluation.draws],
                     "equal": _canon(at_main.evaluation.valued) == _canon(at_served.evaluation.valued),
                     "choices": [at_main.choice, at_served.choice, at_old.choice]})
        return real(vault, repository, **kwargs)

    monkeypatch.setattr(OC, "_hash", recording)
    monkeypatch.setattr(OC, "run_numeric", numeric)
    real_env = RMH.mixture_env
    toml = ("[router_objective]\nheld_reading_map = false\npooled_connections = false\n" if switches == "off"
            else None)

    def env(tmp_path, runtime, **kwargs):
        return real_env(tmp_path, runtime, **{**kwargs, "toml": toml})

    monkeypatch.setattr(RMH, "mixture_env", env)
    _journey(tmp_path, steps=3)
    print("ROSPEED2_R2", json.dumps(seen, default=str))
    assert seen
    for row in seen:
        assert row["old_differs"]  # the two entries change the key (and so main's derivation would move)
        assert row["seed_is_mains"], row
        assert row["draws"] == [8, 8] and row["equal"] and row["choices"][0] == row["choices"][1], row
