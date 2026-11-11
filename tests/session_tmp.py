"""Each pytest run's scratch directory under ``.pytest_tmp``, removed when the run ends.

Fixture vaults, pytest's numbered ``tmp_path`` roots, the isolated config dir and the fresh-schema caches all live in
one ``run-<pid>-*`` directory per run. The pytest session that made it deletes it when the run ends: the shared root
used to keep every run's vaults and grew to tens of gigabytes per checkout. xdist workers, a pytest that a test starts
in a subprocess, and a ``pytest.main()`` nested in the same process inherit the directory and leave it to the session
that made it. A run that was killed (oomd, Ctrl-C twice) leaves its directory behind; the next run in the same checkout
removes it once its pid is gone.

Set ``LEARNLOOP_KEEP_TEST_TMP=1`` to keep the directory, for instance to look at a failed test's vault: it gets a
``KEEP`` marker that later runs respect, so delete it yourself when done.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path

SESSION_ENV = "LEARNLOOP_TEST_SESSION_TMP"
OWNER_ENV = "LEARNLOOP_TEST_SESSION_TMP_OWNER"
KEEP_ENV = "LEARNLOOP_KEEP_TEST_TMP"
KEEP_MARKER = "KEEP"
RUN_PREFIX = "run-"
# What runs before per-run directories left directly under the root. A run still on the old conftest may be using
# them, and nothing tells which, so they go only once untouched for a day (no test run takes that long).
LEGACY_PREFIXES = ("pytest-of-", "global_settings_isolated", "fresh-schema-")
LEGACY_MIN_AGE_SECONDS = 24 * 3600

# The directory this process made, and the first pytest session to claim it: only that session deletes it, so a
# nested pytest.main() in the same process (same pid, same environment) cannot remove its parent's files.
_made: Path | None = None
_claimant: object | None = None


def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _run_pid(name: str) -> int | None:
    if not name.startswith(RUN_PREFIX):
        return None
    pid, _, _ = name[len(RUN_PREFIX) :].partition("-")
    return int(pid) if pid.isdigit() else None


def _is_run_dir(path: Path, temp_root: Path) -> bool:
    """A ``run-<pid>-*`` directory directly under ``temp_root``: the only kind this module ever deletes or adopts."""
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return False
    return (
        resolved.is_dir()
        and not path.is_symlink()
        and resolved.parent == temp_root.resolve()
        and _run_pid(resolved.name) is not None
    )


def _legacy_in_use(entry: Path) -> bool:
    # A run adds a numbered dir to pytest-of-* or writes into the others as it starts, which bumps the mtime.
    return time.time() - entry.lstat().st_mtime < LEGACY_MIN_AGE_SECONDS


def sweep_stale(temp_root: Path) -> list[Path]:
    """Remove the directories of runs whose process is gone (unless kept), and day-old leftovers of older runs."""
    removed = []
    for entry in sorted(temp_root.iterdir()) if temp_root.is_dir() else ():
        pid = _run_pid(entry.name)
        if pid is not None:
            stale = (
                pid != os.getpid()
                and not pid_alive(pid)
                and _is_run_dir(entry, temp_root)
                and not (entry / KEEP_MARKER).exists()
            )
        else:
            stale = entry.name.startswith(LEGACY_PREFIXES) and not entry.is_symlink() and not _legacy_in_use(entry)
        if stale:
            shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)
            removed.append(entry)
    return removed


def session_root(temp_root: Path) -> Path:
    """This run's directory: the one a live run in ``temp_root`` handed down, otherwise a new one this process makes."""
    global _made
    inherited, owner = os.environ.get(SESSION_ENV), os.environ.get(OWNER_ENV, "")
    if inherited and owner.isdigit() and pid_alive(int(owner)) and _is_run_dir(Path(inherited), temp_root):
        return Path(inherited)
    temp_root.mkdir(parents=True, exist_ok=True)
    sweep_stale(temp_root)
    root = Path(tempfile.mkdtemp(prefix=f"{RUN_PREFIX}{os.getpid()}-", dir=temp_root))
    os.environ[SESSION_ENV] = str(root)
    os.environ[OWNER_ENV] = str(os.getpid())
    _made = root
    return root


def claim(session: object) -> None:
    """Called from pytest_configure: the first session in the process that made the directory becomes its owner."""
    global _claimant
    if _made is not None and _claimant is None:
        _claimant = session


def finish(root: Path, session: object) -> str | None:
    """Delete ``root`` if ``session`` owns it. Returns a line to print when it is kept on request, else None."""
    global _claimant
    if _made is None or session is not _claimant or root != _made or os.environ.get(OWNER_ENV) != str(os.getpid()):
        return None
    _claimant = None
    if not _is_run_dir(root, root.parent):
        return None
    if os.environ.get(KEEP_ENV, "").strip() not in ("", "0"):
        (root / KEEP_MARKER).touch()
        return f"{KEEP_ENV} is set: kept this run's test files in {root} (delete it when done)"
    shutil.rmtree(root, ignore_errors=True)
    return None
