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
   one verifier call checks one, and the label is figure-wide.

**Outcomes:** 1 and 2 and 3 pass: ``verified``. 3 alone fails (or cannot
run: no sandbox, no verifier, the spend cap): ``illustrative``, labelled "not
checked against the book". 1 or 2 fails: ``failed``, never shown. A
prediction code cannot decide (no area matches, a value that is not finite)
is dropped, not failed.
"""

from __future__ import annotations

import itertools
import math
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
        where = f"panel {index + 1} ({panel['kind']})"
        if panel["kind"] == "function_plot":
            for series in panel["series"]:
                values += [(f"{where} series {series['label']!r}", value) for value in series["y"]]
            values += [(f"{where} shade {shade['label']!r}", shade["value"]) for shade in panel["shades"]]
            values += [(f"{where} marker {marker['label']!r}", marker["x"]) for marker in panel["markers"]]
        elif panel["kind"] == "pmf_bars":
            for series in panel["series"]:
                values += [(f"{where} series {series['label']!r}", value) for value in series["p"]]
            if panel["highlight"] is not None:
                values.append((f"{where} highlight", panel["highlight"]["value"]))
        elif panel["kind"] == "linear_map_2d":
            values += [(f"{where} matrix", value) for row in panel["matrix"] for value in row]
        else:
            values.append((f"{where} {panel['label']!r}", panel["value"]))
    return values


def structural(compiled: S.CompiledFigure, grid: Sequence[Mapping[str, float]]) -> list[str]:
    problems: list[str] = []
    for point in grid:
        data = S.evaluate_figure(compiled, point)
        for where, value in _shown_values(data):
            if value is None:
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
    if len(checks) != len(pairs):
        return {"matched": False, "reason": "sandbox_failed"}
    accepted = checks[0] is True
    # A control is rejected only by a plain False: a check that raised, timed
    # out or answered nothing (None, or anything not a bool) rejected nothing
    # (Codex review F4).
    inconclusive = any(value is not True and value is not False for value in checks[1:])
    controls_rejected = all(value is False for value in checks[1:])
    matched = accepted and controls_rejected and not degenerate
    reason = "" if matched else (
        "the spec's definition does not equal the source equation" if not accepted
        else "a negative control was inconclusive (the check raised or gave no answer)" if inconclusive
        else "the check accepts a negative control")
    return {"matched": matched, "reason": reason, "checks": checks, "degenerate": degenerate,
            "import_errors": result.output.get("import_errors") or {}}


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
    "equals_source_definition",
    "equals_source_definitions",
    "independent_integral",
    "negative_controls",
    "parameter_grid",
    "quote_in",
    "run_source_match",
    "verified_assumptions",
    "verify_numerics",
]
