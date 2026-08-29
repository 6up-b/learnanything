from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from typer.main import get_command
from typer.testing import CliRunner

from learnloop.cli import app


SNAPSHOT_PATH = Path(__file__).with_name("cli_help_snapshot.json")


def _command_paths(command: object, path: tuple[str, ...] = ()):
    yield path
    commands = getattr(command, "commands", None)
    if isinstance(commands, dict):
        for name, child in commands.items():
            yield from _command_paths(child, (*path, name))


def _help_snapshot() -> dict[str, dict[str, str | int]]:
    command = get_command(app)
    runner = CliRunner()
    snapshot: dict[str, dict[str, str | int]] = {}
    for path in _command_paths(command):
        result = runner.invoke(
            app,
            [*path, "--help"],
            prog_name="learnloop",
            terminal_width=120,
            color=False,
        )
        assert result.exit_code == 0, f"{' '.join(path) or '<root>'}: {result.output}"
        raw = result.output.encode("utf-8")
        snapshot[" ".join(path) or "<root>"] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    return snapshot


def test_recursive_cli_help_is_byte_identical_to_pre_split_oracle() -> None:
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert _help_snapshot() == expected


if __name__ == "__main__" and sys.argv[1:] == ["--write"]:
    SNAPSHOT_PATH.write_text(
        json.dumps(_help_snapshot(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
