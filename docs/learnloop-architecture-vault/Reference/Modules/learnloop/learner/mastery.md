---
title: "learnloop.learner.mastery"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/mastery.py"
source_paths:
  - "src/learnloop/learner/mastery.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Inspect Persistent State"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.learner.mastery module"
  - "src/learnloop/learner/mastery.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.mastery`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.mastery` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Per-LO mastery EKF (spec_irt_difficulty.md §4).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/mastery.py](../../../../../../src/learnloop/learner/mastery.py) |
| Source lines | 1051 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class MasteryObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 37)
- `class MasteryDisplay` ([source](../../../../../../src/learnloop/learner/mastery.py), line 76)
- `class IrtObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 85) — The 2PL link linearized at the prior mean (spec_irt_difficulty.md §4.1).
- `class MasteryObservationTrace` ([source](../../../../../../src/learnloop/learner/mastery.py), line 101) — Full IRT picture of one mastery update, for debug logging (spec §7.1).
- `sigmoid(value: float) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 130)
- `logit(value: float) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 134)
- `display_mastery(state: MasteryState) -> MasteryDisplay` ([source](../../../../../../src/learnloop/learner/mastery.py), line 139)
- `initial_mastery_state(learning_object_id: str, algorithm_version: str, now_iso: str, *, logit_variance: float=1.0) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 157)
- `claim_fixes_live(vault) -> bool` ([source](../../../../../../src/learnloop/learner/mastery.py), line 175) — LP-min (a): the claim-fixes successor's tag AND its kill switch.
- `replaced_claims_kept(vault) -> bool` ([source](../../../../../../src/learnloop/learner/mastery.py), line 193) — The successor mvp-0.36: the replace seam keeps a replaced claim (``superseded_by``).
- `after_what_they_replaced(claims: list[dict[str, Any]], keys: dict[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 218) — ``keys`` (claim id -> order key, or None for an unordered claim) with each replacing claim after what it replaced.
- `initial_mastery_state_for_learning_object(vault, repository, learning_object_id: str, now_iso: str, *, claims_made: Collection[str] | None=None) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 293) — The LO's prior: the cold start, or the covering claim's re-anchor.
- `apply_claim_evidence(state: MasteryState, *, claimed_level: float, prior_pseudo_count: float, now_iso: str, mean_only: bool=False) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 427) — Precision-weighted merge of a learner claim into an existing state.
- `reanchor_mastery_from_claim(vault, repository, learning_object_id: str, *, claimed_level: float, prior_pseudo_count: float, now_iso: str, claims_made: Collection[str] | None=None, claim_id: str | None=None) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 473) — Make a newly written claim take effect on an already-materialized LO.
- `replace_claim_and_reanchor(vault, repository, claim: dict[str, Any], *, clock=None) -> str` ([source](../../../../../../src/learnloop/learner/mastery.py), line 524) — The replace seam and the re-anchor of an LO-scoped learner report, as one write; the claim's id.
- `covering_learner_claim(vault, repository, learning_object_id: str, *, claims_made: Collection[str] | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/learner/mastery.py), line 584) — The one claim that seeds ``learning_object_id``'s prior, or None.
- `covering_claims(vault, repository, learning_object_id: str, *, include_superseded: bool=False) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 622) — Every learner claim in force that covers ``learning_object_id`` (any scope).
- `learning_objects_with_covering_claims(vault, repository, learning_object_ids) -> list[str]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 643) — The given LOs that at least one learner claim covers, sorted.
- `observation_weight(observation: MasteryObservation) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 723) — Reliability weight of an observation (spec §4.1).
- `predicted_logit_variance(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 744) — ``P_pred = min(P + sigma2_drift * days_since, p_max)`` — prior variance grown by drift.
- `item_irt_params(item: 'PracticeItem | None', learning_object: 'LearningObject | None', config: MasteryConfig) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 758) — Resolve ``(a, b)`` for an item from **static** authored/LLM fields (spec §4.3).
- `resolve_item_irt_params(item: 'PracticeItem | None', learning_object: 'LearningObject | None', config: MasteryConfig, item_state: 'ItemParameterState | None'=None) -> tuple[float, float]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 783) — (a, b) with the empirical-Bayes posterior b when enabled, else authored.
- `update_item_difficulty(prior: 'ItemParameterState | None', *, practice_item_id: str, authored_b: float, item_a: float, learner_mu_posterior: float, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, updated_at: str) -> 'ItemParameterState'` ([source](../../../../../../src/learnloop/learner/mastery.py), line 802) — Alternating conditional EKF step on item difficulty b.
- `irt_observation(item_a: float, item_b: float, prior: MasteryState, observation: MasteryObservation, config: MasteryConfig) -> IrtObservation` ([source](../../../../../../src/learnloop/learner/mastery.py), line 852) — Linearize the 2PL link at the prior mean (spec §4.1).
- `update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, *, item_a: float=1.0, item_b: float=0.0) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 888)
- `update_mastery_traced(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, *, item_a: float=1.0, item_b: float=0.0, item_id: str='') -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 903) — Difficulty-aware mastery update returning the posterior plus an IRT trace.

### Module constants

- `REANCHORING_CLAIM_SOURCES` ([src/learnloop/learner/mastery.py](../../../../../../src/learnloop/learner/mastery.py), line 288)

## Internal implementation anchors

- `_in_force(claims: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 206) — The claims among ``claims`` that no claim among them replaced (successor mvp-0.36).
- `_claim_seed(vault, claim: dict[str, Any], cold: MasteryState, now_iso: str, *, fixes: bool) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 354) — The zero-evidence state ``claim`` seeds.
- `_retained_cold_variance(vault, claims: list[dict[str, Any]], learning_object_id: str, cold: MasteryState, now_iso: str) -> float` ([source](../../../../../../src/learnloop/learner/mastery.py), line 384) — The largest variance a re-anchoring claim's seed left on the zero-evidence row (re-review F8).
- `_made_order(claim: dict[str, Any]) -> tuple[float, str]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 420) — A claim's place in the ``(created_at, id)`` order; an unparseable stamp sorts first.
- `_reanchor_in_transaction(vault, repository, learning_object_id: str, *, claimed_level: float, prior_pseudo_count: float, now_iso: str, claims_made: Collection[str] | None) -> MasteryState` ([source](../../../../../../src/learnloop/learner/mastery.py), line 555)
- `_claims_made(vault, repository, learning_object_id: str, claims_made: Collection[str] | None, *, fixes: bool) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 603) — The covering claims made by the caller's point: replay's ``claims_made``, else those in force now.
- `_winning_claim(claims: list[dict[str, Any]], *, fixes: bool) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/learner/mastery.py), line 637)
- `_claim_covers_learning_object(claim: dict[str, Any], learning_object) -> bool` ([source](../../../../../../src/learnloop/learner/mastery.py), line 663)
- `_claim_rank(claim: dict[str, Any]) -> tuple[int, float, float, str, str]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 677)
- `_parse_instant(value: Any) -> datetime | None` ([source](../../../../../../src/learnloop/learner/mastery.py), line 694)
- `_claim_rank_by_recency(claim: dict[str, Any]) -> tuple[int, float, float, str]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 701) — The claim-fixes successor's order: specificity, recency, pseudo-count.
- `_iso(value: datetime) -> str` ([source](../../../../../../src/learnloop/learner/mastery.py), line 719)
- `_ekf_update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, item_a: float, item_b: float, item_id: str) -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 924)
- `_legacy_update_mastery(prior: MasteryState, observation: MasteryObservation, config: MasteryConfig, algorithm_version: str, item_a: float, item_b: float, item_id: str) -> tuple[MasteryState, MasteryObservationTrace]` ([source](../../../../../../src/learnloop/learner/mastery.py), line 999) — The pre-IRT logit-space Kalman update, reproduced bit-for-bit (spec §6.2).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]] — imports `resolve_item_irt_params`; statically calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `MasteryObservation`, `MasteryObservationTrace`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`; statically calls `MasteryObservation`, `display_mastery`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `resolve_item_irt_params`, `update_item_difficulty`, `update_mastery_traced`
- [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]] — imports `MasteryObservation`, `irt_observation`, `logit`, `observation_weight`, `sigmoid`; statically calls `irt_observation`, `logit`, `observation_weight`, `sigmoid`
- [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]] — imports `initial_mastery_state_for_learning_object`, `learning_objects_with_covering_claims`; statically calls `initial_mastery_state_for_learning_object`, `learning_objects_with_covering_claims`
- [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] — imports `replace_claim_and_reanchor`; statically calls `replace_claim_and_reanchor`
- [[Reference/Modules/learnloop/content/authoring/practice_generation|learnloop.content.authoring.practice_generation]] — imports `covering_learner_claim`, `display_mastery`; statically calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/content/authoring/rung_variants|learnloop.content.authoring.rung_variants]] — imports `display_mastery`, `replace_claim_and_reanchor`; statically calls `display_mastery`, `replace_claim_and_reanchor`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; statically calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`; statically calls `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `covering_learner_claim`, `display_mastery`; statically calls `covering_learner_claim`, `display_mastery`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`; statically calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `sigmoid`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`; statically calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `resolve_item_irt_params`; statically calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/field/predictors|learnloop.field.predictors]] — imports `MasteryObservation`, `initial_mastery_state`, `update_mastery`; statically calls `MasteryObservation`, `initial_mastery_state`, `update_mastery`
- [[Reference/Modules/learnloop/field/priors|learnloop.field.priors]] — imports `initial_mastery_state_for_learning_object`; statically calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `covering_learner_claim`; statically calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/capability_grid|learnloop.learner.capability_grid]] — imports `covering_learner_claim`; statically calls `covering_learner_claim`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `MasteryObservation`, `item_irt_params`, `update_mastery`; statically calls `MasteryObservation`, `item_irt_params`, `update_mastery`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/placement/claim_check|learnloop.placement.claim_check]] — imports `claim_fixes_live`; statically calls `claim_fixes_live`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`; statically calls `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `resolve_item_irt_params`; statically calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `item_irt_params`; statically calls `item_irt_params`
- [[Reference/Modules/learnloop/sim/ad_synthetic|learnloop.sim.ad_synthetic]] — imports `MasteryObservation`, `display_mastery`, `initial_mastery_state`, `update_mastery`; statically calls `MasteryObservation`, `display_mastery`, `initial_mastery_state`, `update_mastery`
- [[Reference/Modules/learnloop/sim/metrics|learnloop.sim.metrics]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop/substrate/rebuild_orchestrator|learnloop.substrate.rebuild_orchestrator]] — imports `initial_mastery_state_for_learning_object`; statically calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/substrate/replay|learnloop.substrate.replay]] — imports `module`; statically calls `after_what_they_replaced`, `claim_fixes_live`, `covering_claims`, `initial_mastery_state_for_learning_object`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `initial_mastery_state_for_learning_object`; statically calls `initial_mastery_state_for_learning_object`
- [[Reference/Modules/learnloop/teacher/brief|learnloop.teacher.brief]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; statically calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/teacher/checks|learnloop.teacher.checks]] — imports `initial_mastery_state_for_learning_object`, `item_irt_params`; statically calls `initial_mastery_state_for_learning_object`, `item_irt_params`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `sigmoid`; statically calls `sigmoid`
- [[Reference/Modules/learnloop/tutor/promotions|learnloop.tutor.promotions]] — imports `claim_fixes_live`, `display_mastery`, `reanchor_mastery_from_claim`; statically calls `claim_fixes_live`, `display_mastery`, `reanchor_mastery_from_claim`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/graph|learnloop_sidecar.handlers.graph]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `display_mastery`, `sigmoid`; statically calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `display_mastery`; statically calls `display_mastery`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `display_mastery`, `sigmoid`; statically calls `display_mastery`, `sigmoid`
- [[Reference/Modules/learnloop_sidecar/handlers/vault|learnloop_sidecar.handlers.vault]] — imports `replaced_claims_kept`; statically calls `replaced_claims_kept`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `CLAIM_FIXES_VERSIONS`, `SUPERSEDED_CLAIMS_VERSIONS`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `MasteryConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ItemParameterState`, `MasteryState`; calls `ItemParameterState`, `MasteryState`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LearningObject`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/forecasters|learnloop.adaptive_difficulty.forecasters]], [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/attempts/surprise|learnloop.attempts.surprise]], [[Reference/Modules/learnloop/claim_fixes_upgrade|learnloop.claim_fixes_upgrade]], [[Reference/Modules/learnloop/content/authoring/item_authoring|learnloop.content.authoring.item_authoring]] and 37 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/rebuild_equivalence_helpers.py](../../../../../../tests/rebuild_equivalence_helpers.py) — direct import
- [tests/test_characterization_mastery_reliability.py](../../../../../../tests/test_characterization_mastery_reliability.py) — direct import
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_channel_doubt_never_inverts_direction_on_easy_items`
  - `test_evidence_rich_state_moves_less`
  - `test_interpretation_variance_broadens_not_blocks`
  - `test_quality_state_pays_for_assessment_side_error`
  - `test_soft_score_replaces_raw_fraction`
  - `test_zero_evidence_state_gets_full_merge_weight`
- [tests/test_evidence_config.py](../../../../../../tests/test_evidence_config.py) — direct import
  - `test_override_flows_through_resolvers`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_default_step_cap_leaves_normal_attempts_untouched`
  - `test_difficulty_defaults_to_zero_when_unset`
  - `test_difficulty_falls_back_to_learning_object_prior`
  - `test_difficulty_from_prior_toggle_pins_b_to_default`
  - `test_difficulty_is_clamped_to_b_abs_max`
  - `test_difficulty_resolves_practice_item_first`
  - `test_enabled_ekf_differs_from_legacy_on_target`
  - `test_kalman_gain_well_defined_at_extreme_difficulty`
  - `test_kill_switch_ignores_difficulty_entirely`
  - `test_kill_switch_reproduces_logit_kalman_math`
  - `test_mu_clamp_bounds_the_mean`
  - `test_step_cap_limits_overshoot_on_broad_prior`
  - `test_sustained_brutal_corrects_do_not_drift_past_mu_abs_max`
- [tests/test_item_parameters.py](../../../../../../tests/test_item_parameters.py) — direct import
  - `test_resolver_uses_posterior_only_when_enabled`
- [tests/test_learner_report_superseded.py](../../../../../../tests/test_learner_report_superseded.py) — direct import
  - `test_a_failure_between_the_replacement_and_its_re_anchor_leaves_the_earlier_report_in_force`
  - `test_a_new_starting_level_keeps_the_old_one_for_an_lo_first_practised_under_it`
  - `test_a_report_chain_longer_than_the_recursion_limit_replays_and_seeds`
  - `test_a_second_too_easy_report_keeps_the_first_as_a_replaced_row_that_no_live_reader_reads`
  - `test_after_what_they_replaced_handles_a_chain_longer_than_the_recursion_limit`
  - `test_after_what_they_replaced_moves_only_a_replacement_that_would_sort_first`
  - `test_below_the_tag_the_seam_still_deletes_the_replaced_claim`
  - `test_two_writers_on_one_warm_lo_apply_their_reports_in_the_order_replay_reads`
- [tests/test_lp_claim_fixes.py](../../../../../../tests/test_lp_claim_fixes.py) — direct import
  - `test_defect1_on_a_gap_declaration_reanchors_a_materialized_lo`
  - `test_defect2_on_a_claim_between_attempts_reanchors_between_them`
  - `test_defect3_apply_claim_evidence_mean_only_never_lowers_the_variance`
  - `test_defect4_off_the_predecessor_prefers_pseudo_count_then_the_higher_level`
  - `test_defect4_on_the_most_recent_claim_wins_then_pseudo_count_never_level`
  - `test_one_switch_on_by_default_classified_and_gated_by_the_tag`
- [tests/test_lp_claim_fixes_rereview.py](../../../../../../tests/test_lp_claim_fixes_rereview.py) — direct import
- [tests/test_lp_claim_fixes_review.py](../../../../../../tests/test_lp_claim_fixes_review.py) — direct import
  - `test_f1_a_concurrent_writer_cannot_land_between_the_gap_read_and_write`
  - `test_f4_a_gap_on_a_cold_lo_moves_the_mean_and_keeps_the_cold_variance`
  - `test_f4_off_the_predecessor_seed_variance_is_kept`
  - `test_f5_a_rung_request_claim_still_precedes_its_same_second_attempt`
- [tests/test_mastery.py](../../../../../../tests/test_mastery.py) — direct import
  - `test_display_mastery_formula`
  - `test_drift_increases_movement_after_long_gap`
  - `test_hint_dampening_reduces_update`
  - `test_low_confidence_moves_mean_less_than_high_confidence`
  - `test_positive_score_raises_mean`
  - `test_zero_score_does_not_raise_mean`
- [tests/test_planted_misgrade.py](../../../../../../tests/test_planted_misgrade.py) — direct import
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
- [tests/test_primed_attempts.py](../../../../../../tests/test_primed_attempts.py) — direct import
  - `test_cold_attempt_advances_last_evidence_at`
  - `test_primed_attempt_keeps_last_evidence_at_ekf`
  - `test_primed_attempt_keeps_last_evidence_at_legacy`
  - `test_primed_failure_moves_mean_more_than_cold_failure`
  - `test_primed_success_moves_mean_less_than_cold_success`
  - `test_primed_success_shrinks_variance_less`
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_seeds_from_weak_learner_claim_below_probe_threshold`
  - `test_state_sync_uses_strong_learner_claim_for_initial_mastery`
- [tests/test_surprise.py](../../../../../../tests/test_surprise.py) — direct import
- [tests/test_tutor_promotion_w2.py](../../../../../../tests/test_tutor_promotion_w2.py) — direct import
  - `test_high_claim_preserves_mean_and_respects_claim_variance_floor`
  - `test_low_claim_now_seeds_prior`
  - `test_no_claim_leaves_neutral_prior`
  - `test_very_high_claim_matches_native_logit_clamp`

## Modification guidance

- Change mastery policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/mastery.py](../../../../../../src/learnloop/learner/mastery.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
