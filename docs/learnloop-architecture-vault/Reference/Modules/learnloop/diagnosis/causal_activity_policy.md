---
title: "learnloop.diagnosis.causal_activity_policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/causal_activity_policy.py"
source_paths:
  - "src/learnloop/diagnosis/causal_activity_policy.py"
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
  - "learnloop.diagnosis.causal_activity_policy module"
  - "src/learnloop/diagnosis/causal_activity_policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.causal_activity_policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.causal_activity_policy` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Single authority for causal activity classification (spec §7, P2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py) |
| Source lines | 374 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `contamination_class_for_attempt(*, attempt_type: str, primed: bool=False, hints_used: int=0) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 121) — The contamination class implied by an attempt's own signals.
- `classify_attempt_activity(*, attempt_type: str, primed: bool=False, hints_used: int=0, near_clone: bool=False, explicit_class: str | None=None) -> CausalActivityPolicy` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 145) — Resolve the full policy for one concrete attempt.
- `attempt_counts_as_assisted(*, attempt_type: str, primed: bool=False, hints_used: int=0) -> bool` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 189) — The canonical-projection / facet-timeline assistance test.
- `resolve_attempt_activity_policy(*, attempt_type: str, primed: bool=False, hints_used: int=0, recorded: Mapping[str, Any] | None=None) -> CausalActivityPolicy` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 202) — Fail-closed attempt policy from immutable signals plus recorded facts.
- `resolve_conflicting_classes(existing: str, incoming: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 260) — Most-contaminated wins.
- `class NearCloneAssessment` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 282) — An auditable near-clone verdict.
  - `as_dict(self) -> dict[str, Any]` (line 299; public)
- `assess_near_clone(vault: 'LoadedVault', *, practice_item_id: str, source_practice_item_id: str | None, explicit: bool | None=None) -> NearCloneAssessment` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 309) — Compare the administered item's surface fingerprint against its source.
- `near_clone_from_selection_components(vault: 'LoadedVault', *, practice_item_id: str, selection_components: Mapping[str, Any] | None) -> NearCloneAssessment` ([source](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 359) — ``assess_near_clone`` over a probe presentation's selection components.

### Module constants

- `LEGACY_ASSISTED_ATTEMPT_TYPES` ([src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 93)
- `DIAGNOSTIC_ATTEMPT_TYPES` ([src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 101)
- `ASSISTED_ATTEMPT_TYPES` ([src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 106)
- `NEAR_CLONE_BASES` ([src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py), line 112)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `classify_attempt_activity`; statically calls `classify_attempt_activity`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `NEAR_CLONE_BASES`, `assess_near_clone`, `policy_for_class`; statically calls `assess_near_clone`, `policy_for_class`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `near_clone_from_selection_components`; statically calls `near_clone_from_selection_components`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `attempt_counts_as_assisted`; statically calls `attempt_counts_as_assisted`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `attempt_counts_as_assisted`; statically calls `attempt_counts_as_assisted`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `resolve_attempt_activity_policy`; statically calls `resolve_attempt_activity_policy`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `ASSISTED_ATTEMPT_TYPES`, `resolve_attempt_activity_policy`; statically calls `resolve_attempt_activity_policy`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `CAUSAL_ACTIVITY_POLICY_VERSION`, `CONTAMINATION_CLASSES`, `CONTAMINATION_PRECEDENCE`, `CausalActivityPolicy`, `policy_for_class`; calls `CausalActivityPolicy`, `policy_for_class`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_activity_policy.py](../../../../../../tests/test_causal_activity_policy.py) — direct import
  - `test_attempt_counts_as_assisted`
  - `test_attempt_signals_pick_the_class`
  - `test_concurrent_classification_waits_then_appends_next_sequence`
  - `test_explicit_class_overrides_the_signal_derivation`
  - `test_explicit_near_clone_declaration_wins`
  - `test_legacy_assisted_types_stay_assisted_without_losing_fsrs`
  - `test_matrix_covers_every_class_exactly`
  - `test_near_clone_fails_closed_but_audibly_when_unresolvable`
  - `test_near_clone_is_a_fingerprint_comparison_not_provenance`
  - `test_near_clone_only_moves_the_verification_certification_cell`
  - `test_near_clone_without_a_source_is_false`
  - `test_policy_matrix_cells_are_pinned`
  - `test_precedence_order_is_total_and_ranked`
  - `test_pure_diagnostic_is_stricter_than_spec_section_7`
  - `test_resolve_conflicting_classes_is_most_contaminated_wins`
  - `test_resolved_attempt_policy_separates_assistance_from_eligibility`
  - `test_service_exports_share_the_dependency_neutral_policy_authority`
  - `test_unknown_class_raises`
- [tests/test_causal_factor_deferral.py](../../../../../../tests/test_causal_factor_deferral.py) — direct import
  - `test_a_primed_attempt_is_not_eligible_for_fsrs`
- [tests/test_receipt_exactness.py](../../../../../../tests/test_receipt_exactness.py) — direct import
  - `test_timeline_final_credit_equals_banked_ledger_credit`

## Modification guidance

- Change causal activity policy policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/causal_activity_policy.py](../../../../../../src/learnloop/diagnosis/causal_activity_policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
