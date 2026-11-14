# Refactor I2: the due queue, step 0 (stopped before extracting)

Branch `refactor/i2-due-queue-core`, based on main `6c114e2ae1`. Step I2 of arc I (`docs/specs/refactor_strategy_v3.md`
§2.9, finding F4). Structure track. Line numbers are at the base, in `src/learnloop/scheduling/scheduler.py` unless
another file is named.

**Outcome.** The step stops at step 0, as its brief says to when the pure core would need more than two stages. With
the reads the build makes today, a pure `rank_due` needs a shell read at five points that depend on an earlier
decision of the build (§3), so it would be cut into four or more pure stages. Two stages are reachable only by
reading supersets ahead of the build (more reads than today, done whether or not a decision needs them) and by turning
three objects from other modules into frozen snapshots: the DL2 intent view (`scheduling/intent/serving.py`), the
device filter (`scheduling/device_eligibility.py`) and the value-of-information context (`diagnosis/voi_stopping.py`).
That is more than one review-and-gate cycle, and it changes which reads a build makes, which the brief did not
authorize. Separately, two writes run on today's read path, so read callers cannot move to a pure path without
changing written rows (finding I2-1). No source changed; §5 gives the options.

## 1. The function, stage by stage

`build_due_queue` is `scheduler.py:186-1014` (829 lines). Its admission and scoring live in `_BuildAdmission`
(`:3127-3523`, 397 lines, `probe_score` alone `:3341-3497`), which also serves `check_admission` and `pool_admission`
outside the build with lazy reads (`_Once`, `:3084`; `_outside_build_admission`, `:3590`).

Key: **R** read (repository, clock, config, vault), **W** write, **D** decision, **S** seeded draw. "persist" is
`persist_explanations`.

| # | Lines | What | Kind |
|---|---|---|---|
| 1 | 208 | `now` from `clock` (UTC); `session` defaulted; `config = vault.config` | R clock, config |
| 2 | 213-222 | `records_slate = persist and session_id`; `withheld` appends to the trace's or a local exclusions map | D |
| 3 | 224-244 | `reconcile_diagnostic_surface_needs`, `reconcile_empty_probe_pools` (needs, commissioning, maintenance notices) | W, persist only |
| 4 | 246-255 | `calibration_cap_lifted(repository, session_id)`; `probe_serving_block_reason` (episodes, session observation counts) | R |
| 5 | 260-268 | `voi.VoiContext(vault, repository)` (lazy: latencies, routes, durations, unresolved cost); `voi_probe_active`, `carry_hypothesis_channels` from config | R lazy, config |
| 6 | 269-280 | `practice_item_states`, `practice_item_quality_states`, `routine_serving_exclusions` (exam reserve, held-out, rung holds, staged-owned, generated probes) | R |
| 7 | 290-298 | `_intent_serving` (DL2 view: commitments, FSRS weights; checks, anchors, eligibility and the check gate are lazy closures over the repository); `requested_practice_item_ids` | R, R lazy |
| 8 | 309-316 | `_placement_serving(persist=...)`: on persist, `hold_queued_live_diagnoses` and `reconcile_fast_track` (assumption decisions, queue revision) **before** its reads; then placement state, predictor, out-of-timing exclusions | W persist, then R |
| 9 | 317-330 | `mastery_states`; open episodes (`servable_open_episodes` when placement serves, else `open_probe_episodes`) | R, D (which reader) |
| 10 | 331-337 | `active_error_events`; `short_session`, `readiness_factor` from session and config; `resolve_fsrs_weights` | R |
| 11 | 340-346 | `pending_followup_practice_items(clock)`; `_defer_revealed_cold_followups(persist=...)`: per task a decision, its writes applied in the loop when persist | R, D, W persist |
| 12 | 349-368 | `facet_states_by_lo`; `build_goal_frontier`; `resolve_head` per active goal | R |
| 13 | 379-395 | `list_recent_attempts_by_learning_objects(frontier.by_lo)`; `held_attempt_ids` marks held rows | R |
| 14 | 403-427 | `_BuildAdmission` over the values read so far (`_Once.of`) | D (predicate) |
| 15 | 428-441 | intent: `bind_admission` (the view calls back into the build's admission), `filter_requests` forces the check split, which runs the check gate's reads for every candidate; pending follow-ups filtered by `withhold_reason` | D, then R (depends on 14) |
| 16 | 442-448 | follow-ups filtered by `_held_for_device` (the device filter's media predicate; mutates `device_filter.deferred`) | R callback, mutation |
| 17 | 450-580 | the candidate loop: `admission_reason` per item (`serving_exclusions.py:263`: routine gate, generated-probe reserve, intent gate, freshness, placement, cold start, probe gate, device gate); reserved probe surfaces annotated; `probe_score` (lazy reads below); `score_selection_reward`; floors; `_plain_english` | D, R lazy (18) |
| 18 | `:3396-3495` | inside `probe_score`, only for in-probe items that passed the earlier gates: `administered_surface_exclusions` (once), `_load_episode_context` and `_load_episode_eligible` (per episode, cached), `voi.probe_episode_decision` (per episode: loss tables, durations, observation counts through `VoiContext`), `familiarity_discount(repository, item)` per item | R (depends on 17) |
| 19 | 582-590 | sort by (-selection reward, -priority, id); `_order_new_material` reads `taught_first_by_predecessor` for the new-material slots' LOs | D, R (depends on 17, 19) |
| 20 | 593-603 | due "Check once" picks (`pick_checks`, pure over the forced checks) | D |
| 21 | 607-623 | `_selection_propensities` (design probabilities); `_teach_back_value_admission` over the greedy order through `VoiContext` (latencies; the teach-back site values with an empty prior, so nothing else) | D, R (depends on 19-20) |
| 22 | 624 | `_apply_seeded_exploration`: `_stable_fraction` = sha256 of (label, session id, UTC date of `now`, sorted candidate ids), labels `roll` and `choice` | S |
| 23 | 626-662 | `compose`: teach-back cap or value admission, goal quota, requested floor, same-day rotation, `generated_probe_ids(repository)` + follow-up insertion, contrast-pair order (`plan_contrast_pair_serving`: hash of session or pair) and, with `record=True` and a session, `record_contrast_pair_servings` | D, R, S, **W whatever persist says** |
| 24 | 663-701 | `active_probe_presentation_for_session`; `end_probe_presentation` when the probe is blocked or the assigned item is not in the composed queue (unless held for the device); pin | R, D, **W whatever persist says** |
| 25 | 702-712 | `considered`; `limit` slice; `shadow_intent_plan` (pure) when the probe shadow is on | D |
| 26 | 715-956 | persist with a session: explanations; cold-deferral merge; the head probe's presentation payload (episode context and eligibles from the caches, `routine_planner_shadow`, `active_probe_presentation`, `robust_gate_counterfactual`, `_composed_head_probability` re-running `compose(record=False)` per draw outcome, `presentation_commit_payload`); `active_error_events_overlaid`; decision features; `record_scheduler_slate` (with the presentation); `scheduler_slate_candidates`; `record_offer_value_forecasts`; `record_presentation_forecast`; `insert_scheduler_explanations`; `_record_probe_elicitation` | R, W |
| 27 | 957-990 | `_fill_offer_trace` when a trace is passed: every draw outcome recomposed by `compose(record=False)` (each call re-reads `generated_probe_ids`) | R, D |
| 28 | 991-1013 | `record_slate` (ADR-017 decision record) when the slate was recorded | W |

Draws: only two, both hash-seeded with no RNG state: the exploration tie-break (22; its seed is the session id, the UTC
date and the candidate set) and the contrast pair's member order (23; session and pair, or the pair alone when
`contrast_order_seed == "pair"`). The router's pinned draws (`tests/pinned_draws.py`) are not reached here. Both seeds
are plain values a core could take as inputs.

## 2. Callers

`build_due_queue` has 12 call sites in `src` (`learnloop`, `learnloop_sidecar`; none in `learnloop_mcp` or
`learnloop_mobile`, which reach it through the sidecar), two scripts and 70 test or helper files (117 uses of
`persist_explanations` in tests and scripts).

| Caller | persist | Session | Other flags | Uses |
|---|---|---|---|---|
| `cli/app.py:2058` `review` (re-exported by `cli/runtime.py:99`) | default (True) | none | `limit` | prints the queue; with no session it reconciles (3, 8, 11) but records no slate |
| `daily_plan/engine.py:844` `PlanEnv.build_eligible` | default | `plan_scheduler_session` | `offer_trace` when receipts are on | the plan's pool; the trace for the prefilter receipt |
| `learnloop_sidecar/handlers/daily_plan.py:179` `eligible` | `not prefetch` | `plan_scheduler_session` | `limit=None` | the plan's pool; the prefetch reads through a read-only attach |
| `learnloop_sidecar/handlers/queue.py:175` today's queue | default | the request's | `limit`, `offer_trace`, `device_filter` | `publish_offer`, slate id |
| `learnloop_sidecar/handlers/practice.py:2034` skip and requeue | default | the session's | `offer_trace`, `device_filter` | `publish_offer` |
| `learnloop/tui/state.py:55` | default | given or none | | the TUI list |
| `learnloop/sim/runner.py:351` | False | `sim-s{seed}-d{day}` | `clock` | the day's top items |
| `scheduling/staged_policy.py:692` `_comparator` | False | the staged session | | legacy priorities, shadow only |
| `learnloop_sidecar/handlers/facets.py:62`, `knowledge_map.py:84` | False | none | | priorities and components for charts |
| `scheduler.py:2831` `explain_practice_item` (used by `why/reader.py:336`, sidecar `queue.py:361`, `serializers.py:347`) | False | none | | one item's row |
| `scheduler.py:2849` `exclusion_now` (`why/reader.py:380`) | False | none | `offer_trace` | the trace's exclusions |
| `scripts/voi_cap_report.py:162` | False | `voi-report` | `offer_trace` | timing and the trace's decisions |
| `scripts/benchmark_sqlite_concurrency.py:227` | True | none | | timing |

Read callers with a session (the sim, the staged comparator, the prefetch, the VoI report script) are the ones finding I2-1 is about.

## 3. Reads that depend on an earlier decision

Each is a point where a pure core would have to stop and hand back to the shell, if the build is to read what it
reads today and no more.

1. **The check split (15).** Forcing DL2's checks asks the build's own admission predicate (14) of every check
   candidate, then runs the check gate's reads (`CheckGate`, eligibility, the follow-up gate) for them. The predicate
   is pure only once 5 below is hoisted.
2. **The probe reads (18).** Made per in-probe item, only for items that passed the earlier gates of
   `admission_reason`, and they feed both the probe gate (an admission decision) and the score.
3. **The device's media predicate (16, 17's device gate, 24).** A callback the host supplies, asked last for each
   item that passed every other gate, and for follow-ups and the pinned presentation; it also accumulates
   `device_filter.deferred`, which the sidecar reads after the build.
4. **taught-first (19).** Read for the LOs of the new-material slots in the ranked queue.
5. **The teach-back value admission (21).** Valued over the greedy order through `VoiContext`, which reads latencies
   on first use (here, when no probe decision loaded them).

Hoisting to supersets would remove 2-5 as boundaries: read every in-progress, unblocked episode's context, eligibles,
VoI decision and familiarity before the loop (the recorded VoI decisions filtered to the episodes an item consulted,
in consult order, so rows stay identical); ask the device filter of every item; read taught-first for every LO when
placement serves (`placement/signals.py:82` computes for all LOs and filters, so the values are the same); load the
latencies up front and give the teach-back site a context with no repository. That leaves one boundary (1), so two
pure stages. The costs: more reads than today in every build that has an in-progress episode none of whose items
reaches the probe gate, in every phone build (the media predicate for every item), and in every placement build with
no new material; a read that raises for an episode the build never consulted now fails the build; and the intent
view, the device filter and `VoiContext` each need a frozen form, with `_BuildAdmission` losing its repository while
`check_admission` and `pool_admission` keep lazy reads.

The pre-ranking writes (3, 8, 11) are interleaved with reads in a fixed order (8's fast-track writes before
placement's reads but after 4-7; 11's deferral writes before 12-13). A shell can keep that order exactly, but only by
knowing whether it serves, so the flag moves into the shell's gather unless those writes are first shown to commute
with the reads around them (not done here).

## 4. What pins it today

- Seventy test files call the build. Whole-queue assertions: `tests/test_scheduler_golden.py` (ordering, ties,
  forgetting risk on small vaults, no session). Feature assertions: probe EIG and presentations
  (`test_scheduler_probe_eig.py`, `test_probe_episodes.py`, 14 files touch probes), placement (22), DL2 intent and
  checks (27), contrast pairs (`test_contrast_pairs.py`, 7), teach-back caps and value (8), cold deferrals (7),
  exploration and propensities (`test_router_offer_log.py`, `test_router_probe_ties.py`, 9), slates and explanations
  (15), follow-ups (35). `tests/test_plan_determinism.py` pins the plan's pool order across sessions.
- No test pins a whole queue with explanations, the draws and every written row on a vault that has a probe episode,
  placement, a due check, a teach-back and a contrast pair at once. An extraction needs such goldens first (states
  built with `tests/helpers.py`, `tests/assumed_known_helpers.py`, `tests/intent_fakes.py`, `tests/voi_stopping_helpers.py`
  and the contrast-pair vault in `tests/test_contrast_pairs.py`, each built under a session and without one, recorded
  at the base).
- The draw-for-draw harness of `docs/reviews/router-speed2.md` ("Identity") is not in the repository; P-draw would be
  rerun from that description.

## 5. Options

- **A (recommended): three sub-steps, each one gate.** I2a: freeze the admission's reads (probe reads per episode
  hoisted, the device refusals asked once per item, `_BuildAdmission` without a repository; outside readers keep
  `_Once` readers), with the goldens above recorded first. I2b: a frozen DL2 intent view after the check split (the one
  shell read between the stages) and a `VoiContext` with loaded latencies and no repository for the teach-back site.
  I2c: `rank_due` in two pure stages, the persist call, `serve_due_queue` and `read_due_queue` replacing the flag, the
  117 test uses ported (a mechanical script), measures and P-shadow. Needs the owner's word that superset reads are
  acceptable (they move latency, not values), and I2-1 decided first.
- **B: the stages as they fall.** No superset reads: the core is cut at each of §3's five points, the shell reading
  between them. Exact read set, but four or more stages, each small; the brief's limit is two.
- **C: only the persist split now.** Move 26-28 and the read-path writes of 23-24 behind one persist call the serving
  callers make, and remove `persist_explanations` from the read callers' signature (`read_due_queue`), with admission and
  scoring left as they are. Removes the write flag from the read path's API and gives a smaller function, but no
  pure ranking core; it is blocked on I2-1 in the same way.

## 6. Finding I2-1 (ledger)

A build with `persist_explanations=False` and a session writes. `_apply_contrast_pair_order` (`:2530`) records
contrast-pair servings whenever it has a session (`compose(..., record=True)`, line 662), and `end_probe_presentation`
(lines 668-673 and 696-700) invalidates the session's committed presentation; neither looks at the flag, while the
docstring (lines 203-205) and the comment at 228-230 say a read writes nothing. Shown on the base with a scratch test
(not committed): the contrast-pair vault of `tests/test_contrast_pairs.py` built with `session_id="sess_read"` and
`persist_explanations=False` writes 2 `contrast_pair_servings` rows. Read callers that pass a session: the sim (its own
vaults), the staged comparator (`staged_policy.py:692`: a shadow comparison; serving rows are first-write-wins per item
and session, so its row can stand for a serving the learner never got), and the plan prefetch (a read-only attach: the
contrast write fails and is logged, and a presentation invalidation would raise, so that prefetch returns
"unavailable"; by reading, not run). Moving read callers to a pure path changes those rows, so it is a behaviour
decision, not part of a structure step.

## 7. Measures at the base

`build_due_queue` 829 lines; `_BuildAdmission` 397; `scheduler.py` 3,862. No source changed, so the structure ratchet,
identity pins and functions over 200 lines are unchanged.

## 8. The I2-1 fix (coordinator's decision on step 0: the goldens, then I2-1 as the persist split)

This is option C, done as the fix for I2-1. It lands alone (behaviour track) with no algorithm tag: it removes
writes no spec asked for, and §8.5 checks that replay and the shadow rebuild do not read the fields involved.
Commits, in order:

1. `131f7abdb6`: whole-queue goldens at the base (`tests/test_due_queue_golden.py`, `tests/due_queue_helpers.py`,
   `tests/goldens/due_queue/`). The vault is one synthetic vault with these pieces:
   - DL2's intent vault: three practised LOs due now, and placement's never-practised LOs as new material;
   - a due "Check once" on `lo_a`;
   - an in-progress probe episode with two admitted instruments, and a presentation the session committed an hour
     earlier (value stopping was off for that one build);
   - a teach-back on the probe's LO;
   - a contrast pair on `lo_c`;
   - a cold retry deferred because its answer was shown after it was set;
   - a wide exploration window, so the draw has near-ties and explores.

   It is built three ways: a serving build with that session, a read build with the same session, and a read build
   with no session. Each record pins:
   - the returned queue (ids, order, priorities, components, explanations, reward debug, slate and candidate ids);
   - from the offer trace: the exploration's support, roll, choice, realized item and every outcome's composed
     order, plus the exclusions, cold deferrals, pin and VoI decisions;
   - every row the build added, changed or removed, table by table.

   Ids read `<ulid:n>` in order of first appearance. The ULID stream is also seeded, but how many ids the setup
   mints varies with the hash seed, so one decision-record id moved under `PYTHONHASHSEED=1`, and ids are therefore
   numbered rather than kept. Floats are rounded to ten places. The goldens pass under `PYTHONHASHSEED` 0, 1, 12345
   and 777 at `-n 4`. `test_the_vault_reaches_every_stage` fails if the vault stops reaching a stage.
2. `3c189d12f5`: I2-1's fail-first tests (`tests/test_due_queue_read_builds.py`). At the base, four are red for the
   bug's reasons:
   - a read build with a session writes 2 `contrast_pair_servings` rows;
   - it ends the session's committed presentation when the composition leaves it no place;
   - the plan prefetch's own pool build (`_env(prefetch=True).eligible`) on a read-only attach raises
     `attempt to write a readonly database`, after logging the failed contrast write;
   - `staged_policy.decide` leaves the comparator's 2 serving rows.

   The serving build's own invalidation is the green control.
3. `6c7918046e`: the fix.

### 8.1 What changed

- `persist_explanations` is gone. `build_due_queue` is the serving build and `read_due_queue` the read; both call
  `_due_queue(..., serving=...)`. I kept the name `build_due_queue` for serving because every caller that omitted
  the flag already got the serving build, so 60-odd call sites keep their meaning and their text.
- Every write after the composition is in one persist step, `_persist_offer`, which only a serving build with a
  session reaches. It runs, in order:
  1. it ends the presentation the composition left no place for (or that a probe block invalidated);
  2. it records the contrast pairs' drawn order (`compose` now returns it, and `_apply_contrast_pair_order` no
     longer takes a repository);
  3. it writes the slate block that was inline, unchanged and moved: explanations, the head probe's presentation
     (now `_head_probe_presentation`), decision features, slate, candidates, value forecasts, presentation
     forecast, explanations, elicitation.

  The slate's decision record (`record_slate`) is the one write left after the offer trace, still only on the
  serving path with a session. The trace has to be filled first, because its counterfactual compositions copy the
  `probe_committed` component the persist step stamps.
- For serving builds, the invalidation and the contrast record now come after the presentation decision instead of
  inside the composition. Nothing read between the old and new positions depends on them: the shadow-intent plan is
  pure, and the persist step's presentation reads come after the invalidation, as before. The serving golden is
  byte-identical.
- A serving build's writes before ranking keep their place and order, still guarded (`serving`): surface-needs and
  empty-pool reconciliation, placement's hold and fast track, and the cold lane's deferral writes. They sit between
  reads that must see them (placement reads its state after the fast track), so they cannot move behind the persist
  step without reordering.
- A read build still writes one thing: `Repository.due_followup_tasks` marks due tasks `served` and lapsed ones
  `expired`, and releases cold reservations. These are documented lazy marks inside the repository read, which a
  read-only attach skips. The no-session read golden shows the mark (`followup_tasks`: 1 changed, `pending` to
  `served`). Removing it would change rows outside the allowed delta, so it stays: ledger I2-2.

### 8.2 The flag's fate per caller

| Caller | Before | After |
|---|---|---|
| CLI `review`, `PlanEnv.build_eligible`, sidecar today's queue, skip-requeue, TUI | default (serving) | `build_due_queue`, unchanged |
| sidecar plan `eligible` | `not prefetch` | `read_due_queue` for the prefetch, `build_due_queue` otherwise |
| sim runner, staged comparator, facets chart, knowledge map, `explain_practice_item`, `exclusion_now` | False | `read_due_queue` |
| `scripts/voi_cap_report.py` / `scripts/benchmark_sqlite_concurrency.py` | False / True | `read_due_queue` / `build_due_queue` |
| tests | 117 uses | ported by a script: False to `read_due_queue`, True dropped; `ruff --fix F401` removed the imports left unused; `assumed_known_helpers._queue(persist=...)` picks the entry by hand |

### 8.2a How the change was made

The callers, scripts and test uses were ported by the script described in the "tests" row above. Three edits in
`scheduler.py` were also made by small scripts rather than the Edit tool:
- the line-range move of the slate block into `_persist_offer` and `_head_probe_presentation` (the moved lines are
  unchanged except for indentation);
- two docstring rewordings in the cold-deferral docstrings;
- docstring and doc rewordings: `facets.py`, `Inspect Persistent State`, and the test docstrings in §8.4 (plus the golden module's own).

### 8.3 The delta

Only read builds with a session change, and only in two ways: no `contrast_pair_servings` rows, and no presentation
invalidation. The returned queue is identical for every caller, because the build never re-reads either write.
- The read-with-session golden was regenerated in the fix commit. It differs by exactly the 2 removed
  `contrast_pair_servings` rows: 32 JSON lines deleted, nothing else.
- The serving golden and the no-session read golden are byte-identical.

### 8.4 Tests changed

- **`test_intent_orchestrator_rulings::test_r1_every_gate_of_the_build_is_the_admission_predicates`.** It inspects
  the candidate loop's source and named `build_due_queue`, now a three-line wrapper. It reads `_due_queue` instead;
  no assertion changed. This points a source check at the new location, which T4 discourages. I chose it over
  deleting the R1 guard, and it is listed here for the reviewer.
- **`test_plan_determinism::test_the_per_session_draw_keeps_its_own_path`.** This is the bug's own test. Its
  docstring names the serving surfaces (Today's full list, skip, CLI, TUI, DL1's plan), but it built with
  `persist_explanations=False` and asserted the contrast rows that build recorded. It now builds with
  `build_due_queue`; its assertions are unchanged.
- **Docstrings only:** `test_instruct_handoff_ih0`, `test_scheduler`, `test_slate_record`.

### 8.5 Who reads the removed writes

- **`contrast_pair_servings`** is a RECEIPT (`db/table_roles.py`). Only `diagnosis/contrast_pairs.py` reads it (the
  order-effect metric and the randomization balance report) through the repository. No replayer, the rebuild
  orchestrator and the upgrade table do not read it.
- **`probe_presentations`** is a RAW_LEDGER. The shadow rebuild reads it (`substrate/compat/activity_backfill.py`
  turns presentations into administrations and exposures), but only ids, items, `served_at` and `created_at`, never
  the `status`, `end_reason` or `ended_at` the invalidation sets. The fields are read on the live path:
  - the next serving build's active-presentation lookup;
  - attempt submission, which links an attempt to the item's active presentation;
  - placement's opening-episode test (`submitted` status);
  - EVSI and field reports.

  So the one live effect is this: a presentation a read build used to end now stays active until the next serving
  build ends it under the same conditions, or until it is consumed.

### 8.6 Proof

- Goldens: as in §8.3.
- Fail-first: green after the fix. The prefetch's pool build answers on its read-only attach with the contrast pair
  in the pool, and the comparator leaves no serving row.
- Targeted tests: all 1,261 files `affected_tests.py` names (the 179 scheduler, contrast-pair, probe, placement,
  slate, plan, prefetch, intent, VoI and follow-up files, the two edited ones, then the rest in chunks of 100 at
  `-n 4`). Results are in §8.7.
- P-shadow: on fresh backup-API copies of the three Nov 3 owner copies, upgraded to the head, `rebuild --shadow
  --json` on base code and on branch code gives identical output apart from the timestamp, database hashes and
  marker id. On every copy: `learner_state_diff.summary` facet 0, mastery 0, schedule 0; `schedule_effects` 0 due
  dates moved; queue-due counts equal before and after.
- Identity pins are unmoved.

## 9. For the owner: the decision the pure core waits on

The rest of I2 (a pure `rank_due` in two stages: §5's option A, sub-steps I2a-I2c) needs one answer: **may a queue
build read ahead of its decisions?** A two-stage core needs the build to make some reads before it knows whether it
needs them. That changes what a build reads and how it can fail. It does not change what it decides: every draw,
order and written row stays as it is. Per build, as best I can estimate from the code (not measured):

| Read moved ahead | Builds that pay more | Added work (estimate) | Today |
|---|---|---|---|
| Each in-progress, unblocked probe episode's context, eligible instruments, VoI decision and per-instrument familiarity | builds with such an episode none of whose items gets past the earlier gates (all routine-excluded, intent-held or device-held) | about 5 queries plus one per eligible instrument, and the VoI valuation's compute, per such episode | read only when an item reaches the probe gate |
| The device's refusal (eligibility rules plus the host's media predicate) for every item | phone builds | one predicate call per item the other gates already withheld (up to the vault's item count); the media predicate may look up stored assets | asked last, only for items every other gate admitted |
| taught-first signals for all LOs | placement builds with no new material in the ranked queue | 2 queries (`load_answers`, blocking signals) | read only when new-material slots exist |
| practice latencies (one scan of `practice_attempts` with a latency) | builds that value nothing (no probe decision, teach-back site off) | 1 query | read on first valuation |

The DL2 check split stays the one shell read between the two stages, as today: it already runs before the candidate
loop, so it adds nothing.

**The failure mode it adds:** a read that raises now fails the build even where today's build never made it. For
example, a broken hypothesis set on an episode no candidate reaches, or a media lookup for an item another gate
withheld. Recommendation: accept the superset reads for the probe episodes, taught-first and latencies, which are
cheap and rare, and measure the phone's device predicate on the owner copies before deciding that one.

### 8.7 Measures

- **The same queue on real data.** On each owner copy, a read build with a session at a fixed clock returns the same
  queue under base and branch code: the same count and the same digest of ids, priorities, components and
  explanations. arxiv_v2: 32 items. linear_algebra: 43. probability: 67.
- **Build time.** Three builds per process, two processes per side, alternated, on the copies. Another lane's full
  suite was running on the machine, so the numbers are noisy. Warm builds, in seconds:

  | Copy | Read, base | Read, branch | Serving with a session, base | Serving with a session, branch |
  |---|---|---|---|---|
  | linear_algebra | 0.015-0.016 | 0.015-0.017 | 0.126-0.131 | 0.124-0.228 |
  | arxiv_v2 | 0.021-0.022 | 0.020 | 0.084-0.092 | 0.083-0.090 |
  | probability | 0.014-0.015 | 0.015-0.016 | 0.071-0.124 | 0.066-0.149 |

  No difference beyond the noise. The two branch outliers (0.228 and 0.149) each sit beside runs at the base's level
  in the same process.
- **Lines.** `build_due_queue` was 829 lines and is now a 24-line wrapper. The new pieces are `read_due_queue` (20
  lines), the shared body `_due_queue` (602), `_persist_offer` (177) and `_head_probe_presentation` (141); the
  last two moved out of the old body, and most of their added length is keyword signatures. `scheduler.py` went
  from 3,862 to 4,009 lines. Functions over 200 lines: unchanged, since `_due_queue` replaces `build_due_queue`
  and both new functions are under 200. The structure ratchet is unchanged.
