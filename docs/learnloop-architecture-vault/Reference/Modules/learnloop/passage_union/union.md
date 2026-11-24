---
title: "learnloop.passage_union.union"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/passage_union/union.py"
source_paths:
  - "src/learnloop/passage_union/union.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.passage_union"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.passage_union.union module"
  - "src/learnloop/passage_union/union.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-passage-union"
---

# `learnloop.passage_union.union`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.passage_union.union` exists within [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] to own the behavior summarized by its module contract: ``passage.union_range`` (spec §7.6, owner decision 7: "find everything tied to a passage").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/passage_union/union.py](../../../../../../src/learnloop/passage_union/union.py) |
| Source lines | 301 |
| Owning package | [[Reference/Modules/learnloop/passage_union/_package|learnloop.passage_union]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class UnionError(ValueError)` ([source](../../../../../../src/learnloop/passage_union/union.py), line 36)
  - `__init__(self, code: str, message: str) -> None` (line 37; internal)
- `span_range(ir: Any, *, from_span_id: str | None, to_span_id: str | None, t0: float | None, t1: float | None) -> list[str]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 61)
- `union_range(vault: Any, repository: Any, *, extraction_id: str, from_span_id: str | None=None, to_span_id: str | None=None, t0: float | None=None, t1: float | None=None, notes_by_span: Mapping[str, list[dict[str, Any]]] | None=None, clock: Any=None, include_word_origins: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 105) — ``notes_by_span``: the notes linked beside each passage of this reading, handed in by the caller (the sidecar, which reaches the notes' code; nothing in learnloop below it does).

### Module constants

- `EXACT` ([src/learnloop/passage_union/union.py](../../../../../../src/learnloop/passage_union/union.py), line 33)

### Explicit exports

`__all__` declares:

- `UnionError`
- `span_range`
- `union_range`

## Internal implementation anchors

- `_json_list(value: Any) -> list[Any]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 42)
- `_rows(connection: Any, sql: str, params: Iterable[Any]=()) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 50)
- `_in(values: Iterable[str]) -> tuple[str, list[str]]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 56)
- `class _Placer` ([source](../../../../../../src/learnloop/passage_union/union.py), line 69) — Places a (reading, span) of any reading of the book on this reading's range.
- `_empty(span_id: str, section_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/passage_union/union.py), line 99)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/passage_union/content|learnloop.passage_union.content]] — imports `UnionError`, `span_range`; statically calls `UnionError`, `span_range`
- [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]] — imports `UnionError`, `span_range`, `union_range`; statically calls `span_range`, `union_range`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_withheld`; calls `exam_withheld`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `STATUS_CURRENT`, `SpanTranslator`, `other_readings`, `reading_source`; calls `SpanTranslator`, `other_readings`, `reading_source`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/pad_reads|learnloop.db.stores.pad_reads]] — imports `module`; calls `carried_on_readings`, `head`, `standing_anchors_for_spans`
- [[Reference/Modules/learnloop/db/stores/span_projection_reads|learnloop.db.stores.span_projection_reads]] — imports `module`; calls `rows_on_readings`
- [[Reference/Modules/learnloop/reader/annotations|learnloop.reader.annotations]] — imports `annotation_placements`; calls `annotation_placements`
- [[Reference/Modules/learnloop/section_map|learnloop.section_map]] — imports `RangeError`, `extraction_sections`, `range_span_ids`; calls `extraction_sections`, `range_span_ids`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/passage_union/content|learnloop.passage_union.content]], [[Reference/Modules/learnloop_sidecar/handlers/passage_union|learnloop_sidecar.handlers.passage_union]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_pad_stale_edits_stacks_and_passage_reads.py](../../../../../../tests/test_pad_stale_edits_stacks_and_passage_reads.py) — direct import
  - `test_a_pads_link_on_an_older_reading_marks_the_newer_one_from_the_union_alone`
- [tests/test_reader_rd0_reads.py](../../../../../../tests/test_reader_rd0_reads.py) — direct import
  - `test_a_same_place_alias_is_flagged_never_shown_as_the_cited_text`
  - `test_a_time_range_reads_a_transcripts_cues_and_a_bad_range_is_refused`
  - `test_the_union_returns_every_kind_for_a_passage_across_readings`
- [tests/test_reader_rd4_emission.py](../../../../../../tests/test_reader_rd4_emission.py) — direct import
  - `test_a_lift_made_before_links_moved_still_carries_them`
- [tests/test_reader_rd7_unlocated_marker.py](../../../../../../tests/test_reader_rd7_unlocated_marker.py) — direct import
  - `test_no_passage_says_a_check_is_due_before_it`

## Modification guidance

- Make changes here when the responsibility remains union within learnloop.passage_union; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/passage_union/union.py](../../../../../../src/learnloop/passage_union/union.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
