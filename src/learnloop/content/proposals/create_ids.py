"""Deterministic names for anonymous wire creates, before target validation."""
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from learnloop.ids import snake_case

_PREFIXES = {"learning_object": "lo", "practice_item": "pi", "concept": "concept"}
_reservations: ContextVar[Callable[[], Iterable[str]] | None] = ContextVar("authoring_create_ids", default=None)


@contextmanager
def reserve_create_ids(read_ids: Callable[[], Iterable[str]]) -> Iterator[None]:
    """Supply vault reservations without putting local state in the wire schema/prompt."""
    token = _reservations.set(read_ids)
    try:
        yield
    finally:
        _reservations.reset(token)


@contextmanager
def reserve_vault_create_ids(root: str | Path) -> Iterator[None]:
    def existing_ids() -> set[str]:
        from learnloop.vault.loader import load_vault

        vault = load_vault(Path(root))
        return (set(vault.learning_objects) | set(vault.practice_items) | set(vault.concepts)
                | set(vault.error_types) | set(vault.evidence_facets) | {edge.id for edge in vault.edges})

    # The full vault, not the subject-filtered prompt, must reserve names before the answer is checkpointed.
    with reserve_create_ids(existing_ids):
        yield


def _blank(value: Any) -> bool:
    return value is None or isinstance(value, str) and not value.strip()


def mint_create_ids(data: Any, context: Any = None) -> Any:
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        return data
    unnamed = []
    used = set()
    for index, item in enumerate(data["items"]):
        if not isinstance(item, dict):
            proposed = getattr(item, "proposed_entity_id", None)
            payload_id = getattr(getattr(item, "payload", None), "id", None)
        else:
            payload = item.get("payload")
            proposed = item.get("proposed_entity_id")
            payload_id = payload.get("id") if isinstance(payload, dict) else getattr(payload, "id", None)
            if (item.get("operation") == "create" and isinstance(item.get("item_type"), str)
                    and item["item_type"] in _PREFIXES
                    and isinstance(payload, dict) and _blank(proposed) and _blank(payload_id)):
                unnamed.append(index)
        # Later named rows must win too; reserving only the preceding rows can rename a model's ID.
        used.update(value for value in (proposed, payload_id) if isinstance(value, str) and not _blank(value))
    if not unnamed:
        return data
    read_ids = _reservations.get()
    if read_ids is not None:
        used.update(read_ids())
    if isinstance(context, dict):
        used.update(context.get("existing_entity_ids", ()))
    items = list(data["items"])
    for index in unnamed:
        item = items[index]
        fingerprint = json.dumps([index, item], sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = sha256(fingerprint.encode()).hexdigest()[:20]
        slug = snake_case(str(item.get("client_item_id", "")))
        slug = "".join(char for char in slug if char.isascii())[:40].strip("_") or "unnamed"
        base = f"{_PREFIXES[item['item_type']]}_{slug}_{digest}"
        candidate, suffix = base, 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        used.add(candidate)
        items[index] = {**item, "proposed_entity_id": candidate, "payload": {**item["payload"], "id": None}}
    return {**data, "items": items}
