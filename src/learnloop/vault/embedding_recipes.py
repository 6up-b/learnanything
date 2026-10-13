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

``item/skeleton`` likewise reads persisted paid output: Phase 5a's (PF-b) LLM
solution skeletons (``item_skeletons``) for each item's CURRENT text, one per
item. It never calls a model and yields nothing for an item PF-b has not
skeletonized, so it covers the items PF-b generated or judged, not the bank.
"""
from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import closing
from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.stores.pf import skeletons_for_hashes
from learnloop.db.stores.practice_index import dossier_candidates
from learnloop.vault.hashes import skeleton_content_hash
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
            yield self.record(record_id, text)

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


def learning_object_statement_text(learning_object: Any, concept: Any = None) -> str:
    """Canonical ``learning_object/statement`` text: title, concept and statement.

    Authored (or LLM-drafted and written) LO content only; never learner data.
    """
    parts = [f"Title: {_text(learning_object, 'title').strip()}"]
    concept_title = _text(concept, "title").strip() if concept is not None else ""
    if concept_title:
        parts.append(f"Concept: {concept_title}")
    summary = _text(learning_object, "summary").strip()
    if summary:
        parts.append(f"Statement: {summary}")
    return "\n".join(parts)


def _learning_object_statements(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    for lo_id, learning_object in sorted(loaded.learning_objects.items()):
        if learning_object.status != "active":
            continue
        yield lo_id, learning_object_statement_text(learning_object, loaded.concepts.get(learning_object.concept))


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


def _item_skeletons(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    """PF-b's persisted LLM skeletons for each item's CURRENT text (Slice 2 §5.4).

    Reads ``item_skeletons`` (paid output, never regenerated here) keyed by the
    item text's content hash; one skeleton per item, newest prompt version
    first, then model id. Yields nothing until skeletons exist.
    """
    items = {item_id: item for item_id, item in sorted(loaded.practice_items.items())
             if item.status != "retired"}
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not items or not sqlite_path.exists():
        return
    hashes = {item_id: skeleton_content_hash(item.prompt, item.expected_answer)
              for item_id, item in items.items()}
    with closing(connect(sqlite_path, read_only=True)) as connection:
        if not connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='item_skeletons'"
        ).fetchone():
            return
        skeletons = skeletons_for_hashes(connection, hashes.values())
    for item_id, content_hash in hashes.items():
        rows = sorted(skeletons.get(content_hash, ()),
                      key=lambda row: (row["prompt_version"], row["model_id"]), reverse=False)
        if rows:
            newest = max(row["prompt_version"] for row in rows)
            chosen = min((row for row in rows if row["prompt_version"] == newest),
                         key=lambda row: row["model_id"])
            yield item_id, chosen["skeleton_text"]


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
    # Learner-text gaps (implementation_handoffs §4): the vault-wide LO
    # shortlist a named missing prerequisite is matched against.
    EmbeddingRecipe(
        "learning_object", "statement", 1,
        "LO title, its concept's title and its statement (summary); active LOs only; "
        "excludes ids, facets, items and learner data.",
        _learning_object_statements,
    ),
    EmbeddingRecipe(
        "item", "skeleton", 1,
        "The persisted LLM solution skeleton (technique sequence, checkpoints, "
        "summary) for the item's current text, from item_skeletons; excludes "
        "retired items and learner responses.",
        _item_skeletons,
    ),
)


def select_recipes(
    selectors: Iterable[str] | None = None,
    *,
    registry: Mapping[str, EmbeddingRecipe] | None = None,
) -> tuple[EmbeddingRecipe, ...]:
    """Recipes named ``kind/field``, or every field of a bare ``kind``.

    ``None`` selects every registered recipe; unknown selectors are refused.
    ``registry`` selects from a consumer's own declared recipe set (for
    example Slice 2 T4's contamination record kinds) instead of the default
    vault-content registry; it is never merged into the default backfill.
    """
    recipes = EMBEDDING_RECIPES if registry is None else registry
    if selectors is None:
        return tuple(recipes[name] for name in sorted(recipes))
    chosen: dict[str, EmbeddingRecipe] = {}
    unknown: set[str] = set()
    for selector in selectors:
        matches = [
            recipe for name, recipe in recipes.items()
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
    *, registry: Mapping[str, EmbeddingRecipe] | None = None,
) -> list[EmbeddingRecord]:
    return [
        record for recipe in select_recipes(recipes, registry=registry)
        for record in recipe.records(loaded)
    ]
