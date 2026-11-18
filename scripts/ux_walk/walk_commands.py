"""The Tauri command table, read from the Rust shell's own source at bridge start.

``apps/learnloop-tauri/src-tauri/src/commands.rs`` defines every command the
frontend can ``invoke``; ``main.rs`` registers them. Most forward one sidecar
method. Copying ~300 mappings by hand would drift the first time a command is
added, so the bridge parses the two files instead and refuses to start when a
registered command has a body it cannot classify (tests/test_ux_walk_harness.py
fails the same way).

Three shapes:

- ``passthrough``: ``sidecar_passthrough!(fn, "method")``. The frontend sends
  ``{input}``; the sidecar receives ``input`` unchanged.
- ``forward``: a hand-written ``#[tauri::command]`` whose body is one
  ``blocking_sidecar_call(sidecar, "method", json!({...}))``. Tauri hands the
  Rust parameters over by their camelCase names; the ``json!`` literal says
  which sidecar key each one becomes (``.unwrap_or(x)`` gives a default).
- ``special``: a body that does more than forward (vault selection, the
  isolated CLI call). The bridge carries an emulation for each by name.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS_RS = ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src" / "commands.rs"
MAIN_RS = ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src" / "main.rs"

#: Commands whose Rust body is not a plain forward, with what the bridge does instead.
SPECIAL_COMMANDS: dict[str, str] = {
    "select_vault": "emulated: restarts the sidecar on the chosen folder (only folders inside the walk "
                    "directory), then returns the vault summary, as SidecarManager::select_vault does",
    "run_cli_command": "emulated: forwards to the primary sidecar; `populate-goal` runs there too (the shell "
                       "uses a second, isolated sidecar) and is followed by reload_vault, as the shell does",
}
#: Forwards with a side effect in the shell besides the sidecar call.
WATCHING_COMMANDS = frozenset({"load_vault", "select_vault"})

_PASSTHROUGH = re.compile(r'sidecar_passthrough!\(\s*(\w+)\s*,\s*"([^"]+)"\s*\)', re.S)
_COMMAND = re.compile(
    r"#\[tauri::command\]\s*pub async fn (\w+)\s*\((.*?)\)\s*->[^{]*\{(.*?)\n\}", re.S
)
_FORWARD = re.compile(r'blocking_sidecar_call\(\s*sidecar\s*,\s*"([^"]+)"\s*,\s*json!\((.*?)\)\s*,?\s*\)', re.S)
_PAIR = re.compile(r'"(\w+)"\s*:\s*([a-z_][a-z0-9_]*)(?:\.unwrap_or\(([^)]*)\))?')
_HANDLER_LIST = re.compile(r"generate_handler!\[(.*?)\]", re.S)


class MissingArgument(ValueError):
    """Tauri's own refusal of a call that lacks a required argument (a plain string to the frontend)."""

    def __init__(self, command: str, key: str):
        super().__init__(f"invalid args `{key}` for command `{command}`: command {command} missing required key {key}")


@dataclass(frozen=True)
class Argument:
    sidecar_key: str
    frontend_key: str
    default: object = None
    #: Tauri refuses the call when a non-``Option`` parameter is missing.
    required: bool = True


@dataclass(frozen=True)
class Command:
    name: str
    kind: str  # passthrough | forward | special | unknown
    method: str | None = None
    arguments: tuple[Argument, ...] = field(default_factory=tuple)
    watches_vault: bool = False

    def params_for(self, args: dict) -> object:
        """The sidecar params for one ``invoke(name, args)``, as the Rust command builds them.

        Raises :class:`MissingArgument` where Tauri would refuse the call before it ran."""

        if self.kind == "passthrough":
            if args.get("input") is None:
                raise MissingArgument(self.name, "input")
            return args["input"]
        if self.kind == "forward":
            params = {}
            for argument in self.arguments:
                value = args.get(argument.frontend_key)
                if value is None and argument.required:
                    raise MissingArgument(self.name, argument.frontend_key)
                params[argument.sidecar_key] = argument.default if value is None else value
            return params
        raise ValueError(f"{self.name} is not a forward")


def camel(name: str) -> str:
    """Tauri's argument naming: the Rust parameter ``session_id`` arrives as ``sessionId``."""

    head, *rest = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in rest)


def _default(raw: str | None) -> object:
    if not raw:
        return None
    return json.loads(raw.strip())


def _parameters(signature: str) -> dict[str, bool]:
    """Each non-state parameter and whether Tauri requires it (not an ``Option``)."""

    names: dict[str, bool] = {}
    for part in re.split(r",(?![^<]*>)", signature):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, kind = (piece.strip() for piece in part.split(":", 1))
        if kind.startswith("State<"):
            continue
        names[name] = not kind.startswith("Option<")
    return names


def parse_commands(commands_rs: str) -> dict[str, Command]:
    """Every command defined in ``commands.rs``, classified."""

    table: dict[str, Command] = {}
    for name, method in _PASSTHROUGH.findall(commands_rs):
        table[name] = Command(name, "passthrough", method)
    for name, signature, body in _COMMAND.findall(commands_rs):
        parameters = _parameters(signature)
        if name in SPECIAL_COMMANDS:
            table[name] = Command(name, "special", watches_vault=name in WATCHING_COMMANDS)
            continue
        code = re.sub(r"//[^\n]*", "", body)
        watches = "watcher.watch" in code
        if watches:
            # load_vault's shape: remember the manager, forward, watch the resolved vault, return.
            code = re.sub(r"let manager = sidecar\.inner\(\)\.clone\(\);", "", code)
            code = re.sub(r"watcher\.watch\(manager\.resolved_vault_path\(\)\);", "", code)
            code = re.sub(r"let result = (.*?)\?;\s*Ok\(result\)", r"\1", code, flags=re.S)
        forwards = _FORWARD.findall(code)
        # A forward's whole body is the one call: anything else (a native step, a second call) needs an emulation.
        if len(forwards) != 1 or not re.fullmatch(r"\s*blocking_sidecar_call\(.*\)\s*\.await\s*", code, re.S):
            table[name] = Command(name, "unknown")
            continue
        method, literal = forwards[0]
        arguments = tuple(
            Argument(key, camel(parameter), _default(default), parameters.get(parameter, True))
            for key, parameter, default in _PAIR.findall(literal)
        )
        mapped = {camel(parameter) for parameter in parameters}
        if {argument.frontend_key for argument in arguments} != mapped:
            # A parameter the json! literal drops or a key it invents: not a plain forward.
            table[name] = Command(name, "unknown")
            continue
        if watches and name not in WATCHING_COMMANDS:
            table[name] = Command(name, "unknown")
            continue
        table[name] = Command(name, "forward", method, arguments, watches_vault=watches)
    return table


def registered_commands(main_rs: str) -> list[str]:
    """The names ``main.rs`` registers with ``generate_handler!``, in order."""

    match = _HANDLER_LIST.search(main_rs)
    if match is None:
        raise ValueError("main.rs has no generate_handler! list")
    return [name.strip() for name in match.group(1).split(",") if name.strip()]


def load_table(commands_path: Path = COMMANDS_RS, main_path: Path = MAIN_RS) -> dict[str, Command]:
    """The registered commands, each classified; raises when one cannot be served."""

    defined = parse_commands(commands_path.read_text(encoding="utf-8"))
    registered = registered_commands(main_path.read_text(encoding="utf-8"))
    problems = [name for name in registered if name not in defined]
    problems += [name for name in registered if name in defined and defined[name].kind == "unknown"]
    if problems:
        raise ValueError(
            "commands.rs has commands the walk bridge cannot classify (a new shape needs an emulation in "
            f"scripts/ux_walk/walk_commands.py): {', '.join(sorted(set(problems)))}"
        )
    return {name: defined[name] for name in registered}


def counts(table: dict[str, Command]) -> dict[str, int]:
    tally: dict[str, int] = {}
    for command in table.values():
        tally[command.kind] = tally.get(command.kind, 0) + 1
    return tally


def fidelity_markdown(table: dict[str, Command]) -> str:
    """The command half of the fidelity table, for the record: ``python walk_commands.py``."""

    lines = ["| Command | Sidecar method | Fidelity |", "|---|---|---|"]
    for name, command in table.items():
        if command.kind == "special":
            lines.append(f"| `{name}` | — | {SPECIAL_COMMANDS[name]} |")
        elif command.watches_vault:
            lines.append(f"| `{name}` | `{command.method}` | exact forward; the bridge's watcher then follows "
                         "the vault (polling, below) |")
    forwards = [f"`{name}`" + (f" (`{command.method}`)" if command.method != name else "")
                for name, command in table.items() if command.kind in ("passthrough", "forward")
                and not command.watches_vault]
    lines.append("")
    lines.append(f"Exact forwards ({len(forwards)}), each to the sidecar method of the same name unless shown: "
                 + ", ".join(forwards) + ".")
    return "\n".join(lines)


if __name__ == "__main__":
    loaded = load_table()
    print(counts(loaded))
    print(fidelity_markdown(loaded))
