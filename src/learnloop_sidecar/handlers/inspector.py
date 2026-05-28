from __future__ import annotations

import re
from typing import Any

from learnloop_sidecar.context import SidecarContext
from learnloop_sidecar.dto import ParamsModel, versioned
from learnloop_sidecar.handlers.serializers import (
    attempt_detail,
    error_event_dto,
    learning_object_detail,
    practice_item_detail,
)
from learnloop_sidecar.registry import method


class InspectInput(ParamsModel):
    id: str


@method("inspect_entity", InspectInput)
def inspect_entity(ctx: SidecarContext, params: InspectInput) -> dict[str, Any]:
    vault, repository = ctx.require_vault()
    if params.id in vault.practice_items:
        return versioned({"kind": "practice_item", "id": params.id, "detail": practice_item_detail(vault, repository, params.id)})
    if params.id in vault.learning_objects:
        return versioned(
            {"kind": "learning_object", "id": params.id, "detail": learning_object_detail(vault, repository, params.id)}
        )
    record = repository.find_record(params.id)
    if record is not None:
        kind, payload = record
        if kind == "practice_attempt":
            return versioned({"kind": "attempt", "id": params.id, "detail": attempt_detail(vault, repository, params.id)})
        if kind == "error_event":
            return versioned({"kind": "error_event", "id": params.id, "detail": error_event_dto(vault, payload)})
    return versioned({"kind": "not_found", "id": params.id, "suggestions": _search_suggestions(vault, params.id)})


def _search_suggestions(vault: Any, query: str) -> list[dict[str, Any]]:
    normalized_query = _normalize(query)
    if not normalized_query:
        return []

    suggestions: list[dict[str, Any]] = []
    for item in vault.practice_items.values():
        learning_object = vault.learning_object_for_item(item)
        title = learning_object.title if learning_object is not None else item.learning_object_id
        score = max(
            _match_score(normalized_query, item.id),
            _match_score(normalized_query, title),
            _match_score(normalized_query, item.practice_mode),
            _match_score(normalized_query, " ".join(item.tags)),
            _match_score(normalized_query, item.prompt),
        )
        if score > 0:
            suggestions.append(
                {
                    "kind": "practice_item",
                    "id": item.id,
                    "title": title,
                    "subtitle": item.practice_mode,
                    "score": score,
                }
            )

    for learning_object in vault.learning_objects.values():
        score = max(
            _match_score(normalized_query, learning_object.id),
            _match_score(normalized_query, learning_object.title),
            _match_score(normalized_query, learning_object.summary),
            _match_score(normalized_query, " ".join(learning_object.tags)),
        )
        if score > 0:
            suggestions.append(
                {
                    "kind": "learning_object",
                    "id": learning_object.id,
                    "title": learning_object.title,
                    "subtitle": learning_object.knowledge_type,
                    "score": score,
                }
            )

    suggestions.sort(key=lambda item: (-item["score"], item["kind"] != "practice_item", item["id"]))
    return suggestions[:12]


def _match_score(query: str, value: str | None) -> float:
    haystack = _normalize(value or "")
    if not haystack:
        return 0.0
    if haystack == query:
        return 1.0
    if haystack.startswith(query):
        return 0.92
    if query in haystack:
        return 0.8 + min(0.1, len(query) / max(len(haystack), 1))
    if all(token and any(part.startswith(token) for part in haystack.split()) for token in query.split()):
        return 0.68
    subsequence = _subsequence_score(query, haystack)
    if subsequence > 0:
        return 0.45 + subsequence * 0.2
    return 0.0


def _subsequence_score(query: str, haystack: str) -> float:
    index = -1
    span_start: int | None = None
    for char in query:
        index = haystack.find(char, index + 1)
        if index < 0:
            return 0.0
        if span_start is None:
            span_start = index
    if span_start is None:
        return 0.0
    span = index - span_start + 1
    return len(query) / max(span, 1)


def _normalize(value: str) -> str:
    return " ".join(part for part in re.split(r"[^a-z0-9]+", value.lower()) if part)
