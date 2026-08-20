---
title: "learnloop.diagnosis.ai_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/ai_contracts.py"
source_paths:
  - "src/learnloop/diagnosis/ai_contracts.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.ai_contracts module"
  - "src/learnloop/diagnosis/ai_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.ai_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.ai_contracts` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Structured AI contracts owned by diagnosis and probe features.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py) |
| Source lines | 305 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class MisconceptionMatchContext` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 16)
- `class ProbeInstanceContext` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 23)
- `class ProbeDialogueTurnContext` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 41)
- `class ProbeFamilyTrialsContext` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 55)
- `class MisconceptionMatch(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 71)
- `class DiagnosticTrialResult(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 76)
- `class DiagnosticTrials(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 81)
- `class DiagnosticFireJudgment(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 86)
- `class ProbeInstanceSurface(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 91)
- `class ProbeInstanceSurfaces(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 97)
- `class ProbeDialogueTurn(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 101)
- `class ProbeFamilyTrial(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 106)
- `class ProbeFamilyTrials(WireModel)` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 113)
- `misconception_match_prompt(context: MisconceptionMatchContext) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 212)
- `diagnostic_trials_prompt(context: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 232)
- `diagnostic_fire_prompt(context: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 267)
- `probe_instance_surfaces_prompt(context: ProbeInstanceContext) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 284)
- `probe_dialogue_turn_prompt(context: ProbeDialogueTurnContext) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 292)
- `probe_family_trials_prompt(context: ProbeFamilyTrialsContext) -> str` ([source](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 300)

### Module constants

- `MISCONCEPTION_MATCH_PROMPT_VERSION` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 117)
- `DIAGNOSTIC_TRIALS_PROMPT_VERSION` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 118)
- `PROBE_INSTANCE_PROMPT_VERSION` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 119)
- `PROBE_DIALOGUE_TURN_PROMPT_VERSION` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 120)
- `PROBE_FAMILY_TRIALS_PROMPT_VERSION` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 121)
- `PROBE_INSTANCE_PROMPT` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 123)
- `PROBE_DIALOGUE_TURN_PROMPT` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 156)
- `PROBE_FAMILY_TRIALS_PROMPT` ([src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py), line 186)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]] — imports `DiagnosticFireJudgment`, `DiagnosticTrials`, `diagnostic_fire_prompt`, `diagnostic_trials_prompt`; statically calls `diagnostic_fire_prompt`, `diagnostic_trials_prompt`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `MisconceptionMatch`, `MisconceptionMatchContext`, `misconception_match_prompt`; statically calls `MisconceptionMatchContext`, `misconception_match_prompt`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `PROBE_DIALOGUE_TURN_PROMPT_VERSION`, `ProbeDialogueTurn`, `ProbeDialogueTurnContext`, `probe_dialogue_turn_prompt`; statically calls `ProbeDialogueTurnContext`, `probe_dialogue_turn_prompt`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `PROBE_INSTANCE_PROMPT_VERSION`, `ProbeFamilyTrials`, `ProbeFamilyTrialsContext`, `ProbeInstanceContext`, `ProbeInstanceSurfaces`, `probe_family_trials_prompt`, `probe_instance_surfaces_prompt`; statically calls `ProbeFamilyTrialsContext`, `ProbeInstanceContext`, `probe_family_trials_prompt`, `probe_instance_surfaces_prompt`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `prompt_safe`, `render_structured_prompt`; calls `prompt_safe`, `render_structured_prompt`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `GRADING_PROMPT_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/diagnostic_gate|learnloop.diagnosis.diagnostic_gate]], [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]], [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]], [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/structured_ai.py](../../../../../../tests/structured_ai.py) — direct import
- [tests/test_codex_http_client.py](../../../../../../tests/test_codex_http_client.py) — direct import
  - `test_http_codex_client_misconception_match_bare_payload`
  - `test_http_codex_client_misconception_match_round_trip`
- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_http_adapter_strips_the_usage_envelope_but_not_a_bad_field`
- [tests/test_diagnostic_gate.py](../../../../../../tests/test_diagnostic_gate.py) — direct import
- [tests/test_openai_chat_client.py](../../../../../../tests/test_openai_chat_client.py) — direct import
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
  - `test_gate_rejected_llm_surfaces_fall_back_to_parametric`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
- [tests/test_provider_resolution_parity.py](../../../../../../tests/test_provider_resolution_parity.py) — direct import
  - `test_chat_complete_and_declared_media_capabilities_share_one_contract`
  - `test_diagnostic_fire_uses_the_structured_completion_path`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change feature context, prompt assembly, result models, and operation purposes here; keep provider mechanics in `learnloop.ai`.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/ai_contracts.py](../../../../../../src/learnloop/diagnosis/ai_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
