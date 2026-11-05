---
title: "learnloop.ingest.locators"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ingest/locators.py"
source_paths:
  - "src/learnloop/ingest/locators.py"
source_commit: "5ce697ea8f4fd05519152bfa2f9f7b9e53cf14fa"
source_commit_timestamp: "2026-07-13T21:17:38-04:00"
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
  - "learnloop.ingest.locators module"
  - "src/learnloop/ingest/locators.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ingest"
---

# `learnloop.ingest.locators`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ingest.locators` exists within [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] to own the behavior summarized by its module contract: Locator schemes (spec_source_ingestion_v2 §2.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py) |
| Source lines | 69 |
| Owning package | [[Reference/Modules/learnloop/ingest/_package|learnloop.ingest]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `5ce697ea8f4fd05519152bfa2f9f7b9e53cf14fa` |
| Commit timestamp | `2026-07-13T21:17:38-04:00` |

## Public API

- `format_block_span(extraction_id: str, span_id: str) -> str` ([source](../../../../../../src/learnloop/ingest/locators.py), line 35) — Build a ``block_span_v1`` locator (§2.4).
- `parse_block_span(locator: str) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/ingest/locators.py), line 41) — Return ``(extraction_id, span_id)`` for a ``block_span_v1`` locator.
- `detect_locator_scheme(locator: str) -> str | None` ([source](../../../../../../src/learnloop/ingest/locators.py), line 50) — Shape-detect the declared scheme of a (legacy or new) locator ref.

### Module constants

- `BLOCK_SPAN_V1` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 20)
- `HEADING_PATH_V1` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 21)
- `TIME_RANGE_V1` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 22)
- `ARXIV_LABEL_V1` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 23)
- `KNOWN_SCHEMES` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 25)
- `_BLOCK_SPAN_RE` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 27)
- `_TIME_RANGE_RE` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 28)
- `_ARXIV_LABEL_RE` ([src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py), line 32)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] — imports `BLOCK_SPAN_V1`, `format_block_span`, `parse_block_span`; statically calls `format_block_span`, `parse_block_span`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/sources/span_aliases|learnloop.content.sources.span_aliases]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `detect_locator_scheme`; statically calls `detect_locator_scheme`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/diagnosis/text_gaps/provenance|learnloop.diagnosis.text_gaps.provenance]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/practice_index/dossiers|learnloop.practice_index.dossiers]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/as_printed|learnloop.reader.as_printed]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/reader_authoring|learnloop.reader.reader_authoring]] — imports `BLOCK_SPAN_V1`, `format_block_span`, `parse_block_span`; statically calls `format_block_span`, `parse_block_span`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/reader/workbench|learnloop.reader.workbench]] — imports `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/reading_sources|learnloop.reading_sources]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/remote/sources|learnloop.remote.sources]] — imports `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/source_retrieval/corpus|learnloop.source_retrieval.corpus]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/source_retrieval/find_sources|learnloop.source_retrieval.find_sources]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/source_retrieval/reader_tutor|learnloop.source_retrieval.reader_tutor]] — imports `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_card|learnloop.adaptive_difficulty.history_card]], [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]], [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]], [[Reference/Modules/learnloop/content/facet_identity/authority|learnloop.content.facet_identity.authority]] and 23 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — direct import
- [tests/test_compare_sources.py](../../../../../../tests/test_compare_sources.py) — direct import
  - `test_pins_obey_the_policy_in_a_practice_context`
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_a_repair_never_teaches_from_an_exam_passage`
  - `test_cross_source_teaching_spans_never_carry_exam_material`
  - `test_post_attempt_never_reopens_an_exam_extraction_or_an_exam_item_s_own_span`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
  - `test_pf_never_forwards_a_held_out_parent_quote`
- [tests/test_find_sources_intents.py](../../../../../../tests/test_find_sources_intents.py) — direct import
  - `test_facet_ids_target_retrieval_and_verification`
  - `test_post_attempt_opens_the_solution_only_after_the_window_closes_and_records_a_reveal`
  - `test_remediate_reads_correction_refs_and_reports_missing_sources`
- [tests/test_learner_data_relax_2.py](../../../../../../tests/test_learner_data_relax_2.py) — direct import
- [tests/test_prescription_passages.py](../../../../../../tests/test_prescription_passages.py) — direct import
- [tests/test_roles_judges.py](../../../../../../tests/test_roles_judges.py) — direct import
  - `test_rw3b_contrast_list_a_confident_contrast_the_judge_may_not_be_shown_never_blocks_the_low_one`
- [tests/test_roles_switch_off_legacy_parity.py](../../../../../../tests/test_roles_switch_off_legacy_parity.py) — direct import
- [tests/test_router_r2a_landing.py](../../../../../../tests/test_router_r2a_landing.py) — direct import
- [tests/test_source_layer.py](../../../../../../tests/test_source_layer.py) — direct import
  - `test_backfill_locator_schemes_stamps_and_is_idempotent`
  - `test_block_span_locator_round_trip`
  - `test_locator_scheme_shape_detection`

## Modification guidance

- Change acquisition or extraction mechanics here; keep source-library and downstream learning-content policy in `learnloop.content`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ingest/locators.py](../../../../../../src/learnloop/ingest/locators.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
