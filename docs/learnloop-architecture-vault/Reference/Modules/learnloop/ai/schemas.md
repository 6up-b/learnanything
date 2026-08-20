---
title: "learnloop.ai.schemas"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ai/schemas.py"
source_paths:
  - "src/learnloop/ai/schemas.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-08-18"
package: "learnloop.ai"
layer: "infrastructure"
concepts:
  - "AI Architecture"
  - "Architecture Overview"
workflows:
  - "Configure AI Providers"
  - "Process Model Output"
aliases:
  - "learnloop.ai.schemas module"
  - "src/learnloop/ai/schemas.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/infrastructure"
  - "package/learnloop-ai"
---

# `learnloop.ai.schemas`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps schemas behavior inside its owning package, [[Reference/Modules/learnloop/ai/_package|learnloop.ai]]. Its public surface centers on `WireModel`, `UndeclaredWireFieldError`, `undeclared_wire_fields`, `describe_wire_validation_error`, `FacetCapabilityTargetRef`, `CriterionTargetRef`, `ItemStepTargetRef`, `AnswerSpanTargetRef` and 2 more public symbols.

The authoritative system-level explanation remains in [[AI Architecture]], [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py) |
| Source lines | 209 |
| Owning package | [[Reference/Modules/learnloop/ai/_package|learnloop.ai]] |
| Architecture layer | `infrastructure` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class WireModel(BaseModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 38) — Base for every payload that crosses the provider boundary.
- `class UndeclaredWireFieldError(ValueError)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 61) — A payload carried a field the wire contract does not declare.
  - `__init__(self, model: type[BaseModel], fields: list[str]) -> None` (line 70; internal)
- `undeclared_wire_fields(exc: ValidationError) -> list[str]` ([source](../../../../../../src/learnloop/ai/schemas.py), line 81) — Dotted paths of every ``extra="forbid"`` rejection inside ``exc``.
- `describe_wire_validation_error(model: type[BaseModel], exc: BaseException) -> str` ([source](../../../../../../src/learnloop/ai/schemas.py), line 99) — One actionable line for a failed wire parse, naming model and fields.
- `class FacetCapabilityTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 108)
- `class CriterionTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 114)
- `class ItemStepTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 119)
- `class AnswerSpanTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 125)
  - `validate_offsets(self) -> 'AnswerSpanTargetRef'` (line 132; public)
- `class NoTargetRef(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 144)
- `class CandidateCause(WireModel)` ([source](../../../../../../src/learnloop/ai/schemas.py), line 156) — One free-text candidate explanation of an observed failure.
  - `validate_statement(self) -> 'CandidateCause'` (line 206; public)

### Module constants

- `EXTRA_FORBIDDEN_ERROR_TYPE` ([src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py), line 58)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]] — imports `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]] — imports `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `WireModel`
- [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] — imports `AttributionTargetRef`, `CandidateCause`, `WireModel`
- [[Reference/Modules/learnloop/content/authoring/ai_contracts|learnloop.content.authoring.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/content/proposals/ai_contracts|learnloop.content.proposals.ai_contracts]] — imports `WireModel`, `describe_wire_validation_error`; statically calls `describe_wire_validation_error`
- [[Reference/Modules/learnloop/content/synthesis/ai_contracts|learnloop.content.synthesis.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/curriculum/ai_contracts|learnloop.curriculum.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/ai_contracts|learnloop.diagnosis.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_augmentation|learnloop.diagnosis.diagnostic_augmentation]] — imports `CandidateCause`; statically calls `CandidateCause`
- [[Reference/Modules/learnloop/reader/ai_contracts|learnloop.reader.ai_contracts]] — imports `WireModel`
- [[Reference/Modules/learnloop/tutor/ai_contracts|learnloop.tutor.ai_contracts]] — imports `CandidateCause`, `WireModel`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Configure AI Providers]]
- [[Process Model Output]]

Static participation evidence comes from [[Reference/Modules/learnloop/ai/providers/codex|learnloop.ai.providers.codex]], [[Reference/Modules/learnloop/ai/providers/codex_http|learnloop.ai.providers.codex_http]], [[Reference/Modules/learnloop/ai/strict_schema|learnloop.ai.strict_schema]], [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]], [[Reference/Modules/learnloop/attempts/ai_contracts|learnloop.attempts.ai_contracts]] and 8 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_codex_output_schema.py](../../../../../../tests/test_codex_output_schema.py) — direct import
  - `test_runtime_validation_and_strict_schema_agree_on_what_is_admissible`
  - `test_undeclared_wire_field_is_rejected_by_name`
- [tests/test_structured_transport_parity.py](../../../../../../tests/test_structured_transport_parity.py) — direct import

## Modification guidance

- Change provider-neutral transport/routing policy here; do not move feature prompts or feature result models into the shared AI layer.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ai/schemas.py](../../../../../../src/learnloop/ai/schemas.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
