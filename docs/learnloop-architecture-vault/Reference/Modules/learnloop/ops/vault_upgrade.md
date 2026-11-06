---
title: "learnloop.ops.vault_upgrade"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/ops/vault_upgrade.py"
source_paths:
  - "src/learnloop/ops/vault_upgrade.py"
source_commit: "608f1245694ed864c345c5b7d24f639fd1a1283c"
source_commit_timestamp: "2026-10-16T22:16:14-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.ops"
layer: "domain"
concepts:
  - "State and Persistence"
  - "Configuration"
workflows:
  - "Doctor Migrations and Recovery"
aliases:
  - "learnloop.ops.vault_upgrade module"
  - "src/learnloop/ops/vault_upgrade.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-ops"
---

# `learnloop.ops.vault_upgrade`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.ops.vault_upgrade` exists within [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] to own the behavior summarized by its module contract: mvp-0.7 activation: atomic vault upgrade + mixed-version guards (KM §15, §12.7).

The authoritative system-level explanation remains in [[State and Persistence]], [[Configuration]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py) |
| Source lines | 510 |
| Owning package | [[Reference/Modules/learnloop/ops/_package|learnloop.ops]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `608f1245694ed864c345c5b7d24f639fd1a1283c` |
| Commit timestamp | `2026-10-16T22:16:14-04:00` |

## Public API

- `class UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 43)
- `validate_mvp07_readiness(vault: LoadedVault) -> list[str]` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 56) — Blocking reasons a vault cannot activate the mvp-0.7 knowledge model (§3.2).
- `upgrade_to_mvp07(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 83) — Atomically activate mvp-0.7 and project legacy attempts into its state.
- `upgrade_to_mvp08(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 134) — Activate the mvp-0.8 authority-propagation projection as the default read path (spec §7.2, P0.5 design §7).
- `upgrade_to_mvp09(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 196) — Activate cross-channel reveal accounting on the existing P0 projection.
- `upgrade_to_mvp010(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 256) — Activate the Slice 1 split (blind grader + asynchronous diagnoser).
- `upgrade_to_mvp011(root: Path, *, clock: Clock | None=None) -> UpgradeResult` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 321) — Activate learner field F2: starting new material without ceremony.
- `class CompatibilityDelta` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 442) — Explicit, inspectable mvp-0.7 -> mvp-0.8 reinterpretation delta (§7.2/§9.6).
  - `as_dict(self) -> dict[str, Any]` (line 452; public)
- `compatibility_projection_delta(baseline_cells: dict, candidate_cells: dict) -> CompatibilityDelta` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 456) — Compare two projected facet-capability cell maps (``{key: (pos, neg, cred)}``) and report the explicit delta.
- `rewrite_algorithm_version(config_path: Path, from_version: str, to_version: str, *, durable: bool=False) -> None` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 472) — Atomically flip the single algorithm_version field (write-temp + rename).

### Module constants

- `LEGACY_ALGORITHM_VERSION` ([src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py), line 36)
- `COMPATIBILITY_DELTA_FILENAME` ([src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py), line 39)

## Internal implementation anchors

- `_projected_cells(repository: Repository) -> dict[tuple[str, str], tuple[float, float, float]]` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 411) — The projected facet-capability cells as ``{(facet, capability): (direct_pos, direct_neg, cert_credit)}`` -- the comparable surface for the mvp-0.7 vs mvp-0.8 compatibility delta.
- `_persist_compatibility_delta(sqlite_path: Path, delta: 'CompatibilityDelta', *, from_version: str) -> Path` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 426) — Write the inspectable cutover delta as a JSON artifact next to the sqlite.
- `_rewrite_algorithm_version(config_path: Path, from_version: str, to_version: str, *, durable: bool=False) -> None` ([source](../../../../../../src/learnloop/ops/vault_upgrade.py), line 487) — Atomically flip the single algorithm_version field (write-temp + rename).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `upgrade_to_mvp010`, `upgrade_to_mvp011`, `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`; statically calls `upgrade_to_mvp010`, `upgrade_to_mvp011`, `upgrade_to_mvp07`, `upgrade_to_mvp08`, `upgrade_to_mvp09`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`, `upgrade_to_mvp011`; statically calls `UpgradeResult`, `rewrite_algorithm_version`, `upgrade_to_mvp011`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/interval_factor_upgrade|learnloop.interval_factor_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/learner/recall_calibration|learnloop.learner.recall_calibration]] — imports `KM_ALGORITHM_VERSION`, `LEGACY_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/replay_ledger_upgrade|learnloop.replay_ledger_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/router_calibration_upgrade|learnloop.router_calibration_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/router_followups_upgrade|learnloop.router_followups_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/router_learned_tail_upgrade|learnloop.router_learned_tail_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/teacher_probes_upgrade|learnloop.teacher_probes_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `UpgradeResult`; statically calls `UpgradeResult`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `UpgradeResult`, `rewrite_algorithm_version`; statically calls `UpgradeResult`, `rewrite_algorithm_version`

### Repository tooling consumers

- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `upgrade_to_mvp09`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `DIAGNOSIS_SPLIT_ALGORITHM_VERSION`, `PLACEMENT_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `REVEAL_LEDGER_ALGORITHM_VERSION`
- [[Reference/Modules/learnloop/params/parameter_registry|learnloop.params.parameter_registry]] — imports `module`; calls `freeze_manifest`, `refresh`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/substrate/p0_projection|learnloop.substrate.p0_projection]] — imports `activate_p0_projection`; calls `activate_p0_projection`
- [[Reference/Modules/learnloop/vault/loader|learnloop.vault.loader]] — imports `load_vault`; calls `load_vault`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`
- [[Reference/Modules/learnloop/vault/paths|learnloop.vault.paths]] — imports `VaultPaths`; calls `VaultPaths`
- [[Reference/Modules/learnloop/vault/repository|learnloop.vault.repository]] — imports `open_vault_repository`; calls `open_vault_repository`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `os`, `pathlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Doctor Migrations and Recovery]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] and 35 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_attempt_content_state_successor.py](../../../../../../tests/test_attempt_content_state_successor.py) — direct import
  - `test_the_upgrade_refuses_a_version_before_the_chain`
- [tests/test_batch3_landing.py](../../../../../../tests/test_batch3_landing.py) — direct import
  - `test_i_a_figure_goal_from_the_ask_rail_or_the_tutor_never_spends_an_ask_question`
  - `test_iii_a_figure_grant_never_meters_an_ask_and_an_ask_grant_meters_it_under_the_cap`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_the_upgrade_refuses_a_version_before_the_chain`
- [tests/test_curriculum_c1_landing.py](../../../../../../tests/test_curriculum_c1_landing.py) — direct import
- [tests/test_curriculum_c1_plan_follows_path.py](../../../../../../tests/test_curriculum_c1_plan_follows_path.py) — direct import
  - `test_the_upgrade_refuses_a_version_before_the_chain`
- [tests/test_followups_nov2_help_fold.py](../../../../../../tests/test_followups_nov2_help_fold.py) — direct import
- [tests/test_help_fold_attach_successor.py](../../../../../../tests/test_help_fold_attach_successor.py) — direct import
  - `test_the_upgrade_refuses_a_version_before_the_chain`
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — direct import
  - `test_app_load_repairs_vault_activated_by_old_upgrade`
  - `test_upgrade_is_idempotent`
  - `test_upgrade_projects_existing_attempts_into_canonical_facet_state`
  - `test_upgrade_refuses_from_unknown_version`
  - `test_upgrade_refuses_when_facets_unregistered`
  - `test_upgrade_succeeds_when_registry_complete`
  - `test_validate_readiness_flags_incomplete_contract`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_an_mvp035_journal_is_handed_to_its_own_upgrade_then_the_tag_activates`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_chained_notes_pass_through_an_upgrade_and_a_refusal`
- [tests/test_mvp010_upgrade.py](../../../../../../tests/test_mvp010_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_upgrade_flips_rebuilds_and_preserves_raw_history`
  - `test_upgrade_is_immediate_successor_only`
- [tests/test_mvp011_upgrade.py](../../../../../../tests/test_mvp011_upgrade.py) — direct import
  - `test_head_fixture_predecessor_to_successor_path`
  - `test_upgrade_from_mvp010_flips_rebuilds_and_preserves_history_and_open_episodes`
  - `test_upgrade_from_mvp09_chains_through_the_split`
  - `test_upgrade_refuses_older_versions_and_is_idempotent`
- [tests/test_mvp022_upgrade.py](../../../../../../tests/test_mvp022_upgrade.py) — direct import
  - `test_chained_notes_pass_through_an_upgrade_and_a_refusal`
- [tests/test_mvp023_upgrade.py](../../../../../../tests/test_mvp023_upgrade.py) — direct import
  - `test_chained_notes_pass_through_an_upgrade_and_a_refusal`
- [tests/test_mvp024_upgrade.py](../../../../../../tests/test_mvp024_upgrade.py) — direct import
  - `test_chained_notes_pass_through_an_upgrade_and_a_refusal`
- [tests/test_mvp09_upgrade.py](../../../../../../tests/test_mvp09_upgrade.py) — direct import
  - `test_upgrade_to_mvp09_flips_rebuilds_and_preserves_raw_history`
  - `test_upgrade_to_mvp09_is_immediate_successor_only`
- [tests/test_p0_cutover_mvp08.py](../../../../../../tests/test_p0_cutover_mvp08.py) — direct import
  - `test_already_mvp08_is_a_noop`
  - `test_compatibility_delta_is_explicit_when_changed`
  - `test_compatibility_delta_matches_when_identical`
  - `test_cutover_delta_is_empty_when_projections_match`
  - `test_cutover_delta_is_nonempty_and_inspectable_when_projections_differ`
  - `test_mvp06_derived_output_is_byte_identical_across_p0_machinery`
  - `test_upgrade_does_not_rewrite_raw_history`
  - `test_upgrade_freezes_legacy_manifests_immutably`
  - `test_upgrade_refuses_from_non_mvp07`
  - `test_upgrade_to_mvp08_flips_and_records_receipt`
- [tests/test_rbeq_pr2_landing.py](../../../../../../tests/test_rbeq_pr2_landing.py) — direct import
- [tests/test_reader_followups_successor.py](../../../../../../tests/test_reader_followups_successor.py) — direct import
  - `test_the_upgrade_refuses_a_version_before_the_chain`

## Modification guidance

- Make changes here when the responsibility remains vault upgrade within learnloop.ops; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/ops/vault_upgrade.py](../../../../../../src/learnloop/ops/vault_upgrade.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
