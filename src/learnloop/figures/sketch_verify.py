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
   parameter at min, default and max: at most 81 points), each point a run
   **as the desktop plays it** (Astra sandbox review, finding 1): a freshly
   loaded program, ``init``, then every step of the read schedule
   (:func:`.sketch.read_steps`: play's ticks, the checked samples and the
   graded steps) stepped to and read, ``view()`` then ``probes()``. Every
   call returns within the engine's caps, every scene validates
   (:func:`.sketch.scene_problems`) and every probe is finite and of its
   declared shape (:func:`.sketch.probe_problems`).
3. **Deterministic.** A second run in a fresh engine, the grid in reverse
   order, reading only the checked samples with extra ``view``/``probes``
   calls before each, gives the same scenes and probes as text (catches a
   program whose reads change what it later shows, and anything the shim
   refuses). Whatever this misses, the first run read the schedule every
   run reads, so what it checked is what any run draws at those states; the
   desktop also compares the digests (below).
4. **Bindings hold.** At every step read, each bound element's coordinates
   equal its probe's values exactly (one run produced both), which is what
   lets a check speak for a drawn element.
5. **Claims.** Each claim is checked by code (the grammar's Python evaluator
   is the oracle) at the checked samples (:data:`.sketch.SKETCH_TIME_SAMPLES`
   of the schedule's steps from 0 to ``t_max``): ``equals`` within
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

**What the desktop compares** (Astra, finding 1). The report carries the read
schedule (``read_steps``) and, for every grid point, the digest
(:func:`tested_digest`) of each checked read as the engine wrote it
(``tested``). The desktop computes the same digest for every read it makes;
at a tested state (the grid point's parameters, the verified seed, a checked
step) a different digest withdraws the code-owned checks for that figure,
which then shows as an illustration. Agreement is what lets a check line
speak for what is on the page.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnloop.figures import grammar as G
from learnloop.figures import sketch as K
from learnloop.figures import verify as V
from learnloop.figures.sketch_engine import ENGINE_SHA256, SketchEngine, SketchRunError

#: The seed every verification run (and a sketch's first drawn sample) uses.
VERIFY_SEED = 1
#: The version of what verification decides and reports (Codex review F11,
#: round 3), stored in every report. **Bump it whenever verification's
#: semantics change** (what passes, what a check line or *not covered* says),
#: even when the engine is the same: a stored report from another version is
#: verified again by code before it is shown (``service.sketch_rechecked``),
#: as one from another engine is. Reports without it are from before it
#: existed (round 2's verifier and earlier). v3 (fix round 4, the independent
#: sandbox review): every init on a freshly loaded program, the read schedule,
#: and the digests of every tested read.
VERIFIER_REPORT_VERSION = "sketch-verify-v3"
#: How many hex digits of a read's SHA-256 a report keeps per tested state
#: (128 bits: a program can't search for a collision with its own output).
TESTED_DIGEST_HEX = 32
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
    verifier_version: str = field(default_factory=lambda: VERIFIER_REPORT_VERSION)
    #: The first runtime error, as the engine wrote it (prefills "not right?").
    runtime_error: dict[str, Any] | None = None
    #: The read schedule every run of this sketch follows (:func:`.sketch.read_steps`).
    read_steps: list[int] = field(default_factory=list)
    #: Per grid point: its parameter values (in declared order), the checked
    #: steps and the digest of each read there (what the desktop compares).
    tested: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome, "reason": self.reason, "failed_step": self.failed_step,
            "problems": self.problems[:12], "grid_points": self.grid_points, "samples": self.samples,
            "settings": self.settings, "checks": self.checks, "not_covered": self.not_covered[:40],
            "unnamed_elements": self.unnamed_elements, "dropped_predictions": self.dropped_predictions,
            "claims": self.claims, "engine_sha256": self.engine_sha256,
            "verifier_version": self.verifier_version, "runtime_error": self.runtime_error,
            "read_steps": self.read_steps, "tested": self.tested, "tier": "sketch",
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


class _Budget(G.Meter):
    """Verification's own limits (Codex review F1, F2): the engine output it
    reads (:data:`.sketch.SKETCH_MAX_VERIFY_OUTPUT_BYTES`), the claim work it
    may do (:data:`.sketch.SKETCH_MAX_CLAIM_WORK`) and its wall clock
    (:data:`.sketch.SKETCH_VERIFY_SECONDS`, also every engine call's deadline).

    **Claim work is metered, not estimated** (Codex review F2, round 3). The
    budget is the :class:`.grammar.Meter` every claim check's grammar
    evaluation is charged to, one step per node at the point it is evaluated
    (each RK4 stage, every term of a sum, every integrand evaluation): when
    the claims pass the cap the check stops there, refused as too much
    computation, and every :data:`_TICK_WORK` steps the meter looks at the
    clock, so the deadline stops even one long evaluation. A check's static
    estimate (:attr:`.sketch.CompiledClaim.entry_work`) is still looked at
    first (:meth:`foresee`), but only to refuse early what plainly can't fit;
    the cap holds without it."""

    def __init__(self, deadline: float) -> None:
        super().__init__(K.SKETCH_MAX_CLAIM_WORK, _TICK_WORK)
        self.deadline = deadline
        self.output = 0

    @property
    def work(self) -> int:
        """The claim work done so far: grammar steps actually evaluated."""

        return self.used

    def read(self, *texts: str) -> None:
        self.output += sum(len(text) for text in texts)
        if self.output > K.SKETCH_MAX_VERIFY_OUTPUT_BYTES:
            raise _Failed("runs", [f"the sketch's results are too large to verify (more than "
                                   f"{K.SKETCH_MAX_VERIFY_OUTPUT_BYTES // (1024 * 1024)} MiB over its tested settings)"])

    def _refuse(self, steps: int) -> None:
        raise _Failed("claims", [f"the claims need more computation than verification may do (at least "
                                 f"{steps:,} expression steps; at most {self.limit:,})"])

    def foresee(self, work: int) -> None:
        """An early refusal, before anything is evaluated, of a check whose
        estimate cannot fit in what is left. Nothing is charged: the meter
        charges what actually runs."""

        if self.used + work > self.limit:
            self._refuse(self.used + work)

    def exhausted(self) -> None:  # the meter passed the cap mid-evaluation
        self._refuse(self.used)

    def checkpoint(self) -> None:  # every _TICK_WORK metered steps
        self.tick()

    def tick(self) -> None:
        if time.monotonic() > self.deadline:
            raise _Failed("runs", [f"the sketch takes longer than {K.SKETCH_VERIFY_SECONDS:g} s to verify"])


#: How many metered expression steps pass between the claim checks' looks at
#: the clock (about a millisecond of the oracle).
_TICK_WORK = 4_096


@dataclass
class _Sample:
    """One point read: the parsed scene and probes, held only while it is
    validated, bound and checked (never kept: Codex review F1)."""

    point: dict[str, float]
    step: int
    scene: Any
    probes: Any


def tested_digest(scene_text: str, probes_text: str) -> str:
    """One read's digest, as the desktop's ``sceneDigest`` computes it: the
    SHA-256 of the scene text, a NUL and the probes text (UTF-8), the first
    :data:`TESTED_DIGEST_HEX` hex digits."""

    data = scene_text.encode("utf-8") + b"\0" + probes_text.encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:TESTED_DIGEST_HEX]


def _point_key(point: Mapping[str, float], step: int) -> tuple[str, int]:
    return json.dumps(point, sort_keys=True), step


def _load(compiled: K.CompiledSketch, engine: SketchEngine, budget: _Budget) -> None:
    program = compiled.program
    try:
        budget.tick()
        entries = engine.load(program.code)
    except SketchRunError as exc:
        budget.tick()  # out of time: the sketch is too slow, not broken
        raise _Failed("structure", [f"the code does not load: {exc.message}"],
                      {"message": exc.message, "params": None}) from exc
    needed = ["init", "view", "probes"] + (["step"] if program.clock is not None else [])
    missing = [name for name in needed if not entries.get(name)]
    if missing:
        raise _Failed("structure", [f"the code defines no {', '.join(name + '()' for name in missing)}"])


def _stream(compiled: K.CompiledSketch, engine: SketchEngine, grid: Sequence[Mapping[str, float]],
            steps: Sequence[int], budget: _Budget, *, extra_reads: bool = False) -> Iterator[tuple[_Sample, str]]:
    """Load, then at every grid point (in the given order) init (a freshly
    loaded program: :meth:`.SketchEngine.init`) and read each of ``steps``
    (``view()`` then ``probes()``, as the desktop reads), validated, one at a
    time: each step read is yielded with its digest and dropped before the
    next is read. Raises :class:`_Failed`."""

    _load(compiled, engine, budget)
    program = compiled.program
    names = [parameter.name for parameter in program.parameters]
    dt = program.clock.dt if program.clock is not None else 0.0
    for point in grid:
        params = {**compiled.defaults, **point}
        try:
            budget.tick()
            engine.init(params, VERIFY_SEED)
            at = 0
            for step in steps:
                budget.tick()
                if step > at:
                    engine.step(params, dt, index=at, count=step - at)
                    at = step
                if extra_reads:
                    budget.read(engine.probes_text(params, index=step), engine.view_text(params, index=step))
                scene_text = engine.view_text(params, index=step)
                probes_text = engine.probes_text(params, index=step)
                budget.read(scene_text, probes_text)
                scene, probes = json.loads(scene_text), json.loads(probes_text)
                digest = tested_digest(scene_text, probes_text)
                del scene_text, probes_text
                where = _point_text(point) + (f", t={step * dt:g}" if program.clock is not None else "")
                problems = K.scene_problems(scene, parameters=names)
                if problems:
                    raise _Failed("runs", [f"at {where}: the scene {problems[0]}", *problems[1:4]],
                                  {"message": problems[0], "params": dict(params), "kind": "scene"})
                problems = K.probe_problems(probes, compiled.probes)
                if problems:
                    raise _Failed("runs", [f"at {where}: {problems[0]}", *problems[1:4]],
                                  {"message": problems[0], "params": dict(params), "kind": "probe"})
                yield _Sample(point=dict(point), step=step, scene=scene, probes=probes), digest
        except SketchRunError as exc:
            budget.tick()
            raise _Failed("runs", [f"at {_point_text(point)}: {exc.message}"],
                          {"message": exc.message, "params": dict(params), "kind": exc.kind}) from exc


def _binding_problem(compiled: K.CompiledSketch, sample: _Sample,
                     elements: Mapping[str, Mapping[str, Any]]) -> str | None:
    for binding in compiled.program.bindings:
        probe = compiled.probes[binding.probe]
        element = elements.get(binding.element_id)
        where = f"at {_point_text(sample.point)}"
        if element is None:
            return f"{where}: bound element {binding.element_id!r} is not drawn"
        if not _bound_equal(element, sample.probes[binding.probe], probe.shape):
            return f"{where}: element {binding.element_id!r} is not drawn at probe {binding.probe!r}'s values"
    return None


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


#: What a check says about a bound element when it speaks for one attribute
#: only (Codex review F3): a series binds a line's heights (its y values), a
#: heat map's cell values or a circle's radius; an invariant over a pairs
#: probe reads its y values. ``None``: the whole drawn element (both
#: coordinates, or a series whose x values are the claim's own index).
def _scope(claim: K.Claim, shape: str, kind: str, on_domain: bool) -> str | None | bool:
    """The attribute a passing claim speaks for on one bound element:
    ``None`` (all of it), an attribute name, or False (nothing: a series
    claim over an index the line is not drawn at)."""

    if kind == "circle":
        return "r"
    if kind == "heat_cells":
        return "values"
    if shape == "series":
        if claim.kind == "equals":
            return None if on_domain else False
        return "y"
    if claim.kind == "invariant":
        return "y"
    return None


def _on_domain(claim: K.Claim, element: Mapping[str, Any]) -> bool:
    """A line bound to a series is drawn at the claim's index: its ``i``-th x
    is ``var_from + i * var_step`` (the claim's tolerance)."""

    xs = element.get("x") or []
    return all(_close(float(x), claim.var_from + index * claim.var_step) for index, x in enumerate(xs))


def _close(value: float, expected: float) -> bool:
    return math.isfinite(expected) and abs(value - expected) <= K.CLAIM_REL_TOL * max(1.0, abs(expected))


def _z() -> float:
    return statistics.NormalDist().inv_cdf(1.0 - K.MC_FALSE_ALARM / 2.0)


def _rk4(dx: G.Node, dy: G.Node, names: Sequence[str], env: Mapping[str, float], x: float, y: float, h: float,
         steps: int, budget: _Budget | None = None) -> list[tuple[float, float]]:
    """The grammar's fixed-step RK4 (``spec._path``'s operation order); with
    a ``budget``, every stage's evaluations are metered to it."""

    xv, yv = names
    scope = dict(env)

    def rates(px: float, py: float, pt: float) -> tuple[float, float]:
        scope[xv], scope[yv], scope[K.TIME_NAME] = px, py, pt
        return G.evaluate(dx, scope, None, budget), G.evaluate(dy, scope, None, budget)

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


def claim_entries(claim: K.CompiledClaim, probe: K.Probe, value: Any) -> int:
    """How many entries a claim's check at one point read evaluates (times
    :attr:`.sketch.CompiledClaim.entry_work`, the estimate an early refusal
    looks at before it runs)."""

    if probe.shape == "scalar" or claim.claim.kind == "distribution":
        return 1
    count = len(value)
    if claim.claim.kind == "follows":
        return max(0, count - 1)
    return count


def check_claim(compiled: K.CompiledSketch, claim: K.CompiledClaim, sample: _Sample,
                budget: _Budget | None = None) -> str | None:
    """One claim at one point read: None when it holds, else why not. With a
    ``budget``, the clock is looked at first, a check whose estimate can't
    fit is refused before it runs, and every grammar evaluation is metered
    to it (the cap and the clock stop it mid-evaluation)."""

    spec = claim.claim
    probe = compiled.probes[spec.probe]
    value = sample.probes[spec.probe]
    entry_work = claim.entry_work
    if spec.kind == "equals" and probe.shape == "pairs" and "expr" in claim.nodes and value:
        # A pairs probe's x is its own (Codex re-review F2): charged at the reach this read has.
        xs = [float(pair[0]) for pair in value]
        entry_work = K.claim_entry_work(compiled.program, spec, claim.nodes, "pairs", (min(xs), max(xs)))
    if budget is not None:
        budget.tick()
        budget.foresee(entry_work * claim_entries(claim, probe, value))
    env = _env(compiled, sample.point, sample.step)
    where = f"at {_point_text(sample.point)}" + (f", t={env[K.TIME_NAME]:g}" if K.TIME_NAME in env else "")
    if spec.kind == "equals":
        node = claim.nodes["expr"]
        if probe.shape == "scalar":
            expected = G.evaluate(node, env, None, budget)
            return None if _close(float(value), expected) else \
                f"{where}: {spec.probe} is {float(value):.10g}, the stated {spec.expr} is {expected:.10g}"
        for index, entry in enumerate(value):
            if probe.shape == "series":
                env[spec.var] = spec.var_from + index * spec.var_step
                got = float(entry)
            else:
                env[spec.var] = float(entry[0])
                got = float(entry[1])
            expected = G.evaluate(node, env, None, budget)
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
        full = _rk4(claim.nodes["dx"], claim.nodes["dy"], spec.vars, env, path[0][0], path[0][1], h, steps, budget)
        half = _rk4(claim.nodes["dx"], claim.nodes["dy"], spec.vars, env, path[0][0], path[0][1], h / 2, 2 * steps,
                    budget)
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
    expected = G.evaluate(claim.nodes["expr"], env, None, budget)
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


def prediction_target_step(compiled: K.CompiledSketch, index: int) -> int:
    """The clock step a prediction is graded at (Codex review F5), shared
    with the desktop so its playback stops exactly there
    (:func:`.sketch.prediction_step`)."""

    return K.prediction_step(compiled, index)


def prediction_outcome(compiled: K.CompiledSketch, engine: SketchEngine, index: int, *,
                       seed: int = VERIFY_SEED) -> dict[str, Any]:
    """What a sketch's prediction observes and its answer, decided by code in
    the engine. A parameter change compares the probe before and after (at the
    first step without a clock, at ``t_max`` with one); ``run_to`` compares
    step 0 with the step at that time. ``choice`` names the largest entry of
    the observed series after the change (None on a tie).

    Each side is one run as the desktop plays it (Astra sandbox review,
    finding 1): a freshly loaded program, ``init``, then the read schedule up
    to the graded step, every scheduled step read (``view()`` then
    ``probes()``). The change is the program's own value, which validation
    requires to be one the controls can be set to (finding 2), so the
    desktop plays exactly the value graded here."""

    program = compiled.program
    prediction = program.predictions[index]
    observe = prediction.observe
    probe = compiled.probes[observe.probe]
    defaults = compiled.defaults
    clock = program.clock
    change = dict(prediction.change)
    dt = clock.dt if clock is not None else 0.0

    schedule = K.read_steps(compiled)

    def read(params: Mapping[str, float], step: int) -> Any:
        if step not in schedule:
            raise SketchRunError(1, f"step {step} is not on the read schedule")
        engine.init(params, seed)
        at = 0
        text = "null"
        for point in schedule:
            if point > step:
                break
            if point > at:
                engine.step(params, dt, index=at, count=point - at)
                at = point
            engine.view_text(params, index=point)  # read as the desktop reads: view(), then probes()
            text = engine.probes_text(params, index=point)
        values = json.loads(text)
        problems = K.probe_problems(values, compiled.probes)
        if problems:
            raise SketchRunError(1, problems[0])
        return values[observe.probe]

    target = prediction_target_step(compiled, index)
    if set(change) == {"run_to"}:
        assert clock is not None
        before = read(defaults, 0)
        after = read(defaults, target)
    else:
        before = read(defaults, target)
        after = read({**defaults, **change}, target)
    if observe.kind == "direction":
        b, a = float(before), float(after)
        slack = 1e-6 * max(1.0, abs(b))
        answer = "same" if abs(a - b) <= slack else ("rises" if a > b else "falls")
        return {"kind": "direction", "before": b, "after": a, "answer": answer, "choices": ["rises", "falls", "same"],
                "change": change, "target_step": target}
    series = [float(v) for v in after]
    labels = list(observe.choices)
    answer = None
    if len(series) == len(labels) and series:
        top = max(series)
        winners = [label for label, v in zip(labels, series) if abs(v - top) <= 1e-6 * max(1.0, abs(top))]
        answer = winners[0] if len(winners) == 1 else None
    return {"kind": "choice", "before": None, "after": None, "answer": answer, "choices": labels, "change": change,
            "target_step": target}


def verify_sketch(compiled: K.CompiledSketch, *, engine_factory: EngineFactory = SketchEngine,
                  span_texts: Mapping[str, str] | None = None) -> SketchReport:
    """Steps 2-5 on a parsed program (step 1's static half is
    :func:`.sketch.parse_sketch`): ``failed`` with the reason, or
    ``illustrative`` with its check lines.

    Streamed (Codex review F1): each point read is validated, bound and
    checked as it arrives, and only its digest is kept for step 3's
    comparison, so memory holds one scene at a time whatever the grid. The
    steps still decide in order: a run that fails, then determinism, then
    bindings, then claims."""

    report = SketchReport()
    grid = V.parameter_grid(compiled)  # type: ignore[arg-type]
    steps = K.sample_steps(compiled)
    schedule = K.read_steps(compiled)
    checked = set(steps)
    report.grid_points, report.samples, report.read_steps = len(grid), steps, schedule
    report.claims = [{"span_id": claim.span_id, "quote": claim.quote,
                      "verified": bool(span_texts) and claim.span_id in (span_texts or {})
                      and V.quote_in(claim.quote, (span_texts or {})[claim.span_id])}
                     for claim in compiled.program.source_claims]
    budget = _Budget(time.monotonic() + K.SKETCH_VERIFY_SECONDS)
    program = compiled.program
    # Which bound elements each claim may speak for, and how (F3).
    bound: dict[str, list[str]] = {}
    for binding in program.bindings:
        bound.setdefault(binding.probe, []).append(binding.element_id)
    off_domain: dict[int, set[str]] = {}
    kinds: dict[str, set[str]] = {}
    defaults_point = compiled.defaults
    first_drawn: list[tuple[Any, str]] | None = None
    first = _engine(engine_factory, budget)
    try:
        try:
            digests: dict[tuple[str, int], str] = {}
            binding_problem: str | None = None
            failures: dict[int, str] = {}
            settings = 0
            names = [parameter.name for parameter in program.parameters]
            tested: dict[str, dict[str, Any]] = {}
            for sample, digest in _stream(compiled, first, grid, schedule, budget):
                elements = K.element_index(sample.scene)
                if binding_problem is None:
                    binding_problem = _binding_problem(compiled, sample, elements)
                if sample.step not in checked:
                    del sample, elements
                    continue  # read (the schedule every run reads), validated and bound; not a checked sample
                settings += 1
                key = _point_key(sample.point, sample.step)
                digests[key] = digest
                params = {**defaults_point, **sample.point}
                entry = tested.setdefault(key[0], {"values": [float(params[name]) for name in names],
                                                   "steps": [], "digests": []})
                entry["steps"].append(sample.step)
                entry["digests"].append(digest)
                if first_drawn is None and sample.step == steps[0] and \
                        all(sample.point.get(k, v) == v for k, v in defaults_point.items()):
                    # What the learner first sees: the defaults at the first step.
                    first_drawn = [(element.get("id"), str(element.get("type")))
                                   for element in sample.scene.get("elements") or ()]
                if binding_problem is not None:
                    continue  # bindings fail: the claims can't speak for anything
                for element_id in (b.element_id for b in program.bindings):
                    kinds.setdefault(element_id, set()).add(str(elements[element_id].get("type")))
                for index, claim in enumerate(compiled.claims):
                    spec = claim.claim
                    if spec.kind == "equals" and compiled.probes[spec.probe].shape == "series":
                        for element_id in bound.get(spec.probe, ()):
                            element = elements[element_id]
                            if element.get("type") in ("polyline", "polygon", "points") and \
                                    not _on_domain(spec, element):
                                off_domain.setdefault(index, set()).add(element_id)
                    if index in failures:
                        continue
                    problem = check_claim(compiled, claim, sample, budget)
                    if problem is not None:
                        failures[index] = problem
                del sample, elements
            report.settings = settings
            report.tested = list(tested.values())
            second = _engine(engine_factory, budget)
            try:
                for sample, digest in _stream(compiled, second, list(reversed(grid)), steps, budget,
                                              extra_reads=True):
                    if digests.get(_point_key(sample.point, sample.step)) != digest:
                        raise _Failed("deterministic", [
                            f"at {_point_text(sample.point)}: a second run gives different values (it may not "
                            "depend on anything but its inputs and rand())"])
            finally:
                second.close()
            if binding_problem is not None:
                raise _Failed("bindings", [binding_problem])
            if failures:
                raise _Failed("claims", [f"claim {index + 1} ({compiled.claims[index].claim.kind}) fails {problem}"
                                         for index, problem in sorted(failures.items())])
            checks: list[dict[str, Any]] = []
            for index, claim in enumerate(compiled.claims):
                spec = claim.claim
                shape = compiled.probes[spec.probe].shape
                whole: list[str] = []
                partial: list[dict[str, str]] = []
                for element_id in bound.get(spec.probe, ()):
                    scopes = {_scope(spec, shape, kind, element_id not in off_domain.get(index, ()))
                              for kind in kinds.get(element_id, ())}
                    # One scope at every tested setting, or none at all
                    # (Codex re-review F11): an element drawn as a line at
                    # some settings and as heat cells at others had no one
                    # attribute checked everywhere, so the check speaks for
                    # the probe and the element stays not covered.
                    if len(scopes) != 1 or False in scopes:
                        continue
                    (scope,) = scopes
                    if isinstance(scope, str):
                        partial.append({"element": element_id, "attribute": scope})
                    else:
                        whole.append(element_id)
                checks.append({"claim": index, "kind": spec.kind, "probe": spec.probe, "elements": whole,
                               "partial": partial, "statement": _statement(spec), "settings": settings})
            report.checks = checks
            covered = {element for check in checks for element in
                       [*check["elements"], *(entry["element"] for entry in check["partial"])]}
            drawn = [(element_id, kind) for element_id, kind in first_drawn or () if kind != "handle"]
            report.not_covered = [str(element_id) for element_id, _kind in drawn
                                  if element_id is not None and element_id not in covered]
            report.unnamed_elements = sum(1 for element_id, _kind in drawn if element_id is None)
            for index in range(len(program.predictions)):
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


def _engine(factory: EngineFactory, budget: _Budget) -> SketchEngine:
    engine = factory()
    if hasattr(engine, "deadline"):
        engine.deadline = budget.deadline
    return engine


__all__ = [
    "PROPERTY_WORDS",
    "SketchReport",
    "TESTED_DIGEST_HEX",
    "VERIFIER_REPORT_VERSION",
    "VERIFY_SEED",
    "check_claim",
    "claim_entries",
    "prediction_outcome",
    "prediction_target_step",
    "tested_digest",
    "verify_sketch",
]
