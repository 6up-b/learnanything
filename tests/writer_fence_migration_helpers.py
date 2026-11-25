"""Exact schema additions made by the writer fence's migration (275) for cross-migration diff tests."""

from learnloop.db.writer_fence import GUARDED

WRITER_FENCE_OBJECTS = frozenset(
    {"writer_fence", "writer_fence_no_delete"}
    | {f"writer_fence_{table}_{event.lower()}" for table, event in GUARDED}
)
