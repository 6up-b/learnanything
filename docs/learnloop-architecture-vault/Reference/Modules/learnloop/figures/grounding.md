---
title: "learnloop.figures.grounding"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/figures/grounding.py"
source_paths:
  - "src/learnloop/figures/grounding.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.figures"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.figures.grounding module"
  - "src/learnloop/figures/grounding.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-figures"
---

# `learnloop.figures.grounding`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.figures.grounding` exists within [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] to own the behavior summarized by its module contract: What a figure's author is sent from the learner's books: the passage and its neighbours, or retrieved passages.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py) |
| Source lines | 307 |
| Owning package | [[Reference/Modules/learnloop/figures/_package|learnloop.figures]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SourceContext` ([source](../../../../../../src/learnloop/figures/grounding.py), line 37)
- `class Grounding` ([source](../../../../../../src/learnloop/figures/grounding.py), line 49) — Where a request's source text comes from (spec §8.3): ``anchor`` (the learner chose the passage), ``retrieved`` (found in their books for the goal) or ``none`` (nothing found: an illustration that quotes nothing).
- `source_context(vault: Any, repository: Repository, request: FigureRequest) -> SourceContext` ([source](../../../../../../src/learnloop/figures/grounding.py), line 65)
- `passages_context(vault: Any, repository: Repository, grounding: Grounding) -> SourceContext` ([source](../../../../../../src/learnloop/figures/grounding.py), line 99) — RW5d: the retrieved passages as the author is sent them (spec §8.2, §8.3): each kept block with the paragraphs around it (held-out ones left out), keyed ``extraction_id:span_id`` so a quote is verified against the right block of the right book.
- `ground(vault: Any, repository: Repository, request: FigureRequest, *, find: FindSources | None=None) -> Grounding` ([source](../../../../../../src/learnloop/figures/grounding.py), line 207) — A request's grounding (spec §8.3).
- `crop_image(repository: Repository, request: FigureRequest, context: SourceContext) -> tuple[tuple[str, bytes] | None, str | None, list[float] | None]` ([source](../../../../../../src/learnloop/figures/grounding.py), line 273) — ``(image, asset span, clipped region box)``: a region's crop only, or the figure block's crop; nothing for a selection with no figure.

### Module constants

- `GROUNDING_PASSAGES` ([src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py), line 28)
- `FIGURE_BLOCK_TYPES` ([src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py), line 29)
- `CONTEXT_BLOCKS` ([src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py), line 31)
- `PASSAGE_CHARS` ([src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py), line 32)
- `CONTEXT_CHARS` ([src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py), line 33)

### Explicit exports

`__all__` declares:

- `CONTEXT_BLOCKS`
- `CONTEXT_CHARS`
- `FIGURE_BLOCK_TYPES`
- `FindSources`
- `GROUNDING_PASSAGES`
- `Grounding`
- `PASSAGE_CHARS`
- `SourceContext`
- `crop_image`
- `ground`
- `passages_context`
- `source_context`

## Internal implementation anchors

- `_find_sources(vault: Any, repository: Repository, query: str, **kwargs: Any) -> Any` ([source](../../../../../../src/learnloop/figures/grounding.py), line 155)
- `_reading_learning_objects(vault: Any, repository: Repository, reading_at: Mapping[str, Any] | None) -> list[str]` ([source](../../../../../../src/learnloop/figures/grounding.py), line 161) — The learning objects of the passage the learner was reading (retrieval context only).
- `_passage_ref(hit: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/figures/grounding.py), line 175)
- `_with_sources(repository: Repository, passages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/figures/grounding.py), line 181) — Each passage with its source's id and title (Codex review F8: the Reader's citation chips peek in this book and open another as a detour, which needs the source).
- `_decode(render: str | None) -> tuple[str, bytes] | None` ([source](../../../../../../src/learnloop/figures/grounding.py), line 263)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]] — imports `FindSources`, `Grounding`, `SourceContext`, `crop_image`, `ground`, `passages_context`, `source_context`; statically calls `Grounding`, `crop_image`, `ground`, `passages_context`, `source_context`
- [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]] — imports `module`; statically calls `source_context`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/figure_admission|learnloop.figure_admission]] — imports `FiguresChanged`, `GROUNDING_PASSAGES`
- [[Reference/Modules/learnloop/figures/protection|learnloop.figures.protection]] — imports `keys_withheld`; calls `keys_withheld`
- [[Reference/Modules/learnloop/figures/request|learnloop.figures.request]] — imports `FigureRefused`, `FigureRequest`, `anchored`; calls `FigureRefused`, `anchored`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `build_block_region`; calls `build_block_region`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `find_sources_for_caller`; calls `find_sources_for_caller`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `CallerContext`; calls `CallerContext`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `passage_learning_objects`; calls `passage_learning_objects`

### Platform and third-party dependencies

- Standard library: `__future__`, `base64`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/figures/build|learnloop.figures.build]], [[Reference/Modules/learnloop/figures/prefetch|learnloop.figures.prefetch]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/identity_pins_helpers.py](../../../../../../tests/identity_pins_helpers.py) — direct import
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_iv_with_the_student_off_rw5ds_grounding_retrieval_is_p1s`
- [tests/test_figure_rich_contract.py](../../../../../../tests/test_figure_rich_contract.py) — direct import
  - `test_the_reuse_key_names_the_menu_and_the_rich_versions`
  - `test_with_no_rich_tier_on_the_menu_the_contract_is_v2s_byte_for_byte`
- [tests/test_figure_rich_rereview_fixes.py](../../../../../../tests/test_figure_rich_rereview_fixes.py) — direct import
  - `test_a_different_kind_hashes_apart_from_the_ordinary_correction`
- [tests/test_figures_rw5b_review.py](../../../../../../tests/test_figures_rw5b_review.py) — direct import
  - `test_the_reuse_key_never_names_the_origin_and_keeps_rw5as_keys`
- [tests/test_figures_show_me.py](../../../../../../tests/test_figures_show_me.py) — direct import
  - `test_a_goal_alone_is_grounded_in_the_books_and_lands_where_the_learner_was`
- [tests/test_followups_batch7_prefetch_capped_resume.py](../../../../../../tests/test_followups_batch7_prefetch_capped_resume.py) — direct import
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
  - `test_switched_off_the_payload_prompt_and_key_are_the_predecessors_byte_for_byte`
  - `test_the_learner_state_reaches_the_author_and_protected_work_never_does`
  - `test_the_reuse_key_and_prompt_version_name_the_state_only_when_non_empty`
  - `test_the_rich_author_receives_what_the_figure_author_received`
- [tests/test_rw5c_recheck.py](../../../../../../tests/test_rw5c_recheck.py) — direct import
  - `test_the_reuse_key_is_unchanged_without_a_source_check_id`
- [tests/test_rw5c_source_check.py](../../../../../../tests/test_rw5c_source_check.py) — direct import
  - `test_build_key_holds_the_switch_and_the_reuse_key_does_not`
- [tests/test_sketch_service.py](../../../../../../tests/test_sketch_service.py) — direct import
  - `test_without_the_engine_the_contract_prompt_and_key_are_rw5bs_byte_for_byte`

## Modification guidance

- Make changes here when the responsibility remains grounding within learnloop.figures; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/figures/grounding.py](../../../../../../src/learnloop/figures/grounding.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
