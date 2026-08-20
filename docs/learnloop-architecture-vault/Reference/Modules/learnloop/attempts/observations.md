---
title: "learnloop.attempts.observations"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/observations.py"
source_paths:
  - "src/learnloop/attempts/observations.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.observations module"
  - "src/learnloop/attempts/observations.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.observations`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps observations behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `ObservationTemplatesNotReady`, `ObservationTemplateError`, `ObservationResult`, `parse_template_yaml`, `validate_template`, `register_observation_template`, `record_observation`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/observations.py](../../../../../../src/learnloop/attempts/observations.py) |
| Source lines | 177 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ObservationTemplatesNotReady(RuntimeError)` ([source](../../../../../../src/learnloop/attempts/observations.py), line 16)
- `class ObservationTemplateError(ValueError)` ([source](../../../../../../src/learnloop/attempts/observations.py), line 20)
- `class ObservationResult` ([source](../../../../../../src/learnloop/attempts/observations.py), line 25)
- `parse_template_yaml(template_yaml: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/attempts/observations.py), line 32)
- `validate_template(template: dict[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/attempts/observations.py), line 39)
- `register_observation_template(repository: Repository, *, domain: str, version: str, title: str, template_yaml: str, active: bool=True, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/attempts/observations.py), line 57)
- `record_observation(vault: LoadedVault, repository: Repository, *, template_id: str, response: dict[str, Any], related_learning_object_id: str | None=None, related_practice_item_id: str | None=None, session_id: str | None=None, subject: str | None=None, clock: Clock | None=None) -> ObservationResult` ([source](../../../../../../src/learnloop/attempts/observations.py), line 85)

## Internal implementation anchors

- `_emit_attempt(vault: LoadedVault, repository: Repository, *, emits: dict[str, Any], practice_item_id: str, response: dict[str, Any], clock: Clock | None) -> AttemptResult` ([source](../../../../../../src/learnloop/attempts/observations.py), line 149)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `ObservationTemplateError`, `parse_template_yaml`, `record_observation`, `register_observation_template`; statically calls `parse_template_yaml`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptDraft`, `AttemptResult`, `SelfGradeInput`, `complete_self_graded_attempt`; calls `AttemptDraft`, `SelfGradeInput`, `complete_self_graded_attempt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: `ruamel`

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_observation_templates.py](../../../../../../tests/test_observation_templates.py) — direct import
  - `test_ambiguous_emitting_binding_lands_pending`
  - `test_emitting_template_creates_attempt_through_attempt_service`
  - `test_invalid_template_is_rejected`
  - `test_register_rejects_invalid_template`
  - `test_valid_template_registers_and_loads`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`

## Modification guidance

- Change observations policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/observations.py](../../../../../../src/learnloop/attempts/observations.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
