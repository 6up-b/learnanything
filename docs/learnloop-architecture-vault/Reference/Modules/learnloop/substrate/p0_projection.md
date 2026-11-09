---
title: "learnloop.substrate.p0_projection"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/p0_projection.py"
source_paths:
  - "src/learnloop/substrate/p0_projection.py"
source_commit: "b322ef2e9b5cebc241b612e4963a5aaf1a37f99a"
source_commit_timestamp: "2026-08-20T18:04:29-04:00"
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
  - "learnloop.substrate.p0_projection module"
  - "src/learnloop/substrate/p0_projection.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.p0_projection`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.p0_projection` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: P0.3 projection cutover + reinterpretation receipts (spec §4.2, §7.2).

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/p0_projection.py](../../../../../../src/learnloop/substrate/p0_projection.py) |
| Source lines | 128 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `b322ef2e9b5cebc241b612e4963a5aaf1a37f99a` |
| Commit timestamp | `2026-08-20T18:04:29-04:00` |

## Public API

- `activate_p0_projection(vault: LoadedVault, repository: Repository, *, from_version: str=KM_ALGORITHM_VERSION, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 33) — Rebuild + record activation of the mvp-0.8 projection (§7.2).
- `leading_conclusion(interpretation: Mapping[str, Any] | None) -> str | None` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 78) — The leading actionable conclusion of an interpretation: the top true class of its response posterior (§2.3).
- `record_reinterpretation_if_changed(repository: Repository, *, administration_id: str, observation_id: str, from_interpretation: Mapping[str, Any] | None, to_interpretation: Mapping[str, Any] | None, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/substrate/p0_projection.py), line 90) — Append a ``measurement_reinterpretation`` event when the leading actionable conclusion changed between two interpretations (§2.3).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]] — imports `record_reinterpretation_if_changed`; statically calls `record_reinterpretation_if_changed`
- [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/daily_plan_upgrade|learnloop.daily_plan_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/data_capture_upgrade|learnloop.data_capture_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/decider_upgrade|learnloop.decider_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/deliverable_plan_upgrade|learnloop.deliverable_plan_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/diagnosis/recurrence/upgrade|learnloop.diagnosis.recurrence.upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/eligibility_decision_upgrade|learnloop.eligibility_decision_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/failure_share_upgrade|learnloop.failure_share_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/followup_serve_upgrade|learnloop.followup_serve_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/help_fold_attach_upgrade|learnloop.help_fold_attach_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/intent_upgrade|learnloop.intent_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/learner_text_gap_upgrade|learnloop.learner_text_gap_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/lesson_offers_upgrade|learnloop.lesson_offers_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/lesson_opportunity_upgrade|learnloop.lesson_opportunity_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/lesson_suggestions_upgrade|learnloop.lesson_suggestions_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/method_explicit_upgrade|learnloop.method_explicit_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/one_ask_upgrade|learnloop.one_ask_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/ops/vault_upgrade|learnloop.ops.vault_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/phone_probes_upgrade|learnloop.phone_probes_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/probe_tie_upgrade|learnloop.probe_tie_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/proof_check_upgrade|learnloop.proof_check_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/reader_followups_upgrade|learnloop.reader_followups_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/reading_path_plan_upgrade|learnloop.reading_path_plan_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/regrade_contract_upgrade|learnloop.regrade_contract_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/route_rules_upgrade|learnloop.route_rules_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_calibration_upgrade|learnloop.router_calibration_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_followups_upgrade|learnloop.router_followups_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_learned_tail_upgrade|learnloop.router_learned_tail_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_mixture_upgrade|learnloop.router_mixture_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_objective_upgrade|learnloop.router_objective_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/router_staged_upgrade|learnloop.router_staged_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/slip_gap_upgrade|learnloop.slip_gap_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/sources_upgrade|learnloop.sources_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/stuck_prompt_upgrade|learnloop.stuck_prompt_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/superseded_claims_upgrade|learnloop.superseded_claims_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/teacher_probes_upgrade|learnloop.teacher_probes_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/teacher_upgrade|learnloop.teacher_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/unevidenced_return_upgrade|learnloop.unevidenced_return_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/voi_stopping_upgrade|learnloop.voi_stopping_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`
- [[Reference/Modules/learnloop/workbench_field_signals_upgrade|learnloop.workbench_field_signals_upgrade]] — imports `activate_p0_projection`; statically calls `activate_p0_projection`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `KM_ALGORITHM_VERSION`, `P0_ALGORITHM_VERSION`, `P0_PROJECTION_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/ad_successor_upgrade|learnloop.ad_successor_upgrade]], [[Reference/Modules/learnloop/attempt_content_state_upgrade|learnloop.attempt_content_state_upgrade]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/cli/grading|learnloop.cli.grading]], [[Reference/Modules/learnloop/cold_retry_reschedule_upgrade|learnloop.cold_retry_reschedule_upgrade]] and 39 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_p0_projection_cutover.py](../../../../../../tests/test_p0_projection_cutover.py) — direct import
  - `test_activation_records_derived_state_rebuild`
  - `test_adjudication_reverses_projection_and_preserves_history`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`

## Modification guidance

- Change p0 projection policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/p0_projection.py](../../../../../../src/learnloop/substrate/p0_projection.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
