"""The query process: the adopted student, serving query vectors over a Unix socket (spec_local_contextual_retrieval_v1 §7.1 "Serving", §7.2; P2).

Started lazily by the app on the first local query (``source_retrieval.student_encoder``), in
its own ``systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0`` with the SEPARATE
environment's interpreter::

    <env>/bin/python -I student_server.py --job JOB.json

* **No network.** Every inet connection is refused (the worker's guard); the only socket is a
  Unix socket in ``$XDG_RUNTIME_DIR`` (mode 0600), JSON lines in and out.
* **Start checks (keep, §9.6).** Inside a scope whose ``memory.max`` is at most 4 GiB with
  swap 0; host MemAvailable at least 6 GiB. **Device:** the GPU when at least 4 GiB of VRAM is
  free and no exclusive GPU job holds the lock (it never takes the lock itself; it is counted
  by the big jobs' VRAM checks), else the CPU. BF16 on either.
* **Health.** The checkpoint's files are checked against their SHA-256 pins and the
  checkpoint's own digest before anything loads; the canary queries are encoded at start and
  must match the checkpoint's stored vectors for this device class (cos >= 0.999, an identity
  check), else the process exits ``canary_failed`` and the app reports the student unavailable.
* **Idle exit** after ``idle_minutes`` without a request, or at once when host MemAvailable falls
  below the 9B worker's runtime floor.

The status file (``ready``, the device, the pid, the measured start) is written atomically next
to the socket; the app reads it to know the process is up and to measure cold starts.

This module imports only the standard library and numpy at load time; torch and transformers
load inside :func:`load_service`. The tests drive :func:`serve_forever` with a numpy service.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import time
from typing import Any

import numpy as np

SERVER_VERSION = "query-student-server-v1"


def _worker() -> Any:
    try:
        from learnloop.local_embeddings import worker  # noqa: PLC0415 - optional package import
        return worker
    except ImportError:
        if "learnloop_local_worker" in sys.modules:
            return sys.modules["learnloop_local_worker"]
        path = Path(__file__).resolve().with_name("worker.py")
        spec = importlib.util.spec_from_file_location("learnloop_local_worker", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


W = _worker()


def _trainer() -> Any:
    try:
        from learnloop.local_embeddings import student_trainer  # noqa: PLC0415
        return student_trainer
    except ImportError:
        path = Path(__file__).resolve().with_name("student_trainer.py")
        spec = importlib.util.spec_from_file_location("learnloop_student_trainer", path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def gpu_lock_free(path: Path) -> bool:
    """Whether no exclusive GPU job holds the lock now (probed, never held)."""

    try:
        with open(path, "a+") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return True
    except OSError:
        return False


def choose_device(job: Mapping[str, Any], *, gpu: Callable[[], Mapping[str, Any] | None] = W.gpu_state,
                  lock_free: Callable[[Path], bool] = gpu_lock_free) -> tuple[str, str]:
    """``(device, why)``: the GPU when >= the VRAM floor is free and the GPU lock is free, else the CPU."""

    if job.get("device") == "cpu":
        return "cpu", "forced"
    try:
        state = gpu()
    except Exception:  # noqa: BLE001 - no GPU state is a CPU start
        state = None
    if state is None:
        return "cpu", "no GPU state"
    floor = float(job["limits"]["min_free_vram_gib"])
    if state["free_mib"] * W.MIB < floor * W.GIB:
        return "cpu", f"free VRAM {state['free_mib'] / 1024:.1f} GiB is below {floor} GiB"
    if not lock_free(Path(job["gpu_lock"])):
        return "cpu", "an exclusive GPU job holds the lock"
    return "cuda:0", "ok"


def start_problems(job: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any]) -> list[str]:
    limits = job["limits"]
    problems = []
    if not scope.get("scope"):
        problems.append("not inside a systemd scope (run through systemd-run --user --scope)")
    limit = scope.get("memory_max")
    if limit is None or limit > int(limits["memory_max_bytes"]):
        problems.append("the scope's memory.max is unset or above the plan's 4 GiB")
    swap = scope.get("swap_max")
    if swap is None or swap > int(limits["swap_max_bytes"]):
        problems.append("the scope's memory.swap.max is unset or above the plan's")
    available = int(meminfo.get("MemAvailable", 0))
    if available < float(limits["min_host_available_gib"]) * W.GIB:
        problems.append(f"host MemAvailable {available / W.GIB:.1f} GiB is below {limits['min_host_available_gib']} GiB")
    return problems


def checkpoint_problems(job: Mapping[str, Any]) -> list[str]:
    """The checkpoint's files against their SHA-256 pins and its own digest."""

    trainer = _trainer()
    directory = Path(job["checkpoint_dir"])
    try:
        manifest = json.loads((directory / "student.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ["the checkpoint manifest cannot be read"]
    problems = [f"{name}: SHA-256 differs from the checkpoint's pin" for name, digest in
                sorted((manifest.get("files") or {}).items())
                if not (directory / name).is_file() or trainer.sha256_file(directory / name) != digest]
    if trainer.checkpoint_digest(manifest) != job["checkpoint_sha256"]:
        problems.append("the checkpoint's digest is not the adopted one")
    return problems


def _cos(a: Sequence[float], b: Sequence[float]) -> float:
    x, y = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    return float(x @ y / denominator) if denominator else 0.0


def canary_check(service: Any, job: Mapping[str, Any], device_class: str) -> dict[str, Any]:
    manifest = json.loads((Path(job["checkpoint_dir"]) / "student.json").read_text(encoding="utf-8"))
    stored = (manifest.get("canaries") or {}).get(device_class)
    if not stored:
        return {"ok": False, "reason": f"the checkpoint has no {device_class} canaries"}
    fresh = service.encode(list(job["canary_queries"]))
    lowest = min(_cos(a, b) for a, b in zip(fresh, stored, strict=True))
    tolerance = float(job["canary_min_cos"])
    return {"ok": lowest >= tolerance, "min_cos": round(lowest, 6), "tolerance": tolerance}


class TorchService:
    """The checkpoint on its device, BF16, FP32 normalized output."""

    def __init__(self, job: Mapping[str, Any], device: str) -> None:
        import torch
        from safetensors.torch import load_file

        trainer = _trainer()
        manifest = json.loads((Path(job["checkpoint_dir"]) / "student.json").read_text(encoding="utf-8"))
        base = job["base"]
        model, self.tokenizer = trainer.load_base(Path(job["base_dir"]), base, device="cpu")
        self.student = trainer.build_student(model, hidden=int(base["hidden_size"]), dims=int(manifest["dims"]),
                                             pooling=str(base["pooling"]), frozen_base=True)
        state = load_file(str(Path(job["checkpoint_dir"]) / "student.safetensors"))
        self.student.head.load_state_dict({key[5:]: value for key, value in state.items() if key.startswith("head.")})
        if not manifest.get("frozen_base"):
            self.student.base.load_state_dict({key[5:]: value for key, value in state.items()
                                               if key.startswith("base.")})
        self.student = self.student.to(torch.bfloat16).to(device).eval()
        self.device = device
        self.prefix = str(base.get("query_prefix") or "")
        self.max_tokens = int(manifest["max_query_tokens"])
        self.trainer = trainer

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        return self.trainer.encode(self.student, self.tokenizer, list(texts), prefix=self.prefix,
                                   max_tokens=self.max_tokens, device=self.device, batch_size=8).tolist()


def load_service(job: Mapping[str, Any], device: str) -> Any:
    return TorchService(job, device)


def serve_forever(service: Any, socket_path: Path, *, idle_s: float, timeout_s: float,
                  meminfo: Callable[[], Mapping[str, int]] = W.read_meminfo, floor_gib: float = 3.0,
                  clock: Callable[[], float] = time.monotonic, ready: Callable[[], None] | None = None) -> str:
    """Answer JSON-line requests until idle, a shutdown request or the host floor; returns why it stopped."""

    socket_path = Path(socket_path)
    socket_path.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        server.bind(str(socket_path))
        os.chmod(socket_path, 0o600)
        server.listen(4)
        server.settimeout(min(timeout_s, max(idle_s, 0.05)))
        if ready is not None:
            ready()
        last = clock()
        while True:
            if clock() - last >= idle_s:
                return "idle"
            if int(meminfo().get("MemAvailable", 1 << 62)) < floor_gib * W.GIB:
                return "host_floor"
            try:
                connection, _address = server.accept()
            except TimeoutError:
                continue
            last = clock()
            with connection:
                connection.settimeout(timeout_s)
                reply, stop = _answer(service, _read_line(connection))
                connection.sendall((json.dumps(reply) + "\n").encode("utf-8"))
            if stop:
                return "shutdown"
    finally:
        server.close()
        socket_path.unlink(missing_ok=True)


def _read_line(connection: socket.socket) -> bytes:
    chunks = []
    while True:
        chunk = connection.recv(65536)
        if not chunk:
            break
        chunks.append(chunk)
        if chunk.endswith(b"\n"):
            break
    return b"".join(chunks)


def _answer(service: Any, raw: bytes) -> tuple[dict[str, Any], bool]:
    try:
        request = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, ValueError):
        return {"ok": False, "error": "bad_request"}, False
    operation = request.get("op")
    if operation == "health":
        return {"ok": True, "version": SERVER_VERSION}, False
    if operation == "shutdown":
        return {"ok": True}, True
    if operation == "encode" and isinstance(request.get("texts"), list):
        started = time.monotonic()
        try:
            vectors = service.encode([str(text) for text in request["texts"]])
        except Exception as exc:  # noqa: BLE001 - a failed encode is a reply, never a crash
            return {"ok": False, "error": type(exc).__name__}, False
        return {"ok": True, "vectors": vectors, "latency_s": round(time.monotonic() - started, 5)}, False
    return {"ok": False, "error": "unknown_op"}, False


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LearnLoop query student (Unix socket, idle exit)")
    parser.add_argument("--job", type=Path, required=True)
    args = parser.parse_args(argv)
    job = json.loads(args.job.read_text(encoding="utf-8"))
    status_path = Path(job["status_path"])
    started_wall, started = time.time(), time.monotonic()
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                       "HF_HOME": str(args.job.parent / "hf_home"), "HF_MODULES_CACHE": str(args.job.parent / "hf_modules"),
                       "TOKENIZERS_PARALLELISM": "false"})
    W._guard_network()

    def status(value: Mapping[str, Any]) -> None:
        W._atomic_json(status_path, {"version": SERVER_VERSION, "pid": os.getpid(), "started_unix": started_wall,
                                     "checkpoint_sha256": job["checkpoint_sha256"], **value})

    problems = start_problems(job, meminfo=W.read_meminfo(), scope=W.scope_limits()) + checkpoint_problems(job)
    if problems:
        status({"status": "refused", "reason": "; ".join(problems)})
        return 3
    device, why = choose_device(job)
    try:
        service = load_service(job, device)
        check = canary_check(service, job, "cpu" if device == "cpu" else "gpu")
    except Exception as exc:  # noqa: BLE001 - recorded, the app reports the student unavailable
        status({"status": "failed", "reason": f"{type(exc).__name__}: {str(exc)[:300]}", "device": device})
        return 3
    if not check["ok"]:
        status({"status": "canary_failed", "canary": check, "device": device})
        return 3

    def ready() -> None:
        status({"status": "ready", "device": "cpu" if device == "cpu" else "gpu", "device_reason": why,
                "socket": job["socket_path"], "start_s": round(time.monotonic() - started, 3), "canary": check})

    reason = serve_forever(service, Path(job["socket_path"]), idle_s=float(job["idle_minutes"]) * 60.0,
                           timeout_s=float(job["socket_timeout_s"]), floor_gib=float(job["limits"]["host_floor_gib"]),
                           ready=ready)
    status({"status": "exited", "reason": reason})
    return 0


if __name__ == "__main__":
    sys.exit(main())
