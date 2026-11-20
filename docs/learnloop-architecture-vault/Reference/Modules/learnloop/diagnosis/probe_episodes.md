---
title: "learnloop.diagnosis.probe_episodes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_episodes.py"
source_paths:
  - "src/learnloop/diagnosis/probe_episodes.py"
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
  - "learnloop.diagnosis.probe_episodes module"
  - "src/learnloop/diagnosis/probe_episodes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_episodes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_episodes` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Adaptive diagnostic episode lifecycle, instruments, and posterior replay.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py) |
| Source lines | 1606 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EligibleInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 61) — One (item, compiled instrument) pair usable by the open episode.
  - `selection_components(self) -> dict[str, Any]` (line 96; public) — §7.3 separately-inspectable utility components for telemetry.
- `class EpisodePosterior` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 112)
  - `top(self) -> tuple[str, float]` (line 121; public)
- `episode_open_contract(vault: LoadedVault, repository: Repository, learning_object_id: str, *, trigger: str, goal_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 135) — What an episode opened now for ``trigger`` is held to: its observation budget, required facets, terminal-contract pin, calibration channel pin and algorithm version (the ``probe_episodes`` columns set at open).
- `enter_episode(vault: LoadedVault, repository: Repository, learning_object_id: str, *, trigger: str='initial', origin: str | None=None, goal_id: str | None=None, causal_factor_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, reserved_for: str | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 203) — Open a diagnostic episode with a fresh ULID and locked hypothesis set.
- `episode_has_observations(repository: Repository, episode_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 358) — True when this episode's locked hypothesis set has interpreted evidence.
- `retarget_episode_to_causal_factor(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, causal_factor_id: str, *, origin: str, clock: Clock | None=None, reserved_for: str | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 441) — Point an OBSERVATION-FREE open episode at a causal cause set.
- `adopt_ignored_opening_episode(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, trigger: str, origin: str | None, goal_id: str | None=None, clock: Clock | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 536) — Adopt an unanswered opening episode placement ignores (owner decision 2026-10-12).
- `maybe_reprobe_for_misconception(vault: LoadedVault, repository: Repository, learning_object_id: str, *, severity: float, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 642) — Re-probe trigger (§6.5): a new high-severity misconception opens a new episode with a new locked hypothesis-set snapshot.
- `maybe_reprobe_for_predictive_failure(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 662) — Re-probe trigger (§6.5/Checkpoint 2.7): repeated prediction errors indicate model misspecification.
- `enter_stale_uncertainty_reprobes(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[ProbeEpisodeRecord]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 710) — Periodic re-probe producer (§6.5): high uncertainty that persists after a completed episode re-enters probing with trigger ``stale_uncertainty``.
- `episode_hypothesis_set(repository: Repository, episode: ProbeEpisodeRecord) -> HypothesisSet | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 788)
- `administered_surface_exclusions(vault: LoadedVault, repository: Repository) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 802) — Surfaces the learner has already seen in ANY administration.
- `eligible_instruments(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None, posterior: Mapping[str, float] | None=None, reserved_for: str | None=None) -> list[EligibleInstrument]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 821) — Instruments admitted for this episode's locked set, ranked by EIG.
- `resolve_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> tuple[CompiledInstrument, dict[str, str]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1012) — The executable instrument binding this item to the locked set, if any.
- `compile_fallback_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> CompiledInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1083) — Legacy fallback instrument (§7.2): registry discrimination + IRT model.
- `episode_posterior(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None, held_attempt_ids: Iterable[str]=()) -> EpisodePosterior | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1141) — Replay the episode's evidence into the locked-set posterior.
- `probe_answer_admissibility(repository: Repository, *, probe_attempt_id: str | None, own_answer_rules: bool=False, read_at: str | None=None) -> ProductionAdmissibility | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1256) — Was the probe answer produced before anything was revealed to it?
- `answer_exposure(vault: LoadedVault, repository: Repository, attempt_id: str, *, recorded_at: str | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1320) — Why a probe answer was not an independent production, or None: the discriminating observation's exposure test (feedback shown before it, a recorded display of its causes, or a reveal in its window), from the evidence reading fixes (mvp-0.61) on, with the answer's own rules (:fun…
- `effective_episode_observations(vault: LoadedVault, repository: Repository, episode_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1341) — The episode's observation rows (``probe_observations_for_episode``, the held-grade view) as the episode reads them at the vault's tag.
- `effective_qualifying_total(vault: LoadedVault, repository: Repository, *, session_id: str | None=None) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1400) — Qualifying observations vault-wide, or in one session (``session_id``), as the episodes read them: the serving gates' counts (``probe_presentations.probe_serving_block_reason``: the onboarding ceiling and the session cap) and the value decision's former-cap count.
- `session_qualifying_total(vault: LoadedVault, repository: Repository, session_id: str | None) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1420) — :func:`effective_qualifying_total` for one session; none without a session (the value decision's former cap).
- `effective_posterior_as_of(vault: LoadedVault, repository: Repository, episode_id: str, now_iso: str) -> tuple[str, dict[str, float]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1426) — The episode's posterior as of ``now_iso`` where the tag reads its stored posteriors differently, as ``(as-of instant, posterior)``; None where the stored posteriors stand (below the evidence reading fixes, or no observation up to ``now_iso`` that the episode now reads as updatin…
- `effective_posterior_reader(vault: LoadedVault, repository: Repository) -> Any` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1475) — :func:`effective_posterior_as_of` bound to this vault, for a reader that cannot import this module (the router objective's sensor and decision state, which sit below diagnosis); None below the evidence reading fixes, where the stored posteriors stand.
- `qualifying_observation_count(vault: LoadedVault, repository: Repository, episode_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1487) — The episode's qualifying observations as the episode reads them (:func:`effective_episode_observations`).

### Module constants

- `FALLBACK_FAMILY_ID` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 56)
- `FALLBACK_FAMILY_VERSION` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 57)
- `_CONTRACT_COLUMNS` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 377)
- `ADOPTED_OPENING_EPISODE_KIND` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 533)
- `ANSWER_EXPOSED` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1314)
- `EXPOSURE_JUDGED` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1317)

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 128)
- `_relock_episode_row(repository: Repository, episode_id: str, *, hypothesis_set_id: str, origin: str | None, target_decision: Mapping[str, Any], clock: Clock | None, contract: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 390) — Point the row at the new set.
- `_open_episode_blocks(vault: LoadedVault, repository: Repository, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 626) — Whether an open episode already owns the LO for a re-probe trigger.
- `_record_generation_need(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 760)
- `_resolved_slot_map_from_snapshot(snapshot: Mapping[str, Any], instrument: CompiledInstrument, labels: list[str]) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1054) — Return the frozen selection-time label mapping for this presentation.
- `_reread_exposure(vault: LoadedVault, repository: Repository, observation: Any) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1389) — The exposure a reading at the tag finds in a stored observation that does not already record one: None for a row judged when it was written (:data:`EXPOSURE_JUDGED`, its verdict stands), else the persisted-rows judgment as of its own writing (:func:`answer_exposure` with ``recor…
- `_first_intervention_at(repository: Repository, episode: ProbeEpisodeRecord) -> Any` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1496)
- `_observation_likelihoods_from_row(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, attempt: Mapping[str, Any], observation_row: Mapping[str, Any]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1505)
- `_fired_error_types(repository: Repository, attempt_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1541)
- `_item_max_points(vault: LoadedVault, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1553)
- `_incidental_likelihoods(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], hypothesis_set: HypothesisSet) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1561)
- `_bayes_update(posterior: dict[str, float], likelihoods: Mapping[str, float], *, weight: float=1.0, prior_for_marginal: Mapping[str, float] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1586) — Weighted Bayes step: ``L_w = w·L + (1−w)·marginal`` dampens partially trusted evidence toward the mixture marginal (no update at w=0).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `episode_posterior`; statically calls `episode_posterior`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `effective_episode_observations`, `eligible_instruments`, `enter_episode`, `episode_posterior`; statically calls `effective_episode_observations`, `eligible_instruments`, `enter_episode`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/causal_discrimination|learnloop.diagnosis.causal_discrimination]] — imports `probe_answer_admissibility`; statically calls `probe_answer_admissibility`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `effective_episode_observations`, `module`; statically calls `effective_episode_observations`, `enter_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`; statically calls `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `episode_posterior`, `maybe_reprobe_for_predictive_failure`; statically calls `episode_posterior`, `maybe_reprobe_for_predictive_failure`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `maybe_reprobe_for_misconception`; statically calls `maybe_reprobe_for_misconception`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `_bayes_update`, `_observation_likelihoods_from_row`, `effective_episode_observations`, `episode_hypothesis_set`, `episode_posterior`; statically calls `_bayes_update`, `_observation_likelihoods_from_row`, `effective_episode_observations`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `EpisodePosterior`, `effective_episode_observations`, `eligible_instruments`, `episode_posterior`, `session_qualifying_total`; statically calls `effective_episode_observations`, `eligible_instruments`, `episode_posterior`, `session_qualifying_total`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `EligibleInstrument`, `EpisodePosterior`, `_record_generation_need`, `effective_episode_observations`, `eligible_instruments`, `session_qualifying_total`; statically calls `_record_generation_need`, `effective_episode_observations`, `eligible_instruments`, `session_qualifying_total`
- [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]] — imports `EligibleInstrument`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; statically calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `EligibleInstrument`, `episode_hypothesis_set`; statically calls `EligibleInstrument`, `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]] — imports `ANSWER_EXPOSED`, `EXPOSURE_JUDGED`, `_bayes_update`, `_entropy`, `_fired_error_types`, `_item_max_points`, `_resolved_slot_map_from_snapshot`, `answer_exposure`, `episode_hypothesis_set`, `episode_posterior`; statically calls `_bayes_update`, `_entropy`, `_fired_error_types`, `_item_max_points`, `_resolved_slot_map_from_snapshot`, `answer_exposure`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_hard_stops|learnloop.diagnosis.probe_hard_stops]] — imports `episode_has_observations`; statically calls `episode_has_observations`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `administered_surface_exclusions`, `eligible_instruments`; statically calls `administered_surface_exclusions`, `eligible_instruments`
- [[Reference/Modules/learnloop/diagnosis/probe_offer|learnloop.diagnosis.probe_offer]] — imports `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`; statically calls `eligible_instruments`, `enter_episode`, `retarget_episode_to_causal_factor`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `EligibleInstrument`, `_entropy`, `effective_qualifying_total`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `qualifying_observation_count`, `session_qualifying_total`; statically calls `_entropy`, `effective_qualifying_total`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `qualifying_observation_count`, `session_qualifying_total`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `administered_surface_exclusions`; statically calls `administered_surface_exclusions`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `effective_posterior_reader`; statically calls `effective_posterior_reader`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; statically calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `EligibleInstrument`, `EpisodePosterior`, `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `qualifying_observation_count`, `session_qualifying_total`; statically calls `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `qualifying_observation_count`, `session_qualifying_total`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `eligible_instruments`, `episode_posterior`; statically calls `eligible_instruments`, `episode_posterior`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `episode_hypothesis_set`, `episode_posterior`; statically calls `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `enter_episode`, `enter_stale_uncertainty_reprobes`; statically calls `enter_episode`, `enter_stale_uncertainty_reprobes`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `episode_hypothesis_set`; statically calls `episode_hypothesis_set`
- [[Reference/Modules/learnloop_sidecar/handlers/inspector|learnloop_sidecar.handlers.inspector]] — imports `ANSWER_EXPOSED`, `effective_episode_observations`; statically calls `effective_episode_observations`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `enter_episode`, `episode_hypothesis_set`; statically calls `enter_episode`, `episode_hypothesis_set`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `evidence_reading_fixes_on`; calls `evidence_reading_fixes_on`
- [[Reference/Modules/learnloop/attempts/reveal_ledger|learnloop.attempts.reveal_ledger]] — imports `ProductionAdmissibility`, `production_admissibility`; calls `ProductionAdmissibility`, `production_admissibility`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/probes|learnloop.db.stores.probes]] — imports `ProbeEpisodeRecord`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `lock_causal_hypothesis_set`; calls `lock_causal_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `CompiledInstrument`, `InstrumentCard`, `ProbeFamilyTemplate`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `shrunk_item_calibration_counts`, `validate_and_compile_card`; calls `CompiledInstrument`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `shrunk_item_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`, `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`; calls `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `applicable_families`, `generate_instances_for_episode`; calls `applicable_families`, `generate_instances_for_episode`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `resolve_episode_channel`; calls `resolve_episode_channel`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`; calls `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `door_sets`; calls `door_sets`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_entry`; calls `enqueue_entry`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `probe_answer_exposed`; calls `probe_answer_exposed`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `episode_ignored`; calls `episode_ignored`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `StagedOwnedAdministrationRefused`, `is_learning_object_staged_owned`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `learning_object_servable`; calls `learning_object_servable`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/objective_card|learnloop.daily_plan.objective_card]] and 27 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/due_queue_helpers.py](../../../../../../tests/due_queue_helpers.py) — direct import
- [tests/p2_acceptance_helpers.py](../../../../../../tests/p2_acceptance_helpers.py) — direct import
- [tests/probe_block_end_helpers.py](../../../../../../tests/probe_block_end_helpers.py) — direct import
- [tests/probe_episodes_helpers.py](../../../../../../tests/probe_episodes_helpers.py) — direct import
- [tests/probe_records_helpers.py](../../../../../../tests/probe_records_helpers.py) — direct import
- [tests/probe_robust_cutover_helpers.py](../../../../../../tests/probe_robust_cutover_helpers.py) — direct import
- [tests/router_probe_ties_helpers.py](../../../../../../tests/router_probe_ties_helpers.py) — direct import
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
  - `test_error_driven_episodes_still_open_under_placement`
- [tests/test_attempt_completion.py](../../../../../../tests/test_attempt_completion.py) — direct import
  - `test_block_closing_diagnostic_answer_keeps_grader_provenance`
  - `test_resumed_completion_routes_to_the_episode_the_attempt_was_applied_under`
  - `test_resumed_diagnostic_completion_evaluates_followups_after_its_episode_ended`
- [tests/test_causal_orchestrator.py](../../../../../../tests/test_causal_orchestrator.py) — direct import
  - `test_relocking_an_open_episode_does_not_inherit_its_evidence`
- [tests/test_causal_repair_sidecar_rpcs.py](../../../../../../tests/test_causal_repair_sidecar_rpcs.py) — direct import
  - `test_an_open_episode_with_observations_refuses_the_offer_with_a_typed_reason`
- [tests/test_characterization_probe_regrade.py](../../../../../../tests/test_characterization_probe_regrade.py) — direct import
  - `test_deferred_regrade_rewrites_summary_but_posterior_does_not_follow`
- [tests/test_characterization_probe_replay.py](../../../../../../tests/test_characterization_probe_replay.py) — direct import
  - `test_replay_pins_exact_posterior_under_current_default_policy`
  - `test_replay_rebuilds_from_current_grader_policy_not_a_pinned_snapshot`
- [tests/test_characterization_probe_submission.py](../../../../../../tests/test_characterization_probe_submission.py) — direct import
  - `test_composition_and_update_signatures_omit_grader_confidence`
  - `test_exact_posterior_update_for_uniform_prior`
  - `test_exact_posterior_update_with_weight_damping`
  - `test_posterior_delta_identical_across_grader_confidence_values`
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
  - `test_probe_dialogue_block_refuses_an_inactive_lo`
  - `test_probe_pool_is_empty_for_an_inactive_lo`
  - `test_stale_uncertainty_reprobe_does_not_reopen_an_inactive_lo`
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_fresh_diagnostic_probe_is_selectable_in_the_probe_episode_branch`
  - `test_probe_selection_hard_excludes_an_already_seen_surface_group`
- [tests/test_dual_authority_administration.py](../../../../../../tests/test_dual_authority_administration.py) — direct import
  - `test_staged_owned_item_never_surfaces_in_probe_slate`
  - `test_unowned_probe_slate_is_byte_identical`
  - `test_wholly_staged_owned_lo_refuses_probe_administration`
- [tests/test_evidence_reading_successor.py](../../../../../../tests/test_evidence_reading_successor.py) — direct import
  - `test_g3_1_an_exposed_answer_recorded_below_the_tag_updates_no_belief_after_the_upgrade`
  - `test_r1_a_stored_answer_reads_the_same_at_any_reading_time`
  - `test_r3_the_serving_counts_leave_out_an_exposed_answer`
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_the_mint_and_the_batch_write_the_identity_before_the_file`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_entry_enqueues_deduplicated_work_and_never_calls_a_model_inline`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_routine_selection_cannot_supersede_a_workflows_pin`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_evsi_report_realizes_no_outcome_from_a_held_attempt`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f11_a_held_probe_answer_moves_no_episode_posterior`
  - `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_probe_selection_offers_both_instruments`
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f15_the_probe_contract_carries_the_diagnostic_variant`
- [tests/test_mobile_v3_probes.py](../../../../../../tests/test_mobile_v3_probes.py) — direct import
- [tests/test_p2_acceptance.py](../../../../../../tests/test_p2_acceptance.py) — direct import
  - `test_starting_instruction_closes_measurement_segment_and_reentry_is_fresh`
- [tests/test_p2_leakage_suite.py](../../../../../../tests/test_p2_leakage_suite.py) — direct import
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_adopted_episode_that_completes_without_a_gap_opens_no_tutor`
  - `test_an_adopted_reprobe_is_held_to_the_reprobe_contract`
  - `test_an_error_driven_reprobe_adopts_an_ignored_episode`
  - `test_the_causal_quick_check_stops_the_episode_being_ignored`
- [tests/test_probe_audit.py](../../../../../../tests/test_probe_audit.py) — direct import
  - `test_regrade_checks_record_agreement_and_confusion`
  - `test_replay_audit_detects_a_self_consistent_but_wrong_posterior_transition`
  - `test_shadow_rankings_are_logged_and_reported`
- [tests/test_probe_block_end.py](../../../../../../tests/test_probe_block_end.py) — direct import
  - `test_block_end_payload_carries_open_set_evaluation`
  - `test_block_end_releases_feedback_and_routes_ordinary_practice`
  - `test_block_end_repair_consultation_is_idempotent`
  - `test_block_end_routes_diagnosed_gap_to_typed_tutoring_transition`
  - `test_continuing_episode_opens_fresh_segment_at_block_end`
  - `test_end_diagnostic_block_noop_on_terminal_episode`
  - `test_followup_and_normalization_defer_to_block_end`
  - `test_in_block_failure_gets_decision_receipt_at_block_end_not_before`
  - `test_open_set_trigger_fires_at_threshold_with_dedup`
  - `test_ordinary_attempt_outside_block_still_normalizes`
- [tests/test_probe_dialogue.py](../../../../../../tests/test_probe_dialogue.py) — direct import
  - `test_dialogue_observation_replays_to_its_persisted_weighted_posterior`
  - `test_dialogue_turns_persist_presentation_attempt_observation`
- [tests/test_probe_episode_conflict_one_check.py](../../../../../../tests/test_probe_episode_conflict_one_check.py) — direct import
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_consumed_presentation_cannot_qualify_second_attempt`
  - `test_declared_dont_know_keeps_probe_measurement_type`
  - `test_episode_entry_locks_actionable_set_with_open_set_mass`
  - `test_exam_attempts_do_not_advance_probe`
  - `test_exhausted_instrument_pool_parks_episode_with_generation_need`
  - `test_hinted_probe_attempt_is_contaminated_and_never_completes`
  - `test_item_excluded_from_live_slate_cannot_be_committed_as_a_probe`
  - `test_labels_map_through_open_set_abstention`
  - `test_multi_confusable_set_keeps_instrument_eligible`
  - `test_new_misconception_triggers_unique_reprobe_episode`
  - `test_next_probe_item_peeks_the_unused_surface_without_committing`
  - `test_ordinary_and_hinted_attempts_never_advance_but_update_belief`
  - `test_pending_items_episode_keeps_lo_schedulable_with_belief_updates`
  - `test_presentation_activity_disqualification_precedes_live_projection`
  - `test_presentation_snapshot_matches_compiled_instrument`
  - `test_qualifying_observations_are_counted_per_session`
  - `test_retried_submission_is_idempotent`
  - `test_scheduler_slate_atomically_commits_its_selected_probe_presentation`
  - `test_selected_diagnostic_probe_creates_exactly_one_observation`
  - `test_self_graded_provider_parks_episode_without_observation`
  - `test_stop_and_teach_ends_measurement_and_segments_evidence`
  - `test_two_independent_surfaces_complete_a_stable_episode`
  - `test_unmatched_systematic_signature_raises_open_set_probability`
- [tests/test_probe_hierarchy.py](../../../../../../tests/test_probe_hierarchy.py) — direct import
  - `test_resolve_instrument_reads_calibrated_rows`
- [tests/test_probe_instance_generation.py](../../../../../../tests/test_probe_instance_generation.py) — direct import
  - `test_approving_an_answered_probe_keeps_its_scheduling_state`
  - `test_generation_is_idempotent`
  - `test_provisional_family_instances_park_behind_review`
  - `test_trusted_family_generation_unparks_episode_with_provenance`
- [tests/test_probe_llm_instances.py](../../../../../../tests/test_probe_llm_instances.py) — direct import
  - `test_gate_rejected_llm_surfaces_fall_back_to_parametric`
  - `test_llm_surfaces_config_disable`
  - `test_llm_surfaces_generate_with_provenance`
  - `test_provider_failure_falls_back_to_parametric`
- [tests/test_probe_longform_families.py](../../../../../../tests/test_probe_longform_families.py) — direct import
  - `test_generation_produces_derivation_instance_with_obligation_rubric`
  - `test_longform_observation_records_trace_and_bounded_mass`
- [tests/test_probe_orchestration_remainder.py](../../../../../../tests/test_probe_orchestration_remainder.py) — direct import
  - `test_answer_confidence_is_logged_on_attempt_and_observation`
  - `test_onboarding_ceiling_deactivates_probes_until_practice_starts`
  - `test_planner_shadow_report_summarizes_logged_components`
  - `test_repeated_prediction_errors_reopen_probing`
  - `test_routine_planner_shadow_ranks_open_episodes`
  - `test_session_cap_blocks_further_probe_serving`
  - `test_stale_uncertainty_reprobe_after_configured_days`
  - `test_stale_uncertainty_respects_variance_floor`
- [tests/test_probe_policy.py](../../../../../../tests/test_probe_policy.py) — direct import
  - `test_family_redundancy_penalty_after_observation`
  - `test_sequential_selection_conditions_on_observed_posterior`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_never_authored_pool_is_distinguished_from_excluded_as_seen`
  - `test_pending_items_episode_with_fresh_surfaces_is_not_an_empty_pool`
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
  - `test_hypothesis_fallback_when_target_set_inadequate`
  - `test_predictive_objective_is_default_and_persisted`
- [tests/test_probe_records.py](../../../../../../tests/test_probe_records.py) — direct import
  - `test_a_late_completion_lists_only_evaluated_rules_in_order`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_administration_snapshots_probe_coarse_mapping`
  - `test_an_episode_opened_before_the_cutover_replays_on_the_point_path`
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`
  - `test_episode_pins_channel_and_products_are_deterministic`
  - `test_evaluate_completion_abstains_on_planted_indistinguishable_case`
  - `test_robust_selection_abstains_on_indistinguishable_candidates`
  - `test_selection_and_update_share_the_pinned_channel_hash`
- [tests/test_probe_router_authority.py](../../../../../../tests/test_probe_router_authority.py) — direct import
  - `test_j_a_generated_followups_block_ends_at_its_one_question_and_value_ends_any_other`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_no_probe_is_committed_for_an_item_submit_would_prime`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_a_probe_of_an_item_submit_would_prime_is_refused`
- [tests/test_sidecar_contract.py](../../../../../../tests/test_sidecar_contract.py) — direct import
  - `test_inspector_opens_probe_episode_drilldown`
- [tests/test_sidecar_probe.py](../../../../../../tests/test_sidecar_probe.py) — direct import
  - `test_get_next_probe_item_reflects_the_open_episode`
  - `test_probe_contract_requires_grading_provider_and_parks_episode`
  - `test_stop_probe_diagnosing_converts_episode`
- [tests/test_sidecar_tutor_qa.py](../../../../../../tests/test_sidecar_tutor_qa.py) — direct import
  - `test_preview_tutor_opening_after_stop_diagnosing`
- [tests/test_stuck_prompt.py](../../../../../../tests/test_stuck_prompt.py) — direct import
  - `test_an_empty_stuck_probe_answer_is_the_unanswered_observation`
- [tests/test_teach_handoff_stop_settles.py](../../../../../../tests/test_teach_handoff_stop_settles.py) — direct import
  - `test_a_mid_check_stop_normalizes_joint_answers_and_releases_their_feedback`
  - `test_a_mid_check_stop_queues_the_blind_answers_diagnosis`
  - `test_a_stop_with_nothing_committed_settles_nothing`
  - `test_the_calibration_dialogue_s_stop_settles_its_committed_turns`
- [tests/test_teacher_from_check.py](../../../../../../tests/test_teacher_from_check.py) — direct import
  - `test_the_stop_reports_its_episode_and_a_real_decision_reads_as_topic_words`
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1k_no_probe_is_committed_for_an_item_inside_routine_display_coverage`
  - `test_f1l_a_presentation_committed_before_a_display_is_not_served_inside_its_coverage`
  - `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged`
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
- [tests/test_value_candidates.py](../../../../../../tests/test_value_candidates.py) — direct import
  - `test_an_episode_with_no_pinned_channel_values_instruments_as_ordinary_items`
  - `test_an_instrument_only_request_matches_robust_selection`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_cli_calibration_reports_read_only`
  - `test_probe_selection_forecast_joins_its_realized_answer`
  - `test_robust_completion_override_logs_its_forecast`
  - `test_robust_gate_forecast_records_the_eig_paths_minutes`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_lookahead_batch_never_holds_two_checks_on_one_surface`
  - `test_the_batch_value_equals_the_product_tables_evsi_on_the_real_credible_sets`
  - `test_the_lookahead_on_a_predictive_objective_episode_serves_the_incumbents_pick`
  - `test_the_predictive_information_matches_the_probe_episodes_own_objective`
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change probe episodes policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
