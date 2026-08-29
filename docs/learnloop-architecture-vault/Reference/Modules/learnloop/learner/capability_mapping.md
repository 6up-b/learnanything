---
title: "learnloop.learner.capability_mapping"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/capability_mapping.py"
source_paths:
  - "src/learnloop/learner/capability_mapping.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.capability_mapping module"
  - "src/learnloop/learner/capability_mapping.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.capability_mapping`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.capability_mapping` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Mode->capability defaults, criterion-target compilation, and the launch observation-mass allocation rule (knowledge-model §5.1/§5.4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py) |
| Source lines | 357 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `is_valid_capability(capability: str) -> bool` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 54)
- `default_capability_for(practice_mode: str, *, tier: str='core') -> str` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 58) — The default observed capability for a practice mode / rubric tier (§5.1).
- `compile_criterion_targets(item: PracticeItem, criterion, *, resolved_rubric: Rubric | None=None) -> list[CriterionTarget]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 85) — Targets a criterion observes, authored-or-compiled (§5.1).
- `class TargetAllocation` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 129)
- `allocate_success_mass(targets: list[CriterionTarget], criterion_pseudo_mass: float) -> list[TargetAllocation]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 136) — Split a criterion's success pseudo-mass across its targets by role (§5.4).
- `criterion_pseudo_mass(criterion_points: float, rubric_total: float, evidence_mass: float) -> float` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 163) — A criterion's total pseudo-mass = evidence_mass * (points / rubric total).
- `class CriterionOutcome` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 180) — One graded criterion within an attempt (projection input).
- `class LocalizedCriterion` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 189)
- `localize_criterion_outcomes(outcomes: list[CriterionOutcome]) -> list[LocalizedCriterion]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 196) — First-error localization over a criterion dependency DAG (§5.3).
- `certification_credit(pseudo_mass: float, *, relationship: str, assistance: str) -> float` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 246) — Credit for one observation = its pseudo-mass iff direct/embedded and unassisted; zero otherwise (§5.4 quantity 2).
- `group_budget(attempt_type: str, correlation_group: str | None, *, evidence_mass: float, overrides: Mapping[str, float] | None=None) -> float` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 268) — Per-(attempt_type, correlation-group) certification budget (§5.4 q.3).
- `cap_certification_by_group(credits_by_group: Mapping[str, float], *, attempt_type: str, evidence_mass: float, overrides: Mapping[str, float] | None=None, max_groups_per_attempt: int) -> dict[str, float]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 291) — Apply the per-group cap and the attempt-wide ceiling (§5.4 q.3/q.4).
- `group_proliferation_flag(group_variation_counts: Mapping[str, int], *, min_independent_variations: int=2) -> list[str]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 321) — Correlation groups whose observations never vary independently (§5.4).
- `unregistered_facet_errors(known_facets: Mapping[str, object] | set[str], facet_ids) -> list[str]` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 341) — Facet ids in ``facet_ids`` that are not registered (item gate, §3.2).

### Module constants

- `MODE_CAPABILITY_DEFAULTS` ([src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py), line 22)
- `DEFAULT_CAPABILITY` ([src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py), line 48)
- `ROLE_WEIGHTS` ([src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py), line 51)
- `UNASSISTED` ([src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py), line 175)
- `ASSISTED_CHANNELS` ([src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py), line 176)

## Internal implementation anchors

- `_observed_capability(item: PracticeItem, tier: str) -> str` ([source](../../../../../../src/learnloop/learner/capability_mapping.py), line 70) — Capability a criterion of ``tier`` observes on ``item``.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]] — imports `CriterionOutcome`, `compile_criterion_targets`, `localize_criterion_outcomes`; statically calls `CriterionOutcome`, `compile_criterion_targets`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `CriterionOutcome`, `localize_criterion_outcomes`; statically calls `CriterionOutcome`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]] — imports `compile_criterion_targets`; statically calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; statically calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `default_capability_for`; statically calls `default_capability_for`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `default_capability_for`; statically calls `default_capability_for`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `unregistered_facet_errors`; statically calls `unregistered_facet_errors`
- [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|learnloop.content.synthesis.source_set_synthesis]] — imports `CAPABILITY_VOCABULARY`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `CriterionOutcome`, `localize_criterion_outcomes`; statically calls `CriterionOutcome`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; statically calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `default_capability_for`; statically calls `default_capability_for`
- [[Reference/Modules/learnloop/goals/receipt_contributions|learnloop.goals.receipt_contributions]] — imports `cap_certification_by_group`, `group_budget`; statically calls `cap_certification_by_group`, `group_budget`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_criterion_targets`; statically calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`; statically calls `compile_criterion_targets`, `default_capability_for`, `is_valid_capability`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; statically calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `compile_criterion_targets`; statically calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `is_valid_capability`; statically calls `is_valid_capability`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`; statically calls `CriterionOutcome`, `allocate_success_mass`, `certification_credit`, `compile_criterion_targets`, `criterion_pseudo_mass`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `CAPABILITY_VOCABULARY`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `CAPABILITY_VOCABULARY`, `CriterionTarget`, `PracticeItem`, `Rubric`; calls `CriterionTarget`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempt_trace|learnloop.attempts.attempt_trace]], [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]], [[Reference/Modules/learnloop/content/authoring/conjunctive_items|learnloop.content.authoring.conjunctive_items]], [[Reference/Modules/learnloop/content/authoring/contract_commissioning|learnloop.content.authoring.contract_commissioning]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_capability_mapping.py](../../../../../../tests/test_capability_mapping.py) — direct import
  - `test_authored_targets_override_defaults`
  - `test_capability_vocabulary_validation`
  - `test_default_capability_mapping_table`
  - `test_inference_mass_sums_to_evidence_mass_across_rubric`
  - `test_legacy_criterion_compiles_to_mode_default_capability`
  - `test_supporting_role_gets_less_mass_than_primary`
  - `test_unregistered_facet_errors_flags_unknown_only`
- [tests/test_conjunctive_instruments.py](../../../../../../tests/test_conjunctive_instruments.py) — direct import
  - `test_authored_targets_compile_verbatim_including_supporting`
  - `test_criterion_without_targets_still_compiles_to_all_primary_at_the_item_capability`
- [tests/test_km2_canonical.py](../../../../../../tests/test_km2_canonical.py) — direct import
  - `test_certification_bounded_per_correlation_group`
  - `test_dependency_branch_failure_preserves_independent_work`
  - `test_group_budget_override`
  - `test_group_proliferation_flag`
  - `test_retrieval_evidence_cannot_certify_method_selection`
  - `test_rich_response_earns_several_group_budgets_capped_by_ceiling`
  - `test_whole_item_failure_localizes_to_first_error_only`

## Modification guidance

- Change capability mapping policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/capability_mapping.py](../../../../../../src/learnloop/learner/capability_mapping.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
