---
title: "learnloop.curriculum.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/curriculum/ai_contracts.py"
source_paths:
  - "src/learnloop/curriculum/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.curriculum"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Build a Study Map"
aliases:
  - "learnloop.curriculum.ai_contracts module"
  - "src/learnloop/curriculum/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-curriculum"
---

# `learnloop.curriculum.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.curriculum.ai_contracts` exists within [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] to own the behavior summarized by its module contract: Structured AI contracts owned by curriculum depth features.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py) |
| Source lines | 143 |
| Owning package | [[Reference/Modules/learnloop/curriculum/_package|learnloop.curriculum]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class RungBackfillItem(WireModel)` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 13) — One legacy item's rung classification (candidate-only; deterministic validators admit or skip each entry).
- `class DepthEdgeInstancePayload(WireModel)` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 22) — One LLM-authored depth-edge instance (candidate-only; spec v2 §depth).
- `class RungBackfillContext` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 50)
- `class DepthEdgeInstanceContext` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 56)
- `class RungBackfillClassification(WireModel)` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 66)
- `class DepthEdgeInstanceBatch(WireModel)` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 70)
- `rung_backfill_prompt(context: RungBackfillContext) -> str` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 130)
- `depth_edge_instance_prompt(context: DepthEdgeInstanceContext) -> str` ([source](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 138)

### Module constants

- `RUNG_BACKFILL_PROMPT_VERSION` ([src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 74)
- `DEPTH_EDGE_INSTANCE_PROMPT_VERSION` ([src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 75)
- `RUNG_BACKFILL_PROMPT` ([src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 77)
- `DEPTH_EDGE_INSTANCE_PROMPT` ([src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py), line 104)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]] — imports `DepthEdgeInstanceBatch`, `DepthEdgeInstanceContext`, `depth_edge_instance_prompt`; statically calls `DepthEdgeInstanceContext`, `depth_edge_instance_prompt`
- [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]] — imports `RungBackfillClassification`, `RungBackfillContext`, `rung_backfill_prompt`; statically calls `RungBackfillContext`, `rung_backfill_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `TaskFeaturesPayload`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/depth_edge_authoring|learnloop.curriculum.depth_edge_authoring]], [[Reference/Modules/learnloop/curriculum/rung_backfill|learnloop.curriculum.rung_backfill]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/curriculum/ai_contracts.py](../../../../../../src/learnloop/curriculum/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
