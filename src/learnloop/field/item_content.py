"""Read-only T8 content index: the text each attempt showed, and its stored vectors.

The text follows the outcome view's revision status: an ``exact`` row uses the
graded item snapshot's prompt, an explicitly ``reconstructed_current`` row the
current prompt, and an ``excluded`` row has none. A vector is used only when
one is stored for exactly that text (the recipe content hash), the configured
model and the document prefix; the current text's vector is never substituted
for an edited prompt. Nothing here calls a model or writes, and the coverage
report is aggregate-only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
import sqlite3

import numpy as np

from learnloop.db.stores.embedding_vectors import get_vector
from learnloop.field.evaluation import _eligible
from learnloop.field.success_head import (
    EMBEDDING_DIMENSIONS, SKELETON_VIEW, SOLVER_PANEL, STEM_VIEW, AttemptContent, ContentIndex,
)
from learnloop.field.types import AttemptRow
from learnloop.vault.embedding_recipes import EMBEDDING_RECIPES, EmbeddingRecord
from learnloop.vault.models import LoadedVault, PracticeItem


TASK_PREFIX = "retrieval-document"


def _table_exists(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,),
    ).fetchone() is not None


def mrl_view(vector: np.ndarray, dimensions: int) -> tuple[float, ...] | None:
    """A fixed projection: the first ``dimensions`` MRL dimensions, L2-normalized."""
    if vector.size < dimensions:
        raise ValueError("stored vectors are narrower than the T8 embedding view")
    prefix = np.asarray(vector[:dimensions], dtype=np.float64)
    norm = float(np.linalg.norm(prefix))
    return None if not np.isfinite(norm) or norm <= 1e-12 else tuple(float(v) for v in prefix / norm)


def _kcs(loaded: LoadedVault, lo_id: str, item: PracticeItem | None) -> tuple[str, ...]:
    names = []
    lo = loaded.learning_objects.get(lo_id)
    if lo is not None and lo.title.strip():
        names.append(lo.title.strip())
    for facet_id in (item.evidence_facets if item is not None else ()):
        facet = loaded.evidence_facets.get(loaded.canonical_facet_id(facet_id))
        if facet is not None and facet.title and facet.title.strip() and facet.title.strip() not in names:
            names.append(facet.title.strip())
    return tuple(names)


def _seen_items(connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow]):
    """Yield ``(row, item revision the attempt showed or None, source)``."""
    has_snapshots = _table_exists(connection, "practice_item_snapshots")
    snapshots: dict[str, PracticeItem | None] = {}

    def snapshot(digest: str) -> PracticeItem | None:
        if digest not in snapshots:
            stored = connection.execute(
                "SELECT item_json FROM practice_item_snapshots WHERE content_hash=?", (digest,),
            ).fetchone() if has_snapshots else None
            snapshots[digest] = PracticeItem.model_validate_json(stored[0]) if stored else None
        return snapshots[digest]

    for row in attempts:
        if row.revision_status == "exact" and row.item_snapshot_hash:
            yield row, snapshot(row.item_snapshot_hash), "exact_snapshot"
        elif row.revision_status == "reconstructed_current":
            yield row, loaded.practice_items.get(row.features.item_id), "current_content"
        else:
            yield row, None, "unavailable"


def seen_stem_records(
    connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow],
) -> list[EmbeddingRecord]:
    """``item/stem`` records for the exact text each scored attempt showed.

    Retired items and earlier wordings are included: the recipe's current
    records skip them, but T8 replays history. Retrieval reads only current
    content hashes, so these vectors never enter a live index.
    """
    recipe = EMBEDDING_RECIPES["item/stem"]
    records = {}
    for row, item, _ in _seen_items(connection, loaded, attempts):
        if item is None or not item.prompt.strip() or not _eligible(row):
            continue
        record = EmbeddingRecord("item", row.features.item_id, "stem", item.prompt,
                                 recipe.content_hash(item.prompt))
        records.setdefault((record.record_id, record.content_hash), record)
    return [records[key] for key in sorted(records)]


def load_content_index(
    connection: sqlite3.Connection, loaded: LoadedVault, attempts: Iterable[AttemptRow], *,
    dimensions: int = EMBEDDING_DIMENSIONS,
) -> tuple[ContentIndex, dict]:
    """Return ``(index, aggregate coverage)`` for these replay rows, in one snapshot."""
    model = loaded.config.embedding.model
    stem_recipe = EMBEDDING_RECIPES["item/stem"]
    skeleton_recipe = EMBEDDING_RECIPES.get("item/skeleton")
    has_vectors = _table_exists(connection, "embedding_vectors")
    skeleton_hashes: dict[str, str] = {}
    if skeleton_recipe is not None:
        # PF-b skeletons describe the CURRENT item content, so they apply only
        # to attempts that saw exactly the current prompt.
        skeleton_hashes = {record.record_id: record.content_hash
                           for record in skeleton_recipe.records(loaded)}

    def vector(record_id: str, field: str, content_hash: str) -> tuple[float, ...] | None:
        if not has_vectors:
            return None
        stored = get_vector(connection, record_kind="item", record_id=record_id, field=field,
                            content_hash=content_hash, model_id=model, task_prefix=TASK_PREFIX)
        return None if stored is None else mrl_view(stored, dimensions)

    entries: dict[tuple[str, str], AttemptContent] = {}
    ambiguous: set[tuple[str, str]] = set()
    coverage = defaultdict(Counter)
    solver_panel = Counter()
    for row, item, source in _seen_items(connection, loaded, attempts):
        f = row.features
        key = (f.item_id, f.observed_at)
        stem = item.prompt if item is not None and item.prompt.strip() else None
        vectors = {}
        if stem is not None:
            stem_vector = vector(f.item_id, "stem", stem_recipe.content_hash(stem))
            if stem_vector is not None:
                vectors[STEM_VIEW] = stem_vector
            current = loaded.practice_items.get(f.item_id)
            skeleton_hash = skeleton_hashes.get(f.item_id)
            if skeleton_hash and current is not None and current.prompt == stem:
                skeleton_vector = vector(f.item_id, "skeleton", skeleton_hash)
                if skeleton_vector is not None:
                    vectors[SKELETON_VIEW] = skeleton_vector
        content = AttemptContent(stem=stem, stem_source=source if stem is not None else "unavailable",
                                 kcs=_kcs(loaded, f.lo_id, item), vectors=vectors)
        if key in entries and entries[key] != content:
            ambiguous.add(key)
        entries[key] = content
        counts = coverage[row.revision_status]
        counts["attempts"] += 1
        counts["positive_mass"] += row.effective_mass > 0
        counts["seen_text"] += stem is not None
        counts["stem_vector"] += STEM_VIEW in vectors
        counts["skeleton_vector"] += SKELETON_VIEW in vectors
        solver_panel["attempts"] += 1
        solver_panel["solver_panel"] += f.difficulty_source == SOLVER_PANEL
    for key in ambiguous:
        # Two attempts with one identity but different content: never guess.
        entries[key] = AttemptContent(kcs=entries[key].kcs)
    views = (STEM_VIEW, SKELETON_VIEW) if skeleton_recipe is not None else (STEM_VIEW,)
    index = ContentIndex(entries, embedding_model=model, views=views, dimensions=dimensions)
    report = {
        "embedding_model": model, "task_prefix": TASK_PREFIX, "dimensions": dimensions,
        "projection": "mrl_prefix_l2", "views": list(views),
        "skeleton": ("available: item/skeleton recipe registered" if skeleton_recipe is not None
                     else "unavailable: no item/skeleton recipe (PF-b not landed)"),
        "vectors_table": has_vectors, "ambiguous_attempt_identities": len(ambiguous),
        "by_revision_status": {status: dict(sorted(counts.items()))
                               for status, counts in sorted(coverage.items())},
        "difficulty": {"attempts": solver_panel["attempts"],
                       "solver_panel": solver_panel["solver_panel"],
                       "source_rule": "solver_panel only; LLM-labelled difficulty is never used"},
        "content_digest": index.digest,
    }
    return index, report
