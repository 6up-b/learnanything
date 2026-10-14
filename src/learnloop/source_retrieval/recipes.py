"""The ``source_block/text`` embedding recipe (Slice 2 R3, §12) and its manifests.

One record per substantive block of every source's current extraction:
``Section: <path>`` (when the block has one) and the block's own text,
whitespace collapsed and capped at ``MAX_BLOCK_CHARS``. Canonical source text
only: no learner data, no model output. Page furniture (headers, footers,
tables of contents) and blocks with fewer than ``MIN_BLOCK_CHARS``
non-whitespace characters are not embedded; keyword search still covers them.

The recipe lives in its own registry, ``SOURCE_RETRIEVAL_RECIPES``, so a bare
``learnloop embeddings backfill`` never embeds the source library: it runs only
when named (``--record-kind source_block``). A source corpus is one or two
orders of magnitude larger than the item and facet corpora, so joining the
default would make every default-capped backfill plan exceed its caps (and so
stop backfilling the other recipes), and would buy the whole library for an
owner who never asked for it. A completed extraction queues the recipe for its
own source (``source_retrieval.source_vectors``; tutor delivery fixes) when
both embedding switches are on, so a new import or a re-extraction keeps its
source in dense retrieval without a library-wide run.
"""
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable, Iterator, Mapping
from contextlib import closing
import json
from pathlib import Path
from threading import Lock
from types import MappingProxyType

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    EXCLUDED_BLOCK_TYPES,
    BlockRow,
    extraction_blocks,
    extraction_fingerprint,
    section_header_titles,
)
from learnloop.source_retrieval.corpus import current_extractions
from learnloop.vault.embedding_recipes import EmbeddingRecipe
from learnloop.vault.models import LoadedVault
from learnloop.vault.paths import VaultPaths

SOURCE_BLOCK_KIND = "source_block"
SOURCE_BLOCK_FIELD = "text"
SOURCE_BLOCK_RECIPE = f"{SOURCE_BLOCK_KIND}/{SOURCE_BLOCK_FIELD}"
DOC_TASK_PREFIX = "retrieval-document"
MAX_BLOCK_CHARS = 6000
MIN_BLOCK_CHARS = 20


def block_record_id(extraction_id: str, span_id: str) -> str:
    return f"{extraction_id}/{span_id}"


def split_record_id(record_id: str) -> tuple[str, str]:
    extraction_id, _, span_id = record_id.partition("/")
    return extraction_id, span_id


MAX_SECTION_TITLE_CHARS = 120


def section_path(block: BlockRow, titles: Mapping[str, str] | None = None) -> list[str]:
    """The block's section path, each Marker header ref resolved to its text.

    An element that names no header block of the extraction (a transcript's
    ``transcript``, a web page's anchor) is kept as recorded.
    """

    try:
        value = json.loads(block.section_path_json or "[]")
    except (TypeError, ValueError):
        return []
    if not isinstance(value, list):
        return []
    path = []
    for part in value:
        element = str(part).strip()
        if element:
            path.append((titles or {}).get(element, element)[:MAX_SECTION_TITLE_CHARS])
    return path


def embeddable(block: BlockRow) -> bool:
    return block.block_type not in EXCLUDED_BLOCK_TYPES and len("".join(block.text.split())) >= MIN_BLOCK_CHARS


def source_block_text(block: BlockRow, titles: Mapping[str, str]) -> str:
    """The canonical embedded text of one block (recipe v1).

    ``titles`` is the extraction's ``section_header_titles``: section paths are
    embedded as header text, never as extractor block ids.
    """

    body = " ".join(block.text.split())[:MAX_BLOCK_CHARS]
    path = section_path(block, titles)
    return ("Section: " + " > ".join(path) + "\n" + body) if path else body


def _source_block_texts(loaded: LoadedVault) -> Iterator[tuple[str, str]]:
    sqlite_path = VaultPaths(loaded.root, loaded.config).sqlite_path
    if not sqlite_path.exists():
        return
    repository = Repository.attach(sqlite_path, read_only=True)
    with closing(connect(sqlite_path, read_only=True)) as connection:
        for extraction_id in sorted(current_extractions(repository)):
            titles = section_header_titles(connection, extraction_id)
            for block in extraction_blocks(connection, extraction_id):
                if embeddable(block):
                    yield block_record_id(block.extraction_id, block.span_id), source_block_text(block, titles)


SOURCE_RETRIEVAL_RECIPES: Mapping[str, EmbeddingRecipe] = MappingProxyType({
    SOURCE_BLOCK_RECIPE: EmbeddingRecipe(
        SOURCE_BLOCK_KIND, SOURCE_BLOCK_FIELD, 1,
        "One record per block of every source's current extraction: 'Section: <path>' (header "
        "refs resolved to header text) "
        f"and the block text, whitespace collapsed and capped at {MAX_BLOCK_CHARS} characters; "
        f"page headers, footers and tables of contents and blocks under {MIN_BLOCK_CHARS} "
        "non-whitespace characters excluded. Canonical source text only; never in the default "
        "backfill (select source_block).",
        _source_block_texts,
    ),
})

_MANIFESTS: OrderedDict[tuple[str, str, tuple[int, int]], dict[str, str]] = OrderedDict()
_MANIFEST_LOCK = Lock()
_MANIFEST_CACHE_SIZE = 64


def extraction_manifest(connection, sqlite_path: Path, extraction_id: str,
                        fingerprint: tuple[int, int] | None = None) -> dict[str, str]:
    """``{record_id: content_hash}`` of one extraction's embeddable blocks (cached).

    Keyed by the extraction's block fingerprint (``fingerprint`` when the
    caller already read it), so replaced blocks are rehashed.
    """

    key = (str(sqlite_path), extraction_id,
           fingerprint if fingerprint is not None else extraction_fingerprint(connection, extraction_id))
    with _MANIFEST_LOCK:
        cached = _MANIFESTS.get(key)
        if cached is not None:
            _MANIFESTS.move_to_end(key)
            return cached
    recipe = SOURCE_RETRIEVAL_RECIPES[SOURCE_BLOCK_RECIPE]
    titles = section_header_titles(connection, extraction_id)
    manifest = {
        block_record_id(block.extraction_id, block.span_id): recipe.content_hash(source_block_text(block, titles))
        for block in extraction_blocks(connection, extraction_id) if embeddable(block)
    }
    with _MANIFEST_LOCK:
        _MANIFESTS[key] = manifest
        while len(_MANIFESTS) > _MANIFEST_CACHE_SIZE:
            _MANIFESTS.popitem(last=False)
    return manifest


def scope_manifest(connection, sqlite_path: Path, extraction_ids: Iterable[str]) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for extraction_id in sorted(set(extraction_ids)):
        manifest.update(extraction_manifest(connection, sqlite_path, extraction_id))
    return manifest


__all__ = [
    "DOC_TASK_PREFIX",
    "MAX_BLOCK_CHARS",
    "MIN_BLOCK_CHARS",
    "SOURCE_BLOCK_FIELD",
    "SOURCE_BLOCK_KIND",
    "SOURCE_BLOCK_RECIPE",
    "SOURCE_RETRIEVAL_RECIPES",
    "block_record_id",
    "embeddable",
    "extraction_manifest",
    "scope_manifest",
    "section_path",
    "source_block_text",
    "split_record_id",
]
