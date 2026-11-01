# Reader CA5a: Codex review and fix round

Stage `reader-ca5a-find-section`, branch `reader/ca5a-find-section`. The review was a static read on
gpt-6.1-sol (codex-job `20261027-180159-hseaxe`) of the stage diff up to `39097dea0`. Its runtime validation
could not start because its systemd user scope was refused.

## Review

Each finding was reproduced first. Backend findings got a sidecar test on the synthetic coverage vault. In
that vault, Lay §5.2 is two blocks long and the held-out §5.9 comes right after it. Frontend findings got a
vitest that failed against the stage's `FindSection.tsx` / `useLibraryAsk.ts`, checked by running the new
tests on the old files: the F3, F4 (correction), F6 and both F7 tests failed, and all three F5 tests failed.

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Peek bypasses exam protection | fixed | `295b77168`, `c915181a2` | Reproduction: `test_f1_the_generic_span_read_runs_on_into_the_held_out_unit`. `get_span_view` on Lay §5.2's jump span returns the held-out sentinel among `next_spans`. The fix is a new `reader.correspondent_peek`, which reads protection again on every call and returns only the hit's own section's blocks (at most three, from the jump locator). Tests: `test_f1_a_peek_shows_only_the_hits_own_section`, `test_f1_a_peek_is_bounded_to_the_first_blocks`, `test_f1_protection_marked_after_the_search_refuses_the_peek` (unit held out after the search: `withheld`, no exposure row; a held-out unit and an exam reading are refused), `test_f1_the_peek_is_off_with_the_presentations_switch`. Vitest: `F1: a peek the server refuses…`, `F1: the peek shows exactly the blocks the server returned…` |
| F2 | High | Peek displays passages without recording their exposure | fixed | `295b77168` | Reproduction, in the same test as the fix: the old peek's record (`get_span_view` on the heading `s5`) leaves `_scan_exposures` blind to a cold item authored from the paragraph `s6`. The fix is a new shared `span_view.record_span_exposures`, the same ledger and row shape as `build_span_view`'s, written in one transaction. The peek records one `source_exposure` row (context `library`) per block it shows, before it returns the text. Tests: `test_f2_every_block_the_peek_shows_is_recorded_as_exposure`, `test_f2_a_peeked_paragraph_that_is_a_cold_items_source_makes_the_receipt_see_it` (the scan now reports `cold_item_source_span_viewed`, a hard exposure) |
| F3 | Medium | Multi-LO corrections can leave permanent partial results | fixed | `295b77168`, `c915181a2` | The fix is a new `reader.correspondent_dismiss`, one operation in one `BEGIN IMMEDIATE` transaction. It writes a section-pair `learner_card` verdict (task `section_correspondence`, id `scd_<operation_id>`, the operation's record) plus C0a's learner row and verdict per LO. A repeated `operation_id` answers from the record and writes nothing. Undo is an operation of its own (`undo_of`): the pair verdict `none`, superseding the undone one, and `none` on that operation's LOs that are still `not_about`. The client keeps an unanswered operation's id and resends it, and sends no compensating request. Tests: `test_f3_not_about_this_is_one_operation_and_a_repeat_writes_nothing` (repeat and repeated undo write nothing), `test_f3_a_failure_inside_the_operation_leaves_nothing` (a crash after the first LO's rows rolls back whole; the same id then commits), `test_f3_an_operation_id_is_never_reused_for_another_correction`. Vitest: `F3: a correction that fails is said, nothing is sent to take it back, and pressing again resends the same operation` |
| F4 | Medium | An old correction can dismiss a different section's results | fixed | `295b77168`, `c915181a2` | Every peek and correction captures the section generation and lands only if it is unchanged after the await. The pending operation is keyed by its origin section, hit and act. A section change resets `busyKey`. Vitest: `F4: a correction started on one section never lands on the next one's list, nor its undo` (A → B with a deferred reply; B shows no *not about this* and no undo, and B's own correction is sent with B as origin), `F4: a peek answered after the section changed never opens` |
| F5 | Medium | Retrying Compare loses the comparison and starts notes | fixed | `295b77168`, `c915181a2` | `LibraryAskState` carries an `intent` (`ask`, or `compare` with its pins). `run` takes it: a comparison keeps its pins, leaves the notes cancelled and runs the comparison when the ask lands. `retry` and `setPersonalized` rerun the same intent, and `compareWith` is `run` with the compare intent. Vitest (`libraryAskJobs.test.tsx`): `F5: retrying a failed compare reruns the comparison with the same pins and no notes`, `F5: the personalization chip reruns the comparison, not an ordinary answer with notes`, `F5: an ordinary ask's retry is still an ordinary ask (its notes follow)` |
| F6 | Medium | Unmapped sections cannot use "Not about this" | fixed | `295b77168`, `c915181a2` | C0a's correction contract is extended without inferring an LO. For a section with no LO, *not about this* writes the section-pair verdict only, and `_fallback` hides a hit whose newest pair verdict from this section is `not_about`. The control shows on every unchecked hit. Test: `test_f6_an_unmapped_section_can_say_not_about_this_and_undo_it` (Lay §6.1 has no LO: exactly one ledger row, the hit stays gone on reload, and undo brings it back); `test_f6_dismissing_is_off_with_the_presentations_switch_and_refuses_protected_sections`. Vitest: `F6: a section with no LO still has not about this` |
| F7 | Low | Closing a pending search does not keep it closed | fixed | `295b77168`, `c915181a2` | Searches have their own generation, bumped by each press, by *close* and by a section change. A reply lands only if its generation is current. Vitest: `F7: closing a pending search keeps it closed when the answer lands`, `F7: two searches answered in reverse order show the newer one` |

No finding was rejected.

**The review's "claims that don't hold":** all four claims were in the stage review
(`docs/reviews/reader-ca5a-find-section.md`), and that file now describes what is built:
- the take-back claim is replaced by the one-transaction operation;
- the notes now stay behind *write the notes* on retry and on the personalization chip as well;
- the peek reads protection again and reads only the hit's own blocks;
- the exposure rows cover every block shown.

The spec's as-built paragraph (`ux_reader_compare_ask_v1.md`, §13) and a note under curriculum §6.5
(`spec_deliverable_curriculum_v1.md`) record the new RPCs and the section-pair verdict.

**Scope and rules:**
- No migration, successor or config key.
- The new code adds no learned or decision parameter. The peek's three blocks (`PEEK_BLOCKS`) is a display
  bound: the spec's "first blocks".
- No model call.
- The pair verdict is `learner_card` in the existing append-only `judgment_ledger` (free-text task, no
  schema change). Scoring, scheduling, projection, grading and serving never read it. It hides a hit in one
  section's unchecked list and nothing else.
- Both new RPCs are desktop-only, pinned in `tests/test_mobile_allowlist.py` as `READER_CA5A_RPCS`. They
  are refused while `reader.correspondence.enabled` (or `curriculum.enabled`) is off.

**Still deferred, as before:** the detour-strip crumb for a peek and §6.5's `reader_action_invoked` salience
events, both CA5's. The F1 reproduction test is kept on purpose: it pins why the peek has its own read. The
generic `get_span_view` is shared and unchanged.

## Gate (targeted; the full suite runs once at landing)

Every pytest, vitest, npm and cargo command ran inside
`systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`. Pytest ran at `-n 6` and vitest at
`--maxWorkers=4`.

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- **Targeted pytest:** 565 passed over 23 files:
  - the stage's test: `test_reader_ca5a_find_section.py` (18, of which 13 are new);
  - C0a's tests: `test_section_coverage.py`, `test_section_coverage_review.py`, `test_section_coverage_rpcs.py`,
    `test_section_coverage_migration.py`;
  - contract pins: `test_mobile_allowlist.py` (new `READER_CA5A_RPCS`), `test_desktop_rpc_contract.py`,
    `test_architecture.py`, `test_table_roles.py`, `test_tracked_fixture_databases.py`,
    `test_sidecar_serializer_snapshot.py`;
  - the span view and exposure scan: `test_coldness_receipt.py`, `test_span_view.py`,
    `test_sidecar_span_view.py`, `test_exam_protection.py`, `test_prescription_passages.py`,
    `test_reader_render_views.py`;
  - the library ask: `test_library_ask_review.py`;
  - the prompt-contract pins this stage touched: `test_compare_keep_switch_off.py`, `test_figures_switch_off.py`,
    `test_reader_tutor_switch_off.py`, `test_reading_paths.py`, `test_reader_intent.py`.
- No durability lane: no migration and no DB or connection code changed. The new writes go through the
  existing `Repository.atomic()`.
- **Frontend** (`apps/learnloop-tauri`):
  - `npm install` and `npm run typecheck`: clean.
  - Vitest: 117 passed over 13 files: `findSection.test.tsx` (22), `findSectionReader.test.tsx`,
    `libraryAskJobs.test.tsx` (7, of which 3 are new), `libraryAsk.test.tsx`, `libraryAskSwitchOff.test.tsx`,
    `libraryExercises.test.tsx` (its state literal gained `intent`), `libraryExercisesReader.test.tsx`,
    `libraryRoles.test.tsx`, `compareKeep.test.tsx`, `compareKeepSwitchOff.test.tsx`,
    `figures/advancedPanels.test.tsx`, `figures/libraryOfferSettle.test.tsx`, `paletteAskPostures.test.tsx`.
  - `npm run frontend:build`: ok.
- `cargo check --manifest-path apps/learnloop-tauri/src-tauri/Cargo.toml`: ok (two passthroughs added).
- No schema change, so the DB reference was not regenerated.
- No paid or live call was made, and no Python ran outside pytest.

## Re-review (Codex, gpt-6.1-sol; job 20261027-182940-XntDNf)

Verdict was REOPENED. F1 and F2 were confirmed fixed. One new finding, F8.

| id | severity | title | verdict | commit | test or reason |
|----|----------|-------|---------|--------|----------------|
| F1 | High | Peek reads protection again; target section's blocks only | confirmed fixed (earlier round) | 295b77168 | `test_reader_ca5a_find_section.py` |
| F2 | High | Every block shown is recorded as `source_exposure` | confirmed fixed (earlier round) | 295b77168 | `test_reader_ca5a_find_section.py` |
| F8 | Medium | Personalization restores obsolete comparison pins | fixed | e40baab23 | `libraryAskJobs.test.tsx`: four new `F8:` tests |

**F8: reproduced, then fixed.** I reproduced the scenario through the real hook with mocked RPCs. Three of the
four new tests failed before the fix:
- B replaced by C, compare, then the chip: it compared A/B again.
- B replaced by C without pressing compare, then retry: it compared A/B again.
- One pin left, then the chip: A/B came back and were compared.

The fourth test checks that an ordinary ask's pins never turn it into a comparison. It passed before the fix
and still passes.

The fix is in `useLibraryAsk.ts`:
- **Pins:** in a comparison started from *find this section*, `togglePin` updates `intent.pins` along with
  `pinned`.
- **Explicit compare:** `compare()` writes the pins it compares into the intent.
- **Rerun:** a retry or the chip uses the pins as the learner last left them.
- **One pin left:** the rerun asks again and keeps that pin. It compares nothing, and compare waits for a second
  pin as in an ordinary ask. Before the fix, `run` had silently refused to rerun.
- **Fewer than two pins:** `compareWith` itself now refuses a call with fewer than two pins (the guard moved
  there out of `run`).
- **Ordinary asks:** their intent stays `ask`. RW4a's behaviour is unchanged.

The spec's as-built paragraph (`ux_reader_compare_ask_v1.md` §13) now says the rerun uses the current pins.

**Scope:** frontend only. The change adds no config key, parameter, migration or model call.

### Re-review gate (targeted)

Every npm and vitest command ran inside `systemd-run --user --scope --quiet -p MemoryMax=5G -p MemorySwapMax=1G`.
Vitest ran at `--maxWorkers=4`.
- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 36 kept, 0 broken.
- **Targeted pytest:** none. This round changed no Python. The earlier round's 565 pytest results stand.
- `npm install` and `npm run typecheck`: clean.
- **Vitest:** 121 passed over 13 files. That is the earlier 117 plus the 4 new F8 tests:
  - `libraryAskJobs.test.tsx` (11)
  - `libraryAsk.test.tsx` (16)
  - `libraryAskSwitchOff.test.tsx` (4)
  - `libraryExercises.test.tsx` (10)
  - `libraryExercisesReader.test.tsx` (3)
  - `libraryRoles.test.tsx` (2)
  - `figures/advancedPanels.test.tsx` (23)
  - `figures/libraryOfferSettle.test.tsx` (4)
  - `compareKeep.test.tsx` (15)
  - `compareKeepSwitchOff.test.tsx` (2)
  - `paletteAskPostures.test.tsx` (4)
  - `findSection.test.tsx` (22)
  - `findSectionReader.test.tsx` (5)
- `npm run frontend:build`: ok.
- `git diff --check`: clean.
- **Not run, and why:**
  - `cargo check`: `src-tauri` is unchanged.
  - Durability lane and DB reference: there is no schema or DB change.
- No live or paid call was made, and no Python ran outside the tools above.
