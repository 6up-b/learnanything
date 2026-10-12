# Daily loop DL0: Codex review fixes

**Branch:** `daily-loop/dl0`. The review covered the DL0 build (`65be3b80`..`04b7410a`,
described in `daily-loop-dl0.md`).

**Codex job:** `~/.cache/codex-agent/jobs/20261012-020326-smpbqM`.

**Findings:** three Medium, no High. All three reproduced with a failing test first, and
all three are fixed.

**Paid calls:** none ($0.00). **Migration:** none; the schema is unchanged. **Serving:**
unchanged; no scheduler, queue handler or serializer line moved.

## Review

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | Medium | Auto-advance ignores a newly forced follow-up | fixed | `c684fc49` | `src/app/autoAdvance.test.tsx` "resolves the head of a queue rebuilt after a forced follow-up"; `src/screens/FeedbackScreen.liveQueue.test.tsx` (both tests) |
| F2 | Medium | Next accepts a queue invalidated during its fetch | fixed | `c684fc49` | `src/api/queryCache.test.ts` "follows up a fetch invalidated in flight" (×2); `src/app/autoAdvance.test.tsx` "never resolves a queue invalidated while it was being read"; `src/screens/FeedbackScreen.test.tsx` "never opens a head from a queue invalidated while it was being read" |
| F3 | Medium | TUI minutes are advertised as remembered but never persisted | fixed | `ad578081` | `tests/test_daily_loop_start_minutes.py::test_tui_remembers_the_minutes_it_began_with_across_a_restart`, `::test_tui_minutes_are_the_newer_of_its_own_begin_and_the_last_session`, `::test_the_tui_minutes_store_never_breaks_start` |

All the desktop tests use the real client wrapper and the real query cache, with only the
Tauri transport faked. F1's tests use them so the invalidation comes from the wrapper,
not from the test. The old test called `invalidate()` itself and couldn't see the bug.

### F1: a forced follow-up didn't invalidate the queue

- **Reproduced.** The fake sidecar moved the queue head when `trigger_followup` ran, but
  `resolve()` still returned the old head after one queue read. On screen, ⇧D then `n`
  opened `pi_before`, not the follow-up.
- **Fix.**
  - `api.triggerFollowup` now goes through `mutating([TAG.queue], …)`, so it invalidates
    Today's queue once it settles. The sidecar's `trigger_followup` queues a follow-up
    task or records an intervention need. No other cached read shows either, so `queue`
    is the only tag it needs.
  - **Writes still in flight.** Pressing `n` while ⇧D was still running had the same
    defect: the cached queue was still current when Next read it.
    - `FeedbackScreen` now tracks its own queue-affecting writes and Next waits for any
      still in flight. These are the regrade, the forced follow-up, the clarification
      answer, the eliciting response and the cause report.
    - Esc still cancels a pending advance.
- **Mutation checks.**
  - Dropping the wrapper's invalidation fails 3 tests.
  - Dropping the wait for writes in flight fails 1.

### F2: a queue invalidated mid-read was accepted

- **Reproduced.** Two cache defects showed up together:
  - `resolve()` shared an in-flight prefetch, invalidated before it answered, and opened
    its head (`pi_stale`).
  - The cache's own follow-up after such a fetch never started. It called `getOrFetch`
    while its own promise was still the shared in-flight one, so it got that promise back.
  - A third case: an invalidation in the same millisecond as the fetch start was stamped
    equal to the fetch's `updatedAt`, so the stale result looked fresh.
- **Fix** (`api/queryCache.ts`, `app/autoAdvance.ts`):
  - **Follow-up.** The completed request gives up its in-flight slot before following up,
    so the follow-up is a real request. Until the follow-up lands, the stale result stays
    "fetching", so the key bar never names its head.
  - **Stamp order.** An invalidation is stamped after the start of any request in flight.
    A request records its start as `max(now, invalidatedAt)`, since it reads every write
    already stamped. That keeps the follow-up from looping.
  - **`resolve()`.** Once the request answers, `resolve()` checks the cached state against
    the latest invalidation and reads again when the result is older. After 4 reads it
    returns null, and Next falls back to the list.
- **Mutation checks.**
  - Reverting `resolve()` to "return what was awaited" fails 2 tests.
  - Restoring the self-sharing follow-up fails 2.
  - Dropping the in-flight stamp bump fails the same-millisecond case.
- **Scope.** `queryCache.ts` is shared, but the change only makes its documented rule
  hold: the follow-up "once" after an invalidation in flight. No caller relied on the
  follow-up never running. StartScreen's freshness test (`invalidatedAt <= updatedAt`) is
  the same rule.

### F3: TUI minutes weren't persisted

- **Reproduced.** A fresh TUI picked 60 and began. After a restart, Start offered 25.
- **Why there's no session row.** The TUI still records no session row. A row would be
  adopted by the desktop as its active session (`SidecarContext` reads
  `most_recent_open_session`). It would also move the re-entry gap
  (`most_recent_ended_at`) and the streak. That makes it a serving change, outside a
  UI-only phase, and the owner question in `daily-loop-dl0.md` stays open.
- **The fix** is a defined settings path instead (`learnloop/tui/minutes_memory.py`):
  - **Storage.** A TUI Begin, by Enter or `s`, saves its minutes and time to
    `<LearnLoop config dir>/tui/session-minutes-<hash of the vault path>.json`. That is
    beside `settings.env`, one file per vault, written atomically.
  - **Start.** TUI Start offers the newer of that choice and the last session's minutes
    (`remembered_session_minutes(…, chosen=…)`, new source `last_choice`).
  - **The intro line** names the source: "the minutes you began with last time",
    "minutes from your last session", or, on first run, "they are remembered next time".
    The last one is now true.
  - **Failures.** A missing, damaged or foreign record is ignored. An unwritable directory
    makes Begin show a warning toast, and Begin still works.
  - **Scope.** No vault file is written, so the tracked working vaults gain no untracked
    files. Tests are isolated by conftest's `LEARNLOOP_CONFIG_DIR`, and the new tests point
    it at their own `tmp_path`.
- **What stays as it was.**
  - The desktop keeps DL0's rule, the last session's minutes. It doesn't see a TUI choice.
  - A chip tap without Begin isn't remembered on either client.
  - DL1's `daily_plans.remembered_minutes` replaces both.
- **Mutation checks.**
  - Not saving on Begin fails 1 test.
  - Not reading the store fails 2.
  - "The choice always wins" fails 1.
  - Trusting a foreign or damaged record fails 1.
- **Repository.** `latest_session_available_minutes()` became `latest_session_minutes()`,
  which returns `(minutes, started_at)`. It is a read added by DL0 with no other callers.

### The review's other claims

- **Corrected.** The three claims it disproves ("never opened", "forced follow-ups
  invalidate the queue", "remembered next time") are now true.
- **Changed.** `daily-loop-dl0.md` is corrected where it described them.
- **No action needed.** The spec-conformance rows the review marked as implemented.

## Gate results

| Check | Result |
|---|---|
| `uv sync --extra dev` + `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **6171 passed**, 14 warnings, 0 failed (162.2 s); 6168 before, 3 new |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **62 passed**, 6109 deselected, 0 failed (24.9 s) |
| `npm install` | ok |
| `npm run typecheck` | ok |
| `npm test` (vitest) | **57 passed** in 14 files (49 before; 8 new) |
| `npm run frontend:build` | ok |
| `cargo check` | not run: rustc is broken on this machine. No Rust file changed in this step |
| DB reference scripts | not needed: no schema change |

**New tests:**
- **vitest:**
  - `api/queryCache.test.ts`: 3;
  - `app/autoAdvance.test.tsx`: 2;
  - `screens/FeedbackScreen.liveQueue.test.tsx`: 2;
  - `screens/FeedbackScreen.test.tsx`: 1.
- **pytest:** `tests/test_daily_loop_start_minutes.py`: 3. The file now has 19 tests.

## Files touched

- **Desktop:**
  - `apps/learnloop-tauri/src/api/client.ts` (one wrapper);
  - `api/queryCache.ts`;
  - `app/autoAdvance.ts`;
  - `screens/FeedbackScreen.tsx`;
  - tests.
- **Python:**
  - `src/learnloop/tui/minutes_memory.py` (new);
  - `tui/screens/start.py`;
  - `scheduling/session_minutes.py`;
  - `db/repositories.py` (DL0's read);
  - `tests/test_daily_loop_start_minutes.py`.
- **Docs:**
  - this file;
  - `docs/reviews/daily-loop-dl0.md` (four stale lines).

Nothing touches `TodayScreen.tsx`, the scheduler or the Tauri bridge, so there is no new
overlap with `integrate/slice-a-2-3`, Phase 6 or `mobile/m1`.

## Open questions

1. **Desktop and TUI minutes.** Should the desktop's Start also read the TUI's last choice,
   so one remembered budget spans both clients before DL1? DL1's
   `daily_plans.remembered_minutes` does this anyway.
