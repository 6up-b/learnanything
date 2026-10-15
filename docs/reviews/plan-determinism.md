# Plan determinism (`fix/plan-determinism`)

**Status:** fixed in production planning, tests pinned through the scheduler's own draw seam. Base `6dabbc33c` (`mvp-0.23`). No migration, no schema change, no config key, no new algorithm version.

*Landed on main at `mvp-0.24` (merge `01dc98793`; "Landing onto main" below): the switch also fixes the candidates the R2b mixture draws over, and the flake loop shows 0 failures in 250 runs.*

*Amended by the Codex review (`plan-determinism-codex-review.md`): F1 found a second session-seeded draw in the pool (a contrast pair's member order), now drawn per pair in staged plans; F2 put the rule behind a kill switch, `plan.deterministic_staged_plans` (one config key, all fifteen defaults snapshots recomputed). Still no migration, no schema change and no new algorithm version.*

**In one paragraph.** Today's plan takes its pool from the scheduler's ranked list. The scheduler applies router R1's seeded exploration (`scheduler_seeded_exploration`) to that list: with probability `scheduler.selection_exploration_rate` (0.1), one near-tie within the reward window moves to the front. The draw is a hash of the session id, the UTC date and the candidate ids. Every test run mints a fresh ULID for its session, so about one run in ten planned different blocks. At `mvp-0.23` with the router on, that broke the owner's rule that staged plans are deterministic: the `plan_block` row logged `staged_v1` with propensity 1 for a block built from a randomized pool. The fix keeps the draw out of the pool wherever the router composes Today. DL1's own pair (the router off, or a vault below `mvp-0.23`) keeps the draw unchanged, as G8 requires. Replay is unchanged, because replay never reads a plan.

## The tests

| Test | Version and pair | Flake on base |
|---|---|---|
| `test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]` | `mvp-0.23`, router on (staged) | about 1 run in 10 |
| `test_learner_pick_proposal.py::test_the_delivery_carries_r1s_decision_of_the_block_that_served_it` | `mvp-0.14` (DL1) | none on base; failed once in the VOI v2 landing gate (`21440c9cf`) |
| `test_reader_rw3a_landing.py::test_the_answer_to_a_check_binds_by_the_picks_presentation[new_pick_block]` (found here) | `mvp-0.23`, router on | expected about 1 run in 30 (3 of 30 in the loop below) |

The third test turned up in the `-n 8` loop. Its sibling `test_check_me_goes_through_the_plan_path_and_is_logged_once[new_pick_block]` fails on the same outcome, as the enumeration below shows.

## Reproduction (base code)

Every loop is a separate `pytest` process, with `TMPDIR` in the worktree's `fixtures-local/tmp`. A base run uses either this branch before the change or a `git archive` export of `6dabbc33c` run on `PYTHONPATH`. The process printed the `learnloop` it had loaded.

| Run | Result |
|---|---|
| RW3a `[planned]` alone, 30 runs | **3 failed** (runs 15, 27, 30) |
| RW3a file, learner-pick file and `test_router_r2a_serving.py` under `-n 8`, 30 runs | **4 runs failed**: `[planned]` in 2, `binds[new_pick_block]` in 3 (`KeyError: None`), learner pick in 0 |
| learner-pick R1 test alone, 30 runs | 0 failed |
| RW3a planned world in one process (`-n 8`), 60 runs, plan shape recorded | 50 greedy; 10 explored: `pi_extra_2` 5, `pi_extra_1` 4, `pi_svd_define_002` 1 |
| learner-pick world in one process (`-n 8`), 60 runs | 56 greedy; 4 explored: `pi_svd_define_001` 2, `pi_extra_2` 1, `pi_eig_mid` 1 |

**The plan shapes.** In the RW3a planned world the scheduler's greedy list starts `pi_svd_define_001` (reward 0.492), then `pi_extra_1` and `pi_extra_2` (0.435 each), then `pi_svd_define_002` (0.399). All three are within the 0.15 window, so the draw has three alternatives:

- **Greedy:** one new block, `[pi_svd_define_001, pi_svd_define_002]`. Its decision chose `_001`, and the test passes.
- **`pi_svd_define_002` drawn:** the block is `[pi_svd_define_002, pi_svd_define_001]` and its decision chose `_002`. This is the recorded failure: `'pi_svd_define_002' == 'pi_svd_define_001'`.
- **`pi_extra_1` or `pi_extra_2` drawn:** the first block is the `lo_extra` pair. "Check me" then lands outside the plan as its own `learner_pick` block, which fails `learner_pick == 0` (`assert (1 == 0)`). This is Q-D1's third shape, where the pick became its own `learner_pick` block.

In the RW3a world the plan differed from greedy in exactly the 10 runs whose queue carried `exploration_selected`. In the learner-pick world, 3 of its 4 explored runs changed the plan (a drawn `pi_eig_mid` is in no planned block), and no greedy run did.

**Each outcome, forced** through the scheduler's own seam (`_exploration_draws`, the injection `test_router_probe_ties.py` and `test_evsi_router_composition.py` already use):

| Case | Greedy | `pi_extra_1` | `pi_extra_2` | `pi_svd_define_002` |
|---|---|---|---|---|
| `logged_once[planned]` | pass | fail `1 == 0` | fail `1 == 0` | fail `_002 == _001` |
| `logged_once[new_pick_block]` | pass | pass | pass | fail (`TypeError`: no decision) |
| `binds[new_pick_block]` | pass | pass | pass | fail (`KeyError: None`) |
| `logged_once[open_list]`, `binds[planned]` | pass | pass | pass | pass |

The expected failure rate of `[planned]` is the rate times 3/3, about 10%. That matches 3 of 30 runs alone and 10 of 60 runs in process. The `new_pick_block` cases fail at the rate times 1/3, about 3%.

**The learner-pick test.** Its vault's greedy list starts `pi_extra_1`, `pi_extra_2`, `pi_svd_define_001`, and the draw's alternatives are `pi_extra_2`, `pi_svd_define_001`, `pi_diag_mid` and `pi_eig_mid`. On base every forced outcome passes. On the code just before R2a review F4 (`f9d059bd8^`, exported with `git archive`; the VOI landing `21440c9cf` is its ancestor), the `pi_svd_define_001` outcome fails with `assert (None is not None)`. That is the VOI gate's failure, "the pick's block carried no R1 row". The other outcomes pass. The draw puts `pi_svd_define_001` first, so the plan's first block is that item's alone and the picked `pi_extra_1` is outside the plan. Before F4, a pick outside the plan made a one-item block that logged no decision, so the delivery's `router_decision_id` was None. The draw lands there with probability 0.1 × 1/4, about one session in forty. F4 (`f9d059bd8`, on main since the R2a landing) logs that block's own decision, which is why the test no longer fails. Its plan still varied, though (3 of 60 runs above).

## Cause

**(a), a logged design whose seed the tests do not pin, reaching a plan that must not take it.** The randomness is R1's seeded exploration:

- `scheduler.py::build_due_queue` sorts the list by `(-selection_reward, -priority, practice_item_id)` (`:741`), then calls `_apply_seeded_exploration` (`:762`);
- the roll and the choice come from `_stable_fraction` (`:2495`), a SHA-256 of `(label, session_id, UTC date, sorted candidate ids)`;
- a session's id is `new_ulid()` (`repositories.py:9186`), new on every run.

The draw is a logged design for the Today list: R1 logs the offer with its propensity, and the slate records each candidate's design probability (`base_selection_propensity`) and the realized flag (`exploration_flag`). The plan's pool, though, is built from that same call (the sidecar's `_env` and `PlanEnv.build_eligible`). In it the draw decides more than the order of a list the learner sees:

- the new lane groups items by LO in the pool's order;
- `_pack` fills blocks in that order;
- `planner_value = 1/(1 + rank)` (`lanes.py:504`) is the chooser's tie-break.

Under the router at `mvp-0.23`, the plan's only logged decision is the `plan_block` row (`staged_v1`, propensity 1, `propensity_kind = deterministic`). So a randomized pool reached a decision logged as deterministic. The R2a record says `staged_v1` is deterministic, and the owner's 2026-10-13 rule says exploration comes only from the mixture's logged floor. Production was nondeterministic where it must not be, so production is fixed, not the tests.

**Not (b).** No tie-break is unstable:

- the greedy key ends in the practice item id;
- the lanes keep the scheduler's order, the staged frame sorts by id, `_intents` is sorted, and lane quota's key ends in source order;
- ULIDs are monotonic within a process (`ids.py`);
- the tests freeze `SystemClock`, and nothing in planning reads the wall clock.

Every greedy run planned the same blocks: 50 of 50 and 56 of 56 in process, and every forced miss.

**Not (c).** No background work races the plan:

- every failure reproduces in one process with the draw forced and nothing else running;
- the handoff's guess, a race in plan-block R1 logging, cannot happen: the logger runs inside the block's `BEGIN IMMEDIATE` transaction (`Repository.atomic`, `repositories.py:897`);
- the missing R1 row was the pre-F4 pick block, which logged no decision at all.

## Fix

**Production** (three files, small and local):

- `scheduling/scheduler.py`: `SchedulerSession.seeded_exploration: bool = True`. When it is False, `_exploration_support` returns None (`:1149`). That one support function feeds the draw, the logged design probabilities (`_selection_propensities`), the offer trace and the composed-head probability, so they cannot disagree. A greedy build logs probability one on its head, as a build with no session does.
- `daily_plan/engine.py`: `plan_scheduler_session(vault, session_id, minutes)` (`:235`) is the session every plan build uses: the sidecar's (`handlers/daily_plan.py:121`) and `PlanEnv.build_eligible`'s (`:315`). Its `seeded_exploration` is `not router_active(vault)`, which is `policy_for`'s own switch. The docstring records the stable tie-break: selection reward, then priority (both descending), then the practice item id; then placement's new-material order and the composition. The composition's one session-seeded step is a contrast pair's member order, a recorded measurement design (open question 3). *Superseded by Codex review F1: that step also decides which member a plan packs, so it is now seeded on the pair alone in staged plans (`contrast_order_seed = "pair"`).*
- At `mvp-0.23` with the router on, the pool is therefore the greedy order, and the same vault state plans the same blocks in every session *(not yet for contrast pairs at this commit; Codex review F1 made it true)*. DL1's pair keeps the draw, so G8 still holds: the switch off equals `mvp-0.22`, and `test_switch_off_at_the_successor_serves_the_predecessors_plan_on_fixture_copies` passes.

**How it composes with R2b + R2c** (`router/r2bc`, in flight). That branch changes `policy_for`, `_env`'s signature and return, and `PlanPolicy`. This fix touches none of those lines; it changes the scheduler call inside `_env`'s closure, an import, and a new function in `engine.py` away from R2b's hunks. `git merge-tree --write-tree fix/plan-determinism router/r2bc` (read-only, no ref changed) merges `engine.py` and `handlers/daily_plan.py`, which both sides change, without a conflict. `scheduler.py` and the two test files change on this side only. Its only source conflict, `config/template.py`, is between main and `router/r2bc` themselves: `git merge-tree 6dabbc33c router/r2bc` shows the same conflict. The generated references conflict as usual and are regenerated at the landing. `mixture_active` implies `router_active`, so after both land the mixture's pool is greedy as well, and the mixture's ε floor is the only exploration, as the owner's rule says.

**Tests:**

- `tests/test_plan_determinism.py` (new, 6 tests):
  - thirty fixed sessions on copies of one vault state plan one staged plan, every decision `staged_v1` with propensity 1 and kind `deterministic`, while DL1's pair plans several under the same sessions (on base: 2 staged shapes);
  - each drawn outcome forced (`pi_extra_2`, `pi_svd_define_001`): the staged builds never call the draw, plan the greedy blocks, and their slates log the greedy design; DL1 takes the forced outcome and plans it, and DL1's greedy blocks equal the staged ones (order parity);
  - `plan_scheduler_session` is greedy only where the router composes Today;
  - the scheduler's switch alone: a forced explore is ignored, and the support and design probabilities agree;
  - **the log reproduces DL1's pick.** The first fixed session whose draw explores to an outcome that changes the first block is found from the greedy order. The test then reads the plan build's slate: session, UTC date, candidate ids, rate and window from the config snapshot, the design probabilities and `exploration_flag`. From these it checks:
    - the head carries 1 − rate and each near-tie in the window carries rate/n;
    - the roll from the logged seed is under the rate;
    - the choice over the near-ties in greedy order gives the flagged item;
    - the plan's first block and its decision lead with that item.
- `tests/test_learner_pick_proposal.py`: the fixture pins the draw greedy through `_exploration_draws`, and the R1 test is parametrized:
  - **greedy:** the chooser's block serves the pick, and the decision has `learner_pick` 0, propensity 1, and chose `pi_extra_1`;
  - **draw on `pi_svd_define_001`:** the pick's own block serves it, and its decision has `learner_pick` 1 and no propensity. This case fails on pre-F4 code with the VOI gate's `assert (None is not None)`.

  Assertions were added; none were loosened.
- `tests/test_reader_rw3a_landing.py`: unchanged. The production fix makes it deterministic.

Fail-first: on base, with only the new import removed, the session test fails `assert 2 == 1` and both forced-outcome tests fail (the staged plan follows the draw).

## Replay and persisted meaning

Nothing persisted changes meaning, and replay is identical:

- daily plans are workflow and receipt rows that replay never reads (migration 180's header, and the import contract "Replay, evidence and serving internals never read the daily plan");
- no replayer builds a queue (`build_due_queue` has no caller under `substrate/` or the rebuild orchestrator);
- `SchedulerSession`'s default is unchanged, so the Today list, the CLI, the TUI, the simulator and every other caller build exactly as before;
- no config key and no default changed, so the defaults fingerprints are unchanged.

A past plan keeps its blocks, and a rebuild never recomputes which item it picked. **No successor is needed** by the playbook's step 1. *Codex review F2: the rule is now a live change behind its kill switch `plan.deterministic_staged_plans`, under the owner's standing ruling (live changes behind kill switches, not successors, for serving changes replay never reads); the successor is still not minted.*

What does change is future serving at `mvp-0.23` with the router on. On a vault whose near-ties would move a block, up to one session in ten (the rate) now gets the greedy plan instead of the drawn one. That brings the code in line with `mvp-0.23`'s recorded contract (R2a: `staged_v1` deterministic, p = 1) and the owner's rule. Open question 1 asks the owner to confirm it as an in-place correction.

**A caveat on past rows.** Before this fix, some `mvp-0.23` staged `plan_block` rows logged propensity 1 although their pool had been drawn. They can be identified: the slate the same build wrote (same session, same time) has a candidate with `exploration_flag = 1`. An off-policy analysis of staged decisions should drop or flag them (open question 2). The tracked fixtures are at `mvp-0.8`, so they hold no such rows.

## Manual run (backup-API copies, no model calls)

The worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` were copied with `copy_tree_with_databases` into `fixtures-local/pd-manual` and set to `mvp-0.23` (router on). Settings:

- `LEARNLOOP_CONFIG_DIR` an empty directory and `SystemClock` frozen at 2026-10-12 09:30Z;
- manual grading, no startup maintenance;
- one copy per session, with fixed session ids `s_00` to `s_39`; `get_daily_plan` was called on each, and its blocks, decisions, projection and slates were recorded.

Each fixture was run on base (`git archive 6dabbc33c`) and on this branch.

| Fixture | Base: distinct plans / sessions whose slate explored | Branch |
|---|---|---|
| linear algebra | 1 plan / 2 of 40 explored (the draw changed neither the first block (repair: `pi_orient_operations_omission_rewrite`, `pi_orient_incomplete_spec_02`) nor the projection) | 1 plan / 0 of 40 explored |
| probability | 1 plan / 0 of 40 explored | 1 plan / 0 of 40 explored |

On the owner's data the draw rarely reached the plan: its first block is a repair block that the draw does not move. The tests' vaults put near-ties in the new lane on purpose. The branch never draws for a staged plan. The tracked fixtures were only copied, and the copies were removed afterwards.

## After the fix

The loops ran on the fix's code. The edits made while they ran changed only the helper's docstring and its return annotation.

| Run (this branch) | Result |
|---|---|
| Forced outcomes, every RW3a case (5 cases × 6 outcomes) | **30 of 30 pass**; the draw is never called |
| RW3a `[planned]` alone, 50 runs | **50 of 50 passed** |
| RW3a file alone (all 5 cases), 50 runs | **50 of 50 passed** (250 cases) |
| learner-pick R1 test (both cases) alone, 50 runs | **50 of 50 passed** (100 cases) |
| RW3a file, learner-pick file, `test_router_r2a_serving.py` and `test_plan_determinism.py` under `-n 8`, 50 runs, while other worktrees' full suites loaded the machine | **50 of 50 passed** (41 tests each) |
| plan, router, scheduler, VOI, RW3a and learner-pick files (`-n 8`) | 581 passed |

## Gate

Run in this worktree at `f25592344` (the fix `8137d6d7c` plus its references), with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install restores 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,900 passed**, 0 failed, 49 warnings (14 min 31 s, after waiting for the lock behind other worktrees' suites) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,800 deselected, 1 warning (1 min 46 s) |
| References | Schema and config unchanged; line citations moved. `db_generate_reference.py` rerun (`f25592344`, provenance and line citations only) and `db_validate_reference.py` reports `errors: []` |
| Frontend, `cargo check` | not run: nothing under `apps/` changed |
| CLI help snapshot, defaults snapshots | unchanged (no CLI, config or default change); their tests pass in the full suite |
| Paid calls | none |

## Open questions

1. **In-place correction of `mvp-0.23`.** Future staged plans no longer take the scheduler's draw, at the same algorithm version. Replay and persisted meaning are unchanged. Accept it as a correction to `mvp-0.23`'s own contract, or mint a successor? Recommended: accept in place (the R2a record already says deterministic, and R2b + R2c, `mvp-0.24`, is in flight). *Answered by the Codex review (F2): accepted in place under the owner's standing ruling, with the kill switch it requires; off restores `mvp-0.23` as it landed.*
2. **Past staged rows.** Before this fix, up to one staged plan build in ten (the rate) drew its pool, and its `plan_block` rows still logged propensity 1. Flag them in the router's outcome analysis (join on the same build's slate `exploration_flag`), or leave them? Recommended: flag them when R2b's evaluation first reads staged rows. No tracked vault has any.
3. **Contrast-pair order in staged plans.** The composition still randomizes which member of a contrast pair is served first, seeded on the session and the pair and recorded per session (Meas §3.A4). On a vault with contrast pairs, the same state can plan a pair's two items in either order across sessions. It is a measurement design, not exploration, so it was left in place. Keep it in staged plans? Recommended: keep it, since order randomization is the measurement's point. *Superseded by Codex review F1: kept, but drawn per pair in staged plans, so the plan is deterministic and the draw still varies across pairs (and is recorded); every other queue build keeps the per-session draw.*
4. **DL1's plans.** Below `mvp-0.23`, or with the router off, the plan's pool still takes the draw while lane quota logs propensity 1 (G8 keeps those plans as they were). The draw is reproducible from the slate (the new test). Making DL1 greedy too would change serving at older versions, which needs a successor or an owner decision. Recommended: leave it.

## Landing onto main

**Branch:** `merge/plandet-onto-main` (worktree `learnanything-merge2`), from main `4108e1ccd` (`mvp-0.24` LATEST; GLM-OCR and router R2b + R2c landed since this branch's base `6dabbc33c`; migration head 202, sixteen defaults snapshots). Merge `01dc98793`, a real `--no-ff` merge of `fix/plan-determinism` (`2d5c73af7`, unchanged; the final Codex verify was clean), then this record. Not pushed. Owner-directed, 2026-10-14, single phase. The sections above and `plan-determinism-codex-review.md` describe the branch as built, at `mvp-0.23`.

**Paid calls:** none ($0.00); no network, no key read. **Migration:** none (head 202 is main's). **`apps/`:** unchanged, so no frontend gate and no `cargo check`.

| Commit | What |
|---|---|
| `01dc98793` | the merge: the composed template and recomputed snapshots, the switch's wording at `mvp-0.24`, the regenerated references, the Pipeline Map line and `tests/test_plan_determinism_landing.py` |
| (this commit) | this section |

### Conflicts

| File | Resolution |
|---|---|
| `src/learnloop/config/template.py` (15 hunks, the only source conflict) | The `DEFAULTS_SNAPSHOT_BY_ALGORITHM` block. Main's GLM-OCR and R2b + R2c notes kept and the branch's added after them: its full note in `mvp-0.9` (now saying the switch fixes the order of the candidates the mixture draws over at `mvp-0.24`, and "all fifteen ... on its branch, and all sixteen again ... when it landed on main after GLM-OCR and router R2b + R2c"), and its "moves it too" line in every later entry, `mvp-0.24`'s included. All sixteen hashes recomputed (below). |
| 375 notes under `Reference/` | Taken from main, then regenerated. |
| Auto-merged, both sides kept | `daily_plan/engine.py` (`plan_scheduler_session` and `staged_plans_deterministic` beside R2b + R2c's `policy_for` and env changes), `learnloop_sidecar/handlers/daily_plan.py` (the pool's session inside R2b's `_env`), `config/schema.py` (the key in `PlanConfig`; R2b + R2c's `[router]` keys untouched), `_scripts/db_generate_reference.py`, `spec_daily_loop_v1.md` |
| This side only | `scheduling/scheduler.py`, `diagnosis/contrast_pairs.py` (main has not changed either since `6dabbc33c`), the two test files |

R2b + R2c's modules are untouched by the merge: `git diff 4108e1ccd 01dc98793` is empty for `src/learnloop/router/` and `daily_plan/router_chooser.py`, so the mixture's seed (`seed_for(boundary key, decision id)`), its two-stage draw, its floor and its logged propensities are main's. The switch's wording now names `mvp-0.24` (the schema comment, `staged_plans_deterministic`'s docstring, the reference override and the daily-loop spec's §11 row): the same pool gives the mixture its candidates (the staged rule's pick and the support), the mixture keeps its own seeded draw, and off restores the pool as `mvp-0.23` and `mvp-0.24` landed.

### Compositions

New tests in `tests/test_plan_determinism_landing.py` (19), all at `mvp-0.24`, on the stage's two worlds (R1's near-ties and the contrast pair, both fitting or only one), with the router's fake models (`tests/router_model_fakes.py`; no network):

1. **Staged mode under `mvp-0.24`.** With `router.mode = "staged"`, and with the default mixture when no model is set up (the staged rule decides: `staged_v1`, propensity 1, kind `deterministic`), sixteen fixed sessions and Start's sessionless build plan one plan in each of the three worlds, and Begin on Start's plan keeps Start's block. A pair's order is the pair's own draw, and each session's serving row records it with the seed `pair|pi_pair_a|pi_pair_b`. Every outcome of R1's draw, forced (`pi_extra_2`, `pi_svd_define_001`), leaves the plan greedy, and the draw is never called.
2. **Mixture mode.** With both models answering (uniform) and the chooser's own seeds, every session and Start offer the mixture the same staged pick and the same top-k support, in the same order, with the same items and planner values. For each decision:
   - **G3:** the logged propensity equals `mixture.recompute` over the logged support, staged pick, epsilon, effective weights and model distributions (to 1e-12), and the logged seed reproduces the two-stage draw (choice, component, `u1`, `u2`);
   - **the chooser's own draws:** each seed is `seed_for(boundary key, decision id)`, a different one for every decision;
   - **the floor:** every option of the support keeps at least `epsilon`, outside the support is 0, and the support sums to 1. With both models' mass on the staged pick, every other option is exactly `epsilon`, so the floor binds. A seed whose first uniform falls under `k * epsilon` takes the uniform branch.

   With one pinned seed per session, the sessions draw different blocks over the same candidates, so the mixture's exploration is its own. With R1's roll forced to miss (both pools greedy), each session's decision is identical with the switch on and off, field for field (seed, uniforms, component, choice, every candidate's propensity). The switch changes the pool and nothing in the draw.
3. **The kill switch off at `mvp-0.24`.** `plan_scheduler_session` returns the predecessor's session, field for field, in both modes (and with the router off), and the greedy session with the pair's draw when on. Off, a forced R1 draw moves the staged plan's first block (staged mode) or the mixture's staged pick and candidates (mixture mode), and both still pass G3. The pair is again ordered per session in both modes (both orders across sixteen sessions, each session's seed recorded), and Start keeps the greedy order, unrecorded: main's behaviour. Main's own code was also compared with the switch off on the owner's data (Parity, below).

**Fail-first.** With `staged_plans_deterministic` forced to return False (main's pool), 14 of the 19 fail. The 5 that still pass are the four switch-off tests and the floor test, which do not depend on the switch.

The branch's own tests run unchanged at `mvp-0.23`: `test_plan_determinism.py` 14 passed, and `test_every_defaults_snapshot_records_the_switch_on` passes over all sixteen versions.

### The flake

Every run is a separate `pytest` process on the merge, with `TMPDIR` in this worktree's `fixtures-local/tmp`. The loops ran while this worktree's full suite was running, so the machine was loaded.

| Run (merge `01dc98793`) | Result |
|---|---|
| `test_reader_rw3a_landing.py::test_check_me_goes_through_the_plan_path_and_is_logged_once[planned]` alone, 50 runs | **50 of 50 passed** |
| `tests/test_learner_pick_proposal.py` alone, 50 runs | **50 of 50 passed** (17 tests each) |
| the RW3a `[planned]` case under `-n 8`, 50 runs | **50 of 50 passed** |
| `tests/test_learner_pick_proposal.py` under `-n 8`, 50 runs | **50 of 50 passed** (17 tests each) |
| both together under `-n 8`, 50 runs | **50 of 50 passed** (18 tests each) |
| **Baseline:** main `4108e1ccd` (`git archive`, its own `src` and `tests`, the process loading the archive's `learnloop`), RW3a `[planned]` alone, 50 runs | **8 of 50 failed**, every one `assert (1 == 0)`: R1's draw put a `pi_extra_*` near-tie first, and "check me" became its own `learner_pick` block (the shape described above) |

0 failures on the merge, against about 1 in 6 on main.

### Defaults, CLI help and references

- **Defaults.** All sixteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries (`mvp-0.9`..`mvp-0.24`) were recomputed with `defaults_fingerprint_for_version` from the composed defaults, with the template `.pyc` deleted before and after and the file touched. Every one moved: the branch's lacked GLM-OCR's and R2b + R2c's keys, and main's lacked the switch. A fresh process confirms all sixteen.
- **CLI help.** `test_cli_help_snapshot.py` passes unchanged (the merge adds no CLI option), so the snapshot was not regenerated.
- **References.** `db_generate_reference.py`: schema head 202, 321 table notes; `Config - plan` gains the field (22 leaves). `db_validate_reference.py` reports `errors: []` once `Configuration.md` and `Database.md` read 854 leaves (main's 853 plus the switch; 50 sections).
- **Pipeline Map** (`Maps/LearnLoop Pipeline Map.md`). One line after R2b + R2c's: staged plans are deterministic behind `plan.deterministic_staged_plans` (the pool in greedy order, a contrast pair's order per pair, Start included), and the mixture draws over that fixed candidate order with its own seed, floor and propensities. `validate_vault.py` passed: 1,105 notes.

### Gate

Run in this worktree at `01dc98793` with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install restores 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **11,110 passed**, 0 failed, 48 warnings (14 min 41 s): main's 11,076, the branch's 15 (14 new plus the learner-pick R1 test's second case), and the 19 landing tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability -n auto` | **100 passed**, 0 failed (31 s, after 30 minutes waiting for the lock) |
| Frontend, `cargo check` | not run: nothing under `apps/` changed |
| Targeted, before the merge commit | the plan-determinism, landing, learner-pick, RW3a, R2b + R2c landing, G3, config, reading-step, CLI-help, every `test_mvp0*_upgrade.py`, router, daily-plan, contrast-pair and scheduler files: **694 passed** |

No failure needed a rerun.

### Parity

Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of this worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` (`mvp-0.8`) are in `fixtures-local/plandet-parity`: one pristine copy each, then a copy per side and per check. Each copy was migrated by its own code (`migration_coordinator.migrate_vault`, 47 migrations to 202):

- **main `4108e1ccd`**, exported with `git archive` (`src`, `tests`, `migrations`) and first on `PYTHONPATH`. The migration printed the archive's `learnloop/__init__.py`.
- **the merge's own code.**

On each copy, `learnloop rebuild --shadow --json` and `learnloop doctor --json` ran with `LEARNLOOP_CONFIG_DIR` an empty directory. The outputs were compared after setting aside ULIDs, timestamps, ids, hashes and paths.

| Fixture | Version | Shadow (facet / mastery / schedule) | Doctor issues / errors | Router or plan issues | Differences, main vs merge |
|---|---|---|---|---:|---:|
| linear algebra | `mvp-0.8` (own) | 22 / 6 / 47 | 106 / 1 | 0 | **0** (shadow and doctor) |
| probability | `mvp-0.8` (own) | 2 / 1 / 1 | 134 / 49 (46 `criterion:unknown_dependency`) | 0 | **0** |
| linear algebra | `mvp-0.24` | 0 / 0 / 0 | 56 / 1 | 0 | **0** |
| probability | `mvp-0.24` | 0 / 0 / 0 | 98 / 49 (46) | 0 | **0** |

**How the `mvp-0.24` copies were made.** Each side's own code ran `learnloop upgrade --to mvp-0.9`, then `--to mvp-0.24` (the chain's advisory-guard notes printed), then `learnloop rebuild-derived-state` twice, to its fixed point. The `mvp-0.8` rows are the fixtures' existing drift, the same on both sides and the same as at the R2b + R2c landing.

**Every run left its copy alone.** `live_database.unchanged` is true on every shadow. Each copy's `state.sqlite` hash is the same before and after its shadow and doctor. Doctor exits 1 on both sides, as on main. Replay reads none of this change.

**Plans built on each copy.** Each `mvp-0.24` copy was the template for one backup-API copy per build. The builds ran Today's `get_daily_plan` through the sidecar, with:

- `SystemClock` frozen at 2026-10-14 12:00Z, manual grading and an empty `LEARNLOOP_CONFIG_DIR`;
- the router's fake runtime (no model call, no key);
- five fixed sessions (25 minutes each), plus Start's sessionless build (remembering 25 minutes) and Begin on Start's copy.

The runs covered three modes: staged (`router.mode = "staged"`), the mixture with no model set up, and the mixture with uniform fake models and one pinned seed per session. Each mode ran on main, on the merge with the switch on, and on the merge with it off.

| Fixture | Mode | Merge (on): distinct plans over 5 builds + Start | Begin keeps Start's block | Main: distinct / sessions whose slate explored | Main vs merge (off), all 7 builds |
|---|---|---:|---|---|---|
| linear algebra | staged | **1** | yes | 3 / 2 of 5 | **identical** |
| linear algebra | mixture, no model | **1** (`staged_v1`, deterministic) | yes | 3 / 2 of 5 | **identical** |
| linear algebra | mixture, uniform models | **1** set of candidates; 5 different blocks drawn | yes | 3 / 2 of 5 | **identical** |
| probability | staged | **1** | yes | 1 / 0 of 5 | **identical** |
| probability | mixture, no model | **1** | yes | 1 / 0 of 5 | **identical** |
| probability | mixture, uniform models | **1** set of candidates; 4 different blocks drawn | yes | 1 / 0 of 5 | **identical** |

- **On main, the draw reached the owner's data.** On linear algebra, main's two explored sessions (`s_00`, `s_04`) logged different candidate rows: the planner values of the repair and maintain blocks moved, for example the first repair block's from 0.067 to 1.0. The blocks served, the projection and the support's order did not change; the first block is the repair block `[pi_orient_operations_omission_rewrite, pi_orient_incomplete_spec_02]` in every build. On the merge (switch on), every build logs the same rows, equal to those of main's three unexplored sessions and Start (the greedy order). On probability, no session explored.
- **"Identical" for main against the merge with the switch off** covers every field recorded: blocks, `plan_block` decisions, the mixture's staged pick, support and candidates, the projection, the contrast serving rows and every slate's candidates.

The tracked fixtures were only copied: `git status fixtures/` is clean.

### Safety

- No paid call, no subscription call, no network. No key, credential, `.env` or `settings.env` file was read, nor `~/.config/learnloop/`.
- The main checkout was not touched, and its working vaults were never opened. This worktree's tracked `linear_algebra` and `probability` were opened only by the backup API, and `arxiv_v2` not at all.
- Nothing was pushed, rebased or stashed. `fix/plan-determinism` and its worktree `learnanything-docs` were not modified.

### Open questions for the owner (defaults applied)

1. **The full list's per-session pair order in a staged vault** (Codex review open question 2). Today's full list, one key from the plan, still orders a contrast pair by session, so it can show a pair in the other order from the plan. The serving row is first-wins per item and session, and the plan builds first on Today, so the recorded order is the plan's. The same holds at `mvp-0.24`, where the list is unchanged. **Default: leave it.** A pick from the list is the learner's own order.
2. **The optional successor tag** (Codex review F2 and open question 3). **Decided as none** under the owner's standing ruling (live changes behind kill switches, not successors, for serving changes replay never reads). The switch is the rollback, and the parity above shows it restores main's plans exactly. The review's fallback, folding a tag into R2b + R2c's successor, no longer exists: `mvp-0.24` has landed. If the owner asks for a tag, it would be its own (`mvp-0.25`) with an upgrade step, and no meaning in recorded history would change.
3. **Past staged `plan_block` rows logged with propensity 1** (the stage's open question 2, the review's open question 4). Before this landing, staged builds whose pool R1's draw or a per-session pair order had reordered still logged a deterministic choice. At `mvp-0.24` the same applies to the mixture's logged staged pick, support and candidate rows: the parity above shows their planner values moved on the owner's linear algebra data. The mixture's propensities stay exact given what was logged (G3 conditions on the logged support and staged pick), but the staged component's "deterministic rule" was applied to a randomized pool. Such rows can be found from the same build's slate (`exploration_flag = 1`) or from a serving row whose seed names the session. **Default: flag them when R3's evaluation first reads staged or mixture rows.** No tracked fixture holds any (they are at `mvp-0.8`).
