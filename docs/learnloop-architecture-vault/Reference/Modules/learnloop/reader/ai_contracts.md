---
title: "learnloop.reader.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/reader/ai_contracts.py"
source_paths:
  - "src/learnloop/reader/ai_contracts.py"
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
  - "learnloop.reader.ai_contracts module"
  - "src/learnloop/reader/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-reader"
---

# `learnloop.reader.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.reader.ai_contracts` exists within [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] to own the behavior summarized by its module contract: Structured AI contracts owned by reader producers.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py) |
| Source lines | 117 |
| Owning package | [[Reference/Modules/learnloop/reader/_package|learnloop.reader]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ReaderPresetSynthesisContext` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 14)
- `class ReadingQuickCheckContext` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 26)
- `class ReaderPresetSynthesis(WireModel)` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 31)
- `class ReadingQuickCheck(WireModel)` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 36)
- `reader_preset_synthesis_prompt(context: ReaderPresetSynthesisContext) -> str` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 104)
- `reading_quick_check_prompt(context: ReadingQuickCheckContext) -> str` ([source](../../../../../../src/learnloop/reader/ai_contracts.py), line 112)

### Module constants

- `READER_PRESET_SYNTHESIS_PROMPT_VERSION` ([src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py), line 42)
- `READING_QUICK_CHECK_PROMPT_VERSION` ([src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py), line 43)
- `READER_PRESET_SYNTHESIS_PROMPT` ([src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py), line 45)
- `READING_QUICK_CHECK_PROMPT` ([src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py), line 80)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]] — imports `READING_QUICK_CHECK_PROMPT_VERSION`, `ReadingQuickCheck`, `ReadingQuickCheckContext`, `reading_quick_check_prompt`; statically calls `ReadingQuickCheckContext`, `reading_quick_check_prompt`
- [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]] — imports `ReaderPresetSynthesis`, `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`; statically calls `ReaderPresetSynthesisContext`, `reader_preset_synthesis_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Reader to Practice Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/reader/reader_quick_check|learnloop.reader.reader_quick_check]], [[Reference/Modules/learnloop/reader/reader_requests|learnloop.reader.reader_requests]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_sdk_reader_preset_regenerates_when_app_server_rejects_hex_escape`
  - `test_sdk_reader_preset_repairs_invalid_unicode_json_once`
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_reader_quick_check.py](../../../../../../tests/test_reader_quick_check.py) — direct import
  - `test_author_quick_check_rejects_invented_spans`
- [tests/test_reader_requests.py](../../../../../../tests/test_reader_requests.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/reader/ai_contracts.py](../../../../../../src/learnloop/reader/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
