---
title: "learnloop.content.pipeline.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/content/pipeline/ai_contracts.py"
source_paths:
  - "src/learnloop/content/pipeline/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.content.pipeline"
layer: "domain"
concepts:
  - "Learning System"
  - "AI Architecture"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.content.pipeline.ai_contracts module"
  - "src/learnloop/content/pipeline/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-content-pipeline"
---

# `learnloop.content.pipeline.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.content.pipeline.ai_contracts` exists within [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] to own the behavior summarized by its module contract: Feature-owned canonical-ingest AI input and prompt.

The authoritative system-level explanation remains in [[Learning System]], [[AI Architecture]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/content/pipeline/ai_contracts.py](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py) |
| Source lines | 85 |
| Owning package | [[Reference/Modules/learnloop/content/pipeline/_package|learnloop.content.pipeline]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class SourceChunk` ([source](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py), line 20)
- `class ExtractionPlan` ([source](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py), line 30)
- `class CanonicalIngestContext` ([source](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py), line 41)
- `canonical_ingest_prompt(context: CanonicalIngestContext) -> str` ([source](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py), line 57)

### Module constants

- `CANONICAL_INGEST_PROMPT_VERSION` ([src/learnloop/content/pipeline/ai_contracts.py](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py), line 54)

### Explicit exports

`__all__` declares:

- `CANONICAL_INGEST_PROMPT_VERSION`
- `CanonicalIngestContext`
- `ChunkKind`
- `ExtractionPlan`
- `SourceChunk`
- `SourceKind`
- `canonical_ingest_prompt`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]] — imports `CANONICAL_INGEST_PROMPT_VERSION`, `CanonicalIngestContext`, `ExtractionPlan`, `SourceChunk`, `SourceKind`, `canonical_ingest_prompt`; statically calls `CanonicalIngestContext`, `ExtractionPlan`, `SourceChunk`, `canonical_ingest_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `_AUDIT_GUIDANCE`, `_DIFFICULTY_GUIDANCE`, `_PRACTICE_METADATA_GUIDANCE`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/content/pipeline/source_ingestion|learnloop.content.pipeline.source_ingestion]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../../tests/structured_ai.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../../tests/test_codex_output_schema.py) — direct import
- [tests/test_exam_seeding.py](../../../../../../../tests/test_exam_seeding.py) — direct import
- [tests/test_ingest_instrument_gates.py](../../../../../../../tests/test_ingest_instrument_gates.py) — direct import
- [tests/test_source_ingestion.py](../../../../../../../tests/test_source_ingestion.py) — direct import
- [tests/test_source_ingestion_adapters.py](../../../../../../../tests/test_source_ingestion_adapters.py) — direct import
- [tests/test_source_layer.py](../../../../../../../tests/test_source_layer.py) — direct import
  - `test_legacy_locators_still_resolve_after_backfill`
- [tests/test_structured_transport_parity.py](../../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/content/pipeline/ai_contracts.py](../../../../../../../src/learnloop/content/pipeline/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
