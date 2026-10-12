"""Item-text neighbours for the knowledge map (Slice 2 T7; display only).

Ranks practice items by their stored ``item/stem`` vectors (Slice A Phase 1
substrate). It reads the vector store and nothing else: no embedding client is
built, no model is called and nothing is written. No scheduling, scoring or
evidence path reads the result. Items whose current stem has no stored vector
for the ranking model are absent from the result, so the map keeps their
facet/concept-graph neighbours.

``embedding.model`` is the model the backfill embeds with. The model that
ranks the spokes moves to it only once it has re-embedded every current stem
that any other stored model covers (Slice 2 §4: a full re-embed before
retrieval moves to a new model). Until then the best-covered previous model
keeps ranking, and the summary names the pending one. After that, an edited or
added stem is missing for every model alike, so the active model stays and only
that item falls back.
"""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

from learnloop.db.connection import connect
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES
from learnloop.vault.models import LoadedVault

_STEM = EMBEDDING_RECIPES["item/stem"]


@dataclass(frozen=True)
class ItemTextNeighbors:
    """Per-item ``(neighbour id, similarity)`` lists plus their coverage."""

    enabled: bool
    # The model whose vectors rank the spokes; ``embedding.model`` when no
    # stored model covers any current stem.
    model_id: str
    # Items with a current stem to embed (the recipe skips retired items).
    stems: int = 0
    # Items whose current stem has a stored vector for ``model_id``, counted
    # whether or not there are enough of them to rank.
    embedded: int = 0
    neighbors: dict[str, list[tuple[str, float]]] = field(default_factory=dict)
    # ``embedding.model`` and its current coverage while its re-embed has not
    # yet caught up with ``model_id`` (otherwise None).
    pending_model_id: str | None = None
    pending_embedded: int = 0

    def summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "model_id": self.model_id,
            "stems": self.stems,
            "embedded": self.embedded,
            "pending_model": None if self.pending_model_id is None else {
                "model_id": self.pending_model_id,
                "embedded": self.pending_embedded,
            },
        }


def ranking_model(configured: str, coverage: Mapping[str, frozenset[str]]) -> str | None:
    """The model whose stored vectors rank the spokes (Slice 2 §4).

    ``configured`` (``embedding.model``) ranks once its current stems include
    every current stem of each other stored model, which a completed backfill
    guarantees. Until then the other model with the most current stems keeps
    ranking (ties go to the smaller model ID). ``None`` when nothing is covered.
    """
    own = coverage.get(configured, frozenset())
    others = {model: ids for model, ids in coverage.items() if model != configured and ids}
    if all(ids <= own for ids in others.values()):
        return configured if own else None
    return min(others, key=lambda model: (-len(others[model]), model))


def item_text_neighbors(vault: LoadedVault, sqlite_path: Path, *, limit: int) -> ItemTextNeighbors:
    """Top ``limit`` item-text neighbours of every item with a current stem vector.

    Similarity is the store's mean-centred cosine among the covered items of
    the ranking model (``nearest_among_current``). Vectors of other models, of
    edited stems (stale content hash) and of other task prefixes never mix in.
    """

    config = vault.config.embedding
    if not config.map_neighbors_enabled:
        return ItemTextNeighbors(enabled=False, model_id=config.model)
    expected = {record.record_id: record.content_hash for record in _STEM.records(vault)}
    if not expected:
        return ItemTextNeighbors(enabled=True, model_id=config.model)
    # Imported here: the store needs numpy, which sidecar start-up does not load.
    from learnloop.db.stores.embedding_vectors import current_records_by_model, nearest_among_current
    from learnloop.ops.embedding_backfill import TASK_PREFIX

    with closing(connect(sqlite_path, read_only=True)) as connection:
        coverage = current_records_by_model(
            connection, record_kind=_STEM.record_kind, field=_STEM.field,
            task_prefix=TASK_PREFIX, expected_records=expected,
        )
        model = ranking_model(config.model, coverage)
        covered = coverage.get(model, frozenset()) if model is not None else frozenset()
        matches = {} if model is None or len(covered) < 2 else nearest_among_current(
            connection,
            record_kind=_STEM.record_kind,
            field=_STEM.field,
            model_id=model,
            task_prefix=TASK_PREFIX,
            expected_records=expected,
            limit=limit,
        )
    pending = model is not None and model != config.model
    return ItemTextNeighbors(
        enabled=True,
        model_id=model if model is not None else config.model,
        stems=len(expected),
        embedded=len(covered),
        neighbors={
            item_id: [(match.record_id, match.score) for match in ranked]
            for item_id, ranked in matches.items()
        },
        pending_model_id=config.model if pending else None,
        pending_embedded=len(coverage.get(config.model, frozenset())) if pending else 0,
    )
