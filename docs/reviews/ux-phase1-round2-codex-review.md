# UX Phase 1, usability round 2: Codex review fixes

**Branch:** `ux/phase1-first-run` (worktree `learnanything-ux-impl`, not rebased onto main; the orchestrator merges). The review covered everything since `67ece2c7`: round 1's revision `037de53f` and round 2's `1de7f1f6`, `8cbd71da`, `70f163cd`, `e93d9730` and `ea39cf42` (`docs/reviews/ux-phase1.md`, "Usability round 1" and "Usability round 2 fixes").

**Codex job:** `~/.cache/codex-agent/jobs/20261013-110905-xg8wkg`.

**Findings:** one High (F1) and five Medium (F2–F6), plus six claims in `ux-phase1.md` that did not hold. Every finding was reproduced with a test that failed first. All six are fixed (`high_fixed`). F2 is fixed with the rollback switch, predecessor and successor selection tests, a rebuild comparison and a served-set diff. Its successor tag is not minted on this branch, for the reasons given under F2, and is put to the owner as Q-R. None is rejected.

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. No real provider and no network were used, and no app or server was started.

**Re-review** (below): F1 and F4–F6 confirmed fixed; F2, F3 and the new F7 and F8 fixed. F2's successor is now minted (`mvp-0.15`, a placeholder tag), which settles Q-R.

**Migration:** none. **Schema:** unchanged. `Repository.reader_section_progress_row` is a read. **Config:** one new leaf, `plan.reading_from_furthest = true` (F2). Every defaults snapshot was recomputed because of it, and the configuration reference was regenerated (684 → 685 leaves) and validates.

## Review

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Reading-progress updates reintroduce the sidecar stall | fixed | `39df628d` | `tests/test_ux_phase1_round2_review.py::test_f1_keeping_a_chapter_ahead_never_loads_the_books_text` (6 document loads → 0 on the five-unit test book), `::test_f1_keeping_a_chapter_ahead_reads_the_config_not_the_whole_vault`, `::test_f1_keeping_a_chapter_ahead_still_honours_the_switch_in_the_config`, `::test_f1_progress_within_a_section_already_reached_plans_nothing_again` (the real planner, wrapped: three reports → one call) |
| F2 | Medium | The reading-selection change silently changes serving under the existing algorithm version | fixed: the switch, tests, rebuild comparison and served-set diff. Successor tag open (Q-R). | `39df628d` | `::test_f2_the_switch_off_restores_dl1s_reading_selection_exactly` (×4 reading histories, against DL1's selection as shipped in `67ece2c7`), `::test_f2_the_successor_continues_from_the_furthest_section_and_skips_contents`, `::test_f2_todays_plan_follows_the_switch` (×2, through `set_plan_minutes`), `::test_f2_the_switch_is_on_by_default_and_documented`; the defaults-snapshot tests (`test_config_refactor.py`, `test_mvp01*_upgrade.py`, `test_recurrence_commands.py`) |
| F3 | Medium | Failed progress saves are acknowledged locally and never retried | fixed | `6e0756b2` | `src/screens/ReaderScreen.followsLearner.test.tsx` "F3: a progress save that failed is sent again when the learner leaves the Reader", "F3: … failed once is retried without leaving", "F3: … acknowledged is not sent again on leaving", "F3: leaving a book inside the Reader saves what was just read …" |
| F4 | Medium | Cold PDF resumes still lose the saved passage within its page | fixed | `6e0756b2` | `src/components/PdfReaderPane.scroll.test.tsx` (the real pane: "a resume asked for before the PDF is laid out ends centred on the passage, not the page top", "a passage asked for alone, before its page is drawn, is centred once it is", "the learner's own wheel drops a place still waiting for its page"); `ReaderScreen.followsLearner.test.tsx` R3 geometry now expects the passage request |
| F5 | Medium | Seeking a paused video is counted as watching | fixed | `6e0756b2` | `ReaderScreen.followsLearner.test.tsx` "F5: jumping a paused video to a short section is not watching it" (negative), "F5: playing on after a jump is watching" (positive); the round-2 "watching a video is reading" test still passes |
| F6 | Medium | Merely filing a source hides its missing-questions action | fixed | `39df628d` | `::test_f6_a_book_filed_in_a_collection_but_never_built_still_offers_its_questions`, `::test_f6_a_failed_study_map_build_leaves_the_offer`, `::test_f6_a_finished_build_whose_questions_were_never_applied_asks_for_a_look`, `::test_f6_a_finished_build_whose_questions_were_all_turned_down_offers_them_again`, `::test_f6_a_book_whose_study_map_questions_were_applied_stays_quiet`; round 2's `test_a_book_already_in_a_study_map_never_says_it_has_no_questions` encoded the defect and became `test_a_book_filed_in_a_collection_still_says_it_has_no_questions` |
| C1 | (claim) | "No scoring, scheduling or projection change, so no algorithm successor" | corrected (F2) | this commit | `ux-phase1.md` D13 and the round-2 line now say the reading step is a serving change to the plan's reading block, now behind its switch |
| C2 | (claim) | "Reading progress survives restart and is flushed when the Reader closes" | fixed (F3) | `6e0756b2` | True now: a count is settled only on the backend's acknowledgement |
| C3 | (claim) | "The passage is centered once its page is drawn" | fixed (F4) | `6e0756b2` | True now, verified on the real pane |
| C4 | (claim) | "A jump does not count as reading" | fixed (F5) | `6e0756b2` | True now for a paused video too |
| C5 | (claim) | "Books without a study map receive a missing-questions action" | fixed (F6) | `39df628d` | "Study map" now means a finished build whose questions were applied |
| C6 | (claim) | The library-polling optimisation left the outline on the progress path | fixed (F1) | `39df628d` | The progress path uses the same unit tree |

**Fail-first.** Every test above was run before its fix and failed, except five guards that passed both before and after: F1's switch test, F6's applied case, F3's "acknowledged" test, F4's wheel test and F5's "playing on" test. They pin behaviour the fixes must keep or newly add. The Python tests were written and run first, then the fix: 3 F1 failures (6 loads, a whole-vault parse, 3 planner calls), 8 F2 failures and 4 F6 failures (the applied case was already quiet). The frontend tests were also run with `ReaderScreen.tsx` at `ea39cf42` (stashed): 4 failed (three F3, one F5). The pane test was run against the pane at `ea39cf42`: 2 failed (`expected [ 'top:1200' ] to include 'center:s3'`, `expected 'center:page2' to be 'center:s2'`).

### F1: the progress path stays cheap

**Reproduced.** `advance_reading_build`, which every `spans_seen` report now reached, built the full outline. That is one load of the book's text, then one more per unit (`unit_inventory_marker`): 6 loads on the five-unit test book, and 631 on Codex's 630-unit book. It also parsed the whole vault (`load_vault`) for one switch. Three reports in one section ran the real planner three times.

**Fixed** (`add_source.py`, `handlers/reader.py`):
- The chapter list comes from `_unit_tree`, the same lightweight `source_document_units` read that round 2 gave the library card, in `advance_reading_build` and `_wanted_chapters`. Coverage is the existing receipt read. No document is loaded.
- `_keep_ahead_ready` reads `ingest.auto_build` from `learnloop.toml` (`load_config`), not the whole vault.
- **Coalesced.** `reader.mark_section_progress` asks to keep a chapter ahead only when a section is first reached (its stored `spans_seen` was 0), revealed or completed. Reading on inside a section asks nothing.
- **Off the RPC path.** The RPC queues the planning job and returns, as before. Choosing scope, costing, building and applying all run on the ingest worker.

### F2: the reading step's selection has its switch back to DL1's

**Reproduced.** With a reading history in Ch. 2 and Contents unread, DL1 (`67ece2c7`) serves Contents. The branch served Ch. 2, under the same `mvp-0.14`, with no switch that restored DL1's choice: `plan.reading_blocks` removes the block, and `plan.enabled` removes the plan.

**Fixed.**
- `plan.reading_from_furthest` (default `true`) is a sub-switch of `daily_plan_v1`. With it off, `next_reading_target` is DL1's selection exactly: the first unfinished section in book order, front matter included. The parity test compares it with DL1's code across four reading histories.
- The engine passes the switch. `spec_daily_loop_v1.md` §11 gains the row, and §10's `[plan]` list gains the key. `PlanConfig`, the template's snapshot notes and the configuration reference describe it. All six defaults snapshots were recomputed (`defaults_fingerprint_for_version`); they move only because the effective config gains the key.
- **Rebuild comparison.** On backup-API copies of both tracked fixtures (`fixtures-local/f2-rebuild-la`, `-prob`, migrated with `doctor --fix-state`), `learnloop rebuild --shadow --json --set plan.reading_from_furthest=true|false` gives identical semantic results. `learner_state_diff` is equal (linear algebra: facet 21 changed and 57 unchanged, mastery 6 and 15, schedule 47 and 52; probability: 2 and 0, 1 and 17, 1 and 76), and `live_database.unchanged` is true. Only freshly minted surrogate ids (`marker_id`, family and surface ids) differ. The baseline deltas themselves are the fixtures' pre-existing drift at `mvp-0.8` (the same with either value), not this change.
- **Served-set diff.**
  - Linear-algebra copy, three as-you-read extractions: on, the step is `u50` "Sums of Subspaces" (402 words left, where Axler's history leaves off); off, it is `u1` "Chapter 1 Vector Spaces" (195).
  - Probability copy: no as-you-read source, so there is no step either way.
  - Both tracked fixtures are at `mvp-0.8`, where the plan is dormant, so neither serves a reading block today.

*Superseded by the re-review (below): the reading step is now its own successor, `mvp-0.15` on this branch, a placeholder tag relabelled at the merge.*

**Not done here: a successor tag.** The playbook mints a tag when persisted meaning changes. This change writes no evidence, scoring, scheduling or projection. A plan already composed keeps its row, and replay never reads the switch (shown above). It does change what the plan serves, which `daily_plan_v1` treats as a successor-worthy kind of change. The tag is left open, as Q-R, for three reasons:
- The owner's 2026-10-12 decision is "live changes behind kill switches, no shadow stages by default". Main already records this pattern for mvp-0.16's pipeline: "a live change behind its own switches, not version-gated".
- Gating the fix by a tag would hold it from every existing vault until `learnloop upgrade`. The owner's vaults are the ones the usability rounds asked it for.
- This branch's chain ends at `mvp-0.14`, while main's runs to `mvp-0.17`. A tag here would be a placeholder, relabelled at the merge, with its upgrade function, fixture and snapshot. That is the merge's work.

### F3: a progress save counts only once it is saved

**Reproduced.** `send` advanced `reportedSeenRef` before the request and swallowed the rejection. The unmount flush then skipped that count as already reported. A count gathered in the last 1.5 s before going back to the Reader's own shelf was dropped unsent, because the reset cleared the timer.

**Fixed** (`ReaderScreen.tsx`):
- The acknowledged counts (`reportedSeenRef`) and the in-flight ones (`sendingSeenRef`) are kept apart. A count is acknowledged on success only. A failure releases the in-flight mark and schedules up to three timed retries (3 s, 6 s, 12 s), after which it waits for the next change or the next navigation.
- The unmount flush, and now also a book switch or the Reader's own way back to its shelf (`resetSourceState`), send whatever is neither acknowledged nor in flight.
- The maps and retry state are per book, so a late answer for the last book lands in that book's maps.
- Hydration merges the backend's counts into the acknowledged map with `max`.

### F4: the pane keeps the passage until it can centre it

**Reproduced** on the real `PdfReaderPane` (pdf.js, the document cache and the observers faked): `scrollToPage(3)` and then `scrollToSegment(3, "s3")` before the document loaded ended at `top:1200` with no centring. `scrollToSegment` alone, on a laid-out page that had not been drawn yet, centred the placeholder page and never the passage.

**Fixed** (`PdfReaderPane.tsx`):
- One pending target, `{page, offset, spanId}`, which the newest request replaces. A page offset applies once its page has a size. A passage is centred once its box exists, and its page is brought into view first (once), so the page is drawn.
- The poll starts when the document loads and gives up after 8 s.
- The learner's own wheel or touch drops a waiting target, so a late layout never pulls them back.
- The Reader's `revealSegment` asks for the passage alone.

### F5: only playing on is watching

**Reproduced.** With the video paused, a Contents jump to the short last section moved `currentTime` (the seek), the cue changed, `onPlaybackSpan` set `readingMoved`, and a quick check was written for the unwatched section.

**Fixed** (`ReaderScreen.tsx`, `YouTubeWatchPanel`):
- The panel tracks the player's state from `infoDelivery.playerState` and `onStateChange`.
- Every seek (a jump, the resume, a transcript click) opens a 1.5 s landing window.
- `onPlaybackSpan(spanId, advancing)` passes `advancing = false` for a seek's landing and the late reports around it, and whenever the player is known to be paused. The Reader then only moves its baseline cue.
- The Reader also ignores cue changes inside its own settling window after a jump.
- The quick-check trigger now checks that deadline too.
- A player that never reports its state still counts playback (round 2's R9 test).

### F6: a book's questions are counted from applied builds

**Reproduced.** Filing an imported book in a collection silenced "No questions for this book yet · Build them" with nothing built. A completed synthesis whose proposal had not been applied, or whose items were all turned down, also silenced it.

**Fixed** (`add_source.py`):
- `_study_map_questions` reads the receipts: a completed `synthesis_runs` row whose manifest names one of the book's extractions, joined to its proposal's items.
  - At least one item accepted and applied (`applied_change_batch_id`): `applied`, and the card stays quiet.
  - Items still pending: `pending`, and the card says "Questions for this book need a look · Review" (`open_changes`). This avoids a second build of a map that is waiting for review.
  - Anything else, including collection membership, a failed run or a rejected proposal: "No questions for this book yet · Build them".
- On the round-2 backup copy of the linear-algebra fixture, all three books have applied builds (176 applied items each), so they stay quiet.

## Gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts it back) |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8767 passed**, 0 failed, 0 skipped (5 min 50 s). That is 8750 before plus this round's 17 new tests. It ran on the code of `6e0756b2`; the tests' only later change is an unused import removed from the new file, and that file was rerun alone: 17 passed. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8673 deselected (serial, 1 min 33 s) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date · clean · **52 files, 327 tests passed** · built. Two earlier full runs, made while other stages' suites loaded the machine (load average about 32), each failed timing tests in a file this round does not touch: three in `PracticeScreen.test.tsx`, then one in `FeedbackScreen.test.tsx`. Each file passed alone (20/20 and 11/11), and the final full run above was clean. |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | `db_generate_reference.py` regenerated at `6e0756b2` (schema head 186 unchanged, 300 table notes, 685 configuration leaves); `db_validate_reference.py`: no errors; `validate_vault.py`: passed (1073 notes) |
| F2 rebuild comparison | `learnloop rebuild --shadow --json --set plan.reading_from_furthest=true\|false` on backup-API copies of both tracked fixtures: identical `learner_state_diff`, `live_database.unchanged` true (see F2) |

## Safety

- No paid call, no real provider and no network. No key or credential file was read.
- The owner's working vaults in the main checkout were never opened.
- The worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` were only copied with the backup API (`copy_tree_with_databases`) into the gitignored `fixtures-local/f2-rebuild-la` and `fixtures-local/f2-rebuild-prob`. Doctor and the shadow rebuilds ran on those copies. Round 2's `fixtures-local/la-round2` was read with a read-only connection. `git status fixtures/` is clean.
- No server was started.

## Open questions for the owner

- **Q-R.** *Settled by the re-review (F2): spec_daily_loop_v1 L6 makes every serving change a successor with a kill switch, so the reading step is `mvp-0.15` on this branch, a placeholder the merge relabels after main's `mvp-0.17`.* The question was: should `plan.reading_from_furthest` mint a successor tag when this branch merges, or stay a live sub-switch of `daily_plan_v1` under the 2026-10-12 "live changes behind kill switches" decision?
- **Q-S.** A finished study-map build still waiting for a look says "Questions for this book need a look · Review" (F6). Is that right for a book added through Ingest, or should it stay quiet until the proposal is decided?

## Re-review

**Codex job:** `~/.cache/codex-agent/jobs/20261013-120459-fzJknO`. **Verdict:** REOPENED. F1, F4, F5 and F6 are confirmed fixed. F2 and F3 were reopened, and there are two new Medium findings (F7, F8). No High finding was raised.

**Outcome:** all four open findings are fixed, and none is rejected. Each one was reproduced first, by a test that failed before its fix. The commits are `99608c51` (F7, which also closes F3), `8442299c` (F8) and `004d9ba0` (F2).

**Paid calls:** none ($0.00). Every model call in the tests is a house fake. The manual checks ran on backup-API copies with `LEARNLOOP_CONFIG_DIR` set to an empty scratch directory, so no key was loaded and no provider was reachable. No app or server was started.

**Migration:** none. **Schema:** unchanged. **Algorithm version:** a new successor, `mvp-0.15` (F2). It is a placeholder tag: main's chain already runs to `mvp-0.17`, so the merge relabels it to the next free tag, along with `reading_step_upgrade.upgrade_to_mvp015` and its defaults snapshot. **Config:** no new key. The six earlier defaults snapshots are unchanged, and the `mvp-0.15` snapshot is recorded.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Reading-progress updates reintroduce the sidecar stall | confirmed fixed by the re-review | `39df628d` | — (its coalescing caused F8) |
| F2 | Medium | The reading-selection change changes serving under the existing algorithm version (reopened: successor deferred) | fixed: the reading step is its own successor, `mvp-0.15` (placeholder tag), behind `plan.reading_from_furthest` | `004d9ba0` | `tests/test_ux_phase1_round2_rereview.py::test_f2_the_plans_own_version_serves_dl1s_reading_step_whatever_the_switch` (×2), `::test_f2_the_successor_serves_the_reading_step_behind_its_kill_switch` (×2); `tests/test_reading_step_upgrade.py` (10: vocabulary, the version gate, the upgrade from `mvp-0.14` and through the chain, refusals, idempotence, CLI default, new vaults, the defaults fingerprint, the head-fixture path); shadow rebuild and served-set diff on fixture copies with the plan live (below) |
| F3 | Medium | Failed progress saves are acknowledged locally and never retried (reopened by F7) | fixed with F7 | `99608c51` | round 2's four F3 tests plus F7's two |
| F4 | Medium | Cold PDF resumes lose the saved passage | confirmed fixed by the re-review | `6e0756b2` | — |
| F5 | Medium | Seeking a paused video is counted as watching | confirmed fixed by the re-review | `6e0756b2` | — |
| F6 | Medium | Filing a source hides its missing-questions action | confirmed fixed by the re-review | `39df628d` | — |
| F7 | Medium | A pending retry loses newer progress after leaving the book | fixed | `99608c51` | `src/screens/ReaderScreen.followsLearner.test.tsx` "F7: a retry still waiting when the learner leaves the book saves the newest count, not the one that failed first", "F7: the newest count of a book left behind is still sent when the Reader closes" |
| F8 | Medium | First-reach coalescing prevents recovery from a failed build enqueue | fixed | `8442299c` | `tests/test_ux_phase1_round2_rereview.py::test_f8_a_keep_ahead_that_failed_is_asked_again_by_the_next_report`, `::test_f8_a_keep_ahead_that_failed_is_kept_for_the_next_start`, `::test_f8_a_keep_ahead_that_failed_is_retried_off_the_rpc_path` (the real background worker), `::test_f8_the_worker_retries_a_bounded_number_of_times_then_the_next_report_asks_again`, `::test_f8_the_newest_position_wins_a_pending_retry` |

**Fail-first.**
- **F7.** Both tests failed against `f7cda9c0`. The first reproduced Codex's trace exactly: the failed saves of 1 and 2 were followed by a successful save of 1 (`expected 1 to be 2`). The second ended with `expected [] to deeply equal [ 2 ]`.
- **F8.** All five tests failed before the fix:
  - `assert ['u3'] == ['u3', 'u3']`: no second ask.
  - `(None, None)`: no pending position was recorded.
  - The background worker never retried.
  - Two failed on the retry API, which did not exist yet.
- **F2.** Three tests failed before the fix. An `mvp-0.14` vault with the switch on served `2-matrices` where DL1 serves `contents`, and the successor's two cases could not import the tag. The `mvp-0.14`, switch-off case passed both before and after, as a guard. `tests/test_reading_step_upgrade.py` failed at import (no tag, no upgrade).

### F7: a book's saves outlive leaving it

**Reproduced** (`ReaderScreen.tsx` at `f7cda9c0`):
- Each save's retry closure captured that save's own counts.
- Leaving through the Reader's shelf cleared the current sender (`flushSeenRef`) after its flush had failed.
- The earlier retry then resent its stale count: 1 instead of 2. Nothing was left to send the 2.

**Fixed** (`ReaderScreen.tsx`):
- Each book (extraction) has one `SeenSave` entry in a map that lives as long as the Reader. The entry holds:
  - the newest count per section, with its span count;
  - the acknowledged counts and the in-flight ones;
  - the book's own retry attempts and timer.
- The gathering effect writes the newest counts into the entry at once. Every send reads the entry (`sendSeenCounts`), including the timed retries (3, 6 and 12 s) and the flush when the learner leaves the book. So a retry always sends the book's newest counts.
- Leaving a book flushes it and keeps its entry. The retry carries on until the backend acknowledges the counts or the retries run out. After that, the next change or reopening sends them.
- Closing the Reader sends every book's unsent counts.
- Hydration merges the backend's counts into the book's acknowledged map.

### F8: a failed keep-ahead ask is kept and retried

**Reproduced.**
- Round 2 coalesced "keep one chapter ahead" on saved progress: only a section's first report asked, judged by its stored `spans_seen`.
- The handler saves progress before it asks. So when that ask raised (a busy database, a config mid-edit), every later report in the section looked "already reached".
- Nothing retried the ask. Three reports made one failed attempt, and no planning job was ever queued.

**Fixed:**
- `add_source.keep_ahead_for_reader` (`add_source.py`) wraps `advance_reading_build`. When an ask fails it:
  - records the book's pending reading position durably (`set_source_wanted_reading`). The next start, a finished build and reconnecting an AI act on it (`reconcile_reading_builds`);
  - hands the ask to the ingest worker (`DurableIngestJobs.defer_reading_advance`).

  A successful ask settles it: the build is queued, or durably deferred while the book's work runs.
- **Coalesced on a settled ask, not on saved progress** (`handlers/reader.py`). A report asks when its section is first reached, revealed or completed, as before. It also asks while an earlier ask for the book is unsettled, and then the newest position wins.
- **Retried off the RPC path** (`jobs.py`):
  - The worker loop retries due asks after 2, 10 and 30 s (`READING_RETRY_DELAYS`), and keeps polling until they settle or run out.
  - A newer ask replaces an older one and resets its attempts.
  - Once the retries run out, the ask waits for the Reader's next report.
- `advance_reading_build` now clears a pending position only after its build is queued. Before, it cleared the position first, so a failed enqueue also lost a position deferred earlier. `reconcile_reading_builds` now keeps a failing book's position and carries on with the other books.

### F2: the reading step is its own successor

**Reproduced.** At `mvp-0.14`, with the switch at its default (on), Today served Ch. 2 where DL1 serves Contents. The vault had a reading history in Ch. 2 and an unread Contents. The kill switch existed, but the change shipped under `daily_plan_v1`'s own tag.

**Why fixed, not rejected.** spec_daily_loop_v1 L6 says: "Each change to what is served is an algorithm successor with a kill switch that restores the previous behaviour exactly." The owner's 2026-10-12 "live changes behind kill switches, no shadow stages" does not conflict with that. Every successor on main ships live, with its switch: DL1, probe ties, learner-text gaps and the route check. Main also leaves only the non-serving parts of a change ungated by version, as with mvp-0.16's pipeline.

Round 2 deferred the tag because a tag on this branch would be a placeholder. That is how main's last three successors were built, though: as placeholders relabelled at their merge (`mvp-0.17` was "built as mvp-0.15 (a placeholder)"). Round 2 also worried that gating would hold the change from the owner's vaults. Both tracked fixtures are at `mvp-0.8`, where even the plan is dormant, so they need `learnloop upgrade` either way, and the default target now includes the reading step.

**Fixed** (`004d9ba0`):
- `READING_FROM_FURTHEST_ALGORITHM_VERSION = "mvp-0.15"` is appended to `SUCCESSOR_CHAIN`, so `LATEST_ALGORITHM_VERSION` and new vaults follow. `READING_FROM_FURTHEST_VERSIONS` is the gate.
- `daily_plan.engine.reading_from_furthest_active(vault)` needs three things: the plan is active, the vault is at the successor or later, and `plan.reading_from_furthest` is on. Below the successor, the reading block is mvp-0.14's (DL1's) whatever the switch says.
- `learnloop upgrade --to mvp-0.15` is the new default target. It accepts `mvp-0.14`, or `mvp-0.9` to `mvp-0.13` through `upgrade_to_mvp014`, under T1's guard. The upgrade freezes the parameter manifest, rebuilds the same projection namespace before the atomic config rename, and rewrites nothing.
- The `mvp-0.15` defaults snapshot is recorded. The earlier six are unchanged, because no key was added.
- Updated to match: the CLI help snapshot, the version-vocabulary tests (`test_mvp011/013/014_upgrade.py`, `test_recurrence_commands.py`), §10 and §11 of `spec_daily_loop_v1.md` (successor `reading_from_furthest_v1`), D13 in `ux-phase1.md`, the configuration reference and Q-R above.
- The migration-head fixture (`migration_head_186`, algorithm `mvp-0.6`) needs no regeneration: there is no migration. `test_reading_step_upgrade.py::test_head_fixture_predecessor_to_successor_path` runs the playbook's item 8 on a copy: upgrade, FK check, doctor and an idempotent rebuild.

**Checks on fixture copies with the plan live.** The re-review noted that round 2 compared fixtures where the plan was dormant.
- **Setup.** Fresh backup-API copies were made of both tracked fixtures: `fixtures-local/rr-f2-la-014` and `fixtures-local/rr-f2-prob-014`. Each was migrated (`doctor --fix-state`) and upgraded `mvp-0.8 → mvp-0.9 → mvp-0.14`, so the plan is live. Each was then twinned with the backup API (`-015`) and the twin upgraded to `mvp-0.15` with the CLI's default target.
- **Shadow rebuild.** `learnloop rebuild --shadow --json` was run on all four copies. `live_database.unchanged` is true on each, and every attempt is accounted for (70 linear algebra, 2 probability). Each twin's `learner_state_diff` equals its `mvp-0.14` sibling's, apart from the version stamp. The counts are linear algebra facet 2, mastery 21, schedule 48, and probability 2, 18, 1. These are the fixtures' existing drift and are identical at both versions.
- **Projection.** A direct comparison of every `DERIVED` table between the twins shows zero differences: 17 tables, with 1595 rows (linear algebra) and 539 rows (probability). Version stamps, surrogate ids and timestamps were ignored.
- **Served-set diff.** Today's plan was composed with one pinned clock: `get_daily_plan`, then `set_plan_minutes` 60 on linear algebra.
  - The plans are identical at both versions. On these copies the review load keeps the new lane closed, so neither version serves a reading block today.
  - The section the block would serve differs. On the linear-algebra copy, with three as-you-read extractions, `mvp-0.15` gives `u50` "Sums of Subspaces" (402 words left) and `mvp-0.14` gives `u1` "Chapter 1 Vector Spaces" (195).
  - The probability copy has no as-you-read source, so there is no reading block at either version.
  - The served difference itself is exercised end to end through `set_plan_minutes` by the F2 tests above.

### Re-review gate

Run in the worktree with `TMPDIR=<worktree>/fixtures-local/tmp`, at `004d9ba0`.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` · `uv pip install pypdfium2` | ok (the sync removes pypdfium2; the install puts it back) |
| `uv run lint-imports --no-cache` | 14 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8792 passed**, 0 failed, 0 skipped (4 min 42 s; 8792 collected). This round adds 19 tests, 9 in `test_ux_phase1_round2_rereview.py` and 10 in `test_reading_step_upgrade.py`. Seven tests parametrized over the version chain also gain an `mvp-0.15` case. |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **94 passed**, 8698 deselected (serial, 1 min 29 s) |
| `npm install` · `npm run typecheck` · `npm test` · `npm run frontend:build` | up to date · clean · **52 files, 329 tests passed** (327 + F7's 2) · built |
| `cargo check` | not run: nothing under `src-tauri` changed |
| DB reference scripts | `db_generate_reference.py` regenerated at `004d9ba0`: schema head 186 unchanged, 300 table notes, 685 configuration leaves; `plan.reading_from_furthest` now reads as the successor's kill switch. `db_validate_reference.py`: no errors. `validate_vault.py`: passed (1073 notes) |

### Re-review safety

- No paid call, no real provider and no network. No key or credential file was read. The CLI and the scripts ran with `LEARNLOOP_CONFIG_DIR` set to an empty scratch directory.
- The owner's working vaults in the main checkout were never opened.
- The worktree's tracked `fixtures/linear_algebra` and `fixtures/probability` were only copied with the backup API (`copy_tree_with_databases`) into the gitignored `fixtures-local/rr-f2-{la,prob}-014`. The `-015` twins are backup-API copies of those copies. Doctor, the upgrades, the shadow rebuilds and the plan composition all ran on the copies. `git status fixtures/` is clean.
- No server was started.

### Re-review open questions

- **Q-S** (unchanged) is still open.
- **Q-T.** At the merge, `mvp-0.15` (the reading step) is relabelled after main's `mvp-0.17`, as `mvp-0.18` if nothing else lands first. The relabel covers the tag, `reading_step_upgrade.upgrade_to_mvp015`, the `--to` choice, the defaults snapshot, the version-vocabulary tests and the spec's §11 row. Nothing for the owner to decide unless they prefer the reading step to stay unversioned. If so, `plan.reading_from_furthest` already restores DL1's selection exactly.
