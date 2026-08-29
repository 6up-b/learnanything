---
title: "learnloop.learner.assessment_contracts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/assessment_contracts.py"
source_paths:
  - "src/learnloop/learner/assessment_contracts.py"
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
  - "learnloop.learner.assessment_contracts module"
  - "src/learnloop/learner/assessment_contracts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.assessment_contracts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.assessment_contracts` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Immutable assessment-contract snapshots (knowledge-model §5.2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/assessment_contracts.py](../../../../../../src/learnloop/learner/assessment_contracts.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `compile_assessment_contract(vault: LoadedVault, item: PracticeItem, *, rubric: Rubric | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 74) — Deterministic assessment-contract content for an item (§5.2).
- `rubric_from_contract(contract: dict[str, Any]) -> Rubric` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 154) — Rehydrate the immutable grading rubric used at presentation time.
- `contract_hash(contract: dict[str, Any]) -> str` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 185) — Content-addressed hash of a compiled contract (attribution-affecting only).
- `snapshot_for_presentation(repository, vault: LoadedVault, item: PracticeItem, *, rubric: Rubric | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 191) — Ensure an assessment-contract snapshot exists for a presented item (§5.2).

### Module constants

- `CONTRACT_SCHEMA_VERSION` ([src/learnloop/learner/assessment_contracts.py](../../../../../../src/learnloop/learner/assessment_contracts.py), line 42)

## Internal implementation anchors

- `_content_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 45)
- `_blueprint_recipes(lo: LearningObject | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/assessment_contracts.py), line 50)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `rubric_from_contract`, `snapshot_for_presentation`; statically calls `rubric_from_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `P0_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]] — imports `compile_assessment_contract`, `snapshot_for_presentation`; statically calls `compile_assessment_contract`, `snapshot_for_presentation`
- [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `P0_PROJECTION_VERSIONS`, `rubric_from_contract`; statically calls `rubric_from_contract`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner/residual_diagnostics|learnloop.learner.residual_diagnostics]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/ops/doctor|learnloop.ops.doctor]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `compile_assessment_contract`; statically calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/substrate/administration_adapters|learnloop.substrate.administration_adapters]] — imports `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/substrate/canonical_projection_rollout|learnloop.substrate.canonical_projection_rollout]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/substrate/compat/activity_backfill|learnloop.substrate.compat.activity_backfill]] — imports `compile_assessment_contract`; statically calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_SUCCESSOR_VERSIONS`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `KM_ALGORITHM_VERSION`, `snapshot_for_presentation`; statically calls `snapshot_for_presentation`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `CANONICAL_STATE_VERSIONS`, `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`, `P0_SUCCESSOR_VERSIONS`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `compile_criterion_targets`; calls `compile_criterion_targets`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`, `PracticeItem`, `Rubric`, `RubricCriterion`, `RubricFatalError`, `recipe_components`; calls `Rubric`, `RubricCriterion`, `RubricFatalError`, `recipe_components`

### Platform and third-party dependencies

- Standard library: `__future__`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]], [[Reference/Modules/learnloop/attempts/measurement_corrections|learnloop.attempts.measurement_corrections]], [[Reference/Modules/learnloop/content/proposals/patches|learnloop.content.proposals.patches]], [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_architecture.py](../../../../../../tests/test_architecture.py) — direct import
  - `test_assessment_service_reexports_neutral_algorithm_versions`
- [tests/test_assessment_contracts.py](../../../../../../tests/test_assessment_contracts.py) — direct import
  - `test_contract_hash_changes_when_targets_change`
  - `test_identical_item_versions_reuse_one_snapshot`
  - `test_snapshot_authoritative_after_live_rubric_change`
- [tests/test_characterization_assessment_exam.py](../../../../../../tests/test_characterization_assessment_exam.py) — direct import
  - `test_contract_hash_is_single_monolithic_content_hash`
  - `test_single_hash_moves_when_any_covered_component_changes`

## Modification guidance

- Change assessment contracts policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/assessment_contracts.py](../../../../../../src/learnloop/learner/assessment_contracts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
