# Daily-loop bugs: fixes for the 2026-10-11 audit

**Branch:** `fix/daily-loop-bugs`, from `main` at `1a0f7a0`.
**Scope:** the four items under "Known bugs to fix first" in
`docs/specs/daily_loop_frictionless_defaults.md`.
**Migration:** none.

Every fix started from a regression test that failed on `1a0f7a0` for the reason the
audit gave, and passes now. Line numbers in "root cause" refer to `1a0f7a0`.

| # | Bug | Commit | Successor? |
|---|---|---|---|
| 1 | The reader's "write my own question" goes nowhere | `8c131e6` | No: serving only |
| 2 | Dormant or resolved learning objects are still served | `e303ca9` | No: serving only |
| 3 | The Start screen's "postpone" has no handler | `cf81aa2` | No: UI only |
| 4 | The welcome-back "N refreshers" doesn't limit the queue | `eb4b8f6` | No: serving only |

---

## 1. The reader's "write my own question" goes nowhere

### Root cause

- **Where the card went.** `reader.author_qa` (`src/learnloop_sidecar/handlers/reader.py:959`)
  calls `reader_authoring.author_qa` (`src/learnloop/reader/reader_authoring.py:63-131`). That
  writes three things and stops:
  - a `help_me_remember` commitment (`:89`);
  - an activity card version on the shared `learner_authored` family (`:111`);
  - a lineage (`:115`).
- **What the scheduler reads.** `build_due_queue` iterates `vault.practice_items` only
  (`src/learnloop/scheduling/scheduler.py:212`). No practice item was ever created, so the
  card could never be served.
- **The false promise.** The reader still said "✓ Saved in your exact words. It will return
  as personal practice." (`apps/learnloop-tauri/src/screens/ReaderScreen.tsx:2619`).
- **A second blocker.** Even a real item would usually have been dropped. Reading new
  material means the item's LO has no evidence and is on no goal frontier, and the
  cold-start gate (`scheduler.py:283`) drops such items. A fresh item also has no
  `due_at`, so its forgetting risk is 0.

### Fix

Writing the question counts as adopting it into practice, so nothing new is asked of the
learner. `author_qa` now takes the vault `root` and an optional `learning_object_id`. After
the existing writes, which are unchanged and still happen before any AI, it also does
three things.

1. **Files a real practice item** through the existing learner-authored path,
   `item_authoring.author_item`. That means vault YAML, `origin: human`, the learner's exact
   words, the plain correctness rubric, and a `block_span_v1` source ref to the passage. The
   item goes under:
   - the explicit `learning_object_id`, if one was passed; or
   - the first active LO, sorted by id, whose provenance cites the passage's section. This
     uses `reader_progression.learning_objects_for_span`, the same resolution tutor
     promotions use.

   `author_item` gained two optional keyword arguments, `source_refs` and `event_detail`.
2. **Links the item to the commitment** by appending a commitment version with a
   `legacy_practice_item` target (`commitments.add_target`).
3. **Makes it a learner request.**
   - `Repository.requested_practice_item_ids` gained a `UNION` branch. It reads the
     `legacy_practice_item` target of any unretired `help_me_remember` commitment as a
     request, dated from the first version that named the item.
   - The card therefore gets the existing requested-item eligibility floor and front slot
     until its first attempt. After that it is ordinary FSRS practice.
   - `build_due_queue`'s cold-start gate now exempts requested items, so a never-practised
     LO no longer swallows a card the learner explicitly adopted. This also lets tutor
     promotions and rung variants on cold LOs through. They are learner requests too, and
     were being dropped the same way.

**When no active LO fits,** no card is invented. The result says
`practice_status: "reference_only"`, and the reader says the question is "Saved in your
exact words as a reference … not scheduled for practice". The UI makes no promise the
sidecar did not report (`screens/reader/authoredQuestion.ts`). Offline demo mode now
says that nothing was saved.

**Supporting changes:**

- The sidecar reloads the vault after creating a card, so Today sees it immediately.
- Retrying with the same idempotency key adopts one card.
- The DTOs gained `practiceStatus`, `practiceItemId` and `learningObjectId` on the result,
  and an optional `learningObjectId` on the input.

### Successor

**Not needed.** The request is derived at queue time from the raw commitment ledger.
`requested_practice_item_ids` is read only by `build_due_queue` (`scheduler.py:143`).
Nothing in replay, rebuild or any projection changes. The new practice item is ordinary
learner-authored vault content, exactly like `author_practice_item`.

### Tests

`tests/test_daily_loop_reader_authored_practice.py` (8 tests):
- The card is filed, linked and served first on a cold LO with no goal frontier.
- It keeps returning once due after an attempt.
- A retry with the same key adopts one card.
- No topic means reference only.
- An explicit LO is honoured.
- RPC end to end: `reader.author_qa` then `get_today_queue`. The pre-fix failure here was
  the card going nowhere.
- A dormant or resolved LO is never filed under.

`apps/learnloop-tauri/src/screens/reader/authoredQuestion.test.ts` (2 tests): the
personal-practice promise appears only for `scheduled`.

---

## 2. Dormant or resolved learning objects are still served

### Root cause

`LearningObject.status` can be `active`, `dormant` or `resolved`. No serving path read it.

- **Main loop.** The item loop in `build_due_queue` checked item status, derived state and
  that the LO exists (`scheduler.py:212-255`). It never checked the LO's lifecycle.
- **Follow-up lane.** `_insert_pending_followups` rebuilds items by id at maximum priority
  (`scheduler.py:1147`), with the same gap.
- **Probe pool.** `eligible_instruments` (`diagnosis/probe_episodes.py:632`) had the same gap,
  and `enter_stale_uncertainty_reprobes` (`:528`) kept reopening probing on parked LOs.
- **Other doors**, all by id: the probe dialogue, `start_exam`'s pooled ids, and the sidecar
  doors `open_queue_item`, session `get_practice_item`, `start_teach_back` and
  `start_overconfidence_probe`.

### Fix

**One pure rule.** The new module `src/learnloop/vault/lifecycle.py` answers whether an
LO's items may be served (`learning_object_serving_block` / `learning_object_servable`).
Every serving door asks it:

| Door | Change |
|---|---|
| `build_due_queue` candidate loop | Skips the item. This also covers Today, skip, the TUI, CLI `review`/`why`, `explain_practice_item` and the display-only queue readers. |
| `_insert_pending_followups` | Skips the item: cold retries, certification cold probes, intervention and surprise follow-ups. |
| `eligible_instruments` | Returns `[]`. This also covers `next_probe_item`, `get_probe_contract`, calibration and probe offers. |
| `enter_stale_uncertainty_reprobes` | Skips parked LOs. |
| `enter_episode` / `_record_generation_need` | Commission no generation for a parked LO. Its pool is empty because of its lifecycle, not because a surface is missing. |
| `begin_dialogue_block` / `next_dialogue_turn` | Refuses, or ends the block. |
| `start_exam` | Drops pooled items whose LO was put away after reservation. Raises if none are left. |
| Sidecar `open_queue_item`, session `get_practice_item`, `start_teach_back`, `start_overconfidence_probe` | Refuse with the typed code `learning_object_inactive` (`src/learnloop_sidecar/serving.py`). |

**Writes are not gated.** `submit_attempt`, `submit_dont_know` and draft saves still accept
an answer, so an answer typed before the LO was put away still saves.

**Refreshers already behaved.** They come from `resolve_goal_scope`, which already keeps only
active LOs (`goals/goal_projection.py:288-289`). Session building selects nothing itself.

### Successor

**Not needed.** This is a pure serving-eligibility rule. Nothing is persisted, deactivated or
recomputed, so setting the LO back to `active` serves its items again with history, FSRS
state and projections untouched; the tests assert this. `probe_episodes` and
`followup_tasks` are `WORKFLOW` tables, not replayed projections.

### Tests

`tests/test_daily_loop_lo_lifecycle_serving.py` (11 tests): each covers both `dormant` and
`resolved`, and each failed on `1a0f7a0` at the door it names.
- Due queue, including reactivation.
- Follow-up lane.
- Probe pool.
- Stale-uncertainty re-probe.
- Probe dialogue.
- Exam start.
- Sidecar Today queue.
- Sidecar serve doors.

---

## 3. The Start screen's "postpone" button has no handler

### Root cause

- **Desktop.** `apps/learnloop-tauri/src/screens/StartScreen.tsx:1831-1833` rendered a
  `postpone` span with `cursor: pointer` and no handler.
- **TUI.** The TUI's Start screen had the same control as a key binding and a button
  (`src/learnloop/tui/screens/start.py:212, 239, 291-292`). It only flashed "Session
  postponed 1h." and did nothing.
- **No backing behaviour exists.** I searched the DTOs, the sidecar handlers, the Tauri
  commands and plugins, and the CLI. There is no reminder or notification plugin, no
  deferred-start state, and no sidecar method. The only snooze in the codebase belongs to
  maintenance notices. Leaving Start without beginning a session is already one tab away,
  so a "postpone" that only navigated would add nothing.

### Fix

The control is removed from both surfaces, along with the TUI binding, button, action and
CSS selector. A short comment records why. Under the honest-labels rule, a control that
claims an action that never happens is removed rather than wired to a fake.

### Successor

**Not needed.** UI only; nothing persisted.

### Tests

- `apps/learnloop-tauri/src/screens/StartScreen.test.tsx`: no `postpone` control next to
  "begin session".
- `tests/test_daily_loop_start_postpone.py`: the TUI has no button and no binding, and
  pressing `p` does not claim a postponement.

---

## 4. The welcome-back "N refreshers" doesn't limit the queue

### Root cause

- **Where N comes from.** `reentry_summary` sets `refresher_count = len(slipped)`
  (`src/learnloop/scheduling/reentry_summary.py:144`). The panel renders it
  (`apps/learnloop-tauri/src/screens/TodayScreen.tsx:1533`).
- **Nothing used N.** Today calls `get_today_queue` without a `limit`
  (`TodayScreen.tsx:165-175`), and `get_today_queue`
  (`src/learnloop_sidecar/handlers/queue.py:76-93`) built the full, unlimited queue.
- `reentry_adapter.plan_reentry`, which has a small visible cap, is not wired anywhere live.

### Fix

The fix moves toward P6, "a small automatic session of the most useful checks and
reviews", without redesigning re-entry.

- **`reentry_session_cap`** (new, in `reentry_summary.py`) returns the panel's refresher
  count while the panel shows and something slipped. Otherwise it returns `None`. It reads
  the same summary the panel renders.
- **`get_today_queue`** limits the queue to that cap, using the same nearest active goal as
  the panel (`_nearest_active_goal`).
  - The N items are the scheduler's own top picks, the most useful checks and reviews.
  - A smaller requested limit still wins.
  - The slate records the limit it was built under.
  - The reply carries `reentryRefresherCap`.
- **The panel** names the number of items the capped queue actually serves
  (`screens/today/reentry.ts`). The number shown and the session therefore cannot
  disagree, even when fewer items are servable than facets slipped. When nothing will be
  served, the line is dropped rather than saying "0 refreshers". It also says "1 refresher"
  instead of "1 refreshers".

**The cap is live, not frozen.** As refreshed facets recover, the count and the queue shrink
together. Once nothing has slipped, the ordinary queue returns. Freezing N for the whole
session would need per-session persistence (a migration), which this fix avoids. See the
open questions.

### Successor

**Not needed.** This is a serving limit on the offered queue. No projection, replay or
rebuild output changes, and nothing new is persisted. Slates already record
`requested_limit`.

### Tests

- `tests/test_daily_loop_reentry_cap.py` (3 tests): the queue serves exactly the panel's
  count after a break (2 were served for 1 shown before the fix); a smaller requested
  limit wins; with no break, nothing is capped.
- `apps/learnloop-tauri/src/screens/today/reentry.test.ts` (3 tests): the panel shows the
  served count, falls back before the queue is known, and claims nothing at 0.

---

## Files touched

To anticipate conflicts when this merges with the Phase 2 and Phase 3 branches.

**New files** (no conflict risk):
- `src/learnloop/vault/lifecycle.py`
- `src/learnloop_sidecar/serving.py`
- `apps/learnloop-tauri/src/screens/reader/authoredQuestion.ts`, plus `.test.ts`
- `apps/learnloop-tauri/src/screens/today/reentry.ts`, plus `.test.ts`
- `apps/learnloop-tauri/src/screens/StartScreen.test.tsx`
- `tests/test_daily_loop_reader_authored_practice.py`
- `tests/test_daily_loop_lo_lifecycle_serving.py`
- `tests/test_daily_loop_start_postpone.py`
- `tests/test_daily_loop_reentry_cap.py`
- `docs/reviews/daily-loop-bugs.md`

**Edited files.** All edits are small and localized; nothing is renamed or reformatted.

| File | Change |
|---|---|
| `src/learnloop/scheduling/scheduler.py` | One import; an LO gate in the candidate loop; an LO gate in `_insert_pending_followups`; requested items exempted from the cold-start gate. **Most likely to meet Phase 2/3 edits.** |
| `src/learnloop/db/repositories.py` | One `UNION` branch and its docstring in `requested_practice_item_ids`. |
| `src/learnloop/diagnosis/probe_episodes.py` | One import and four small guards. |
| `src/learnloop/diagnosis/probe_dialogue.py` | One import and two guards. |
| `src/learnloop/goals/exam_session.py` | One import; pooled-item filter in `start_exam`. |
| `src/learnloop/reader/reader_authoring.py` | Imports; two keyword arguments on `author_qa`; three new private helpers. |
| `src/learnloop/content/authoring/item_authoring.py` | Optional `source_refs` / `event_detail` on `author_item`. |
| `src/learnloop/scheduling/reentry_summary.py` | New `reentry_session_cap`; docstring paragraph. |
| `src/learnloop/tui/screens/start.py`, `start.tcss` | Postpone removed. |
| `src/learnloop_sidecar/handlers/queue.py` | Re-entry cap; LO refusal in `open_queue_item`. |
| `src/learnloop_sidecar/handlers/practice.py` | LO refusal in session `get_practice_item` and `start_overconfidence_probe`. |
| `src/learnloop_sidecar/handlers/teach_back.py` | LO refusal in `start_teach_back`. |
| `src/learnloop_sidecar/handlers/reader.py` | `author_qa` passes `root` / `learning_object_id` and reloads after a new card. |
| `apps/learnloop-tauri/src/api/dto.ts` | `ReaderAuthorQAInput.learningObjectId`; `ReaderAuthoredCardDto` practice fields; `QueueSnapshot.reentryRefresherCap`. |
| `apps/learnloop-tauri/src/screens/ReaderScreen.tsx` | Status state; honest message. |
| `apps/learnloop-tauri/src/screens/TodayScreen.tsx` | `ReentryPanel` gets the served count. |
| `apps/learnloop-tauri/src/screens/StartScreen.tsx` | Postpone removed. |

**Not touched:**
- the learner-field, embedding and practice-family code;
- migrations and the head fixture;
- the docs vault and its generated references (`docs/learnloop-architecture-vault/`), whose
  line numbers for `tui/screens/start.py` are now slightly stale;
- the tracked fixture vaults.

**Migration:** none. Nothing needs renumbering at merge.

## Verification

All results are from this worktree on `fix/daily-loop-bugs`.

| Check | Result |
|---|---|
| `uv run pytest -n auto` (full suite) | 6152 passed, 0 failed (4 min 6 s) |
| `uv run pytest -m durability` | 62 passed, 6090 deselected |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| `npm run typecheck` (apps/learnloop-tauri) | exit 0 |
| `npm test` (vitest) | 10 files, 32 tests passed |
| Baseline before any change: `uv run pytest -n auto` at `1a0f7a0` | 6129 passed |

**Smoke runs.** I ran these against backup-API copies (`learnloop.db.copies`) of this
worktree's `linear_algebra`, `probability` and `arxiv_v2` fixtures under `fixtures-local/`.
The copies were deleted afterwards and the tracked fixtures are unchanged. Each run drove the
sidecar handlers in-process with no AI.
- Setting the first queued item's LO to `dormant` removed all of that LO's items from the
  Today queue: 40 → 33, 67 → 64 and 32 → 30, with 0 items of the dormant LO served.
- Re-entry on the `linear_algebra` copy, with sessions backdated by 30 days and its goal
  reactivated, showed the panel with 0 slipped facets. The queue was correctly left uncapped
  and the panel line dropped. None of the three fixtures has an active goal as tracked, so
  their re-entry panel never shows.

New regression tests: 23 pytest (8 + 11 + 1 + 3, with parametrized cases counted
individually) and 6 vitest (1 + 2 + 3).

## Open questions for the owner

1. **Which LO a written question is filed under.**
   - Today: an explicit `learningObjectId`, else the first active LO (by id) whose
     provenance cites the passage's section.
   - The reader UI does not yet pass `learningObjectId`. It could pass the guide plan's
     strongest passage LO (as quick-check escalation does) or offer a one-tap move.
   - C2 says filing should be "by LLM, correctable later with one tap". That is a follow-up.
2. **Questions with no LO.** A question on a passage that no study-map LO cites is kept as a
   reference, not scheduled. Should such questions later be adopted automatically when the
   source is added to a study map, or once an LO appears that cites the passage?
3. **Reader "retire" on an adopted card.** It retires the commitment, which ends the request,
   but leaves the practice item active as ordinary practice. Should it also retire the item?
4. **Re-entry cap: live or frozen?**
   - The cap tracks the live slipped-facet count. Doing N refreshers successfully ends
     re-entry and the normal queue returns. A failed refresher keeps its facet in the count.
   - A cap frozen for the whole session would need a `sessions` column (a migration).
   - There is also no explicit "re-entry done, keep going" moment yet. P1 ("done when done,
     with keep going") belongs to the daily-plan work.
5. **What fills the N re-entry slots.** They are the scheduler's top picks, which can
   include a follow-up or cold check rather than an item for a slipped facet. If they
   should be strictly refreshers for the slipped facets, add a reorder floor like
   `_apply_requested_floor`.
6. **Other surfaces not capped.** Skip's queue snapshot is a receipt that is not displayed,
   and it is not re-entry-capped. CLI `review` is not capped. The CLI `reentry-summary`
   prints "Best next session: N refreshers" (`cli/app.py:840`) without serving a session.
7. **Dormant LOs, not fixed here:**
   - The golden-path assessment door (`golden_path.assess_open`) burns its reserved surface
     before an item check could run, so it is not LO-gated. It belongs to the P2 controller.
   - Today's "deferred cold checks" strip can still list a waiting check whose LO is
     dormant. It is display only and never offered.
   - The empty-probe-pool notice sweep (`diagnostic_surface_supply`) is not LO-gated. It
     raises notices, not practice.
8. **A stale open session hides re-entry.** This predates the fix and was not changed.
   `start_session` ends any stale open session at "now" (`end_open_sessions_except`), which
   resets the gap. If the app was closed mid-session before a break, the welcome-back panel
   never shows. Measuring the gap from that session's last attempt would fix it.
9. **The cold-start exemption is broader than bug 1.** It also serves tutor promotions and
   rung variants on never-practised LOs. That is the stated intent of requested items, but
   it is a behaviour change for those paths too.

---

## Follow-ups (branch `fix/daily-loop-followups`, from `main` at `be33cdd`)

The owner approved four items from the open questions above: 8, 7, 2 and 3. Line
numbers in "root cause" refer to `be33cdd`. Every regression test was run against the
`be33cdd` source: 12 of the 13 new tests failed there. The 13th is a guard that passes
both before and after (see F1). None of the four needed a migration or a successor.

| # | Follow-up | Commit | Successor? |
|---|---|---|---|
| F1 | A stale open session hid re-entry (open question 8) | `c0eb2332` | No: workflow timestamps, read live |
| F2 | The guided-path assessment burned a parked LO's surface (open question 7) | `5cd2eb0e` | No: refusal only |
| F3 | Reference-only questions are adopted later (open question 2) | `7b541744` | No: content, not projections |
| F4 | Retiring a reader question retires its card (open question 3) | `e2f2c691` | No: the existing retire path |

### F1. A stale open session hid the welcome-back panel

**Root cause**

- `start_session` calls `repository.end_open_sessions_except`
  (`src/learnloop_sidecar/handlers/sessions.py:47`). That stamped every session left
  open `ended_at = now` (`src/learnloop/db/repositories.py:9056-9062`). A session is
  left open when the app is closed mid-session.
- The welcome-back gap is measured from `most_recent_ended_at`, the latest
  `sessions.ended_at` (`repositories.py:8865`, read at
  `src/learnloop/scheduling/reentry_summary.py:110`). The stamp therefore reset the
  break to zero, and the panel never showed after a break that began with the app
  closed mid-session.
- The stamp also stretched the stale session over the whole break. That widened the
  attempts window `session_attempt_counts` uses for it.
- An attempt made outside any session never counted as activity.

**Fix**

- `end_open_sessions_except` now ends a stale session at its own last activity. That is
  `MAX(started_at, last attempt in the session, checkpoint write)`, computed from
  existing columns only.
- `most_recent_ended_at` returns the learner's last real activity outside an open
  session: the latest completed-session end, or the latest attempt that belongs to no
  still-open session. The method is not renamed; its only callers are the re-entry
  surfaces.
- The open session's own attempts are excluded, so practising inside the re-entry
  session never ends it.
- No migration.

**Successor: not needed.** `sessions` is a `WORKFLOW` table, and the gap is read live.
Nothing in replay, rebuild or any projection changes.

**Tests:** `tests/test_daily_loop_reentry_break.py` (3 tests).

| Test | Result at `be33cdd` |
|---|---|
| A stale open session ends at its last attempt, and the panel shows a 20-day break | Failed: `ended_at` was now, panel hidden |
| A session-less attempt 2 days ago means no welcome-back from a month-old session end | Failed: the panel showed |
| Practising inside the re-entry session keeps the 30-day break (guard) | Passes before and after |

### F2. The guided-path assessment burned a parked LO's reserved surface

**Root cause**

- `golden_path.assess_open` (`src/learnloop_sidecar/handlers/golden_path_assessment.py:32`)
  called `GA.open_assessment` at `:35` first.
- `open_assessment` (`src/learnloop/curriculum/golden_path_assessment.py:173`) advances
  the run to `assessing` (`:208`) and opens the cold administration (`:215`). That is
  the burn: the held-out surface is consumed.
- Only afterwards did the handler read the surface's item (`:47`). Nothing checked the
  LO's lifecycle.

**Fix**

- Before `open_assessment`, the handler resolves the run's `reserved_surface_id` to its
  practice item. If the owning LO is dormant or resolved, it refuses with
  `learning_object_inactive` (`vault.lifecycle` via `learnloop_sidecar.serving`).
- A refused open does not advance the run and does not burn the surface.
- After reactivation the same still-pristine reserve opens normally.

**Successor: not needed.** The refusal persists nothing.

**Tests:** `tests/test_daily_loop_golden_path_lifecycle.py` (2 tests, one each for
dormant and resolved). Each asserts the error code, zero administrations on the surface
and the run still `ready_to_assess`, then that the reserve opens after reactivation.
Both failed at `be33cdd`: the open succeeded and burned the surface.

### F3. Reference-only reader questions are adopted later

**Root cause**

- `_adopt_into_practice` returned `reference_only` when no active LO cited the passage
  (`src/learnloop/reader/reader_authoring.py:224`).
- Nothing ever looked at that question again, even after the study map gained an LO for
  the passage.

**Fix**

- **New sweep.** `reader_authoring.adopt_reference_questions` finds `reader_authored_qa`
  commitments that have no `legacy_practice_item` target and were never retired. It
  resolves each one's span to an active LO the same way writing does, then adopts it
  through `_adopt_into_practice`. The result is a learner-authored card in the learner's
  exact words, linked to the commitment, and therefore requested and served first.
- **Trigger.** The sweep runs in `SidecarContext.load`, right after `sync_vault_state`
  (`src/learnloop_sidecar/context.py:60`).
  - Every study-map apply that adds or links an LO ends in that reload, so this is where
    the LO first becomes visible.
  - When something is adopted, the vault is reloaded and resynced, and the queue
    revision is bumped.
  - A failure is logged and never blocks loading the vault.
  - State sync itself cannot import the reader: that would close a substrate↔reader
    cycle, which `lint-imports` forbids.
  - Queue build was avoided to stay out of `scheduler.py`.
- **Idempotent.**
  - An adopted commitment carries its card as a target and is never swept again.
  - `_adopt_into_practice` also reuses a card already written in the same words under
    the same LO. That covers a crash between writing the YAML and linking it.
- `_adopt_into_practice` now derives the source id from the extraction when the caller
  has none.

**Behaviour to know.** Reader questions saved before the first daily-loop fix, when the
card went nowhere, are reference-only commitments too. They will be adopted once an
active LO cites their passage. That keeps the old "It will return as personal practice"
promise.

**Successor: not needed.** The sweep writes content (a vault item and a commitment
version) through the existing authoring path. No projection, replay or rebuild changes.

**Tests:** `tests/test_daily_loop_reference_adoption.py` (5 tests, all failing at
`be33cdd`):
- Adopted, linked and served first once an LO cites the passage; a second sweep is a
  no-op with no duplicate card.
- A dormant or resolved LO citing the passage adopts nothing (2 cases).
- A retired question is never adopted.
- Sidecar: `reader.author_qa` stays reference-only, the LO is linked, `ctx.reload`
  runs, and Today serves the card.

### F4. Retiring a reader question retires its card

**Root cause**

- The reader's retire (`reader.maintain`, action `retire`) only called `C.retire`
  (`src/learnloop/reader/reader_authoring.py:454-459`), a commitment disposition event.
- The adopted practice item stayed active, so it kept being served as ordinary practice.

**Fix**

- `maintain` takes the vault `root`. Retiring a `reader_authored_qa` commitment also
  retires each active `legacy_practice_item` target through `item_authoring.retire_item`,
  the existing learner retire path, with the typed reason `no_longer_relevant`. That path:
  - flips the YAML status to `retired` and keeps all history;
  - closes the serving doors (`deactivate_practice_item_serving`);
  - retires the substrate surfaces and makes queued surface-mint work obsolete;
  - bumps the queue revision.
- Other commitments' targets are left alone.
- The sidecar handler passes the root and reloads when a card was retired.

**Un-retire.** Nothing to restore: the reader has no un-retire verb, and card retirement
is terminal by design. Also, no desktop control calls `reader.maintain` today; it is
reachable over the API.

**Successor: not needed.** This is the existing content-lifecycle path, with no
projection or replay change.

**Tests:** `tests/test_daily_loop_reader_retire.py` (3 tests, all failing at `be33cdd`):
- The card is retired with its reason and retirement event, its state is inactive, it
  is no longer requested, and it leaves the queue.
- A reference-only question retires nothing else.
- Sidecar: `reader.maintain` retire takes the card out of Today.

### Files touched (follow-ups)

**New:**
- `tests/test_daily_loop_reentry_break.py`
- `tests/test_daily_loop_golden_path_lifecycle.py`
- `tests/test_daily_loop_reference_adoption.py`
- `tests/test_daily_loop_reader_retire.py`

**Edited** (small and local; no frontend, no `scheduler.py`, no migration):

| File | Change |
|---|---|
| `src/learnloop/db/repositories.py` | `most_recent_ended_at` SQL and docstring; `end_open_sessions_except` SQL and docstring |
| `src/learnloop/reader/reader_authoring.py` | `adopt_reference_questions`, `_retire_adopted_items`; source-id derivation and card reuse in `_adopt_into_practice`; `root` on `maintain` |
| `src/learnloop_sidecar/context.py` | Adoption sweep after state sync in `load` |
| `src/learnloop_sidecar/handlers/golden_path_assessment.py` | Lifecycle refusal before `open_assessment` |
| `src/learnloop_sidecar/handlers/reader.py` | `reader.maintain` passes `root` and reloads after a retire |

### Verification (follow-ups)

| Check | Result |
|---|---|
| `uv run pytest -n auto` (full suite) | 6165 passed, 0 failed (3 min 10 s); 6152 before plus 13 new |
| `uv run pytest -m durability` | 62 passed, 6103 deselected |
| `uv run lint-imports --no-cache` | 6 contracts kept, 0 broken |
| Frontend checks | Not needed: no frontend file changed |
| New regression tests against the `be33cdd` source | 12 failed, 1 passed (the F1 guard) |
