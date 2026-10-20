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

## Fix round 3 (orchestrator)

The verify of round 2 (Codex job `20261020-165958-KahjKV`, VERDICT: REOPENED) confirmed the duplicate-keep, card and stored-caller fixes. It also confirmed the proposal boundaries, atomicity, mapping, tutor gating, takes and both switch-off pins. Two findings remained. Each has a test that fails on `91fa03116`, and each is fixed in `79a6f7e12`. References were regenerated in `76d1b2442`: commit labels, and `library_asks`' note now lists `reader/source_objects.py`. The schema is unchanged, head 213, 0 errors. Same rules as round 2: no model call, fakes only, the reference scripts only under `env -i`.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F1 | High | The comparison's question, copied into every object, carried a withheld quotation | fixed | `test_a_question_quoting_a_held_out_passage_is_redacted_in_every_object` (the quoted-question regression), `test_a_held_out_passage_the_question_came_from_redacts_the_shared_fields`, `test_shared_comparison_fields_fail_closed` |
| F2 | Low | The pin did not enumerate individual RPC readers | fixed | `test_every_registered_handler_reading_source_objects_is_pinned`, `test_the_pin_catches_a_second_raw_reader` |

- **F1.** `reader.source_objects.comparison_passages` names every passage that contributed to a comparison:
  - the stored comparison's sources, counterparts, unverified sources and dropped pins;
  - the ask's anchor, or the tutor request's selection.

  `withheld_comparisons` asks the one predicate once over all of them. It fails closed: an unreadable comparison or predicate counts as withheld.

  While any contributing passage is held out now, the shared fields read `(withheld: part of this comparison is held out for an exam now)`. The shared fields are `query`, `question`, `requested_perspectives` and `missing_perspectives`. They are redacted at read time, so already-stored objects are covered. The redaction applies to:
  - every object of the comparison in `reader.source_objects`, whose own lines and citations stay;
  - the `⇄` marks' comparison entries;
  - the reopened table's question and perspectives.

  The card omits such an episode. `reader.proposal_inbox` carries no comparison field (kept comparisons write no mapping proposals). It is still read in both regressions.

  **Decision.** The ask's anchor counts as contributing: a question is typed from the passage it was asked about.
- **F2.** `handlers/reader.py` declares `SOURCE_OBJECT_READ_PATHS = {"reader.source_objects": "SO.source_objects_for_source(vault, ...)"}`.
  - **The pin.** It parses every module of the sidecar, MCP, mobile and CLI packages (AST). It lists each function that reads source objects, with the RPC it is registered as and its read paths. Guarded service calls (the vault first) are kept apart from raw reads: a repository reader named or passed, or SQL over the source-object tables. That list must equal the declaration, and the declared RPC must be the handler `METHOD_REGISTRY` serves.
  - **The mutation check.** It appends each of these to `handlers/reader.py`, and each fails the pin:
    - a second RPC returning `repository.source_objects_for_source(...)`;
    - an RPC with raw SQL;
    - a second guarded RPC;
    - a raw helper.

    Swapping the declared guarded call for a raw one fails it too.

### Fail first

- The 5 new tests ran on `91fa03116`'s `src` (`git archive`, `-o pythonpath=`): **5 of 5 failed**.
- `91fa03116`'s own pin was run against its tree with a second raw RPC appended to `handlers/reader.py`. It **passed**: the gap the verify reproduced.

### Gate (round 2's)

- `lint-imports --no-cache`: **28 kept**, 0 broken.
- `pytest -n auto` over the same 17 files: **482 passed**.
- `--durable-sqlite` on `test_compare_sources_keep` and `test_compare_keep_switch_off`: **55 passed**.
- `npm run typecheck`: clean.
- vitest `src/screens/reader`: **61 files, 463 tests passed**.
- `npm run frontend:build`: built.
- No frontend file changed in this round.

## Fix round 4 (orchestrator ruling)

The verify of round 3 (Codex job `20261020-171709-CsefBL`, VERDICT: REOPENED) confirmed:
- the registered-handler pin, with all its mutations rejected;
- the card omission;
- the allowlisted fine labels;
- every non-protection invariant.

It found two Highs. F1: comparison-derived prose survived the round-3 redaction (`lines[].text` and `.perspective`, relation statements, `kept_relations`, takes). F2: Keep ignored a withheld contributing anchor.

The orchestrator's binding ruling was to stop redacting fields. The round-3 redaction (`redact_shared`, `SHARED_WITHHELD`) is removed. Fixed in `7764235c3`; references were regenerated in `519ce7ca0` (schema unchanged, head 213, 0 errors).

**The rule.** If **any** contributing passage of a comparison is withheld now, or its protection or provenance cannot be resolved, the comparison is withheld **whole**. Contributing passages are:
- its sources, counterparts, unverified sources and dropped pins;
- the ask's anchor and binding;
- the tutor question's passage and given spans.

**Reads.** `reader.source_objects` and `reader.proposal_inbox` leave out every object kept from such a comparison (`hidden_source_objects`); `proposal_inbox` now takes the vault. The ⇄ marks, "you compared these on", the table's keep state (`compare_kept_state`) and the card also omit it. Reopen refuses with `comparison_withheld`, so no object, line, relation, statement or take derived from the comparison is returned. Ledger rows stay.

**Writes.** These check every contributing passage inside the transaction, before any write:
- Keep, also before writing a fork row;
- `keep_tutor`, before its ask row;
- adding a take, on the library and tutor paths alike.

`comparison_passages` now also reads the tutor question's passages. These cases refuse with `comparison_withheld`:
- a withheld passage;
- an unreadable comparison, ask or question;
- a tutor request that names no question;
- an unreadable predicate.

Earlier refusals of a kept comparison (`exam_material`) now use this one code. The UI shows any refusal's message, so no frontend change was needed.

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F1 | High | Comparison-derived prose survives | fixed (whole withholding) | `test_a_withheld_quotation_in_any_derived_field_is_never_returned[lines_text, lines_perspective, relation_statement, kept_relations, take]` |
| F2 | High | Keep ignores a withheld contributing anchor | fixed | `test_withholding_the_anchor_before_the_first_keep_refuses_it_with_no_writes`, `test_a_new_take_on_an_existing_keep_after_withholding_is_refused`, `test_a_tutor_keep_checks_its_question_passage_before_any_write`; fail-closed: `test_an_unreadable_comparison_is_withheld_whole` |

**Fail first on `9f182a473`'s `src`.** All 9 new tests failed.
- The three write tests and the tutor test failed on substance (`DID NOT RAISE`).
- The other six (the 5 field cases and the unreadable-comparison test) first stopped at the new `compare_kept_state(vault, …)` signature.
- A throwaway copy of the test file with the base signatures, deleted afterwards, showed all 6 failing on substance. The quotation leaked through reopen (relation statement, `kept_relations`, take) and `reader.source_objects` (the lines), and the take's text leaked from the unreadable comparison.

**Gate (round 3's).**
- `lint-imports`: 28 kept, 0 broken.
- `pytest -n auto` over the same 17 files: **488 passed**.
- `--durable-sqlite` on the two RW4d files: **61 passed**.
- `typecheck`: clean.
- vitest `src/screens/reader`: **61 files, 463 tests passed**.
- `frontend:build`: built.

**Rule note.** In rounds 2 to 4, small Python scripts that only rewrote source and test text ran without `env -i`. One read-only `sqlite3` query of `fixtures/migration_head_213` (column nullability) also ran without it. None imported LearnLoop or could reach a model or network, and no vault was opened. From round 4's test edits on, every such script ran under `env -i` with empty `HOME`, `CODEX_HOME` and `LEARNLOOP_CONFIG_DIR`.

## Fix round 5 (orchestrator rulings)

The verify of round 4 (Codex job `20261020-173613-n7Zkp3`, VERDICT: REOPENED) confirmed the RPC pin, its bypass mutations and the non-protection invariants. It found two Highs (F1, F2) and two Mediums (F3, F4). Fixed in `03f3ac0bc`. References were regenerated in `501ed27c6` (schema unchanged, head 213, 0 errors).

| id | severity | title | verdict | test |
|---|---|---|---|---|
| F1 | High | Reusing a comparison loses contributing provenance | fixed | `test_reuse_keeps_every_asks_provenance` (the verify's A/B reuse: a take through B, whose anchor is held out, is refused), `test_a_take_another_ask_added_stays_its_provenance_after_it_moves_on`, `test_a_tutor_take_on_a_learner_keep_is_hidden_once_its_question_is_held_out` |
| F2 | High | Completed comparison jobs return protected cached content | fixed | `test_a_comparison_job_read_after_withholding_returns_nothing_of_it` (the verify's sequence), `test_a_comparison_jobs_first_delivery_is_withheld_whole`; vitest "a comparison withheld whole says why, and shows nothing of it" |
| F3 | Medium | Unresolvable passage references fail open | fixed | `test_a_dropped_pin_naming_no_passage_withholds_the_comparison` |
| F4 | Medium | Remove bypasses the write refusal | **rejected** (orchestrator ruling) | `test_remove_on_a_withheld_comparison_answers_only_a_status` |

- **F1: the union across reuse.**
  - `comparison_passages` now reads the stored comparison's contributors and its own `caller_ref`: a tutor question, or for the Reader its reading.
  - It also reads every ask that refers to the comparison: one showing it now, its keep, a removal's snapshot, or a contributor its keep recorded. Each ask brings its anchor, binding and question. It also reads every tutor question whose request ran the comparison (`source_tool_calls.result_ref`), and the ask or question acting now.
  - Keep and adding a take record the acting ask or tutor question on the keep (`kept_json.contributors`, carried into removal snapshots and re-keeps). A later reuse cannot drop it: B's take stays B's provenance after B compares something else.
  - Deduplication and the per-row caller guards are unchanged.
  - One limit: an ask that was only *shown* a comparison, and later compared something else, no longer refers to it. It never wrote anything derived from the comparison.
- **F2: comparison jobs.** `reader.library_compare`'s job gets a deliver hook, RW4b's pattern (`deliver_comparison`). It runs at the first delivery and at every cached read through `reader.library_job`. A comparison withheld whole is refused with `comparison_withheld`: no table, keep state or take. Otherwise the keep state is read again. The library answer shows the refusal's reason (`failureLine`), as it does for `exam_material`.
- **F3: every contributor is resolved.** Each named passage must exist as a block of its reading (keys only, `source_block_fts.existing_spans`). Each ask, question, tutor request's question and reading must also exist. A malformed or unresolvable one withholds the comparison.
  - Consequence: a comparison whose dropped pins name a passage that no longer exists is never shown or kept.
- **F4 rejected.** Remove stays allowed on a withheld comparison. It is the learner's cleanup action. It appends supersessions and clears the keep, and writes no content derived from protected material. This matches open question 6 (the owner may want *remove* without reopening). Its response is only a status (`{askId, kept: null, removed: true}`), pinned by the test above. That test passes on `e664b701c` too: the response was already only a status.
- **RW4b's statement-reader pin, restored.** Round 3 broke `test_library_exercises::test_r2_no_handler_reader_module_or_s1_path_reads_an_exercise_statement_another_way`, which was outside my gate then. The cause was `exam_withheld` and `blocks_by_key` in `reader/source_objects.py`. The predicate is now read through `exam_material(...).withheld`, and passages are resolved through the keys-only `existing_spans`. The pin passes, and it is in the gate from now on.

### Fail first on `e664b701c`

- The 6 new fix tests and the updated `test_a_comparison_holding_exam_material_is_refused` ran on its `src` (`git archive`, `-o pythonpath=`): **7 failed**.
- The provenance-after-moving-on test failed first at its `contributors` check. A throwaway copy without that line, deleted afterwards, showed B's take leaking.
- The new vitest failed on the base frontend (1 of 16).

### Gate (round 4's, widened)

- `lint-imports`: 28 kept, 0 broken.
- `pytest -n auto`: **587 passed** over 28 files, round 4's 17 plus:
  - `test_library_exercises`
  - `test_reader_compare_table`
  - `test_compare_sources`
  - `test_sources_merge_composition`
  - `test_pinned_span_bridge`
  - `test_tutor_tool_requests`
  - `test_tool_results_withhold_answers`
  - `test_sidecar_serializer_snapshot`
  - `test_table_roles`
  - `test_registry_audit`
  - `test_instructional_layering`
- `--durable-sqlite` on the two RW4d files: **68 passed**.
- `typecheck`: clean.
- vitest `src/screens/reader`: **61 files, 464 tests passed**.
- `frontend:build`: built.

### Rule note

All Python run outside pytest in this round ran under `env -i` (edit scripts and the reference scripts), except one no-op `python3 -c "print()"` while searching. It imported nothing.
