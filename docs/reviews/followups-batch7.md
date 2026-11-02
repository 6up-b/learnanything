# Follow-ups batch 7 (stage `followups-batch7`, branch `fix/followups-batch7`)

Base `aae65635b6` (main: follow-ups batches 5 and 6 landed; mvp-0.43, migration 237). Worktree
`learnanything-dl2`.

Three queued follow-ups (A to C). Each defect has a reproduce-first test, and each item is its own commit.
**No successor and no migration.** No config key was added, and no new constant. Kill switches are unchanged.
The Decider and the router LLM still do not score lesson candidates (TE1b R1 stays deferred).

## (A) Budget deferrals never resume

**Finding** (Codex verify job `20261102-181511-QNGSpd`, P2). A positive decision became `capped` when today's
capacity was exhausted, and `pending_builds` left it out because `capped` was not in `BUILD_DECISIONS`. The next
day, with the section unread and capacity free, `run_trigger` made zero builds and the row stayed open.

**Ruling R10** (recorded verbatim): "Batch 6 landed with this open, under the owner's proportionate bar: a capped
prebuild costs only a build the learner can still get by pressing, with no wrong figure, no spend and no evidence
harm. It predates batch 6's step 0."

**Fix.** `capped` is a build decision (`prefetch_ledger.BUILD_DECISIONS`), so a capped row waits in the same queue as
a power-deferred one and goes through the same `run_builds` guards: cancelled, foreground work, a prebuild's rich job
in flight, the switch and mains on the vault as configured now, the author route on the plan, and the items'
protection over the whole author context. `run_trigger` still only runs that queue on mains with no plan wait.

* **Both caps before any request.** `run_builds` only checked `max_daily_builds` (`reserve_build`). A row capped by
  `max_daily_render_minutes` would have reached the author with the render budget still used up, so `run_builds` now
  checks `render_minutes_left` first, for every row in the queue. That also covers a power-deferred row, and a fresh
  `build` row whose budget ran out mid-queue; `decide_and_log` already caps both the same way.
* **No new draw.** The row keeps its id, verdict, propensity, `sampled_eu` and digest; only its `request_id` and
  `input_hash` are set (once). A pass with unchanged inputs adds 0 rows and 0 draws: the open row's request key keeps
  the candidate out (`filter_candidates`), so batch 6's guarantee holds.
* **A closed horizon stays closed.** `close_horizons` runs before `pending_builds`, which reads open rows only.
* **Order.** Oldest first, and a batch in its sampled-EU order (spec §10b.3), since a cap now chooses among rows
  waiting together. Before, a batch's order within one timestamp was its ULIDs'.

**Counting.**

* The opening model's `observations` and the report's `built` use `BUILD_DECISIONS`, so a resumed build counts in
  both. `started_today`, `render_minutes_today`, `waits` and `incremental` read request rows and receipts, so they
  already counted it, on the day it started.
* `skipped` now counts deferred decisions with no build yet, and a new `resumed` block counts those built after
  waiting, so one decision is never in both. This changes `skipped.power` and `skipped.plan` for a deferral that was
  later built: they used to count it as skipped and built at once.
* `pauses.with_prebuilds_earlier_that_day` read the decision's time, which is the wrong day for a resumed build. It
  now reads the request's. `report_block` still selects rows with `since` by the decision's time, so a resumed build
  appears in the window of its decision.

**Found on the way, fixed because a resume would otherwise build the wrong thing:**

* **A resumed planned visual was the wrong request** (reproduced with `deferred_power`, so older than this item).
  `pending_builds` rebuilt a lesson's candidate from its anchor, which has no grounding keys. It built on the first
  book's passage, under an input hash the lesson's step never asks for, with a rich job on the menu. It now asks
  `_lesson_candidates` again and matches by the row's `request_key`. A node reached or replanned since has no match
  and is not built; the row closes with the lesson.
* **A press while waiting.** A capped row lasts for days, so the learner may press for the same input first. Resuming
  would spend a build, record a prebuild request on the pressed figure, and turn the press into an observation of
  opening. `run_builds` now passes over a row whose figure exists (`already_built`) and its horizon closes it `asked`.
  A row with a request already stored (a pass that died before `_link`) still goes through, so it gets linked.
* **The Reader's "a prebuild is coming"** (`prefetch_pending`) had its own copy of the decision list. It now reads
  `BUILD_DECISIONS` and needs today's caps to have room (`capacity_left`), so a read doesn't poll for work no pass will
  start today (Codex re-review F18's rule).

**Reproduce-first.** `tests/test_followups_batch7_prefetch_capped_resume.py` (21 tests). Before the fix, 9 failed: the
next-day build, the render-cap resume, the unchanged-inputs pass (its note), the EU order, the report and model
counts, the planned visual for `capped` and for `deferred_power`, the unlinked request, and the Reader's pending
read. The horizon, guard and already-built tests passed before the fix as well, because nothing resumed then; they
pin what the fix must not break.

**Spec.** §10b.4 and §10b.6 carry *as built* notes.
