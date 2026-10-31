"""Headless verification of a sketch (spec_reader_show_me_figures_v1 §9.5; RW5d P2).

Run in the sidecar, in the sealed engine (:mod:`.sketch_engine`), after the
program parses and before anything is stored as shown. Steps 1-4 decide
whether a sketch is shown at all; step 5 decides what it may claim.

1. **Structure.** :func:`.sketch.parse_sketch` (the JSON, the caps,
   parameters as ``ifs-v1``'s, probes, bindings and predictions naming
   declared things, claim expressions in the grammar); then the code loads in
   the engine and defines ``init``, ``view``, ``probes`` (and ``step`` with a
   clock).
2. **Runs everywhere it can be moved.** On RW5a's parameter grid (each
   parameter at min, default and max: at most 81 points) and, with a clock,
   at :data:`.sketch.SKETCH_TIME_SAMPLES` points from 0 to ``t_max``: every
   call returns within the engine's caps, every scene validates
   (:func:`.sketch.scene_problems`) and every probe is finite and of its
   declared shape (:func:`.sketch.probe_problems`).
3. **Deterministic.** A second run in a fresh engine, the grid in reverse
   order, with extra ``view``/``probes`` calls in between, gives the same
   scenes and probes as text (catches reliance on hidden state or on
   anything the shim refuses).
4. **Bindings hold.** At every point read, each bound element's coordinates
   equal its probe's values exactly (one run produced both), which is what
   lets a check speak for a drawn element.
5. **Claims.** Each claim is checked by code (the grammar's Python evaluator
   is the oracle) at the same points: ``equals`` within
   :data:`.sketch.CLAIM_REL_TOL`; ``follows`` against the grammar's RK4 at
   the path's step, the tolerance the difference from a half-step run (a
   Richardson estimate) times :data:`.sketch.ODE_SAFETY`; ``invariant`` as
   RW5a's property checks; ``distribution`` within z standard errors, z for a
   :data:`.sketch.MC_FALSE_ALARM` false alarm per check.

**Outcomes.** Steps 1-4 fail, or a claim fails: ``failed``, never shown (the
second author attempt is told why). Otherwise ``illustrative``: the passing
checks become code-owned check lines (each naming the bound elements or the
probe by their identifiers, the stated equation as the grammar parsed it,
marked AI-stated, and how many settings were tested), and drawn elements no
check covers are named as *not covered*. No claim at all: *nothing in it
checked*. Never "matches the book" (that is RW5c's question).
"""

from __future__ import annotations

import json
import math
import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures import sketch as K
from learnloop.figures import verify as V
from learnloop.figures.sketch_engine import ENGINE_SHA256, SketchEngine, SketchRunError

#: The seed every verification run (and a sketch's first drawn sample) uses.
VERIFY_SEED = 1
#: Words for an invariant's property in a check line (closed, code-owned).
PROPERTY_WORDS = {"finite": "finite", "bounded": "bounded", "nonnegative": "never negative",
                  "sums_to_one": "sums to one", "monotone_nondecreasing": "never decreasing"}

EngineFactory = Callable[[], SketchEngine]


@dataclass
class SketchReport:
    """What verification found, as stored in ``verification_report_json``."""

    outcome: str = V.FAILED
    reason: str = ""
    #: Which step failed (``structure``, ``runs``, ``deterministic``, ``bindings``, ``claims``), if one did.
    failed_step: str | None = None
    problems: list[str] = field(default_factory=list)
    grid_points: int = 0
    samples: list[int] = field(default_factory=list)
    settings: int = 0
    checks: list[dict[str, Any]] = field(default_factory=list)
    not_covered: list[str] = field(default_factory=list)
    unnamed_elements: int = 0
    dropped_predictions: list[int] = field(default_factory=list)
    claims: list[dict[str, Any]] = field(default_factory=list)
    engine_sha256: str = ENGINE_SHA256
    #: The first runtime error, as the engine wrote it (prefills "not right?").
    runtime_error: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome, "reason": self.reason, "failed_step": self.failed_step,
            "problems": self.problems[:12], "grid_points": self.grid_points, "samples": self.samples,
            "settings": self.settings, "checks": self.checks, "not_covered": self.not_covered[:40],
            "unnamed_elements": self.unnamed_elements, "dropped_predictions": self.dropped_predictions,
            "claims": self.claims, "engine_sha256": self.engine_sha256, "runtime_error": self.runtime_error,
            "tier": "sketch",
        }


class _Failed(Exception):
    def __init__(self, step: str, problems: Sequence[str], runtime: dict[str, Any] | None = None) -> None:
        super().__init__(problems[0] if problems else step)
        self.step = step
        self.problems = list(problems)[:12]
        self.runtime = runtime


def _point_text(point: Mapping[str, float]) -> str:
    return ", ".join(f"{name}={value:g}" for name, value in point.items()) or "the defaults"


def _env(compiled: K.CompiledSketch, point: Mapping[str, float], step: int) -> dict[str, float]:
    env = compiled.defaults
    env.update(point)
    clock = compiled.program.clock
    if clock is not None:
        env[K.TIME_NAME] = step * clock.dt
    return env


@dataclass
class _Sample:
    point: dict[str, float]
    step: int
    scene: Any
    probes: Any
    scene_text: str
    probes_text: str


def _run(compiled: K.CompiledSketch, engine: SketchEngine, grid: Sequence[Mapping[str, float]],
         steps: Sequence[int], *, extra_reads: bool = False) -> list[_Sample]:
    """Load, then at every grid point init and read each sampled step (the
    grid in the given order). Raises :class:`_Failed` (``runs``)."""

    program = compiled.program
    try:
        entries = engine.load(program.code)
    except SketchRunError as exc:
        raise _Failed("structure", [f"the code does not load: {exc.message}"],
                      {"message": exc.message, "params": None}) from exc
    needed = ["init", "view", "probes"] + (["step"] if program.clock is not None else [])
    missing = [name for name in needed if not entries.get(name)]
    if missing:
        raise _Failed("structure", [f"the code defines no {', '.join(name + '()' for name in missing)}"])
    names = [parameter.name for parameter in program.parameters]
    samples: list[_Sample] = []
    for point in grid:
        params = {**compiled.defaults, **point}
        samples.extend(_read_all(compiled, engine, params, point, steps, names, extra_reads=extra_reads))
    return samples


def _read_all(compiled: K.CompiledSketch, engine: SketchEngine, params: Mapping[str, float],
              point: Mapping[str, float], steps: Sequence[int], names: Sequence[str], *,
              extra_reads: bool) -> list[_Sample]:
    """Init at one grid point and read every sampled step (validated)."""

    program = compiled.program
    dt = program.clock.dt if program.clock is not None else 0.0
    out: list[_Sample] = []
    try:
        engine.init(params, VERIFY_SEED)
        at = 0
        for step in steps:
            if step > at:
                engine.step(params, dt, index=at, count=step - at)
                at = step
            if extra_reads:
                engine.probes_text(params, index=step)
                engine.view_text(params, index=step)
            scene_text = engine.view_text(params, index=step)
            probes_text = engine.probes_text(params, index=step)
            scene, probes = json.loads(scene_text), json.loads(probes_text)
            where = _point_text(point) + (f", t={step * dt:g}" if program.clock is not None else "")
            problems = K.scene_problems(scene, parameters=names)
            if problems:
                raise _Failed("runs", [f"at {where}: the scene {problems[0]}", *problems[1:4]],
                              {"message": problems[0], "params": dict(params), "kind": "scene"})
            problems = K.probe_problems(probes, compiled.probes)
            if problems:
                raise _Failed("runs", [f"at {where}: {problems[0]}", *problems[1:4]],
                              {"message": problems[0], "params": dict(params), "kind": "probe"})
            out.append(_Sample(point=dict(point), step=step, scene=scene, probes=probes, scene_text=scene_text,
                               probes_text=probes_text))
    except SketchRunError as exc:
        raise _Failed("runs", [f"at {_point_text(point)}: {exc.message}"],
                      {"message": exc.message, "params": dict(params), "kind": exc.kind}) from exc
    return out


def _bindings(compiled: K.CompiledSketch, samples: Sequence[_Sample]) -> list[str]:
    problems: list[str] = []
    for sample in samples:
        elements = K.element_index(sample.scene)
        for binding in compiled.program.bindings:
            probe = compiled.probes[binding.probe]
            element = elements.get(binding.element_id)
            where = f"at {_point_text(sample.point)}"
            if element is None:
                problems.append(f"{where}: bound element {binding.element_id!r} is not drawn")
                return problems
            value = sample.probes[binding.probe]
            if not _bound_equal(element, value, probe.shape):
                problems.append(f"{where}: element {binding.element_id!r} is not drawn at probe "
                                f"{binding.probe!r}'s values")
                return problems
    return problems


def _bound_equal(element: Mapping[str, Any], value: Any, shape: str) -> bool:
    kind = element.get("type")
    if kind in ("polyline", "polygon", "points"):
        if shape == "pairs":
            return [float(x) for x in element["x"]] == [float(p[0]) for p in value] and \
                [float(y) for y in element["y"]] == [float(p[1]) for p in value]
        if shape == "series":
            return [float(y) for y in element["y"]] == [float(v) for v in value]
        return False
    if kind == "heat_cells":
        return shape == "series" and [float(v) for v in element["values"]] == [float(v) for v in value]
    if kind == "circle":
        return shape == "scalar" and float(element["r"]) == float(value)
    if kind in ("segment", "arrow"):
        return shape == "pairs" and len(value) == 2 and [float(element[k]) for k in ("x1", "y1", "x2", "y2")] == \
            [float(value[0][0]), float(value[0][1]), float(value[1][0]), float(value[1][1])]
    return False


def _close(value: float, expected: float) -> bool:
    return math.isfinite(expected) and abs(value - expected) <= K.CLAIM_REL_TOL * max(1.0, abs(expected))


def _z() -> float:
    return statistics.NormalDist().inv_cdf(1.0 - K.MC_FALSE_ALARM / 2.0)


def _rk4(dx: G.Node, dy: G.Node, names: Sequence[str], env: Mapping[str, float], x: float, y: float, h: float,
         steps: int) -> list[tuple[float, float]]:
    """The grammar's fixed-step RK4 (``spec._path``'s operation order)."""

    xv, yv = names
    scope = dict(env)

    def rates(px: float, py: float, pt: float) -> tuple[float, float]:
        scope[xv], scope[yv], scope[K.TIME_NAME] = px, py, pt
        return G.evaluate(dx, scope), G.evaluate(dy, scope)

    out = [(x, y)]
    half = h / 2
    t = 0.0
    for i in range(steps):
        k1x, k1y = rates(x, y, t)
        k2x, k2y = rates(x + half * k1x, y + half * k1y, t + half)
        k3x, k3y = rates(x + half * k2x, y + half * k2y, t + half)
        k4x, k4y = rates(x + h * k3x, y + h * k3y, t + h)
        x = x + h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
        y = y + h / 6 * (k1y + 2 * k2y + 2 * k3y + k4y)
        t = h * (i + 1)
        out.append((x, y))
    return out


def check_claim(compiled: K.CompiledSketch, claim: K.CompiledClaim, sample: _Sample) -> str | None:
    """One claim at one point read: None when it holds, else why not."""

    spec = claim.claim
    probe = compiled.probes[spec.probe]
    value = sample.probes[spec.probe]
    env = _env(compiled, sample.point, sample.step)
    where = f"at {_point_text(sample.point)}" + (f", t={env[K.TIME_NAME]:g}" if K.TIME_NAME in env else "")
    if spec.kind == "equals":
        node = claim.nodes["expr"]
        if probe.shape == "scalar":
            expected = G.evaluate(node, env)
            return None if _close(float(value), expected) else \
                f"{where}: {spec.probe} is {float(value):.10g}, the stated {spec.expr} is {expected:.10g}"
        entries = (list(enumerate(value)) if probe.shape == "series" else [(None, pair) for pair in value])
        for index, entry in entries:
            if probe.shape == "series":
                env[spec.var] = spec.var_from + index * spec.var_step
                got = float(entry)
            else:
                env[spec.var] = float(entry[0])
                got = float(entry[1])
            expected = G.evaluate(node, env)
            if not _close(got, expected):
                return f"{where}: {spec.probe} at {spec.var}={env[spec.var]:g} is {got:.10g}, " \
                       f"the stated {spec.expr} is {expected:.10g}"
        return None
    if spec.kind == "follows":
        path = [(float(p[0]), float(p[1])) for p in value]
        if len(path) < 2:
            return f"{where}: {spec.probe} has fewer than two points"
        steps = len(path) - 1
        h = float(spec.h)
        full = _rk4(claim.nodes["dx"], claim.nodes["dy"], spec.vars, env, path[0][0], path[0][1], h, steps)
        half = _rk4(claim.nodes["dx"], claim.nodes["dy"], spec.vars, env, path[0][0], path[0][1], h / 2, 2 * steps)
        for i, (px, py) in enumerate(path):
            fx, fy = full[i]
            hx, hy = half[2 * i]
            if not all(math.isfinite(v) for v in (fx, fy, hx, hy)):
                return f"{where}: the stated system is not finite along the path"
            for got, want, estimate in ((px, fx, hx), (py, fy, hy)):
                tolerance = K.ODE_SAFETY * abs(want - estimate) + K.CLAIM_REL_TOL * max(1.0, abs(want))
                if abs(got - want) > tolerance:
                    return f"{where}: point {i} of {spec.probe} is off the stated system's path by {abs(got - want):.3g}"
        return None
    if spec.kind == "invariant":
        numbers = K.probe_numbers(value, probe.shape)
        prop = spec.property
        if prop == "finite":
            return None
        if prop == "bounded":
            bound = float(spec.bound if spec.bound is not None else V.DEFAULT_BOUND)
            worst = max((abs(v) for v in numbers), default=0.0)
            return None if worst <= bound else f"{where}: {spec.probe} reaches {worst:.6g}, past {bound:g}"
        if prop == "nonnegative":
            worst = min(numbers, default=0.0)
            return None if worst >= -V.NONNEGATIVE_SLACK else f"{where}: {spec.probe} goes negative ({worst:.6g})"
        if prop == "sums_to_one":
            total = math.fsum(numbers)
            return None if abs(total - 1.0) <= V.PMF_TOLERANCE else f"{where}: {spec.probe} sums to {total:.12g}"
        for left, right in zip(numbers, numbers[1:]):
            if right < left - V.MONOTONE_SLACK * max(1.0, abs(left)):
                return f"{where}: {spec.probe} decreases from {left:.6g} to {right:.6g}"
        return None
    # distribution
    n = float(sample.probes[spec.n_probe])
    variance = float(sample.probes[spec.var_probe])
    if not (n >= 2 and variance >= 0):
        return f"{where}: {spec.n_probe} must be at least 2 and {spec.var_probe} not negative"
    expected = G.evaluate(claim.nodes["expr"], env)
    if not math.isfinite(expected):
        return f"{where}: the stated {spec.expr} is not finite"
    margin = _z() * math.sqrt(variance / n) + K.CLAIM_REL_TOL * max(1.0, abs(expected))
    estimate = float(value)
    return None if abs(estimate - expected) <= margin else \
        f"{where}: {spec.probe} is {estimate:.6g}, more than {margin:.3g} from the stated {spec.expr} ({expected:.6g})"


def _statement(claim: K.Claim) -> str:
    if claim.kind == "follows":
        return f"d{claim.vars[0]}/dt = {' '.join(claim.dx.split())}, d{claim.vars[1]}/dt = {' '.join(claim.dy.split())}"
    if claim.kind == "invariant":
        return PROPERTY_WORDS.get(str(claim.property), str(claim.property))
    return " ".join(claim.expr.split())


def prediction_outcome(compiled: K.CompiledSketch, engine: SketchEngine, index: int, *,
                       seed: int = VERIFY_SEED) -> dict[str, Any]:
    """What a sketch's prediction observes and its answer, decided by code in
    the engine. A parameter change compares the probe before and after (at the
    first step without a clock, at ``t_max`` with one); ``run_to`` compares
    step 0 with the step at that time. ``choice`` names the largest entry of
    the observed series after the change (None on a tie)."""

    program = compiled.program
    prediction = program.predictions[index]
    observe = prediction.observe
    probe = compiled.probes[observe.probe]
    defaults = compiled.defaults
    clock = program.clock
    change = dict(prediction.change)
    dt = clock.dt if clock is not None else 0.0

    def read(params: Mapping[str, float], step: int) -> Any:
        engine.init(params, seed)
        if step:
            engine.step(params, dt, index=0, count=step)
        values = engine.probes(params, index=step)
        problems = K.probe_problems(values, compiled.probes)
        if problems:
            raise SketchRunError(1, problems[0])
        return values[observe.probe]

    if set(change) == {"run_to"}:
        assert clock is not None
        before = read(defaults, 0)
        after = read(defaults, min(compiled.steps, max(1, round(change["run_to"] / clock.dt))))
    else:
        end = compiled.steps
        before = read(defaults, end)
        after = read({**defaults, **change}, end)
    if observe.kind == "direction":
        b, a = float(before), float(after)
        slack = 1e-6 * max(1.0, abs(b))
        answer = "same" if abs(a - b) <= slack else ("rises" if a > b else "falls")
        return {"kind": "direction", "before": b, "after": a, "answer": answer, "choices": ["rises", "falls", "same"],
                "change": change}
    series = [float(v) for v in after]
    labels = list(observe.choices)
    answer = None
    if len(series) == len(labels) and series:
        top = max(series)
        winners = [label for label, v in zip(labels, series) if abs(v - top) <= 1e-6 * max(1.0, abs(top))]
        answer = winners[0] if len(winners) == 1 else None
    return {"kind": "choice", "before": None, "after": None, "answer": answer, "choices": labels, "change": change}


def verify_sketch(compiled: K.CompiledSketch, *, engine_factory: EngineFactory = SketchEngine,
                  span_texts: Mapping[str, str] | None = None) -> SketchReport:
    """Steps 2-5 on a parsed program (step 1's static half is
    :func:`.sketch.parse_sketch`): ``failed`` with the reason, or
    ``illustrative`` with its check lines."""

    report = SketchReport()
    grid = V.parameter_grid(compiled)  # type: ignore[arg-type]
    steps = K.sample_steps(compiled)
    report.grid_points, report.samples = len(grid), steps
    report.claims = [{"span_id": claim.span_id, "quote": claim.quote,
                      "verified": bool(span_texts) and claim.span_id in (span_texts or {})
                      and V.quote_in(claim.quote, (span_texts or {})[claim.span_id])}
                     for claim in compiled.program.source_claims]
    first = engine_factory()
    try:
        try:
            samples = _run(compiled, first, grid, steps)
            report.settings = len(samples)
            second = engine_factory()
            try:
                again = _run(compiled, second, list(reversed(grid)), steps, extra_reads=True)
            finally:
                second.close()
            texts = {(json.dumps(s.point, sort_keys=True), s.step): (s.scene_text, s.probes_text) for s in samples}
            for sample in again:
                if texts.get((json.dumps(sample.point, sort_keys=True), sample.step)) != (sample.scene_text,
                                                                                        sample.probes_text):
                    raise _Failed("deterministic", [f"at {_point_text(sample.point)}: a second run gives different "
                                                    "values (it may not depend on anything but its inputs and rand())"])
            problems = _bindings(compiled, samples)
            if problems:
                raise _Failed("bindings", problems)
            failures: list[str] = []
            checks: list[dict[str, Any]] = []
            bound = {}
            for binding in compiled.program.bindings:
                bound.setdefault(binding.probe, []).append(binding.element_id)
            for index, claim in enumerate(compiled.claims):
                problem = next((p for p in (check_claim(compiled, claim, s) for s in samples) if p), None)
                if problem is not None:
                    failures.append(f"claim {index + 1} ({claim.claim.kind}) fails {problem}")
                    continue
                checks.append({"claim": index, "kind": claim.claim.kind, "probe": claim.claim.probe,
                               "elements": list(bound.get(claim.claim.probe, ())),
                               "statement": _statement(claim.claim), "settings": len(samples)})
            if failures:
                raise _Failed("claims", failures)
            report.checks = checks
            covered = {element for check in checks for element in check["elements"]}
            # What the learner first sees: the defaults at the first step.
            defaults_point = compiled.defaults
            defaults_scene = next((s.scene for s in samples if s.step == steps[0]
                                   and all(s.point.get(k, v) == v for k, v in defaults_point.items())), None)
            drawn = [element for element in (defaults_scene or {}).get("elements") or ()
                     if element.get("type") != "handle"]
            report.not_covered = [str(element["id"]) for element in drawn
                                  if element.get("id") is not None and element["id"] not in covered]
            report.unnamed_elements = sum(1 for element in drawn if element.get("id") is None)
            for index in range(len(compiled.program.predictions)):
                try:
                    if prediction_outcome(compiled, first, index).get("answer") is None:
                        report.dropped_predictions.append(index)
                except SketchRunError:
                    report.dropped_predictions.append(index)
        except _Failed as failed:
            report.outcome, report.failed_step = V.FAILED, failed.step
            report.problems = failed.problems
            report.reason = failed.problems[0] if failed.problems else failed.step
            if failed.runtime is not None:
                report.runtime_error = failed.runtime
            return report
    finally:
        first.close()
    report.outcome = V.ILLUSTRATIVE
    return report


__all__ = [
    "PROPERTY_WORDS",
    "SketchReport",
    "VERIFY_SEED",
    "check_claim",
    "prediction_outcome",
    "verify_sketch",
]
