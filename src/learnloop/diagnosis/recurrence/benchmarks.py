"""Benchmarks B1 (Eedi 2024) and B3 (vault replay) for Slice 2 T1 (§3.3).

Both are written to the shared harness contract Phase 5a builds for
``learnloop embeddings compare`` (``ops/embedding_compare.CompareSuite``):
``name``, ``description``, ``load(vault, request)``, ``plan(vault, data,
request)`` and ``run(data, request, ctx)``, with ``ctx.vectors(model, texts,
dims=..., task_prefix=...)`` returning unit vectors by text from a vector
cache in the output directory (never the vault).

**Integration point.** Phase 5a's harness is not on this branch's base. Until
it merges, :func:`run_bench` is a small local runner with the same contract
(``learnloop recurrence bench``). The suites read 5a's actual request and
context, not a look-alike: ``request.dims`` is a TUPLE of widths (an int is
accepted too), there is no ``request.k`` (B1's k is its own constant), and
B1's one LLM role is a registered PF role, :data:`B1_WRITER_ROLE`, routed to
the ``diagnosis`` task. At merge, the composition root (``cli/embeddings.py``)
calls ``register_suites(SUITES, role_tasks=ROLE_TASKS)`` with 5a's registries
before ``run_compare``: the suites join 5a's ``SUITES`` and the writer role
joins 5a's ``ROLE_TASKS``, so 5a's whole-plan admission prices it and
``ctx.role(B1_WRITER_ROLE)`` resolves it. Calls then go through
``ctx.caller.call`` (5a) or ``ctx.complete`` (the local runner).

* **B1**: Eedi "Mining Misconceptions in Mathematics" (2024). The data needs
  a Kaggle login, so the owner downloads it; the loader reads ``train.csv``
  and ``misconception_mapping.csv`` next to a ``manifest.json`` (each source's
  name, version and licence). One query per (question, wrong answer) with a
  labelled misconception; the query is either the raw response or an
  LLM-written hypothesis (the Eedi efficiency-prize pattern, written on the
  diagnoser's route); the corpus is the misconception names. Methods: each
  embedding model (raw and mean-centred cosine), BM25 and a BM25 + embedding
  hybrid (reciprocal rank). Metrics: recall@25 and MAP@25. Owner batch 2
  (2026-10-12): hypotheses are cached in the output directory under the
  writer's identity (model, generation settings, output budget), so a rerun
  with another writer never reuses old text; the writer's output budget is
  ``writer_output_tokens``, by default the shared output-budget policy's for
  the writer's route (``learnloop.ai.output_budget``: ``ai.output_tokens``,
  16,384, unless the route or profile says otherwise; owner 2026-10-12: never
  cut the writer off early); a truncated or invalid output is a logged
  failed case (not retried, not cached, a miss in the hypothesis view), and
  the suite renders its own Markdown table (``markdown_lines``).
* **B3**: the vault's own labelled hypothesis pairs (owner verdicts imported
  from M1, the same-cause judge, validated diagnoser citations, card taps),
  re-scored under each candidate model: AUC, recall@k of confirmed matches
  under the production shortlist rule, the recall-oriented blocking cutoff and
  its judge load (this sets ``recurrence.blocking_cutoffs`` and ``top_k``),
  and merge precision/recall when the groups are replayed from a subset of
  sources. Every label carries how its pair was nominated (second review F3):
  the same-cause judge only ever sees pairs the embedding shortlist chose, so
  its verdicts are reported apart and never measure the shortlist's recall,
  set its top_k or cutoff, or grade the P6 replay (they would ratchet the
  cutoff up and top_k down run after run). No LLM call; embeddings only. It embeds the PRODUCTION recipe
  (the hypothesis text and task prefix the shortlist ranks) at the SERVING
  width (``embedding.dimensions``) by default, and every recommended cutoff
  names the model, width, recipe and prefix it was measured on; the
  shortlist refuses an entry that does not match its stored vectors.

Reports are aggregate except B3's config recommendation; no learner text.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field, field_validator

from learnloop.ai.errors import AIInterrupted, AIInvalidOutput, AIProviderUnavailable
from learnloop.ai.execution import generation_limit
from learnloop.ai.execution import content_key, record_model_calls
from learnloop.ai.output_budget import DEFAULT_OUTPUT_TOKENS, output_budget
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import estimate_tokens, sum_estimates
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, compatible, hypothesis_subjects, scope_of
from learnloop.matching.union import UnionEdge, effective_verdicts, union_with_refusals
from learnloop.substrate.recurrence_groups import (
    AUTHORITY,
    NOMINATED_BY_CITATION,
    NOMINATED_BY_M1_LINK,
    NOMINATED_BY_SHORTLIST,
    compute_groups,
)
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

HARNESS_CONTRACT = "embeddings-compare-v1"
B1_PROMPT_VERSION = "b1-misconception-hypothesis-v1"
#: B1's hypothesis writer as a harness role, and the AI task that serves it
#: (production hypotheses are diagnoser text, so the diagnoser's own route).
B1_WRITER_ROLE = "recurrence_hypothesis_writer"
B1_WRITER_TASK = "diagnosis"
B1_WRITER_PURPOSE = "recurrence_b1_hypothesis"
#: Roles these suites add to the harness's role registry.
ROLE_TASKS = {B1_WRITER_ROLE: B1_WRITER_TASK}
#: B1's retrieval depth (recall@25, MAP@25; the Eedi metric).
B1_K = 25
DEFAULT_MODELS = (
    "qwen/qwen3-embedding-8b",
    "qwen/qwen3-embedding-4b",
    "google/gemini-embedding-2",
    "openai/text-embedding-3-large",
    "openai/text-embedding-3-small",
)
#: B1 compares models at one common MRL width (every candidate reaches it);
#: B3 defaults to the vault's serving width instead (``embedding.dimensions``).
B1_DEFAULT_DIMS = 1024
DEFAULT_TARGET_RECALL = 0.95
EMBED_BATCH = 32
EMBEDDING_ROUTE = "embedding"
#: Published per-million input prices (estimates for admission, not quotes).
#: Models without one need ``--embedding-price-per-million``.
EMBEDDING_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}
#: The writer's output budget per hypothesis without ``--writer-output-tokens``
#: and without a config: the shared policy's code default. With a vault, the
#: default is the policy's budget for the writer's route (``ai.output_tokens``,
#: ``ai.route_output_tokens.diagnosis`` or the profile's ``max_tokens``).
#: Owner batch 2: 300 truncated current writers (a reasoning model's
#: reasoning tokens count against it; one model failed on its first call).
B1_DEFAULT_WRITER_OUTPUT_TOKENS = DEFAULT_OUTPUT_TOKENS
#: The profile settings that change what the writer writes: part of every
#: hypothesis cache key, with the model and the output budget.
WRITER_SETTING_KEYS = ("type", "base_url", "reasoning_effort", "thinking", "response_format", "max_tokens")
#: B3 reports a cutoff and top_k for every model, but RECOMMENDS a config line
#: only once this many confirmed matches back it; below it the report says to
#: keep top-k only (a reporting rule, not a decision threshold: R6).
MIN_CONFIRMED_FOR_RECOMMENDATION = 30
_TOKEN = re.compile(r"\w+")


# -- request and context ------------------------------------------------------------------


@dataclass(frozen=True)
class BenchRequest:
    """The local runner's request: the fields of Phase 5a's ``CompareRequest``
    the suites read, with the same types (``dims`` is a tuple of widths)."""

    suite: str
    output_dir: Path
    benchmark_dir: Path | None = None
    models: tuple[str, ...] = ()
    dims: tuple[int, ...] = ()
    views: tuple[str, ...] = ()
    target_recall: float = DEFAULT_TARGET_RECALL
    max_cases: int | None = None
    writer_output_tokens: int | None = None
    dry_run: bool = False


def requested_dims(request: Any, default: int) -> tuple[int, ...]:
    """The widths a request asks for: 5a's tuple, a bare int, or ``default``."""

    raw = getattr(request, "dims", None)
    if raw is None or raw == () or raw == []:
        return (int(default),)
    values = (raw,) if isinstance(raw, int) else tuple(raw)
    widths = tuple(sorted({int(value) for value in values}))
    if not widths or any(width <= 0 for width in widths):
        raise ValueError("dims must be positive widths")
    return widths


class VectorCache:
    """Content-addressed float32 unit vectors in the output directory."""

    def __init__(self, root: Path, model: str, task_prefix: str, dims: int) -> None:
        slug = hashlib.sha256(f"{model}|{task_prefix}|{dims}".encode()).hexdigest()[:16]
        self.directory = root / slug
        self.index_path = self.directory / "index.json"
        self.vectors_path = self.directory / "vectors.npy"
        self._index: dict[str, int] = {}
        self._vectors: np.ndarray | None = None
        if self.index_path.exists() and self.vectors_path.exists():
            self._index = json.loads(self.index_path.read_text(encoding="utf-8"))["index"]
            self._vectors = np.load(self.vectors_path)
        self.model = model

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> np.ndarray | None:
        position = self._index.get(self.key(text))
        return None if position is None or self._vectors is None else self._vectors[position]

    def put_many(self, texts: Sequence[str], vectors: Sequence[Sequence[float]]) -> None:
        array = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        array = array / np.where(norms == 0, 1, norms)
        start = 0 if self._vectors is None else len(self._vectors)
        self._vectors = array if self._vectors is None else np.vstack([self._vectors, array])
        for offset, text in enumerate(texts):
            self._index[self.key(text)] = start + offset
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.directory / "vectors.tmp.npy"
        np.save(temporary, self._vectors)
        os.replace(temporary, self.vectors_path)
        index_tmp = self.directory / "index.tmp"
        index_tmp.write_text(json.dumps({"model": self.model, "index": self._index}), encoding="utf-8")
        os.replace(index_tmp, self.index_path)


class BenchContext:
    """The local runner's context: the 5a contract's ``vectors`` plus ``complete``."""

    def __init__(
        self,
        vault: LoadedVault,
        spend: ReviewSpend,
        *,
        output_dir: Path,
        embedding_clients: Mapping[str, Any] | None = None,
        writer_client: Any = None,
        embedding_price: float | None = None,
    ) -> None:
        self.vault = vault
        self.spend = spend
        self.output_dir = output_dir
        self._injected = dict(embedding_clients or {})
        self._clients: dict[tuple[str, int], Any] = {}
        self._writer = writer_client
        self._registered: set[str] = set()
        self.embedding_price = embedding_price

    def _embedder(self, model: str, dims: int) -> Any:
        key = (model, dims)
        if key not in self._clients:
            if model in self._injected:
                self._clients[key] = self._injected[model]
            else:
                from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

                route = self.vault.config.ai.routing.embedding
                profile = self.vault.config.ai.providers.get(route or "")
                if not self.vault.config.embedding.enabled or profile is None or profile.type != "openai_embedding":
                    raise AIProviderUnavailable(
                        "Benchmarks embed through the vault's embedding route: set embedding.enabled = true and "
                        "ai.routing.embedding to an openai_embedding profile on the copy you benchmark"
                    )
                self._clients[key] = OpenAIEmbeddingProviderClient(
                    route, profile.model_copy(update={"model": model, "dimensions": dims})
                )
        return self._clients[key]

    def vectors(self, model: str, texts: Sequence[str], *, dims: int, task_prefix: str = "similarity") -> dict[str, np.ndarray]:
        cache = VectorCache(self.output_dir / "cache", model, task_prefix, dims)
        missing = [text for text in dict.fromkeys(texts) if cache.get(text) is None]
        if missing:
            client = self._embedder(model, dims)
            price = self.embedding_price if self.embedding_price is not None else EMBEDDING_PRICES_PER_MILLION.get(model)
            route = f"{EMBEDDING_ROUTE}:{model}"
            if route not in self.spend.routes:
                # Metered; an unknown price fails closed at admission.
                source = "known" if model in EMBEDDING_PRICES_PER_MILLION and self.embedding_price is None else (
                    "owner_override" if price is not None else "unknown"
                )
                self.spend.routes[route] = RouteInfo(route, "embedding", model, "metered", price, source, 0)
            for start in range(0, len(missing), EMBED_BATCH):
                batch = missing[start:start + EMBED_BATCH]
                tokens = sum(estimate_tokens(text) + 32 for text in batch)
                with self.spend.collector.observing():
                    with self.spend.request(route, "embedding", input_tokens=tokens, output_tokens=0):
                        vectors = client.embed(list(batch), task_prefix)
                cache.put_many(batch, vectors)
        return {text: cache.get(text) for text in texts}

    def writer_client(self, role: str) -> Any:
        if self._writer is None:
            from learnloop.ai.routing import ready_client_for_task

            task = ROLE_TASKS.get(role, role)
            resolved = ready_client_for_task(self.vault.root, self.vault.config, task)  # type: ignore[arg-type]
            if not resolved.ready:
                raise AIProviderUnavailable(f"the {task} route ({role}) is not ready")
            self._writer = resolved.client
        return self._writer

    def complete(self, role: str, prompt: str, result_model: type[WireModel], purpose: str,
                 output_tokens: int | None = None) -> Any:
        writer = self.writer_client(role)
        if role not in self._registered:
            # Billed as the client actually built (the plan classified it from config).
            self.spend.register(role, writer)
            self._registered.add(role)
        with self.spend.collector.observing():
            # B1's rule: an invalid output (a truncation included) is one
            # failed case, so the transport never retries it either.
            with self.spend.request(role, purpose, input_tokens=estimate_tokens(prompt), output_tokens=output_tokens,
                                    retry_truncation=False):
                with generation_limit(output_tokens):
                    return execute_structured_operation(
                        writer, purpose=purpose, prompt=prompt, result_model=result_model, isolated=True
                    )


def _complete(ctx: Any, role: str, prompt: str, result_model: type[WireModel], purpose: str, prompt_version: str,
              output_tokens: int) -> tuple[Any, str | None]:
    """Through the local context, or Phase 5a's PF caller (``ctx.role`` + ``ctx.caller.call``).

    Returns the result and the resolved model when the caller reports one. An
    invalid output (truncated, malformed or blank) is not retried: the suite
    records the case as failed, and no retry reserves work the plan did not
    admit (Codex review F2). Transport failures are still retried.
    """

    if hasattr(ctx, "complete"):
        return ctx.complete(role, prompt, result_model, purpose, output_tokens=output_tokens), None
    entry = ctx.role(role)[0]
    call = ctx.caller.call(entry, prompt=prompt, prompt_version=prompt_version, result_model=result_model,
                           output_tokens=output_tokens, retry_invalid_output=False)
    return call.result, getattr(call, "model", None)


def writer_tokens(prompt: str, result_model: type[WireModel],
                  output_tokens: int = B1_DEFAULT_WRITER_OUTPUT_TOKENS) -> int:
    """One writer call's input-plus-output bound, as 5a's harness counts it."""

    schema = len(json.dumps(result_model.model_json_schema()).encode("utf-8"))
    return len(prompt.encode("utf-8")) + schema + 512 + int(output_tokens)


def requested_writer_output_tokens(request: Any, config: Any | None = None) -> int:
    """The writer's output budget a request asks for.

    Without ``writer_output_tokens``, the shared policy's budget for the
    writer's route under ``config`` (``learnloop.ai.output_budget``; None: the
    policy's code default, :data:`B1_DEFAULT_WRITER_OUTPUT_TOKENS`).
    """

    value = getattr(request, "writer_output_tokens", None)
    if value is None:
        return output_budget(config, B1_WRITER_TASK)
    if int(value) <= 0:
        raise ValueError("writer_output_tokens must be positive")
    return int(value)


def _settings_view(profile: Any) -> dict[str, Any]:
    if profile is None:
        return {key: None for key in WRITER_SETTING_KEYS}
    if isinstance(profile, Mapping):
        return {key: profile.get(key) for key in WRITER_SETTING_KEYS}
    return {key: getattr(profile, key, None) for key in WRITER_SETTING_KEYS}


def _client_settings(client: Any) -> dict[str, Any]:
    """An injected or resolved client's generation settings (its profile or config)."""

    view = _settings_view(getattr(client, "profile", None) or getattr(client, "config", None))
    if not view.get("type"):
        view["type"] = getattr(client, "provider_type", None)
    return view


def writer_identity(model: str | None, settings: Mapping[str, Any], output_tokens: int) -> dict[str, Any]:
    """Who writes B1's hypotheses: part of every hypothesis cache key (owner batch 2).

    A rerun with another model, another generation setting (reasoning effort,
    thinking, response format, endpoint, profile output cap) or another
    output budget never reuses text another writer wrote.
    """

    return {
        "prompt_version": B1_PROMPT_VERSION,
        "model": model,
        "settings": {key: settings.get(key) for key in WRITER_SETTING_KEYS},
        "output_tokens": int(output_tokens),
    }


def configured_writer(vault: LoadedVault, output_tokens: int) -> dict[str, Any]:
    """The writer identity from config alone, as the harness plans the role.

    The same route resolution as ``pf_calls.planned_role_clients`` (the writer
    is not a tiered role), so the dry run's cached count matches the run.
    """

    from learnloop.ai.routing import provider_for_task

    selection = provider_for_task(vault.config, B1_WRITER_TASK)  # type: ignore[arg-type]
    profile = vault.config.ai.providers.get(selection.provider_name)
    dump = profile.model_dump(mode="json") if profile is not None else None
    return writer_identity(getattr(profile, "model", None), _settings_view(dump), output_tokens)


def _run_writer(ctx: Any, output_tokens: int) -> dict[str, Any]:
    """The writer identity of the client this run actually calls."""

    if hasattr(ctx, "role"):
        entry = ctx.role(B1_WRITER_ROLE)[0]
        settings = getattr(entry, "settings", None)
        profile = settings.get("profile") if isinstance(settings, Mapping) else None
        view = _settings_view(profile) if profile is not None else _client_settings(entry.client)
        return writer_identity(getattr(entry, "model", None), view, output_tokens)
    client = ctx.writer_client(B1_WRITER_ROLE)
    return writer_identity(getattr(client, "model", None), _client_settings(client), output_tokens)


# -- metrics --------------------------------------------------------------------------------


def roc_auc(scores: Sequence[float], labels: Sequence[bool]) -> float | None:
    positives = [score for score, label in zip(scores, labels) if label]
    negatives = [score for score, label in zip(scores, labels) if not label]
    if not positives or not negatives:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return round(wins / (len(positives) * len(negatives)), 6)


def blocking_cutoff(scores: Sequence[float], labels: Sequence[bool], target_recall: float) -> dict[str, Any]:
    """The highest cutoff whose recall on confirmed matches reaches the target (R4)."""

    positives = sorted((score for score, label in zip(scores, labels) if label), reverse=True)
    negatives = [score for score, label in zip(scores, labels) if not label]
    if not positives:
        return {"cutoff": None, "recall": None, "positives": 0, "negatives": len(negatives)}
    needed = max(1, math.ceil(target_recall * len(positives)))
    cutoff = positives[needed - 1]
    recall = sum(1 for score in positives if score >= cutoff) / len(positives)
    return {
        "cutoff": round(float(cutoff), 6),
        "recall": round(recall, 6),
        "negatives_above": sum(1 for score in negatives if score >= cutoff),
        "positives": len(positives),
        "negatives": len(negatives),
    }


def rank_metrics(ranks: Sequence[int | None], k: int) -> dict[str, Any]:
    n = len(ranks)
    if not n:
        return {"n": 0, f"recall@{k}": None, f"map@{k}": None}
    hits = [rank for rank in ranks if rank is not None and rank <= k]
    return {
        "n": n,
        f"recall@{k}": round(len(hits) / n, 6),
        f"map@{k}": round(sum(1.0 / rank for rank in hits) / n, 6),
    }


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN.findall(text)]


class BM25:
    """Okapi BM25 over short documents, scored through postings."""

    def __init__(self, documents: Sequence[str], *, k1: float = 1.5, b: float = 0.75) -> None:
        docs = [_tokens(doc) for doc in documents]
        self.size = len(docs)
        avgdl = (sum(len(doc) for doc in docs) / len(docs)) if docs else 0.0
        norms = [k1 * (1 - b + b * len(doc) / (avgdl or 1.0)) for doc in docs]
        self.postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for index, doc in enumerate(docs):
            for term, count in Counter(doc).items():
                self.postings[term].append((index, count * (k1 + 1) / (count + norms[index])))
        self.idf = {
            term: math.log(1 + (self.size - len(rows) + 0.5) / (len(rows) + 0.5)) for term, rows in self.postings.items()
        }

    def scores(self, query: str) -> np.ndarray:
        out = np.zeros(self.size)
        for term in set(_tokens(query)):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for index, weight in self.postings[term]:
                out[index] += idf * weight
        return out


def _rank_of(scores: np.ndarray, gold: int) -> int:
    """1-based rank of ``gold``; ties broken by index (deterministic)."""

    value = scores[gold]
    return int(np.sum(scores > value) + np.sum(scores[:gold] == value) + 1)


def _ranks_from_order(scores: np.ndarray) -> np.ndarray:
    order = np.lexsort((np.arange(len(scores)), -np.asarray(scores, dtype=np.float64)))
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    return ranks


def _matrix(vectors: Mapping[str, np.ndarray], texts: Sequence[str], dims: int) -> np.ndarray:
    matrix = np.vstack([np.asarray(vectors[text], dtype=np.float64)[:dims] for text in texts])
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.where(norms == 0, 1, norms)


def _centred(matrix: np.ndarray) -> np.ndarray:
    centred = matrix - matrix.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(centred, axis=1, keepdims=True)
    return centred / np.where(norms == 0, 1, norms)


# -- B1: Eedi 2024 ----------------------------------------------------------------------------


class MisconceptionHypothesis(WireModel):
    misconception: str = Field(
        description="The belief that leads a student to this wrong answer, stated as what the student thinks is true."
    )

    @field_validator("misconception")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        """A blank hypothesis breaks the contract (Codex review F1).

        Rejected where the provider's output is parsed, so it is invalid
        output (one failed case) and never checkpointed; a blank checkpoint
        saved before this check no longer validates and is discarded. A
        validator, not ``min_length``: the JSON schema, and with it every
        valid checkpoint's key, is unchanged.
        """

        if not value.strip():
            raise ValueError("misconception is blank")
        return value


def b1_prompt(case: Mapping[str, Any]) -> str:
    return render_structured_prompt(
        "learnloop B1 misconception hypothesis",
        B1_PROMPT_VERSION,
        {
            "task": (
                "A student chose the wrong answer below. In one sentence, state the misconception "
                "(the mistaken belief, in general terms that would apply to other questions) that "
                "most plausibly led to it. Do not restate the question or the answer."
            ),
            "context": {
                "construct": case["construct"],
                "subject": case["subject"],
                "question": case["question"],
                "correct_answer": case["correct_answer"],
                "wrong_answer": case["wrong_answer"],
            },
        },
    )


def _read_manifest(directory: Path) -> dict[str, Any]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ValueError(f"{directory} has no manifest.json (each source's name, version and licence)")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources or not all(
        isinstance(source, dict) and all(str(source.get(key) or "").strip() for key in ("name", "version", "licence"))
        for source in sources
    ):
        raise ValueError("manifest.json must list sources, each with name, version and licence")
    return manifest


@dataclass
class B1Data:
    manifest: dict[str, Any]
    misconceptions: list[tuple[str, str]]  # (id, name)
    cases: list[dict[str, Any]]
    models: tuple[str, ...]
    views: tuple[str, ...]
    dims: tuple[int, ...] = (B1_DEFAULT_DIMS,)


def load_eedi(directory: Path, *, max_cases: int | None = None) -> tuple[dict[str, Any], list[tuple[str, str]], list[dict[str, Any]]]:
    """Read the Kaggle files the owner downloaded (no network here)."""

    manifest = _read_manifest(directory)
    mapping_path, train_path = directory / "misconception_mapping.csv", directory / "train.csv"
    for path in (mapping_path, train_path):
        if not path.is_file():
            raise ValueError(
                f"{path.name} is missing: download the Eedi 'Mining Misconceptions in Mathematics' data "
                f"from Kaggle (login required) into {directory}"
            )
    with mapping_path.open(encoding="utf-8", newline="") as handle:
        misconceptions = [
            (str(row["MisconceptionId"]).strip(), str(row["MisconceptionName"]).strip())
            for row in csv.DictReader(handle)
            if str(row.get("MisconceptionId") or "").strip()
        ]
    known = {identifier for identifier, _name in misconceptions}
    cases: list[dict[str, Any]] = []
    with train_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            correct = str(row.get("CorrectAnswer") or "").strip()
            for option in "ABCD":
                if option == correct:
                    continue
                raw_id = str(row.get(f"Misconception{option}Id") or "").strip()
                if not raw_id or raw_id.lower() == "nan":
                    continue
                gold = str(int(float(raw_id))) if raw_id.replace(".", "", 1).isdigit() else raw_id
                if gold not in known:
                    continue
                cases.append(
                    {
                        "id": f"{row.get('QuestionId')}{option}",
                        "construct": str(row.get("ConstructName") or ""),
                        "subject": str(row.get("SubjectName") or ""),
                        "question": str(row.get("QuestionText") or ""),
                        "correct_answer": str(row.get(f"Answer{correct}Text") or ""),
                        "wrong_answer": str(row.get(f"Answer{option}Text") or ""),
                        "gold": gold,
                    }
                )
    cases.sort(key=lambda case: hashlib.sha256(case["id"].encode()).hexdigest())
    if max_cases is not None:
        cases = cases[:max_cases]
    return manifest, misconceptions, cases


def raw_query(case: Mapping[str, Any]) -> str:
    return (
        f"{case['construct']}\nQuestion: {case['question']}\nCorrect answer: {case['correct_answer']}\n"
        f"Student's answer: {case['wrong_answer']}"
    )


class B1Suite:
    name = "b1"
    description = "Eedi 2024 misconception retrieval: raw response vs LLM-written hypothesis queries (recall@25, MAP@25)."
    VIEWS = ("raw", "hypothesis")

    def load(self, vault: LoadedVault, request: BenchRequest) -> B1Data:
        if request.benchmark_dir is None:
            raise ValueError("b1 needs --benchmark <dir> holding the Eedi files and a manifest.json")
        manifest, misconceptions, cases = load_eedi(request.benchmark_dir, max_cases=request.max_cases)
        views = tuple(request.views or self.VIEWS)
        unknown = sorted(set(views) - set(self.VIEWS))
        if unknown:
            raise ValueError(f"unknown b1 view(s): {', '.join(unknown)}")
        return B1Data(manifest, misconceptions, cases, tuple(request.models or DEFAULT_MODELS), views,
                      requested_dims(request, B1_DEFAULT_DIMS))

    def _hypothesis_cache(self, request: BenchRequest) -> Path:
        return request.output_dir / "b1_hypotheses.jsonl"

    def _cached_hypotheses(self, request: BenchRequest) -> dict[str, str]:
        """Cached hypotheses by key. Rows that name no writer (written before
        owner batch 2) are ignored, never reused."""

        path = self._hypothesis_cache(request)
        if not path.exists():
            return {}
        out: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            writer = row.get("writer")
            if not isinstance(writer, Mapping) or not writer.get("model"):
                continue
            out[str(row["key"])] = str(row["misconception"])
        return out

    @staticmethod
    def _case_key(case: Mapping[str, Any], writer: Mapping[str, Any]) -> str:
        return content_key({"prompt_version": B1_PROMPT_VERSION, "case": dict(case), "writer": dict(writer)})

    def plan(self, vault: LoadedVault, data: B1Data, request: BenchRequest) -> dict[str, Any]:
        output_tokens = requested_writer_output_tokens(request, vault.config)
        writer = configured_writer(vault, output_tokens) if "hypothesis" in data.views else None
        cached = self._cached_hypotheses(request) if writer is not None else {}
        to_write = [case for case in data.cases if self._case_key(case, writer) not in cached] if writer is not None else []
        corpus_tokens = sum(estimate_tokens(name) + 32 for _id, name in data.misconceptions)
        query_tokens = sum(estimate_tokens(raw_query(case)) + 32 for case in data.cases) if "raw" in data.views else 0
        hypothesis_tokens = 100 * len(data.cases) if "hypothesis" in data.views else 0
        per_model_tokens = corpus_tokens + query_tokens + hypothesis_tokens
        # The corpus and each query view are separate vector requests, each batched.
        requests = math.ceil(len(data.misconceptions) / EMBED_BATCH) + len(data.views) * math.ceil(
            len(data.cases) / EMBED_BATCH
        )
        return {
            "cases": len(data.cases),
            "misconceptions": len(data.misconceptions),
            "views": list(data.views),
            "models": list(data.models),
            "dims": list(data.dims),
            # The configured writer (the run uses the resolved client's identity).
            "writer": writer,
            "roles": {
                B1_WRITER_ROLE: {
                    "calls": len(to_write),
                    # Input plus output of every call not cached yet.
                    "tokens": sum(writer_tokens(b1_prompt(case), MisconceptionHypothesis, output_tokens)
                                  for case in to_write),
                    # The output share of ``tokens`` (priced at the output rate).
                    "output_tokens": output_tokens * len(to_write),
                    "cached": len(data.cases) - len(to_write) if writer is not None else 0,
                }
            },
            "embedding": {model: {"calls": requests, "tokens": per_model_tokens} for model in data.models},
            "note": "embedding calls are an upper bound; texts already in the output directory's cache are not sent",
        }

    def _write_hypotheses(self, data: B1Data, request: BenchRequest, ctx: Any) -> tuple[dict[str, str], dict[str, Any]]:
        """Each case's hypothesis, written or reused, and the writer's summary.

        A truncated, malformed or blank output is a failed case: recorded, not
        retried, never cached or checkpointed (a rerun asks again), and a miss
        in the hypothesis view. Provider outages that outlast the retry cap,
        caps and cancellation still stop the run.
        """

        vault = getattr(ctx, "vault", None)
        output_tokens = requested_writer_output_tokens(request, getattr(vault, "config", None))
        writer = _run_writer(ctx, output_tokens)
        cached = self._cached_hypotheses(request)
        path = self._hypothesis_cache(request)
        path.parent.mkdir(parents=True, exist_ok=True)
        hypotheses: dict[str, str] = {}
        written = reused = 0
        failures: Counter[str] = Counter()
        resolved: Counter[str] = Counter()
        for case in data.cases:
            key = self._case_key(case, writer)
            if key in cached:
                reused += 1
                hypotheses[case["id"]] = cached[key]
                continue
            try:
                result, model = _complete(ctx, B1_WRITER_ROLE, b1_prompt(case), MisconceptionHypothesis,
                                          B1_WRITER_PURPOSE, B1_PROMPT_VERSION, output_tokens)
            except AIInvalidOutput as exc:
                failures[type(exc).__name__] += 1
                continue
            text = str(result.misconception).strip()
            if not text:
                failures["EmptyHypothesis"] += 1
                continue
            cached[key] = text
            with path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"key": key, "writer": writer, "resolved_model": model, "misconception": text}) + "\n")
            if model:
                resolved[model] += 1
            written += 1
            hypotheses[case["id"]] = text
        summary = {
            "model": writer["model"],
            "settings": writer["settings"],
            "output_tokens": output_tokens,
            "resolved_models": dict(resolved),
            "written": written,
            "cached": reused,
            "failed_cases": sum(failures.values()),
            "failed_by_error": dict(failures),
            "failed_case_scoring": "a failed case has no hypothesis; it counts as a miss in the hypothesis view",
        }
        return hypotheses, summary

    def run(self, data: B1Data, request: BenchRequest, ctx: Any) -> dict[str, Any]:
        hypotheses: dict[str, str] = {}
        writer_summary: dict[str, Any] | None = None
        if "hypothesis" in data.views:
            hypotheses, writer_summary = self._write_hypotheses(data, request, ctx)
        ids = [identifier for identifier, _name in data.misconceptions]
        names = [name for _identifier, name in data.misconceptions]
        position = {identifier: index for index, identifier in enumerate(ids)}
        k = B1_K
        bm25 = BM25(names)
        # None: the writer failed on this case (a miss in the hypothesis view).
        queries: dict[str, list[str | None]] = {
            view: [raw_query(case) if view == "raw" else hypotheses.get(case["id"]) for case in data.cases]
            for view in data.views
        }
        gold = [position[case["gold"]] for case in data.cases]
        results: dict[str, Any] = {"bm25": {}, "embedding": {}, "hybrid": {}}
        bm25_ranks: dict[str, list[np.ndarray | None]] = {}
        for view, texts in queries.items():
            scored = [bm25.scores(text) if text is not None else None for text in texts]
            bm25_ranks[view] = [_ranks_from_order(scores) if scores is not None else None for scores in scored]
            results["bm25"][view] = rank_metrics(
                [_rank_of(scores, gold_index) if scores is not None else None
                 for scores, gold_index in zip(scored, gold, strict=True)], k
            )
        widest = max(data.dims)
        for model in data.models:
            # Embedded once at the widest width; narrower widths are MRL truncations.
            corpus_vectors = ctx.vectors(model, list(names), dims=widest, task_prefix="retrieval-document")
            query_vectors = {
                view: ctx.vectors(model, [text for text in texts if text is not None], dims=widest,
                                  task_prefix="retrieval-query")
                for view, texts in queries.items()
            }
            for dims in data.dims:
                label = model if len(data.dims) == 1 else f"{model}@{dims}"
                corpus = _matrix(corpus_vectors, names, dims)
                corpus_centred = _centred(corpus)
                for view, texts in queries.items():
                    present = [index for index, text in enumerate(texts) if text is not None]
                    variants: dict[str, list[int | None]] = {"cosine": [None] * len(texts), "centred": [None] * len(texts)}
                    fused: list[int | None] = [None] * len(texts)
                    if present:
                        matrix = _matrix(query_vectors[view], [texts[index] for index in present], dims)
                        for variant, (left, right) in {"cosine": (matrix, corpus), "centred": (_centred(matrix), corpus_centred)}.items():
                            scores = left @ right.T
                            for row, index in zip(scores, present, strict=True):
                                variants[variant][index] = _rank_of(row, gold[index])
                                if variant == "centred":
                                    emb_rank = _ranks_from_order(row)
                                    rrf = 1.0 / (60 + emb_rank) + 1.0 / (60 + bm25_ranks[view][index])
                                    fused[index] = _rank_of(rrf, gold[index])
                    for variant, ranks in variants.items():
                        results["embedding"].setdefault(label, {}).setdefault(view, {})[variant] = rank_metrics(ranks, k)
                    results["hybrid"].setdefault(label, {})[view] = rank_metrics(fused, k)
        results["dims"] = list(data.dims)
        results["k"] = k
        if writer_summary is not None:
            results["writer"] = writer_summary
        return results

    def markdown_lines(self, results: Mapping[str, Any]) -> list[str]:
        """The aggregate table the harness's Markdown report renders (owner batch 2)."""

        return b1_markdown_lines(results)


def b1_markdown_lines(results: Mapping[str, Any]) -> list[str]:
    if not results:
        return []
    k = results.get("k", B1_K)
    lines = [f"| Method | Model | View | recall@{k} | MAP@{k} |", "|---|---|---|---|---|"]
    for view, metrics in (results.get("bm25") or {}).items():
        lines.append(f"| BM25 | - | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
    for model, views in (results.get("embedding") or {}).items():
        for view, variants in views.items():
            for variant, metrics in variants.items():
                lines.append(f"| embedding ({variant}) | {model} | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
    for model, views in (results.get("hybrid") or {}).items():
        for view, metrics in views.items():
            lines.append(f"| hybrid | {model} | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
    writer = results.get("writer")
    if writer:
        cases = int(writer.get("written", 0)) + int(writer.get("cached", 0)) + int(writer.get("failed_cases", 0))
        settings = writer.get("settings") or {}
        lines += [
            "",
            f"Hypothesis writer: {writer.get('model')} (effort {settings.get('reasoning_effort') or 'default'}, "
            f"output budget {writer.get('output_tokens')} tokens); {writer.get('written')} written, "
            f"{writer.get('cached')} reused from this writer's cache.",
        ]
        if writer.get("failed_cases"):
            errors = ", ".join(f"{name} {count}" for name, count in sorted((writer.get("failed_by_error") or {}).items()))
            lines.append(
                f"{writer['failed_cases']} of {cases} hypothesis cases failed ({errors}); each counts as a miss in "
                "the hypothesis view. A rerun asks the writer again for them only."
            )
    return lines


# -- B3: vault replay -----------------------------------------------------------------------


@dataclass
class B3Data:
    subjects: list[Any]
    #: Labels the shortlist did NOT select: the only ones that measure it.
    pairs: list[dict[str, Any]]
    groups: Any
    models: tuple[str, ...]
    dims: tuple[int, ...] = ()
    #: The width the shortlist serves (``embedding.dimensions``): only a
    #: cutoff measured there is recommended for the config.
    serving_dims: int = 0
    #: Labels on pairs the shortlist nominated (the judge's), reported apart.
    shortlist_pairs: list[dict[str, Any]] = field(default_factory=list)
    #: Effective labels per nomination, over every label.
    labels_by_nomination: dict[str, int] = field(default_factory=dict)


def _episode_labels(build: Any, *, exclude_nominations: Sequence[str] = (), only_nominations: Sequence[str] = ()) -> list[dict[str, Any]]:
    """One effective verdict per episode pair (highest authority; a tie is
    ``different``), over the labels of the chosen nominations."""

    edges = [
        UnionEdge(
            left=row["left_episode"], right=row["right_episode"], verdict=row["verdict"],
            authority=AUTHORITY[row["judge"]], judge=row["judge"], source=row["source"], ref=row["ref"],
            occurred_at=row["occurred_at"], detail={"nominated_by": row.get("nominated_by")},
        )
        for row in build.labelled
        if row.get("left_episode") and row.get("right_episode") and row["left_episode"] != row["right_episode"]
        and row.get("nominated_by") not in exclude_nominations
        and (not only_nominations or row.get("nominated_by") in only_nominations)
    ]
    effective, _conflicts = effective_verdicts(edges)
    return [
        {"left": edge.left, "right": edge.right, "same": edge.verdict == "same", "judge": edge.judge,
         "source": edge.source, "nominated_by": edge.detail.get("nominated_by")}
        for edge in sorted(effective.values(), key=UnionEdge.order)
    ]


class B3Suite:
    name = "b3"
    description = "Vault replay: re-scores the vault's labelled same-cause pairs under candidate models; sets T1's blocking cutoff."

    def markdown_lines(self, results: Mapping[str, Any]) -> list[str]:
        """The aggregate table the harness's Markdown report renders (owner batch 2)."""

        return b3_markdown_lines(results)

    def load(self, vault: LoadedVault, request: BenchRequest) -> B3Data:
        sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
        repository = Repository.attach(sqlite_path, read_only=True)
        subjects = hypothesis_subjects(vault, repository)
        with closing(connect(sqlite_path, read_only=True)) as connection:
            build = compute_groups(connection)
        known = {subject.id for subject in subjects}

        def labels(**kwargs: Any) -> list[dict[str, Any]]:
            return [pair for pair in _episode_labels(build, **kwargs) if pair["left"] in known and pair["right"] in known]

        pairs = labels(exclude_nominations=(NOMINATED_BY_SHORTLIST,))
        nominated = labels(only_nominations=(NOMINATED_BY_SHORTLIST,))
        serving = int(vault.config.embedding.dimensions)
        return B3Data(subjects, pairs, build, tuple(request.models or (vault.config.embedding.model,)),
                      requested_dims(request, serving), serving, shortlist_pairs=nominated,
                      labels_by_nomination=dict(Counter(str(pair["nominated_by"]) for pair in labels())))

    def plan(self, vault: LoadedVault, data: B3Data, request: BenchRequest) -> dict[str, Any]:
        tokens = sum(estimate_tokens(subject.text) + 32 for subject in data.subjects)
        return {
            "hypotheses": len(data.subjects),
            # Labels independent of the shortlist (the ones that calibrate it).
            "labelled_pairs": len(data.pairs),
            "positives": sum(1 for pair in data.pairs if pair["same"]),
            "negatives": sum(1 for pair in data.pairs if not pair["same"]),
            "labels_by_judge": dict(Counter(pair["judge"] for pair in data.pairs)),
            "labels_by_nomination": dict(data.labels_by_nomination),
            "shortlist_nominated_pairs": len(data.shortlist_pairs),
            "models": list(data.models),
            "dims": list(data.dims),
            "serving_dims": data.serving_dims,
            "recipe": SAME_CAUSE.recipe,
            "task_prefix": SAME_CAUSE.task_prefix,
            "roles": {},
            "embedding": {model: {"calls": math.ceil(len(data.subjects) / EMBED_BATCH), "tokens": tokens} for model in data.models},
        }

    def run(self, data: B3Data, request: BenchRequest, ctx: Any) -> dict[str, Any]:
        by_id = {subject.id: subject for subject in data.subjects}
        texts = [subject.text for subject in data.subjects]
        results: dict[str, Any] = {"models": {}, "merge_replay": _merge_replay(data.groups)}
        widest = max(data.dims) if data.dims else data.serving_dims
        target_recall = float(getattr(request, "target_recall", DEFAULT_TARGET_RECALL))
        for model in data.models:
            # The production recipe and prefix (what the shortlist ranks),
            # embedded once at the widest width and truncated per width.
            vectors = ctx.vectors(model, list(texts), dims=widest, task_prefix=SAME_CAUSE.task_prefix)
            for dims in data.dims:
                label = model if len(data.dims) == 1 else f"{model}@{dims}"
                results["models"][label] = self._score(
                    data, by_id, vectors, texts, model=model, dims=dims, target_recall=target_recall,
                )
        results["dims"] = list(data.dims)
        results["serving_dims"] = data.serving_dims
        results["recipe"] = SAME_CAUSE.recipe
        results["task_prefix"] = SAME_CAUSE.task_prefix
        results["target_recall"] = target_recall
        return results

    def _score(self, data: B3Data, by_id: Mapping[str, Any], vectors: Mapping[str, np.ndarray], texts: list[str],
               *, model: str, dims: int, target_recall: float) -> dict[str, Any]:
        ids = [subject.id for subject in data.subjects]
        unit = _centred(_matrix(vectors, texts, dims)) if ids else np.zeros((0, dims))
        row_of = {identifier: index for index, identifier in enumerate(ids)}

        def score(left: str, right: str) -> float:
            return float(unit[row_of[left]] @ unit[row_of[right]])

        labels = [pair["same"] for pair in data.pairs]
        scores = [score(pair["left"], pair["right"]) for pair in data.pairs]

        def positive_ranks(pairs: Sequence[Mapping[str, Any]]) -> tuple[list[int | None], int]:
            ranks: list[int | None] = []
            out_of_scope = 0
            for pair in pairs:
                if not pair["same"]:
                    continue
                left, right = by_id[pair["left"]], by_id[pair["right"]]
                query, candidate = (left, right) if scope_of(right).attempt_order < scope_of(left).attempt_order else (right, left)
                if not compatible(query, candidate):
                    out_of_scope += 1
                    ranks.append(None)
                    continue
                pool = [
                    other for other in data.subjects
                    if other.id != query.id and compatible(query, other)
                    and scope_of(other).statement_normalized != scope_of(query).statement_normalized
                ]
                ordered = sorted(pool, key=lambda other: (-score(query.id, other.id), other.id))
                ranks.append(next((position for position, other in enumerate(ordered, start=1) if other.id == candidate.id), None))
            return ranks, out_of_scope

        # Only labels the shortlist did not select measure it (second review F3).
        ranks, out_of_scope = positive_ranks(data.pairs)
        recall_at = {f"recall@{k}": rank_metrics(ranks, k)[f"recall@{k}"] for k in (1, 2, 3, 5, 10)}
        nominated_ranks, _nominated_out = positive_ranks(data.shortlist_pairs)
        recommended_k = next(
            (k for k in range(1, 21) if (rank_metrics(ranks, k)[f"recall@{k}"] or 0.0) >= target_recall),
            None,
        )
        in_scope_labels = [label for label, pair in zip(labels, data.pairs, strict=True) if _in_scope(by_id, pair)]
        in_scope_scores = [value for value, pair in zip(scores, data.pairs, strict=True) if _in_scope(by_id, pair)]
        cutoff = blocking_cutoff(in_scope_scores, in_scope_labels, target_recall)
        provenance = {
            "model_id": model, "dims": dims, "recipe": SAME_CAUSE.recipe, "task_prefix": SAME_CAUSE.task_prefix,
            "target_recall": target_recall, "confirmed_matches": sum(labels),
        }
        backed = sum(labels) >= MIN_CONFIRMED_FOR_RECOMMENDATION
        if not backed:
            config = [
                f"# {sum(labels)} confirmed matches (< {MIN_CONFIRMED_FOR_RECOMMENDATION}): too few to set a "
                "cutoff; keep recurrence.blocking_cutoffs empty (top-k only) and rerun B3 later",
            ]
        elif dims != data.serving_dims:
            config = [
                f"# measured at {dims} dimensions; the shortlist serves {data.serving_dims} "
                "(embedding.dimensions), where this cutoff does not apply: rerun B3 at the serving width",
            ]
        else:
            config = _config_lines(provenance, cutoff.get("cutoff"), recommended_k)
        return {
            "auc": roc_auc(scores, labels),
            "positives": sum(labels),
            "positives_out_of_scope": out_of_scope,
            # The judge's verdicts: pairs the shortlist chose. Never used to
            # set top_k or the cutoff (their recall is ~1 by construction).
            "shortlist_nominated": {
                "pairs": len(data.shortlist_pairs),
                "positives": sum(1 for pair in data.shortlist_pairs if pair["same"]),
                "recall@3": rank_metrics(nominated_ranks, 3)["recall@3"],
                "note": "pairs the embedding shortlist nominated (same-cause judge verdicts); "
                "reported only: they cannot measure the shortlist's recall",
            },
            **recall_at,
            "recommended_top_k": recommended_k,
            "blocking_cutoff": {**cutoff, **provenance},
            "judge_load": _judge_load(data.subjects, score, recommended_k or 3, cutoff.get("cutoff")),
            "recommendation_backed": backed,
            "serving_width": dims == data.serving_dims,
            "config": config,
        }


def _in_scope(by_id: Mapping[str, Any], pair: Mapping[str, Any]) -> bool:
    left, right = by_id[pair["left"]], by_id[pair["right"]]
    query, candidate = (left, right) if scope_of(right).attempt_order < scope_of(left).attempt_order else (right, left)
    return compatible(query, candidate)


def _judge_load(subjects: Sequence[Any], score: Callable[[str, str], float], top_k: int, cutoff: float | None) -> dict[str, Any]:
    """Judge calls the live rule would make over the whole history."""

    pairs = 0
    above = 0
    for query in subjects:
        pool = [
            other for other in subjects
            if other.id != query.id and compatible(query, other)
            and scope_of(other).statement_normalized != scope_of(query).statement_normalized
        ]
        ranked = sorted((score(query.id, other.id) for other in pool), reverse=True)[:top_k]
        pairs += len(ranked)
        above += sum(1 for value in ranked if cutoff is None or value >= cutoff)
    return {"top_k": top_k, "pairs_top_k": pairs, "pairs_reaching_judge": above}


def _config_lines(provenance: Mapping[str, Any], cutoff: float | None, top_k: int | None) -> list[str]:
    """The [recurrence] lines; a cutoff always carries what it was measured on."""

    lines = ["[recurrence]"]
    if top_k is not None:
        lines.append(f"top_k = {top_k}")
    if cutoff is not None:
        entry = (
            f'cutoff = {cutoff}, dims = {int(provenance["dims"])}, recipe = "{provenance["recipe"]}", '
            f'task_prefix = "{provenance["task_prefix"]}", target_recall = {provenance["target_recall"]}, '
            f'confirmed_matches = {int(provenance["confirmed_matches"])}'
        )
        lines.append(f'blocking_cutoffs = {{ "{provenance["model_id"]}" = {{ {entry} }} }}')
    return lines


def _merge_replay(build: Any) -> dict[str, Any]:
    """Merge precision/recall when the union is replayed from a subset of sources (P6).

    Labels are the owner's verdicts only, held out of every replay so they
    never grade themselves. The same-cause judge's verdicts are never labels
    (second review F3): the judge only sees pairs the citations did NOT
    settle, so citation recall graded by them is near zero by construction.
    The report names how the labelled pairs were nominated: owner labels on
    pairs a diagnoser linked (M1's link review) favour ``exact_plus_citations``,
    so P6 is decided only on labels nominated by neither component.
    """

    labels = [
        edge for edge in build.edges
        if edge.judge == "owner" and edge.verdict in ("same", "different") and edge.left != edge.right
    ]
    if not labels:
        return {
            "label_judge": None, "labels": 0,
            "note": "no owner verdicts: P6 needs labels independent of the judge and of the citations; "
            "the judge's own verdicts are never used (it only sees pairs the citations left open)",
        }
    nominations = Counter(str((edge.detail or {}).get("nominated_by")) for edge in labels)
    neither = sum(count for name, count in nominations.items() if name not in (NOMINATED_BY_SHORTLIST, NOMINATED_BY_CITATION, NOMINATED_BY_M1_LINK))
    label_judge = "owner"
    variants = {
        "exact_only": [],
        "exact_plus_citations": [edge for edge in build.edges if edge.source == "citation"],
        "all_but_labels": [edge for edge in build.edges if edge.judge != label_judge],
    }
    out: dict[str, Any] = {
        "label_judge": label_judge, "labels": len(labels), "label_nominations": dict(nominations),
        "p6_decidable": neither > 0,
        "note": None if neither else "every owner label is on a pair a diagnoser linked: the replay favours "
        "exact_plus_citations; decide P6 only on labels nominated by neither component",
    }
    for name, edges in variants.items():
        result = union_with_refusals(build.classes, edges, order=build.class_order)
        merged = [edge for edge in labels if result.root_of.get(edge.left) == result.root_of.get(edge.right)]
        positives = [edge for edge in labels if edge.verdict == "same"]
        out[name] = {
            "merged_label_pairs": len(merged),
            "precision": round(sum(1 for edge in merged if edge.verdict == "same") / len(merged), 6) if merged else None,
            "recall": round(sum(1 for edge in positives if edge in merged) / len(positives), 6) if positives else None,
            "refused_unions": len(result.refused),
        }
    return out


SUITES: dict[str, Any] = {"b1": B1Suite(), "b3": B3Suite()}


def register_suites(registry: dict[str, Any], *, role_tasks: dict[str, str] | None = None) -> dict[str, Any]:
    """Register B1/B3 on Phase 5a's harness (call from the composition root).

    ``role_tasks`` is 5a's ``pf_calls.ROLE_TASKS``: B1's writer role joins it,
    so 5a's plan admission prices the role from its route and ``ctx.role``
    resolves it. Registration alone is not enough without it.
    """

    for name, suite in SUITES.items():
        registry.setdefault(name, suite)
    if role_tasks is not None:
        for role, task in ROLE_TASKS.items():
            role_tasks.setdefault(role, task)
    return registry


# -- the local runner (until Phase 5a merges) -----------------------------------------------


def run_bench(
    vault: LoadedVault,
    *,
    request: BenchRequest,
    caps: SpendCaps,
    price_per_million: float | None = None,
    embedding_price_per_million: float | None = None,
    cancelled: Callable[[], bool] | None = None,
    embedding_clients: Mapping[str, Any] | None = None,
    writer_client: Any = None,
) -> dict[str, Any]:
    suite = SUITES.get(request.suite)
    if suite is None:
        raise ValueError(f"Unknown suite {request.suite!r}; registered: {', '.join(sorted(SUITES))}")
    data = suite.load(vault, request)
    plan = suite.plan(vault, data, request)
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million, config=vault.config)
    report: dict[str, Any] = {
        "status": "dry_run" if request.dry_run else "pending",
        "suite": suite.name,
        "description": suite.description,
        "harness_contract": HARNESS_CONTRACT,
        "plan": plan,
        "caps": caps.as_dict(),
        "manifest": {
            "algorithm_version": vault.config.algorithms.algorithm_version,
            "embedding_model": vault.config.embedding.model,
            "benchmark": getattr(data, "manifest", None),
        },
    }
    try:
        estimate = plan_admission(
            vault, plan, spend, writer_client=writer_client, embedding_price_per_million=embedding_price_per_million,
        )
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    report["estimate"] = estimate
    try:
        spend.check(estimate.pop("_total"))
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    if request.dry_run:
        return report
    output = request.output_dir
    output.mkdir(parents=True, exist_ok=True)
    ctx = BenchContext(
        vault, spend, output_dir=output, embedding_clients=embedding_clients, writer_client=writer_client,
        embedding_price=embedding_price_per_million,
    )
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    try:
        if sqlite_path.exists():
            # Every admitted call is observed by the spend collector, which
            # forwards it to the vault's model_call_receipts.
            receipts = Repository(sqlite_path)
            spend.collector.sink = lambda action, event: receipts.record_model_event(
                action, event, owner_kind="recurrence_benchmark", owner_id=suite.name
            )
            with record_model_calls(receipts, owner_kind="recurrence_benchmark", owner_id=suite.name):
                report["results"] = suite.run(data, request, ctx)
        else:
            report["results"] = suite.run(data, request, ctx)
        report["status"] = "complete"
    except (AIInterrupted, KeyboardInterrupt):
        report["status"] = "cancelled"
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
    except AIProviderUnavailable as exc:
        report.update(status="provider_failed", reason=str(exc)[:300])
    report["spend"] = spend.summary()
    identity = content_key({"suite": suite.name, "plan": plan})[:16]
    report["report_files"] = [f"{suite.name}-{identity}.json", f"{suite.name}-{identity}.md"]
    (output / report["report_files"][0]).write_text(json.dumps(report, sort_keys=True, indent=2, default=str), encoding="utf-8")
    (output / report["report_files"][1]).write_text(render_markdown(report), encoding="utf-8")
    return report


def plan_admission(
    vault: LoadedVault,
    plan: Mapping[str, Any],
    spend: ReviewSpend,
    *,
    writer_client: Any = None,
    embedding_price_per_million: float | None = None,
) -> dict[str, Any]:
    """The whole plan's estimate on ``spend``'s routes (no client built, nothing sent).

    Each LLM role is classified from its configured route (or the injected
    client): a subscription route (Codex) counts its calls only and its cost
    is ``estimated_only``; a metered route counts its input-plus-output tokens
    at the owner's price, and an unknown price fails closed at admission.
    Embeddings are metered at the published or owner price (unknown: refused
    here). ``_total`` is the combined estimate to check.
    """

    from learnloop.diagnosis.recurrence.backlog import route_profile

    estimates: list[SpendEstimate] = []
    billing: dict[str, str] = {}
    subscription = {"calls": 0, "tokens": 0}
    llm_calls = llm_tokens = 0
    for role, info in (plan.get("roles") or {}).items():
        calls, tokens = int(info.get("calls", 0)), int(info.get("tokens", 0))
        llm_calls += calls
        llm_tokens += tokens
        if writer_client is not None:
            route = spend.register(role, writer_client)
        else:
            profile = route_profile(vault, ROLE_TASKS.get(role, role))
            route = spend.register_profile(role, provider=profile["provider"], model=profile["model"],
                                           subscription=bool(profile["subscription"]), max_tokens=profile["max_tokens"])
        billing[role] = route.billing
        if route.billing == "subscription":
            subscription["calls"] += calls
            subscription["tokens"] += tokens
        # ``tokens`` already holds input plus output.
        estimates.append(spend.estimate(role, calls=calls, input_tokens=tokens, output_tokens=0))
    embed_calls = embed_tokens = 0
    for model, entry in (plan.get("embedding") or {}).items():
        calls, tokens = int(entry.get("calls", 0)), int(entry.get("tokens", 0))
        if not calls:
            continue
        price = embedding_price_per_million if embedding_price_per_million is not None else EMBEDDING_PRICES_PER_MILLION.get(model)
        if price is None:
            raise SpendLimitExceeded(f"Unknown embedding price for {model}: pass --embedding-price-per-million")
        route_name = f"{EMBEDDING_ROUTE}:{model}"
        source = "owner_override" if embedding_price_per_million is not None else "known"
        spend.routes[route_name] = RouteInfo(route_name, "embedding", model, "metered", price, source, 0)
        billing[route_name] = "metered"
        embed_calls += calls
        embed_tokens += tokens
        estimates.append(spend.estimate(route_name, calls=calls, input_tokens=tokens, output_tokens=0))
    total = sum_estimates(*estimates) if estimates else SpendEstimate(estimated_usd=0.0)
    return {
        "llm_calls": llm_calls,
        "llm_tokens": llm_tokens,
        "embedding_calls": embed_calls,
        "embedding_tokens": embed_tokens,
        "metered": {"calls": total.calls - subscription["calls"], "tokens": total.total_tokens,
                    "estimated_usd": total.estimated_usd, "cost_basis": "metered_caps"},
        "subscription": {**subscription, "cost_basis": "estimated_only"},
        "billing": billing,
        "_total": total,
    }


def b3_markdown_lines(results: Mapping[str, Any]) -> list[str]:
    if not results:
        return []
    lines = ["| Model | AUC | recall@1 | recall@3 | recall@10 | top_k | cutoff | pairs to judge |", "|---|---|---|---|---|---|---|---|"]
    for model, metrics in (results.get("models") or {}).items():
        cutoff = metrics["blocking_cutoff"]
        lines.append(
            f"| {model} | {metrics['auc']} | {metrics['recall@1']} | {metrics['recall@3']} | {metrics['recall@10']} | "
            f"{metrics['recommended_top_k']} | {cutoff.get('cutoff')} | {metrics['judge_load']['pairs_reaching_judge']} |"
        )
    lines += ["", "Recommended config (per model; recall-oriented, R4):", ""]
    for _model, metrics in (results.get("models") or {}).items():
        lines += ["```toml", *metrics["config"], "```", ""]
    lines += ["Merge replay:", "", "```json", json.dumps(results.get("merge_replay"), indent=2, sort_keys=True), "```"]
    return lines


def render_markdown(report: Mapping[str, Any]) -> str:
    """The local runner's report (the harness renders through ``markdown_lines``)."""

    lines = [f"# Recurrence benchmark {report['suite']}", "", f"Status: {report['status']}.", ""]
    results = report.get("results") or {}
    if report["suite"] == "b1":
        lines += b1_markdown_lines(results)
    elif report["suite"] == "b3":
        lines += b3_markdown_lines(results)
    lines += ["", "Aggregates only; every call is in model_call_receipts."]
    return "\n".join(lines) + "\n"


__all__ = [
    "B1_DEFAULT_WRITER_OUTPUT_TOKENS",
    "B1_WRITER_ROLE",
    "B1Suite",
    "B3Suite",
    "BenchContext",
    "BenchRequest",
    "SUITES",
    "VectorCache",
    "b1_markdown_lines",
    "b3_markdown_lines",
    "blocking_cutoff",
    "configured_writer",
    "load_eedi",
    "plan_admission",
    "rank_metrics",
    "register_suites",
    "requested_dims",
    "requested_writer_output_tokens",
    "roc_auc",
    "run_bench",
    "writer_identity",
    "writer_tokens",
]
