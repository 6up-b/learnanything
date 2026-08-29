from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from learnloop.bootstrap import BootstrapError, create_vault
from learnloop.cli import app
from learnloop.clock import FrozenClock
from learnloop.db.repositories import Repository
from learnloop.vault.loader import init_vault
from learnloop.vault.yaml_io import read_yaml


CLOCK = FrozenClock(datetime(2026, 5, 19, tzinfo=UTC))


def test_init_creates_vault_and_applies_migration(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault, clock=CLOCK)

    assert (vault / "learnloop.toml").exists()
    assert (vault / "AGENTS.md").exists()
    assert (vault / "concepts" / "concepts.yaml").exists()
    assert (vault / "errors" / "error_types.yaml").exists()
    assert (vault / "state.sqlite").exists()
    for unused_directory in [
        "prompts",
        "sessions",
        "exports",
        ".learnloop/backups",
        ".learnloop/session-checkpoints",
    ]:
        assert not (vault / unused_directory).exists()

    with sqlite3.connect(vault / "state.sqlite") as connection:
        row = connection.execute("SELECT version, name FROM schema_migrations").fetchone()
    assert row == (1, "initial")


def test_bootstrap_seeds_subject_and_starting_level(tmp_path):
    vault = tmp_path / "vault"

    result = create_vault(
        vault,
        subject="Linear Algebra",
        starting_level="some_exposure",
        level_note="Returning after a long break.",
        clock=CLOCK,
    )

    assert result.root == vault.resolve()
    assert result.subject_id == "linear-algebra"
    assert (vault / "subjects" / "linear-algebra" / "subject.md").exists()
    assert read_yaml(vault / "profile" / "learner.yaml") == {
        "schema_version": 1,
        "starting_level": "some_exposure",
        "level_note": "Returning after a long break.",
        "updated_at": "2026-05-19T00:00:00Z",
    }
    claims = Repository(vault / "state.sqlite").learner_claims()
    assert len(claims) == 1
    assert claims[0]["source"] == "init_wizard"
    assert claims[0]["claimed_level"] == pytest.approx(0.35)


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"starting_level": "expert"}, "invalid_starting_level"),
        ({"subject": "---"}, "invalid_subject"),
    ],
)
def test_bootstrap_validates_request_before_writing(tmp_path, kwargs, code):
    vault = tmp_path / "vault"

    with pytest.raises(BootstrapError) as exc_info:
        create_vault(vault, **kwargs)

    assert exc_info.value.code == code
    assert not vault.exists()


def test_cli_init_refuses_populated_non_vault_without_force(tmp_path):
    vault = tmp_path / "notes"
    vault.mkdir()
    unrelated = vault / "keep.txt"
    unrelated.write_text("keep me", encoding="utf-8")
    runner = CliRunner()

    refused = runner.invoke(app, ["init", str(vault)])

    assert refused.exit_code == 2
    assert "not empty and is not a LearnLoop vault" in refused.output
    assert unrelated.read_text(encoding="utf-8") == "keep me"
    assert not (vault / "learnloop.toml").exists()

    forced = runner.invoke(app, ["init", str(vault), "--force"])

    assert forced.exit_code == 0, forced.output
    assert unrelated.read_text(encoding="utf-8") == "keep me"
    assert (vault / "learnloop.toml").exists()


def test_cli_invalid_starting_level_leaves_no_partial_vault(tmp_path):
    vault = tmp_path / "vault"

    result = CliRunner().invoke(
        app,
        ["init", str(vault), "--starting-level", "expert"],
    )

    assert result.exit_code == 2
    assert "Unknown starting level 'expert'" in result.output
    assert not vault.exists()


def test_bootstrap_completes_partial_vault_without_touching_config(tmp_path):
    vault = tmp_path / "vault"
    init_vault(vault, clock=CLOCK)
    config_path = vault / "learnloop.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8") + "\n# user-owned sentinel\n",
        encoding="utf-8",
    )
    before = config_path.read_bytes()
    missing = vault / "concepts" / "concepts.yaml"
    missing.unlink()

    result = create_vault(vault, clock=CLOCK)

    assert result.root == vault.resolve()
    assert missing.exists()
    assert config_path.read_bytes() == before
