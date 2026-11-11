---
title: "learnloop.scheduling.staged_policy"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/staged_policy.py"
source_paths:
  - "src/learnloop/scheduling/staged_policy.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.staged_policy module"
  - "src/learnloop/scheduling/staged_policy.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.staged_policy`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.staged_policy` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: P4 step 2 -- the transparent staged decision policy (spec §4, design B step 2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py) |
| Source lines | 1048 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class AttentionBlock` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 90) — One coherent 5-15 minute block (§4.1).
  - `content_hash(self) -> str` (line 105; public)
- `class StagedIntent` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 120) — The one canonical action the §4.2 ladder produced, and which rung fired.
- `class StateSignals` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 132) — Decision-relevant state signals feeding the §4.2 ladder.
- `is_short_session(snapshot: cs.ControllerSnapshot) -> bool` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 151) — A short session (§12.2): available minutes are known and below the 5-min lower bound of the coherent attention block.
- `evaluate_staged_rule(snapshot: cs.ControllerSnapshot, signals: StateSignals) -> StagedIntent` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 216) — The §4.2 global staged rule as an explicit if/elif ladder.
- `ladder_eligibility(snapshot: cs.ControllerSnapshot, signals: StateSignals, *, short_circuited: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 294) — Every §4.2 rung with whether its condition holds (router R1's staged eligibility).
- `choose_block(snapshot: cs.ControllerSnapshot, signals: StateSignals, *, continuation: Mapping[str, Any] | None=None, explicit_choice: Mapping[str, Any] | None=None, served_administration: Mapping[str, Any] | None=None) -> tuple[AttentionBlock, StagedIntent]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 370) — Level one (§4.1).
- `class DiagnosticSelector` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 435) — P4 step 3 within-block ranking context (§6.4).
- `class DecisionResult` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 732)
- `decide(vault: LoadedVault, repository: Repository, session: Any | None=None, *, signals: StateSignals | None=None, candidates: Sequence[cs.Candidate] | None=None, continuation: Mapping[str, Any] | None=None, explicit_choice: Mapping[str, Any] | None=None, served_administration: Mapping[str, Any] | None=None, receipt_key: str | None=None, shadow_scorers: Sequence[Callable[[cs.ControllerSnapshot, cs.Candidate | None], Any]] | None=None, record_comparator: bool=True, diagnostic: DiagnosticSelector | None=None, mode: str='shadow', owned_item_refs: set[str] | None=None, clock: Clock | None=None) -> DecisionResult` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 747) — Run one staged decision end to end and persist its full trace (shadow mode).

### Module constants

- `STAGED_POLICY_VERSION` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 49)
- `ATTENTION_BLOCK_MIN_MINUTES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 53)
- `ATTENTION_BLOCK_MAX_MINUTES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 54)
- `DEFAULT_BLOCK_BUDGET_MINUTES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 55)
- `CONTEXT_SWITCH_COST_MINUTES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 56)
- `NEGATIVE_AFFECT_DOWNGRADE_THRESHOLD` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 60)
- `SHORT_SESSION_MAX_MINUTES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 68)
- `SHORT_SESSION_PREFERRED_PATTERNS` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 73)
- `_ACTION_PURPOSES` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 78)
- `IRREVERSIBLE_RUNGS` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 289)
- `OWNERSHIP_REFUSAL_KEY` ([src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py), line 630)

## Internal implementation anchors

- `_block_budget(snapshot: cs.ControllerSnapshot) -> float` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 159)
- `_as_short_block(block: AttentionBlock, snapshot: cs.ControllerSnapshot) -> AttentionBlock` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 173) — Mark a block as a short-session completing block (§12.2): one completed activity ends the session, so its single exit rule is ``session_complete_on_one_activity`` and its neighborhood records the short-session budget.
- `_pick_commitment(snapshot: cs.ControllerSnapshot, *, want_auto: bool=False) -> cs.CommitmentSummary | None` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 191)
- `_feasible_reviewed_edge(commitment: cs.CommitmentSummary, milestone: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 201) — A reviewed edge originating at the reached milestone, wholly inside the envelope (§5 depth constraints, structural).
- `_select_within_block(block: AttentionBlock, report: ce.FeasibilityReport, snapshot: cs.ControllerSnapshot | None=None) -> tuple[cs.Candidate | None, str, list[tuple[cs.Candidate, int]]]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 450) — Level two (§4.4): apply the block-specific TRANSPARENT selector over the feasible set.
- `_tiebreak_seed(snapshot_hash: str, experiment_id: str, refs: Sequence[str]) -> str` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 487) — The decision-specific ε tie-break seed (audit M2/F4): derived from the snapshot hash + experiment id + the tied candidate refs so two DIFFERENT decisions draw differently while the SAME decision replays to the same draw.
- `_diagnostic_candidates(report: ce.FeasibilityReport, diagnostic: DiagnosticSelector) -> tuple[dict[str, cs.Candidate], list[EV.DiagnosticCandidate]]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 496) — The feasible candidates that carry diagnostic material, as EVSI candidates.
- `_record_diagnostic_forecast(vault: LoadedVault, repository: Repository, *, decision_id: str, mode: str, report: ce.FeasibilityReport, diagnostic: DiagnosticSelector, result: EV.RankResult, chosen: cs.Candidate | None, assignment: Mapping[str, Any] | None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 519) — EVSI calibration Part B: the committed staged diagnostic decision's forecast.
- `_select_diagnostic(report: ce.FeasibilityReport, diagnostic: DiagnosticSelector, *, repository: Repository | None, clock: Clock | None, snapshot_hash: str | None=None, decision_id: str | None=None) -> tuple[cs.Candidate | None, str, list[tuple[cs.Candidate, int]], EV.RankResult, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 573) — Robust-EVSI-per-minute selection over the feasible set (§6.4).
- `_apply_ownership(report: ce.FeasibilityReport, owned_item_refs: set[str]) -> tuple[ce.FeasibilityReport, list[str]]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 633) — Refuse every feasible candidate the staged controller does not own (§14.2 step 3).
- `_affect_downgrade(snapshot: cs.ControllerSnapshot, commitment_id: str | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 665) — U-011 affect check, evaluated BEFORE any depth edge is considered.
- `_comparator(vault: LoadedVault, repository: Repository, session: Any | None, feasible_refs: set[str]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 682) — Run the LEGACY scheduler weighted sum in shadow and record its outputs for comparison only (design §B4).
- `_run_shadow_scorers(scorers: Sequence[Callable[[cs.ControllerSnapshot, cs.Candidate | None], Any]] | None, snapshot: cs.ControllerSnapshot, chosen: cs.Candidate | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 711) — Evaluate injected shadow scorers with ZERO authority (invariant 3).
- `_why_copy(intent: StagedIntent, block: AttentionBlock, chosen: cs.Candidate | None) -> str` ([source](../../../../../../src/learnloop/scheduling/staged_policy.py), line 1040) — Learner-facing 'why' comes from the staged reason + commitment, never the largest opaque score term (§3.3).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `module`; statically calls `StateSignals`, `ladder_eligibility`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `AttentionBlock`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `StateSignals`, `decide`, `ladder_eligibility`
- [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]] — imports `AttentionBlock`
- [[Reference/Modules/learnloop/scheduling/frame_constraints|learnloop.scheduling.frame_constraints]] — imports `module`; statically calls `AttentionBlock`
- [[Reference/Modules/learnloop/scheduling/interleaving|learnloop.scheduling.interleaving]] — imports `AttentionBlock`
- [[Reference/Modules/learnloop/scheduling/state_signals|learnloop.scheduling.state_signals]] — imports `module`; statically calls `StateSignals`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/curriculum/depth_transition|learnloop.curriculum.depth_transition]] — imports `module`; calls `commit_one_edge`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `module`; calls `ExclusionReason`, `Feasibility`, `FeasibilityReport`, `feasible_set`
- [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; calls `build_snapshot`, `persist_snapshot`
- [[Reference/Modules/learnloop/scheduling/controller_store|learnloop.scheduling.controller_store]] — imports `module`; calls `append_block_event`, `create_attention_block`, `decision_by_receipt_key`, `persist_decision`, `persist_shadow_prediction`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `rank_feasible`
- [[Reference/Modules/learnloop/scheduling/randomization_layer|learnloop.scheduling.randomization_layer]] — imports `module`; calls `epsilon_tiebreak`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `build_due_queue`; calls `build_due_queue`
- [[Reference/Modules/learnloop/scheduling/voi_forecasts|learnloop.scheduling.voi_forecasts]] — imports `module`; calls `forecast_enabled`, `record_rank_feasible_forecast`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `canonical_hash`; calls `canonical_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]], [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]], [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop/scheduling/dispersion|learnloop.scheduling.dispersion]], [[Reference/Modules/learnloop/scheduling/frame_constraints|learnloop.scheduling.frame_constraints]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
- [tests/test_constraint_engine.py](../../../../../../tests/test_constraint_engine.py) — direct import
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
  - `test_a_standing_decisions_persisted_trace_names_the_same_veto`
  - `test_constraint_emptied_feasible_set_is_a_veto`
  - `test_evsi_abstain_is_a_veto`
  - `test_ladder_stop_is_not_a_veto`
  - `test_ownership_only_emptying_is_not_a_veto`
- [tests/test_cross_seam_exposure.py](../../../../../../tests/test_cross_seam_exposure.py) — direct import
  - `test_assessment_reserve_not_poached_by_practice_at_plan_time`
- [tests/test_dispersion.py](../../../../../../tests/test_dispersion.py) — direct import
- [tests/test_evsi_staged_binding.py](../../../../../../tests/test_evsi_staged_binding.py) — direct import
- [tests/test_router_ladder_parity.py](../../../../../../tests/test_router_ladder_parity.py) — direct import
  - `test_a_short_circuited_block_fires_no_rung`
  - `test_the_fired_rung_is_the_rule_the_staged_policy_applies`
- [tests/test_router_staged_p2.py](../../../../../../tests/test_router_staged_p2.py) — direct import
  - `test_a_randomized_within_block_choice_logs_its_assignment_propensity`
  - `test_short_circuited_blocks_are_logged_as_the_learner_pick_or_the_continuation`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
  - `test_affect_check_precedes_depth_edge`
  - `test_decision_persists_snapshot_decision_candidates_and_block`
  - `test_decision_trace_is_complete`
  - `test_depth_progression_only_under_auto_within_envelope`
  - `test_high_shadow_score_cannot_resurrect_infeasible_candidate`
  - `test_legacy_comparator_is_logged_but_not_authority`
  - `test_no_feasible_activity_is_typed_stop`
  - `test_one_edge_discipline_and_u018_gate_off`
  - `test_planted_state_selects_expected_action`
  - `test_retry_after_commit_yields_same_decision`
  - `test_shadow_scorer_has_zero_authority`
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
  - `test_epsilon_tiebreak_seed_is_decision_specific`
  - `test_evsi_selector_ranks_only_within_feasible_set`
  - `test_evsi_stop_is_a_typed_stop_not_no_feasible_activity`
  - `test_randomize_refuses_static_fallback_seed_without_snapshot`
- [tests/test_staged_policy_short_session.py](../../../../../../tests/test_staged_policy_short_session.py) — direct import
  - `test_short_session_depth_edge_stops_if_it_cannot_fit`
  - `test_short_session_prefers_admitted_short_p1_patterns`
  - `test_short_session_retry_after_commit_is_idempotent`
  - `test_short_session_stops_honestly_when_nothing_fits`
  - `test_three_minute_activity_completes_a_session`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import

## Modification guidance

- Change staged policy policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/staged_policy.py](../../../../../../src/learnloop/scheduling/staged_policy.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
