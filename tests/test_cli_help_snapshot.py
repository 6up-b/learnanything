"""The CLI's contract: what a script may call stays callable with the same meaning, and every command prints its help.

This replaces a sha256 of every command's rendered help. That test failed on any reworded sentence and was re-recorded
in 211 commits, so a failure meant "regenerate", and a rename went through the same way. ``tests/cli_surface.json`` pins
each command's parameters as a contract: positional order, type, default and whether required. A compatible addition
needs no edit: a new command, a new optional option, an optional positional at the end, a new alias, a widened choice, or
a required parameter made optional. An incompatible change fails until the file is edited on purpose in the same
commit: something removed, a reordered positional, a changed type or default, something newly required. Help prose is
never pinned.
"""

from __future__ import annotations

import enum
import json
from pathlib import Path, PurePath
import sys
from typing import Any

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


def _plain(value: Any) -> Any:
    """A parameter default as JSON. A computed default is pinned as computed: its value may depend on the machine."""

    if isinstance(value, enum.Enum):
        return _plain(value.value)
    if isinstance(value, PurePath):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return f"<{'computed' if callable(value) else type(value).__name__}>"


def _contract(parameter: Any) -> dict[str, Any]:
    kind = parameter.type
    contract = {"type": kind.name, "required": bool(parameter.required), "default": _plain(parameter.default),
                "nargs": parameter.nargs}
    if getattr(kind, "choices", None) is not None:
        contract["choices"] = sorted(str(_plain(choice)) for choice in kind.choices)
    if parameter.param_type_name == "option":
        contract["multiple"] = bool(parameter.multiple)
        contract["flag"] = bool(parameter.is_flag)
    return contract


def _surface() -> dict[str, dict[str, Any]]:
    surface: dict[str, dict[str, Any]] = {}
    for path, command in _command_paths(get_command(app)):
        arguments: list[dict[str, Any]] = []
        options: dict[str, dict[str, Any]] = {}
        for parameter in command.params:
            if parameter.param_type_name == "option":
                for flag in (*parameter.opts, *parameter.secondary_opts):
                    options[flag] = _contract(parameter)
            else:
                arguments.append({"name": parameter.name, **_contract(parameter)})
        surface[" ".join(path) or "<root>"] = {"arguments": arguments, "options": options}
    return surface


def _changed_meaning(name: str, was: dict[str, Any], now: dict[str, Any]) -> list[str]:
    problems = []
    if now["required"] and not was["required"]:
        problems.append(f"{name}: newly required")
    for field in ("type", "default", "nargs", "multiple", "flag"):
        if was.get(field) != now.get(field):
            problems.append(f"{name}: {field} was {was.get(field)!r}, now {now.get(field)!r}")
    lost = set(was.get("choices") or ()) - set(now.get("choices") or ())
    if was.get("choices") is not None and lost:
        problems.append(f"{name}: choices removed: {sorted(lost)}")
    return problems


def _incompatibilities(pinned: dict[str, dict[str, Any]], current: dict[str, dict[str, Any]]) -> list[str]:
    problems: list[str] = []
    for command, contract in pinned.items():
        if command not in current:
            problems.append(f"{command}: removed")
            continue
        now = current[command]
        was_arguments, now_arguments = contract["arguments"], now["arguments"]
        for position, was in enumerate(was_arguments):
            label = f"{command}: positional {position + 1} ({was['name']})"
            if position >= len(now_arguments):
                problems.append(f"{label}: removed")
            elif now_arguments[position]["name"] != was["name"]:
                problems.append(f"{label}: is now {now_arguments[position]['name']}")
            else:
                problems.extend(_changed_meaning(label, was, now_arguments[position]))
        problems.extend(f"{command}: new positional {added['name']} is required"
                        for added in now_arguments[len(was_arguments):] if added["required"])
        for flag, was in contract["options"].items():
            if flag not in now["options"]:
                problems.append(f"{command} {flag}: removed")
            else:
                problems.extend(_changed_meaning(f"{command} {flag}", was, now["options"][flag]))
        problems.extend(f"{command} {flag}: new option is required" for flag, added in now["options"].items()
                        if flag not in contract["options"] and added["required"])
    return problems


def test_no_command_or_parameter_changed_incompatibly() -> None:
    pinned = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
    problems = _incompatibilities(pinned, _surface())
    assert not problems, "incompatible CLI changes (edit tests/cli_surface.json only if deliberate):\n" + "\n".join(problems)


def test_the_surface_pins_the_commands_a_learner_runs() -> None:
    """Guards the file itself: an emptied surface would pass the test above."""

    pinned = json.loads(SURFACE_PATH.read_text(encoding="utf-8"))
    assert len(pinned) > 200
    assert {"--vault", "--fix-state", "--json"} <= set(pinned["doctor"]["options"])
    assert pinned["doctor"]["options"]["--fix-state"]["flag"] is True
    assert {"upgrade", "rebuild", "config effective"} <= set(pinned)


def _option(**changes: Any) -> dict[str, Any]:
    return {"type": "text", "required": False, "default": None, "nargs": 1, "multiple": False, "flag": False, **changes}


def _argument(name: str, **changes: Any) -> dict[str, Any]:
    return {"name": name, "type": "text", "required": True, "default": None, "nargs": 1, **changes}


_PINNED = {"run": {"arguments": [_argument("first"), _argument("second")],
                   "options": {"--mode": _option(type="choice", choices=["a", "b"], default="a"), "--x": _option()}}}


def _changed(**fields: Any) -> dict[str, Any]:
    return {"run": {**json.loads(json.dumps(_PINNED["run"])), **fields}}


@pytest.mark.parametrize("current", [
    _changed(),
    {**_changed(), "new command": {"arguments": [_argument("required")], "options": {"--y": _option(required=True)}}},
    _changed(options={**_PINNED["run"]["options"], "--new": _option(), "--x-alias": _option()}),
    _changed(arguments=[*_PINNED["run"]["arguments"], _argument("third", required=False)]),
    _changed(arguments=[_argument("first", required=False), _argument("second")]),
    _changed(options={**_PINNED["run"]["options"], "--mode": _option(type="choice", choices=["a", "b", "c"], default="a")}),
], ids=["same", "new command", "new option and alias", "new optional positional", "required made optional", "wider choice"])
def test_a_compatible_addition_needs_no_edit(current):
    assert _incompatibilities(_PINNED, current) == []


@pytest.mark.parametrize(("current", "named"), [
    ({}, "run: removed"),
    (_changed(arguments=[_argument("second"), _argument("first")]), "is now second"),
    (_changed(arguments=[_argument("first")]), "positional 2 (second): removed"),
    (_changed(arguments=[_argument("first", type="integer"), _argument("second")]), "type was"),
    (_changed(arguments=[*_PINNED["run"]["arguments"], _argument("third")]), "new positional third is required"),
    (_changed(options={"--mode": _PINNED["run"]["options"]["--mode"]}), "--x: removed"),
    (_changed(options={**_PINNED["run"]["options"], "--x": _option(default="y")}), "default was"),
    (_changed(options={**_PINNED["run"]["options"], "--x": _option(type="integer")}), "type was"),
    (_changed(options={**_PINNED["run"]["options"], "--x": _option(required=True)}), "newly required"),
    (_changed(options={**_PINNED["run"]["options"], "--new": _option(required=True)}), "new option is required"),
    (_changed(options={**_PINNED["run"]["options"], "--mode": _option(type="choice", choices=["a"], default="a")}),
     "choices removed"),
], ids=["removed command", "reordered positional", "removed positional", "positional type", "new required positional",
        "removed option", "default", "option type", "newly required", "new required option", "narrowed choice"])
def test_an_incompatible_change_fails_and_says_which(current, named):
    assert any(named in problem for problem in _incompatibilities(_PINNED, current))


def test_help_prose_is_not_part_of_the_contract() -> None:
    assert '"help"' not in SURFACE_PATH.read_text(encoding="utf-8")


#: The commands split into this many tests, every command in exactly one, so no single test is the suite's floor.
HELP_SHARDS = 6


@pytest.mark.slow
@pytest.mark.parametrize("shard", range(HELP_SHARDS))
def test_every_command_prints_its_help(shard: int) -> None:
    """Help rendering runs each command's Typer and Rich formatting (about 50 s for all of them, so the commands are
    dealt round-robin into ``HELP_SHARDS`` tests): a bad signature or bad markup in one fails here. The rendered text
    itself isn't pinned."""

    runner = CliRunner()
    paths = list(_command_paths(get_command(app)))
    assert len(paths) >= HELP_SHARDS
    for path, _command in paths[shard::HELP_SHARDS]:
        result = runner.invoke(app, [*path, "--help"], prog_name="learnloop", terminal_width=120, color=False)
        name = " ".join(path) or "<root>"
        assert result.exit_code == 0, f"{name}: {result.output}"
        assert "Usage" in result.output and (not path or path[-1] in result.output), f"{name}: {result.output}"


if __name__ == "__main__" and sys.argv[1:] == ["--write"]:
    SURFACE_PATH.write_text(json.dumps(_surface(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
