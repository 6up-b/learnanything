# Reader workbench v2: batch 2 integration (2026-11-23)

One landing branch, `land/workbench-batch-2`, cut from batch 1's gated tip `ee2d8dfc7d`, with the next finished
branches merged in, the wiring the other workers left for the integration, the fixes the merges needed, and the
proof. No new feature beyond that wiring.

## 1. What was merged, in order (one merge commit each)

| # | Branch (tip merged) | Merge | Conflicts and how they were resolved |
|---|---|---|---|
| 1 | `notebook/frame-b4-b5` (`a946f886f2`: the frame and paper theme B4, cells in pads B6, a lesson notebook B7; with `reader/rd9a-lesson-windows` `f3635b9b50`) | `70fda0ec00` | `client.ts`, `dto.ts`: one copy of the notebook runtime's calls and types, the notebook side's (it gains `cellRuns`, `padCells`, `lesson` and an optional `path`). `fakeCore.ts`: both imports, the ink pad and the lesson stack pushes, both pad lists. `fixtures/desks/pads.ts`: the ink pad and the cells pad. `PadStackWindow.tsx`: both imports (ink, cells), both block cases (`ink`, `cell`, each with its `break`), an editor skipping sketch, ink and cell blocks. `pads/host.ts`: both imports. DeskShell: the lesson props and transport beside the menu, goal and pen ones; the pads host's `lessons` with the menu's dependencies; a lesson in a slot is a stack of one (RD9a) and the stack keeps the title-bar ⓘ; the pen host provider around the notebook bridge provider. The generator's areas: pen, menu, notebook, lesson (one pads line). `desktop_validate.py`: recomputed (409 files, 390 entry-reachable, 15 vitest-support, ACTIVE 415). Ledger: this branch's rows, then the notebook frame's NBF-1..4. Harness runners and visual stages: the union (rd5, rd8, rd9, notebook). Allowlist: one copy of each pin, RD9A added |
| 2 | `refactor/k10.11-figure-records` (`b1a651a920`) | `1570b3dd7b` | None |
| 3 | `reader/visual-parity-fixes` (`f4e48c24a8`, VR-46) | `4b676ed67f` | None |
| 3b | `reader/visual-parity-fixes` (`9b64fe7c01`, the record's reproducible counts) | `6d0e43d11e` | Ledger: VR-46 and VR-47 after VR-45, the integration's sections after them |
| 4 | `reader/rd10-video-carried` (`c1160f308c`: migration 268, follow-along, suggested chapters, alt+;, carried questions resurfacing) | `d72ddc5638` | `dto.ts`, `fakeCore.ts`: this branch's (RD10 holds neither the notebook types nor the lesson push in the same place). `ReaderScreen.tsx`, `SourceWindow.tsx`: RD10's (its `video` extras beside `lens` and `onPenSurface`). DeskShell: the video transport after the lessons'; the `follow` and `timestamp` key actions beside `path` and `pen`; the pads host with the menu's dependencies; the notebook bridge provider kept; the pane head keeps the pad stack's ⓘ and "yours" and gains RD10's follow chip on a source. Generator: both area sets (menu, notebook, video, carried). `desktop_validate.py`: 417 files, 397 entry-reachable, 16 vitest-support, ACTIVE 423. Ledger: RD8a-1 stays in its own section. Harness runners: `menus` and `video`. Visual tool: one `query` field (with its "?") and RD10's `reference` field; stages rd1-rd6, rd8, rd9, rd10, notebook; one copy of the rd9 state. Allowlist: RD10's pins with the others |
| 5 | `refactor/k2.4c-b-split-appends` (`b20394c179`: oversized appends in checkpointed passes, K2-20; on top of K10.11) | `7fc92a16ce` | None |

After every merge `git grep -n -E '^(<<<<<<< |>>>>>>> )'` was empty before the commit; the clean merges committed
themselves and the check was run after them. The status file merged cleanly each time. No ledger row was lost.

`tests/goldens/structure.toml`: K10 raised `golden_json_lines` (295,944 → 296,669) and the notebook branch kept it;
the merge took K10's value, and `test_structure_ratchets` passes on the merged tree with it and with
`modules_in_an_import_cycle` at 219.

### 1.1 Batch 1 again (`land/workbench-batch-1` at `efe02a5fab`)

Merged last (`5976d79836`) for its notebook guard fix: the runtime's four `notebooks.*` resource limits classified
in the parameter registry, and `notebook_runtime/proxy.py` and `supervisor.py` added to the audited HTTP modules.
One conflict, `tests/test_notebook_runtime.py`: both new test groups kept (the pad cells' session tests from B6 and
the runtime's loopback-only HTTP test from the fix). Batch 2 adds no further unclassified leaf or unaudited module:
before this merge the guards failed on exactly batch 1's ten (the four `notebooks.*` leaves and the two modules),
nothing from RD10, the notebook steps or K10.

## 2. Wiring left for the integration

- **The pad menu's marimo row is live** (B6's follow-up): in the one menu, `{ ...MARIMO_CELL_ROW, run: … onInsert(MARIMO_CELL_INSERT) }`
  from `notebook/menuBridge`; it inserts an empty learner cell below the line (or at a frame pad's end).
- **A notebook frame's right-click opens the pad menu** (B6/B7's follow-up): DeskShell registers
  `setNotebookMenuOpener` once (cleared on unmount). It finds the stack window on the desk that shows the request's pad
  or lesson (a stack entry, a lesson in a slot, or an opening in flight), focuses it first (a press inside a frame
  never reaches the desks, and the pad menu belongs to the active window: without the focus it closed at once; found
  writing the test), then opens the menu at the frame's point through the stack's new `openFrameMenu`. The header is
  the request's label ("the lesson", "your pad") over the frame's selection, quoted as text (never markup); the
  insert heading is the request's ("add under this lesson (the notebook stays as the teacher made it)"). A lesson's
  inserts go through `writeUnderLesson` to its additions pad, never into the notebook; a pad's land at its end; a
  lesson's menu has no "mute suggestions on this pad".
- **The menu's Teach me opens a lesson tab** through RD9a's `openLesson` (an opening in the desk's stack while its
  first turn runs), with the passage as `reader_selection` (or the words as `new_topic`). The interim `lesson` pane
  case and the menu's own `lesson.turn` call are gone: one path.
- **The goal path view's Teacher lesson row** was already wired by RD9a through `useGoalDesk`'s `lessonRow`; it
  merged as is.
- **Key scopes**: `notebook, check, menu, typing, arrange, strip, pen, overview, focus, reading`. A notebook frame
  owns the keys while it has the focus (they never reach the desks; its bridge sends `c`, escape and `menu`); the
  lesson window's inputs are typing targets; the context menu and the lesson's menus claim `menu`. RD10's `alt+;` and
  follow keys resolve in the reading scope.

Changed assertions (the feature changed, not loosened): `PadStackWindow.test.tsx` and the harness's `#s11=menu`
check expect the marimo row live, where they expected "arrives with notebooks"; `verbs.test.ts` and
`DeskShell.menu.test.tsx` expect Teach me to open a lesson opening in the stack, where they expected the menu's own
`lesson.turn` and a lesson window; the failed-call test uses Note in margin's capture.

## 3. Fixes the merges needed

- **BATCH2-1** (ledger): the visual tool kept RD8a's exact stroke-width check beside the parity round's 0.05 px one;
  VR-46's link stroke (4.70588 against 4.7) then counted as a difference in RD2 and RD3. One check now (RD2 21, RD3 7;
  rd8 unchanged at 4).
- **BATCH2-2** (ledger): RD10's `source_retrieval/video_chapters.py` writes its table but was not a registered SQL
  owner, so `test_architecture` failed (on RD10's own branch too); registered.

## 4. Proof

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| vitest, 4 workers | 388 files, 4285 tests, exit 0 |
| `cargo check --offline` | clean |
| desk harness, every run (desks, overview, companion, intent, pads, menus, latex, goal, lesson, video, preview) | 152 passed, 0 failed (display math included) |
| notebook harness (`scripts/desk_harness/notebook.py`, a real sandboxed session, with the reference) | 36 of 36 checks; the frame against the mockup: no difference |
| visual reference, every stage, both viewports | 117 comparisons, none unreachable (below) |

The frontend checks ran on the tree with RD10 merged and the wiring in; what came after is backend and test only
(K2.4c, batch 1's guard fix, the visual tool's one check, the SQL owner) and the visual stages it touches were run
again.

**The comparison** (the tool's own `findings rdN:` lines; the baseline is the parity round's reproducible counts, RD1
37, RD2 22, RD3 7, RD4 20, rd6 7, and each record's for the later stages):

| Stage | This branch | Baseline | Note |
|---|---|---|---|
| RD1 | 36 | 37 | `shelf_lower_head` missing is gone (RD5b's TODAY · RUNNING PAD) |
| RD2 | 21 | 22 | the same row gone; VR-46's links equal by the tool's rule after BATCH2-1 |
| RD3 | 7 | 7 | the anchored companion's `box.y` row reads 90/125 here, 89/124 there (one pixel of the fixture's page) |
| RD4 | 19 | 20 | `pad_jot` missing at the laptop size is gone |
| rd5 | 2 | 2 (batch 1) | which row each mockup link has selected |
| rd6 | 7 | 7 | identical rows |
| rd8 | 4 | 4 (batch 1) | the RD8a record's explained rows |
| rd9 | 4 | the RD9a and B7 records | only the stack paper's width and the frame's box (RD4's stack margins); the border and head colours those records listed are gone with the parity round |
| rd10 | 0 | 0 (the RD10 record) | — |
| notebook | 0 frame differences; the lesson state's 4 geometry rows per viewport | the B7 record | the B7 record's widths and the frame's place (one tab higher: the fixture's stack has two pads above the lesson); its colour rows are gone |

Nothing got worse through the merges.

**Python** (memory-capped, `-n 1`, one command at a time):

- The gate set (`test_mobile_allowlist`, `test_desktop_rpc_contract`, `test_identity_pins`, `test_structure_ratchets`,
  `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`,
  `test_public_tip_guards`, `test_desktop_activation_audit`, `test_generated_provenance`) with `test_registry_audit`,
  `test_grading_cli` and `test_plan_first_transport`: before batch 1's fix, 899 passed and its ten guard tests failed
  (no others); after it, those, the notebook runtime's tests and the pins and ratchets again: 959 passed.
- `test_architecture` alone: 18 passed (after BATCH2-2). `test_test_layout` alone: 3 passed.
- The notebook runtime, pad cells and lessons (the real-sandbox ones included, none skipped), RD9a, K10's figure
  records and why-cases (with the row-recording goldens it moved), K2.4c and K2-20, RD10's sidecar tests, the menu's,
  RD3, RD4, RD6a, RD8a and the job types: 670 passed.
- Every test that reads the migration head fixture (70 files, head 268): 896 passed.
- `ruff check` clean; `lint-imports --no-cache` 54 kept, 0 broken; `check_gate_partition` 33,912 (landing 33,846 +
  arc_close 66). `desktop_validate.py`'s counts hold (417, 397, 16, ACTIVE 423); its other errors are the generated
  notes the landing regenerates.
- Ledger: every row id of each merged tip is in the result (460 at batch 1's tip, 469 after).
