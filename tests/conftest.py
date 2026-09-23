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

# Disable sqlite durability for every test connection. The tmpfs relocation
# above solves the fsync problem on Linux, but Windows has no tmpfs: each
# durable commit pays a rollback-journal create/delete plus an fsync, and
# on-access antivirus scanning amplifies every one of those file operations
# (measured: a fresh 100+-migration vault took ~17.5s with default pragmas vs
# ~0.3s with these — the difference between a ~10-minute suite on Linux and a
# multi-hour one on Windows). Tests are deterministic and their databases
# disposable, so crash durability buys nothing here. Patch the shared connect()
# at the source AND rebind any already-imported `from ... import connect`
# aliases so every module sees the fast version.
import learnloop.db.connection as _db_connection  # noqa: E402

_durable_connect = _db_connection.connect
_durability_active = False


def _fast_test_connect(sqlite_path, *, read_only=False):
    connection = _durable_connect(sqlite_path, read_only=read_only)
    if not read_only and not _durability_active:
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA journal_mode=MEMORY")
    return connection


_db_connection.connect = _fast_test_connect
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


def pytest_configure(config):
    global _session_durable
    _session_durable = bool(config.getoption("--durable-sqlite"))
    _set_sqlite_test_mode(durable=_session_durable)


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
    paths = helpers.create_basic_vault(tmp_path_factory.mktemp("basic-template") / "vault", fresh=True)
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
