# Refactor E6: an action is one place (stopped at step 0)

Branch `refactor/e6-action-one-place`, based on main `f8300a3f00` (E1 to E5 and the second batch of K5 fixes). Step E6
of arc E (`docs/specs/refactor_strategy_v3.md` §2.7, leak 9, the "add an action" row of §6's change-cost table).
Structure track. Line numbers are at the base.

**Verdict: the step stops after step 0, by its own rule (§4).** The TE3b replay at the base touches 10 files and 17
definitions. The best `actions.py` the strategy allows would still touch 5 files. That is exactly half, and only if six
placements, each contested, all go into `actions.py`. On definitions it would touch 18 with plain matches, or 8 only if
each kind's function answers a selector naming the part asked for. That selector is a plugin protocol, which the rule
forbids. Four of the ten files are out of reach under the strategy's own limits: the rollout arithmetic, the offer's
builder, and the builder's wiring in the policy and the engine. Nothing in `src` changed. §5 gives the smallest
alternative I see.

## 1. Step 0a: the inventory

### Three vocabularies, not one

The code has no single "action kind". Three vocabularies meet at the router, and each site branches on one of them:

| Vocabulary | Values | Defined in | Owns |
|---|---|---|---|
| **Objective kinds** (how the rollouts value a candidate) | `review`, `new_practice`, `reading`, `probe`, `repair`, `teach_back`, `lesson`, `stop`, `sequence` | `router_objective/types.py:21-33` | the rollout step (`rollouts._Model`), `Action`'s validation, RO6's features (`learned_tail.kind_group`), the trace row's `kind` |
| **Plan option kinds** (what the plan offers and serves at a boundary) | a block (with its `lane` and `reading`), a lesson offer (`subtype` `lesson_offer`, ref `lesson_offer:<LO>`), stop (`stop_for_today`), IH2's follow-up contest (`followup_contest:<item>`), IH2's generated-probe stand-in (annotation `followup_probe`), and mid-block `insert_now` / `continue_current` / `no_intervention` | `daily_plan/types.py:46-57`, `objective_inputs.py:57-59`, `router_chooser.py` | candidate construction, the trace label (`trace_assembly.option_kind`), the LLM policy's option row, withdrawal and supersession, the plan record and view, the step payload, `why` |
| **Preference kinds** (the learner's words, IH4) | `question`, `review`, `new`, `read`, `lesson`, `stop` | `router_objective/preferences.py:81-98` (`kind_of(reading, subtype, lane)`) | the learner's "something else" options, the preference model and report |

The maps between them are data-driven, not one-to-one. A plan *block* becomes one of six objective kinds according to
its items' practice modes, its lane, whether it has a reading, and whether its topics have been practised
(`objective_inputs.action_for:610-659`). A lesson offer is objective kind `lesson` with an offer's `accept`. The
follow-up contest is a block, and the probe stand-in is a `probe`. An objective `sequence` has no plan option of its
own: it is the mid-block refs' ordered blocks.

### Every site, by class

The sweep was `git grep` over `src/` and `apps/learnloop-tauri/src`. It covered the objective-kind constants
(`OT.*`, `PRACTICE_KINDS`, `action.kind`, `step.kind`, `learned_tail`'s `*_KIND`), the plan names (`LESSON_OFFER_*`,
`FOLLOWUP_CONTEST_*`, `FOLLOWUP_PROBE_NOTE`, `OFFER_DECLINED_STEPS`, `STOP_FOR_TODAY`, `CONTINUE_CURRENT`,
`is_lesson_offer`, `open_lesson_offer(s)`, `held_lesson_offers`, `block_below_offer`, `LO.withdraw/supersede/end_block`)
and the preference kinds (`PF.*`, `kind_of`). It also matched their string values (`"lesson_offer"`,
`"lesson_offer:"`, `"stop_for_today"`, `"followup_contest"`, `"continue_current"`). That gives 322 lines, with false
positives in `adaptive_difficulty` (AD's own event kinds), `hints`, `workbench` and `source_retrieval` removed; the
scratch scripts are `inventory.py` and `touched_defs.py`. Tests are left out.

Class key: **1** candidate construction (from what inputs), **2** rollout step, **3** trace label and what the trace
and decision record say, **4** reversibility, withdrawal, decline or expiry, **5** plan record and view shape, **6**
`why` and learner-facing wording, **7** other (named).

| File | Function (lines) | What the branch decides | Class |
|---|---|---|---|
| `router_objective/types.py` | module (21-33) | the objective kinds, `PRACTICE_KINDS`, `KINDS` | 7: the vocabulary |
| | `Action.__post_init__` (157-163) | kind in `KINDS`; a sequence and only a sequence has steps; steps are not sequences, stops or offers | 1 |
| `router_objective/rollouts.py` | `_Model.apply` (617-662) | `PRACTICE_KINDS`: `_practice` per slot, plus `_cause_gain` for `repair`. `lesson`: about 25 lines inline (γ or SG2's cause split, plus TE3a's curve shift). `reading`: `_read` per LO | 2 |
| | `_Model._effect_correction` (891-899) | no effect correction for `stop` | 2 |
| | `_Model._segment` (936-941) | `probe` observes (`_observe`); every other kind applies | 2 |
| | `_Model._steps`, `_Model._do` (944-973) | a sequence's steps and a lesson's commitments, chosen by the fields `steps` and `commitments`, not by kind | 2 |
| | `_Model.tail_action` (983-997) | the tail's own block is `review` or `new_practice` | 1 (the tail's candidate) |
| | `_Model.value` (999-1045) | `stop`: accepted and overridden branches and the return effect. Any `accept`: accepted and declined branches. `lesson`: `branch_terms`. `probe`: `_probe` | 2; 3 (the extras the trace reads) |
| | `_Model._probe` (1108) | a probe's default repair is a `repair` | 1 |
| | `evaluate` (1190) | `Valued.kind = action.kind` | 3 |
| `router_objective/trace_assembly.py` | module (38-42) | stop's ref (`stop_coin.STOP`), the offer subtype repeated, the option kinds `stop`, `lesson_offer`, `block` | 3 |
| | `option_kind` (45-52), `option_label` (55-69) | the option's kind from its ref and subtype, then its plain label (a `match`, E4's) | 3 |
| | `candidate_row` (71-130) | the row's `kind` is the objective kind; a lesson offer gets its `offer` section | 3 |
| | `_offer_trace` (172-223) | the lesson offer's trace section | 3 |
| | `decision_trace` (246), `objective_trace` (402-409) | stop's `Q̄` for `q_minus_stop`; `stop_in_support`; IH2's contest section | 3 |
| `router_objective/learned_tail.py` | module (99-122), `kind_group` (199-206), `vector` (209-226) | RO6's features: indicators for stop, reading and probe, and for `lesson` at TE3b's features version; **any other kind is silently "practice"** | 7: RO6 features |
| `router_objective/tail_serve.py` | `features` (115); `tail_data` (344) | the feature view takes the objective kind, from the candidate or from a trace entry | 7: RO6 features |
| `router_objective/preferences.py` | module (81-95), `kind_of` (98) | a plan block to a preference kind; the offer subtype repeated | 6, 7: IH4 |
| `router_objective/preference_report.py` | module (36), `_topic_of` (65), `section` (178-183) | the offer prefix repeated; stop by literal; `kind_of` | 7: report |
| `router_objective/forecast_resolve.py` | module (30-35), `groups` (90) | a drawn offer's forecast binding; declined or ignored is censored | 4 |
| `router_objective/` `stop_coin` (77), `sessions` (50), `objective_report.build` (56, 65), `offer_report` (19), `miss_cause_report` (27, 89), `miss_cause._offer_rows` (675), `calibration_report.floor_section` (122) | | stop's and the offer's refs, repeated or literal | 7: reports, the coin |
| `daily_plan/types.py` | module (46-57) | `CONTINUE_CURRENT`, `STOP_FOR_TODAY`, `LESSON_OFFER_SUBTYPE` and `_PREFIX`, `FOLLOWUP_CONTEST_PREFIX` and `_NOTE` | 7: the plan's vocabulary |
| `daily_plan/objective_inputs.py` | module (57-59) | `FOLLOWUP_PROBE_NOTE`, `OFFER_DECLINED_STEPS` | 1 |
| | `action_for` (610-659) | plan option to `Action`. Offer subtype: `lesson` with `accept`, minutes, mass and checks (`lesson_offer.action_inputs`). Probe stand-in: `probe` and `repair`. Reading: `reading`. Probe modes: `probe` and `repair`. All teach-back: `teach_back`. Otherwise by lane, or by whether the topics are practised: `repair`, `review` or `new_practice` | 1 |
| | `_step` (680-684) | a probe step carries no nested repair | 1 |
| | `build` (789-815) | stop is `stop`; `sequences` are `sequence`; the contest or `OFFER_DECLINED_STEPS` is a lesson offer's declined branch (`kind == LESSON`); the tail's block leaves offers out | 1; 4 (the declined branch) |
| `daily_plan/objective_chooser.py` | `_preference_record` (423) | each ref's preference kind | 6, 7 |
| | `run_numeric` (590) | the reference row is complete when every action but stop is valued | 7: completeness |
| | `_offer_option` (683-692), `_is_contest`, `_contest_option` (695-713) | the LLM policy's option row for an offer and for the contest | 7: LLM option row |
| | `ObjectiveChooser.choose` (726-761) | offers leave staged's feasible set and join the support just before stop; staged's pick is stop below 5 minutes | 1 |
| | `_start_objective` (833-837) | the option row by option kind (offer, contest, block, stop) | 7: LLM option row |
| | `ObjectiveRestraintGate.decide`, `_decide_with_lesson`, `_mixed`, `_numeric_restraint`, `decide_followup` (1046-1439) | mid-block options `insert_now`, `continue_current` and `no_intervention` as sequences; an offer as the third option; a drawn offer's `why` and card | 1, 5, 6 |
| `daily_plan/router_chooser.py` | `support_order` (166), `_freeze_objective` (487), `_start` (496), and the mid-block `wait`, `decide`, `_state`, `_support`, `_followup_state`, `decide_followup`, `_start_followup` | stop joins the support; stop's option row; `continue_current` mid-block | 1, 7 |
| `daily_plan/chooser.py` | `choose` (47) | the stop candidate | 1 |
| `daily_plan/lesson_offer.py` | `is_offer` (78, **no caller**), `offer_ref`, `build` (267-378) | the offer's candidate: subtype, `reversible: True`, `reason_code`, card | 1 |
| | `end_block`, `withdraw`, `supersede`, `record_ignored`, `release_never_shown`, `sweep_due`, `sweep_ignored` (400-616) | what happens when the offer is declined, ignored, withdrawn or superseded | 4 |
| | `card`, `action_inputs` (619-638) | what the value reads from the card | 1 |
| | `record_shown` (653-690) | the offer-shown event | 5 |
| `daily_plan/policy.py` | `policy_for` (111), `_lesson_offer_builder` (142-) | wires the offer builder at TE3b's tag | 1 |
| `daily_plan/engine.py` | `PlanPolicy.lesson_offer` (675) | the builder slot | 1 |
| | `decide` (2639-2735) | the offer joins the feasible set; stop is valid only when offered; the fallback never picks an offer | 1, 4 |
| | `_boundary` (3118-3340) | builds the offer; the decision's detail (`lesson_offers`, `lesson_offer`, `followup_contest`); whether the offer won; an offer skips supersession and the objective's arms | 1, 3, 4 |
| | `_persist_block` (2977), `_replace_open_offers` (2900-2925), `_supersede_offer` (3435), `_followups_lost` (3442) | a new offer supersedes the open ones; follow-ups lost to a lesson | 4 |
| | `_lessons_compete` (3376), `interrupt_offer` (3508), `place_interrupt_offer` (3532-3541) | IH2's offer at a mid-block boundary | 1, 5 |
| | `_followup_contest` (3425-3431) | the contest candidate | 1 |
| | `_frozen_objective` (3788) | stop's frozen support | 5 |
| | `_insert_followups` (4598-4601), `_place_followup_probes` (4720-4735), `prefetch_boundary` (5601-5624) | an offer block counts as a boundary | 7: traversal |
| | `_restrained_followups` (4876-4894) | the offer won the mid-block decision | 4 |
| | `_lesson_offer_step` (5092-) | the step payload (`"kind": "lesson_offer"`) | 5 |
| | `_device_block` (5185), `_held_step` (5275) | the phone holds a drawn offer for the desktop | 4, 5 |
| | `advance_with_context` (5382-5486) | serving an offer block: withdrawn (offers off, or forced items arrived), `ignored` when the learner moves on, otherwise the card | 4, 5 |
| `daily_plan/records.py` | module (34), `PlannedBlock.is_lesson_offer`, `interrupts`, `followups_lost`, `est_minutes`, `finished`; `PlanRecord.current_block`, `block_below_offer`, `open_lesson_offer(s)` (157-325) | an offer block's minutes (0), when it is finished, and its place in the plan | 5 |
| `daily_plan/view.py` | `_block_row` (143), `_offer_card_shown` (151) | the offer row in the plan view | 5 |
| `daily_plan/learner_action.py` | module (58), `_waiting_block`, `_plans_pick_label`, `_frozen_inputs`, `options`, `_end_offer`, `_lesson_view` | the learner's options by preference kind; an offer the choice replaces ends superseded | 4, 5, 6 |
| `daily_plan/` `lesson_suggestion.offer_card_view` (688), `objective_card._card_topics` (164), `objective_seeds.bare_row` (69), `plan_records` (159) | | the offer card's view; the card's topics; the seed row without the card; mid-block record codes | 5, 7 |
| `router/plan_log.py` | module (72-73, 521), `build_plan_block_decision` (304-309), `_offer_arm`, `_offer_detail`, `drawn_lesson_on`, `held_a_lesson` (528-569) | the decision row's offer and contest detail, offer candidate rows (`"kind": "lesson_offer"`) | 5 |
| `router/requests.py` | `lesson_offer_description` (113), `STOP_DESCRIPTION`, `STOP_OFFER_DESCRIPTION` (126-129) | the LLM policy's words for an offer and for stop | 7: LLM option wording |
| `router/why.py` | `SENTENCES` (50-55), `stop_code` (162) | the plain sentence for an offer and for stop | 6 |
| `router/` `decisions` (45-46), `lesson_suggestions` (429, 455) | | stop's and continue's refs; TE1b's lesson kind | 5, 7 |
| `db/stores/router_suggestions.py` | module (79), `_offer_decision`, `offer_decisions`, `offer_decision`, `offer_drawn_since` | which decisions are offers (prefix match) | 4, 5 |
| `followup_run/` `router` (38-40, 76, 236), `jobs` (421), `decision_view` (40); `followup_serve/workflow` (67) | | a follow-up that lost to an offer; the label | 4, 6 |
| `teacher/diagnosed_sources.py` (73, 328), `why/reconstructed.py` (42), `refusal_records.py` (378), `params/parameter_registry.py` (251, 555-565) | | the offer prefix repeated; the gate record; the offer module's priors | 6, 7 |
| `scheduling/device_eligibility.py` | `PlanStepFilter.held_lesson_offers` (357) | the phone's held offers | 4 |
| `learnloop_sidecar/handlers/daily_plan.py` | (646-648) | `lesson_offer.record_shown` | 5 |
| Desktop (`apps/learnloop-tauri/src`) | `api/dto.ts` (`PlanLessonOfferStepDto`, `kind: "lesson_offer"`), `app/App.tsx` (1243, 1276), `app/dailyPlan.ts` (193), `screens/today/{DailyPlanView,TodayPlace,LessonOfferBlock,LessonOfferPage}.tsx` | the offer card, its page and routing | 5, 6 |
| Phone, terminal app, MCP | none by name. The phone holds offers through the engine's device path. The terminal app may not import `daily_plan` (import contract). MCP reaches no plan | — |

The offer's ref and subtype (`lesson_offer`, `lesson_offer:`) are spelled in **15 modules**, mostly copies kept equal by
tests: `daily_plan/types`, `trace_assembly`, `preferences`, `preference_report`, `plan_log`, `forecast_resolve`,
`miss_cause_report`, `offer_report`, `db/stores/router_suggestions`, `followup_run/router`, `followup_run/decision_view`,
`followup_serve/workflow`, `teacher/diagnosed_sources`, `why/reconstructed`, and `objective_inputs`'s
`lesson_offer:declined`. Stop's ref (`stop_for_today`) is spelled in 9 (`daily_plan/types`, `stop_coin`,
`forecast_resolve`, `sessions`, `router/decisions`, `plan_log`, `records`, `learner_action`, and literally in
`objective_report` and `preference_report`).

## 2. Step 0b: the TE3b replay, measured (the base count)

On a scratch branch at the base, now deleted (the patch is in the step's scratch directory as `te3b_replay_base.patch`;
it was never pushed), I added a dummy kind shaped like the lesson offer. It is an offer with two branches and a delayed
check: objective kind `trial`, plan subtype `trial_offer`, ref `trial_offer:<LO>`, `accept` Beta(2, 2), 10 minutes
log-normal, γ at its mass as its effect, and a 3-day check committed. It was wired end to end far enough that the
chooser values it and the trace labels it. A scratch test (not kept) built a vault with `tests/router_mixture_helpers.mixture_env`
at the head tag, with TE1b's candidates emptied so that the lesson builder offers nothing. The trial offer joined the
objective's support, and its trace row read `offer a trial on Diagonalization (about 10 min)`, kind `trial`, branches
`accepted` 3.164, `declined` 3.183, `p_accept` 0.497, with its own `offer` section. Nothing else was required to pass.

**Base count: 10 files, 17 definitions** (enclosing definitions of the diff's hunks, by AST; a new file counts whole):

| File | Definitions touched | What the dummy needed |
|---|---|---|
| `router_objective/types.py` | module only | the constant, `KINDS`, `__all__` |
| `router_objective/rollouts.py` | `_Model.apply`, `_Model.value` (plus the import) | its effect arm; its branch terms beside `lesson`'s |
| `daily_plan/types.py` | module only | the subtype and prefix |
| `daily_plan/trial_offer.py` (new) | `build`, `action_inputs` | the boundary's candidate and what the value reads from its card |
| `daily_plan/policy.py` | `policy_for`, `_trial_offer_builder` | the builder's wiring |
| `daily_plan/engine.py` | `PlanPolicy` (class body), `_boundary` | the builder slot and its call at the boundary |
| `daily_plan/objective_chooser.py` | `_trial_option` (new), `ObjectiveChooser.choose`, `ObjectiveChooser._start_objective` (plus the import) | out of staged's feasible set and into the support; its LLM option row |
| `router/requests.py` | `trial_offer_description` (new) | the LLM policy's words for it |
| `daily_plan/objective_inputs.py` | `action_for`, `build` (plus the import) | its `Action`; its declined branch; kept out of the tail's block |
| `router_objective/trace_assembly.py` | `option_kind`, `option_label`, `candidate_row` (plus constants) | its option kind, label and trace section |

78 lines added and 7 removed in existing files, and 39 in the new module.

**What serving it to the learner would add.** These are counted from the lesson offer's own sites in §1, not
implemented. In `engine.py`: the decision detail, supersession of open offers, withdrawal when offers are switched off
or forced items arrive, `ignored` when the learner moves on, the step payload, and the phone's hold. Also
`records.py`'s offer predicates and minutes, `view.py`'s row, `plan_log.py`'s detail and candidate rows,
`learner_action.py`'s options and supersession, `router/why.py`'s sentence, `followup_run`'s lost-to-offer path,
`forecast_resolve.py`'s binding, the offer report, the response store, the sidecar's shown event, and the desktop's DTO,
card, page and routing (7 files). With a tag: `algorithm_versions.py`, `ops/upgrades.py` and `tests/test_upgrades.py`.
That makes 20 or more files, which agrees with the strategy's "20 files". No `actions.py` can reach these sites: each is
the shape of one surface or one database write, and most sit on engine traversal, which the strategy keeps where it is.

## 3. Step 0c: the design on paper

`src/learnloop/router_objective/actions.py`: one function per kind, dispatched by a plain `match` on the kind, giving its
candidate, its rollout step, its trace label and its reversibility.

### What could move there, file by file

| From | What | Moves? | Cost |
|---|---|---|---|
| `trace_assembly.py` | `option_kind`, `option_label`, `_offer_trace`, the offer branch of `candidate_row` | yes, as moves (AST-identical but for annotations) | none: they already read only attributes |
| `objective_chooser.py` | the offer filter in `choose`; `_offer_option`, `_contest_option` and the option dispatch in `_start_objective` | yes, if `actions.py` imports `router.requests` and `router.why` (`_option` is `router_chooser`'s, shared with `RouterChooser`) | the LLM rows of two choosers split across modules |
| `router/requests.py` | each kind's option wording (`lesson_offer_description`) | only if the prompt text leaves the request module | prompt text out of its module: the change-cost table keeps a prompt in "its module" |
| `objective_inputs.py` | `action_for`'s per-kind branches, `_step`, `build`'s offer tests | only as a **rewrite**: `action_for` becomes a gather (items' modes and topics, reading topics through a callable, the card) and a dispatch, because its branches read `vault` and `repository` | not a move; the brief asks for moves |
| `lesson_offer.py` | `action_inputs` | yes | — |
| `router_objective/types.py` | the kind constants and `KINDS` | only together with `Action` (measured below): if the kinds alone moved, `types` (`Action`'s validation) and `actions` (which builds `Action`s) would import each other | reverses E5's placement of `Action`; 12 test files name `OT.Action` |
| `daily_plan/types.py` | the offer's subtype and prefix | possible (`daily_plan` may import `router_objective`) | 3 of the 14 other copies cannot follow: `router/plan_log`, `db/stores/router_suggestions` and `followup_serve/workflow` sit in packages that `router_objective` imports, so importing back would make a package cycle (the package-level contract). Their held-equal tests stay |
| `rollouts.py` | the rollout steps | **no** (next table) | — |
| `engine.py`, `policy.py`, the builder module | building the offer and wiring the builder | **no**: engine traversal stays (the strategy's limit), and the builder's sensors are database reads in `daily_plan` | — |

### The rollout step of each kind, and what the one place can hold

| Kind | Where its step is | Callable from one place without restructuring `_Model`? |
|---|---|---|
| `review`, `new_practice`, `teach_back` | `apply`'s `PRACTICE_KINDS` arm, calling `_practice` per slot | the step is `_practice`, already a named method; the kind's part is membership in `PRACTICE_KINDS` |
| `repair` | the same arm, plus `_cause_gain` (SG2) | named (`_practice`, `_cause_gain`) |
| `reading` | `apply`'s `READING` arm, calling `_read` per LO | named (`_read`) |
| `lesson` | `apply`'s `LESSON` arm (about 25 lines of masked updates inline: γ or the cause split, TE3a's shift and spread along γ's stream, the lesson count) and `value`'s `branch_terms` | **no**: the arm is not a method. Making it one moves F2's arithmetic out of the class (E5 judgment call 2) |
| `probe` | `_segment` (observe instead of apply), `value` to `_probe`, `_probe_choice`, `_belief_model` | named (`_probe`), but whether it observes is decided inside `_segment` |
| `stop` | `value`'s `STOP` arm (inline: `_stop_accepted`, the overridden branch, the return effect), `_effect_correction` | inline in `value` |
| `sequence` | `_steps` and `_do`, by the field `steps` | named; chosen by a field, not by kind |
| any offer | `value`'s offer arm, by the field `accept` | chosen by a field, not by kind |

So `actions.py` can hold only a pointer: kind to the `_Model` methods that accrue it. A new kind with its own arithmetic
still edits `apply`, so `rollouts.py` stays in the count.

### Import order (measured with hypothetical edges)

`cycle_whatif.py` (E5's script, untracked files included) was run with the edges `actions -> router_objective.types`,
`actions -> router.requests`, `actions -> router.why`, and `rollouts`, `trace_assembly`, `objective_inputs`,
`objective_chooser`, `lesson_offer`, `daily_plan.types`, `engine`, `records`, `view` and `preferences` each importing
`actions`. Result: the largest component stays 84 and the number of modules in a cycle stays 220, so `actions.py`
would join no cycle. Adding `types -> actions` (kinds in `actions.py`, `Action` left in `types.py`) puts the two in a new
cycle (220 → 222). Hence the table's condition: the kinds move only together with `Action`.

### Predicted count for the same dummy after the design

The best case takes every placement in the first table, including the four contested ones (kinds and `Action`, the
plan's subtype names, the prompt wording, `action_for`'s rewrite). It still touches **5 files**: `actions.py`,
`rollouts.py` (`apply`), the new builder module (`build`), `policy.py` and `engine.py`. That is exactly half of 10.

Definitions depend on how "one function per kind" is dispatched:

- **Plain matches, one entry per part.** Each part has its own inputs and call site: the candidate, the option kind,
  the label, the trace section, the offer predicate, the LLM option row, the branch-terms test, the rollout-step pointer
  and reversibility. A new kind adds its own functions (`trial`, `_trial_trace`, `_trial_option`) and a case in each of
  the nine dispatchers: 12 definitions in `actions.py`. Add `apply`, `build`, `policy_for`, the builder, `PlanPolicy`
  and `_boundary`, and it comes to **18 definitions, more than the base's 17**. The base spreads its cases over
  functions that exist anyway; the design adds the dispatchers.
- **One function per kind answering a part selector** (`def trial(part, **inputs)`, with one `match kind` calling it):
  2 definitions in `actions.py`, **8 in all** (under half). But every kind's function then has to answer every part name
  with heterogeneous keyword inputs. That is a plugin protocol without the base class.

The realistic design leaves the prompt text in `requests.py` and the plan's names in `daily_plan/types.py`, and so
touches **7 files**.

**Lines.** Outside `actions.py` the design would remove more than it adds: roughly 230 lines leave the callers, against
about 40 of imports, calls and the gather. The line rule does not stop it; the count does.

## 4. Step 0d: the stop rule's verdict

| Test | Result |
|---|---|
| Predicted count at most half the base count | **Fails.** Files: 5 of 10 (exactly half) only in the best case; 7 of 10 realistically. Definitions: 18 of 17 with plain matches; 8 of 17 only with a part selector |
| Adds no more lines than it removes outside `actions.py` | passes (estimated, about −190) |
| Needs nothing beyond one function per kind and a match | **Fails** at the only form that meets half on definitions (the part selector is a protocol). The plain form also has to bridge the three vocabularies of §1: a block's objective kind is decided from data, so "one function per kind" cannot give both the label (per plan option) and the rollout step (per objective kind) |

**Stop after step 0.** No source edit was made.

## 5. The smallest alternative

Each piece below changes no served or persisted value, and none needs a registry.

1. **A guard against a half-made kind** (T3, plain values, no vault). One test that, for every kind in `types.KINDS`,
   builds an `Action` and checks it is handled where the code branches on the kind. In `rollouts`, `apply`, `_segment`
   or `value` must change the state or the ledger, unless the kind is one of the declared field-driven kinds (`stop`,
   `sequence`). In `learned_tail`, `kind_group` must be told explicitly whether the kind is practice. In
   `trace_assembly`, `option_label` must label each plan option kind. This is the one part of the brief's build that pays
   without `actions.py`: today a kind missing from `apply` is silently valued with no effect, and `kind_group` silently
   calls any new kind "practice". Neither is a bug at this tip, because every current kind is handled.
2. **One offer predicate.** `subtype == LESSON_OFFER_SUBTYPE` (or `!=`) is spelled at 17 sites (chooser 5, engine 4,
   `objective_inputs` 2, `lesson_offer` 2, `records`, `objective_card`, `preferences`, `trace_assembly`). `lesson_offer.is_offer` exists and
   has no caller. Used everywhere, a second offer kind would change one predicate instead of 17 sites. In the replay that
   saves `choose` and `build` (2 definitions), not a file.
3. **One definition of the offer's and stop's refs where the import graph allows.** In `router_objective/types.py`
   (`daily_plan/types.py` would import it), 11 of the 14 repeated `lesson_offer` copies could read one name. The copies in
   `router`, `db` and `followup_serve` cannot (package cycle) and keep their held-equal tests.
4. **"How to add an action kind" in the Router Objective note** (§6's list), so a reader starts in one place and is
   pointed to each part. This is the honest form of the pointer `actions.py` would have held.

Items 1 and 4 are small (one test file and a note section). Items 2 and 3 are mechanical edits over about 30 sites, with
P-draw as their proof.

## 6. What E7, TE4, RE3 and RE5 should know: adding an action kind at this tip

The replay's list, in order. The four lines marked † are the ones no design under the strategy's limits removes.

1. `router_objective/types.py`: the kind constant and `KINDS` (and `PRACTICE_KINDS` if it learns as practice).
2. † `router_objective/rollouts.py`: its arm in `_Model.apply` (or `_segment` if it observes), and `value` if it reports
   branch terms. If it has none, it is valued with no effect, silently.
3. `router_objective/learned_tail.py`: `kind_group` (it is otherwise "practice"). An indicator of its own is a features
   version, which is an RO6 change point.
4. `daily_plan/types.py`: its subtype and ref prefix, if it is a plan option of its own.
5. † Its builder module in `daily_plan` (its candidate with `reversible`, `reason_code` and its card), and
   `action_inputs`.
6. † `daily_plan/policy.py` and † `daily_plan/engine.py` (`PlanPolicy` and `_boundary`): the builder's wiring.
7. `daily_plan/objective_inputs.py`: `action_for` (its `Action`) and `build` (its declined branch, kept out of the
   tail's block).
8. `daily_plan/objective_chooser.py` and `router/requests.py`: the support position and the LLM option row.
9. `router_objective/trace_assembly.py`: `option_kind`, `option_label` and its trace section.

Then, to serve it: the engine's step, withdrawal and supersession; `records`, `view`, `plan_log` and `why`; the response
store and forecast binding; the sidecar and the desktop (§2). With a tag: the playbook's three files.

## 7. What was run, and what was not

- The replay (§2) on a scratch branch at the base: one scratch test, 1 passed, in a 5 GB scope. The branch was deleted;
  its patch is kept in scratch. No `pytest` run on this branch: no source or test file changed.
- `cycle_whatif.py` on this worktree (§3): base 84 / 220, design 84 / 220, with `types -> actions` 84 / 222.
- Not run: the targeted gate, P-draw, P2, identity pins and lint, since nothing in `src` or `tests` changed. Vault
  references were not regenerated, because no source changed.
- Not verified: the predicted counts are on paper, not built. The line estimate in §3 is a count of the bodies that
  would move, not a diff.
- Implementer: one Opus session, no subagents. Token use is not visible from inside the session.
