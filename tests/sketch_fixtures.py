"""Sketch programs for RW5d P2's tests (spec_reader_show_me_figures_v1 §9; G-SM9-G-SM13).

``GOOD`` are sketches that pass verification (with the check lines each
should produce); ``PLANTED`` are planted-wrong ones, each refused at a named
step for a named reason (G-SM10). Hand-written, deterministic, no network.
"""

from __future__ import annotations

import copy
import json
from typing import Any

WALK_CODE = r"""
function init(p, seed) { var w = []; for (var i = 0; i < p.walkers; i++) w.push(0); return {w: w, n: 0}; }
function step(s, p, dt) {
  var w = s.w.slice();
  for (var i = 0; i < w.length; i++) w[i] += rand() < 0.5 ? -1 : 1;
  return {w: w, n: s.n + 1};
}
function env(s) { var pts = []; for (var i = 0; i <= s.n; i++) pts.push([i, Math.sqrt(i)]); return pts; }
function probes(s, p) {
  var k = s.w.length, m = 0, m2 = 0;
  for (var i = 0; i < k; i++) { var q = s.w[i] * s.w[i]; m += q; m2 += q * q; }
  m /= k;
  var v = (m2 - k * m * m) / (k - 1);
  return {envelope: env(s), msd: m, count: k, sqvar: Math.max(v, 0)};
}
function view(s, p) {
  var e = env(s), xs = [], ys = [];
  for (var i = 0; i < e.length; i++) { xs.push(e[i][0]); ys.push(e[i][1]); }
  var px = [], py = [];
  for (var j = 0; j < s.w.length; j++) { px.push(s.n); py.push(s.w[j]); }
  return {viewport: {x: [0, 100], y: [-30, 30]}, axes: {x_label: "n", y_label: "position"},
          elements: [{type: "polyline", id: "envelope", x: xs, y: ys, style: {color: "accent"}},
                     {type: "points", id: "walkers", x: px, y: py, style: {color: "series0", opacity: 0.4}}]};
}
"""


def walk(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "a random walk's spread grows like the square root of n",
        "assumptions": [{"text": "steps of +1 or -1 with equal probability"}],
        "parameters": [{"name": "walkers", "label": "walkers", "min": 100, "max": 400, "step": 100, "default": 200}],
        "clock": {"dt": 1, "t_max": 100},
        "seeded": True,
        "code": WALK_CODE,
        "probes": [{"name": "envelope", "label": "the square-root envelope", "shape": "pairs"},
                   {"name": "msd", "label": "mean squared position", "shape": "scalar"},
                   {"name": "count", "label": "walkers", "shape": "scalar"},
                   {"name": "sqvar", "label": "variance of the squared positions", "shape": "scalar"}],
        "claims": [{"kind": "equals", "probe": "envelope", "expr": "sqrt(x)", "var": "x"},
                   {"kind": "distribution", "probe": "msd", "expr": "t", "n_probe": "count", "var_probe": "sqvar"}],
        "bindings": [{"element_id": "envelope", "probe": "envelope"}],
        "predictions": [{"prompt": "Run the walk to n = 100. What happens to the mean squared position?",
                         "change": {"run_to": 100}, "observe": {"kind": "direction", "probe": "msd"}}],
        "annotations": [],
    }
    program.update(changes)
    return program


SPIRAL_CODE = r"""
function rates(p, x, y) { return [p.a * x - p.b * y, p.b * x + p.a * y]; }
function path(p) {
  var h = 0.05, x = 1, y = 0, pts = [[x, y]];
  for (var i = 0; i < 120; i++) {
    var k1 = rates(p, x, y);
    var k2 = rates(p, x + h / 2 * k1[0], y + h / 2 * k1[1]);
    var k3 = rates(p, x + h / 2 * k2[0], y + h / 2 * k2[1]);
    var k4 = rates(p, x + h * k3[0], y + h * k3[1]);
    x = x + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);
    y = y + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);
    pts.push([x, y]);
  }
  return pts;
}
function init(p, seed) { return {}; }
function probes(s, p) { return {path: path(p), radius: Math.sqrt(p.a * p.a + p.b * p.b)}; }
function view(s, p) {
  var pts = path(p), xs = [], ys = [];
  for (var i = 0; i < pts.length; i++) { xs.push(pts[i][0]); ys.push(pts[i][1]); }
  return {viewport: {x: [-2, 2], y: [-2, 2]},
          elements: [{type: "polyline", id: "trajectory", x: xs, y: ys, style: {color: "series1", width: 2}},
                     {type: "handle", id: "ab", x: p.a, y: p.b, binds: {x: "a", y: "b"}},
                     {type: "text", x: -1.9, y: 1.8, text: "a ± bi"}]};
}
"""


def spiral(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "complex eigenvalues a ± bi make trajectories spiral, in when a < 0 and out when a > 0",
        "parameters": [{"name": "a", "label": "real part a", "min": -0.5, "max": 0.5, "step": 0.05, "default": -0.2},
                       {"name": "b", "label": "imaginary part b", "min": 0.2, "max": 1.5, "step": 0.05,
                        "default": 0.8}],
        "seeded": False,
        "code": SPIRAL_CODE,
        "probes": [{"name": "path", "label": "the trajectory from (1, 0)", "shape": "pairs"},
                   {"name": "radius", "label": "|a + bi|", "shape": "scalar"}],
        "claims": [{"kind": "follows", "probe": "path", "dx": "a*x - b*y", "dy": "b*x + a*y", "vars": ["x", "y"],
                    "h": 0.05},
                   {"kind": "equals", "probe": "radius", "expr": "sqrt(a^2 + b^2)"}],
        "bindings": [{"element_id": "trajectory", "probe": "path"}],
        "predictions": [{"prompt": "Make a positive. Does the size of a + bi rise, fall or stay the same?",
                         "change": {"a": 0.3}, "observe": {"kind": "direction", "probe": "radius"}}],
    }
    program.update(changes)
    return program


PI_CODE = r"""
function init(p, seed) {
  var hits = 0, xs = [], ys = [];
  for (var i = 0; i < p.n; i++) {
    var x = rand(), y = rand();
    if (x * x + y * y <= 1) hits++;
    if (i < 300) { xs.push(x); ys.push(y); }
  }
  return {hits: hits, n: p.n, xs: xs, ys: ys};
}
function probes(s, p) {
  var q = s.hits / s.n;
  return {estimate: 4 * q, samples: s.n, variance: 16 * q * (1 - q) * s.n / (s.n - 1)};
}
function view(s, p) {
  var ax = [], ay = [];
  for (var i = 0; i <= 32; i++) { var t = i / 32 * Math.PI / 2; ax.push(Math.cos(t)); ay.push(Math.sin(t)); }
  return {viewport: {x: [0, 1], y: [0, 1]},
          elements: [{type: "points", id: "darts", x: s.xs, y: s.ys, r: 2},
                     {type: "polyline", id: "arc", x: ax, y: ay, style: {color: "accent"}},
                     {type: "rect", x: 0, y: 0, w: 1, h: 1, style: {color: "muted"}}]};
}
"""


def monte_carlo_pi(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "the share of random darts inside the quarter circle estimates pi / 4",
        "parameters": [{"name": "n", "label": "darts", "min": 1000, "max": 5000, "step": 1000, "default": 2000}],
        "seeded": True,
        "code": PI_CODE,
        "probes": [{"name": "estimate", "label": "4 x the share inside", "shape": "scalar"},
                   {"name": "samples", "label": "darts thrown", "shape": "scalar"},
                   {"name": "variance", "label": "sample variance of 4 x inside", "shape": "scalar"}],
        "claims": [{"kind": "distribution", "probe": "estimate", "expr": "pi", "n_probe": "samples",
                    "var_probe": "variance"},
                   {"kind": "invariant", "probe": "estimate", "property": "bounded", "bound": 4}],
    }
    program.update(changes)
    return program


AUTOMATON_CODE = r"""
function init(p, seed) { var c = []; for (var i = 0; i < 32; i++) c.push(i === 16 ? 1 : 0); return {rows: [c]}; }
function rule(l, c, r) { var k = l * 4 + c * 2 + r; return (30 >> k) & 1; }
function step(s, p, dt) {
  var last = s.rows[s.rows.length - 1], next = [];
  for (var i = 0; i < 32; i++) next.push(rule(last[(i + 31) % 32], last[i], last[(i + 1) % 32]));
  var rows = s.rows.slice(-15); rows.push(next); return {rows: rows};
}
function cells(s) { var out = []; for (var r = 0; r < 16; r++) { var row = s.rows[r] || []; for (var i = 0; i < 32; i++) out.push(row[i] || 0); } return out; }
function probes(s, p) { var c = cells(s), alive = 0; for (var i = 0; i < c.length; i++) alive += c[i]; return {cells: c, alive: alive}; }
function view(s, p) { return {viewport: {x: [0, 32], y: [0, 16]}, elements: [{type: "heat_cells", id: "grid", x: [0, 32], y: [0, 16], cols: 32, rows: 16, values: cells(s)}]}; }
"""


def automaton(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "rule 30 grows an irregular pattern from one live cell",
        "parameters": [],
        "clock": {"dt": 1, "t_max": 40},
        "seeded": False,
        "code": AUTOMATON_CODE,
        "probes": [{"name": "cells", "label": "the last 16 rows", "shape": "series"},
                   {"name": "alive", "label": "live cells shown", "shape": "scalar"}],
        "claims": [{"kind": "invariant", "probe": "cells", "property": "bounded", "bound": 1},
                   {"kind": "invariant", "probe": "cells", "property": "nonnegative"}],
        "bindings": [{"element_id": "grid", "probe": "cells"}],
    }
    program.update(changes)
    return program


#: The independent sandbox review's repro, exactly (Astra, finding 1): radius 9
#: on the program's first start at a = 1, 1 on every other start.
COUNTING_CODE = r"""
let starts = 0;
function init(p) { starts++; return p.a === 1 && starts === 1 ? 9 : 1; }
function view(s, p) { return {viewport: {x: [-10, 10], y: [-10, 10]}, elements: [{type: "circle", id: "dot", cx: 0, cy: 0, r: s}]}; }
function probes(s, p) { return {radius: s}; }
"""
#: The same program, its probes also saying which start this is (the engine-level cases).
COUNTING_STARTS_CODE = COUNTING_CODE.replace("return {radius: s};", "return {radius: s, starts: starts};")


def counting_starts(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "a dot of radius one",
        "parameters": [{"name": "a", "label": "a", "min": 0, "max": 2, "step": 1, "default": 1}],
        "code": COUNTING_CODE,
        "probes": [{"name": "radius", "label": "radius", "shape": "scalar"}],
        "claims": [{"kind": "equals", "probe": "radius", "expr": "1"}],
        "bindings": [{"element_id": "dot", "probe": "radius"}],
    }
    program.update(changes)
    return program


#: Reads that count themselves (a program's globals are its own within a run).
READ_COUNTING_CODE = r"""
var reads = 0;
function init(p) { return {}; }
function view(s, p) { reads++; return {viewport: {x: [0, 1], y: [0, 1]}, elements: []}; }
function probes(s, p) { reads++; return {reads: reads}; }
"""

#: A program that changes its state when read (Astra, finding 1): view()
#: marks the state at n = 13, and once marked each step adds 10, not 1.
MARKS_CODE = r"""
function init(p) { return {n: 0, x: 0, mark: false}; }
function step(s, p, dt) { return {n: s.n + 1, x: s.x + (s.mark ? 10 : 1), mark: s.mark}; }
function view(s, p) {
  if (s.n === 13) s.mark = true;
  return {viewport: {x: [0, 100], y: [0, 1000]}, elements: [{type: "segment", id: "bar", x1: 0, y1: 0, x2: s.n, y2: s.x}]};
}
function probes(s, p) { return {x: s.x}; }
"""


def marks_when_read(**changes: Any) -> dict[str, Any]:
    program = {
        "program_version": "sketch-v1",
        "demonstrates": "a total that grows faster once it has been looked at",
        "parameters": [],
        "clock": {"dt": 1, "t_max": 100},
        "code": MARKS_CODE,
        "probes": [{"name": "x", "label": "the total", "shape": "scalar"}],
        "claims": [{"kind": "invariant", "probe": "x", "property": "finite"}],
        "predictions": [{"prompt": "Run to n = 50. Does the total rise?", "change": {"run_to": 50},
                         "observe": {"kind": "direction", "probe": "x"}}],
    }
    program.update(changes)
    return program


def unchecked() -> dict[str, Any]:
    """A sketch that states no claim: shown as "nothing in it checked"."""

    program = spiral(claims=[], bindings=[], predictions=[])
    return program


def _replace_code(program: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    out = copy.deepcopy(program)
    assert old in out["code"], old
    out["code"] = out["code"].replace(old, new)
    return out


#: (name, program, the step it fails at, a phrase the first problem contains).
def planted() -> list[tuple[str, dict[str, Any], str, str]]:
    off_by_constant = walk(claims=[{"kind": "equals", "probe": "envelope", "expr": "sqrt(x) + 1", "var": "x"}])
    broken_binding = _replace_code(walk(), "ys.push(e[i][1]);", "ys.push(e[i][1] * 1.01);")
    hidden_state = _replace_code(spiral(), "function init(p, seed) { return {}; }",
                                 "var calls = 0;\nfunction init(p, seed) { return {}; }")
    hidden_state = _replace_code(hidden_state, "return {path: path(p), radius: Math.sqrt(p.a * p.a + p.b * p.b)};",
                                 "calls++; return {path: path(p), radius: Math.sqrt(p.a * p.a + p.b * p.b) + (calls % 2) * 1e-3};")
    hidden_state["claims"] = []
    nan_corner = monte_carlo_pi(parameters=[{"name": "n", "label": "darts", "min": 0, "max": 4000, "step": 1000,
                                             "default": 2000}], claims=[])
    over_fuel = _replace_code(walk(), "return {w: w, n: s.n + 1};",
                              "if (s.n >= 50) { while (true) {} } return {w: w, n: s.n + 1};")
    no_step = walk()
    no_step = _replace_code(no_step, "function step(s, p, dt) {", "function stepper(s, p, dt) {")
    unbound_target = walk(bindings=[{"element_id": "missing", "probe": "envelope"}])
    return [
        ("claim off by a constant", off_by_constant, "claims", "the stated sqrt(x) + 1"),
        ("a bound path drawn off its probe", broken_binding, "bindings", "is not drawn at probe"),
        ("hidden state between calls", hidden_state, "deterministic", "second run gives different values"),
        ("NaN at one grid corner", nan_corner, "runs", "NaN"),
        ("an over-fuel step", over_fuel, "runs", "work budget"),
        ("a clock with no step()", no_step, "structure", "defines no step()"),
        ("a binding to an element never drawn", unbound_target, "bindings", "is not drawn"),
    ]


def good() -> list[tuple[str, dict[str, Any]]]:
    return [("random walk", walk()), ("spiral", spiral()), ("monte carlo pi", monte_carlo_pi()),
            ("rule 30", automaton()), ("unchecked", unchecked())]


def as_json(program: dict[str, Any]) -> str:
    return json.dumps(program)
