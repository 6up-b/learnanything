---
title: "learnloop.ai.chatgpt_plan.routes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/chatgpt_plan/routes.py"
source_paths:
  - "src/learnloop/ai/chatgpt_plan/routes.py"
source_commit: "71c35989c55fc30b9f80cf5bbd019ebb7240c137"
source_commit_timestamp: "2026-10-12T21:47:01-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ai.chatgpt_plan"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.chatgpt_plan.routes module"
  - "src/learnloop/ai/chatgpt_plan/routes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai-chatgpt-plan"
---

# `learnloop.ai.chatgpt_plan.routes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ai.chatgpt_plan.routes` exists within [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] to own the behavior summarized by its module contract: Which configured routes use a ChatGPT-plan profile (config only, no network).

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/chatgpt_plan/routes.py](../../../../../../../src/learnloop/ai/chatgpt_plan/routes.py) |
| Source lines | 43 |
| Owning package | [[Reference/Modules/learnloop/ai/chatgpt_plan/_package|learnloop.ai.chatgpt_plan]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `71c35989c55fc30b9f80cf5bbd019ebb7240c137` |
| Commit timestamp | `2026-10-12T21:47:01-04:00` |

## Public API

- `plan_profiles(config: LearnLoopConfig) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/ai/chatgpt_plan/routes.py), line 10) — Every ``chatgpt_plan`` profile and the routes that name it.

### Explicit exports

`__all__` declares:

- `plan_profiles`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]] — imports `plan_profiles`; statically calls `plan_profiles`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `plan_profiles`; statically calls `plan_profiles`
- [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]] — imports `plan_profiles`; statically calls `plan_profiles`
- [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]] — imports `plan_profiles`; statically calls `plan_profiles`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/routing|learnloop.ai.routing]] — imports `route_names`; calls `route_names`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `CHATGPT_PLAN_PROFILE_TYPE`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ai|learnloop.cli.ai]], [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]], [[Reference/Modules/learnloop/ops/plan_transport|learnloop.ops.plan_transport]], [[Reference/Modules/learnloop_sidecar/handlers/chatgpt_plan|learnloop_sidecar.handlers.chatgpt_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_apply_write_ahead.py](../../../../../../../tests/test_apply_write_ahead.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_assessment_enforcement.py](../../../../../../../tests/test_assessment_enforcement.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_calibration.py](../../../../../../../tests/test_calibration.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_chatgpt_plan_cli.py](../../../../../../../tests/test_chatgpt_plan_cli.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_codex_runtime.py](../../../../../../../tests/test_codex_runtime.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_concepts.py](../../../../../../../tests/test_concepts.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_contract_reachability.py](../../../../../../../tests/test_contract_reachability.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_contrast_pairs.py](../../../../../../../tests/test_contrast_pairs.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_diagnosis_pipeline.py](../../../../../../../tests/test_diagnosis_pipeline.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_discrimination_profiles.py](../../../../../../../tests/test_discrimination_profiles.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_doctor.py](../../../../../../../tests/test_doctor.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]
- [tests/test_error_hunt_items.py](../../../../../../../tests/test_error_hunt_items.py) — imports consumer [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]]

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/chatgpt_plan/routes.py](../../../../../../../src/learnloop/ai/chatgpt_plan/routes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
