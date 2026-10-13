from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

# Keep the 4,000+ fixture vaults off the capacity-constrained system temp
# volume. PYTEST_DEBUG_TEMPROOT controls pytest's numbered tmp_path roots when
# --basetemp is not supplied, while still allowing CI to override it.
_TEMP_ROOT = Path(__file__).resolve().parent.parent / ".pytest_tmp"
_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMP_ROOT))

# Isolate tests from machine-global learnloop settings. Point LEARNLOOP_CONFIG_DIR
# at an empty dir (so a developer's real ~/.config/learnloop/settings.env is not
# read) and clear LEARNLOOP_CODEX_CHECKOUT_PATH, so per-test fixtures that inject
# a temp Codex checkout/revision are not overridden by the ambient environment.
os.environ["LEARNLOOP_CONFIG_DIR"] = str(_TEMP_ROOT / "global_settings_isolated")
os.environ.pop("LEARNLOOP_CODEX_CHECKOUT_PATH", None)
# The ChatGPT-plan sign-in store lives under LEARNLOOP_CONFIG_DIR (isolated
# above); forcing its file backend keeps every test away from an OS keyring.
os.environ["LEARNLOOP_CHATGPT_SECRET_STORE"] = "file"
# Tier 1 (mvp-0.20, the template's version) asks the Decider by default, on the
# code-default openrouter_decider profile's key: never a real key in a test, so
# an unfaked Decider is unavailable and its LLM fallback runs (a test that
# exercises the Decider injects a fake client).
for _decider_key in ("OPENROUTER_API_KEY", "PERPLEXITY_API_KEY"):
    os.environ.pop(_decider_key, None)

# Disable sqlite durability for every test connection. Each durable commit
# pays a journal write plus an fsync, and on Windows on-access antivirus
# scanning amplifies every one of those file operations (measured: a fresh
# 100+-migration vault took ~17.5s with default pragmas vs ~0.3s with these —
# the difference between a suite that runs in minutes on Linux and a multi-hour
# one on Windows). Tests are deterministic and their databases disposable, so
# crash durability buys nothing here. Patch the shared connect() at the source
# AND rebind any already-imported `from ... import connect` aliases so every
# module sees the fast version.
#
# The fast lane also skips the migration's one-way switch to WAL, so its
# databases keep a rollback header and the in-memory journal applies. The
# durability lane (`durability` marker or --durable-sqlite) runs the production
# path: the switch to WAL and synchronous=FULL.
import learnloop.db.connection as _db_connection  # noqa: E402
import learnloop.db.migrate as _db_migrate  # noqa: E402

_durable_connect = _db_connection.connect
_production_switch_to_wal = _db_migrate.switch_to_wal
_durability_active = False


def _fast_test_connect(sqlite_path, *, read_only=False):
    connection = _durable_connect(sqlite_path, read_only=read_only)
    if not read_only and not _durability_active:
        connection.execute("PRAGMA synchronous=OFF")
        # A WAL database built by a durability-lane fixture stays WAL: leaving
        # WAL needs exclusive access and would silently fail while another
        # connection is open, making the mode depend on test order.
        if connection.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
            connection.execute("PRAGMA journal_mode=MEMORY")
    return connection


def _lane_switch_to_wal(connection, sqlite_path):
    if _durability_active:
        return _production_switch_to_wal(connection, sqlite_path)
    return "fast test lane keeps the in-memory journal"


_db_connection.connect = _fast_test_connect
_db_migrate.switch_to_wal = _lane_switch_to_wal
for _module in list(sys.modules.values()):
    if getattr(_module, "__name__", "").startswith("learnloop") and getattr(_module, "connect", None) is _durable_connect:
        _module.connect = _fast_test_connect


def pytest_addoption(parser):
    parser.addoption("--durable-sqlite", action="store_true", help="Use production SQLite durability for every selected test.")


# The SQLite mode is switched in runtest hooks rather than in a fixture because
# pytest builds module- and session-scoped fixtures before any function-scoped
# autouse fixture runs; a fixture-based switch would leave shared fixtures in
# the fast lane. The mode active when a shared fixture is first built is the
# one it keeps, so a module fixture used by both `durability` tests and plain
# tests runs in whichever lane its first consumer selected.
_session_durable = False


def _set_sqlite_test_mode(*, durable: bool) -> None:
    from tests import helpers

    global _durability_active
    _durability_active = durable
    # Durability tests also exercise real vault construction, not a copy.
    helpers._FRESH_VAULTS = durable


# Tracked fixture databases must never be opened writable in place: that
# would switch their header to WAL and leave -wal/-shm files in the working
# tree. The state is recorded at start and compared when the session ends, so
# the check covers every test that ran, whatever its order.
_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
_fixture_state_at_start: dict[str, tuple[str, tuple[str, ...]]] = {}


def _fixture_database_state() -> dict[str, tuple[str, tuple[str, ...]]]:
    from learnloop.db.copies import COMPANION_SUFFIXES
    from learnloop.db.storage import header_journal_mode

    # A read-only open of a WAL database creates an empty -wal and a -shm, so
    # companion presence alone is not a change; only the header mode and
    # un-checkpointed WAL frames are.
    state = {}
    for database in sorted(_FIXTURES.rglob("*.sqlite")):
        pending = tuple(
            database.name + suffix
            for suffix in COMPANION_SUFFIXES
            if database.with_name(database.name + suffix).exists()
            and database.with_name(database.name + suffix).stat().st_size > 0
            and suffix != "-shm"
        )
        state[str(database.relative_to(_FIXTURES))] = (header_journal_mode(database), pending)
    return state


def pytest_configure(config):
    global _session_durable
    _session_durable = bool(config.getoption("--durable-sqlite"))
    _set_sqlite_test_mode(durable=_session_durable)
    _fixture_state_at_start.update(_fixture_database_state())


def pytest_sessionfinish(session, exitstatus):
    current = _fixture_database_state()
    changed = {
        name: (_fixture_state_at_start.get(name), current.get(name))
        for name in sorted(set(_fixture_state_at_start) | set(current))
        if _fixture_state_at_start.get(name) != current.get(name)
    }
    if not changed:
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    message = (
        "tracked fixture databases changed during the test run (journal mode or un-checkpointed WAL frames); "
        f"a test opened one writable in place instead of copying it first: {changed}"
    )
    if reporter is not None:
        reporter.write_line(f"ERROR: {message}", red=True)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    durable = _session_durable or item.get_closest_marker("durability") is not None
    _set_sqlite_test_mode(durable=durable)


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    _set_sqlite_test_mode(durable=_session_durable)


@pytest.fixture(scope="session", autouse=True)
def basic_vault_template(tmp_path_factory):
    from tests import helpers
    global _durability_active
    # Only fast-lane tests copy the template, so it is built in the session's
    # lane even when a durability test is the first to request it; otherwise
    # it would carry a WAL header into every fast-lane copy.
    requesting_lane = _durability_active
    _durability_active = _session_durable
    try:
        paths = helpers.create_basic_vault(tmp_path_factory.mktemp("basic-template") / "vault", fresh=True)
    finally:
        _durability_active = requesting_lane
    # Copying a database with embedded template-root identities would silently
    # point tests at shared state. Scan text and SQLite bytes before enabling it.
    prefix = str(paths.root).encode()
    files_naming_root = [
        str(path.relative_to(paths.root))
        for path in paths.root.rglob("*")
        if path.is_file() and prefix in path.read_bytes()
    ]
    assert not files_naming_root, f"template vault files embed their absolute root: {files_naming_root}"
    helpers._BASIC_VAULT_TEMPLATE = paths
    yield
    helpers._BASIC_VAULT_TEMPLATE = None
