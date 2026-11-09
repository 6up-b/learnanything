---
title: "learnloop.experiments.contextual_embeddings.delivery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/experiments/contextual_embeddings/delivery.py"
source_paths:
  - "src/learnloop/experiments/contextual_embeddings/delivery.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.experiments.contextual_embeddings"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.experiments.contextual_embeddings.delivery module"
  - "src/learnloop/experiments/contextual_embeddings/delivery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-experiments-contextual-embeddings"
---

# `learnloop.experiments.contextual_embeddings.delivery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.experiments.contextual_embeddings.delivery` exists within [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] to own the behavior summarized by its module contract: E0 delivery arms D0-D3 (spec §5.3): what the same tutor reads.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/experiments/contextual_embeddings/delivery.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py) |
| Source lines | 391 |
| Owning package | [[Reference/Modules/learnloop/experiments/contextual_embeddings/_package|learnloop.experiments.contextual_embeddings]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Selection` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 63) — A known location: a Reader selection (its primary block, the other blocks it covers, the learner's exact quote).
- `class Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 74)
  - `tokens(self) -> int` (line 80; public)
  - `coverage(self, blocks: Mapping[tuple[str, str], BlockRow]) -> list[tuple[str, str, int, int]]` (line 83; public) — ``(extraction, span, start, end)`` of canonical text actually delivered (a cut covers only its canonical prefix).
- `canonical_prefix_end(canonical: str, delivered: str) -> int` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 102) — How much of ``canonical`` a delivered prefix covers: exact for a canonical prefix, and for a whitespace-collapsed cut the canonical offset reached after the same non-whitespace characters.
- `quote_covered(quote: str | None, span_ids: Sequence[str], text_of: Callable[[str], str | None], permitted: Callable[[str], bool]) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 144) — Whether a learner's quote is PROVEN to come from permitted canonical text (fix round 4, High 7): it names at least one span, every span it names exists and is permitted, and the whitespace-normalized quote is a substring of those spans' whitespace-normalized canonical text joine…
- `reader_d0(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection, *, budget_tokens: int=D0_BUDGET_TOKENS) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 202) — Today's Reader context (the kill switch off; no references).
- `reader_d1(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection, *, budget_tokens: int=pins.D1_EVIDENCE_TOKENS) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 232) — The delivery stage's Reader context within the D1 ceiling.
- `retrieved_d0(snapshot: CorpusSnapshot, unit_ids: Sequence[str]) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 267) — Today's retrieved context: the first four spans, 600 collapsed characters.
- `retrieved_d1(source: BlockSource, snapshot: CorpusSnapshot, unit_ids: Sequence[str], *, budget_tokens: int=pins.D1_EVIDENCE_TOKENS) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 287) — Complete blocks of the ranked units, their references, one budget.
- `section_span_ids(snapshot: CorpusSnapshot, selection: Selection) -> tuple[list[str], str]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 339) — The smallest outline unit holding the selection, else its section path.
- `whole_section(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 356)
- `whole_source(source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 368)
- `deliver(arm: str, source: BlockSource, snapshot: CorpusSnapshot, selection: Selection) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 378)

### Module constants

- `D0_BUDGET_TOKENS` ([src/learnloop/experiments/contextual_embeddings/delivery.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 57)
- `MAX_CITATION_SPANS` ([src/learnloop/experiments/contextual_embeddings/delivery.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 58)
- `MAX_SELECTION_SPANS` ([src/learnloop/experiments/contextual_embeddings/delivery.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 59)

### Explicit exports

`__all__` declares:

- `Delivered`
- `Selection`
- `canonical_prefix_end`
- `deliver`
- `reader_d0`
- `reader_d1`
- `retrieved_d0`
- `retrieved_d1`
- `section_span_ids`
- `whole_section`
- `whole_source`

## Internal implementation anchors

- `class _Policy` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 119)
- `_span(extraction_id: str, block: BlockRow, relation: str, **extra: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 139)
- `_selection_spans(text: Any, selection: Selection, policy: _Policy) -> tuple[list[dict[str, Any]], list[int]] | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 165)
- `_block(snapshot: CorpusSnapshot, extraction_id: str, span_id: str) -> BlockRow | None` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 309)
- `_fits(tokens: int) -> bool` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 316)
- `_whole(snapshot: CorpusSnapshot, extraction_id: str, span_ids: Sequence[str] | None, arm: str) -> Delivered` ([source](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py), line 320)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]] — imports `Delivered`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]] — imports `Selection`, `quote_covered`; statically calls `Selection`, `quote_covered`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]] — imports `Delivered`, `deliver`, `retrieved_d1`; statically calls `deliver`, `retrieved_d1`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/source_block_fts|learnloop.db.stores.source_block_fts]] — imports `BlockRow`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `CorpusSnapshot`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/pins|learnloop.experiments.contextual_embeddings.pins]] — imports `module`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `BlockSource`, `MAX_REFERENCES`, `NEIGHBOUR_RADIUS`, `PREVIEW_CHARS`, `SPAN_CHARS`, `apply_budget`, `estimate_tokens`, `follow_references`, `is_content`, `neighbour_order`, `passage_label`, `predecessor_window`; calls `apply_budget`, `estimate_tokens`, `follow_references`, `is_content`, `neighbour_order`, `passage_label`, `predecessor_window`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/experiments/contextual_embeddings/answers|learnloop.experiments.contextual_embeddings.answers]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/bank|learnloop.experiments.contextual_embeddings.bank]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/paid|learnloop.experiments.contextual_embeddings.paid]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_e0_delivery.py](../../../../../../../tests/test_e0_delivery.py) — direct import
  - `test_a_source_that_does_not_fit_runs_the_named_fallback_never_a_truncation`
  - `test_d0_and_d1_reproduce_the_production_reader_delivery`
  - `test_d0_cuts_cover_only_their_canonical_prefix`
  - `test_d2_is_the_whole_permitted_section_and_d3_the_whole_permitted_source`
  - `test_retrieved_d0_and_d1_deliver_the_same_initial_evidence`
- [tests/test_e0_review_round1.py](../../../../../../../tests/test_e0_review_round1.py) — direct import
  - `test_f10_verdicts_enter_judgment_ledger_once`
  - `test_f6_a_quote_over_withheld_spans_falls_back_to_the_selected_block`
  - `test_f6_deictic_questions_carry_their_own_selection_to_every_role`
- [tests/test_e0_review_round2.py](../../../../../../../tests/test_e0_review_round2.py) — direct import
  - `test_f6_a_permitted_quote_is_still_delivered`
  - `test_f6_a_rejected_quote_never_reaches_delivery_tutor_or_judges`
  - `test_f6_delivery_refuses_a_protected_quote_even_from_an_unfrozen_selection`
- [tests/test_e0_review_round4.py](../../../../../../../tests/test_e0_review_round4.py) — direct import
  - `test_h7_a_quote_without_complete_canonical_coverage_is_dropped`

## Modification guidance

- Make changes here when the responsibility remains delivery within learnloop.experiments.contextual_embeddings; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/experiments/contextual_embeddings/delivery.py](../../../../../../../src/learnloop/experiments/contextual_embeddings/delivery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
