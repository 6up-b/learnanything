# Reader workbench v2, RD4a: scratchpads, the backend half

The backend half of stage RD4 of `docs/specs/spec_reader_workbench_v2.md` (§10, §15, §16's RD4 row). Branch
`reader/rd4a-pads-backend`, from origin/main `b495b1e67f` (migration head 265, latest tag mvp-0.67). RD4's frontend
(sticky tabs, the live editor, gutter marks and hover cards, sketch tools, arrange and split, the pad menu) follows
separately; this step builds what it calls and the persisted-meaning part. The tag's own record is
`docs/reviews/algorithm-mvp-0.68.md`.

**What it delivers.** Migration 266 (the five RD4 tables, `pad_text` in both gap tables, two pad reversals); the
emission contract under mvp-0.68 (pad text is learner text through `learnloop.pads.emission` alone); `pad.submit_block`
handing a frozen block version to the existing attempt and teach-back entry points; carried questions with their
labels and the desk drain's read; proposals and labels with a model-free generator from the passage links; the Rust
passthroughs and typed `client.ts`/`dto.ts` entries. No UI, no config key, no kill switch, no prompt text changed,
nothing on the phone, no live model call (fakes only).

## 1. What landed, per spec item

| Spec item | Where |
|---|---|
| §15.1's RD4 tables (five) and §15.2's `pad_text` | `migrations/266_reader_workbench_pads.sql`; roles in `db/table_roles.py`; writer `db/stores/pad_ledgers.py`, reads `db/stores/pad_reads.py` |
| The emission contract (§10.11, review F4) | `pads/emission.py`, `pads/quoting.py`; the pipeline's adapter `diagnosis/text_gaps/sources.py:pad_text`; registration in `diagnosis/text_gaps/contract.py` |
| Submitting a block (§10.9) | `pads/submission.py`; hand-off in `H:pads.py` (`pad.submit_block`) |
| Carried questions and the drain (§10.12) | `pads/carried.py`, `pads/drain.py`; the union read's `carried` rows (`passage_union/union.py`) |
| Proposals and labels (§10.6, §14) | `pads/proposals.py` |
| Rust passthroughs, typed client | `src-tauri/src/commands.rs`, `main.rs` (seven commands); `src/api/client.ts`, `src/api/dto.ts` |
| Desktop only | `tests/test_mobile_allowlist.py` (`READER_RD4A_RPCS`, pinned to `PAD_RD4_RPCS`) |

## 2. The RPCs

Every params model is `extra="forbid"` and every reply `versioned` (`tests/test_reader_rd4_rpcs.py`). None is on the
phone allowlist.

| Method | Input | Reply | Notes |
|---|---|---|---|
| `pad.submit_block` | `{submissionId, blockId, versionId, as: attempt\|teach_back, target: {sessionId, practiceItemId, assessmentContractVersionId?, schedulerCandidateId?, latencySeconds?, activeSeconds?}}` | `{submissionId, blockId, versionId, as, practiceItemId, attemptId, teachBackId, duplicate, entry}` | Idempotent by `submissionId` (§3 below). `entry` is the entry point's own reply on the call that handed the text over, `null` on a retry |
| `pad.proposals` | `{padId}` | `{padId, proposals: [{proposalId, blockId, blockVersionId, foundBy, target, reasonMd, quote, judgmentRef, createdAt, current, labels, shown}]}` | One per standing block's current words at most; `shown` false once dismissed or "not this"; `target` is `{content: ContentRef, target: {span_id}}`, keys as stored |
| `proposal.label` | `{labelId, proposalKind: pad_proposal\|promoted_row, proposalId, label: opened\|not_this\|dismiss\|ignored}` | `{labelId, applied, at}` | Idempotent by `labelId`; a pad proposal must exist, a promoted row's id is RD5's (not checked) |
| `pad.drain` | `{deskId, day?}` | `{deskId, day, pads: [{padId, kind, title, kept, version, firstLine, lastLine, carryCandidate, updatedAt}]}` | Read only: the pads homed on the desk that changed that local day; keep/leave are `pad.apply`'s `keep`/`unkeep`, carry is `carried.carry` with origin `drain` |
| `carried.carry` | `{carriedId, text, originKind: block\|selection\|note\|drain\|typed, originRef?, anchor?: {extractionId, spanId, anchor?}, deskId?}` | `{carried, created}` | Idempotent by `carriedId` (another request under the same id is refused, `carried_id_reused`); one `carried` event |
| `carried.list` | `{which?: open\|closed\|all, deskId?, cursor?}` | `{carried, shelfLimit, cursor}` | Longest carried first; `shelfLimit` is the spec's attention limit of three, returned so every client applies the same one |
| `carried.mark` | `{eventId, carriedId, event: fruitful\|not_now\|let_go\|surfaced\|ignored, expectedVersion?, ref?}` | `{carried, applied, conflict}` | A label names the version it expects (stale: `conflict`, nothing written); `surfaced` and `ignored` are notices (logged, no state change); idempotent by `eventId` |

`pad.get`'s blocks gain `submissions` (the "submitted · …" tag, `current` false for an earlier version);
`passage.union_range`'s spans gain `carried` (questions still carried beside the passage, through span aliases like
every other row). `pad.apply` now emits the committed blocks' words and computes their proposals after its batch
commits; neither can fail the batch.

## 3. Submitting a block

`pads.submission.prepare` checks and freezes; the handler hands the text over; `pads.submission.record` writes the row.

- **Only the learner's own words**: `text`/`note` of provenance `learner`, `ink` of `ink_transcription` or
  `learner_correction`, a `check_cell`'s answer (its body; the check's prompt is its payload). Else
  `not_learners_words`; a blank block `empty_block`.
- **No quoted text**: a whole sentence of one of the pad's quote blocks, or of a passage the block (or the quote it is
  a note under) is linked to, inside the block (`pads.quoting`) is refused, `includes_quote`, with the spec's words
  "this includes quoted text · submit only your own words".
- **"My answer to <item>"** only from the item's problem pad (its workbench session's item) or a check cell naming
  it (`not_an_answer`). A teach-back from any of the learner's blocks; the entry point refuses a non-teach-back item.
- **The current words**: a version that is not the block's current wording is `stale_version` with the head.
- **Attempt**: `submit_attempt_on` (the one submit implementation, as RW2's workbench uses it) with the frozen text,
  the item's answer-box attempt type, `entry_surface = "desktop_scratchpad"`, `hint_window_fold=True` (the help
  shown on this item in this session is folded in by the server, so worked help makes it assisted exactly as on the
  practice screen) and the attempt path's own idempotency key `pad:<submissionId>`.
- **Teach-back**: `submit_teach_back_turn` with the text as the opening explanation; `teachBackId` is the
  conversation's id (the attempt that finishes it carries it as its agent run). A conversation this submission
  already opened (its first learner turn is the block's text) is found on a retry and nothing is handed over again;
  another teach-back of the item under way in the session is refused (`teach_back_in_progress`), since its next turn
  would take the block as an answer.
- **Idempotent**: the row is keyed by the client-minted `submissionId` with a request hash; the same request returns
  the row (`duplicate`), another request under the id is `submission_reused`.

## 4. What waits for RD5 and for the frontend

- **RD5 (`passage.promoted`)**: proposals found by `search_spans` and correspondents ("<video> ▶ <time> says this
  another way"), their `verify_spans` confirmation, and ranking by the learner's history for the object. RD4a's
  generator uses the cue judge's passage links alone: a block linked to a passage that a link ties to one of the
  learner's open problems gets the best other passage (by the link's `pick_rank`) tied to the same problem. A block
  with no linked passage gets no proposal until RD5. Labels on promoted rows are already stored
  (`proposal_kind = promoted_row`).
- **The frontend (RD4b)**: the gutter marks and hover cards (from `pad.proposals`, `pad.get`'s `submissions`, the
  union's `carried`); the ⓘ popover's words; logging `ignored` for a marker passed by and `surfaced` for a carried
  question shown beside a passage (the client decides when); muting proposals per pad (a view preference in the
  window's view, never sent: the generator computes the same rows either way); the "? carry" chip; the drain panel.
- **RD7**: "a block written during an open administration is emitted only after it closes" (§10.11) needs the
  administrations, which do not exist yet.
- **RD10**: carried questions resurfacing beyond the union read's margin rows.

## 5. Deviations and open design questions, with reasons

1. **Carried questions do not inform the router or the Teacher yet** (spec §10.12 "Effect on the router", D9). The
   spec names `router_learner_preferences` with `propensity_kind='none'`, but that table has no such column, its
   `chosen_kind` is one of the router's six kinds (another question, review, something new, read, learn this,
   stop), and its rows feed IH4's choice model and every boundary's identity (`router_objective.preferences.mark`).
   Writing a carried question there would change router identities and the choice model's counts, a router change
   outside this stage. Options for the owner: (a) a `carried` kind in the preference ledger with its own handling in
   the choice model and the Teacher's sources (a router successor); (b) carried questions as a separate learner-pick
   sensor the router and Teacher read beside preferences; (c) Teacher context only (no routing effect) until the
   router objective's offline exploration can value it. RD4a stores everything any of these needs.
2. **The emission rides the gap job's payload.** Fence 1 keeps the gap pipeline off every pad module, so the pads'
   emission freezes a snapshot (the words, transcribed or not, quoted or not, the linked passages, the problem pad's
   workbench session) into the `pad_text` job's payload (key `db.stores.learner_gaps.PAD_TEXT_SNAPSHOT`), and the
   pipeline's adapter reads it there. The gap row keeps its passages in `detail_json.pad_text`, so the span recipe
   (`substrate.passage_spans`) needs no pad table either.
3. **One extra rebuilt table**: `learner_text_gap_reversals` gains `superseded` and `retracted` (§15.2 names only the
   two gap tables). The spec's "marked superseded" and "retracts its gaps from routing" need a reversal; every reader
   that leaves out a reversed gap already leaves out any reversal, and reusing `unlinked` (a note's) would mislabel
   them in reports.
4. **Quoted text is never read for a gap.** "Emitted as 'quoted by the learner', not as the learner's belief": the
   block is queued and its gap row records the words (for the companion and the Teacher) with kind `none`, action
   `none`, reason `quoted_by_learner`, and no model call. Reading it and then not acting would still leave a named
   misconception that the learner context and the router card read by kind.
5. **The reader's task for pad text is the note reader's** (`READER_NOTE_TASK`, `learner-gap-reader-note-v1`): free
   writing beside what the learner studies, never an answer, never graded. No prompt text changed; the Decider's
   state gains one sentence naming the new kind (`judges.kind_state`). A pad-specific task would be a prompt change of
   its own landing.
6. **Pads are emitted at the batch's commit, not on a separate "left the pad" event**: the client flushes on idle,
   blur, leaving a pad and closing (§3.5), which are exactly the spec's emission moments.
7. **The quote check's floor** (`pads.quoting.MIN_SENTENCE_CHARS = 12`): a sentence shorter than twelve normalized
   characters never counts as copied (so "yes", or a number the passage states, is not refused); the same floor the
   tutor's answer-leak measure uses for a verbatim hit.
8. **`entry_surface = "desktop_scratchpad"`** for a submitted block's attempt (a label; the column has no CHECK).

## 6. Tests, and fail-first evidence

New: `tests/test_reader_rd4_migration.py` (6), `test_reader_rd4_emission.py` (19), `test_reader_rd4_submission.py`
(9), `test_reader_rd4_carried_and_proposals.py` (8), `test_reader_rd4_rpcs.py` (21); helpers
`tests/reader_rd4_migration_helpers.py`, `tests/reader_rd4_helpers.py`. Edited: the earlier migrations' upgrade diffs
(admit `RD4_ADDED_OBJECTS`; AD2+AD3's 218 diff also `RD4_ALTERED_TABLES`), `test_teacher_te2_migration.py` (undoes
266's schema before its own downgrade and compares with the head as 248 left it), `test_mobile_allowlist.py` (the
seven RPCs pinned desktop-only), `test_architecture.py` (the new SQL owner `db/stores/pad_ledgers.py`), and the tag's
mechanical moves (the tag's record). No assertion was loosened.

**AD's material view** (`adaptive_difficulty/protected_tables.GAP_SOURCES`, `material_view._gap_source_withheld`):
`pad_text` is listed and withheld, like a note (AD reads no pad). `test_ro2_history_protection.py`'s registry test
caught the unlisted kind, as it is written to.

**Fail-first.** Each behaviour below was broken on purpose in the worktree (one line replaced by
a scratch script), its test run, and the file restored (`git status` clean after):

| Broken | Test | Result |
|---|---|---|
| supersession (every reversal `retracted`) | `test_a_correction_supersedes_the_gap_read_from_the_old_words` | 1 failed |
| retraction (every reversal `superseded`) | `test_a_removed_block_retracts_its_gaps` | 1 failed |
| quote blocks emitted | `test_quotes_sketches_cells_and_stubs_emit_nothing` | 1 failed |
| quoted text read for a gap | `test_a_quote_pasted_into_the_learners_block_is_kept_but_never_read_for_a_gap` | 1 failed |
| a superseded queued reading not set aside | `test_words_superseded_before_they_were_read_are_set_aside_unread` | 1 failed |
| the tag's gate | `test_below_the_tag_a_pad_emits_nothing_and_the_upgrade_queues_its_standing_words` | 1 failed |
| the span recipe for `pad_text` | `test_the_passages_a_block_is_linked_to_place_its_gap_and_live_equals_rebuild` | 1 failed |
| the quoted-text refusal | `test_what_is_refused` | 1 failed, 2 passed |
| the submission's idempotency | `test_a_retry_hands_nothing_over_again_and_a_reused_id_is_refused` | 1 failed |
| a stale label's conflict | `test_three_labels_each_logged_and_a_stale_label_is_a_conflict` | 1 failed |
| `pad_reads` left out of fence 1 (ledger RD4a-1) | `test_fence_one_refuses_the_pads_read_and_ledger_modules_too` | 2 failed (its `pad_reads` cases), 2 passed |

The migration's tests fail at the base, where the tables do not exist.

## 7. Commands and results

Each pytest run: a script with explicit targets, `uv run --no-sync pytest -q -n 1 -p no:cacheprovider`, through the
scratch wrapper (`env -i`, empty `HOME`/`CODEX_HOME`, isolated config dir) in a `systemd-run --user --scope -p
MemoryMax=3G -p MemorySwapMax=1G` scope.

| Command | Result |
|---|---|
| `uv sync --extra dev --extra mobile --extra tui --extra notebook`, `uv pip install pypdfium2==5.14.0` | installed (5.14.0 replaced 4.30.0) |
| Head fixture upgrade (CLAUDE.md's procedure) | applied `[266]`; checkpoint (0, 0, 0); `delete`; integrity ok; foreign keys clean; 28 objects added, three definitions changed (the rebuilt tables' CHECK), rows changed only in `schema_migrations`; header 1/1; no companions |
| The 59 migration and schema files (each `range(n, migration_head() + 1)` file, the diff files, table roles, the rebuild orchestrator) with the new fixture | 2 failed (the 218 diff's changed set, the TE2 downgrade), 363 passed; after the two edits, those files and the new migration test: 20 passed |
| The tag commit's 49 files (the moved successor files, identity pins, effective defaults, CLI snapshot, journey golden, upgrades, placement, the mastery seed's), `-m "not arc_close"` | 1 failed (the mastery seed's own version set), 1480 passed, 12 skipped; fixed in the tag commit: 1 passed |
| The five new test files, during the build | 19, 9, 8, 21, 6 passed |
| `scripts/affected_tests.py --files <the 21 changed and new src files>` | 798 files (more than 150) |
| The 141 of them whose names match `reader_rd|text_gap|learner_gap|gaps|notes_as|note_source|rebuild|replay|table_role|pad|desk|workbench_text|mobile_allowlist|golden|diagnosis_input_provenance|passage|union|source_kinds|hint_feedback_texts|formative_texts|stuck_prompt|sidecar_teach_back|teach_back_entry|journey|synthesis_tail|due_queue|grade_application|architecture|router_card_reading|learner_context|companion|sqlite_file|structure_ratchet|identity_pins|context_load|sidecar_context|post_attempt_worker|vault_open|reconcile`, united with every one that counts table writes or names the gap tables (`table_counts`, `row_delta`, `_database_changes`, `GAP_TABLES`, `learner_text_gap`), in four chunks of at most 40, `-m "not arc_close"` | 721 passed, 2 xfailed; 1412 passed; 1 failed, 969 passed (AD's gap-source registry, fixed: `pad_text` withheld); 326 passed |
| AD's guard and registry set, the RD0 fence/span/read files and the RD4 files after the AD fix | 344 passed |
| Fail-first (§6) | as tabled; tree clean after |
| `test_identity_pins`, `test_structure_ratchets`, `test_effective_defaults_golden`, `test_cli_help_snapshot`, `test_kill_switches`, `test_sqlite_file_copies`, `test_public_tip_guards`, `test_retired_config_identities` | 435 passed |
| `tests/test_test_layout.py` alone / `tests/test_architecture.py` alone | 3 passed / 18 passed |
| `uv run ruff check` / `uv run lint-imports --no-cache` | All checks passed! / Contracts: 52 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 33404: landing 33338 + arc_close 66 |
| `npm ci` (the shared npm cache) / `npm run typecheck` | installed / exit 0, no errors |
| `npx vitest run --maxWorkers=2 src/api` | 4 files, 57 tests passed |
| `cargo check --offline --manifest-path src-tauri/Cargo.toml` (the shared cargo cache) | Finished `dev` profile |

No row-recording golden moved (journey, grade application, synthesis tail, due queue: none of their journeys writes a
pad, and no new table gains a row in them); no identity pin moved but the tag's nine; the structure golden needed no
change; `desktop_validate.py`'s counts stand (no new TypeScript file).

## 8. What I did not verify

- The teach-back entry end to end with a naive-student provider (the tests replace `submit_teach_back_turn` with a
  recorder; the conversation guard reads a real checkpoint).
- Anything on owner copies (the orchestrator's lane, in the tag's record), the packaged app, the landing gate, the
  full suite, the durability lane, `npm test` beyond `src/api`, `npm run frontend:build`.
