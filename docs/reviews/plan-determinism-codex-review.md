# Plan determinism: the Codex review (`fix/plan-determinism`)

**Status:** both findings reproduced. F1 is fixed. F2 is fixed in part (a kill switch, rollback parity against the base code, shadow rebuilds and a replay test) and rejected in part (the algorithm successor), under the owner's standing ruling. Codex job `20261014-121306-JCHU7I`; base `6dabbc33c` (`mvp-0.23`); the stage's own record is `docs/reviews/plan-determinism.md`, now annotated where the review showed its claims did not hold.

**Commits:** `9b0cd86a8` (the fix and its tests), `bba3c569f` (references regenerated), and this record.

## Findings

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Contrast-pair randomization still changes staged selections | **fixed** | `9b0cd86a8` | `test_plan_determinism.py::test_a_contrast_pair_plans_the_same_staged_block_in_every_session[both_fit]` and `[one_fits]` (both failed `assert 2 == 1` before the fix); `test_the_per_session_draw_keeps_its_own_path` |
| F2 | Medium | Serving behaviour changes without a successor or rollback control | **fixed in part** (kill switch `plan.deterministic_staged_plans`, rollback parity, shadow rebuilds, replay test); **rejected in part** (algorithm successor) | `9b0cd86a8`, `bba3c569f` | `test_the_switch_acts_only_where_the_router_composes_today`, `test_the_plans_scheduler_session_is_greedy_only_where_the_router_composes_today` (off: the predecessor's session, field for field), `test_with_the_switch_off_the_schedulers_draw_reaches_the_staged_plan_again`, `test_with_the_switch_off_a_contrast_pair_follows_the_session_again`, `test_every_defaults_snapshot_records_the_switch_on`, `test_replay_never_reads_the_switch`; base-versus-switch-off parity and shadow rebuilds below. Successor: the owner's standing ruling (live changes behind kill switches, not successors, for serving changes replay never reads) |

The two claims the review rejected are corrected. "The same vault state plans the same blocks whatever the session" now holds for contrast pairs too, including which member is chosen when only one fits (F1). "No successor is needed" now rests on the owner's standing ruling and the kill switch it requires (F2).

## F1: a contrast pair's member order was a second session-seeded draw

**Reproduction.** As reported. The pool's composition ends in `_apply_contrast_pair_order` (`scheduling/scheduler.py`, Meas §3.A4), which swaps a pair's two slots on a draw seeded on the session id and the pair. The plan packs its pool in that order. `seeded_exploration = False` turned off R1's draw only, so the swap still decided the block:

- **Exploratory run, 12 sessions (branch before the fix).** A vault at `mvp-0.23` (router on) with one LO whose two items name each other in `contrast_of`:
  - **both fit** (1.5 estimated minutes each, a 25-minute plan): 8 sessions planned `[pi_pair_a, pi_pair_b]`, and 4 planned `[pi_pair_b, pi_pair_a]`;
  - **only one fits** (5.0 minutes each, a 5-minute plan, the review's scenario): 8 sessions planned `pi_pair_a` alone, and 4 planned `pi_pair_b` alone.
  - Every `plan_block` decision logged `staged_v1`, propensity 1, kind `deterministic`, and chose the block's first item.
- **The regressions, fail-first.** `test_a_contrast_pair_plans_the_same_staged_block_in_every_session[both_fit]` and `[one_fits]` (30 fixed sessions on copies of one vault state) both failed `assert 2 == 1` on the branch before the fix.
- **The base code, 40 sessions** (`git archive 6dabbc33c`, the parity run below): both fit gives 22 `[a, b]`, 15 `[b, a]` and 3 R1-explored plans; only one fits gives 22 `a`, 15 `b` and 3 explored.

**Fix: the staged plan draws the pair's order per pair, not per session.**

- `diagnosis/contrast_pairs.py`: `serving_seed(key, session_id=..., scope=...)` names the two seed scopes. `SEED_PER_SESSION` is the existing seed (`"<session>|<pair key>"`). `SEED_PER_PAIR` is the pair alone (`"pair|<pair key>"`). `plan_contrast_pair_serving(..., seed_scope=...)` uses it; the default is unchanged.
- `scheduling/scheduler.py`: `SchedulerSession.contrast_order_seed` (default `"session"`) is passed through `_apply_contrast_pair_order`. The live composition and R1's counterfactual composition use it alike, so an offer's logged propensity is still computed through the same steps.
- `daily_plan/engine.py`: `staged_plans_deterministic(vault)` is `router_active(vault)` with the F2 switch on. Where it holds, `plan_scheduler_session` builds the pool with `seeded_exploration = False` and `contrast_order_seed = "pair"`. Everywhere else it returns the predecessor's session, `SchedulerSession(session_id, available_minutes)`, field for field.

**Why per pair, and not the greedy order.**

- **The plan is a fixed function of the vault.** The pair's draw no longer reads the session, so the same vault state plans the same blocks in every session. That covers which member is chosen when only one fits.
- **A4's control survives in staged plans.** Its order-effect check reads one serving order per pair (`contrast_pair_order_effect` keys its rows by pair and takes the latest), and its balance audit is the share of pairs whose first member is the lower id. A draw seeded on the pair still varies across pairs, which is exactly what the check consumes, and the serving rows still record it with its seed.
- **Dropping the swap would have hurt the measurement.** Staged plans are the default at `mvp-0.23`. In them the plan's own build records the pair's serving, first-wins per item and session. With no swap, either those rows would claim an order the plan did not serve, or there would be no rows at all.
- **Measurement randomization keeps its own path.** Every other queue build keeps the per-session draw: Today's full list (`get_today_queue`), `skip_practice_item`, the CLI and TUI queues, the simulator, and DL1's plan. `test_the_per_session_draw_keeps_its_own_path` shows a staged vault's ordinary queue build still orders the pair by session and records each session's seed.
- **What this vault draws.** Here the pair's own draw puts `pi_pair_b` first. That is not the greedy order (`pi_pair_a` leads it on the id tie-break), so the measurement's swap is still live. It is just the same in every session.

**After the fix.** Thirty sessions plan one staged block in each case (`[pi_pair_b, pi_pair_a]` both fitting, `[pi_pair_b]` one fitting). Its one decision chose `pi_pair_b` with propensity 1, and every session's serving row records `pi_pair_b` first with seed `pair|pi_pair_a|pi_pair_b`. The parity run below shows the same over 40 sessions, with the default config, in all three worlds.

## F2: a kill switch, and no algorithm successor

**Reproduction.** As reported. The branch changed which blocks a staged plan serves at `mvp-0.23`, with no setting that restored the landed behaviour: `router.enabled = false` returns DL1's pair and removes the staged frame with it. This is a process requirement rather than a behaviour defect. What can be tested is the switch and its parity, and what can be run is the rebuild validation; both follow.

**Fixed: the kill switch.**

- **The key.** `plan.deterministic_staged_plans` (default `true`) is a modelled default, left out of the decision-only template. It sits in `[plan]` rather than `[router]`, because router R2b + R2c rewrites `RouterConfig`. It is read through one function, `daily_plan.engine.staged_plans_deterministic`.
- **What it governs.** Only where the router composes Today (`mvp-0.23` or later, `plan.enabled` and `router.enabled` on). Below `mvp-0.23`, or with either switch off, it has no effect. A vault whose config predates the key, which is every existing `mvp-0.23` vault, reads it on.
- **Off: the predecessor's session, field for field.** `plan_scheduler_session` returns exactly the `SchedulerSession(session_id=..., available_minutes=...)` that `6dabbc33c` built. Both session-seeded draws then reach the staged pool again: R1's exploration (forced in `test_with_the_switch_off_the_schedulers_draw_reaches_the_staged_plan_again`) and the per-session pair order (`test_with_the_switch_off_a_contrast_pair_follows_the_session_again`).
- **Snapshots and references.** All fifteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed with `defaults_fingerprint_for_version`. Each moves only because the effective config gains the key, and `test_every_defaults_snapshot_records_the_switch_on` pins every one. The DB/config references gain the field (830 effective leaves), and §11 of `spec_daily_loop_v1.md` gains its row.

**Rollback parity against the base code (run).** The base was exported with `git archive 6dabbc33c` (`src`, `tests`, `migrations`) and run on `sys.path`; the process asserted it had loaded the export's `learnloop`. The branch ran with `[plan] deterministic_staged_plans = false`. Settings:

- three worlds at `mvp-0.23` with the router on: R1's near-ties (the stage's `EXTRA` vault) and the contrast pair both fitting and only one fitting;
- 40 fixed sessions each, one backup-API copy per session, `SystemClock` frozen, manual grading, an empty `LEARNLOOP_CONFIG_DIR`;
- recorded for each case: the plan's blocks, the `plan_block` decisions, the view's projection, the session's contrast serving rows (seed, value, position, adjacency) and its slate candidates (rank, design probability, realized flag).

| Run | Distinct plans (near-ties / pair, both fit / pair, one fits) | Same as base |
|---|---|---|
| Base `6dabbc33c` | 2 / 3 / 3 | — |
| Branch, switch off | 2 / 3 / 3 | **120 of 120 cases identical** (every field above) |
| Branch, default (on) | 1 / 1 / 1 | — (the fix) |

**Rejected: the algorithm successor.**

- **The ruling.** The owner's standing ruling, applied at UX Phase 1's landing on main (`docs/reviews/ux-phase1.md`, "Landing onto main"), is: live changes behind kill switches, not successors, for serving changes that replay never reads. The facet-locks F6 ruling and exam protection's F6 (`exam-protection-codex-review.md`) cite the same decision. The 2026-10-12 owner decisions in force for this stage say the same ("live changes behind kill switches, no shadow stages by default").
- **This is such a change.** It decides which items a plan's pool offers, in which order. Daily plans are workflow and receipt rows that replay never reads (migration 180, and the import contract "Replay, evidence and serving internals never read the daily plan"). No replayer builds a queue, and a logged plan keeps its blocks. The contrast serving rows (`contrast_pair_servings`, RECEIPT) keep their meaning, and each records its own seed.
- **What a successor would cost now.** Router R2b + R2c (`router/r2bc`, in flight) mints the next tag, `mvp-0.24`, and this stage was asked to stay small and local so it composes. `SUCCESSOR_CHAIN` is unchanged (latest `mvp-0.23`).
- **No upgrade path is needed.** The key's default applies when a vault loads, so an existing `mvp-0.23` vault serves deterministic staged plans with no config write (tested), and setting the key false restores the landed serving.

**Shadow-rebuild validation (run).**

- **Copies.** Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the worktree's three tracked fixtures, under `fixtures-local/pd-review/shadow/`. Each was migrated to head 202 with `db.migrate.apply_migrations`: 155 → 202 for `linear_algebra` and `probability`, 152 → 202 for `arxiv_v2`.
- **Runs.** `learnloop rebuild --shadow --json`, with an empty `LEARNLOOP_CONFIG_DIR`, in two groups:
  - at the copy's own version (`mvp-0.8`): HEAD with the copy's config, HEAD with `--set plan.deterministic_staged_plans=false`, HEAD with `=true`, and the base export;
  - at the candidate `--set algorithms.algorithm_version=mvp-0.23`, where the switch acts: HEAD with the switch on, HEAD with it off, and the base export.

| Copy | Replayed attempts | Rebuilt LOs | Rows at `mvp-0.8` (facet / mastery / schedule) | Four `mvp-0.8` runs identical | Rows at candidate `mvp-0.23` | Three `mvp-0.23` runs identical | Live DB sha256, before = after every run |
|---|---|---|---|---|---|---|---|
| `linear_algebra` | 70 | 8 | 22 / 6 / 47 | yes | 79 / 21 / 47 | yes | `85be152d1a3395a3…` |
| `probability` | 2 | 1 | 2 / 1 / 1 | yes | 2 / 18 / 1 | yes | `7a0d83a411be744c…` |
| `arxiv_v2` | 3 | 3 | 2 / 34 / 3 | yes | 6 / 34 / 3 | yes | `f4166aba0093cea1…` |

Every run (ten per copy over two batches: the first ran all seven variants, the second reran the three `mvp-0.23` variants to compare them with each other) reported `live_database.unchanged: true`. The candidate-version rows are larger than the own-version rows because that comparison also changes the algorithm version; what the switch is checked for is that the runs within each group agree.

- **What "identical" means.** Equal once the surrogate ULIDs the replay mints (the shadow marker id and the replayed family ids, which playbook step 6 ignores) and the echoed `applied_overrides` are set aside.
- **The diff rows are the baseline gap, not this change.** They compare each fixture's stored projections with a replay today. The base code reports the same rows with the same values.
- **The head fixture too.** `test_replay_never_reads_the_switch` shows the same on `fixtures/migration_head_202` at the latest tag: every DERIVED table is identical after rebuilds with the switch on and off, and no plan row is written.

## How it composes with router R2b + R2c

- **Files `router/r2bc` does not touch.** `scheduling/scheduler.py` and `diagnosis/contrast_pairs.py` change on this side only.
- **`engine.py`.** The change is inside `plan_scheduler_session`, which this stage added, plus the new `staged_plans_deterministic` and one `__all__` line. None of it is in R2b's hunks.
- **`schema.py`.** The key goes in `PlanConfig` after `reading_from_furthest`. `router/r2bc` rewrites `RouterConfig` and adds `RouterWeights` after `PlanConfig`'s validator, so the hunks do not meet.
- **`config/template.py`.** The snapshot hashes conflict as every config change's do, and are recomputed from the composed defaults at the landing.
- **After both land.** `mixture_active` implies `router_active`, so the mixture's pool is deterministic too, and the mixture's ε floor is the only exploration (owner rule 2026-10-13).

## Gate

Run in this worktree at `bba3c569f` (the fix and its references; this record changes only `docs/reviews/`), with `TMPDIR=<worktree>/fixtures-local/tmp`. The two pytest runs added `-q -p no:cacheprovider` (output and cache only).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install restores 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,908 passed**, 0 failed, 49 warnings (10 min 59 s): the stage's 10,900 plus the 8 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,808 deselected, 1 warning (1 min 50 s) |
| Targeted, before the gate | `test_plan_determinism.py` 14 passed; the plan, router, scheduler, contrast-pair, RW3a, learner-pick, reading-step, UX round-2, CLI-help, config and `mvp-0.23` upgrade files 484 passed; every `test_mvp0*_upgrade.py`, `test_recurrence_commands.py` and `test_exam_protection_review.py` 204 passed |
| Defaults snapshots | all fifteen recomputed (`defaults_fingerprint_for_version`); each moves only because the effective config gains the key |
| References | `db_generate_reference.py` rerun (`bba3c569f`): `Config - plan` gains the field, the two prose counts move from 829 to 830, the rest is provenance and moved line citations. `db_validate_reference.py` reports `errors: []` |
| Schema | unchanged (head 202), no migration, no table |
| CLI help snapshot | unchanged (no CLI option); its test passes in the full suite |
| Frontend, `cargo check` | not run: nothing under `apps/` changed |
| Manual runs | rollback parity and shadow rebuilds above, on test vaults and backup-API copies under `fixtures-local/pd-review/` only; the tracked fixtures were only copied |
| Paid calls | none |

## Open questions

1. **Per-pair seeding in staged plans (F1).** A staged plan now gives each contrast pair one member order, drawn on the pair and recorded, instead of a fresh order every session. Recommended: keep it. It is deterministic, and A4's order-effect check reads one order per pair anyway. The alternative is the scheduler's greedy order, which would leave A4 with no randomized staged rows.
2. **The full list in a staged vault.** Today's full list (one key from the plan) keeps the per-session pair order, so it can show a pair in the other order from the plan. The serving row is first-wins per item and session, and the plan builds first on Today, so the recorded order is the plan's. Recommended: leave it. A learner pick from the list is the learner's own order, as before.
3. **The successor (F2).** Rejected under the standing ruling, with the kill switch it requires. The owner may still ask for a tag at the checkpoint; it would then be folded into R2b + R2c's successor at its landing rather than minted separately.
4. **Past staged rows** (the stage's open question 2) stands. Before this branch, staged `plan_block` rows whose pool was drawn logged propensity 1. Pools reordered by a contrast pair's per-session draw are a second such case. They can be found from the same build's serving rows (a seed that names the session).

## Re-review (Codex job `20261014-125619-vXT7lT`)

**Status:** the re-review reopened F1 and confirmed F2 fixed under the owner's standing ruling. F1 reproduced, and it is fixed. It reported no new defects in `73b2a9e9f..fix/plan-determinism`.

**Commits:** `1be65010a` (the fix and its tests), `906064c98` (references regenerated), and this record.

| Id | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | REOPENED: Start's sessionless staged build skips the pair's deterministic order | **fixed** | `1be65010a` | `test_plan_determinism.py::test_a_contrast_pair_plans_the_same_staged_block_in_every_session[both_fit]` and `[one_fits]` now include Start's sessionless build. Both failed `assert 2 == 1` without the scheduler change. `test_the_same_vault_state_plans_the_same_staged_blocks_in_every_session` also includes Start, and `test_with_the_switch_off_a_contrast_pair_follows_the_session_again` pins Start's rollback order |
| F2 | Medium | Kill switch, rollback parity, no successor | **confirmed fixed** by the re-review (no change) | — | The reviewer independently verified the rollback session settings and all fifteen defaults fingerprints. This fix leaves the switch-off path as it was; the sessionless parity run below covers it |

### F1: Start's build has no session

**Reproduction.** As reported:

- Start calls `useDailyPlan(null)` (`StartScreen.tsx`), which builds and persists the daily plan through `get_daily_plan` with no session.
- `_apply_contrast_pair_order` (`scheduling/scheduler.py`) returned a sessionless queue before any draw. So Start's pool kept the greedy order, while every named session's pool took the pair's own draw.
- On the two regressions with Start added, without the scheduler change:
  - **both fit:** Start planned `[pi_pair_a, pi_pair_b]`; the thirty sessions planned `[pi_pair_b, pi_pair_a]`;
  - **only one fits:** Start chose `pi_pair_a`; the sessions chose `pi_pair_b`.
  - Both failed `assert 2 == 1`.

**A second effect: the A4 record contradicted the plan.** The probe ran Start's build and then Begin (session `s_begin`) on one vault, on the branch before this fix. Begin kept the block Start had planned, `[pi_pair_a, pi_pair_b]` (or `pi_pair_a` alone). The session's serving row, written by Begin's pool build with the pair's seed, recorded `pi_pair_b` first. A4's order-effect check would therefore have read an order the learner was never served.

**Fix (`1be65010a`).**

- **Sessionless builds take the pair's draw.** A per-pair draw (`contrast_order_seed == "pair"`, set only on the staged plan's pool where `staged_plans_deterministic` holds) is seeded on the pair alone, so it needs no session. `_apply_contrast_pair_order` now applies it to a sessionless queue as well.
- **No serving row without a session.** A sessionless build still writes none, because there is no session to key the idempotent row on. The receipt write is suppressed on the same path as the R1 counterfactual composition (`record=False`).
- **The per-session draw is unchanged.** With no session it still leaves the queue untouched. That covers the switch off, DL1's plan and every other queue build, so they behave as before.
- **One docstring.** `plan_scheduler_session` (this stage's function in `daily_plan/engine.py`) gains a sentence saying the guarantee covers a build with no session.

**Tests.**

- **Both fit cases.** Start's sessionless build joins the thirty named sessions' shapes: one plan, with the same blocks, decisions and projection. The tests also assert that:
  - Start writes no serving row;
  - Begin on Start's plan keeps Start's block;
  - Begin's serving row records the pair's own order and seed.
- **The general test.** `test_the_same_vault_state_plans_the_same_staged_blocks_in_every_session` adds Start to its thirty sessions.
- **Rollback.** With the switch off, Start's sessionless build keeps the greedy order `[pi_pair_a, pi_pair_b]` and records nothing. That was the base behaviour.

**Sessionless parity (run).**

- **Setup.** The probe ran Start's build and then Begin on three worlds at `mvp-0.23` with the router on: R1's near-ties, and the contrast pair with both members fitting and with only one fitting. It used test vaults under `fixtures-local/pd-rereview/`, `SystemClock` frozen, manual grading and an empty `LEARNLOOP_CONFIG_DIR`. It recorded the blocks, the `plan_block` decisions, the projection, the serving rows and the slate candidates.
- **Base and switch off.** The base export (`git archive 6dabbc33c` under `fixtures-local/archive-base`, asserted to be the `learnloop` loaded) and the branch with `plan.deterministic_staged_plans = false` matched in **all 6 cases**, on every field.
- **Switch on.**
  - Start and Begin plan the same blocks in every world.
  - The pair is `[pi_pair_b, pi_pair_a]` (or `pi_pair_b` alone).
  - Begin's serving row records `pi_pair_b` first with seed `pair|pi_pair_a|pi_pair_b`.
  - The near-tie world's Start block is the base's. Only Begin's slate and projection differ, because the base's session explored there (R1).

**Composition with router R2b + R2c.** The change is in `scheduling/scheduler.py`, which `router/r2bc` does not touch, plus one docstring sentence inside `plan_scheduler_session`. It is still small and local.

### Gate (re-review)

Run in this worktree at `906064c98` (the fix and its references; this record changes only `docs/reviews/`), with `TMPDIR=<worktree>/fixtures-local/tmp`. The two pytest runs added `-q -p no:cacheprovider` (output and cache only). A full suite started before the Claude Code restart (at `1be65010a`, 10,908 passed) is superseded by this run on the final tree; its durability lane never ran.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install restores 5.14.0) |
| `uv run lint-imports --no-cache` | **17 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10,908 passed**, 0 failed, 48 warnings (11 min 25 s). The count is unchanged: the fix extends existing tests and adds none |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **100 passed**, 10,808 deselected, 1 warning (1 min 48 s) |
| Targeted, before the gate | `test_plan_determinism.py` **14 passed** |
| References | regenerated in `906064c98` (provenance and moved line citations only). Rerun on `906064c98`: `db_generate_reference.py` changes only the `source_commit` provenance lines, so that churn was not kept; `db_validate_reference.py` reports `errors: []` |
| Schema, config, defaults snapshots, CLI help | unchanged (no migration, no config key, no CLI option) |
| Frontend, `src-tauri` | unchanged, so the npm and cargo checks do not apply |
