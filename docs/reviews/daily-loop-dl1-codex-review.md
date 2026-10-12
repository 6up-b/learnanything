# Daily loop DL1: Codex review fixes

**Branch:** `daily-loop/dl1`, worktree `learnanything-dl1`. The review covered the DL1 build
(`0afa38c2`..`80161805`, described in `daily-loop-dl1.md`).

**Findings:** one High, five Medium, four Low (F1–F10; F10 bundles six small gaps). All ten
reproduced, nine of them with a failing test first; F6 and the first F10 gap were missing
receipts, so their tests are new assertions on receipts that did not exist. All ten are
fixed. Re-measuring the fixture copies after the fixes turned up one more defect in DL1's
own code (**N1**, below), also reproduced and fixed.

**Paid calls:** none ($0.00). No model or embedding route was touched, and the manual runs
build plans only (no grading). **Migration:** none; the schema is unchanged (stop and
closed-plan pick receipts use the existing `attention_blocks` columns, see F6).
**Algorithm version:** still `daily_plan_v1` = `mvp-0.12`; every change is serving-only
inside the successor, with `plan.enabled = false` still DL0's Today (G1 tests unchanged
and passing).

## Review

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Never-attempted items go into the repair lane, bypassing admission and entering re-entry | fixed | `8aaf6fb8` | `tests/test_daily_plan_review_regressions.py::test_f1_reentry_never_plans_an_unseen_sibling_of_an_old_error`, `::test_f1_a_recent_error_repairs_the_failed_item_and_the_unseen_one_is_new`, `::test_f1_admission_off_serves_no_never_attempted_item` (real scheduler), `::test_f1_repair_needs_a_recent_error_not_any_active_one`; `test_daily_plan_build.py::test_each_item_takes_the_first_lane_that_matches` updated |
| F2 | Medium | A false re-entry plan the day after every break | fixed | `00e2cd07` | `::test_f2_practice_in_a_session_left_open_yesterday_is_not_a_break`, `::test_f2_a_stale_session_without_attempts_counts_from_its_start`, `::test_f2_the_break_still_shows_when_the_only_open_session_began_today` |
| F3 | Medium | The view's projection runs the live chooser | fixed | `bfa7fcb5` | `::test_f3_plan_reads_never_call_the_live_chooser` |
| F4 | Medium | Mid-plan follow-ups break the re-entry item cap and lane allotments | fixed | `8683f2e2` | `::test_f4_followups_keep_a_reentry_plan_within_its_item_cap_and_lanes`, `::test_f4_a_followup_that_cannot_fit_is_declined_not_appended` |
| F5 | Medium | Plan RPCs publish full-queue offer receipts the learner never saw | fixed | `5ad52948` | `::test_f5_plan_rpcs_finalize_no_offer_and_picks_keep_the_list_offer` |
| F6 | Low | Stop decisions are not receipts and can be lost | fixed | `ba2f22d7` | `::test_f6_a_reopened_plan_that_stops_again_keeps_both_stop_receipts`, `::test_f6_a_router_stop_keeps_its_propensity_and_candidates` |
| F7 | Low | Chooser output is not validated at the seam | fixed | `715a0c37` | `::test_f7_malformed_choices_fall_back_and_are_flagged` |
| F8 | Low | `expected_minutes` unbounded on the wire, bounded on the model | fixed | `eea41453` | `::test_f8_out_of_range_expected_minutes_reach_the_writer_bounded` (through the vault writer) |
| F9 | Low | Displayed numbers don't match what is served (L1) | fixed | `a0eb1c15`, `bc3446e5` | `::test_f9_extensions_hold_the_review_load_to_the_days_budget`, `::test_f9_more_new_preview_is_what_confirming_plans`, `::test_f9_reentry_panel_names_only_what_it_counts`; vitest `app/dailyPlan.test.tsx` "rounds minutes a day honestly…", `screens/today/DailyPlanView.test.tsx` "shows a small trade-off as computed…" |
| F10 | Low | Other gaps (six) | fixed | `ba2f22d7`, `a0eb1c15` | `::test_f10_a_pick_after_the_plan_closed_is_recorded`, `::test_f10_more_new_on_an_open_plan_is_refused_and_keeps_the_plan`, `::test_f10_keep_going_with_nothing_left_is_idempotent`, `::test_f10_a_crash_before_the_first_block_keeps_requests_first`; `test_daily_plan_replay.py` (asserts `wal`; forbids embedding clients) |
| N1 | (found re-measuring) | An item whose estimate is its lane's whole load misses the stored allotment | fixed | `c93f7427` | `::test_n1_an_item_whose_estimate_is_its_lanes_whole_load_is_planned` |

Each new test was run against the unfixed code (the fix stashed) and failed there, except
where noted: F1 4 of 4; F2 2 of 3 (the third pins that today's own session still never ends
a break, true before and after); F3; F4 2 of 2; F5; F7; F8; F9 3 of 3; F10's crash and
idempotency tests; N1. F6's two tests, F10's closed-plan pick test and F10's open-plan
test failed structurally (the receipts and `PlanStillOpenError` did not exist); the
open-plan defect itself was reproduced by the reviewer's reading of `more_new`, which
closed an open plan before building.

### F1: never-attempted items are new material; repair has a recency bound

- **Reproduced** with the real scheduler (`build_due_queue`, no fake components): an LO
  with one failed item and an unseen sibling. With an 80-day-old error the sibling's
  `recent_error` is about 1e-5, never zero, so the classifier made it `repair`: it was in the
  re-entry plan (`stopped_by = reentry`), and with `plan.new_admission_enabled = false` it was
  still served. With a 1-day-old error the sibling was `repair`, not `new`.
- **Fix** (`daily_plan/lanes.py`):
  - **Repair** = follow-ups, and *previously attempted* items whose `recent_error` is at
    least `REPAIR_MIN_RECENT_ERROR = exp(-2)`: a full-severity error within 14 days (two of
    the scheduler's 7-day decay constants), a half-severity one within about 9.
  - **A never-attempted item is new material** even on an LO with errors, so §6.3's
    admission (ceiling, cap, floor, the switch) and §7 (re-entry has no new material) govern
    it. Follow-ups stay repair whatever their history.
- **Spec reading.** §6.1's order lists repair before new, and its table puts "items on LOs
  with recent errors" in repair. Read literally, an unseen sibling is repair. But §6.1 also
  carves out exactly one class of never-attempted items as "never new material" (scheduled
  checks), and §6.3, §7, G10 and the `new_admission_enabled` switch all assume
  never-attempted material is admitted new material. The fix follows those. The recency
  bound is a module constant, not a `[plan]` key (no config or fingerprint churn); see open
  question 1.

### F2: a session left open yesterday is activity, not a break

- **Reproduced:** last ended session 12 days ago, practice yesterday in a session never
  ended (Done and closing the app end none; only `start_session` ends stale sessions, after
  Start has already read the plan) → `kind = reentry`, `gap_days = 12`.
- **Fix:** `Repository.most_recent_ended_at(stale_open_before=…)`. An open session that
  started before that instant is stale, and its last activity counts: its last attempt or
  checkpoint write, else its start, which is what `end_open_sessions_except` would end it
  at. The plan passes local midnight (`PlanEnv.gap()`), so today's own session still never
  ends a break. The DL0 panel and the re-entry adapter keep calling it without the argument
  (unchanged).
- **Effect on the fixture copies.** `probability`'s only session (2026-08-03) was never
  ended, so before this fix the plan saw *no* activity at all and built a normal plan; it is
  now a 69-day re-entry, as §7 intends. `linear_algebra`'s gap moves from 76 to 69 days for
  the same reason.

### F3: projections never call the live chooser

- **Reproduced:** a counting router-like chooser was called 3 times by one `plan_view`.
- **Fix:** `PlanPolicy.projection_chooser` (default `lane_quota_v1`) and
  `PlanPolicy.projection()`; `project_blocks` always simulates with it, never with
  `policy.chooser`. The source is shared (sources are already pure: the container probes them
  for redistribution). The shared simulation is `engine.simulate_blocks`, which the more-new
  preview uses too (F9). Router R2's seam stays `PlanPolicy(source, chooser)`; R2 can supply
  its own cheap projection chooser if it wants one.
- **Test:** the router chooser makes the first real decision, is then armed to raise, and
  `plan_view` must not call it; two reads give identical projections.

### F4: follow-ups respect the item cap and are charged to their lane

- **Reproduced:** the reviewer's re-entry scenario ended at 9 items over a cap of 8, repair
  spent about 9 minutes on an allotment of 0, one follow-up displaced another. Separately, a
  follow-up too large to fit had already displaced tail items before being declined.
- **Fix** (`engine._insert_followups`, `_displacement_plan`, `_followup_release`;
  `records.PlannedItem.lane_release`, `PlanRecord.ledger`):
  - A follow-up joins only if a *displacement plan* frees both its minutes and, in
    re-entry, an item slot from the unserved tail. Earlier follow-ups and learner picks are
    never displaced for it. Otherwise it is declined without displacing anything and waits in
    the pool (not debt).
  - It is charged to its lane (repair). When that lane has too few minutes left, the other
    lanes release the shortfall in a pick's order (push, new, maintain), then from plan
    minutes no lane holds; the release is recorded as `lane_release` on its `item_planned`
    event and folded into the ledger while the follow-up is not displaced.
  - Follow-ups forced into the next block (no block current) respect the item cap and the
    same charge, which `decide()` now sees (`forced_allotment`, `forced_spent`).
  - A minutes re-plan dates its epoch (`split.epoch_at`) so earlier releases stop applying.
- **Test:** after every step of the reviewer's scenario, `item_count() ≤ 8`, every lane's
  spent ≤ its allotment, planned ≤ budget; no follow-up is displaced; only chooser items are.

### F5: no false offer receipts

- **Reproduced:** `get_daily_plan`, a serve and a prefetch wrote 4 `desktop_queue` offer
  receipts for lists no screen showed.
- **Fix:** the plan's eligible builder no longer calls `finalize_scheduler_offer`. The plan's
  own `item_served` receipt records what was served; the served candidate still binds (it is
  a returned candidate of the build's slate in the session; tested with
  `bind_submission_offer`). `get_today_queue` still publishes the full list when it is shown.
  `plan_learner_pick` takes that list's `scheduler_candidate_id` (validated: same item,
  returned, same session), so a pick is served with the offer the learner actually picked
  from; Today passes it.
- **Field.** Plan-served attempts now read as `unknown` serving in the learner field's
  `_serving` (no offer receipt), instead of `learner_pick` from a list never shown. A
  distinct `daily_plan` serving kind in the field is out of DL1's scope; see open question 3.

### F6 (and F10's closed-plan pick): append-only receipts

- **Fix:** a decision that is not a block is a *receipt row*: an `attention_blocks` row of the
  plan with a NULL `plan_ordinal` (NULLs are distinct under the existing unique index, so no
  schema change) and its `block_chosen` event. Each STOP appends one
  (`action = stop_for_today`, the candidate set, chooser, `chosen_by`, propensity, fallback,
  `decision_ref`, the state, the stop reason); `split_json.stop` is gone. A pick after the
  plan closed appends an `open_list_pick` receipt with its `item_served` event
  (`serving_origin = learner_pick`, no propensity).
- `PlanRecord.receipts` / `stops()` fold them; they never count toward minutes, items or
  block numbers. `learnloop plan report` adds `stop_decisions`, `open_list_picks_after_plan`
  and counts stop fallbacks in `chooser_fallbacks`; `plan show` lists the receipts.
- This keeps §6.8 rule 6 literal (every decision is an `attention_block_events`
  `block_chosen` row) and supersedes deviation 2 of `daily-loop-dl1.md` (corrected there).

### F7: the seam validates a chooser's choice

- `decide()` treats a choice as malformed when `chosen_by` is not `lane_quota`, `staged` or
  `mixture` (`learner_pick` is the container's alone, rule 3), when the propensity is not a
  finite number in (0, 1] (booleans rejected), or when `why_kind` is unknown. It falls back
  to `lane_quota_v1`, flagged, with `fallback_reason` on the receipt (also recorded for
  unoffered ids, `continue_current` and a chooser that raised).

### F8: the wire keeps `expected_minutes` inside the model's bounds

- `PracticeItemPatchPayload.expected_minutes` coerces before validation: a non-number,
  zero, a negative or a non-finite value is dropped (the estimator falls back to the mode
  median, then 3.0); above 240 it is clamped. The JSON schema the model sees is unchanged
  (a `BeforeValidator`), so no prompt or schema snapshot moved. Tested through
  `upsert_practice_item`, which validates `PracticeItem`.

### F9: the numbers shown are the numbers served

- **Ceiling.** An extension (keep going, the plan after re-entry) held L to 0.80 × its own
  10 minutes. It now uses the day's remembered budget (`ceiling_basis = remembered_minutes`
  on the admission receipt). Test: L = 14 min/day, remembered 40, the extension's ceiling is
  32 and it admits past the floor (before: 8, stopped by the ceiling).
- **More-new preview.** It was a greedy fit that ignored requests-first and LO packing.
  `build_plan` is split into `_prepare_plan` (classify, admit, split) and the persist step;
  the preview prepares the extension and dry-runs it with `simulate_blocks`, so its items,
  minutes and trade-off are what confirming plans (`practice_item_ids` in the preview).
  Test: a 5.5-minute request first in a 10-minute extension leaves room for one new item;
  the old preview said two.
- **Rounding.** The done screen shows `minutesPerDay`: whole minutes from 1 up, one decimal
  below ("0.3"), "less than 0.1" for a trace; never rounded up to 1.
- **Re-entry panel.** Names now come from the counted (slipped) LOs: with a goal, in the
  goal's blueprint order first (all of its slipped facets, not just its top 3), then the
  rest by largest drop. A goal facet whose LO did not slip is not named; nothing slipped,
  nothing named.

### F10: the other gaps

| Gap | Fix |
|---|---|
| A pick after the plan closed lost its record | `open_list_pick` receipt (F6) |
| `plan_more_new(confirm)` on an open plan stopped it | `PlanStillOpenError` → `invalid_request`; the preview stays read-only |
| Keep going on an empty pool inserted an empty plan per tap | One empty extension says so; further taps return it when the new extension would plan nothing (decided by feasibility, never by asking the live chooser) |
| A crash between the plan insert and its first block lost requests-first | The next step finds an open plan with no block and no receipt and places its stored requests first |
| The durability test accepted `delete` | Asserts `wal` (the marker builds the vault fresh with production pragmas) |
| The replay test did not guard embeddings | Embeddings switched on; `ready_client_for_task`, `default_embedding_client` and `OpenAIEmbeddingProviderClient` construction forbidden |

### N1: estimates at the precision the split stores

- **Found** re-measuring the fixture copies after F1/F2: `probability`'s 15-minute re-entry
  plan, with one due 9.76-minute item, came out empty ("nothing more worth doing today
  fits"). The split stores lane minutes rounded to 4 decimals (`9.7613`); the item's estimate
  kept full precision (`9.76134`). The lane's only candidate missed by 4e-5, the lane
  released its minutes, and the plan stopped.
- **Fix:** `Estimator.item_minutes` / `reading_minutes` return the estimate quantized to the
  4 decimals the split, admission and item events persist, so the container compares like
  with like (`ItemEstimate` keeps full precision).

## The review's claims that didn't hold

All corrected by the fixes above, and the stale lines in `daily-loop-dl1.md` are corrected
(pool and repair definition, projection, re-entry gap, deviation 2, the closed-plan pick,
the replay test, and the served-set table marked superseded):

- "Re-entry: repair and maintain only, no new" — now true with real scheduler components
  (F1).
- "`new_admission_enabled = false` admits none" — now true (F1).
- "Re-entry respects ≤ 8 items" — now true with mid-plan follow-ups (F4).
- "The projected blocks (the deterministic pair run forward without logging)" — the
  projection now always uses the deterministic projection chooser (F3).
- "Every block decision logged" — stop decisions are now `block_chosen` receipts (F6).
- "Rebuild and replay make zero model calls (tested)" — now also no embedding client, and the
  WAL test asserts `wal` (F10).
- "Re-entry: last real activity (F1)" — stale open sessions now count (F2).

**Spec conformance rows** the review marked "Built with defects" are now built: §6.1
classification, §6.3 admission (no repair bypass; extension ceiling), §6.8 rule 6, the
projection seam, follow-ups within lane allotments. Deviation 6 (re-entry order across
lanes), deviation 10 (Esc to the plan view) and deviation 12 (§9 latency report) are
unchanged and remain open questions in `daily-loop-dl1.md`.

## Manual runs after the fixes (backup-API copies, no paid calls)

Fresh `copy_tree_with_databases` copies (`fixtures-local/dl1fix-*`) of the DL1 copies
(`fixtures-local/dl1-*`, already at `mvp-0.12`), their old plan rows deleted, then today's
plan built with the real scheduler and real clock (2026-10-12, no session). No tracked
fixture was touched.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Plan kind, gap | re-entry, 69 days (was 76) | **re-entry**, 69 days (was normal: its only session was never ended, F2) | re-entry, 83 days |
| Budget (remembered) | 10 (10) | 15 (30) | 15 (25) |
| Split line | `10 min · maintain 10` (was `maintain 7 · repair 3`) | `15 min · maintain 10` | `15 min · maintain 10` (was `maintain 7 · repair 3`) |
| Pool lanes | maintain 21, no repair (errors are 69+ days old, F1) | maintain 1 | maintain 3 |
| Chosen + projected blocks | maintain 3 items (9.9 min) | maintain 1 item (9.76 min; empty before N1) | maintain 2 + 1 (10.5 min) |

Then "Re-entry done → keep going" on each (the post-re-entry plan for the day's rest, or a
keep-going extension when less than a minute is left), and a more-new preview:

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Plan | keep_going, 10 min | normal, 20.24 min | normal, 18 min |
| Split line | `maintain 6 · new 4` | `maintain 10 · new 10` | `maintain 8 · new 6` |
| Pool lanes | maintain 21, new 20, **no repair** | new 66, maintain 1, **no repair** (was `repair 9 · new 21`) | new 29, maintain 3 |
| Admission (L, ceiling, basis) | 1 (floor); L 23.7 > 8, `remembered_minutes` | 10, daily cap; L 4.2, ceiling 24, `remembered_minutes` | 8, load ceiling; L 9.0, ceiling 20, `remembered_minutes` |
| More-new preview | 3 items, 8.3 min, +2.97 min/day | 2 items, 7.0 min, +2.5 | 1 item, 3.5 min, +1.25 |

`probability`'s repair lane disappears because its 9 repair minutes were unseen siblings of
two old errors (F1); they are now new material under admission.

## Gate results

Run on `c93f7427` (only the two review docs changed after it).

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, then `uv pip install pypdfium2` | OK |
| `uv run lint-imports --no-cache` | **13 kept, 0 broken** |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7,900 passed**, 0 failed, 46 existing warnings; 221 s. 7,877 before, 23 new (`test_daily_plan_review_regressions.py`). An earlier run of the same tree also gave 7,900 passed; it was rerun because a source file was briefly swapped during it to check a test against the old classifier |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **86 passed**, 7,814 deselected, 1 warning; 93 s (the replay test now asserts `wal` and forbids embedding clients) |
| `npm install`, `npm run typecheck` (apps/learnloop-tauri) | OK; 0 type errors (npm install reports esbuild's blocked postinstall, as before) |
| `npm test` (vitest) | **122 passed** in 26 files (120 before; 2 new) |
| `npm run frontend:build` | Passed; existing >500 kB chunk warning |
| `cargo check` | Not runnable (broken `rustc`); no Rust file changed |
| DB reference scripts | Not needed: no schema or config change |
| Mobile pins | Unchanged: no new RPC; the eight DL1 RPCs stay never phone-allowed (`test_mobile_allowlist.py`, `test_mobile_host_auth.py` pass in the suite) |
| Tracked working vaults | Untouched (`git status` clean for `fixtures/linear_algebra`, `probability`, `arxiv_v2`); manual runs only on `fixtures-local/dl1fix-*` |

## Files touched

- **Python:** `daily_plan/lanes.py` (F1), `engine.py` (F2–F7, F9, F10), `records.py` (F4,
  F6), `view.py` (F3, F9), `admission.py` (F9), `reentry.py` (F2, F9), `report.py` (F6),
  `estimates.py` (N1); `db/repositories.py` (`most_recent_ended_at` argument, F2);
  `db/stores/daily_plans.py` (NULL ordinal receipt rows, F6);
  `content/proposals/ai_contracts.py` (F8); sidecar `handlers/daily_plan.py` (F5, F10).
- **Desktop:** `api/client.ts`, `api/dto.ts`, `screens/TodayScreen.tsx` (F5's pick offer),
  `app/dailyPlan.ts`, `screens/today/DailyPlanView.tsx` (F9), tests.
- **Tests:** `tests/test_daily_plan_review_regressions.py` (new, 23), `test_daily_plan_build.py`
  (one assertion), `test_daily_plan_replay.py` (F10).
- **Docs:** this file; `docs/reviews/daily-loop-dl1.md` (stale lines).
- No new RPC (the eight stay pinned never phone-allowed), no migration, no config key, no
  Rust file.

## Open questions (new)

1. **Repair recency.** Repair now needs `recent_error ≥ exp(-2)` (a full-severity error
   within 14 days). Keep it a constant, or make it `plan.repair_recent_error_days`?
2. **Unseen siblings of a recent error** are new material (admitted, capped, never in
   re-entry), against §6.1's literal repair-before-new order. Confirm, or should a sibling
   on an LO with an error from the last day or two be repair after all?
3. **Field serving kind.** Plan-served attempts now have no offer receipt, so the learner
   field reads their serving as `unknown`. Add a `daily_plan` serving kind to the field
   (reading the plan's `item_served` receipts), or leave it to router R1?
