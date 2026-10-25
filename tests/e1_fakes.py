"""E1 test doubles: a fake v2 model (numpy only, no torch, no download), healthy
resource probes, an in-process launcher, and the Anthropic role answers for
the supplementary labels."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
import re
from typing import Any

import numpy as np

from learnloop.experiments.contextual_embeddings.e1 import worker

GIB = worker.GIB
HEALTHY_MEMINFO = {"MemTotal": 32 * GIB, "MemAvailable": 24 * GIB, "SwapTotal": 8 * GIB, "SwapFree": 8 * GIB}
HEALTHY_SCOPE = {"cgroup": "/user.slice/run-e1.scope", "scope": True, "memory_max": 12 * GIB, "swap_max": 0,
                 "memory_current": 1 * GIB, "memory_peak": 2 * GIB}
HEALTHY_GPU = {"name": "RTX 5090", "driver": "615.78.08", "total_mib": 32_607, "used_mib": 2_200, "free_mib": 30_400,
               "utilization_pct": 2, "processes": [{"pid": 1, "used_mib": 300}]}


class FakeV2Model:
    """Deterministic int8-valued vectors: a chunk's vector mixes its own text
    with its document's context (unless ``contextual=False``); queries use a
    separate method; ``oom_at`` raises a device OOM at that many tokens."""

    def __init__(self, *, dims: int = 2048, contextual: bool = True, oom_at: int | None = None,
                 query_like_document: bool = False) -> None:
        self.dims = dims
        self.contextual = contextual
        self.oom_at = oom_at
        self.query_like_document = query_like_document
        self.info = {"load_s": 0.01, "parameter_dtypes": {"bfloat16": 10, "float32": 1},
                     "fp32_modules": {"contextual_projection": True}, "kernel_messages": [], "precision": "bf16"}
        self.encoded_documents = 0
        self.encoded_queries = 0
        self.unloaded = False

    def _vector(self, seed: str) -> np.ndarray:
        generator = np.random.default_rng(int(hashlib.sha256(seed.encode()).hexdigest()[:12], 16))
        return generator.standard_normal(self.dims)

    @staticmethod
    def _int8(values: np.ndarray) -> np.ndarray:
        return np.clip(np.round(np.tanh(values) * 127), -128, 127).astype(np.float32)

    def count_tokens(self, chunks: Sequence[str], *, task: str = "document") -> int:
        return sum(len(chunk.encode()) // 4 + 1 for chunk in chunks) + 1

    def encode_documents(self, documents: Sequence[Sequence[str]], *, batch_size: int = 1) -> list[np.ndarray]:
        rows = []
        for chunks in documents:
            if self.oom_at is not None and self.count_tokens(chunks) >= self.oom_at:
                raise worker.WorkerOOM("fake device out of memory")
            context = "|".join(chunks) if self.contextual else ""
            rows.append(np.stack([self._int8(0.8 * self._vector("d:" + chunk) + 0.4 * self._vector("c:" + context))
                                  for chunk in chunks]))
            self.encoded_documents += 1
        return rows

    def encode_queries(self, queries: Sequence[str], *, batch_size: int = 1) -> list[np.ndarray]:
        self.encoded_queries += len(queries)
        if self.query_like_document:
            return [row for row in self.encode_documents([[query] for query in queries])]
        return [np.stack([self._int8(self._vector("q:" + query))]) for query in queries]

    def device_memory(self) -> dict[str, int | None]:
        return {"allocated": 17 * GIB, "reserved": 18 * GIB, "max_allocated": 17 * GIB, "max_reserved": 18 * GIB,
                "free": 12 * GIB, "total": 32 * GIB}

    def reset_peak(self) -> None:
        return None

    def unload(self) -> dict[str, Any]:
        self.unloaded = True
        return {"allocated_after": 0, "reserved_after": 0, "complete": True}


def run_fake_job(job: Mapping[str, Any], model: FakeV2Model, **overrides: Any) -> dict[str, Any]:
    kwargs = dict(model_factory=lambda _dir, _job: model, meminfo=lambda: HEALTHY_MEMINFO,
                  scope=lambda: HEALTHY_SCOPE, gpu=lambda: HEALTHY_GPU, model_check=lambda _job: [],
                  hard_exit=lambda code: (_ for _ in ()).throw(SystemExit(code)))
    kwargs.update(overrides)
    return worker.run_job(job, **kwargs)


class InProcessLauncher:
    """The worker's ``run_job`` in this process, under the real GPU meter."""

    def __init__(self, model: FakeV2Model) -> None:
        self.model = model
        self.jobs: list[dict[str, Any]] = []

    def __call__(self, job: dict[str, Any], workdir: Any, *, meter: Any, plan_id: str) -> dict[str, Any]:
        entry, deadline = meter.open(plan_id=plan_id, label=workdir.name, min_slot_s=0)
        job["limits"]["deadline_unix"] = deadline
        self.jobs.append(job)
        try:
            return run_fake_job(job, self.model)
        finally:
            meter.close(entry, status="exited", returncode=0)


def _context(prompt: str) -> dict[str, Any]:
    return json.loads(prompt[prompt.index("{"):])["context"]


def _words(text: str) -> set[str]:
    return {word.strip(".,;:()$'").lower() for word in str(text).split() if len(word.strip(".,;:()$'")) > 3}


def e1_respond(role: str, prompt: str, model: Any) -> dict[str, Any]:
    """Supplementary label passes and verdicts from the prompt's own JSON."""

    context = _context(prompt)
    name = getattr(model, "__name__", "")
    if name == "SupplementPass":
        question = _words(context["question"])
        threshold = 3 if role == "label_a" else 4
        labels, required = [], []
        for candidate in context["candidates"]:
            overlap = len(question & _words(candidate["text"]))
            relevance = ("required" if overlap >= threshold else "helpful" if overlap >= 2
                         else "background" if overlap == 1 else "unrelated")
            labels.append({"ref": candidate["ref"], "relevance": relevance})
            if relevance == "required":
                required.append(candidate["ref"])
        return {"labels": labels, "new_sets": [[ref] for ref in required[:1]]}
    if name == "SupplementVerdict":
        first = context.get("pass_1") or {}
        return {"labels": [{"ref": candidate["ref"], "relevance": first.get(candidate["ref"]) or "unrelated"}
                           for candidate in context["candidates"]],
                "new_sets": context.get("pass_1_sets") or [], "unresolved": False}
    raise AssertionError(f"unexpected E1 request {role} {name}")


def refs_in(prompt: str) -> list[str]:
    return re.findall(r'"ref": "([a-z]\d+)"', prompt)
