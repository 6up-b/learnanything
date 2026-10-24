"""``InteractiveFigureSpecV1``: the declarative figure (spec_reader_workbench_v1 §8.2).

The figure author writes this JSON; :func:`parse_spec` validates it (the strict
schema, the caps, every expression through :mod:`.grammar` with its names
resolved) and :func:`evaluate_figure` turns a compiled spec and parameter
values into the panels' data, the shape the Reader's renderer draws and the
unit the golden corpus pins in both evaluators (G22).

Panels (RW5a): ``function_plot`` (series over ``x``, markers, shaded areas
under a series between two bounds whose values are linked integral
readouts), ``pmf_bars`` (series over the integers ``k``, a highlighted range
whose sum is its readout), ``linear_map_2d`` (the unit square and its image
under a 2x2 matrix) and ``readout`` (a labelled value, which may use
``integral()`` and ``sum()``).

RW5b's panels (§8.7; the same grammar, the same evaluators, behind
``figures.advanced_panels_enabled``): ``heatmap_2d`` (an expression over a
grid of ``x`` and ``y``, with contour levels), ``vector_field_2d`` (``u``
and ``v`` over a grid, with an optional heat map under the arrows),
``trajectory_2d`` (a 2-D system integrated by fixed-step RK4, written in the
same operation order as figureSpec.ts so the two agree step for step) and
``iterate_2d`` (a discrete map such as gradient descent). Their computation
is capped by code (:data:`MAX_HEATMAP_CELLS`, :data:`MAX_FIELD_CELLS`,
:data:`MAX_TRAJECTORY_STEPS`, :data:`MAX_ITERATIONS` and, over every point
expression, :data:`MAX_PANEL_WORK`); a point expression may use ``sum`` with
bounds the compiler can count, never ``integral``. A path is cut where it
leaves its plot (padded by :data:`ESCAPE_MARGIN`) or stops being finite, and
says so (``stopped``): nothing past either is drawn.

Predictions are decided by code, never by a model: ``direction`` compares
the observed expression before and after the prediction's change (rises,
falls, stays the same); ``area`` asks which shaded area has the observed
value.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from learnloop.figures import grammar as G

SPEC_VERSION = "ifs-v1"
#: Samples per function plot (``SAMPLES + 1`` points), identical in figureGrammar.ts.
SAMPLES = 120
MAX_PARAMETERS = 4
MAX_DEFINITIONS = 12
MAX_PANELS = 4
MAX_SERIES = 4
MAX_SHADES = 4
MAX_MARKERS = 6
MAX_INVARIANTS = 12
MAX_PREDICTIONS = 3
MAX_ANNOTATIONS = 6
MAX_ASSUMPTIONS = 8
MAX_CLAIMS = 6
MAX_BARS = 200
MAX_TEXT = 400
MAX_LABEL = 80
MAX_QUOTE = 600
MAX_STEPS = 10_000
#: The widest a function plot's x range may be (fix round 4): its samples are
#: computed from it, and the renderer pads it.
MAX_DOMAIN_SPAN = 1e12
#: RW5b (§8.7): the panels behind ``figures.advanced_panels_enabled``.
ADVANCED_KINDS = ("heatmap_2d", "vector_field_2d", "trajectory_2d", "iterate_2d")
#: Code-owned caps on computation (W4): a grid's cells per axis (cells + 1
#: samples), a trajectory's RK4 steps, a map's iterations and contour levels.
MAX_HEATMAP_CELLS = 40
DEFAULT_HEATMAP_CELLS = 40
MAX_FIELD_CELLS = 20
DEFAULT_FIELD_CELLS = 12
MAX_TRAJECTORY_STEPS = 2_000
DEFAULT_TRAJECTORY_STEPS = 400
MAX_ITERATIONS = 500
DEFAULT_ITERATIONS = 50
MAX_CONTOURS = 8
#: The most expression nodes one evaluation of the figure's RW5b panels may
#: visit (points x the expanded nodes of each point expression, a sum's body
#: counted once per term): what keeps a slider live and verification bounded.
MAX_PANEL_WORK = 250_000
#: A path is cut where it leaves its plot window padded by this share of the
#: window's span on each side (it "leaves the plot"), so nothing far outside
#: the panel range is drawn and an exploding iterate stops before overflow.
ESCAPE_MARGIN = 0.25
#: Why a path stopped (``None``: it ran every step inside the plot).
STOP_LEFT = "left_plot"
STOP_NOT_FINITE = "not_finite"
STOP_OUTSIDE = "starts_outside"
#: The answers a ``direction`` prediction offers (UX W11).
DIRECTIONS = ("rises", "falls", "same")
DIRECTION_LABELS = {"rises": "it rises", "falls": "it falls", "same": "it stays the same"}
#: Relative slack under which a change counts as "stays the same".
SAME_TOLERANCE = 1e-6


class SpecError(ValueError):
    """A spec outside the schema, the caps or the grammar; ``problems`` lists why."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = [str(problem) for problem in problems][:20]
        super().__init__("; ".join(self.problems) or "invalid figure spec")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


Text = Annotated[str, Field(max_length=MAX_TEXT)]
Label = Annotated[str, Field(max_length=MAX_LABEL)]
Expr = Annotated[str, Field(min_length=1, max_length=G.MAX_EXPR_CHARS)]


class SourceClaim(_Strict):
    span_id: Annotated[str, Field(min_length=1, max_length=200)]
    quote: Annotated[str, Field(min_length=1, max_length=MAX_QUOTE)]


class Region(_Strict):
    span_id: Annotated[str, Field(min_length=1, max_length=200)]
    bbox: Annotated[list[float], Field(min_length=4, max_length=4)]


class Assumption(_Strict):
    text: Text
    span_id: str | None = None
    quote: Annotated[str, Field(max_length=MAX_QUOTE)] | None = None


class Parameter(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)]
    label: Label
    min: float
    max: float
    step: float
    default: float
    animate: bool = False


class Definition(_Strict):
    name: Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)]
    expr: Expr


class Axis(_Strict):
    var: Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)]
    min: float
    max: float


class Series(_Strict):
    expr: Expr
    label: Label


class Marker(_Strict):
    x: Expr
    label: Label


class Shade(_Strict):
    #: The label of the series the area is under.
    series: Label
    from_: Annotated[Expr, Field(alias="from")]
    to: Expr
    label: Label


class FunctionPlot(_Strict):
    kind: Literal["function_plot"]
    x: Axis
    series: Annotated[list[Series], Field(min_length=1, max_length=MAX_SERIES)]
    markers: Annotated[list[Marker], Field(max_length=MAX_MARKERS)] = []
    shade: Annotated[list[Shade], Field(max_length=MAX_SHADES)] = []


class Highlight(_Strict):
    from_: Annotated[Expr, Field(alias="from")]
    to: Expr
    label: Label


class PmfBars(_Strict):
    kind: Literal["pmf_bars"]
    k: Axis
    series: Annotated[list[Series], Field(min_length=1, max_length=MAX_SERIES)]
    highlight: Highlight | None = None


class LinearMap2D(_Strict):
    kind: Literal["linear_map_2d"]
    matrix: Annotated[list[Annotated[list[Expr], Field(min_length=2, max_length=2)]],
                      Field(min_length=2, max_length=2)]
    label: Label = ""


class Readout(_Strict):
    kind: Literal["readout"]
    label: Label
    expr: Expr
    format: Literal["number", "percent"] = "number"


class GridAxis(_Strict):
    """A heat map's or vector field's axis: ``cells`` intervals, ``cells + 1`` samples."""

    var: Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)]
    min: float
    max: float
    cells: Annotated[int, Field(ge=1, le=MAX_HEATMAP_CELLS)] | None = None


class Heatmap2D(_Strict):
    kind: Literal["heatmap_2d"]
    x: GridAxis
    y: GridAxis
    expr: Expr
    #: Contour levels (expressions of the parameters).
    contours: Annotated[list[Expr], Field(max_length=MAX_CONTOURS)] = []
    label: Label = ""


class FieldHeatmap(_Strict):
    """The heat map under a vector field's arrows (its axes are the field's)."""

    expr: Expr
    cells: Annotated[int, Field(ge=1, le=MAX_HEATMAP_CELLS)] | None = None
    contours: Annotated[list[Expr], Field(max_length=MAX_CONTOURS)] = []
    label: Label = ""


class VectorField2D(_Strict):
    kind: Literal["vector_field_2d"]
    x: GridAxis
    y: GridAxis
    u: Expr
    v: Expr
    heatmap: FieldHeatmap | None = None
    label: Label = ""


class Trajectory2D(_Strict):
    kind: Literal["trajectory_2d"]
    #: The plot window; ``var`` names the state variables dx and dy read.
    x: Axis
    y: Axis
    x0: Expr
    y0: Expr
    dx: Expr
    dy: Expr
    t_max: Expr
    steps: Annotated[int, Field(ge=1, le=MAX_TRAJECTORY_STEPS)] = DEFAULT_TRAJECTORY_STEPS
    #: The time variable's name, when dx or dy read it (a forced system).
    time: Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)] | None = None
    label: Label = ""


class Iterate2D(_Strict):
    kind: Literal["iterate_2d"]
    x: Axis
    y: Axis
    x0: Expr
    y0: Expr
    fx: Expr
    fy: Expr
    n: Annotated[int, Field(ge=1, le=MAX_ITERATIONS)] = DEFAULT_ITERATIONS
    label: Label = ""


Panel = Annotated[Union[FunctionPlot, PmfBars, LinearMap2D, Readout, Heatmap2D, VectorField2D, Trajectory2D,
                        Iterate2D], Field(discriminator="kind")]
INVARIANT_KINDS = ("finite", "bounded", "nonnegative", "integrates_to_one", "sums_to_one",
                   "monotone_nondecreasing", "equals_source")
RANGED_INVARIANTS = ("integrates_to_one", "sums_to_one", "monotone_nondecreasing")


class Invariant(_Strict):
    kind: Literal["finite", "bounded", "nonnegative", "integrates_to_one", "sums_to_one",
                  "monotone_nondecreasing", "equals_source"]
    #: The checked expression (every kind but ``equals_source``).
    expr: Annotated[str, Field(max_length=G.MAX_EXPR_CHARS)] = ""
    #: A variable the expression is sampled, integrated or summed over, and its range.
    var: str | None = None
    from_: Annotated[float | None, Field(alias="from")] = None
    to: float | None = None
    #: ``bounded``: the largest magnitude allowed (default 1e6).
    bound: float | None = None
    #: ``equals_source``: the definition that must equal the quoted source equation.
    name: str | None = None


class Observe(_Strict):
    kind: Literal["direction", "area"]
    expr: Expr


class Prediction(_Strict):
    prompt: Text
    change: dict[str, float] = {}
    observe: Observe


class Annotation(_Strict):
    target: Label
    text: Text


class InteractiveFigureSpecV1(_Strict):
    spec_version: Literal["ifs-v1"]
    kind: Literal["reconstructed", "illustrative"]
    source_claims: Annotated[list[SourceClaim], Field(max_length=MAX_CLAIMS)] = []
    region: Region | None = None
    demonstrates: Text
    assumptions: Annotated[list[Assumption], Field(max_length=MAX_ASSUMPTIONS)] = []
    parameters: Annotated[list[Parameter], Field(max_length=MAX_PARAMETERS)] = []
    definitions: Annotated[list[Definition], Field(max_length=MAX_DEFINITIONS)] = []
    panels: Annotated[list[Panel], Field(min_length=1, max_length=MAX_PANELS)]
    invariants: Annotated[list[Invariant], Field(max_length=MAX_INVARIANTS)] = []
    predictions: Annotated[list[Prediction], Field(max_length=MAX_PREDICTIONS)] = []
    annotations: Annotated[list[Annotation], Field(max_length=MAX_ANNOTATIONS)] = []

    def dump(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)

    def canonical_json(self) -> str:
        return json.dumps(self.dump(), sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Compilation: every expression parsed, every name resolved
# ---------------------------------------------------------------------------

@dataclass
class CompiledPanel:
    kind: str
    model: Any
    nodes: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompiledFigure:
    spec: InteractiveFigureSpecV1
    parameters: list[Parameter]
    definitions: dict[str, G.Node]
    panels: list[CompiledPanel]
    invariants: list[tuple[Invariant, G.Node | None]]
    predictions: list[tuple[Prediction, G.Node]]
    variables: frozenset[str]

    @property
    def defaults(self) -> dict[str, float]:
        return {parameter.name: float(parameter.default) for parameter in self.parameters}

    def shade_labels(self) -> list[str]:
        return [shade.label for panel in self.panels if panel.kind == "function_plot" for shade in panel.model.shade]


def expanded_free(node: G.Node, definitions: Mapping[str, G.Node], bound: frozenset[str] = frozenset(),
                  _seen: tuple[str, ...] = ()) -> set[str]:
    """The variables and parameters ``node`` needs, definitions expanded
    where they are used (a bound variable reaches a definition's body).
    Iterative (fix round 4)."""

    found: set[str] = set()
    stack: list[tuple[G.Node, frozenset[str], tuple[str, ...]]] = [(node, frozenset(bound), tuple(_seen))]
    while stack:
        current, scope, seen = stack.pop()
        if current.kind == "name":
            name = current.text
            if name in scope or name in G.CONSTANTS:
                continue
            if name in definitions and name not in seen:
                stack.append((definitions[name], scope, (*seen, name)))
            else:
                found.add(name)
        elif current.kind in ("integral", "sum"):
            body, lower, upper = current.args
            stack += [(body, scope | {current.text}, seen), (lower, scope, seen), (upper, scope, seen)]
        else:
            stack += [(child, scope, seen) for child in current.args]
    return found



class _Compiler:
    def __init__(self, spec: InteractiveFigureSpecV1) -> None:
        self.spec = spec
        self.problems: list[str] = []
        self.definitions: dict[str, G.Node] = {}
        self.params = {parameter.name for parameter in spec.parameters}
        #: RW5b: the expression steps one evaluation of the panels takes.
        self.work = 0

    def problem(self, text: str) -> None:
        if len(self.problems) < 20:
            self.problems.append(text)

    def parse(self, where: str, source: str) -> G.Node | None:
        try:
            return G.parse(source)
        except G.GrammarError as exc:
            self.problem(f"{where}: {exc}")
            return None

    def needs(self, where: str, node: G.Node | None, allowed: set[str]) -> G.Node | None:
        """``node``'s names resolved against ``allowed`` (plus definitions);
        integral nesting and the expansion cap checked."""

        if node is None:
            return None
        try:
            G.check_names(node, known=frozenset(allowed | self.variables), definitions=self.definitions)
        except G.GrammarError as exc:
            self.problem(f"{where}: {exc}")
            return None
        missing = expanded_free(node, self.definitions) - allowed
        if missing:
            self.problem(f"{where}: needs {', '.join(sorted(missing))}, which is not defined here")
            return None
        return node

    def compile(self) -> CompiledFigure:
        spec = self.spec
        seen: set[str] = set()
        for parameter in spec.parameters:
            name = parameter.name
            if not G.is_name(name) or name in G.RESERVED:
                self.problem(f"parameter {name!r} is not a usable name")
            if name in seen:
                self.problem(f"parameter {name!r} is defined twice")
            seen.add(name)
            values = (parameter.min, parameter.max, parameter.step, parameter.default)
            if not all(math.isfinite(value) for value in values):
                self.problem(f"parameter {name!r} has a value that is not finite")
                continue
            if not parameter.min < parameter.max:
                self.problem(f"parameter {name!r}: min must be below max")
            if not parameter.min <= parameter.default <= parameter.max:
                self.problem(f"parameter {name!r}: default outside [min, max]")
            if parameter.step <= 0 or (parameter.max - parameter.min) / parameter.step > MAX_STEPS:
                self.problem(f"parameter {name!r}: step must be positive and at most {MAX_STEPS} steps")
        # Variables: every panel axis and every bound variable used anywhere.
        variables: set[str] = set()
        for panel in spec.panels:
            if isinstance(panel, FunctionPlot):
                variables.add(panel.x.var)
            elif isinstance(panel, PmfBars):
                variables.add(panel.k.var)
            elif isinstance(panel, ADVANCED_MODELS):
                variables |= {panel.x.var, panel.y.var}
                if isinstance(panel, Trajectory2D) and panel.time:
                    variables.add(panel.time)
        for invariant in spec.invariants:
            if invariant.var:
                variables.add(invariant.var)
        parsed_defs: list[tuple[Definition, G.Node | None]] = []
        for definition in spec.definitions:
            node = self.parse(f"definition {definition.name!r}", definition.expr)
            parsed_defs.append((definition, node))
            if node is not None:
                variables |= {child.text for child in G.walk(node) if child.kind in ("integral", "sum")}
        for source in self._all_expressions():
            node = self.parse("expression", source)
            if node is not None:
                variables |= {child.text for child in G.walk(node) if child.kind in ("integral", "sum")}
        bad = sorted(name for name in variables if not G.is_name(name) or name in G.RESERVED or name in self.params)
        for name in bad:
            self.problem(f"variable {name!r} is a reserved word or a parameter's name")
        self.variables = frozenset(variables - set(bad))
        for definition, node in parsed_defs:
            name = definition.name
            if not G.is_name(name) or name in G.RESERVED or name in self.params or name in self.variables:
                self.problem(f"definition {name!r} is not a usable name")
                continue
            if name in self.definitions:
                self.problem(f"definition {name!r} is defined twice")
                continue
            checked = self.needs(f"definition {name!r}", node, self.params | set(self.variables))
            if checked is not None:
                self.definitions[name] = checked
        panels = [self.panel(index, panel) for index, panel in enumerate(spec.panels)]
        invariants = [self.invariant(index, invariant) for index, invariant in enumerate(spec.invariants)]
        predictions = [self.prediction(index, prediction) for index, prediction in enumerate(spec.predictions)]
        if self.problems:
            raise SpecError(self.problems)
        return CompiledFigure(spec=spec, parameters=list(spec.parameters), definitions=dict(self.definitions),
                              panels=panels, invariants=invariants,  # type: ignore[arg-type]
                              predictions=predictions, variables=self.variables)  # type: ignore[arg-type]

    def _all_expressions(self) -> list[str]:
        spec = self.spec
        sources: list[str] = []
        for panel in spec.panels:
            if isinstance(panel, FunctionPlot):
                sources += [series.expr for series in panel.series] + [marker.x for marker in panel.markers]
                sources += [text for shade in panel.shade for text in (shade.from_, shade.to)]
            elif isinstance(panel, PmfBars):
                sources += [series.expr for series in panel.series]
                if panel.highlight is not None:
                    sources += [panel.highlight.from_, panel.highlight.to]
            elif isinstance(panel, LinearMap2D):
                sources += [cell for row in panel.matrix for cell in row]
            elif isinstance(panel, ADVANCED_MODELS):
                sources += advanced_expressions(panel)
            else:
                sources.append(panel.expr)
        sources += [invariant.expr for invariant in spec.invariants if invariant.expr]
        sources += [prediction.observe.expr for prediction in spec.predictions]
        return sources

    def expr(self, where: str, source: str, allowed: set[str]) -> G.Node | None:
        return self.needs(where, self.parse(where, source), allowed)

    def panel(self, index: int, panel: Any) -> CompiledPanel:
        where = f"panel {index + 1} ({panel.kind})"
        nodes: dict[str, Any] = {}
        if isinstance(panel, (FunctionPlot, PmfBars)):
            axis = panel.x if isinstance(panel, FunctionPlot) else panel.k
            if not (math.isfinite(axis.min) and math.isfinite(axis.max) and axis.min < axis.max):
                self.problem(f"{where}: its range must be finite with min below max")
            elif isinstance(panel, FunctionPlot) and axis.max - axis.min > MAX_DOMAIN_SPAN:
                # Its samples (min + span * i / SAMPLES) must not overflow (fix round 4).
                self.problem(f"{where}: its range may span at most {MAX_DOMAIN_SPAN:g}")
            if isinstance(panel, PmfBars) and math.isfinite(axis.min) and math.isfinite(axis.max):
                if axis.min != math.floor(axis.min) or axis.max != math.floor(axis.max):
                    self.problem(f"{where}: k's range must be whole numbers")
                elif abs(axis.min) > G.MAX_SAFE_INTEGER or abs(axis.max) > G.MAX_SAFE_INTEGER:
                    # Past it k + 1 == k in a double (fix round 2).
                    self.problem(f"{where}: k's range must lie within ±{G.MAX_SAFE_INTEGER}")
                elif axis.max - axis.min + 1 > MAX_BARS:
                    self.problem(f"{where}: at most {MAX_BARS} bars")
            allowed = self.params | {axis.var}
            labels = [series.label for series in panel.series]
            if len(set(labels)) != len(labels):
                self.problem(f"{where}: series labels must differ")
            nodes["series"] = [self.expr(f"{where} series {series.label!r}", series.expr, allowed)
                               for series in panel.series]
            if isinstance(panel, FunctionPlot):
                nodes["markers"] = [self.expr(f"{where} marker {marker.label!r}", marker.x, set(self.params))
                                    for marker in panel.markers]
                shades = []
                for shade in panel.shade:
                    if shade.series not in labels:
                        self.problem(f"{where}: shaded area {shade.label!r} names no series of this panel")
                    shades.append((self.expr(f"{where} shade {shade.label!r}", shade.from_, set(self.params)),
                                   self.expr(f"{where} shade {shade.label!r}", shade.to, set(self.params))))
                nodes["shades"] = shades
            elif panel.highlight is not None:
                nodes["highlight"] = (self.expr(f"{where} highlight", panel.highlight.from_, set(self.params)),
                                      self.expr(f"{where} highlight", panel.highlight.to, set(self.params)))
        elif isinstance(panel, LinearMap2D):
            nodes["matrix"] = [[self.expr(f"{where} matrix", cell, set(self.params)) for cell in row]
                               for row in panel.matrix]
        elif isinstance(panel, ADVANCED_MODELS):
            nodes = self.advanced_panel(where, panel)
        else:
            nodes["expr"] = self.expr(f"{where} {panel.label!r}", panel.expr, set(self.params))
        return CompiledPanel(panel.kind, panel, nodes)

    # -- RW5b's panels -------------------------------------------------------
    def _window(self, where: str, axes: Sequence[Any]) -> None:
        for axis in axes:
            if not (math.isfinite(axis.min) and math.isfinite(axis.max) and axis.min < axis.max):
                self.problem(f"{where}: its {axis.var} range must be finite with min below max")
            elif axis.max - axis.min > MAX_DOMAIN_SPAN:
                self.problem(f"{where}: its {axis.var} range may span at most {MAX_DOMAIN_SPAN:g}")
        names = [axis.var for axis in axes]
        if len(set(names)) != len(names):
            self.problem(f"{where}: its x and y variables must differ")

    def point_expr(self, where: str, source: str, allowed: set[str], ranges: Mapping[str, tuple[float, float]]
                   ) -> G.Node | None:
        """A per-point expression of a RW5b panel: resolved as any other, then
        no ``integral`` (its cost has no small bound) and every ``sum``'s
        bounds countable (a number, a parameter or the grid's own axis)."""

        node = self.expr(where, source, allowed)
        if node is None:
            return None
        for child, _depth in G.expansion(node, self.definitions):
            if child.kind == "integral":
                self.problem(f"{where}: an integral at every point is too much computation for this panel "
                             "(use sum, or a readout)")
                return None
            if child.kind == "sum" and _sum_terms(child, self.spec.parameters, ranges) is None:
                self.problem(f"{where}: a sum's bounds here must each be a number, a parameter or the grid's "
                             "own axis, so its terms can be counted")
                return None
        return node

    def advanced_panel(self, where: str, panel: Any) -> dict[str, Any]:
        params = set(self.params)
        self._window(where, [panel.x, panel.y])
        grid = {panel.x.var, panel.y.var}
        nodes: dict[str, Any] = {}
        if isinstance(panel, VectorField2D):
            for axis in (panel.x, panel.y):
                if axis.cells is not None and axis.cells > MAX_FIELD_CELLS:
                    self.problem(f"{where}: at most {MAX_FIELD_CELLS} arrows' cells per axis")
        if isinstance(panel, (Heatmap2D, VectorField2D)):
            ranges = {panel.x.var: (panel.x.min, panel.x.max), panel.y.var: (panel.y.min, panel.y.max)}
            cells = {"x": _cells(panel, panel.x), "y": _cells(panel, panel.y)}
            if isinstance(panel, Heatmap2D):
                nodes["expr"] = self.point_expr(f"{where} value", panel.expr, params | grid, ranges)
                nodes["contours"] = [self.expr(f"{where} contour", level, params) for level in panel.contours]
                work = (cells["x"] + 1) * (cells["y"] + 1) * self._work(nodes["expr"], ranges)
            else:
                nodes["u"] = self.point_expr(f"{where} u", panel.u, params | grid, ranges)
                nodes["v"] = self.point_expr(f"{where} v", panel.v, params | grid, ranges)
                work = (cells["x"] + 1) * (cells["y"] + 1) * (self._work(nodes["u"], ranges)
                                                               + self._work(nodes["v"], ranges))
                if panel.heatmap is not None:
                    side = _overlay_cells(panel.heatmap)
                    nodes["heatmap"] = self.point_expr(f"{where} heat map", panel.heatmap.expr, params | grid, ranges)
                    nodes["contours"] = [self.expr(f"{where} contour", level, params)
                                         for level in panel.heatmap.contours]
                    work += (side + 1) * (side + 1) * self._work(nodes["heatmap"], ranges)
        else:
            state = set(grid)
            if isinstance(panel, Trajectory2D) and panel.time:
                if panel.time in grid:
                    self.problem(f"{where}: the time variable must differ from x and y")
                state.add(panel.time)
            nodes["x0"] = self.expr(f"{where} x0", panel.x0, params)
            nodes["y0"] = self.expr(f"{where} y0", panel.y0, params)
            if isinstance(panel, Trajectory2D):
                nodes["dx"] = self.point_expr(f"{where} dx", panel.dx, params | state, {})
                nodes["dy"] = self.point_expr(f"{where} dy", panel.dy, params | state, {})
                nodes["t_max"] = self.expr(f"{where} t_max", panel.t_max, params)
                # Four stages a step, each reading dx and dy.
                work = 4 * panel.steps * (self._work(nodes["dx"], {}) + self._work(nodes["dy"], {}))
            else:
                nodes["fx"] = self.point_expr(f"{where} fx", panel.fx, params | state, {})
                nodes["fy"] = self.point_expr(f"{where} fy", panel.fy, params | state, {})
                work = panel.n * (self._work(nodes["fx"], {}) + self._work(nodes["fy"], {}))
        self.work += work
        if self.work > MAX_PANEL_WORK:
            self.problem(f"{where}: the figure's panels need more computation than a figure may do "
                         f"(about {self.work:,} expression steps; at most {MAX_PANEL_WORK:,})")
        return nodes

    def _work(self, node: G.Node | None, ranges: Mapping[str, tuple[float, float]]) -> int:
        return 0 if node is None else expression_work(node, self.definitions, self.spec.parameters, ranges)

    def invariant(self, index: int, invariant: Invariant) -> tuple[Invariant, G.Node | None]:
        where = f"invariant {index + 1} ({invariant.kind})"
        if invariant.kind == "equals_source":
            if not invariant.name or invariant.name not in {d.name for d in self.spec.definitions}:
                self.problem(f"{where}: name must be one of the definitions")
            return invariant, None
        if not invariant.expr:
            self.problem(f"{where}: needs an expression")
            return invariant, None
        allowed = set(self.params)
        if invariant.var:
            allowed.add(invariant.var)
        if invariant.kind in RANGED_INVARIANTS or invariant.var:
            if not invariant.var or invariant.from_ is None or invariant.to is None:
                self.problem(f"{where}: needs var, from and to")
            elif not (math.isfinite(invariant.from_) and math.isfinite(invariant.to)
                      and invariant.from_ < invariant.to):
                self.problem(f"{where}: from must be below to, both finite")
        return invariant, self.expr(where, invariant.expr, allowed)

    def prediction(self, index: int, prediction: Prediction) -> tuple[Prediction, G.Node | None]:
        where = f"prediction {index + 1}"
        by_name = {parameter.name: parameter for parameter in self.spec.parameters}
        for name, value in prediction.change.items():
            parameter = by_name.get(name)
            if parameter is None:
                self.problem(f"{where}: changes {name!r}, which is not a parameter")
            elif not (math.isfinite(value) and parameter.min <= value <= parameter.max):
                self.problem(f"{where}: {name} = {value} is outside its range")
        if prediction.observe.kind == "direction" and not prediction.change:
            self.problem(f"{where}: a direction prediction needs a change")
        return prediction, self.expr(where, prediction.observe.expr, set(self.params))


ADVANCED_MODELS = (Heatmap2D, VectorField2D, Trajectory2D, Iterate2D)


def advanced_expressions(panel: Any) -> list[str]:
    """Every expression of a RW5b panel."""

    if isinstance(panel, Heatmap2D):
        return [panel.expr, *panel.contours]
    if isinstance(panel, VectorField2D):
        overlay = [panel.heatmap.expr, *panel.heatmap.contours] if panel.heatmap is not None else []
        return [panel.u, panel.v, *overlay]
    if isinstance(panel, Trajectory2D):
        return [panel.x0, panel.y0, panel.dx, panel.dy, panel.t_max]
    return [panel.x0, panel.y0, panel.fx, panel.fy]


def _cells(panel: Any, axis: GridAxis) -> int:
    default = DEFAULT_HEATMAP_CELLS if isinstance(panel, Heatmap2D) else DEFAULT_FIELD_CELLS
    cap = MAX_HEATMAP_CELLS if isinstance(panel, Heatmap2D) else MAX_FIELD_CELLS
    return min(int(axis.cells if axis.cells is not None else default), cap)


def _overlay_cells(overlay: FieldHeatmap) -> int:
    return min(int(overlay.cells if overlay.cells is not None else DEFAULT_HEATMAP_CELLS), MAX_HEATMAP_CELLS)


def _bound_range(node: G.Node, parameters: Sequence[Parameter],
                 ranges: Mapping[str, tuple[float, float]]) -> tuple[float, float] | None:
    """The values a sum's bound can take, when the compiler can tell: a
    number (or its negation), a parameter (its min..max) or a grid axis."""

    if node.kind == "num":
        return node.value, node.value
    if node.kind == "neg" and node.args[0].kind == "num":
        return -node.args[0].value, -node.args[0].value
    if node.kind == "name":
        for parameter in parameters:
            if parameter.name == node.text:
                return float(parameter.min), float(parameter.max)
        if node.text in ranges:
            return ranges[node.text]
    return None


def _sum_terms(node: G.Node, parameters: Sequence[Parameter],
               ranges: Mapping[str, tuple[float, float]]) -> int | None:
    """The most terms a sum can have (its bounds' widest reach), or None
    when its bounds are not countable."""

    lower = _bound_range(node.args[1], parameters, ranges)
    upper = _bound_range(node.args[2], parameters, ranges)
    if lower is None or upper is None or not all(math.isfinite(value) for value in (*lower, *upper)):
        return None
    low = math.ceil(lower[0] - 1e-9)
    high = math.floor(upper[1] + 1e-9)
    return max(0, min(high - low + 1, G.MAX_SUM_TERMS))


def expression_work(node: G.Node, definitions: Mapping[str, G.Node], parameters: Sequence[Parameter],
                    ranges: Mapping[str, tuple[float, float]], _seen: tuple[str, ...] = ()) -> int:
    """How many nodes one evaluation of ``node`` visits at most, definitions
    expanded and a sum's body counted once per term (figureSpec.ts's
    expressionWork). Bounded by the expanded-node and depth caps the compiler
    checked first."""

    if node.kind == "name" and node.text in definitions and node.text not in _seen:
        return expression_work(definitions[node.text], definitions, parameters, ranges, (*_seen, node.text))
    if node.kind == "sum":
        terms = _sum_terms(node, parameters, ranges) or 0
        body, lower, upper = node.args
        return (1 + expression_work(lower, definitions, parameters, ranges, _seen)
                + expression_work(upper, definitions, parameters, ranges, _seen)
                + terms * expression_work(body, definitions, parameters, ranges, _seen))
    return 1 + sum(expression_work(child, definitions, parameters, ranges, _seen) for child in node.args)


def advanced_kinds(spec: InteractiveFigureSpecV1 | Mapping[str, Any]) -> list[str]:
    """The RW5b panel kinds a spec (or its JSON mapping) uses, in order."""

    panels = spec.panels if isinstance(spec, InteractiveFigureSpecV1) else (spec.get("panels") or [])
    kinds = [panel.kind if not isinstance(panel, Mapping) else panel.get("kind") for panel in panels]
    return [kind for kind in kinds if kind in ADVANCED_KINDS]


def parse_spec(raw: str | Mapping[str, Any], *, advanced: bool = True) -> CompiledFigure:
    """A spec from its JSON (or mapping), validated and compiled, or :class:`SpecError`.

    ``advanced`` (``figures.advanced_panels_enabled``): False refuses RW5b's
    panels, so an author may not emit them while the switch is off."""

    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except ValueError as exc:
        raise SpecError([f"not JSON: {exc}"]) from exc
    if not isinstance(data, dict):
        raise SpecError(["a figure spec is a JSON object"])
    try:
        spec = InteractiveFigureSpecV1.model_validate(data)
    except ValidationError as exc:
        problems = []
        for error in exc.errors()[:12]:
            where = ".".join(str(part) for part in error.get("loc", ()))
            problems.append(f"{where}: {error.get('msg')}")
        raise SpecError(problems) from exc
    if not advanced and advanced_kinds(spec):
        raise SpecError([f"{kind} panels are switched off (figures.advanced_panels_enabled)"
                         for kind in dict.fromkeys(advanced_kinds(spec))])
    try:
        return _Compiler(spec).compile()
    except RecursionError as exc:
        # A safety net only: the iterative passes and the expanded-depth cap
        # keep compilation inside the limit (fix round 4).
        raise SpecError(["an expression nests too deeply to check"]) from exc


# ---------------------------------------------------------------------------
# Evaluation: the panels' data (the golden corpus's parity unit)
# ---------------------------------------------------------------------------

def _num(value: float) -> float | None:
    """A shown value: None when not finite, never -0 (fix round 3)."""

    return G.canonical(value) if math.isfinite(value) else None


def _value(node: G.Node | None, env: Mapping[str, float], definitions: Mapping[str, G.Node]) -> float:
    return G.NAN if node is None else G.evaluate(node, env, definitions)


def plot_xs(axis: Axis) -> list[float]:
    return [G.canonical(axis.min + (axis.max - axis.min) * i / SAMPLES) for i in range(SAMPLES + 1)]


def bar_ks(axis: Axis) -> list[float]:
    """The bars' k values: counted from the support's start, at most
    :data:`MAX_BARS` of them (fix round 2; validation refuses more)."""

    low = int(axis.min)
    return [float(low + index) for index in range(max(0, min(int(axis.max) - low + 1, MAX_BARS)))]


def shade_value(compiled: CompiledFigure, panel: CompiledPanel, shade_index: int,
                env: Mapping[str, float]) -> tuple[float, float, float]:
    """A shaded area's clipped bounds and its value (the linked readout)."""

    model: FunctionPlot = panel.model
    shade = model.shade[shade_index]
    lower_node, upper_node = panel.nodes["shades"][shade_index]
    lower = _value(lower_node, env, compiled.definitions)
    upper = _value(upper_node, env, compiled.definitions)
    lower = min(max(lower, model.x.min), model.x.max) if math.isfinite(lower) else G.NAN
    upper = min(max(upper, model.x.min), model.x.max) if math.isfinite(upper) else G.NAN
    series_index = [series.label for series in model.series].index(shade.series)
    node = panel.nodes["series"][series_index]
    variable = model.x.var
    scope = dict(env)

    def at(t: float) -> float:
        scope[variable] = t
        return _value(node, scope, compiled.definitions)

    return lower, upper, G.adaptive_simpson(at, lower, upper)


def highlight_value(compiled: CompiledFigure, panel: CompiledPanel, env: Mapping[str, float]
                    ) -> tuple[float, float, float]:
    model: PmfBars = panel.model
    lower_node, upper_node = panel.nodes["highlight"]
    lower = _value(lower_node, env, compiled.definitions)
    upper = _value(upper_node, env, compiled.definitions)
    node = panel.nodes["series"][0]
    variable = model.k.var
    scope = dict(env)

    def at(k: float) -> float:
        scope[variable] = k
        return _value(node, scope, compiled.definitions)

    lower = max(lower, model.k.min) if math.isfinite(lower) else G.NAN
    upper = min(upper, model.k.max) if math.isfinite(upper) else G.NAN
    return lower, upper, G.exact_sum(at, lower, upper)


def evaluate_panel(compiled: CompiledFigure, panel: CompiledPanel, env: Mapping[str, float]) -> dict[str, Any]:
    defs = compiled.definitions
    model = panel.model
    if panel.kind == "function_plot":
        xs = plot_xs(model.x)
        series = []
        for item, node in zip(model.series, panel.nodes["series"]):
            scope = dict(env)
            ys = []
            for x in xs:
                scope[model.x.var] = x
                ys.append(_num(_value(node, scope, defs)))
            series.append({"label": item.label, "y": ys})
        shades = []
        for index, shade in enumerate(model.shade):
            lower, upper, value = shade_value(compiled, panel, index, env)
            shades.append({"label": shade.label, "series": shade.series, "from": _num(lower), "to": _num(upper),
                           "value": _num(value)})
        markers = [{"label": marker.label, "x": _num(_value(node, env, defs))}
                   for marker, node in zip(model.markers, panel.nodes["markers"])]
        return {"kind": "function_plot", "x": xs, "series": series, "shades": shades, "markers": markers}
    if panel.kind == "pmf_bars":
        ks = bar_ks(model.k)
        series = []
        for item, node in zip(model.series, panel.nodes["series"]):
            scope = dict(env)
            ps = []
            for k in ks:
                scope[model.k.var] = k
                ps.append(_num(_value(node, scope, defs)))
            series.append({"label": item.label, "p": ps})
        out: dict[str, Any] = {"kind": "pmf_bars", "k": ks, "series": series, "highlight": None}
        if model.highlight is not None:
            lower, upper, value = highlight_value(compiled, panel, env)
            out["highlight"] = {"label": model.highlight.label, "from": _num(lower), "to": _num(upper),
                                "value": _num(value)}
        return out
    if panel.kind == "linear_map_2d":
        m = [[_value(node, env, defs) for node in row] for row in panel.nodes["matrix"]]
        a, b, c, d = m[0][0], m[0][1], m[1][0], m[1][1]
        corners = [[0.0, 0.0], [a, c], [a + b, c + d], [b, d]]
        return {"kind": "linear_map_2d", "matrix": [[_num(v) for v in row] for row in m],
                "square": [[_num(x), _num(y)] for x, y in corners], "determinant": _num(a * d - b * c)}
    if panel.kind in ADVANCED_KINDS:
        return _evaluate_advanced(panel, env, defs)
    return {"kind": "readout", "label": model.label, "format": model.format,
            "value": _num(_value(panel.nodes["expr"], env, defs))}


# -- RW5b's panels (identical, operation for operation, in figureSpec.ts) ------

def grid_points(axis: Any, cells: int) -> list[float]:
    """``cells + 1`` samples from ``axis.min`` to ``axis.max``."""

    return [G.canonical(axis.min + (axis.max - axis.min) * i / cells) for i in range(cells + 1)]


def _grid_values(node: G.Node | None, xs: Sequence[float], ys: Sequence[float], xv: str, yv: str,
                 env: Mapping[str, float], defs: Mapping[str, G.Node]) -> list[list[float | None]]:
    """Rows by y, columns by x."""

    scope = dict(env)
    rows = []
    for y in ys:
        scope[yv] = y
        row = []
        for x in xs:
            scope[xv] = x
            row.append(_num(_value(node, scope, defs)))
        rows.append(row)
    return rows


def _heatmap_data(node: G.Node | None, contours: Sequence[G.Node | None], xs: list[float], ys: list[float],
                  xv: str, yv: str, label: str, env: Mapping[str, float], defs: Mapping[str, G.Node]
                  ) -> dict[str, Any]:
    return {"label": label, "x": xs, "y": ys, "z": _grid_values(node, xs, ys, xv, yv, env, defs),
            "contours": [{"level": _num(_value(level, env, defs))} for level in contours]}


def escape_box(axis: Any) -> tuple[float, float]:
    """The window a path may stay in: the axis range padded by :data:`ESCAPE_MARGIN` of its span."""

    pad = (axis.max - axis.min) * ESCAPE_MARGIN
    return axis.min - pad, axis.max + pad


def _path(model: Any, nodes: Mapping[str, Any], env: Mapping[str, float], defs: Mapping[str, G.Node]
          ) -> dict[str, Any]:
    """A trajectory (fixed-step RK4) or an iterated map, cut where it leaves
    its padded window or stops being finite (``stopped``)."""

    xv, yv = model.x.var, model.y.var
    (x_low, x_high), (y_low, y_high) = escape_box(model.x), escape_box(model.y)
    trajectory = model.kind == "trajectory_2d"
    time = model.time if trajectory else None
    scope = dict(env)
    xs: list[float] = []
    ys: list[float] = []
    steps: list[float] = []
    x = _value(nodes["x0"], env, defs)
    y = _value(nodes["y0"], env, defs)
    out: dict[str, Any] = {"kind": model.kind, "label": model.label}
    index_key = "t" if trajectory else "k"

    def done(stopped: str | None) -> dict[str, Any]:
        return {**out, index_key: steps, "x": xs, "y": ys, "stopped": stopped}

    if not (math.isfinite(x) and math.isfinite(y)):
        return done(STOP_NOT_FINITE)
    if not (x_low <= x <= x_high and y_low <= y <= y_high):
        return done(STOP_OUTSIDE)
    xs.append(G.canonical(x))
    ys.append(G.canonical(y))
    steps.append(0.0)

    def rates(px: float, py: float, pt: float, first: G.Node | None, second: G.Node | None) -> tuple[float, float]:
        scope[xv] = px
        scope[yv] = py
        if time:
            scope[time] = pt
        return _value(first, scope, defs), _value(second, scope, defs)

    if trajectory:
        count = int(model.steps)
        h = _value(nodes["t_max"], env, defs) / count
        if not (math.isfinite(h) and h > 0):
            return done(STOP_NOT_FINITE)
        half = h / 2
        t = 0.0
        for i in range(count):
            k1x, k1y = rates(x, y, t, nodes["dx"], nodes["dy"])
            k2x, k2y = rates(x + half * k1x, y + half * k1y, t + half, nodes["dx"], nodes["dy"])
            k3x, k3y = rates(x + half * k2x, y + half * k2y, t + half, nodes["dx"], nodes["dy"])
            k4x, k4y = rates(x + h * k3x, y + h * k3y, t + h, nodes["dx"], nodes["dy"])
            nx = x + h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
            ny = y + h / 6 * (k1y + 2 * k2y + 2 * k3y + k4y)
            t = h * (i + 1)
            if not (math.isfinite(nx) and math.isfinite(ny)):
                return done(STOP_NOT_FINITE)
            if not (x_low <= nx <= x_high and y_low <= ny <= y_high):
                return done(STOP_LEFT)
            x, y = nx, ny
            xs.append(G.canonical(x))
            ys.append(G.canonical(y))
            steps.append(G.canonical(t))
        return done(None)
    for k in range(int(model.n)):
        nx, ny = rates(x, y, 0.0, nodes["fx"], nodes["fy"])
        if not (math.isfinite(nx) and math.isfinite(ny)):
            return done(STOP_NOT_FINITE)
        if not (x_low <= nx <= x_high and y_low <= ny <= y_high):
            return done(STOP_LEFT)
        x, y = nx, ny
        xs.append(G.canonical(x))
        ys.append(G.canonical(y))
        steps.append(float(k + 1))
    return done(None)


def _evaluate_advanced(panel: CompiledPanel, env: Mapping[str, float], defs: Mapping[str, G.Node]
                       ) -> dict[str, Any]:
    model = panel.model
    nodes = panel.nodes
    if panel.kind == "heatmap_2d":
        xs, ys = grid_points(model.x, _cells(model, model.x)), grid_points(model.y, _cells(model, model.y))
        return {"kind": "heatmap_2d", **_heatmap_data(nodes["expr"], nodes["contours"], xs, ys, model.x.var,
                                                      model.y.var, model.label, env, defs)}
    if panel.kind == "vector_field_2d":
        xs, ys = grid_points(model.x, _cells(model, model.x)), grid_points(model.y, _cells(model, model.y))
        overlay = None
        if model.heatmap is not None:
            side = _overlay_cells(model.heatmap)
            overlay = _heatmap_data(nodes["heatmap"], nodes["contours"], grid_points(model.x, side),
                                    grid_points(model.y, side), model.x.var, model.y.var, model.heatmap.label,
                                    env, defs)
        return {"kind": "vector_field_2d", "label": model.label, "x": xs, "y": ys,
                "u": _grid_values(nodes["u"], xs, ys, model.x.var, model.y.var, env, defs),
                "v": _grid_values(nodes["v"], xs, ys, model.x.var, model.y.var, env, defs),
                "heatmap": overlay}
    return _path(model, nodes, env, defs)


def evaluate_figure(compiled: CompiledFigure, params: Mapping[str, float] | None = None) -> dict[str, Any]:
    """Every panel's data at ``params`` (defaults for the rest)."""

    env = compiled.defaults
    for name, value in (params or {}).items():
        if name in env:
            env[name] = float(value)
    return {"params": dict(env), "panels": [evaluate_panel(compiled, panel, env) for panel in compiled.panels]}


def observed(compiled: CompiledFigure, index: int, params: Mapping[str, float] | None = None) -> float:
    prediction, node = compiled.predictions[index]
    env = compiled.defaults
    env.update({name: float(value) for name, value in (params or {}).items() if name in env})
    return _value(node, env, compiled.definitions)


def prediction_outcome(compiled: CompiledFigure, index: int) -> dict[str, Any]:
    """What a prediction observes and its right answer, decided by code.

    ``direction``: the observed value at the defaults and after the change,
    and whether it rises, falls or stays the same (within
    :data:`SAME_TOLERANCE`, relative). ``area``: the shaded area (at the
    defaults) whose value is the observed one; None when no area matches or
    two do (the prediction is then not asked)."""

    prediction, _node = compiled.predictions[index]
    before = observed(compiled, index)
    if prediction.observe.kind == "direction":
        after_params = {**compiled.defaults, **prediction.change}
        after = observed(compiled, index, after_params)
        answer = None
        if math.isfinite(before) and math.isfinite(after):
            slack = SAME_TOLERANCE * max(1.0, abs(before))
            answer = "same" if abs(after - before) <= slack else ("rises" if after > before else "falls")
        return {"kind": "direction", "before": _num(before), "after": _num(after), "answer": answer,
                "choices": list(DIRECTIONS), "change": dict(prediction.change)}
    env = compiled.defaults
    areas = []
    for panel in compiled.panels:
        if panel.kind != "function_plot":
            continue
        for shade_index, shade in enumerate(panel.model.shade):
            areas.append((shade.label, shade_value(compiled, panel, shade_index, env)[2]))
    close = [label for label, value in areas
             if math.isfinite(before) and math.isfinite(value) and abs(value - before) <= 1e-6 * max(1.0, abs(before))]
    return {"kind": "area", "before": _num(before), "after": _num(before), "answer": close[0] if len(close) == 1 else None,
            "choices": [label for label, _value_ in areas], "change": {}}


__all__ = [
    "ADVANCED_KINDS",
    "DIRECTIONS",
    "MAX_FIELD_CELLS",
    "MAX_HEATMAP_CELLS",
    "MAX_ITERATIONS",
    "MAX_PANEL_WORK",
    "MAX_TRAJECTORY_STEPS",
    "advanced_kinds",
    "DIRECTION_LABELS",
    "SAMPLES",
    "SPEC_VERSION",
    "CompiledFigure",
    "CompiledPanel",
    "InteractiveFigureSpecV1",
    "SpecError",
    "evaluate_figure",
    "evaluate_panel",
    "expanded_free",
    "observed",
    "parse_spec",
    "prediction_outcome",
    "shade_value",
]
