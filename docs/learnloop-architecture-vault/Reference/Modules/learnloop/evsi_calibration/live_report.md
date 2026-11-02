---
title: "learnloop.evsi_calibration.live_report"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/evsi_calibration/live_report.py"
source_paths:
  - "src/learnloop/evsi_calibration/live_report.py"
source_commit: "13e1676316b8f447ed8dad3f17ffaccda556f867"
source_commit_timestamp: "2026-10-13T20:56:51-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.evsi_calibration"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.evsi_calibration.live_report module"
  - "src/learnloop/evsi_calibration/live_report.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-evsi-calibration"
---

# `learnloop.evsi_calibration.live_report`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.evsi_calibration.live_report` exists within [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] to own the behavior summarized by its module contract: `learnloop evsi calibration`: how good were the live VOI forecasts?

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py) |
| Source lines | 1124 |
| Owning package | [[Reference/Modules/learnloop/evsi_calibration/_package|learnloop.evsi_calibration]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `13e1676316b8f447ed8dad3f17ffaccda556f867` |
| Commit timestamp | `2026-10-13T20:56:51-04:00` |

## Public API

- `class RouterOutcomeAdapter` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 131) — R1: the attempt that took a logged router decision (when R1 is present).
  - `__init__(self, connection: sqlite3.Connection) -> None` (line 136; internal)
  - `attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None` (line 140; public) — The attempt R1 bound to the forecast's offer, or ``None`` to defer.
- `class LedgerOutcomeAdapter` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 176) — The probe and attempt ledgers (always available).
  - `__init__(self, connection: sqlite3.Connection) -> None` (line 181; internal)
  - `attempt_for(self, forecast: Mapping[str, Any]) -> tuple[str | None, str] | None` (line 184; public)
  - `_requeued_after(self, item: str, gate: str, queued_at: str) -> bool` (line 215; internal) — A newer decision queued the same item (``pending_followup_practice_items`` keeps the newest queue per item, so the older decision is superseded).
  - `_value_decision_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]` (line 228; internal) — The attempt a value-of-information decision's check was answered by, through that site's own receipts only (module docstring).
  - `_candidate_attempt(self, candidate_id: Any, item: Any) -> tuple[str | None, str]` (line 249; internal) — The attempt bound to one scheduler candidate (the offer it answered).
  - `_followup_value_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]` (line 261; internal) — A queued follow-up value decision: its own receipt (``followup_value_decisions``, ``decision_ref``) must be the decision in force on its source attempt (any later decision there, a queue again or a suppression, rewrote the attempt's queue and supersedes it), then the queue and t…
  - `_plan_probe_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]` (line 291; internal) — An admitted project probe: router R1's ``plan_block`` row (``decision_ref``, or the block itself when R1 logged nothing) -> the block that decision persisted -> the probe planned in it -> its serving's scheduler candidate -> the attempt bound to it.
  - `_presentation_attempt(self, block_ids: Sequence[str], item: str) -> tuple[str | None, str] | None` (line 337; internal) — The attempt bound to the item's presentation in one of ``block_ids`` (router R2a's receipt): ``(attempt, "taken")``, ``(None, "presented_unanswered")``, or None when the item was never presented there (or the database predates the receipt).
  - `_staged_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]` (line 363; internal) — The attempt that administered a staged diagnostic decision (review F3).
  - `_queue_serving_at(self, item: str, at: str) -> tuple[str, str] | None` (line 410; internal) — The queued decision the scheduler would serve for ``item`` at ``at``.
  - `_answered_delayed_task(self, attempt_id: str) -> bool` (line 434; internal) — The attempt consumed a delayed follow-up task (cold retry, certification probe): those lanes ride the same ``intervention_followup`` component and shadow a queued follow-up of the same item, so its offer was theirs.
  - `_followup_attempt(self, forecast: Mapping[str, Any]) -> tuple[str | None, str]` (line 445; internal) — The attempt that took a queued follow-up decision (review F6, re-review F6).
- `realized_emission(connection: sqlite3.Connection, vault: LoadedVault, forecast: Mapping[str, Any], attempt_id: str) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 678) — The realized emission in the forecast's alphabet, or (None, why not).
- `truth_for(connection: sqlite3.Connection, forecast: Mapping[str, Any], *, realized_attempt_id: str | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 826) — Independent later diagnostic truth about the forecast's hypotheses, or None.
- `calibration_report(vault: LoadedVault, *, since: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 970)
- `summarize_joined(rows: Sequence[tuple[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any] | None]], *, since: str | None=None, router_available: bool=False, logging_enabled: bool=True, measured_loss_enabled: bool=False) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 997)

### Module constants

- `REPORT_VERSION` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 86)
- `PROBE_VALUE_SITE` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 106)
- `FOLLOWUP_VALUE_SITE` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 107)
- `TEACH_BACK_VALUE_SITE` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 108)
- `PROJECT_PROBE_VALUE_SITE` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 109)
- `VALUE_DECISION_SITES` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 110)
- `BINARY_CORRECTNESS_CUT` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 116)
- `REPAIR_RESOLUTION_KINDS` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 749)
- `_OBSERVATION_COLUMNS` ([src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 752)

## Internal implementation anchors

- `_has(connection: sqlite3.Connection, table: str) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 89)
- `_loads(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 95)
- `_administered(forecast: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 119) — A value decision whose described check was administered or admitted (``forecast_of`` committed, or a per-check receipt that kept its check).
- `_queues_item(action: Any, item: str) -> bool` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 167) — Whether an ``attempt_surprise`` action queued a follow-up of ``item``.
- `_observation(connection: sqlite3.Connection, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 511)
- `_target_facet_emission(connection: sqlite3.Connection, body: Mapping[str, Any], attempt_id: str) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 522) — A follow-up answer read as its TARGET facet's outcome (review F5).
- `_value_decision_emission(connection: sqlite3.Connection, vault: LoadedVault, forecast: Mapping[str, Any], attempt_id: str) -> tuple[str | None, str]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 616) — A value decision's realized emission, in the alphabet its described check was valued in.
- `_independent_match(row: Mapping[str, Any] | None, realized_attempt_id: str | None) -> str | None` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 757) — The one hypothesis an observation is independent evidence for, else None.
- `_support_delta(support: Mapping[str, Any]) -> float` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 779)
- `_cited_support(connection: sqlite3.Connection, support: Mapping[str, Any], linked: set[str], hypotheses: set[str], realized_attempt_id: str | None) -> tuple[str, set[str]] | None` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 786) — What a cold verification's diagnosis support proves, after resolving its evidence.
- `_join(connection: sqlite3.Connection, vault: LoadedVault, forecast: Mapping[str, Any], adapters: Sequence[Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 942)
- `_round(value: float | None, digits: int=4) -> float | None` ([source](../../../../../../src/learnloop/evsi_calibration/live_report.py), line 966)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]] — imports `calibration_report`; statically calls `calibration_report`
- [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]] — imports `module`; statically calls `LedgerOutcomeAdapter`, `RouterOutcomeAdapter`, `_join`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/voi_forecasts|learnloop.db.stores.voi_forecasts]] — imports `module`; calls `list_forecasts`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `SUPPORT_BASIS_AUTHORITY`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `score_bucket`; calls `score_bucket`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `facet_contract_criteria_hash`; calls `facet_contract_criteria_hash`
- [[Reference/Modules/learnloop/evsi_calibration/metrics|learnloop.evsi_calibration.metrics]] — imports `reliability`; calls `reliability`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `facet_outcome_bucket`; calls `facet_outcome_bucket`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/scheduling/unresolved_cost|learnloop.scheduling.unresolved_cost]] — imports `estimate_unresolved_cost`; calls `estimate_unresolved_cost`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `FORECAST_VERSION`, `entropy`, `posterior`; calls `entropy`, `posterior`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `held_for_review_attempts`, `unassessed_evidence_row`; calls `held_for_review_attempts`, `unassessed_evidence_row`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`

### Platform and third-party dependencies

- Standard library: `__future__`, `contextlib`, `json`, `math`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/evsi|learnloop.cli.evsi]], [[Reference/Modules/learnloop/evsi_calibration/forecast_report|learnloop.evsi_calibration.forecast_report]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_evsi_router_composition.py](../../../../../../tests/test_evsi_router_composition.py) — direct import
- [tests/test_evsi_staged_binding.py](../../../../../../tests/test_evsi_staged_binding.py) — direct import
  - `test_the_report_version_moved_with_the_presentation_join`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_evsi_report_realizes_no_outcome_from_a_held_attempt`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_a_later_teach_back_naming_the_same_cause_confirms_it`
  - `test_cold_verification_support_counts_only_its_resolved_admitted_observation`
  - `test_cold_verification_with_independent_diagnostic_support_is_truth`
  - `test_factor_resolution_by_repair_is_repair_effect_and_by_observation_is_truth`
  - `test_followup_offer_belongs_to_the_decision_that_produced_it`
  - `test_followup_outcome_is_the_target_facets_not_the_whole_items`
  - `test_followup_outcome_joins_only_the_attempt_that_took_the_followup`
  - `test_followup_outcome_maps_into_the_forecasts_alphabet`
  - `test_followup_outcome_needs_the_frozen_facet_map`
  - `test_one_cold_verification_is_one_repair_outcome`
  - `test_probe_selection_forecast_joins_its_realized_answer`
  - `test_regret_counts_only_independent_truth`
  - `test_repair_outcomes_are_not_diagnostic_truth`
  - `test_router_outcomes_are_preferred_when_r1_is_present`
  - `test_staged_emission_reads_the_administered_probe_outcome`
  - `test_staged_forecast_is_the_committed_selection_with_its_decision`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import

## Modification guidance

- Make changes here when the responsibility remains live report within learnloop.evsi_calibration; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/evsi_calibration/live_report.py](../../../../../../src/learnloop/evsi_calibration/live_report.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
