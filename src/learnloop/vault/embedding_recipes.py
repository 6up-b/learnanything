"""Declared, versioned recipes for canonical text sent to embedding providers.

Recipes are not evidence and do not inspect attempts, answers or learner state.
Adding a record kind means declaring its text here, not guessing in a caller.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType

from learnloop.vault.models import LoadedVault


@dataclass(frozen=True)
class EmbeddingRecord:
    record_kind: str
    record_id: str
    field: str
    text: str
    content_hash: str


@dataclass(frozen=True)
class EmbeddingRecipe:
    record_kind: str
    field: str
    version: int
    text_recipe: str
    texts: Callable[[LoadedVault], Iterator[tuple[str, str]]]

    def records(self, loaded: LoadedVault) -> Iterator[EmbeddingRecord]:
        for record_id, text in self.texts(loaded):
            if not text.strip():
                continue
            # Version the composition, not just the authored text: a future
            # recipe change must not silently reuse the former representation.
            payload = json.dumps(
                [self.record_kind, self.field, self.version, text],
                ensure_ascii=False, separators=(",", ":"),
            )
            yield EmbeddingRecord(
                self.record_kind, record_id, self.field, text,
                hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            )


def _facet_definitions(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for facet_id, facet in sorted(loaded.evidence_facets.items()):
        if facet.status == "retired":
            continue
        parts = [
            f"{label}: {value}" for label, value in (
                ("Title", facet.title), ("Claim", facet.claim),
                ("Description", facet.description),
            ) if value and value.strip()
        ]
        for label, values in (
            ("Preconditions", facet.preconditions),
            ("Postconditions", facet.postconditions),
            ("Applicability", facet.applicability),
            ("Positive examples", facet.positive_examples),
            ("Negative examples", facet.negative_examples),
            ("Non-goals", facet.non_goals),
        ):
            if values:
                parts.append(f"{label}:\n" + "\n".join(f"- {value}" for value in values))
        yield facet_id, "\n".join(parts)


def _item_stems(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for item_id, item in sorted(loaded.practice_items.items()):
        if item.status != "retired":
            yield item_id, item.prompt


RECORD_KIND_RECIPES: Mapping[str, EmbeddingRecipe] = MappingProxyType({
    "facet": EmbeddingRecipe(
        "facet", "definition", 1,
        "Authored title, claim, description, pre/postconditions, applicability, "
        "positive/negative examples and non-goals; excludes retired facets.",
        _facet_definitions,
    ),
    "item": EmbeddingRecipe(
        "item", "stem", 1,
        "Canonical practice item prompt only; excludes retired items, expected "
        "answers, hints, grading material and learner responses.",
        _item_stems,
    ),
})


def embedding_records(
    loaded: LoadedVault, record_kinds: tuple[str, ...] = ("facet", "item"),
) -> list[EmbeddingRecord]:
    unknown = set(record_kinds) - RECORD_KIND_RECIPES.keys()
    if unknown:
        raise ValueError(f"Unknown embedding record kinds: {', '.join(sorted(unknown))}")
    return [
        record
        for kind in sorted(set(record_kinds))
        for record in RECORD_KIND_RECIPES[kind].records(loaded)
    ]
