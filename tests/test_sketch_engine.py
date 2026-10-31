"""RW5d P2: the sketch engine and its sidecar runner (spec_reader_show_me_figures_v1 §9.2-9.4; G-SM13).

The pinned artifact, its digest in three places, the deny-all import surface,
the compiled-in caps, chunking-independent seeding, the status of each cap,
and the refusal of a digest mismatch.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from learnloop.figures import sketch_engine as E
from learnloop.figures.sketch_engine import SketchEngine, SketchRunError

ROOT = Path(__file__).resolve().parents[1]
TS_ENGINE = ROOT / "apps" / "learnloop-tauri" / "src" / "screens" / "reader" / "figures" / "sketch" / "sketchEngine.ts"

COUNTER = r"""
function init(p, seed) { return {n: 0, draws: []}; }
function step(s, p, dt) { return {n: s.n + 1, draws: s.draws.concat([rand()])}; }
function view(s, p) { return {viewport: {x: [0, 1], y: [0, 1]}, elements: []}; }
function probes(s, p) { return {n: s.n, draws: s.draws, k: p.k}; }
"""


def test_the_artifact_hashes_to_the_pin_in_the_lock_file_and_the_runner():
    lock = json.loads(E.LOCK_PATH.read_text(encoding="utf-8"))
    digest = hashlib.sha256(E.ENGINE_PATH.read_bytes()).hexdigest()
    assert digest == lock["output"]["sha256"] == E.ENGINE_SHA256
    assert E.ENGINE_PATH.stat().st_size == lock["output"]["bytes"] < 5 * 1024 * 1024
    # Every source the build fetches is pinned by digest.
    for source in lock["sources"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) and source["url"].startswith("https://")


def test_the_desktop_pins_the_same_digest():
    text = TS_ENGINE.read_text(encoding="utf-8")
    assert f'ENGINE_SHA256 = "{E.ENGINE_SHA256}"' in text


def test_the_module_imports_only_what_the_deny_all_shim_answers():
    import wasmtime

    engine = wasmtime.Engine()
    module = wasmtime.Module(engine, E.ENGINE_PATH.read_bytes())
    assert {(item.module, item.name) for item in module.imports} <= E.ALLOWED_IMPORTS
    exports = {item.name for item in module.exports}
    assert {"memory", "_initialize", "sk_load", "sk_init", "sk_step", "sk_view", "sk_probes"} <= exports


def test_the_caps_are_compiled_in_and_match_the_constants():
    with SketchEngine() as engine:
        limits = engine.limits()
    assert limits["memory_bytes"] == E.SKETCH_MEMORY_BYTES
    assert limits["ticks_per_call"] == E.SKETCH_FUEL_PER_CALL
    assert limits["serialize_ticks"] == E.SKETCH_SERIALIZE_TICKS
    assert limits["quickjs"] == "0.17.0"


def test_load_reports_entry_points_and_calls_return_json():
    with SketchEngine() as engine:
        assert engine.load(COUNTER) == {"init": True, "step": True, "view": True, "probes": True}
        engine.init({"k": 2}, 7)
        engine.step({"k": 2}, 1.0, index=0, count=3)
        probes = engine.probes({"k": 2}, index=3)
    assert probes["n"] == 3 and probes["k"] == 2 and len(probes["draws"]) == 3
    assert all(0 <= value < 1 for value in probes["draws"])


def test_seeding_depends_on_seed_and_step_never_on_how_calls_are_chunked():
    def draws(chunks: list[int], seed: int) -> list[float]:
        with SketchEngine() as engine:
            engine.load(COUNTER)
            engine.init({"k": 0}, seed)
            index = 0
            for count in chunks:
                engine.step({"k": 0}, 1.0, index=index, count=count)
                # Reads in between never move the stream.
                engine.view({"k": 0}, index=index + count)
                index += count
            return engine.probes({"k": 0}, index=index)["draws"]

    one = draws([6], 3)
    assert draws([1, 2, 3], 3) == one == draws([2, 2, 1, 1], 3)
    assert draws([6], 4) != one


@pytest.mark.parametrize("entry", ["init", "view", "probes", "step"])
def test_an_endless_loop_in_any_entry_point_hits_the_work_cap(entry):
    bodies = {name: "return {};" for name in ("init", "step", "view", "probes")}
    bodies[entry] = "while (true) {}"
    code = "\n".join(f"function {name}() {{ {body} }}" for name, body in bodies.items())
    with SketchEngine() as engine:
        engine.load(code)
        with pytest.raises(SketchRunError) as caught:
            engine.init({}, 1)
            engine.step({}, 1.0, index=0, count=1)
            engine.view({}, index=1)
            engine.probes({}, index=1)
    assert caught.value.kind == "work_cap" and not caught.value.trap
    assert entry in caught.value.message


def test_a_load_time_loop_is_capped_too():
    with SketchEngine() as engine, pytest.raises(SketchRunError) as caught:
        engine.load("for (;;) {}")
    assert caught.value.kind == "work_cap"


def test_memory_and_recursion_have_their_own_statuses():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function view(){ var a=[]; for(;;) a.push(new Float64Array(100000)); }"
                    " function probes(){ function f(n){ return f(n + 1) + 1; } return f(0); }")
        engine.init({}, 1)
        with pytest.raises(SketchRunError) as memory:
            engine.view({}, index=0)
        with pytest.raises(SketchRunError) as stack:
            engine.probes({}, index=0)
    assert memory.value.kind == "memory_cap"
    assert stack.value.kind == "stack"


def test_a_thrown_error_is_reported_in_the_engines_words():
    with SketchEngine() as engine:
        engine.load("function init(){ throw new Error('bad start'); } function view(){} function probes(){}")
        with pytest.raises(SketchRunError) as caught:
            engine.init({}, 1)
    assert caught.value.kind == "error" and "bad start" in caught.value.message


def test_non_finite_numbers_cross_as_named_strings():
    with SketchEngine() as engine:
        engine.load("function init(){return 1} function view(){return {}} "
                    "function probes(){ return {a: 0/0, b: 1/0, c: -1/0, d: 1.5}; }")
        engine.init({}, 1)
        assert engine.probes({}, index=0) == {"a": "NaN", "b": "Infinity", "c": "-Infinity", "d": 1.5}


def test_a_new_load_starts_from_nothing():
    with SketchEngine() as engine:
        engine.load("var leaked = 41; function init(){return 1} function view(){return {}} function probes(){return {}}")
        entries = engine.load("function init(){return 1} function view(){return {}} "
                              "function probes(){ return {seen: typeof leaked}; }")
        engine.init({}, 1)
        assert entries["step"] is False
        assert engine.probes({}, index=0) == {"seen": "undefined"}


def test_a_digest_mismatch_refuses_to_load(tmp_path):
    """G-SM13: a tampered or different engine is never run."""

    tampered = tmp_path / "sketch-engine.wasm"
    data = bytearray(E.ENGINE_PATH.read_bytes())
    data[-1] ^= 0x01
    tampered.write_bytes(bytes(data))
    with pytest.raises(E.EngineUnavailable, match="not the pinned"):
        SketchEngine(path=tampered)
    assert E.engine_ready(path=tampered) is False
    assert E.engine_ready(path=tmp_path / "missing.wasm") is False
    assert E.engine_ready() is True


def test_a_trapped_instance_is_never_called_again(monkeypatch):
    monkeypatch.setattr(E, "WASM_FUEL_PER_CALL", 50_000)
    with SketchEngine() as engine:
        with pytest.raises(SketchRunError) as caught:
            engine.load("var x = 0; for (var i = 0; i < 1e9; i++) x += i;")
        assert caught.value.trap and caught.value.kind == "work_cap"
        with pytest.raises(SketchRunError, match="new one is needed"):
            engine.limits()


# ---------------------------------------------------------------------------
# Codex review F7: one sketch's timeout never stops another
# ---------------------------------------------------------------------------

#: A native loop the interpreter barely polls (one poll per copy of 16 MB):
#: wall-clock work the epoch deadline, not the tick budget, has to stop.
COPIES = ("var a = new Float64Array(2000000); "
          "function init(p) { for (var i = 0; i < p.n; i++) a.copyWithin(0, 1); return {}; } "
          "function view() { return {}; } function probes() { return {}; }")


def _timed_init(engine: SketchEngine, n: int, out: dict, key: str) -> None:
    import time

    started = time.monotonic()
    try:
        engine.init({"n": n}, 1)
        out[key] = ("ok", time.monotonic() - started)
    except SketchRunError as exc:
        out[key] = (exc.kind, time.monotonic() - started)


def test_one_sketchs_timeout_does_not_stop_a_concurrent_one(monkeypatch):
    """Two stores of the one cached wasmtime Engine run at once; A has a
    0.3 s deadline and endless native work, B has the normal allowance and
    ~0.5 s of work. A is stopped at its deadline; B finishes. (Before F7's
    fix, A's timer advanced the shared epoch and trapped B too.)"""

    import threading
    import time

    monkeypatch.setattr(E, "WASM_FUEL_PER_CALL", 10 ** 15)  # wall clock, not fuel, is what bites
    out: dict = {}
    with SketchEngine() as a, SketchEngine() as b:
        a.load(COPIES)
        b.load(COPIES)
        a.deadline = time.monotonic() + 0.3
        runner = threading.Thread(target=_timed_init, args=(a, 10 ** 9, out, "a"))
        runner.start()
        _timed_init(b, 5_000, out, "b")
        runner.join()
    assert out["a"][0] == "work_cap" and out["a"][1] < 5
    assert out["b"][0] == "ok", out
    assert out["b"][1] > 0.3, out  # B was still running when A's deadline passed


def test_another_stores_epoch_tick_does_not_trap_a_running_call(monkeypatch):
    """The old per-call timer advanced the shared epoch by one on a timeout;
    a call's deadline is now many ticks of the shared clock ahead, so a stray
    tick from elsewhere never stops it."""

    import threading
    import time

    monkeypatch.setattr(E, "WASM_FUEL_PER_CALL", 10 ** 15)
    out: dict = {}
    with SketchEngine() as engine:
        engine.load(COPIES)
        runner = threading.Thread(target=_timed_init, args=(engine, 5_000, out, "b"))
        runner.start()
        time.sleep(0.05)
        for _ in range(3):
            engine.engine.increment_epoch()
        runner.join()
    assert out["b"][0] == "ok", out


def test_a_call_never_starts_past_the_callers_deadline():
    import time

    with SketchEngine() as engine:
        engine.deadline = time.monotonic() - 1
        with pytest.raises(SketchRunError, match="out of time") as caught:
            engine.load(COUNTER)
    assert caught.value.kind == "work_cap"
    assert E.deadline_ticks(E.CALL_SECONDS) == round(E.CALL_SECONDS / E.EPOCH_TICK_SECONDS) + 1


def test_the_epoch_clock_runs_only_while_an_engine_is_open():
    import threading

    def clocks() -> list[threading.Thread]:
        return [thread for thread in threading.enumerate() if thread.name == "sketch-epoch-clock"]

    assert clocks() == []
    with SketchEngine(), SketchEngine():
        assert len(clocks()) == 1  # one clock per wasmtime Engine, shared
    assert clocks() == []
