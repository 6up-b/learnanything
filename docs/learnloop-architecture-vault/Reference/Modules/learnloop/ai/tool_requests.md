---
title: "learnloop.ai.tool_requests"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/tool_requests.py"
source_paths:
  - "src/learnloop/ai/tool_requests.py"
source_commit: "d9ea71ceca56513332f1893187c8d54befa0173e"
source_commit_timestamp: "2026-10-13T02:22:30-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.tool_requests module"
  - "src/learnloop/ai/tool_requests.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.tool_requests`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.tool_requests` exists within [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] to own the behavior summarized by its module contract: Tool requests as structured output (spec_source_practice_and_probes_v1 §10.2; S4).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/tool_requests.py](../../../../../../src/learnloop/ai/tool_requests.py) |
| Source lines | 53 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `d9ea71ceca56513332f1893187c8d54befa0173e` |
| Commit timestamp | `2026-10-13T02:22:30-04:00` |

## Public API

- `class FindPracticeRequest(WireModel)` ([source](../../../../../../src/learnloop/ai/tool_requests.py), line 25)
- `class FindSourcesRequest(WireModel)` ([source](../../../../../../src/learnloop/ai/tool_requests.py), line 34)
- `class CompareSourcesRequest(WireModel)` ([source](../../../../../../src/learnloop/ai/tool_requests.py), line 42)

### Module constants

- `TUTOR_TOOLS` ([src/learnloop/ai/tool_requests.py](../../../../../../src/learnloop/ai/tool_requests.py), line 22)

### Explicit exports

`__all__` declares:

- `CompareSourcesRequest`
- `FindPracticeRequest`
- `FindSourcesRequest`
- `TUTOR_TOOLS`
- `ToolRequest`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `ToolRequest`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/library_ask_fixtures.py](../../../../../../tests/library_ask_fixtures.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/reader_tutor_fakes.py](../../../../../../tests/reader_tutor_fakes.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/source_service_fakes.py](../../../../../../tests/source_service_fakes.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_authoring_contract.py](../../../../../../tests/test_authoring_contract.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_field_signal_production_paths.py](../../../../../../tests/test_field_signal_production_paths.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_figure_offers.py](../../../../../../tests/test_figure_offers.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_figures_codex_review.py](../../../../../../tests/test_figures_codex_review.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]
- [tests/test_figures_rw5b_fix_round2.py](../../../../../../tests/test_figures_rw5b_fix_round2.py) — imports consumer [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]]

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/tool_requests.py](../../../../../../src/learnloop/ai/tool_requests.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
