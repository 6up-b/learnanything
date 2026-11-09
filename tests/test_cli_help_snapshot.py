"""The CLI's surface: what a script may call stays callable, and every command can print its help.

This replaces a sha256 of every command's rendered help. That test failed on any reworded sentence and was re-recorded
in 211 commits, so a failure meant "regenerate", and a rename went through the same way. ``tests/cli_surface.json``
pins names instead: removing or renaming a command or an option fails, because a script or the desktop could depend on
it; adding one doesn't. A deliberate removal deletes its entry from the file in the same commit.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from learnloop.cli import app

SURFACE_PATH = Path(__file__).with_name("cli_surface.json")


def _command_paths(command: object, path: tuple[str, ...] = ()):
    yield path, command
    commands = getattr(command, "commands", None)
    if isinstance(commands, dict):
        for name, child in commands.items():
            yield from _command_paths(child, (*path, name))


def _surface() -> dict[str, list[str]]:
    surface: dict[str, list[str]] = {}
    for path, command in _command_paths(get_command(app)):
        names: list[str] = []
        for parameter in command.params:
            if parameter.param_type_name == "option":
                names.extend(parameter.opts)
                names.extend(parameter.secondary_opts)
            else:
                names.append(f"<{parameter.name}>")
        surface[" ".join(path) or "<root>"] = sorted(names)
    return surface


def test_no_command_or_option_disappeared() -> None:
    pinned = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
    current = _surface()
    missing_commands = sorted(set(pinned) - set(current))
    assert not missing_commands, f"commands removed or renamed: {missing_commands}"
    missing_options = {
        command: sorted(set(names) - set(current[command]))
        for command, names in pinned.items()
        if set(names) - set(current[command])
    }
    assert not missing_options, f"options removed or renamed: {missing_options}"


def test_the_surface_pins_the_commands_a_learner_runs() -> None:
    """Guards the file itself: an emptied surface would pass the test above."""

    pinned = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
    assert len(pinned) > 200
    assert "--vault" in pinned["doctor"] and "--fix-state" in pinned["doctor"]
    assert {"upgrade", "rebuild", "config effective"} <= set(pinned)


@pytest.mark.slow
def test_every_command_prints_its_help() -> None:
    """Help rendering runs each command's Typer and Rich formatting (about 60 s for all of them): a bad signature or
    bad markup in one fails here. The rendered text itself isn't pinned."""

    runner = CliRunner()
    for path, _command in _command_paths(get_command(app)):
        result = runner.invoke(app, [*path, "--help"], prog_name="learnloop", terminal_width=120, color=False)
        name = " ".join(path) or "<root>"
        assert result.exit_code == 0, f"{name}: {result.output}"
        assert "Usage" in result.output and (not path or path[-1] in result.output), f"{name}: {result.output}"


if __name__ == "__main__" and sys.argv[1:] == ["--write"]:
    SURFACE_PATH.write_text(json.dumps(_surface(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
