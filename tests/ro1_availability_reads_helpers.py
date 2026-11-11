"""What other test files use from ``tests/test_ro1_availability_reads.py``, kept here because a test file never
imports another (``tests/test_test_layout.py``; refactor step T1)."""

from __future__ import annotations

from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.goals.exam_seeding import seed_exam_attempts
from learnloop.vault.loader import load_vault
from learnloop.vault.paths import VaultPaths

from tests.helpers import append_config_toml, set_algorithm_version
from tests.exam_seeding_helpers import _exam_vault, _outcomes


#: Codex's reproduction: the exam happened on May 1 and was imported on May 19 ...
IMPORTED_AT = datetime(2026, 5, 19, 15, 30, 7, tzinfo=UTC)
#: ... and a decision on May 5 could not have known it.
CUTOFF = "2026-05-05T09:00:00Z"
AFTER = "2026-05-20T00:00:00Z"
LO = "lo_svd_definition"


def _seeded(tmp_path, version: str, toml: str | None):
    vault_root, _loaded, repository = _exam_vault(tmp_path)
    set_algorithm_version(VaultPaths(vault_root, load_vault(vault_root).config), version)
    if toml:
        append_config_toml(vault_root, toml)
    seed_exam_attempts(load_vault(vault_root), repository, outcomes=_outcomes(), clock=FrozenClock(IMPORTED_AT))
    return load_vault(vault_root), repository
