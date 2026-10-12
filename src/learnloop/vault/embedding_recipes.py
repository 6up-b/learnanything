"""Declared, versioned recipes for canonical text sent to embedding providers.

Recipes are not evidence and do not inspect attempts, answers or learner state.
Adding a record kind or field means declaring its text here, not guessing in a
caller. A recipe is named ``record_kind/field`` (Slice 2 R3/§12: ``item/stem``,
``item/skeleton``, ``facet/dossier_scope`` ...), so one kind can carry several
independently versioned fields.

Most recipes read authored vault content. The four ``facet/dossier_*`` recipes
read persisted paid dossiers (``facet_dossiers``, Slice 2 §5.9) for each
facet's CURRENT content; they never call a model and yield nothing until a
dossier has been generated. They yield the text of EVERY dossier revision
written for the facet's current content (one record id, several content
hashes), because which revision serves depends on the facet's current sources,
which only the practice index can compute. Retrieval then reads exactly the
selected revision's vector by its content hash.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType

from learnloop.db.connection import connect
from learnloop.db.stores.practice_index import dossier_candidates
from learnloop.vault.models import EvidenceFacet, LoadedVault
from learnloop.vault.paths import VaultPaths


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


def facet_content_hash(facet: EvidenceFacet) -> str:
    """Content address of a facet's authored meaning, excluding its provenance.

    Sources are hashed separately by the dossier writer, so a source change and a
    facet change are distinguishable. The derived semantic fingerprint is omitted.
    """
    payload = facet.model_dump(mode="json", exclude={"provenance", "semantic_fingerprint"})
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


DOSSIER_FIELDS = ("scope", "moves", "errors", "contrast")


def facet_dossier_candidates(loaded: LoadedVault) -> dict[str, list[object]]:
    """Every persisted dossier per non-retired facet's current revision, oldest first."""
    hashes = {
        facet_id: facet_content_hash(facet)
        for facet_id, facet in loaded.evidence_facets.items() if facet.status != "retired"
    }
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not hashes or not sqlite_path.exists():
        return {}
    with closing(connect(sqlite_path, read_only=True)) as connection:
        return dict(dossier_candidates(connection, hashes))


def _dossier_field(field: str) -> Callable[[LoadedVault], Iterator[tuple[str, str]]]:
    def texts(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
        for facet_id, rows in sorted(facet_dossier_candidates(loaded).items()):
            seen: set[str] = set()
            for dossier in rows:
                text = dossier.field(field)  # type: ignore[attr-defined]
                if text not in seen:
                    seen.add(text)
                    yield facet_id, text

    return texts


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
    *(
        EmbeddingRecipe(
            "facet", f"dossier_{field}", 1,
            f"The {field} field of the facet's LLM-written dossiers (facet_dossiers, "
            "every revision written for the facet's current content; retrieval reads "
            "the selected one); rendered dossier text only, no learner data.",
            _dossier_field(field),
        )
        for field in DOSSIER_FIELDS
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
