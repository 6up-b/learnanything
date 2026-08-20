---
title: "learnloop.substrate.administration_adapters"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/administration_adapters.py"
source_paths:
  - "src/learnloop/substrate/administration_adapters.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.administration_adapters module"
  - "src/learnloop/substrate/administration_adapters.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.administration_adapters`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.administration_adapters` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P1 step 5 -- purpose-specific administration adapters (spec_p1_shared_substrate §3.10, standing rule 4, invariants 8/9).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py) |
| Source lines | 350 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class PurposeMismatch(Exception)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 50) — An administration was routed to the wrong adapter (§7.5 purpose mismatch).
- `class OpportunisticDiagnosisRejected(Exception)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 54) — Invariant 8: only an administration committed to a diagnostic episode and its frozen hypothesis set may update that episode.
- `class AdministrationEffects` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 61) — The three intentionally-different projections + lifecycle for one purpose (§1, §3.10).
  - `as_dict(self) -> dict[str, Any]` (line 74; public)
- `class Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 87)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 90; public)
  - `apply_scheduling(self, repository: Repository, *, card_lineage_id: str, scheduler_algorithm_version: str, review_event: Mapping[str, Any] | None, eligible: bool, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, clock: Clock | None=None) -> dict[str, Any] | None` (line 93; public) — Default: no scheduling projection.
- `class DiagnosticAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 111)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 114; public)
  - `update_episode(self, *, committed_episode_id: str | None) -> str` (line 126; public) — Invariant 8 / §9.4: an episode update requires a committed diagnostic presentation.
- `class InstructionalAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 137)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 140; public)
- `class PracticeAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 155)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 158; public)
  - `apply_scheduling(self, repository: Repository, *, card_lineage_id: str, scheduler_algorithm_version: str, review_event: Mapping[str, Any] | None, eligible: bool, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, clock: Clock | None=None) -> dict[str, Any] | None` (line 170; public) — Card-level review, ONLY when the observation is eligible (§3.8, §3.10).
- `class AssessmentAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 200)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 203; public)
- `resolve_adapter(purpose: str) -> Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 224) — Select the adapter by immutable family purpose (never attempt_type/route).
- `resolve_adapter_for_administration(repository: Repository, administration_id: str) -> Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 233)
- `class ProjectionResult` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 243)
  - `as_dict(self) -> dict[str, Any]` (line 249; public)
- `project_administration(repository: Repository, *, administration_id: str, eligible: bool, failed: bool, card_lineage_id: str | None=None, scheduler_algorithm_version: str | None=None, review_event: Mapping[str, Any] | None=None, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', clock: Clock | None=None) -> ProjectionResult` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 258) — Resolve the purpose adapter and project scheduling in one fail-safe unit.
- `purpose_adapter_path_live(algorithm_version: str | None) -> bool` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 312) — Whether the purpose-adapter path is the LIVE scheduling authority for a vault.
- `hot_path_applies_practice_review(*, attempt_type: str, eligible: bool=True, algorithm_version: str | None=None) -> bool` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 334) — Whether the attempt hot path applies its FSRS practice review.

### Module constants

- `PURPOSES` ([src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py), line 42)
- `P1_PURPOSE_ADAPTERS_ENABLED` ([src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py), line 47)
- `_ADAPTERS` ([src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py), line 216)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `hot_path_applies_practice_review`; statically calls `hot_path_applies_practice_review`
- [[Reference/Modules/learnloop/curriculum/pattern_ladder|learnloop.curriculum.pattern_ladder]] — imports `module`; statically calls `resolve_adapter`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `resolve_adapter`
- [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]] — imports `OpportunisticDiagnosisRejected`, `module`; statically calls `PracticeAdapter`, `project_administration`, `resolve_adapter`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `Rating`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `module`; calls `rebuild_card_state`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/curriculum/pattern_ladder|learnloop.curriculum.pattern_ladder]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]], [[Reference/Modules/learnloop/substrate/compat/substrate_cutover|learnloop.substrate.compat.substrate_cutover]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
  - `test_diagnostic_episode_requires_committed_presentation`
  - `test_hot_path_gate_default_off_is_unconditional`
  - `test_hot_path_gate_on_defers_to_practice_eligibility`
  - `test_ineligible_practice_observation_leaves_card_state_untouched`
  - `test_only_practice_eligible_updates_card_state`
  - `test_practice_effects_never_touch_a_probe_episode`
  - `test_practice_failure_opens_lapse_flag_but_instruction_never_does`
  - `test_project_administration_is_fail_safe_on_missing_administration`
  - `test_purpose_matrix_effects`
  - `test_purpose_mismatch_rejected`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_instructional_administration_never_certifies`
- [tests/test_substrate_cutover.py](../../../../../../tests/test_substrate_cutover.py) — direct import
  - `test_deferred_projection_rebuild_is_deterministic_and_idempotent`
  - `test_hot_path_review_is_byte_identical_for_eligible_practice_on_both_paths`
  - `test_module_override_forces_live_regardless_of_version`
  - `test_projection_failure_defers_without_half_update`

## Modification guidance

- Change administration adapters policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
