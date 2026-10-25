"""Local contextual retrieval test doubles: a fake 9B model (numpy only: no torch,
no download, no GPU), an in-process launcher under the real meter, a set-up
data root, and a fake Voyage client. No test here starts a process or sends a
request."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from learnloop.ai.execution import model_call, report_call_usage
from learnloop.local_embeddings import pins, worker

GIB = worker.GIB
HEALTHY_MEMINFO = {"MemTotal": 32 * GIB, "MemAvailable": 24 * GIB, "SwapTotal": 8 * GIB, "SwapFree": 8 * GIB}
HEALTHY_SCOPE = {"cgroup": "/user.slice/run-local.scope", "scope": True, "memory_max": 12 * GIB, "swap_max": 0,
                 "memory_current": 1 * GIB, "memory_peak": 2 * GIB}
HEALTHY_GPU = {"name": "RTX 5090", "driver": "615.78.08", "total_mib": 32_607, "used_mib": 2_200, "free_mib": 30_400,
               "utilization_pct": 2, "processes": [{"pid": 1, "used_mib": 300}]}
EPOCH = {"torch": "2.14.0+cu130", "transformers": "5.18.0", "cuda": "13.0"}


def _seeded(seed: str, dims: int) -> np.ndarray:
    return np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16)).standard_normal(dims)


class FakeLocalModel:
    """Deterministic int8-valued vectors that depend on the whole window;
    ``salt`` changes every vector (a different computation: epoch drift);
    ``count_tokens`` is the word count (a stand-in for the model's tokenizer)."""

    def __init__(self, *, dims: int = pins.MODEL_DIMENSIONS, salt: str = "") -> None:
        self.dims = dims
        self.salt = salt
        self.info = {"load_s": 0.01, "parameter_dtypes": {"bfloat16": 10, "float32": 1},
                     "fp32_modules": {"contextual_projection": True}, "kernel_messages": [], "precision": "bf16",
                     "torch": EPOCH["torch"], "transformers": EPOCH["transformers"], "cuda": EPOCH["cuda"]}
        self.documents: list[list[str]] = []
        self.queries: list[str] = []

    def _int8(self, values: np.ndarray) -> np.ndarray:
        return np.clip(np.round(np.tanh(values) * 127), -128, 127).astype(np.float32)

    def count_tokens(self, chunks: Sequence[str], *, task: str = "document") -> int:
        return sum(len(chunk.split()) for chunk in chunks) + len(chunks)

    def encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int = 1) -> list[np.ndarray]:
        rows = []
        for chunks in documents:
            self.documents.append(list(chunks))
            context = "|".join(chunks)
            rows.append(np.stack([self._int8(0.8 * _seeded(self.salt + "d:" + chunk, self.dims)
                                             + 0.4 * _seeded(self.salt + "c:" + context, self.dims))
                                  for chunk in chunks]))
        return rows

    def encode_queries(self, queries: Sequence[str], *, batch_size: int = 1) -> list[np.ndarray]:
        self.queries.extend(queries)
        return [np.stack([self._int8(_seeded(self.salt + "q:" + query, self.dims))]) for query in queries]

    def device_memory(self) -> dict[str, int | None]:
        return {"allocated": 17 * GIB, "reserved": 18 * GIB, "max_allocated": 17 * GIB, "max_reserved": 18 * GIB,
                "free": 12 * GIB, "total": 32 * GIB}

    def reset_peak(self) -> None:
        return None

    def unload(self) -> dict[str, Any]:
        return {"allocated_after": 0, "reserved_after": 0, "complete": True}


def run_fake_job(job: Mapping[str, Any], model: FakeLocalModel, **overrides: Any) -> dict[str, Any]:
    kwargs = dict(model_factory=lambda _dir, _job: model, meminfo=lambda: HEALTHY_MEMINFO,
                  scope=lambda: HEALTHY_SCOPE, gpu=lambda: HEALTHY_GPU, model_check=lambda _job: [],
                  hard_exit=lambda code: (_ for _ in ()).throw(SystemExit(code)))
    kwargs.update(overrides)
    return worker.run_job(job, **kwargs)


class InProcessLauncher:
    """The production worker's ``run_job`` in this process, under the real meter."""

    def __init__(self, model: FakeLocalModel) -> None:
        self.model = model
        self.jobs: list[dict[str, Any]] = []

    def __call__(self, job: dict[str, Any], workdir: Path, *, meter: Any, plan_id: str) -> dict[str, Any]:
        entry, deadline = meter.open(plan_id=plan_id, label=workdir.name, min_slot_s=0)
        job["limits"]["deadline_unix"] = deadline
        self.jobs.append(job)
        try:
            return run_fake_job(job, self.model)
        finally:
            meter.close(entry, status="exited", returncode=0)


@contextmanager
def no_locks():
    yield


def set_up_data_root(root: Path) -> dict[str, Any]:
    """A data root as ``learnloop embeddings local setup`` leaves it (fake env and model dir)."""

    env_python = root / "envs" / "fake" / "bin" / "python"
    env_python.parent.mkdir(parents=True, exist_ok=True)
    env_python.write_text("#!/bin/sh\n", encoding="utf-8")
    model_dir = root / "models" / "fake"
    model_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"version": 1, "model_dir": str(model_dir), "env_python": str(env_python), "repo": pins.MODEL_REPO,
                "revision": pins.MODEL_REVISION, "requirements": list(pins.LOCAL_REQUIREMENTS),
                "software_epoch": dict(EPOCH), "weights_verified": True}
    pins.manifest_path(root).write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


class FakeVoyageClient:
    """The fallback space's client: hashing vectors per chunk and its window
    context, receipts through ``model_call`` like the real one."""

    provider_name = "voyage_context"
    provider_type = "voyage_contextual_embedding"
    model = model_id = "voyage-context-4"
    profile = None

    def __init__(self, dims: int = 64) -> None:
        self.dims = dims
        self.document_calls: list[list[list[str]]] = []
        self.query_calls: list[list[str]] = []

    def _unit(self, vector: np.ndarray) -> list[float]:
        return (vector / np.linalg.norm(vector)).tolist()

    def _words(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dims)
        for word in text.lower().split():
            vector[int(hashlib.sha256(word.strip(".,;:?").encode()).hexdigest(), 16) % self.dims] += 1.0
        vector[-1] += 0.5
        return vector

    def embed_documents(self, documents: Sequence[Sequence[str]]) -> list[list[list[float]]]:
        with model_call(self, purpose="embedding", prompt=["document", [list(d) for d in documents]]):
            self.document_calls.append([list(document) for document in documents])
            report_call_usage({"input_tokens": sum(len(c) for d in documents for c in d) // 4, "output_tokens": 0})
            return [[self._unit(self._words(chunk) + 0.2 * self._words(" ".join(document))) for chunk in document]
                    for document in documents]

    def embed_queries(self, queries: Sequence[str]) -> list[list[float]]:
        with model_call(self, purpose="embedding", prompt=["query", list(queries)]):
            self.query_calls.append(list(queries))
            report_call_usage({"input_tokens": sum(len(q) for q in queries) // 4, "output_tokens": 0})
            return [self._unit(self._words(query)) for query in queries]


VOYAGE_PROFILE = """
[ai.providers.voyage_context]
type = "voyage_contextual_embedding"
dimensions = 64

[embedding.fallback]
enabled = true
"""
