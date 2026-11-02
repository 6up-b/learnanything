---
title: "learnloop.substrate.intervention_outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/intervention_outcomes.py"
source_paths:
  - "src/learnloop/substrate/intervention_outcomes.py"
source_commit: "e575da4c2ecce36ebc48e97417a86ec23167c062"
source_commit_timestamp: "2026-10-21T14:39:41-04:00"
source_worktree_state: "clean"
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
  - "learnloop.substrate.intervention_outcomes module"
  - "src/learnloop/substrate/intervention_outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.intervention_outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.intervention_outcomes` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: The outcome join for retrieval interventions (spec_source_practice_and_probes_v1 §11.2; S5).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py) |
| Source lines | 430 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e575da4c2ecce36ebc48e97417a86ec23167c062` |
| Commit timestamp | `2026-10-21T14:39:41-04:00` |

## Public API

- `is_assisted(attempt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 103) — Not an unaided attempt: another attempt type, a hint used, or primed.
- `exposure_evidence(connection: Any, *, cutoff: datetime | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 118) — The persisted exposure and coldness records the cold search reads; with ``cutoff`` (the historical read, :func:`outcomes_as_of`) only those written by then.
- `outcome_for(intervention: Mapping[str, Any], attempts: Sequence[Mapping[str, Any]], vault: LoadedVault, *, as_of: datetime, signals: list[dict[str, Any]], evidence: Mapping[str, Any] | None=None, interventions_seen: Sequence[Mapping[str, Any]]=()) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 234)
- `outcomes_as_of(vault: LoadedVault, connection: Any, as_of: datetime, *, grades: Mapping[str, tuple[Any, bool]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 374) — Every intervention's outcome AS IT STOOD at ``as_of`` (S5's own historical read; Reader RW2c fix round 2, 5), keyed by intervention id.
- `rebuild_intervention_outcomes(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 412) — The single DERIVED replayer: pure recomputation inside the caller's transaction.

### Module constants

- `OUTCOME_VERSION` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 54)
- `COLD_DELAY` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 56)
- `CENSOR_HORIZON` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 58)
- `SUCCESS_CORRECTNESS` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 61)
- `COLD_STATES` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 62)
- `MEASURED_COLD_STATES` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 66)
- `COLDNESS_DIMENSIONS` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 68)
- `USAGE_TASK` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 69)
- `UNAIDED_TYPES` ([src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 100)

### Explicit exports

`__all__` declares:

- `COLD_STATES`
- `MEASURED_COLD_STATES`
- `OUTCOME_VERSION`
- `SUCCESS_CORRECTNESS`
- `exposure_evidence`
- `is_assisted`
- `outcome_for`
- `outcomes_as_of`
- `rebuild_intervention_outcomes`

## Internal implementation anchors

- `_parse(value: str) -> datetime` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 72)
- `_attempts(connection: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 77)
- `_table(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 113)
- `_contamination(attempt: Mapping[str, Any], intervention: Mapping[str, Any], interventions_on_targets: Sequence[Mapping[str, Any]], evidence: Mapping[str, Any], vault: LoadedVault) -> list[str]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 150) — Why ``attempt`` is not independent of exposure (empty: it is), from persisted rows only: anything in the cold delay before it.
- `_targets(intervention: Mapping[str, Any], vault: LoadedVault) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 187)
- `_bucket(attempt: Mapping[str, Any], predicted: Mapping[str, float] | None) -> str | None` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 198)
- `_signals(connection: Any, proposal_id: str | None, *, cutoff: datetime | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 215)
- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 324)
- `_observation(row: dict[str, Any], valuation: Mapping[str, Any], likelihood: Mapping[str, Mapping[str, float]] | None) -> None` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 328) — What the observed bucket implies, from persisted rows only (§11.4 items 2 and 3; Codex re-review F11): the posterior on the target hypotheses by Bayes' rule over the check's own member-0 likelihood (the model's implied movement, labelled so; calibration compares it with the pred…
- `_dont_know(attempt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 365)
- `_overlaps(other: Mapping[str, Any], items: set[str], facets: set[str], vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/substrate/intervention_outcomes.py), line 369)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]] — imports `COLD_STATES`, `MEASURED_COLD_STATES`, `SUCCESS_CORRECTNESS`, `rebuild_intervention_outcomes`; statically calls `rebuild_intervention_outcomes`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; statically calls `is_assisted`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; statically calls `is_assisted`
- [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]] — imports `SUCCESS_CORRECTNESS`, `is_assisted`; statically calls `is_assisted`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `rebuild_intervention_outcomes`; statically calls `rebuild_intervention_outcomes`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `outcomes_as_of`; statically calls `outcomes_as_of`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `interventions`, `replace_outcomes`; calls `interventions`, `replace_outcomes`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`, `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/instructional/interventions|learnloop.instructional.interventions]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]], [[Reference/Modules/learnloop/reader/reader_report|learnloop.reader.reader_report]], [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intervention_outcomes_replayer.py](../../../../../../tests/test_intervention_outcomes_replayer.py) — direct import
  - `test_a_valued_check_logs_its_bucket_beside_the_prediction`
  - `test_an_assisted_attempt_no_longer_masks_a_later_independent_one`
  - `test_an_attempt_right_after_another_exposure_is_not_cold`
  - `test_outcome_states`
  - `test_the_replayer_is_registered_deterministic_and_calls_nothing`
  - `test_the_replayer_reads_persisted_exposure`
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_5_the_s5_historical_read_leaves_current_behaviour_alone`
- [tests/test_sources_merge_composition.py](../../../../../../tests/test_sources_merge_composition.py) — direct import
  - `test_a_held_grade_is_no_intervention_outcome`
- [tests/test_valuation_calibration_fields.py](../../../../../../tests/test_valuation_calibration_fields.py) — direct import
  - `test_a_valued_pick_followed_by_an_attempt_records_hypothesis_movement`
  - `test_decision_fields_reach_the_record_and_the_outcome_derives_the_action_change`

## Modification guidance

- Change intervention outcomes policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/intervention_outcomes.py](../../../../../../src/learnloop/substrate/intervention_outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
