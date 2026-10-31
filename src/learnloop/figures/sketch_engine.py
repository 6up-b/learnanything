"""The sketch engine's sidecar runner (spec_reader_show_me_figures_v1 §9.2-9.4; RW5d P2).

The same ``sketch-engine.wasm`` the desktop runs in its Web Worker (QuickJS-ng
compiled to WebAssembly by ``apps/learnloop-tauri/sketch-engine/build.py``
from pinned sources) runs here under ``wasmtime``, in-process: WebAssembly's
memory safety is the boundary, so no subprocess or bubblewrap is needed.

**Sealed.** The module's only imports are the five WASI functions wasi-libc
links (``clock_time_get``, ``fd_close``, ``fd_fdstat_get``, ``fd_seek``,
``fd_write``); each is answered by a deny-all shim (no clock, no files, no
randomness, no environment, no network; ``fd_write`` keeps at most
:data:`STDERR_KEEP` bytes of error text and nothing else). A module that asks
for anything else is refused before it is instantiated.

**Pinned.** The artifact's SHA-256 must equal :data:`ENGINE_SHA256` (the
digest ``engine.lock.json`` records); a mismatch refuses to load
(:class:`EngineUnavailable`), it never runs a different engine.

**Caps (keep: machine safety, never model parameters).** Inside the engine,
each entry-point call has the same deterministic work budget (QuickJS
interrupt ticks, :data:`SKETCH_FUEL_PER_CALL`) and the runtime a memory cap
(:data:`SKETCH_MEMORY_BYTES`); both are compiled into the engine, so the
desktop runs under the same caps. Here, wasmtime adds backstops for what the
interpreter cannot interrupt (a native loop such as a huge BigInt power):
fuel per call (:data:`WASM_FUEL_PER_CALL`), a store memory limit
(:data:`WASM_MEMORY_BYTES`) and an epoch deadline (:data:`CALL_SECONDS`).
"""

from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

#: The tracked artifact (G8 allows it as an application asset).
ENGINE_PATH = (Path(__file__).resolve().parents[3] / "apps" / "learnloop-tauri" / "src" / "screens" / "reader"
               / "figures" / "sketch" / "sketch-engine.wasm")
LOCK_PATH = Path(__file__).resolve().parents[3] / "apps" / "learnloop-tauri" / "sketch-engine" / "engine.lock.json"
#: The pinned digest of the artifact (``engine.lock.json``'s ``output.sha256``;
#: a test keeps the two equal). A stored sketch records the digest it was
#: verified under; a different one re-verifies it (spec §8.5).
ENGINE_SHA256 = "f6bb52fdad6fda05ecd929330a979a2a900287026689bf710abb31768e583e23"
#: The runtime version a figure records beside the digest.
ENGINE_VERSION = "sketch-engine-v1"

#: keep (machine safety): the engine's memory cap, compiled in (sk_limits).
SKETCH_MEMORY_BYTES = 64 * 1024 * 1024
#: keep (deterministic work cap): interrupt ticks per entry-point call, each
#: tick QuickJS's 10,000 interrupt polls (function calls and loop back-edges);
#: compiled in. Measured on carson (review file): one call at the cap takes
#: about one frame (``SKETCH_FRAME_MS``) in the desktop's engine.
SKETCH_FUEL_PER_CALL = 48
#: keep (machine safety): wasmtime's backstops, above anything the interrupt
#: budget allows, for native work the interpreter cannot interrupt.
WASM_MEMORY_BYTES = 96 * 1024 * 1024
WASM_FUEL_PER_CALL = 4_000_000_000
CALL_SECONDS = 10.0
#: keep: wasm stack for the interpreter's own recursion (the engine's JS
#: recursion guard fires well before it).
WASM_STACK_BYTES = 1536 * 1024
#: keep: error text kept from fd_write.
STDERR_KEEP = 4096

#: The engine's statuses (sketch_engine.c).
OK, ERROR, WORK, MEMORY, STACK, NOPROGRAM, OUTPUT, INPUT = range(8)
STATUS_NAMES = {OK: "ok", ERROR: "error", WORK: "work_cap", MEMORY: "memory_cap", STACK: "stack",
                NOPROGRAM: "no_program", OUTPUT: "output", INPUT: "input"}
#: What the module may import, and nothing more.
ALLOWED_IMPORTS = frozenset({("wasi_snapshot_preview1", name) for name in
                             ("clock_time_get", "fd_close", "fd_fdstat_get", "fd_seek", "fd_write")})
#: WASI errno values the shim answers with.
_EBADF = 8
_ENOSYS = 52


class EngineUnavailable(RuntimeError):
    """The engine artifact is missing, has the wrong digest or imports more
    than the deny-all shim answers."""


class SketchRunError(RuntimeError):
    """A call into the program failed: ``status`` (:data:`STATUS_NAMES`) and the
    engine's message (code-written, quoting the program's own error)."""

    def __init__(self, status: int, message: str, *, trap: bool = False) -> None:
        super().__init__(message)
        self.status = status
        self.kind = STATUS_NAMES.get(status, "error")
        self.message = message
        self.trap = trap


@dataclass(frozen=True)
class EngineInfo:
    sha256: str
    path: Path


def artifact_digest(path: Path = ENGINE_PATH) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=4)
def _compiled(path_text: str, expected: str) -> tuple[Any, Any, str]:
    import wasmtime

    path = Path(path_text)
    if not path.is_file():
        raise EngineUnavailable(f"the sketch engine is missing ({path.name}); run apps/learnloop-tauri/sketch-engine/build.py")
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise EngineUnavailable(f"the sketch engine's digest {digest[:12]} is not the pinned {expected[:12]}; "
                                "it is not run")
    config = wasmtime.Config()
    config.consume_fuel = True
    config.epoch_interruption = True
    config.max_wasm_stack = WASM_STACK_BYTES
    config.cranelift_nan_canonicalization = True
    engine = wasmtime.Engine(config)
    module = wasmtime.Module(engine, data)
    imports = {(item.module, item.name) for item in module.imports}
    extra = sorted(imports - ALLOWED_IMPORTS)
    if extra:
        raise EngineUnavailable(f"the sketch engine imports {extra}, which the sandbox does not answer")
    return engine, module, digest


def engine_info(*, path: Path = ENGINE_PATH, expected: str = ENGINE_SHA256) -> EngineInfo:
    _compiled(str(path), expected)
    return EngineInfo(sha256=expected, path=path)


def engine_ready(*, path: Path = ENGINE_PATH, expected: str = ENGINE_SHA256) -> bool:
    try:
        engine_info(path=path, expected=expected)
    except EngineUnavailable:
        return False
    except Exception:  # noqa: BLE001 - wasmtime missing or broken: the tier is unavailable, honestly
        return False
    return True


class SketchEngine:
    """One sealed engine instance (one program at a time). Not thread-safe:
    one per verification or prediction; :meth:`close` (or ``with``) frees it."""

    def __init__(self, *, path: Path = ENGINE_PATH, expected: str = ENGINE_SHA256) -> None:
        import wasmtime

        self._wasmtime = wasmtime
        engine, module, digest = _compiled(str(path), expected)
        self.engine = engine
        self.digest = digest
        self.stderr = bytearray()
        self.store = wasmtime.Store(engine)
        self.store.set_limits(memory_size=WASM_MEMORY_BYTES, instances=1, tables=2, memories=1)
        self.store.set_fuel(WASM_FUEL_PER_CALL)
        self.store.set_epoch_deadline(1)
        linker = wasmtime.Linker(engine)
        self._define_shim(linker)
        self.instance = linker.instantiate(self.store, module)
        exports = self.instance.exports(self.store)
        self.memory = exports["memory"]
        self._fn = {name: exports[name] for name in ("sk_buffer", "sk_output_ptr", "sk_output_len", "sk_limits",
                                                     "sk_load", "sk_init", "sk_step", "sk_view", "sk_probes",
                                                     "sk_unload")}
        self.broken = False
        self._call("initialize", exports["_initialize"])
        self.entry_points: dict[str, bool] = {}

    # -- the deny-all WASI shim --------------------------------------------

    def _define_shim(self, linker: Any) -> None:
        wasmtime = self._wasmtime
        i32, i64 = wasmtime.ValType.i32(), wasmtime.ValType.i64()
        module = "wasi_snapshot_preview1"

        def deny(*_args: Any) -> int:
            return _EBADF

        def no_clock(*_args: Any) -> int:
            return _ENOSYS

        def fd_write(caller: Any, fd: int, iovs: int, count: int, written: int) -> int:
            memory = caller["memory"]
            total = 0
            for index in range(max(0, min(int(count), 64))):
                base = iovs + 8 * index
                pointer = int.from_bytes(memory.read(caller, base, base + 4), "little")
                length = int.from_bytes(memory.read(caller, base + 4, base + 8), "little")
                room = STDERR_KEEP - len(self.stderr)
                if room > 0 and length > 0:
                    self.stderr += memory.read(caller, pointer, pointer + min(length, room))
                total += length
            memory.write(caller, int(total & 0xFFFFFFFF).to_bytes(4, "little"), written)
            return 0

        linker.define_func(module, "clock_time_get", wasmtime.FuncType([i32, i64, i32], [i32]), no_clock)
        linker.define_func(module, "fd_close", wasmtime.FuncType([i32], [i32]), deny)
        linker.define_func(module, "fd_fdstat_get", wasmtime.FuncType([i32, i32], [i32]), deny)
        linker.define_func(module, "fd_seek", wasmtime.FuncType([i32, i64, i32, i32], [i32]), deny)
        linker.define_func(module, "fd_write", wasmtime.FuncType([i32, i32, i32, i32], [i32]), fd_write,
                           access_caller=True)

    # -- calls -------------------------------------------------------------

    def _call(self, name: str, function: Any, *args: int) -> Any:
        """One call with fresh backstops: fuel, and an epoch deadline a
        timer thread trips after :data:`CALL_SECONDS` (joined before return)."""

        wasmtime = self._wasmtime
        if self.broken:
            # A trap can stop the interpreter mid-update: the instance is
            # never called again (a new one is cheap).
            raise SketchRunError(ERROR, "the engine was stopped earlier; a new one is needed", trap=True)
        self.store.set_fuel(WASM_FUEL_PER_CALL)
        self.store.set_epoch_deadline(1)
        timer = threading.Timer(CALL_SECONDS, self.engine.increment_epoch)
        timer.daemon = True
        timer.start()
        try:
            return function(self.store, *args)
        except wasmtime.Trap as exc:
            self.broken = True
            raise SketchRunError(WORK if _is_exhaustion(exc) else ERROR,
                                 f"{_label(name)}: the engine stopped it ({_trap_reason(exc)})", trap=True) from exc
        except wasmtime.WasmtimeError as exc:
            self.broken = True
            raise SketchRunError(ERROR, f"{_label(name)}: the engine stopped it", trap=True) from exc
        finally:
            timer.cancel()
            timer.join()

    def _write(self, data: bytes) -> int:
        pointer = self._call("buffer", self._fn["sk_buffer"], len(data))
        if not pointer:
            raise SketchRunError(MEMORY, "the engine could not take the input")
        self.memory.write(self.store, data, pointer)
        return len(data)

    def _output(self) -> str:
        pointer = self._fn["sk_output_ptr"](self.store)
        length = self._fn["sk_output_len"](self.store)
        return bytes(self.memory.read(self.store, pointer, pointer + length)).decode("utf-8", errors="replace")

    def _run(self, name: str, *args: int) -> str:
        status = self._call(name, self._fn[name], *args)
        text = self._output()
        if status != OK:
            raise SketchRunError(int(status), text or STATUS_NAMES.get(int(status), "error"))
        return text

    def limits(self) -> dict[str, Any]:
        return json.loads(self._run("sk_limits"))

    def load(self, code: str) -> dict[str, bool]:
        length = self._write(code.encode("utf-8"))
        self.entry_points = json.loads(self._run("sk_load", length) or "{}")
        return self.entry_points

    def init(self, params: Mapping[str, float], seed: int) -> None:
        length = self._write(_json(params))
        self._run("sk_init", length, int(seed) & 0xFFFFFFFF)

    def step(self, params: Mapping[str, float], dt: float, *, index: int, count: int = 1) -> None:
        length = self._write(_json({"p": dict(params), "dt": float(dt)}))
        self._run("sk_step", length, int(index), int(count))

    def view(self, params: Mapping[str, float], *, index: int) -> Any:
        length = self._write(_json(params))
        return json.loads(self._run("sk_view", length, int(index)))

    def probes(self, params: Mapping[str, float], *, index: int) -> Any:
        length = self._write(_json(params))
        return json.loads(self._run("sk_probes", length, int(index)))

    def view_text(self, params: Mapping[str, float], *, index: int) -> str:
        """The scene exactly as the engine wrote it (the parity corpus compares text)."""

        length = self._write(_json(params))
        return self._run("sk_view", length, int(index))

    def probes_text(self, params: Mapping[str, float], *, index: int) -> str:
        length = self._write(_json(params))
        return self._run("sk_probes", length, int(index))

    def close(self) -> None:
        try:
            self._fn["sk_unload"](self.store)
        except Exception:  # noqa: BLE001 - closing never raises
            pass
        self.store.close()

    def __enter__(self) -> "SketchEngine":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()


def _label(name: str) -> str:
    return name.removeprefix("sk_")


def _json(value: Any) -> bytes:
    return json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _is_exhaustion(exc: Exception) -> bool:
    text = str(exc).lower()
    return "fuel" in text or "interrupt" in text or "epoch" in text


def _trap_reason(exc: Exception) -> str:
    text = str(exc).lower()
    if "fuel" in text or "epoch" in text or "interrupt" in text:
        return "it ran too long"
    if "stack" in text:
        return "recursion too deep"
    if "memory" in text or "out of bounds" in text:
        return "out of memory"
    return "a fault"


__all__ = [
    "ALLOWED_IMPORTS",
    "CALL_SECONDS",
    "ENGINE_PATH",
    "ENGINE_SHA256",
    "ENGINE_VERSION",
    "EngineInfo",
    "EngineUnavailable",
    "SKETCH_FUEL_PER_CALL",
    "SKETCH_MEMORY_BYTES",
    "STATUS_NAMES",
    "SketchEngine",
    "SketchRunError",
    "WASM_FUEL_PER_CALL",
    "WASM_MEMORY_BYTES",
    "artifact_digest",
    "engine_info",
    "engine_ready",
]
