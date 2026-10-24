"""Verification before a figure shows (spec_reader_workbench_v1 §8.3 steps 1-2; G45).

Run in the sidecar, on the compiled spec, before anything is stored as shown:

1. **Structural.** Every expression parsed and resolved (:func:`spec.parse_spec`
   already refused anything else), and every value a panel shows (every
   numeric leaf of its data, the renderer's padded scales and a percent
   readout's scaled value) is finite on the parameter grid: each parameter at
   its min, default and max (at most 3^4 = 81 combinations,
   :data:`spec.MAX_PARAMETERS`).
2. **Invariants.** Each declared invariant holds at every grid point,
   numerically: ``integrates_to_one`` within 1e-3 by the shared Simpson rule,
   ``sums_to_one`` within 1e-9, ``nonnegative``, ``bounded``, ``finite`` and
   ``monotone_nondecreasing`` on 121 samples of their range. Every shaded
   area's readout is checked against an independent integration
   (:func:`independent_integral`: 10-point Gauss-Legendre on 200 panels per
   piece, split at the piecewise breakpoints of the series) within 1e-6.

RW5b's panels (§8.7) pass the same two steps. Step 1 reads every value they
show (a heat map's grid, a field's arrows and its heat map, a path's points)
and their scales; a path that stops being finite or starts outside its plot
at a grid point fails it (:func:`path_problems`: nothing garbage is drawn,
and a path is cut where it leaves its padded plot, saying so). Their caps on
computation are the compiler's (:data:`spec.MAX_PANEL_WORK` and the grid,
step and iteration maxima), so verification stays bounded.

Step 3, the source match ("matches the book's equation (checked)"), is not in
RW5a: the owner shipped RW5a with every figure an illustration (2026-10-21)
and deferred the claim to RW5c, code-owned labels designed first. A
reconstruction is stored ``illustrative`` like any other figure.

**Outcomes:** 1 and 2 pass: ``illustrative`` (labelled "not checked against the
book"). 1 or 2 fails: ``failed``, never shown. A prediction code cannot
decide (no area matches, a value that is not finite) is dropped, not failed.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures import spec as S

ILLUSTRATIVE = "illustrative"
FAILED = "failed"
UNSUPPORTED = "unsupported"
#: What RW5a stores (``verified``, in migration 216's CHECK, is RW5c's; nothing
#: here produces it).
OUTCOMES = (ILLUSTRATIVE, FAILED, UNSUPPORTED)

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
    dropped_predictions: list[int] = field(default_factory=list)
    grid_points: int = 0
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome, "structural": self.structural[:12], "invariants": self.invariants[:24],
            "invariant_problems": self.invariant_problems[:12], "shades": self.shades[:24],
            "claims": self.claims,
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
            if key in OPTIONAL_PARTS and item is None:
                continue
            name = f"{where} {item['label']!r}" if isinstance(item, dict) and "label" in item else f"{where} {key}"
            _leaves(item, name, into)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _leaves(item, where if isinstance(item, dict) and "label" in item else f"{where}[{index}]", into)
    elif value is None or (isinstance(value, (int, float)) and not isinstance(value, bool)):
        into.append((where, value))


#: Keys whose None means "absent", never a value that is not finite (a PMF
#: with no highlight, a field with no heat map, a path that ran every step).
OPTIONAL_PARTS = frozenset({"highlight", "heatmap", "stopped"})


#: The renderer pads a plot's value range by 5% a side and a map's reach by
#: 10% (FigurePanels.tsx): those must stay finite too.
RENDER_PADDING = 1.1


def _extents(panel: Mapping[str, Any], where: str) -> list[tuple[str, Any]]:
    """The scales the renderer derives from a panel's values (its value
    range and its reach, padded), as values that must be finite: None when
    one is not (fix round 3: [[1e200, 0], [0, 1e200]] has finite entries
    and a determinant of 1e400)."""

    if panel["kind"] == "readout":
        # A percent readout is shown times 100 (FigurePanels.formatValue): the
        # scaled number is displayed, so it must be finite too (fix round 5).
        if panel.get("format") == "percent" and panel.get("value") is not None:
            scaled = panel["value"] * 100
            return [(f"{where} {panel['label']!r} as a percent", scaled if math.isfinite(scaled) else None)]
        return []
    if panel["kind"] == "function_plot":
        numbers = [v for series in panel["series"] for v in series["y"] if v is not None]
    elif panel["kind"] == "pmf_bars":
        numbers = [v for series in panel["series"] for v in series["p"] if v is not None]
    elif panel["kind"] == "linear_map_2d":
        numbers = [v for point in panel["square"] for v in point if v is not None]
    elif panel["kind"] == "heatmap_2d":
        numbers = [v for row in panel["z"] for v in row if v is not None]
    elif panel["kind"] == "vector_field_2d":
        # The arrows are scaled by the longest (FigurePanels.tsx).
        numbers = [v for grid in (panel["u"], panel["v"]) for row in grid for v in row if v is not None]
        overlay = panel.get("heatmap")
        extra = [] if overlay is None else _extents({"kind": "heatmap_2d", **overlay}, f"{where} heat map")
        return extra + _spread(numbers, where)
    elif panel["kind"] in ("trajectory_2d", "iterate_2d"):
        numbers = [*panel["x"], *panel["y"]]
    else:
        return []
    return _spread(numbers, where)


def _spread(numbers: Sequence[float], where: str) -> list[tuple[str, Any]]:
    if not numbers:
        return []
    low, high = min(numbers), max(numbers)
    spread = (high - low) * RENDER_PADDING
    reach = max(abs(low), abs(high)) * RENDER_PADDING
    return [(f"{where} value range", spread if math.isfinite(spread) else None),
            (f"{where} reach", reach if math.isfinite(reach) else None)]


def path_problems(data: Mapping[str, Any], point: Mapping[str, float]) -> list[str]:
    """RW5b: a path that stops being finite, or starts outside its plot, at a
    grid point (one that leaves its padded plot is cut there and says so)."""

    problems = []
    for index, panel in enumerate(data["panels"]):
        if panel["kind"] not in ("trajectory_2d", "iterate_2d"):
            continue
        where = f"panel {index + 1} ({panel['kind']})"
        if panel.get("stopped") == S.STOP_NOT_FINITE:
            problems.append(f"{where}: the path's values are not finite at {_point(point)}")
        elif panel.get("stopped") == S.STOP_OUTSIDE:
            problems.append(f"{where}: the path starts outside its plot at {_point(point)}")
    return problems


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
        if not problems:
            problems += path_problems(data, point)[:1]
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
    "UNSUPPORTED",
    "check_claims",
    "check_invariant",
    "decidable_predictions",
    "independent_integral",
    "parameter_grid",
    "path_problems",
    "quote_in",
    "verified_assumptions",
    "verify_numerics",
]
