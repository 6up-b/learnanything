# Reader RW4d: Codex review and fixes

Stage `reader-rw4d`, branch `reader/rw4d`, worktree `learnanything-rw4b`. Codex
reviewed `3988cf778..reader/rw4d` at `14de0ed39` (job
`20261020-155929-bt0iPc`): one High and nine Medium findings. Each was
reproduced first (a test that failed on `14de0ed39`), then fixed. None was
rejected. No migration, no new config key, no live or paid model call: every
test uses fakes, and no vault copy was opened.

## Findings

| id | severity | title | verdict | commit | test or reason |
|---|---|---|---|---|---|
| F1 | High | Keep and Remove can leave durable partial state | fixed | e05e3fc2b | `test_a_keep_interrupted_after_its_proposals_writes_nothing_and_a_retry_keeps_once`, `test_an_interrupted_remove_leaves_the_keep_whole`, `test_concurrent_keeps_of_one_comparison_write_one_set` (also run with `--durable-sqlite`, WAL) |
| F2 | Medium | Adding a take to an older comparison targets the newer comparison | fixed | e05e3fc2b, cca623480 | `test_a_take_on_an_older_kept_comparison_stays_on_it`; vitest "a take added to a reopened comparison names that comparison (F2)" |
| F3 | Medium | Keep and reopen are missing on the library landing page | fixed | cca623480 | vitest "keep and reopen work on the library page with no book open (F3)" |
| F4 | Medium | Retrying a take duplicates learner content | fixed | e05e3fc2b | `test_replaying_a_take_does_not_duplicate_it_even_at_the_limit` |
| F5 | Medium | Reopen restores relations rejected during Keep | fixed | e05e3fc2b | `test_reopen_shows_only_the_relations_kept_among_same_labelled_pairs` |
| F6 | Medium | The card reader does not honor historical `as_of` | fixed | e05e3fc2b | `test_the_card_reads_keeps_takes_and_removals_as_of` |
| F7 | Medium | Relation successors have no persisted lineage | fixed (no migration; see open question) | e05e3fc2b | `test_relation_successors_record_what_they_supersede` |
| F8 | Medium | A valid partial keep loses its Remove control | fixed | cca623480 | vitest "a kept comparison that retained one source keeps its takes and its remove (F8)" |
| F9 | Medium | A passage's mark opens only its newest comparison | fixed | e05e3fc2b, cca623480 | `test_a_passages_mark_lists_every_comparison_kept_on_it`; vitest "a passage in two kept comparisons lists both and opens the one picked (F9)" |
| F10 | Medium | Kept-comparison marks are absent from the PDF surface | fixed | cca623480 | vitest "⇄ marks the original PDF too, beside the cue marks and outside their count (F10)" |

References regenerated in 27b3fe711. The only change was cited line numbers in `kept_comparisons.py`. The schema is unchanged, head 213, 0 errors.

## What changed

- **F1.** `keep`, `keep_tutor` and `remove` each run inside one
  `Repository.atomic()` (`BEGIN IMMEDIATE`). That transaction covers the state read, the
  fork or new tutor row, the proposals, the keep record (`kept_json` /
  `kept_at`) and the salience-only event. All reads in
  `kept_comparisons.py` now go through `repository.connection()`, which is the
  transaction's own connection inside `atomic()`. The separate
  `connect(read_only=True)` handles are gone. A second request waits for the first,
  then reads its keep, and never writes a second set.
- **F2.** `keep(..., comparison_id=)` and `remove(..., comparison_id=)` (the RPC
  inputs `comparisonId`) name the comparison that was shown. The cases:
  - The row keeps that comparison: its takes are added there.
  - It is the ask's latest comparison and the ask keeps another: it is kept on its own forked row, as before.
  - Neither: the request is refused with `stale_comparison` and nothing is written.

  `CompareKeep` sends the table's `comparisonId` on keep and on remove. Omitting it keeps the old behaviour (the ask's latest).
- **F3.** The library landing branch's `LibraryAnswer` is wrapped in
  `CompareKeepContext.Provider`.
- **F4.** `take_key(keys, text)` is a sha256 over the passages in order plus the normalised words, and it is stored on each take. Validation still covers every take. Takes already kept, and duplicates within one request, are skipped. The twelve-take limit counts only new takes, so a replay at the limit succeeds and writes nothing.
- **F5.** Reopen matches each kept relation by its full signature: endpoints,
  label, statement and both quotes. Matching is a multiset, so each kept relation is shown once and a
  same-labelled relation that failed Keep's recheck is not shown.
- **F6.** Each removal's history entry now stores the removed keep's
  `kept_at` and a snapshot of its objects, relations, takes, keys, LOs and caller.
  `kept_comparisons_for_card` reads every ask with a `kept_json`, live or removed
  (`library_asks.asks_with_keeps`). For `as_of` it shows the keeps that had been kept by
  then and not yet removed, and counts only the takes created by then. Without `as_of`
  it shows the keeps that are live now, as before.
- **F7.** Remove records each successor as `{relation_id, supersedes}` in the
  ask row's `relation_successors`. RW4d's removal is the only writer of
  relation successors (`git grep supersede_relation`). `relation_lineage(repository)`
  and `relation_head(repository, relation_id)` read a relation's current head from that record.
- **F8.** `CompareKeep` requires two rows only for a new keep. A table that
  is kept keeps its takes, add-a-take and remove whatever it retained.
- **F9.** Each mark now carries `comparisons`: ask id, `kept_at`, question
  and other sources, newest first. `KeptMark` with more than one lists them
  ("“question” · with Book · 3 Oct") and opens the one picked.
- **F10.** `ReaderScreen` merges the `⇄` marks into the PDF pane's overlay
  gutter. A kept mark sits below the cue mark when the passage has one. The marks are added after cue placement, so the density setting never counts them. `KeptMark` has a `pdf` variant: a gutter slot that also stops mouse events, so the page's selection does not start, and the table opens beside it.

## Open question for the owner

- F7 is fixed without a migration: the lineage lives on the ask row
  (`library_asks.kept_json`), which is the only producer of successors. A generic
  consumer that reads only `source_object_relations` still cannot see a predecessor.
  A `supersedes_relation_id` column would need migration 216. That is deferred unless P3's
  review inbox comes to need relation heads straight from the table.

## Gate (fix step; owner rule 2026-10-17: targeted only)

- `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2`: ok.
- `uv run lint-imports --no-cache`: 28 kept, 0 broken.
- `TMPDIR=fixtures-local/tmp uv run pytest -n auto`: **585 passed** over 21 files:
  - `tests/test_compare_sources_keep.py`
  - `tests/test_compare_keep_switch_off.py`
  - `tests/test_mobile_allowlist.py`
  - `tests/test_architecture.py`
  - `tests/test_find_sources_intents.py`
  - `tests/test_reread_safety.py`
  - `tests/test_sidecar_reader_p3_slice2.py`
  - `tests/test_source_objects.py`
  - `tests/test_desktop_rpc_contract.py`
  - `tests/test_sidecar_contract.py`
  - `tests/test_table_roles.py`
  - `tests/test_coordinated_migrations.py`
  - `tests/test_tracked_fixture_databases.py`
  - `tests/test_reader_intent.py`
  - `tests/test_reader_tutor_switch_off.py`
  - `tests/test_rw4_kill_switches.py`
  - `tests/test_library_ask.py`
  - `tests/test_library_ask_expand.py`
  - `tests/test_library_ask_review.py`
  - `tests/test_library_asks_migration.py`
  - `tests/test_reader_report.py`
- `uv run pytest -n auto --durable-sqlite tests/test_compare_sources_keep.py`:
  **42 passed** (production pragmas and WAL, including the concurrency test).
- The concurrency test was rerun alone 3 times: 1 passed each time.
- Frontend (`apps/learnloop-tauri`):
  - `npm install`: ok.
  - `npm run typecheck`: ok.
  - `npx vitest run`, first run: **58 passed** over 7 files:
    - `src/screens/reader/compareKeep.test.tsx` (14)
    - `src/screens/reader/compareKeepSwitchOff.test.tsx`
    - `src/screens/reader/libraryAsk.test.tsx`
    - `src/screens/reader/TutorOffers.test.tsx`
    - `src/components/PdfReaderPane.marks.test.tsx`
    - `src/screens/ReaderScreen.marginMarksReview.test.tsx`
    - `src/screens/ReaderScreen.pdfSelection.test.tsx`
  - `npx vitest run`, second run: **36 passed** over 3 files:
    - `src/screens/ReaderScreen.marginMarks.test.tsx`
    - `src/screens/reader/TutorOffers.test.tsx` (again)
    - `src/screens/reader/cues.test.ts`
  - The switch-off snapshot is unchanged.
  - `npm run frontend:build`: ok.
- Reproduction, frontend: with `CompareKeep.tsx`, `KeptMark.tsx` and
  `ReaderScreen.tsx` reverted to `14de0ed39`, `compareKeep.test.tsx` had 7
  failures. They were the 5 new tests plus the 2 updated assertions for `comparisonId`.
- Reproduction, backend: all 9 new pytest tests failed on `14de0ed39`.
- References: `db_generate_reference.py` and then `db_validate_reference.py`: 0 errors.
- Not needed in this step:
  - `cargo check`: nothing under `src-tauri` changed; the RPCs are passthroughs.
  - Config, CLI help and serializer snapshots: no key or command changed.

## Fix round 2 (orchestrator)

The whole-stage verify of `3988cf778..27215b877` (Codex job
`20261020-163406-Kr0sIB`, VERDICT: REOPENED) found two High and two Medium
findings. The orchestrator's rulings were binding. Each finding has a test that fails on
`27215b877`, and each is fixed in `eaafb6f45`. References were regenerated in `18f4b0600`
(commit labels and `kept_comparisons.py`'s cited lines; schema unchanged,
head 213, 0 errors). No migration, no new config key, no model call. Every
test uses fakes. The reference scripts ran only under `env -i` with an empty
`HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR` and the model base URLs at
`127.0.0.1:9`. No vault copy or fixture vault was opened.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F1 | High | Adding a take duplicates a kept comparison | fixed | `test_a_comparison_another_ask_keeps_is_modified_there_never_kept_twice` (the verify's A/B sequence: 2 objects, one live keep), `test_the_tutor_shown_a_comparison_the_learner_keeps_modifies_that_keep`; vitest "a take on a comparison another question keeps goes to the row that keeps it (verify F1)" |
| F2 | High | Held-out kept quotes through `reader.source_objects` | fixed | `test_a_kept_comparison_held_out_later_is_not_returned_by_any_reader_rpc`, `test_source_objects_fail_closed`, `test_every_entry_point_reading_source_objects_is_pinned` |
| F3 | Medium | The card read ignores current held-out status | fixed | `test_the_card_omits_a_comparison_held_out_now_at_every_as_of` |
| F4 | Medium | Tutor keeps cannot take a take with the library answer off | fixed | `test_a_tutor_keep_takes_a_take_with_the_library_answer_off` (including its cold-attempt refusal) |

### What changed

- **F1.** `kept_comparisons.live_keep_of(repository, comparison_id, prefer=)` returns the row that keeps a comparison now. That is the named ask when it keeps it; otherwise it is the earliest live keep of that comparison from any caller, because the service reuses a stored comparison across callers too.
  - `keep` calls it inside its `atomic()` transaction, before any proposal is written. A comparison the ask shows that another row keeps is modified on that row. It is never kept a second time. `compare_kept_state` and `keep_tutor` use the same resolution.
  - `CompareKeep` sends `kept.askId` (with the `comparisonId` shown) whenever it modifies an existing keep, for library and tutor tables alike.
- **F2.** `reader.source_objects.withheld_source_objects(vault, repository, heads)` reads each object's provenance:
  - every citation's span, on the reading it was made on (`CitationResolver`), on its book's current reading, and on every reading of its revision;
  - plus the `selected_span_ids` in its content.

  It asks the one predicate (`exam_material`). It fails closed. If the predicate cannot be read, every object is withheld. An object with no span to place is withheld while its book has any exam or held-out material.

  `source_objects_for_source(vault, repository, source_id=)` now requires the vault and filters through it. `reader.source_objects` passes it. Rows stay in the ledger.

  **The enumeration.** In every entry-point package (`learnloop_sidecar`, `learnloop_mcp`, `learnloop_mobile`, `learnloop/cli`), `reader.source_objects` is the only RPC that reads source objects, their versions or their citations. The pin test fails if another one appears. The other source-object RPCs are covered in the same keep-then-withhold-then-read test:
  - `reader.proposal_inbox` returns mapping proposals and no object content;
  - `reader.review_source_object` and `reader.link_relation` return ids only;
  - RW4d's `reader.kept_comparisons` and `reader.library_compare_reopen` were already filtered or refused.

  Two library modules read the tables but serialize nothing: `find_sources`' intent boost and `corpus.role_proposal_keys`. They return span keys, which then pass the search's own exam exclusion.
- **F3.** `kept_comparisons_for_card(vault, repository, *, learning_object_ids, as_of)` asks `exam_withheld` once over every candidate episode's passages: its `keys` and each kept object's span.
  - It omits any episode holding a passage withheld now, at every `as_of`.
  - It also omits an episode whose passages cannot be named.
  - If the predicate raises, it returns `[]`.
- **F4.** The sidecar's `_row_guard(vault, repository, row)` chooses the guard from the row's persisted caller:
  - a tutor keep (`caller = 'tutor'`) gets `tutor_keep_enabled` plus its request's cold check;
  - a library keep gets `keep_enabled` plus its ask's binding (`follow_up_caller`).

  `keep` and `keep_tutor` take it as `guard` and call it on the row they will write, inside the transaction and before any write. On a fork it is called on the source row, whose caller the fork copies. The askId path of `reader.library_compare_keep` first requires that either surface's keep is on (the switch-off golden is unchanged), then leaves the rest to the guard.

  `reader.library_compare_reopen` uses the same guard, so adding a take follows reopen's rules exactly. The `⇄` marks (`kept_marks(..., available=)`) leave out a keep whose caller's switch is off, so no mark opens a table that would refuse. Remove still needs only one of the switches.

**Decisions.** The two calls that go beyond the verify's text:
- **Any caller.** `live_keep_of` resolves across callers. The ruling "never kept twice" holds even when a library ask is shown a comparison the tutor kept, or the reverse.
- **Reopen and marks.** Reopen and the marks now follow the per-row rule as well as Keep. This changes one behaviour: with the library answer off and the tutor's keep on, a library keep is no longer reopened or marked. Before, it was reopened, but a take on it was refused.

### Gate (targeted; owner rule 2026-10-17)

- `uv run lint-imports --no-cache`: **28 kept**, 0 broken.
- `uv run pytest -n auto`: **478 passed** over 17 files:
  - `test_compare_sources_keep`
  - `test_compare_keep_switch_off`
  - `test_source_objects`
  - `test_library_ask`
  - `test_library_ask_expand`
  - `test_library_ask_review`
  - `test_library_asks_migration`
  - `test_reader_tutor_offers`
  - `test_reader_tutor_retrieval`
  - `test_reader_tutor_switch_off`
  - `test_mobile_allowlist`
  - `test_desktop_rpc_contract`
  - `test_architecture`
  - `test_sidecar_reader_p3_slice2`
  - `test_rw4_kill_switches`
  - `test_reread_safety`
  - `test_find_sources_intents`
- `uv run pytest -n auto --durable-sqlite tests/test_compare_sources_keep.py tests/test_compare_keep_switch_off.py`: **51 passed**.
- Frontend (`apps/learnloop-tauri`):
  - `npm run typecheck`: clean.
  - `npx vitest run src/screens/reader`: **61 files, 463 tests passed**. `compareKeepSwitchOff`'s snapshots are unchanged.
  - `npm run frontend:build`: built (the usual chunk-size warning).
- Fail first, backend: the 7 new pytest tests ran on `27215b877`'s `src` (`git archive`, `-o pythonpath=`) and **all 7 failed**.
- Fail first, frontend: the new test file ran on `27215b877`'s `apps/learnloop-tauri`, extracted to the scratchpad with the worktree's `node_modules`. **1 failed** (the new F1 test) and 14 passed.
- References: `db_generate_reference.py` then `db_validate_reference.py`: 0 errors.
- Not run: `cargo check`, because nothing under `src-tauri` changed.
