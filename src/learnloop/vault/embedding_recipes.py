"""Declared, versioned recipes for canonical text sent to embedding providers.

Recipes are not evidence and do not inspect attempts, answers or learner state.
Adding a record kind or field means declaring its text here, not guessing in a
caller. A recipe is named ``record_kind/field`` (Slice 2 R3/§12: ``item/stem``,
``item/skeleton``, ``facet/dossier_scope`` ...), so one kind can carry several
independently versioned fields.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
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

    @property
    def name(self) -> str:
        return f"{self.record_kind}/{self.field}"

    def content_hash(self, text: str) -> str:
        # Version the composition, not just the authored text: a future
        # recipe change must not silently reuse the former representation.
        payload = json.dumps(
            [self.record_kind, self.field, self.version, text],
            ensure_ascii=False, separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def records(self, loaded: LoadedVault) -> Iterator[EmbeddingRecord]:
        for record_id, text in self.texts(loaded):
            if not text.strip():
                continue
            yield EmbeddingRecord(
                self.record_kind, record_id, self.field, text, self.content_hash(text),
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


def _registry(*recipes: EmbeddingRecipe) -> Mapping[str, EmbeddingRecipe]:
    registry = {recipe.name: recipe for recipe in recipes}
    if len(registry) != len(recipes):
        raise RuntimeError("duplicate embedding recipe declarations")
    return MappingProxyType(registry)


EMBEDDING_RECIPES: Mapping[str, EmbeddingRecipe] = _registry(
    EmbeddingRecipe(
        "facet", "definition", 1,
        "Authored title, claim, description, pre/postconditions, applicability, "
        "positive/negative examples and non-goals; excludes retired facets.",
        _facet_definitions,
    ),
    EmbeddingRecipe(
        "item", "stem", 1,
        "Canonical practice item prompt only; excludes retired items, expected "
        "answers, hints, grading material and learner responses.",
        _item_stems,
    ),
)


def select_recipes(selectors: Iterable[str] | None = None) -> tuple[EmbeddingRecipe, ...]:
    """Recipes named ``kind/field``, or every field of a bare ``kind``.

    ``None`` selects every registered recipe; unknown selectors are refused.
    """
    if selectors is None:
        return tuple(EMBEDDING_RECIPES[name] for name in sorted(EMBEDDING_RECIPES))
    chosen: dict[str, EmbeddingRecipe] = {}
    unknown: set[str] = set()
    for selector in selectors:
        matches = [
            recipe for name, recipe in EMBEDDING_RECIPES.items()
            if selector in (name, recipe.record_kind)
        ]
        if not matches:
            unknown.add(selector)
        chosen.update((recipe.name, recipe) for recipe in matches)
    if unknown:
        raise ValueError(f"Unknown embedding recipes: {', '.join(sorted(unknown))}")
    if not chosen:
        raise ValueError("Select at least one embedding recipe")
    return tuple(chosen[name] for name in sorted(chosen))


def embedding_records(
    loaded: LoadedVault, recipes: Iterable[str] | None = None,
) -> list[EmbeddingRecord]:
    return [record for recipe in select_recipes(recipes) for record in recipe.records(loaded)]
