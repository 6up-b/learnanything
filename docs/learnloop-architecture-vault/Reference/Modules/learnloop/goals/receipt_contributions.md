---
title: "learnloop.goals.receipt_contributions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/receipt_contributions.py"
source_paths:
  - "src/learnloop/goals/receipt_contributions.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.goals"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Goals Exams and Certification Workflow"
aliases:
  - "learnloop.goals.receipt_contributions module"
  - "src/learnloop/goals/receipt_contributions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.receipt_contributions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.receipt_contributions` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Shared authoritative certification-credit capping for projections and receipts.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/receipt_contributions.py](../../../../../../src/learnloop/goals/receipt_contributions.py) |
| Source lines | 131 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class CellContribution` ([source](../../../../../../src/learnloop/goals/receipt_contributions.py), line 18) — One (facet, capability) cell's staged→banked credit within one attempt.
- `itemize_observation_contributions(staged_by_group: Mapping[str, Mapping[Cell, float]], *, attempt_type: str, evidence_mass: float, group_budget_overrides: Mapping[str, float] | None, max_groups_per_attempt: int) -> tuple[dict[Cell, float], list[CellContribution]]` ([source](../../../../../../src/learnloop/goals/receipt_contributions.py), line 35) — Cap the staged credit AND itemize each cell's raw/capped/binding rule.
- `cap_observation_contributions(staged_by_group: Mapping[str, Mapping[Cell, float]], *, attempt_type: str, evidence_mass: float, group_budget_overrides: Mapping[str, float] | None, max_groups_per_attempt: int) -> dict[Cell, float]` ([source](../../../../../../src/learnloop/goals/receipt_contributions.py), line 109) — Apply group budgets and the attempt ceiling, preserving cell shares.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `itemize_observation_contributions`; statically calls `itemize_observation_contributions`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `itemize_observation_contributions`; statically calls `itemize_observation_contributions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `cap_certification_by_group`, `group_budget`; calls `cap_certification_by_group`, `group_budget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]], [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_facet_evidence_timeline.py](../../../../../../tests/test_facet_evidence_timeline.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_observation_ledger_bulk.py](../../../../../../tests/test_observation_ledger_bulk.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_projection_evidence_polarity.py](../../../../../../tests/test_projection_evidence_polarity.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_receipt_derivation.py](../../../../../../tests/test_receipt_derivation.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — imports consumer [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]]
- [tests/test_anti_double_count.py](../../../../../../tests/test_anti_double_count.py) — imports consumer [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]]
- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — imports consumer [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]]
- [tests/test_causal_activity_policy.py](../../../../../../tests/test_causal_activity_policy.py) — imports consumer [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]]
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — imports consumer [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]]
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — imports consumer [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]]

## Modification guidance

- Change receipt contributions policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/receipt_contributions.py](../../../../../../src/learnloop/goals/receipt_contributions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
