"""The v2 local arms: the job, the scoped worker launch, the vector store and ranking.

The app process never imports torch: it writes one private job (every
missing v2 document and query of every copy, the smoke and the profiling
windows), runs ONE worker process in its own ``systemd-run --user --scope``
(``MemoryMax``, ``MemorySwapMax``) with the separate environment's
interpreter, under the GPU-hours meter, then validates and stores what came
back. The worker loads once, encodes, unloads and exits: no residency.

Identity follows E0's formula (``adapters.document_space_id`` /
``query_encoder_id``) with the model's repo, revision and BF16 precision in
the pinned model name, so a later FP8 or revision is another space. Raw
int8-valued rows are kept beside the L2-normalized FP32 scoring copy
(``adapters.decode``), exactly as for the hosted int8 arms; grouped and
singleton share one query encoder (the same ``encode_queries``).

``WorkerLauncher`` is the seam the tests replace: ``ScopedLauncher`` is the
real one; the tests run ``worker.run_job`` in-process with a fake model.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from learnloop.experiments.contextual_embeddings import pins
from learnloop.experiments.contextual_embeddings.adapters import (
    AdapterError,
    Document,
    VectorStore,
    build_index,
    decode,
    document_space_id,
    query_encoder_id,
    query_vector_key,
)
from learnloop.experiments.contextual_embeddings.corpus import CorpusSnapshot, _inside_local_root
from learnloop.experiments.contextual_embeddings.e1 import pins as e1_pins
from learnloop.experiments.contextual_embeddings.e1 import worker as worker_module
from learnloop.experiments.contextual_embeddings.e1.gpu_meter import GpuMeter, supervise
from learnloop.experiments.contextual_embeddings.retrieval import documents_for, exact_search


@dataclass(frozen=True)
class V2Space:
    arm: str
    encoding: str
    recipe: str
    document_space_id: str
    query_encoder_id: str

    @property
    def query_space(self) -> str:
        return f"{self.query_encoder_id}_queries"


def v2_space(snapshot: CorpusSnapshot, arm: str) -> V2Space:
    spec = e1_pins.V2_ARMS[arm]
    pin = e1_pins.v2_pin()
    revisions = sorted(f"{info.extractor}/{info.extractor_version}/{info.extraction_id}"
                       for info in snapshot.infos.values())
    return V2Space(arm, spec["encoding"], spec["recipe"],
                   document_space_id(pin, encoding=spec["encoding"], recipe=spec["recipe"],
                                     extraction_revisions=revisions),
                   query_encoder_id(pin))


def v2_documents(snapshot: CorpusSnapshot, space: V2Space) -> tuple[list[Document], dict[str, str]]:
    return documents_for(snapshot, space.encoding, space.recipe, space.document_space_id)


def limits(*, deadline_unix: float | None = None) -> dict[str, Any]:
    """The worker's limits, from the pins (frozen into the plan)."""

    return {"memory_max_bytes": e1_pins.SCOPE_MEMORY_MAX_BYTES, "swap_max_bytes": int(e1_pins.SCOPE_SWAP_MAX),
            "min_host_available_gib": e1_pins.MIN_HOST_AVAILABLE_GIB, "min_free_vram_gib": e1_pins.MIN_FREE_VRAM_GIB,
            "max_other_gpu_process_mib": e1_pins.MAX_OTHER_GPU_PROCESS_MIB,
            "max_other_gpu_total_mib": e1_pins.MAX_OTHER_GPU_TOTAL_MIB,
            "forbidden_gpu_workloads": list(e1_pins.FORBIDDEN_GPU_WORKLOADS),
            "max_gpu_utilization_pct": e1_pins.MAX_GPU_UTILIZATION_PCT, "host_floor_gib": e1_pins.HOST_FLOOR_GIB,
            "device_peak_target_gib": e1_pins.DEVICE_PEAK_TARGET_GIB,
            "sample_interval_s": e1_pins.SAMPLE_INTERVAL_S, "hard_abort_grace_s": e1_pins.KILL_GRACE_S,
            "deadline_unix": deadline_unix}


def profile_windows(snapshot: CorpusSnapshot) -> dict[str, list[str]]:
    """One document per profiling size: consecutive permitted units (token
    ESTIMATES; the worker measures the model's own count)."""

    windows: dict[str, list[str]] = {}
    for size in e1_pins.PROFILE_TOKENS:
        chunks, total = [], 0
        for unit in snapshot.units:
            chunks.append(unit.text)
            total += pins.token_estimate(unit.text) + pins.CHUNK_MARKER_TOKENS
            if total >= size:
                break
        windows[str(size)] = chunks
    return windows


def build_job(plan_id: str, copies: Sequence[tuple[str, CorpusSnapshot, Mapping[str, str]]], store: VectorStore, *,
              model_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """The job (private: carries text) and its index (job ids -> store keys).

    ``copies``: ``(label, snapshot, {query_id: effective query text})``.
    Only what the store lacks is sent (a resumed run re-encodes nothing)."""

    documents: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    index: dict[str, Any] = {"documents": {}, "queries": {}}
    seen_queries: set[tuple[str, str]] = set()
    for label, snapshot, texts in copies:
        for arm in e1_pins.V2_ARMS:
            space = v2_space(snapshot, arm)
            docs, _chunk_unit = v2_documents(snapshot, space)
            for document in docs:
                saved = store.get(space.document_space_id, document.key)
                if saved is not None and len(saved) == len(document.chunks):
                    continue
                job_id = f"{label}|{arm}|{document.document_id}"
                documents.append({"id": job_id, "chunks": [{"id": chunk.chunk_id, "text": chunk.text}
                                                           for chunk in document.chunks]})
                index["documents"][job_id] = {"space": space.document_space_id, "key": document.key,
                                              "chunks": len(document.chunks)}
            for query_id, text in texts.items():
                key = query_vector_key(space.query_encoder_id, text)
                if (space.query_space, key) in seen_queries or store.get(space.query_space, key) is not None:
                    continue
                seen_queries.add((space.query_space, key))
                job_id = f"{label}|{query_id}"
                queries.append({"id": job_id, "text": text})
                index["queries"][job_id] = {"space": space.query_space, "key": key}
    first = copies[0][1] if copies else None
    job = {
        "version": worker_module.WORKER_VERSION, "plan_id": plan_id, "model_dir": str(model_dir),
        "model_files": {name: list(value) for name, value in e1_pins.MODEL_FILES.items()},
        "remote_code": list(e1_pins.REMOTE_CODE_FILES), "precision": e1_pins.PRECISION,
        "attention": e1_pins.ATTENTION_IMPLEMENTATION, "fp32_modules": list(e1_pins.FP32_MODULES),
        "dimensions": e1_pins.MODEL_DIMENSIONS, "max_document_tokens": e1_pins.MAX_DOCUMENT_TOKENS,
        "index_batch_size": e1_pins.INDEX_BATCH_SIZE, "query_batch_size": e1_pins.QUERY_BATCH_SIZE,
        "batch_invariance_min_cos": e1_pins.BATCH_INVARIANCE_MIN_COS,
        "context_max_cos": e1_pins.CONTEXT_SENSITIVITY_MAX_COS,
        "smoke": {"context": e1_pins.SMOKE_CONTEXT, "query": e1_pins.SMOKE_QUERY,
                  "padding_document": e1_pins.SMOKE_PADDING_DOCUMENT},
        "profile": profile_windows(first) if first is not None else {},
        "profile_repeats": e1_pins.PROFILE_REPEATS,
        "documents": documents, "queries": queries, "limits": limits(),
    }
    return job, index


def store_outputs(output: Mapping[str, Any], index: Mapping[str, Any], store: VectorStore) -> dict[str, Any]:
    """Validate and store the worker's vectors; returns the counts by outcome.
    A wrong count, width, value or a missing id stores nothing for that item."""

    pin = e1_pins.v2_pin()
    counts: dict[str, int] = {"documents_stored": 0, "queries_stored": 0}

    def bump(name: str) -> None:
        counts[name] = counts.get(name, 0) + 1

    for job_id, target in index["documents"].items():
        entry = (output.get("documents") or {}).get(job_id)
        if entry is None:
            bump("documents_missing")
            continue
        if "error" in entry:
            bump(f"documents_{entry['error']}")
            continue
        rows = entry.get("vectors") or []
        if len(rows) != int(target["chunks"]):
            bump("documents_wrong_count")
            continue
        try:
            vectors = [decode(list(row), pin, where=f"{job_id}[{position}]").tolist()
                       for position, row in enumerate(rows)]
        except AdapterError:
            bump("documents_invalid")
            continue
        store.put(target["space"], target["key"], vectors, raw=[list(row) for row in rows])
        counts["documents_stored"] += 1
    for job_id, target in index["queries"].items():
        entry = (output.get("queries") or {}).get(job_id)
        if entry is None or "error" in entry:
            bump("queries_missing" if entry is None else f"queries_{entry['error']}")
            continue
        try:
            vector = decode(list(entry["vector"]), pin, where=job_id).tolist()
        except AdapterError:
            bump("queries_invalid")
            continue
        store.put(target["space"], target["key"], [vector], raw=[list(entry["vector"])])
        counts["queries_stored"] += 1
    return counts


def measurements(output: Mapping[str, Any]) -> dict[str, Any]:
    """The worker output without vectors or ids: what the report may show."""

    documents = [entry for entry in (output.get("documents") or {}).values() if "latency_s" in entry]
    queries = [entry for entry in (output.get("queries") or {}).values() if "latency_s" in entry]
    from learnloop.experiments.contextual_embeddings.metrics import latency_summary

    return {
        "status": output.get("status"), "reason": output.get("reason"), "failed_step": output.get("failed_step"),
        "traceback": output.get("traceback"),
        "start_check": {key: value for key, value in (output.get("start_check") or {}).items() if key != "scope"},
        "scope": {key: value for key, value in ((output.get("start_check") or {}).get("scope") or {}).items()
                  if key != "cgroup"},
        "load": output.get("load"), "smoke": output.get("smoke"), "profile": output.get("profile"),
        "peaks": output.get("peaks"), "device_peak": output.get("device_peak"), "unload": output.get("unload"),
        "documents": {"encoded": len(documents), "tokens": sum(int(entry["tokens"]) for entry in documents),
                      "latency_s": latency_summary([float(entry["latency_s"]) for entry in documents])},
        "queries": {"encoded": len(queries),
                    "batch_one_latency_s": latency_summary([float(entry["latency_s"]) for entry in queries])},
        "wall_s": (round(float(output["ended_unix"]) - float(output["started_unix"]), 3)
                   if output.get("ended_unix") and output.get("started_unix") else None),
    }


# -- launching ------------------------------------------------------------------------------
class WorkerLauncher(Protocol):
    def __call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]: ...


def scope_command(env_python: Path, job: Path, out: Path, heartbeat: Path, *, unit: str) -> list[str]:
    """The worker inside its own transient scope with the plan's memory caps."""

    return ["systemd-run", "--user", "--scope", "--quiet", f"--unit={unit}",
            "-p", f"MemoryMax={e1_pins.SCOPE_MEMORY_MAX}", "-p", f"MemorySwapMax={e1_pins.SCOPE_SWAP_MAX}", "--",
            str(env_python), "-I", str(Path(worker_module.__file__).resolve()),
            "--job", str(job), "--out", str(out), "--heartbeat", str(heartbeat)]


def launch_environment(home: Path) -> dict[str, str]:
    """``env -i``-like: PATH, an empty private HOME, and what ``systemd-run
    --user`` needs to reach the user manager. No key, no app setting."""

    home.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8"}
    for name in ("XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS"):
        if os.environ.get(name):
            env[name] = os.environ[name]
    return env


class ScopedLauncher:
    """The real launcher: the job file, the scoped worker under the meter, its output."""

    def __init__(self, env_python: Path, *, popen: Callable[..., Any] | None = None) -> None:
        self.env_python = Path(env_python)
        self.popen = popen

    def __call__(self, job: dict[str, Any], workdir: Path, *, meter: GpuMeter, plan_id: str) -> dict[str, Any]:
        if not _inside_local_root(workdir):
            raise ValueError("the worker's private directory must be under fixtures-local")
        workdir.mkdir(parents=True, exist_ok=True)
        job_path, out_path, heartbeat = workdir / "job.json", workdir / "out.json", workdir / "heartbeat.json"
        out_path.unlink(missing_ok=True)

        def write_job(deadline: float) -> None:
            job["limits"]["deadline_unix"] = deadline
            job_path.write_text(json.dumps(job), encoding="utf-8")
            os.chmod(job_path, 0o600)

        unit = f"learnloop-e1-{plan_id}-{workdir.name}".replace("_", "-")
        kwargs: dict[str, Any] = {} if self.popen is None else {"popen": self.popen}
        supervised = supervise(scope_command(self.env_python, job_path, out_path, heartbeat, unit=unit),
                               meter=meter, plan_id=plan_id, label=workdir.name, heartbeat=heartbeat,
                               env=launch_environment(workdir / "home"), on_open=write_job,
                               log=workdir / "worker.stderr.log", **kwargs)
        output = (json.loads(out_path.read_text(encoding="utf-8")) if out_path.is_file()
                  else {"status": "no_output", "reason": f"the worker wrote no output ({supervised['status']})",
                        "documents": {}, "queries": {}})
        output["supervised"] = supervised
        return output


# -- ranking ---------------------------------------------------------------------------------
def rank_v2(snapshot: CorpusSnapshot, questions: Sequence[Any], texts: Mapping[str, str], store: VectorStore,
            arm: str, *, allowed: Callable[[Any], set[str]]) -> tuple[dict[str, list[str]], dict[str, int]]:
    """One v2 arm's rankings from the store (exact cosine, id tie-breaks).
    A missing document leaves its units out of the index and is counted; a
    missing query vector leaves that question unranked (never substituted)."""

    space = v2_space(snapshot, arm)
    documents, chunk_unit = v2_documents(snapshot, space)
    entries, missing = [], {"documents": 0, "queries": 0}
    for document in documents:
        vectors = store.get(space.document_space_id, document.key)
        if vectors is None or len(vectors) != len(document.chunks):
            missing["documents"] += 1
            continue
        for chunk, vector in zip(document.chunks, vectors, strict=True):
            entries.append((chunk_unit[chunk.chunk_id], space.document_space_id, space.query_encoder_id, vector))
    if missing["documents"] or not entries:
        return {}, missing | {"queries": len(questions)}
    index = build_index(entries)
    ranked: dict[str, list[str]] = {}
    for question in questions:
        saved = store.get(space.query_space, query_vector_key(space.query_encoder_id, texts[question.query_id]))
        if saved is None:
            missing["queries"] += 1
            continue
        hits = exact_search(index, np.asarray(saved[0], dtype=np.float32), query_encoder=space.query_encoder_id,
                            top_k=pins.POOL_DEPTH, allowed=allowed(question))
        ranked[question.query_id] = [unit_id for unit_id, _score in hits]
    return ranked, missing
