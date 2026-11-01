"""Reader RW5d P2b: the ``manim`` tier's program, ``ManimFigureV1``, and its declared-function checks.

A Manim figure (spec_reader_show_me_figures_v1 §9b.1, §9b.3, §9b.4) is the
concept animation pipeline's scene contract (``ManimAnimation``: the scene
code, its class, a title and the narration) plus what code can check:

* ``functions``: top-level pure ``def``s in the scene code (``math`` and
  ``numpy`` only), each with its arguments' ranges;
* ``claims`` over them: ``equals`` (the function equals an expression in the
  figure grammar over its arguments) and ``invariant`` (``finite``,
  ``nonnegative``, ``bounded``) on the grid of each argument's min, midpoint
  and max;
* ``plotted_from``: where the scene draws from a declared function, checked by
  AST (the function is an argument of a plot call), so a check line may say
  *the curve is drawn from f*.

**Extraction** (:func:`extract_functions`): code keeps, by AST, only the
declared top-level ``def``s and the module constants they read, with imports
limited to ``math`` and ``numpy``; a function that needs anything else (a
Manim name, ``self``, an undeclared helper, an import of its own) is **not
checkable**: its claims are dropped from the check list, never failed
(G-SM26). The extracted module never names ``manim``: the checks run in a
separate sandboxed ``python`` (:mod:`learnloop.content.authoring.pf_sandbox`,
the concept pipeline's bubblewrap profile with rlimits), and the grammar
oracle compares in this process (:func:`check_claims`).

Nothing here renders, calls a model or touches the vault.
"""

from __future__ import annotations

import ast
import itertools
import json
import math
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures.sketch import CLAIM_REL_TOL, SKETCH_MAX_CLAIM_WORK, expression_steps, impersonates

MANIM_FIG_VERSION = "manim-fig-v1"
#: keep (operational): declared functions per figure (check work, check lines).
MAX_FUNCTIONS = 4
#: keep (operational): arguments per declared function (3 grid values each: at most 81 points).
MAX_FUNCTION_ARGS = 4
#: keep (operational): claims per figure.
MAX_FIGURE_CLAIMS = 8
#: keep (operational): ``plotted_from`` entries per figure.
MAX_PLOTTED = 8
#: keep (display): a title's and a narration's length (the transcript is the video's text alternative).
MAX_TITLE = 120
MAX_NARRATION = 4_000
#: keep (operational): the declared-function check's sandbox wall clock and memory.
FUNCTION_CHECK_SECONDS = 30
FUNCTION_CHECK_MEMORY_MB = 1024
#: keep (machine safety, Codex review F2): the most grammar-expression steps
#: the claim oracle may take over one figure's claims, metered as they run
#: (``grammar.Meter``): the sketch verifier's cap, reused.
MAX_CLAIM_WORK = SKETCH_MAX_CLAIM_WORK
#: keep (machine safety, Codex review F2): the wall clock of one figure's
#: whole check (the sandboxed run and the oracle), as the sketch verifier's
#: (``sketch.SKETCH_VERIFY_SECONDS``); past it the claims fail as too slow.
CHECK_SECONDS = 60.0
#: keep (operational): how often a long oracle phase calls its ``interrupt``
#: hook (the rich job's heartbeat, where a cancel is noticed), at most.
INTERRUPT_SECONDS = 1.0
#: How many metered steps pass between the oracle's looks at the clock (about
#: a millisecond), as the sketch verifier's.
_TICK_WORK = 4_096
CLAIM_KINDS = ("equals", "invariant")
INVARIANT_PROPERTIES = ("finite", "nonnegative", "bounded")
#: The names a declared function may read besides its arguments, the module's
#: math/numpy names, its constants and other checkable declared functions.
SAFE_BUILTINS = frozenset({"abs", "min", "max", "round", "pow", "float", "int", "sum", "range", "len",
                           "enumerate", "zip", "list", "tuple", "bool", "True", "False", "None"})
#: Manim's plotting entry points a ``plotted_from`` entry may name the function
#: in, each with the keyword of its function argument (else the first
#: positional one). Only that argument counts (Codex review F5): a name in
#: ``x_range`` or a colour is not the curve's function.
PLOT_FUNCTION_ARGS: dict[str, str] = {
    "plot": "function", "plot_parametric_curve": "function", "plot_polar_graph": "r_func",
    "get_graph": "function", "plot_implicit_curve": "func", "plot_surface": "function",
    "ParametricFunction": "function", "FunctionGraph": "function", "ImplicitFunction": "func",
    "ParametricSurface": "func", "Surface": "func", "ArrowVectorField": "func", "StreamLines": "func",
}
PLOT_CALLS = frozenset(PLOT_FUNCTION_ARGS)
_ALLOWED_MODULES = ("math", "numpy")


class ManimFigureError(ValueError):
    """A Manim figure outside its contract; ``problems`` says why (sent back to the author)."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = [str(problem) for problem in problems][:20]
        super().__init__("; ".join(self.problems) or "invalid Manim figure")


@dataclass(frozen=True)
class Argument:
    name: str
    low: float
    high: float


@dataclass(frozen=True)
class Function:
    name: str
    args: tuple[Argument, ...]


@dataclass(frozen=True)
class Claim:
    kind: str
    function: str
    expr: str | None = None
    prop: str | None = None
    bound: float | None = None


@dataclass(frozen=True)
class ManimFigure:
    scene_code: str
    scene_class: str
    title: str
    narration_md: str
    functions: tuple[Function, ...] = ()
    claims: tuple[Claim, ...] = ()
    plotted_from: tuple[str, ...] = ()

    def declared(self) -> dict[str, Any]:
        return {
            "functions": [{"name": f.name, "args": [{"name": a.name, "min": a.low, "max": a.high} for a in f.args],
                           "shape": "scalar"} for f in self.functions],
            "claims": [{k: v for k, v in (("kind", c.kind), ("function", c.function), ("expr", c.expr),
                                          ("property", c.prop), ("bound", c.bound)) if v is not None}
                       for c in self.claims],
            "plotted_from": [{"function": name} for name in self.plotted_from],
        }


def _number(value: Any, what: str, problems: list[str]) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        problems.append(f"{what} must be a finite number")
        return None
    return float(value)


def parse_declared(raw: Any) -> tuple[tuple[Function, ...], tuple[Claim, ...], tuple[str, ...], list[str]]:
    """The declared functions, claims and ``plotted_from`` entries of
    ``declared_json`` (JSON text or a mapping): what is well formed, and the
    problems of what is not. An empty declaration is fine (*not checked*)."""

    problems: list[str] = []
    if raw in (None, ""):
        return (), (), (), problems
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, ValueError):
        return (), (), (), ["declared_json is not a JSON object"]
    if not isinstance(data, dict):
        return (), (), (), ["declared_json is not a JSON object"]
    unknown = set(data) - {"functions", "claims", "plotted_from"}
    if unknown:
        problems.append(f"declared_json has unknown keys {sorted(unknown)}")
    functions: list[Function] = []
    for index, entry in enumerate(list(data.get("functions") or ())[:MAX_FUNCTIONS + 1]):
        if index >= MAX_FUNCTIONS:
            problems.append(f"at most {MAX_FUNCTIONS} declared functions")
            break
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            problems.append(f"functions[{index}] needs a name")
            continue
        name = entry["name"]
        if not name.isidentifier() or name.startswith("_") or impersonates(name):
            problems.append(f"functions[{index}].name {name!r} is not an allowed identifier")
            continue
        if entry.get("shape", "scalar") != "scalar":
            # Series and pairs functions are drawn, not checked, in v1.
            continue
        args: list[Argument] = []
        raw_args = list(entry.get("args") or ())
        if len(raw_args) > MAX_FUNCTION_ARGS:
            problems.append(f"functions[{index}] takes at most {MAX_FUNCTION_ARGS} checked arguments")
            continue
        ok = True
        for position, arg in enumerate(raw_args):
            if not isinstance(arg, dict) or not isinstance(arg.get("name"), str) or not G.is_name(arg["name"]) \
                    or arg["name"] in G.RESERVED or impersonates(arg["name"]):
                problems.append(f"functions[{index}].args[{position}] needs a name the expression grammar allows")
                ok = False
                continue
            low = _number(arg.get("min"), f"functions[{index}].args[{position}].min", problems)
            high = _number(arg.get("max"), f"functions[{index}].args[{position}].max", problems)
            if low is None or high is None or not low < high:
                if low is not None and high is not None:
                    problems.append(f"functions[{index}].args[{position}]: min must be below max")
                ok = False
                continue
            args.append(Argument(arg["name"], low, high))
        if ok and len({a.name for a in args}) == len(args):
            functions.append(Function(name, tuple(args)))
        elif ok:
            problems.append(f"functions[{index}] repeats an argument name")
    names = {f.name for f in functions}
    claims: list[Claim] = []
    for index, entry in enumerate(list(data.get("claims") or ())[:MAX_FIGURE_CLAIMS + 1]):
        if index >= MAX_FIGURE_CLAIMS:
            problems.append(f"at most {MAX_FIGURE_CLAIMS} claims")
            break
        if not isinstance(entry, dict) or entry.get("kind") not in CLAIM_KINDS:
            problems.append(f"claims[{index}].kind must be one of {list(CLAIM_KINDS)}")
            continue
        function = entry.get("function")
        if function not in names:
            problems.append(f"claims[{index}] names {function!r}, which is not a declared scalar function")
            continue
        if entry["kind"] == "equals":
            expr = entry.get("expr")
            if not isinstance(expr, str) or not expr.strip():
                problems.append(f"claims[{index}] needs expr (the expression grammar over the function's arguments)")
                continue
            claims.append(Claim("equals", function, expr=expr.strip()[:400]))
        else:
            prop = entry.get("property")
            if prop not in INVARIANT_PROPERTIES:
                problems.append(f"claims[{index}].property must be one of {list(INVARIANT_PROPERTIES)}")
                continue
            bound = None
            if prop == "bounded":
                bound = _number(entry.get("bound"), f"claims[{index}].bound", problems)
                if bound is None or bound <= 0:
                    if bound is not None:
                        problems.append(f"claims[{index}].bound must be positive")
                    continue
            claims.append(Claim("invariant", function, prop=prop, bound=bound))
    plotted: list[str] = []
    for index, entry in enumerate(list(data.get("plotted_from") or ())[:MAX_PLOTTED]):
        name = entry.get("function") if isinstance(entry, dict) else None
        if name in names and name not in plotted:
            plotted.append(name)
        elif name not in names:
            problems.append(f"plotted_from[{index}] names {name!r}, which is not a declared scalar function")
    return tuple(functions), tuple(claims), tuple(plotted), problems


def parse_figure(output: Any) -> ManimFigure:
    """A :class:`ManimFigure` from the rich author's answer (scene fields and
    ``declared_json``), or :class:`ManimFigureError` with every problem."""

    problems: list[str] = []
    code = str(getattr(output, "scene_code", "") or "")
    if not code.strip():
        problems.append("scene_code is empty")
    scene_class = str(getattr(output, "scene_class", "") or "").strip()
    title = " ".join(str(getattr(output, "title", "") or "").split())[:MAX_TITLE]
    narration = str(getattr(output, "narration_md", "") or "").strip()[:MAX_NARRATION]
    functions, claims, plotted, declared_problems = parse_declared(getattr(output, "declared_json", ""))
    problems += declared_problems
    if problems:
        raise ManimFigureError(problems)
    return ManimFigure(code, scene_class, title, narration, functions, claims, plotted)


# ---------------------------------------------------------------------------
# Extraction (by AST: the declared defs and the constants they read)
# ---------------------------------------------------------------------------

@dataclass
class Extraction:
    #: The module the sandbox runs: math/numpy imports, constants, the checkable defs. Never names manim.
    source: str
    checkable: list[str] = field(default_factory=list)
    #: Declared functions that cannot be checked, with code's reason.
    dropped: dict[str, str] = field(default_factory=dict)


def _module_aliases(tree: ast.Module) -> tuple[dict[str, str], list[str]]:
    """Top-level ``math``/``numpy`` names (alias -> what it is) and their import lines."""

    aliases: dict[str, str] = {}
    lines: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _ALLOWED_MODULES and alias.name == root:
                    bound = alias.asname or root
                    aliases[bound] = root
                    lines.append(f"import {root} as {bound}" if alias.asname else f"import {root}")
        elif isinstance(node, ast.ImportFrom) and not node.level and (node.module or "") in _ALLOWED_MODULES:
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                aliases[bound] = f"{node.module}.{alias.name}"
                lines.append(f"from {node.module} import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
    return aliases, lines


def _bound_names(node: ast.AST) -> set[str]:
    """Names a function binds locally (its arguments, assignments, loop and comprehension targets)."""

    bound: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.arg):
            bound.add(child.arg)
        elif isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            bound.add(child.id)
    return bound


def _free_reads(node: ast.AST) -> set[str]:
    return {child.id for child in ast.walk(node) if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)}


def _forbidden_shape(node: ast.AST) -> str | None:
    for child in ast.walk(node):
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            return "it imports inside itself"
        if isinstance(child, (ast.Global, ast.Nonlocal)):
            return "it declares global or nonlocal names"
        if isinstance(child, (ast.Yield, ast.YieldFrom, ast.Await, ast.AsyncFunctionDef, ast.ClassDef)):
            return "it is not a plain function"
        if isinstance(child, ast.Attribute) and child.attr.startswith("_"):
            return f"it reads the private attribute {child.attr!r}"
    return None


_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
#: Builtins whose result is an immutable scalar (a constant built only from
#: these, literals, math and other immutable constants can't be mutated).
_SCALAR_BUILTINS = frozenset({"abs", "min", "max", "round", "pow", "float", "int", "bool", "len", "sum"})


def module_bindings(tree: ast.Module) -> Counter[str]:
    """How many times each name is bound in the module's own scope (Codex
    review F4): assignments (augmented included), deletions, defs, classes,
    imports and loop or ``with`` targets at module level, outside any def,
    lambda or class body; a name declared ``global`` anywhere counts twice
    (any function may rebind it)."""

    counts: Counter[str] = Counter()

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                counts[child.name] += 1
                for part in (*child.decorator_list, *getattr(child, "bases", ()),
                             *(k.value for k in getattr(child, "keywords", ()))):
                    visit_expr(part)
                if not isinstance(child, ast.ClassDef):
                    for default in (*child.args.defaults, *(d for d in child.args.kw_defaults if d is not None)):
                        visit_expr(default)
                continue
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    counts[alias.asname or alias.name.split(".")[0]] += 1
                continue
            visit_expr(child) if isinstance(child, ast.expr) else visit(child)

    def visit_expr(node: ast.AST) -> None:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                counts[child.id] += 1

    visit(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                counts[name] += 2
    return counts


def _root_name(node: ast.AST) -> str | None:
    while isinstance(node, (ast.Attribute, ast.Subscript, ast.Starred)):
        node = node.value
    return node.id if isinstance(node, ast.Name) else None


def _mutated_names(tree: ast.Module) -> set[str]:
    """Names whose object is mutated somewhere in the scene, in any scope
    (Codex review F4): an item or attribute assigned, augmented or deleted
    (``A[0] = 1``, ``A.x += 1``, ``del A[0]``), or a method called on it
    (``A.fill(0)``, ``L.append(1)``) or written through ``out=A``."""

    mutated: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Attribute, ast.Subscript)) and isinstance(node.ctx, (ast.Store, ast.Del)):
            name = _root_name(node)
            if name:
                mutated.add(name)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                name = _root_name(node.func.value)
                if name:
                    mutated.add(name)
            for keyword in node.keywords:
                # numpy's ``out=A`` writes into A, wherever it is called (the declared functions too).
                if keyword.arg == "out" and (name := _root_name(keyword.value)):
                    mutated.add(name)
    return mutated


def _passed_names(tree: ast.Module, skip: Sequence[ast.AST]) -> set[str]:
    """Names handed bare to a call as an argument (``g(A)``, ``g(x=A)``,
    ``g(*A)``) anywhere outside ``skip`` (the declared functions and the
    constants' own definitions): a mutable object handed to arbitrary code may
    be changed by it."""

    skipped = {id(node) for root in skip for node in ast.walk(root)}
    passed: set[str] = set()
    for node in ast.walk(tree):
        if id(node) in skipped or not isinstance(node, ast.Call):
            continue
        for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
            name = _root_name(argument)
            if name:
                passed.add(name)
    return passed


def _immutable_value(node: ast.AST, aliases: Mapping[str, str], immutable: set[str]) -> bool:
    """A constant's value can't be a mutable object: literals, arithmetic,
    tuples, ``math`` (or ``numpy`` scalar names, never calls), scalar
    builtins and other immutable constants (Codex review F4)."""

    for child in ast.walk(node):
        if isinstance(child, (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.SetComp, ast.DictComp,
                              ast.GeneratorExp, ast.Lambda, ast.NamedExpr)):
            return False
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name) and (func.id in _SCALAR_BUILTINS or aliases.get(func.id, "").startswith("math")):
                continue
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and aliases.get(func.value.id) == "math":
                continue
            return False
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            if child.id in aliases or child.id in immutable or child.id in SAFE_BUILTINS:
                continue
            return False
    return True


def extract_functions(scene_code: str, functions: Sequence[Function]) -> Extraction:
    """The checkable part of the scene (module docstring). Never raises for
    model code: what can't be extracted is dropped with a reason.

    Codex review F4: a module constant is kept only when the scene can't
    change what the declared functions read through it: bound once in the
    module's scope (no ``A += 1``, no rebinding, never ``global``), never
    mutated in any scope (no item or attribute assigned, no method called on
    it) and, when its value may be a mutable object (a ``numpy`` call, a
    list), never handed to other code as an argument. A declared function is
    also bound once (no later ``f = ...`` or second ``def f``). A function
    that reads a constant that isn't kept is not checkable."""

    try:
        tree = ast.parse(scene_code)
    except SyntaxError as exc:
        return Extraction("", [], {f.name: f"the scene does not parse ({exc.msg})" for f in functions})
    aliases, import_lines = _module_aliases(tree)
    defs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    declared = {f.name for f in functions}
    bindings = module_bindings(tree)
    mutated = _mutated_names(tree)
    # Module constants: a plain NAME = <expression over literals, math/numpy and earlier constants>.
    constants: dict[str, ast.Assign] = {}
    immutable: set[str] = set()
    unstable: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            reads = _free_reads(node.value)
            if _forbidden_shape(node.value) is None and all(
                    read in aliases or read in constants or read in SAFE_BUILTINS for read in reads):
                constants[name] = node
                if _immutable_value(node.value, aliases, immutable):
                    immutable.add(name)
                else:
                    immutable.discard(name)
            else:
                constants.pop(name, None)
    passed = _passed_names(tree, [*(defs[name] for name in declared if name in defs),
                                  *(node.value for node in constants.values())])
    for name in list(constants):
        if bindings[name] != 1:
            unstable[name] = "the scene changes it after setting it"
        elif name in mutated:
            unstable[name] = "the scene changes what it holds"
        elif name not in immutable and name in passed:
            unstable[name] = "the scene hands it (which may be changed in place) to other code"
        else:
            continue
        del constants[name]
    # A constant built from one the scene changes is not kept either.
    grew = True
    while grew:
        grew = False
        for name, node in list(constants.items()):
            bad = sorted(read for read in _free_reads(node.value) if read in unstable)
            if bad:
                unstable[name] = f"it is built from {bad[0]!r}, which the scene changes"
                del constants[name]
                grew = True
    dropped: dict[str, str] = {}
    for function in functions:
        node = defs.get(function.name)
        if node is None:
            dropped[function.name] = "it is not a top-level def in the scene"
        elif bindings[function.name] != 1:
            dropped[function.name] = "the scene binds its name more than once"
        elif node.decorator_list:
            dropped[function.name] = "it is decorated"
        elif node.args.vararg or node.args.kwarg or node.args.kwonlyargs or node.args.posonlyargs:
            dropped[function.name] = "its signature is not plain positional arguments"
        elif [a.arg for a in node.args.args] != [a.name for a in function.args]:
            dropped[function.name] = "its arguments are not the declared ones, in order"
        elif (reason := _forbidden_shape(node)) is not None:
            dropped[function.name] = reason
    # A function may call another declared function only while that one stays
    # checkable (to a fixpoint); any other free name drops it.
    changed = True
    while changed:
        changed = False
        for function in functions:
            if function.name in dropped:
                continue
            node = defs[function.name]
            free = _free_reads(node) - _bound_names(node)
            for name in sorted(free):
                if name in aliases or name in constants or name in SAFE_BUILTINS:
                    continue
                if name in declared and name not in dropped and name != function.name:
                    continue
                if name == function.name:
                    continue
                dropped[function.name] = (f"it calls {name!r}, which is not checkable" if name in declared
                                          else f"it reads {name!r}, and {unstable[name]}" if name in unstable
                                          else f"it needs {name!r}, which is neither math, numpy, a module "
                                               "constant nor another declared function")
                changed = True
                break
    checkable = [f.name for f in functions if f.name not in dropped]
    if not checkable:
        return Extraction("", [], dropped)
    body = ["# Extracted by LearnLoop: the declared functions only.", *dict.fromkeys(import_lines)]
    used = set()
    for name in checkable:
        used |= _free_reads(defs[name])
    # Constants are kept in their order, each with the constants it reads.
    needed = {name for name in constants if name in used}
    grew = True
    while grew:
        grew = False
        for name in list(needed):
            for read in _free_reads(constants[name].value):
                if read in constants and read not in needed:
                    needed.add(read)
                    grew = True
    body += [ast.unparse(node) for name, node in constants.items() if name in needed]
    body += [ast.unparse(defs[name]) for name in checkable]
    return Extraction("\n".join(body) + "\n", checkable, dropped)


# ---------------------------------------------------------------------------
# The sandboxed run and the grammar oracle
# ---------------------------------------------------------------------------

def grid(function: Function) -> list[list[float]]:
    """Each argument's min, midpoint and max, every combination (at most 81 points)."""

    axes = [[a.low, (a.low + a.high) / 2.0, a.high] for a in function.args]
    return [list(point) for point in itertools.product(*axes)] if axes else [[]]


HARNESS = '''\
import json, math, os, sys
from pathlib import Path

# One BLAS thread: numpy's OpenBLAS reserves memory per thread, past the address-space cap.
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[name] = "1"

MARKER = {marker!r}


def number(value):
    try:
        value = float(value)
    except Exception:
        return {{"error": "not a number"}}
    if math.isnan(value):
        return {{"value": "nan"}}
    if math.isinf(value):
        return {{"value": "inf" if value > 0 else "-inf"}}
    return {{"value": value}}


def main():
    workdir = Path(sys.argv[1])
    sys.path.insert(0, str(workdir))
    request = json.loads((workdir / "input.json").read_text())
    try:
        import figure_functions as module
    except Exception as exc:
        print(MARKER + json.dumps({{"error": "load: " + type(exc).__name__}}))
        return
    results = {{}}
    for name, points in request["points"].items():
        function = getattr(module, name, None)
        values = []
        for point in points:
            try:
                values.append(number(function(*point)))
            except Exception as exc:
                values.append({{"error": type(exc).__name__}})
        results[name] = values
    print(MARKER + json.dumps({{"results": results}}))


main()
'''

#: ``(module_source, points) -> {"results": {name: [{"value"| "error"}]}}`` or ``{"error": ...}``.
FunctionRunner = Callable[[str, Mapping[str, list[list[float]]]], Mapping[str, Any]]


def sandboxed_runner(module_source: str, points: Mapping[str, list[list[float]]]) -> Mapping[str, Any]:
    """Run the extracted functions in the concept pipeline's bubblewrap profile
    (:func:`learnloop.content.authoring.pf_sandbox.run_sandboxed_python`: no
    network, no home or vault, read-only system, rlimits, a wall clock);
    manim is never imported (the module names only math and numpy)."""

    from learnloop.content.authoring import pf_sandbox

    harness = HARNESS.format(marker=pf_sandbox._OUTPUT_MARKER)
    limits = pf_sandbox.SandboxLimits(cpu_seconds=FUNCTION_CHECK_SECONDS, memory_mb=FUNCTION_CHECK_MEMORY_MB,
                                      wall_seconds=FUNCTION_CHECK_SECONDS)
    try:
        result = pf_sandbox.run_sandboxed_python(harness, {"points": dict(points)},
                                                 modules={"figure_functions": module_source}, limits=limits)
    except pf_sandbox.SandboxUnavailable as exc:
        return {"error": f"sandbox unavailable: {exc}"}
    if not result.ok:
        return {"error": result.error or "the sandboxed run failed"}
    return result.output if isinstance(result.output, dict) else {"error": "unparseable output"}


@dataclass
class CheckReport:
    #: The check lines code ran (code-owned: function names, expressions, settings counts).
    checks: list[dict[str, Any]] = field(default_factory=list)
    #: Failed claims, in code's words (sent back to the author).
    failures: list[str] = field(default_factory=list)
    #: Claims dropped because their function is not checkable (G-SM26), with why.
    not_checkable: list[dict[str, str]] = field(default_factory=list)
    plotted: list[str] = field(default_factory=list)

    @property
    def failed(self) -> bool:
        return bool(self.failures)


def _value(entry: Mapping[str, Any]) -> float | None:
    raw = entry.get("value") if isinstance(entry, Mapping) else None
    if raw in ("nan", "inf", "-inf"):
        return float(raw)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    return None


def _close(value: float, expected: float) -> bool:
    """The sketch tier's tolerance (spec §9b.4: same tolerances)."""

    return math.isfinite(expected) and abs(value - expected) <= CLAIM_REL_TOL * max(1.0, abs(expected))


def _scope_binds(scope: ast.AST, name: str) -> bool:
    """``name`` is bound in this def, lambda or class (its arguments or any
    store in its body; nested scopes included, which only errs towards
    *not* recognizing a plotted function)."""

    for node in ast.walk(scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node is not scope \
                and node.name == name:
            return True
        if isinstance(node, (ast.Import, ast.ImportFrom)) and any(
                (alias.asname or alias.name.split(".")[0]) == name for alias in node.names):
            return True
    return name in _bound_names(scope)


def _function_argument(call: ast.Call, keyword: str) -> ast.AST | None:
    for item in call.keywords:
        if item.arg == keyword:
            return item.value
    return call.args[0] if call.args and not isinstance(call.args[0], ast.Starred) else None


def _draws_from(argument: ast.AST, function: str) -> bool:
    """The plot call's function argument is the module's ``function``: the
    bare name, or a lambda that calls it (and doesn't take it as an argument)."""

    if isinstance(argument, ast.Name):
        return argument.id == function
    if isinstance(argument, ast.Lambda):
        if function in _bound_names(argument):
            return False
        return any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == function
                   for node in ast.walk(argument.body))
    return False


def plotted_from_ok(scene_code: str, function: str) -> bool:
    """``function`` supplies a Manim plot call's curve (spec §9b.1,
    AST-checked; Codex review F5): it is that call's function argument
    (:data:`PLOT_FUNCTION_ARGS`), by name or inside a lambda that calls it,
    and the name there resolves to the module's ``def``: bound once in the
    module and not rebound in any def, lambda or class around the call.
    When that can't be shown, the check line keeps the function check and
    drops the curve."""

    try:
        tree = ast.parse(scene_code)
    except SyntaxError:
        return False
    if module_bindings(tree)[function] != 1 or not any(
            isinstance(node, ast.FunctionDef) and node.name == function for node in tree.body):
        return False

    def visit(node: ast.AST, scopes: tuple[ast.AST, ...]) -> bool:
        if isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
            if name in PLOT_FUNCTION_ARGS:
                argument = _function_argument(node, PLOT_FUNCTION_ARGS[name])
                if argument is not None and _draws_from(argument, function) and not any(
                        _scope_binds(scope, function) for scope in scopes):
                    return True
        inner = (*scopes, node) if isinstance(node, _SCOPES) else scopes
        return any(visit(child, inner) for child in ast.iter_child_nodes(node))

    return visit(tree, ())


class ClaimWorkExceeded(Exception):
    """The claim check passed its work cap or its wall clock (code's words in ``reason``)."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _ClaimBudget(G.Meter):
    """The oracle's limits (Codex review F2), the sketch verifier's pattern:
    every node the grammar evaluates for a claim is charged as it runs
    (:data:`MAX_CLAIM_WORK`), and every :data:`_TICK_WORK` steps the clock is
    read against the deadline of the whole check (:data:`CHECK_SECONDS`)
    and, at most every :data:`INTERRUPT_SECONDS`, the caller's ``interrupt``
    hook runs (the rich job's heartbeat, which raises when it is cancelled)."""

    def __init__(self, deadline: float, interrupt: Callable[[], None] | None) -> None:
        super().__init__(MAX_CLAIM_WORK, _TICK_WORK)
        self.deadline = deadline
        self.interrupt = interrupt
        self.last_interrupt = time.monotonic()

    def foresee(self, work: int) -> None:
        if self.used + work > self.limit:
            self._refuse(self.used + work)

    def _refuse(self, steps: int) -> None:
        raise ClaimWorkExceeded(f"the claims need more computation than checking may do (at least {steps:,} "
                                f"expression steps; at most {self.limit:,})")

    def exhausted(self) -> None:
        self._refuse(self.used)

    def checkpoint(self) -> None:
        self.tick()

    def tick(self) -> None:
        now = time.monotonic()
        if now > self.deadline:
            raise ClaimWorkExceeded(f"the claims take longer than {CHECK_SECONDS:g} s to check")
        if self.interrupt is not None and now - self.last_interrupt >= INTERRUPT_SECONDS:
            self.last_interrupt = now
            self.interrupt()


def check_claims(figure: ManimFigure, *, runner: FunctionRunner | None = None,
                 interrupt: Callable[[], None] | None = None) -> CheckReport:
    """Check the figure's declared claims (module docstring). A claim on an
    unextractable function is dropped (``not_checkable``); an expression that
    doesn't parse, a value off the expression, a non-finite value or a failed
    run is a failure (the figure gets its second attempt, then isn't shown).

    Codex review F2: the whole check has one deadline (:data:`CHECK_SECONDS`)
    and the oracle a metered work cap (:data:`MAX_CLAIM_WORK`); a claim set
    past either fails as too costly to check. ``interrupt`` is called now and
    then while the oracle runs (it may raise to stop the check)."""

    budget = _ClaimBudget(time.monotonic() + CHECK_SECONDS, interrupt)
    report = CheckReport()
    try:
        return _check_claims(figure, runner=runner, budget=budget, report=report)
    except ClaimWorkExceeded as exc:
        report.failures.append(exc.reason)
        report.checks = []
        return report


def _check_claims(figure: ManimFigure, *, runner: FunctionRunner | None, budget: _ClaimBudget,
                  report: CheckReport) -> CheckReport:
    if not figure.claims:
        return report
    extraction = extract_functions(figure.scene_code, figure.functions)
    by_name = {f.name: f for f in figure.functions}
    report.plotted = [name for name in figure.plotted_from
                      if name in extraction.checkable and plotted_from_ok(figure.scene_code, name)]
    wanted = [claim for claim in figure.claims if claim.function in extraction.checkable]
    for claim in figure.claims:
        if claim.function not in extraction.checkable:
            report.not_checkable.append({"function": claim.function,
                                         "reason": extraction.dropped.get(claim.function, "not checkable")})
    if not wanted:
        return report
    compiled: dict[int, G.Node] = {}
    for index, claim in enumerate(wanted):
        if claim.kind != "equals":
            continue
        try:
            node = G.parse(str(claim.expr))
            G.check_names(node, known=frozenset(a.name for a in by_name[claim.function].args),
                          definitions={})
        except G.GrammarError as exc:
            report.failures.append(f"the claim on {claim.function} has an expression the grammar refuses: {exc}")
            continue
        compiled[index] = node
    if report.failures:
        return report
    points = {name: grid(by_name[name]) for name in dict.fromkeys(claim.function for claim in wanted)}
    # An early refusal of what plainly can't fit (nothing is charged: the
    # meter charges what actually runs, so the cap holds without it).
    budget.foresee(sum(expression_steps(node, {a.name: (a.low, a.high) for a in by_name[wanted[index].function].args})
                       * len(points[wanted[index].function]) for index, node in compiled.items()))
    found = (runner or sandboxed_runner)(extraction.source, points)
    budget.tick()
    if found.get("error") or not isinstance(found.get("results"), Mapping):
        report.failures.append(f"the declared functions could not be run in the sandbox ({found.get('error') or 'no results'})")
        return report
    results = found["results"]
    for index, claim in enumerate(wanted):
        function = by_name[claim.function]
        values = list(results.get(claim.function) or ())
        if len(values) != len(points[claim.function]):
            report.failures.append(f"{claim.function} gave no value at some tested settings")
            continue
        bad = None
        for point, entry in zip(points[claim.function], values):
            value = _value(entry)
            at = ", ".join(f"{a.name} = {v:g}" for a, v in zip(function.args, point))
            if value is None:
                bad = f"{claim.function}({at}) raised {entry.get('error') or 'an error'}"
                break
            if claim.kind == "equals":
                try:
                    expected = G.evaluate(compiled[index], dict(zip((a.name for a in function.args), point)),
                                          meter=budget)
                except (G.GrammarError, ArithmeticError, ValueError) as exc:
                    bad = f"the claimed expression for {claim.function} can't be evaluated at {at} ({exc})"
                    break
                if not math.isfinite(value) or not _close(value, expected):
                    bad = f"{claim.function}({at}) = {value:g}, but {claim.expr} = {expected:g} there"
                    break
            elif not math.isfinite(value):
                bad = f"{claim.function}({at}) is not finite"
                break
            elif claim.prop == "nonnegative" and value < -CLAIM_REL_TOL:
                bad = f"{claim.function}({at}) = {value:g} is negative"
                break
            elif claim.prop == "bounded" and claim.bound is not None and abs(value) > claim.bound * (1 + CLAIM_REL_TOL):
                bad = f"|{claim.function}({at})| = {abs(value):g} exceeds the stated bound {claim.bound:g}"
                break
        if bad is not None:
            report.failures.append(bad)
            continue
        line: dict[str, Any] = {"kind": claim.kind, "function": claim.function,
                                "settings": len(points[claim.function]),
                                "plotted": claim.function in report.plotted}
        if claim.kind == "equals":
            line["expr"] = claim.expr
        else:
            line["property"] = claim.prop
            if claim.bound is not None:
                line["bound"] = claim.bound
        report.checks.append(line)
    return report


__all__ = [
    "CLAIM_KINDS",
    "CheckReport",
    "ClaimWorkExceeded",
    "Extraction",
    "Function",
    "FunctionRunner",
    "MANIM_FIG_VERSION",
    "ManimFigure",
    "ManimFigureError",
    "check_claims",
    "extract_functions",
    "grid",
    "parse_declared",
    "parse_figure",
    "plotted_from_ok",
    "sandboxed_runner",
]
