---
title: "learnloop.attempts.ability_transition"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/ability_transition.py"
source_paths:
  - "src/learnloop/attempts/ability_transition.py"
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
  - "learnloop.attempts.ability_transition module"
  - "src/learnloop/attempts/ability_transition.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.ability_transition`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps ability transition behavior inside its owning package, [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]]. Its public surface centers on `estimate_ability_transition`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/ability_transition.py](../../../../../../src/learnloop/attempts/ability_transition.py) |
| Source lines | 39 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `estimate_ability_transition(item: PracticeItem, *, correctness: float, attempt_type: str, target_facets: list[str], error_event_written: bool) -> dict[str, object]` ([source](../../../../../../src/learnloop/attempts/ability_transition.py), line 7) — Audit the modeled learning gain from doing/reviewing an item.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `estimate_ability_transition`; statically calls `estimate_ability_transition`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `estimate_ability_transition`; statically calls `estimate_ability_transition`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]].

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

- Change ability transition policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/ability_transition.py](../../../../../../src/learnloop/attempts/ability_transition.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
