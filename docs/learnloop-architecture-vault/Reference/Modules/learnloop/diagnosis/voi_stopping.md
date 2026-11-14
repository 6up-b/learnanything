---
title: "learnloop.diagnosis.voi_stopping"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/voi_stopping.py"
source_paths:
  - "src/learnloop/diagnosis/voi_stopping.py"
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
  - "learnloop.diagnosis.voi_stopping module"
  - "src/learnloop/diagnosis/voi_stopping.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.voi_stopping`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.voi_stopping` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: mvp-0.21 Part 1: four count caps lifted onto value of information.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py) |
| Source lines | 2494 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `voi_stopping_active(config: Any, site: str | None=None) -> bool` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 237) — True with the kill switch (and the site's sub-switch) on.
- `probe_lane_reads_diagnosis(config: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 249) — mvp-0.21 Part 2: the probe hypothesis lane reads the diagnosis overlay.
- `probe_lane_holds_out_pending(config: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 260)
- `class VoiSettings` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 266) — The multi-family EVSI study's three switches (``[voi_stopping]``, ``docs/reviews/evsi-multisim.md`` §6.1 ranks 1-3), read once per decision.
  - `from_config(cls, config: Any) -> 'VoiSettings'` (line 279; public)
  - `is_study_default(self, name: str) -> bool` (line 290; public)
- `class MinutesEstimate` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 302) — One candidate's expected minutes and where they came from.
  - `provenance(self) -> str` (line 310; public)
  - `as_dict(self) -> dict[str, Any]` (line 319; public)
- `unresolved_scope_for_label(label: str) -> tuple[str, str]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 366) — ``(scope, reason)`` of one hypothesis label for rank 4's loss: a persistent scope (``learner_state``, ``unknown``) is charged Part C's estimate; ``no_problem`` and ``knowledge_gap`` are not (the reason names why on the cell).
- `class VoiContext` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 381) — What one serving decision reads once: latencies, routes, loss tables.
  - `__init__(self, vault: Any, repository: Any) -> None` (line 388; internal)
  - `settings(self) -> VoiSettings` (line 400; public) — The study's switches from the vault's config.
  - `plausible_threshold(self) -> float` (line 408; public)
  - `_load_latencies(self) -> tuple[dict[str, list[float]], dict[str, list[float]]]` (line 414; internal)
  - `item_minutes(self, item: Any, *, authored_minutes: float | None=None) -> MinutesEstimate` (line 433; public) — The learner's expected minutes on ``item``.
  - `_route_rows(self) -> list[dict[str, Any]]` (line 465; internal)
  - `label_actions(self, labels: Iterable[str]) -> dict[str, str] | None` (line 473; public) — Each hypothesis label's effective repair, or None when any lacks a route.
  - `measured_loss(self) -> bool` (line 503; public) — EVSI calibration Part C's switch, ``evsi.measured_loss_enabled`` (off by default): the loss table also charges what leaving a cause unresolved costs later (the multi-family study's rank 4).
  - `loss_regime(self) -> str` (line 512; public)
  - `unresolved_minutes(self, labels: Iterable[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]` (line 515; public) — The decision's per-label unresolved-cost cell entries and the full estimate (for the receipt), read once per label set.
  - `unresolved_estimate(self, labels: Iterable[str]) -> dict[str, Any] | None` (line 542; public) — The measured unresolved cost a decision's table charged, or None in the minutes-only regime.
  - `loss_table(self, label_actions: Mapping[str, str]) -> AL.LossTable | None` (line 550; public) — ``action_loss.build_loss_table`` over hypothesis labels (one route per label).
  - `duration_sources(self, actions: Iterable[str]) -> dict[str, dict[str, Any]]` (line 592; public)
- `heuristic_parameters(minutes: MinutesEstimate, *, method: str, evsi_used: bool, settings: VoiSettings | None=None, lookahead_site: bool=True, loss_regime: str=LOSS_REGIME_MINUTES, unresolved_cost: Mapping[str, Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 675) — Every number the decision ran on, with its provenance: heuristic but the minutes, and the multi-family study's recommendations (``evsi_multisim``) where its switches are at their defaults.
- `class Candidate` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 735) — One possible next observation at a site.
- `class CandidateValue` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 763)
  - `continues(self) -> bool` (line 781; public)
  - `value_per_minute(self) -> float` (line 785; public)
  - `summary(self) -> dict[str, Any]` (line 788; public)
  - `as_dict(self) -> dict[str, Any]` (line 803; public)
- `class SiteDecision` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 814) — One value-of-information stop/continue decision at a site.
  - `value_for(self, ref: str) -> CandidateValue | None` (line 833; public)
  - `best(self) -> CandidateValue | None` (line 837; public)
  - `chosen(self) -> CandidateValue | None` (line 841; public) — The recommended next observation: the first candidate (in robust value-per-minute order) whose value pays for its minutes, or None.
  - `admits(self, ref: str) -> bool` (line 847; public)
  - `cap_comparison(self) -> str` (line 851; public) — How value compared with the former cap: ``agree``, ``earlier`` (value stopped where the cap would not) or ``later`` (value continued where the cap would have bound).
  - `as_dict(self, *, served_ref: str | None=None, served_by: Mapping[str, Any] | None=None, subject_ref: str | None=None) -> dict[str, Any]` (line 863; public) — The logged decision.
- `candidate_forecasts(decisions: Iterable[SiteDecision]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 923) — Every evaluated candidate's whole valuation (its likelihood rows, prior and minutes), economically rejected or not, for the prefilter receipt's content-addressed part (data capture A1, Codex review F3).
- `value_candidates(ctx: VoiContext, site: str, candidates: Sequence[Candidate], *, prior: Mapping[str, float], learning_object_id: str | None, former_cap: Mapping[str, Any], context: Mapping[str, Any] | None=None, evsi_enabled: bool=True) -> SiteDecision` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 988) — Value each candidate next observation and decide stop or continue.
- `with_robust_gate_counterfactual(decision: SiteDecision, verdict: str | None) -> SiteDecision` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1333) — The value decision with the robust completion gate's verdict as a counterfactual on its former-cap receipt (the study's rank 1): the gate did not run because value decides; ``verdict`` is what it would have said (``couldnt_reliably_distinguish``) or None.
- `former_cap(site: str, *, value: int, count: int) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1350) — The replaced cap's counterfactual: would it have bound at this decision?
- `information_candidate(ref: str, *, eig_nats: float, minutes: MinutesEstimate, predicted_correct: float | None=None, detail: Mapping[str, Any] | None=None, infeasible_reason: str | None=None) -> Candidate` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1363) — A candidate valued only through an adapter's EIG (no hypothesis members).
- `predictive_information(likelihood: Mapping[str, Mapping[str, float]], targets: Sequence[Mapping[str, Mapping[str, float]]], posterior: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1486) — The §7.4 predictive EIG of a check (rows ``likelihood``) about held-out ``targets`` under ``posterior``, in nats: ``H_prior - sum_o m(o) H_post(o)``.
- `class HypothesisChannel` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1528) — What one check tells about the learner's rival hypotheses: its likelihood rows ``P(E | H)`` over one hypothesis variable (``belief_key``, an open probe episode's locked set) with that variable's current belief.
  - `from_mapping(cls, body: Mapping[str, Any] | None, *, hypothesis_term: float) -> 'HypothesisChannel | None'` (line 1561; public) — ``{belief_key, prior, likelihood, objective, targets}`` (the scheduler's ``ScheduledItem.hypothesis_channel``), or None when it carries no information or the reward logged no hypothesis term.
  - `recomputes_predictive(self) -> bool` (line 1598; public) — The predictive objective with its held-out targets carried.
  - `standalone_nats(self) -> float` (line 1604; public) — The check's information at the current belief, under its objective.
  - `at(self, posterior: Mapping[str, float]) -> float` (line 1609; public) — The check's information (nats, its own objective) under ``posterior``.
  - `labelled(self) -> str` (line 1617; public) — How the conditional hypothesis term is computed, for the receipt.
  - `root(self) -> _Branches` (line 1628; public)
  - `information(self, branches: _Branches) -> float` (line 1631; public) — The check's information in nats (its own objective), expected over ``branches``: recomputed on each branch, never scaled.
  - `split(self, branches: _Branches) -> tuple[_Branches, bool]` (line 1637; public) — The posterior branches after this check's outcome, merged; the flag says whether coarser merging was needed (the bound was passed).
- `class InformationTerms` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1679) — One candidate's information as the selection reward decomposes it.
  - `from_reward_debug(cls, learning_object_id: str, debug: Mapping[str, Any] | None, *, total_nats: float | None=None, hypothesis_channel: Mapping[str, Any] | None=None) -> 'InformationTerms | None'` (line 1717; public) — The terms behind a scheduled item's ``reward_debug``, or None when the body is missing or does not reproduce ``total_nats``.
  - `lo_precision(self) -> float` (line 1773; public)
  - `hypothesis_conditioning(self) -> str` (line 1777; public)
  - `_hypothesis_nats(self, state: 'InformationState') -> float` (line 1784; internal)
  - `conditional_nats(self, state: 'InformationState') -> dict[str, float]` (line 1796; public) — This check's information given the checks already in ``state``.
- `class InformationState` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1820) — The belief the checks chosen so far are expected to leave behind.
  - `after(self, terms: InformationTerms) -> 'InformationState'` (line 1834; public)
- `class InformationEntry` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1867) — One check valued through the selection reward's information (no hypothesis members): a teach-back or a due project probe.
- `class GreedyAdmission` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1881) — Checks admitted one at a time, each valued conditionally on those already admitted; ``steps`` holds every step's decision (the last one is the stop, unless every candidate was admitted).
  - `step_for(self, ref: str) -> tuple[int, SiteDecision] | None` (line 1897; public) — The step that admitted ``ref``, else the final step (its stop).
  - `receipt_for(self, ref: str) -> dict[str, Any] | None` (line 1907; public)
  - `bodies(self) -> list[dict[str, Any]]` (line 1941; public)
- `greedy_information_admission(ctx: VoiContext, site: str, entries: Sequence[InformationEntry], *, cap_value: int, cap_count: int=0, context: Mapping[str, Any] | None=None, minutes_budget: float | None=None, max_item_minutes: float | None=None, preselected: Iterable[str]=(), preselected_reasons: Mapping[str, str] | None=None) -> GreedyAdmission` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1950) — Admit checks greedily, each valued conditionally on those already chosen.
- `not_in_plan_receipt(site: str, ref: str, why: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2097) — The receipt of a due check a plan refresh cannot take (Codex review of voi-v2, F10): ``why`` is ``skipped_in_this_plan``, ``answered_in_this_plan`` or ``outside_plan_universe``.
- `label_conditionals(conditionals: Mapping[str, Mapping[Any, float]], slot_map: Mapping[str, str], labels: Iterable[str]) -> dict[str, dict[Any, float]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2115) — ``{label: P(E | slot(label))}``: a card's slot rows keyed by episode label.
- `hypothesis_channel_body(belief_key: str, eligible: Any, posterior: Mapping[str, float], *, objective: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2131) — An in-episode probe's likelihood rows over its episode's hypotheses (``{belief_key, prior, likelihood, objective}``, plus ``targets`` on the predictive objective), the input of :meth:`HypothesisChannel.from_mapping`: the instrument's composed ``P(E | H)`` keyed by episode label,…
- `probe_episode_decision(ctx: VoiContext, episode: Any, eligible: Sequence[Any], posterior: Mapping[str, float], *, session_id: str | None, familiarity: Mapping[str, float] | None=None) -> SiteDecision` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2168) — (a) Does this episode's next observation pay for its minutes?
- `record_followup_decision(repository: Any, *, attempt_id: str, learning_object_id: str, session_id: str | None, outcome: str, decision: Mapping[str, Any] | None, manual_override: bool, need_id: str | None, algorithm_version: str, clock: Any=None) -> str` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2266) — Append one follow-up value decision to its immutable receipt table.
- `record_offer_value_forecasts(vault: Any, repository: Any, *, slate_id: str, candidate_ids: Mapping[str, str], probe_decisions: Mapping[str, SiteDecision], teach_back_receipts: Sequence[Mapping[str, Any]], exploration_by_item: Mapping[str, Mapping[str, Any]] | None=None, clock: Any=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2314) — The value decisions a Today offer acted on, as EVSI calibration forecasts (``voi_forecasts``, behind ``evsi.forecast_logging``; logging only, never raises).
- `record_plan_value_forecasts(vault: Any, repository: Any, receipts: Sequence[Mapping[str, Any]], *, block_id: str, decision_ref: str | None, clock: Any=None) -> None` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2372) — A daily-plan block decision's due project probe receipts as EVSI calibration forecasts (``project_probe_value_decision``; logging only).
- `followup_receipts(repository: Any, attempt_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2408) — Every follow-up value decision on ``attempt_id``, in decision order.
- `followup_receipt(repository: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 2424) — The latest valued follow-up decision on ``attempt_id`` (its ``SiteDecision`` body), or None.

### Module constants

- `FORECAST_VERSION` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 136)
- `SITE_PROBE_EPISODE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 138)
- `SITE_FOLLOWUP` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 139)
- `SITE_TEACH_BACK` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 140)
- `SITE_PROJECT_PROBE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 141)
- `SITES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 142)
- `SITE_SWITCH` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 145)
- `FORMER_CAPS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 153)
- `EPISODE_MAXIMUM_CAP` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 164)
- `VOI_VALUE_SUPPRESSION` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 168)
- `VALUATION_SUPPRESSION_REASONS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 174)
- `CONTINUE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 176)
- `STOP` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 177)
- `METHOD_ROBUST_EVSI` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 178)
- `METHOD_EIG_VALUE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 179)
- `METHOD_LOOKAHEAD_PREFIX` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 181)
- `LOOKAHEAD_SITES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 187)
- `LOSS_REGIME_MINUTES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 196)
- `LOSS_REGIME_MEASURED` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 197)
- `REASON_EVSI_CLEARS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 200)
- `REASON_EVSI_BELOW` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 201)
- `REASON_EIG_CLEARS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 202)
- `REASON_EIG_BELOW` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 203)
- `REASON_EVSI_BATCH_CLEARS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 206)
- `ROBUST_GATE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 211)
- `ROBUST_GATE_SWITCH` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 212)
- `STUDY_PROVENANCE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 215)
- `STUDY_REFERENCE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 216)
- `MAX_RECORDED_CANDIDATES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 219)
- `DURATION_PSEUDO_OBSERVATIONS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 224)
- `DEFAULT_LATENCY_CAP_MINUTES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 227)
- `_ROUND_DIGITS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 229)
- `UNRESOLVED_NO_PROBLEM_LABELS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 352)
- `UNRESOLVED_GAP_LABELS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 353)
- `SCOPE_NO_PROBLEM` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 362)
- `SCOPE_KNOWLEDGE_GAP` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 363)
- `_VARIANCE_FLOOR` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1400)
- `_DEFAULT_FACET_VARIANCE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1402)
- `_RECONSTRUCTION_TOLERANCE` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1404)
- `_BRANCH_MERGE_DIGITS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1406)
- `_MAX_BELIEF_BRANCHES` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1410)
- `_COARSE_MERGE_DIGITS` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1412)
- `REASON_DOES_NOT_FIT` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1416)
- `REASON_ALREADY_PLANNED` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1420)
- `REASON_LEARNER_REQUEST` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1424)
- `REASON_NOT_IN_PLAN` ([src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1428)

### Explicit exports

`__all__` declares:

- `CONTINUE`
- `LOOKAHEAD_SITES`
- `LOSS_REGIME_MEASURED`
- `LOSS_REGIME_MINUTES`
- `UNRESOLVED_GAP_LABELS`
- `UNRESOLVED_NO_PROBLEM_LABELS`
- `unresolved_scope_for_label`
- `METHOD_LOOKAHEAD_PREFIX`
- `REASON_EVSI_BATCH_CLEARS`
- `REASON_LEARNER_REQUEST`
- `REASON_NOT_IN_PLAN`
- `ROBUST_GATE`
- `ROBUST_GATE_SWITCH`
- `VoiSettings`
- `with_robust_gate_counterfactual`
- `EPISODE_MAXIMUM_CAP`
- `VALUATION_SUPPRESSION_REASONS`
- `VOI_VALUE_SUPPRESSION`
- `probe_episode_decision`
- `Candidate`
- `CandidateValue`
- `FORECAST_VERSION`
- `FORMER_CAPS`
- `GreedyAdmission`
- `HypothesisChannel`
- `InformationEntry`
- `InformationState`
- `InformationTerms`
- `METHOD_EIG_VALUE`
- `METHOD_ROBUST_EVSI`
- `MinutesEstimate`
- `REASON_ALREADY_PLANNED`
- `REASON_DOES_NOT_FIT`
- `SITES`
- `SITE_FOLLOWUP`
- `SITE_PROBE_EPISODE`
- `SITE_PROJECT_PROBE`
- `SITE_TEACH_BACK`
- `STOP`
- `SiteDecision`
- `VoiContext`
- `followup_receipt`
- `followup_receipts`
- `record_offer_value_forecasts`
- `record_plan_value_forecasts`
- `former_cap`
- `greedy_information_admission`
- `heuristic_parameters`
- `candidate_forecasts`
- `hypothesis_channel_body`
- `information_candidate`
- `label_conditionals`
- `not_in_plan_receipt`
- `predictive_information`
- `probe_lane_holds_out_pending`
- `probe_lane_reads_diagnosis`
- `record_followup_decision`
- `value_candidates`
- `voi_stopping_active`

## Internal implementation anchors

- `_outcome_key(outcome: Any) -> str` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 605)
- `_keyed(member: Mapping[str, Mapping[Any, float]]) -> dict[str, dict[str, float]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 611)
- `_normalized(prior: Mapping[str, float], labels: Sequence[str]) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 622)
- `_predictive(member: Mapping[str, Mapping[Any, float]], prior: Mapping[str, float]) -> dict[Any, float]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 630)
- `_posterior(member: Mapping[str, Mapping[Any, float]], prior: Mapping[str, float], outcome: Any) -> dict[str, float]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 638)
- `_map_label(distribution: Mapping[str, float]) -> str | None` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 646)
- `_quantile_parameter(settings: VoiSettings) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 652)
- `_lookahead_parameter(settings: VoiSettings) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 667)
- `_forecast(member0: Mapping[str, Mapping[Any, float]], prior: Mapping[str, float], *, eig_nats: float, label_actions: Mapping[str, str] | None, loss_table: AL.LossTable | None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 935) — Predicted outcomes, the action after each, and P(action change).
- `_lookahead(values: list[CandidateValue], candidates: Sequence[Candidate], diagnostic: Sequence[EV.DiagnosticCandidate], rank: EV.RankResult, loss_table: AL.LossTable, settings: VoiSettings, *, record_all: bool=False) -> tuple[list[CandidateValue], dict[str, Any]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1201) — The multi-family study's lookahead (rank 2, ``evsi_multisim`` §6.1; ``evsi_calibration/policies.py:_paying_batch`` and ``decide_package``).
- `_clamp01(value: float) -> float` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1433)
- `_merge_branches(branches: Iterable[tuple[float, Mapping[str, float]]], digits: int) -> list[tuple[float, dict[str, float]]]` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1437) — Branches whose posteriors agree to ``digits`` places become one, with their total weight and their weighted mean posterior.
- `_entropy(distribution: Mapping[Any, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1459)
- `_targets_predictive_entropy(targets: Sequence[Mapping[str, Mapping[str, float]]], belief: Mapping[str, float]) -> float` ([source](../../../../../../src/learnloop/diagnosis/voi_stopping.py), line 1463) — Summed predictive outcome entropy of the held-out targets under ``belief`` (each target over the labels it has a row for, renormalized).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `FORECAST_VERSION`, `module`; statically calls `InformationEntry`, `MinutesEstimate`, `VoiContext`, `greedy_information_admission`, `not_in_plan_receipt`, `record_plan_value_forecasts`, `voi_stopping_active`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `SITE_FOLLOWUP`, `VOI_VALUE_SUPPRESSION`, `module`, `record_followup_decision`, `voi_stopping_active`; statically calls `Candidate`, `VoiContext`, `former_cap`, `record_followup_decision`, `value_candidates`, `voi_stopping_active`
- [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]] — imports `VALUATION_SUPPRESSION_REASONS`
- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `module`; statically calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `SITE_PROBE_EPISODE`, `VoiSettings`, `module`, `voi_stopping_active`; statically calls `VoiContext`, `probe_episode_decision`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `probe_lane_holds_out_pending`, `probe_lane_reads_diagnosis`; statically calls `probe_lane_holds_out_pending`, `probe_lane_reads_diagnosis`
- [[Reference/Modules/learnloop/scheduling/scheduler|learnloop.scheduling.scheduler]] — imports `module`; statically calls `InformationEntry`, `VoiContext`, `candidate_forecasts`, `greedy_information_admission`, `hypothesis_channel_body`, `probe_episode_decision`, `record_offer_value_forecasts`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `FORECAST_VERSION`

### Repository tooling consumers

- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `Candidate`, `MinutesEstimate`, `VoiContext`, `former_cap`, `label_conditionals`, `value_candidates`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/config/schema|learnloop.config.schema]] — imports `VoiStoppingConfig`; calls `VoiStoppingConfig`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `serving_on`; calls `serving_on`
- [[Reference/Modules/learnloop/db/stores/followup_value|learnloop.db.stores.followup_value]] — imports `decisions_for_attempt`, `insert_decision`; calls `decisions_for_attempt`, `insert_decision`
- [[Reference/Modules/learnloop/diagnosis/probe_families|learnloop.diagnosis.probe_families]] — imports `instrument_conditionals`; calls `instrument_conditionals`
- [[Reference/Modules/learnloop/diagnosis/probe_hypotheses|learnloop.diagnosis.probe_hypotheses]] — imports `triage_reason_for_label`; calls `triage_reason_for_label`
- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `instrument_ensemble`, `load_pinned_channel`; calls `instrument_ensemble`, `load_pinned_channel`
- [[Reference/Modules/learnloop/diagnosis/robust_composition|learnloop.diagnosis.robust_composition]] — imports `BURDEN_COST`, `LAMBDA_TIME`, `ROBUST_QUANTILE`, `VALUE_PER_NAT_MINUTES`, `expected_information_gain`, `robust_quantile`; calls `expected_information_gain`, `robust_quantile`
- [[Reference/Modules/learnloop/diagnosis/voi_forecasting|learnloop.diagnosis.voi_forecasting]] — imports `record_value_decision_forecast`; calls `record_value_decision_forecast`
- [[Reference/Modules/learnloop/scheduling/action_loss|learnloop.scheduling.action_loss]] — imports `module`; calls `attempt_minutes_by_intervention`, `build_loss_table`
- [[Reference/Modules/learnloop/scheduling/evsi|learnloop.scheduling.evsi]] — imports `module`; calls `DiagnosticCandidate`, `rank_feasible`, `robust_batch_evsi`
- [[Reference/Modules/learnloop/scheduling/unresolved_cost|learnloop.scheduling.unresolved_cost]] — imports `module`; calls `estimate_unresolved_cost`, `unresolved_minutes_for_scopes`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `math`, `statistics`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]], [[Reference/Modules/learnloop/diagnosis/gate_fit|learnloop.diagnosis.gate_fit]], [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] and 3 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a1_prefilter.py](../../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_a_plan_built_with_no_session_links_the_schedulers_gates_into_its_decision`
  - `test_a_voi_receipt_no_longer_truncates_candidates_to_six`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f3_a_build_with_no_valued_probe_keeps_no_forecasts`
  - `test_f3_every_evaluated_probe_keeps_its_forecast_in_the_receipt_only`
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_a_committed_probe_logs_its_value_decision_once_beside_the_selection_forecast`
  - `test_a_follow_up_decided_again_on_its_attempt_is_superseded`
  - `test_a_suppression_revokes_the_queue_and_administers_nothing`
  - `test_each_follow_up_value_decision_is_one_forecast`
  - `test_forecast_logging_off_records_no_value_decision`
  - `test_plan_blocks_log_project_probe_value_decisions_with_r1s_decision_ref`
  - `test_rank_four_off_prices_the_minutes_only_table_exactly`
  - `test_rank_four_on_charges_only_misconceptions_confusions_and_unknown_causes`
  - `test_rank_four_on_prices_the_decision_only_where_a_persistent_cause_is_at_stake`
  - `test_rank_four_reads_each_label_class_by_part_cs_definition`
  - `test_the_report_scores_a_queued_follow_up_through_its_receipt_and_offer`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_cheaper_follow_up_that_pays_is_queued_when_the_old_winner_does_not`
  - `test_a_need_then_a_queue_on_one_attempt_keeps_both_decisions`
  - `test_a_probe_the_plan_cannot_fit_neither_takes_a_slot_nor_discounts_another`
  - `test_a_project_probe_that_duplicates_an_admitted_one_is_not_admitted`
  - `test_a_project_probe_whose_value_does_not_pay_stays_later`
  - `test_a_second_teach_back_that_tells_the_same_thing_is_not_admitted`
  - `test_a_served_probe_records_its_probability_over_the_composed_queue`
  - `test_a_sole_teach_back_is_valued_and_receipted`
  - `test_a_teach_back_whose_value_does_not_pay_is_dropped_the_first_included`
  - `test_a_value_stop_ends_the_episode_only_with_the_switch_on`
  - `test_a_value_suppressed_follow_up_keeps_its_receipt`
  - `test_an_automatic_suppression_then_a_manual_follow_up_keeps_both_decisions`
  - `test_an_explored_probe_carries_its_own_forecast`
  - `test_at_the_successor_a_further_follow_up_is_queued_while_its_value_pays`
  - `test_at_the_successor_a_further_follow_up_whose_value_does_not_pay_is_suppressed`
  - `test_at_the_successor_value_keeps_asking_past_the_former_cap`
  - `test_at_the_successor_value_stops_an_episode_whose_next_observation_does_not_pay`
  - `test_each_follow_up_decision_keeps_its_own_receipt_through_rebuilds`
  - `test_every_decision_is_a_logged_forecast_with_heuristic_parameters`
  - `test_former_cap_counterfactuals`
  - `test_greater_certainty_never_restarts_an_unprofitable_measurement`
  - `test_greedy_admission_keeps_independent_checks_and_drops_a_repeat`
  - `test_hypothesis_information_is_valued_over_the_expected_posterior_branches`
  - `test_past_the_branch_bound_posteriors_merge_and_the_receipt_says_so`
  - `test_teach_backs_stay_while_their_conditional_value_pays`
  - `test_the_continue_decision_rides_on_the_committed_presentation_and_the_offer`
  - `test_the_first_follow_up_in_a_session_is_valued_too`
  - `test_the_plan_values_probes_on_one_episode_over_its_hypotheses`
  - `test_the_plan_values_project_probes_and_counts_them_with_the_switches_off`
  - `test_the_probe_lane_gate_needs_its_switch`
  - `test_the_scheduler_hands_an_in_episode_probe_its_likelihood_rows`
  - `test_the_value_gate_needs_the_switch_and_the_site`
  - `test_value_carries_one_episode_past_its_former_maximum`
  - `test_value_suppressions_never_label_the_trigger`
  - `test_where_routes_differ_robust_evsi_and_rank_feasibles_stop_rule_decide`
  - `test_with_no_routes_the_robust_eig_in_minutes_must_pay_for_the_minutes`
  - `test_with_the_switches_off_no_follow_up_receipt_carries_a_value_decision`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_batch_skips_a_check_that_shares_a_surface_with_a_better_ranked_one`
  - `test_a_lookahead_batch_is_built_from_distinct_surfaces`
  - `test_a_lookahead_batch_never_holds_two_checks_on_one_surface`
  - `test_a_probe_outside_the_plans_universe_does_not_suppress_one_inside`
  - `test_a_refresh_admits_against_the_minutes_left_and_conditions_on_planned_probes`
  - `test_a_skipped_probe_does_not_suppress_its_alternative_on_refresh`
  - `test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt`
  - `test_a_value_stop_records_the_gates_verdict_as_a_counterfactual`
  - `test_after_a_check_reveals_x_one_revealing_x_and_y_adds_no_predictive_information`
  - `test_each_switch_alone_moves_only_its_own_decisions`
  - `test_greedy_admission_never_runs_the_lookahead`
  - `test_migration_201_backfills_a_legacy_follow_up_receipt_once`
  - `test_project_probes_are_admitted_against_the_minutes_left_after_requests`
  - `test_rank_feasible_values_the_episode_at_the_configured_quantile`
  - `test_requested_probes_and_requests_share_one_request_rule`
  - `test_the_batch_value_equals_the_product_tables_evsi_on_the_real_credible_sets`
  - `test_the_greedy_admission_does_not_admit_a_check_whose_targets_are_already_known`
  - `test_the_lookahead_acts_at_probe_episodes_only`
  - `test_the_lookahead_does_not_run_when_a_single_check_pays_or_rank_abstains`
  - `test_the_lookahead_on_a_predictive_objective_episode_serves_the_incumbents_pick`
  - `test_the_lookahead_tries_three_checks_when_two_do_not_pay`
  - `test_the_predictive_information_matches_the_probe_episodes_own_objective`
  - `test_the_study_switches_default_to_the_recommendation`
  - `test_the_value_gate_reads_the_configured_robust_quantile`
  - `test_when_no_single_check_pays_a_paying_pair_continues_with_its_forecast`
- [tests/voi_restore_scenarios.py](../../../../../../tests/voi_restore_scenarios.py) — direct import
- [tests/voi_stopping_helpers.py](../../../../../../tests/voi_stopping_helpers.py) — direct import

## Modification guidance

- Change voi stopping policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/voi_stopping.py](../../../../../../src/learnloop/diagnosis/voi_stopping.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
