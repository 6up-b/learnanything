---
title: "learnloop.diagnosis.probes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probes.py"
source_paths:
  - "src/learnloop/diagnosis/probes.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probes module"
  - "src/learnloop/diagnosis/probes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps probes behavior inside its owning package, [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]]. Its public surface centers on `Hypothesis`, `HypothesisSet`, `build_hypothesis_set`, `enter_probe`, `resolve_item_irt`, `self_tag_weight`, `ErrorTypeCandidate`, `rank_error_type_candidates` and 13 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py) |
| Source lines | 1571 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Hypothesis` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 41)
  - `channel_key(self) -> str | None` (line 52; public) — The error-dimension key this hypothesis owns in the outcome space (§3).
  - `as_record(self) -> dict[str, object]` (line 61; public)
- `class HypothesisSet` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 73)
  - `known_error_types(self) -> list[str]` (line 80; public) — Error-channel keys across the set: legacy error types and registry ids (§3).
  - `from_record(cls, record: dict) -> 'HypothesisSet'` (line 91; public)
- `build_hypothesis_set(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> HypothesisSet` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 112)
- `enter_probe(vault: LoadedVault, repository: Repository, learning_object_id: str, *, claimed_level: float | None=None, clock: Clock | None=None) -> HypothesisSet` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 251)
- `resolve_item_irt(vault: LoadedVault, item: PracticeItem) -> tuple[float, float, ProbeIRTConfig]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 298) — ``(a, b, ProbeIRTConfig)`` for an item — the same ``(a, b)`` Channel 1 uses.
- `self_tag_weight(vault: LoadedVault, item: PracticeItem, error_type: str, bucket: str, config: ProbeSelfTagConfig | None=None) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 359) — Trust weight ``w_self`` for a learner self-attached misconception (spec §12.3).
- `class ErrorTypeCandidate` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 402) — A ranked error-type suggestion for the self-grade misconception picker (§12.5).
- `rank_error_type_candidates(vault: LoadedVault, *, item: PracticeItem | None=None, learning_object_id: str | None=None, query: str | None=None, limit: int=10) -> list[ErrorTypeCandidate]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 422) — Rank the error-type taxonomy for the self-grade misconception picker (spec §12.5).
- `conditional_distribution(hypothesis: Hypothesis, *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None, fatal_error_ids: set[str], known_error_types: list[str], discrimination: dict[str, ItemMisconceptionDiscrimination] | None=None, discriminated_ids: set[str] | None=None) -> dict[Outcome, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 475) — ``P(score_bucket, error_type | h, item)`` under the difficulty-aware model.
- `item_registry_discrimination(repository: Repository, vault: LoadedVault, item: PracticeItem, rubric: Rubric | None, hypothesis_set: HypothesisSet) -> tuple[dict[str, ItemMisconceptionDiscrimination], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 641) — ``(discrimination_rows, discriminated_ids)`` for an item vs the set (spec §3).
- `hypothesis_conditionals(hypothesis_set: HypothesisSet, item: PracticeItem, rubric: Rubric | None=None, *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None, discrimination: dict[str, ItemMisconceptionDiscrimination] | None=None, discriminated_ids: set[str] | None=None) -> dict[str, dict[Outcome, float]]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 674) — ``{label: P(outcome | hypothesis)}`` for one item over a hypothesis set: the conditionals :func:`expected_information_gain` integrates over (and mvp-0.21's value of information forecasts with).
- `expected_information_gain(hypothesis_set: HypothesisSet, item: PracticeItem, rubric: Rubric | None=None, *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None, discrimination: dict[str, ItemMisconceptionDiscrimination] | None=None, discriminated_ids: set[str] | None=None) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 706)
- `facet_conditional_distribution(hypothesis_label: str, *, facet_id: str, candidate_facet_support: set[str], fatal_error_ids: set[str], known_error_types: list[str], item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None) -> dict[Outcome, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 750) — Per-facet diagnostic outcome model for v0.3 follow-up selection.
- `facet_expected_information_gain(hypothesis_marginal: dict[str, float], *, facet_id: str, candidate_facet_support: set[str], fatal_error_ids: set[str], item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 805) — Expected entropy drop for one facet marginal, in nats.
- `apply_facet_observation(hypothesis_marginal: dict[str, float], *, facet_id: str, candidate_facet_support: set[str], fatal_error_ids: set[str], observed_bucket: str, observed_error_type: str | None, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 860)
- `class ProbePosterior` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 905) — The hypothesis-set belief after replaying observed probe attempts.
  - `top_probability(self) -> float` (line 922; public)
- `score_bucket(rubric_score: int, max_points: int=4) -> str` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 926) — Bucketize on the legacy quarter-scale after ratio normalization.
- `probe_posterior(vault: LoadedVault, repository: Repository, learning_object_id: str, *, probe_state: ProbeStateRecord | None=None, hypothesis_set: HypothesisSet | None=None) -> ProbePosterior | None` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1147) — Replay probe-phase attempts into the hypothesis-set posterior.
- `current_hypothesis_set(vault: LoadedVault, repository: Repository, learning_object_id: str, *, probe_state: ProbeStateRecord | None=None) -> HypothesisSet | None` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1297) — The locked hypothesis set with its prior replaced by the live posterior.
- `persist_probe_beliefs(vault: LoadedVault, repository: Repository, learning_object_id: str, posterior: ProbePosterior, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1322) — Persist the misconception marginals of the posterior to `learner_state_beliefs`.
- `record_probe_attempt(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1363) — Advance an in-progress probe after an attempt on its Learning Object.

### Module constants

- `SCORE_BUCKETS` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 27)
- `_CONCEPT_CLOSENESS_HOP_DECAY` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 33)
- `_ULID_RE` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 37)
- `_BRIDGE_SENSITIVITY` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 583)
- `_BRIDGE_SPECIFICITY` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 584)
- `BRIDGE_SENSITIVITY` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 587)
- `BRIDGE_SPECIFICITY` ([src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py), line 588)

## Internal implementation anchors

- `_concept_graph_adjacency(vault: LoadedVault) -> dict[str, set[str]]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 310) — Undirected adjacency over the concept graph (all relation types).
- `_concept_closeness(adjacency: dict[str, set[str]], source_concept: str | None, related_concepts: list[str], hop_decay: float) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 320) — Hop-decay closeness from ``source_concept`` to its nearest related concept (§12.3).
- `_mean_concept_degree(adjacency: dict[str, set[str]], concept_count: int) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 352)
- `_fuzzy_match(query: str, text: str) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 412)
- `_graded_marginals(eta: float, cut_mid: float, cut_high: float) -> tuple[float, float, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 467) — Fixed 3-level graded score-bucket marginals (spec §5.2): ``(low, mid, high)``.
- `_fire_probabilities(fire_channel: str, discrimination: dict[str, ItemMisconceptionDiscrimination]) -> tuple[float, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 591) — ``(E[sens], E[spec])`` for the item's fire channel, with the bridge default.
- `_fire_overlay_distribution(hypothesis: Hypothesis, distribution: dict[Outcome, float], *, discriminated_ids: set[str], discrimination: dict[str, ItemMisconceptionDiscrimination], item_a: float, item_b: float, irt: ProbeIRTConfig) -> dict[Outcome, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 603) — Overlay the registry fire channel for a discriminating item (spec §3).
- `_entropy(distribution: dict[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 937)
- `_normalized_prior(distribution: dict[str, float]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 941)
- `_observation_likelihoods(hypothesis_set: HypothesisSet, item: PracticeItem, rubric: Rubric | None, bucket: str, error_type: str | None, *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None, self_tag_weight: float | None=None, discrimination: dict[str, ItemMisconceptionDiscrimination] | None=None, discriminated_ids: set[str] | None=None, fired_channel: str | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 949) — `P(observed | h, item)` per hypothesis for one attempt outcome.
- `_registry_observation_likelihoods(hypothesis_set: HypothesisSet, bucket: str, fired_channel: str | None, *, discrimination: dict[str, ItemMisconceptionDiscrimination], discriminated_ids: set[str], item_a: float, item_b: float, irt: ProbeIRTConfig | None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1030) — Fire-keyed observation on a discriminating item (spec §7).
- `_self_tag_likelihoods(hypothesis_set: HypothesisSet, bucket: str, error_type: str, fatal_error_ids: set[str], known_error_types: list[str], *, item_a: float, item_b: float, irt: ProbeIRTConfig | None, weight: float) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1073) — Trust-weighted *label* mixture ``L(h) = w·P_probe(s,E|h) + (1−w)·P_marg(s|h)`` (§12.2).
- `_resolve_self_tag_weight(vault: LoadedVault, item: PracticeItem, rubric: Rubric | None, hypothesis_set: HypothesisSet, error_type: str | None, bucket: str) -> float | None` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1122) — ``w_self`` for a self-attached misconception, or ``None`` for the standard path.
- `_apply_observation(hypothesis_set: HypothesisSet, item: PracticeItem, rubric: Rubric | None, bucket: str, error_type: str | None, posterior: dict[str, float], *, item_a: float=1.0, item_b: float=0.0, irt: ProbeIRTConfig | None=None, self_tag_weight: float | None=None, discrimination: dict[str, ItemMisconceptionDiscrimination] | None=None, discriminated_ids: set[str] | None=None, fired_channel: str | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1228)
- `_probe_phase_attempts(repository: Repository, learning_object_id: str, entered_at: str | None) -> list[dict[str, object]]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1273)
- `_fatal_error_ids(item: PracticeItem, rubric: Rubric | None=None) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1424)
- `_decay(created_at: str | None, now: datetime) -> float` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1431)
- `_lane_error_events(vault: LoadedVault, repository: Repository, learning_object_id: str | None) -> list[ActiveErrorEvent]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1439) — The active error events the probe hypothesis lane reads.
- `_neighbor_misconceptions(vault: LoadedVault, repository: Repository, concept_id: str, now: datetime) -> list[tuple[str, ActiveErrorEvent]]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1480)
- `_neighbor_registry_misconceptions(vault: LoadedVault, repository: Repository, concept_id: str, now: datetime) -> list[tuple[str, 'MisconceptionRecord']]` ([source](../../../../../../src/learnloop/diagnosis/probes.py), line 1526) — Registry rows on confusable-neighbor concepts, gated by neighbor mastery ≥ 0.7.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `rank_error_type_candidates`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `Hypothesis`, `HypothesisSet`; statically calls `Hypothesis`, `HypothesisSet`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `_BRIDGE_SENSITIVITY`, `_BRIDGE_SPECIFICITY`, `build_hypothesis_set`, `expected_information_gain`, `facet_expected_information_gain`, `hypothesis_conditionals`, `item_registry_discrimination`, `probe_posterior`, `resolve_item_irt`; statically calls `build_hypothesis_set`, `expected_information_gain`, `facet_expected_information_gain`, `hypothesis_conditionals`, `item_registry_discrimination`, `probe_posterior`, `resolve_item_irt`
- [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]] — imports `facet_conditional_distribution`; statically calls `facet_conditional_distribution`
- [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] — imports `apply_facet_observation`, `facet_conditional_distribution`, `resolve_item_irt`; statically calls `apply_facet_observation`, `facet_conditional_distribution`, `resolve_item_irt`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`; statically calls `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `Hypothesis`, `HypothesisSet`, `_decay`, `_graded_marginals`; statically calls `Hypothesis`, `HypothesisSet`, `_decay`, `_graded_marginals`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `facet_conditional_distribution`, `resolve_item_irt`; statically calls `facet_conditional_distribution`, `resolve_item_irt`
- [[Reference/Modules/learnloop/evsi_calibration/experiments|learnloop.evsi_calibration.experiments]] — imports `BRIDGE_SENSITIVITY`, `BRIDGE_SPECIFICITY`
- [[Reference/Modules/learnloop/evsi_calibration/live_report|learnloop.evsi_calibration.live_report]] — imports `score_bucket`; statically calls `score_bucket`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `build_hypothesis_set`; statically calls `build_hypothesis_set`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `Hypothesis`, `HypothesisSet`, `build_hypothesis_set`, `conditional_distribution`, `facet_conditional_distribution`, `item_registry_discrimination`, `resolve_item_irt`; statically calls `build_hypothesis_set`, `conditional_distribution`, `facet_conditional_distribution`, `item_registry_discrimination`, `resolve_item_irt`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `apply_facet_observation`; statically calls `apply_facet_observation`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `HypothesisSet`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `resolve_item_irt`; statically calls `resolve_item_irt`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `probe_posterior`; statically calls `probe_posterior`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `ProbeIRTConfig`, `ProbeSelfTagConfig`; calls `ProbeIRTConfig`, `ProbeSelfTagConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `ItemMisconceptionDiscrimination`, `MisconceptionRecord`, `ProbeStateRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `probe_lane_holds_out_pending`, `probe_lane_reads_diagnosis`; calls `probe_lane_holds_out_pending`, `probe_lane_reads_diagnosis`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`; calls `covering_learner_claim`, `initial_mastery_state_for_learning_object`, `item_irt_params`, `sigmoid`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`, `Rubric`, `discriminates`; calls `discriminates`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `difflib`, `math`, `re`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/forecast_receipts|learnloop.diagnosis.forecast_receipts]], [[Reference/Modules/learnloop/diagnosis/predictive_eig|learnloop.diagnosis.predictive_eig]] and 11 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_confusable_concepts.py](../../../../../../tests/test_confusable_concepts.py) — direct import
  - `test_repeated_probe_evidence_promotes_learner_observed_confusable`
  - `test_single_observation_does_not_promote_confusable`
- [tests/test_facet_diagnostics_v03.py](../../../../../../tests/test_facet_diagnostics_v03.py) — direct import
  - `test_facet_eig_is_zero_for_unsupported_candidate_and_positive_for_isolating_probe`
- [tests/test_hypothesis_sets.py](../../../../../../tests/test_hypothesis_sets.py) — direct import
  - `test_hypothesis_set_adds_active_misconception`
  - `test_hypothesis_set_always_has_mastered_and_unfamiliar`
  - `test_hypothesis_set_caps_and_drops_lowest_severity`
- [tests/test_irt_difficulty.py](../../../../../../tests/test_irt_difficulty.py) — direct import
  - `test_conditional_masses_match_spec_table_at_b_zero`
  - `test_eig_prefers_boundary_items_over_trivial_and_impossible`
  - `test_every_conditional_is_normalized`
  - `test_misconception_overlay_routes_error_fractions_exactly`
- [tests/test_irt_end_to_end.py](../../../../../../tests/test_irt_end_to_end.py) — direct import
  - `test_decisive_hard_correct_concentrates_posterior_more_than_trivial`
  - `test_hard_correct_completes_probe_on_hypothesis_convergence`
- [tests/test_misconception_registry.py](../../../../../../tests/test_misconception_registry.py) — direct import
  - `test_build_hypothesis_set_registry_and_legacy_coexist`
  - `test_build_hypothesis_set_skips_linked_legacy_event`
  - `test_discriminating_item_has_higher_eig`
  - `test_item_registry_discrimination_reads_rows`
- [tests/test_predictive_eig.py](../../../../../../tests/test_predictive_eig.py) — direct import
  - `test_single_target_data_processing_bound`
- [tests/test_probe_attempt_updates.py](../../../../../../tests/test_probe_attempt_updates.py) — direct import
  - `test_attempt_service_never_writes_legacy_probe_state`
  - `test_record_probe_attempt_completes_on_convergence`
  - `test_record_probe_attempt_does_not_converge_on_uninformative_prior`
  - `test_record_probe_attempt_increments_until_target`
  - `test_record_probe_attempt_is_noop_when_not_probing`
- [tests/test_probe_belief_posterior.py](../../../../../../tests/test_probe_belief_posterior.py) — direct import
  - `test_decisive_high_score_converges_early_on_hypothesis_family`
  - `test_dont_know_outcome_does_not_break_posterior`
  - `test_high_score_with_error_type_falls_back_to_bucket_marginal`
  - `test_low_score_with_misconception_shifts_posterior_and_persists_belief`
  - `test_mid_scores_run_probe_to_target_not_one`
  - `test_no_misconception_writes_no_belief_rows_but_updates_base_posterior`
  - `test_probe_posterior_is_idempotent`
  - `test_probe_posterior_none_when_not_probing`
  - `test_realized_information_gain_is_positive_for_informative_attempt`
  - `test_scheduler_eig_uses_live_posterior`
  - `test_score_bucket_boundaries`
  - `test_unknown_error_type_uses_bucket_marginal`
- [tests/test_probe_eig.py](../../../../../../tests/test_probe_eig.py) — direct import
  - `test_conditional_distribution_is_normalized_for_every_hypothesis`
  - `test_probe_hypothesis_set_ignores_transient_errors`
- [tests/test_probe_entry.py](../../../../../../tests/test_probe_entry.py) — direct import
  - `test_enter_probe_creates_in_progress_state_and_locked_hypothesis_set`
  - `test_enter_probe_is_deterministic`
  - `test_enter_probe_reduces_target_with_strong_claim`
- [tests/test_probe_migration.py](../../../../../../tests/test_probe_migration.py) — direct import
  - `test_legacy_probe_history_replays_identically_after_migration`
- [tests/test_self_attributed_misconceptions.py](../../../../../../tests/test_self_attributed_misconceptions.py) — direct import
  - `test_brand_new_self_tag_does_not_touch_current_posterior_but_seeds_next_set`
  - `test_candidate_ranking_fuzzy_query_surfaces_match`
  - `test_candidate_ranking_prefers_concept_relevant_misconception`
  - `test_concept_closeness_direct_one_hop_two_hop_and_disconnected`
  - `test_mixture_posterior_misconception_is_monotone_in_w`
  - `test_mixture_softly_downweights_mastered_without_eliminating_it`
  - `test_mixture_w0_reproduces_no_label_update_bit_for_bit`
  - `test_mixture_w1_equals_rubric_fatal_path`
  - `test_resolve_self_tag_weight_only_fires_for_in_set_non_fatal_label`
  - `test_self_tag_on_non_probing_item_credits_misconception`
  - `test_self_tag_replay_is_idempotent`
  - `test_self_tag_weight_consistency_gate_zeroes_high_bucket`
  - `test_self_tag_weight_dense_graph_close_neighbor_uses_closeness`
  - `test_self_tag_weight_dense_graph_genuine_mismatch_drops_to_zero`
  - `test_self_tag_weight_sparse_graph_falls_back_to_w_base`
  - `test_self_tag_weight_unlinked_endpoint_is_neutral`
- [tests/test_show.py](../../../../../../tests/test_show.py) — direct import
  - `test_show_inspects_every_deterministic_id`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import

## Modification guidance

- Change probes policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probes.py](../../../../../../src/learnloop/diagnosis/probes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
