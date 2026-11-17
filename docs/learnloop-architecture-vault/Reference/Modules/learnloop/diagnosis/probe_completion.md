---
title: "learnloop.diagnosis.probe_completion"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_completion.py"
source_paths:
  - "src/learnloop/diagnosis/probe_completion.py"
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
  - "learnloop.diagnosis.probe_completion module"
  - "src/learnloop/diagnosis/probe_completion.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_completion`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_completion` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Completion policy for diagnostic episodes: decide when measurement ends.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_completion.py](../../../../../../src/learnloop/diagnosis/probe_completion.py) |
| Source lines | 684 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `persist_episode_beliefs(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 31) — Persist registry-misconception marginals to `learner_state_beliefs`.
- `evaluate_completion(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 66)
- `voi_probe_site_active(vault: LoadedVault) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 229)
- `value_decides_episode(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 235) — Does value of information decide this episode's next observation?
- `robust_gate_applies(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 255) — May the mvp-0.8 robust completion gate end this unstable episode?
- `episode_maximum_binds(vault: LoadedVault, repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 285) — Does ``probe.episode.maximum_observations`` (stamped on the episode at entry) end the episode by count?
- `robust_gate_counterfactual(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: Mapping[str, float]) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 344) — The robust completion gate's verdict for a value CONTINUE receipt (the multi-family EVSI study's rank 1): ``(applies, verdict)``.
- `robust_gate_completion(decision: Any, *, stop_only: bool) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 458) — The completion the robust gate's decision asks for: ``couldnt_reliably_distinguish`` or None.
- `close_diagnostic_segment(repository: Repository, episode_id: str, *, reason: str='converted_to_tutoring', clock: Clock | None=None) -> ProbeEpisodeRecord | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 635) — Close a still-open diagnostic episode when instruction/repair begins (P0 invariant 7 / §12.2 "starting instruction closes the measurement segment").
- `set_target_decision(repository: Repository, episode_id: str, decision: Mapping[str, Any], *, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 673)

## Internal implementation anchors

- `_latest_observation_session(repository: Repository, qualifying: Sequence[Mapping[str, Any]]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 274) — The session of the episode's latest qualifying observation (oldest first).
- `_plausible_actions_agree(repository: Repository, posterior: EpisodePosterior, episode_config) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 302) — True when every plausible hypothesis routes to one first intervention.
- `_robust_completion_override(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, *, record_forecast: bool=True) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 376) — The mvp-0.8 robust stop/abstain gate (§4.2).
- `_robust_gate_verdict(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, belief: Mapping[str, float], *, record_forecast: bool=False) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 403) — :func:`_robust_completion_override` on a posterior mapping (a counterfactual by default: nothing is logged unless ``record_forecast``).
- `_record_robust_selection_forecast(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, channel: Any, decision: Any, robust_candidates: Sequence[Any], posterior: Mapping[str, float], observations: int) -> None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 475) — EVSI calibration Part B: log the robust gate's forecast (logging only).
- `_surface_key(vault: LoadedVault, practice_item_id: str) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 516) — The independent-group key for a probe observation (augmentation §8).
- `_complete(repository: Repository, episode: ProbeEpisodeRecord, reason: str, *, posterior: EpisodePosterior | None=None, detail: Mapping[str, Any] | None=None, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 538)
- `_complete_on_value_stop(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, value_stop: Mapping[str, Any], *, clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 566) — Complete the episode on its value stop (the decision kept in ``completion_detail_json``) and log that stop as a forecast (``probe_episode_value_decision``, once per episode; EVSI calibration's ``voi_forecasts`` behind ``evsi.forecast_logging``, logging only).
- `_value_of_information_stop(vault: LoadedVault, repository: Repository, episode: ProbeEpisodeRecord, posterior: EpisodePosterior, qualifying: list[dict[str, Any]], candidates: list[EligibleInstrument], *, gate_counterfactual: Any=None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_completion.py), line 597) — mvp-0.21 (voi_stopping, site ``probe_episode``): the logged stop decision when the episode's next observation no longer pays for its minutes, or None (keep asking, or the site is off).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]] — imports `module`; statically calls `close_diagnostic_segment`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `episode_maximum_binds`, `evaluate_completion`, `persist_episode_beliefs`, `set_target_decision`; statically calls `episode_maximum_binds`, `evaluate_completion`, `persist_episode_beliefs`, `set_target_decision`
- [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]] — imports `set_target_decision`, `voi_probe_site_active`; statically calls `set_target_decision`, `voi_probe_site_active`
- [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]] — imports `close_diagnostic_segment`, `persist_episode_beliefs`; statically calls `close_diagnostic_segment`, `persist_episode_beliefs`
- [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] — imports `robust_gate_counterfactual`; statically calls `robust_gate_counterfactual`
- [[Reference/Modules/learnloop/evsi_calibration/policies|learnloop.evsi_calibration.policies]] — imports `robust_gate_completion`; statically calls `robust_gate_completion`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `robust_gate_counterfactual`; statically calls `robust_gate_counterfactual`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ProbeEpisodeRecord`, `Repository`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`; calls `calibration_cap_lifted`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `EpisodePosterior`, `_record_generation_need`, `eligible_instruments`; calls `_record_generation_need`, `eligible_instruments`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `strong_prior_claim`, `triage_reason_for_label`; calls `strong_prior_claim`, `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `robust_gate_fixes_on`, `robust_selection`; calls `RobustCandidate`, `instrument_ensemble`, `load_pinned_channel`, `robust_gate_fixes_on`, `robust_selection`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `record_robust_selection_forecast`, `record_value_decision_forecast`; calls `record_robust_selection_forecast`, `record_value_decision_forecast`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `SITE_PROBE_EPISODE`, `VoiSettings`, `module`, `voi_stopping_active`; calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/curriculum/golden_path_run|learnloop.curriculum.golden_path_run]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/probe_controls|learnloop.diagnosis.probe_controls]], [[Reference/Modules/learnloop/diagnosis/probe_evidence|learnloop.diagnosis.probe_evidence]], [[Reference/Modules/learnloop/diagnosis/probe_presentations|learnloop.diagnosis.probe_presentations]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/diagnosis_journey_helpers.py](../../../../../../tests/diagnosis_journey_helpers.py) — direct import
- [tests/test_independent_group_counting.py](../../../../../../tests/test_independent_group_counting.py) — direct import
  - `test_an_unknown_probe_item_stays_distinct_rather_than_collapsing`
  - `test_probe_completion_keys_on_the_group_not_the_authored_string`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_adopted_episode_that_completes_without_a_gap_opens_no_tutor`
- [tests/test_probe_robust_cutover.py](../../../../../../tests/test_probe_robust_cutover.py) — direct import
  - `test_evaluate_completion_abstains_on_planted_indistinguishable_case`
- [tests/test_robust_completion_gate.py](../../../../../../tests/test_robust_completion_gate.py) — direct import
  - `test_a_fragile_pick_does_not_end_the_episode_and_a_fragile_stop_does`
  - `test_without_the_fix_every_abstention_ends_the_episode`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
  - `test_robust_completion_override_logs_its_forecast`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt`

## Modification guidance

- Change probe completion policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_completion.py](../../../../../../src/learnloop/diagnosis/probe_completion.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
