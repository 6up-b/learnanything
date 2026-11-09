---
title: "learnloop.tutor.context_delivery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/tutor/context_delivery.py"
source_paths:
  - "src/learnloop/tutor/context_delivery.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.tutor"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Tutor and Teach-Back Workflow"
aliases:
  - "learnloop.tutor.context_delivery module"
  - "src/learnloop/tutor/context_delivery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-tutor"
---

# `learnloop.tutor.context_delivery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.tutor.context_delivery` exists within [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] to own the behavior summarized by its module contract: What the tutor actually reads of its sources (tutor delivery fixes, 2026-10-13).

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py) |
| Source lines | 453 |
| Owning package | [[Reference/Modules/learnloop/tutor/_package|learnloop.tutor]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `estimate_tokens(text: str | None) -> int` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 82)
- `is_content(block: BlockRow) -> bool` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 90) — A block a reader would read: not page furniture, not empty.
- `class ExtractionText` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 97) — One extraction's blocks in document order, with its numbered labels.
  - `__post_init__(self) -> None` (line 105; internal)
  - `position(self, span_id: str) -> int | None` (line 108; public)
  - `block(self, span_id: str) -> BlockRow | None` (line 111; public)
  - `label_of(self, index: int) -> NumberedLabel | None` (line 115; public)
  - `labels(self) -> dict[str, list[tuple[int, NumberedLabel]]]` (line 120; public) — ``number -> [(position, label)]`` of every numbered block, in order.
  - `resolve(self, reference: NumberedReference, anchor: int) -> int | None` (line 132; public) — The numbered block ``reference`` names, nearest before ``anchor``, else after.
- `class BlockSource` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 149) — Extraction texts read once per delivery (read-only).
  - `__init__(self, sqlite_path: Path | str) -> None` (line 152; internal)
  - `extraction(self, extraction_id: str | None) -> ExtractionText | None` (line 156; public)
  - `block(self, extraction_id: str | None, span_id: str | None) -> BlockRow | None` (line 166; public)
- `passage_label(text: str | None) -> str` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 171) — A short citation label from a passage's own words.
- `neighbour_order(text: ExtractionText, first: int, last: int, *, radius: int=NEIGHBOUR_RADIUS) -> list[tuple[int, int]]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 178) — ``(position, offset)`` of the content blocks around ``first..last``, nearest first and alternating sides: i-1, i+1, i-2, i+2, ...
- `predecessor_window(text: ExtractionText, index: int, *, radius: int=PREDECESSOR_RADIUS) -> list[int]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 205) — The predecessor's Reader neighbours of the block at ``index``: the span view's ordinal-adjacent blocks, page furniture and empty blocks included, the ``radius`` before (in document order) then the ``radius`` after.
- `predecessor_cut(span: Mapping[str, Any], limit: int, *, collapse: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 215) — ``span`` with its text cut as the predecessor cut it: the first ``limit`` characters, of the whitespace-collapsed text for a retrieved or pinned span (``collapse``), else as stored (a span-view preview).
- `class References` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 227) — The referenced spans to add, and what was and was not followed.
  - `describe(self) -> dict[str, Any]` (line 234; public)
  - `empty(self) -> bool` (line 238; public)
- `follow_references(source: BlockSource, spans: Sequence[Mapping[str, Any]], *, allow: BlockFilter, delivered: Iterable[SpanKey]=(), max_references: int=MAX_REFERENCES, span_extra: Callable[[str, BlockRow], Mapping[str, Any]] | None=None) -> References` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 280) — Resolve the numbered references in ``spans`` (in order) to ``referenced`` spans.
- `apply_budget(spans: Sequence[Mapping[str, Any]], budget_tokens: int) -> tuple[list[dict[str, Any]], dict[str, Any]]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 374) — Keep ``spans`` in order within ``budget_tokens``: the first that does not fit is trimmed to the remainder (dropped below ``MIN_TRIM_TOKENS``), every later one dropped.
- `hydrate(source: BlockSource, spans: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 405) — Each span with its complete canonical block text (when its block is found); returns the spans and how many were completed from a cut.
- `notable(receipt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 422) — Whether a delivery receipt records something (a trim, a drop, a reference).

### Module constants

- `CHARS_PER_TOKEN` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 56)
- `NEIGHBOUR_RADIUS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 58)
- `MAX_REFERENCES` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 60)
- `MAX_REFERENCE_BLOCKS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 62)
- `MIN_TRIM_TOKENS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 64)
- `PREVIEW_CHARS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 67)
- `SPAN_CHARS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 68)
- `PREDECESSOR_RADIUS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 70)
- `_TERMINAL` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 72)
- `_HEADER_TYPES` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 73)
- `_EQUATION_TYPES` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 74)
- `_BOUNDARY_LEADS` ([src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py), line 75)

### Explicit exports

`__all__` declares:

- `CHARS_PER_TOKEN`
- `MAX_REFERENCES`
- `MAX_REFERENCE_BLOCKS`
- `MIN_TRIM_TOKENS`
- `NEIGHBOUR_RADIUS`
- `PREDECESSOR_RADIUS`
- `PREVIEW_CHARS`
- `SPAN_CHARS`
- `BlockFilter`
- `BlockSource`
- `ExtractionText`
- `References`
- `apply_budget`
- `estimate_tokens`
- `follow_references`
- `hydrate`
- `is_content`
- `neighbour_order`
- `notable`
- `passage_label`
- `predecessor_cut`
- `predecessor_window`

## Internal implementation anchors

- `_block_kind(block: BlockRow) -> str` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 86)
- `_completes_statement(previous: BlockRow, following: BlockRow, *, header: bool) -> bool` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 242) — Whether ``following`` still belongs to the environment ``previous`` is part of.
- `_environment(text: ExtractionText, start: int) -> list[int]` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 256) — The numbered block at ``start`` and the blocks completing its statement: a heading label's body, a display equation after it, or a sentence the label block leaves open ("...
- `_trim(text: str, max_chars: int) -> str` ([source](../../../../../../src/learnloop/tutor/context_delivery.py), line 361) — A prefix of ``text`` of at most ``max_chars``, cut at a word boundary when one is near (the last tenth); the canonical text up to that point.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `ExtractionText`; statically calls `ExtractionText`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]] — imports `BlockSource`, `MAX_REFERENCES`, `NEIGHBOUR_RADIUS`, `PREVIEW_CHARS`, `SPAN_CHARS`, `apply_budget`, `estimate_tokens`, `follow_references`, `is_content`, `neighbour_order`, `passage_label`, `predecessor_window`; statically calls `apply_budget`, `estimate_tokens`, `follow_references`, `is_content`, `neighbour_order`, `passage_label`, `predecessor_window`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `BlockSource`; statically calls `BlockSource`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `BlockFilter`, `BlockSource`, `SPAN_CHARS`, `follow_references`, `predecessor_cut`; statically calls `BlockSource`, `follow_references`, `predecessor_cut`
- [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] — imports `apply_budget`, `notable`; statically calls `apply_budget`, `notable`
- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `BlockFilter`, `BlockSource`, `MAX_REFERENCES`, `NEIGHBOUR_RADIUS`, `PREDECESSOR_RADIUS`, `PREVIEW_CHARS`, `References`, `SPAN_CHARS`, `apply_budget`, `follow_references`, `hydrate`, `neighbour_order`, `notable`, `passage_label`, `predecessor_cut`, `predecessor_window`; statically calls `BlockSource`, `References`, `apply_budget`, `follow_references`, `hydrate`, `neighbour_order`, `notable`, `passage_label`, `predecessor_cut`, `predecessor_window`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `BlockSource`; statically calls `BlockSource`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `BlockRow`, `EXCLUDED_BLOCK_TYPES`, `extraction_blocks`; calls `extraction_blocks`
- [[Reference/Modules/learnloop/ingest/block_roles|learnloop.ingest.block_roles]] — imports `NumberedLabel`, `NumberedReference`, `lead_role`, `numbered_label`, `numbered_references`; calls `lead_role`, `numbered_label`, `numbered_references`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `math`, `pathlib`, `re`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Tutor and Teach-Back Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/delivery|learnloop.experiments.contextual_embeddings.delivery]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]], [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]], [[Reference/Modules/learnloop/tutor/reader_modes|learnloop.tutor.reader_modes]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_delivery.py](../../../../../../tests/test_e0_delivery.py) — direct import
  - `test_a_source_that_does_not_fit_runs_the_named_fallback_never_a_truncation`
  - `test_d0_and_d1_reproduce_the_production_reader_delivery`
  - `test_d2_is_the_whole_permitted_section_and_d3_the_whole_permitted_source`
  - `test_retrieved_d0_and_d1_deliver_the_same_initial_evidence`
- [tests/test_e0_review_round2.py](../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f6_a_permitted_quote_is_still_delivered`
  - `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges`
  - `test_f6_delivery_refuses_a_protected_quote_even_from_an_unfrozen_selection`
- [tests/test_e0_review_round4.py](../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h7_a_quote_without_complete_canonical_coverage_is_dropped`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_a_retrieved_spans_reference_to_an_exercise_caption_is_refused_while_practising`
  - `test_an_exercise_continuing_a_cited_theorem_is_cut_while_practising`

## Modification guidance

- Change context delivery policy here when tutor owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/tutor/context_delivery.py](../../../../../../src/learnloop/tutor/context_delivery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
