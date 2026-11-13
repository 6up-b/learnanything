---
title: "learnloop.substrate.administration_adapters"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/administration_adapters.py"
source_paths:
  - "src/learnloop/substrate/administration_adapters.py"
generated: true
generated_at: "2026-11-02"
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
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.administration_adapters` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P1 step 5 -- purpose-specific administration adapters (spec_p1_shared_substrate §3.10, standing rule 4, invariants 8/9).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py) |
| Source lines | 306 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class PurposeMismatch(Exception)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 37) — An administration was routed to the wrong adapter (§7.5 purpose mismatch).
- `class OpportunisticDiagnosisRejected(Exception)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 41) — Invariant 8: only an administration committed to a diagnostic episode and its frozen hypothesis set may update that episode.
- `class AdministrationEffects` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 48) — The three intentionally-different projections + lifecycle for one purpose (§1, §3.10).
  - `as_dict(self) -> dict[str, Any]` (line 61; public)
- `class Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 74)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 77; public)
  - `apply_scheduling(self, repository: Repository, *, card_lineage_id: str, scheduler_algorithm_version: str, review_event: Mapping[str, Any] | None, eligible: bool, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, clock: Clock | None=None) -> dict[str, Any] | None` (line 80; public) — Default: no scheduling projection.
- `class DiagnosticAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 98)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 101; public)
  - `update_episode(self, *, committed_episode_id: str | None) -> str` (line 113; public) — Invariant 8 / §9.4: an episode update requires a committed diagnostic presentation.
- `class InstructionalAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 124)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 127; public)
- `class PracticeAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 142)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 145; public)
  - `apply_scheduling(self, repository: Repository, *, card_lineage_id: str, scheduler_algorithm_version: str, review_event: Mapping[str, Any] | None, eligible: bool, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, clock: Clock | None=None) -> dict[str, Any] | None` (line 157; public) — Card-level review, ONLY when the observation is eligible (§3.8, §3.10).
- `class AssessmentAdapter(Adapter)` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 187)
  - `effects(self, *, eligible: bool, failed: bool) -> AdministrationEffects` (line 190; public)
- `resolve_adapter(purpose: str) -> Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 211) — Select the adapter by immutable family purpose (never attempt_type/route).
- `resolve_adapter_for_administration(repository: Repository, administration_id: str) -> Adapter` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 220)
- `class ProjectionResult` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 230)
  - `as_dict(self) -> dict[str, Any]` (line 236; public)
- `project_administration(repository: Repository, *, administration_id: str, eligible: bool, failed: bool, card_lineage_id: str | None=None, scheduler_algorithm_version: str | None=None, review_event: Mapping[str, Any] | None=None, prior_reviews: Sequence[Mapping[str, Any]]=(), model_label: str='fsrs', clock: Clock | None=None) -> ProjectionResult` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 245) — Resolve the purpose adapter and project scheduling in one fail-safe unit.
- `hot_path_applies_practice_review(*, attempt_type: str, eligible: bool=True) -> bool` ([source](../../../../../../src/learnloop/substrate/administration_adapters.py), line 299) — Whether the attempt hot path applies its FSRS practice review: the practice adapter's eligibility semantics.

### Module constants

- `PURPOSES` ([src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py), line 35)
- `_ADAPTERS` ([src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py), line 203)

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `hot_path_applies_practice_review`; statically calls `hot_path_applies_practice_review`
- [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]] — imports `module`; statically calls `resolve_adapter`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`
- [[Reference/Modules/learnloop/substrate/card_lineage|learnloop.substrate.card_lineage]] — imports `module`; calls `rebuild_card_state`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/reader/reader_dialogue|learnloop.reader.reader_dialogue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_administration_adapters.py](../../../../../../tests/test_administration_adapters.py) — direct import
  - `test_diagnostic_episode_requires_committed_presentation`
  - `test_hot_path_defers_to_practice_eligibility`
  - `test_ineligible_practice_observation_leaves_card_state_untouched`
  - `test_only_practice_eligible_updates_card_state`
  - `test_practice_effects_never_touch_a_probe_episode`
  - `test_practice_failure_opens_lapse_flag_but_instruction_never_does`
  - `test_project_administration_is_fail_safe_on_missing_administration`
  - `test_purpose_matrix_effects`
  - `test_purpose_mismatch_rejected`
- [tests/test_reader_dialogue.py](../../../../../../tests/test_reader_dialogue.py) — direct import
  - `test_instructional_administration_never_certifies`

## Modification guidance

- Change administration adapters policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/administration_adapters.py](../../../../../../src/learnloop/substrate/administration_adapters.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
