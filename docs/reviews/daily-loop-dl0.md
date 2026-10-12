# Daily loop DL0: start friction

**Branch:** `daily-loop/dl0`, from `main` at `242ac903`.

**Spec:** `docs/specs/spec_daily_loop_v1.md`:
- §12 row "DL0";
- §6.5 (auto-advance);
- §6.6 (minutes, no readiness form);
- §8 (the streak's honest label);
- §13 gate G11;
- §17 (agent prompt).

**Migration:** none. Schema unchanged.

**Algorithm successor:** none. §11 lists DL0's UI changes as "display and formative only",
with no kill switch.

**Paid calls:** none ($0.00). No model routes and no `judgment_ledger` writes.

| Commit | What |
|---|---|
| `65be3b80` | Remembered minutes and the `get_start_summary` read (Python, Tauri bridge, client) |
| `a5ba091f` | Minutes-only Start with one-tap chips and the honest streak label (desktop and TUI); the TUI's Start stylesheet now loads |
| `9d92353f` | Auto-advance from feedback to the head of the live queue (desktop and TUI) |
| `c4617474` | `tests/test_daily_loop_start_minutes.py` |
| *(this file)* | Review |

---

## What was built

### 1. Minutes-only Start (§6.6, P4)

- **Desktop** (`screens/StartScreen.tsx`). These are removed:
  - the energy and sleep sliders;
  - the client-side `readiness_factor` card. The browser computed it from the sliders, and
    it was never the scheduler's number;
  - the readiness-derived `limit` on the Start preview. Today never applied it (§3.1).

  Begin sends `{ availableMinutes }` only. The preview now asks for the same scheduler
  inputs Begin starts with: minutes and no energy. The "scheduler mode" line keeps the
  scheduler's real rule (probe EIG suppressed at ≤ 20 minutes).
- **TUI** (`tui/screens/start.py`):
  - the `Slider` widget is deleted;
  - the scheduler-mode line now uses the real rule, `minutes <= scheduler.short_session_minutes`.
    Before, it said "short_session" whenever energy was below 0.4, which the scheduler never
    did;
  - `SchedulerSession` gets minutes and no energy.
- **Old clients.** `start_session` still accepts `energy` and `sleepQuality` for old clients
  and the CLI. The scheduler's `energy` input stays and logs `None`.

### 2. Remembered minutes (the last session's)

- **The rule.** `learnloop/scheduling/session_minutes.py`:
  - the remembered value is the `available_minutes` of the most recently started session that
    recorded any (`Repository.latest_session_available_minutes`). A session with NULL minutes,
    from an old client, doesn't erase it;
  - a fresh vault gets 25 (D1).
- **The read.** `get_start_summary` is a new read-only RPC, wired through all four bridge
  layers. It returns the remembered minutes, their source (`last_session` or `first_run`), the
  presets, the chip choices and the streak.
- **Desktop.** Start reads it under `TAG.queue`, which `start_session` invalidates. A summary
  cached before the last session began is not used: Start waits for the re-read, so it never
  previews the queue twice.
- **TUI.** The TUI reads the same rule straight from the repository.

### 3. One-tap minute chips

- **The chips.** 10, 15, 25, 40 and 60.
- **A remembered value that isn't a preset** (30 or 45 from the old chips) is shown as its own
  selected chip. It doesn't silently snap to a value the learner never chose.
- **Desktop.** A click sets the minutes. ←/→ step through the chips; the key bar already
  claimed "←/→ adjust" and nothing handled it. A tap repaints the preview for those minutes,
  dimming the previous one while it loads.
- **TUI.** Click or ←/→.

### 4. Auto-advance (§6.5, P2)

- **Desktop** (`app/autoAdvance.ts`, `FeedbackScreen.tsx`, `App.tsx`). "Next" (`n` or
  Enter) opens the head of the live queue: the item Today focuses first, served with the
  candidate id of the slate that ranked it.
  - The queue is read while feedback shows, once the feedback bundle has loaded, so the
    read never queues ahead of feedback on the single sidecar pipe.
  - The read uses Today's own cache key, which one shared helper, `todayQueueInput`, now
    builds for both. Going back to the list repaints from it.
  - A head from a queue that predates an invalidation (a regrade or a forced follow-up on
    the feedback screen) is never opened. Next waits for the rebuilt queue, which is
    Today's own rule for actionable rows.
  - These fall back to the list, as before:
    - an empty queue;
    - a failed read;
    - an active calibration round, which keeps returning to its own screen.
  - Esc and `b` still open the list, and they cancel a pending advance.
  - The key bar says what Next will do:
    - "next: <topic>" when the head is known;
    - "opening next…" while the queue is read;
    - "list (queue empty)" when there is nothing to open;
    - "continue" when no live queue applies.
- **TUI** (`tui/screens/feedback.py`, `today.py`):
  - `n` on graded feedback returns to Today, which rebuilds the queue as it always did and
    opens its head;
  - Esc, "Back to today" and an ungraded `n` return to the list.

### 5. The honest streak label (§8, D8, G11)

- **The count is unchanged:** local days with a started session.
- **The badge says what is counted:**
  - "begin a session today to keep your streak" while today isn't counted yet;
  - "today ✓" once a session has started today.

  It replaces the old tooltip, "practice today to keep your streak".
- **Freshness.** The badge reads the streak from `get_start_summary`. App's snapshot copy
  was only refreshed when the vault loaded, so mid-session the badge used to show yesterday's
  state.

---

## `get_today_queue` unchanged on fixture copies

No line of the queue handler, scheduler or serializers changed. The evidence:

1. **The test.** `test_today_queue_serves_the_same_queue_without_energy_on_fixture_copies`
   runs on backup-API copies of `linear_algebra`, `probability` and `arxiv_v2`, with a
   frozen clock, because forgetting risk decays continuously.
   - For each fixture, the queue served with `energy` = `medium`, `low`, `high` and absent
     is identical item for item: sections, ids, order, priorities and every component.
   - Only the logged `readinessFactor` moves (0.875 → 1.0 at 25 minutes). It never reaches
     priority (§3.1).
2. **A manual cross-commit run.** Fresh backup-API copies of the three tracked fixtures went
   under `fixtures-local/dl0-{base,branch}-<fixture>/`.
   - Each was loaded once with the base commit's `src/` and `migrations/` (`git archive
     242ac903`) and once with this branch's.
   - Both runs used the same frozen clock and deterministic ULIDs. Session-seeded
     randomization (exploration, contrast-pair order) needs the same session id in both
     runs; without it the two `probability` runs differed even on identical inputs.
   - Each run recorded five calls:
     - the old Start preview (`energy`, `limit`);
     - the DL0 preview;
     - Today with and without `energy`;
     - Today at 15 minutes.
   - The two JSON dumps are **byte-identical** for all three fixtures, ids included.
   - The run also confirmed the §3.1 finding. The old preview's readiness `limit` showed 5–6
     items while Today served 40, 67 and 32. The DL0 preview shows the full count.

## G11

- `test_the_streak_count_is_unchanged_on_fixture_copies` checks the three tracked fixtures.
  `session_day_streak` equals an independent SQL reading of §8 (distinct
  `date(started_at, 'localtime')`) on the last session day and the two days after it.
  `get_start_summary` reports the same streak as the vault load.
- `test_the_streak_counts_any_clients_started_sessions` uses a session row written the way
  another client writes one, with no minutes and no readiness inputs. Mobile M2 sessions are
  rows in `sessions`. The row counts, and beginning a session today keeps the streak.
- The label is tested in `StartScreen.test.tsx`.

---

## Deviations and decisions

1. **No minute chips on Today yet.** §6.6 puts chips "on Start and Today", where a tap
   "re-plans the remaining blocks". DL0 has no plan to re-plan. The DL0 row and its listed
   tests (`StartScreen.test.tsx … chips`) name only Start's chips. A Today chip would need a
   session-write RPC that DL1's `set_plan_minutes` replaces, so it lands with DL1.
2. **The label says "session", not "today's plan".** DL0 has no plan, and beginning a session
   is what the streak counts. "today ✓" appears once a session has started today; §8 ties it
   to plan completion, which arrives in DL1. DL1 should switch both wordings.
3. **Minutes are remembered when a session begins.** A chip tap without Begin is not
   remembered, because DL0 has nowhere to store it. DL1's `daily_plans.remembered_minutes`
   replaces this.
4. **The TUI creates no session row (pre-existing, unchanged).**
   - The TUI reads the remembered minutes, but a TUI Begin is not remembered, and TUI
     practice doesn't count toward the streak.
   - TUI queue refreshes after the first build use the default session, also pre-existing.
     Making them keep the chosen minutes would change what the TUI serves at ≤ 20 minutes, so
     it is left alone. The TUI's Today "min budget" now shows the chosen minutes, display only.
     It used to show `max(20, round(readiness_factor × 30))`, a number nobody chose.
5. **No auto-advance after the probe-block review** (`DiagnosticReviewScreen`). §6.5 names
   feedback only, and the block review has its own continue flow.
6. **Pre-existing TUI bug fixed: `start.tcss` never loaded.** Textual loads a screen's
   `CSS_PATH` only when the screen is pushed, never for the default screen. Start's layout
   rules had never applied: the minutes row was 18 lines tall and the chips sat at column 158
   of a 160-column terminal. Chips are now Start's only control, so `LearnLoopApp.CSS_PATH`
   also loads `screens/start.tcss`. Its selectors are Start's own ids and widget types, with
   no collisions. A regression test checks the chips are on screen and whole at 120 columns.
7. **A slate and a scheduler pass more per Esc.** The feedback screen reads the queue once
   per attempt. With Next, Today never mounts in between, so the count is one per item, as
   before. With Esc, Today revalidates on mount, as it always has, making two. Each Today
   read records a slate.

---

## Tests and gates

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6168 passed**, 14 warnings, 0 failed (140.9 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **62 passed**, 6106 deselected, 0 failed (38.5 s) |
| `npm install` | ok |
| `npm run typecheck` | ok |
| `npm test` (vitest) | 49 passed in 11 files (32 before; 17 new) |
| `npm run frontend:build` | ok |
| `cargo check` | not run: rustc is broken on this machine. The bridge change is two mechanical lines, checked by `tests/test_desktop_rpc_contract.py` |
| DB reference scripts | not needed: no schema change |

**New tests:**
- `apps/learnloop-tauri/src/screens/StartScreen.test.tsx`: 10 tests (1 existing, 9 new):
  - no sliders;
  - remembered minutes sent on Begin, with one preview and no limit or energy;
  - the chips and a tap;
  - ←/→;
  - a non-preset remembered value;
  - 25 on first run and when the summary fails;
  - the chip list helper;
  - the streak label, and "today ✓" over a stale snapshot.
- `apps/learnloop-tauri/src/screens/FeedbackScreen.test.tsx`: 8 new tests:
  - Next opens the head with its candidate;
  - Enter;
  - Esc and `b` open the list;
  - the queue is read only after feedback loads;
  - no stale head after an invalidation;
  - an empty or failing queue falls back to the list;
  - Esc cancels a pending advance;
  - no live queue keeps the old Next.
- `tests/test_daily_loop_start_minutes.py`: 16 tests. Two functions are parametrized over the
  three tracked fixtures.

Mutation checks:
- reverting Next to `onNext()` fails 4 vitest cases;
- `staleAfterMs: 0` in the head resolver fails the invalidation case;
- reverting TUI auto-advance fails its test;
- reading NULL minutes fails two tests;
- removing the stylesheet fix fails the layout test.

## Files touched

- **Python:**
  - `src/learnloop/scheduling/session_minutes.py` (new);
  - `src/learnloop/db/repositories.py` (one read);
  - `src/learnloop_sidecar/handlers/sessions.py`;
  - `src/learnloop/tui/app.py`, `state.py`;
  - `src/learnloop/tui/screens/start.py`, `start.tcss`, `today.py`, `feedback.py`.
- **Desktop:**
  - `apps/learnloop-tauri/src/app/autoAdvance.ts` (new);
  - `App.tsx`;
  - `screens/StartScreen.tsx`, `FeedbackScreen.tsx`, `TodayScreen.tsx` (the shared queue
    input only);
  - `api/client.ts`, `api/dto.ts`;
  - `src-tauri/src/commands.rs`, `main.rs` (one line each).
- **Tests:**
  - `tests/test_daily_loop_start_minutes.py`;
  - `apps/learnloop-tauri/src/screens/StartScreen.test.tsx`, `FeedbackScreen.test.tsx`.

The other branches in flight (`integrate/slice-a-2-3`, Phase 6, `mobile/m1`'s Inbox strip)
should see only these overlaps:
- one import and one `useMemo` body in `TodayScreen.tsx`, away from the hero and the Inbox
  strip;
- one line each in the Tauri `main.rs` and `commands.rs` lists.

## Owner-run commands

None required. To try it, use a copy rather than a tracked vault:
`uv run python -c "from learnloop.db.copies import copy_tree_with_databases as c; c('fixtures/linear_algebra', 'fixtures-local/dl0-try')"`,
then `LEARNLOOP_VAULT=$PWD/fixtures-local/dl0-try npm run dev` in `apps/learnloop-tauri`.
Begin from Start, answer an item, and press `n`. Run `cargo check --manifest-path
apps/learnloop-tauri/src-tauri/Cargo.toml` on a machine with a working rustc.

## Open questions

1. **Logging.** Auto-advanced serves look the same as list picks in the slate logs: both
   carry the head's candidate id. DL1's `serving_origin` (`daily_plan` | `learner_pick`)
   tells them apart. Should DL0 tag them sooner, for router R1's decision logging?
2. **TUI sessions.** Should the TUI create real session rows, so its Begin is remembered
   and counts toward the streak? That changes the streak for TUI users, so it is left to the
   owner.
3. **Wording.** DL1 should change the streak label to §8's "begin today's plan…" and tie
   "today ✓" to plan completion.
