"""The opt-in ``owner_vaults`` lane and the fixtures that stay on the public tip.

Storage S0 (``docs/specs/spec_storage_sync_v1.md`` §6.11, §7.2) took the
owner's vaults out of the repository: the three working vaults
(``linear_algebra``, ``probability``, ``arxiv_v2``), the early vaults
(``arxiv``, ``conic-sections``, ``law``, ``physical_therapy``) and the frozen
``linear_algebra_legacy``. Tests that read one of them for its real data run
only in the ``owner_vaults`` lane, which is skipped unless
``LEARNLOOP_OWNER_VAULTS`` names a directory holding backup-API copies of
those vaults under their old fixture names, for example::

    LEARNLOOP_OWNER_VAULTS=~/learnloop-owner-lane uv run pytest -m owner_vaults

Never point it at a live vault: some of these tests read a vault in place.
Make the copies with ``learnloop.db.copies.copy_tree_with_databases`` (or
``scripts/s0_landing.py copy-out``). S3's synthetic builders bring each test's
default-lane coverage back.

Fixture walkers (every fixture database must upgrade, replay, ...) walk the
databases git tracks under ``fixtures/`` and, in the owner lane, the copies
too, so an untracked leftover in a checkout never changes what the default
lane tests.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[1]
FIXTURES = REPOSITORY / "fixtures"
OWNER_VAULTS_ENV = "LEARNLOOP_OWNER_VAULTS"

#: Every vault S0 removed from ``fixtures/``, by its old fixture name.
OWNER_VAULT_NAMES = (
    "linear_algebra",
    "probability",
    "arxiv_v2",
    "arxiv",
    "conic-sections",
    "law",
    "physical_therapy",
    "linear_algebra_legacy",
)
#: The owner's working vaults (the three the old CLAUDE.md named).
WORKING_VAULT_NAMES = ("linear_algebra", "probability", "arxiv_v2")

OWNER_VAULTS_SKIP_REASON = (
    f"owner_vaults lane: set {OWNER_VAULTS_ENV}=<directory of backup-API copies of the owner's vaults> "
    "to run it (spec_storage_sync_v1 §7.2)"
)

owner_vaults = pytest.mark.owner_vaults


def owner_vaults_root() -> Path | None:
    """The directory of owner-vault copies, or None when the lane is off."""
    value = os.environ.get(OWNER_VAULTS_ENV, "").strip()
    if not value:
        return None
    return Path(value).expanduser().resolve()


def owner_vault(name: str) -> Path:
    """Path of the copy of one owner vault.

    Module-level constants call this at import, so it never raises: with the
    lane off it names a path that does not exist (the tests using it carry the
    ``owner_vaults`` marker and are skipped before they run).
    """
    if name not in OWNER_VAULT_NAMES:
        raise ValueError(f"{name!r} is not one of the owner vaults S0 removed: {OWNER_VAULT_NAMES}")
    root = owner_vaults_root()
    if root is None:
        return REPOSITORY / ".owner-vaults-lane-is-off" / name
    return root / name


def _tracked_fixture_paths() -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z", "--", "fixtures"],
            capture_output=True, check=True, cwd=REPOSITORY,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


def tracked_fixture_files(pattern: str) -> list[Path]:
    """Files git tracks under ``fixtures/`` whose path matches a glob pattern.

    Outside a git checkout it falls back to the files on disk, minus the
    owner vaults' old directories.
    """
    tracked = _tracked_fixture_paths()
    if tracked is None:
        return sorted(
            path for path in FIXTURES.rglob("*")
            if path.is_file() and path.match(pattern)
            and path.relative_to(FIXTURES).parts[0] not in OWNER_VAULT_NAMES
        )
    return sorted(
        REPOSITORY / path for path in tracked
        if (REPOSITORY / path).match(pattern) and (REPOSITORY / path).is_file()
    )


def tracked_fixture_databases() -> list[Path]:
    """Every ``fixtures/<name>/state.sqlite`` that git tracks.

    Outside a git checkout (an exported tarball) it falls back to the
    directories on disk, minus the owner vaults' old names.
    """
    tracked = _tracked_fixture_paths()
    if tracked is None:
        return sorted(
            path for path in FIXTURES.glob("*/state.sqlite") if path.parent.name not in OWNER_VAULT_NAMES
        )
    return sorted(
        REPOSITORY / path
        for path in tracked
        if path.count("/") == 2 and path.endswith("/state.sqlite") and (REPOSITORY / path).exists()
    )


def owner_vault_databases() -> list[Path]:
    """The owner-lane copies' databases (empty when the lane is off)."""
    root = owner_vaults_root()
    if root is None or not root.is_dir():
        return []
    return sorted(
        root / name / "state.sqlite" for name in OWNER_VAULT_NAMES if (root / name / "state.sqlite").exists()
    )


def fixture_database_params() -> list:
    """Walker parameters: tracked fixture databases, then the owner-lane copies (marked)."""
    params = [pytest.param(path, id=path.parent.name) for path in tracked_fixture_databases()]
    params += [
        pytest.param(path, id=f"owner:{path.parent.name}", marks=owner_vaults)
        for path in owner_vault_databases()
    ]
    return params


def fixture_vault_params() -> list:
    """Like :func:`fixture_database_params`, but the vault directories."""
    return [
        pytest.param(param.values[0].parent, id=param.id, marks=param.marks)
        for param in fixture_database_params()
    ]


def working_vault_params() -> list:
    """The three working vaults as parameters in the owner lane."""
    return [pytest.param(name, id=name, marks=owner_vaults) for name in WORKING_VAULT_NAMES]
