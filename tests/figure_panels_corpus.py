"""The golden corpus of RW5b's figure panels (reader workbench RW5b; spec §8.7, G21, G22, G46).

RW5a's corpus (``tests/figure_corpus.py``, ``figureGoldenCorpus.json``) is
kept byte for byte; RW5b's panels have their own file beside it, run by both
evaluators: ``tests/test_figure_panels.py`` (Python) and
``apps/learnloop-tauri/src/screens/reader/figures/figurePanels.test.ts``
(TypeScript). Regenerate it after changing a case:

    uv run python -m tests.figure_panels_corpus --write

Each figure case carries :func:`learnloop.figures.spec.evaluate_figure`'s
output at each parameter set. A case marked ``exact`` uses only ``+ - *`` and
``/`` (correctly rounded in both languages), so its trajectory or iterated map
must agree EXACTLY, step for step (the RK4 parity test); the others agree
within the corpus tolerance (``exp``, ``sin`` and ``cos`` may differ by an ulp
between the two runtimes' libraries). ``caps`` pins the code-owned maxima
both evaluators read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CORPUS_PATH = ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures" / "figurePanelsCorpus.json"

RELATIVE = 1e-9


def _spec(panels: list[dict[str, Any]], parameters: list[dict[str, Any]], *, definitions: list | None = None,
          demonstrates: str = "how the picture changes as the sliders move") -> dict[str, Any]:
    return {"spec_version": "ifs-v1", "kind": "illustrative", "demonstrates": demonstrates,
            "parameters": parameters, "definitions": definitions or [], "panels": panels}


def _param(name: str, low: float, high: float, step: float, default: float, label: str | None = None
           ) -> dict[str, Any]:
    return {"name": name, "label": label or name, "min": low, "max": high, "step": step, "default": default}


def quadratic_landscape() -> dict[str, Any]:
    """An objective landscape f(x, y) = a x² + b y² + c x y with two contours."""

    return _spec([{"kind": "heatmap_2d", "x": {"var": "x", "min": -2, "max": 2, "cells": 16},
                   "y": {"var": "y", "min": -2, "max": 2, "cells": 12}, "expr": "f",
                   "contours": ["1", "a + b"], "label": "loss"}],
                 [_param("a", 0.5, 3, 0.1, 1), _param("b", 0.5, 3, 0.1, 2), _param("c", -1, 1, 0.1, 0.5)],
                 definitions=[{"name": "f", "expr": "a*x*x + b*y*y + c*x*y"}])


def attention_weights() -> dict[str, Any]:
    """Attention-like weights over indices: a softmax over j by the sum construct."""

    return _spec([{"kind": "heatmap_2d", "x": {"var": "j", "min": 1, "max": 6, "cells": 5},
                   "y": {"var": "i", "min": 1, "max": 6, "cells": 5},
                   "expr": "exp(tau*i*j/6) / sum(exp(tau*i*m/6), m, 1, 6)", "label": "weight of j for query i"},
                  {"kind": "heatmap_2d", "x": {"var": "j", "min": 1, "max": 6, "cells": 5},
                   "y": {"var": "i", "min": 1, "max": 6, "cells": 5},
                   "expr": "sum(m*tau, m, 1, j) - sum(m, m, i, n)", "label": "bounds by the grid and a parameter"}],
                 [_param("tau", 0.1, 3, 0.1, 1, "temperature"), _param("n", 1, 6, 1, 4)])


def gaussian_density() -> dict[str, Any]:
    """A joint density with a correlation slider (exp and sqrt: tolerance, not exact)."""

    return _spec([{"kind": "heatmap_2d", "x": {"var": "x", "min": -3, "max": 3, "cells": 20},
                   "y": {"var": "y", "min": -3, "max": 3, "cells": 20},
                   "expr": "exp(-(x*x - 2*r*x*y + y*y)/(2*(1 - r*r))) / (2*pi*sqrt(1 - r*r))",
                   "label": "density"}],
                 [_param("r", -0.9, 0.9, 0.05, 0.3, "correlation")])


def gradient_field() -> dict[str, Any]:
    """The negative gradient of a bowl, over the bowl as a heat map."""

    return _spec([{"kind": "vector_field_2d", "x": {"var": "x", "min": -2, "max": 2, "cells": 8},
                   "y": {"var": "y", "min": -2, "max": 2, "cells": 8}, "u": "-2*a*x", "v": "-2*b*y",
                   "heatmap": {"expr": "a*x*x + b*y*y", "cells": 10, "contours": ["1"], "label": "loss"},
                   "label": "negative gradient"}],
                 [_param("a", 0.5, 2, 0.1, 1), _param("b", 0.5, 2, 0.1, 1.5)])


def rotation_field() -> dict[str, Any]:
    return _spec([{"kind": "vector_field_2d", "x": {"var": "x", "min": -1, "max": 1},
                   "y": {"var": "y", "min": -1, "max": 1}, "u": "-y + s*x", "v": "x + s*y", "label": "flow"}],
                 [_param("s", -1, 1, 0.1, 0)])


def damped_oscillator() -> dict[str, Any]:
    """dx/dt = y, dy/dt = -w² x - c y by RK4: arithmetic only, so EXACT step for step."""

    return _spec([{"kind": "trajectory_2d", "x": {"var": "x", "min": -2, "max": 2}, "y": {"var": "y", "min": -3, "max": 3},
                   "x0": "1", "y0": "0", "dx": "y", "dy": "-w*w*x - c*y", "t_max": "10", "steps": 200,
                   "label": "phase path"}],
                 [_param("w", 0.5, 2, 0.1, 1), _param("c", 0, 1, 0.05, 0.2)])


def forced_oscillator() -> dict[str, Any]:
    """A forced system (dy reads the time variable): cos, so within tolerance."""

    return _spec([{"kind": "trajectory_2d", "x": {"var": "x", "min": -4, "max": 4}, "y": {"var": "y", "min": -4, "max": 4},
                   "x0": "0", "y0": "0", "dx": "y", "dy": "-x - 0.3*y + A*cos(om*t)", "t_max": "12", "steps": 300,
                   "time": "t", "label": "driven path"}],
                 [_param("A", 0, 1.5, 0.1, 0.8), _param("om", 0.5, 2, 0.1, 1.2)])


def growth_leaves_plot() -> dict[str, Any]:
    """Exponential growth leaves its plot: the path is cut there and says so."""

    return _spec([{"kind": "trajectory_2d", "x": {"var": "x", "min": -2, "max": 2}, "y": {"var": "y", "min": -2, "max": 2},
                   "x0": "0.5", "y0": "0.1", "dx": "g*x", "dy": "-y", "t_max": "5", "steps": 100}],
                 [_param("g", 0.1, 2, 0.1, 1)])


def gradient_descent() -> dict[str, Any]:
    """Gradient descent on a x² + b y² with a learning-rate slider: EXACT; at a
    large learning rate it diverges and is cut where it leaves the plot."""

    return _spec([{"kind": "iterate_2d", "x": {"var": "x", "min": -2, "max": 2}, "y": {"var": "y", "min": -2, "max": 2},
                   "x0": "1.5", "y0": "1.8", "fx": "x - lr*2*a*x", "fy": "y - lr*2*b*y", "n": 40,
                   "label": "iterates"}],
                 [_param("lr", 0.01, 1, 0.01, 0.1, "learning rate"), _param("a", 0.5, 2, 0.1, 1),
                  _param("b", 0.5, 2, 0.1, 2)])


def henon_map() -> dict[str, Any]:
    """The Hénon map (chaotic: an ulp would grow to O(1)), arithmetic only: EXACT."""

    return _spec([{"kind": "iterate_2d", "x": {"var": "x", "min": -2, "max": 2}, "y": {"var": "y", "min": -1, "max": 1},
                   "x0": "0", "y0": "0", "fx": "1 - a*x*x + y", "fy": "b*x", "n": 200}],
                 [_param("a", 1, 1.4, 0.01, 1.4), _param("b", 0.1, 0.3, 0.01, 0.3)])


def not_finite_map() -> dict[str, Any]:
    """A map that divides by zero on its first step: ``not_finite`` (verification refuses it)."""

    return _spec([{"kind": "iterate_2d", "x": {"var": "x", "min": -2, "max": 2}, "y": {"var": "y", "min": -2, "max": 2},
                   "x0": "s", "y0": "0", "fx": "1/(x - s)", "fy": "y", "n": 5}],
                 [_param("s", 0, 1, 0.1, 1)])


def starts_outside() -> dict[str, Any]:
    return _spec([{"kind": "trajectory_2d", "x": {"var": "x", "min": -1, "max": 1}, "y": {"var": "y", "min": -1, "max": 1},
                   "x0": "x0v", "y0": "0", "dx": "-x", "dy": "-y", "t_max": "1", "steps": 10}],
                 [_param("x0v", 0, 3, 0.5, 3)])


#: (id, spec, parameter sets, exact)
FIGURES = (
    ("heatmap_quadratic_landscape", quadratic_landscape, [{}, {"a": 3, "b": 0.5, "c": -1}], True),
    ("heatmap_attention_weights", attention_weights, [{}, {"tau": 3, "n": 6}], False),
    ("heatmap_gaussian_density", gaussian_density, [{}, {"r": -0.9}], False),
    ("vector_field_gradient_over_heatmap", gradient_field, [{}, {"a": 2, "b": 0.5}], True),
    ("vector_field_rotation_default_cells", rotation_field, [{}, {"s": 0.5}], True),
    ("trajectory_damped_oscillator", damped_oscillator, [{}, {"w": 2, "c": 0}, {"w": 0.5, "c": 1}], True),
    ("trajectory_forced_with_time", forced_oscillator, [{}, {"A": 1.5, "om": 2}], False),
    ("trajectory_leaves_plot", growth_leaves_plot, [{}, {"g": 0.1}], True),
    ("iterate_gradient_descent", gradient_descent, [{}, {"lr": 0.45}, {"lr": 1}], True),
    ("iterate_henon_map", henon_map, [{}, {"a": 1.2, "b": 0.2}], True),
    ("iterate_not_finite", not_finite_map, [{}, {"s": 0.5}], True),
    ("trajectory_starts_outside", starts_outside, [{}, {"x0v": 0.5}], True),
)


def _rejected() -> list[dict[str, Any]]:
    one = [_param("a", 0, 1, 0.1, 0.5)]
    heat = {"kind": "heatmap_2d", "x": {"var": "x", "min": 0, "max": 1}, "y": {"var": "y", "min": 0, "max": 1}}
    path = {"kind": "trajectory_2d", "x": {"var": "x", "min": -1, "max": 1}, "y": {"var": "y", "min": -1, "max": 1},
            "x0": "0", "y0": "0", "dx": "y", "dy": "-x", "t_max": "1"}
    big = "x" + "+x" * 75  # 151 nodes, at 41 x 41 points: past MAX_PANEL_WORK
    rows = [
        ("integral_at_every_point", [{**heat, "expr": "integral(t*x, t, 0, 1)"}]),
        ("sum_bound_not_countable", [{**heat, "expr": "sum(m, m, 1, a + 1)"}]),
        ("sum_bound_a_definition", [{**heat, "expr": "sum(m, m, 1, top)"}]),
        ("sum_bound_a_path_state", [{**path, "dx": "sum(m, m, 1, x)"}]),
        ("same_axis_variable", [{**heat, "y": {"var": "x", "min": 0, "max": 1}, "expr": "x"}]),
        ("contour_reads_the_grid", [{**heat, "expr": "x*y", "contours": ["x"]}]),
        ("heatmap_too_many_cells", [{**heat, "x": {"var": "x", "min": 0, "max": 1, "cells": 41}, "expr": "x"}]),
        ("too_many_contours", [{**heat, "expr": "x", "contours": ["0.1"] * 9}]),
        ("field_too_many_cells", [{"kind": "vector_field_2d", "x": {"var": "x", "min": 0, "max": 1, "cells": 21},
                                   "y": {"var": "y", "min": 0, "max": 1}, "u": "1", "v": "0"}]),
        ("heatmap_range_not_increasing", [{**heat, "x": {"var": "x", "min": 1, "max": 1}, "expr": "x"}]),
        ("too_much_computation", [{**heat, "x": {"var": "x", "min": 0, "max": 1, "cells": 40},
                                   "y": {"var": "y", "min": 0, "max": 1, "cells": 40}, "expr": big}]),
        ("too_much_computation_across_panels", [
            {**heat, "x": {"var": "x", "min": 0, "max": 1, "cells": 40},
             "y": {"var": "y", "min": 0, "max": 1, "cells": 40}, "expr": "x" + "+x" * 40},
            {**heat, "x": {"var": "x", "min": 0, "max": 1, "cells": 40},
             "y": {"var": "y", "min": 0, "max": 1, "cells": 40}, "expr": "x" + "+x" * 40}]),
        ("trajectory_zero_steps", [{**path, "steps": 0}]),
        ("trajectory_too_many_steps", [{**path, "steps": 2001}]),
        ("trajectory_time_is_x", [{**path, "time": "x"}]),
        ("trajectory_unknown_name", [{**path, "dy": "-x*z"}]),
        ("trajectory_start_reads_the_state", [{**path, "x0": "y"}]),
        ("iterate_too_many", [{"kind": "iterate_2d", "x": {"var": "x", "min": -1, "max": 1},
                               "y": {"var": "y", "min": -1, "max": 1}, "x0": "0", "y0": "0", "fx": "x", "fy": "y",
                               "n": 501}]),
    ]
    out = []
    for case_id, panels in rows:
        definitions = [{"name": "top", "expr": "3"}] if case_id == "sum_bound_a_definition" else []
        out.append({"id": case_id, "spec": _spec(panels, one, definitions=definitions)})
    return out


def caps() -> dict[str, Any]:
    from learnloop.figures import spec as S

    return {"MAX_HEATMAP_CELLS": S.MAX_HEATMAP_CELLS, "DEFAULT_HEATMAP_CELLS": S.DEFAULT_HEATMAP_CELLS,
            "MAX_FIELD_CELLS": S.MAX_FIELD_CELLS, "DEFAULT_FIELD_CELLS": S.DEFAULT_FIELD_CELLS,
            "MAX_TRAJECTORY_STEPS": S.MAX_TRAJECTORY_STEPS, "DEFAULT_TRAJECTORY_STEPS": S.DEFAULT_TRAJECTORY_STEPS,
            "MAX_ITERATIONS": S.MAX_ITERATIONS, "DEFAULT_ITERATIONS": S.DEFAULT_ITERATIONS,
            "MAX_CONTOURS": S.MAX_CONTOURS, "MAX_PANEL_WORK": S.MAX_PANEL_WORK, "ESCAPE_MARGIN": S.ESCAPE_MARGIN}


def build() -> dict[str, Any]:
    from learnloop.figures import spec as S

    figures = []
    for case_id, make, params, exact in FIGURES:
        spec = make()
        compiled = S.parse_spec(spec)
        figures.append({"id": case_id, "spec": spec, "params": params, "exact": exact,
                        "expected": [S.evaluate_figure(compiled, values) for values in params]})
    return {
        "version": 1,
        "note": "Generated by tests/figure_panels_corpus.py (uv run python -m tests.figure_panels_corpus --write); "
                "read by tests/test_figure_panels.py and figurePanels.test.ts.",
        "tolerance": {"relative": RELATIVE},
        "caps": caps(),
        "figures": figures,
        "rejected_figures": _rejected(),
    }


def render() -> str:
    return json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    if "--write" in sys.argv:
        CORPUS_PATH.write_text(render(), encoding="utf-8")
        print(f"wrote {CORPUS_PATH}")
    else:
        sys.stdout.write(render())
