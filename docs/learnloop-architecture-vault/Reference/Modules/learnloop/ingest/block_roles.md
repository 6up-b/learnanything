---
title: "learnloop.ingest.block_roles"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/block_roles.py"
source_paths:
  - "src/learnloop/ingest/block_roles.py"
source_commit: "9e7cafc82c7b6d5a5b480c9c132c4a293bb1c141"
source_commit_timestamp: "2026-10-27T05:54:16-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ingest"
layer: "infrastructure"
concepts:
  - "Architecture Overview"
workflows:
  - "Import Canonical Sources"
aliases:
  - "learnloop.ingest.block_roles module"
  - "src/learnloop/ingest/block_roles.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.block_roles`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.block_roles` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Deterministic block-role hints (spec_source_ingestion_v2 §2.6).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py) |
| Source lines | 378 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `9e7cafc82c7b6d5a5b480c9c132c4a293bb1c141` |
| Commit timestamp | `2026-10-27T05:54:16-04:00` |

## Public API

- `lead_role(text: str) -> str | None` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 101) — The role a block's own lead text names ("Solution:", "Example 5.2"), or None.
- `unit_heading_role(heading: str | None) -> str | None` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 112) — The role of a heading that names a whole exercise, solution or example unit, or None for any other heading (a teaching section's title that only contains such a word).
- `classify_block_role(block_type: str, section_path: list[str] | None, text: str) -> str` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 125) — Return the most likely pedagogical role for a block (§2.6).
- `class NumberedLabel` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 231) — A block's own number: ``kind`` (normalized; None for a bare number-first label such as "1.3 properties of complex arithmetic"), ``number``, and whether the number leads the block (``number_first``: the books that refer to results by bare number, "by 1.32").
  - `text(self) -> str` (line 242; public)
- `class NumberedReference` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 247) — One numbered environment a passage refers to, as written (``text``).
- `numbered_label(text: str, block_type: str='') -> NumberedLabel | None` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 256) — The numbered environment a block opens ("Theorem 3.2 (Name).
- `numbered_references(text: str) -> list[NumberedReference]` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 290) — The numbered environments ``text`` refers to, in order of appearance.
- `figure_numbers(text: str | None) -> set[str]` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 337) — The figure numbers a text names ("Figure 3.2", "Fig.
- `figure_is_unsafe(role: str | None, rejected: str | None) -> bool` ([source](../../../../../../src/learnloop/ingest/block_roles.py), line 370) — Whether a figure's recorded role makes it unsafe content: an answer or worked role, or a refused stimulus claim whose reason says so (an unknown reason does: fail closed).

### Module constants

- `ROLES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 15)
- `_BLOCK_TYPE_ROLES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 31)
- `_CUES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 47)
- `_WORKED_LEAD_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 61)
- `_ENVIRONMENT_WORDS` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 62)
- `_LEAD_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 65)
- `_LEAD_ROLE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 66)
- `_UNIT_WORDS` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 86)
- `_UNIT_FILLER` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 93)
- `_ROMAN_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 97)
- `_UNIT_ROLE_ORDER` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 98)
- `NUMBERED_KINDS` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 163)
- `_NUMBER` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 167)
- `_LABEL_PREFIX` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 170)
- `_LABEL_END` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 173)
- `_NUMBERED_LEAD_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 174)
- `_NUMBER_FIRST_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 179)
- `_EQUATION_TAG_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 185)
- `_EQUATION_END_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 186)
- `_EQUATION_BLOCK_TYPES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 187)
- `_TOC_LEADER_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 194)
- `_TOC_COLUMN_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 195)
- `_TOC_BLOCK_TYPES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 196)
- `_REF_KINDS` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 198)
- `_REF_KIND_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 214)
- `_REF_ONE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 218)
- `_REF_SEPARATOR` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 219)
- `_REFERENCE_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 220)
- `_BARE_REFERENCE_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 226)
- `_NUMBER_IN_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 227)
- `_FIGURE_REFERENCE_RE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 333)
- `FIGURE_ANSWER_ROLES` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 354)
- `FIGURE_REJECTED_ANOTHER_ANSWER` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 356)
- `FIGURE_REJECTED_NUMBER_MISMATCH` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 357)
- `FIGURE_REJECTION_UNSAFE` ([src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py), line 364)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `FIGURE_ANSWER_ROLES`, `FIGURE_REJECTED_ANOTHER_ANSWER`, `FIGURE_REJECTED_NUMBER_MISMATCH`, `figure_numbers`; statically calls `figure_numbers`
- [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]] — imports `lead_role`, `numbered_label`, `numbered_references`; statically calls `lead_role`, `numbered_label`, `numbered_references`
- [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]] — imports `classify_block_role`, `numbered_label`; statically calls `classify_block_role`, `numbered_label`
- [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]] — imports `classify_block_role`; statically calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] — imports `classify_block_role`; statically calls `classify_block_role`
- [[Reference/Modules/learnloop/ingest/extractors/pypdf|learnloop.ingest.extractors.pypdf]] — imports `classify_block_role`; statically calls `classify_block_role`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `figure_is_unsafe`; statically calls `figure_is_unsafe`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `lead_role`, `unit_heading_role`; statically calls `lead_role`, `unit_heading_role`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `lead_role`; statically calls `lead_role`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `lead_role`; statically calls `lead_role`
- [[Reference/Modules/learnloop/tutor/context_delivery|learnloop.tutor.context_delivery]] — imports `NumberedLabel`, `NumberedReference`, `lead_role`, `numbered_label`, `numbered_references`; statically calls `lead_role`, `numbered_label`, `numbered_references`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `lead_role`; statically calls `lead_role`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/experiments/contextual_embeddings/corpus|learnloop.experiments.contextual_embeddings.corpus]], [[Reference/Modules/learnloop/ingest/extractors/glm_ocr|learnloop.ingest.extractors.glm_ocr]], [[Reference/Modules/learnloop/ingest/extractors/marker|learnloop.ingest.extractors.marker]], [[Reference/Modules/learnloop/ingest/extractors/normalizers|learnloop.ingest.extractors.normalizers]] and 7 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — direct import
- [tests/test_document_ir.py](../../../../../../tests/test_document_ir.py) — direct import
  - `test_block_role_classifier_recognizes_structures`
- [tests/test_glm_ocr.py](../../../../../../tests/test_glm_ocr.py) — direct import
  - `test_cr_f2_list_items_keep_their_numbers_without_the_documents_numbering_behind_them`
  - `test_cr_f5_a_formulas_own_brackets_never_stop_an_equation_number_from_coming_back`
  - `test_q2c_split_numbering_is_collapsed_where_it_is_a_label`
  - `test_q3_a_real_pdfs_text_layer_gives_the_footnote_and_the_equation_number`
  - `test_q3_equation_numbers_become_tags_that_numbered_label_reads`
- [tests/test_reader_ca1_astra_redesign.py](../../../../../../tests/test_reader_ca1_astra_redesign.py) — direct import
  - `test_every_rejection_reason_the_validator_emits_is_classified`
- [tests/test_source_retrieval_rereview.py](../../../../../../tests/test_source_retrieval_rereview.py) — direct import
  - `test_heading_cues_do_not_drop_teaching_sections_from_practice`
- [tests/test_tutor_delivery_fixes.py](../../../../../../tests/test_tutor_delivery_fixes.py) — direct import
  - `test_numbered_labels`
  - `test_numbered_references`
  - `test_numbered_statements_ending_in_a_number_are_labels_and_toc_lines_are_not`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/block_roles.py](../../../../../../src/learnloop/ingest/block_roles.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
