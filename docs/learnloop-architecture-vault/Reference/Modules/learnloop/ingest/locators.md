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
generated_at: "2026-08-18"
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

- [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `detect_locator_scheme`; statically calls `detect_locator_scheme`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`
- [[Reference/Modules/learnloop/reader/source_review|learnloop.reader.source_review]] — imports `parse_block_span`; statically calls `parse_block_span`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `BLOCK_SPAN_V1`, `format_block_span`; statically calls `format_block_span`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/authoring/exercise_authoring|learnloop.content.authoring.exercise_authoring]], [[Reference/Modules/learnloop/content/authoring/practice_leakage|learnloop.content.authoring.practice_leakage]], [[Reference/Modules/learnloop/content/pipeline/revision_refresh|learnloop.content.pipeline.revision_refresh]], [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]], [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] and 4 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

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
