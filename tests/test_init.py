from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from learnloop.clock import FrozenClock
from learnloop.vault.loader import init_vault


def test_init_creates_vault_and_applies_migration(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault, clock=FrozenClock(datetime(2026, 5, 19, tzinfo=UTC)))

    assert (vault / "learnloop.toml").exists()
    assert (vault / "AGENTS.md").exists()
    assert (vault / "concepts" / "concepts.yaml").exists()
    assert (vault / "errors" / "error_types.yaml").exists()
    assert (vault / "state.sqlite").exists()

    with sqlite3.connect(vault / "state.sqlite") as connection:
        row = connection.execute("SELECT version, name FROM schema_migrations").fetchone()
    assert row == (1, "initial")
