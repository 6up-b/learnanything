"""The E1 local worker: one batch process that loads pplx v2 BF16, runs the
smoke checks, profiles, encodes every document and query, unloads and exits.

Run ONLY by ``e1.local.launch`` inside its own ``systemd-run --user --scope``
with ``MemoryMax``, with the SEPARATE environment's interpreter (spec §6: the
app pins transformers 4.57.6, the model needs >= 5.4)::

    <env>/bin/python -I worker.py --job JOB.json --out OUT.json --heartbeat HB.json

This module imports only the standard library and numpy at load time (the
app imports its probes and checks; the tests drive ``run_job`` with a fake
model). torch and transformers are imported inside ``load_model`` only.

What it guarantees (spec §8, D2):

* **Refuses to start** unless it runs inside a systemd scope whose
  ``memory.max`` is set and within the plan's, measured host MemAvailable and
  free VRAM meet the plan's thresholds, and no other substantial GPU process
  or utilization is present.
* **No network.** Offline Hugging Face flags, an empty private HF home and
  modules cache, and a socket guard that refuses every inet connection.
* **Reviewed code only.** The two remote-code files are hashed against the
  pins before ``trust_remote_code`` imports them; every file's size is checked.
* **BF16, shards straight to the GPU** (``dtype=bfloat16``,
  ``device_map={"": 0}``): the FP32 checkpoint is never materialized in host
  RAM; the projection stays fp32 (checked).
* **Bounded.** A sampler records host, scope and device peaks every second,
  writes a heartbeat, aborts below the host floor, above the device peak
  target or past the GPU-hours deadline (partial results are written, then
  the process exits). Larger profiling sizes stop after a failure (OOMs count).
* **No residency.** After the queries it unloads, records whether the device
  memory was released, and exits.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import gc
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Protocol

import numpy as np

WORKER_VERSION = "e1-worker-v1"
GIB = 1024 ** 3
MIB = 1024 ** 2


class Refused(RuntimeError):
    """A start condition failed: nothing was loaded."""


class WorkerOOM(RuntimeError):
    """The device ran out of memory (counted, never retried at a larger size)."""


class Aborted(RuntimeError):
    """The sampler stopped the run (host floor, device target, deadline)."""


# -- probes (stdlib; injectable) ---------------------------------------------------------
def read_meminfo(text: str | None = None) -> dict[str, int]:
    """``/proc/meminfo`` in bytes (MemTotal, MemAvailable, SwapTotal, SwapFree)."""

    if text is None:
        text = Path("/proc/meminfo").read_text(encoding="ascii")
    values = {}
    for line in text.splitlines():
        name, _sep, rest = line.partition(":")
        parts = rest.split()
        if parts and parts[0].isdigit():
            values[name.strip()] = int(parts[0]) * (1024 if len(parts) > 1 and parts[1] == "kB" else 1)
    return values


def own_cgroup(text: str | None = None) -> str | None:
    """This process's cgroup v2 path (``0::/...``), or None."""

    if text is None:
        try:
            text = Path("/proc/self/cgroup").read_text(encoding="ascii")
        except OSError:
            return None
    for line in text.splitlines():
        if line.startswith("0::"):
            return line[3:].strip()
    return None


def cgroup_value(path: str, name: str, *, root: Path = Path("/sys/fs/cgroup")) -> str | None:
    try:
        return (root / path.lstrip("/") / name).read_text(encoding="ascii").strip()
    except OSError:
        return None


def scope_limits(*, cgroup_text: str | None = None, root: Path = Path("/sys/fs/cgroup")) -> dict[str, Any]:
    """The worker's scope: its cgroup path, ``memory.max`` and ``memory.swap.max``
    (None when unlimited or unreadable) and the current/peak usage."""

    path = own_cgroup(cgroup_text)
    if path is None:
        return {"cgroup": None, "scope": False, "memory_max": None, "swap_max": None}

    def number(name: str) -> int | None:
        value = cgroup_value(path, name, root=root)
        return int(value) if value is not None and value.isdigit() else None

    return {"cgroup": path, "scope": path.endswith(".scope"), "memory_max": number("memory.max"),
            "swap_max": number("memory.swap.max"), "memory_current": number("memory.current"),
            "memory_peak": number("memory.peak")}


def run_nvidia_smi(arguments: Sequence[str]) -> str:
    return subprocess.run(["nvidia-smi", *arguments], capture_output=True, text=True, check=True,
                          timeout=20).stdout


def gpu_state(run: Callable[[Sequence[str]], str] = run_nvidia_smi) -> dict[str, Any]:
    """Device 0's memory and utilization and every compute process, from nvidia-smi."""

    line = run(["--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu",
                "--format=csv,noheader,nounits", "--id=0"]).strip().splitlines()[0]
    name, driver, total, used, free, utilization = [part.strip() for part in line.split(",")]
    processes = []
    for row in run(["--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits",
                    "--id=0"]).strip().splitlines():
        if row.strip():
            pid, memory = [part.strip() for part in row.split(",")[:2]]
            processes.append({"pid": int(pid), "used_mib": int(memory) if memory.isdigit() else None})
    return {"name": name, "driver": driver, "total_mib": int(total), "used_mib": int(used), "free_mib": int(free),
            "utilization_pct": int(utilization) if utilization.isdigit() else None, "processes": processes}


def disk_free_bytes(path: Path) -> int:
    stats = os.statvfs(path)
    return stats.f_bavail * stats.f_frsize


def start_problems(limits: Mapping[str, Any], *, meminfo: Mapping[str, int], scope: Mapping[str, Any],
                   gpu: Mapping[str, Any] | None, own_pids: Sequence[int] = (), require_scope: bool = True) -> list[str]:
    """Why this process must not start (empty: it may). Shared by the
    orchestrator's preflight (``require_scope=False``: it is not the scope)
    and the worker itself (``require_scope=True``)."""

    problems = []
    if require_scope:
        if not scope.get("scope"):
            problems.append("not inside a systemd scope (run through systemd-run --user --scope)")
        limit = scope.get("memory_max")
        if limit is None:
            problems.append("the scope has no memory.max")
        elif limit > int(limits["memory_max_bytes"]):
            problems.append(f"the scope's memory.max {limit} exceeds the plan's {limits['memory_max_bytes']}")
        swap = scope.get("swap_max")
        if swap is None or swap > int(limits["swap_max_bytes"]):
            problems.append("the scope's memory.swap.max is unset or above the plan's")
    available = int(meminfo.get("MemAvailable", 0))
    if available < float(limits["min_host_available_gib"]) * GIB:
        problems.append(f"host MemAvailable {available / GIB:.1f} GiB is below {limits['min_host_available_gib']} GiB")
    if gpu is None:
        problems.append("no GPU state (nvidia-smi failed)")
    else:
        if gpu["free_mib"] * MIB < float(limits["min_free_vram_gib"]) * GIB:
            problems.append(f"free VRAM {gpu['free_mib'] / 1024:.1f} GiB is below {limits['min_free_vram_gib']} GiB")
        others = [item for item in gpu.get("processes") or [] if item["pid"] not in set(own_pids)
                  and (item.get("used_mib") or 0) > int(limits["max_other_gpu_process_mib"])]
        if others:
            problems.append(f"{len(others)} other GPU compute process(es) above "
                            f"{limits['max_other_gpu_process_mib']} MiB (no concurrent GLM-OCR or GPU workload)")
        utilization = gpu.get("utilization_pct")
        if utilization is not None and utilization > int(limits["max_gpu_utilization_pct"]):
            problems.append(f"GPU utilization {utilization}% is above {limits['max_gpu_utilization_pct']}%")
    deadline = limits.get("deadline_unix")
    if deadline is not None and time.time() >= float(deadline):
        problems.append("the GPU-hours allowance is spent")
    return problems


# -- the reviewed model files ------------------------------------------------------------
def sha256_file(path: Path, *, chunk: int = 16 * MIB) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while block := handle.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def model_dir_problems(model_dir: Path, files: Mapping[str, Sequence[Any]], remote_code: Sequence[str], *,
                       verify_digests: bool = False) -> list[str]:
    """Missing or wrong files: every size always, the remote code's digest
    always, every digest when ``verify_digests``."""

    problems = []
    for name, (size, digest) in sorted(files.items()):
        path = Path(model_dir) / name
        if not path.is_file():
            problems.append(f"{name}: missing")
            continue
        if path.stat().st_size != int(size):
            problems.append(f"{name}: size {path.stat().st_size} is not the pinned {size}")
            continue
        if (verify_digests or name in remote_code or path.stat().st_size < 64 * MIB) and sha256_file(path) != digest:
            problems.append(f"{name}: SHA-256 differs from the pinned digest")
    unexpected = sorted(path.name for path in Path(model_dir).glob("*.py") if path.name not in remote_code)
    if unexpected:
        problems.append("unreviewed Python files in the model directory: " + ", ".join(unexpected))
    return problems


# -- the model interface (the real wrapper below; tests pass a fake) -----------------------
class LoadedModel(Protocol):
    info: dict[str, Any]

    def count_tokens(self, chunks: Sequence[str], *, task: str = "document") -> int: ...
    def encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int = 1) -> list[np.ndarray]: ...
    def encode_queries(self, queries: Sequence[str], *, batch_size: int = 1) -> list[np.ndarray]: ...
    def device_memory(self) -> dict[str, int | None]: ...
    def reset_peak(self) -> None: ...
    def unload(self) -> dict[str, Any]: ...


KERNEL_HINTS = ("fast path", "flash-linear-attention", "flash_linear_attention", "causal-conv1d", "causal_conv1d",
                "fla ", "kernel", "falling back", "fallback")


class TransformersModel:
    """pplx v2 through its own reviewed ``encode``/``encode_queries`` (never a
    reimplementation), loaded BF16 with shards straight onto device 0."""

    def __init__(self, model_dir: Path, *, precision: str, attention: str, fp32_modules: Sequence[str]) -> None:
        import logging
        import warnings

        import torch
        import transformers
        from transformers import AutoModel

        if precision != "bf16":
            raise Refused(f"precision {precision!r} is not in this plan (BF16 first; FP8 needs a new plan)")
        self.torch = torch
        captured: list[str] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured.append(record.getMessage())

        handler = _Capture(level=logging.WARNING)
        library = logging.getLogger("transformers")
        library.addHandler(handler)
        started = time.monotonic()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                self.model = AutoModel.from_pretrained(
                    str(model_dir), trust_remote_code=True, local_files_only=True, dtype=torch.bfloat16,
                    device_map={"": 0}, attn_implementation=attention)
                self.model.eval()
                # One tiny forward so lazily chosen kernels report themselves.
                self.model.encode([["warm up"]], batch_size=1)
                torch.cuda.synchronize()
        finally:
            library.removeHandler(handler)
        messages = [*captured, *(str(item.message) for item in caught)]
        dtypes: dict[str, int] = {}
        for parameter in self.model.parameters():
            key = str(parameter.dtype).removeprefix("torch.")
            dtypes[key] = dtypes.get(key, 0) + parameter.numel()
        fp32_ok = {name: str(getattr(self.model, name).weight.dtype) == "torch.float32" for name in fp32_modules}
        self.info = {
            "load_s": round(time.monotonic() - started, 3), "parameter_dtypes": dtypes, "fp32_modules": fp32_ok,
            "attention": attention, "precision": precision,
            "kernel_messages": sorted({message[:200] for message in messages
                                       if any(hint in message.lower() for hint in KERNEL_HINTS)}),
            "torch": torch.__version__, "transformers": transformers.__version__,
            "cuda": torch.version.cuda, "device": torch.cuda.get_device_name(0),
            "capability": list(torch.cuda.get_device_capability(0)),
        }
        if not all(fp32_ok.values()):
            raise Refused("a module that must stay fp32 did not (" + ", ".join(
                name for name, ok in fp32_ok.items() if not ok) + ")")

    def _oom(self) -> type[BaseException]:
        return self.torch.cuda.OutOfMemoryError

    def count_tokens(self, chunks: Sequence[str], *, task: str = "document") -> int:
        rows = [[chunks[0]]] if task == "query" else [list(chunks)]
        return int(self.model.prepare_inputs(rows, task)["input_ids"].shape[1])

    def encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int = 1) -> list[np.ndarray]:
        try:
            rows = self.model.encode([list(chunks) for chunks in documents], batch_size=batch_size,
                                     normalize_embeddings=False)
            self.torch.cuda.synchronize()
        except self._oom() as exc:
            self.torch.cuda.empty_cache()
            raise WorkerOOM("device out of memory while encoding documents") from exc
        return [np.asarray(row, dtype=np.float32) for row in rows]

    def encode_queries(self, queries: Sequence[str], *, batch_size: int = 1) -> list[np.ndarray]:
        try:
            rows = self.model.encode_queries([[query] for query in queries], batch_size=batch_size,
                                             normalize_embeddings=False)
            self.torch.cuda.synchronize()
        except self._oom() as exc:
            self.torch.cuda.empty_cache()
            raise WorkerOOM("device out of memory while encoding queries") from exc
        return [np.asarray(row, dtype=np.float32) for row in rows]

    def device_memory(self) -> dict[str, int | None]:
        cuda = self.torch.cuda
        free, total = cuda.mem_get_info(0)
        return {"allocated": cuda.memory_allocated(0), "reserved": cuda.memory_reserved(0),
                "max_allocated": cuda.max_memory_allocated(0), "max_reserved": cuda.max_memory_reserved(0),
                "free": free, "total": total}

    def reset_peak(self) -> None:
        self.torch.cuda.reset_peak_memory_stats(0)

    def unload(self) -> dict[str, Any]:
        cuda = self.torch.cuda
        del self.model
        gc.collect()
        cuda.synchronize()
        cuda.empty_cache()
        allocated, reserved = cuda.memory_allocated(0), cuda.memory_reserved(0)
        return {"allocated_after": allocated, "reserved_after": reserved, "complete": allocated == 0}


def load_model(model_dir: Path, job: Mapping[str, Any]) -> LoadedModel:
    return TransformersModel(Path(model_dir), precision=job["precision"], attention=job["attention"],
                             fp32_modules=job["fp32_modules"])


# -- the run ---------------------------------------------------------------------------------
class Sampler(threading.Thread):
    """Peaks every interval, a heartbeat file, and the abort conditions."""

    def __init__(self, limits: Mapping[str, Any], *, heartbeat: Path | None, meminfo: Callable[[], Mapping[str, int]],
                 scope: Callable[[], Mapping[str, Any]], gpu: Callable[[], Mapping[str, Any] | None],
                 device: Callable[[], Mapping[str, int | None]] | None = None, interval: float = 1.0,
                 on_hard_abort: Callable[[str], None] | None = None) -> None:
        super().__init__(daemon=True)
        self.limits = dict(limits)
        self.heartbeat = heartbeat
        self.meminfo, self.scope, self.gpu, self.device = meminfo, scope, gpu, device
        self.interval = interval
        self.on_hard_abort = on_hard_abort
        self.step = "start"
        self.abort_reason: str | None = None
        self.peaks: dict[str, Any] = {"host_available_min": None, "rss_max": None, "scope_current_max": None,
                                      "scope_peak": None, "gpu_used_mib_max": None, "device_reserved_max": None,
                                      "samples": 0}
        self._stop = threading.Event()
        self._abort_at: float | None = None

    def _max(self, key: str, value: Any) -> None:
        if value is not None and (self.peaks[key] is None or value > self.peaks[key]):
            self.peaks[key] = value

    def sample(self) -> None:
        info = self.meminfo()
        available = info.get("MemAvailable")
        if available is not None and (self.peaks["host_available_min"] is None
                                      or available < self.peaks["host_available_min"]):
            self.peaks["host_available_min"] = available
        self._max("rss_max", _own_rss())
        scope = self.scope()
        self._max("scope_current_max", scope.get("memory_current"))
        self._max("scope_peak", scope.get("memory_peak"))
        try:
            gpu = self.gpu()
        except Exception:  # noqa: BLE001 - a failed nvidia-smi sample is not a reason to stop
            gpu = None
        if gpu is not None:
            own = [item.get("used_mib") or 0 for item in gpu.get("processes") or [] if item["pid"] == os.getpid()]
            self._max("gpu_used_mib_max", max(own) if own else None)
        if self.device is not None:
            try:
                self._max("device_reserved_max", self.device().get("max_reserved"))
            except Exception:  # noqa: BLE001
                pass
        self.peaks["samples"] += 1
        reason = None
        if available is not None and available < float(self.limits["host_floor_gib"]) * GIB:
            reason = f"host MemAvailable fell below {self.limits['host_floor_gib']} GiB"
        target = float(self.limits["device_peak_target_gib"]) * GIB
        device_peak = max(self.peaks["device_reserved_max"] or 0, (self.peaks["gpu_used_mib_max"] or 0) * MIB)
        if device_peak > target:
            reason = f"the device peak passed the {self.limits['device_peak_target_gib']} GiB target"
        deadline = self.limits.get("deadline_unix")
        if deadline is not None and time.time() >= float(deadline):
            reason = "the GPU-hours allowance ran out"
        if reason and self.abort_reason is None:
            self.abort_reason = reason
            self._abort_at = time.monotonic()
        if self.heartbeat is not None:
            _atomic_json(self.heartbeat, {"at": time.time(), "pid": os.getpid(), "step": self.step,
                                          "abort": self.abort_reason})

    def run(self) -> None:
        while not self._stop.wait(self.interval):
            self.sample()
            # A forward pass cannot be interrupted: past the grace, exit hard.
            if (self._abort_at is not None and self.on_hard_abort is not None
                    and time.monotonic() - self._abort_at > float(self.limits.get("hard_abort_grace_s", 60))):
                self.on_hard_abort(self.abort_reason or "aborted")

    def stop(self) -> None:
        self._stop.set()


def _own_rss() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except OSError:
        return None
    return None


def _atomic_json(path: Path, value: Any) -> None:
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64).ravel()
    b = np.asarray(b, dtype=np.float64).ravel()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def check_vector(vector: np.ndarray, dims: int) -> str | None:
    """Why a raw output row is not a valid int8-valued vector (None: valid)."""

    values = np.asarray(vector, dtype=np.float64)
    if values.shape != (dims,):
        return "dimensions"
    if not np.all(np.isfinite(values)):
        return "non_finite"
    if not np.any(values):
        return "zero"
    if not np.all(values == np.round(values)) or values.min() < -128 or values.max() > 127:
        return "not_int8_valued"
    return None


def smoke(model: LoadedModel, job: Mapping[str, Any]) -> dict[str, Any]:
    """Spec §8's smoke checks on PUBLIC text (each recorded with its values)."""

    dims = int(job["dimensions"])
    context = job["smoke"]["context"]
    central = context["central"]
    documents = [[left, central, right] for left, right in context["contexts"]] + [[central]]
    checks: dict[str, Any] = {}
    forward = model.encode_documents(documents, batch_size=1)
    backward = list(reversed(model.encode_documents(list(reversed(documents)), batch_size=1)))
    checks["dims_and_order"] = {
        "ok": all(row.shape == (len(chunks), dims) for row, chunks in zip(forward, documents, strict=True))
        and all(min(_cos(a, b) for a, b in zip(x, y, strict=True)) >= 0.99999
                for x, y in zip(forward, backward, strict=True)),
        "shapes": [list(row.shape) for row in forward]}
    in_a, in_b, alone = forward[0][1], forward[1][1], forward[2][0]
    sensitivity = {"a_vs_b": _cos(in_a, in_b), "a_vs_alone": _cos(in_a, alone), "b_vs_alone": _cos(in_b, alone)}
    checks["context_sensitive"] = {"ok": all(value < float(job["context_max_cos"]) for value in sensitivity.values()),
                                   "cosines": {key: round(value, 6) for key, value in sensitivity.items()}}
    query = job["smoke"]["query"]
    as_query = model.encode_queries([query], batch_size=1)[0][0]
    as_document = model.encode_documents([[query]], batch_size=1)[0][0]
    checks["methods_separate"] = {"ok": _cos(as_query, as_document) < float(job["context_max_cos"]),
                                  "query_vs_document_cos": round(_cos(as_query, as_document), 6)}
    rows = [vector for row in forward for vector in row] + [as_query]
    problems = sorted({problem for vector in rows if (problem := check_vector(vector, dims))})
    norms = [float(np.linalg.norm(vector)) for vector in rows]
    checks["decoding"] = {"ok": not problems and min(norms) > 1.0, "problems": problems,
                          "unnormalized_norm_min": round(min(norms), 3)}
    checks["finite_nonzero"] = {"ok": not ({"non_finite", "zero"} & set(problems))}
    padding = job["smoke"]["padding_document"]
    batched = model.encode_documents([documents[0], padding], batch_size=2)[0]
    queries_batched = model.encode_queries([query, " ".join(padding)], batch_size=2)[0][0]
    document_cos = min(_cos(a, b) for a, b in zip(forward[0], batched, strict=True))
    query_cos = _cos(as_query, queries_batched)
    tolerance = float(job["batch_invariance_min_cos"])
    checks["padding_batch_invariance"] = {"ok": document_cos >= tolerance and query_cos >= tolerance,
                                          "document_min_cos": round(document_cos, 6),
                                          "query_cos": round(query_cos, 6), "tolerance": tolerance}
    again = model.encode_documents([documents[0]], batch_size=1)[0]
    checks["deterministic"] = {"ok": bool(np.array_equal(again, forward[0]))}
    long_chunks = [" ".join(padding) * 30]
    long_tokens = model.count_tokens(long_chunks)
    checks["no_truncation"] = {
        "ok": long_tokens > int(job["max_document_tokens"]) and over_limit(long_tokens, job) is not None,
        "limit": int(job["max_document_tokens"]), "probe_tokens": long_tokens,
        "smoke_tokens": [model.count_tokens(chunks) for chunks in documents]}
    checks["all_ok"] = all(value.get("ok") for key, value in checks.items() if isinstance(value, dict))
    return checks


def over_limit(tokens: int, job: Mapping[str, Any]) -> str | None:
    """The harness's own limit (never a truncation): None when it fits."""

    return None if tokens <= int(job["max_document_tokens"]) else "over_limit"


def profile(model: LoadedModel, job: Mapping[str, Any], sampler: Sampler | None = None) -> dict[str, Any]:
    """Serialized indexing at each size, smallest first; a failure stops the larger sizes."""

    results: dict[str, Any] = {}
    stopped = None
    for size, chunks in sorted(((int(key), value) for key, value in (job.get("profile") or {}).items())):
        if stopped is not None:
            results[str(size)] = {"skipped": stopped}
            continue
        if sampler is not None and sampler.abort_reason:
            raise Aborted(sampler.abort_reason)
        tokens = model.count_tokens(chunks)
        model.reset_peak()
        latencies = []
        try:
            for _repeat in range(int(job["profile_repeats"])):
                started = time.monotonic()
                model.encode_documents([chunks], batch_size=1)
                latencies.append(round(time.monotonic() - started, 4))
        except WorkerOOM:
            results[str(size)] = {"tokens": tokens, "oom": True, "latencies_s": latencies}
            stopped = f"oom at {size}"
            continue
        memory = model.device_memory()
        results[str(size)] = {"tokens": tokens, "oom": False, "latencies_s": latencies,
                              "device_max_reserved": memory.get("max_reserved"),
                              "device_max_allocated": memory.get("max_allocated")}
    return results


def encode_all(model: LoadedModel, job: Mapping[str, Any], output: dict[str, Any], sampler: Sampler | None,
               lock: threading.Lock) -> None:
    dims = int(job["dimensions"])
    for document in job.get("documents") or []:
        if sampler is not None and sampler.abort_reason:
            raise Aborted(sampler.abort_reason)
        chunks = [chunk["text"] for chunk in document["chunks"]]
        tokens = model.count_tokens(chunks)
        if (problem := over_limit(tokens, job)) is not None:
            entry: dict[str, Any] = {"error": problem, "tokens": tokens}
        else:
            started = time.monotonic()
            [row] = model.encode_documents([chunks], batch_size=int(job["index_batch_size"]))
            latency = round(time.monotonic() - started, 4)
            bad = [check_vector(vector, dims) for vector in row]
            if row.shape[0] != len(chunks) or any(bad):
                entry = {"error": "invalid_output", "tokens": tokens}
            else:
                entry = {"vectors": [[int(value) for value in vector] for vector in row], "tokens": tokens,
                         "latency_s": latency}
        with lock:
            output["documents"][document["id"]] = entry
    for query in job.get("queries") or []:
        if sampler is not None and sampler.abort_reason:
            raise Aborted(sampler.abort_reason)
        tokens = model.count_tokens([query["text"]], task="query")
        if (problem := over_limit(tokens, job)) is not None:
            entry = {"error": problem, "tokens": tokens}
        else:
            started = time.monotonic()
            [row] = model.encode_queries([query["text"]], batch_size=int(job["query_batch_size"]))
            latency = round(time.monotonic() - started, 4)
            entry = ({"error": "invalid_output", "tokens": tokens} if check_vector(row[0], dims)
                     else {"vector": [int(value) for value in row[0]], "tokens": tokens, "latency_s": latency})
        with lock:
            output["queries"][query["id"]] = entry


def run_job(job: Mapping[str, Any], *, model_factory: Callable[[Path, Mapping[str, Any]], LoadedModel] = load_model,
            meminfo: Callable[[], Mapping[str, int]] = read_meminfo,
            scope: Callable[[], Mapping[str, Any]] = scope_limits,
            gpu: Callable[[], Mapping[str, Any] | None] = gpu_state, heartbeat: Path | None = None,
            write_partial: Callable[[Mapping[str, Any]], None] | None = None,
            hard_exit: Callable[[int], None] = os._exit) -> dict[str, Any]:
    """One worker process's whole job; always returns the output record."""

    lock = threading.Lock()
    output: dict[str, Any] = {"version": WORKER_VERSION, "plan_id": job["plan_id"], "status": "started",
                              "reason": None, "started_unix": time.time(), "documents": {}, "queries": {},
                              "environment": {"python": platform.python_version(), "pid": os.getpid()}}
    limits = job["limits"]
    try:
        gpu_now = gpu()
    except Exception:  # noqa: BLE001 - recorded as a refusal below
        gpu_now = None
    scope_now = scope()
    problems = start_problems(limits, meminfo=meminfo(), scope=scope_now, gpu=gpu_now, own_pids=(os.getpid(),))
    model_problems = model_dir_problems(Path(job["model_dir"]), job["model_files"], job["remote_code"])
    output["start_check"] = {"problems": [*problems, *model_problems], "scope": dict(scope_now),
                             "gpu": None if gpu_now is None else {key: gpu_now[key] for key in
                                                                   ("name", "driver", "total_mib", "free_mib",
                                                                    "used_mib", "utilization_pct")},
                             "host_available": meminfo().get("MemAvailable")}
    if problems or model_problems:
        output.update(status="refused", reason="; ".join([*problems, *model_problems]), ended_unix=time.time())
        return output

    def hard_abort(reason: str) -> None:
        with lock:
            output.update(status="aborted", reason=reason, ended_unix=time.time(), peaks=dict(sampler.peaks))
            if write_partial is not None:
                write_partial(output)
        hard_exit(4)

    sampler = Sampler(limits, heartbeat=heartbeat, meminfo=meminfo, scope=scope, gpu=gpu,
                      interval=float(limits.get("sample_interval_s", 1.0)), on_hard_abort=hard_abort)
    sampler.sample()
    sampler.start()
    model = None
    try:
        sampler.step = "load"
        model = model_factory(Path(job["model_dir"]), job)
        sampler.device = model.device_memory
        output["load"] = dict(model.info)
        output["load"]["device_after_load"] = model.device_memory()
        sampler.step = "smoke"
        output["smoke"] = smoke(model, job)
        if not output["smoke"]["all_ok"]:
            raise Aborted("a smoke check failed; nothing is indexed")
        sampler.step = "profile"
        output["profile"] = profile(model, job, sampler)
        sampler.step = "encode"
        encode_all(model, job, output, sampler, lock)
        output["status"] = "complete"
    except Aborted as exc:
        output.update(status="aborted", reason=str(exc))
    except WorkerOOM as exc:
        output.update(status="failed", reason=f"oom: {exc}")
    except Refused as exc:
        output.update(status="refused", reason=str(exc))
    except Exception as exc:  # noqa: BLE001 - the type only (library messages can carry paths)
        output.update(status="failed", reason=f"failed: {type(exc).__name__}")
    finally:
        sampler.step = "unload"
        if model is not None:
            try:
                output["device_peak"] = model.device_memory()
                output["unload"] = model.unload()
            except Exception as exc:  # noqa: BLE001
                output["unload"] = {"complete": False, "error": type(exc).__name__}
        sampler.sample()
        sampler.stop()
        output["peaks"] = dict(sampler.peaks)
        output["ended_unix"] = time.time()
    return output


def _guard_network() -> None:
    """Refuse every inet connection from this process (zero network)."""

    original = socket.socket.connect

    def connect(self: socket.socket, address: Any) -> Any:
        if self.family in (socket.AF_INET, socket.AF_INET6):
            raise ConnectionRefusedError("the E1 worker makes no network connection")
        return original(self, address)

    socket.socket.connect = connect  # type: ignore[method-assign]
    socket.create_connection = lambda *_a, **_k: (_ for _ in ()).throw(  # type: ignore[assignment]
        ConnectionRefusedError("the E1 worker makes no network connection"))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="E1 local pplx v2 worker (one batch, then exit)")
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--heartbeat", type=Path, required=True)
    args = parser.parse_args(argv)
    job = json.loads(args.job.read_text(encoding="utf-8"))
    private = args.job.parent
    os.environ.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                       "HF_HOME": str(private / "hf_home"), "HF_MODULES_CACHE": str(private / "hf_modules"),
                       "TOKENIZERS_PARALLELISM": "false",
                       "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"})
    _guard_network()
    output = run_job(job, heartbeat=args.heartbeat, write_partial=lambda value: _atomic_json(args.out, value))
    _atomic_json(args.out, output)
    return 0 if output["status"] == "complete" else 3


if __name__ == "__main__":
    sys.exit(main())
