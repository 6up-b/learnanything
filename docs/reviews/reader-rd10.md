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
