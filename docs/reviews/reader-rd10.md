# Reader workbench v2, RD10: video and carried polish

Stage RD10 of `docs/specs/spec_reader_workbench_v2.md` (§7.4's `alt+;`, §7.5, §7.9, §10.12, §16's RD10 row, §21.1's video
rows). Branch `reader/rd10-video-carried`, cut from RD9a's tip, with `origin/main`, `reader/visual-parity-fixes` (the
transcript on its paper sheet) and `reader/rd8a-pen-ui` (migration 267 and its fixture) merged in first. **Migration
268** (`video_chapters`); six new RPCs, all desktop only; one new structured prompt (the chapters
judge), registered with the identity pins; no algorithm tag, config key, kill switch, change to an existing prompt or
persisted meaning, and nothing on the phone.

## 1. What landed

| Scope item | Where |
|---|---|
| **Migration 268**: `video_chapters` (WORKFLOW): a chapter's reading, time range, title, LO tags, state (`suggested`, `accepted`, `dismissed`), the judge's ledger row; a decision made once and a decided chapter kept, by trigger. Classified in `table_roles`; the migration-head fixture upgraded in place from the tracked 267 copy by CLAUDE.md's procedure (its own commit, README section); the earlier migrations' upgrade diffs subtract its objects, as they do 267's | `migrations/268_reader_workbench_video_chapters.sql`, `tests/reader_rd10_migration_helpers.py`, `tests/test_reader_rd10_migration.py`, `fixtures/migration_head/` |
| **Follow-along** (§7.5), no hand maps: `reader.follow_along` gives the playing cue's transcript section (the video's section map of `t=` cues) with the bounds its answer holds for, the accepted chapter, and per LO the book's correspondent sections from judged coverage (`section_coverage.correspondents`, never the search fallback); no model call, no write | `src/learnloop/source_retrieval/follow_along.py`, `src/learnloop_sidecar/handlers/video.py` |
| The desk's side: a book window beside a video shows "following ▶ <chapter> <time> · <passage>" in its head ("… · no passage here" where none corresponds; "unlinked · u to follow ▶ <chapter>"), marks the passage in cyan, and scrolls to it while the video plays and the passage changed; the goal path's primary section is preferred among the correspondents. One ask per transcript section the video enters, per book window not paused. `u` unlinks or follows again (the focused book, else every book on the desk) | `F:screens/desks/video/desk.ts` (`VideoDesk`), `video/model.ts`, `video/FollowChip.tsx`, `video/followLens.ts`; `goal/GoalLayer.tsx` (`primaryFor`) |
| **Suggested chapters** (§7.9): `chapters.suggest` / `chapters.job` / `chapters.cancel`, a polled, cancellable, vault-scoped job on the coverage judge's listwise machinery, route, price, daily envelope, kill switch and protection guard (a protected section is never sent; a change while it runs keeps nothing; the same request is answered from the ledger with no call); stored `suggested`, a new run replacing only what is still suggested. `chapters.list`, `chapters.decide` (accept, not this; once) | `src/learnloop/source_retrieval/video_chapters.py`, `handlers/video.py` |
| The window's side: "◇ suggested chapters" under the player's line (range, title, ◇ LO tag, accept / not this; "suggest from the transcript" on the learner's ask; "judging…" with cancel); read once the window is live, the job polled through the app's poller under the window. Accepted chapters draw their ticks on the scrub track and their ranges on the shelf row's minimap | `F:screens/desks/video/ChaptersPanel.tsx`, `video/VideoWindow.tsx`; `reader/YouTubeWatchPanel.tsx` (`VideoExtras`: ticks, a side cell, the clock), `ReaderScreen.tsx`, `windows/SourceWindow.tsx` (pass-through), `Shelf.tsx` (`chapters` ranges) |
| **`alt+;`** (§7.4, §4.4's defect): "▶ <video> at m:ss" into the current desk's running pad (ensured if it has none) as a `source_quote` anchored to the cue span (`link_anchor`), from the focused video's clock, else the video this desk played last | `DeskShell.tsx` (`videoKeys.timestamp`) |
| **Carried questions resurfacing** (§10.12) beyond RD4's ◌ beside the passage a question was carried from: every page of the carried list is read (`carried.list`'s cursor), and a question also comes back beside its passage's judged correspondents in the other open readings (its section by the union read, `reader.correspondents` without search), the same quiet ◌, logged `surfaced` once as before | `F:screens/desks/carried/related.ts`, `DeskShell.tsx` |
| Keys: `u` and `alt+;` built (no longer marked RD10) | `keys/router.ts` |
| Styles in the reference's values (the `follow_*` and `chap_*` regions) | `F:styles/video.css` |
| Fixture, harness and reference: the fixture video's sections, follow-along and the chapters judge as the sidecar answers (`?video=1`: three chapters suggested, the second accepted); the harness's `video` run; the visual tool's `rd10` stage and a state's `reference` link | `F:fixtures/desks/video.ts`, `fakeCore.ts`; `scripts/desk_harness/run.py`, `visual_reference.py` |

## 2. Judgment calls (please confirm)

1. **The chapters judge reuses the coverage judge's route** (`ai.routing.section_coverage_judge`), price, daily envelope
   and kill switch (`curriculum.enabled`), so no config key is added. Its prompt is new (`video_chapters_judge.v1`): one
   listwise call, each transcript section "starts" or "continues" a chapter, a start with its title and LO refs from the
   listed LOs (`source_learning_objects`, titles only). The prompt, its schema and a chapter's id are pinned (new pins,
   nothing moved).
2. **Chapters are judged on the learner's ask** ("suggest from the transcript"), never on opening a video: a judgment
   is paid.
3. **Only accepted chapters tick the track** (the spec); the reference ticks its suggestions.
4. **The chip names the accepted chapter** the time falls in, else the transcript section's own label (a time range,
   as the extractor labels caption sections); the time shown is the time the section was asked for.
5. **Follow bounds run to the next section's start** (from the video's start for the first, open for the last), so a
   time between two sections' cues has its answer and the desk asks once per section. The desk also never asks twice
   for the same second.
6. **A paused video still drives the mark** (where it stands); only playing scrolls. A watch panel reports its clock
   only once the player has said a time.
7. **"not this" is logged by its decision** (`state = 'dismissed'`, `decided_at`); no separate ledger table.
8. **A learner-accepted chapter does not feed `section_coverage`** yet (§7.9 says it *can*, through
   `curriculum.coverage_correct`): left for the owner to decide.
9. **`u` is per book window and kept in memory** (not the window's stored view).
10. **The private capture tool's `--add-regions`** measured the new regions into the existing plain, `desk=1`,
    `#goal=video` captures, keeping their screenshots.

## 3. The reference compared (measured)

`visual_reference.py --stage rd10`, both viewports: `follow` (against the plain view) and `chapters` (against
`#goal=video`) show **no colour, token or geometry difference** in any compared region (the chip; the panel, its rows,
ranges, titles, accept button and an accepted chapter's tick). `chap_head` is measured on our side only (the
reference's is scrolled out of `#goal=video`; its plain-view values, 9.5 px uppercase `#8b8b9d` with 0.76 px spacing,
are set). The pixel shares (23–37 %) are the desks' different compositions (the reference's stack beside the video).
The reference's chip is a search hit's; ours names the judged correspondent.

## 4. Tests

- sidecar: `tests/test_reader_rd10_video.py` (7: registration desktop only and `extra="forbid"`, follow-along on a
  fixture with coverage and without, chapters judged once and stored, accept and not this once, a new run keeping
  decisions, a failed job keeping nothing, the curriculum off, assembly); `tests/test_reader_rd10_migration.py` (5).
  The related set (coverage, RD4/RD6a/RD8a/RD9a/RD10, CA5, the allowlist, RPC contract, identity pins, layout,
  public-tip guards, tracked fixtures, copies, table roles, activation audit): 1087 passed; the migration set: 148.
- vitest: `video/video.test.tsx` (10) and `video/deskVideo.test.tsx` (2: the chip and the scroll on the desks, `u`;
  `alt+;` into the running pad); the full suite 378 files, 4182 tests, no unhandled error. Fail-first: with the paused
  book's guard, the "only while playing" scroll guard and the chapters' wait for a live window removed, 3 of 10 tests
  fail; restored, all pass.
- Assertions changed: `keys/router.test.ts` (no chord waits on RD10; `u` and `alt+;` are built) and
  `DeskShell.test.tsx` (the which-key panel lists "insert ▶ timestamp" now).
- harness: the `video` run (14 checks); every run passes (144). `cargo check` ok; typecheck clean; `lint-imports` 52
  kept; ruff clean.

## 5. Not built here, and what waits

- Feeding an accepted chapter into `section_coverage` (§2.8). A chip naming a new accepted chapter inside an already
  answered section is updated at once; a chapter boundary inside one transcript section is not re-asked mid-section.
- The pad menu's own "insert ▶ timestamp" row (the key works; the menus worker owns the menu).

## 6. Bugs

None in existing code. While merging `reader/rd8a-pen-ui`, `visual_reference.py`'s `State` had two `query` fields
(from the two branches); one is kept, with the pen states' query in the shared form.

## 7. Not verified

- The desktop app itself (only the harness's real webview and jsdom); a live chapters judgment (fakes only); a real
  YouTube player (the harness's stub reports its time).
- The vault's generated notes are not regenerated (the validator's counts are updated; its coverage rows and the
  database reference wait for the regeneration after landing).

## Owner copies (the orchestrator, 2026-11-23)

Migration 268 was applied to backup-API copies of the owner's three vaults (the floor set, upgraded by
`learnloop upgrade`), in a gitignored directory, deleted afterwards. On every copy: the upgrade exited 0,
`integrity_check` is ok, `foreign_key_check` is empty, the migration head is 268, and `video_chapters` holds no rows.
No live vault was opened.

## Fix round: the RD10 adversarial review (Codex Astra, 2026-11-23)

Branch `reader/rd9-rd10-fix`, cut from RD6's fix round (its goal lens protection) with main merged in. The review had
1 blocker, 4 majors and 5 minors. Each was checked against the code here and held. Nine are fixed, each with a
fail-first test (shown failing before the fix) and a ledger row, RD10-1 upward. One is stopped: it needs a schema
change. No migration, algorithm tag, prompt or config key.

| Finding | Ledger | What changed | Fail-first test |
|---|---|---|---|
| Blocker: follow-along and the chip named a topic whose check is due (chapter title, section label, passage) | RD10-1 | The goal lens's one protection (`curriculum.goal_lens`: `protect_follow`, `protect_chapters`; the due-LO set through `handlers.goal_lens.protection_now`, shared with the goal lens) masks `reader.follow_along`, `chapters.list`, `chapters.decide` and a suggestion's result at every poll, with the same neutral words. A chapter is held when it is tagged with a held LO, its title names one, or it spans a transcript section that treats one. The replies carry `next_check_due`; the desk shows nothing of an answer past it (linked or unlinked) and asks again, and the chapters panel reads again then | `test_reader_rd10_fix_protection.py` (field tables over both functions; every string of the four replies walked end to end), `video/protection.test.tsx` (DOM text, titles and attributes; a stale answer) |
| Major: a suggestion cancelled after its request was sent still stored its chapters | RD10-2 | `store_suggestions(wanted=...)`: inside the write transaction, the job must be neither cancelled nor out of its epoch | `…::test_a_suggestion_cancelled_while_its_request_is_out_stores_nothing` |
| Major: the curriculum switched off while a suggestion ran did not stop it | RD10-3 | The judgment's guard takes `gate=SC.enabled`, read at every request and at the write | `…::test_the_curriculum_switched_off_while_a_suggestion_runs_stores_nothing` |
| Major: one last-playing video for every desk | RD10-4 | Each window's last play is a sequence number; the driver is the latest among the current desk's videos | `video/video.test.tsx` ("the driver per desk…") |
| Major: chapter decisions merged into a stale list; conflicts never reconciled | RD10-5 | Replies merge into what is shown now; a refused decision reads the stored chapters again; a stored decision makes every window on the video read them again (`VideoDesk.decided`) | `video/video.test.tsx` ("chapter decisions", 2) |
| Minor: a late follow answer applied whatever had changed | RD10-6 | Dropped unless its book is still on the desk, not paused, on that reading, and its video still drives | `video/video.test.tsx` ("a follow answer that comes back late…") |
| Minor: a question let go resurfaced after a failed refresh | RD10-7 | A successful closing mark removes the question from both lists, and no refresh this session brings it back (DeskShell) | `DeskShell.test.tsx` ("a question let go leaves the shelf at once…") |
| Minor: two placements of one carried question shared a key | RD10-8 | The key includes the passage (PassageMarks) | `pads/passageMarks.test.tsx` |
| Minor: a judged video could not replay from the ledger once the budget was spent | RD10-9 | A spent budget no longer refuses at admission; the daily envelope refuses the paid request itself | `…::test_a_judged_video_replays_from_the_ledger_with_the_budget_spent_and_an_unjudged_one_is_capped` |
| Minor: migration 268's replacement hole | RD10-10 | Guarded by test (the owner's option c): no code in `src/` or `migrations/` writes to `video_chapters` with `INSERT OR REPLACE`, `REPLACE INTO` or a replacing `ON CONFLICT`. The schema guard joins the next migration (SQL below) | `tests/test_video_chapters_no_replace.py` (shown failing with the writer switched to `OR REPLACE`) |

**The D15 sweep.** I checked where else a held LO's name can reach the workbench outside RD6's and this round's fixes.
Promoted rows and proposals are left to the menus round.

- **Lesson tabs and the path view's lesson row:** a finding, fixed here (RD10-11). `lesson.list` masks through `GL.protect_lessons`, and a held lesson's additions pad is not given its topic in its stored title.
- **Lesson bodies:** a finding for RD7's veils (RD10-12, owner). An open lesson's turns teach the LO.
- **Companion history and search's `threads` and `exchanges` groups:** a finding for the owner (RD10-13). They show past tutor answers.
- **Source titles:** a finding for the owner (RD10-14). They are masked nowhere: window heads, shelf rows, the path view's `book`, and the timestamp block. The timestamp block's label is the video's own title (`DeskShell`'s `titleOf(window)` → `timestampLine`), never follow-along or chapter text, so no follow or chapters reply reaches it.
- **Today's "Continue your lesson on X":** outside the workbench (RD10-15).
- **Carried questions' text:** checked safe. It is the learner's own words (`pads/carried.py` `carry(text=…)`, stored as typed). The related-passages view places marks only and renders no correspondent's title (`carried/related.ts` `beside()` copies the question with a new anchor).
- **Search's passage rows:** checked safe. They are the reading's own text, which the Reader shows anyway (veiling it is RD7's).

Assertions changed: none in the RD10 tests (the masking is inactive without a due check, so their replies are unchanged).

Shared files touched (small, additive):
- `DeskShell.tsx`: the closed carried set.
- `PassageMarks.tsx`: the key.
- `PadStackWindow.tsx`: the held lesson's pad title.
- `api/dto.ts`: `held` flags, `nextCheckDue`, chapter `learningObjectIds`.
- `handlers/goal_lens.py`: `protection_now`.
- `handlers/lesson.py`: masking `lesson.list`.

Checked:
- rd10 visual comparison: unchanged (no findings before or after).
- Desk harness, every run: 152 passed.
- The whole vitest suite passes.

**For the next migration's author (RD10-10).** Paste this trigger. It turns any insert that reuses a decided chapter's id
into a no-op, so `INSERT OR REPLACE` can no longer delete a decision. A legitimate `INSERT OR IGNORE` duplicate ends the
same way, and a suggested row is still replaced as before. I checked this against SQLite in memory: without the trigger
the replacement overwrote an accepted row; with it the accepted row stayed, and a suggested row was still replaced. Add
the trigger to the migration's added-objects set for the upgrade diffs, as 268's were.

```sql
-- A decided chapter is never replaced: an insert reusing its id is skipped (recursive triggers are off, so a
-- REPLACE's implicit delete would not fire video_chapters_keep_decided).
CREATE TRIGGER video_chapters_no_replace_decided
BEFORE INSERT ON video_chapters
WHEN EXISTS (SELECT 1 FROM video_chapters WHERE chapter_id = NEW.chapter_id AND state != 'suggested')
BEGIN
  SELECT RAISE(IGNORE);
END;
```

Once it lands, `tests/test_video_chapters_no_replace.py` can give way to a migration test that replaces a decided row
and finds it unchanged.

## Accepted chapters feed section coverage (branch `reader/chapters-feed-coverage`)

The owner decided on 2026-11-23: "yes, accepted video chapters feed section coverage". This closes judgment call 8 and
the open line in §5.

**What it does.** Accepting a judged chapter (`chapters.decide`, accept) writes coverage in the same transaction as
the decision (`section_coverage.chapter_accepted`, called from `video_chapters.decide`). Each tagged LO gets one row
per transcript section that lies wholly inside the chapter's time range and is readable and not withheld. Each row is
C0a's correction row, as `curriculum.coverage_correct` writes it:
- a `learner` row with `is_about`;
- a `learner_card` verdict in the judgment ledger.

Its provenance says where it came from:
- `origin` is `learner`, because it was the learner's act;
- `prompt_version` is `section_coverage_chapter_accepted.v1` and `state_key` is `chapter:<chapter id>`;
- the verdict's rationale names the source (`accepted_chapter`), the chapter, the chapter judge's ledger row and the
  range.

`origin`'s CHECK (`provenance`, `retrieval`, `learner`) holds this with no migration: the act is the learner's, and the
chapter is named by the version, the key and the verdict.

**The rules.**
- **Once per chapter.** A chapter is decided once. A second accept answers the stored decision, and any row already
  carrying the chapter's key stops the write.
- **"Not this" feeds nothing.**
- **The learner's own correction stands.** A section whose newest learner row for the LO is a correction (not about,
  also about) is left alone.
- **Decisions are final.** Un-acceptance does not exist. A wrong acceptance is corrected by the existing coverage
  correction: "not about this" on that section's line in the Guide's *also in your books*, which reaches the video's
  sections. That correction is newer, so it stands over the chapter's row (tested). The panel says this before the
  learner accepts (below).
- **A chapter's row describes the transcript as it was.** Once a section changes (its `section_hash` moves), the row
  stops standing (`standing()` skips it). A learner's own correction, by contrast, stands across changes, as before.
  The goal lens then reads the section as stale for that LO, so it is partial, never skippable.
- **Only whole sections.** A section the range covers in part is not covered (tested with a range starting halfway
  through the introduction).
- **The curriculum's switch applies.** With `curriculum.enabled` off, accepting writes no coverage, since coverage
  belongs to the curriculum. No new switch, no model call, no prompt change.

**The goal lens.** A standing row from a chapter with no judge treatment reads as `chapter` (`goal_lens.CHAPTER_ABOUT`,
beside the learner's `learner`):
- per LO it is *supporting* (`chapter_about`): "A chapter you accepted here is about “<LO>”, a topic of your goal.";
- the coverage line reads "coverage: is about (a chapter you accepted) “<LO>” · …".

It is never core, even where the path places the LO, because core needs a judged `introduces` or `develops`. Over a
judge's row the learner's acceptance keeps the judge's treatment when that treatment is about the LO, and stands over
a judge's "not about", as "also about" does. That raises the section's need and never lowers it.

**The costly error (review F6).** An accepted chapter must never make a needed section read as skippable. A section
becomes skippable only by the lens's existing rules over all of its coverage. The table test
(`test_reader_rd6a_goal_lens_core.py`) has eight rows with chapter-sourced coverage, covering these cases:
- mapped;
- never core where the path places it;
- partial while a goal topic is unchecked;
- beside a judge's "not about";
- an off-goal chapter beside a goal LO's primary, where core stays;
- an off-goal chapter while a goal topic is unchecked (partial);
- an off-goal chapter with every goal topic settled, which is skippable by the existing rule, exactly as an off-goal
  judge row is;
- the learner's own skip.

Further tests:
- **Stale:** after the transcript changed, the section is partial.
- **Held topic:** the lens's protection still masks a held LO from a chapter, with the held reason, no title and no
  coverage line.
- **Never-lowers property:** for every rule row and every LO a chapter could be tagged with, adding the chapter's row
  never lowers a needed level and never makes a mapped, non-skippable section skippable.
- **Integration:** over the video, accepting a chapter over the introduction (which the judge read as not about the
  goal) makes it supporting (`chapter_about`) and leaves every other section's level unchanged. Re-recording the
  introduction's words makes it partial.

**Persisted meaning: no tag.** Under `docs/algorithm-change-playbook.md`, a tag is needed "when scoring, scheduling,
projection, or admissibility semantics change". Section coverage steers the deliverable path and the goal lens, which
are display and retrieval context. It is "never evidence, never a prerequisite edge, never provenance": nothing in
scoring, scheduling, projection, grading or serving reads it (`section_coverage`'s module contract). AD's guard refuses
the table. `section_coverage` is WORKFLOW, never rebuilt by replay. No identity pin moved.

**The panel.** While any chapter is undecided, the chapters panel says, before the learner accepts and on the accept
button's title: "accepting counts this stretch as teaching its topic for your goal · it stays; if part of it isn't, mark
that part not about this".

**Tests.**
- `tests/test_chapters_feed_coverage.py`, seven tests:
  - accept writes once, with its provenance;
  - not this writes nothing;
  - whole sections only;
  - the learner's correction stands and corrects a wrong acceptance;
  - stale after a transcript change;
  - the curriculum switched off;
  - the lens over the video.
- The table rows and the property, as above.
- `video/video.test.tsx`: the panel's line, and its going once nothing is undecided.
- The harness's `video` run checks the line.
- Fail-first: each new test failed against `origin/main`'s sources.
- Green: the RD6, RD10, coverage, CA5, deliverable-path, identity-pin, notes-fence and architecture tests (712 passed);
  vitest on the video and goal folders; the harness's `video` and `goal` runs (38 passed); typecheck, ruff and the
  import contracts.

**Not done here.**
- The visual reference's `rd10` stage, design viewport: the one finding is the chapters panel's height (`chap_panel`,
  157 px against the reference's 127 px), which is the new line. The reference has no such line, because the mockup
  never fed coverage.
- No owner vault was opened.
