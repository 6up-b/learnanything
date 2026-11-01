# Reader CA5: also in your books — Codex review, fix round

Branch `reader/ca5-also-in-your-books` (worktree `learnanything-docs`), on the stage commit `646d739fa`.
Codex review job `20261031-192914-QXwzEl` (gpt-6.1-sol; static review, its memory scope could not reach the user bus).
Each finding was reproduced with a failing test first. Every one reproduced, and all six are fixed. No finding
was rejected. No migration, no new config key, no new parameter, no model call, and no live call.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Dismissal retries can acknowledge the wrong LO set | fixed | `e113f31b7` (server), `2ce89d4f4` (client) | Server: `section_coverage.dismiss` now refuses an operation id replayed with a different named LO set (`validation_error`, nothing written). The check applies to a `not_about` that names its LOs; CA5a's unnamed form is unchanged. Client: the pending-operation key includes the normalized LO set (`notAboutAct`), so a line that gained an LO through *also about…* gets a new operation. Tests: `tests/test_reader_ca5_also_in_books.py::test_an_operation_id_reused_for_another_lo_set_is_refused_and_writes_nothing`; `alsoInBooks.test.tsx` "F1: a retried 'not about this' whose line gained an LO is a new operation" |
| F2 | Medium | Hide preferences can overwrite another writer's changes | fixed | `e113f31b7` | `reader.set_correspondence_preferences` re-reads `[reader.correspondence]` from `learnloop.toml` on disk while holding the vault's mutation lock (`vault_mutation_lock`, `.learnloop/vault.lock`, the cross-process flock that `workbench_admit` already uses). It computes the add or remove against that copy and writes atomically inside the lock. It reloads the context whenever the file differs from its in-memory copy. A lock timeout returns `vault_busy`. Test: `test_hide_preferences_from_a_stale_context_keep_another_writers_changes` (two independently loaded contexts; failed before the fix with `['src_lay'] == ['src_book', 'src_lay']`) |
| F3 | Medium | Refreshing after "also about…" removes earlier undo controls | fixed | `2ce89d4f4` | Undo rows now render from `gone` itself, not only while iterating the returned groups. A dismissed line that a reread no longer lists stays under the LO it was listed under. If that LO has left the answer too, the row goes in a trailing group with that LO's title. The block stays mounted while any undo is pending, even when the reread finds nothing judged. Undoing a line the reread omitted reads the list again so the section comes back. Tests: `alsoInBooks.test.tsx` "F3: a reread after 'also about…' that omits a dismissed section keeps its undo, and undo reads again" (the reread really omits the section) and "F3: the last line corrected away and a reread that finds nothing judged still keeps its undo" |
| F4 | Medium | CA5a's deferred peek crumb remains unimplemented | fixed | `2ce89d4f4` | `FindSection` takes `onPeekChange` and `closePeekToken`, the same contract as `AlsoInBooks`. The crumb helpers (`bookShort`, `sectionShort`, `peekCrumb`) moved into `FindSection.tsx`, and `AlsoInBooks` re-exports them, which avoids an import cycle. The Reader keeps `findPeek` beside `alsoPeek` and shows one display-only crumb (`alsoPeek ?? findPeek`). The strip's *close peek* bumps the close token that both lists share. No return-stack entry is added. Tests: `findSection.test.tsx` "a peek reports its crumb, and the strip's close token closes it"; `alsoInBooksReader.test.tsx` "F4: a peek from CA5a's pressed list puts the same crumb in the detour strip, and the crumb closes it" |
| F5 | Low | `x` remains active while the comparison hides the Guide | fixed | `2ce89d4f4` | The `x` gate (`alsoKeyRef`) and the key bar's `x` hint both now require `!comparing`. This matches the rail's own `display: none` while comparing. Test: `alsoInBooksReader.test.tsx` "F5: x is neither offered nor acts while the comparing posture hides the Guide" |
| F6 | Low | Peek headers omit the supplied role labels | fixed | `2ce89d4f4` | The peek header shows the line's `roles` in plain words (`definition, worked example`, each once) in the model's colour, with `data-voice="model"` and the visible label `(model's reading)`. That label is the convention `LibraryAnswer` uses for a model's role reading. The roles come from the coverage judge and RW4e's proposals, so they are AI-written. A section without roles shows nothing. Test: `alsoInBooks.test.tsx` "F6: the peek header names the section's roles, labelled as the model's" |

**Claims that didn't hold** (from the review) are now addressed. The peek crumb covers both lists (F4). A correction-triggered
reread keeps every earlier undo (F3). `x` acts only in the reading posture with the line on screen (F5). Hide
preferences apply to the latest on-disk config under a cross-process lock (F2).

## Gate (fix round)

Environment: `TMPDIR` set to the session scratchpad, outside this worktree's path (the known `docs` substring quirk).
Every test command ran in `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **36 kept, 0 broken**.
- `uv run pytest -n 6` on `tests/test_reader_ca5_also_in_books.py tests/test_reader_ca5a_find_section.py
  tests/test_section_coverage.py tests/test_section_coverage_review.py tests/test_section_coverage_rpcs.py
  tests/test_curriculum_c0b_landing.py tests/test_deliverable_codex_review.py tests/test_deliverable_rpcs.py
  tests/test_deliverable_scope.py tests/test_coverage_on_extract.py tests/test_vault_lock.py tests/test_architecture.py
  tests/test_desktop_rpc_contract.py tests/test_mobile_allowlist.py tests/test_reader_ca3_landing_ca5a.py
  tests/test_reader_ca4_landing.py`: **503 passed**.
- `uv run pytest -n 6` on `tests/test_activity_families.py tests/test_ingest_ownership.py tests/test_migration_coordinator.py
  tests/test_regrade_contract_upgrade.py` (they also reference `section_coverage` / `vault_mutation_lock`): **67 passed**.
- Frontend (`apps/learnloop-tauri`): `npm install` ok; `npm run typecheck` clean; `npm run frontend:build` ok.
- `npx vitest run --maxWorkers=4` on `src/screens/reader/alsoInBooks.test.tsx src/screens/reader/findSection.test.tsx
  src/screens/reader/alsoInBooksReader.test.tsx src/screens/reader/findSectionByPoint.test.tsx
  src/screens/reader/findSectionReader.test.tsx src/screens/reader/inquiryComponents.test.tsx
  src/screens/reader/readerCorrespondenceSettings.test.tsx src/screens/ReaderScreen.inquiry.test.tsx
  src/screens/ReaderScreen.inquiryOff.test.tsx src/screens/ReaderScreen.parity.test.tsx src/screens/ReaderScreen.review.test.tsx
  src/screens/reader/readerHooks.parity.test.tsx src/screens/reader/compareScope.test.tsx
  src/screens/reader/compareScopeCodexReview.test.tsx src/screens/reader/libraryAsk.test.tsx
  src/screens/reader/paletteAskPostures.test.tsx`: **16 files, 167 passed**.
- Not run in this step, as the owner's rule requires: the full pytest suite, the durability lane and the whole vitest run (they run in the landing gate).
  No migration, schema, DB/connection or `src-tauri` change, so no durability-marked tests, no DB reference regeneration and no `cargo check`.

## Notes for landing

- CA6 is running side by side in `learnanything-merge2`, and it touches `s` and the Guide. This round changed
  `ReaderScreen.tsx` only at the `x` gate and its key-bar hint (adding `!comparing`), at the detour strip's `peek` prop
  (`peekCrumbShown`), and at `FindSection`'s two new props. Expect small textual merges there.
- `FindSection.tsx` now holds `bookShort`, `sectionShort` and `peekCrumb`. `AlsoInBooks.tsx` re-exports the first two,
  so existing imports keep working.
