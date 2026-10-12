"""`learnloop embeddings compare`: the shared benchmark harness (Slice 2 §4, §5.5, §5.6).

PF builds it first. Every benchmark is a registered **suite** with the same
contract, so later tracks add a suite rather than a harness: T1 adds B1/B3,
T6 adds B4 (multimodal pages), and Slice 2 T6 reuses the B2 machinery.

Suite contract (``CompareSuite``):

* ``name`` / ``description``;
* ``load(request) -> SuiteData``: read and validate inputs (a benchmark
  directory with ``manifest.json`` naming every source's ``name``, ``version``
  and ``licence``, or vault content);
* ``plan(data, request) -> dict``: calls and tokens per role, no requests;
* ``run(data, request, ctx) -> dict``: the aggregate-only report body.

Shared services in ``CompareContext``: the PF caller (spend admission, receipts,
checkpoints, ``judgment_ledger``), PF role clients, an embedding vector cache in
the output directory (content-addressed, resumable, never in the vault) and
metric helpers (ROC-AUC, recall-oriented blocking cutoffs, binary metrics).

Registered suites:

* ``b2`` — isomorph / near-duplicate (GSM-Symbolic positives, MATH-Perturb hard
  negatives, MELD equivalences). Views: ``stem`` and ``skeleton`` embeddings
  (MRL dimension sweep, mean-centered cosine as retrieval uses), the symbolic
  ``fingerprint`` and the production ``judge``. It derives the recall-oriented
  blocking cutoff per ``(model_id, record_kind, view, dims)`` (R4); cutoffs are
  never hand-set and are re-derived when the model changes.
* ``valid_alternative`` — the per-family regression suite of canonical and
  valid-alternative traces (frontier-generated, CAS-checked), graded by the
  learner-blind grader; reports valid-alternative false rejection. Only
  synthetic traces reach ``BlindGradingContext``; no learner answer or grade.

Everything reported is aggregate (counts, metrics, model ids); inputs are never
echoed. A dry run constructs no client and sends nothing.
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from learnloop.ai.errors import AIInterrupted, AIProviderUnavailable
from learnloop.ai.execution import content_key
from learnloop.ai.spend import SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.attempts.blind_grading import (
    BLIND_GRADING_PROMPT_VERSION, BlindGradingProposal, blind_grading_context, blind_grading_prompt,
)
from learnloop.content.authoring import pf_contracts as C
from learnloop.content.authoring.pf_sandbox import (
    equivalence_confirmations, run_equivalence_checks, sandbox_available,
)
from learnloop.db.repositories import Repository
from learnloop.ids import new_ulid
from learnloop.ops.pf_calls import (
    PFCaller, PFUnavailable, RoleClient, estimate_tokens, planned_role_clients, resolve_role_clients,
)
from learnloop.substrate.item_fingerprints import final_answer_text, fingerprint_keys, shared_keys
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

HARNESS_VERSION = "embeddings-compare-v1"
DEFAULT_TARGET_RECALL = 0.95
EMBED_BATCH = 32
# The published estimate for the default model (Slice 1 §9.1), not a quote.
EMBEDDING_PRICES_PER_MILLION = {"qwen/qwen3-embedding-8b": 0.01}


# -- request and context ------------------------------------------------------------

@dataclass(frozen=True)
class CompareRequest:
    suite: str
    output_dir: Path
    benchmark_dir: Path | None = None
    models: tuple[str, ...] = ()
    dims: tuple[int, ...] = ()
    views: tuple[str, ...] = ()
    family_ids: tuple[str, ...] = ()
    target_recall: float = DEFAULT_TARGET_RECALL
    max_cases: int | None = None
    alternatives: int = 2
    max_items: int = 20
    dry_run: bool = False


class CompareContext:
    def __init__(self, vault: LoadedVault, caller: PFCaller, *, clients: Mapping[str, Any] | None,
                 embedding_clients: Mapping[str, Any] | None, embedding_price: float | None,
                 output_dir: Path) -> None:
        self.vault = vault
        self.caller = caller
        self.injected = dict(clients or {})
        self.embedding_injected = dict(embedding_clients or {})
        self.embedding_price = embedding_price
        self.output_dir = output_dir
        self._roles: dict[str, list[RoleClient]] = {}
        self._embedders: dict[tuple[str, int], Any] = {}

    def role(self, name: str) -> list[RoleClient]:
        if name not in self._roles:
            self._roles[name] = resolve_role_clients(self.vault, name, injected=self.injected.get(name))
        return self._roles[name]

    def embedder(self, model: str, dims: int) -> Any:
        key = (model, dims)
        if key not in self._embedders:
            if model in self.embedding_injected:
                self._embedders[key] = self.embedding_injected[model]
            else:
                self._embedders[key] = _embedding_client(self.vault, model, dims)
        return self._embedders[key]

    def price_for(self, model: str) -> float | None:
        return self.embedding_price if self.embedding_price is not None else EMBEDDING_PRICES_PER_MILLION.get(model)

    def embedding_config(self, model: str) -> dict[str, Any]:
        """What besides model, width and prefix identifies the vectors (cache key)."""
        if model in self.embedding_injected:
            client = self.embedding_injected[model]
            return {"injected": type(client).__name__, "model_id": getattr(client, "model_id", model)}
        route = self.vault.config.ai.routing.embedding
        profile = self.vault.config.ai.providers.get(route or "")
        settings = profile.model_dump(mode="json", exclude={"model", "dimensions"}) if profile is not None else None
        return {"route": route, "profile": settings}

    def vectors(self, model: str, texts: list[str], *, dims: int,
                task_prefix: str = "similarity") -> dict[str, np.ndarray]:
        """Unit vectors of width ``dims`` by text, embedding only uncached texts.

        The cache is keyed by model, task prefix, requested width and embedding
        configuration, so a later sweep at another width never reads vectors
        embedded at this one; a provider returning narrower vectors than
        requested is refused before anything is cached.
        """
        cache = VectorCache(self.output_dir / "cache", model, task_prefix, dims=dims,
                            config=self.embedding_config(model))
        missing = [text for text in dict.fromkeys(texts) if cache.get(text) is None]
        if missing:
            price = self.price_for(model)
            if price is None:
                raise SpendLimitExceeded(
                    f"Unknown embedding price for {model}: pass --embedding-price-per-million")
            client = self.embedder(model, dims)
            for start in range(0, len(missing), EMBED_BATCH):
                batch = missing[start:start + EMBED_BATCH]
                vectors = self.caller.embed(client, batch, task_prefix=task_prefix, price_per_million=price)
                widths = {len(vector) for vector in vectors}
                if any(width < dims for width in widths):
                    raise PFUnavailable(f"{model} returned {min(widths)}-wide vectors for a {dims}-dimension request")
                cache.put_many(batch, vectors)
        return {text: cache.get(text) for text in texts}


def _embedding_client(vault: LoadedVault, model: str, dims: int) -> Any:
    from learnloop.ai.providers.openai_embedding import OpenAIEmbeddingProviderClient

    if not vault.config.embedding.enabled:
        raise PFUnavailable("Embeddings are disabled; set embedding.enabled = true on the copy you benchmark")
    route = vault.config.ai.routing.embedding
    profile = vault.config.ai.providers.get(route or "")
    if profile is None or profile.type != "openai_embedding":
        raise PFUnavailable("ai.routing.embedding must name an openai_embedding profile")
    return OpenAIEmbeddingProviderClient(route, profile.model_copy(update={"model": model, "dimensions": dims}))


class VectorCache:
    """Content-addressed float32 unit vectors in the output directory, not the vault.

    One cache per (model, task prefix, requested width, embedding config): the
    width and config are part of the directory key and are validated on load.
    """

    def __init__(self, root: Path, model: str, task_prefix: str, *, dims: int,
                 config: Mapping[str, Any] | None = None) -> None:
        self.identity = {"model": model, "task_prefix": task_prefix, "dims": int(dims),
                         "config": dict(config or {})}
        slug = content_key(self.identity)[:16]
        self.directory = root / slug
        self.index_path = self.directory / "index.json"
        self.vectors_path = self.directory / "vectors.npy"
        self.model = model
        self.dims = int(dims)
        self._index: dict[str, int] = {}
        self._vectors: np.ndarray | None = None
        if self.index_path.exists() and self.vectors_path.exists():
            stored = json.loads(self.index_path.read_text(encoding="utf-8"))
            vectors = np.load(self.vectors_path)
            if stored.get("identity") == self.identity and vectors.ndim == 2 and vectors.shape[1] >= self.dims:
                self._index = stored["index"]
                self._vectors = vectors

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> np.ndarray | None:
        position = self._index.get(self.key(text))
        return None if position is None or self._vectors is None else self._vectors[position]

    def put_many(self, texts: list[str], vectors: list[list[float]]) -> None:
        array = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(array, axis=1, keepdims=True)
        array = array / np.where(norms == 0, 1, norms)
        if self._vectors is not None and self._vectors.shape[1] != array.shape[1]:
            raise ValueError("Cached vectors have a different width for this model")
        start = 0 if self._vectors is None else len(self._vectors)
        self._vectors = array if self._vectors is None else np.vstack([self._vectors, array])
        for offset, text in enumerate(texts):
            self._index[self.key(text)] = start + offset
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = self.vectors_path.with_suffix(".tmp.npy")
        np.save(temporary, self._vectors)
        os.replace(temporary, self.vectors_path)
        index_tmp = self.index_path.with_suffix(".tmp")
        index_tmp.write_text(json.dumps({"model": self.model, "identity": self.identity, "index": self._index}),
                             encoding="utf-8")
        os.replace(index_tmp, self.index_path)


# -- metrics -------------------------------------------------------------------------

def roc_auc(scores: list[float], labels: list[bool]) -> float | None:
    positives = [score for score, label in zip(scores, labels) if label]
    negatives = [score for score, label in zip(scores, labels) if not label]
    if not positives or not negatives:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return round(wins / (len(positives) * len(negatives)), 6)


def blocking_cutoff(scores: list[float], labels: list[bool], target_recall: float) -> dict[str, Any]:
    """The highest cutoff whose recall on positives reaches the target (R4)."""
    positives = sorted((score for score, label in zip(scores, labels) if label), reverse=True)
    negatives = [score for score, label in zip(scores, labels) if not label]
    if not positives:
        return {"cutoff": None, "recall": None, "judge_load": None, "positives": 0}
    needed = max(1, math.ceil(target_recall * len(positives)))
    cutoff = positives[needed - 1]
    recall = sum(1 for score in positives if score >= cutoff) / len(positives)
    load = (sum(1 for score in negatives if score >= cutoff) / len(negatives)) if negatives else None
    return {"cutoff": round(float(cutoff), 6), "recall": round(recall, 6),
            "judge_load": round(load, 6) if load is not None else None,
            "positives": len(positives), "negatives": len(negatives)}


def binary_metrics(predictions: list[bool], labels: list[bool]) -> dict[str, Any]:
    tp = sum(1 for p, y in zip(predictions, labels) if p and y)
    fp = sum(1 for p, y in zip(predictions, labels) if p and not y)
    fn = sum(1 for p, y in zip(predictions, labels) if not p and y)
    tn = sum(1 for p, y in zip(predictions, labels) if not p and not y)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 6) if precision is not None else None,
            "recall": round(recall, 6) if recall is not None else None,
            "accuracy": round((tp + tn) / len(labels), 6) if labels else None}


def centered_cosines(pairs: list[tuple[np.ndarray, np.ndarray]], dims: int) -> list[float]:
    """Mean-centered cosine on MRL-truncated vectors, as retrieval scores them."""
    if not pairs:
        return []
    if any(len(vector) < dims for pair in pairs for vector in pair):
        raise ValueError(f"vectors narrower than the requested {dims} dimensions cannot be truncated to it")
    stacked = np.vstack([vector[:dims] for pair in pairs for vector in pair]).astype(np.float64)
    stacked /= np.where(np.linalg.norm(stacked, axis=1, keepdims=True) == 0, 1,
                        np.linalg.norm(stacked, axis=1, keepdims=True))
    centered = stacked - stacked.mean(axis=0, keepdims=True)
    norms = np.linalg.norm(centered, axis=1)
    scores = []
    for index in range(len(pairs)):
        left, right = centered[2 * index], centered[2 * index + 1]
        denominator = norms[2 * index] * norms[2 * index + 1]
        scores.append(float(left @ right / denominator) if denominator else 0.0)
    return scores


# -- suites --------------------------------------------------------------------------

class CompareSuite(Protocol):
    name: str
    description: str

    def load(self, vault: LoadedVault, request: CompareRequest) -> Any: ...

    def plan(self, vault: LoadedVault, data: Any, request: CompareRequest) -> dict[str, Any]: ...

    def run(self, data: Any, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]: ...


def _read_manifest(directory: Path) -> dict[str, Any]:
    path = directory / "manifest.json"
    if not path.is_file():
        raise ValueError(f"{directory} has no manifest.json (source, version and licence per source)")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources or not all(
            isinstance(source, dict) and all(str(source.get(key) or "").strip()
                                             for key in ("name", "version", "licence"))
            for source in sources):
        raise ValueError("manifest.json must list sources, each with name, version and licence")
    return manifest


@dataclass
class B2Case:
    id: str
    left: dict[str, Any]
    right: dict[str, Any]
    positive: bool
    category: str
    domain: str


@dataclass
class B2Data:
    manifest: dict[str, Any]
    cases: list[B2Case]
    views: tuple[str, ...]
    models: tuple[str, ...]
    dims: tuple[int, ...]


class B2Suite:
    name = "b2"
    description = "Isomorph / near-duplicate benchmark; sets PF's per-view blocking cutoffs."
    VIEWS = ("stem", "skeleton", "fingerprint", "judge")

    def load(self, vault: LoadedVault, request: CompareRequest) -> B2Data:
        if request.benchmark_dir is None:
            raise ValueError("b2 needs --benchmark DIR with manifest.json and pairs.jsonl")
        manifest = _read_manifest(request.benchmark_dir)
        cases = []
        path = request.benchmark_dir / "pairs.jsonl"
        if not path.is_file():
            raise ValueError(f"{request.benchmark_dir} has no pairs.jsonl")
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            label = row.get("label")
            if label not in {"positive", "negative"}:
                raise ValueError(f"pairs.jsonl line {number}: label must be positive or negative")
            for side in ("left", "right"):
                if not isinstance(row.get(side), dict) or not str(row[side].get("stem") or "").strip():
                    raise ValueError(f"pairs.jsonl line {number}: {side}.stem is required")
            cases.append(B2Case(id=str(row.get("id") or number), left=row["left"], right=row["right"],
                                positive=label == "positive", category=str(row.get("category") or "unspecified"),
                                domain=str(row.get("domain") or "unspecified")))
        if request.max_cases is not None:
            cases = cases[:request.max_cases]
        views = request.views or self.VIEWS
        unknown = set(views) - set(self.VIEWS)
        if unknown:
            raise ValueError(f"Unknown b2 views: {', '.join(sorted(unknown))}")
        models = request.models or (vault.config.embedding.model,)
        dims = tuple(sorted(set(request.dims or (vault.config.embedding.dimensions,))))
        return B2Data(manifest, cases, tuple(views), tuple(models), dims)

    def _skeleton_texts(self, data: B2Data) -> list[str]:
        return [side["stem"] for case in data.cases for side in (case.left, case.right)
                if not side.get("skeleton")]

    def plan(self, vault: LoadedVault, data: B2Data, request: CompareRequest) -> dict[str, Any]:
        plan: dict[str, Any] = {"cases": len(data.cases), "views": list(data.views), "models": list(data.models),
                                "dims": list(data.dims), "roles": {}, "embedding": {}}
        texts = {side["stem"] for case in data.cases for side in (case.left, case.right)}
        needs_skeletons = "skeleton" in data.views or "fingerprint" in data.views
        if needs_skeletons:
            missing = self._skeleton_texts(data)
            sample = C.skeleton_prompt(prompt=missing[0] if missing else "x", expected_answer="")
            plan["roles"]["skeleton"] = {"calls": len(set(missing)),
                                         "tokens": len(set(missing)) * estimate_tokens(sample, C.SkeletonResult, 1200)}
        if "judge" in data.views:
            sample = C.freshness_prompt(candidate={"stem": data.cases[0].left["stem"] if data.cases else ""},
                                        comparisons=[{"ref": "item_0", "prompt": ""}])
            plan["roles"]["freshness"] = {"calls": len(data.cases), "pairs": len(data.cases),
                                          "tokens": len(data.cases) * estimate_tokens(sample, C.FreshnessVerdict, 2500)}
        embed_views = [view for view in ("stem", "skeleton") if view in data.views]
        for model in data.models:
            count = len(texts) * len(embed_views)
            tokens = sum(len(text.encode()) + 128 for text in texts) * len(embed_views)
            plan["embedding"][model] = {"texts": count, "calls": math.ceil(count / EMBED_BATCH) if count else 0,
                                        "tokens": tokens}
        return plan

    def run(self, data: B2Data, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]:
        labels = [case.positive for case in data.cases]
        report: dict[str, Any] = {"cases": len(data.cases), "positives": sum(labels),
                                  "negatives": len(labels) - sum(labels),
                                  "categories": dict(_count(case.category for case in data.cases)),
                                  "views": {}, "blocking_cutoffs": []}
        skeletons: dict[str, dict[str, Any]] = {}
        if "skeleton" in data.views or "fingerprint" in data.views:
            entry = ctx.role("skeleton")[0]
            for case in data.cases:
                for side in (case.left, case.right):
                    if side.get("skeleton"):
                        given = side["skeleton"]
                        techniques = given if isinstance(given, list) else [str(given)]
                        skeletons[side["stem"]] = {"techniques": techniques, "text": "Techniques: " + "; ".join(techniques),
                                                   "model_id": "benchmark"}
                    elif side["stem"] not in skeletons:
                        call = ctx.caller.call(entry, prompt=C.skeleton_prompt(prompt=side["stem"], expected_answer=side.get("answer") or ""),
                                               prompt_version=C.SKELETON_PROMPT, result_model=C.SkeletonResult,
                                               output_tokens=1200)
                        result = call.result
                        skeletons[side["stem"]] = {
                            "techniques": result.techniques, "model_id": call.model,
                            "text": "Techniques: " + "; ".join(result.techniques)
                                    + "\nCheckpoints: " + "; ".join(result.checkpoints)
                                    + "\nSummary: " + result.summary}
        for view in ("stem", "skeleton"):
            if view not in data.views:
                continue
            for model in data.models:
                texts = [(case.left["stem"], case.right["stem"]) if view == "stem" else
                         (skeletons[case.left["stem"]]["text"], skeletons[case.right["stem"]]["text"])
                         for case in data.cases]
                vectors = ctx.vectors(model, [text for pair in texts for text in pair], dims=max(data.dims))
                for dims in data.dims:
                    scores = centered_cosines([(vectors[a], vectors[b]) for a, b in texts], dims)
                    key = f"{view}|{model}|{dims}"
                    report["views"][key] = {
                        "view": view, "model_id": model, "dims": dims, "auc": roc_auc(scores, labels),
                        "by_category": {category: roc_auc(
                            [s for s, case in zip(scores, data.cases) if case.category == category or not case.positive],
                            [case.positive for case in data.cases if case.category == category or not case.positive])
                            for category in sorted({case.category for case in data.cases if case.positive})},
                    }
                    cutoff = blocking_cutoff(scores, labels, request.target_recall)
                    report["blocking_cutoffs"].append({"model_id": model, "record_kind": "item", "view": view,
                                                       "dims": dims, "target_recall": request.target_recall,
                                                       **cutoff})
        if "fingerprint" in data.views:
            predictions = []
            for case in data.cases:
                keys = [fingerprint_keys(prompt=side["stem"], expected_answer=side.get("answer") or "",
                                         skeletons=[skeletons[side["stem"]]] if side["stem"] in skeletons else [])
                        for side in (case.left, case.right)]
                predictions.append(bool(shared_keys(keys[0], keys[1])))
            report["views"]["fingerprint"] = {"view": "fingerprint", **binary_metrics(predictions, labels)}
        if "judge" in data.views:
            entry = ctx.role("freshness")[0]
            predictions = []
            case_models: list[str] = []
            for case, label in zip(data.cases, labels):
                call = ctx.caller.call(
                    entry, prompt=C.freshness_prompt(
                        candidate={"stem": case.left["stem"], "final_answer": case.left.get("answer") or ""},
                        comparisons=[{"ref": "item_0", "prompt": case.right["stem"]}]),
                    prompt_version=C.FRESHNESS_PROMPT, result_model=C.FreshnessVerdict, output_tokens=2500, pairs=1)
                verdict = next((c.verdict for c in call.result.comparisons if c.ref == "item_0"), "missing")
                ctx.caller.ledger(task="isomorph", left_kind="b2_case", left_id=f"{case.id}:left",
                                  right_kind="b2_case", right_id=f"{case.id}:right", judge="llm",
                                  judge_model=call.model, prompt_version=C.FRESHNESS_PROMPT,
                                  input_hash=call.input_hash, verdict=verdict,
                                  rationale={"benchmark": data.manifest.get("name"), "label": "positive" if label else "negative"})
                predictions.append(verdict in {"same_surface", "isomorph"})
                case_models.append(call.model)
            report["views"]["judge"] = {
                "view": "judge", **binary_metrics(predictions, labels),
                "by_model": {model: binary_metrics(
                    [p for p, m in zip(predictions, case_models) if m == model],
                    [y for y, m in zip(labels, case_models) if m == model])
                    for model in sorted(set(case_models))},
            }
        return report


def _count(values) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for value in values:
        counts[value] += 1
    return dict(sorted(counts.items()))


@dataclass
class VAItem:
    family_id: str
    item_id: str
    reference: str
    prompt: str


@dataclass
class VAData:
    items: list[VAItem]
    models: tuple[str, ...]


class ValidAlternativeSuite:
    name = "valid_alternative"
    description = ("Per-family regression suite: canonical and valid-alternative traces (CAS-checked), "
                   "graded by the learner-blind grader; reports valid-alternative false rejection.")

    def load(self, vault: LoadedVault, request: CompareRequest) -> VAData:
        wanted = set(request.family_ids)
        items = []
        for item_id, item in sorted(vault.practice_items.items()):
            if not item.family_id or item.status == "retired":
                continue
            if wanted and item.family_id not in wanted:
                continue
            items.append(VAItem(item.family_id, item_id, final_answer_text(item.expected_answer), item.prompt))
        return VAData(items[:request.max_items], request.models or (vault.config.embedding.model,))

    def plan(self, vault: LoadedVault, data: VAData, request: CompareRequest) -> dict[str, Any]:
        n = len(data.items)
        traces = n * (1 + request.alternatives)
        return {"items": n, "families": len({item.family_id for item in data.items}),
                "roles": {"valid_alternative": {"calls": n}, "equivalence": {"calls": n},
                          "grading": {"calls": traces}},
                "embedding": {"optional": "with --view embedding"}}

    def run(self, data: VAData, request: CompareRequest, ctx: CompareContext) -> dict[str, Any]:
        writer = ctx.role("valid_alternative")[0]
        verifier = ctx.role("equivalence")[0]
        grader = ctx.role("grading")[0]
        suite_cases = []
        excluded = degenerate_checks = 0
        for va in data.items:
            item = ctx.vault.practice_items[va.item_id]
            call = ctx.caller.call(writer, prompt=C.valid_alternative_prompt(
                prompt=item.prompt, reference=str(item.expected_answer), count=request.alternatives),
                prompt_version=C.VALID_ALTERNATIVE_PROMPT, result_model=C.ValidAlternativeTraces,
                output_tokens=6000)
            traces = [("canonical", call.result.canonical), *[("alternative", t) for t in call.result.alternatives]]
            eq = ctx.caller.call(verifier, prompt=C.equivalence_prompt(
                stem=item.prompt, reference=va.reference, answers=[t.final_answer for _, t in traces]),
                prompt_version=C.EQUIVALENCE_PROMPT, result_model=C.EquivalenceResult, output_tokens=2500)
            agreements = list(eq.result.agreements) if len(eq.result.agreements) == len(traces) else [False] * len(traces)
            degenerate = False
            if eq.result.answer_kind in {"numeric", "symbolic"}:
                checks: list[Any] = [None] * len(traces)
                if eq.result.sympy_check and sandbox_available():
                    sandbox = run_equivalence_checks({"check": eq.result.sympy_check}, [
                        {"program": "check", "reference": va.reference, "answer": t.final_answer} for _, t in traces])
                    # The production rule: a check that accepts a negative
                    # control (always True) confirms no trace.
                    checks, degenerate = equivalence_confirmations(sandbox, len(traces))
                agreements = [a and c is True for a, c in zip(agreements, checks)]
                degenerate_checks += int(degenerate)
            for index, ((kind, trace), verified) in enumerate(zip(traces, agreements)):
                trace_id = "va_" + content_key([va.item_id, call.input_hash, index])[:24]
                ctx.caller.ledger(task="answer_equivalence", left_kind="va_trace", left_id=trace_id,
                                  right_kind="practice_item", right_id=va.item_id, judge="verifier",
                                  prompt_version=C.EQUIVALENCE_PROMPT, input_hash=eq.input_hash,
                                  verdict="degenerate_check" if degenerate else ("agree" if verified else "disagree"),
                                  rationale={"kind": kind, "answer_kind": eq.result.answer_kind})
                if not verified:
                    excluded += 1
                    continue
                suite_cases.append({"trace_id": trace_id, "family_id": va.family_id, "item_id": va.item_id,
                                    "kind": kind, "trace": trace.trace, "writer_model": call.model})
        suite_path = ctx.output_dir / "valid_alternative_suite.json"
        suite_path.parent.mkdir(parents=True, exist_ok=True)
        suite_path.write_text(json.dumps({"version": HARNESS_VERSION, "cases": suite_cases}, sort_keys=True), encoding="utf-8")
        scores: dict[tuple[str, str], list[float]] = defaultdict(list)
        by_family: dict[tuple[str, str], list[float]] = defaultdict(list)
        for case in suite_cases:
            item = ctx.vault.practice_items[case["item_id"]]
            # Learner-blind by construction: only the synthetic trace reaches the context.
            context = blind_grading_context(ctx.vault, item, attempt_id=case["trace_id"],
                                            learner_answer_md=case["trace"])
            call = ctx.caller.call(grader, prompt=blind_grading_prompt(context),
                                   prompt_version=BLIND_GRADING_PROMPT_VERSION, result_model=BlindGradingProposal,
                                   output_tokens=4000)
            rubric = ctx.vault.rubric_for_item(item)
            maximum = getattr(rubric, "max_points", None) or 1
            score = min(1.0, call.result.rubric_score / maximum)
            ctx.caller.ledger(task="valid_alternative_grade", left_kind="va_trace", left_id=case["trace_id"],
                              right_kind="practice_item", right_id=case["item_id"], judge="llm",
                              judge_model=call.model, prompt_version=BLIND_GRADING_PROMPT_VERSION,
                              input_hash=call.input_hash, verdict=case["kind"], score=score,
                              rationale={"fatal_errors": len(call.result.fatal_errors)})
            scores[(call.model, case["kind"])].append(score)
            by_family[(case["family_id"], case["kind"])].append(score)

        def summary(values: list[float]) -> dict[str, Any]:
            return {"n": len(values), "mean_score": round(sum(values) / len(values), 6) if values else None,
                    "not_full_credit": round(sum(1 for v in values if v < 1.0) / len(values), 6) if values else None,
                    "below_half": round(sum(1 for v in values if v < 0.5) / len(values), 6) if values else None}

        return {"items": len(data.items), "suite_traces": len(suite_cases), "excluded_unverified_traces": excluded,
                "degenerate_checks": degenerate_checks,
                "suite_file": suite_path.name,
                "by_grader_model": {f"{model}|{kind}": summary(values) for (model, kind), values in sorted(scores.items())},
                "by_family": {f"{family}|{kind}": summary(values) for (family, kind), values in sorted(by_family.items())},
                "false_rejection_definition": "share of CAS-verified valid-alternative traces graded below full credit (and below half)"}


SUITES: dict[str, CompareSuite] = {"b2": B2Suite(), "valid_alternative": ValidAlternativeSuite()}


def run_compare(
    vault: LoadedVault, *, request: CompareRequest, caps: SpendCaps, price_per_million: float | None = None,
    embedding_price_per_million: float | None = None, cancelled: Callable[[], bool] | None = None,
    clients: Mapping[str, Any] | None = None, embedding_clients: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Plan (or run) one registered suite and write an aggregate report."""
    suite = SUITES.get(request.suite)
    if suite is None:
        raise ValueError(f"Unknown suite {request.suite!r}; registered: {', '.join(sorted(SUITES))}")
    data = suite.load(vault, request)
    plan = suite.plan(vault, data, request)
    sqlite_path = VaultPaths(vault.root, vault.config).sqlite_path
    repository = Repository.attach(sqlite_path, read_only=True) if request.dry_run else Repository(sqlite_path)
    caller = PFCaller(vault, repository, caps=caps, price_per_million=price_per_million, run_id=new_ulid(),
                      owner_kind="embeddings_compare", cancelled=cancelled)
    report: dict[str, Any] = {
        "status": "dry_run" if request.dry_run else "pending", "suite": suite.name,
        "description": suite.description, "harness_version": HARNESS_VERSION, "plan": plan,
        "caps": caps.as_dict(), "price_per_million": price_per_million,
        "embedding_price_per_million": embedding_price_per_million,
        "manifest": {"algorithm_version": vault.config.algorithms.algorithm_version,
                     "config_hash": content_key(vault.config.model_dump(mode="json")),
                     "embedding_model": vault.config.embedding.model,
                     "benchmark": getattr(data, "manifest", None)},
    }
    llm_calls = sum(int(role.get("calls", 0)) for role in plan.get("roles", {}).values())
    llm_tokens = sum(int(role.get("tokens", 0)) for role in plan.get("roles", {}).values())
    embed_calls = sum(int(entry.get("calls", 0)) for entry in plan.get("embedding", {}).values() if isinstance(entry, dict))
    embed_tokens = sum(int(entry.get("tokens", 0)) for entry in plan.get("embedding", {}).values() if isinstance(entry, dict))
    report["estimate"] = {"llm_calls": llm_calls, "llm_tokens": llm_tokens,
                          "embedding_calls": embed_calls, "embedding_tokens": embed_tokens}
    try:
        caller.check_shared(SpendEstimate(calls=llm_calls + embed_calls,
                                          pairs=int(plan.get("roles", {}).get("freshness", {}).get("pairs", 0))))
        if embed_calls:
            for model, entry in plan.get("embedding", {}).items():
                price = embedding_price_per_million if embedding_price_per_million is not None \
                    else EMBEDDING_PRICES_PER_MILLION.get(model)
                if price is None and entry.get("calls"):
                    raise SpendLimitExceeded(f"Unknown embedding price for {model}: pass --embedding-price-per-million")
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
        return report
    if request.dry_run:
        return report
    output = request.output_dir
    output.mkdir(parents=True, exist_ok=True)
    ctx = CompareContext(vault, caller, clients=clients, embedding_clients=embedding_clients,
                         embedding_price=embedding_price_per_million, output_dir=output)
    try:
        report["results"] = suite.run(data, request, ctx)
        report["status"] = "complete"
    except (AIInterrupted, KeyboardInterrupt):
        report["status"] = "cancelled"
    except SpendLimitExceeded as exc:
        report.update(status="over_budget", reason=str(exc))
    except (AIProviderUnavailable, PFUnavailable) as exc:
        report.update(status="provider_failed", error_type=type(exc).__name__, reason=str(exc)[:300])
    report["usage"] = caller.report()
    identity = content_key({"suite": suite.name, "plan": plan, "manifest": report["manifest"]})[:16]
    report["report_files"] = [f"{suite.name}-{identity}.json", f"{suite.name}-{identity}.md"]
    (output / report["report_files"][0]).write_text(json.dumps(report, sort_keys=True, indent=2, default=str), encoding="utf-8")
    (output / report["report_files"][1]).write_text(_markdown(report), encoding="utf-8")
    return report


def _markdown(report: dict[str, Any]) -> str:
    lines = [f"# `learnloop embeddings compare` — {report['suite']}", "",
             f"Status: {report['status']}; harness {report['harness_version']}.", ""]
    results = report.get("results") or {}
    if report["suite"] == "b2":
        lines += ["| View | Model | Dims | AUC |", "|---|---|---|---|"]
        for entry in results.get("views", {}).values():
            if "auc" in entry:
                lines.append(f"| {entry['view']} | {entry['model_id']} | {entry['dims']} | {entry['auc']} |")
        lines += ["", "## Blocking cutoffs (recall-oriented, R4)", "",
                  "| Model | Record kind | View | Dims | Cutoff | Recall | Judge load |", "|---|---|---|---|---|---|---|"]
        for cutoff in results.get("blocking_cutoffs", []):
            lines.append(f"| {cutoff['model_id']} | {cutoff['record_kind']} | {cutoff['view']} | {cutoff['dims']} | "
                         f"{cutoff['cutoff']} | {cutoff['recall']} | {cutoff['judge_load']} |")
        for name in ("fingerprint", "judge"):
            if name in results.get("views", {}):
                metrics = results["views"][name]
                lines.append(f"\n{name}: precision {metrics['precision']}, recall {metrics['recall']}, "
                             f"accuracy {metrics['accuracy']}")
    else:
        lines += ["| Grader model / trace kind | n | mean | not full credit | below half |", "|---|---|---|---|---|"]
        for key, entry in results.get("by_grader_model", {}).items():
            lines.append(f"| {key} | {entry['n']} | {entry['mean_score']} | {entry['not_full_credit']} | {entry['below_half']} |")
    lines += ["", "Aggregates only; every verdict is in judgment_ledger and every call in model_call_receipts."]
    return "\n".join(lines) + "\n"


__all__ = [
    "B2Suite", "CompareContext", "CompareRequest", "CompareSuite", "HARNESS_VERSION", "SUITES",
    "ValidAlternativeSuite", "VectorCache", "binary_metrics", "blocking_cutoff", "centered_cosines",
    "roc_auc", "run_compare",
]
