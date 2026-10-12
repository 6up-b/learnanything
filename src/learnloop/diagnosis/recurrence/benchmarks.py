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
  hybrid (reciprocal rank). Metrics: recall@25 and MAP@25.
* **B3**: the vault's own labelled hypothesis pairs (owner verdicts imported
  from M1, the same-cause judge, validated diagnoser citations, card taps),
  re-scored under each candidate model: AUC, recall@k of confirmed matches
  under the production shortlist rule, the recall-oriented blocking cutoff and
  its judge load (this sets ``recurrence.blocking_cutoffs`` and ``top_k``),
  and merge precision/recall when the groups are replayed from a subset of
  sources. No LLM call; embeddings only. It embeds the PRODUCTION recipe
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
from pydantic import Field

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key, record_model_calls
from learnloop.ai.schemas import WireModel
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.ai.transport import execute_structured_operation, render_structured_prompt
from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.diagnosis.offline_review.spend import ReviewSpend, RouteInfo
from learnloop.diagnosis.recurrence.judging import estimate_tokens, sum_estimates
from learnloop.diagnosis.recurrence.kind import SAME_CAUSE, compatible, hypothesis_subjects, scope_of
from learnloop.matching.union import UnionEdge, effective_verdicts, union_with_refusals
from learnloop.substrate.recurrence_groups import AUTHORITY, compute_groups
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
WRITER_OUTPUT_TOKENS = 300
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

    def complete(self, role: str, prompt: str, result_model: type[WireModel], purpose: str) -> Any:
        if self._writer is None:
            from learnloop.ai.routing import ready_client_for_task

            task = ROLE_TASKS.get(role, role)
            resolved = ready_client_for_task(self.vault.root, self.vault.config, task)  # type: ignore[arg-type]
            if not resolved.ready:
                raise AIProviderUnavailable(f"the {task} route ({role}) is not ready")
            self._writer = resolved.client
        if role not in self._registered:
            # Billed as the client actually built (the plan classified it from config).
            self.spend.register(role, self._writer)
            self._registered.add(role)
        with self.spend.collector.observing():
            with self.spend.request(role, purpose, input_tokens=estimate_tokens(prompt)):
                return execute_structured_operation(
                    self._writer, purpose=purpose, prompt=prompt, result_model=result_model, isolated=True
                )


def _complete(ctx: Any, role: str, prompt: str, result_model: type[WireModel], purpose: str, prompt_version: str) -> Any:
    """Through the local context, or Phase 5a's PF caller (``ctx.role`` + ``ctx.caller.call``)."""

    if hasattr(ctx, "complete"):
        return ctx.complete(role, prompt, result_model, purpose)
    entry = ctx.role(role)[0]
    return ctx.caller.call(entry, prompt=prompt, prompt_version=prompt_version, result_model=result_model,
                           output_tokens=WRITER_OUTPUT_TOKENS).result


def writer_tokens(prompt: str, result_model: type[WireModel]) -> int:
    """One writer call's input-plus-output bound, as 5a's harness counts it."""

    schema = len(json.dumps(result_model.model_json_schema()).encode("utf-8"))
    return len(prompt.encode("utf-8")) + schema + 512 + WRITER_OUTPUT_TOKENS


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
        path = self._hypothesis_cache(request)
        if not path.exists():
            return {}
        out: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            out[str(row["key"])] = str(row["misconception"])
        return out

    @staticmethod
    def _case_key(case: Mapping[str, Any]) -> str:
        return content_key({"prompt_version": B1_PROMPT_VERSION, "case": dict(case)})

    def plan(self, vault: LoadedVault, data: B1Data, request: BenchRequest) -> dict[str, Any]:
        cached = self._cached_hypotheses(request) if "hypothesis" in data.views else {}
        to_write = [case for case in data.cases if self._case_key(case) not in cached] if "hypothesis" in data.views else []
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
            "roles": {
                B1_WRITER_ROLE: {
                    "calls": len(to_write),
                    # Input plus output of every call not cached yet.
                    "tokens": sum(writer_tokens(b1_prompt(case), MisconceptionHypothesis) for case in to_write),
                    "cached": len(data.cases) - len(to_write) if "hypothesis" in data.views else 0,
                }
            },
            "embedding": {model: {"calls": requests, "tokens": per_model_tokens} for model in data.models},
            "note": "embedding calls are an upper bound; texts already in the output directory's cache are not sent",
        }

    def run(self, data: B1Data, request: BenchRequest, ctx: Any) -> dict[str, Any]:
        hypotheses: dict[str, str] = {}
        if "hypothesis" in data.views:
            cached = self._cached_hypotheses(request)
            path = self._hypothesis_cache(request)
            path.parent.mkdir(parents=True, exist_ok=True)
            for case in data.cases:
                key = self._case_key(case)
                if key not in cached:
                    result = _complete(ctx, B1_WRITER_ROLE, b1_prompt(case), MisconceptionHypothesis, B1_WRITER_PURPOSE, B1_PROMPT_VERSION)
                    cached[key] = str(result.misconception).strip()
                    with path.open("a", encoding="utf-8") as handle:
                        handle.write(json.dumps({"key": key, "misconception": cached[key]}) + "\n")
                hypotheses[case["id"]] = cached[key]
        ids = [identifier for identifier, _name in data.misconceptions]
        names = [name for _identifier, name in data.misconceptions]
        position = {identifier: index for index, identifier in enumerate(ids)}
        k = B1_K
        bm25 = BM25(names)
        queries = {
            view: [raw_query(case) if view == "raw" else hypotheses.get(case["id"], "") for case in data.cases]
            for view in data.views
        }
        gold = [position[case["gold"]] for case in data.cases]
        results: dict[str, Any] = {"bm25": {}, "embedding": {}, "hybrid": {}}
        bm25_ranks: dict[str, list[np.ndarray]] = {}
        for view, texts in queries.items():
            scored = [bm25.scores(text) for text in texts]
            bm25_ranks[view] = [_ranks_from_order(scores) for scores in scored]
            results["bm25"][view] = rank_metrics(
                [_rank_of(scores, gold_index) for scores, gold_index in zip(scored, gold, strict=True)], k
            )
        widest = max(data.dims)
        for model in data.models:
            # Embedded once at the widest width; narrower widths are MRL truncations.
            corpus_vectors = ctx.vectors(model, list(names), dims=widest, task_prefix="retrieval-document")
            query_vectors = {
                view: ctx.vectors(model, list(texts), dims=widest, task_prefix="retrieval-query")
                for view, texts in queries.items()
            }
            for dims in data.dims:
                label = model if len(data.dims) == 1 else f"{model}@{dims}"
                corpus = _matrix(corpus_vectors, names, dims)
                corpus_centred = _centred(corpus)
                for view, texts in queries.items():
                    matrix = _matrix(query_vectors[view], texts, dims)
                    for variant, (left, right) in {"cosine": (matrix, corpus), "centred": (_centred(matrix), corpus_centred)}.items():
                        scores = left @ right.T
                        ranks = [_rank_of(row, gold_index) for row, gold_index in zip(scores, gold, strict=True)]
                        results["embedding"].setdefault(label, {}).setdefault(view, {})[variant] = rank_metrics(ranks, k)
                        if variant == "centred":
                            fused = []
                            for row, bm, gold_index in zip(scores, bm25_ranks[view], gold, strict=True):
                                emb_rank = _ranks_from_order(row)
                                rrf = 1.0 / (60 + emb_rank) + 1.0 / (60 + bm)
                                fused.append(_rank_of(rrf, gold_index))
                            results["hybrid"].setdefault(label, {})[view] = rank_metrics(fused, k)
        results["dims"] = list(data.dims)
        results["k"] = k
        return results


# -- B3: vault replay -----------------------------------------------------------------------


@dataclass
class B3Data:
    subjects: list[Any]
    pairs: list[dict[str, Any]]
    groups: Any
    models: tuple[str, ...]
    dims: tuple[int, ...] = ()
    #: The width the shortlist serves (``embedding.dimensions``): only a
    #: cutoff measured there is recommended for the config.
    serving_dims: int = 0


def _episode_labels(build: Any) -> list[dict[str, Any]]:
    """One effective verdict per episode pair (highest authority, latest)."""

    edges = [
        UnionEdge(
            left=row["left_episode"], right=row["right_episode"], verdict=row["verdict"],
            authority=AUTHORITY[row["judge"]], judge=row["judge"], source=row["source"], ref=row["ref"],
            occurred_at=row["occurred_at"],
        )
        for row in build.labelled
        if row.get("left_episode") and row.get("right_episode") and row["left_episode"] != row["right_episode"]
    ]
    effective, _conflicts = effective_verdicts(edges)
    return [
        {"left": edge.left, "right": edge.right, "same": edge.verdict == "same", "judge": edge.judge, "source": edge.source}
        for edge in sorted(effective.values(), key=UnionEdge.order)
    ]


class B3Suite:
    name = "b3"
    description = "Vault replay: re-scores the vault's labelled same-cause pairs under candidate models; sets T1's blocking cutoff."

    def load(self, vault: LoadedVault, request: BenchRequest) -> B3Data:
        sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
        repository = Repository.attach(sqlite_path, read_only=True)
        subjects = hypothesis_subjects(vault, repository)
        with closing(connect(sqlite_path, read_only=True)) as connection:
            build = compute_groups(connection)
        known = {subject.id for subject in subjects}
        pairs = [pair for pair in _episode_labels(build) if pair["left"] in known and pair["right"] in known]
        serving = int(vault.config.embedding.dimensions)
        return B3Data(subjects, pairs, build, tuple(request.models or (vault.config.embedding.model,)),
                      requested_dims(request, serving), serving)

    def plan(self, vault: LoadedVault, data: B3Data, request: BenchRequest) -> dict[str, Any]:
        tokens = sum(estimate_tokens(subject.text) + 32 for subject in data.subjects)
        return {
            "hypotheses": len(data.subjects),
            "labelled_pairs": len(data.pairs),
            "positives": sum(1 for pair in data.pairs if pair["same"]),
            "negatives": sum(1 for pair in data.pairs if not pair["same"]),
            "labels_by_judge": dict(Counter(pair["judge"] for pair in data.pairs)),
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
        ranks: list[int | None] = []
        out_of_scope = 0
        for pair in data.pairs:
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
        recall_at = {f"recall@{k}": rank_metrics(ranks, k)[f"recall@{k}"] for k in (1, 2, 3, 5, 10)}
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
    """Merge precision/recall when the union is replayed from a subset of sources.

    Labels are the owner's verdicts when there are any, else the judge's; the
    label source is held out of every replay so it never grades itself.
    """

    owner = [edge for edge in build.edges if edge.judge == "owner"]
    label_judge = "owner" if owner else "llm"
    labels = [edge for edge in build.edges if edge.judge == label_judge and edge.verdict in ("same", "different") and edge.left != edge.right]
    variants = {
        "exact_only": [],
        "exact_plus_citations": [edge for edge in build.edges if edge.source == "citation"],
        "all_but_labels": [edge for edge in build.edges if edge.judge != label_judge],
    }
    out: dict[str, Any] = {"label_judge": label_judge, "labels": len(labels)}
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
    spend = ReviewSpend(caps, cancelled=cancelled, price_per_million=price_per_million)
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


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [f"# Recurrence benchmark {report['suite']}", "", f"Status: {report['status']}.", ""]
    results = report.get("results") or {}
    if report["suite"] == "b1" and results:
        k = results.get("k", 25)
        lines += [f"| Method | Model | View | recall@{k} | MAP@{k} |", "|---|---|---|---|---|"]
        for view, metrics in (results.get("bm25") or {}).items():
            lines.append(f"| BM25 | - | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
        for model, views in (results.get("embedding") or {}).items():
            for view, variants in views.items():
                for variant, metrics in variants.items():
                    lines.append(f"| embedding ({variant}) | {model} | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
        for model, views in (results.get("hybrid") or {}).items():
            for view, metrics in views.items():
                lines.append(f"| hybrid | {model} | {view} | {metrics.get(f'recall@{k}')} | {metrics.get(f'map@{k}')} |")
    elif report["suite"] == "b3" and results:
        lines += ["| Model | AUC | recall@1 | recall@3 | recall@10 | top_k | cutoff | pairs to judge |", "|---|---|---|---|---|---|---|---|"]
        for model, metrics in (results.get("models") or {}).items():
            cutoff = metrics["blocking_cutoff"]
            lines.append(
                f"| {model} | {metrics['auc']} | {metrics['recall@1']} | {metrics['recall@3']} | {metrics['recall@10']} | "
                f"{metrics['recommended_top_k']} | {cutoff.get('cutoff')} | {metrics['judge_load']['pairs_reaching_judge']} |"
            )
        lines += ["", "Recommended config (per model; recall-oriented, R4):", ""]
        for model, metrics in (results.get("models") or {}).items():
            lines += ["```toml", *metrics["config"], "```", ""]
        lines += ["Merge replay:", "", "```json", json.dumps(results.get("merge_replay"), indent=2, sort_keys=True), "```"]
    lines += ["", "Aggregates only; every call is in model_call_receipts."]
    return "\n".join(lines) + "\n"


__all__ = [
    "B1_WRITER_ROLE",
    "B1Suite",
    "B3Suite",
    "BenchContext",
    "BenchRequest",
    "SUITES",
    "VectorCache",
    "blocking_cutoff",
    "load_eedi",
    "plan_admission",
    "rank_metrics",
    "register_suites",
    "requested_dims",
    "roc_auc",
    "run_bench",
]
