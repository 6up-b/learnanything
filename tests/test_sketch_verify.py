"""RW5d P2: SketchProgramV1, the Scene validator and headless verification
(spec_reader_show_me_figures_v1 §9.1, §9.5; G-SM10).

Good sketches pass with the right check lines; planted-wrong ones are each
refused at the right step for the right reason.
"""

from __future__ import annotations

import copy

import pytest

from learnloop.figures import sketch as K
from learnloop.figures import sketch_verify as SV
from learnloop.figures import verify as V
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
                      "statement": "sqrt(x)", "settings": 27}
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
