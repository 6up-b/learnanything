"""Item-text neighbours for the knowledge map (Slice 2 T7; display only).

Ranks practice items by their stored ``item/stem`` vectors (Slice A Phase 1
substrate). It reads the vector store and nothing else: no embedding client is
built, no model is called and nothing is written. No scheduling, scoring or
evidence path reads the result. Items whose current stem has no stored vector
for ``embedding.model`` are absent from the result, so the map keeps their
facet/concept-graph neighbours.
"""
from __future__ import annotations

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
    model_id: str
    # Items with a current stem to embed (the recipe skips retired items).
    stems: int = 0
    neighbors: dict[str, list[tuple[str, float]]] = field(default_factory=dict)

    @property
    def embedded(self) -> int:
        """Items whose current stem has a stored vector for ``model_id``."""
        return len(self.neighbors)

    def summary(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "model_id": self.model_id,
            "stems": self.stems,
            "embedded": self.embedded,
        }


def item_text_neighbors(vault: LoadedVault, sqlite_path: Path, *, limit: int) -> ItemTextNeighbors:
    """Top ``limit`` item-text neighbours of every item with a current stem vector.

    Similarity is the store's mean-centred cosine among the covered items
    (``nearest_among_current``). Vectors of other models, of edited stems
    (stale content hash) and of other task prefixes are ignored.
    """

    config = vault.config.embedding
    if not config.map_neighbors_enabled:
        return ItemTextNeighbors(enabled=False, model_id=config.model)
    expected = {record.record_id: record.content_hash for record in _STEM.records(vault)}
    if len(expected) < 2:
        return ItemTextNeighbors(enabled=True, model_id=config.model, stems=len(expected))
    # Imported here: the store needs numpy, which sidecar start-up does not load.
    from learnloop.db.stores.embedding_vectors import nearest_among_current
    from learnloop.ops.embedding_backfill import TASK_PREFIX

    with closing(connect(sqlite_path, read_only=True)) as connection:
        matches = nearest_among_current(
            connection,
            record_kind=_STEM.record_kind,
            field=_STEM.field,
            model_id=config.model,
            task_prefix=TASK_PREFIX,
            expected_records=expected,
            limit=limit,
        )
    return ItemTextNeighbors(
        enabled=True,
        model_id=config.model,
        stems=len(expected),
        neighbors={
            item_id: [(match.record_id, match.score) for match in ranked]
            for item_id, ranked in matches.items()
        },
    )
