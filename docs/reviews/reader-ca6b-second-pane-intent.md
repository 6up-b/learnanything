# Reader CA6b: the second pane's intent box and cue marks

Stage `reader-ca6b-second-pane-intent`, branch `reader/ca6b-second-pane-intent` (base `2b8b530279`), worktree
`learnanything-merge2`. Spec: `docs/specs/ux_reader_compare_ask_v1.md` §6.4 ("Everything else works in both panes"),
UX §4.1 (the intent box), §4.4 / RW3a–RW3b (margin cues and the attention budget), §13 (kill switch). This is the
remainder of CA6's Codex review F1 (`reader-ca6-side-by-side-codex-review.md`, open question 1; CA6 record open item 1).

Owner decisions in force (2026-10-12): the spec's recommended defaults; frictionless defaults (honest labels,
generous defaults, live changes behind kill switches). No migration, no successor, no config key, no backend change,
no model call, no paid or live call, no vault opened, no GUI launched.

## What ships

- **Per-pane intent routing (the pane context).** `ReaderScreen` now has one router, `runIntentIn(pane, action, text,
  how)`, and one cancel, `cancelIntentIn(pane, cancel)`. An `IntentPane` says what an intent acts on: the selection's
  passages and words, the pane's active reading, its fold, its figures, its region, and (`side`) the second pane's
  context. The main pane's context is built from exactly the values the old switch read (`selectionSpanIds`, the
  selection's words, `activeCtl`, `localFold`, `figuresCtl`, the selection's region), so every main-pane call is the
  same call with the same arguments. `runIntentRef` / `cancelIntentRunRef` (the main box) and the new
  `runSideIntentRef` / `cancelSideIntentRunRef` (the second pane's box) both go through it. The shared handlers take
  an optional target instead of being copied: `invokePreset(…, target?)`, `captureHighlight(…, target?)`,
  `importExercise(target?)`, `askLibraryHere(…, anchorExtractionId?)`, and `submitAsk(…, { anchor })`. Absent, each is
  the main pane's path, unchanged. One new helper, `captureIn(target, preset | highlight)`, is the second pane's
  capture. It is the same `reader.invoke_preset` / `reader.capture` call and does not touch the main pane's margin
  state.
- **The second pane's context** (`screens/reader/useSidePane.ts`, new) holds that pane's selection and its own
  `useIntentBox`, hosted in the pane's body, with routing on this pane's reading and passages. It also holds the
  capture target (this book's source, the revision from `reader.side_by_side_section`, the reading, the selection's
  nodes), a `useActiveReading` and a `useFigures` on this reading, the fold for "let me try the next step" over this
  section's next blocks, and the margin cues. While side by side is not shown it holds and reads nothing.
- **Selecting in the second pane shows the intent box exactly as in the main pane** (UX §4.1). It appears unfocused
  about 150 ms after mouse-up. The first printable key types into it. Enter routes (speculation as configured),
  and an empty Enter asks with no model call. Tab opens the palette, `?` focuses the box, and Esc closes it. The
  routed line has *change* (cancel or revert, then the palette). A held-out passage cannot occur here, because the
  section RPC refuses protected sections. With `reader_intent` off, CA6's one-line bar (highlight, note, CA3's verb)
  stays as it was. With it on, the box replaces the bar, since its palette carries the same verbs.
- **Each routed action in the second pane resolves against the second pane's source:**

  | Action (palette) | In the second pane |
  |---|---|
  | ask · ask me first · help me reason | `reader.ask` on its reading, passage and words. The answer lands in the Ask rail (side by side's overlay opens), labelled *about Axler · 7.A …*. Its follow-ups keep that book. |
  | empty Enter | The composer, anchored on its selection (*ASKING ABOUT YOUR SELECTION IN Axler · 7.A …*, with *ask about this book instead*). No model call. |
  | explain differently, worked example, research this, revisit once, help me remember, connect it, why this matters, confusing, not worth remembering | `reader.invoke_preset` with its source, revision and reading (`renderViewId` null, as CA6's capture). The pane re-reads its own marks. *change* reverts it. |
  | highlight, note | `reader.capture` on its book (the same call as CA6's bar) |
  | add this exercise to practice | `reader.import_exercise` on its book. The Notes import card shows its progress. |
  | why does this step work?, what does this assume?, let me try the next step, reconstruct this later, another way to see this | Active reading on its reading. The card shows in the pane, and the next-step fold covers this book's next lines in the pane. |
  | make this explorable / show me… | `reader.figure_request` / `figure.request` on its reading. The figure lands under its passage in the pane. |
  | where else is this explained?, where is this used?, what do I need first? | The library ask, anchored on its reading (in the comparing posture; side by side comes back when it closes) |
  | how do my other books treat this? | A comparison anchored on its selection, with `openSourceId` its book and `sourceIds` **the other pane's book** (§4.1) |
  | work through this, what matters here? | Not in the second pane's palette (absent, not disabled; U13). See deviation 1. |

- **Cue marks in the second pane (RW3a/RW3b).** The pane reads its own book's Guide plan (`readGuidePlan`, a local
  read through the Reader's cache) and takes only that reading's own cues. Those are already within the learner's
  density budget for that book, with RW3b's discovered marks merged when the plan carries discovery. The pane places
  them by the Reader's restraint rules (`placeCueMarks`: skim mutes, one mark per screenful of that pane), computed
  when the pane's text is laid out, never while scrolling. Each pane places its marks alone. The marks are static, in
  the pane's gutter, out of the text column (`MarginMark`, surface `text`). They are switchable from their popover:
  *not relevant*, *fewer marks like this*, *marks off for this book* and *marks off everywhere*, each with its
  receipt and *undo* in the pane's foot. The density is one vault-wide setting with a per-book off, so a change from
  either pane re-reads both plans (the side plan is re-read whenever the main plan's density or book-off changes).
  `cue_shown` is recorded once per mark per visit, with the pane's book as `target_source_id` /
  `target_extraction_id`.
- **Keys.** The box's rules apply in the pane that has the selection. Selecting in the second pane disarms the main
  pane's box (`onSelectedHere` → `noteIntentCleared`), and selecting in the main pane disarms the second pane's
  (`releaseKeys`). Nothing reaches either box while a text field has focus. Esc in the second pane closes its box
  first, and only then closes side by side. F6 still moves focus between the panes. CA5's `x` is off while either box
  shows.
- **Funnel events** for second-pane actions carry `target_source_id` / `target_extraction_id`, two fields that are
  already in `ACTIVITY_FIELDS`. No backend change.
- **Kill switch.** With `reader.side_by_side.enabled` off there is no second pane, so `useSidePane` is never shown.
  It holds nothing, reads nothing and registers no key. The Reader is exactly as before (test *switched off*, and
  CA6's own switch-off tests are unchanged and green).

## Main-pane parity

Every existing vitest file is unchanged and green (the 82 files below beside the new one). The main pane's router
arguments are built from the same values as before. `askLibraryHere`'s extra arguments default to the old ones, and
the shared handlers' new optional target is absent on the main path. The other two changes are inert for the main
pane: `useIntentBox`'s placement fallback now also matches `[data-sbs-span]`, which never occurs inside the main
pane's host, and `visiblePalette`'s new `hiddenKinds` is absent for the main box.

## Deviations and decisions (proposed defaults; owner may override)

1. **No *work through this* and no *what matters here?* in the second pane.** The working posture closes side by side
   (CA6 disables it while working), and the workbench works on the open book. The Guide's reading path is the open
   book's plan. *(Codex fix round, F7: the second pane's routings now ask `reader.route_intent` with `sidePane`,
   so the Decider is never offered either one; a routed action a box does not offer runs Ask and is recorded as not
   used.)*
2. ~~The second pane's marks offer no *check me* and record no RW3b receipts.~~ **Superseded by the Codex fix round
   (F4-F6, F8, F9):** the pane runs the Reader's own cue controller on its book, so check me, discovery, impression
   receipts, taps with the visit, try-first's tap, placement on resize and Alt+↓ / Alt+↑ all work there. See
   `reader-ca6b-second-pane-intent-codex-review.md`.
3. **An Ask from the second pane lands in the Ask rail,** labelled with that book. *show passage* is not shown for it,
   because its passage is beside the rail, not in the open book. Same-reading citations are not jump buttons there
   (another book's citation opens there, as RW1c's do). Its thread pushes no branch crumbs. The answer is stored in
   that book's Ask history: it shows in the rail this visit and is in that book's rail when that book is opened.
4. **An empty Enter in the second pane** opens the composer anchored on that pane's selection, the closest equivalent
   of the main pane's "the composer, on the selection". The anchor goes when the second pane's selection goes, when
   the learner selects in the main pane, or on *ask about this book instead*.
5. **Preset results** are that book's requests: they appear in its Notes when it is open. A commit preset's arc shows
   in the rail, as from the main pane.

## Tests (vitest, fail-first)

New: `src/screens/reader/sideBySideIntent.test.tsx`, 19 tests. Run against the base sources (the changed files
checked out at `2b8b530279`, the test file kept), **15 fail and 3 pass**. The 3 that pass are the guards that hold on
both: another reading's plan draws nothing, CA6's bar with the intent box off, and switch off. One test was added
later (skim and key ownership, below) and was not part of that run. The tests cover:

- the box in the second pane (in its text, unfocused, the only box);
- each routed action resolving to the second pane's source: ask with its label, empty Enter → the composer anchored
  there, preset, highlight, exercise import, where else, compare naming **the other pane's book**, active reading with
  the card in the pane and the next-step fold, another way, figure;
- the palette leaving out work through and what matters here;
- keys: `?` focuses the box, Esc closes the box before the pane, F6, a focused text field, and the first printable key;
- selecting in the main pane gives it the keys, with main-pane routing and CA6's compare naming the second book while
  side by side is open;
- skim: no marks, the box only on `?`, and key ownership in both directions;
- cue marks per pane beside the main pane's;
- density off: no marks;
- *marks off for this book* from the popover (`reader.set_cue_preferences` on the second book, marks gone, receipt);
- another reading's plan draws nothing;
- intent off keeps CA6's bar;
- switch off.

**Mutation checks** (each reverted):

| Mutation | Result |
|---|---|
| M1: drop `sourceIds: [render.sourceId]` from the second pane's compare | fails the compare test |
| M2: send the second pane's preset without its target | fails the preset test |
| M4: no `hiddenKinds` for the second pane | fails the palette test |
| M5: accept another reading's plan cues | fails that test |
| M6: drop `onSelectedHere` (a second-pane selection keeps the main box armed) | fails the skim key-ownership test |
| M3: drop `releaseKeys` on a main-pane selection | **survives** |

M3 survives because the release is defensive. The main box's key listener is registered before the second pane's in
every render and claims a key (`preventDefault`) first, so the main pane already wins when both are armed. The
release is kept so the second pane's box state never outlives a selection elsewhere.

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest and npm command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`), 12 files: **6019 passed**. No Python changed. These are the contract pins and the
  Reader/side-by-side backend files the frontend calls: `test_reader_ca6_side_by_side.py`, `test_reader_intent.py`,
  `test_reader_cues.py`, `test_reader_activity.py` (the `target_*` activity fields), `test_desktop_activation_audit.py`
  (new TS file), `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`, `test_architecture.py`,
  `test_public_tip_guards.py`, `test_salience_firewall.py`, `test_reader_rw3b_protection.py`,
  `test_tracked_fixture_databases.py`.
- No migration, no DB/connection code, no schema or config change: no durability run, no DB reference regeneration.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean. Vitest (`--maxWorkers=4`), 83 files:
  **675 passed**. The files: app/App.fixRound2, App.fixRound3, App.fixRound4, App.fixRound5, App.shell, App.today,
  App.wrapUpSkim, app/classicIsBase, app/keymap, app/shellChrome, screens/attentionBudget, and every
  `screens/ReaderScreen.*.test.tsx` (23 files: branches, checkOffer, cuesSwitchOff, discoveredCuesReview,
  discoveredCues, doseOffer, followsLearner, guide, inquiryOff, inquiry, k7, marginMarksReview, marginMarks, parity,
  pdfSelection, preparing, quickcheck, recapReview, recap, review, rw2cExample, workbench). Then screens/reader:
  alsoInBooksReader, checkOffer, compareKeepSwitchOff, compareKeep, compareScopeCodexReview, compareScope, cues,
  figures/libraryOfferSettle, figures/readerFigures, figures/showMe, figures/tutorOfferPress, figuresWithReadingPath,
  findSectionByPoint, findSectionReader, findSectionSideBySide, findSection, inquiryComponents, intentBoxInShell,
  IntentBox, intentSwitchOff, libraryAskSwitchOff, libraryAsk, libraryExercisesReader, libraryRoles, nextStepFold,
  paletteAskPostures, paletteAsk, ReaderAskBranches, readerHooks.parity, readerKeys, readingPathsReader,
  readingPathsRefresh, readingPathsSwitchOff, recapSwitchOff, returnStack, rw1bReview, rw3bReview,
  sideBySideCorrespondence, **sideBySideIntent (new, 19)**, sideBySideReader, splitRails, TutorAnswer, tutorBoundAsk,
  tutorExercises, tutorReader, tutorReview, tutorSwitchOff, useSideBySide, voices; and screens/workbench/switchOff.
  These are every test file that imports or renders `ReaderScreen`, `SideBySidePane`, `useIntentBox`,
  `intentPalette`, `AskRail`, `ReaderAskBranches` or `useReaderInquiry`, plus the cue, figure, keymap and side-by-side
  hook files. `npm run frontend:build`: ok.
- `src-tauri` unchanged: no cargo check needed.

## Commits

`48b6324521` (pane context, second pane's box, cues, figures, active reading), `d752e2cdb7` (vitest; the composer
anchored on the second pane), `debe6a26ea` (the skim/key-ownership test), and this record.

## Open items

1. **Desktop catalog at landing.** `useSidePane.ts` is a new entry-reachable TS file (and the changed modules' notes
   are stale), so `desktop_validate.py` reports drift until the landing regenerates the catalog with
   `desktop_generate.py` and moves its hard-coded counts (293 → 294 TS/TSX, 285 → 286 entry-build, ACTIVE 298 → 299,
   before C1 / RW6b part 2's own changes). This follows CA6's precedent: the catalog was regenerated in the landing,
   on the merged tree.
2. Owner check on deviations 1–5 (above), notably the two actions absent from the second pane's palette and *check
   me* not offered on its marks.
3. RW6b part 2 (parallel in `learnanything-dl2`) also touches `ReaderScreen`. CA6b's ReaderScreen changes are
   confined to the side pane context, the router and the `SideBySidePane` props, so a merge conflict, if any, should
   be local to those hunks.
