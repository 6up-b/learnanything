---
title: "learnloop.scheduling.scheduler"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/scheduler.py"
source_paths:
  - "src/learnloop/scheduling/scheduler.py"
source_commit: "14bb2c615356cfabd9cf1c0e631e48b1ef153fd8"
source_commit_timestamp: "2026-11-03T03:24:48-05:00"
source_worktree_state: "clean"
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
  - "learnloop.scheduling.scheduler module"
  - "src/learnloop/scheduling/scheduler.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.scheduler`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

This module keeps scheduler behavior inside its owning package, [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]]. Its public surface centers on `SchedulerSession`, `ScheduledItem`, `ExplorationOutcome`, `OfferTrace`, `build_due_queue`, `probe_ties_admitted`, `cold_check_decision`, `apply_eligibility_writes` and 8 more public symbols.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py) |
| Source lines | 3727 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `14bb2c615356cfabd9cf1c0e631e48b1ef153fd8` |
| Commit timestamp | `2026-11-03T03:24:48-05:00` |

## Public API

- `class SchedulerSession` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 71)
- `class ScheduledItem` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 94)
- `class ExplorationOutcome` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 124) — One outcome of the seeded epsilon tie-break and the offer it composes to.
- `class OfferTrace` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 139) — What one queue build decided, for router decision logging (router R1).
- `build_due_queue(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None, session: SchedulerSession | None=None, limit: int | None=None, persist_explanations: bool=True, offer_trace: OfferTrace | None=None, device_filter: DeviceFilter | None=None) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 183)
- `probe_ties_admitted(config: LearnLoopConfig) -> bool` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 966) — Router R1's successor (``mvp-0.15``): probe near-ties join the tie-break.
- `cold_check_decision(vault: LoadedVault, repository: Repository, practice_item_id: str, *, clock: Clock | None=None, now_iso: str | None=None, learning_object_id: str | None=None)` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1619) — The one eligibility decision for serving the item's cold check now (``serve_eligibility.decide(..., COLD_CHECK)``): serve it, serve the item as ordinary practice (re-timing the due cold task), or defer it until a time-bounded hold lifts.
- `apply_eligibility_writes(vault: LoadedVault, repository: Repository, decision: Any, *, clock: Clock | None=None) -> None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1643) — Act on a cold-check decision's writes (the one eligibility decision's imperative shell): its re-times (monotone pushes of a time-bounded hold) and its withdrawals (a check the item can no longer take cold ends now, with its typed disposition: ``remediation.withdraw_cold_measurem…
- `cold_check_hold_until(vault: LoadedVault, repository: Repository, practice_item_id: str, *, clock: Clock | None=None, persist: bool=True) -> str | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1966) — When a cold check's hold lifts (ledger format), or None when it is not held: the one eligibility decision's ``defer_until`` (``serve_eligibility``).
- `cold_check_serve_hold(vault: LoadedVault, repository: Repository, practice_item_id: str, *, clock: Clock | None=None, persist: bool=True) -> str | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2059) — Revalidate a cold check at the moment it would be served (UX Phase 4, rounds 5 to 7; one eligibility decision): the reason it cannot be served AS the cold check now and must wait (the decision's reason code), or None when it is served, as the cold check or as practice with its c…
- `cold_check_serve_decision(vault: LoadedVault, repository: Repository, practice_item_id: str, *, clock: Clock | None=None, persist: bool=True)` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2085) — :func:`cold_check_decision` at a serve, with its writes applied (persisted when ``persist``: :func:`apply_eligibility_writes`) and its record logged.
- `deferred_cold_followups(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2120) — Live cold tasks currently held back because their answer was shown.
- `explain_practice_item(vault: LoadedVault, repository: Repository, practice_item_id: str) -> ScheduledItem | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2728)
- `dominant_scheduler_reason(components: dict[str, float], config: LearnLoopConfig) -> str` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2769) — Stable learner-facing reason from the same weighted ranking terms.
- `check_admission(vault: LoadedVault, repository: Repository, *, now: datetime, intent_view: Any, reasons: bool=False) -> Any` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3393) — The build's admission for a DL2 intent view built outside the queue (the plan's pool, the practice view, settling): the same predicate over the same reads, with no session and nothing written, each read on first use.
- `pool_admission(vault: LoadedVault, repository: Repository, *, now: datetime, item_states: Any=None) -> Any` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3406) — THE plan pool's per-item predicate asked of one item outside a queue build: ``refusal(item_id) -> reason | None``.

### Module constants

- `_CHECK_EXCLUDED_MODES` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1271)
- `SELECTION_POLICY` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1409)
- `UNAVAILABLE_PROPENSITY_KIND` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1414)
- `SELECTION_FEATURE_SCHEMA` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1420)
- `FOLLOWUP_REASONS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1537)
- `_INTERVENTION_FOLLOWUP_KINDS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1545)
- `REPAIR_JOURNEY_TASK_KINDS` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1564)
- `ANSWER_SHOWN_PRACTICE` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1954)
- `COLD_CHECK_ROUTINE_DISPLAY` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1958)
- `COLD_CHECK_HOLD_UNKNOWN_RELEASE` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 1963)
- `_COLD_DEFERRAL_REASON` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 2197)
- `_COLD_PRACTICE_REASON` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 2200)
- `_TEACH_BACK_PRIORITY_FLOOR` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 2421)
- `_REQUESTED_PRIORITY_FLOOR` ([src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py), line 2425)

## Internal implementation anchors

- `_is_probe_intent(item: ScheduledItem) -> bool` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 981)
- `_exploration_support(queue: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig) -> tuple[float, list[ScheduledItem]] | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 985) — The seeded epsilon tie-break's design: ``(rate, near-tie alternatives)``.
- `_explore_to_front(queue: list[ScheduledItem], selected: ScheduledItem, rate: float) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1022) — The order an exploration draw that chose ``selected`` produces.
- `_pin_presentation(queue: list[ScheduledItem], practice_item_id: str | None) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1045) — The committed presentation pin, without its invalidation side effect.
- `_exploration_draws(queue: list[ScheduledItem], session: SchedulerSession, now: datetime, alternatives: list[ScheduledItem]) -> tuple[float, float]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1058) — The seeded roll and choice fractions ``_apply_seeded_exploration`` uses.
- `_held_for_device(vault: LoadedVault, device_filter: DeviceFilter, practice_item_id: str, withheld: Any) -> bool` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1070) — The by-id ways into a build: a follow-up task, a committed presentation.
- `_fill_offer_trace(trace: OfferTrace, *, config: LearnLoopConfig, session: SchedulerSession, now: datetime, limit: int | None, greedy_queue: list[ScheduledItem], considered: list[ScheduledItem], compose, base_propensity: dict[str, float], pinned_item_id: str | None, probe_block_reason: str | None, cold_deferrals: list[dict[str, Any]], slate_id: str | None, candidate_ids: dict[str, str], placement_active: bool, session_context: dict[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1083) — Record the build's decision inputs and its exploration's whole support.
- `_support_outcomes(greedy_queue: list[ScheduledItem], support: tuple[float, list[ScheduledItem]], compose, pinned_item_id: str | None) -> list[ExplorationOutcome]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1184) — Every outcome of the seeded draw, each recomposed through ``compose`` (the live build's own composition, without audit writes) and the committed presentation pin: the greedy order (when ``1 - rate > 0``) first, then one outcome per near-tie alternative.
- `_composed_head_probability(practice_item_id: str, *, greedy_queue: list[ScheduledItem], considered: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig, compose, pinned_item_id: str | None) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1219) — ``P(practice_item_id heads the composed queue)`` over the seeded draw's whole support: each outcome recomposed exactly as the live build composes (router R1's offer-trace machinery), so a teach-back value dropped, a requested floor or a follow-up insertion is accounted for.
- `class _PlacementServing` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1251) — What learner-field F2 placement changes about one queue build.
- `_placement_serving(vault: LoadedVault, repository: Repository, *, clock: Clock | None, persist: bool, item_states: Mapping[str, PracticeItemState], excluded_item_ids: set[str]) -> _PlacementServing | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1274) — F2 placement state for one build, or None when placement is off.
- `_order_new_material(vault: LoadedVault, repository: Repository, queue: list[ScheduledItem], placement: _PlacementServing) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1360) — Reorder new-material items among the slots they already hold.
- `_selection_decision_features(vault: LoadedVault, item: PracticeItem, *, mastery_states: Mapping[str, MasteryState], facet_states_by_lo: Mapping[str, list[Any]], errors_by_lo: Mapping[str, list[ActiveErrorEvent]], quality_states: Mapping[str, PracticeItemQualityState], ability_by_lo: dict[str, dict[str, object]]) -> dict[str, object] | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1423) — Compact, immutable features for one considered candidate.
- `_practice_item_snapshot(item: PracticeItem) -> tuple[str, str]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1482) — Canonical JSON of the whole item and the SHA-256 of exactly that text.
- `_selection_ability_features(vault: LoadedVault, learning_object_id: str, *, mastery: MasteryState | None, facet_states: list[Any], active_errors: list[ActiveErrorEvent]) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1500) — The selector's ability vector plus the mastery summary behind it.
- `_cold_task_reveals(repository: Repository, *, item_id: str, learning_object_id: str | None, since: str, now_iso: str) -> list[tuple[dict[str, Any], str]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1567) — The reveals that hold a cold task back now, each with the first moment it no longer holds it (ledger format), oldest first.
- `_defer_revealed_cold_followups(vault: LoadedVault, repository: Repository, pending_followups: list[dict[str, str]], *, clock: Clock | None=None, persist: bool=True) -> tuple[list[dict[str, str]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1666) — The queue's cold lane: hold back, or withdraw, due cold tasks that cannot be served as cold checks now.
- `_predecessor_defer_revealed_cold_followups(vault: LoadedVault, repository: Repository, pending_followups: list[dict[str, str]], *, clock: Clock | None=None, persist: bool=True) -> tuple[list[dict[str, str]], list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 1814) — mvp-0.26's cold lane, kept exactly for the predecessor and the kill switch (``eligibility.enabled = false``): hold back due cold tasks whose answer has been revealed since creation.
- `_predecessor_cold_check_hold_until(vault: LoadedVault, repository: Repository, practice_item_id: str, *, clock: Clock | None=None, persist: bool=True) -> str | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2001) — mvp-0.26's serve-time hold, kept exactly for the predecessor and the kill switch: when a cold check's routine-display hold lifts (ledger format), or None when it is not held (UX Phase 4, rounds 5 to 7).
- `_merge_cold_deferral_explanations(vault: LoadedVault, explanations: list[dict[str, Any]], deferrals: list[dict[str, Any]], readiness_factor: float | None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2203) — Mark every deferred cold task in the slate, exactly once per item.
- `_deferral_components(deferral: Mapping[str, Any]) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2257)
- `_deferral_reasons(deferral: Mapping[str, Any]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2264)
- `_bare_scheduled(vault: LoadedVault, practice_item: Any, readiness_factor: float | None) -> ScheduledItem | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2270) — A queue row for an item the ranked queue did not hold (a follow-up's item).
- `_insert_pending_followups(vault: LoadedVault, queue: list[ScheduledItem], pending_followups: list[dict[str, str]], readiness_factor: float | None, *, item_states: dict[str, PracticeItemState] | None=None) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2293)
- `_apply_contrast_pair_order(vault: LoadedVault, repository: Repository, queue: list[ScheduledItem], session: SchedulerSession, *, clock: Clock | None=None, record: bool=True) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2428) — Meas §3.A4: randomize which member of a contrast pair is served first.
- `_rotate_same_day_frontier_repeats(queue: list[ScheduledItem], item_states: dict[str, PracticeItemState], now: datetime) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2525) — Within goal-frontier queue slots, serve items not yet attempted today first.
- `_enforce_teach_back_session_cap(queue: list[ScheduledItem], cap: int, *, admitted: frozenset[str] | None=None, keep: frozenset[str]=frozenset()) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2562) — Keep at most ``cap`` teach_back items per built queue (config ``teach_back.session_cap``), preserving order for everything else.
- `_teach_back_value_admission(vault: LoadedVault, context: 'voi.VoiContext', greedy_queue: list[ScheduledItem], config: LearnLoopConfig) -> tuple[frozenset[str] | None, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2595) — mvp-0.21 (c): value every teach-back, greedily and conditionally.
- `_load_episode_context(vault: LoadedVault, repository: Repository, episode, cache: dict[str, tuple[HypothesisSet, dict[str, float], float] | None]) -> tuple[HypothesisSet, dict[str, float], float] | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2652)
- `_load_episode_eligible(vault: LoadedVault, repository: Repository, episode, context: tuple[HypothesisSet, dict[str, float], float], cache: dict[str, dict[str, EligibleInstrument]]) -> dict[str, EligibleInstrument]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2675) — The episode's eligible instruments (with §7.4 predictive components), computed once per episode per queue build and keyed by item id.
- `_record_probe_elicitation(repository: Repository, queue: list[ScheduledItem], probe_item_ids: dict[str, str], session: SchedulerSession, *, entropy_before: dict[str, float] | None=None, clock: Clock | None) -> None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2694)
- `_practice_information(item, learning_object, mastery, config: LearnLoopConfig) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2736) — Display-only measurement value of one ordinary attempt (never selection).
- `_priority(components: dict[str, float], config: LearnLoopConfig) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2760)
- `_selection_propensities(queue: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig) -> dict[str, float]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2787) — ``P(item is served as the top candidate | slate)`` under seeded exploration.
- `_apply_seeded_exploration(queue: list[ScheduledItem], session: SchedulerSession, config: LearnLoopConfig, now: datetime) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2826)
- `_stable_fraction(label: str, session_id: str, now: datetime, candidate_ids: list[str]) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2844)
- `_intent_for_item(item: PracticeItem, *, in_probe: bool, components: dict[str, float]) -> SchedulerIntent` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2850)
- `_readiness_factor(session: SchedulerSession, config: LearnLoopConfig) -> float | None` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2874)
- `_session_context(session: SchedulerSession, *, short_session: bool, readiness_factor: float | None, shadow_intent: dict[str, object] | None=None) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2894)
- `_scheduler_config_snapshot(config: LearnLoopConfig) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2914)
- `_forgetting_risk(state: PracticeItemState | None, now: datetime, weights: tuple[float, ...]=FSRS6_DEFAULT_WEIGHTS, *, effective_due: datetime | None=None) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2931) — ``effective_due`` (DL2, §5.3) replaces ``due_at`` as the due gate when given; the retrievability is the item's own, as before.
- `_intent_serving(vault: LoadedVault, repository: Repository, now: datetime)` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2953) — DL2's per-build intent view (``learnloop.scheduling.intent.serving``), or None.
- `class _Once` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2961) — A build read made at most once, on first use.
- `class _ProbeScore` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 2986) — An item's ranking components before its selection reward, with its probe's when it is a candidate of an in-progress probe episode.
- `class _BuildAdmission` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3004) — One build's gates after the routine one (``serving_exclusions.BuildGates``) and the reads behind them, each item's read once per build.
- `_outside_build_admission(vault: LoadedVault, repository: Repository, *, now: datetime, intent_view: Any, item_states: Any=None) -> '_BuildAdmission'` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3457)
- `_goal_frontier(vault: LoadedVault, item: PracticeItem, entry) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3548) — Fraction of the item's evidence facets on its LO's goal frontier, scaled by goal priority.
- `_apply_goal_quota(queue: list[ScheduledItem], floor: float) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3566) — Reorder-only greedy quota guaranteeing a floor share of goal-frontier items.
- `_apply_requested_floor(queue: list[ScheduledItem], requested_item_ids: list[str], cap: int) -> list[ScheduledItem]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3607) — Prefix-floor reorder guaranteeing requested items a front slot (spec §4a).
- `_recent_error(errors: list[ActiveErrorEvent], now: datetime) -> float` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3641)
- `_errors_by_learning_object(errors: list[ActiveErrorEvent]) -> dict[str, list[ActiveErrorEvent]]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3652) — Active LEARNER errors per LO.
- `_plain_english(item: PracticeItem, components: dict[str, float]) -> list[str]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3673)
- `_explanation_payload(item: ScheduledItem, *, selected: bool=True, selection_propensity: float | None=None) -> dict[str, object]` ([source](../../../../../../src/learnloop/scheduling/scheduler.py), line 3703)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]] — imports `apply_eligibility_writes`, `cold_check_serve_decision`; statically calls `apply_eligibility_writes`, `cold_check_serve_decision`
- [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]] — imports `SchedulerSession`, `build_due_queue`, `explain_practice_item`
- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `SchedulerSession`, `build_due_queue`, `cold_check_hold_until`, `cold_check_serve_decision`, `cold_check_serve_hold`; statically calls `SchedulerSession`, `build_due_queue`, `cold_check_hold_until`, `cold_check_serve_decision`, `cold_check_serve_hold`
- [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]] — imports `pool_admission`; statically calls `pool_admission`
- [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] — imports `UNAVAILABLE_PROPENSITY_KIND`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `check_admission`; statically calls `check_admission`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop/sim/runner|learnloop.sim.runner]] — imports `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop/tui/screens/feedback|learnloop.tui.screens.feedback]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/screens/practice|learnloop.tui.screens.practice]] — imports `ScheduledItem`, `cold_check_serve_hold`; statically calls `cold_check_serve_hold`
- [[Reference/Modules/learnloop/tui/screens/start|learnloop.tui.screens.start]] — imports `SchedulerSession`; statically calls `SchedulerSession`
- [[Reference/Modules/learnloop/tui/screens/today|learnloop.tui.screens.today]] — imports `ScheduledItem`
- [[Reference/Modules/learnloop/tui/state|learnloop.tui.state]] — imports `ScheduledItem`, `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/facets|learnloop_sidecar.handlers.facets]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_map|learnloop_sidecar.handlers.knowledge_map]] — imports `build_due_queue`; statically calls `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `SchedulerSession`, `build_due_queue`; statically calls `SchedulerSession`, `build_due_queue`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `OfferTrace`, `SELECTION_POLICY`, `ScheduledItem`, `SchedulerSession`, `build_due_queue`, `cold_check_serve_decision`, `deferred_cold_followups`, `explain_practice_item`; statically calls `OfferTrace`, `SchedulerSession`, `build_due_queue`, `cold_check_serve_decision`, `deferred_cold_followups`, `explain_practice_item`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `FOLLOWUP_REASONS`, `ScheduledItem`, `dominant_scheduler_reason`, `explain_practice_item`; statically calls `dominant_scheduler_reason`, `explain_practice_item`

### Repository tooling consumers

- [scripts/benchmark_sqlite_concurrency.py](../../../../../../scripts/benchmark_sqlite_concurrency.py); calls `build_due_queue`
- [scripts/voi_cap_report.py](../../../../../../scripts/voi_cap_report.py); calls `OfferTrace`, `SchedulerSession`, `build_due_queue`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `PROBE_TIE_VERSIONS`
- [[Reference/Modules/learnloop/attempt_types|learnloop.attempt_types]] — imports `DEFAULT_ATTEMPT_TYPE`
- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `COLD_FOLLOWUP_TASK_KINDS`
- [[Reference/Modules/learnloop/attempts/evidence|learnloop.attempts.evidence]] — imports `attempt_evidence_mass`; calls `attempt_evidence_mass`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `FrozenClock`, `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/config/__init__|learnloop.config]] — imports `LearnLoopConfig`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `ActiveErrorEvent`, `MasteryState`, `PracticeItemQualityState`, `PracticeItemState`, `Repository`
- [[Reference/Modules/learnloop/db/scopes|learnloop.db.scopes]] — imports `pinned_repository_call`
- [[Reference/Modules/learnloop/diagnosis/calibration_sessions|learnloop.diagnosis.calibration_sessions]] — imports `calibration_cap_lifted`, `routine_planner_shadow`; calls `calibration_cap_lifted`, `routine_planner_shadow`
- [[Reference/Modules/learnloop/diagnosis/contrast_pairs|learnloop.diagnosis.contrast_pairs]] — imports `SEED_PER_PAIR`, `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`; calls `apply_serving_decisions`, `plan_contrast_pair_serving`, `record_contrast_pair_servings`
- [[Reference/Modules/learnloop/diagnosis/diagnostic_surface_supply|learnloop.diagnosis.diagnostic_surface_supply]] — imports `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`; calls `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools`
- [[Reference/Modules/learnloop/diagnosis/error_taxonomy_map|learnloop.diagnosis.error_taxonomy_map]] — imports `ASSESSMENT_SIDE_ERROR_TYPES`, `map_legacy_error_type`; calls `map_legacy_error_type`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `EligibleInstrument`, `EpisodePosterior`, `RoutineDisplayCovered`, `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`, `robust_gate_counterfactual`; calls `administered_surface_exclusions`, `eligible_instruments`, `episode_hypothesis_set`, `episode_posterior`, `presentation_commit_payload`, `probe_serving_block_reason`, `record_presentation_forecast`, `robust_gate_counterfactual`
- [[Reference/Modules/learnloop/diagnosis/probes|learnloop.diagnosis.probes]] — imports `HypothesisSet`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `COLD_RETRIEVAL_DELAY`, `withdraw_cold_measurement`; calls `withdraw_cold_measurement`
- [[Reference/Modules/learnloop/diagnosis/voi_stopping|learnloop.diagnosis.voi_stopping]] — imports `module`; calls `InformationEntry`, `VoiContext`, `greedy_information_admission`, `hypothesis_channel_body`, `probe_episode_decision`, `record_offer_value_forecasts`, `voi_stopping_active`, `with_robust_gate_counterfactual`
- [[Reference/Modules/learnloop/goals/goal_contracts|learnloop.goals.goal_contracts]] — imports `resolve_head`; calls `resolve_head`
- [[Reference/Modules/learnloop/goals/goal_projection|learnloop.goals.goal_projection]] — imports `build_goal_frontier`; calls `build_goal_frontier`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_attempt_ids`; calls `held_attempt_ids`
- [[Reference/Modules/learnloop/learner/facet_state_reader|learnloop.learner.facet_state_reader]] — imports `facet_states_by_lo`; calls `facet_states_by_lo`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `resolve_item_irt_params`; calls `resolve_item_irt_params`
- [[Reference/Modules/learnloop/learner/recall_coverage|learnloop.learner.recall_coverage]] — imports `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`; calls `familiarity_discount`, `familiarity_discount_from_attempts`, `resolve_coverage`
- [[Reference/Modules/learnloop/numeric|learnloop.numeric]] — imports `clamp`; calls `clamp`
- [[Reference/Modules/learnloop/outcome_contract|learnloop.outcome_contract]] — imports `HELD_ROW_KEY`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`
- [[Reference/Modules/learnloop/placement/decisions|learnloop.placement.decisions]] — imports `reconcile_fast_track`; calls `reconcile_fast_track`
- [[Reference/Modules/learnloop/placement/predictor|learnloop.placement.predictor]] — imports `active_predictor`; calls `active_predictor`
- [[Reference/Modules/learnloop/placement/signals|learnloop.placement.signals]] — imports `taught_first_by_predecessor`; calls `taught_first_by_predecessor`
- [[Reference/Modules/learnloop/placement/state|learnloop.placement.state]] — imports `choose_check_items`, `diagnosis_can_arrive`, `load_placement_state`, `order_new_material`, `placement_active`, `servable_open_episodes`; calls `choose_check_items`, `diagnosis_can_arrive`, `load_placement_state`, `order_new_material`, `placement_active`, `servable_open_episodes`
- [[Reference/Modules/learnloop/reveal_coverage|learnloop.reveal_coverage]] — imports `is_routine_display`, `routine_displays_covering`, `routine_released_at`, `routine_row_covers`; calls `is_routine_display`, `routine_displays_covering`, `routine_released_at`, `routine_row_covers`
- [[Reference/Modules/learnloop/scheduling/device_eligibility|learnloop.scheduling.device_eligibility]] — imports `DeviceFilter`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `FSRS6_DEFAULT_WEIGHTS`, `forgetting_curve`; calls `forgetting_curve`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `intent_serving`; calls `intent_serving`
- [[Reference/Modules/learnloop/scheduling/intent_planner|learnloop.scheduling.intent_planner]] — imports `shadow_intent_plan`; calls `shadow_intent_plan`
- [[Reference/Modules/learnloop/scheduling/selection_rewards|learnloop.scheduling.selection_rewards]] — imports `SchedulerIntent`, `ability_vector`, `item_demand_vector`, `score_selection_reward`; calls `ability_vector`, `item_demand_vector`, `score_selection_reward`
- [[Reference/Modules/learnloop/scheduling/serving_exclusions|learnloop.scheduling.serving_exclusions]] — imports `DEVICE_INELIGIBLE`, `PROBE_RESERVED_GATES`, `ServingExclusions`, `admission_reason`, `out_of_timing_serving_exclusions`, `routine_serving_exclusions`; calls `admission_reason`, `out_of_timing_serving_exclusions`, `routine_serving_exclusions`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `module`; calls `EligibilityDecision`, `decide`, `decision_active`, `gather`, `log_decision`, `retime`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `surface_group_id`; calls `surface_group_id`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_servable`; calls `practice_item_servable`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`, `PracticeItem`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `datetime`, `hashlib`, `json`, `logging`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/app|learnloop.cli.app]], [[Reference/Modules/learnloop/cli/runtime|learnloop.cli.runtime]], [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/slot_facts|learnloop.daily_plan.slot_facts]], [[Reference/Modules/learnloop/scheduling/evaluation|learnloop.scheduling.evaluation]] and 14 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/daily_plan_fakes.py](../../../../../../tests/daily_plan_fakes.py) — direct import
- [tests/intent_fakes.py](../../../../../../tests/intent_fakes.py) — direct import
- [tests/test_ad1_migration.py](../../../../../../tests/test_ad1_migration.py) — direct import
  - `test_a_served_revision_hashes_as_the_scheduler_snapshots_it`
- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
- [tests/test_assumed_known.py](../../../../../../tests/test_assumed_known.py) — direct import
- [tests/test_attempts.py](../../../../../../tests/test_attempts.py) — direct import
  - `test_attempt_links_to_scheduler_slate_and_later_retention_label`
- [tests/test_cli_generate_practice.py](../../../../../../tests/test_cli_generate_practice.py) — direct import
  - `test_accepting_diagnostic_proposal_queues_today_followup`
- [tests/test_cold_retry_reschedule.py](../../../../../../tests/test_cold_retry_reschedule.py) — direct import
  - `test_off_or_below_the_tag_the_assisted_retry_is_left_open_exactly_as_the_predecessor`
- [tests/test_cold_start_revision.py](../../../../../../tests/test_cold_start_revision.py) — direct import
  - `test_scheduler_excludes_assessment_side_errors`
- [tests/test_collection_dataset.py](../../../../../../tests/test_collection_dataset.py) — direct import
  - `test_adjudication_accepts_evidence_keyed_by_a_non_id_primary_key`
  - `test_exact_offer_survives_refresh_recovery_and_dataset_export`
  - `test_final_offer_refuses_filtered_and_cross_session_candidates`
  - `test_scored_item_text_is_snapshotted_once_per_revision_and_exported`
  - `test_selection_decision_features_reference_the_item_and_stay_compact`
  - `test_writers_stamp_the_current_collection_version`
- [tests/test_compare_methods.py](../../../../../../tests/test_compare_methods.py) — direct import
  - `test_the_reveal_makes_the_cold_lane_treat_the_family_as_revealed_and_primes_the_next_attempt`
- [tests/test_contrast_pairs.py](../../../../../../tests/test_contrast_pairs.py) — direct import
  - `test_the_scheduler_records_a_serving_for_a_real_session`
- [tests/test_controller_cutover.py](../../../../../../tests/test_controller_cutover.py) — direct import
- [tests/test_controller_ownership.py](../../../../../../tests/test_controller_ownership.py) — direct import
  - `test_legacy_scheduler_excludes_staged_owned_items`
  - `test_rollback_is_all_or_nothing_on_mid_failure`
  - `test_rollback_returns_to_legacy_and_restores_queue`
- [tests/test_controller_snapshot.py](../../../../../../tests/test_controller_snapshot.py) — direct import
- [tests/test_daily_loop_lo_lifecycle_serving.py](../../../../../../tests/test_daily_loop_lo_lifecycle_serving.py) — direct import
  - `test_follow_up_lanes_do_not_resurrect_items_of_an_inactive_lo`
- [tests/test_daily_loop_reader_authored_practice.py](../../../../../../tests/test_daily_loop_reader_authored_practice.py) — direct import
- [tests/test_daily_plan_composition.py](../../../../../../tests/test_daily_plan_composition.py) — direct import
  - `test_a_check_miss_awaiting_its_diagnosis_stays_assumed_and_is_not_rechecked`
- [tests/test_daily_plan_review_regressions.py](../../../../../../tests/test_daily_plan_review_regressions.py) — direct import
- [tests/test_device_eligibility.py](../../../../../../tests/test_device_eligibility.py) — direct import
  - `test_a_check_once_asks_the_same_gate`
- [tests/test_diagnostic_probe_freshness.py](../../../../../../tests/test_diagnostic_probe_freshness.py) — direct import
  - `test_diagnostic_probe_is_servable_when_injected_by_id_via_followup_task`
  - `test_probe_selection_hard_excludes_an_already_seen_surface_group`
- [tests/test_diagnostic_probe_single_use.py](../../../../../../tests/test_diagnostic_probe_single_use.py) — direct import
- [tests/test_e2e_codex_mock.py](../../../../../../tests/test_e2e_codex_mock.py) — direct import
  - `test_codex_mocked_end_to_end`
- [tests/test_evaluation.py](../../../../../../tests/test_evaluation.py) — direct import
  - `test_propensity_report_marks_composed_offers_unavailable_not_degenerate`
  - `test_report_on_real_session_flow`
- [tests/test_evsi_router_composition.py](../../../../../../tests/test_evsi_router_composition.py) — direct import
  - `test_a_probe_the_eig_chose_records_no_draw`
  - `test_an_explored_probes_forecast_says_the_scheduler_drew_it`
- [tests/test_evsi_staged_binding.py](../../../../../../tests/test_evsi_staged_binding.py) — direct import
- [tests/test_exam_pool.py](../../../../../../tests/test_exam_pool.py) — direct import
  - `test_scheduler_skips_reserved_items`
- [tests/test_exam_protection_review.py](../../../../../../tests/test_exam_protection_review.py) — direct import
- [tests/test_followup_diagnostic_selection.py](../../../../../../tests/test_followup_diagnostic_selection.py) — direct import
  - `test_repair_journey_task_with_administered_diagnostic_still_serves`
  - `test_stale_generic_task_with_administered_diagnostic_is_refused`
- [tests/test_followups.py](../../../../../../tests/test_followups.py) — direct import
  - `test_manual_override_forces_followup_when_gate_silent`
  - `test_negative_surprise_followup_stops_forcing_after_followup_attempt`
  - `test_negative_surprise_inserts_followup_when_item_exists`
- [tests/test_goal_frontier.py](../../../../../../tests/test_goal_frontier.py) — direct import
  - `test_cold_start_lo_on_frontier_is_schedulable`
  - `test_goal_quota_guarantees_floor_share_at_top_of_queue`
  - `test_known_gap_and_uncertain_facets_are_both_on_frontier`
  - `test_no_active_goals_means_no_goal_frontier`
  - `test_unexamined_facet_on_goal_frontier_scales_by_goal_priority`
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — direct import
  - `test_a_delayed_followup_can_serve_an_instrument`
- [tests/test_intent_codex_rereview.py](../../../../../../tests/test_intent_codex_rereview.py) — direct import
  - `test_f2_below_the_tag_commitments_change_nothing_with_the_switch_on`
- [tests/test_intent_codex_review.py](../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f2_with_intent_off_commitments_change_nothing_in_the_ranked_list_or_the_plan`
- [tests/test_intent_exclusion.py](../../../../../../tests/test_intent_exclusion.py) — direct import
- [tests/test_intent_fix_round4.py](../../../../../../tests/test_intent_fix_round4.py) — direct import
  - `test_f14_the_teach_back_count_cap_never_drops_a_check`
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
  - `test_f22_an_admission_error_is_a_named_refusal_not_an_exception`
- [tests/test_intent_orchestrator_rulings.py](../../../../../../tests/test_intent_orchestrator_rulings.py) — direct import
  - `test_r1_check_selection_asks_the_builds_admission_predicate`
  - `test_r1_every_gate_of_the_build_is_the_admission_predicates`
  - `test_r1_the_predicate_names_the_freshness_reserve_for_a_check_candidate`
- [tests/test_intent_planner.py](../../../../../../tests/test_intent_planner.py) — direct import
- [tests/test_intent_recall_targets.py](../../../../../../tests/test_intent_recall_targets.py) — direct import
  - `test_identity_at_090_uncommitted_items_are_served_exactly_as_with_intent_off`
- [tests/test_item_authoring.py](../../../../../../tests/test_item_authoring.py) — direct import
  - `test_retire_item_stops_all_serving`
- [tests/test_km5_sim_gates.py](../../../../../../tests/test_km5_sim_gates.py) — direct import
  - `test_shadow_intent_logs_practice_integration_at_the_right_moment`
- [tests/test_large_practice_flow.py](../../../../../../tests/test_large_practice_flow.py) — direct import
  - `test_many_open_text_practice_items_schedule_and_record_attempt`
- [tests/test_learner_pick_proposal.py](../../../../../../tests/test_learner_pick_proposal.py) — direct import
- [tests/test_learner_text_gaps_flow.py](../../../../../../tests/test_learner_text_gaps_flow.py) — direct import
- [tests/test_learner_text_gaps_review.py](../../../../../../tests/test_learner_text_gaps_review.py) — direct import
  - `test_f13_the_pipeline_switched_off_queues_exactly_as_the_predecessor_version`
- [tests/test_method_explicit_upgrade.py](../../../../../../tests/test_method_explicit_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_migrations.py](../../../../../../tests/test_migrations.py) — direct import
  - `test_head_163_database_upgrades_to_snapshots_and_fk_free_adjudications`
- [tests/test_mvp015_upgrade.py](../../../../../../tests/test_mvp015_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_that_admits_probe_ties`
  - `test_upgrade_from_mvp014_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp016_upgrade.py](../../../../../../tests/test_mvp016_upgrade.py) — direct import
  - `test_an_earlier_vault_goes_through_mvp012s_guard_when_it_is_required`
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_sooner_checks`
  - `test_upgrade_from_mvp015_flips_rebuilds_and_rewrites_nothing`
- [tests/test_mvp017_upgrade.py](../../../../../../tests/test_mvp017_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
- [tests/test_mvp020_upgrade.py](../../../../../../tests/test_mvp020_upgrade.py) — direct import
  - `test_each_version_activates_exactly_its_features`
  - `test_new_vaults_start_at_a_successor_with_the_route_rules`
- [tests/test_mvp021_upgrade.py](../../../../../../tests/test_mvp021_upgrade.py) — direct import
- [tests/test_placement_diagnosis_decides.py](../../../../../../tests/test_placement_diagnosis_decides.py) — direct import
  - `test_a_diagnosis_that_never_lands_stops_holding_the_check`
  - `test_a_miss_the_diagnosis_does_not_call_a_gap_keeps_the_topic_in_maintenance`
  - `test_the_decision_waits_while_the_diagnosis_is_pending`
  - `test_the_first_serving_build_with_the_split_off_records_the_hold`
  - `test_the_kill_switch_ignores_diagnosis_decided_outcomes`
- [tests/test_placement_fixture_copies.py](../../../../../../tests/test_placement_fixture_copies.py) — direct import
  - `test_placement_ignores_unanswered_opening_episodes_on_fixture_copies`
- [tests/test_placement_opening_probes.py](../../../../../../tests/test_placement_opening_probes.py) — direct import
  - `test_an_answered_opening_episode_is_not_ignored`
  - `test_an_in_progress_opening_episode_serves_no_probe_and_is_not_parked`
  - `test_the_overconfidence_list_adopts_an_ignored_episode`
  - `test_unanswered_opening_episodes_are_ignored_and_their_los_start_as_learning`
- [tests/test_plan_determinism.py](../../../../../../tests/test_plan_determinism.py) — direct import
  - `test_a_greedy_scheduler_session_never_draws_and_logs_the_greedy_design`
  - `test_the_per_session_draw_keeps_its_own_path`
  - `test_the_plans_scheduler_session_is_greedy_only_where_the_router_composes_today`
- [tests/test_plan_determinism_landing.py](../../../../../../tests/test_plan_determinism_landing.py) — direct import
  - `test_the_plans_scheduler_session_at_mvp024`
- [tests/test_practice_index_admission.py](../../../../../../tests/test_practice_index_admission.py) — direct import
  - `test_everything_the_scheduler_would_serve_is_admitted`
  - `test_shared_rules_exclude_exactly_what_the_scheduler_drops`
- [tests/test_practice_information.py](../../../../../../tests/test_practice_information.py) — direct import
  - `test_boundary_item_maximizes_information`
  - `test_claim_seeded_theta_shifts_information`
  - `test_practice_information_never_reaches_priority`
- [tests/test_probe_episodes.py](../../../../../../tests/test_probe_episodes.py) — direct import
  - `test_pending_items_episode_keeps_lo_schedulable_with_belief_updates`
  - `test_scheduler_slate_atomically_commits_its_selected_probe_presentation`
- [tests/test_probe_pool_empty.py](../../../../../../tests/test_probe_pool_empty.py) — direct import
  - `test_scheduler_build_raises_the_notice_without_a_provider`
- [tests/test_probe_remint.py](../../../../../../tests/test_probe_remint.py) — direct import
- [tests/test_probe_surface_mint.py](../../../../../../tests/test_probe_surface_mint.py) — direct import
  - `test_minted_surface_serves_through_the_probe_branch_and_is_single_use`
- [tests/test_reentry_short_session.py](../../../../../../tests/test_reentry_short_session.py) — direct import
- [tests/test_remediation_cold_retry.py](../../../../../../tests/test_remediation_cold_retry.py) — direct import
  - `test_only_the_cold_lane_is_deferred_by_a_reveal`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_committed_presentation_is_logged_as_the_continue_choice`
  - `test_a_draw_composition_always_undoes_is_logged_as_deterministic`
  - `test_a_recomposition_that_disagrees_with_the_served_head_is_refused`
  - `test_candidate_propensities_are_one_distribution_with_continue_counted_once`
  - `test_every_counterfactual_outcome_reproduces_the_build_that_draw_would_make`
  - `test_the_snapshot_hash_covers_the_decision_inputs_not_the_build_time`
- [tests/test_router_probe_ties.py](../../../../../../tests/test_router_probe_ties.py) — direct import
  - `test_a_greedy_probe_presentation_carries_no_exploration_mark`
  - `test_an_explored_probe_presentation_is_marked_as_drawn_not_as_the_eig_choice`
  - `test_kill_switch_serves_the_predecessors_probe_offer_exactly`
  - `test_predecessor_and_kill_switch_keep_the_probe_exclusion_exactly`
  - `test_successor_admits_probe_near_ties_both_ways`
  - `test_teach_back_items_are_probe_near_ties_at_the_successor`
  - `test_the_draw_can_displace_a_probe_only_at_the_successor`
  - `test_the_gate_needs_the_successor_and_the_switch`
- [tests/test_router_staged_p2.py](../../../../../../tests/test_router_staged_p2.py) — direct import
- [tests/test_scheduler.py](../../../../../../tests/test_scheduler.py) — direct import
  - `test_a_clean_cold_task_is_served_as_the_cold_lane`
  - `test_a_revealed_cold_task_is_withheld_and_says_so_in_the_slate`
  - `test_a_side_effect_free_build_withholds_without_rescheduling`
  - `test_frontier_items_attempted_today_rotate_behind_fresh_ones`
  - `test_inserted_followup_records_its_lane`
  - `test_ordinary_due_pick_carries_no_followup_kind`
  - `test_rotation_leaves_non_frontier_slots_untouched`
  - `test_rotation_no_op_when_all_frontier_items_attempted_today`
  - `test_scheduler_bulk_loads_item_quality_once`
  - `test_scheduler_candidate_logs_are_retained_per_configured_limit`
  - `test_scheduler_orders_eligible_items_by_selection_reward_before_id`
  - `test_scheduler_persists_bounded_reward_debug_and_rejected_candidates`
  - `test_scheduler_preserves_draw_diagnostics_without_claiming_final_propensity`
  - `test_scheduler_scores_due_goal_item`
  - `test_scheduler_selects_item_on_weak_canonical_facet_boundary`
  - `test_selection_propensities_epsilon_split_over_near_ties`
  - `test_selection_propensities_greedy_when_disabled_or_singleton_or_probe`
  - `test_selection_propensities_window_excludes_far_candidates`
  - `test_unrecognised_followup_action_reports_the_lane_it_lands_on`
- [tests/test_scheduler_golden.py](../../../../../../tests/test_scheduler_golden.py) — direct import
  - `test_scheduler_forgetting_risk_zero_before_due_date`
  - `test_scheduler_goal_frontier_follows_explicit_scope_only`
  - `test_scheduler_recent_error_decays_by_exp_days_over_seven`
  - `test_scheduler_ties_by_lowest_practice_item_id_and_filters_inactive`
- [tests/test_scheduler_probe_eig.py](../../../../../../tests/test_scheduler_probe_eig.py) — direct import
  - `test_probe_eig_included_only_for_in_progress_probe`
  - `test_probe_eig_persisted_in_scheduler_explanation`
  - `test_probe_eig_uses_prospective_familiarity_discount`
  - `test_readiness_factor_is_persisted_without_changing_priority`
  - `test_scheduler_explanations_persist_only_for_named_sessions`
  - `test_short_session_keeps_probe_eig_when_probe_is_only_reason`
  - `test_short_session_suppresses_probe_eig`
- [tests/test_scheduler_requested_floor.py](../../../../../../tests/test_scheduler_requested_floor.py) — direct import
  - `test_cap_limits_number_pulled`
  - `test_cap_two_pulls_both_in_requested_order`
  - `test_ineligible_requested_item_is_never_forced_in`
  - `test_noop_when_cap_zero_or_nothing_requested`
  - `test_requested_floor_honored_before_limit_slice`
  - `test_requested_item_pulled_to_front`
  - `test_requested_item_surfaces_and_respects_gates`
  - `test_stateless_requested_item_survives_eligibility`
- [tests/test_serve_eligibility.py](../../../../../../tests/test_serve_eligibility.py) — direct import
  - `test_the_queue_serves_a_cold_retry_submit_would_prime_as_practice_and_ends_it_honestly`
  - `test_the_real_serve_paths_agree_with_submit`
- [tests/test_serve_eligibility_review.py](../../../../../../tests/test_serve_eligibility_review.py) — direct import
  - `test_f2_a_certification_probe_whose_answer_was_shown_expires_unmeasured`
  - `test_f2_a_non_persisting_read_withdraws_nothing`
  - `test_f3_a_cold_check_is_never_served_on_an_item_practised_since_it_was_set`
  - `test_f3_a_cold_check_served_unpractised_is_still_served`
  - `test_f3_a_delayed_open_and_submit_after_a_withdrawing_build_are_plain_practice`
  - `test_f4_below_the_tag_or_switched_off_a_practised_cold_check_is_served`
  - `test_f4_below_the_tag_or_switched_off_the_12_9_case_is_served_as_on_mvp_026`
- [tests/test_sidecar_queue_serialization.py](../../../../../../tests/test_sidecar_queue_serialization.py) — direct import
  - `test_queue_serialization_bulk_loads_state_once`
- [tests/test_sidecar_serializer_snapshot.py](../../../../../../tests/test_sidecar_serializer_snapshot.py) — direct import
  - `test_queue_practice_and_reader_wire_snapshots`
- [tests/test_sqlite_wal_lifecycle.py](../../../../../../tests/test_sqlite_wal_lifecycle.py) — direct import
  - `test_wal_stays_bounded_across_twenty_queue_builds_on_a_fixture_copy`
- [tests/test_staged_policy.py](../../../../../../tests/test_staged_policy.py) — direct import
- [tests/test_staged_policy_evsi.py](../../../../../../tests/test_staged_policy_evsi.py) — direct import
- [tests/test_state_sync.py](../../../../../../tests/test_state_sync.py) — direct import
  - `test_state_sync_enters_probe_for_new_active_goal_learning_object`
  - `test_state_sync_enters_probe_for_new_active_learning_object_without_goal`
  - `test_state_sync_enters_probe_when_practice_item_arrives_after_learning_object`
- [tests/test_teach_back.py](../../../../../../tests/test_teach_back.py) — direct import
  - `test_scheduler_caps_teach_back_items_per_queue`
  - `test_teach_back_stays_weakly_schedulable_on_solid_knowledge`
- [tests/test_tui_today.py](../../../../../../tests/test_tui_today.py) — direct import
  - `test_today_queue_matches_scheduler_and_opens_practice`
- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f1j_no_serve_path_serves_a_cold_check_submit_would_prime`
  - `test_f1k_a_future_task_never_masks_a_due_one`
  - `test_f1l_a_hold_that_lifts_today_waits_instead_of_finishing_the_plan`
  - `test_f1l_the_scheduler_never_commits_or_serves_a_covered_probe`
- [tests/test_voi_forecasts.py](../../../../../../tests/test_voi_forecasts.py) — direct import
- [tests/test_voi_merge_composition.py](../../../../../../tests/test_voi_merge_composition.py) — direct import
  - `test_a_dropped_teach_back_is_not_administered`
  - `test_an_explored_probe_value_forecast_carries_router_r1s_marker`
  - `test_teach_back_offers_log_one_forecast_per_teach_back_per_offer`
  - `test_the_report_scores_a_kept_teach_back_through_its_offers_candidate`
  - `test_the_robust_gates_counterfactual_is_never_logged_as_a_gate_decision`
- [tests/test_voi_stopping.py](../../../../../../tests/test_voi_stopping.py) — direct import
  - `test_a_second_teach_back_that_tells_the_same_thing_is_not_admitted`
  - `test_a_served_probe_records_its_probability_over_the_composed_queue`
  - `test_a_sole_teach_back_is_valued_and_receipted`
  - `test_a_teach_back_whose_value_does_not_pay_is_dropped_the_first_included`
  - `test_an_explored_probe_carries_its_own_forecast`
  - `test_at_the_successor_value_keeps_asking_past_the_former_cap`
  - `test_at_the_successor_value_stops_an_episode_whose_next_observation_does_not_pay`
  - `test_below_the_successor_the_new_switches_change_nothing`
  - `test_teach_backs_stay_while_their_conditional_value_pays`
  - `test_the_decision_features_receipt_reads_the_overlay_and_says_so`
  - `test_the_kill_switch_serves_mvp020s_probe_queue_exactly`
- [tests/test_voi_v2.py](../../../../../../tests/test_voi_v2.py) — direct import
  - `test_a_value_continue_past_the_gate_carries_its_verdict_on_the_committed_receipt`
  - `test_at_their_restore_values_the_switches_reproduce_the_branchs_decisions_exactly`
  - `test_each_switch_alone_moves_only_its_own_decisions`
  - `test_in_the_real_probe_vault_the_gate_no_longer_ends_a_paying_episode`
  - `test_rank_feasible_values_the_episode_at_the_configured_quantile`
  - `test_robust_batch_evsi_is_the_robust_quantile_of_the_joint_evsi_per_member`
  - `test_the_lookahead_acts_at_probe_episodes_only`
  - `test_the_lookahead_does_not_run_when_a_single_check_pays_or_rank_abstains`
  - `test_the_value_gate_reads_the_configured_robust_quantile`
- [tests/voi_restore_scenarios.py](../../../../../../tests/voi_restore_scenarios.py) — direct import

## Modification guidance

- Change scheduler policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/scheduler.py](../../../../../../src/learnloop/scheduling/scheduler.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
