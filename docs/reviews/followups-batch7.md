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
  A row with a request already stored (a pass that died before `_link`) is linked by `link_stored_requests` before
  any horizon closes and before any build guard (Codex review F1; `docs/reviews/followups-batch7-codex-review.md`).
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
* Only a `file:` URI is rewritten, which is what `Path.as_uri` writes for an imported file. A web address stays what the
  Library shows. A legacy source note with no canonical URI keeps its relative note path as `original_uri`
  (`source_library`), so a note on such a source would still show that path; the Library shows its file name. Not
  observed on a vault, and not a URI, so left alone.

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

## Gate (this stage, on `fix/followups-batch7`)

The full suite, the durability lane and whole vitest were not run: they belong to the landing gate on the merged tree
(owner rule, 2026-10-17).

* `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2`.
* `lint-imports --no-cache`: 42 kept, 0 broken.
* Targeted pytest in the 5G scope, `-n 6`, on the 60 files in `docs/reviews/followups-batch7.targeted-tests.txt`:
  **1364 passed, 5 skipped**, 0 failed. Which tests skipped, and why, was not read (the run used `-q`).
* `module_validate.py`: PASS, run outside pytest under `env -i` with an empty, existing `HOME`, `CODEX_HOME` and
  `LEARNLOOP_CONFIG_DIR`. The catalog was not regenerated, since this stage adds no module; notes' contents stay stale
  until the landing's usual regeneration.
* Not run because nothing touched them: frontend (typecheck, vitest, build), `cargo check`, durability-marked tests,
  the DB reference scripts. No migration, no schema change, no DB or connection code.

**No live or paid call was made.** Every model is a fake. No vault was opened outside pytest's synthetic ones, and the
desktop app was not launched. The only runs outside pytest (`lint-imports`, `module_validate.py`) ran under `env -i`.

## Open questions

1. **Other surfaces that name a source can show the same URI** on a source with no display title: Compare's books, tutor
   citations, the library's text search, the source deletion dialog. They read `corpus._title` or a copy of its chain.
   The fix at the root changes `SourceExtraction.title`, which feeds `scope_signature`, prompts and keys, so it would
   re-judge on affected vaults. Suggested as its own item, by display at each surface, or by setting display titles on
   those sources (the owner's call, since it writes rows). Not observed beyond the note on the probability copy.
2. **A prebuild refused by a switch still spends a reservation.** A waiting decision with a goal, with `show_me` switched
   off, reserves one of today's builds in this process before the build refuses it, and no request goes out. Older than
   this item (a deferred row does it too), and only reachable with that switch off. Left under the proportionate bar.

## Landing onto main

Prepared on `fix/followups-batch7` (worktree `learnanything-dl2`) from the stage tip `d6b2a772a9`, onto main
`aae65635b6`; the orchestrator fast-forwards main and pushes. No merge was needed: main was still `aae65635b6` before
the gate and when this was written. No migration, no successor and no config key, so no fingerprint recompute.

**One thing needs a decision: the full suite is not green, because of the Codex CLI, not this branch.** See "Codex CLI
0.166.0" below.

### Step 0: V1, a decision linked to the wrong request — `68c4f7d12e`

**The defect** (scoped verify job `20261102-185455-Vue122`, Low). A rich-only prebuild has no figure until its job stores
one. After an enqueue failure left an orphan request (no figure, no job), a successful retry's request had no figure yet
either, so `_link` took the older orphan, once and for good. The retry's figure then named a request the decision didn't,
and opening it closed the decision `neither`. Reading the code, `retry_plan_waits` selects by the decisions' linked
requests, so it would also have missed that retry's job (not tested separately).

**Fix (`figures/prefetch.py`).** `_served_request` is the one predicate: a request names a figure or its rich job exists.
`_link` and `link_stored_requests` both use it. `_link` now returns whether it linked, and `run_builds` counts a build in
`result.built` only then.

**A case the predicate also changes, beyond the brief's.** A request recorded against *another* request's pending rich
job (`service._rich_pending`) has neither a figure nor its own job. It used to be linked at once and could never be
opened, since that job's figure names the other request. Now the row stays in the queue with a note, no model is called,
and a later pass reuses the stored figure on a request that names it, so opening it closes `opened` (tested).

The cost is that each pass while that other job is pending or waiting for the plan adds one more `figure_requests` row
for the decision. No request goes out, and the decision still takes one slot of today's builds. It is bounded by the
passes inside the decision's horizon. This was not measured on a vault; it is on the open list below.

**Reproduce-first.** `tests/test_followups_batch7_prefetch_link_served.py` (4 tests), through the pass functions and the
durable job queue. Against `d6b2a772a9`'s `prefetch.py`: 2 failed, 2 passed (the two that pass pin `link_stored_requests`
and a second failed enqueue, which were already right). With the fix: 4 passed. The decision's `input_hash` stays null on
a rich-only build, as it did before; the assertion on it was removed from the first draft of the test, not fixed in code.

### Step 0: V2, the module catalog guard read untracked files — `9b98323472`

**The defect** (same job, Low). `inventory_gaps` globbed the filesystem, so an untracked `src/learnloop/local_probe.py`,
an ignored `src/learnloop/build/generated.py` or a temporary note under the catalog failed an unrelated suite.

**Fix (`_scripts/module_validate.py`).** `tracked_files` reads `git ls-files -z --cached`, existing files only, on both the
source and the catalog side. Generated output is excluded because it is ignored, so git doesn't track it; there is no
separate list. `main()` and `source_files()` keep their whole-tree inventory. With no git checkout the guard skips, as
`test_public_tip_guards.py` does.

**What this changes in section (C).** The check recorded there, a stray `zz_probe_module.py` failing the guard, no longer
holds for an untracked file: the guard now fails once the file is added to the index, and an untracked note doesn't
satisfy a tracked module. Confirmed by a stray untracked module on the real tree (guard passes, probe removed).

**Reproduce-first.** `tests/test_module_catalog_inventory.py`, now 9 tests. Before the fix 3 failed (untracked module and
note; ignored module; tracked module with only an untracked note). With the fix: 9 passed.

### Regeneration — `49647ffe3f`

* `db_generate_reference` 372 table notes; `db_validate_reference` errors `[]`.
* `desktop_generate` 308 TS/TSX and 6 Rust notes; `desktop_validate` passed.
* `module_generate` 1148 module notes and 63 package maps; `module_validate` PASS (1212/1212 YAML, 39636 wikilinks,
  37677 file links).
* `validate_vault` passed (2096 notes).

### Gate (tip `49647ffe3f`, main `aae65635b6`)

| Check | Result |
|---|---|
| Targeted pytest (61 listed files, at `9b98323472`) | 1381 passed, 5 skipped |
| `lint-imports --no-cache` | 42 kept, 0 broken |
| Full suite (`-n 8 --dist worksteal`, 10G scope, `flock`, `env -i`) | **1 failed**, 24183 passed, 90 skipped, 47 xfailed (46:24) |
| Durability lane | 188 passed, 1 skipped |
| Owner lane (fresh backup-API copies, `fixtures-local/landing-batch7/owner-lane`) | 83 passed, 4 skipped, and the 2 known failures only (`test_activity_backfill.py::test_backfill_logs_attempt_duration_interaction_events`, `test_placement_fixture_copies.py::...[arxiv_v2]`) |
| Frontend | `npm install`, typecheck clean, whole vitest 260 files / **2475 passed** (`--maxWorkers=4`, 5G scope), `frontend:build` built |

`src-tauri` does not differ from main, so cargo check was not run. The smoke ran alongside most of the full suite, which
may be why that took 46 minutes against batch 6's 42 (not measured).

### Codex CLI 0.166.0: three failures that are not this branch's

The installed CLI changed during the gate: `/usr/lib/node_modules/@openai/codex` is dated 2026-11-02 19:35:30, and the
full suite ran from about 19:18 to 20:05. `codex --version` now reports 0.166.0. This agent did not install it.

| Test | Full suite | Alone on 0.166.0, 3 runs | On main's code (`aae65635b6`) |
|---|---|---|---|
| `test_diagnosis_isolation.py::test_configured_mcp_servers_are_listed_and_disabled` | failed | failed 3 of 3 | failed |
| `test_codex_isolation_mcp_check.py::test_the_installed_codex_passes_the_launch_check[False]` | passed (before the upgrade, by inference: the file's run time wasn't checked) | failed 3 of 3 | failed |
| `test_codex_isolation_mcp_check.py::test_the_installed_codex_passes_the_launch_check[True]` | passed (same) | failed 3 of 3 | failed |

All three assert the overrides list exactly. 0.166.0 lists a feature the lockdown has not classified,
`plugin_discovery_prefetch`, on by default, and `_verified_isolated_overrides` adds
`features.plugin_discovery_prefetch=false` as designed for a newer CLI's unknown feature. So the launch check returned
its overrides and the feature is switched off; what fails is the tests' exact list. Whether that feature is otherwise
harmless was not reviewed.

The 12 test files that use the real CLI were rerun together on 0.166.0: 697 passed, 1 skipped, and these 3 failed. Any
landing from now on will see these failures until the feature is classified, as was done for 0.164 and 0.165. That is
not done here: it is outside this batch and the classification is a security review.

### Smoke (fresh owner copies, `fixtures-local/landing-batch7-smoke/`, driver `scripts/smoke.sh`, then `scripts/hidden.sh`)

**Setup.** Adapted from batch 6's: fresh backup-API copies of the three mvp035 owner copies, each neutralized under its
own side's code (every AI route at `127.0.0.1:9`, key variable unset), `env -i` with an empty `HOME`, `CODEX_HOME` and
config directory, and an audit hook logging process starts and refusing non-loopback sockets and Codex starts (its
self-test refused `1.1.1.1:443` and `codex --version`). Code: `git archive` of main `aae65635b6` and the branch
`49647ffe3f`, each with `src/` and `migrations/`. On each side: `upgrade` mvp-0.35 -> **mvp-0.43**, the primary desktop
load, `migrate_vault` (head 237, 0 applied), `rebuild-derived-state`.

| Check | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| Today, branch vs main | byte-identical (525266 B) | byte-identical (740827 B) | byte-identical (344204 B) |
| Plan dump, branch vs main | byte-identical (84721 B) | byte-identical (124046 B) | byte-identical (32458 B) |
| Library card titles, branch vs main | 3 cards, 0 differ | 4 cards, 0 differ | 12 cards, 0 differ |
| Vault notes' content hash and embedded text hash, branch vs main | 2, identical | 3, identical | no notes |
| Vault notes' display title | unchanged | **3 changed**, URI to readable | no notes |
| `rebuild --shadow` (branch) | 0/0/0, live unchanged | same | same |

No copy has a file name with a space, so the `%20` decoding on Library cards wasn't exercised on a vault; it is covered
only by the tests in section (B).

**Hidden notes.** No copy has a hidden note or a `learner_notes` row, so one was made: the copy's first readable Reader
note, linked by hand to a passage and hidden through the sidecar's handlers, under main's code. The branch's code then read
that same copy. `arxiv_v2` has no readable note. On probability:

| | Title on the hidden-notes row | `where` | Stored `learner_notes.title` |
|---|---|---|---|
| Main's code | `file:///home/saturn/.../joseph_blitzstein_jessica_hwang-introduction_to_probability.pdf` | the same URI › Naive definition of probability | the URI |
| Branch's code, same row | Joseph Blitzstein Jessica Hwang Introduction To Probability | that title › Naive definition of probability | the URI, row unchanged |
| Branch's code, new write | same | same | the readable title |

On both probability and linear_algebra, the rows were identical main and branch and unchanged by the branch's read, no note
read as changed against its stored row, and a new write's stored `content_hash` equals main's. So nothing is queued to be
re-judged or re-embedded. linear_algebra's titles are real titles and read the same on both sides.

**A capped decision** (`scripts/capped.py`). Seeded by the real pass with `max_daily_builds = 0`, a seeded measured wait so
the real model draws, a stubbed judge, and a stub author injected as the plan's client. Identical on all three copies:

| | main | branch |
|---|---|---|
| Seeded | 1 `capped` row, 1 draw | same |
| 3 passes, cap still 0 | 0 author calls, 0 draws, 0 rows | 0 author calls, 0 draws, 0 rows ("today's prebuilds are used up") |
| Cap raised to 5, next pass | **nothing built**, row still open | built on its original row: 1 author call, 0 new draws, 0 new decision rows |
| Row's id, verdict, propensity, `sampled_eu`, digest, `created_at` | unchanged | unchanged; `request_id` set, outcome still open |
| Figure | none | `illustrative`, origin `prefetch` |

**Audit.**
- `model_call_receipts`: 3 new, one on each branch `capped` copy, all provider `fake_figures` (the stub author, in
  process). 0 on any other compared database. No real model was called.
- No socket connect and no Codex start beyond the self-test's two refused ones. The only other process starts were
  `powerprofilesctl get` and the self-test's `true`.
- After each close, the only thread left is `learnloop-reading-sweep`, on both sides.
- Two Codex processes started at 19:54:50 during the smoke. Their parent chain is a sandboxed `launch.sh` under another
  parent, not the smoke, and the audit log records no such start. All other Codex processes on the machine started earlier.

**Runs outside `env -i`.** Every pytest, lint, generator and smoke run was isolated. These small commands were not:
stdlib `python3` scripts that patched source and test text in the worktree and read `full.xml` and the smoke's JSON,
`codex --version`, and `sqlite3` reads of the smoke's `cb` copies. They read no vault outside those copies and no
credentials, and made no model call.

### Rulings (orchestrator, verbatim)

- R1: "Other surfaces can show a source's file:// title (Compare's books, tutor citations, library text search, the source deletion dialog). Queued for the UX journey audit, fixed per surface at display. corpus._title is not changed, because that would alter scope_signature, prompts and keys and so re-judge on affected vaults."
- R2: "A legacy source note with no canonical URI keeps its relative path as a title; it isn't a URI and hasn't been seen on a vault. Left alone."
- R3: "A waiting decision with a goal, while show_me is off, spends one in-process reservation of today's builds before the build refuses it; no request goes out. Accepted."
- R4: "V1 and V2 are both Low and are fixed at landing with tests; they get no further Codex round."

R10 is recorded in section (A).

### Open items (landing)

* **Codex CLI 0.166.0:** classify `plugin_discovery_prefetch` and update the pins. Three tests fail on any tree until then,
  main included.
* **The `file://` surfaces, for the UX journey audit (R1):** Compare's books, tutor citations, the library's text search and
  the source deletion dialog.
* **A prebuild waiting on another request's rich job** adds one `figure_requests` row per pass while that job runs (V1 above).
  No spend. Worth a look only if a long plan wait makes the rows pile up.
