---
title: "learnloop.diagnosis.failure_triage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/failure_triage.py"
source_paths:
  - "src/learnloop/diagnosis/failure_triage.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.failure_triage module"
  - "src/learnloop/diagnosis/failure_triage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.failure_triage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.failure_triage` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: P2 DIAGNOSTIC track -- two-tier failure-reason triage (U-027) (spec_p2_narrow_golden_path §6.1, §6.2, §12.2; design B.5; migration 083).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py) |
| Source lines | 1054 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TriageError(Exception)` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 124) — A triage action references an unknown run/event or an unknown reason.
- `class CausalSupportNormalization` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 129) — One normalization of a P2 diagnosis receipt's causal support, shared by the tier-one gate and the tier-two provisional distribution (contract §2).
- `normalize_causal_support(causal_support: Mapping[str, Any] | None) -> CausalSupportNormalization` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 171) — Normalize a causal-support snapshot into action-relative reason mass.
- `class TriageResult` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 287)
  - `as_dict(self) -> dict[str, Any]` (line 304; public)
- `triage(repository: Repository, run_id: str, *, attempt: Mapping[str, Any], routing_prior: Mapping[str, Any] | None=None, idempotency_key: str | None=None, clock: Clock | None=None) -> TriageResult` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 710) — Produce a triage record for a qualifying miss (§6.1).
- `decide(repository: Repository, run_id: str, *, triage_event_id: str, chosen_reason: str, actor: str='learner', idempotency_key: str | None=None, clock: Clock | None=None) -> TriageResult` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 890) — Commit a tier-two decision aid by selecting a named alternative (§6.1).
- `override(repository: Repository, run_id: str, *, triage_event_id: str, chosen_reason: str, actor: str='owner', idempotency_key: str | None=None, clock: Clock | None=None) -> TriageResult` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 960) — Explicitly override any triage outcome (a decisive tier-one route or a tier-two recommendation) with a corrected reason (§6.1).
- `triage_status(repository: Repository, run_id: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 1027) — The current triage state + full append-only trace for a run (§6.1 audit).

### Module constants

- `TRIAGE_ROUTES_SCHEMA_VERSION` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 53)
- `TRIAGE_CONFIDENCE_BUCKET_EDGES` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 58)
- `TRIAGE_DOMINANCE_SHARE` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 67)
- `TRIAGE_REASONS` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 70)
- `_SIGNATURE_REASON_MAP` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 85)
- `UNKNOWN_REASON` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 101)
- `TRACE_CONSISTENCY_STATES` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 106)
- `TIER_ONE_BASIS_DETERMINISTIC` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 119)
- `TIER_ONE_BASIS_LEGACY` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 120)
- `TIER_ONE_BASIS_CAUSAL` ([src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 121)

## Internal implementation anchors

- `_causal_rows(causal_support: Mapping[str, Any] | None) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 149)
- `_is_open_set(row: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 159)
- `_reason_trace_state(causal_support: Mapping[str, Any] | None, reason: str) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 261) — Collapse the per-hypothesis trace-consistency states of every concrete hypothesis mapping to ``reason`` (§5.6).
- `_confidence_bucket(confidence: float) -> str` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 314)
- `_blueprint_signature_map(repository: Repository, run: Mapping[str, Any]) -> dict[str, str]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 323)
- `_decisive_route(inputs: Mapping[str, Any], signature_map: Mapping[str, str], *, distribution: Mapping[str, float] | None=None, causal_support: Mapping[str, Any] | None=None, causal_support_available: bool=False) -> tuple[str | None, str | None]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 334) — Tier-one decisive route (§6.1).
- `_decisive_reason(inputs: Mapping[str, Any], signature_map: Mapping[str, str], *, distribution: Mapping[str, float] | None=None, causal_support: Mapping[str, Any] | None=None, causal_support_available: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 409) — The reason half of :func:`_decisive_route` (kept for callers that do not care which arm of the gate fired).
- `_latest_discriminating_observation(repository: Repository, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 429) — The newest ADMITTED §7 observation bearing on this attempt's diagnosis.
- `_causal_support_snapshot(repository: Repository, inputs: Mapping[str, Any], signature_map: Mapping[str, str] | None=None) -> tuple[dict[str, Any] | None, bool]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 445) — Project a P2 diagnosis receipt into the support snapshot the gate consumes.
- `_supplied_distribution(inputs: Mapping[str, Any]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 552) — The P0-supplied provisional distribution filtered to the ten reasons, or None when the grading pass supplied none.
- `_signature_is_dominant(reason: str, distribution: Mapping[str, float] | None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 568) — True when ``reason`` owns a dominant share of the provisional distribution mass (>= ``TRIAGE_DOMINANCE_SHARE``) and is the argmax (C3).
- `_provisional_distribution(inputs: Mapping[str, Any], signature_map: Mapping[str, str], *, causal_support: Mapping[str, Any] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 585) — Tier-two provisional distribution over reasons (§6.1).
- `_recommended_reason(distribution: Mapping[str, float]) -> str` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 617)
- `_route_summary(route: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 621)
- `_row_belongs_to(row: Mapping[str, Any], reason: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 634) — Which alternative a causal-support row is evidence for -- the same bucketing :func:`normalize_causal_support` used to build the distribution.
- `_alternatives(repository: Repository, distribution: Mapping[str, float], *, causal_support: Mapping[str, Any] | None=None, top_k: int=3) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 643)
- `_goal_contract_head(repository: Repository, run: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 677)
- `_route_run(repository: Repository, run_id: str, reason: str, route: Mapping[str, Any], *, idempotency_key: str, clock: Clock | None) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 682) — Advance the run into the ladder entry stage the route names -- but only from the ``triaging`` gate, so triage stays usable diagnostically outside the run's happy path without forcing an illegal transition.
- `_log_adjudication_anchor(repository: Repository, *, run: Mapping[str, Any], attempt_id: str | None, actor: str, chosen_reason: str, prior_reason: str | None, clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/diagnosis/failure_triage.py), line 854) — Log a learner/owner override as an adjudication anchor into the U-020 calibration stream (P0.2 machinery).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]] — imports `module`; statically calls `decide`, `override`, `triage`, `triage_status`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/calibration_streams|learnloop.attempts.calibration_streams]] — imports `module`; calls `record_adjudicated_anchor_sample`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; calls `advance`, `project_run`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `APPROVED_SUPPORT_AUTHORITIES`, `OPEN_SET_CAUSE_ID`, `receipt_trace_consistency`; calls `receipt_trace_consistency`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_json`; calls `canonical_json`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/diagnostic|learnloop_sidecar.handlers.diagnostic]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_attribution_p2.py](../../../../../../tests/test_causal_attribution_p2.py) — direct import
  - `test_triage_signature_authority_is_an_and_gate_not_a_replacement`
- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_a_deterministic_sensor_earns_validator_owned_and_reaches_triage`
  - `test_causal_disambiguation_end_to_end_acceptance`
  - `test_causal_lane_health_watches_both_tails_and_pins_the_tier_one_basis`
  - `test_dominance_veto_is_reachable_through_the_real_triage_entrypoint`
- [tests/test_failure_triage.py](../../../../../../tests/test_failure_triage.py) — direct import
  - `test_ambiguous_cause_defaults_to_unknown_distribution`
  - `test_bare_high_confidence_signature_still_routes_tier_one`
  - `test_concentrated_signature_distribution_stays_tier_one`
  - `test_decide_commits_the_aid_and_routes_the_run`
  - `test_decide_diverging_from_recommendation_logs_an_anchor`
  - `test_diffuse_signature_distribution_downgrades_to_tier_two`
  - `test_dont_know_on_never_exposed_routes_unfamiliar_decisively`
  - `test_expired_memory_trace_routes_lapse_decisively`
  - `test_high_confidence_signature_takes_intended_route`
  - `test_low_confidence_yields_decision_aid_that_never_auto_commits`
  - `test_override_logs_adjudication_anchor`
  - `test_quarantined_surface_routes_fault_never_a_deficit`
  - `test_retried_triage_is_idempotent_on_the_ledger`
  - `test_route_table_is_seeded_data_over_ten_reasons`
  - `test_supplied_p0_distribution_is_used_and_normalized`
  - `test_triage_trace_is_append_only_and_logs_goal_contract_head`
- [tests/test_failure_triage_causal_gate.py](../../../../../../tests/test_failure_triage_causal_gate.py) — direct import
  - `test_a_discriminating_observation_overlays_scores_but_not_always_authority`
  - `test_all_none_scores_produce_zero_mass_and_no_dominance`
  - `test_alternatives_surface_the_residual_bucket_and_its_hypotheses`
  - `test_authority_approval_reads_the_causal_attribution_vocabulary`
  - `test_causal_veto_downgrades_an_otherwise_legacy_valid_route`
  - `test_deterministic_triggers_report_their_own_basis`
  - `test_incomplete_support_blocks_promotion_but_not_the_legacy_arm`
  - `test_legacy_receipt_states_are_unknown_and_cannot_promote`
  - `test_missing_score_on_a_concrete_hypothesis_is_incomplete`
  - `test_negative_score_is_clamped_and_flagged`
  - `test_no_receipt_keeps_the_pure_legacy_behaviour`
  - `test_open_set_row_never_credits_a_mapped_reason`
  - `test_promotion_requires_positive_trace_evidence_not_mere_absence`
  - `test_provisional_distribution_keeps_the_residual_bucket_visible`
  - `test_real_receipt_from_apply_attempt_does_not_force_tier_two`
  - `test_receipt_presence_alone_does_not_downgrade_the_legacy_route`
  - `test_snapshot_uses_the_merged_signature_map_and_keeps_open_set_rows`
  - `test_supplied_distribution_still_takes_precedence`
  - `test_ties_and_residual_maxima_name_no_dominant_reason`
  - `test_triage_records_tier_one_basis_on_the_result_and_the_event`
  - `test_two_hypotheses_on_one_reason_aggregate`
  - `test_unapproved_authority_cannot_promote`
  - `test_unmapped_and_open_set_mass_stays_in_the_denominator`
  - `test_zero_mass_causal_support_falls_through_to_the_signature_fallback`
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_event_replay_equivalence_after_full_walk`
  - `test_golden_path_ten_step_fixture_journey`
  - `test_misconception_planted_learner_takes_signature_route_and_repair_rung`
- [tests/test_pattern_ladder.py](../../../../../../tests/test_pattern_ladder.py) — direct import
  - `test_entry_stage_is_set_by_the_triage_route`

## Modification guidance

- Change failure triage policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/failure_triage.py](../../../../../../src/learnloop/diagnosis/failure_triage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
