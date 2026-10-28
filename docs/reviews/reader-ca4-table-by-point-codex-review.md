# Reader CA4: the table by point, Codex review record

Stage `reader-ca4-table-by-point`, branch `reader/ca4-table-by-point` (worktree `learnanything-dl1`).
Review: Codex (gpt-6.1-sol), job `20261027-204313-XUrr9U`, on the stage tip `2bc351278`. Eight
Medium findings, no High. The stage record is `docs/reviews/reader-ca4-table-by-point.md`.

## Review

Each finding was reproduced first with a test that fails on the pre-fix code. The backend
tests fail on `2bc351278`. The 7 frontend tests were run against the pre-fix
`ComparePointTable.tsx`, `useLibraryAsk.ts` and `LibraryAnswer.tsx` (taken from `HEAD` and then
restored, with no stash) and all 7 failed. All of them pass after the fix. No migration, config
key, RPC shape or DTO changed. No paid or live call was made: every model is a fake.

| id | sev | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Switching off by point can bring back a hidden row's line | fixed | `0105c383a` | `tests/test_reader_ca4_table_by_point.py::test_switched_off_a_hidden_row_sharing_a_quote_stays_hidden_by_book`. `_reopen_by_book` now filters a keep by point by kept cell (`cell_key(passage, point_id)`), not by quote text. Its kept relations also match on their row; a v1 keep is unchanged. |
| F2 | Medium | A hidden row's draft stops the comparison from being kept | fixed | `d9064cea2` | `comparePointTableCodexReview.test.tsx` "F2…". Keep no longer sends a take on a row that is hidden now; the take stays in its row. Showing the row after the keep sends the take in the same request (the server shows the row, then adds takes). The backend test `test_a_take_waiting_on_a_hidden_row_goes_with_showing_it` pins both the refusal the client now avoids and the show+take path. |
| F3 | Medium | Rapid hides undo an earlier hide | fixed | `d9064cea2` | "F3…". The rows the learner wants hidden change at once on every press. Keep requests run one at a time, and each hide sends the latest wanted set (a set the server already has is skipped). A reply updates the rows only when no later hide is waiting. A failed hide puts back the server's rows. |
| F4 | Medium | By book loses the row takes; empty take cells have no pointer control | fixed | `d9064cea2` | "F4…". By book now ends with a *› you* card holding the learner's take on each shown point; `t` on a book's cell opens the box there, and the roving focus reaches it. An empty take cell (grid, cards, the by-book card) has a pressable *› add your take*. There is none on a hidden row or a view no book fills, the same rule as `t`. |
| F5 | Medium | A quote across two anchor blocks gets the wrong span key | fixed | `0105c383a` | `test_a_quote_across_two_anchor_blocks_is_not_shown_as_one_blocks_words`. `_verified_points` now requires a block that holds the whole quote. A quote that spans two blocks is shown as *not addressed* and listed as dropped ("its quote runs across two blocks of the passage"). This matches Keep's `_holder`, which could not cite it either. A multi-block quote anchor (the review's alternative) would widen the stage. |
| F6 | Medium | *Compare again by point* widens a named-book comparison | fixed | `d9064cea2` | "F6…". With CA3 on, the rerun sends `sourceIds`, the books the table shows, with its pins. Pins alone do not narrow discovery. With CA3 off the request is today's pinned one, which takes no `sourceIds`. |
| F7 | Medium | A missing perspective has no recovery action | fixed | `d9064cea2` | "F7…" (2 tests). `useLibraryAsk.whereElse(words, question)` runs a library ask (`entry: where_else_explained`) on *question: view* from the same open book and passage, so the server derives the same caller. `LibraryAnswer` wires it as `onWhereElse`. The table passes its own question, so a reopened keep works too. |
| F8 | Medium | Hiding the focused book cell removes the grid's tab stop | fixed | `d9064cea2` | "F8…". `-` moves the focus to the row header it collapses to. An effect also clamps the roving focus whenever the rows or the layout change, and moves DOM focus when the focused cell went away. |

Notes on the review's conformance table. These were not numbered findings. They are left for the
landing reviewer or a follow-up and were not changed here, to keep the scope to the findings:

- The section locators in cells, and actionable *also discussed in* entries (§5.1).
- The rerun action on a margin-mark reopen (§5.3).
- §14 evaluation recording for by-book choices and pre-Keep row hides.

The claims "a quoted cell names the block that holds its quote" (F5), "by book keeps the take
interaction" (F4), "hidden content stays excluded with the switch off" (F1) and "hide row is a
reliable edit" (F2, F3) now hold, each pinned by the tests above.

## Gate (fix step)

Per the owner rule of 2026-10-17, the full suite runs once, in the landing gate. Every test
command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- Targeted pytest, `uv run pytest -n 6`: **771 passed** (2:08) over these files:
  `tests/test_compare_keep_switch_off.py`, `tests/test_compare_sources_keep.py`, `tests/test_compare_sources.py`,
  `tests/test_e0_review_round2.py`, `tests/test_e0_review_round3.py`, `tests/test_figures_rw5b_fix_round2.py`,
  `tests/test_find_sources_intents.py`, `tests/test_library_ask.py`, `tests/test_library_ask_review.py`,
  `tests/test_library_exercises.py`, `tests/test_mobile_allowlist.py`, `tests/test_output_budget.py`,
  `tests/test_reader_ca3_codex_review.py`, `tests/test_reader_ca3_codex_round3.py`,
  `tests/test_reader_ca3_compare_anywhere.py`, `tests/test_reader_ca4_table_by_point.py` (21 tests, 3 new),
  `tests/test_reader_compare_table.py`, `tests/test_reader_find_sources_callers.py`, `tests/test_reader_intentions.py`,
  `tests/test_reader_intent.py`, `tests/test_reader_tutor_offers.py`, `tests/test_retrieval_interventions_write_points.py`,
  `tests/test_rw4d_rw3b_composition.py`, `tests/test_source_service_spend_envelopes.py`,
  `tests/test_sources_merge_composition.py`, `tests/test_tool_registry.py`, `tests/test_tool_results_withhold_answers.py`,
  `tests/test_tools_cli.py`, `tests/test_tutor_tool_requests.py`, `tests/test_reader_tutor_switch_off.py`,
  `tests/test_rw4_kill_switches.py`, `tests/test_figures_switch_off.py`, `tests/test_reading_paths.py`,
  `tests/test_architecture.py`.
- No durability run: no migration and no DB or connection code changed.
- Frontend (`apps/learnloop-tauri`):
  - `npm install`: ok.
  - `npm run typecheck`: clean.
  - `npx vitest run --maxWorkers=4` on the touched files: **10 files, 111 passed**. The files were
    `src/screens/reader/comparePointTableCodexReview.test.tsx` (new, 7), `comparePointTable.test.tsx`,
    `compareKeep.test.tsx`, `compareScope.test.tsx`, `compareScopeCodexReview.test.tsx`, `libraryAskJobs.test.tsx`,
    `libraryExercises.test.tsx`, `figures/advancedPanels.test.tsx`, `figures/libraryOfferSettle.test.tsx` and
    `src/app/classicIsBase.test.ts`.
  - `npm run frontend:build`: built.
- No cargo check (nothing under `src-tauri` changed) and no DB reference regeneration (no schema change).
