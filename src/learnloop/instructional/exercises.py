"""The source-exercise arm of ``find_practice`` (spec_source_practice_and_probes_v1 §7.1).

Textbook exercises become practice candidates before anyone imports them:

* **scope**: the teaching scope of the constraints' LOs (or every source with
  a role when none is given), so exam, held-out problem-set and
  assessment-linked spans never appear (the teaching exclusions apply);
* **positive role filter**: ``search_spans(roles=("exercise",))`` keeps only
  blocks whose *effective* role hint is ``exercise``; each hit is widened to
  its exercise region (the lead block and the body after it);
* **already imported**: a region an item already presents (its provenance
  refs or ``canonical_exercise``, the same text in another extraction of the
  source included) is dropped;
* proposals carry the exercise's own statement, source, page and revision.

It is injected into ``find_practice`` by the adapters (``practice_index``
never imports the service, SC12). Worked examples are not practice
candidates: their solution sits beside them, so they are passages
(``find_sources(intent="worked_example")``), never independent checks.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import closing
from dataclasses import dataclass, field
import re
from typing import Any

from learnloop.db.connection import connect
from learnloop.db.repositories import Repository
from learnloop.db.stores.source_block_fts import (
    MAX_REGION_BLOCKS,
    REGION_BODY_HINTS,
    block_content_hashes,
    blocks_by_key,
    extraction_hint_rows,
    section_header_titles,
    spans_with_content_hashes,
)
from learnloop.db.stores.source_service import exercise_key as _store_exercise_key, imported_regions
from learnloop.ingest.locators import parse_block_span
from learnloop.source_retrieval.corpus import Scope, effective_hint, teaching_scope
from learnloop.source_retrieval.search import SpanSearch, search_spans
from learnloop.vault.models import LoadedVault

#: Characters of an exercise statement a proposal carries (display and prompt
#: size bound, not a learning threshold).
STATEMENT_CHARS = 1800
_LABEL_RE = re.compile(r"^\s*((?:exercise|problem|question)s?\s*[\dA-Za-z.()\-]*\d[\dA-Za-z.()\-]*)", re.IGNORECASE)
_NUMBER_RE = re.compile(r"^\s*(\(?\d+(?:\.\d+)*[.)]?|\([a-z]\))\s")


@dataclass(frozen=True)
class ExerciseRegion:
    extraction_id: str
    span_ids: tuple[str, ...]
    text: str

    @property
    def key(self) -> tuple[str, ...]:
        return (self.extraction_id, *self.span_ids)


@dataclass
class ExercisePool:
    """The arm's candidates for one request, best fused rank first."""

    candidates: list[dict[str, Any]] = field(default_factory=list)
    search: dict[str, Any] = field(default_factory=dict)
    dropped: dict[str, int] = field(default_factory=dict)
    scope: dict[str, Any] = field(default_factory=dict)
    list_ends: dict[str, bool] = field(default_factory=dict)
    list_depths: dict[str, int] = field(default_factory=dict)
    unjudged: int = 0

    def describe(self) -> dict[str, Any]:
        return {"candidates": len(self.candidates), "search": self.search, "dropped": dict(self.dropped),
                "scope": self.scope, "list_ends": dict(self.list_ends), "unjudged": self.unjudged}


def starts_exercise(text: str | None) -> bool:
    """Whether a block's own text opens an exercise: "20 Suppose ...",
    "3. Show ...", "Exercise 4.12", "Problem 2". A sub-part "(a)" does not."""

    value = text or ""
    if _LABEL_RE.match(value):
        return True
    number = _NUMBER_RE.match(value)
    return number is not None and re.fullmatch(r"\([a-z]\)", number.group(1)) is None


#: Marker's page furniture: never an exercise, never part of one.
PAGE_FURNITURE = frozenset({"PageHeader", "PageFooter"})


def exercise_regions(connection, extraction_id: str) -> list[ExerciseRegion]:
    """One extraction's exercise regions in document order.

    A block whose effective hint is ``exercise`` leads a region; the unhinted
    body after it (prose, equations, tables, figures) joins it, up to the next
    section header, the next lead or ``MAX_REGION_BLOCKS``.
    """

    titles = section_header_titles(connection, extraction_id)
    regions: list[ExerciseRegion] = []
    current: list[Any] = []
    body_left = 0

    def close() -> None:
        if current:
            regions.append(ExerciseRegion(
                extraction_id, tuple(row.span_id for row in current),
                "\n\n".join(" ".join(row.text.split()) for row in current if row.text.strip())))
        current.clear()

    for row in extraction_hint_rows(connection, extraction_id):
        if row.block_type in PAGE_FURNITURE or not (row.text or "").strip():
            # Page headers, footers and empty blocks neither lead nor end a
            # region (an exercise can run across a page break).
            continue
        hint = effective_hint(row, titles)
        if (hint == "exercise" and row.block_type != "SectionHeader" and current and body_left
                and not starts_exercise(row.text)):
            # Under an "Exercises" heading every block carries the heading's
            # hint; only a numbered or labelled block starts a new exercise.
            # The rest ("Find a subspace W ..." after "20 Suppose U = ...", a
            # "Hint:" line) belong to the exercise they follow.
            current.append(row)
            body_left -= 1
        elif hint == "exercise" and row.block_type != "SectionHeader":
            close()
            current.append(row)
            body_left = MAX_REGION_BLOCKS
        elif current and body_left and hint in REGION_BODY_HINTS and row.block_type != "SectionHeader":
            current.append(row)
            body_left -= 1
        else:
            close()
            body_left = 0
    close()
    return regions


def exercise_label(text: str, page: int | None) -> str:
    """"Exercise 4.12" when the lead names one, else the number, else the page."""

    match = _LABEL_RE.match(text or "")
    if match:
        return " ".join(match.group(1).split()).rstrip(".")
    number = _NUMBER_RE.match(text or "")
    if number:
        return f"Exercise {number.group(1).strip('.)( ')}" + (f", p. {page}" if page is not None else "")
    return f"Exercise on p. {page}" if page is not None else "Exercise"


def _ref_keys(ref: Any) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    parsed = parse_block_span(str(getattr(ref, "locator", "") or ""))
    if parsed is not None:
        keys.add((parsed[0], parsed[1]))
    extraction_id = getattr(ref, "extraction_id", None)
    for span in getattr(ref, "span_ids", None) or ():
        span = str(span)
        if "/" in span:
            head, _, tail = span.partition("/")
            keys.add((head, tail))
        elif extraction_id:
            keys.add((str(extraction_id), span))
    return keys


def imported_span_keys(vault: LoadedVault, repository: Repository) -> set[tuple[str, str]]:
    """Spans any item already presents: provenance refs, canonical exercises, written imports."""

    keys: set[tuple[str, str]] = set()
    for item in vault.practice_items.values():
        canonical = getattr(item, "canonical_exercise", None)
        if canonical is not None:
            keys.update((canonical.extraction_id, str(span)) for span in canonical.span_ids)
        for ref in item.provenance.source_refs:
            keys |= _ref_keys(ref)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        for extraction_id, span_ids in imported_regions(connection):
            keys.update((extraction_id, str(span)) for span in span_ids)
    return keys


def _same_text_keys(connection, keys: set[tuple[str, str]], extraction_ids: Sequence[str]) -> set[tuple[str, str]]:
    """The imported blocks' text in the searched extractions (a re-extraction renumbers spans)."""

    by_extraction: dict[str, set[str]] = {}
    for extraction_id, span_id in keys:
        by_extraction.setdefault(extraction_id, set()).add(span_id)
    hashes: set[str] = set()
    for extraction_id, spans in by_extraction.items():
        hashes.update(block_content_hashes(connection, extraction_id, spans))
    if not hashes:
        return set()
    found: set[tuple[str, str]] = set()
    for extraction_id in extraction_ids:
        found.update((extraction_id, span) for span in spans_with_content_hashes(connection, extraction_id, hashes))
    return found


def exercise_scope(vault: LoadedVault, repository: Repository,
                   learning_object_ids: Sequence[str]) -> Scope:
    return teaching_scope(vault, repository, learning_object_ids, item_bound=False)


def exercise_region_count(vault: LoadedVault, repository: Repository,
                          learning_object_ids: Sequence[str] = ()) -> dict[str, int]:
    """Unimported exercise regions in the teaching scope (no search, no model call)."""

    scope = exercise_scope(vault, repository, list(learning_object_ids))
    counts = {"regions": 0, "already_imported": 0, "excluded": 0}
    if not scope.extractions:
        return counts
    imported = imported_span_keys(vault, repository)
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        imported |= _same_text_keys(connection, imported, sorted(scope.extractions))
        for extraction_id in sorted(scope.extractions):
            for region in exercise_regions(connection, extraction_id):
                if any((region.extraction_id, span) in imported for span in region.span_ids):
                    counts["already_imported"] += 1
                elif any(not scope.allows(region.extraction_id, span) for span in region.span_ids):
                    counts["excluded"] += 1
                else:
                    counts["regions"] += 1
    return counts


def exercise_candidates(vault: LoadedVault, repository: Repository, query: str, constraints: Any, *,
                        pool_size: int, embedder: Any | None = None, rewrite_client: Any | None = None,
                        owner_id: str = "", deadline: float | None = None,
                        list_depth: int | Mapping[str, int] | None = None,
                        exclude_keys: Sequence[str | Sequence[str]] = ()) -> ExercisePool:
    """Up to ``pool_size`` exercise regions for the request (a prompt-size bound).

    ``exclude_keys`` are regions already judged in an earlier page (resumable
    paging, §8.3.4), as exercise keys (``srcex:...``) or region tuples; they
    are dropped before the pool is cut, so a continuation reaches the next
    regions instead of re-reading the first pool.
    """

    lo_ids = list(getattr(constraints, "learning_object_ids", ()) or ())
    scope = exercise_scope(vault, repository, lo_ids)
    pool = ExercisePool(scope=scope.describe())
    if not scope.extractions:
        pool.dropped["no_scope"] = 1
        return pool
    search: SpanSearch = search_spans(
        vault, repository, query, scope, limit=max(pool_size * 4, 40), deep=True,
        rewrite=False, embedder=embedder, rewrite_client=rewrite_client, owner_id=owner_id,
        deadline=deadline, roles=("exercise",),
        **({} if list_depth is None else {"list_depth": list_depth}),
    )
    pool.search = search.describe()
    pool.list_ends = dict(search.list_ends)
    pool.list_depths = dict(search.list_depths)
    imported = imported_span_keys(vault, repository)
    excluded_regions = {key if isinstance(key, str) else exercise_key(str(key[0]), [str(span) for span in key[1:]])
                        for key in exclude_keys}
    seen: set[tuple[str, ...]] = set()
    dropped = {"already_imported": 0, "excluded": 0, "no_region": 0, "judged_earlier": 0}
    with closing(connect(repository.sqlite_path, read_only=True)) as connection:
        imported |= _same_text_keys(connection, imported, sorted(scope.extractions))
        regions_by_extraction: dict[str, list[ExerciseRegion]] = {}
        region_of: dict[tuple[str, str], ExerciseRegion] = {}
        ordered: list[ExerciseRegion] = []
        for key in search.fused_keys:
            extraction_id = key[0]
            if extraction_id not in regions_by_extraction:
                regions_by_extraction[extraction_id] = exercise_regions(connection, extraction_id)
                for region in regions_by_extraction[extraction_id]:
                    for span_id in region.span_ids:
                        region_of[(extraction_id, span_id)] = region
            region = region_of.get(key)
            if region is None:
                dropped["no_region"] += 1
                continue
            if region.key in seen:
                continue
            seen.add(region.key)
            if any((region.extraction_id, span) in imported for span in region.span_ids):
                dropped["already_imported"] += 1
                continue
            if any(not scope.allows(region.extraction_id, span) for span in region.span_ids):
                dropped["excluded"] += 1
                continue
            if exercise_key(region.extraction_id, region.span_ids) in excluded_regions:
                dropped["judged_earlier"] += 1
                continue
            ordered.append(region)
        pool.unjudged = max(0, len(ordered) - pool_size)
        chosen = ordered[:pool_size]
        leads = blocks_by_key(connection, [(region.extraction_id, region.span_ids[0]) for region in chosen])
        runs: dict[str, Any] = {}
        for region in chosen:
            if region.extraction_id not in runs:
                runs[region.extraction_id] = repository.get_extraction_run(region.extraction_id) or {}
            lead = leads.get((region.extraction_id, region.span_ids[0]))
            page = lead.page if lead is not None else None
            source = scope.extractions[region.extraction_id]
            statement = region.text if len(region.text) <= STATEMENT_CHARS else region.text[:STATEMENT_CHARS - 1] + "…"
            pool.candidates.append({
                "kind": "source_exercise",
                "extraction_id": region.extraction_id,
                "span_ids": list(region.span_ids),
                "source_id": source.source_id,
                "revision_id": runs[region.extraction_id].get("revision_id"),
                "source_title": source.title,
                "label": exercise_label(region.text, page),
                "page": page,
                "statement": statement,
                "key": exercise_key(region.extraction_id, region.span_ids),
            })
    pool.dropped = {name: count for name, count in dropped.items() if count}
    return pool


def exercise_key(extraction_id: str, span_ids: Sequence[str]) -> str:
    """A stable identity for an unimported exercise (ledger ids, receipts, impressions)."""

    return _store_exercise_key(extraction_id, span_ids)


__all__ = [
    "STATEMENT_CHARS",
    "ExercisePool",
    "ExerciseRegion",
    "exercise_candidates",
    "exercise_key",
    "exercise_label",
    "exercise_regions",
    "exercise_scope",
    "imported_span_keys",
]
