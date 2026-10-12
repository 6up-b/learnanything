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
