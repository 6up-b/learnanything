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

`learnloop.diagnosis.probe_episodes` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Adaptive diagnostic episodes (spec_probe_eig_redesign.md §5/§7/§10/§11).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py) |
| Source lines | 3651 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class EligibleInstrument` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 83) — One (item, compiled instrument) pair usable by the open episode.
  - `selection_components(self) -> dict[str, Any]` (line 118; public) — §7.3 separately-inspectable utility components for telemetry.
- `class EpisodePosterior` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 134)
  - `top(self) -> tuple[str, float]` (line 143; public)
- `episode_open_contract(vault: LoadedVault, repository: Repository, learning_object_id: str, *, trigger: str, goal_id: str | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 157) — What an episode opened now for ``trigger`` is held to: its observation budget, required facets, terminal-contract pin, calibration channel pin and algorithm version (the ``probe_episodes`` columns set at open).
- `enter_episode(vault: LoadedVault, repository: Repository, learning_object_id: str, *, trigger: str='initial', origin: str | None=None, goal_id: str | None=None, causal_factor_id: str | None=None, clock: Clock | None=None, ai_client: object | None=None, reserved_for: str | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 228) — Open a diagnostic episode with a fresh ULID and locked hypothesis set.
- `episode_has_observations(repository: Repository, episode_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 383) — True when this episode's locked hypothesis set has interpreted evidence.
- `retarget_episode_to_causal_factor(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, causal_factor_id: str, *, origin: str, clock: Clock | None=None, reserved_for: str | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 466) — Point an OBSERVATION-FREE open episode at a causal cause set.
- `adopt_ignored_opening_episode(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, trigger: str, origin: str | None, goal_id: str | None=None, clock: Clock | None=None) -> ProbeEpisodeRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 561) — Adopt an unanswered opening episode placement ignores (owner decision 2026-10-12).
- `maybe_reprobe_for_misconception(vault: LoadedVault, repository: Repository, learning_object_id: str, *, severity: float, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 667) — Re-probe trigger (§6.5): a new high-severity misconception opens a new episode with a new locked hypothesis-set snapshot.
- `maybe_reprobe_for_predictive_failure(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 687) — Re-probe trigger (§6.5/Checkpoint 2.7): repeated prediction errors indicate model misspecification.
- `enter_stale_uncertainty_reprobes(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[ProbeEpisodeRecord]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 735) — Periodic re-probe producer (§6.5): high uncertainty that persists after a completed episode re-enters probing with trigger ``stale_uncertainty``.
- `episode_hypothesis_set(repository: Repository, episode: ProbeEpisodeRecord) -> HypothesisSet | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 813)
- `administered_surface_exclusions(vault: LoadedVault, repository: Repository) -> tuple[set[str], set[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 827) — Surfaces the learner has already seen in ANY administration.
- `eligible_instruments(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None, posterior: Mapping[str, float] | None=None, reserved_for: str | None=None) -> list[EligibleInstrument]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 846) — Instruments admitted for this episode's locked set, ranked by EIG.
- `resolve_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> tuple[CompiledInstrument, dict[str, str]] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1037) — The executable instrument binding this item to the locked set, if any.
- `compile_fallback_instrument(vault: LoadedVault, repository: Repository, item: PracticeItem, hypothesis_set: HypothesisSet) -> CompiledInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1108) — Legacy fallback instrument (§7.2): registry discrimination + IRT model.
- `shadow_selection_rankings(candidates: list[EligibleInstrument], *, top_k: int=3) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1166) — Alternative selection-policy rankings for shadow logging (§13.3).
- `class RoutineDisplayCovered(Exception)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1202) — A probe or placement presentation refused: the item's answer was shown, so it cannot test the learner (the one eligibility decision, ``serve_eligibility.decide(..., PROBE)``).
  - `__init__(self, practice_item_id: str, *, decision: object | None=None) -> None` (line 1210; internal)
- `probe_eligibility(repository: Repository, practice_item_id: str, *, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1226) — The one eligibility decision for a probe or placement presentation of the item now (``serve_eligibility``, request ``PROBE``).
- `routine_display_covers_item(repository: Repository, practice_item_id: str, *, clock: Clock | None=None, vault: LoadedVault | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1239) — Was the item's answer shown, so that no probe may test it now?
- `refuse_routine_display_covered(repository: Repository, practice_item_id: str, *, clock: Clock | None=None, vault: LoadedVault | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1261) — Raise :class:`RoutineDisplayCovered` when a probe of the item cannot test the learner now: the one guard every presentation commit (and serve) passes through.
- `commit_presentation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, supersede_active: bool=True, clock: Clock | None=None) -> ProbePresentationRecord` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1285) — Durably commit the selection before the item is returned to the client.
- `record_presentation_forecast(vault: LoadedVault, repository: Repository, presentation: ProbePresentationRecord, *, learning_object_id: str | None=None, candidate_count: int | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1342) — EVSI calibration Part B: log the forecast this probe selection ran on.
- `presentation_commit_payload(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, *, scheduler_candidate_id: str | None=None, extra_selection_components: Mapping[str, Any] | None=None, candidates: list[EligibleInstrument] | None=None, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1394) — Build the frozen presentation row before its owning transaction.
- `serve_presentation(repository: Repository, presentation_id: str, *, clock: Clock | None=None, vault: LoadedVault | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1517) — Mark a committed presentation served: the administration itself, and the only path to ``served``.
- `probe_serving_block_reason(vault: LoadedVault, repository: Repository, *, session_id: str | None=None, cap_lifted: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1540) — The §5.9 orchestration gate shared by every serving surface.
- `probe_value_block_reason(vault: LoadedVault, repository: Repository, episode: 'ProbeEpisodeRecord', practice_item_id: str, *, session_id: str | None=None, cap_lifted: bool=False) -> tuple[str | None, dict[str, Any] | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1577) — mvp-0.21 (voi_stopping, site ``probe_episode``): may this item be the episode's next observation?
- `commit_item_presentation(vault: LoadedVault, repository: Repository, episode: 'ProbeEpisodeRecord', item, hypothesis_set, *, extra_selection_components: Mapping[str, Any] | None=None, clock: Clock | None=None)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1626) — Commit and serve a presentation for one specific item.
- `plan_precommitted_block(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, block_size: int | None=None, clock: Clock | None=None) -> list[ProbePresentationRecord]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1664) — Greedy conditional/joint EIG for one precommitted block (Checkpoint 5.3).
- `class PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1818)
- `validate_presentation_for_submission(repository: Repository, presentation_id: str, *, practice_item_id: str, attempt_id: str | None=None, clock: Clock | None=None) -> PresentationValidation` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1825) — §5.4/§5.1 submission validation: active, same episode/item/segment, unexpired, unconsumed.
- `episode_posterior(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, *, hypothesis_set: HypothesisSet | None=None, held_attempt_ids: Iterable[str]=()) -> EpisodePosterior | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1869) — Replay the episode's evidence into the locked-set posterior.
- `record_episode_evidence(vault: LoadedVault, repository: Repository, *, learning_object_id: str, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str | None, grading_source: str, tutor_contaminated: bool=False, ai_client: object | None=None, grade_held_for_review: bool=False, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2100) — Post-persist accounting for one attempt on an in-episode LO.
- `record_presentation_activity_classification(vault: LoadedVault, repository: Repository, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool=False, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2180) — Persist presentation-derived eligibility before canonical projection.
- `dual_write_presentationless_probe_grade(vault: LoadedVault, repository: Repository, *, practice_item_id: str, attempt_id: str, grading_source: str, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2408) — The same fail-safe dual-write for a probe answer with no presentation and no instrument (teacher TE2's lesson probe, ``attempts.attempts._record_lesson_probe``): a raw grade event and calibrated interpretation on a diagnostic administration, so the canonical projection banks the…
- `dual_write_regraded_probe_grade(vault: LoadedVault, repository: Repository, *, attempt_id: str, grading_source: str, grader_identity: tuple[str, str] | None, fired_error_types: Iterable[str], held: bool, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2437) — A regrade's probe grade, published under the replacement grade's own identity (TE2 landing ruling R1).
- `persist_episode_beliefs(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2864) — Persist registry-misconception marginals to `learner_state_beliefs`.
- `voi_probe_site_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3055)
- `value_decides_episode(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3061) — Does value of information decide this episode's next observation?
- `robust_gate_applies(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3081) — May the mvp-0.8 robust completion gate end this unstable episode?
- `episode_maximum_binds(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3111) — Does ``probe.episode.maximum_observations`` (stamped on the episode at entry) end the episode by count?
- `robust_gate_counterfactual(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: Mapping[str, float]) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3170) — The robust completion gate's verdict for a value CONTINUE receipt (the multi-family EVSI study's rank 1): ``(applies, verdict)``.
- `stop_diagnosing_and_teach(vault: LoadedVault, repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3447) — `Stop diagnosing and teach me`: end measurement, open a post-intervention state segment, and persist a typed transition decision (§12.1).
- `close_diagnostic_segment(repository: Repository, episode_id: str, *, reason: str='converted_to_tutoring', clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3497) — Close a still-open diagnostic episode when instruction/repair begins (P0 invariant 7 / §12.2 "starting instruction closes the measurement segment").
- `abandon_episode(repository: Repository, learning_object_id: str, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3549)
- `episode_contract(vault: LoadedVault, repository: Repository, learning_object_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3573) — The probe UX contract for one LO, or None when no episode is active.
- `next_probe_item(vault: LoadedVault, repository: Repository, learning_object_id: str) -> EligibleInstrument | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3608) — The item that would be served next for this LO's open episode, or None.

### Module constants

- `FALLBACK_FAMILY_ID` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 69)
- `FALLBACK_FAMILY_VERSION` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 70)
- `PROBE_ASSISTANCE_RESTRICTIONS` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 73)
- `_CONTRACT_COLUMNS` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 402)
- `ADOPTED_OPENING_EPISODE_KIND` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 558)
- `PROBE_ITEM_ANSWER_SHOWN` ([src/learnloop/diagnosis/probe_episodes.py](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1223)

## Internal implementation anchors

- `_entropy(distribution: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 150)
- `_relock_episode_row(repository: Repository, episode_id: str, *, hypothesis_set_id: str, origin: str | None, target_decision: Mapping[str, Any], clock: Clock | None, contract: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 415) — Point the row at the new set.
- `_open_episode_blocks(vault: LoadedVault, repository: Repository, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 651) — Whether an open episode already owns the LO for a re-probe trigger.
- `_record_generation_need(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 785)
- `_resolved_slot_map_from_snapshot(snapshot: Mapping[str, Any], instrument: CompiledInstrument, labels: list[str]) -> dict[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1079) — Return the frozen selection-time label mapping for this presentation.
- `_robust_channel_pin(repository: Repository, episode: ProbeEpisodeRecord, eligible: EligibleInstrument, belief: Mapping[str, float]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1482) — The mvp-0.8 decision-time channel pin + robust product for the chosen candidate (§1.5/§2.1).
- `_first_intervention_at(repository: Repository, episode: ProbeEpisodeRecord) -> Any` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1984)
- `_observation_likelihoods_from_row(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, attempt: Mapping[str, Any], observation_row: Mapping[str, Any]) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 1993)
- `_fired_error_types(repository: Repository, attempt_id: str) -> list[str]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2029)
- `_item_max_points(vault: LoadedVault, practice_item_id: str) -> int` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2041)
- `_incidental_likelihoods(vault: LoadedVault, repository: Repository, attempt: Mapping[str, Any], hypothesis_set: HypothesisSet) -> dict[str, float] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2049)
- `_bayes_update(posterior: dict[str, float], likelihoods: Mapping[str, float], *, weight: float=1.0, prior_for_marginal: Mapping[str, float] | None=None) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2074) — Weighted Bayes step: ``L_w = w·L + (1−w)·marginal`` dampens partially trusted evidence toward the mixture marginal (no update at w=0).
- `_presentation_contamination(*, attempt_type: str, hints_used: int, tutor_contaminated: bool) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2231)
- `_record_presentation_activity_fact(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, presentation: ProbePresentationRecord, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, tutor_contaminated: bool, clock: Clock | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2246)
- `_robust_observation_snapshot(repository: Repository, episode: ProbeEpisodeRecord, instrument: CompiledInstrument, slot_map: Mapping[str, str], posterior_before: Mapping[str, float], *, observed_outcome: str, grader_confidence: float | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2292) — The mvp-0.8 decision-time posterior snapshot for one observation (§4.2).
- `_dual_write_probe_grade(vault: LoadedVault, repository: Repository, *, instrument: CompiledInstrument | None=None, practice_item_id: str, attempt_id: str, grading_source: str, observed_outcome: str, grader_identity: tuple[str, str] | None=None, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2325) — P0.2 dual-write for probe submissions (§4.1, §7.2).
- `_record_presentation_observation(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, hypothesis_set: HypothesisSet, *, attempt_id: str, practice_item_id: str, attempt_type: str, hints_used: int, probe_presentation_id: str, grading_source: str, tutor_contaminated: bool, grade_held_for_review: bool=False, grader_identity: tuple[str, str] | None=None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2519)
- `_attempt_rubric_score(repository: Repository, attempt_id: str) -> int | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2781)
- `_assess_longform_trace(vault: LoadedVault, repository: Repository, presentation: ProbePresentationRecord, instrument: CompiledInstrument, *, attempt_id: str, practice_item_id: str, attempt_type: str)` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2788) — Assess the §8.2 structured trace for a long-form response, or None when the presentation's card declares no obligations (microprobes).
- `_observation_features(repository: Repository, presentation: ProbePresentationRecord, *, attempt_id: str, structured_trace: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2836) — Logged-only observation features (§7.1): answer confidence, latency (both submitted and derived from presentation timestamps), and the §8.2 structured trace.
- `_evaluate_completion(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 2902)
- `_latest_observation_session(repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3100) — The session of the episode's latest qualifying observation (oldest first).
- `_plausible_actions_agree(repository: Repository, posterior: EpisodePosterior, episode_config) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3128) — True when every plausible hypothesis routes to one first intervention.
- `_robust_completion_override(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, record_forecast: bool=True) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3202) — The mvp-0.8 robust stop/abstain gate (§4.2).
- `_robust_gate_verdict(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, belief: Mapping[str, float], *, record_forecast: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3229) — :func:`_robust_completion_override` on a posterior mapping (a counterfactual by default: nothing is logged unless ``record_forecast``).
- `_record_robust_selection_forecast(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, channel: Any, decision: Any, robust_candidates: Sequence[Any], posterior: Mapping[str, float], observations: int) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3284) — EVSI calibration Part B: log the robust gate's forecast (logging only).
- `_surface_key(vault: LoadedVault, practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3325) — The independent-group key for a probe observation (augmentation §8).
- `_complete(repository: Repository, episode: ProbeEpisodeRecord, reason: str, *, posterior: EpisodePosterior | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3347)
- `_complete_on_value_stop(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, value_stop: Mapping[str, Any], *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3375) — Complete the episode on its value stop (the decision kept in ``completion_detail_json``) and log that stop as a forecast (``probe_episode_value_decision``, once per episode; EVSI calibration's ``voi_forecasts`` behind ``evsi.forecast_logging``, logging only).
- `_value_of_information_stop(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, qualifying: list[dict[str, Any]], candidates: list[EligibleInstrument], *, gate_counterfactual: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3406) — mvp-0.21 (voi_stopping, site ``probe_episode``): the logged stop decision when the episode's next observation no longer pays for its minutes, or None (keep asking, or the site is off).
- `_set_target_decision(repository: Repository, episode_id: str, decision: Mapping[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_episodes.py), line 3535)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`; statically calls `dual_write_presentationless_probe_grade`, `dual_write_regraded_probe_grade`, `record_episode_evidence`, `record_presentation_activity_classification`, `validate_presentation_for_submission`
- [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]] — imports `episode_posterior`; statically calls `episode_posterior`
- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; statically calls `close_diagnostic_segment`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `eligible_instruments`, `enter_episode`, `episode_posterior`; statically calls `eligible_instruments`, `enter_episode`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `RoutineDisplayCovered`, `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`, `routine_display_covers_item`; statically calls `commit_presentation`, `eligible_instruments`, `enter_episode`, `episode_has_observations`, `retarget_episode_to_causal_factor`, `routine_display_covers_item`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_pack|learnloop.diagnosis.diagnostic_pack]] — imports `module`; statically calls `enter_episode`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`; statically calls `_record_generation_need`, `administered_surface_exclusions`, `episode_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `episode_posterior`, `maybe_reprobe_for_predictive_failure`; statically calls `episode_posterior`, `maybe_reprobe_for_predictive_failure`
- [[Reference/Modules/learnloop/diagnosis/misconceptions|learnloop.diagnosis.misconceptions]] — imports `maybe_reprobe_for_misconception`; statically calls `maybe_reprobe_for_misconception`
- [[Reference/Modules/learnloop/diagnosis/probe_audit|learnloop.diagnosis.probe_audit]] — imports `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`; statically calls `_bayes_update`, `_observation_likelihoods_from_row`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `EpisodePosterior`, `_evaluate_completion`, `_set_target_decision`, `eligible_instruments`, `episode_maximum_binds`, `episode_posterior`, `persist_episode_beliefs`; statically calls `_evaluate_completion`, `_set_target_decision`, `eligible_instruments`, `episode_maximum_binds`, `episode_posterior`, `persist_episode_beliefs`
- [[Reference/Modules/learnloop/diagnosis/probe_dialogue|learnloop.diagnosis.probe_dialogue]] — imports `EligibleInstrument`, `RoutineDisplayCovered`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`; statically calls `EligibleInstrument`, `commit_presentation`, `episode_hypothesis_set`, `serve_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `administered_surface_exclusions`, `eligible_instruments`; statically calls `administered_surface_exclusions`, `eligible_instruments`
- [[Reference/Modules/learnloop/followup_run/admission|learnloop.followup_run.admission]] — imports `administered_surface_exclusions`; statically calls `administered_surface_exclusions`
- [[Reference/Modules/learnloop/instructional/valuation|learnloop.instructional.valuation]] — imports `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`; statically calls `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `EligibleInstrument`, `EpisodePosterior`, `RoutineDisplayCovered`, `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`, `robust_gate_counterfactual`; statically calls `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`, `robust_gate_counterfactual`
- [[Reference/Modules/learnloop/sim/diagnostic_validation|learnloop.sim.diagnostic_validation]] — imports `RoutineDisplayCovered`, `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`; statically calls `commit_presentation`, `eligible_instruments`, `episode_posterior`, `serve_presentation`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `episode_hypothesis_set`, `episode_posterior`; statically calls `episode_hypothesis_set`, `episode_posterior`
- [[Reference/Modules/learnloop/substrate/state_sync|learnloop.substrate.state_sync]] — imports `enter_episode`, `enter_stale_uncertainty_reprobes`; statically calls `enter_episode`, `enter_stale_uncertainty_reprobes`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `probe_value_block_reason`, `stop_diagnosing_and_teach`; statically calls `commit_item_presentation`, `episode_contract`, `episode_hypothesis_set`, `probe_serving_block_reason`, `probe_value_block_reason`, `stop_diagnosing_and_teach`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `PROBE_ITEM_ANSWER_SHOWN`, `RoutineDisplayCovered`, `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`; statically calls `commit_item_presentation`, `enter_episode`, `episode_contract`, `episode_hypothesis_set`, `next_probe_item`, `probe_serving_block_reason`, `probe_value_block_reason`, `routine_display_covers_item`, `serve_presentation`, `stop_diagnosing_and_teach`, `validate_presentation_for_submission`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grade_resolution|learnloop.attempts.grade_resolution]] — imports `record_grade_dual_write`; calls `record_grade_dual_write`
- [[Reference/Modules/learnloop/attempts/outcome_schemas|learnloop.attempts.outcome_schemas]] — imports `BUILTIN_SCHEMAS`, `COARSE_RESPONSE_SLUG`
- [[Reference/Modules/learnloop/causal_activity_policy|learnloop.causal_activity_policy]] — imports `LESSON_PROBE_EVIDENCE_ORIGIN`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `ProbePresentationRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`; calls `calibration_cap_lifted`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `near_clone_from_selection_components`; calls `near_clone_from_selection_components`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `lock_causal_hypothesis_set`; calls `lock_causal_hypothesis_set`
- [[Reference/Modules/learnloop/diagnosis/longform_trace|learnloop.diagnosis.longform_trace]] — imports `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`; calls `assess_trace`, `classify_trace_outcome`, `obligations_from_bindings`, `outcomes_from_grading_evidence`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`; calls `_first_error_from_block`, `block_complete`, `block_observation_rows`, `build_typed_transition_decision`, `end_diagnostic_block`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `APPROVED_DIAGNOSTIC_GRADING_SOURCES`, `CompiledInstrument`, `InstrumentCard`, `ProbeFamilyTemplate`, `SELECTION_POLICY_VERSION`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`; calls `CompiledInstrument`, `classify_outcome`, `ensure_builtin_families`, `information_rate`, `instrument_expected_information_gain`, `instrument_observation_likelihoods`, `instrument_predictive_information_gain`, `map_episode_labels_to_slots`, `record_real_observation_counts`, `shrunk_item_calibration_counts`, `validate_and_compile_card`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `H_OTHER`, `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`; calls `build_episode_hypothesis_set`, `generic_bucket_marginals`, `item_observation_context`, `strong_prior_claim`, `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probe_instance_generation|learnloop.diagnosis.probe_instance_generation]] — imports `applicable_families`, `generate_instances_for_episode`; calls `applicable_families`, `generate_instances_for_episode`
- [[Reference/Modules/learnloop/diagnosis/probe_outcome_mapping|learnloop.diagnosis.probe_outcome_mapping]] — imports `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`; calls `coarse_class_for_outcome`, `coarse_schema_slug`, `mapping_snapshot`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`; calls `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `pinned_decision_posterior`, `resolve_episode_channel`, `robust_selection`, `use_robust_probe`
- [[Reference/Modules/learnloop/diagnosis/probe_targeting|learnloop.diagnosis.probe_targeting]] — imports `open_cause_sets_for_learning_object`, `select_discriminating_instrument`; calls `open_cause_sets_for_learning_object`, `select_discriminating_instrument`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`; calls `HypothesisSet`, `item_registry_discrimination`, `resolve_item_irt`, `score_bucket`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `robust_eig_per_second`; calls `robust_eig_per_second`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `record_probe_presentation_forecast`, `record_robust_selection_forecast`, `record_value_decision_forecast`; calls `record_probe_presentation_forecast`, `record_robust_selection_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `SITE_PROBE_EPISODE`, `VoiSettings`, `module`, `voi_stopping_active`; calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop/followup_serve/gates|learnloop.followup_serve.gates]] — imports `generate_and_serve_on`; calls `generate_and_serve_on`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `door_sets`; calls `door_sets`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_entry`; calls `enqueue_entry`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `required_facets`; calls `required_facets`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `GRADE_HELD_FOR_REVIEW`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `episode_ignored`; calls `episode_ignored`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `routine_displays_covering`; calls `routine_displays_covering`
- [[Reference/Modules/learnloop/scheduling/controller_ownership|learnloop.scheduling.controller_ownership]] — imports `module`; calls `StagedOwnedAdministrationRefused`, `is_learning_object_staged_owned`, `staged_owned_practice_item_ids`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `decide`, `decision_active`, `gather`, `log_decision`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `learning_object_servable`; calls `learning_object_servable`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]], [[Reference/Modules/learnloop/curriculum/confusable_concepts|learnloop.curriculum.confusable_concepts]], [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]], [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] and 16 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/due_queue_helpers.py](../../../../../../tests/due_queue_helpers.py) — direct import
- [tests/p2_acceptance_helpers.py](../../../../../../tests/p2_acceptance_helpers.py) — direct import
- [tests/probe_block_end_helpers.py](../../../../../../tests/probe_block_end_helpers.py) — direct import
- [tests/probe_episodes_helpers.py](../../../../../../tests/probe_episodes_helpers.py) — direct import
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
- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f3_the_mint_and_the_batch_write_the_identity_before_the_file`
- [tests/test_followup_generate_e2e.py](../../../../../../tests/test_followup_generate_e2e.py) — direct import
  - `test_entry_enqueues_deduplicated_work_and_never_calls_a_model_inline`
- [tests/test_followup_journey.py](../../../../../../tests/test_followup_journey.py) — direct import
  - `test_a_routine_selection_cannot_supersede_a_workflows_pin`
- [tests/test_grade_resolution_pipeline.py](../../../../../../tests/test_grade_resolution_pipeline.py) — direct import
  - `test_probe_dual_write_helper_records_diagnostic_grade`
- [tests/test_held_grade_composition.py](../../../../../../tests/test_held_grade_composition.py) — direct import
  - `test_the_evsi_report_realizes_no_outcome_from_a_held_attempt`
- [tests/test_held_grade_evidence.py](../../../../../../tests/test_held_grade_evidence.py) — direct import
  - `test_f11_a_held_probe_answer_moves_no_episode_posterior`
  - `test_review_f3_diagnostic_observations_held_by_a_regrade_qualify_nothing`
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_an_unknown_probe_item_stays_distinct_rather_than_collapsing`
  - `test_probe_completion_keys_on_the_group_not_the_authored_string`
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
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_budget_exhaustion_completes_episode`
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
  - `test_precommitted_block_commits_all_before_answers`
  - `test_sequential_selection_conditions_on_observed_posterior`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_never_authored_pool_is_distinguished_from_excluded_as_seen`
  - `test_pending_items_episode_with_fresh_surfaces_is_not_an_empty_pool`
- [tests/test_probe_predictive_eig.py](../../../../../../tests/test_probe_predictive_eig.py) — direct import
  - `test_hypothesis_fallback_when_target_set_inadequate`
  - `test_predictive_objective_is_default_and_persisted`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
  - `test_remint_surface_group_stays_probe_ineligible`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_administration_snapshots_probe_coarse_mapping`
  - `test_decision_snapshot_byte_stable_after_model_activation_with_receipt`
  - `test_episode_pins_channel_and_products_are_deterministic`
  - `test_evaluate_completion_abstains_on_planted_indistinguishable_case`
  - `test_legacy_mvp07_episode_is_byte_identical`
  - `test_robust_selection_abstains_on_indistinguishable_candidates`
  - `test_selection_and_update_share_the_pinned_channel_hash`
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_mint_refuses_a_surface_group_the_learner_has_seen`
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_no_probe_is_committed_for_an_item_submit_would_prime`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f4_a_probe_of_an_item_submit_would_prime_is_refused_only_at_the_successor`
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
- [tests/test_teacher_te2_landing_r1.py](../../../../../../tests/test_teacher_te2_landing_r1.py) — direct import
  - `test_fg1s_presentation_path_stamps_the_submissions_identity_and_its_regrade_the_replacements`
- [tests/test_today_surfaces.py](../../../../../../tests/test_today_surfaces.py) — direct import
  - `test_overconfidence_probe_origin_survives_target_selection`
  - `test_overconfidence_probe_records_origin`
  - `test_probe_episode_without_origin_is_null`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1k_no_probe_is_committed_for_an_item_inside_routine_display_coverage`
  - `test_f1l_a_precommitted_block_stamps_its_surviving_members_size_and_indices`
  - `test_f1l_a_presentation_committed_before_a_display_is_not_served_inside_its_coverage`
  - `test_f1l_a_refused_causal_offer_leaves_the_episode_and_its_presentation_unchanged`
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
  - `test_f1l_the_sim_skips_a_covered_instrument_instead_of_aborting_the_run`
- [tests/test_value_candidates.py](../../../../../../tests/test_value_candidates.py) — direct import
  - `test_an_instrument_only_request_matches_robust_selection`
  - `test_below_the_robust_cutover_instruments_are_ordinary_items`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_cli_calibration_reports_read_only`
  - `test_probe_selection_forecast_joins_its_realized_answer`
  - `test_robust_completion_override_logs_its_forecast`
  - `test_robust_gate_forecast_records_the_eig_paths_minutes`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_a_committed_probe_logs_its_value_decision_once_beside_the_selection_forecast`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_at_the_successor_value_keeps_asking_past_the_former_cap`
  - `test_at_the_successor_value_stops_an_episode_whose_next_observation_does_not_pay`
  - `test_below_the_successor_the_new_switches_change_nothing`
  - `test_below_the_successor_the_spent_session_cap_blocks_probes`
  - `test_the_probe_contract_says_value_decides_only_at_the_successor`
  - `test_value_carries_one_episode_past_its_former_maximum`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_lookahead_batch_never_holds_two_checks_on_one_surface`
  - `test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt`
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
