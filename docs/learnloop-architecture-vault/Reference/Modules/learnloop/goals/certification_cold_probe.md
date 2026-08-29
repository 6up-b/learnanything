---
title: "learnloop.goals.certification_cold_probe"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/goals/certification_cold_probe.py"
source_paths:
  - "src/learnloop/goals/certification_cold_probe.py"
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
  - "learnloop.goals.certification_cold_probe module"
  - "src/learnloop/goals/certification_cold_probe.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-goals"
---

# `learnloop.goals.certification_cold_probe`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.goals.certification_cold_probe` exists within [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] to own the behavior summarized by its module contract: Delayed cold probe per certified LO, and `false_certification_rate`.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py) |
| Source lines | 1850 |
| Owning package | [[Reference/Modules/learnloop/goals/_package|learnloop.goals]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class ColdProbeParameters` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 209) — Resolved probe knobs plus their provenance.
  - `__getitem__(self, key: str) -> float` (line 222; internal)
  - `horizon_days(self) -> float` (line 226; public)
  - `window_days(self) -> float` (line 230; public)
  - `success_correctness(self) -> float` (line 234; public)
  - `manifest(self) -> dict[str, Any]` (line 237; public)
- `resolve_cold_probe_parameters(repository: Repository | None) -> ColdProbeParameters` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 247) — Active fitted cold-probe knobs, else the pinned heuristic defaults.
- `class CertifiedCell` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 290) — One (facet, capability) cell the certificate rests on.
  - `as_dict(self) -> dict[str, Any]` (line 309; public)
- `class Certificate` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 322) — A derived §5.3 certificate: LO + satisfying recipe + the cells it rests on.
  - `certificate_id(self) -> str` (line 333; public) — Content hash over the certificate's identity.
  - `integration_cell(self) -> CertifiedCell | None` (line 358; public)
  - `used_surface_groups(self) -> tuple[str, ...]` (line 361; public) — Every surface group the certifying evidence came from.
  - `as_receipt(self) -> dict[str, Any]` (line 372; public) — The §5.3 receipt: which cells, at what credit, from which surfaces.
- `current_certificate(vault: LoadedVault, repository: Repository, learning_object: LearningObject) -> Certificate | None` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 394) — The certificate this LO currently holds, or None if it holds none.
- `class HeldOutSelection` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 535) — The chosen probe item, or the typed reason there is none.
  - `as_dict(self) -> dict[str, Any]` (line 559; public)
- `select_held_out_probe_item(vault: LoadedVault, repository: Repository, certificate: Certificate) -> HeldOutSelection` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 576) — Pick one active item that observes a certified cell on an unused surface.
- `class ScheduleDecision` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 731) — What the scheduler did (or declined to do) for one LO.
  - `as_dict(self) -> dict[str, Any]` (line 744; public)
- `class ScheduleReport` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 759)
  - `counts(self) -> dict[str, int]` (line 764; public)
  - `as_dict(self) -> dict[str, Any]` (line 770; public)
- `schedule_certification_cold_probes(vault: LoadedVault, repository: Repository, *, learning_object_id: str | None=None, clock: Clock | None=None) -> ScheduleReport` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 780) — Queue one delayed cold probe per certified LO.
- `probe_window(certified_at: str | None, parameters: ColdProbeParameters, *, clock: Clock | None=None) -> tuple[str, str]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1104) — ``(not_before, expires_at)`` for a certificate earned at ``certified_at``.
- `record_certification_cold_probe_attempt(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], *, grading_source: str | None=None, grading_agent_run_id: str | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1204) — Consume a due probe and record whether the certificate held.
- `class FalseCertificationRate` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1481) — `false_certification_rate` with its denominator and availability arm.
  - `available(self) -> bool` (line 1520; public)
  - `keys(self) -> tuple[str, ...]` (line 1532; public)
  - `__getitem__(self, key: str) -> Any` (line 1535; internal)
  - `as_dict(self) -> dict[str, Any]` (line 1538; public) — The §3 B5 scoreboard entry.
- `false_certification_rate(repository: Repository, *, clock: Clock | None=None) -> FalseCertificationRate` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1578) — Certified-then-failed over certified-and-probed (§5.7, §3 B5).
- `cold_outcome_labels(repository: Repository) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1667) — The certification lane's cold-outcome labels, in the causal P4 shape.
- `certification_cold_probe_report(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1714) — `false_certification_rate` plus the coverage of the probe lane itself.

### Module constants

- `COLD_PROBE_STORE_VERSION` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 105)
- `COLD_PROBE_POLICY_VERSION` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 109)
- `COLD_PROBE_TASK_KIND` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 112)
- `COLD_PROBE_CASE_KIND` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 114)
- `COLD_PROBE_CONTEXT_KIND` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 116)
- `PROBE_VERDICTS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 122)
- `SCORED_VERDICTS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 124)
- `INDETERMINATE_REASONS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 129)
- `SCHEDULE_DECISIONS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 141)
- `HELD_OUT_BASES` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 159)
- `_BASE_AVOIDED_AFFORDANCES` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 168)
- `COLD_PROBE_POLICY_DEFAULTS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 187)
- `_COLD_PROBE_POLICY_BOUNDS` ([src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 199)

### Explicit exports

`__all__` declares:

- `COLD_PROBE_CASE_KIND`
- `COLD_PROBE_CONTEXT_KIND`
- `COLD_PROBE_POLICY_DEFAULTS`
- `COLD_PROBE_POLICY_VERSION`
- `COLD_PROBE_STORE_VERSION`
- `COLD_PROBE_TASK_KIND`
- `Certificate`
- `CertifiedCell`
- `ColdProbeParameters`
- `FalseCertificationRate`
- `HELD_OUT_BASES`
- `HeldOutSelection`
- `INDETERMINATE_REASONS`
- `PROBE_VERDICTS`
- `SCHEDULE_DECISIONS`
- `SCORED_VERDICTS`
- `ScheduleDecision`
- `ScheduleReport`
- `certification_cold_probe_report`
- `cold_outcome_labels`
- `current_certificate`
- `false_certification_rate`
- `probe_window`
- `record_certification_cold_probe_attempt`
- `resolve_cold_probe_parameters`
- `schedule_certification_cold_probes`
- `select_held_out_probe_item`

## Internal implementation anchors

- `_recipe(learning_object: LearningObject, blueprint_id: str, recipe_id: str)` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 479)
- `_certified_components(vault: LoadedVault, recipe, gaps) -> list[tuple[Any, str]]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 489) — The components `recipe_gaps` actually gated on, with their roles.
- `_selection_inventory_trigger(vault: LoadedVault, repository: Repository, certificate: Certificate) -> str` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1026) — Stable pre-selection identity for the currently available item pool.
- `_target_learning_objects(vault: LoadedVault, learning_object_id: str | None) -> list[LearningObject]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1072)
- `_cancel_stale_probes(repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> ScheduleDecision` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1081) — Retire probes for an LO that is no longer certified.
- `_probe_context(certificate: Certificate, selection: HeldOutSelection, parameters: ColdProbeParameters, not_before: str, expires_at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1128) — Everything the consume side will need, resolved NOW (migration 124's rule).
- `_avoided_affordances(certificate: Certificate, selection: HeldOutSelection) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1178) — What the probe gives up relative to the certifying evidence.
- `_record_probe_outcome(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], *, grading_source: str | None, grading_agent_run_id: str | None, clock: Clock | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1245)
- `_attempt_is_assisted(attempt: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1407) — The shared assistance test, not a local re-derivation.
- `_certificate_state_at_probe(vault: LoadedVault, repository: Repository, learning_object_id: str, certificate_id: str) -> str` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1425) — ``active`` iff the LO still holds the exact certificate being probed.
- `_grader_stamp(repository: Repository, attempt_id: str, *, grading_source: str | None, grading_agent_run_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1442) — Grader provenance for the label, following `diagnosis_adjudication`.
- `_rate(bucket: Mapping[str, int]) -> float | None` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1655)
- `_horizon_key(value: Any) -> str` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1660)
- `_carried(context: Mapping[str, Any], key: str, fallback: float) -> float` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1797) — A numeric knob carried on the task, else the live default.
- `_content_id(prefix: str, value: Any) -> str` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1813)
- `_iso(value) -> str` ([source](../../../../../../src/learnloop/goals/certification_cold_probe.py), line 1818)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `record_certification_cold_probe_attempt`; statically calls `record_certification_cold_probe_attempt`
- [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]] — imports `schedule_certification_cold_probes`; statically calls `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `certification_cold_probe_report`, `schedule_certification_cold_probes`; statically calls `certification_cold_probe_report`, `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `schedule_certification_cold_probes`; statically calls `schedule_certification_cold_probes`
- [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]] — imports `certification_cold_probe_report`, `schedule_certification_cold_probes`; statically calls `certification_cold_probe_report`, `schedule_certification_cold_probes`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/coldness_receipt|learnloop.attempts.coldness_receipt]] — imports `LANE_CERTIFICATION_COLD_PROBE`, `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`; calls `evaluate_final_coldness`, `record_final_receipt`, `record_schedule_refusal_receipt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `attempt_counts_as_assisted`; calls `attempt_counts_as_assisted`
- [[Reference/Modules/learnloop/goals/goal_certification|learnloop.goals.goal_certification]] — imports `lo_certification`, `recipe_gaps`; calls `lo_certification`, `recipe_gaps`
- [[Reference/Modules/learnloop/learner/contract_reachability|learnloop.learner.contract_reachability]] — imports `CONTRACT_MODALITIES`, `build_instrument_pool`; calls `build_instrument_pool`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `CERTIFICATION_COLD_PROBE_SCOPE`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Goals Exams and Certification Workflow]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/post_attempt|learnloop.attempts.post_attempt]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/measurement|learnloop_sidecar.handlers.measurement]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_certification_cold_probe.py](../../../../../../tests/test_certification_cold_probe.py) — direct import
  - `test_a_fresh_diagnostic_surface_remains_selectable_for_the_probe`
  - `test_a_queued_probe_refuses_an_assisted_attempt`
  - `test_a_superseded_certificate_has_its_probe_cancelled_and_a_fresh_one_queued`
  - `test_abstained_probes_are_not_training_labels`
  - `test_an_uncertified_lo_schedules_nothing`
  - `test_certificate_id_and_selection_are_deterministic`
  - `test_cli_schedules_and_reports_the_unavailable_arm`
  - `test_cold_outcome_labels_expose_the_causal_p4_shape`
  - `test_new_inventory_creates_a_fresh_opportunity_after_structural_refusal`
  - `test_no_active_instrument_at_all_reports_no_candidate`
  - `test_one_probe_per_certified_lo_idempotently`
  - `test_only_administered_diagnostic_candidates_means_no_held_out_surface`
  - `test_outcome_rows_are_append_only`
  - `test_probe_against_a_withdrawn_certificate_abstains_rather_than_failing`
  - `test_probe_is_due_at_the_horizon_and_invisible_before_it`
  - `test_probe_prefers_the_whole_task_item_that_covers_integration`
  - `test_probe_records_a_durable_versioned_label`
  - `test_rate_is_correct_over_a_mix_of_held_and_failed_certificates`
  - `test_rate_over_zero_probes_is_unavailable_not_zero`
  - `test_selected_surface_is_never_one_the_certificate_used`
  - `test_selection_never_picks_an_administered_diagnostic_surface`
  - `test_shared_surface_group_makes_the_certificate_unmeasurable`
  - `test_the_only_instrument_being_the_certifying_one_is_unmeasurable`
  - `test_withdrawn_certificate_schedules_nothing_and_cancels_a_queued_probe`
- [tests/test_goal_certification_any_of.py](../../../../../../tests/test_goal_certification_any_of.py) — direct import
  - `test_all_of_only_recipe_behaviour_is_unchanged`
  - `test_any_of_only_recipe_does_not_certify_without_evidence`
  - `test_certificate_cells_include_the_satisfying_alternative`
  - `test_certificate_id_tracks_which_alternative_certified`
  - `test_recipe_with_no_contract_component_never_certifies`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_the_certification_cold_probe_selects_an_instrument_as_its_held_out_item`
- [tests/test_scoreboard.py](../../../../../../tests/test_scoreboard.py) — direct import
  - `test_false_certification_rate_is_composed_from_item_4_2`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_sidecar_submission_schedules_certification_cold_probe`

## Modification guidance

- Change certification cold probe policy here when goals owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/goals/certification_cold_probe.py](../../../../../../src/learnloop/goals/certification_cold_probe.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
