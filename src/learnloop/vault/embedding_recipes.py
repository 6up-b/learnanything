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
from typing import Any

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

    def records(self, loaded: LoadedVault) -> Iterator[EmbeddingRecord]:
        for record_id, text in self.texts(loaded):
            if not text.strip():
                continue
            yield self.record(record_id, text)

    def content_hash(self, text: str) -> str:
        # Version the composition, not just the authored text: a future
        # recipe change must not silently reuse the former representation.
        payload = json.dumps(
            [self.record_kind, self.field, self.version, text],
            ensure_ascii=False, separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record(self, record_id: str, text: str) -> EmbeddingRecord:
        """One record of this recipe's text, hashed exactly as a backfill would.

        Ingest uses this for candidate text that is not in the vault yet, so the
        vector it pays for is the one the record's later backfill would find.
        """
        return EmbeddingRecord(self.record_kind, record_id, self.field, text, self.content_hash(text))


def _value(source: Any, name: str) -> Any:
    return source.get(name) if isinstance(source, Mapping) else getattr(source, name, None)


def _text(source: Any, name: str) -> str:
    value = _value(source, name)
    return value if isinstance(value, str) else ""


def _texts(source: Any, name: str) -> list[str]:
    # Every listed value, verbatim: facet/definition v1 hashes must not move.
    return [str(value) for value in (_value(source, name) or [])]


def facet_definition_text(facet: Any) -> str:
    """Canonical ``facet/definition`` text of a facet model or proposal payload."""
    parts = [
        f"{label}: {value}" for label, value in (
            ("Title", _text(facet, "title")), ("Claim", _text(facet, "claim")),
            ("Description", _text(facet, "description")),
        ) if value and value.strip()
    ]
    for label, name in (
        ("Preconditions", "preconditions"),
        ("Postconditions", "postconditions"),
        ("Applicability", "applicability"),
        ("Positive examples", "positive_examples"),
        ("Negative examples", "negative_examples"),
        ("Non-goals", "non_goals"),
    ):
        values = _texts(facet, name)
        if values:
            parts.append(f"{label}:\n" + "\n".join(f"- {value}" for value in values))
    return "\n".join(parts)


def concept_definition_text(concept: Any) -> str:
    """Canonical ``concept/definition`` text: the LLM-written definition, not a bare label.

    Title and type name the idea; the synthesis-authored description defines
    it; aliases are other names for it. Edges, tags and ids are excluded.
    """
    parts = [f"{label}: {value}" for label, value in (
        ("Title", _text(concept, "title")), ("Type", _text(concept, "type")),
        ("Description", _text(concept, "description")),
    ) if value and value.strip()]
    aliases = [alias for alias in _texts(concept, "aliases") if alias.strip()]
    if aliases:
        parts.append("Aliases: " + "; ".join(aliases))
    return "\n".join(parts)


def repair_record_id(text: str) -> str:
    """A repair text's record id: its own digest, so one text is one record."""
    return "repair_" + hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:32]


def _facet_definitions(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for facet_id, facet in sorted(loaded.evidence_facets.items()):
        if facet.status == "retired":
            continue
        yield facet_id, facet_definition_text(facet)


def _concept_definitions(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for concept_id, concept in sorted(loaded.concepts.items()):
        yield concept_id, concept_definition_text(concept)


def _facet_repairs(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    seen: set[str] = set()
    for _facet_id, facet in sorted(loaded.evidence_facets.items()):
        if facet.status == "retired":
            continue
        for repair in facet.instructional_repairs:
            text = repair.strip()
            record_id = repair_record_id(text)
            if text and record_id not in seen:
                seen.add(record_id)
                yield record_id, text


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
    # Slice 2 T5 (§8, §12): the synthesis-written concept definition and each
    # distinct instructional repair, for nominations and the repair shadow.
    EmbeddingRecipe(
        "concept", "definition", 1,
        "Concept title, type, synthesis-authored description and aliases; "
        "excludes ids, tags and edges.",
        _concept_definitions,
    ),
    EmbeddingRecipe(
        "facet_repair", "text", 1,
        "One record per distinct instructional repair of a non-retired facet, "
        "keyed by the repair text's digest; excludes every other facet field.",
        _facet_repairs,
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
