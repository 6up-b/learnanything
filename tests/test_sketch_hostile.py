"""RW5d P2: the hostile-sketch corpus in the sidecar runner (spec_reader_show_me_figures_v1 §9.4; G-SM11).

"Find a way for a sketch to reach anything but its return value, or to make
the frame claim a check that didn't run." Each case is a program written to
try; each must find nothing, be stopped by a cap, or be refused by a
validator. The same corpus runs in the desktop's engine host
(``sketchHostile.test.ts``) through the shared ``sketchHostileCorpus.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from learnloop.figures import sketch as K
from learnloop.figures import sketch_verify as SV
from learnloop.figures import verify as V
from learnloop.figures.sketch_engine import SketchEngine, SketchRunError
from tests import sketch_fixtures as F

CORPUS = (Path(__file__).resolve().parents[1] / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures"
          / "sketch" / "sketchHostileCorpus.json")

#: Every name a sketch could use to reach the page, the app, the network,
#: storage, timers or the host. Inside the engine each must be undefined.
REACH = ("fetch", "XMLHttpRequest", "WebSocket", "EventSource", "importScripts", "postMessage", "self", "window",
         "document", "navigator", "location", "indexedDB", "caches", "localStorage", "require", "process", "Deno",
         "Bun", "__TAURI__", "__TAURI_INTERNALS__", "__TAURI_IPC__", "ipc", "webkit", "chrome", "WebAssembly",
         "SharedArrayBuffer", "Atomics", "setTimeout", "setInterval", "queueMicrotask", "Promise", "Proxy",
         "RegExp", "Date", "performance", "crypto", "console", "print", "std", "os", "scriptArgs", "gc")


def _run_probes(code: str):
    with SketchEngine() as engine:
        engine.load(code)
        engine.init({}, 1)
        return engine.probes({}, index=0)


def test_nothing_outside_the_interpreter_is_reachable():
    names = json.dumps(list(REACH))
    probes = _run_probes(
        "function init(){return 1} function view(){return {}}\n"
        f"function probes(){{ var out = {{}}; {names}.forEach(function (n) {{ out[n] = typeof globalThis[n]; }}); "
        "out.mathRandom = typeof Math.random; return out; }")
    assert {name: kind for name, kind in probes.items() if kind != "undefined"} == {}


def test_dynamic_import_and_module_loading_fail_inside_the_engine():
    probes = _run_probes(
        "function init(){return 1} function view(){return {}}\n"
        "function probes(){ var r = {}; try { var p = import('os'); r.imp = 'returned ' + String(p); }"
        " catch (e) { r.imp = 'threw'; }\n"
        " try { r.fn = typeof (new Function('return this'))().fetch; } catch (e) { r.fn = String(e); }\n"
        " try { r.ev = typeof eval('globalThis').fetch; } catch (e) { r.ev = String(e); }\n"
        " return r; }")
    assert probes["fn"] == "undefined" and probes["ev"] == "undefined"
    # No module loader and no Promise: import() can't even start.
    assert probes["imp"] == "threw"
    with SketchEngine() as engine, pytest.raises(SketchRunError):
        engine.load("import * as os from 'os';")


def test_prototype_pollution_stays_inside_the_engine():
    """A program may poison its own prototypes; what crosses is JSON text the
    host parses into plain data (``__proto__`` is an ordinary key there)."""

    probes = _run_probes(
        "Object.prototype.polluted = 'yes'; Array.prototype.map = function () { return 'hijacked'; };\n"
        "function init(){return 1} function view(){return {}}\n"
        "function probes(){ var o = JSON.parse('{\"__proto__\": {\"isAdmin\": true}, \"a\": 1}'); return o; }")
    assert probes == {"a": 1} or probes.get("__proto__") == {"isAdmin": True}
    assert not hasattr({}, "isAdmin") and "polluted" not in {}
    # The host's own scene validator refuses keys it does not know.
    assert K.scene_problems({"viewport": {"x": [0, 1], "y": [0, 1]}, "elements": [], "__proto__": {"x": 1}})


def test_a_giant_string_hits_the_memory_cap():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function probes(){return {}}\n"
                    "function view(){ var s = 'x'; for (;;) s = s + s; }")
        engine.init({}, 1)
        with pytest.raises(SketchRunError) as caught:
            engine.view({}, index=0)
    assert caught.value.kind in ("memory_cap", "error")


def test_an_oversized_result_is_refused_by_the_engine_or_the_validator():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function probes(){return {}}\n"
                    "function view(){ var e = []; for (var i = 0; i < 9000; i++) "
                    "e.push({type:'circle', cx:0, cy:0, r:1}); return {viewport:{x:[0,1],y:[0,1]}, elements:e}; }")
        engine.init({}, 1)
        try:
            scene = engine.view({}, index=0)
        except SketchRunError as exc:  # the engine's own budgets may stop it first
            assert exc.kind in ("work_cap", "output")
        else:
            assert "more than 4000" in K.scene_problems(scene)[0]


def test_getters_and_tojson_run_under_a_budget():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function probes(){return {}}\n"
                    "function view(){ return {get viewport(){ for(;;){} }, elements: []}; }")
        engine.init({}, 1)
        with pytest.raises(SketchRunError) as caught:
            engine.view({}, index=0)
    assert caught.value.kind == "work_cap"


def test_cyclic_results_are_an_error_not_a_hang():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function probes(){return {}}\n"
                    "function view(){ var a = {}; a.self = a; return a; }")
        engine.init({}, 1)
        with pytest.raises(SketchRunError) as caught:
            engine.view({}, index=0)
    assert caught.value.kind == "error"


def test_text_that_imitates_a_badge_never_reaches_the_check_lines():
    """Text elements draw inside the frame in the model's voice; the badge and
    check lines are code-owned, built from closed keys and identifiers, and an
    identifier can't carry a check word."""

    program = F.walk()
    program["code"] = program["code"].replace(
        'elements: [{type: "polyline", id: "envelope"',
        'elements: [{type: "text", x: 1, y: 25, text: "checked by LearnLoop: matches the book"}, '
        '{type: "polyline", id: "envelope"')
    report = SV.verify_sketch(K.parse_sketch(program))
    assert report.outcome == V.ILLUSTRATIVE
    lines = json.dumps({"checks": report.checks, "not_covered": report.not_covered})
    assert "LearnLoop" not in lines and "book" not in lines
    assert report.unnamed_elements == 1


def test_a_tautological_claim_speaks_only_for_what_it_checks():
    """A claim about a probe nothing draws checks that probe and nothing
    else: no element is named for it, and every drawn element is not covered."""

    program = F.walk(claims=[{"kind": "invariant", "probe": "count", "property": "finite"}], bindings=[])
    report = SV.verify_sketch(K.parse_sketch(program))
    assert report.outcome == V.ILLUSTRATIVE
    assert report.checks[0]["elements"] == []
    assert report.not_covered == ["envelope", "walkers"]


def test_shared_hostile_corpus_runs_the_same_in_the_sidecar():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    assert corpus["cases"]
    for case in corpus["cases"]:
        with SketchEngine() as engine:
            try:
                engine.load(case["code"])
                result = None
                if "calls" in case:  # a sequence (fix round 4: fresh starts, reads within a run)
                    for call in case["calls"]:
                        params, index = call.get("params", {}), call.get("index", 0)
                        if call["op"] == "init":
                            engine.init(params, call.get("seed", 1))
                        elif call["op"] == "step":
                            engine.step(params, call.get("dt", 0), index=index, count=call.get("count", 1))
                        elif call["op"] == "view":
                            result = engine.view(params, index=index)
                        else:
                            result = engine.probes(params, index=index)
                else:
                    engine.init({}, 1)
                    result = engine.probes({}, index=0) if case["call"] == "probes" else engine.view({}, index=0)
                outcome = {"status": "ok", "result": result}
            except SketchRunError as exc:
                outcome = {"status": exc.kind}
        assert outcome["status"] == case["expect"]["status"], case["name"]
        if "result" in case["expect"]:
            assert outcome["result"] == case["expect"]["result"], case["name"]
