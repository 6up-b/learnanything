---
title: "learnloop.goals.goal_certification"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/goal_certification.py"
source_paths:
  - "src/learnloop/goals/goal_certification.py"
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
  - "learnloop.goals.goal_certification module"
  - "src/learnloop/goals/goal_certification.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.goal_certification`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.goal_certification` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Goal certification semantics (knowledge-model §9.5).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/goal_certification.py](../../../../../../src/learnloop/goals/goal_certification.py) |
| Source lines | 313 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class FacetDemonstration` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 31) — Capability-matched demonstration state for one facet within an LO (§9.5).
  - `demonstrated(self) -> bool` (line 40; public) — Every required capability has capability-matched direct evidence.
- `required_capabilities_for_facet(vault: LoadedVault, learning_object: LearningObject, facet_id: str) -> tuple[tuple[str, ...], bool]` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 53) — Capabilities ``facet_id`` is required at within ``learning_object`` (§9.5).
- `demonstrated_capabilities_for_facet(vault: LoadedVault, repository: Repository, facet_id: str) -> set[str]` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 85) — Capabilities with capability-matched direct/embedded certification credit.
- `facet_demonstration(vault: LoadedVault, repository: Repository, learning_object: LearningObject, facet_id: str) -> FacetDemonstration` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 104) — The §9.5 demonstration state of one facet within an LO.
- `class LoCertification` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 127) — Composite-LO certification: component coverage + integration (§9.2/§9.5).
- `class RecipeGaps` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 137) — The unmet requirements of ONE recipe (§9.2 last bullet, §9.5).
  - `satisfied(self) -> bool` (line 168; public)
- `recipe_gaps(vault: LoadedVault, repository: Repository, learning_object: LearningObject) -> tuple[RecipeGaps, ...]` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 192) — Per-recipe gaps for every declared recipe, in declaration order.
- `lo_certification(vault: LoadedVault, repository: Repository, learning_object: LearningObject) -> LoCertification` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 275) — Whether a composite LO is demonstrated (§9.2 last bullet, §9.5).

## Internal implementation anchors

- `_demonstrated_resolver(vault: LoadedVault, repository: Repository)` ([source](../../../../../../src/learnloop/goals/goal_certification.py), line 176) — Memoized ``facet -> demonstrated capabilities`` over the ledger.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `demonstrated_capabilities_for_facet`, `lo_certification`; statically calls `demonstrated_capabilities_for_facet`, `lo_certification`
- [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]] — imports `lo_certification`; statically calls `lo_certification`
- [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]] — imports `lo_certification`, `recipe_gaps`; statically calls `lo_certification`, `recipe_gaps`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `facet_demonstration`; statically calls `facet_demonstration`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `required_capabilities_for_facet`; statically calls `required_capabilities_for_facet`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_capabilities_for_facet`; statically calls `required_capabilities_for_facet`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `lo_certification`; statically calls `lo_certification`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/goals/certification|learnloop.goals.certification]] — imports `is_demonstrated_credit`; calls `is_demonstrated_credit`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `default_capability_for`; calls `default_capability_for`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CONTRACT_MODALITIES`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `is_canonical_state_vault`; calls `is_canonical_state_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`, `recipe_components`; calls `recipe_components`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]], [[Reference/Modules/learnloop/diagnosis/scoreboard|learnloop.diagnosis.scoreboard]], [[Reference/Modules/learnloop/goals/certification_cold_probe|learnloop.goals.certification_cold_probe]], [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]], [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
  - `test_all_of_only_recipe_behaviour_is_unchanged`
  - `test_any_of_only_recipe_does_not_certify_without_evidence`
  - `test_mixed_recipe_needs_the_conjunct_and_one_alternative`
  - `test_one_demonstrated_alternative_satisfies_the_group`
  - `test_recipe_with_no_contract_component_never_certifies`
  - `test_single_hard_component_recipe_still_certifies`
- [tests/test_km3_projections.py](../../../../../../tests/test_km3_projections.py) — direct import
  - `test_hinted_component_not_demonstrated`
  - `test_planted_integration_gap_not_shown_demonstrated`
  - `test_retrieval_style_component_demonstrates_only_its_capability`

## Modification guidance

- Change goal certification policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/goal_certification.py](../../../../../../src/learnloop/goals/goal_certification.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
