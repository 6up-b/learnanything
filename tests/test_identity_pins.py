"""Identity pins (refactor step K0): no refactor moves a compared identity at a fixed input without saying so.

Three checks, one design (``tests/identity_pins_helpers.py``; record ``docs/reviews/refactor-k0.md``):

- **Pins.** Each compared identity (cache and reuse keys, manifest and version hashes, seeds, the structured prompts
  whose text keys reuse) is computed through its production path at a fixed input and held to its digest in
  ``tests/goldens/identities.toml``.
- **Shapes.** Each type a compared identity dumps whole is held to its field names, annotations and defaults in
  ``tests/goldens/identity_shapes.toml``: adding, removing or renaming a field, or changing a default, fails here
  even where the fixed inputs would not show it.
- **Coverage.** An AST scan of ``src/``: a ``model_dump``, ``asdict``, ``model_json_schema`` or ``json.dumps`` of a
  config whose value reaches a hash, seed, manifest or structured-prompt call in the same function must be a
  registered source of a pinned site, or be listed as provenance-only with a reason. It cannot see a dump returned
  to another function that hashes it (the synthesis scope, ``router_settings``, ``prompt_safe``'s automatic dumps of
  a model placed in a prompt): the pins cover those.

A failure says which site moved, what compares it and what moving it costs, and the two ways out: keep the bytes
(``RETIRED_FIELDS``, ``exclude_if``, an explicit identity view) or bump deliberately under
``docs/algorithm-change-playbook.md`` and regenerate in that commit: ``uv run python tests/test_identity_pins.py
--write``. Regeneration is never automatic.
"""

from __future__ import annotations

import ast
from functools import cache
from pathlib import Path
import sys
import tomllib

import pytest

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.ast_cache import python_files, source_ast, source_text
from tests.identity_pins_helpers import (
    IDENTITIES_PATH,
    IDENTITY_SITES,
    KEEP_OR_BUMP,
    PROVENANCE_ONLY,
    REGENERATE,
    REPO,
    SHAPES_PATH,
    current_digests,
    current_shapes,
    digest,
    pin_names,
    site_for,
)

IDENTITIES_HEADER = (
    "# Compared identities at fixed inputs, one sha256 per pin (tests/identity_pins_helpers.py), sorted.\n"
    "# Generated; never edit by hand. Regenerate only with a deliberate bump (docs/algorithm-change-playbook.md when\n"
    f"# persisted meaning changes; the reason goes in the landing note): {REGENERATE}\n"
)
SHAPES_HEADER = (
    "# The shape of every type a compared identity dumps whole: field, annotation, default (and retired fields),\n"
    "# with the sites that dump it (tests/identity_pins_helpers.py SHAPE_ROOTS). Generated; never edit by hand.\n"
    f"# Regenerate only with a deliberate bump: {REGENERATE}\n"
)


def _golden_identities() -> dict[str, str]:
    return tomllib.loads(IDENTITIES_PATH.read_text(encoding="utf-8")) if IDENTITIES_PATH.exists() else {}


def _golden_shapes() -> dict[str, dict]:
    return tomllib.loads(SHAPES_PATH.read_text(encoding="utf-8")) if SHAPES_PATH.exists() else {}


def _site_message(pin: str) -> str:
    site, _ = site_for(pin)
    return (f"Identity {pin} ({site.title}) moved at a fixed input.\n"
            f"  computed by: {', '.join(site.sources)}\n"
            f"  compared by: {site.consumer}\n"
            f"  if it moves: {site.consequence}\n{KEEP_OR_BUMP}")


@pytest.mark.parametrize("pin", pin_names())
def test_identity_pin(pin: str) -> None:
    golden = _golden_identities()
    assert pin in golden, f"{pin} has no pin: a new site? Record it with `{REGENERATE}`."
    _site, compute = site_for(pin)
    assert digest(compute()) == golden[pin], _site_message(pin)


def test_the_goldens_pin_exactly_the_sites() -> None:
    stale = sorted(set(_golden_identities()) - set(pin_names()))
    assert not stale, f"pins with no site any more: {stale}. A site removed on purpose: `{REGENERATE}`."


def _shape_message(name: str, golden: dict, now: dict) -> str:
    before, after = golden.get("fields", []), now["fields"]
    removed = [line for line in before if line not in after]
    added = [line for line in after if line not in before]
    return (f"The shape of {name}, which compared identities dump whole, changed.\n"
            f"  dumped by sites: {', '.join(now['sites'])} (tests/identity_pins_helpers.py IDENTITY_SITES)\n"
            f"  gone or changed: {removed}\n  new or changed: {added}\n"
            "A field added, removed or renamed, or a default changed, moves every whole dump of this type unless the "
            f"site keeps its bytes.\n{KEEP_OR_BUMP}")


@pytest.mark.parametrize("name", sorted(_golden_shapes()))
def test_identity_shape(name: str) -> None:
    now = current_shapes()
    assert name in now, (f"{name} is no longer dumped by a pinned site (or was renamed): "
                         f"{_shape_message(name, _golden_shapes()[name], {'fields': [], 'sites': []})}")
    assert now[name]["fields"] == _golden_shapes()[name]["fields"], _shape_message(name, _golden_shapes()[name],
                                                                                   now[name])


def test_every_whole_dumped_type_has_a_shape_pin() -> None:
    missing = sorted(set(current_shapes()) - set(_golden_shapes()))
    assert not missing, f"types dumped whole into a compared identity with no shape pin: {missing}. `{REGENERATE}`"


# -- coverage ---------------------------------------------------------------------------------------------------

SRC = REPO / "src"
#: Calls that make an identity: hashing, seeding, a manifest or a structured prompt.
SINK_NAMES = frozenset({
    "content_key", "content_hash", "canonical_hash", "render_structured_prompt", "build_manifest",
    "compute_manifest_hash", "checkpoint_key", "generator_key", "seed_for", "numeric_seed",
})
SINK_SUFFIXES = ("hash", "sha1", "sha256", "sha", "digest", "seed", "fingerprint", "content_id")
_MUTATORS = frozenset({"update", "append", "extend", "setdefault", "add", "insert"})


def _callee(node: ast.Call) -> str | None:
    func = node.func
    return func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else None


def _is_sink(node: ast.Call) -> bool:
    func, name = node.func, _callee(node)
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "hashlib":
        return True
    return name is not None and (name in SINK_NAMES or any(
        name == suffix or name.endswith("_" + suffix) for suffix in SINK_SUFFIXES))


def _mentions_config(node: ast.AST) -> bool:
    return any((isinstance(n, ast.Attribute) and n.attr == "config") or (isinstance(n, ast.Name) and n.id == "config")
               for n in ast.walk(node))


def _is_dump(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    name = _callee(node)
    if name in {"model_dump", "model_json_schema", "asdict"}:
        return True
    func = node.func
    return (name == "dumps" and isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
            and func.value.id == "json" and bool(node.args) and _mentions_config(node.args[0]))


def _bases(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple | ast.List):
        return [name for element in target.elts for name in _bases(element)]
    if isinstance(target, ast.Starred):
        return _bases(target.value)
    while isinstance(target, ast.Subscript | ast.Attribute):
        target = target.value
    return [target.id] if isinstance(target, ast.Name) else []


def _own_nodes(function: ast.AST) -> list[ast.AST]:
    nested = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
    out, stack = [], list(ast.iter_child_nodes(function))
    while stack:
        node = stack.pop()
        out.append(node)
        stack.extend(child for child in ast.iter_child_nodes(node) if not isinstance(child, nested))
    return out


def _dump_reaches_sink(function: ast.AST) -> bool:
    """A dump's value reaches a sink call's arguments in ``function``: directly, or through names assigned from it
    (or mutated with it), followed to a fixed point. Same function only; order and branches are ignored."""

    nodes = _own_nodes(function)
    if not any(_is_dump(node) for node in nodes):
        return False

    def summary(parts: list[ast.AST]) -> tuple[frozenset[str], bool]:
        """The names an expression reads and whether it holds a dump itself."""
        inner = [n for part in parts for n in ast.walk(part)]
        return frozenset(n.id for n in inner if isinstance(n, ast.Name)), any(_is_dump(n) for n in inner)

    flows: list[tuple[list[str], frozenset[str], bool]] = []  # (names written, names read, holds a dump)
    sinks: list[tuple[frozenset[str], bool]] = []
    for node in nodes:
        if isinstance(node, ast.Assign | ast.AnnAssign | ast.AugAssign) and node.value is not None:
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            flows.append(([name for target in targets for name in _bases(target)], *summary([node.value])))
        elif isinstance(node, ast.Call):
            arguments = [*node.args, *(k.value for k in node.keywords)]
            if isinstance(node.func, ast.Attribute) and node.func.attr in _MUTATORS:
                flows.append((_bases(node.func.value), *summary(arguments)))
            if _is_sink(node):
                sinks.append(summary(arguments))
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for written, read, dump in flows:
            if (dump or read & tainted) and not set(written) <= tainted:
                tainted.update(written)
                changed = True
    return any(dump or read & tainted for read, dump in sinks)


def _functions(tree: ast.Module):
    def visit(node: ast.AST, prefix: str):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                yield f"{prefix}{child.name}", child
                yield from visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, ast.ClassDef):
                yield from visit(child, f"{prefix}{child.name}.")
    yield from visit(tree, "")


#: A file none of these appear in has no dump the scan would see, so it is never parsed.
_DUMP_TOKENS = ("model_dump", "asdict", "model_json_schema", "json.dumps")


@cache
def flagged_functions() -> frozenset[str]:
    """``path::qualname`` of every function under ``src/`` whose dump reaches an identity sink."""

    found = set()
    for path in python_files(SRC):
        text = source_text(path)
        if not any(token in text for token in _DUMP_TOKENS):
            continue
        relative = path.relative_to(REPO).as_posix()
        found.update(f"{relative}::{name}" for name, function in _functions(source_ast(text))
                     if _dump_reaches_sink(function))
    return frozenset(found)


def _registered() -> set[str]:
    return {source for site in IDENTITY_SITES for source in site.sources}


def test_every_dump_beside_an_identity_is_pinned_or_provenance_only() -> None:
    unregistered = sorted(flagged_functions() - _registered() - set(PROVENANCE_ONLY))
    assert not unregistered, (
        "A model_dump / asdict / model_json_schema / json.dumps(config) reaches a hash, seed, manifest or structured "
        f"prompt in: {unregistered}.\nIf the value is compared later (a cache, reuse or dedupe key, a version, a "
        "seed), pin it: add an IdentitySite (production path, fixed input) to tests/identity_pins_helpers.py and "
        f"record it with `{REGENERATE}`. If it is stored only as provenance, or is a prompt that should change with "
        "its fields, add it to PROVENANCE_ONLY with the reason.")


def test_the_provenance_allowlist_has_no_stale_entries() -> None:
    flagged = flagged_functions()
    stale = sorted(set(PROVENANCE_ONLY) - flagged)
    assert not stale, f"PROVENANCE_ONLY entries the scan no longer flags (moved, renamed or fixed): {stale}"
    pinned = sorted(set(PROVENANCE_ONLY) & _registered())
    assert not pinned, f"both pinned and listed provenance-only: {pinned}"


def test_every_registered_source_exists() -> None:
    missing = []
    for source in sorted(_registered()):
        path, _, qualname = source.partition("::")
        names = {name for name, _function in _functions(source_ast(source_text(REPO / path)))}
        if qualname not in names:
            missing.append(source)
    assert not missing, f"IdentitySite sources that no longer exist (renamed or moved): {missing}"


def test_an_identity_view_leaves_out_an_added_field_and_refuses_a_removed_one() -> None:
    from pydantic import BaseModel

    from learnloop.config.retired import identity_view

    class Section(BaseModel):
        enabled: bool = True
        top_k: int = 5
        added_later: int = 3

    assert identity_view(Section(), ("enabled", "top_k")) == {"enabled": True, "top_k": 5}
    with pytest.raises(KeyError, match="RETIRED_FIELDS"):
        identity_view(Section(), ("enabled", "removed"))


def test_the_scan_sees_the_shapes_it_is_meant_to_see() -> None:
    def flags(code: str) -> bool:
        return _dump_reaches_sink(source_ast(code).body[0])

    assert flags("def f(c):\n    return content_key(c.model_dump())")
    assert flags("def f(c):\n    d = {'x': c.model_dump()}\n    d2 = d\n    return hashlib.sha256(d2)")
    assert flags("def f(c):\n    d = {}\n    d.update(x=asdict(c))\n    return _hash(d)")
    assert flags("def f(vault):\n    return _sha256(json.dumps(vault.config.router))")
    assert flags("def f(ctx):\n    return render_structured_prompt('t', 'v', {'context': asdict(ctx)})")
    assert not flags("def f(c):\n    stored = c.model_dump()\n    return content_key({'id': c.id})")
    assert not flags("def f(c):\n    return json.dumps(c.items)")
    # Its limit: the dump is returned and hashed by the caller (the pins cover those).
    assert not flags("def f(c):\n    return {'w': c.weights.model_dump()}")


def _write() -> None:
    lines = [IDENTITIES_HEADER]
    lines += [f'"{pin}" = "{value}"\n' for pin, value in current_digests().items()]
    IDENTITIES_PATH.write_text("".join(lines), encoding="utf-8")
    out = [SHAPES_HEADER]
    for name, shape in current_shapes().items():
        out.append(f'\n["{name}"]\nsites = [{", ".join(_toml_string(s) for s in shape["sites"])}]\nfields = [\n')
        out += [f"  {_toml_string(line)},\n" for line in shape["fields"]]
        out.append("]\n")
    SHAPES_PATH.write_text("".join(out), encoding="utf-8")


def _toml_string(value: str) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


if __name__ == "__main__" and sys.argv[1:] == ["--write"]:
    _write()
