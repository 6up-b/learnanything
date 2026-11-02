# followups-nov1c: Codex review (gpt-6.1-sol) and fix step

Codex job: `/home/saturn/.cache/codex-agent/jobs/20261101-194828-ENBlAv`. Branch `fix/followups-nov1c`
in `learnanything-ad1`, on the stage tip 04467f9907. No live calls, no paid commands, no
migration, no new table, no config key. Fake tend only. The owner's notes and vaults were not read.

## Review

Each finding was reproduced first: the new tests failed on the stage tip (code reverted
in place for the run, tests kept) and pass with the fix.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Unreadable Reader provenance is treated as safe | fixed | 44faaaad73 | `tests/test_router_card_reading_gaps.py::test_a_reader_question_whose_passage_is_unreadable_or_missing_fails_closed`, `::test_an_extraction_named_without_a_block_is_checked_whole` (both failed before the fix) |
| F2 | Low | A clock correction can block note refreshes across restarts | fixed | 13c0b95b25 | `tests/test_notes_linked.py::test_r6_review_f2_a_clock_correction_and_restart_never_blocks_later_refreshes` (failed before the fix: 0 refreshed), `tests/test_ids.py::test_new_ulid_after_sorts_after_a_floor_persisted_by_a_process_whose_clock_ran_ahead`, `::test_new_ulid_after_ignores_a_floor_that_is_not_a_ulid_or_is_behind` |
| F3 | Low | The passage action misstates what the resolver reads and changes | fixed | 47ef1fe071 | `scopeFromPassage.test.tsx` "says the passage joins earlier scope inputs and the scope is updated, not only added to" (failed before the fix) |
| F4 | Low | Restoring a model's passage link reports an unconditional success | fixed | abe50f75b0 | `hiddenNotesSettings.test.tsx` "a model's passage link whose proposal is gone gets the model's copy, not the manual one" (failed before the fix) |

Desktop catalog regenerated in b4a88359d6.

### What changed

- **F1** (`diagnosis/text_gaps/provenance.py`): `reading_sources` now fails closed
  (`((), False)`, so the card shows `WITHHELD_UNREADABLE`) when a question's recorded
  `source_context_json` is not a JSON object, when a Reader question (`context = 'reader'`,
  the only context `tutor_qa` records a passage under) names no passage, or when a block is
  named without its extraction or a delivered span is not an object. An extraction named
  without a block, at the top level or in `source_spans`, is now a whole-extraction ref
  (`span_ids: []`), which `exam_material.source_ref_keys` checks conservatively (any material
  in that extraction withholds the words). A practice question with no recorded context
  still has no reading and shows as before. `question_record` (the C1 write record) is
  unchanged: the stricter parser is used only by the router card's reading check.
- **F2** (`ids.new_ulid_after`, `learner_notes.newest_read_token`,
  `note_links._read_token`): when a read of a hand-linked note starts, it reads the newest
  `read_token` any current-snapshot marker carries from the database, and mints its token
  above both that floor and every ULID the process minted before. A token persisted while
  the clock ran ahead before a restart no longer fences off later refreshes. Two processes
  lifted to the same floor get distinct ids: the randomness lands up to 2^32 past the floor
  (`_FLOOR_JITTER_BITS`, labelled `keep`, spacing only). The fence check is unchanged, so the
  R6 safety property holds: an older read never publishes over a newer one.
- **F3** (`ScopeFromPassage.tsx`): the copy now reads "This passage joins what you've
  already given your deliverable (its description, earlier passages, a syllabus).
  LearnLoop's model reads them all again and updates its scope, which can add topics or drop
  some. Review them in the Guide." This matches `deliverables.resolve`, which rereads every
  `SCOPE_KINDS` input in order, plus `_INSTRUCTIONS` ("A later input refines or corrects an
  earlier one"). The stage record's quote of the old copy (`followups-nov1c.md`, section D)
  is superseded by this one.
- **F4** (`HiddenNotesSettings.tsx`): the "show again" toast now picks its copy by the
  link's origin (`learningObjectId` present means the model made it). This is the same rule
  `note_links.hidden` uses for `by_label`. The target kind no longer decides it.

### Claims that don't hold (from the review)

All four (A, C, D, E) were the same defects as F2, F4, F3 and F1, and are fixed by those commits.

## Gate (this step; the full suite runs once in the landing gate)

- `uv sync --extra dev --extra mobile` then `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: **40 kept, 0 broken**.
- Targeted pytest:
  `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G -- uv run pytest -n 6 <files>`
  ran **463 passed, 0 failed**, over:
  - tests/test_router_card_reading_gaps.py (changed)
  - tests/test_notes_linked.py (changed)
  - tests/test_ids.py (changed)
  - tests/test_diagnosis_input_provenance.py
  - tests/test_figure_predictions.py
  - tests/test_figures_codex_review.py
  - tests/test_figures_show_me.py
  - tests/test_ux_phase4_landing.py
  - tests/test_mcp_c1a_landing.py
  - tests/test_router_card.py
  - tests/test_router_reader_activity.py
  - tests/test_mcp_tools.py
  - tests/test_curriculum_c3_exam_scoping.py
  - tests/test_learner_notes_migration.py
  - tests/test_notes_never_read.py
  - tests/test_architecture.py
  - tests/test_ad23_contract.py and tests/test_hint_telemetry.py (both patch the `ids` generator state)
  - tests/test_voi_v2.py and tests/test_voi_merge_composition.py (the same, through `voi_restore_scenarios`)
  - tests/test_table_roles.py
  - tests/test_tracked_fixture_databases.py
- Durable SQLite (`--durable-sqlite`, memory-capped, serial) for the new store query:
  tests/test_notes_linked.py and tests/test_ids.py ran **56 passed**.
- Frontend (`apps/learnloop-tauri`, each memory-capped): `npm install` ok, `npm run typecheck`
  exit 0, `npx vitest run --maxWorkers=4 src/screens/reader/scopeFromPassage.test.tsx
  src/screens/reader/hiddenNotesSettings.test.tsx` ran **2 files, 14 passed**, `npm run frontend:build` ok.
- Desktop catalog: `desktop_generate.py` then `desktop_validate.py` passed (304/304 TS + 6/6 Rust,
  ACTIVE=310, reproducible byte-for-byte). No schema change: `db_validate_reference.py`
  returned `errors: []` without regeneration.
- Not run: cargo (nothing under `src-tauri` changed), and the full pytest, durability or
  vitest suites (owner rule 2026-10-17: landing gate only).
