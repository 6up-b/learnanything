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

## (B) A Reader note's title can be a `file://` URI

**Where it comes from.** A source with no display title is titled by its URI in `corpus._title` (`display_title`, then
the revision's `original_uri`, then `canonical_uri`). `current_extractions` carries that as `SourceExtraction.title`,
and `vault_notes._source_titles` makes it the note's title. So the raw value is written too: `_store_snapshot` stored
it in `learner_notes.title`, which then reached every view. It is also on the same Settings row twice: the row's
`where` came from `reading.source_title`.

**Fix.**

* **New writes.** `_store_snapshot` stores `VaultNote.display_title`: the source's title, with a `file:` URI read as its
  file name in words (`source_outline.title_from_local_uri`). The judge's prompt and the search hits use it too, and
  the note search now matches the words the learner reads, not the path's.
* **Stored rows, at display.** `note_links.named_for_display` shows a URI-titled snapshot by its source's display title
  now, else its file name. `effective` (the Reader's marks, the path lines, Compare's take, the lesson's notes) and
  `hidden` both call it. `learner_notes` is append-only and no row is rewritten.
* **`where`** on the hidden-notes row names the book the same way.

**Nothing reads as changed.** `VaultNote.title` keeps the source's title as retrieval names it, and the content hash
and the embedded text keep reading it. A readable name changing the hash would have made every such note a new
snapshot, a new judgment and a new embedding. So a note whose row already exists keeps it (stored once per content
hash) and shows the readable name by the display path.

**Left as it is, on purpose.**

* `corpus._title` stays raw. It feeds `section_coverage.scope_signature`, the prompts and keys of Compare, the tutor
  and search, and the persisted family map; changing it would refresh all of those for this one display matter.
* C5's gap reading (`effective_rows`) sends an old snapshot's stored title to its model as it is. That is not a display,
  and a new snapshot's is readable already.
* Only a `file:` URI is rewritten. A web address stays what the Library shows, and `Path.as_uri` is what writes these,
  so no bare path was seen on the write paths read.

**The Library's name, same helper.** `title_from_file_name` moved down to `content.sources.source_outline` (the
notes may not import `content.pipeline`), and `add_source.learner_title` uses the decoded URI too. A file with a space
in its name showed `%20` on its Library card before; now the card and the note say the same thing.

**Reproduce-first.** `tests/test_followups_batch7_note_titles.py` (14). Before the view fix, 4 failed, showing
`file:///home...one_right.pdf` as the note's title. No real vault was opened: the batch 5 observation came from the
probability copy, and these tests rebuild the state synthetically (no display title, a percent-encoded URI).

**Open.** Other surfaces name a source by `extraction.title` and so can show the same URI on such a source (Compare's
books, tutor citations, the library's text search via `source_search._artifact_title`, the source deletion dialog).
They are source titles, not note titles, so they stayed out of this item. See open questions below.

## (C) Module catalog staleness

**Measured.** `module_validate.py` runs in about 3 s (2.98 s wall clock, 1148 modules, 1212 notes), so a guard is
worth having. But its `main()` also checks each note's frontmatter, headings, Wikilinks and test links, and those can
change with ordinary edits, so the guard doesn't call it.

**Guard.** `tests/test_module_catalog_inventory.py` runs `module_validate.inventory_gaps()`, which compares paths only and
never opens a note (0.07 s): a source module or package with no note (*missing*), or a note with no module (*orphaned*).
The failure names the notes and the command, `uv run python docs/learnloop-architecture-vault/_scripts/module_generate.py`.
The generator never deletes a note, so the orphan message says to delete it first. It uses the validator's own inventory
functions, so the two can't disagree about what a module is. Three more tests run it on a small tree: in step (with a
note's contents garbled), a new module and package, and a module gone.

**Effect on landings.** A stage that adds a module now fails the landing gate until the catalog is regenerated, which is
already a landing step. A stage's targeted tests are unaffected unless they list this file.

**Checked on the real tree.** With a stray `src/learnloop/zz_probe_module.py` the guard failed and named its note and the
command (the probe was removed before the commit).
