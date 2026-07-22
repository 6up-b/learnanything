from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# On Windows only: relocate pytest's temp root into the repo. The default
# location under the user's AppData/Local/Temp can be unwritable on some
# Windows setups, which makes every test that uses tmp_path error during
# setup. Everywhere else the OS temp dir must be used as-is — on Linux it is
# typically tmpfs, and a repo-local root would put every per-test sqlite
# vault on the project filesystem, where fsync-heavy commits dominate the
# suite (measured ~9s/test on btrfs vs ~30ms on tmpfs).
if sys.platform == "win32":
    _TEMP_ROOT = Path(__file__).resolve().parent.parent / ".pytest_tmp"
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_TEMP_ROOT))
else:
    _TEMP_ROOT = Path(tempfile.gettempdir()) / "learnloop_pytest"
    _TEMP_ROOT.mkdir(parents=True, exist_ok=True)

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


def _fast_test_connect(sqlite_path):
    connection = _durable_connect(sqlite_path)
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA journal_mode=MEMORY")
    return connection


_db_connection.connect = _fast_test_connect
for _module in list(sys.modules.values()):
    if getattr(_module, "__name__", "").startswith("learnloop") and getattr(_module, "connect", None) is _durable_connect:
        _module.connect = _fast_test_connect
