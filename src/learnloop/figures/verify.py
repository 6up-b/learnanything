"""Verification before a figure shows (spec_reader_workbench_v1 §8.3; G23, G45).

Run in the sidecar, on the compiled spec, before anything is stored as shown:

1. **Structural.** Every expression parsed and resolved (:func:`spec.parse_spec`
   already refused anything else), and every value a panel shows is finite on
   the parameter grid: each parameter at its min, default and max (at most
   3^4 = 81 combinations, :data:`spec.MAX_PARAMETERS`).
2. **Invariants.** Each declared invariant holds at every grid point,
   numerically: ``integrates_to_one`` within 1e-3 by the shared Simpson rule,
   ``sums_to_one`` within 1e-9, ``nonnegative``, ``bounded``, ``finite`` and
   ``monotone_nondecreasing`` on 121 samples of their range. Every shaded
   area's readout is checked against an independent integration
   (:func:`independent_integral`: 10-point Gauss-Legendre on 200 panels per
   piece, split at the piecewise breakpoints of the series) within 1e-6.
3. **Source match** (``kind = reconstructed`` only): the source claims'
   quotes are verbatim in the selected passage; the verifier (route
   ``figure_verifier``) transcribes the quoted equation into sympy and writes
   ``check(reference, answer)``; the PF-b sandbox runs it on (the transcribed
   source, the spec's definition as :func:`grammar.to_sympy` writes it) and on
   two negative controls of ours (that definition times 8/7, and halved)
   plus the sandbox's standard ones. Only a check that accepts the definition
   and rejects every control with a plain ``False`` is a match (a control
   the check raised on, timed out on or gave no answer for rejected nothing),
   and only one definition may be named in ``equals_source``: the request's
   one verifier call checks one, and the label is figure-wide. The check is
   bound to what is displayed (:func:`displayed_source_problem`, structural,
   no model): at least one series, readout or map cell is the checked
   definition itself, and every series or readout whose label names the
   source equation (the definition's name, or the quote's left-hand side)
   is exactly that definition, by reference, with no transform; otherwise
   the figure is an illustration whatever the check says.

**Outcomes:** 1 and 2 and 3 pass: ``verified``. 3 alone fails (or cannot
run: no sandbox, no verifier, the spend cap): ``illustrative``, labelled "not
checked against the book". 1 or 2 fails: ``failed``, never shown. A
prediction code cannot decide (no area matches, a value that is not finite)
is dropped, not failed.
"""

from __future__ import annotations

import itertools
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures import spec as S

VERIFIED = "verified"
ILLUSTRATIVE = "illustrative"
FAILED = "failed"
UNSUPPORTED = "unsupported"
OUTCOMES = (VERIFIED, ILLUSTRATIVE, FAILED, UNSUPPORTED)

DENSITY_TOLERANCE = 1e-3
PMF_TOLERANCE = 1e-9
SHADE_TOLERANCE = 1e-6
NONNEGATIVE_SLACK = 1e-12
MONOTONE_SLACK = 1e-9
DEFAULT_BOUND = 1e6
RANGE_SAMPLES = 120
GL_PANELS = 200
#: 10-point Gauss-Legendre nodes and weights on [-1, 1].
_GL = (
    (-0.9739065285171717, 0.0666713443086881), (-0.8650633666889845, 0.1494513491505806),
    (-0.6794095682990244, 0.2190863625159820), (-0.4333953941292472, 0.2692667193099963),
    (-0.1488743389816312, 0.2955242247147529), (0.1488743389816312, 0.2955242247147529),
    (0.4333953941292472, 0.2692667193099963), (0.6794095682990244, 0.2190863625159820),
    (0.8650633666889845, 0.1494513491505806), (0.9739065285171717, 0.0666713443086881),
)


@dataclass
class Report:
    """What each step found, as stored in ``verification_report_json``."""

    outcome: str = FAILED
    structural: list[str] = field(default_factory=list)
    invariants: list[dict[str, Any]] = field(default_factory=list)
    invariant_problems: list[str] = field(default_factory=list)
    shades: list[dict[str, Any]] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    source_match: dict[str, Any] = field(default_factory=dict)
    dropped_predictions: list[int] = field(default_factory=list)
    grid_points: int = 0
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome, "structural": self.structural[:12], "invariants": self.invariants[:24],
            "invariant_problems": self.invariant_problems[:12], "shades": self.shades[:24],
            "claims": self.claims, "source_match": self.source_match,
            "dropped_predictions": self.dropped_predictions, "grid_points": self.grid_points, "reason": self.reason,
        }


def parameter_grid(compiled: S.CompiledFigure) -> list[dict[str, float]]:
    """Each parameter at its min, default and max (duplicates dropped)."""

    axes = []
    for parameter in compiled.parameters:
        values = list(dict.fromkeys([float(parameter.min), float(parameter.default), float(parameter.max)]))
        axes.append([(parameter.name, value) for value in values])
    if not axes:
        return [{}]
    return [dict(combo) for combo in itertools.product(*axes)]


def _range_samples(low: float, high: float, count: int = RANGE_SAMPLES) -> list[float]:
    return [low + (high - low) * i / count for i in range(count + 1)]


def _shown_values(data: Mapping[str, Any]) -> list[tuple[str, Any]]:
    """Every value a panel shows, with where it is."""

    values: list[tuple[str, Any]] = []
    for index, panel in enumerate(data["panels"]):
        _leaves(panel, f"panel {index + 1} ({panel['kind']})", values)
        values += _extents(panel, f"panel {index + 1} ({panel['kind']})")
    return values


def _leaves(value: Any, where: str, into: list[tuple[str, Any]]) -> None:
    """Every number (or None, a value that is not finite) the panel data
    holds, at any depth: the inputs and every derived value the renderer
    shows (a map's determinant and corners, a shaded area's bounds and value,
    readouts), so a new field is checked without being listed (fix round 3).
    A panel with no highlight holds ``highlight: None``, which is not a value."""

    if isinstance(value, dict):
        for key, item in value.items():
            if key == "highlight" and item is None:
                continue
            name = f"{where} {item['label']!r}" if isinstance(item, dict) and "label" in item else f"{where} {key}"
            _leaves(item, name, into)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _leaves(item, where if isinstance(item, dict) and "label" in item else f"{where}[{index}]", into)
    elif value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        into.append((where, value))


#: The renderer pads a plot's value range by 5% a side and a map's reach by
#: 10% (FigurePanels.tsx): those must stay finite too.
RENDER_PADDING = 1.1


def _extents(panel: Mapping[str, Any], where: str) -> list[tuple[str, Any]]:
    """The scales the renderer derives from a panel's values (its value
    range and its reach, padded), as values that must be finite: None when
    one is not (fix round 3: [[1e200, 0], [0, 1e200]] has finite entries
    and a determinant of 1e400)."""

    if panel["kind"] == "function_plot":
        numbers = [v for series in panel["series"] for v in series["y"] if v is not None]
    elif panel["kind"] == "pmf_bars":
        numbers = [v for series in panel["series"] for v in series["p"] if v is not None]
    elif panel["kind"] == "linear_map_2d":
        numbers = [v for point in panel["square"] for v in point if v is not None]
    else:
        return []
    if not numbers:
        return []
    low, high = min(numbers), max(numbers)
    spread = (high - low) * RENDER_PADDING
    reach = max(abs(low), abs(high)) * RENDER_PADDING
    return [(f"{where} value range", spread if math.isfinite(spread) else None),
            (f"{where} reach", reach if math.isfinite(reach) else None)]


def structural(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> list[str]:
    problems: list[str] = []
    for point in grid:
        data = S.evaluate_figure(compiled, point)
        for where, value in _shown_values(data):
            # Every numeric leaf must be a finite number: None, NaN and
            # infinity all fail (fix round 4).
            if value is None or not math.isfinite(value):
                problems.append(f"{where} is not finite at {_point(point)}")
                break
        if problems:
            break
    return problems


def _point(point: Mapping[str, float]) -> str:
    return ", ".join(f"{name}={value:g}" for name, value in point.items()) or "the defaults"


def _env(compiled: S.CompiledFigure, point: Mapping[str, float]) -> dict[str, float]:
    env = compiled.defaults
    env.update(point)
    return env


def _sampler(compiled: S.CompiledFigure, node: G.Node, variable: str | None, env: Mapping[str, float]
             ) -> Callable[[float], float]:
    scope = dict(env)

    def at(value: float) -> float:
        if variable:
            scope[variable] = value
        return G.evaluate(node, scope, compiled.definitions)

    return at


def check_invariant(compiled: S.CompiledFigure, invariant: Any, node: G.Node | None,
                    point: Mapping[str, float]) -> tuple[bool, str, float | None]:
    """One invariant at one grid point: (holds, why not, the measured value)."""

    if node is None:
        return False, "it has no expression", None
    env = _env(compiled, point)
    at = _sampler(compiled, node, invariant.var, env)
    kind = invariant.kind
    if kind == "integrates_to_one":
        value = G.adaptive_simpson(at, float(invariant.from_), float(invariant.to))
        return (math.isfinite(value) and abs(value - 1.0) <= DENSITY_TOLERANCE,
                f"integrates to {value:.6g}, not 1", value)
    if kind == "sums_to_one":
        value = G.exact_sum(at, float(invariant.from_), float(invariant.to))
        return (math.isfinite(value) and abs(value - 1.0) <= PMF_TOLERANCE, f"sums to {value:.12g}, not 1", value)
    xs = _range_samples(float(invariant.from_), float(invariant.to)) if invariant.var else [0.0]
    values = [at(x) for x in xs]
    if any(not math.isfinite(value) for value in values):
        return False, "a value is not finite", None
    if kind == "finite":
        return True, "", None
    if kind == "bounded":
        bound = float(invariant.bound if invariant.bound is not None else DEFAULT_BOUND)
        worst = max(abs(value) for value in values)
        return worst <= bound, f"reaches {worst:.6g}, past the bound {bound:g}", worst
    if kind == "nonnegative":
        worst = min(values)
        return worst >= -NONNEGATIVE_SLACK, f"goes negative ({worst:.6g})", worst
    if kind == "monotone_nondecreasing":
        for left, right in zip(values, values[1:]):
            if right < left - MONOTONE_SLACK * max(1.0, abs(left)):
                return False, f"decreases from {left:.6g} to {right:.6g}", right - left
        return True, "", None
    return False, f"unknown invariant {kind!r}", None


def _breakpoints(node: G.Node, defs: Mapping[str, G.Node], variable: str, env: Mapping[str, float],
                 _seen: tuple[str, ...] = ()) -> set[float]:
    """Where a piecewise condition compares the variable with an expression
    free of it (``x < c``, ``c >= x``): the points a series may jump at."""

    found: set[float] = set()
    if node.kind == "name" and node.text in defs and node.text not in _seen:
        return _breakpoints(defs[node.text], defs, variable, env, (*_seen, node.text))
    if node.kind in ("integral", "sum") and node.text == variable:
        # The body binds the variable: only the bounds are in the outer scope.
        for bound in node.args[1:]:
            found |= _breakpoints(bound, defs, variable, env, _seen)
        return found
    if node.kind == "cmp":
        left, right = node.args
        for mine, other in ((left, right), (right, left)):
            if mine.kind == "name" and mine.text == variable and variable not in S.expanded_free(other, defs):
                value = G.evaluate(other, env, defs)
                if math.isfinite(value):
                    found.add(value)
    for child in node.args:
        found |= _breakpoints(child, defs, variable, env, _seen)
    return found


def independent_integral(compiled: S.CompiledFigure, node: G.Node, variable: str, low: float, high: float,
                         env: Mapping[str, float]) -> float:
    """The verifier's own integration: Gauss-Legendre on :data:`GL_PANELS`
    panels per piece, the range split at the series' piecewise breakpoints
    (nodes are interior, so each piece reads its own side of a jump)."""

    if not (math.isfinite(low) and math.isfinite(high)):
        return math.nan
    if low == high:
        return 0.0
    sign = 1.0
    if low > high:
        low, high, sign = high, low, -1.0
    cuts = sorted(point for point in _breakpoints(node, compiled.definitions, variable, env) if low < point < high)
    edges = [low, *cuts, high]
    at = _sampler(compiled, node, variable, env)
    total = 0.0
    for a, b in zip(edges, edges[1:]):
        width = (b - a) / GL_PANELS
        for panel in range(GL_PANELS):
            left = a + panel * width
            middle = left + width / 2
            half = width / 2
            total += half * sum(weight * at(middle + half * x) for x, weight in _GL)
    return sign * total


def check_shades(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    problems: list[str] = []
    for panel in compiled.panels:
        if panel.kind != "function_plot":
            continue
        model = panel.model
        labels = [series.label for series in model.series]
        for index, shade in enumerate(model.shade):
            node = panel.nodes["series"][labels.index(shade.series)]
            worst = 0.0
            for point in grid:
                env = _env(compiled, point)
                low, high, value = S.shade_value(compiled, panel, index, env)
                reference = independent_integral(compiled, node, model.x.var, low, high, env)
                gap = abs(value - reference) if math.isfinite(value) and math.isfinite(reference) else math.inf
                worst = max(worst, gap)
                if gap > SHADE_TOLERANCE * max(1.0, abs(reference) if math.isfinite(reference) else 1.0):
                    problems.append(f"the shaded area {shade.label!r} reads {value:.9g} but integrates to "
                                    f"{reference:.9g} at {_point(point)}")
                    break
            results.append({"label": shade.label, "worst_gap": worst if math.isfinite(worst) else None})
    return results, problems


def check_invariants(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]
                     ) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    problems: list[str] = []
    for invariant, node in compiled.invariants:
        if invariant.kind == "equals_source":
            continue
        entry = {"kind": invariant.kind, "expr": invariant.expr, "holds": True}
        for point in grid:
            holds, why, value = check_invariant(compiled, invariant, node, point)
            if not holds:
                entry.update(holds=False, why=why, at=_point(point))
                problems.append(f"{invariant.kind} on {invariant.expr!r}: {why} at {_point(point)}")
                break
        results.append(entry)
    return results, problems


# ---------------------------------------------------------------------------
# Quotes
# ---------------------------------------------------------------------------

def _squash(text: str) -> str:
    return " ".join(str(text or "").split())


def quote_in(quote: str, text: str) -> bool:
    """A quote is the source's own words: verbatim after collapsing whitespace."""

    needle = _squash(quote)
    return bool(needle) and needle in _squash(text)


def check_claims(compiled: S.CompiledFigure, span_texts: Mapping[str, str]) -> list[dict[str, Any]]:
    return [{"span_id": claim.span_id, "quote": claim.quote,
             "verified": claim.span_id in span_texts and quote_in(claim.quote, span_texts[claim.span_id])}
            for claim in compiled.spec.source_claims]


def verified_assumptions(compiled: S.CompiledFigure, span_texts: Mapping[str, str]) -> list[dict[str, Any]]:
    """The assumptions as shown: a quote that is not verbatim in its span is dropped (the text stays, AI-written)."""

    shown = []
    for assumption in compiled.spec.assumptions:
        quote = assumption.quote if (assumption.quote and assumption.span_id in span_texts
                                     and quote_in(assumption.quote, span_texts[assumption.span_id])) else None
        shown.append({"text": assumption.text, "span_id": assumption.span_id if quote else None, "quote": quote})
    return shown


# ---------------------------------------------------------------------------
# Step 3: the sandboxed source match
# ---------------------------------------------------------------------------

@dataclass
class SourceCheck:
    """What the verifier wrote: the quoted equation in sympy, and the check."""

    source_expression: str
    check_program: str
    quote: str = ""
    model: str | None = None


def negative_controls(answer: str) -> list[str]:
    """Our own controls: the definition scaled (8/7) and halved, which a real
    equality check must reject (the sandbox adds its standard ones)."""

    return [f"({answer})*Rational(8, 7)", f"({answer})/2"]


_PROGRAM_CHARS = 6_000
_EXPRESSION_CHARS = 2_000


def run_source_match(answer: str, check: SourceCheck, *, run: Callable[..., Any] | None = None) -> dict[str, Any]:
    """The verifier's check run in the PF-b sandbox, never in-process:
    ``matched`` only when it accepts the definition and rejects every control."""

    from learnloop.content.authoring.pf_sandbox import SandboxLimits, SandboxUnavailable, run_equivalence_checks

    if not check.check_program.strip() or not check.source_expression.strip():
        return {"matched": False, "reason": "the verifier wrote no check"}
    if len(check.check_program) > _PROGRAM_CHARS or len(check.source_expression) > _EXPRESSION_CHARS:
        return {"matched": False, "reason": "the verifier's check is too long"}
    controls = negative_controls(answer)
    pairs = [{"program": "check", "reference": check.source_expression, "answer": candidate}
             for candidate in (answer, *controls)]
    kwargs: dict[str, Any] = {"limits": SandboxLimits(cpu_seconds=20, wall_seconds=40)}
    if run is not None:
        kwargs["run"] = run
    try:
        result = run_equivalence_checks({"check": check.check_program}, pairs, **kwargs)
    except SandboxUnavailable:
        return {"matched": False, "reason": "sandbox_unavailable"}
    if not result.ok or not isinstance(result.output, dict):
        return {"matched": False, "reason": "sandbox_failed", "error": result.error}
    checks = list(result.output.get("checks") or [])
    degenerate = bool((result.output.get("degenerate") or {}).get("check"))
    # The sandbox's standard controls ("", nonsense, a far number): one the
    # check answered with something not a boolean confirms nothing either.
    standard_unclear = bool((result.output.get("inconclusive_controls") or {}).get("check"))
    if len(checks) != len(pairs):
        return {"matched": False, "reason": "sandbox_failed"}
    # The harness never coerces an answer (fix round 2, F4): the candidate
    # must be exactly True and each of our controls exactly False. A check
    # that raised, timed out or answered None, 0, "" or anything not a
    # boolean decided nothing, and the figure stays an illustration.
    accepted = checks[0] is True
    inconclusive = standard_unclear or any(value is not True and value is not False for value in checks[1:])
    controls_rejected = all(value is False for value in checks[1:])
    matched = accepted and controls_rejected and not degenerate and not standard_unclear
    reason = "" if matched else (
        "the spec's definition does not equal the source equation" if not accepted
        else "a negative control was inconclusive (the check raised or gave no answer)" if inconclusive
        else "the check accepts a negative control")
    return {"matched": matched, "reason": reason, "checks": checks, "degenerate": degenerate,
            "import_errors": result.output.get("import_errors") or {}}


# ---------------------------------------------------------------------------
# Step 3, certified (fix round 4): "checked" needs the display to agree
# ---------------------------------------------------------------------------

#: (a) Every numeric literal of a checked definition is a small exact
#: decimal: SymPy reads it as that decimal exactly, and the evaluator's double
#: is within an ulp of it, so a literal can never be where the two part.
MAX_LITERAL = 1e6
MAX_LITERAL_DIGITS = 9
#: (d) The displayed value and the checked equation agree to a relative or
#: absolute 1e-9 at every sample, evaluated by mpmath at 50 digits.
AGREEMENT_TOLERANCE = 1e-9
AGREEMENT_DIGITS = 50


def literal_problem(node: G.Node, definitions: Mapping[str, G.Node]) -> str | None:
    """Rule (a): why a literal of ``node`` (definitions expanded) is not a
    small exact decimal (|x| <= 1e6, at most 9 significant digits), or None.
    ``pi`` and ``e`` are names, not literals, and are allowed."""

    from decimal import Decimal, InvalidOperation

    for current, _depth in G.expansion(node, definitions):
        if current.kind != "num":
            continue
        try:
            value = Decimal(current.text)
        except InvalidOperation:
            return f"the literal {current.text!r} is not a decimal number"
        digits = len(value.normalize().as_tuple().digits)
        if abs(value) > Decimal(int(MAX_LITERAL)) or digits > MAX_LITERAL_DIGITS:
            return (f"the literal {current.text!r} is not a small exact decimal (at most {MAX_LITERAL:g} with "
                    f"{MAX_LITERAL_DIGITS} significant digits), so the figure and the check could part on it")
    return None


def _conditions(node: G.Node, definitions: Mapping[str, G.Node]) -> tuple[list[G.Node], bool]:
    """Every piecewise condition of ``node`` (definitions expanded), and
    whether one sits in a sum's body (its branch is chosen per term, which
    the display samples cannot pin down: not certifiable)."""

    found: list[G.Node] = []
    in_body = False
    stack: list[tuple[G.Node, bool, tuple[str, ...]]] = [(node, False, ())]
    while stack:
        current, inside, seen = stack.pop()
        if current.kind == "name" and current.text in definitions and current.text not in seen:
            stack.append((definitions[current.text], inside, (*seen, current.text)))
            continue
        if current.kind == "piecewise":
            in_body = in_body or inside
            found += [current.args[index] for index in range(0, len(current.args) - 1, 2)]
        if current.kind in ("sum", "integral"):
            body, lower, upper = current.args
            stack += [(body, True, seen), (lower, inside, seen), (upper, inside, seen)]
        else:
            stack += [(child, inside, seen) for child in current.args]
    return found, in_body


def _exact(value: float) -> list[int]:
    from fractions import Fraction

    fraction = Fraction(value)
    return [fraction.numerator, fraction.denominator]


def _displayed(compiled: S.CompiledFigure, name: str
               ) -> list[tuple[str | None, list[float], list[float | None], dict[str, float]]]:
    """``(variable, samples, displayed values, the grid point)`` for every
    place the checked definition is drawn by reference, at every point of the
    parameter grid: the production evaluator's own displayed data."""

    places = []
    for index, panel in enumerate(compiled.panels):
        if panel.kind in ("function_plot", "pmf_bars"):
            for series_index, node in enumerate(panel.nodes.get("series") or []):
                if node is not None and node.kind == "name" and node.text == name:
                    places.append((index, "series", series_index))
        elif panel.kind == "readout":
            node = panel.nodes.get("expr")
            if node is not None and node.kind == "name" and node.text == name:
                places.append((index, "readout", 0))
        else:
            for row, cells in enumerate(panel.nodes.get("matrix") or []):
                for column, node in enumerate(cells):
                    if node is not None and node.kind == "name" and node.text == name:
                        places.append((index, "cell", row * 2 + column))
    groups = []
    for point in parameter_grid(compiled):
        data = S.evaluate_figure(compiled, point)
        env = _env(compiled, point)
        for index, where, position in places:
            panel, model = data["panels"][index], compiled.panels[index].model
            if where == "series" and panel["kind"] == "function_plot":
                groups.append((model.x.var, list(panel["x"]), list(panel["series"][position]["y"]), env))
            elif where == "series":
                groups.append((model.k.var, list(panel["k"]), list(panel["series"][position]["p"]), env))
            elif where == "readout":
                groups.append((None, [], [panel["value"]], env))
            else:
                groups.append((None, [], [panel["matrix"][position // 2][position % 2]], env))
    return groups


_DISPLAY_HARNESS = r'''
import json, sys
workdir = sys.argv[1]
MARKER = "@@PF-SANDBOX-RESULT@@"


def emit(value):
    sys.stdout.write(MARKER + json.dumps(value))
    sys.stdout.flush()


with open(workdir + "/input.json", encoding="utf-8") as handle:
    payload = json.load(handle)
try:
    import mpmath
    import sympy
    mpmath.mp.dps = payload["digits"]
    symbols = {name: sympy.Symbol(name, real=True) for name in payload["symbols"]}
    expression = sympy.sympify(payload["expression"], locals=symbols)
    conditions = [sympy.sympify(text, locals=symbols) for text in payload["conditions"]]
except BaseException as exc:
    emit({"error": type(exc).__name__ + ": " + str(exc)[:300]})
    sys.exit(0)


def exact(pair):
    return sympy.Rational(int(pair[0]), int(pair[1]))


def real(value):
    value = mpmath.mpmathify(value)
    if isinstance(value, mpmath.mpc):
        if value.imag != 0:
            return "complex"
        value = value.real
    if not mpmath.isfinite(value):
        return "not finite"
    return mpmath.nstr(value, 40, strip_zeros=False)


def compiled(form, symbol):
    form = form.doit()
    if symbol is None or form.has(sympy.Sum):
        return None, form
    return sympy.lambdify([symbol], form, modules="mpmath"), form


groups = []
for group in payload["groups"]:
    fixed = {symbols[name]: exact(pair) for name, pair in group["params"].items()}
    symbol = symbols[group["var"]] if group["var"] else None
    entry = {"values": [], "conditions": []}
    try:
        value_fn, value_form = compiled(expression.subs(fixed), symbol)
        condition_forms = [compiled(condition.subs(fixed), symbol) for condition in conditions]
    except BaseException as exc:
        groups.append({"error": type(exc).__name__ + ": " + str(exc)[:200]})
        continue
    samples = group["samples"] if symbol is not None else [None]
    for sample in samples:
        argument = None if sample is None else mpmath.mpf(int(sample[0])) / int(sample[1])
        try:
            if value_fn is not None:
                entry["values"].append(real(value_fn(argument)))
            else:
                form = value_form if symbol is None else value_form.subs(symbol, exact(sample)).doit()
                entry["values"].append(real(sympy.N(form, payload["digits"])))
        except BaseException as exc:
            entry["values"].append("error: " + type(exc).__name__)
        truths = []
        for function, form in condition_forms:
            try:
                if function is not None:
                    truths.append(bool(function(argument)))
                else:
                    truth = form if symbol is None else form.subs(symbol, exact(sample))
                    truths.append(bool(truth))
            except BaseException:
                truths.append(None)
        entry["conditions"].append(truths)
    groups.append(entry)
emit({"groups": groups})
'''


def display_agreement(compiled: S.CompiledFigure, name: str, *, run: Callable[..., Any] | None = None
                      ) -> dict[str, Any]:
    """Rule (d), computed in code after the check passed (no model call):
    at every point of the parameter grid and every plotted sample, the value
    the figure DISPLAYS equals the checked SymPy expression (the unmodified
    production translation, :func:`grammar.to_sympy`) evaluated by mpmath at
    50 digits, to a relative or absolute 1e-9, and every piecewise condition
    chooses the same branch. Any disagreement, a value that is not finite, a
    SymPy evaluation that fails, or a sandbox that cannot run: not agreed.

    The SymPy text is read only inside the PF-b sandbox, by the fixed
    harness above; the comparison is made here."""

    from learnloop.content.authoring.pf_sandbox import SandboxLimits, SandboxUnavailable, run_sandboxed_python

    definitions = compiled.definitions
    node = definitions[name]
    conditions, in_body = _conditions(node, definitions)
    if in_body:
        return {"agreed": False, "reason": "a piecewise choice sits inside a sum's body, which the display cannot "
                                           "pin down sample by sample"}
    groups = _displayed(compiled, name)
    if not groups:
        return {"agreed": False, "reason": "the checked definition is not drawn"}
    symbols = sorted({parameter.name for parameter in compiled.parameters}
                     | {var for var, _samples, _values, _env in groups if var})
    payload = {
        "digits": AGREEMENT_DIGITS,
        "expression": G.to_sympy(node, definitions),
        "conditions": [G.to_sympy(condition, definitions) for condition in conditions],
        "symbols": symbols,
        "groups": [{"params": {key: _exact(value) for key, value in env.items()}, "var": var,
                    "samples": [_exact(sample) for sample in samples]} for var, samples, _values, env in groups],
    }
    kwargs: dict[str, Any] = {"limits": SandboxLimits(cpu_seconds=40, wall_seconds=90)}
    if run is not None:
        kwargs["run"] = run
    try:
        result = run_sandboxed_python(_DISPLAY_HARNESS, payload, **kwargs)
    except SandboxUnavailable:
        return {"agreed": False, "reason": "the display could not be compared with the check (no sandbox)"}
    output = result.output if result.ok and isinstance(result.output, dict) else None
    if output is None or "error" in output or len(output.get("groups") or []) != len(groups):
        why = (output or {}).get("error") or result.error or "no result"
        return {"agreed": False, "reason": f"the checked equation could not be evaluated where it is drawn ({why})"}
    checked = 0
    for (var, samples, values, env), answer in zip(groups, output["groups"]):
        if "error" in answer:
            return {"agreed": False, "reason": f"the checked equation could not be evaluated ({answer['error']})"}
        points = samples if var else [None]
        if len(answer["values"]) != len(points) or len(answer["conditions"]) != len(points):
            return {"agreed": False, "reason": "the comparison was incomplete"}
        for sample, shown, reference, truths in zip(points, values, answer["values"], answer["conditions"]):
            at = dict(env)
            if var:
                at[var] = sample
            where = ", ".join(f"{key}={value:g}" for key, value in at.items()) or "the defaults"
            if shown is None or not math.isfinite(shown):
                return {"agreed": False, "reason": f"the figure shows no finite value at {where}"}
            try:
                exact_value = float(reference)
            except (TypeError, ValueError):
                return {"agreed": False, "reason": f"the checked equation is {reference} at {where}"}
            gap = abs(shown - exact_value)
            if not (gap <= AGREEMENT_TOLERANCE or gap <= AGREEMENT_TOLERANCE * abs(exact_value)):
                return {"agreed": False, "reason": f"the figure shows {shown:.12g} where the checked equation is "
                                                   f"{exact_value:.12g} (at {where})"}
            for condition, truth in zip(conditions, truths):
                if truth is None or G._truth(condition, at, definitions) is not truth:
                    return {"agreed": False, "reason": f"a piecewise branch the figure takes is not the checked "
                                                       f"equation's (at {where})"}
            checked += 1
    return {"agreed": True, "reason": "", "samples": checked}


def equals_source_definitions(compiled: S.CompiledFigure) -> list[str]:
    """Every definition an ``equals_source`` invariant names, once each, in
    order. A figure is ``verified`` only when every one of them is checked
    (Codex review F3): the label is figure-wide."""

    names: list[str] = []
    for invariant, _node in compiled.invariants:
        if invariant.kind == "equals_source" and invariant.name in compiled.definitions and invariant.name not in names:
            names.append(str(invariant.name))
    return names


def equals_source_definition(compiled: S.CompiledFigure) -> str | None:
    """The one definition named as the source equation, or None (none, or
    more than one: then no single check covers the figure)."""

    names = equals_source_definitions(compiled)
    return names[0] if len(names) == 1 else None


_LABEL_NOISE = re.compile(r"[\s\\{}$]")


def _label_key(text: str) -> str:
    return _LABEL_NOISE.sub("", str(text or ""))


def _names_source(label: str, name: str, left_sides: Sequence[str]) -> bool:
    """Whether a label names the source equation: the checked definition's
    name as its first word (``f``, ``f(x)``, ``f_X(x)``; not ``frequency``),
    or a source quote's left-hand side (``f_X(x)`` of "f_X(x) = ...")."""

    key = _label_key(label)
    if not key:
        return False
    if re.match(re.escape(name) + r"(?![A-Za-z0-9])", key):
        return True
    return any(key == side or key.startswith(side + "=") for side in left_sides)


def _is_reference(node: G.Node | None, name: str) -> bool:
    return node is not None and node.kind == "name" and node.text == name


def displayed_source_problem(compiled: S.CompiledFigure, name: str,
                             claims: Sequence[Mapping[str, Any]] = ()) -> str | None:
    """Why the checked definition ``name`` is not what the figure displays
    as the book's equation, or None (fix round 2, F3; structural, no model).

    "Matches the book's equation (checked)" is a claim about what is drawn,
    so the check must cover it: at least one series or readout (or a map's
    cell) is ``name`` itself, and every plotted series and readout whose
    label names the source equation (:func:`_names_source`) is exactly
    ``name``, by reference, with no transform (``2*f`` labelled ``f(x)``
    shows an equation nobody checked)."""

    left_sides = []
    for claim in claims:
        quote = str(claim.get("quote") or "")
        if claim.get("verified", True) and "=" in quote:
            side = _label_key(quote.split("=", 1)[0])
            if side:
                left_sides.append(side)
    shown = False
    for panel in compiled.panels:
        if panel.kind in ("function_plot", "pmf_bars"):
            entries = list(zip([series.label for series in panel.model.series], panel.nodes.get("series") or []))
        elif panel.kind == "readout":
            entries = [(panel.model.label, panel.nodes.get("expr"))]
        else:
            cells = [cell for row in panel.nodes.get("matrix") or [] for cell in row]
            shown = shown or any(_is_reference(cell, name) for cell in cells)
            continue
        for label, node in entries:
            reference = _is_reference(node, name)
            shown = shown or reference
            if not reference and _names_source(label, name, left_sides):
                return (f"{label!r} is labelled as the book's equation but draws something other than the "
                        f"checked definition {name!r}")
    if not shown:
        return f"the figure draws no series or readout that is the checked definition {name!r}"
    return None


def decidable_predictions(compiled: S.CompiledFigure) -> tuple[list[int], list[int]]:
    """Predictions code can decide (an answer exists), and those it cannot (dropped)."""

    kept, dropped = [], []
    for index in range(len(compiled.predictions)):
        outcome = S.prediction_outcome(compiled, index)
        (kept if outcome.get("answer") is not None else dropped).append(index)
    return kept, dropped


def verify_numerics(compiled: S.CompiledFigure) -> Report:
    """Steps 1 and 2 (no model, no sandbox): ``failed`` or a report to carry on."""

    report = Report()
    grid = parameter_grid(compiled)
    report.grid_points = len(grid)
    report.structural = structural(compiled, grid)
    if report.structural:
        report.outcome, report.reason = FAILED, report.structural[0]
        return report
    report.invariants, report.invariant_problems = check_invariants(compiled, grid)
    report.shades, shade_problems = check_shades(compiled, grid)
    report.invariant_problems += shade_problems
    if report.invariant_problems:
        report.outcome, report.reason = FAILED, report.invariant_problems[0]
        return report
    _kept, report.dropped_predictions = decidable_predictions(compiled)
    report.outcome = ILLUSTRATIVE
    return report


__all__ = [
    "FAILED",
    "ILLUSTRATIVE",
    "OUTCOMES",
    "Report",
    "SourceCheck",
    "UNSUPPORTED",
    "VERIFIED",
    "check_claims",
    "check_invariant",
    "decidable_predictions",
    "display_agreement",
    "displayed_source_problem",
    "equals_source_definition",
    "equals_source_definitions",
    "independent_integral",
    "literal_problem",
    "negative_controls",
    "parameter_grid",
    "quote_in",
    "run_source_match",
    "verified_assumptions",
    "verify_numerics",
]
