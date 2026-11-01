"""Builders and fakes for Reader RW5d P2b's rich-tier tests (the Manim half; no network, no Manim, no bwrap).

* :func:`ready_manim` makes this machine look ready for the Manim tier
  (Linux, ``bwrap``, Manim installed) without probing anything.
* :class:`RichAuthorFake` answers ``figure_rich_author`` from a queue of
  ``FigureManimOutputV1`` dicts (or exceptions), recording every prompt.
* :func:`ok_renderer` / :func:`failing_renderer` stand in for the concept
  pipeline's ``render_scene`` (a tiny real mp4, or a failure with stderr);
  :func:`inprocess_runner` runs the extracted functions in this process
  (the module the sandbox would run; tests only), and asserts it never
  names manim.
* :func:`brief` is an author's rich brief; :data:`SCENE` a valid scene with a
  declared function ``x(t, a, b)`` drawn by ``axes.plot``.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from learnloop.content.authoring.concept_animation import RenderResult
from learnloop.figures import rich as RICH
from tests.figure_fixtures import _Recording
from tests.media_fakes import tiny_mp4

SCENE = '''from manim import *
import numpy as np
import math

DAMPING = 0.5


def x(t, a, b):
    return math.exp(a * t) * math.cos(b * t)


def helper_uses_manim(t):
    return ValueTracker(t).get_value()


class SpiralExplainer(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 6], y_range=[-2, 2])
        curve = axes.plot(lambda t: x(t, -DAMPING, 2.0), color=BLUE)
        self.play(Create(axes), run_time=2)
        self.play(Create(curve), run_time=4)
        for _ in range(8):
            self.wait(4)
'''

DECLARED = {
    "functions": [{"name": "x", "args": [{"name": "t", "min": 0, "max": 6}, {"name": "a", "min": -1, "max": 0},
                                         {"name": "b", "min": 1, "max": 3}], "shape": "scalar"},
                  {"name": "helper_uses_manim", "args": [{"name": "t", "min": 0, "max": 1}], "shape": "scalar"}],
    "claims": [{"kind": "equals", "function": "x", "expr": "exp(a*t)*cos(b*t)"},
               {"kind": "invariant", "function": "x", "property": "bounded", "bound": 2},
               {"kind": "invariant", "function": "helper_uses_manim", "property": "finite"}],
    "plotted_from": [{"function": "x"}],
}


def scene_output(*, scene: str = SCENE, declared: Any = None, scene_class: str = "SpiralExplainer") -> dict[str, Any]:
    return {"scene_code": scene, "scene_class": scene_class, "title": "Why the trajectory spirals",
            "narration_md": "When the eigenvalues are complex the solution turns as it decays.",
            "declared_json": json.dumps(DECLARED if declared is None else declared)}


def brief(**changes: Any) -> dict[str, Any]:
    found = {"tier": "manim", "brief": "Animate x(t) = e^{at} cos(bt) as b grows; show the spiral tighten.",
             "demonstrates": "why the trajectory spirals when the eigenvalues are complex",
             "assumptions": [{"text": "a < 0"}], "source_claims": [],
             "claims_planned": ["x equals exp(a*t)*cos(b*t)"]}
    found.update(changes)
    return found


def ready_manim(monkeypatch: Any, *, version: str = "Manim Community v0.19.1") -> None:
    import learnloop.content.authoring.concept_animation as CA

    monkeypatch.setattr(RICH, "manim_runtime_state",
                        lambda vault, probe=True: {"ready": True, "reason": None, "version": version})
    # No transient systemd scope is started by a test: the capped scope falls back to prlimit.
    monkeypatch.setattr(CA, "_SCOPE_PROBE", {"ok": False})


class RichAuthorFake(_Recording):
    def __init__(self, answers: list[Any] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.answers = list(answers or [])

    def complete(self, request: Any) -> Any:
        assert request.purpose == RICH.RICH_TASK
        self._record(request)
        answer = self.answers.pop(0) if self.answers else scene_output()
        if isinstance(answer, BaseException):
            raise answer
        return request.result_model.model_validate(answer)


class Renders:
    """A ``render_scene`` stand-in that records its calls (scene, class, kwargs)."""

    def __init__(self, results: list[RenderResult] | None = None) -> None:
        self.results = list(results or [])
        self.calls: list[dict[str, Any]] = []

    def __call__(self, scene_code: str, scene_class: str, **kwargs: Any) -> RenderResult:
        self.calls.append({"scene_code": scene_code, "scene_class": scene_class, **kwargs})
        if self.results:
            return self.results.pop(0)
        return RenderResult(True, tiny_mp4(), "", 0)


def failed_render(stderr: str = "NameError: name 'Cirle' is not defined") -> RenderResult:
    return RenderResult(False, None, stderr, 1)


class InProcessRunner:
    """Runs the extracted module in this process (tests only) and records what it was given."""

    def __init__(self) -> None:
        self.sources: list[str] = []

    def __call__(self, source: str, points: Mapping[str, list[list[float]]]) -> dict[str, Any]:
        assert "manim" not in source, "the extracted module must never name manim"
        self.sources.append(source)
        namespace: dict[str, Any] = {}
        exec(compile(source, "<figure_functions>", "exec"), namespace)  # noqa: S102 - test-only stand-in
        results: dict[str, list[dict[str, Any]]] = {}
        for name, grid in points.items():
            values = []
            for point in grid:
                try:
                    values.append({"value": float(namespace[name](*point))})
                except Exception as exc:  # noqa: BLE001 - as the sandbox harness reports it
                    values.append({"error": type(exc).__name__})
            results[name] = values
        return {"results": results}


def configure(paths: Any, **values: Any) -> None:
    """Set ``[figures]`` keys in place (``set_config`` appends; a key set twice would not parse)."""

    from learnloop.ops.settings_store import apply_config_updates

    apply_config_updates(paths.root / "learnloop.toml", {("figures", key): value for key, value in values.items()})
