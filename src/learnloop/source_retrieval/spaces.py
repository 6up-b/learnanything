"""The source-space resolver: the ONE new seam in ``search_spans`` (spec_local_contextual_retrieval_v1 §5).

``resolve_source_spaces`` decides, per query, which embedding spaces may
contribute a meaning ranking and with what weight, and records why each
space is in or out. Scores from different spaces are never mixed raw: each
space ranks its own covered extractions by its own cosine, and the rankings
are combined by rank, ``fused(d) = sum_s w_s / (rrf_k + rank_s(d))``.

* **Availability (§5.1).** A space contributes only when it is enabled, it
  covers the extraction (its whole current window set; a stale or partial
  extraction is uncovered, never served from stale vectors), its query
  encoder can answer within the existing time box, and it is not in
  ``epoch_drift``. Reasons: ``ok``, ``incomplete``, ``encoder_unavailable``,
  ``encoder_late``, ``disabled``, ``epoch_drift``, ``retired``.
* **Weights (§5.2, §9.2).** The seed puts full weight on the current default
  space (``embedding.source_space.default``, Qwen) and zero on the others.
  With ``learned_fusion`` off (the default) the served weights ARE the seed;
  the learned posterior's weights are only logged.
* **Coverage completion.** An extraction no positively weighted available
  space covers is served by a stand-in: the cheapest available space that
  covers it (by its price per million tokens; the local space is free, then
  Qwen, then Voyage), with the weight of the space it stands in for. A new
  import waiting for the GPU is therefore still found by meaning through Voyage
  or Qwen, and a hosted space is queried only for what it alone covers.

With the default left at Qwen and Qwen covering the scope, the fused meaning
list is exactly Qwen's ranking (tested byte-identical on ``find_sources``).
With both new switches off the resolver is never consulted at all.

The local space's query encoder is :data:`LOCAL_QUERY_ENCODER`: in production the
ADOPTED query student (P2, ``student_encoder.adopted_encoder``), or None (no student adopted,
``embedding.local.student`` off): then the local space reports ``encoder_unavailable``. A
student whose query process is not up is started in the background, and the query waits for it
only when ``P(in time) > 1 / (1 + w)`` on its measured start times, ``w`` the local lists'
weight share (§5.1 item 3, ``student_decision.should_wait``); otherwise the local space is
``encoder_late`` for this query and the others serve.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
import time
from typing import Any

import numpy as np

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.local_embeddings import fusion
from learnloop.source_retrieval.corpus import Scope
from learnloop.source_retrieval.recipes import block_record_id, split_record_id
from learnloop.vault.models import LoadedVault

QWEN = "qwen"
LOCAL_GROUPED = "local:grouped"
LOCAL_SINGLETON = "local:singleton"
VOYAGE = "voyage"
USABLE = ("ok", "partial")
#: structural: the spaces whose query embedding is a paid request (the local
#: space's encoder runs on this machine): a caller's shared budget makes room
#: for each of them (Codex re-review F17).
PAID_QUERY_SPACES = (QWEN, VOYAGE)


class LocalQueryEncoder:
    """The protocol a P1c teacher session or a P2 student implements."""

    encoder_id: str

    def encode(self, texts: Sequence[str], *, deadline: float | None = None) -> list[Sequence[float]]:  # pragma: no cover
        raise NotImplementedError


def _adopted_student(vault: LoadedVault) -> LocalQueryEncoder | None:
    from learnloop.source_retrieval.student_encoder import adopted_encoder

    return adopted_encoder(vault)  # type: ignore[return-value]


#: ``vault -> encoder or None``: the adopted query student (P2), else None.
LOCAL_QUERY_ENCODER: Callable[[LoadedVault], LocalQueryEncoder | None] = _adopted_student


def _encode(encoder: Any, texts: Sequence[str], *, deadline: float | None, receipt_id: str) -> list[Sequence[float]]:
    """A local encoder's vectors; the receipt goes to an encoder that queues the teacher replay."""

    if getattr(encoder, "accepts_receipt", False):
        return encoder.encode(list(texts), deadline=deadline, receipt_id=receipt_id or None)
    return encoder.encode(list(texts), deadline=deadline)


def _cold_start(encoder: Any, *, deadline: float | None, box_s: float, share: float) -> tuple[str, str] | None:
    """``(status, reason)`` when a not-yet-running student should not be waited for, else None."""

    ready = getattr(encoder, "ready", None)
    if ready is None or ready():
        return None
    try:
        encoder.start()
    except Exception:  # noqa: BLE001 - a failed start is an unavailable encoder, never a failed search
        return "encoder_unavailable", "the query student could not be started"
    remaining = box_s if deadline is None else deadline - time.monotonic()
    wait, probability = encoder.wait_decision(remaining, share)
    if wait:
        return None
    return "encoder_late", (f"the query student is starting (P(in time) {probability:.2f} for its weight share "
                            f"{share:.2f}: not waited for)")


def resolver_active(config: Any) -> bool:
    """The resolver runs only when a new space is switched on (else today's path, untouched)."""

    embedding = config.embedding
    return bool(config.source_retrieval.dense and (embedding.local.enabled or embedding.fallback.enabled))


def query_kind(*, roles: Sequence[str], context_text: str | None, rewritten: bool) -> str:
    """The query kind from existing features (§5.2): a role filter, a selection
    present (deictic), the conceptual rewrite, else a lookup."""

    if roles:
        return "role_filtered"
    if context_text:
        return "deictic"
    return "conceptual" if rewritten else "lookup"


@dataclass
class SpaceState:
    name: str
    kind: str
    status: str
    reason: str | None = None
    space_id: str | None = None
    price_per_million: float = 0.0
    #: extraction id -> {span id: document vector} (local and hosted spaces).
    vectors: dict[str, dict[str, np.ndarray]] = field(default_factory=dict)
    covered: set[str] = field(default_factory=set)
    expected: int = 0
    assigned: list[str] = field(default_factory=list)
    query: dict[str, Any] = field(default_factory=dict)
    #: The query encoder (a local space's teacher session or student), part of its list identity.
    encoder_id: str | None = None

    @property
    def usable(self) -> bool:
        return self.status in USABLE

    @property
    def list_key(self) -> str:
        """The list's immutable identity in the fusion model (Codex review F12)."""

        return fusion.list_key(self.name, self.space_id, self.encoder_id)

    def describe(self) -> dict[str, Any]:
        return {"kind": self.kind, "status": self.status, "reason": self.reason, "space_id": self.space_id,
                "list": self.list_key,
                "covered_sources": len(self.covered), "sources": self.expected,
                "assigned_sources": len(self.assigned), "query": dict(self.query)}


@dataclass
class Resolution:
    consumer: str
    query_kind: str
    spaces: dict[str, SpaceState]
    seed: dict[str, float]
    served: dict[str, float]
    learned: dict[str, float] | None
    weights_source: str
    rrf_k: float
    #: extraction id -> [(space, weight)] contributing to it.
    assignment: dict[str, list[tuple[str, float]]]
    posterior: Mapping[str, Any] | None = None
    receipt_id: str = ""
    exploration: dict[str, Any] = field(default_factory=dict)
    #: ``{record id: {list identity: rank}}`` of the contributing spaces' query lists.
    space_ranks: dict[str, dict[str, int]] = field(default_factory=dict)
    #: ``{list identity: P(selected)}`` under the Thompson draw and the
    #: assignment policy (empty under the seed).
    query_propensity: dict[str, float] = field(default_factory=dict)
    #: The joint probability that the policy selected exactly the lists it
    #: did (Codex re-review F18); None under the seed (not random).
    query_set_propensity: float | None = None
    #: The extractions some contributing space actually answered for (set by
    #: :func:`meaning_lists`; None before it ran): coverage counts these only.
    answered: set[str] | None = None
    owner_id: str = ""
    #: The identities of the lists available at resolve time (the fusion model's support).
    lists_available: list[str] = field(default_factory=list)

    def contributing(self) -> list[str]:
        return sorted({name for pairs in self.assignment.values() for name, _w in pairs})

    def queried(self) -> list[str]:
        """The identities of the lists whose query answered (set by :func:`meaning_lists`)."""

        return sorted(state.list_key for state in self.spaces.values() if state.query.get("answered"))

    @property
    def coverage(self) -> str:
        """``ready`` when every embeddable extraction in scope has a contributor
        that answered (Codex review F6: an assigned space whose query failed
        does not cover anything)."""

        expected = max((state.expected for state in self.spaces.values()), default=0)
        covered = len(self.answered) if self.answered is not None else len(self.assignment)
        if expected and covered >= expected:
            return "ready"
        return "partial" if covered else "incomplete"

    def describe(self) -> dict[str, Any]:
        return {"receipt_id": self.receipt_id, "consumer": self.consumer, "query_kind": self.query_kind,
                "coverage": self.coverage, "contributing": self.contributing(),
                "spaces": {name: state.describe() for name, state in sorted(self.spaces.items())},
                "weights": {"served": dict(self.served), "seed": dict(self.seed), "learned": self.learned,
                            "source": self.weights_source, "query_propensity": dict(self.query_propensity),
                            "query_set_propensity": self.query_set_propensity},
                "rrf_k": self.rrf_k, "exploration": dict(self.exploration)}


def _qwen_state(index: Any, price: float) -> SpaceState:
    status = "ok" if getattr(index, "status", None) == "ready" else (
        "partial" if getattr(index, "status", None) == "partial" else
        {"disabled": "disabled", "incomplete": "incomplete", "empty": "incomplete"}.get(
            str(getattr(index, "status", "disabled")), "disabled"))
    covered = {split_record_id(record_id)[0] for record_id in (getattr(index, "ids", None) or [])}
    return SpaceState(QWEN, "incumbent", status, getattr(index, "reason", None), getattr(index, "model_id", None),
                      price, covered=covered, expected=int(getattr(index, "sources", 0) or 0))


def _contextual_vectors(read: Callable[[str, Mapping[str, Sequence[tuple[str, int]]]], dict[str, np.ndarray]],
                        space_id: str, windows: Mapping[str, Sequence[Any]]) -> tuple[dict[str, dict[str, np.ndarray]], int]:
    from learnloop.source_retrieval.windows import expected_keys

    covered: dict[str, dict[str, np.ndarray]] = {}
    expected = 0
    for extraction_id, rows in windows.items():
        keys = expected_keys(space_id, rows)
        if not keys:
            continue
        expected += 1
        vectors = read(extraction_id, keys)
        if len(vectors) == len(keys):
            covered[extraction_id] = vectors
    return covered, expected


def _local_states(vault: LoadedVault, repository: Repository, windows: Mapping[tuple[str, str], Sequence[Any]],
                  known: Mapping[str, Mapping[str, Any]], *, deadline: float | None = None,
                  share: float = 0.0) -> dict[str, SpaceState]:
    from learnloop.local_embeddings.cache import CacheUnreadable, VectorCache, cache_path
    from learnloop.source_retrieval.local_index import LIST_NAMES, local_reason, local_spaces
    from learnloop.source_retrieval.windows import mean_vector

    names = (LOCAL_GROUPED, LOCAL_SINGLETON)
    manifest, reason = local_reason(vault)
    if manifest is None:
        return {name: SpaceState(name, "local", "disabled", reason) for name in names}
    encoder = LOCAL_QUERY_ENCODER(vault)
    states: dict[str, SpaceState] = {}
    for variant, (space, _pins) in local_spaces(manifest).items():
        name = LIST_NAMES[variant]
        row = known.get(space) or {}
        if row.get("status") in ("epoch_drift", "retired"):
            states[name] = SpaceState(name, "local", str(row["status"]), row.get("status_reason"), space)
            continue
        cache = VectorCache(cache_path(vault.root, space))

        def read(extraction_id: str, keys: Mapping[str, Sequence[tuple[str, int]]]) -> dict[str, np.ndarray]:
            flat = [key for parts in keys.values() for key, _w in parts]
            try:
                found = cache.vectors(flat)
            except CacheUnreadable:
                return {}
            out: dict[str, np.ndarray] = {}
            for span_id, parts in keys.items():
                if all(key in found for key, _w in parts):
                    vectors = [found[key] for key, _w in parts]
                    out[span_id] = (vectors[0] if len(vectors) == 1 else
                                    np.asarray(mean_vector(vectors, [w for _k, w in parts])))
            return out

        per_extraction = {extraction_id: rows for (extraction_id, kind), rows in windows.items() if kind == variant}
        covered, expected = _contextual_vectors(read, space, per_extraction)
        status, why = ("ok", None) if covered else ("incomplete", "no source in scope is fully indexed in this space")
        if covered and encoder is None:
            status, why = "encoder_unavailable", "no local query encoder (no query student adopted, or embedding.local.student is off)"
        elif covered:
            late = _cold_start(encoder, deadline=deadline, share=share,
                               box_s=float(vault.config.source_retrieval.retrieval_timeout_seconds))
            if late is not None:
                status, why = late
        states[name] = SpaceState(name, "local", status, why, space, 0.0, vectors=covered, covered=set(covered),
                                  expected=expected, encoder_id=getattr(encoder, "encoder_id", None))
    return states


def _voyage_state(vault: LoadedVault, repository: Repository,
                  windows: Mapping[tuple[str, str], Sequence[Any]]) -> SpaceState:
    from learnloop.source_retrieval import fallback_space

    reason = fallback_space.fallback_reason(vault.config)
    if reason is not None:
        return SpaceState(VOYAGE, "hosted", "disabled", reason)
    space, _pins = fallback_space.fallback_space(vault.config)
    price = float(vault.config.embedding.fallback.price_per_million)
    with closing(connect(Path(repository.sqlite_path), read_only=True)) as connection:
        def read(extraction_id: str, keys: Mapping[str, Sequence[tuple[str, int]]]) -> dict[str, np.ndarray]:
            return fallback_space.window_vectors(connection, space, extraction_id, keys)

        per_extraction = {extraction_id: rows for (extraction_id, kind), rows in windows.items() if kind == "grouped"}
        covered, expected = _contextual_vectors(read, space, per_extraction)
    status, why = ("ok", None) if covered else ("incomplete", "no source in scope is fully indexed in this space")
    return SpaceState(VOYAGE, "hosted", status, why, space, price, vectors=covered, covered=set(covered),
                      expected=expected)


def resolve_source_spaces(vault: LoadedVault, repository: Repository, scope: Scope, *, consumer: str,
                          query_kind: str, deadline: float | None, qwen_index: Any,
                          posteriors: Mapping[str, Mapping[str, Any]] | None = None,
                          receipt_id: str = "") -> Resolution:
    """The available spaces and their weights for one query, with every reason.

    ``receipt_id`` seeds the Thompson draw (a replay is reproducible)."""

    from learnloop.db.stores.retrieval_spaces import fusion_posteriors, spaces as known_spaces
    from learnloop.ops.embedding_backfill import PRICES_PER_MILLION
    from learnloop.source_retrieval.windows import windows_by_extraction

    config = vault.config
    extraction_ids = sorted(scope.extractions)
    qwen_price = config.source_retrieval.query_embedding_price_per_million
    qwen_price = float(qwen_price if qwen_price is not None else PRICES_PER_MILLION.get(config.embedding.model, 0.0))
    states: dict[str, SpaceState] = {QWEN: _qwen_state(qwen_index, qwen_price)}
    variants = ("grouped", "singleton") if config.embedding.local.enabled else ("grouped",)
    windows = (windows_by_extraction(vault, repository, extraction_ids, variants)
               if extraction_ids and (config.embedding.local.enabled or config.embedding.fallback.enabled) else {})
    with closing(connect(Path(repository.sqlite_path), read_only=True)) as connection:
        known = known_spaces(connection)
        if posteriors is None:
            posteriors = fusion_posteriors(connection)
    if config.embedding.local.enabled:
        share_lists = list(fusion.SPACE_LISTS)
        share_seed = fusion.seed_weights(config.embedding.source_space.default, share_lists)
        total = sum(share_seed.values()) or 1.0
        local_share = sum(share_seed.get(name, 0.0) for name in (LOCAL_GROUPED, LOCAL_SINGLETON)) / total
        states.update(_local_states(vault, repository, windows, known, deadline=deadline, share=local_share))
    else:
        states.update({name: SpaceState(name, "local", "disabled", "embedding.local.enabled is false")
                       for name in (LOCAL_GROUPED, LOCAL_SINGLETON)})
    states[VOYAGE] = _voyage_state(vault, repository, windows)
    if deadline is not None and time.monotonic() >= deadline:
        for state in states.values():
            if state.usable and state.kind != "incumbent":
                state.status, state.reason = "encoder_late", "the retrieval time box ran out"
    lists = list(fusion.SPACE_LISTS)
    seed = fusion.seed_weights(config.embedding.source_space.default, lists)
    posterior = fusion.posterior_for(posteriors or {}, consumer, query_kind)
    available = [name for name in lists if states[name].usable]
    keys = {name: states[name].list_key for name in available}
    by_key = fusion.learned_weights(posterior, [keys[name] for name in available])
    learned = None if by_key is None else {name: by_key[keys[name]] for name in available}
    served, source, propensity, set_propensity = dict(seed), "seed", {}, None
    rrf_k = float(config.source_retrieval.rrf_k)

    def assign(weights: Mapping[str, float]) -> dict[str, list[tuple[str, float]]]:
        """The coverage assignment: each extraction to its positively weighted
        covering spaces, else to the cheapest covering stand-in."""

        top = max(weights.values(), default=0.0)
        result: dict[str, list[tuple[str, float]]] = {}
        for extraction_id in extraction_ids:
            candidates = [name for name in available if extraction_id in states[name].covered]
            if not candidates:
                continue
            weighted = [(name, weights[name]) for name in candidates if weights[name] > 0]
            if not weighted:
                stand_in = min(candidates, key=lambda name: (states[name].price_per_million, name))
                weighted = [(stand_in, top or 1.0)]
            result[extraction_id] = weighted
        return result

    def selected(assignment: Mapping[str, Sequence[tuple[str, float]]]) -> frozenset[str]:
        return frozenset(keys[name] for pairs in assignment.values() for name, _w in pairs)

    if config.embedding.source_space.learned_fusion:
        # §5.2 (Codex review F7, F14): a Thompson draw, seeded by the receipt,
        # at the posterior's own rrf_k.
        drawn = fusion.thompson_weights(posterior, [keys[name] for name in available],
                                        seed=fusion.rng_seed(receipt_id or "unseeded"))
        if drawn is not None:
            served = {name: (drawn.get(keys[name], 0.0) if name in keys else 0.0) for name in lists}
            source = "learned"
            rrf_k = float((posterior or {}).get("rrf_k") or rrf_k)
    assignment = assign(served)
    if source == "learned":
        # Codex re-review F18: the logged probability is the joint one of the
        # set this policy selected (the assignment above applied to a draw,
        # the forced stand-in included), under the posterior's covariance.
        def policy(positive: frozenset[str]) -> frozenset[str]:
            return selected(assign({name: (1.0 if name in keys and keys[name] in positive else 0.0)
                                    for name in lists}))

        set_propensity, propensity = fusion.selection_propensity(
            posterior, [keys[name] for name in available], policy, selected(assignment),
            seed=fusion.rng_seed((receipt_id or "unseeded") + ":selection"))
    for extraction_id, pairs in assignment.items():
        for name, _w in pairs:
            states[name].assigned.append(extraction_id)
    return Resolution(consumer, query_kind, states, seed, served, learned, source, rrf_k, assignment, posterior,
                      receipt_id=receipt_id, query_propensity=dict(propensity),
                      query_set_propensity=set_propensity,
                      lists_available=[keys[name] for name in available])


def _rank(vectors: Mapping[str, Mapping[str, np.ndarray]], extraction_ids: Sequence[str], query: np.ndarray, *,
          limit: int, allow: Callable[[str], bool]) -> list[str]:
    """Plain cosine over a contextual space's covered blocks (E1's transform), ties by record id."""

    ids, rows = [], []
    for extraction_id in sorted(extraction_ids):
        for span_id, vector in sorted((vectors.get(extraction_id) or {}).items()):
            ids.append(block_record_id(extraction_id, span_id))
            rows.append(np.asarray(vector, dtype=np.float64))
    if not ids or limit <= 0:
        return []
    matrix = np.stack(rows)
    q = np.asarray(query, dtype=np.float64)
    if q.ndim != 1 or q.size != matrix.shape[1]:
        raise ValueError("query dimension does not match the space")
    norms = np.linalg.norm(matrix, axis=1)
    unit = np.divide(matrix, norms[:, None], out=np.zeros_like(matrix), where=norms[:, None] != 0)
    qn = float(np.linalg.norm(q))
    scores = unit @ (q / qn) if qn else np.zeros(len(ids))
    order = sorted(range(len(ids)), key=lambda index: (-scores[index], ids[index]))
    ranked = []
    for index in order:
        if allow(ids[index]):
            ranked.append(ids[index])
            if len(ranked) >= limit:
                break
    return ranked


def meaning_lists(vault: LoadedVault, repository: Repository, resolution: Resolution, texts: Mapping[str, str], *,
                  qwen_index: Any, qwen_vectors: Callable[[], tuple[dict[str, np.ndarray], dict[str, Any]]],
                  depth: Callable[[str], int], permit: Callable[[str], bool], owner_id: str,
                  deadline: float | None, budget: Any | None = None) -> dict[str, Any]:
    """Each contributing space's ranking per query text, and the fused lists.

    A space whose query does not answer (its encoder is unavailable, its
    request failed, timed out or was over budget) covers nothing: the
    extractions it alone was serving are reassigned to the cheapest other
    available space that covers them, within the remaining time box and the
    caller's budget, and that space is queried (Codex review F6).
    ``resolution.answered`` records the extractions some answered query covers.

    Returns ``{"fused": {key: [record ids]}, "per_space": {space: {key: [record ids]}},
    "ends": {key: bool}, "qwen_query": status or None}``."""

    from learnloop.source_retrieval import fallback_space

    per_space: dict[str, dict[str, list[str]]] = {}
    qwen_query: dict[str, Any] | None = None
    notes: list[str] = []
    list_name = {"query": "meaning", "rewrite": "rewrite_meaning"}
    tried: set[str] = set()
    failed: set[str] = set()

    def late() -> bool:
        return deadline is not None and time.monotonic() >= deadline

    def query(name: str) -> dict[str, np.ndarray]:
        nonlocal qwen_query
        state = resolution.spaces[name]
        if name == QWEN:
            vectors, qwen_query = qwen_vectors()
            state.query = {"status": (qwen_query or {}).get("status")}
            return vectors
        if name == VOYAGE:
            client, why = fallback_space.fallback_client(vault)
            vectors, status = (fallback_space.query_vectors(vault, repository, texts, client=client, owner_id=owner_id,
                                                            deadline=deadline, budget=budget)
                               if client is not None else ({}, {"status": "unavailable", "reason": why, "paid": False}))
            state.query = status
            return vectors
        encoder = LOCAL_QUERY_ENCODER(vault)
        if encoder is None:
            state.query = {"status": "encoder_unavailable"}
            return {}
        keys = sorted(texts)
        try:
            encoded = _encode(encoder, [texts[key] for key in keys], deadline=deadline,
                              receipt_id=resolution.receipt_id)
        except Exception as exc:  # noqa: BLE001 - an encoder failure is a reason, never a failed search
            state.query = {"status": "encoder_failed", "error_type": type(exc).__name__, "paid": False}
            return {}
        state.query = {"status": "encoded", "encoder_id": getattr(encoder, "encoder_id", None), "paid": False}
        return {key: np.asarray(vector, dtype=np.float64) for key, vector in zip(keys, encoded, strict=True)}

    pending = resolution.contributing()
    while pending:
        for name in pending:
            tried.add(name)
            state = resolution.spaces[name]
            if late() and name != QWEN:
                state.status, state.reason = "encoder_late", "the retrieval time box ran out"
                failed.add(name)
                continue
            vectors = query(name)
            if not vectors:
                failed.add(name)
                if state.status in USABLE:
                    state.status = "encoder_unavailable"
                    state.reason = f"its query did not answer ({state.query.get('status')})"
                continue
            assigned = set(state.assigned)

            def allow(record_id: str, _assigned: set[str] = assigned) -> bool:
                return split_record_id(record_id)[0] in _assigned and permit(record_id)

            for key, vector in vectors.items():
                name_for_depth = list_name.get(key, key)
                try:
                    if name == QWEN:
                        ranked = [record_id for record_id, _score in
                                  qwen_index.rank(vector, limit=depth(name_for_depth), allow=allow)]
                    else:
                        ranked = _rank(state.vectors, sorted(assigned), vector, limit=depth(name_for_depth),
                                       allow=allow)
                except ValueError:
                    notes.append(f"{name_for_depth} ({name}): the query vector does not match the space's width")
                    continue
                per_space.setdefault(name, {})[key] = ranked
            if name not in per_space:
                failed.add(name)
            else:
                state.query["answered"] = True
        # Reassign what only failed spaces were serving (cheapest covering
        # stand-in not yet tried, at the weight of the space it replaces).
        pending = []
        if late():
            break
        for extraction_id, pairs in resolution.assignment.items():
            if any(name not in failed for name, _w in pairs):
                continue
            candidates = [name for name, state in resolution.spaces.items()
                          if state.usable and name not in tried and extraction_id in state.covered]
            if not candidates:
                continue
            stand_in = min(candidates, key=lambda name: (resolution.spaces[name].price_per_million, name))
            pairs.append((stand_in, max((weight for _n, weight in pairs), default=0.0) or 1.0))
            resolution.spaces[stand_in].assigned.append(extraction_id)
            if stand_in not in pending:
                pending.append(stand_in)
    resolution.answered = {extraction_id for extraction_id, pairs in resolution.assignment.items()
                           if any(name in per_space for name, _w in pairs)}
    fused: dict[str, list[str]] = {}
    ends: dict[str, bool] = {}
    for key in texts:
        lists = {name: ranked[key] for name, ranked in per_space.items() if key in ranked}
        if not lists:
            continue
        scores: dict[str, float] = {}
        for name, ranked in lists.items():
            for position, record_id in enumerate(ranked, start=1):
                extraction_id = split_record_id(record_id)[0]
                weight = dict(resolution.assignment.get(extraction_id, ())).get(name, 0.0)
                scores[record_id] = scores.get(record_id, 0.0) + weight / (resolution.rrf_k + position)
        limit = depth(list_name.get(key, key))
        fused[key] = sorted(scores, key=lambda record_id: (-scores[record_id], record_id))[:limit]
        ends[key] = all(len(ranked) < limit for ranked in lists.values())
    return {"fused": fused, "per_space": per_space, "ends": ends, "qwen_query": qwen_query, "notes": notes}


def space_ranks(per_space: Mapping[str, Mapping[str, Sequence[str]]], key: str = "query", *,
                identities: Mapping[str, str] | None = None) -> dict[str, dict[str, int]]:
    """``{record id: {list identity: rank}}`` in each space's ``key`` list (the
    fusion model's features); ``identities`` maps a space name to its list
    identity (Codex review F12), else the name is used."""

    ranks: dict[str, dict[str, int]] = {}
    for name, lists in per_space.items():
        label = (identities or {}).get(name, name)
        for position, record_id in enumerate(lists.get(key) or [], start=1):
            ranks.setdefault(record_id, {})[label] = position
    return ranks


__all__ = ["LOCAL_GROUPED", "LOCAL_QUERY_ENCODER", "LOCAL_SINGLETON", "LocalQueryEncoder", "PAID_QUERY_SPACES", "QWEN", "Resolution",
           "SpaceState", "VOYAGE", "meaning_lists", "query_kind", "resolve_source_spaces", "resolver_active",
           "space_ranks"]
