"""RW5d P2: SketchProgramV1, the Scene validator and headless verification
(spec_reader_show_me_figures_v1 §9.1, §9.5; G-SM10).

Good sketches pass with the right check lines; planted-wrong ones are each
refused at the right step for the right reason.
"""

from __future__ import annotations

import copy
import time
import tracemalloc

import pytest

from learnloop.figures import sketch as K
from learnloop.figures import sketch_verify as SV
from learnloop.figures import verify as V
from learnloop.figures.sketch_engine import SketchEngine
from tests import sketch_fixtures as F


def verify(program):
    return SV.verify_sketch(K.parse_sketch(program))


def test_the_random_walk_passes_with_element_scoped_check_lines():
    report = verify(F.walk())
    assert report.outcome == V.ILLUSTRATIVE
    assert report.grid_points == 3 and report.samples == [0, 12, 25, 38, 50, 62, 75, 88, 100]
    assert report.settings == 27  # "at 27 tested settings" (spec §6.6)
    equals, distribution = report.checks
    assert equals == {"claim": 0, "kind": "equals", "probe": "envelope", "elements": ["envelope"],
                      "partial": [], "statement": "sqrt(x)", "settings": 27}
    assert distribution["kind"] == "distribution" and distribution["elements"] == []
    assert report.not_covered == ["walkers"]  # drawn, not checked


@pytest.mark.parametrize("name,program", F.good())
def test_every_good_sketch_passes(name, program):
    report = verify(program)
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    assert report.failed_step is None
    assert len(report.checks) == len(program.get("claims") or [])


def test_a_follows_claim_checks_the_drawn_trajectory_against_rk4():
    report = verify(F.spiral())
    follows = report.checks[0]
    assert follows["kind"] == "follows" and follows["elements"] == ["trajectory"]
    assert follows["statement"] == "dx/dt = a*x - b*y, dy/dt = b*x + a*y"
    assert report.unnamed_elements == 1  # the text label: drawn, not checked
    # An Euler path is not "the system's path" at RK4's accuracy.
    euler = F.spiral(code=F.SPIRAL_CODE.replace(
        "x = x + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]);\n    y = y + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]);",
        "x = x + h * k1[0];\n    y = y + h * k1[1];"))
    failed = verify(euler)
    assert failed.outcome == V.FAILED and failed.failed_step == "claims" and "off the stated system" in failed.reason


def test_no_claims_is_shown_as_nothing_checked():
    report = verify(F.unchecked())
    assert report.outcome == V.ILLUSTRATIVE and report.checks == []
    assert report.not_covered == ["trajectory"]


@pytest.mark.parametrize("name,program,step,phrase", F.planted())
def test_each_planted_wrong_sketch_is_refused_for_its_reason(name, program, step, phrase):
    report = verify(program)
    assert report.outcome == V.FAILED, name
    assert report.failed_step == step, (name, report.reason)
    assert phrase in report.reason, (name, report.reason)


def test_a_runtime_failure_keeps_the_settings_for_not_right():
    program = F.planted()[4][1]  # the over-fuel step
    report = verify(program)
    assert report.runtime_error["kind"] == "work_cap"
    assert report.runtime_error["params"] == {"walkers": 100.0}


def test_undecidable_predictions_are_dropped_not_failed():
    tie = F.automaton(predictions=[{"prompt": "which is largest?", "change": {"run_to": 10},
                                    "observe": {"kind": "choice", "probe": "cells", "choices": ["a", "b"]}}])
    tie = K.parse_sketch(tie)
    report = SV.verify_sketch(tie)
    assert report.outcome == V.ILLUSTRATIVE and report.dropped_predictions == [0]


def test_sketch_predictions_are_decided_by_code_in_the_engine():
    from learnloop.figures.sketch_engine import SketchEngine

    compiled = K.parse_sketch(F.walk())
    with SketchEngine() as engine:
        engine.load(compiled.program.code)
        outcome = SV.prediction_outcome(compiled, engine, 0)
    assert outcome["kind"] == "direction" and outcome["answer"] == "rises"
    assert outcome["before"] == 0.0 and outcome["after"] > 50
    spiral = K.parse_sketch(F.spiral())
    with SketchEngine() as engine:
        engine.load(spiral.program.code)
        moved = SV.prediction_outcome(spiral, engine, 0)
    assert moved["answer"] == "rises"  # |0.3 + 0.8i| > |-0.2 + 0.8i|


def test_a_heat_map_bound_series_is_checked_in_its_cell_values_only():
    report = verify(F.automaton())
    assert report.outcome == V.ILLUSTRATIVE
    assert [check["partial"] for check in report.checks] == [[{"element": "grid", "attribute": "values"}]] * 2
    assert all(check["elements"] == [] for check in report.checks) and report.not_covered == []


# ---------------------------------------------------------------------------
# Codex review F3: a series bound to a line speaks for its x values only when
# they are the claim's index
# ---------------------------------------------------------------------------

LINE_CODE = r"""
function init(p, seed) { return {}; }
function probes(s, p) { return {v: [0, 1]}; }
function view(s, p) { return {viewport: {x: [-1, 200], y: [-1, 2]},
  elements: [{type: "polyline", id: "line", x: [XS], y: [0, 1]}]}; }
"""


def _line(xs, claims):
    return {"program_version": "sketch-v1", "demonstrates": "a line", "parameters": [], "seeded": False,
            "code": LINE_CODE.replace("XS", xs), "probes": [{"name": "v", "label": "v", "shape": "series"}],
            "claims": claims, "bindings": [{"element_id": "line", "probe": "v"}]}


EQUALS_X = {"kind": "equals", "probe": "v", "expr": "x", "var": "x"}


def test_a_series_line_drawn_at_unrelated_x_is_not_claimed_as_the_equation():
    """F3's reproduction: probe [0, 1] equals x at indices [0, 1], bound to a
    polyline drawn at x = [100, 101]. The claim holds for the value; the
    drawn line is not "x", so the check names the value and the line is not
    covered."""

    report = verify(_line("100, 101", [EQUALS_X]))
    assert report.outcome == V.ILLUSTRATIVE
    (check,) = report.checks
    assert check["elements"] == [] and check["partial"] == []
    assert report.not_covered == ["line"]


def test_a_series_line_drawn_at_its_index_is_claimed_whole():
    report = verify(_line("0, 1", [EQUALS_X]))
    (check,) = report.checks
    assert check["elements"] == ["line"] and report.not_covered == []
    shifted = verify(_line("5, 7", [{**EQUALS_X, "expr": "(x - 5) / 2", "var_from": 5, "var_step": 2}]))
    assert shifted.checks[0]["elements"] == ["line"]


def test_an_invariant_over_a_series_line_speaks_for_its_y_values_only():
    report = verify(_line("100, 101", [{"kind": "invariant", "probe": "v", "property": "nonnegative"}]))
    (check,) = report.checks
    assert check["elements"] == [] and check["partial"] == [{"element": "line", "attribute": "y"}]
    assert report.not_covered == []


# ---------------------------------------------------------------------------
# Codex review F1 and F2: verification's own memory, work and time
# ---------------------------------------------------------------------------

def _grid_program(points: int, claims=(), probes=None, probe_code="{v: []}"):
    """Four parameters (81 grid points) and a clock read at 9 times: the
    largest legal grid, 729 point reads per run. The scene's line has
    ``points`` points (filled natively, so the engine's work cap is not what
    stops it)."""

    code = (
        "function init(p, seed) { return {n: 0}; }\n"
        "function step(s, p, dt) { return {n: s.n + 1}; }\n"
        f"function probes(s, p) {{ return {probe_code}; }}\n"
        f"function view(s, p) {{ var xs = new Array({points}).fill(p.a + p.c / 3 + 1 / 7), "
        f"ys = new Array({points}).fill(p.b + s.n / 7 + p.d / 11 + 1 / 3);\n"
        "  return {viewport: {x: [-1, 50], y: [-5, 5]}, elements: [{type: 'polyline', id: 'big', x: xs, y: ys}]}; }\n")
    return {"program_version": "sketch-v1", "demonstrates": "a big scene",
            "parameters": [{"name": name, "label": name, "min": 0, "max": 1, "step": 0.5, "default": 0.5}
                           for name in ("a", "b", "c", "d")],
            "clock": {"dt": 1, "t_max": 8}, "seeded": False, "code": code,
            "probes": probes or [{"name": "v", "label": "v", "shape": "series"}], "claims": list(claims)}


def test_the_largest_legal_grid_is_verified_one_point_read_at_a_time():
    """F1: 81 grid points x 9 times x 2 runs. Each scene is validated, bound
    and checked as it arrives and dropped, so Python's memory holds one at a
    time (the old two lists held every scene, probe and text of both runs)."""

    compiled = K.parse_sketch(_grid_program(1_000))
    SketchEngine().close()  # compiled and cached outside the measurement
    tracemalloc.start()
    try:
        report = SV.verify_sketch(compiled)
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert report.outcome == V.ILLUSTRATIVE, report.reason
    assert report.grid_points == 81 and len(report.samples) == 9 and report.settings == 729
    # One scene of 1,000 points is ~38 KB as text and ~70 KB parsed; 1,458 kept would be ~150 MB.
    assert peak < 8 * 1024 * 1024, peak


def test_scenes_at_the_point_cap_over_the_largest_grid_hit_the_output_budget():
    """F1: 1,458 scenes of 40,000 points (~1.5 MB each here, up to ~4 MB with
    longer numbers) would be gigabytes; the aggregate output budget refuses
    the sketch long before, holding one scene at a time."""

    compiled = K.parse_sketch(_grid_program(K.SKETCH_MAX_POINTS))
    SketchEngine().close()
    tracemalloc.start()
    started = time.monotonic()
    try:
        report = SV.verify_sketch(compiled)
        _current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert report.outcome == V.FAILED and report.failed_step == "runs"
    assert "too large to verify" in report.reason
    assert peak < 96 * 1024 * 1024, peak
    assert time.monotonic() - started < 60


def test_claim_steps_are_counted_soundly():
    sums = K.parse_sketch(_grid_program(10, claims=[{"kind": "equals", "probe": "v", "expr": "sum(x, k, 0, 10000)",
                                                    "var": "x"}]))
    # Ten thousand and one terms per entry, whatever the index.
    assert sums.claims[0].entry_work >= 10_001
    bounded = K.parse_sketch(_grid_program(10, claims=[{"kind": "equals", "probe": "v", "expr": "sum(k, k, 0, a)",
                                                       "var": "x"}]))
    assert 2 <= bounded.claims[0].entry_work < 20  # a's range is [0, 1]: two terms
    by_index = K.parse_sketch(_grid_program(10, claims=[{"kind": "equals", "probe": "v", "expr": "sum(k, k, 0, x)",
                                                        "var": "x"}]))
    assert by_index.claims[0].entry_work >= K.SKETCH_MAX_SERIES  # x reaches the series' last index
    follows = K.parse_sketch(F.spiral())
    assert follows.claims[0].entry_work == 12 * (7 + 7)  # a*x - b*y: seven nodes each


def test_a_claim_whose_work_exceeds_the_budget_is_refused_before_it_runs():
    """F2's reproduction: a 4,000-entry series claimed equal to
    sum(x, k, 0, 10000) at every point read (2.9e10 term evaluations
    unbudgeted). The first evaluation's charge is past the budget."""

    program = _grid_program(10, claims=[{"kind": "equals", "probe": "v", "expr": "sum(x, k, 0, 10000)", "var": "x"}],
                            probe_code="{v: Array.from({length: 4000}, function (_, i) { return 0; })}")
    started = time.monotonic()
    report = verify(program)
    assert report.outcome == V.FAILED and report.failed_step == "claims"
    assert "more computation than verification may do" in report.reason
    assert time.monotonic() - started < 30


def test_verification_stops_at_its_wall_clock(monkeypatch):
    monkeypatch.setattr(K, "SKETCH_VERIFY_SECONDS", -1.0)
    report = verify(F.spiral())
    assert report.outcome == V.FAILED and report.failed_step == "runs"
    assert "longer than -1 s to verify" in report.reason


def test_prediction_target_steps_are_where_the_answers_are_graded():
    walk = K.parse_sketch(F.walk())
    assert SV.prediction_target_step(walk, 0) == 100  # run_to 100 at dt 1
    early = K.parse_sketch(F.walk(predictions=[{"prompt": "?", "change": {"run_to": 5},
                                                "observe": {"kind": "direction", "probe": "msd"}}]))
    assert SV.prediction_target_step(early, 0) == 5
    changed = K.parse_sketch(F.walk(predictions=[{"prompt": "?", "change": {"walkers": 400},
                                                  "observe": {"kind": "direction", "probe": "msd"}}]))
    assert SV.prediction_target_step(changed, 0) == 100  # t_max
    assert SV.prediction_target_step(K.parse_sketch(F.spiral()), 0) == 0  # no clock


# ---------------------------------------------------------------------------
# Step 1's static half: the program's schema
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("change,phrase", [
    ({"code": "x" * (K.SKETCH_MAX_SOURCE_BYTES + 1)}, "longer than"),
    ({"clock": {"dt": 0.001, "t_max": 100}}, "more than 2000 steps"),
    ({"probes": [{"name": "a_b", "label": "x", "shape": "scalar"}]}, "not a usable name"),
    ({"bindings": [{"element_id": "envelope", "probe": "nope"}]}, "not declared"),
    ({"claims": [{"kind": "equals", "probe": "envelope", "expr": "sqrt(x)"}]}, "needs var"),
    ({"claims": [{"kind": "equals", "probe": "msd", "expr": "t + walkers + q"}]}, "unknown name"),
    ({"claims": [{"kind": "follows", "probe": "msd", "dx": "x", "dy": "y", "h": 1}]}, "needs a pairs probe"),
    ({"claims": [{"kind": "distribution", "probe": "msd", "expr": "t", "n_probe": "envelope",
                  "var_probe": "sqvar"}]}, "declared scalar probe"),
    ({"seeded": False}, "needs a seeded sketch"),
    ({"predictions": [{"prompt": "?", "change": {"walkers": 1000}, "observe": {"kind": "direction",
                                                                              "probe": "msd"}}]}, "outside its range"),
    ({"predictions": [{"prompt": "?", "change": {"run_to": 500}, "observe": {"kind": "direction",
                                                                            "probe": "msd"}}]}, "run_to needs"),
    ({"extra": 1}, "Extra inputs"),
    ({"probes": [{"name": "checkedByLearnLoop", "label": "x", "shape": "scalar"}]}, "not a usable name"),
    ({"bindings": [{"element_id": "verified-check", "probe": "msd"}]}, "element ids"),
])
def test_a_program_outside_the_schema_is_refused(change, phrase):
    with pytest.raises(K.SketchError) as caught:
        K.parse_sketch(F.walk(**change))
    assert any(phrase in problem for problem in caught.value.problems), caught.value.problems


def test_a_parameter_named_like_a_check_is_refused():
    program = F.spiral()
    program["parameters"][0]["name"] = "checked"
    with pytest.raises(K.SketchError, match="not a usable name"):
        K.parse_sketch(program)


# ---------------------------------------------------------------------------
# The Scene validator (one view() result)
# ---------------------------------------------------------------------------

BASE = {"viewport": {"x": [0, 1], "y": [0, 1]}, "elements": []}


def scene(*elements, **extra):
    return {**copy.deepcopy(BASE), "elements": list(elements), **extra}


@pytest.mark.parametrize("bad,phrase", [
    ([], "must return an object"),
    ({"viewport": {"x": [1, 0], "y": [0, 1]}, "elements": []}, "min < max"),
    (scene(html="<b>x</b>"), "unknown keys"),
    (scene({"type": "image", "href": "https://example.com/a.png"}), "is not one of"),
    (scene({"type": "text", "x": 0, "y": 0, "text": "x", "href": "javascript:alert(1)"}), "unknown keys"),
    (scene({"type": "polyline", "x": [0, "NaN"], "y": [0, 1]}), "not a finite number (NaN)"),
    (scene({"type": "circle", "cx": "Infinity", "cy": 0, "r": 1}), "Infinity"),
    (scene({"type": "polyline", "x": [0, 1], "y": [0]}), "different lengths"),
    (scene({"type": "text", "x": 0, "y": 0, "text": "y" * 81}), "1-80 characters"),
    (scene({"type": "points", "x": [0], "y": [0], "style": {"color": "#ff0000"}}), "color must be"),
    (scene({"type": "points", "x": [0], "y": [0], "style": {"width": 9}}), "width"),
    (scene({"type": "points", "x": [0], "y": [0], "style": {"onclick": "x"}}), "style may have only"),
    (scene({"type": "heat_cells", "x": [0, 1], "y": [0, 1], "cols": 65, "rows": 64, "values": []}), "at most 4096"),
    (scene({"type": "handle", "id": "h", "x": 0, "y": 0, "binds": {"x": "nope"}}), "must name a parameter"),
    (scene({"type": "handle", "x": 0, "y": 0, "binds": {"x": "a"}}), "id must be"),
    (scene({"type": "points", "id": "a", "x": [0], "y": [0]}, {"type": "points", "id": "a", "x": [0], "y": [0]}),
     "used twice"),
    (scene({"type": "points", "id": "checked-by-LearnLoop", "x": [0], "y": [0]}), "check words"),
])
def test_scene_problems_name_what_cant_be_drawn(bad, phrase):
    problems = K.scene_problems(bad, parameters=["a"])
    assert problems and any(phrase in problem for problem in problems), problems


def test_a_scene_over_the_caps_is_refused():
    many = scene(*[{"type": "circle", "cx": 0, "cy": 0, "r": 1} for _ in range(K.SKETCH_MAX_ELEMENTS + 1)])
    assert "more than 4000" in K.scene_problems(many)[0]
    dense = scene(*[{"type": "polyline", "x": [0.0] * 4_000, "y": [0.0] * 4_000} for _ in range(11)])
    assert any("more than 40000 points" in problem for problem in K.scene_problems(dense))


def test_a_good_scene_has_no_problems():
    good = scene({"type": "polyline", "id": "p", "x": [0, 1], "y": [0, 1], "style": {"color": "series0", "dash": True}},
                 {"type": "arrow", "x1": 0, "y1": 0, "x2": 1, "y2": 1},
                 {"type": "text", "x": 0.5, "y": 0.5, "text": "label"},
                 {"type": "handle", "id": "h", "x": 0.2, "y": 0.3, "binds": {"x": "a"}},
                 axes={"x_label": "x", "y_label": "y"})
    assert K.scene_problems(good, parameters=["a"]) == []


def test_probe_problems_check_every_declared_shape():
    probes = {"s": K.Probe(name="s", label="s", shape="scalar"), "v": K.Probe(name="v", label="v", shape="series"),
              "p": K.Probe(name="p", label="p", shape="pairs")}
    assert K.probe_problems({"s": 1, "v": [1, 2], "p": [[0, 1]], "extra": "ignored"}, probes) == []
    assert "missing" in K.probe_problems({"v": [], "p": []}, probes)[0]
    assert "NaN" in K.probe_problems({"s": "NaN", "v": [], "p": []}, probes)[0]
    assert "pair" in K.probe_problems({"s": 1, "v": [], "p": [[0]]}, probes)[0]
