"""Static contract checks for the four-layer desktop RPC bridge.

The bridge is intentionally thin, but every operation is named independently in
TypeScript, the Tauri handler list, Rust forwarding code, and Python decorators.
These checks turn omissions at any one layer into a test failure instead of a
learner-visible "command not found" or "unknown method" error.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import learnloop_sidecar.handlers  # noqa: F401 -- populate METHOD_REGISTRY
from learnloop_sidecar.registry import METHOD_REGISTRY


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "apps" / "learnloop-tauri" / "src" / "api" / "client.ts"
COMMANDS = ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src" / "commands.rs"
MAIN = ROOT / "apps" / "learnloop-tauri" / "src-tauri" / "src" / "main.rs"
HANDLERS = ROOT / "src" / "learnloop_sidecar" / "handlers"


def _typescript_calls(source: str) -> set[str]:
    """Read the first string argument from each local ``call<T>(...)`` use."""

    names: set[str] = set()
    for match in re.finditer(r"\bcall(?=\s*[<(])", source):
        cursor = match.end()
        while source[cursor].isspace():
            cursor += 1
        if source[cursor] == "<":
            depth = 0
            while cursor < len(source):
                if source[cursor] == "<":
                    depth += 1
                elif source[cursor] == ">":
                    depth -= 1
                    if depth == 0:
                        cursor += 1
                        break
                cursor += 1
            while source[cursor].isspace():
                cursor += 1
        if source[cursor] != "(":
            continue
        cursor += 1
        while source[cursor].isspace():
            cursor += 1
        if source[cursor] not in {'"', "'"}:
            continue
        quote = source[cursor]
        end = source.find(quote, cursor + 1)
        if end != -1:
            names.add(source[cursor + 1 : end])
    return names


def _tauri_handlers(source: str) -> set[str]:
    marker = ".invoke_handler(tauri::generate_handler!["
    body = source.split(marker, 1)[1].split("])", 1)[0]
    return set(re.findall(r"^\s*([a-z][a-z0-9_]*)\s*,?\s*$", body, re.MULTILINE))


def _rust_commands(source: str) -> tuple[set[str], dict[str, str]]:
    functions = set(re.findall(r"\bpub async fn ([a-z][a-z0-9_]*)\s*\(", source))
    passthroughs = {
        command: method
        for command, method in re.findall(
            r"\b(?:p2_|sidecar_)?passthrough!\(\s*([a-z][a-z0-9_]*)\s*,\s*\"([a-z0-9_.]+)\"",
            source,
        )
    }
    return functions | set(passthroughs), passthroughs


def _decorated_methods() -> tuple[set[str], dict[str, list[Path]]]:
    methods: set[str] = set()
    locations: dict[str, list[Path]] = {}
    for path in HANDLERS.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "method"
                    and decorator.args
                    and isinstance(decorator.args[0], ast.Constant)
                    and isinstance(decorator.args[0].value, str)
                ):
                    name = decorator.args[0].value
                    methods.add(name)
                    locations.setdefault(name, []).append(path)
    return methods, locations


def test_every_frontend_call_is_registered_with_tauri() -> None:
    client_calls = _typescript_calls(CLIENT.read_text(encoding="utf-8"))
    tauri_handlers = _tauri_handlers(MAIN.read_text(encoding="utf-8"))

    assert client_calls
    assert client_calls <= tauri_handlers, sorted(client_calls - tauri_handlers)


def test_tauri_handler_list_matches_rust_command_declarations() -> None:
    tauri_handlers = _tauri_handlers(MAIN.read_text(encoding="utf-8"))
    rust_commands, _passthroughs = _rust_commands(COMMANDS.read_text(encoding="utf-8"))

    assert tauri_handlers == rust_commands, {
        "missing_declaration": sorted(tauri_handlers - rust_commands),
        "not_registered": sorted(rust_commands - tauri_handlers),
    }


def test_every_tauri_command_reaches_a_registered_sidecar_method() -> None:
    tauri_handlers = _tauri_handlers(MAIN.read_text(encoding="utf-8"))
    _rust_commands_set, passthroughs = _rust_commands(COMMANDS.read_text(encoding="utf-8"))
    sidecar_methods, _locations = _decorated_methods()

    # Vault selection is Rust orchestration over initialize + load_vault, not a
    # one-to-one sidecar method. All other public commands follow their own name
    # or declare an explicit dotted-method mapping in the passthrough macro.
    expected_methods = {
        passthroughs.get(command, command)
        for command in tauri_handlers
        if command != "select_vault"
    }
    assert expected_methods <= sidecar_methods, sorted(expected_methods - sidecar_methods)


def test_every_decorated_handler_is_loaded_once() -> None:
    decorated, locations = _decorated_methods()
    duplicates = {
        name: [str(path.relative_to(ROOT)) for path in paths]
        for name, paths in locations.items()
        if len(paths) > 1
    }

    assert not duplicates
    assert decorated == set(METHOD_REGISTRY), {
        "handler_module_not_loaded": sorted(decorated - set(METHOD_REGISTRY)),
        "runtime_only_registration": sorted(set(METHOD_REGISTRY) - decorated),
    }
