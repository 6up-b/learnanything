---
title: "learnloop.reader.reader_restoration"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_restoration.py"
source_paths:
  - "src/learnloop/reader/reader_restoration.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.reader"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Reader to Practice Workflow"
aliases:
  - "learnloop.reader.reader_restoration module"
  - "src/learnloop/reader/reader_restoration.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_restoration`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_restoration` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: P3 slice 3, step 10 -- post-cold reader restoration (spec_p3_reader_integration §11, design B step 10).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_restoration.py](../../../../../../src/learnloop/reader/reader_restoration.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderRestorationError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_restoration.py), line 44) — Domain error for the reader-restoration service.
- `restore(repository: Repository, *, source_id: str, extraction_id: str | None=None, run_id: str | None=None, idempotency_key: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_restoration.py), line 53) — Restore source + annotations after a closed cold observation (§11).
- `restore_before_response(repository: Repository, *, extraction_id: str, span_id: str, cold_surface_id: str | None=None, cold_administration_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_restoration.py), line 150) — Opening restoration material BEFORE the cold response (§11, §15.6): appends a contamination/feedback exposure event and removes cold eligibility.

### Module constants

- `RESTORATION_SCHEMA_VERSION` ([src/learnloop/reader/reader_restoration.py](../../../../../../src/learnloop/reader/reader_restoration.py), line 37)
- `_ATTACHABLE` ([src/learnloop/reader/reader_restoration.py](../../../../../../src/learnloop/reader/reader_restoration.py), line 40)
- `_REVIEW` ([src/learnloop/reader/reader_restoration.py](../../../../../../src/learnloop/reader/reader_restoration.py), line 41)

## Internal implementation anchors

- `_annotation_provenance(head: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/reader/reader_restoration.py), line 48)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `restore`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/salience_firewall|learnloop.attempts.salience_firewall]] — imports `salience_payload`; calls `salience_payload`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/golden_path_restoration|learnloop.curriculum.golden_path_restoration]] — imports `module`; calls `restore`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; calls `restore_source`
- [[Reference/Modules/learnloop/reader/span_view|learnloop.reader.span_view]] — imports `SpanViewError`, `build_span_view`; calls `build_span_view`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `log_interaction_event`; calls `log_interaction_event`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p3_journeys.py](../../../../../../tests/test_p3_journeys.py) — direct import
  - `test_annotation_survival_across_reextraction`
  - `test_journey2_quick_insight_capture`
  - `test_journey7_tutor_exchange_to_durable`
- [tests/test_reader_restoration.py](../../../../../../tests/test_reader_restoration.py) — direct import
  - `test_early_open_is_contamination`
  - `test_orphaned_annotation_shows_quote_without_false_attachment`
  - `test_restoration_records_salience_exposure_and_cannot_be_evidence`
  - `test_restore_returns_cited_blocks_and_annotation_heads_alongside_learner_wording`

## Modification guidance

- Change reader restoration policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_restoration.py](../../../../../../src/learnloop/reader/reader_restoration.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
