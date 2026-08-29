---
title: "learnloop.reader.reader_quick_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/reader_quick_check.py"
source_paths:
  - "src/learnloop/reader/reader_quick_check.py"
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
  - "learnloop.reader.reader_quick_check module"
  - "src/learnloop/reader/reader_quick_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.reader_quick_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.reader_quick_check` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Reader quick-check producer: AI-authored section-boundary questions.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderQuickCheckError(ValueError)` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 47) — Domain error for the reader quick-check producer.
- `request_reading_quick_check(client: StructuredTransport, context: ReadingQuickCheckContext) -> ReadingQuickCheck` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 51) — Author one section quick check through the shared transport.
- `section_view(repository: Repository, *, extraction_id: str, section_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 64) — The bounded, readable view of ONE guide section: {section_id, label, blocks:[{span_id, kind, text}]}.
- `author_quick_check(repository: Repository, client: Any, *, extraction_id: str, section_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 93) — Author + persist one quick check for a section (idempotent).
- `record_action(repository: Repository, *, question_id: str, action: str, response_md: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 156) — Record the learner's self-check outcome on the row (salience-only): ``answered`` stamps their response; ``dismissed`` is the durable "don't bring this back".
- `escalate(root: Path, repository: Repository, *, question_id: str, learning_object_id: str, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/reader/reader_quick_check.py), line 186) — Escalate an authored quick check into a real PracticeItem.

### Module constants

- `MAX_SECTION_BLOCKS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 41)
- `MAX_SECTION_CHARS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 42)
- `QUESTION_ACTIONS` ([src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py), line 44)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]] — imports `module`; statically calls `author_quick_check`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `module`; statically calls `escalate`, `record_action`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `StructuredTransport`, `execute_structured_operation`; calls `execute_structured_operation`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/ingest/locators|learnloop.ingest.locators]] — imports `BLOCK_SPAN_V1`, `format_block_span`; calls `format_block_span`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `READING_QUICK_CHECK_PROMPT_VERSION`, `ReadingQuickCheck`, `ReadingQuickCheckContext`, `reading_quick_check_prompt`; calls `ReadingQuickCheckContext`, `reading_quick_check_prompt`
- [[Reference/Modules/learnloop/reader/reader_guidance|learnloop.reader.reader_guidance]] — imports `extraction_sections`; calls `extraction_sections`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/writer|learnloop.vault.writer]] — imports `upsert_practice_item`; calls `upsert_practice_item`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/jobs|learnloop.content.pipeline.jobs]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_quick_check.py](../../../../../../tests/test_reader_quick_check.py) — direct import
  - `test_author_quick_check_is_idempotent_per_section`
  - `test_author_quick_check_persists_span_grounded_row`
  - `test_author_quick_check_rejects_invented_spans`
  - `test_dismissed_question_suppresses_reauthoring_and_display`
  - `test_escalate_mints_practice_item_with_span_provenance`
  - `test_guide_plan_falls_back_to_authored_question`
  - `test_owner_reviewed_placement_wins_over_authored`
  - `test_record_answer_stamps_response_on_the_row`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change reader quick check policy here when reader owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/reader_quick_check.py](../../../../../../src/learnloop/reader/reader_quick_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
