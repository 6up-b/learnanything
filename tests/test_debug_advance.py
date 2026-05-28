from __future__ import annotations

import json

from typer.testing import CliRunner

from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository

from tests.helpers import NOW, create_basic_vault


def test_debug_advance_shifts_practice_item_state_timestamps(tmp_path):
    vault_root = tmp_path / "vault"
    paths = create_basic_vault(vault_root)
    repository = Repository(paths.sqlite_path)
    repository.upsert_practice_item_state(
        "pi_svd_define_001",
        difficulty=1.0,
        stability=3.0,
        retrievability=0.9,
        due_at="2026-05-25T12:00:00Z",
        last_attempt_at="2026-05-22T12:00:00Z",
        clock=FrozenClock(NOW),
    )
    runner = CliRunner()

    result = runner.invoke(app, ["debug-advance", "3", "--vault", str(vault_root), "--json"])

    state = repository.practice_item_state("pi_svd_define_001")
    payload = json.loads(result.output)["debug_advance"]
    assert result.exit_code == 0, result.output
    assert state is not None
    assert state.due_at == "2026-05-22T12:00:00Z"
    assert state.last_attempt_at == "2026-05-19T12:00:00Z"
    assert state.updated_at == "2026-05-16T12:00:00Z"
    assert payload["days"] == 3
    assert payload["shifted_fields"]["practice_item_state.due_at"] == 1
    assert payload["shifted_fields"]["practice_item_state.last_attempt_at"] == 1


def test_debug_advance_rejects_non_positive_days(tmp_path):
    vault_root = tmp_path / "vault"
    create_basic_vault(vault_root)
    runner = CliRunner()

    result = runner.invoke(app, ["debug-advance", "0", "--vault", str(vault_root), "--json"])

    assert result.exit_code == 1
    assert json.loads(result.output)["error"] == "invalid_debug_advance"
