# Check credit, steps 1 to 4: lesson offers credited with checks that never happen (TV2-1)

Branch `algo/check-credit`, on main `9658a9ce2f`. Steps 1 to 4 of the seven-step fix of ledger row TV2-1
([refactor-bug-ledger.md](refactor-bug-ledger.md#from-the-teacher-v2-reviews-2026-11-20)); the spec is
`docs/specs/spec_teacher_v2.md` §7.4, with the reviewers' evidence in `docs/reviews/teacher-v2-arc-reviews-2026-11-20.md`. Nothing served or stored changes:
no algorithm tag, no upgrade row, no migration, no config key, no kill switch, no prompt. The activation at `mvp-0.62`
(step 6), the stored-row report (step 5) and the record with the comparison on copies of the owner's vaults (step 7)
are later steps.

## Commits

| Commit | Step | What |
|---|---|---|
| `a1a8433609` | 1 | `tests/test_check_credit_characterization.py`, `tests/check_credit_helpers.py`; ledger row TV2-1 |
| `b7030a184b` | 2 | the receipt reader (then at `src/learnloop/check_delivery.py`), `tests/test_check_delivery.py` |
| `d068ec449f` | 3 | `delayed_checks.check_available`, `teacher/te2.delayed_check_words` through it, `src/learnloop/daily_plan/check_inputs.py`, `tests/test_check_inputs.py` |
| `b32f4222d3` | 4 | `types.CheckCommitment` and `Action.checks`; `rollouts` (a refusal, a hook, two extractions); `src/learnloop/router_objective/check_value.py`; `tests/test_check_value.py`; step 1's expected failures that the new path satisfies turned into both-paths tests; this record |
| (follow-up) | 2 | the reader moved to `src/learnloop/teacher/check_delivery.py` (judgment call 1); the record's results |

## Read first: the judgment calls

1. **The receipt reader is `learnloop/teacher/check_delivery.py`, not `router_objective/commitment_delivery.py`** (the
   design's example). In `router_objective` it broke the import contract `frozen-cross-package-cycles` ("Existing
   deferred cross-package cycles are frozen": `router_objective -> scheduling` closes a cycle), because it reads the
   intent resolver (`scheduling.intent`). Step 2 committed it as a root module, `learnloop/check_delivery.py`; the
   structure ratchet `first_level_root_modules` (and `first_level_root_modules_not_upgrade`) then rose from 36 to 37,
   which `tests/test_structure_ratchets.py` refused at step 4's gate, so the follow-up commit moved it into `teacher`
   rather than raise the golden. The teacher package already reads `scheduling`,
   `serve_eligibility` and the attempt availability rule, and the receipts are its own. The offer adapters are in
   `daily_plan/check_inputs.py`: they need the plan's estimator, which the plan alone may import.
2. **The new path is a subclass of the rollouts' model, reached only through `check_value.evaluate`.** The rollouts
   gained no option that selects it. Four edits to `rollouts.py`, each inert for every existing input: `run_tail` takes
   `on_return` (None everywhere but the new path; with None the session starts at minute 0 of the day with the same
   arrays as before); `_do`'s tail is the method `_tail` (the same lines); `value`'s refusal is the method `_screen` (the
   diagnostic refusal, same message, then a refusal of typed checks); `evaluate`'s loop is `_evaluate(model_for, ...)`,
   which `evaluate` calls with the same `_Model`. The rollouts refuse typed checks (in `value`, and in `_tail` for a
   direct `_do` such as G2's evaluator's offer branch); the new path refuses the untyped `commitments`. Like G2's
   evaluator, nothing under `src` imports `check_value`, `check_delivery` or `check_inputs` (an AST scan per module).
3. **Undated uses on a check's day follow the tail's existing rule**: the day's pieces integrated on the state after
   that day's session, exactly as for the tail block the check displaces. The design's "integrate undated uses over the
   pre-answer interval once" is the action segment's rule (`_segment`); applying it to checks alone would value a check
   differently from the block it displaces. Dated uses a check's end crosses are scored on the state before it, as for a
   tail block.
4. **The return model is untouched.** Its first gap depends on today's session only, and a check is never answered on
   the decision's own day (`run_tail` runs return sessions from day 1); later sessions keep the existing rule (a tail
   session runs to the remembered minutes, with or without checks: checks never exceed them).
5. **One number copied, not set**: `check_value.FIT_TOLERANCE_MINUTES = 1e-6`, the plan's own admission tolerance for a
   "Check once" (`daily_plan.engine._EPS`), copied because the objective's package cannot import the plan; a test keeps
   the two equal. The only prior strength is the design's one-trial seed (`check_delivery.SEED_TRIALS = 1.0`,
   `PRIORS_VERSION = "check_delivery_one_trial_seed_v1"`, basis `legacy`: one hypothetical promised check supplies one
   seed observation). The 1e-9 and 1e-12 comparisons in the new path are the rollouts' own float resolutions.
6. **Grade availability as of a decision** reads the blind grade records recorded by then (an answer whose grade was
   recorded later had no grade then). The hold's evidence half and the contract-unrecorded hold have no as-of form in the
   store: they are read as they stand now, and a hold released now by evidence alone counts as released at the decision
   too. Stated in the module.
7. **"Replaced" is as of the read**: another commitment deciding the check's item then (the resolver's F21 rule). If that
   commitment is retired later, a later read counts the check pending again.
8. **A satisfaction event is evidence.** An answer this read derives and the settlement of the same answer count once; a
   satisfaction naming an attempt this read does not derive (here an attempt before the check's date) counts as a
   success when its grade is usable, or with no attempt row, as the settlement alone.
9. **A session that a clipped check leaves past the horizon still runs**: a check that would end past `C + H` is charged
   its in-window minutes and answers nothing, and the session's tail block after it lands past the window, as the
   tail's blocks already can on a fractional horizon. Its cost is charged as the rollouts charge a straddling session.
10. **The availability predicate reads "now".** `eligible_now` is the live decision's read (as `delayed_check_words`
    is); only the minutes' evidence is filtered to the decision time. The stored-row report (step 5) will need an as-of
    availability if it reconstructs historical offers.

## Step 1: today's pricing, characterized

`tests/test_check_credit_characterization.py` (shared fixture in `tests/check_credit_helpers.py`).

**The worked fixture**, to nine decimals (one topic, performance `σ(η)`, `γ = ln 1.5` fixed, `η₀ = −γ/2`, a 15-minute
lesson at mass 0.5, one check three days later, one dated use of weight 1 at day 5, no undated use, attention price 0, no
tail practice, return gap 100 days):

| Quantity | Today (rollouts) | Intended (new path) |
|---|---:|---:|
| Accepted branch | 0.600000000 | 0.500000000 |
| Declined branch | 0.449489743 | 0.449489743 |
| Mixed offer at p = 0.5 | 0.524744871 | 0.474744871 |
| Increment attributable to the phantom check (mixed) | 0.050000000 | 0 |

The tests pin the accepted and declined ledgers (all value in `tail_reward`; `crossed`, `undated`, `kappa`, `tail_cost`
and `terminal` zero), the mixture at the drawn `p̄` (the acceptance Beta is `(1e6, 1e6)`) and at exactly 0.5, and the
state effects at state level: with no return before day 100 the check due at day 3.0104 is answered at the day-4
boundary (`last = 4.0`), practised, `η` up by exactly `γ`, FSRS stability set, belief variance down, lesson window 0.

Also pinned: no minutes charged (an attention price and a day-6 return leave the accepted branch's costs equal with and
without the check), the offer built with a retention check at 3 days on a topic whose only question was attempted
(`delayed_check_words` says "none yet"; `action_for` gives `commitments == (("lo_m2", 3.0),)`), and the ninth commitment
reusing the first one's outcome draw (identical FSRS state on topics 1 and 9, draw for draw, 64 draws).

The four intended behaviours were strict expected failures (`raises=AssertionError`, so a broken setup fails the test),
each failing on its own number: 0.6 against 0.5; a cost difference of 5.6e-17 against 0.041125; equal arrays; 0.6 against
0.5 for the built offer. Step 4 turned the first three into both-paths tests; the fourth stays (below).

## Step 2: the receipt statistics (`learnloop/teacher/check_delivery.py`)

`classify(repository, *, as_of, config)` reads every planned entry of every lesson receipt recorded by `as_of`; one
trial per entry, keyed `lesson:<id>:<purpose>:<node or "lesson">` (with the entry's ordinal when two share a key).
`counts(trials, purpose=...)` pools one purpose and the legacy regime (`legacy_vault_item`); `posterior(counts,
eligible_now=...)` is the one-trial seed, `alpha = e + S`, `beta = (1 − e) + F`, with the point mass at an endpoint
(`DeliveryPosterior.endpoint`); `as_dict()` gives the fields the design freezes into the record (policy and priors
versions, basis, as-of, purpose, regime, `eligible_now`, `S`, `F`, censored by reason, `alpha`, `beta`, predictive mean,
evidence digest). The repository is attached read-only by the caller; settlement is never called.

**The classes, one synthetic case each** (`tests/test_check_delivery.py`; check dated Nov 4, read Nov 10 unless
said):

| Case | Rows | Class (reason) |
|---|---|---|
| missing | receipt entry `missing: true` | failure (`missing`) |
| correct cold | own-answer attempt Nov 5, correctness 1 | success (`answered_cold`) |
| wrong cold | own-answer attempt Nov 5, correctness 0 | success (`answered_cold`) |
| helped, then cold | hinted Nov 5 (date moves to Nov 12), own answer Nov 11 | censored (`not_yet_due`); with an own answer Nov 13, read Nov 14: success |
| before-due attempt | own answer Nov 2 | censored (`pending`) |
| late-arriving grade | own answer Nov 5, its blind grade recorded Nov 12 | censored (`ungraded`); read Nov 14: success |
| pending | no attempt | censored (`pending`) |
| not yet due | dated Nov 20 | censored (`not_yet_due`) |
| paused | paused Nov 3 | censored (`paused`) |
| paused then resumed | resumed Nov 3 (the fold's `active`) | censored (`not_pending`) |
| stopped | retired Nov 3 | failure (`stopped`) |
| replaced | another commitment on the item Nov 3 | failure (`replaced`) |
| duplicate settlement | own answer Nov 5, settled Nov 6 | success once (`answered_cold`), before and after the settlement |
| settlement only | attempt Nov 2 (skipped by the derivation), settled Nov 3 naming it | success (`settled`) |
| not cold at the attempt | a reveal on its topic before the own answer | censored (`not_yet_due`: the attempt moved the date) |
| unplanned | entry with no commitment and no `missing` | not a trial |
| transfer | a missing transfer entry; another lesson's answered one | pooled with transfer only |
| as of before the facts | read Nov 4, 18:00 | answered checks censored (`pending`); before the receipts: no trial |

Retention as of Nov 10: S = 4, F = 3, censored 8 (`not_yet_due` 3, `pending` 2, `ungraded` 1, `paused` 1,
`not_pending` 1); transfer S = 1, F = 1. The reader leaves the database file byte-identical, and an insert through its
attachment fails as read-only. The seed: an empty vault gives `(1, 0)` (mean 1) with a question and `(0, 1)` (mean 0)
without; the documented legacy sample (retention `S = 0, F = 19`) gives `(0, 20)` (mean 0) and `(1, 19)` (mean 0.05);
`S = 3, F = 1` without a question today gives 0.6 (availability is a seed, never a factor).

## Step 3: availability and minutes

**The predicate.** `delayed_checks.check_available(vault, repository, lo, *, withheld, attempted)` is the candidate
rule `delayed_check_words` used inline (no exclusions, the withheld view, attempted, revealed by the auto-prime
threshold); `delayed_check_words` now calls it. `daily_plan/check_inputs.eligible_now(vault, repository, lo)` calls the
same rule with the vault's own protection view and attempts, returning False when protection is unavailable or anything
fails to read.

**Evidence that `delayed_check_words` is unchanged**: `tests/test_check_inputs.py` compares its words with the
predecessor's expression (written inline in the test) over a fresh topic, all questions attempted, one attempted, the
last one revealed, protection unreadable and a topic the vault does not hold, and checks the predicate agrees with the
words in each; `tests/test_teacher_te2_lessons.py` (the brief's words) passes unchanged. The adapters through a read-only
attachment leave the database byte-identical, with the provider routing functions made to raise if called.

**The minutes.** `dry_check_minutes(vault, repository, lo, *, as_of)` builds the plan's `Estimator` over the evidence
recorded by `as_of` (attempt latencies by the ledger's availability rule, plan feedback events by their time, through
`load_duration_evidence`'s explicit inputs) and returns the four-decimal planning estimate of the item the delayed
picker would choose now (`pick_with_receipt`, no receipt written, nothing reserved; the item is provenance only), or,
with no candidate, the same estimator's estimate for an unknown item. Tests: it equals the engine's own estimator
(`engine._estimator`) on the same item, with mode evidence moving it off the prior and the feedback prior included;
an attempt recorded after the decision does not move it; with no candidate and no duration history it is 3.0 + 0.5 =
3.5 minutes.

## Step 4: the new rollout path, unreachable

`types.CheckCommitment(lo, days, minutes, delivery=(alpha, beta), key, purpose, group)`: numbers and names only (no
repository, vault, question text or protection object; a test pins the fields), validated (a key, non-negative shapes
not both zero, non-negative minutes and delay). `Action.checks` (default empty) is allowed only on a lesson, never with
the untyped `commitments`, with unique keys.

`router_objective/check_value.py`: `evaluate` (the rollouts' signature and loop through `_evaluate`), `simulate` (one
action's path, its final state and each check's answer time), `uniforms`, `propensity`; the rule is in the module
docstring. Tests (`tests/test_check_value.py`):

| Property | Test |
|---|---|
| No-check actions identical on both paths | every action kind on AD's link under each rollout option, reference row included (bytes); the eve-of-exam case with a check-free lesson offer |
| Zero delivery is no event | delivery `(0, 1)` and `(0, 20)`: rows identical to the lesson without checks, on both paths |
| Due-time rounding and returns | due 3.0104 with daily returns: answered day 4; due 2.9104: day 3; first return day 7: day 7; no return in the window: never |
| A graded attempt at its end | FSRS review, `η` exactly `γ` after the lesson, last-practice time at its end, lesson window reset; undelivered, a tail block takes the session instead |
| Capacity deferral | two 6-minute checks against 10 remembered minutes: day 4 and day 5; cost added exactly twice `cost(0,6) + cost(6,10) − cost(0,10)`; return draws equal to the rollouts' |
| `C` crossing | `C` 2.88 minutes into the session: `cost(0, 2.88)` to the tail, `cost(2.88, 0.62)` to `T_C`; the dated use at day 6.001 scored on the pre-answer state (0.5) |
| Horizon clipping | `C + H` 2.88 minutes into the session: only the in-window minutes charged, no answer effect |
| Streams | nine checks: the ninth's outcome its own; the first eight unchanged by adding it; listing order irrelevant; two checks on one topic distinct; delivery and outcome streams apart; `K` to `2K` keeps prefixes, and the first 8 of 16 draws of an offer with checks equal the 8-draw run |
| Delivery | endpoints are point masses; one propensity per group, a Bernoulli per check, equal to the streams' formula draw for draw |
| Plan's tolerance | `FIT_TOLERANCE_MINUTES == engine._EPS` |

Step 1's expected failures that this path satisfies are now both-paths tests in the characterization file:
`test_both_paths_a_check_happens_only_on_a_simulated_return` (0.6 today, 0.5 and the lesson's own draws on the new
path; mixed 0.474744871 at p = 0.5), `test_both_paths_a_check_is_charged_its_minutes_on_the_session_clock` (0 today,
0.041125 on the new path), `test_both_paths_the_ninth_commitment_draws_its_own_outcome` (aliased today, its own on the
new path).

**What makes the new path unreachable**: (a) `rollouts.evaluate`, `baselines` and `gain` keep their parameters (a test
pins `evaluate`'s list; none names a model or path), and no option selects the new model; (b) the rollouts refuse typed
checks (in `value` and in `_tail`, so G2's evaluator's direct `_do` refuses too: tested); (c) no module under `src`
imports `check_value`, `check_delivery` or `check_inputs` (AST scans, by name, package or importlib); (d) the live offer
builder and `objective_inputs.action_for` build only untyped `commitments` (pinned by step 1), which the new path
refuses.

## Expected failures left for the activation

- `tests/test_check_credit_characterization.py::test_intended_an_offer_with_no_eligible_question_credits_no_check`
  (strict): an offer built on a topic with no eligible question is worth exactly its lesson. It needs the offer to carry
  its sensors and the live path to price them (step 6).

## Pins and goldens

Unchanged: `tests/test_identity_pins.py` passed after every commit (345 passed after each of steps 1 to 3; in the gate
run after step 4 and after the follow-up), the journey golden (`tests/test_diagnosis_journey_golden.py`), the
effective-defaults golden, the CLI help snapshot, the kill-switch list and the structure ratchets; no golden or pin file
was rewritten. No pinned draw moved: every existing router-objective test passes with its seeds unchanged, and the new
path's streams have names of their own.

## What ran

Through the scratch wrapper, `-n 1`, in a 3G scope, one command at a time:

| Command | Result |
|---|---|
| step files during the steps | step 1: 5 passed, 4 xfailed; step 2: 9 passed; step 3 with `test_teacher_te2_lessons.py`: 17 passed; step 4: 23 passed |
| `tests/test_identity_pins.py` after steps 1, 2, 3 | 345 passed each time |
| the brief's name filter (38 files: router_objective, rollout, lesson_offer, objective_inputs, delayed_check, te2, te3, daily_plan, estimates), `-m "not arc_close"`, at step 4's tree | 317 passed, 3 skipped, 1 xfailed |
| `scripts/affected_tests.py --files` (the seven changed source files) listed 213 files; beyond the name filter, the 46 router and check files among them (`test_ro*`, `test_rospeed*`, `diagnostic_probe_value`, `action_kinds_complete`, `probe_router*`, `instruct_handoff_ih0/1`, `data_capture_a6_delayed_pick`, the four new files), two chunks, `-m "not arc_close"` | 315 passed, 1 xfailed; 352 passed |
| after the follow-up: the four new test files and `test_teacher_te2_lessons.py` | 57 passed, 1 xfailed |
| after the follow-up: identity pins, journey golden, effective-defaults golden, CLI help snapshot, kill switches, SQLite file copies, structure ratchets | 407 passed (at step 4's commit the ratchet failed on the root module; see judgment call 1) |
| `tests/test_test_layout.py` alone; `tests/test_architecture.py` alone | 3 passed; 18 passed |
| `ruff check`; `lint-imports --no-cache`; `scripts/check_gate_partition.py` | All checks passed; 43 kept, 0 broken; 32068 collected: landing 32003 + arc_close 65 |

## Not verified

- The wide chunks were run at step 4's tree, before the follow-up moved the reader (nothing they import changed).
- The 167 affected files outside the name filters (the change reaches them through `types`, `rollouts`, `delayed_checks`
  and `te2` imports; their behaviour is covered by the byte-identity tests and the pins, not by running them).
- Any owner vault or copy: the census (24 missing entries, 19 retention and 5 transfer) is the reviews' number, not
  reproduced here.
- The activation's surfaces: the offer record, traces, prefetch identity, `diagnostic_value`'s continuation of typed
  checks, and the report.
