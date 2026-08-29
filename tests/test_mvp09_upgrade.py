"""mvp-0.9 is an explicit successor upgrade on the P0 projection namespace."""

from __future__ import annotations

from typer.testing import CliRunner

from learnloop.clock import FrozenClock
from learnloop.cli import app
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.ops.vault_upgrade import upgrade_to_mvp09
from learnloop.vault.loader import load_vault

from tests.helpers import NOW, create_basic_vault, set_algorithm_version


def test_upgrade_to_mvp09_flips_rebuilds_and_preserves_raw_history(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")
    repository = Repository(paths.sqlite_path)
    with connect(paths.sqlite_path) as connection:
        before = connection.execute(
            "SELECT id, created_at FROM practice_attempts ORDER BY id"
        ).fetchall()
        before = [tuple(row) for row in before]

    result = upgrade_to_mvp09(paths.root, clock=FrozenClock(NOW))

    assert result.upgraded is True
    assert result.from_version == "mvp-0.8"
    assert result.to_version == "mvp-0.9"
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.9"
    latest = repository.latest_derived_state_rebuild()
    assert latest is not None
    assert latest["algorithm_version"] == "mvp-0.9"
    with connect(paths.sqlite_path) as connection:
        after = connection.execute(
            "SELECT id, created_at FROM practice_attempts ORDER BY id"
        ).fetchall()
    assert [tuple(row) for row in after] == before


def test_upgrade_to_mvp09_is_immediate_successor_only(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.7")
    refused = upgrade_to_mvp09(paths.root, clock=FrozenClock(NOW))
    assert refused.upgraded is False
    assert "only 'mvp-0.8'" in refused.problems[0]

    set_algorithm_version(paths, "mvp-0.9")
    already = upgrade_to_mvp09(paths.root, clock=FrozenClock(NOW))
    assert already.upgraded is False
    assert already.problems == ["vault is already mvp-0.9"]


def test_upgrade_command_defaults_to_current_mvp09_target(tmp_path):
    paths = create_basic_vault(tmp_path / "vault")
    set_algorithm_version(paths, "mvp-0.8")

    result = CliRunner().invoke(app, ["upgrade", "--vault", str(paths.root)])

    assert result.exit_code == 0, result.output
    assert "mvp-0.8 -> mvp-0.9" in result.output
    assert load_vault(paths.root).config.algorithms.algorithm_version == "mvp-0.9"
