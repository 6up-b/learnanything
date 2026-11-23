# Reader workbench v2: batch 1 integration (2026-11-23)

One landing branch, `land/workbench-batch-1`, cut from RD5b's tip `e93c396b84` (RD4's fix round, RD5a and RD5b), with
the finished workbench branches merged in, the conflicts resolved, the fixes the merges needed, and the proof that
the whole still works and still matches the mockup. No new feature. Not merged (still being built): lesson windows
and the notebook frame.

## 1. What was merged, in order (one merge commit each)

| # | Branch (tip merged) | Merge | Conflicts and how they were resolved |
|---|---|---|---|
| 1 | `origin/main` (`4654bdcf1d`: RD3's fix round, the goal lens backend RD6a) | `e8ba476ca2` | Generated vault notes: main's side (the landing regenerates them). `refactor-status.md`: this branch's RD4a and RD4b rows (with their fix round) plus main's RD6a row and its "RD5, RD9a" row. `tests/test_mobile_allowlist.py`: both pin lists (RD4's fix round, RD5a, RD6a) and all of them in the desktop-only parameter list |
| 2 | `reader/rd4-fix-frontend` (`62c06d013a`: `8344e01da6`, the same fake fix as RD5b-2, and a later regeneration) | `5fb7689595` | `DeskShell.test.tsx`'s union-range fake: the RD4 tip's line. Generated notes: its side |
| 3 | `reader/rd6b-goal-lens-ui` (`1029b57a58`) | `dc3d58973e` | DeskShell: both transports and both defaults; the router's `menu` scope is open for the context menu or the goal path (`menuOpenRef` or `goalPathRef`). The watch panel's cue keeps `data-t` beside the lens's class. `desktop_generate.py`: both area descriptions (menu, goal). `desktop_validate.py`: the counts recomputed for both sets of files. `run.py`: runners `menus` and `goal`. `visual_reference.py`: stages rd5 and rd6 kept, both region sets. The allowlist: one copy of each pin (RD6b had its own copy of RD4's fix-round pin) |
| 4 | `reader/visual-parity-fixes` (`3d157295b1`, which already held RD6b) | `fc10d9f232` | The ⓘ: this branch's placement (in the pad stack's title bar) with the parity round's ring markup (`<span class="ic">`) on the stack's own bar where no desk holds it; the parity round's ring style equals the title-bar ⓘ's. `desk.css`: their sketch styles; their `.desk-padmenu` rules dropped, because the pad menu is the one context menu now and `.desk-menu` already carries VR-40's measured values (360 px, 5 px padding, `#eee`, the 10 px `#a8a8b8` heading with no rule, rows on 1.4, the `#241d12` selection with its amber bar). `visual_reference.py`: `pad_info_button` measures the title-bar ⓘ or the stack's ring; `pad_menu` compares the width only (the parity round's choice: its height follows the rows), `pad_menu_row` an unselected row; `d_info` clicks the title-bar ⓘ. Ledger: their VR rows with this branch's VR-29 (fixed by RD5b), then RD5b's section |
| 4b | `reader/visual-parity-fixes` again (`6e343a97e4`, round 2: the transcript's paper sheet, the laptop strip over the rail, Inter removed) | `c88bcd77ed` | `Shelf.tsx`: both new props (`today`, and `open`/`onOpenChange`). Ledger: their VR-45 text with RD5b's section after it |
| 5 | `refactor/k2.7-job-type-rows` (`debfa75492`) | `1967952f4b` | None (merged cleanly; the conflict-marker check was empty) |
| 6 | `notebook/na0.2-sandboxed-server` (`c09471f7d1`) | `cd2ef20514` | `client.ts`, `dto.ts`: both blocks (the goal lens's types and the notebook runtime's, each interface closed). The allowlist: the notebook pins beside the others. `SidecarContext.load` merged cleanly with both hooks (the polled jobs' `interrupt_vault` and `_stop_notebooks`) |
| 7 | `reader/rd8a-pen-ui` (`ca1ad9d240`, added to the batch by the coordinator) | `0eee7833d2` | `commands.rs`, `main.rs`: both passthrough sets (goal and ink). `dto.ts`: both blocks. `fakeCore.ts`: both imports (ink pads, `FIXTURE_SOURCES` for the menu's judged row) and both sets of answers. `ReaderScreen.tsx`: `ReaderWindowing` gains both `lens` and `onPenSurface`; `ReaderLens` and `PenSurface` both kept. `SourceWindow.tsx`: both. DeskShell: the three transports (menu, goal, pen), the context menu's state beside pen mode's, both key actions (`path`, `pen`), the pads host's dependencies then the pen host, the shell's class with `pen-mode` and `has-goal` inside the pen host provider, both footer hints. `desktop_validate.py`: the counts for all three sets. `visual_reference.py`: both drivers; one `query` field on `State` (the goal lens's form, with its "?"; the ink pad's `?inkpad=1`); stages rd1-rd6 and rd8. The allowlist: the RD8a pins too. Ledger: RD8a-1 in a section of its own after RD5b's |

After every merge `git grep -n -E '^(<<<<<<< |>>>>>>> )'` was empty before the commit. No ledger or status row was
lost: every row id of the bug ledger at each merged tip is in the result (451 ids at RD5b's tip, 460 after; VR 45,
RD3 23, RD4 22, RD5b 2, K2 22, RD8a 1, BATCH1 1). The status file's only rows not carried word for word are rows their owners renamed
on the merged side (main's "RD5, RD9a"; the notebook branch's NA0.2 split).

### Reconciled across branches

- **The key router's scopes**: `notebook, check, menu, typing, arrange, strip, pen, overview, focus, reading`. An open
  context menu claims `menu`; the goal path does too; the laptop strip's `strip` takes esc and passes the rest; pen
  mode's `pen` passes every key, so `.` still opens the menu in pen mode (the pen footer says so).
- **PadStackWindow**: the pen's ink lines and loading sit beside the menu's `openMenu`/`showPad` handle methods; no
  `onContextMenu` came back (the stage's capture listener is still the only one in the desks).
- **`c` on a pen lasso** still asks the companion: the lasso makes the DOM selection and the pen host calls the
  companion key (the pen's tests pass unchanged).
- **The fixture core** answers the menu's calls and the ink calls side by side.
- **`desktop_validate.py`**: 397 TypeScript files (378 + 4 menu + 7 goal + 8 pen), entry-reachable 379, ACTIVE 403,
  vitest-support 14.

## 2. Fixes the merges needed

- **BATCH1-1** (ledger): RD5a's `passage.promoted_job` and `passage.promoted_cancel` read the polled jobs by id alone;
  RD3's fix round keys them by vault. On the merged tree every poll and cancel raised (8 RD5a tests failed); both now
  pass `vault_key(ctx)`, as RD8a's ink reading does after its own RD8a-1.

## 3. Proof

| Check | Result |
|---|---|
| `npm run typecheck` | clean |
| vitest, 4 workers | 378 files, 4195 tests, exit 0 |
| `cargo check --offline` | clean |
| desk harness, every run (desks, overview, companion, intent, pads, menus, latex, goal, preview) | 128 passed, 0 failed (the display-math checks included) |
| visual reference, rd1-rd6 and rd8, both viewports | 111 comparisons, none unreachable (table below) |
| pytest gates | see §4 |

### The comparison (grouped rows from `findings__all.json`, both viewports, excused rows included)

| Stage | Last reported | This branch | Against the parity round's own last findings file |
|---|---|---|---|
| RD1 | 21, then 19 after round 2 (the parity record) | 36 | 37 there: the same rows less `shelf_lower_head` missing (RD5b's TODAY · RUNNING PAD) |
| RD2 | 27, then 21 | 22 | 22 there: `shelf_lower_head` missing gone; two `ov_link` `stroke_width` rows new (below) |
| RD3 | 5 | 8 | 7 there: one `ov_link` `stroke_width` row new (below) |
| RD4 | 20 | 19 | 20 there: `pad_jot` missing at the laptop size gone |
| rd5 (the menu) | 4 per state in RD5b's record (height, and one reason colour) | 2 | The height is no longer compared (the parity round's width-only choice for the menu); the reason colour follows which row each link selects |
| rd6 (the goal lens) | the RD6b record's table | 7 | Identical rows: the reading ring's LO, a hover against a programmatic open, out-of-view marks, a shelf row not on the fixture's desk |
| rd8 (pen and ink) | the RD8a record's list | 4 | The pad paper's gradient shorthand, the note's label wrapping and the underline mark's height (all in the record); the top-bar chip's 12 px row is gone (the parity round's VR-9) |

The parity record's 19/21/5/20 do not match its own findings file (37/22/7/20 for the same states); measured against
that file, nothing got worse through the merges except two rows of one kind that the merge made measurable:

- **`ov_link` `stroke_width`** (the overview's links, `#ov`, `#ovg`, `#cov`): RD8a taught the tool to compare an SVG's
  `stroke-width`. The desks draw a link 2 px on screen (1.2 px for a weaker relation) where the mockup draws every
  link 1.4 px (4.7 world px at the overview's 0.34). The overview is unchanged by the merges; the row is RD2's and is
  left to its owner (the link weights are spec'd per relation), not changed here.

The goal lens and the menu were already set in JetBrains Mono (`--desk-mono`), so the interface font change asked
nothing of them; display math stays unclipped (the harness's LaTeX run passes).

## 4. Python

- `test_mobile_allowlist`, `test_desktop_rpc_contract`, `test_identity_pins`, `test_structure_ratchets` (K2.7's 219),
  `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`,
  `test_public_tip_guards`, `test_reader_rd1_model_parity`, `test_desktop_activation_audit`,
  `test_generated_provenance`: 807 passed.
- `test_architecture` alone: 18 passed. `test_test_layout` alone: 3 passed.
- K2.7, the notebook runtime, RD0, RD3, RD4, RD5a, RD6a and RD8a tests: 504 (8 RD5a tests failed before BATCH1-1;
  they and RD3's fix-round tests pass after it, 40 of 40); identity pins and structure ratchets again after it: 363
  passed.
- Every test that reads the migration head fixture (69 files, the head now 267): 891 passed.
- `ruff check` clean; `lint-imports --no-cache` 54 kept, 0 broken; `check_gate_partition` 33,768 (landing 33,702 +
  arc_close 66). `desktop_validate.py`'s counts hold; its remaining errors are the generated notes the landing
  regenerates (missing notes for the new menu, goal and pen modules, stale ones, reproducibility).
