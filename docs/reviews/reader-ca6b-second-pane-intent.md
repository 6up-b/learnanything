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
  | work through this, what matters here? | *(Codex re-review F7.)* **work through this**: that book comes to the main pane at the passage (a source detour from side by side's crumb), and the workbench opens there on the selection through the usual import. Side by side is one step back (Alt+← or the crumb). **what matters here?**: that book's reading path (the Guide's card, on its reading) in the pane. A section on it opens in the pane, and *try it* goes the way work through does. |

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

1. ~~No *work through this* and no *what matters here?* in the second pane.~~ **Superseded by the Codex re-review
   (F7):** both are in the second pane's palette, as in the main pane (§6.4 "Everything else works in both panes").
   The working posture is still the open book's, so *work through this* first takes the second pane's book to the
   main pane as a source detour, with side by side one step back. The fix round's `reader.route_intent` `sidePane`
   restriction is removed, so the Decider is offered the same actions in both panes. A routed action a box does not
   offer, such as work through with the workbench off, still runs Ask and is recorded as not used.
2. ~~The second pane's marks offer no *check me* and record no RW3b receipts.~~ **Superseded by the Codex fix round
   (F4-F6, F8, F9):** the pane runs the Reader's own cue controller on its book, so check me, discovery, impression
   receipts, taps with the visit, try-first's tap, placement on resize and Alt+↓ / Alt+↑ all work there. See
   `reader-ca6b-second-pane-intent-codex-review.md`. *(Re-review F8: check me first takes that book to the main pane
   at the mark, so the way back to side by side is kept, and the shell carries it across its practice and feedback
   screens.)*
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
- the palette leaving out work through and what matters here (since the re-review: the palette offering both, F7);
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
2. Owner check on deviations 3–5 (above). Deviations 1 and 2 were superseded in the Codex rounds: both actions and
   *check me* now work in the second pane.
3. RW6b part 2 (parallel in `learnanything-dl2`) also touches `ReaderScreen`. CA6b's ReaderScreen changes are
   confined to the side pane context, the router and the `SideBySidePane` props, so a merge conflict, if any, should
   be local to those hunks.

## Landing onto main

The branch `reader/ca6b-second-pane-intent` (worktree `learnanything-merge2`; the stage and fix rounds 1–6, round 6
at `ff3b06e953`) is merged with main `06f54da975`: curriculum C1 mvp-0.40 and Reader RW6b part 2, the digest card.
The orchestrator fast-forwards main and pushes.

### Sol verdict (verbatim)

The scoped Sol verify of round 6 (job `20261101-050244-su2sQH`) returned CLEAN:

> No findings. All three round-6 fixes are closed for app-produced flows. No false refusals or main-pane regressions found; side-by-side off remains inert.

### Merges, conflicts and regeneration

| commit | what |
|---|---|
| `7c433f99dd` | Merge of main `06f54da975`. **No textual conflicts.** RW6b part 2's recap/wrap-up files (`useReaderRecap.ts`, `RecapCard.tsx`, `WrapUpPanel.tsx`, `DigestNarrative.tsx`) and CA6b's `ReaderScreen.tsx`, `useSidePane.ts` and reader hooks merged cleanly. The merged tree typechecks with every CA6b type requirement in force (`SourceIdentity` on persisting requests, checks and handoffs; `ReaderRawSelection.extractionId`); none of RW6b part 2's new code builds a raw selection or a check. CA6b touches no config, so no template snapshot or fingerprint. Main's `pyproject.toml` change is import-linter contracts only (no dependency). |
| `4f7831bf92` | References and the desktop catalog regenerated on the merged tree. `db_generate_reference.py` (358 table notes; 478 notes restamped) and `db_validate_reference.py` (errors `[]`); `validate_vault.py` passes (1363 notes). `desktop_generate.py`: 295 TS/TSX + 5 Rust notes. The stage's `useSidePane.ts` (the stage's open item 1) is classified **entry-build**. `desktop_validate.py` counts moved to 295 TS / 287 entry-build / ACTIVE 300, and it passes byte for byte. |
| `87fae5b2ef` | `tests/test_ux_phase3_today.py` (UX Phase 3, from main): three of its tests opened workbench problems on readings that did not exist (`ext_other`, `ext_gone`, `ext_book_v1`, mapped to sources by a monkeypatch). The passage-identity guard refuses passages of a reading that does not exist (fail closed), so the tests now seed those readings with the passages their problems name. The tests' assertions are unchanged; on main the file passes as it was. |

`module_generate.py` / `module_validate.py` were not part of this landing. They report a long-stale Python module
catalog on main itself (1287 issues: missing package descriptions and notes for many existing packages). That is
pre-existing, and it is listed under open items.

### Gate (at `4f7831bf92`; the test fix `87fae5b2ef` was rerun alone)

- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest (`-n 6`, 5G, under `flock`): the CA6b guard tests (`test_reader_source_identity_guard.py`),
  `test_desktop_activation_audit.py`, `test_public_tip_guards.py`, RW6b part 2's tests (`test_reader_rw6b_p2_landing.py`,
  `test_reader_digest_narrative.py`, `test_router_reader_activity.py`, `test_reader_session_digests_migration.py`,
  `test_reader_rw6b_landing.py`), the round-5/6 fixture files (`test_reader_workbench_rw2a.py`,
  `test_figures_rpc.py`, `test_reading_paths.py`), and `test_desktop_rpc_contract.py`, `test_mobile_allowlist.py`,
  `test_architecture.py`: **570 passed**.
- Targeted vitest (`--maxWorkers=4`, 5G): the 122-file set plus RW6b part 2's `DigestNarrative.test.tsx`,
  `narrativeLanding.test.tsx` and the recap tests: **124 files, 1343 passed**.
- **Full pytest** (`flock /tmp/learnloop-fullsuite.lock`, 10G, `-n 8 --dist worksteal`, `env -i`): **23077 passed,
  7 failed, 89 skipped, 47 xfailed** (36:35).
  - **3 failures** were `test_ux_phase3_today.py`'s problems on non-existent readings (above). After `87fae5b2ef`
    the file passes: 5 passed.
  - **4 failures are pre-existing on main**: `test_route_rules_in_grader.py::test_f3_live_a_clarification_regrade_keeps_an_error_the_reply_reveals`,
    `::test_f4_the_graders_route_verdict_reaches_the_judgment_ledger_and_regrades_supersede_it`,
    `::test_f5_a_joint_regrade_supersedes_a_route_verdict` and
    `test_required_method_grading.py::test_a_regrade_at_the_successor_keeps_the_method_rule_and_a_full_credit_regrade_clears_it`.
    Each fails alone, 3 times out of 3, on this branch. They also fail identically on `git archive 06f54da975` (main's
    code and tests, the same interpreter): 4 failed, 67 passed with `test_ux_phase3_today.py` in the same run. They
    touch no CA6b file. Open item for the orchestrator.
- **Durability lane** (`-m durability`, 10G, under `flock`): **177 passed, 1 skipped**.
- **Owner lane** (`-m owner_vaults`, fresh backup-API copies of
  `learnanything-ad1/fixtures-local/owner-copies-mvp035/{linear_algebra,probability,arxiv_v2}` in
  `fixtures-local/landing-ca6b/`): **83 passed, 2 failed, 4 skipped**. The failures are exactly the two known ones,
  `test_activity_backfill::test_backfill_logs_attempt_duration_interaction_events` and
  `test_placement_fixture_copies::…[arxiv_v2]`.
- **Frontend:** `npm install` ok; `npm run typecheck` clean; the whole vitest (`--maxWorkers=4`, 5G): **245 files,
  2342 passed**; `npm run frontend:build` ok.
- Nothing under `src-tauri` differs from main, so no cargo check.

### Smoke on fresh owner copies (`fixtures-local/landing-ca6b-smoke/`, driver `scripts/smoke.sh`)

**Setup.** Fresh backup-API copies of the three mvp035 owner copies, neutralized under each side's own code
(`neutralize3.py`: every route at the `127.0.0.1:9` blackhole, key variable unset; rewrite, rerank, dense and
embeddings off). Main's code is `git archive 06f54da975` and the branch's `git archive 4f7831bf92`, both with
`src/` and `migrations/`. Each copy then ran:
- a bare `upgrade` (**mvp-0.35 → mvp-0.40**, head 228);
- the desktop start (primary load);
- `rebuild-derived-state`.

Every process ran under `env -i` with empty `HOME`, `CODEX_HOME` and config dir, and an audit hook that refuses
non-loopback sockets and Codex process starts. Counts only.

| | linear_algebra | probability | arxiv_v2 |
|---|---|---|---|
| upgrade, primary load, rebuild-derived-state (main and branch) | mvp-0.35 → mvp-0.40, ok | same | same |
| Today, branch vs main | identical (525,266 bytes) | identical (740,827) | identical (344,204) |
| daily plan dump, branch vs main | identical (84,702 bytes) | identical (124,027) | identical (32,439) |
| reader books with a ready render view / span ids shared by the two books driven | 3 / **160** | 2 / **10** | 4 / **125** |
| `reader.capture` with the passage's own SourceIdentity | ok (7 tables written) | same | same |
| … naming another reading's extraction id | `span_extraction_mismatch`, 0 tables changed | same | same |
| … naming another book's source | `span_extraction_mismatch`, 0 changed | same | same |
| … a colliding span id from another book through that book's render view | `span_extraction_mismatch`, 0 changed | same | same |
| … a colliding span id with the selection naming that book | `span_extraction_mismatch`, 0 changed | same | same |
| `reader.reanchor` / `reader.manual_anchor` to a reading of the same source | ok / ok | same | same |
| `reader.reanchor` / `reader.manual_anchor` to another source | `span_extraction_mismatch` / same, 0 changed | same | same |
| `rebuild --shadow` (branch copy; and after the guarded RPCs) | 0/0/0, live unchanged; 0/0/0 | same | same |

- **Model call receipts:** across the 15 smoke databases compared with their base copies, **0 new**.
  probability's 56 historical rows are unchanged in each copy.
- **Audit:** the audit log was never written, so there was no process start and no socket connect of any kind. No
  Codex process ran.
- **Colliding ids are real:** the copies' readings share span ids across books (160, 10 and 125 between the two books
  driven), which is the case round 6 closed.
- **Same-source reanchor:** no copy has two readings of one source with a ready render view, so the smoke moved
  annotations to the same reading. The move to an earlier or later reading of the same source is covered by
  `test_round6_reanchoring_moves_an_annotation_only_within_its_own_book`.

### Orchestrator rulings so far (verbatim from the review records)

- Round 4: "The orchestrator ruled that finding 1 and the earlier F1 are one class: something begun in the second
  pane is persisted or opened under the main book. So this round fixes the handler and also audits every action
  reachable from the second pane, or from an object that came from it (table below)."
- Round 5: "Wrong-book attribution had then produced Highs in four rounds. The orchestrator therefore directed a
  structural change, so that the class cannot happen rather than being patched case by case. It has four parts: (a)
  a fail-closed backend guard in one shared helper; (b) one client `SourceIdentity` type, required wherever a passage
  is persisted or handed on; (c) an honest UI state for the typed refusal; (d) active-reading state and drafts kept
  outside the conditionally mounted card."
- Round 6: "The direction was to tighten the guard. Span-id membership alone is not identity, because production
  extractors number every book's blocks the same way (`s0`, `s1`, …). So wherever the guard sees a render view, a node
  id, a crosswalk or a region, it must check that it belongs to the named reading. The other guarded RPCs were audited
  for the same weakness."
- Round 6 brief: "After this I land it, ruling any finding that needs a hand-crafted RPC beyond what the UI can
  produce as Low."

### Owner notes

- Cue discovery in the second pane shares the per-open judge-call budget: one open of the second book is one budget,
  as when that book is opened alone, and moving among its sections never adds to it. It runs only while RW3b's
  discovery is on.
- Returning from a check or a work through begun in the second pane lands on the mark's (or the selection's)
  passage in that book, with side by side one step back on the return stack: **Alt+←** reopens it, on the section the
  pane showed at the handoff.
- Every Reader write that names passages is now checked on the server against its reading. A refusal reads "That
  passage belongs to another reading; reopen it." and writes nothing.

### Open items

1. **Extraction-qualified span keys** for the reading-only RPCs, where the reading id is the only provenance on the
   wire: `workbench.open` (problem spans, source exercise), `reader.ask`, `set_answer_mode`, `route_intent`,
   `active_question`, both figure requests, `reader.library_ask` and `enqueue_request`. A mismatch there needs a
   hand-crafted RPC (Low by the round-6 ruling).
2. Not guarded, listed in round 5: the reads, and the non-Reader RPCs `curriculum.set_scope`,
   `import_source_exercise`, `compare_sources` and `ask_tutor_question`.
3. **Pre-existing on main:** the 4 grader tests above (`test_route_rules_in_grader.py` ×3,
   `test_required_method_grading.py` ×1) fail on main `06f54da975`'s own archive.
4. **Pre-existing on main:** the Python module catalog (`module_generate.py` / `module_validate.py`) is stale, with
   1287 issues. It belongs to the end-of-queue docs workflow.
5. The stage's open items 2 and 3 (owner check on deviations 3–5; the RW6b part 2 overlap) are settled: the
   overlap merged without conflict.
