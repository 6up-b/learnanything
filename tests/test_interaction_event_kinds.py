"""Every kind the code can write through ``append_interaction_event`` is one the table accepts (G2-R37).

``interaction_events.kind`` carries a CHECK; a kind outside it raises ``sqlite3.IntegrityError``, and a best-effort
wrapper around the write used to swallow that, so the event was silently never recorded (``probe_reminted`` and
``rung_variant_requested`` were dropped this way). This reads the source, not a run: every kind reaching
``append_interaction_event`` -- a literal at a direct call, a module constant (``CHAT_TOOL_CALL_KIND``), or a literal
passed to a function that forwards its own ``kind`` parameter (``log_interaction_event``, ``item_authoring._record``,
found by the scan, not listed by hand) -- must be in the vocabulary of the newest migration that defines the CHECK.
A kind the scan cannot resolve to a string fails too, so a new indirection is either resolvable or looked at.
"""

from __future__ import annotations

import ast
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pytest

from learnloop.clock import FrozenClock
from learnloop.content.authoring import item_authoring
from tests.helpers import NOW, create_basic_vault, seed_due_item

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = (ROOT / "src" / "learnloop", ROOT / "src" / "learnloop_sidecar")
MIGRATIONS = ROOT / "migrations"
WRITER = "append_interaction_event"

_KIND_CHECK = re.compile(r"CREATE TABLE interaction_events\w*\s*\(.*?\bkind\s+TEXT\s+NOT\s+NULL\s+CHECK\s*\(\s*kind\s+IN\s*\(",
                         re.DOTALL | re.IGNORECASE)


def _strip_sql_comments(text: str) -> str:
    return re.sub(r"--[^\n]*", "", text)


def _reader_client_kinds() -> set[str]:
    from learnloop.reader.reader_inquiry import CLIENT_ACTIVITY_KINDS

    return {*CLIENT_ACTIVITY_KINDS, "reader_action_invoked"}


#: Call sites whose kind is a variable the code validates against a vocabulary before the write: (file, the kind
#: expression) -> that vocabulary. Every kind it admits is checked like a literal.
DYNAMIC_KIND_SITES = {
    # record_activity's _validate admits CLIENT_ACTIVITY_KINDS and reader_action_invoked only.
    ("src/learnloop/reader/reader_inquiry.py", "kind"): _reader_client_kinds,
}


def kind_vocabulary() -> tuple[str, frozenset[str]]:
    """The kinds the newest migration defining ``interaction_events.kind``'s CHECK accepts, and that migration."""

    for path in sorted(MIGRATIONS.glob("*.sql"), reverse=True):
        text = _strip_sql_comments(path.read_text(encoding="utf-8"))
        match = _KIND_CHECK.search(text)
        if match is None:
            continue
        depth, end = 1, match.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            end += 1
        return path.name, frozenset(re.findall(r"'([^']*)'", text[match.end():end]))
    raise AssertionError("no migration defines interaction_events.kind's CHECK")


@dataclass(frozen=True)
class _Module:
    path: Path
    tree: ast.Module
    constants: dict[str, str]
    imports: dict[str, str]  # local name -> imported name


def _modules() -> list[_Module]:
    modules = []
    for source_root in SOURCE_ROOTS:
        for path in sorted(source_root.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            constants: dict[str, str] = {}
            imports: dict[str, str] = {}
            for node in tree.body:
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        for target in targets:
                            if isinstance(target, ast.Name):
                                constants[target.id] = node.value.value
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports[alias.asname or alias.name] = alias.name
            modules.append(_Module(path, tree, constants, imports))
    return modules


def _callee(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return None


#: A forwarder's kind parameter: its name and, when it can be passed positionally, its position.
_Param = tuple[str, "int | None"]


def _kind_argument(call: ast.Call, param: _Param) -> ast.expr | None:
    name, position = param
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    if position is not None and len(call.args) > position:
        return call.args[position]
    return None


def _enclosing_functions(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _forwarders(modules: list[_Module]) -> dict[tuple[Path, str], _Param]:
    """Functions that pass their own ``kind`` parameter on to the writer (or to another forwarder): (module, name)
    -> that parameter. A fixed point, so a forwarder of a forwarder is found too."""

    forwarders: dict[tuple[Path, str], _Param] = {}
    changed = True
    while changed:
        changed = False
        for module in modules:
            for function in _enclosing_functions(module.tree):
                key = (module.path, function.name)
                if key in forwarders:
                    continue
                positional = [arg.arg for arg in [*function.args.posonlyargs, *function.args.args]]
                params = {*positional, *(arg.arg for arg in function.args.kwonlyargs)}
                for call in (n for n in ast.walk(function) if isinstance(n, ast.Call)):
                    target = _target(module, call, forwarders)
                    if target is None:
                        continue
                    kind = _kind_argument(call, target)
                    if isinstance(kind, ast.Name) and kind.id in params:
                        index = positional.index(kind.id) if kind.id in positional else None
                        if index is not None and function.args.args and function.args.args[0].arg == "self":
                            index -= 1
                        forwarders[key] = (kind.id, index)
                        changed = True
                        break
    return forwarders


def _target(module: _Module, call: ast.Call, forwarders: dict[tuple[Path, str], _Param]) -> _Param | None:
    """The kind parameter of the writer or forwarder this call reaches, or None when it reaches neither."""

    name = _callee(call)
    if name is None:
        return None
    if name == WRITER:
        return ("kind", None)
    if not isinstance(call.func, ast.Name):
        return None
    for (path, forwarder), param in forwarders.items():
        if path == module.path and name == forwarder:
            return param
        if not forwarder.startswith("_") and module.imports.get(name) == forwarder:
            return param
    return None


def _calls_with_enclosing_function(tree: ast.Module):
    """Every call in the module with the name of its innermost enclosing function (None at module level)."""

    def visit(node: ast.AST, enclosing: str | None):
        for child in ast.iter_child_nodes(node):
            inner = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else enclosing
            if isinstance(child, ast.Call):
                yield child, enclosing
            yield from visit(child, inner)

    yield from visit(tree, None)


def _resolve(module: _Module, modules_by_constant: dict[str, set[str]], expr: ast.expr) -> set[str] | None:
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return {expr.value}
    if isinstance(expr, ast.Name):
        if expr.id in module.constants:
            return {module.constants[expr.id]}
        imported = module.imports.get(expr.id)
        if imported is not None and imported in modules_by_constant:
            return modules_by_constant[imported]
    return None


def written_kinds() -> tuple[dict[str, list[str]], list[str]]:
    """Every kind the source passes towards the writer (kind -> call sites), and the call sites whose kind the scan
    could not resolve."""

    modules = _modules()
    forwarders = _forwarders(modules)
    modules_by_constant: dict[str, set[str]] = {}
    for module in modules:
        for name, value in module.constants.items():
            modules_by_constant.setdefault(name, set()).add(value)

    kinds: dict[str, list[str]] = {}
    unresolved: list[str] = []
    for module in modules:
        own_params = {name: param for (path, name), param in forwarders.items() if path == module.path}
        for call, enclosing in _calls_with_enclosing_function(module.tree):
            target = _target(module, call, forwarders)
            if target is None:
                continue
            kind = _kind_argument(call, target)
            site = f"{module.path.relative_to(ROOT)}:{call.lineno}"
            if kind is None:
                unresolved.append(f"{site} (no kind=)")
                continue
            if isinstance(kind, ast.Name) and enclosing is not None and own_params.get(enclosing, (None,))[0] == kind.id:
                continue  # a forwarder passing its own parameter on: its callers' kinds are checked instead
            resolved = _resolve(module, modules_by_constant, kind)
            if resolved is None:
                validated = DYNAMIC_KIND_SITES.get((module.path.relative_to(ROOT).as_posix(), ast.unparse(kind)))
                resolved = set(validated()) if validated is not None else None
            if resolved is None:
                unresolved.append(f"{site} ({ast.unparse(kind)})")
                continue
            for value in resolved:
                kinds.setdefault(value, []).append(site)
    for value in kinds:
        kinds[value] = sorted(set(kinds[value]))
    return kinds, sorted(set(unresolved))


def test_every_written_interaction_event_kind_is_in_the_tables_vocabulary():
    migration, vocabulary = kind_vocabulary()
    kinds, _ = written_kinds()
    outside = {kind: sites for kind, sites in kinds.items() if kind not in vocabulary}
    assert not outside, (
        f"kinds written to interaction_events that {migration}'s CHECK refuses "
        f"(the write raises IntegrityError): {outside}"
    )


def test_every_kind_passed_towards_the_writer_resolves_to_a_string():
    _, unresolved = written_kinds()
    assert not unresolved, f"kinds the scan cannot resolve (make them a literal or a module constant): {unresolved}"


def test_the_scan_sees_the_known_writers():
    """The scan is not vacuous: it reaches a direct literal, a constant, both forwarders' callers."""

    kinds, _ = written_kinds()
    assert "retirement_reason" in kinds  # direct literal
    assert "chat_tool_call" in kinds  # CHAT_TOOL_CALL_KIND, imported
    assert "learner_item_edited" in kinds  # through item_authoring._record
    assert "reader_action_invoked" in kinds  # through log_interaction_event (sidecar)
    _, vocabulary = kind_vocabulary()
    assert {"chat_tool_call", "learner_item_split"} <= vocabulary



def test_a_best_effort_provenance_write_still_raises_a_refused_kind(tmp_path):
    """The best-effort wrappers keep swallowing an ordinary failure, but not the table refusing the row: that is
    the defect the scan above guards, and it must surface wherever the scan cannot see it."""

    repo = seed_due_item(create_basic_vault(tmp_path / "vault"))
    clock = FrozenClock(NOW)
    with pytest.raises(sqlite3.IntegrityError):
        item_authoring._record(repo, kind="not_a_kind", practice_item_id="pi_x", detail={}, clock=clock)
    item_authoring._record(repo, kind="learner_item_edited", practice_item_id="pi_x", detail={}, clock=clock)
    with repo.connection() as connection:
        kinds = [row[0] for row in connection.execute("SELECT kind FROM interaction_events WHERE subject_id = 'pi_x'")]
    assert kinds == ["learner_item_edited"]
