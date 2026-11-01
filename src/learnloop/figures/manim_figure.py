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
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures.sketch import CLAIM_REL_TOL, impersonates

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
CLAIM_KINDS = ("equals", "invariant")
INVARIANT_PROPERTIES = ("finite", "nonnegative", "bounded")
#: The names a declared function may read besides its arguments, the module's
#: math/numpy names, its constants and other checkable declared functions.
SAFE_BUILTINS = frozenset({"abs", "min", "max", "round", "pow", "float", "int", "sum", "range", "len",
                           "enumerate", "zip", "list", "tuple", "bool", "True", "False", "None"})
#: The calls a ``plotted_from`` entry may name the function inside (Manim's plotting entry points).
PLOT_CALLS = frozenset({"plot", "plot_parametric_curve", "plot_polar_graph", "plot_line_graph", "get_graph",
                        "plot_implicit_curve", "plot_surface", "ParametricFunction", "FunctionGraph",
                        "ImplicitFunction", "ParametricSurface", "Surface", "ArrowVectorField", "StreamLines",
                        "always_redraw", "add_updater"})
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


def extract_functions(scene_code: str, functions: Sequence[Function]) -> Extraction:
    """The checkable part of the scene (module docstring). Never raises for
    model code: what can't be extracted is dropped with a reason."""

    try:
        tree = ast.parse(scene_code)
    except SyntaxError as exc:
        return Extraction("", [], {f.name: f"the scene does not parse ({exc.msg})" for f in functions})
    aliases, import_lines = _module_aliases(tree)
    defs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    declared = {f.name for f in functions}
    # Module constants: a plain NAME = <expression over literals, math/numpy and earlier constants>.
    constants: dict[str, ast.Assign] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            reads = _free_reads(node.value)
            if _forbidden_shape(node.value) is None and all(
                    name in aliases or name in constants or name in SAFE_BUILTINS for name in reads):
                constants[node.targets[0].id] = node
            else:
                constants.pop(node.targets[0].id, None)
    dropped: dict[str, str] = {}
    for function in functions:
        node = defs.get(function.name)
        if node is None:
            dropped[function.name] = "it is not a top-level def in the scene"
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
                                          else f"it needs {name!r}, which is neither math, numpy, a module "
                                               "constant nor another declared function")
                changed = True
                break
    checkable = [f.name for f in functions if f.name not in dropped]
    if not checkable:
        return Extraction("", [], dropped)
    body = ["# Extracted by LearnLoop: the declared functions only (no manim).", *dict.fromkeys(import_lines)]
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
import json, math, sys
from pathlib import Path

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


def plotted_from_ok(scene_code: str, function: str) -> bool:
    """``function`` is an argument (or read inside a lambda argument) of a
    Manim plot call in the scene (spec §9b.1, AST-checked)."""

    try:
        tree = ast.parse(scene_code)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", None)
        if name not in PLOT_CALLS:
            continue
        for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
            if any(isinstance(child, ast.Name) and child.id == function for child in ast.walk(argument)):
                return True
    return False


def check_claims(figure: ManimFigure, *, runner: FunctionRunner | None = None) -> CheckReport:
    """Check the figure's declared claims (module docstring). A claim on an
    unextractable function is dropped (``not_checkable``); an expression that
    doesn't parse, a value off the expression, a non-finite value or a failed
    run is a failure (the figure gets its second attempt, then isn't shown)."""

    report = CheckReport()
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
    found = (runner or sandboxed_runner)(extraction.source, points)
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
                    expected = G.evaluate(compiled[index], dict(zip((a.name for a in function.args), point)))
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
