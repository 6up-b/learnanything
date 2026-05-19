from __future__ import annotations

from typer.testing import CliRunner

from learnloop.cli import app

MVP_COMMANDS = [
    "init",
    "add-subject",
    "add-note",
    "propose",
    "proposals",
    "accept",
    "reject",
    "attempt",
    "review",
    "why",
    "show",
    "doctor",
    "today",
]


def test_entrypoint_lists_every_mvp_command():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in MVP_COMMANDS:
        assert command in result.output


def test_console_script_target_imports():
    # Mirrors the [project.scripts] entry: learnloop = learnloop.cli:app
    from learnloop.cli import app as resolved

    assert resolved is app
