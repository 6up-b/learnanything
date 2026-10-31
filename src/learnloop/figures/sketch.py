"""``SketchProgramV1`` and its ``Scene``: the sketch tier's data (spec_reader_show_me_figures_v1 §9.1; RW5d P2).

A sketch is a small JavaScript program the figure author writes when the
declarative grammar cannot express the idea (a random process, a simulation
with state, a geometric construction, a discrete structure). It runs in the
sealed engine (:mod:`.sketch_engine`) and returns data: a ``Scene`` (a
display list in data units, drawn by the Reader's trusted renderer as SVG
primitives) and declared **probes** (named numbers, the values table and
what claims are checked against).

This module is the schema and both validators' Python half
(``sketchScene.ts`` is the desktop's, kept identical by
``tests/test_sketch_scene_parity.py``'s shared corpus):

* :func:`parse_sketch`: the program JSON (strict keys, the caps, parameters
  as ``ifs-v1`` validates them, probes, bindings and predictions naming
  declared things, every claim expression parsed by :mod:`.grammar` with its
  names resolved);
* :func:`scene_problems`: one ``view()`` result (closed element kinds, a
  closed style palette, finite numbers everywhere, ids, the caps; no HTML,
  CSS, URLs or images can be expressed at all);
* :func:`probe_problems`: one ``probes()`` result against the declared shapes.

Interaction is the host's: sliders and fields come from ``parameters``, a
``handle`` is a draggable point bound to parameters, *play* advances the
host's clock, *new sample* changes the seed. The program never receives
pointer events, timers or keys.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from learnloop.figures import grammar as G
from learnloop.figures import spec as S

SKETCH_VERSION = "sketch-v1"
#: keep (operational): bounds a program to one idea, reviewable.
SKETCH_MAX_SOURCE_BYTES = 32_768  # 32 KiB
#: keep (display): renderer cost.
SKETCH_MAX_ELEMENTS = 4_000
#: keep (display): every coordinate the renderer draws, over all elements.
SKETCH_MAX_POINTS = 40_000
#: keep (display): one heat map's cells (64 x 64).
SKETCH_MAX_CELLS = 4_096
#: keep (display): a probe series' length (the values table, the claims).
SKETCH_MAX_SERIES = 4_000
#: keep (numerical): verification coverage of a clocked sketch.
SKETCH_TIME_SAMPLES = 9
#: keep (operational): the most steps a clock runs to t_max, so verification stays bounded.
SKETCH_MAX_CLOCK_STEPS = 2_000
#: keep (display, desktop): one frame, and how many a call may take before the Worker is paused.
SKETCH_FRAME_MS = 16
SKETCH_WATCHDOG_FRAMES = 30
#: keep (numerical): float equality, the golden corpus's tolerance.
CLAIM_REL_TOL = 1e-9
#: keep (numerical): the margin on the Richardson estimate of RK4's integration error.
ODE_SAFETY = 4.0
#: keep (numerical): how often a correct Monte Carlo sketch may be refused by chance, per check.
MC_FALSE_ALARM = 1e-6
#: The widest viewport span (as the grammar's plot range).
MAX_VIEWPORT_SPAN = S.MAX_DOMAIN_SPAN
MAX_PROBES = 12
MAX_CLAIMS = 8
MAX_BINDINGS = 16
MAX_CHOICES = 6
MAX_ID = 40
SHAPES = ("scalar", "series", "pairs")
COLORS = ("series0", "series1", "series2", "series3", "muted", "accent")
ELEMENT_KINDS = ("polyline", "polygon", "points", "segment", "arrow", "circle", "rect", "text", "heat_cells",
                 "handle")
INVARIANT_PROPERTIES = ("finite", "bounded", "nonnegative", "sums_to_one", "monotone_nondecreasing")
#: Names a sketch's claims may bind: the clock's time.
TIME_NAME = "t"
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,39}\Z")
_IDENT = re.compile(r"[A-Za-z][A-Za-z0-9]{0,31}\Z")


class SketchError(ValueError):
    """A program outside the schema, the caps or the grammar; ``problems`` lists why."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = [str(problem) for problem in problems][:20]
        super().__init__("; ".join(self.problems) or "invalid sketch")


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


Text = Annotated[str, Field(max_length=S.MAX_TEXT)]
Label = Annotated[str, Field(max_length=S.MAX_LABEL)]
Name = Annotated[str, Field(min_length=1, max_length=G.MAX_NAME_CHARS)]
Expr = Annotated[str, Field(min_length=1, max_length=G.MAX_EXPR_CHARS)]


class SketchClaimQuote(_Strict):
    span_id: Annotated[str, Field(min_length=1, max_length=200)]
    quote: Annotated[str, Field(min_length=1, max_length=S.MAX_QUOTE)]


class Clock(_Strict):
    dt: float
    t_max: float


class Probe(_Strict):
    name: Name
    label: Label
    shape: Literal["scalar", "series", "pairs"]


class Claim(_Strict):
    """What code checks (spec §9.5), each over one probe.

    * ``equals``: the probe equals ``expr`` of the parameters (and ``t``): a
      scalar as is; a series entry by entry with ``var`` bound to its index
      (``var_from + i * var_step``); a pairs probe's y with ``var`` bound to
      its x.
    * ``follows``: a pairs probe is the path of ``dx/dt = dx, dy/dt = dy``
      (``vars`` name the state; ``t`` the time) from its first point, a point
      every ``h`` time units.
    * ``invariant``: ``property`` holds over the probe's values.
    * ``distribution``: a scalar Monte Carlo estimate is within z standard
      errors of ``expr``; ``n_probe`` and ``var_probe`` are its sample size
      and sample variance.
    """

    kind: Literal["equals", "follows", "invariant", "distribution"]
    probe: Name
    expr: Annotated[str, Field(max_length=G.MAX_EXPR_CHARS)] = ""
    var: Name | None = None
    var_from: float = 0.0
    var_step: float = 1.0
    dx: Annotated[str, Field(max_length=G.MAX_EXPR_CHARS)] = ""
    dy: Annotated[str, Field(max_length=G.MAX_EXPR_CHARS)] = ""
    vars: Annotated[list[Name], Field(min_length=2, max_length=2)] = ["x", "y"]
    h: float | None = None
    property: Literal["finite", "bounded", "nonnegative", "sums_to_one", "monotone_nondecreasing"] | None = None
    bound: float | None = None
    n_probe: Name | None = None
    var_probe: Name | None = None


class Binding(_Strict):
    element_id: Annotated[str, Field(min_length=1, max_length=MAX_ID)]
    probe: Name


class SketchObserve(_Strict):
    kind: Literal["direction", "choice"]
    probe: Name
    #: ``choice``: one label per entry of the (series) probe; the answer is the largest's.
    choices: Annotated[list[Label], Field(max_length=MAX_CHOICES)] = []


class SketchPrediction(_Strict):
    prompt: Text
    #: ``{param: value}`` (re-run with the change) or ``{"run_to": t}`` (run the clock to t).
    change: dict[str, float] = {}
    observe: SketchObserve


class SketchProgramV1(_Strict):
    program_version: Literal["sketch-v1"]
    demonstrates: Text
    assumptions: Annotated[list[S.Assumption], Field(max_length=S.MAX_ASSUMPTIONS)] = []
    source_claims: Annotated[list[SketchClaimQuote], Field(max_length=S.MAX_CLAIMS)] = []
    parameters: Annotated[list[S.Parameter], Field(max_length=S.MAX_PARAMETERS)] = []
    clock: Clock | None = None
    seeded: bool = False
    code: Annotated[str, Field(min_length=1)]
    probes: Annotated[list[Probe], Field(max_length=MAX_PROBES)] = []
    claims: Annotated[list[Claim], Field(max_length=MAX_CLAIMS)] = []
    bindings: Annotated[list[Binding], Field(max_length=MAX_BINDINGS)] = []
    predictions: Annotated[list[SketchPrediction], Field(max_length=S.MAX_PREDICTIONS)] = []
    annotations: Annotated[list[S.Annotation], Field(max_length=S.MAX_ANNOTATIONS)] = []

    def dump(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)

    def canonical_json(self) -> str:
        return json.dumps(self.dump(), sort_keys=True, separators=(",", ":"))


@dataclass
class CompiledClaim:
    claim: Claim
    nodes: dict[str, G.Node] = field(default_factory=dict)


@dataclass
class CompiledSketch:
    program: SketchProgramV1
    claims: list[CompiledClaim]
    probes: dict[str, Probe]

    @property
    def parameters(self) -> list[S.Parameter]:
        return list(self.program.parameters)

    @property
    def defaults(self) -> dict[str, float]:
        return {parameter.name: float(parameter.default) for parameter in self.program.parameters}

    @property
    def steps(self) -> int:
        """How many clock steps reach ``t_max`` (0 without a clock)."""

        clock = self.program.clock
        return 0 if clock is None else clock_steps(clock)


def clock_steps(clock: Clock) -> int:
    return max(1, math.ceil(clock.t_max / clock.dt - 1e-9))


def sample_steps(compiled: CompiledSketch) -> list[int]:
    """The step indices verification reads (``SKETCH_TIME_SAMPLES`` from 0 to
    t_max; only 0 without a clock)."""

    total = compiled.steps
    if total == 0:
        return [0]
    count = SKETCH_TIME_SAMPLES
    return sorted({round(j * total / (count - 1)) for j in range(count)})


# ---------------------------------------------------------------------------
# The program
# ---------------------------------------------------------------------------

def _parse_expr(where: str, source: str, allowed: set[str], problems: list[str]) -> G.Node | None:
    try:
        node = G.parse(source)
        G.check_names(node, known=frozenset(allowed), definitions={})
    except G.GrammarError as exc:
        problems.append(f"{where}: {exc}")
        return None
    missing = G.free_names(node) - allowed
    if missing:
        problems.append(f"{where}: needs {', '.join(sorted(missing))}, which is not defined here")
        return None
    return node


def parse_sketch(raw: str | Mapping[str, Any]) -> CompiledSketch:
    """Validate a program (step 1's static half). Raises :class:`SketchError`."""

    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (TypeError, ValueError) as exc:
        raise SketchError([f"sketch_json is not JSON: {exc}"]) from exc
    try:
        program = SketchProgramV1.model_validate(data)
    except ValidationError as exc:
        raise SketchError([f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                           for error in exc.errors()[:20]]) from exc
    problems: list[str] = []
    if len(program.code.encode("utf-8")) > SKETCH_MAX_SOURCE_BYTES:
        problems.append(f"code is longer than {SKETCH_MAX_SOURCE_BYTES // 1024} KiB")
    params: set[str] = set()
    for parameter in program.parameters:
        name = parameter.name
        if not G.is_name(name) or name in G.RESERVED or name == TIME_NAME:
            problems.append(f"parameter {name!r} is not a usable name")
        if name in params:
            problems.append(f"parameter {name!r} is defined twice")
        params.add(name)
        values = (parameter.min, parameter.max, parameter.step, parameter.default)
        if not all(math.isfinite(value) for value in values):
            problems.append(f"parameter {name!r} has a value that is not finite")
            continue
        if not parameter.min < parameter.max:
            problems.append(f"parameter {name!r}: min must be below max")
        if not parameter.min <= parameter.default <= parameter.max:
            problems.append(f"parameter {name!r}: default outside [min, max]")
        if parameter.step <= 0 or (parameter.max - parameter.min) / parameter.step > S.MAX_STEPS:
            problems.append(f"parameter {name!r}: step must be positive and at most {S.MAX_STEPS} steps")
    clock = program.clock
    if clock is not None:
        if not (math.isfinite(clock.dt) and math.isfinite(clock.t_max) and clock.dt > 0 and clock.t_max > 0):
            problems.append("clock: dt and t_max must be positive numbers")
        elif clock.t_max / clock.dt > SKETCH_MAX_CLOCK_STEPS + 1e-9:
            problems.append(f"clock: t_max / dt is more than {SKETCH_MAX_CLOCK_STEPS} steps")
    probes: dict[str, Probe] = {}
    for probe in program.probes:
        if not _IDENT.match(probe.name) or probe.name in G.RESERVED:
            problems.append(f"probe {probe.name!r} is not a usable name (letters and digits)")
        if probe.name in probes:
            problems.append(f"probe {probe.name!r} is declared twice")
        probes[probe.name] = probe
    time_names = {TIME_NAME} if clock is not None else set()
    claims: list[CompiledClaim] = []
    for index, claim in enumerate(program.claims):
        where = f"claim {index + 1} ({claim.kind})"
        probe = probes.get(claim.probe)
        if probe is None:
            problems.append(f"{where}: probe {claim.probe!r} is not declared")
            continue
        compiled = CompiledClaim(claim=claim)
        allowed = params | time_names
        if claim.kind == "equals":
            var_names: set[str] = set()
            if probe.shape != "scalar":
                if not claim.var or not G.is_name(claim.var) or claim.var in G.RESERVED or claim.var in allowed:
                    problems.append(f"{where}: a {probe.shape} probe needs var, a free name for its index or x")
                    continue
                var_names = {claim.var}
                if not (math.isfinite(claim.var_from) and math.isfinite(claim.var_step)):
                    problems.append(f"{where}: var_from and var_step must be finite")
            if not claim.expr:
                problems.append(f"{where}: needs expr")
                continue
            node = _parse_expr(where, claim.expr, allowed | var_names, problems)
            if node is not None:
                compiled.nodes["expr"] = node
        elif claim.kind == "follows":
            if probe.shape != "pairs":
                problems.append(f"{where}: follows needs a pairs probe (the path's points)")
                continue
            names = set(claim.vars)
            if len(names) != 2 or any(not G.is_name(n) or n in G.RESERVED or n in allowed for n in names):
                problems.append(f"{where}: vars must be two free names")
                continue
            if claim.h is None or not math.isfinite(claim.h) or claim.h <= 0:
                problems.append(f"{where}: needs h, the time between the path's points")
                continue
            if not (claim.dx and claim.dy):
                problems.append(f"{where}: needs dx and dy")
                continue
            for key in ("dx", "dy"):
                node = _parse_expr(f"{where} {key}", getattr(claim, key), allowed | names | {TIME_NAME}, problems)
                if node is not None:
                    compiled.nodes[key] = node
        elif claim.kind == "invariant":
            if claim.property is None:
                problems.append(f"{where}: needs property")
                continue
            if claim.bound is not None and not (math.isfinite(claim.bound) and claim.bound > 0):
                problems.append(f"{where}: bound must be a positive number")
        else:  # distribution
            if probe.shape != "scalar":
                problems.append(f"{where}: a distribution claim checks a scalar estimate")
                continue
            for key in ("n_probe", "var_probe"):
                other = getattr(claim, key)
                if not other or other not in probes or probes[other].shape != "scalar":
                    problems.append(f"{where}: {key} must name a declared scalar probe")
            if not claim.expr:
                problems.append(f"{where}: needs expr (the value the estimate estimates)")
                continue
            node = _parse_expr(where, claim.expr, allowed, problems)
            if node is not None:
                compiled.nodes["expr"] = node
            if not program.seeded:
                problems.append(f"{where}: a Monte Carlo claim needs a seeded sketch (rand())")
        claims.append(compiled)
    element_ids: set[str] = set()
    for binding in program.bindings:
        if not _ID.match(binding.element_id):
            problems.append(f"binding {binding.element_id!r}: element ids are letters, digits, - and _")
        if binding.element_id in element_ids:
            problems.append(f"binding {binding.element_id!r} is bound twice")
        element_ids.add(binding.element_id)
        if binding.probe not in probes:
            problems.append(f"binding {binding.element_id!r}: probe {binding.probe!r} is not declared")
    for index, prediction in enumerate(program.predictions):
        where = f"prediction {index + 1}"
        observe = prediction.observe
        probe = probes.get(observe.probe)
        if probe is None:
            problems.append(f"{where}: probe {observe.probe!r} is not declared")
            continue
        if observe.kind == "direction" and probe.shape != "scalar":
            problems.append(f"{where}: a direction prediction observes a scalar probe")
        if observe.kind == "choice" and (probe.shape != "series" or not 2 <= len(observe.choices) <= MAX_CHOICES):
            problems.append(f"{where}: a choice prediction observes a series probe with 2-{MAX_CHOICES} choices")
        change = dict(prediction.change)
        if set(change) == {"run_to"}:
            if clock is None or not (0 < change["run_to"] <= clock.t_max):
                problems.append(f"{where}: run_to needs a clock and a time within (0, t_max]")
        elif not change or any(name not in params for name in change):
            problems.append(f"{where}: change must set declared parameters, or be {{\"run_to\": t}}")
        else:
            for name, value in change.items():
                parameter = next(p for p in program.parameters if p.name == name)
                if not (math.isfinite(value) and parameter.min <= value <= parameter.max):
                    problems.append(f"{where}: {name} = {value} is outside its range")
    if problems:
        raise SketchError(problems)
    return CompiledSketch(program=program, claims=claims, probes=probes)


# ---------------------------------------------------------------------------
# One view() result: the Scene
# ---------------------------------------------------------------------------

_STYLE_KEYS = frozenset({"color", "dash", "width", "fill", "opacity"})
_COMMON = frozenset({"type", "id", "style"})
_ELEMENT_KEYS: dict[str, frozenset[str]] = {
    "polyline": _COMMON | {"x", "y"},
    "polygon": _COMMON | {"x", "y"},
    "points": _COMMON | {"x", "y", "r"},
    "segment": _COMMON | {"x1", "y1", "x2", "y2"},
    "arrow": _COMMON | {"x1", "y1", "x2", "y2"},
    "circle": _COMMON | {"cx", "cy", "r"},
    "rect": _COMMON | {"x", "y", "w", "h"},
    "text": _COMMON | {"x", "y", "text"},
    "heat_cells": _COMMON | {"x", "y", "cols", "rows", "values"},
    "handle": frozenset({"type", "id", "x", "y", "binds"}),
}


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _describe(value: Any) -> str:
    if isinstance(value, str) and value in ("NaN", "Infinity", "-Infinity"):
        return value
    return type(value).__name__ if not isinstance(value, (int, float)) else repr(value)


class _Problems(list):
    def add(self, text: str) -> None:
        if len(self) < 12:
            self.append(text)


def _numbers(problems: _Problems, where: str, value: Any, *, limit: int) -> list[float] | None:
    if not isinstance(value, list):
        problems.add(f"{where} must be a list of numbers")
        return None
    if len(value) > limit:
        problems.add(f"{where} has {len(value)} values, more than {limit}")
        return None
    for index, item in enumerate(value):
        if not _finite(item):
            problems.add(f"{where}[{index}] is not a finite number ({_describe(item)})")
            return None
    return [float(item) for item in value]


def scene_problems(scene: Any, *, parameters: Sequence[str] = ()) -> list[str]:
    """Why a ``view()`` result can't be drawn (none: drawable). Mirrors
    ``sketchScene.ts``'s ``sceneProblems``."""

    problems = _Problems()
    if not isinstance(scene, dict):
        return ["view() must return an object {viewport, elements}"]
    extra = sorted(set(scene) - {"viewport", "elements", "axes"})
    if extra:
        problems.add(f"the scene has unknown keys {extra}")
    viewport = scene.get("viewport")
    if not isinstance(viewport, dict) or set(viewport) != {"x", "y"}:
        problems.add("viewport must be {x: [min, max], y: [min, max]}")
    else:
        for axis in ("x", "y"):
            pair = _numbers(problems, f"viewport.{axis}", viewport.get(axis), limit=2)
            if pair is not None and (len(pair) != 2 or not pair[0] < pair[1] or pair[1] - pair[0] > MAX_VIEWPORT_SPAN):
                problems.add(f"viewport.{axis} must be [min, max] with min < max")
    axes = scene.get("axes")
    if axes is not None:
        if not isinstance(axes, dict) or set(axes) - {"x_label", "y_label"}:
            problems.add("axes may have only x_label and y_label")
        else:
            for key, value in axes.items():
                if not isinstance(value, str) or len(value) > S.MAX_LABEL:
                    problems.add(f"axes.{key} must be text of at most {S.MAX_LABEL} characters")
    elements = scene.get("elements")
    if not isinstance(elements, list):
        problems.add("elements must be a list")
        return list(problems)
    if len(elements) > SKETCH_MAX_ELEMENTS:
        problems.add(f"the scene has {len(elements)} elements, more than {SKETCH_MAX_ELEMENTS}")
        return list(problems)
    known = set(parameters)
    ids: set[str] = set()
    points = 0
    for index, element in enumerate(elements):
        where = f"element {index}"
        if len(problems) >= 12:
            break
        if not isinstance(element, dict):
            problems.add(f"{where} is not an object")
            continue
        kind = element.get("type")
        if kind not in _ELEMENT_KEYS:
            problems.add(f"{where}: type {str(kind)[:40]!r} is not one of {', '.join(ELEMENT_KINDS)}")
            continue
        where = f"element {index} ({kind})"
        extra = sorted(set(element) - _ELEMENT_KEYS[kind])
        if extra:
            problems.add(f"{where}: unknown keys {extra}")
            continue
        element_id = element.get("id")
        if element_id is not None or kind == "handle":
            if not isinstance(element_id, str) or not _ID.match(element_id):
                problems.add(f"{where}: id must be letters, digits, - and _ (at most {MAX_ID})")
            elif element_id in ids:
                problems.add(f"{where}: id {element_id!r} is used twice")
            else:
                ids.add(element_id)
        style = element.get("style")
        if style is not None:
            if not isinstance(style, dict) or set(style) - _STYLE_KEYS:
                problems.add(f"{where}: style may have only {', '.join(sorted(_STYLE_KEYS))}")
            else:
                if "color" in style and style["color"] not in COLORS:
                    problems.add(f"{where}: color must be one of {', '.join(COLORS)}")
                if "width" in style and not (_finite(style["width"]) and 0 < style["width"] <= 3):
                    problems.add(f"{where}: width must be in (0, 3]")
                if "opacity" in style and not (_finite(style["opacity"]) and 0 <= style["opacity"] <= 1):
                    problems.add(f"{where}: opacity must be in [0, 1]")
                for flag in ("dash", "fill"):
                    if flag in style and not isinstance(style[flag], bool):
                        problems.add(f"{where}: {flag} must be true or false")
        if kind in ("polyline", "polygon", "points"):
            xs = _numbers(problems, f"{where}.x", element.get("x"), limit=SKETCH_MAX_POINTS)
            ys = _numbers(problems, f"{where}.y", element.get("y"), limit=SKETCH_MAX_POINTS)
            if xs is not None and ys is not None:
                if len(xs) != len(ys):
                    problems.add(f"{where}: x and y have different lengths")
                points += len(xs)
            if kind == "points" and "r" in element and not (_finite(element["r"]) and 0 < element["r"] <= 12):
                problems.add(f"{where}: r must be in (0, 12] (pixels)")
        elif kind in ("segment", "arrow"):
            for key in ("x1", "y1", "x2", "y2"):
                if not _finite(element.get(key)):
                    problems.add(f"{where}.{key} is not a finite number ({_describe(element.get(key))})")
            points += 2
        elif kind == "circle":
            for key in ("cx", "cy", "r"):
                if not _finite(element.get(key)):
                    problems.add(f"{where}.{key} is not a finite number ({_describe(element.get(key))})")
            if _finite(element.get("r")) and element["r"] < 0:
                problems.add(f"{where}: r must not be negative")
            points += 1
        elif kind == "rect":
            for key in ("x", "y", "w", "h"):
                if not _finite(element.get(key)):
                    problems.add(f"{where}.{key} is not a finite number ({_describe(element.get(key))})")
            if (_finite(element.get("w")) and element["w"] < 0) or (_finite(element.get("h")) and element["h"] < 0):
                problems.add(f"{where}: w and h must not be negative")
            points += 2
        elif kind == "text":
            for key in ("x", "y"):
                if not _finite(element.get(key)):
                    problems.add(f"{where}.{key} is not a finite number ({_describe(element.get(key))})")
            text = element.get("text")
            if not isinstance(text, str) or not text or len(text) > S.MAX_LABEL:
                problems.add(f"{where}: text must be 1-{S.MAX_LABEL} characters")
            points += 1
        elif kind == "heat_cells":
            for key in ("x", "y"):
                pair = _numbers(problems, f"{where}.{key}", element.get(key), limit=2)
                if pair is not None and (len(pair) != 2 or not pair[0] < pair[1]):
                    problems.add(f"{where}.{key} must be [min, max]")
            cols, rows = element.get("cols"), element.get("rows")
            if not (isinstance(cols, int) and isinstance(rows, int) and not isinstance(cols, bool)
                    and not isinstance(rows, bool) and cols >= 1 and rows >= 1 and cols * rows <= SKETCH_MAX_CELLS):
                problems.add(f"{where}: cols and rows must be whole numbers with at most {SKETCH_MAX_CELLS} cells")
            else:
                values = _numbers(problems, f"{where}.values", element.get("values"), limit=SKETCH_MAX_CELLS)
                if values is not None and len(values) != cols * rows:
                    problems.add(f"{where}: values must have cols * rows entries")
                points += cols * rows
        else:  # handle
            for key in ("x", "y"):
                if not _finite(element.get(key)):
                    problems.add(f"{where}.{key} is not a finite number ({_describe(element.get(key))})")
            binds = element.get("binds")
            if not isinstance(binds, dict) or not binds or set(binds) - {"x", "y"}:
                problems.add(f"{where}: binds must be {{x?: parameter, y?: parameter}}")
            else:
                for axis, name in binds.items():
                    if name not in known:
                        problems.add(f"{where}: binds.{axis} must name a parameter")
            points += 1
        if points > SKETCH_MAX_POINTS:
            problems.add(f"the scene draws more than {SKETCH_MAX_POINTS} points")
            break
    return list(problems)


def probe_problems(values: Any, probes: Mapping[str, Probe]) -> list[str]:
    """Why a ``probes()`` result does not match the declared probes (every
    declared one present, of its shape, every number finite; undeclared
    names are ignored, never shown)."""

    problems = _Problems()
    if not isinstance(values, dict):
        return ["probes() must return an object of the declared probes"]
    for name, probe in probes.items():
        if name not in values:
            problems.add(f"probe {name!r} is missing")
            continue
        value = values[name]
        if probe.shape == "scalar":
            if not _finite(value):
                problems.add(f"probe {name!r} is not a finite number ({_describe(value)})")
        elif probe.shape == "series":
            _numbers(problems, f"probe {name!r}", value, limit=SKETCH_MAX_SERIES)
        else:
            if not isinstance(value, list) or len(value) > SKETCH_MAX_SERIES:
                problems.add(f"probe {name!r} must be a list of [x, y] pairs (at most {SKETCH_MAX_SERIES})")
                continue
            for index, pair in enumerate(value):
                if not (isinstance(pair, list) and len(pair) == 2 and _finite(pair[0]) and _finite(pair[1])):
                    problems.add(f"probe {name!r}[{index}] is not a pair of finite numbers")
                    break
    return list(problems)


def probe_numbers(value: Any, shape: str) -> list[float]:
    """A validated probe's values as one list (a pairs probe's y values)."""

    if shape == "scalar":
        return [float(value)]
    if shape == "series":
        return [float(item) for item in value]
    return [float(pair[1]) for pair in value]


def element_index(scene: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(element["id"]): element for element in scene.get("elements") or () if element.get("id") is not None}


__all__ = [
    "CLAIM_REL_TOL",
    "COLORS",
    "Claim",
    "CompiledClaim",
    "CompiledSketch",
    "ELEMENT_KINDS",
    "MC_FALSE_ALARM",
    "ODE_SAFETY",
    "Probe",
    "SKETCH_FRAME_MS",
    "SKETCH_MAX_CELLS",
    "SKETCH_MAX_CLOCK_STEPS",
    "SKETCH_MAX_ELEMENTS",
    "SKETCH_MAX_POINTS",
    "SKETCH_MAX_SERIES",
    "SKETCH_MAX_SOURCE_BYTES",
    "SKETCH_TIME_SAMPLES",
    "SKETCH_VERSION",
    "SKETCH_WATCHDOG_FRAMES",
    "SketchError",
    "SketchProgramV1",
    "clock_steps",
    "element_index",
    "parse_sketch",
    "probe_numbers",
    "probe_problems",
    "sample_steps",
    "scene_problems",
]
