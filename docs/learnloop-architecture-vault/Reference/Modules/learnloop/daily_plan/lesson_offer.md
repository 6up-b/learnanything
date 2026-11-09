---
title: "learnloop.daily_plan.lesson_offer"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/lesson_offer.py"
source_paths:
  - "src/learnloop/daily_plan/lesson_offer.py"
source_commit: "4be77a51f600217467f5594eab9f98af4a2bd3e4"
source_commit_timestamp: "2026-11-09T15:29:00-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.lesson_offer module"
  - "src/learnloop/daily_plan/lesson_offer.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.lesson_offer`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.lesson_offer` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: Teacher TE3b (spec_teacher_v1 rev 5 §15.1a): lesson offers as candidates of the router objective.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py) |
| Source lines | 650 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `4be77a51f600217467f5594eab9f98af4a2bd3e4` |
| Commit timestamp | `2026-11-09T15:29:00-05:00` |

## Public API

- `offers_on(vault: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 67) — Lesson offers serve: TE3b's tag and switch with the objective serving and TE1b's suggestions on (``router_objective_switches.lesson_offers_on``), on a plan the objective decides (``policy.objective_active``).
- `is_offer(candidate: Any) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 77)
- `offer_ref(learning_object_id: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 81)
- `class Offer` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 86) — One boundary's offer (``candidate`` None: none, ``record`` says why) and its record for the decision.
- `accept_moments(state: LS.AcceptanceState, context: LS.Context, candidate: LS.Candidate) -> tuple[float, float]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 100) — ``P(accept)``'s posterior mean and sd: the recovery grid's mixture of ``σ(h·θ)``, ``h·θ ~ N(h·m, h·Σ·h)`` per grid point, each by AD's quadrature (the mean is :meth:`LS.AcceptanceState.p_accept`'s).
- `beta_from_moments(mean: float, sd: float) -> tuple[float, float]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 116) — The Beta with this mean and sd (moment matching; structural): the value's per-draw ``p``.
- `lesson_active_minutes(connection: Any, *, at: str) -> list[float]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 138) — Each lesson closed by ``at`` with foreground intervals: its active minutes (TE2-log §11.6: the union of its foreground intervals inside its opening and close; a lesson with none has active unknown and is left out).
- `duration_model(connection: Any, *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 164) — The lesson's active minutes, log-normal: the log median's normal posterior from its labelled prior and the closed lessons' active minutes (known spread :data:`DURATION_LOG_SD`), and the predictive's median and log-sd (sampled in the value, never averaged).
- `check_mass(vault: Any, repository: Any, learning_object_id: str, *, at: str) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 181) — The lesson-check mass the lesson's effect is scaled by (RO4's placeholder, ``γ`` at it; spec §12.1's learned weight, ``learner.lesson_weight``): its posterior mean and sd as of ``at`` on the target (no confidence or prediction term).
- `shown_today(decisions: Sequence[Mapping[str, Any]], today: str) -> int` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 219) — The day's shown cards and drawn offers together (the ceiling's count), among ``decisions``.
- `on_screen(connection: Any, decision: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 226) — A drawn offer reached the learner: its card or page rendered (IH1's ``offer_shown``), a step served it (``block_started``), or they answered it.
- `never_on_screen(config: Any, connection: Any, decision: Mapping[str, Any]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 238) — An offer the learner never saw, as far as the record can say: neither a seen offer against the day's ceiling nor a decline.
- `pending_start(connection: Any, decisions: Sequence[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 253) — An accepted card or offer whose lesson never opened (TE1b ruling R2's reservation) is still waiting.
- `build(vault: Any, repository: Any, *, today: str, now_iso: str, local_hour: float, minutes_left: float | None, reentry: bool, forced: bool, learner_asked: bool=False, replacing: bool=False) -> Offer` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 266) — This boundary's offer, or none with why (module docstring).
- `end_block(connection: Any, block_id: str | None, outcome: str, *, at: str, reason: str | None=None, extra: Mapping[str, Any] | None=None) -> None` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 413) — End the offer's block with the learner's response (once; a block already ended is left as it is).
- `withdrawn(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 431) — The row that took a drawn offer back before an answer (:func:`withdraw`), if one did.
- `withdraw(connection: Any, block: Any, *, at: str, why: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 441) — Take back a drawn offer nobody answered (Codex review F1, F2): forced items arrived after it was drawn (a probe FG1 made ready while the offer waited, a follow-up), or offers no longer serve (switch off: the predecessor's boundary decides next).
- `supersede(connection: Any, block: Any, *, at: str, by: str | None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 462) — IH2 §5 item 1: a newer decision replaces an offer nobody answered, in that decision's own transaction.
- `offer_standing(connection: Any, decision_id: str, *, today: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 489) — Whether the lesson offer ``decision_id`` drew is still open, was taken (a Start or an alternative), or passed (declined, ignored, taken back by the plan, its block ended or its day gone).
- `record_ignored(connection: Any, decision: Mapping[str, Any], *, at: str, why: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 508) — The boundary passed with no answer (spec §15.1a): ``ignored`` on the offer's own decision, once (the ledger's one response a decision), its block ended so.
- `release_never_shown(connection: Any, decision: Mapping[str, Any], *, at: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 521) — The boundary passed on an offer nobody saw (:func:`never_on_screen`): the plan's act, as :func:`withdraw` is.
- `sweep_due(connection: Any, *, today: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 554) — :func:`sweep_ignored` has something to write (an ``ignored`` moves the acceptance model the offer is scored by).
- `sweep_ignored(connection: Any, *, config: Any, today: str, now_iso: str) -> int` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 560) — Every offer :func:`_sweep_decisions` finds (the next boundary's step): ``ignored`` if the learner saw it and moved on; if they never did, released (:func:`release_never_shown`), since a draw on a background read is no refusal.
- `card(candidate: BlockCandidate) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 573) — The offer card a drawn offer's block shows and its decision records (``lesson_offer`` on the block's detail and the decision row): its context and candidates (the acceptance model's replay inputs), the value's sensors.
- `action_inputs(candidate: BlockCandidate) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 580) — What the value estimator reads for the offer (``objective_inputs.action_for``).
- `record_shown(repository: Any, *, block_id: str | None, surface: str, session_id: str | None=None, clock: Any=None) -> bool` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 607) — Write ``offer_shown`` on the offer's block: at most once per block and surface, only on a lesson offer's block that has not ended (an answered offer's card is not an offer any more).

### Module constants

- `LOG` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 48)
- `OFFER_VERSION` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 50)
- `DURATION_VERSION` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 52)
- `DURATION_PRIOR_MEDIAN` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 56)
- `DURATION_LOG_SD` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 59)
- `DURATION_MEDIAN_PRIOR_SD` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 61)
- `CONTEXT_RESOLUTION_DAYS` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 64)
- `WITHDRAWN` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 381)
- `WITHDRAWN_FORCED` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 384)
- `WITHDRAWN_OFF` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 385)
- `WITHDRAWN_NEVER_SHOWN` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 387)
- `ENDED_OUTCOMES` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 391)
- `SUPERSEDED` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 395)
- `SUPERSEDED_BY` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 396)
- `OFFER_OPEN` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 484)
- `OFFER_TAKEN` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 485)
- `OFFER_PASSED` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 486)
- `SHOWN_EVENT` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 602)
- `SHOWN_SURFACES` ([src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 604)

### Explicit exports

`__all__` declares:

- `CONTEXT_RESOLUTION_DAYS`
- `DURATION_LOG_SD`
- `DURATION_MEDIAN_PRIOR_SD`
- `DURATION_PRIOR_MEDIAN`
- `DURATION_VERSION`
- `OFFER_OPEN`
- `OFFER_PASSED`
- `OFFER_TAKEN`
- `OFFER_VERSION`
- `Offer`
- `SHOWN_EVENT`
- `SHOWN_SURFACES`
- `SUPERSEDED`
- `SUPERSEDED_BY`
- `WITHDRAWN`
- `WITHDRAWN_FORCED`
- `WITHDRAWN_NEVER_SHOWN`
- `WITHDRAWN_OFF`
- `accept_moments`
- `action_inputs`
- `beta_from_moments`
- `build`
- `card`
- `check_mass`
- `duration_model`
- `is_offer`
- `lesson_active_minutes`
- `never_on_screen`
- `offer_ref`
- `offer_standing`
- `offers_on`
- `on_screen`
- `pending_start`
- `record_shown`
- `release_never_shown`
- `shown_today`
- `supersede`
- `withdraw`
- `withdrawn`

## Internal implementation anchors

- `_union_seconds(rows: Sequence[tuple[str, str]]) -> float` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 126)
- `_quantized(context: LS.Context) -> LS.Context` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 209)
- `_block_state(connection: Any, block_id: str | None) -> tuple[bool, str | None]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 399) — Whether the offer's block has ended, and its plan's status.
- `_sweep_decisions(connection: Any, *, today: str) -> list[Mapping[str, Any]]` ([source](../../../../../../src/learnloop/daily_plan/lesson_offer.py), line 536) — Every drawn offer left unanswered whose boundary has passed (its block ended, its plan no longer open, or an earlier day).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `end_block`, `offer_standing`, `offers_on`, `record_ignored`, `supersede`, `withdraw`
- [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]] — imports `module`; statically calls `build`, `offers_on`, `supersede`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `end_block`, `module`, `offers_on`; statically calls `end_block`, `never_on_screen`, `offers_on`, `release_never_shown`, `withdrawn`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `action_inputs`; statically calls `action_inputs`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `module`; statically calls `Offer`, `build`, `sweep_due`, `sweep_ignored`
- [[Reference/Modules/learnloop/daily_plan/view|learnloop.daily_plan.view]] — imports `offers_on`; statically calls `offers_on`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `module`; statically calls `record_shown`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adf_numeric|learnloop.adf_numeric]] — imports `NODES`, `WEIGHTS`, `sigmoid`; calls `sigmoid`
- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `FAILURE_SHARE_VERSIONS`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `card_view`, `module`; calls `build_candidates`, `card_view`, `reason_words`
- [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] — imports `objective_active`; calls `objective_active`
- [[Reference/Modules/learnloop/daily_plan/types|learnloop.daily_plan.types]] — imports `BlockCandidate`, `LESSON_OFFER_PREFIX`, `LESSON_OFFER_SUBTYPE`; calls `BlockCandidate`
- [[Reference/Modules/learnloop/db/stores/daily_plans|learnloop.db.stores.daily_plans]] — imports `module`; calls `append_block_event`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `learner_preference_rows`; calls `learner_preference_rows`
- [[Reference/Modules/learnloop/db/stores/router_suggestions|learnloop.db.stores.router_suggestions]] — imports `module`; calls `all_decisions`, `insert_response`, `offer_decision`, `offer_decisions`, `release_for`, `releases`, `response_for`, `responses`, `tables_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `module`; calls `replay_state`
- [[Reference/Modules/learnloop/router/lesson_suggestions|learnloop.router.lesson_suggestions]] — imports `module`; calls `Context`, `days_between`, `declines_by_learning_object`, `observations`, `replay`, `score`, `unprompted_observations`, `with_unprompted`
- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `module`; calls `sensor`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `MISS_CAUSE_OFFER_KEY`, `lesson_offers_on`, `lessons_compete_with_followups_on`, `miss_cause_sensor_on`, `preferences_inform_router_on`; calls `lesson_offers_on`, `lessons_compete_with_followups_on`, `miss_cause_sensor_on`, `preferences_inform_router_on`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `json`, `logging`, `math`, `typing`
- Third party: `numpy`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/learner_action|learnloop.daily_plan.learner_action]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/daily_plan/policy|learnloop.daily_plan.policy]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ih2_lessons_compete.py](../../../../../../tests/test_ih2_lessons_compete.py) — direct import
  - `test_a_followup_arriving_over_an_interrupting_offer_joins_the_block_below_and_the_offer_stands`
  - `test_a_probe_arriving_during_an_open_offer_gets_a_new_decision_holding_both`
  - `test_not_now_with_the_ceiling_reached_the_followup_serves`
  - `test_off_or_below_the_tag_a_probe_withdraws_the_offer_as_the_predecessor`
  - `test_the_journey_on_a_real_miss_lesson_then_not_now_then_the_question`
- [tests/test_ih2_offer_ceiling_and_unseen.py](../../../../../../tests/test_ih2_offer_ceiling_and_unseen.py) — direct import
  - `test_an_offer_drawn_after_a_miss_and_never_rendered_is_no_decline`
  - `test_an_offer_drawn_after_the_followups_decision_is_contested`
  - `test_off_or_below_the_tag_every_drawn_offer_counts_and_an_unseen_one_is_ignored`
  - `test_offers_nobody_saw_use_up_nothing_and_a_lesson_keeps_competing_past_the_ceiling`
  - `test_rows_from_before_the_record_keep_their_reading`
  - `test_the_block_of_an_offer_nobody_saw_ends_taken_back`
  - `test_the_todays_card_sweep_agrees`
- [tests/test_ih2_one_open_offer.py](../../../../../../tests/test_ih2_one_open_offer.py) — direct import
  - `test_a_read_drawing_an_offer_during_a_jobs_decision_leaves_one_offer`
  - `test_a_superseded_offer_passing_a_later_day_is_not_read_as_a_decline`
  - `test_two_reads_contesting_one_offer_decide_it_once`
- [tests/test_ih4_preferences_inform_router.py](../../../../../../tests/test_ih4_preferences_inform_router.py) — direct import
  - `test_a_card_passed_over_is_no_answer_so_the_phones_request_still_counts`
  - `test_a_learner_asked_lesson_reaches_p_accept_flagged_unprompted`
  - `test_a_phone_agreement_is_a_request_it_reaches_the_model_on_the_drawn_offers_card`
- [tests/test_ih_lesson_candidate_after_cold_miss.py](../../../../../../tests/test_ih_lesson_candidate_after_cold_miss.py) — direct import
  - `test_the_offer_block_and_the_llms_row_carry_the_dated_words`
- [tests/test_instruct_handoff_ih1.py](../../../../../../tests/test_instruct_handoff_ih1.py) — direct import
  - `test_offer_shown_is_ignored_by_the_plan_and_changes_no_decision`
  - `test_offer_shown_is_written_once_per_block_and_surface`
  - `test_offer_shown_only_on_a_live_offers_block`
  - `test_record_shown_never_raises`
- [tests/test_te3b_binding.py](../../../../../../tests/test_te3b_binding.py) — direct import
- [tests/test_te3b_clock.py](../../../../../../tests/test_te3b_clock.py) — direct import
- [tests/test_te3b_codex_review.py](../../../../../../tests/test_te3b_codex_review.py) — direct import
  - `test_f1_a_probe_ready_after_the_prefetched_offer_is_served_next_and_the_offer_withdrawn`
  - `test_f2_switching_off_takes_back_a_prefetched_offer_and_its_card`
- [tests/test_te3b_features.py](../../../../../../tests/test_te3b_features.py) — direct import
- [tests/test_te3b_offers.py](../../../../../../tests/test_te3b_offers.py) — direct import
  - `test_no_offer_beside_forced_items`
- [tests/test_te3b_population.py](../../../../../../tests/test_te3b_population.py) — direct import
- [tests/test_te3b_value.py](../../../../../../tests/test_te3b_value.py) — direct import
  - `test_the_acceptance_posterior_is_moment_matched_to_a_beta`
  - `test_the_duration_sensor_reads_only_intervals_received_by_its_decision`
  - `test_the_lessons_duration_starts_at_the_seed_and_learns_from_active_minutes`

## Modification guidance

- Make changes here when the responsibility remains lesson offer within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/lesson_offer.py](../../../../../../src/learnloop/daily_plan/lesson_offer.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
