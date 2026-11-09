---
title: "learnloop.content.sources.span_aliases"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/sources/span_aliases.py"
source_paths:
  - "src/learnloop/content/sources/span_aliases.py"
source_commit: "bf930ea08e1644f3acecb9d331a6fcedbf0fec19"
source_commit_timestamp: "2026-10-23T18:05:56-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.content.sources"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.sources.span_aliases module"
  - "src/learnloop/content/sources/span_aliases.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-sources"
---

# `learnloop.content.sources.span_aliases`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.sources.span_aliases` exists within [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] to own the behavior summarized by its module contract: The one alias authority for a book read again (re-read safety, 2026-10-14).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py) |
| Source lines | 468 |
| Owning package | [[Reference/Modules/learnloop/content/sources/_package|learnloop.content.sources]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `bf930ea08e1644f3acecb9d331a6fcedbf0fec19` |
| Commit timestamp | `2026-10-23T18:05:56-04:00` |

## Public API

- `class SpanResolution` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 64) — Where one span of one reading lands in another reading of its book.
  - `exact(self) -> bool` (line 75; public)
  - `key(self) -> SpanKey | None` (line 79; public)
  - `as_dict(self) -> dict[str, Any]` (line 82; public)
- `completed_readings(repository: Any, revision_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 96) — The revision's completed top-level readings, oldest first.
- `source_readings(repository: Any, source_id: str) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 106) — Every completed top-level reading of a source, oldest first.
- `current_reading(repository: Any, source_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 116) — The reading the Reader opens for a source (its current revision's latest).
- `reading_source(repository: Any, extraction_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 124)
- `previous_readings(repository: Any, extraction_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 132) — The completed top-level readings of the same revision made before ``extraction_id``, newest first: what a re-read's references were made on.
- `other_readings(repository: Any, extraction_id: str) -> list[str]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 147) — Every other completed top-level reading of the reading's book, newest first: its reading history, whether or not any alias was recorded (a re-read made before aliases were, or one that matched nothing).
- `legacy_place_origin(repository: Any, extraction_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 159) — The reading a bare span id names when it was saved before places recorded their reading (the desktop's ``localStorage``), for a book whose Reader now opens ``extraction_id``; ``None`` when that is unknown, and the place is then never read as a span of this reading (Codex review…
- `computed_aliases(repository: Any, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 229) — The aliases computed from the two readings' IR as ``repository`` loads it, never the persisted ones: an adaptive-difficulty operation's aliases, from its projected readings (cached per protection epoch by the repository's ``projection_key``).
- `alias_map(repository: Any, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 237) — ``{old span: (new span, match kind, confidence)}`` from one reading to another: the persisted aliases, else (none recorded) the same computation in memory.
- `record_aliases(repository: Any, from_extraction_id: str, to_extraction_id: str, *, clock: Clock | None=None) -> dict[str, int]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 248) — Re-anchor every span of ``from`` onto ``to`` and persist the aliases.
- `class SpanTranslator` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 268) — Resolves spans of any reading of a book onto one target reading.
  - `__init__(self, repository: Any, to_extraction_id: str) -> None` (line 271; internal)
  - `aliases_from(self, from_extraction_id: str) -> dict[str, _Alias]` (line 276; public)
  - `resolve(self, from_extraction_id: str, span_id: str) -> SpanResolution` (line 281; public)
- `resolve_span(repository: Any, from_extraction_id: str, span_id: str, to_extraction_id: str) -> SpanResolution` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 293)
- `class CurrentKeys` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 297) — Moves span keys onto their book's current reading when they match there exactly; any other key stays on the reading it was made on, whose text it still names (a reader scoped to current readings then drops it rather than show another block).
  - `__init__(self, repository: Any) -> None` (line 303; internal)
  - `current_of(self, extraction_id: str) -> str | None` (line 309; public)
  - `resolve(self, extraction_id: str, span_id: str) -> SpanResolution` (line 319; public)
  - `key(self, extraction_id: str, span_id: str) -> SpanKey` (line 325; public)
- `cited_reading(repository: Any, *, revision_id: str, span_id: str, block_content_hash: str | None=None, created_at: str | None=None, readings_of: Callable[[str], list[dict[str, Any]]] | None=None, hash_of: Callable[[str, str], str | None] | None=None) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 359) — The reading a source-object citation (revision + span) was made on.
- `class CitationResolver` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 388) — Source-object citations on their book's current reading (or flagged).
  - `__init__(self, repository: Any) -> None` (line 391; internal)
  - `_readings_of(self, revision_id: str) -> list[dict[str, Any]]` (line 400; internal)
  - `_hash_of(self, extraction_id: str, span_id: str) -> str | None` (line 405; internal)
  - `resolve(self, citation: Mapping[str, Any]) -> SpanResolution | None` (line 415; public) — ``None`` when the reading the citation was made on is unknown.
  - `current_key(self, citation: Mapping[str, Any]) -> SpanKey | None` (line 428; public) — The citation on its book's current reading when it matches exactly there, else on the reading it was made on (``None``: unknown reading).
- `locator_key(repository: Any, *, revision_id: str | None, locator: str | None, created_at: str | None=None) -> SpanKey | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 445) — Where a ``span:`` locator opens: on its book's current reading when it matches exactly there, else on the reading it was made on (whose text it names).
- `is_span_locator(locator: str | None) -> bool` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 467)

### Module constants

- `STATUS_CURRENT` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 52)
- `STATUS_NEEDS_REANCHOR` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 53)
- `STATUS_STALE` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 54)
- `SAME_TEXT_KINDS` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 57)
- `_MEMO_LIMIT` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 183)
- `CITATION_MADE_AT_SQL` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 351)
- `_BARE_SPAN` ([src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 442)

## Internal implementation anchors

- `_memo_key(repository: Any, from_extraction_id: str, to_extraction_id: str) -> tuple[str, str, str, str]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 188)
- `_computed(repository: Any, from_extraction_id: str, to_extraction_id: str) -> dict[str, _Alias]` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 196) — Aliases computed in memory for two completed readings of one source.
- `_block_hash(repository: Any, extraction_id: str, span_id: str) -> str | None` ([source](../../../../../../../src/learnloop/content/sources/span_aliases.py), line 335)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `computed_aliases`; statically calls `computed_aliases`
- [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]] — imports `module`; statically calls `alias_map`, `reading_source`
- [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]] — imports `module`; statically calls `alias_map`, `completed_readings`, `current_reading`, `previous_readings`, `reading_source`, `record_aliases`, `source_readings`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`, `CurrentKeys`, `reading_source`; statically calls `CitationResolver`, `CurrentKeys`, `reading_source`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `SpanTranslator`; statically calls `SpanTranslator`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `SpanTranslator`; statically calls `SpanTranslator`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `SpanTranslator`; statically calls `SpanTranslator`
- [[Reference/Modules/learnloop/reader/source_objects|learnloop.reader.source_objects]] — imports `CitationResolver`; statically calls `CitationResolver`
- [[Reference/Modules/learnloop/reader/source_roles|learnloop.reader.source_roles]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`; statically calls `CitationResolver`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `SpanTranslator`; statically calls `SpanTranslator`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`; statically calls `CitationResolver`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `CITATION_MADE_AT_SQL`, `CitationResolver`, `CurrentKeys`; statically calls `CitationResolver`, `CurrentKeys`
- [[Reference/Modules/learnloop_sidecar/handlers/ingest|learnloop_sidecar.handlers.ingest]] — imports `is_span_locator`, `locator_key`; statically calls `is_span_locator`, `locator_key`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `STATUS_STALE`, `legacy_place_origin`, `other_readings`, `resolve_span`; statically calls `legacy_place_origin`, `other_readings`, `resolve_span`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/content/sources/source_outline|learnloop.content.sources.source_outline]] — imports `resolve_extraction_id`; calls `resolve_extraction_id`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `parse_block_span`; calls `parse_block_span`
- [[Reference/Modules/learnloop/ingest/reanchor|learnloop.ingest.reanchor]] — imports `EXACT_HASH`, `MANUAL`, `reanchor_spans`; calls `reanchor_spans`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `re`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/content/pipeline/exam_marking|learnloop.content.pipeline.exam_marking]], [[Reference/Modules/learnloop/content/pipeline/reread|learnloop.content.pipeline.reread]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] and 9 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad_epoch.py](../../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_the_replay_cache_and_the_alias_memo_are_keyed_by_the_epoch`
- [tests/test_ad_protected_readings.py](../../../../../../../tests/test_ad_protected_readings.py) — direct import
- [tests/test_mobile_v4_reader.py](../../../../../../../tests/test_mobile_v4_reader.py) — direct import
  - `test_render_view_without_a_range_is_todays_reply_byte_for_byte`
- [tests/test_reread_safety.py](../../../../../../../tests/test_reread_safety.py) — direct import
  - `test_a_new_citation_records_its_blocks_content_hash`
  - `test_citations_resolve_against_the_reading_they_were_made_on`
  - `test_every_reference_lands_on_the_same_text_or_is_flagged_never_another_block`
  - `test_f7_a_carry_over_that_fails_is_finished_later_never_lost`
  - `test_references_still_resolve_for_a_reread_made_before_the_aliases_were_recorded`
  - `test_rereview_f2_a_held_out_passage_split_in_two_protects_both_halves`
- [tests/test_reread_safety_landing.py](../../../../../../../tests/test_reread_safety_landing.py) — direct import
  - `test_a_cue_on_a_reread_resolves_the_cited_passage_and_shows_the_question_with_its_method`

## Modification guidance

- Change span aliases policy here when content owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/content/sources/span_aliases.py](../../../../../../../src/learnloop/content/sources/span_aliases.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
