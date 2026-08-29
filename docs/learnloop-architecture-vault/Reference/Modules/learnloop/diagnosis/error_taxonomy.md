---
title: "learnloop.diagnosis.error_taxonomy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/error_taxonomy.py"
source_paths:
  - "src/learnloop/diagnosis/error_taxonomy.py"
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
  - "learnloop.diagnosis.error_taxonomy module"
  - "src/learnloop/diagnosis/error_taxonomy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.error_taxonomy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps error taxonomy behavior inside its owning package, [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]]. Its public surface centers on `persist_unknown_error_type_proposals`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/error_taxonomy.py](../../../../../../src/learnloop/diagnosis/error_taxonomy.py) |
| Source lines | 99 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `persist_unknown_error_type_proposals(vault: LoadedVault, repository: Repository, *, attributions: Iterable[ValidatedErrorAttribution], attempt_id: str, agent_run_id: str | None, related_concept_id: str | None=None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/error_taxonomy.py), line 22)

### Module constants

- `BUILTIN_ERROR_TYPES` ([src/learnloop/diagnosis/error_taxonomy.py](../../../../../../src/learnloop/diagnosis/error_taxonomy.py), line 12)

## Internal implementation anchors

- `_error_type_payload(attribution: ValidatedErrorAttribution, related_concept_id: str | None) -> dict[str, object]` ([source](../../../../../../src/learnloop/diagnosis/error_taxonomy.py), line 82)
- `_title_from_id(error_type: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/error_taxonomy.py), line 97)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `persist_unknown_error_type_proposals`; statically calls `persist_unknown_error_type_proposals`
- [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]] — imports `persist_unknown_error_type_proposals`; statically calls `persist_unknown_error_type_proposals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `ValidatedErrorAttribution`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/regrade|learnloop.attempts.regrade]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_agent_run_tokens.py](../../../../../../tests/test_agent_run_tokens.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_answer_calibration_duel.py](../../../../../../tests/test_answer_calibration_duel.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_attempt_ai_flow.py](../../../../../../tests/test_attempt_ai_flow.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_attempt_write_order.py](../../../../../../tests/test_attempt_write_order.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_calibration.py](../../../../../../tests/test_calibration.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_causal_attribution_exhibit.py](../../../../../../tests/test_causal_attribution_exhibit.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_causal_attribution_p0.py](../../../../../../tests/test_causal_attribution_p0.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]
- [tests/test_causal_attribution_p1.py](../../../../../../tests/test_causal_attribution_p1.py) — imports consumer [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]]

## Modification guidance

- Change error taxonomy policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/error_taxonomy.py](../../../../../../src/learnloop/diagnosis/error_taxonomy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
