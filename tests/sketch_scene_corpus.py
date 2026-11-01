"""RW5d P2: the shared Scene/probe validator corpus (spec_reader_show_me_figures_v1 §9.1, "both validators").

Each case is a view() or probes() result and the problems the sidecar's
validator (``learnloop.figures.sketch``) finds; ``sketchScene.test.ts`` asserts
the desktop's validator (``sketchScene.ts``) finds exactly the same.
Regenerate after an intended change::

    uv run python -m tests.sketch_scene_corpus
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learnloop.figures import sketch as K

PATH = (Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures"
        / "sketch" / "sketchSceneCorpus.json")
PARAMETERS = ["a", "b"]
PROBES = [{"name": "s", "label": "a scalar", "shape": "scalar"}, {"name": "v", "label": "a series", "shape": "series"},
          {"name": "p", "label": "pairs", "shape": "pairs"}]


def _scene(*elements: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {"viewport": {"x": [0, 1], "y": [0, 1]}, "elements": list(elements), **extra}


SCENES: list[tuple[str, Any]] = [
    ("empty but valid", _scene()),
    ("every kind, valid", _scene(
        {"type": "polyline", "id": "line", "x": [0, 0.5, 1], "y": [0, 1, 0], "style": {"color": "series0", "dash": True}},
        {"type": "polygon", "x": [0, 1, 1], "y": [0, 0, 1], "style": {"fill": True, "opacity": 0.5}},
        {"type": "points", "id": "dots", "x": [0.1, 0.2], "y": [0.3, 0.4], "r": 3},
        {"type": "segment", "x1": 0, "y1": 0, "x2": 1, "y2": 1, "style": {"width": 2}},
        {"type": "arrow", "x1": 0, "y1": 1, "x2": 1, "y2": 0},
        {"type": "circle", "cx": 0.5, "cy": 0.5, "r": 0.2, "style": {"color": "accent"}},
        {"type": "rect", "x": 0, "y": 0, "w": 1, "h": 1, "style": {"color": "muted"}},
        {"type": "text", "x": 0.5, "y": 0.5, "text": "<b>not markup</b>"},
        {"type": "heat_cells", "id": "heat", "x": [0, 1], "y": [0, 1], "cols": 2, "rows": 2, "values": [0, 1, 2, 3]},
        {"type": "handle", "id": "h", "x": 0.2, "y": 0.3, "binds": {"x": "a", "y": "b"}},
        axes={"x_label": "x", "y_label": "y"})),
    ("not an object", []),
    ("a reversed viewport", {"viewport": {"x": [1, 0], "y": [0, 1]}, "elements": []}),
    ("a viewport with NaN", {"viewport": {"x": [0, "NaN"], "y": [0, 1]}, "elements": []}),
    ("markup at the top level", _scene(html="<b>x</b>")),
    ("an image element", _scene({"type": "image", "href": "https://example.com/a.png"})),
    ("a missing type", _scene({"x": [0], "y": [0]})),
    ("a link on text", _scene({"type": "text", "x": 0, "y": 0, "text": "x", "href": "javascript:alert(1)"})),
    ("NaN in a path", _scene({"type": "polyline", "x": [0, "NaN"], "y": [0, 1]})),
    ("Infinity in a circle", _scene({"type": "circle", "cx": "Infinity", "cy": 0, "r": 1})),
    ("a boolean coordinate", _scene({"type": "segment", "x1": True, "y1": 0, "x2": 1, "y2": None})),
    ("lengths differ", _scene({"type": "polyline", "x": [0, 1], "y": [0]})),
    ("text too long", _scene({"type": "text", "x": 0, "y": 0, "text": "y" * 81})),
    ("a colour outside the palette", _scene({"type": "points", "x": [0], "y": [0], "style": {"color": "#ff0000"}})),
    ("too wide a line", _scene({"type": "points", "x": [0], "y": [0], "style": {"width": 9}})),
    ("an event in a style", _scene({"type": "points", "x": [0], "y": [0], "style": {"onclick": "x"}})),
    ("too many cells", _scene({"type": "heat_cells", "x": [0, 1], "y": [0, 1], "cols": 65, "rows": 64, "values": []})),
    ("cells and values disagree", _scene({"type": "heat_cells", "x": [0, 1], "y": [0, 1], "cols": 2, "rows": 2,
                                          "values": [1, 2, 3]})),
    ("a handle bound to nothing", _scene({"type": "handle", "id": "h", "x": 0, "y": 0, "binds": {"x": "nope"}})),
    ("a handle with no id", _scene({"type": "handle", "x": 0, "y": 0, "binds": {"x": "a"}})),
    ("an id used twice", _scene({"type": "points", "id": "a", "x": [0], "y": [0]},
                                {"type": "points", "id": "a", "x": [0], "y": [0]})),
    ("an id with a check word", _scene({"type": "points", "id": "checked-by-LearnLoop", "x": [0], "y": [0]})),
    ("a negative radius and size", _scene({"type": "circle", "cx": 0, "cy": 0, "r": -1},
                                          {"type": "rect", "x": 0, "y": 0, "w": -1, "h": 1})),
    ("axes with markup keys", _scene(axes={"x_label": "x", "title": "<script>"})),
    # (the element and point caps are tested in each language: their scenes are large)
]

PROBE_CASES: list[tuple[str, Any]] = [
    ("every shape, valid, an extra ignored", {"s": 1, "v": [1, 2], "p": [[0, 1]], "extra": "ignored"}),
    ("not an object", [1, 2]),
    ("missing ones", {"v": []}),
    ("a NaN scalar", {"s": "NaN", "v": [], "p": []}),
    ("Infinity in a series", {"s": 1, "v": [1, "Infinity"], "p": []}),
    ("a broken pair", {"s": 1, "v": [], "p": [[0]]}),
]


def build() -> dict[str, Any]:
    probes = {item["name"]: K.Probe(**item) for item in PROBES}
    return {
        "about": "RW5d P2 shared validator corpus: the problems learnloop.figures.sketch finds; sketchScene.ts must "
                 "find exactly the same (tests/sketch_scene_corpus.py regenerates it).",
        "parameters": PARAMETERS, "probes": PROBES,
        "scenes": [{"name": name, "scene": scene, "problems": K.scene_problems(scene, parameters=PARAMETERS)}
                   for name, scene in SCENES],
        "probe_cases": [{"name": name, "values": values, "problems": K.probe_problems(values, probes)}
                        for name, values in PROBE_CASES],
    }


def write() -> None:
    PATH.write_text(json.dumps(build(), ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write()
