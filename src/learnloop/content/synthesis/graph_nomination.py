"""Slice 2 T5: embedding nominations for ingest and graph review (spec §8).

Nominations only, never identity (``spec_knowledge_model.md`` §14: "no
embeddings for facet identity"; Slice 2 R1). This module shortlists: the
append-reconciliation model, the graph-structuring model or the owner decides
every merge, alias and mint. Nothing here writes vault content, evidence or a
verdict, and no cosine cutoff is set in code (R4): nominations are the top-k
by exact mean-centred cosine, the Phase 1 retrieval maths.

Two modes:

* **review** (:meth:`GraphNominator.for_review`): stored vectors only. Doctor
  and review passes use it for their cosine column; it never constructs a
  client, so it can never pay.
* **ingest** (:meth:`GraphNominator.for_ingest`): also embeds new LLM-written
  candidate text (inventory claims, candidate facet and concept definitions,
  repair texts) through the ``ai.routing.embedding`` route, under the Phase 1
  spend budget with ``[graph_nomination]`` caps, with receipts. Vectors are
  content-addressed, so a rerun, a revalidation or the record's later backfill
  finds the vector it already paid for.

Registry vectors come from the backfill (``facet/definition``,
``concept/definition``). An incomplete or missing index, a disabled route, an
unknown price, an exhausted cap or a provider failure degrades the caller to
today's lexical behaviour; :meth:`GraphNominator.summary` says which, so the
manifest never claims a nomination that did not happen. Replay and rebuild
never construct a nominator.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

import numpy as np

from learnloop.ai.embedding import EMBEDDING_PRICES_PER_MILLION, EmbeddingClient
from learnloop.ai.execution import observe_model_calls
from learnloop.ai.spend import SpendBudget, SpendCaps, SpendEstimate, SpendLimitExceeded
from learnloop.content.synthesis.facet_mint_gate import distinct_repair
from learnloop.db.connection import connect
from learnloop.diagnosis.diagnostic_gate import normalize_answer
from learnloop.db.stores.embedding_vectors import (
    IncompleteEmbeddingIndex,
    current_vectors,
    get_vector_by_content,
    put_vector,
)
from learnloop.ids import new_ulid
from learnloop.vault.embedding_recipes import (
    EMBEDDING_RECIPES,
    concept_definition_text,
    facet_definition_text,
    repair_record_id,
)
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

NOMINATION_VERSION = "t5-graph-nomination-1"
DOCUMENT_PREFIX = "retrieval-document"
FACET_RECIPE = "facet/definition"
CONCEPT_RECIPE = "concept/definition"
REPAIR_RECIPE = "facet_repair/text"
# Query-side records for new inventory text (append). Not registry recipes:
# they are formatted like the registry recipe they are compared with, so both
# sides are embedded as documents (symmetric similarity).
INVENTORY_CLAIM_KIND = "inventory_claim"
INVENTORY_CONCEPT_KIND = "inventory_concept"
INVENTORY_QUERY_VERSION = 1
OWNER_KIND = "graph_nomination"
_BATCH = 32


def is_active(config: Any) -> bool:
    """The kill switch and the embedding master switch must both be on."""

    return bool(config.graph_nomination.enabled and config.embedding.enabled)


@dataclass(frozen=True)
class Nomination:
    record_id: str
    cosine: float
    rank: int

    def as_dict(self) -> dict[str, Any]:
        return {"id": self.record_id, "cosine": round(self.cosine, 4), "rank": self.rank}


@dataclass(frozen=True)
class QueryText:
    """New text to embed (or find already embedded) for one comparison."""

    record_kind: str
    field: str
    record_id: str
    text: str
    content_hash: str
    task_prefix: str = DOCUMENT_PREFIX


def _recipe_query(recipe_name: str, record_id: str, text: str) -> QueryText:
    record = EMBEDDING_RECIPES[recipe_name].record(record_id, text)
    return QueryText(record.record_kind, record.field, record.record_id, record.text, record.content_hash)


def facet_query(payload: Mapping[str, Any], record_id: str | None = None) -> QueryText | None:
    """A candidate facet's ``facet/definition`` text, hashed as its backfill would."""

    text = facet_definition_text(payload)
    if not text.strip():
        return None
    return _recipe_query(FACET_RECIPE, str(record_id or payload.get("id") or ""), text)


def concept_query(concept: Any, record_id: str) -> QueryText | None:
    text = concept_definition_text(concept)
    if not text.strip():
        return None
    return _recipe_query(CONCEPT_RECIPE, record_id, text)


def repair_query(text: str) -> QueryText | None:
    text = str(text or "").strip()
    if not text:
        return None
    return _recipe_query(REPAIR_RECIPE, repair_record_id(text), text)


def _inventory_query(kind: str, text: str) -> QueryText | None:
    if not text.strip():
        return None
    digest = hashlib.sha256(json.dumps(
        [kind, "definition", INVENTORY_QUERY_VERSION, text],
        ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return QueryText(kind, "definition", digest, text, digest)


def inventory_queries(new_inventories: Iterable[Mapping[str, Any]]) -> tuple[list[QueryText], list[QueryText]]:
    """LLM-written inventory claims (vs facets) and concept mentions (vs concepts).

    Claims and procedure contracts are composed in the ``facet/definition``
    layout; concept mentions in the ``concept/definition`` layout. Order is
    deterministic (inventory order, de-duplicated by text).
    """

    claims: dict[str, QueryText] = {}
    concepts: dict[str, QueryText] = {}
    for entry in new_inventories:
        inventory = entry.get("inventory") if "inventory" in entry else entry
        if not isinstance(inventory, Mapping):
            continue
        for claim in inventory.get("claims", []) or []:
            query = _inventory_query(INVENTORY_CLAIM_KIND, facet_definition_text({
                "claim": claim.get("statement") or "",
                "preconditions": claim.get("preconditions") or [],
                "postconditions": claim.get("postconditions") or [],
                "applicability": claim.get("applicability") or [],
                "positive_examples": claim.get("examples") or [],
                "negative_examples": claim.get("counterexamples") or [],
                "non_goals": claim.get("non_goals") or [],
            }))
            if query is not None:
                claims.setdefault(query.content_hash, query)
        for procedure in inventory.get("procedure_signals", []) or []:
            query = _inventory_query(INVENTORY_CLAIM_KIND, facet_definition_text({
                "claim": procedure.get("contract") or "",
                "preconditions": procedure.get("preconditions") or [],
            }))
            if query is not None:
                claims.setdefault(query.content_hash, query)
        for mention in inventory.get("concept_mentions", []) or []:
            query = _inventory_query(INVENTORY_CONCEPT_KIND, concept_definition_text({
                "title": mention.get("name") or "",
                "aliases": mention.get("aliases") or [],
            }))
            if query is not None:
                concepts.setdefault(query.content_hash, query)
    return list(claims.values()), list(concepts.values())


class RegistryIndex:
    """The complete current index of one registry recipe for one model."""

    def __init__(self, recipe_name: str, vectors: Mapping[str, np.ndarray]):
        self.recipe_name = recipe_name
        self.ids = sorted(vectors)
        if self.ids:
            matrix = np.stack([vectors[key] for key in self.ids])
            widths = {matrix.shape[1]}
        else:
            matrix = np.zeros((0, 0))
            widths = set()
        self.dims = next(iter(widths)) if widths else 0
        self.mean = matrix.mean(axis=0) if self.ids else np.zeros(0)
        self._centered = matrix - self.mean if self.ids else matrix
        self._norms = np.linalg.norm(self._centered, axis=1) if self.ids else np.zeros(0)
        self._row = {key: index for index, key in enumerate(self.ids)}

    def __len__(self) -> int:
        return len(self.ids)

    def __contains__(self, record_id: object) -> bool:
        return record_id in self._row

    def _centre(self, vector: np.ndarray) -> np.ndarray | None:
        vector = np.asarray(vector, dtype=np.float64)
        if not self.ids or vector.ndim != 1 or vector.size != self.dims:
            return None
        return vector - self.mean

    def _scores(self, centred_query: np.ndarray) -> np.ndarray:
        denominator = self._norms * np.linalg.norm(centred_query)
        return np.divide(self._centered @ centred_query, denominator,
                         out=np.zeros(len(self.ids)), where=denominator != 0)

    def nearest(self, vector: np.ndarray, k: int, *, exclude: Collection[str] = ()) -> list[Nomination]:
        """Top-k by mean-centred cosine; ties break on record id (deterministic)."""

        centred = self._centre(vector)
        if centred is None or k <= 0:
            return []
        scores = self._scores(centred)
        excluded = set(exclude)
        ranked = sorted(
            ((float(scores[index]), key) for index, key in enumerate(self.ids) if key not in excluded),
            key=lambda pair: (-pair[0], pair[1]),
        )[:k]
        return [Nomination(key, score, rank) for rank, (score, key) in enumerate(ranked, start=1)]

    def ranks(self, vector: np.ndarray, *, exclude: Collection[str] = ()) -> dict[str, tuple[int, float]]:
        """Every record's (rank, cosine) against ``vector``; used by the report."""

        return {nomination.record_id: (nomination.rank, nomination.cosine)
                for nomination in self.nearest(vector, len(self.ids), exclude=exclude)}

    def vector(self, record_id: str) -> np.ndarray | None:
        row = self._row.get(record_id)
        return None if row is None else self._centered[row] + self.mean

    def cosine(self, left: np.ndarray, right: np.ndarray) -> float | None:
        """Mean-centred cosine of two vectors under this index's centroid."""

        left_c, right_c = self._centre(left), self._centre(right)
        if left_c is None or right_c is None:
            return None
        denominator = float(np.linalg.norm(left_c) * np.linalg.norm(right_c))
        return float(left_c @ right_c / denominator) if denominator else 0.0

    def pair(self, left_id: str, right_id: str) -> float | None:
        left, right = self.vector(left_id), self.vector(right_id)
        if left is None or right is None:
            return None
        return self.cosine(left, right)

    def pairwise(self) -> np.ndarray:
        """All-pairs centred cosine matrix (the report's noise floor)."""

        unit = np.divide(self._centered, self._norms[:, np.newaxis],
                         out=np.zeros_like(self._centered), where=self._norms[:, np.newaxis] != 0)
        return unit @ unit.T


def raw_cosine(left: np.ndarray | None, right: np.ndarray | None) -> float | None:
    """Uncentred cosine, for text pairs with no registry centroid (repair shadow)."""

    if left is None or right is None or left.shape != right.shape:
        return None
    denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(left @ right / denominator) if denominator else 0.0


class GraphNominator:
    """Stored-vector lookups plus capped embedding of new candidate text.

    Never raises into its caller for an embedding or index problem: it records
    the reason and returns nothing to nominate, which is the lexical fallback.
    """

    def __init__(
        self,
        vault: LoadedVault,
        sqlite_path: Path,
        *,
        allow_new_text: bool,
        repository: Any = None,
        client_factory: Callable[[], EmbeddingClient] | None = None,
    ) -> None:
        config = vault.config
        self.vault = vault
        self.sqlite_path = Path(sqlite_path)
        self.model_id = config.embedding.model
        self.dims = config.embedding.dimensions
        self.top_k = config.graph_nomination.top_k
        self.mode = "ingest" if allow_new_text else "review"
        self._allow_new_text = bool(allow_new_text and config.graph_nomination.embed_new_text)
        self._repository = repository
        self._client_factory = client_factory
        self._client: EmbeddingClient | None = None
        self._client_unusable = False
        self._indexes: dict[str, RegistryIndex | None] = {}
        self._index_status: dict[str, str] = {}
        self._notes: list[str] = []
        self._cache: dict[tuple[str, str, str, str], np.ndarray] = {}
        self._run_id = new_ulid()
        self._price = EMBEDDING_PRICES_PER_MILLION.get(self.model_id)
        self._budget = SpendBudget(SpendCaps(
            max_candidates=config.graph_nomination.max_query_texts,
            max_pairs=0, max_retries=0,
            max_calls=config.graph_nomination.max_query_calls,
            max_total_tokens=config.graph_nomination.max_query_tokens,
            max_estimated_usd=config.graph_nomination.max_query_cost_usd,
        ))
        self.counts = {"queries": 0, "cached": 0, "embedded": 0, "calls": 0, "not_embedded": 0}

    # -- construction -----------------------------------------------------

    @classmethod
    def for_review(cls, vault: LoadedVault) -> GraphNominator | None:
        """Stored vectors only; ``None`` when the kill switch or embeddings are off."""

        if not is_active(vault.config):
            return None
        return cls(vault, VaultPaths(vault.root, vault.config).sqlite_path, allow_new_text=False)

    @classmethod
    def for_ingest(
        cls, vault: LoadedVault, repository: Any, *,
        client_factory: Callable[[], EmbeddingClient] | None = None,
    ) -> GraphNominator | None:
        if not is_active(vault.config):
            return None
        return cls(
            vault, Path(repository.sqlite_path), allow_new_text=True,
            repository=repository, client_factory=client_factory,
        )

    def stored_only(self) -> GraphNominator:
        """The same vault and model with no paid path (revalidation, review)."""

        return GraphNominator(self.vault, self.sqlite_path, allow_new_text=False)

    # -- reporting ---------------------------------------------------------

    def _note(self, reason: str) -> None:
        if reason not in self._notes:
            self._notes.append(reason)

    def summary(self) -> dict[str, Any]:
        """Honest label for manifests and reports: what was and was not nominated."""

        statuses = dict(sorted(self._index_status.items()))
        if any(status == "complete" for status in statuses.values()):
            status = "active"
        elif statuses and all(status == "empty" for status in statuses.values()):
            status = "empty_registry"  # nothing registered yet to nominate
        elif statuses:
            status = "lexical_only"  # an index is missing or incomplete
        else:
            status = "unused"
        return {
            "version": NOMINATION_VERSION,
            "mode": self.mode,
            "status": status,
            "model_id": self.model_id,
            "top_k": self.top_k,
            "indexes": statuses,
            "counts": dict(self.counts),
            "charged": asdict(self._budget.used) if self.counts["calls"] else None,
            "notes": list(self._notes),
        }

    # -- registry indexes ----------------------------------------------------

    def index(self, recipe_name: str) -> RegistryIndex | None:
        """The complete current index for one registry recipe, or ``None``."""

        if recipe_name in self._indexes:
            return self._indexes[recipe_name]
        recipe = EMBEDDING_RECIPES[recipe_name]
        manifest = {record.record_id: record.content_hash for record in recipe.records(self.vault)}
        index: RegistryIndex | None = None
        if not self.sqlite_path.exists():
            status = "no_database"
        else:
            try:
                with closing(connect(self.sqlite_path, read_only=True)) as connection:
                    vectors = current_vectors(
                        connection, record_kind=recipe.record_kind, field=recipe.field,
                        model_id=self.model_id, task_prefix=DOCUMENT_PREFIX,
                        expected_records=manifest,
                    )
            except IncompleteEmbeddingIndex:
                status = "index_incomplete"
            except sqlite3.Error:
                status = "no_vector_store"
            else:
                if not manifest:
                    status = "empty"
                elif any(vector.size != self.dims for vector in vectors.values()):
                    status = "dimension_mismatch"
                else:
                    index = RegistryIndex(recipe_name, vectors)
                    status = "complete"
        self._indexes[recipe_name] = index
        self._index_status[recipe_name] = status
        return index

    # -- vectors for new text -------------------------------------------------

    def vectors(self, queries: Sequence[QueryText | None]) -> dict[str, np.ndarray]:
        """``content_hash -> vector`` for every query that is stored or embeddable.

        Stored vectors (by identical content) are used first. In ingest mode the
        rest are embedded within the caps; anything not embedded is absent from
        the result, which callers treat as "no nomination".
        """

        wanted: dict[tuple[str, str, str, str], QueryText] = {}
        for query in queries:
            if query is not None:
                wanted.setdefault(self._key(query), query)
        result: dict[str, np.ndarray] = {}
        pending: list[QueryText] = []
        for key, query in wanted.items():
            if key in self._cache:
                result[query.content_hash] = self._cache[key]
        lookups = [(key, query) for key, query in wanted.items() if key not in self._cache]
        if lookups and self.sqlite_path.exists():
            try:
                with closing(connect(self.sqlite_path, read_only=True)) as connection:
                    for key, query in lookups:
                        vector = get_vector_by_content(
                            connection, record_kind=query.record_kind, field=query.field,
                            content_hash=query.content_hash, model_id=self.model_id,
                            task_prefix=query.task_prefix,
                        )
                        if vector is None or vector.size != self.dims:
                            pending.append(query)
                            continue
                        self._cache[key] = vector
                        result[query.content_hash] = vector
                        self.counts["cached"] += 1
            except sqlite3.Error:
                self._note("no_vector_store")
                pending = [query for _key, query in lookups]
        else:
            pending = [query for _key, query in lookups]
        self.counts["queries"] += len(wanted)
        if pending:
            for query, vector in self._embed(pending).items():
                self._cache[self._key(query)] = vector
                result[query.content_hash] = vector
        return result

    def _key(self, query: QueryText) -> tuple[str, str, str, str]:
        return (query.record_kind, query.field, query.content_hash, query.task_prefix)

    def _ready_client(self) -> EmbeddingClient | None:
        if self._client is not None or self._client_unusable:
            return self._client
        try:
            if self._client_factory is not None:
                client = self._client_factory()
            else:
                from learnloop.ai.routing import ready_client_for_task

                resolved = ready_client_for_task(self.vault.root, self.vault.config, "embedding")
                if resolved.client is None or not resolved.runtime.ready:
                    self._note("embedding_route_unavailable")
                    self._client_unusable = True
                    return None
                client = resolved.client
        except Exception as exc:  # noqa: BLE001 - nominations never fail ingest
            self._note(f"embedding_route_unavailable:{type(exc).__name__}")
            self._client_unusable = True
            return None
        if client.model_id != self.model_id or client.dims != self.dims:
            self._note("embedding_client_mismatch")
            self._client_unusable = True
            return None
        if "text" not in client.modalities:
            self._note("embedding_client_not_text")
            self._client_unusable = True
            return None
        self._client = client
        return client

    def _embed(self, pending: list[QueryText]) -> dict[QueryText, np.ndarray]:
        if not self._allow_new_text:
            self.counts["not_embedded"] += len(pending)
            self._note("new_text_not_embedded" if self.mode == "ingest" else "review_uses_stored_vectors_only")
            return {}
        if self._price is None:
            self.counts["not_embedded"] += len(pending)
            self._note("unknown_embedding_price")
            return {}
        client = self._ready_client()
        if client is None:
            self.counts["not_embedded"] += len(pending)
            return {}
        sendable = []
        for query in pending:
            if len(query.text.encode("utf-8")) + 128 > client.max_input_tokens:
                self._note("oversized_text_skipped")
                self.counts["not_embedded"] += 1
            else:
                sendable.append(query)
        out: dict[QueryText, np.ndarray] = {}
        by_prefix: dict[str, list[QueryText]] = {}
        for query in sendable:
            by_prefix.setdefault(query.task_prefix, []).append(query)
        batches = [
            (prefix, queries[offset:offset + _BATCH])
            for prefix, queries in sorted(by_prefix.items())
            for offset in range(0, len(queries), _BATCH)
        ]
        stopped = False
        for prefix, batch in batches:
            if stopped:
                self.counts["not_embedded"] += len(batch)
                continue
            tokens = sum(len(query.text.encode("utf-8")) + 128 for query in batch)
            estimate = SpendEstimate(
                candidates=len(batch), calls=1, total_tokens=tokens,
                estimated_usd=tokens * self._price / 1_000_000,
            )
            usage: dict[str, Any] = {}
            try:
                with observe_model_calls(self._observer(prefix, usage)):
                    with self._budget.request(estimate) as charge:
                        try:
                            vectors = client.embed([query.text for query in batch], prefix)
                        finally:
                            actual = usage.get("input_tokens")
                            charge.reconcile(
                                total_tokens=actual,
                                estimated_usd=(max(usage.get("cost") or 0.0, actual * self._price / 1_000_000)
                                               if actual is not None else usage.get("cost")),
                            )
                if len(vectors) != len(batch) or any(len(vector) != self.dims for vector in vectors):
                    raise ValueError("embedding response has the wrong count or width")
            except SpendLimitExceeded:
                self._note("query_caps_reached")
                self.counts["not_embedded"] += len(batch)
                stopped = True
                continue
            except Exception as exc:  # noqa: BLE001 - degrade to lexical, never fail ingest
                self._note(f"embedding_failed:{type(exc).__name__}")
                self.counts["not_embedded"] += len(batch)
                stopped = True
                continue
            self.counts["calls"] += 1
            arrays = [np.asarray(vector, dtype=np.float64) for vector in vectors]
            try:
                with closing(connect(self.sqlite_path)) as connection, connection:
                    for query, vector in zip(batch, arrays, strict=True):
                        put_vector(
                            connection, record_kind=query.record_kind, record_id=query.record_id,
                            field=query.field, content_hash=query.content_hash,
                            model_id=self.model_id, task_prefix=query.task_prefix, vector=vector,
                        )
            except sqlite3.Error as exc:
                # The paid vectors still serve this run; a later run pays again.
                self._note(f"vector_store_write_failed:{type(exc).__name__}")
            for query, vector in zip(batch, arrays, strict=True):
                # Round-trip through float16, as stored, so this run and a
                # later rerun from the store rank identically.
                out[query] = vector.astype("<f2").astype(np.float64)
            self.counts["embedded"] += len(batch)
        return out

    def _observer(self, prefix: str, usage: dict[str, Any]) -> Callable[[str, dict[str, Any]], None]:
        def observe(action: str, event: dict[str, Any]) -> None:
            if action == "start":
                declared = json.loads(event.get("budget_json") or "{}")
                declared["graph_nomination"] = {
                    "version": NOMINATION_VERSION, "model_id": self.model_id,
                    "dimensions": self.dims, "task_prefix": prefix,
                    "price_per_million": self._price, "price_source": "spec_estimate",
                }
                event = {**event, "budget_json": json.dumps(declared, sort_keys=True)}
            elif action == "finish":
                usage.update(event)
            if self._repository is not None:
                self._repository.record_model_event(
                    action, event, owner_kind=OWNER_KIND, owner_id=self._run_id,
                )
        return observe

    # -- nominations ---------------------------------------------------------

    def nominate(
        self, recipe_name: str, queries: Sequence[QueryText | None], *,
        exclude: Mapping[str, Collection[str]] | None = None, k: int | None = None,
    ) -> dict[str, list[Nomination]]:
        """``query.record_id -> top-k registry nominations``; empty when degraded."""

        index = self.index(recipe_name)
        if index is None or not len(index):
            return {}
        present = [query for query in queries if query is not None]
        vectors = self.vectors(present)
        return self.nominate_vectors(
            recipe_name,
            {query.record_id: vectors[query.content_hash]
             for query in present if query.content_hash in vectors},
            exclude=exclude, k=k,
        )

    def nominate_vectors(
        self, recipe_name: str, vectors: Mapping[str, np.ndarray], *,
        exclude: Mapping[str, Collection[str]] | None = None, k: int | None = None,
    ) -> dict[str, list[Nomination]]:
        index = self.index(recipe_name)
        if index is None or not len(index):
            return {}
        limit = self.top_k if k is None else k
        out: dict[str, list[Nomination]] = {}
        for record_id, vector in vectors.items():
            nominations = index.nearest(vector, limit, exclude=(exclude or {}).get(record_id, ()))
            if nominations:
                out[record_id] = nominations
        return out

    def facet_cosine(self, left: Any, right: Any) -> float | None:
        """Cosine of two facets, each a registered id or a proposal payload.

        Payload vectors come from what ingest already embedded (or the store);
        this never pays for a display column on its own.
        """

        index = self.index(FACET_RECIPE)
        if index is None or not len(index):
            return None

        def vector(side: Any) -> np.ndarray | None:
            if isinstance(side, str):
                return index.vector(side)
            query = facet_query(side) if isinstance(side, Mapping) else None
            if query is None:
                return None
            cached = self._cache.get(self._key(query))
            if cached is not None:
                return cached
            return self.stored_only().vectors([query]).get(query.content_hash)

        left_vector, right_vector = vector(left), vector(right)
        if left_vector is None or right_vector is None:
            return None
        return index.cosine(left_vector, right_vector)

    def pair_cosine(self, recipe_name: str, left_id: str, right_id: str) -> float | None:
        index = self.index(recipe_name)
        return None if index is None else index.pair(left_id, right_id)

    def cosine_column(self, recipe_name: str, left_id: str, right_id: str) -> dict[str, Any]:
        """The review-pass cosine column: a value, or why there is none."""

        cosine = self.pair_cosine(recipe_name, left_id, right_id)
        if cosine is not None:
            return {"cosine": round(cosine, 4)}
        status = self._index_status.get(recipe_name, "unavailable")
        return {"cosine": None, "cosine_status": "record_missing" if status == "complete" else status}


def cosine_suffix(column: Mapping[str, Any] | None) -> str:
    """``", cosine 0.91"`` for a message, or nothing when there is no value."""

    if not column or column.get("cosine") is None:
        return ""
    return f", cosine {float(column['cosine']):.2f}"


# --- D2 mint gate: embedding neighbours and the repair-equivalence shadow ----


def annotate_mint_report(
    nominator: GraphNominator,
    report: Any,
    candidates: Sequence[Mapping[str, Any]],
    registered: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Shadow record beside the D2 verdicts. It never changes a disposition.

    * ``embedding_neighbours``: each candidate's top-k registered facets by
      definition embedding, with ``d2`` marking those the gate also compared.
    * ``d2_cosines``: the cosine column for every pair D2 nominated.
    * ``repair_shadows``: for every D2 pair where ``distinct_repair`` can be
      evaluated, the text verdict next to the embedding view: for each repair
      the candidate prescribes and the neighbour (by normalized text) does not,
      the best raw cosine to any neighbour repair. ``min_best_cosine`` is the
      least-covered "distinct" repair: when it is high, the text test called
      two paraphrased repair sets distinct (spec §8: the MINT bias).

    New text is embedded only when the registered facet index is complete and
    non-empty; otherwise the record uses whatever is already stored.
    """

    by_id: dict[str, Mapping[str, Any]] = {str(p.get("id") or ""): p for p in registered}
    for payload in candidates:
        by_id[str(payload.get("id") or "")] = payload
    registered_ids = {str(p.get("id") or "") for p in registered}
    facet_queries = {str(p.get("id") or ""): facet_query(p) for p in candidates}
    index = nominator.index(FACET_RECIPE)
    definition_vectors = (
        nominator.vectors([q for q in facet_queries.values() if q is not None])
        if index is not None and len(index) else {}
    )
    nominations = nominator.nominate_vectors(
        FACET_RECIPE,
        {candidate_id: definition_vectors[query.content_hash]
         for candidate_id, query in facet_queries.items()
         if query is not None and query.content_hash in definition_vectors},
        exclude={candidate_id: {candidate_id} for candidate_id in facet_queries},
    )

    def definition_vector(facet_id: str) -> np.ndarray | None:
        query = facet_queries.get(facet_id)
        if query is not None:
            return definition_vectors.get(query.content_hash)
        return index.vector(facet_id) if index is not None else None

    shadow_pairs: list[tuple[str, str]] = []
    for verdict in report.verdicts:
        for neighbour in verdict.neighbours:
            left, right = by_id.get(verdict.candidate_id), by_id.get(neighbour.facet_id)
            if left is not None and right is not None and (left.get("instructional_repairs") and right.get("instructional_repairs")):
                shadow_pairs.append((verdict.candidate_id, neighbour.facet_id))
    repair_texts = {
        str(text).strip()
        for left, right in shadow_pairs
        for payload in (by_id[left], by_id[right])
        for text in payload.get("instructional_repairs") or []
        if str(text).strip()
    }
    repair_queries = {text: repair_query(text) for text in sorted(repair_texts)}
    # Ingest pays only to compare against a complete, non-empty registry: with
    # no registered facet index the shadow uses stored vectors or stays empty.
    source = nominator if index is not None and len(index) else nominator.stored_only()
    repair_vectors = source.vectors(list(repair_queries.values())) if repair_queries else {}

    def repair_vector(text: str) -> np.ndarray | None:
        query = repair_queries.get(str(text).strip())
        return None if query is None else repair_vectors.get(query.content_hash)

    def shadow(candidate_id: str, neighbour_id: str) -> dict[str, Any]:
        candidate, neighbour = by_id[candidate_id], by_id[neighbour_id]
        neighbour_norms = {
            normalize_answer(str(text)) for text in neighbour.get("instructional_repairs") or []
        }
        exclusive = [
            str(text) for text in candidate.get("instructional_repairs") or []
            if normalize_answer(str(text)) and normalize_answer(str(text)) not in neighbour_norms
        ]
        neighbour_vectors = [repair_vector(text) for text in neighbour.get("instructional_repairs") or []]
        best: list[float | None] = []
        for text in exclusive:
            own = repair_vector(text)
            scores = [raw_cosine(own, other) for other in neighbour_vectors]
            known = [score for score in scores if score is not None]
            best.append(round(max(known), 4) if known and own is not None else None)
        measured = [score for score in best if score is not None]
        return {
            "neighbour_id": neighbour_id,
            "text_distinct_repair": distinct_repair(candidate, neighbour),
            "exclusive_repairs": len(exclusive),
            "best_cosines": best,
            "min_best_cosine": min(measured) if measured and len(measured) == len(best) else None,
            "cosine_kind": "raw",
        }

    records = []
    for verdict in report.verdicts:
        candidate_id = verdict.candidate_id
        d2_ids = {neighbour.facet_id for neighbour in verdict.neighbours}
        vector = definition_vector(candidate_id)
        d2_cosines = {}
        if index is not None and vector is not None:
            for facet_id in sorted(d2_ids):
                other = definition_vector(facet_id)
                cosine = index.cosine(vector, other) if other is not None else None
                d2_cosines[facet_id] = None if cosine is None else round(cosine, 4)
        records.append({
            "candidate_id": candidate_id,
            "disposition": str(verdict.disposition),
            "embedding_neighbours": [
                {**nomination.as_dict(), "d2": nomination.record_id in d2_ids,
                 "registered": nomination.record_id in registered_ids}
                for nomination in nominations.get(candidate_id, [])
            ],
            "d2_cosines": d2_cosines,
            "repair_shadows": [
                shadow(left, right) for left, right in shadow_pairs if left == candidate_id
            ],
        })
    return {"version": NOMINATION_VERSION, "candidates": records}


__all__ = [
    "CONCEPT_RECIPE",
    "FACET_RECIPE",
    "GraphNominator",
    "NOMINATION_VERSION",
    "Nomination",
    "QueryText",
    "REPAIR_RECIPE",
    "RegistryIndex",
    "annotate_mint_report",
    "concept_query",
    "cosine_suffix",
    "facet_query",
    "inventory_queries",
    "is_active",
    "raw_cosine",
    "repair_query",
]
