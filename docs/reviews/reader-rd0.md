# Reader workbench v2, RD0: Foundations

Stage RD0 of `docs/specs/spec_reader_workbench_v2.md` (§16). Branch `reader/rd0-foundations`, based on main
`533495a5c9` (migration head 260, latest algorithm tag mvp-0.64). It takes **migration 262**
(`262_reader_workbench_foundations.sql`): the parallel D8 step takes 261, and whichever lands second renumbers its
migration and redoes the migration-head fixture (kept in its own commit here for that reason).

**What it delivers.** The storage, the write protocol, the read RPCs, the two derived span tables and the import
fences that RD1 (desk shell), RD3 (companion) and RD4 (scratchpads) build on. No UI, no client local store (the
RD-spike decides between IndexedDB and a SQLite outbox, §3.5), no change to the existing Reader's screens, no model
call, no config key, no kill switch, nothing on the phone, and no algorithm tag (§9 below).

## 1. What landed, per spec item

| Spec item | Where |
|---|---|
| §15.1's RD0 tables (ten) | `migrations/262_reader_workbench_foundations.sql`; roles in `db/table_roles.py` |
| The write protocol (§3.4, review F3) | `desks/protocol.py`, receipts in `db/stores/workspace_batches.py` |
| `desk.state`, `desk.apply` (the seventeen ops) | `desks/workspace.py`, `db/stores/desks.py`, `H:desks.py` |
| `pad.get`, `pad.list`, `pad.apply` (no submission) | `pads/blocks.py`, `db/stores/pads.py`, `H:pads.py` |
| The `ContentRef` model (review F14) | `desks/content_ref.py` (every window's content, a stack's entries, and `TargetedRef` for later stages) |
| The two DERIVED span tables, recipes, write-through, replayers, seeded fixtures (§7.6, review F5) | `substrate/passage_spans.py`, `db/stores/span_projections.py`, two replayers in `substrate/rebuild_orchestrator.py`, `tests/desk_helpers.py` |
| `passage.union_range` (§7.6) | `passage_union/union.py`, `H:passage_union.py` |
| `companion.history` and the exchange context (§8.5) | `companion/history.py`, `H:companion.py` |
| `checks.due_for` (read only, §12.6.1) | `intent/inline_checks.py`, `H:inline_checks.py` |
| The six import fences (§3.3) | `pyproject.toml` (seven contracts, one edited), `tests/test_reader_rd0_fences.py` |
| Rust passthroughs, `client.ts`/`dto.ts` | `src-tauri/src/commands.rs`, `main.rs`, `src/api/client.ts`, `src/api/dto.ts` |

## 2. Tables and roles

| Table | Role | Notes |
|---|---|---|
| `desks` | WORKFLOW | `version` counts applied ops; `position` is a client-minted fractional key (order: position, then id) |
| `desk_windows` | WORKFLOW | `slot` 0..n-1 among open windows; a pair is two windows sharing a slot (panes 0, 1; `active` marks the active pane); `kind` adds `pad_stack`; `spec_json` holds `{content}` or `{stack}`; soft close (`closed_at`) |
| `desk_op_receipts` | RECEIPT | keyed `(client_id, seq)`; `request_hash`, `result_json` (the stored reply); append-only by trigger |
| `pads` | WORKFLOW | `version` counts pad-level ops (title, keep); block edits are versioned per block |
| `pad_block_versions` | RAW_LEDGER | append-only by trigger; one chain per block, enforced in the schema (a unique index on `supersedes_id`, one first version per block, a trigger refusing a version that continues another block's chain) |
| `pad_block_anchors` | RAW_LEDGER | append-only link/unlink events; the newest per (block, reading, passage) stands |
| `pad_op_receipts` | RECEIPT | as `desk_op_receipts`, plus `pad_id` |
| `companion_exchange_context` | RAW_LEDGER | append-only; origin `live` or `backfill` |
| `question_event_spans` | DERIVED | one replayer (`question_event_spans`) |
| `learner_text_gap_spans` | DERIVED | one replayer (`learner_text_gap_spans`) |

None is classified for adaptive difficulty (`adaptive_difficulty/protected_tables.py`): a table outside its registry
is unreadable inside an AD operation altogether, which is what these tables should be.

## 3. The write protocol and its guarantees

Every write call carries `{client_id, seq, ops}`; `seq` is **one sequence per client across `desk.apply` and
`pad.apply`** (the spec's "strictly increasing per client"; one outbox). In `desks/protocol.py:apply_batch`, inside one
`BEGIN IMMEDIATE` transaction (`Repository.atomic`):

| Guarantee | Behaviour | Test (`tests/test_reader_rd0_protocol.py` unless named) |
|---|---|---|
| In order | a `seq` other than the client's last + 1 is refused (`seq_gap`, with `expected_seq`); nothing applied or stored | `test_a_batch_out_of_seq_order_is_refused_and_applies_nothing` |
| Exactly once | an applied `seq` returns the stored reply unchanged and applies nothing | `test_a_retried_batch_returns_its_stored_receipt_and_applies_nothing_again` |
| No silent reuse | the same `seq` with other ops (or on the other channel) is refused (`seq_reused`) | `test_a_batch_number_used_with_other_ops_is_refused`, `test_desk_and_pad_batches_share_one_sequence_per_client` |
| Conflicts return heads | an op whose expected head is stale is not applied; its result is `conflict` with the current head; the batch's other ops land | `test_a_stale_head_is_a_conflict_with_the_current_head_and_is_not_applied`, `test_blocks_chain_and_a_stale_edit_returns_the_current_head` |
| No partial op | each op runs in a savepoint; a refused op (`refused`, with a code) leaves none of its writes, and the batch still lands, so one bad op never blocks an outbox | `test_a_refused_op_leaves_no_partial_write_and_the_batch_still_lands` |
| Out-of-order replay converges | 1, 3 (refused), 2, 2 (receipt), 3 equals 1, 2, 3 | `test_batches_replayed_out_of_order_converge_to_the_in_order_state` |
| Batch and receipt in one transaction | the receipt is inserted in the transaction that applies the batch | by construction (`apply_batch`); the RPC errors in `tests/test_reader_rd0_rpcs.py` |

Client-minted ids (`desk_id`, `window_id`, `pad_id`, `block_id`, `version_id`, anchor `event_id`) let a client chain
ops in its outbox before the server answers; a create for an id that exists is a conflict naming the current head
(`test_a_create_for_an_existing_pad_or_block_conflicts`). Provenance is never laundered: quoted source, tutor and
figure blocks and lifted stubs are not editable (`not_editable`), and an ink block's edit becomes
`learner_correction` (`test_provenance_is_never_laundered`).

## 4. The replayers' recipes (`substrate/passage_spans.py`)

Rows name the reading they were made on; aliases across re-reads are applied when the union is read, so a re-read
never rewrites a derived row. No recipe uses `entity_source_links` to place a row.

`question_event_spans`, per `question_events` row:

| Context | Recipe | Role / quality |
|---|---|---|
| `reader` | the anchor in `note_id` (`span:<reading>/<span>`); from each `reader_answer_submitted` event naming the exchange (`payload.question_event_id`): its anchor and selection span ids, and its citations (by span id or `span:` locator). The passages the tutor was only *given* (neighbours, retrieved, explorable) are not rows. The payload is read by `exchange_places`, which `reader_dialogue.ask_provenance` now also reads through (its output is unchanged) | `selection`/`exact_selection`, `cited`/`citation` |
| `practice`, `feedback` | the item's source passages (`canonical_exercise`, `provenance.source_refs` with spans); with none, the item's LO | `context`/`source_context`, else `context`/`unanchored` with the LO |
| `library` | none | none |

`learner_text_gap_spans`, per `learner_text_gaps` row:

| Source kind | Recipe | Quality |
|---|---|---|
| `tutor_question` | the question event's recipe | as the event |
| `reader_formative` | the authored question's anchor spans, else its spans | `exact_selection` |
| `workbench_text` | the workbench session's `span_ids_json` (a stuck step, or a workbench help reply) | `source_context` |
| `learner_note` | the passages the learner linked the note to by hand (the learner's newest row per passage stands; a hidden link places nothing) | `exact_selection` |
| `stuck_answer`, `diagnosis`, `hint_feedback`, `lesson`, `external_chat` | the item's source passages | `source_context` |
| any | with no passage, one `unanchored` row with the gap's (or its item's) LO; with neither, no row | `unanchored` |

**Write-through.** `tutor_qa.ask_question` projects each new question event, `reader_dialogue.ask` projects the
exchange (and its cold-hint practice link) once its answer event is logged, and the gap pipeline (`pipeline.py`'s
ledger write and `jobs.py`'s two failed-row writes) projects each gap inside its transaction, in a savepoint. A failed
projection is logged and never fails the learner's act; the next rebuild writes the same rows.

## 5. The fences (`pyproject.toml`)

| # | Contract | Shape |
|---|---|---|
| 1 | `evidence-never-reads-desks-or-pads` | the workbench contract's shape: substrate, learner, attempts, scheduling, goals, diagnosis, placement, field, router, adaptive difficulty never import `desks`, `pads`, their stores, the receipts store or the veil sets (`intent.inline_veils`, declared for RD7); indirect imports refused |
| 2 | `graders-never-read-the-workbench-v2` | `attempts` never imports `desks`, `pads`, `companion`, `passage_union`, their stores, the veils or the goal lens (`curriculum.goal_lens`, declared for RD6) |
| 3 | `desks-stay-off-scheduling-and-evidence` | `desks` imports nothing from scheduling, evidence, the router or the plan; indirect refused |
| 4 | `passage-projections-are-read-only`, `passage-spans-reach-only-the-stores` | the union read imports no evidence writer; the span projection imports nothing above the stores (indirect refused). The goal lens joins the first in RD6 (a source module must exist) |
| 5 | `workbench-v2-calls-the-one-hint-service` | the Reader's contract stands; `desks`, `pads`, `companion` and `passage_union` get the same forbidden list |
| 6 | `notes-are-never-a-source-or-evidence` (edited) | its text names the difference (a pad is the learner's text emitted; a note stays never a source, input or evidence) and its sources gain `desks`, `pads`, `passage_union`, `companion` |

`tests/test_reader_rd0_fences.py` builds the import graph once and, for each, checks it holds, that every module it
names exists or is declared, and that one forbidden import added to a copy of the graph breaks it. Two guard lists
were extended deliberately: `tests/test_notes_never_read.py`'s files that may name the notes' tables (the span
projection's `learner_note` recipe; the union handler, which hands the linked notes to the read so nothing below the
sidecar reaches the notes' code), and the experiments and notebook-authoring contracts' package lists.

## 6. The reads

- **`passage.union_range`**: per span of one range (two passages, or two times over a transcript's `t=` cues):
  annotations (where each lands on this reading), linked pad blocks, exchanges by role and quality, the tutor's
  adjustments, gaps with their quality, passage links, figures (newest versions), the hosts of due checks (the
  commitment id only), linked notes, authored questions, exposure (times shown and when last, exam or held-out
  withholding); per section, its LOs and coverage (newest row per LO). Every row from another reading of the book
  carries `alias`: `exact`, or `needs_reanchor` for a same-place alias, never shown as the cited text.
- **`companion.history`**: exchanges by day (local), then desk, newest first, paged by cursor; lexical query; an answer
  withheld as worked help shows as the learner was shown it. An exchange with no context row is `origin: backfill`,
  no desk, its surface from its own context, and nothing is written for it. `record_exchange_context` is the live
  writer for RD3's `companion.ask`.
- **`checks.due_for`**: due "Check once" commitments as serving reads them (`intent_serving(...).due_checks()`), one
  row per learning object; host = the goal's latest path, first core section's first passage, else the section of the
  LO's primary passage; `provenance` is one word (`via`, `origin` or `source`), never an item, question or annotation.

## 7. Deviations from the spec, with reasons

1. **Migration 262, not the next free number**: the brief's instruction (D8 takes 261). On this branch alone the 23
   upgrade tests that assert `range(N, migration_head() + 1)` fail on the missing 261; they pass with an empty
   placeholder `261` present (verified, §10), and pass as they are once D8's 261 is under this, or after renumbering.
2. **Receipt columns**: `(client_id, seq)` keys, `request_hash`, `result_json`, `applied_at`, not `op_id`/`result`: the
   protocol numbers batches, and the stored reply is what a retry returns. Spec corrected (its own commit).
3. **One sequence per client across desk and pad batches.** Spec made explicit.
4. **Extra columns** the essential lists leave out: `desks.version`, `pads.version`, `desk_windows.active`, the
   `pad_stack` window kind, and the derived tables' `quality` and `learning_object_id` (§7.6 asks every row to carry
   its quality; an unanchored row keeps its LO). No `needs_reanchor` column: rows stay on their own reading and the
   union computes alias status when read.
5. **Replies list what the spec keys by data** (`versions`, `server_seq`, the union's `spans`): `versioned()` camelCases
   every key and would rewrite ids. Op results add `refused` (with a code) beside `ok` and `conflict`. Spec corrected.
6. **Module homes**: the derived span tables live in `learnloop.substrate.passage_spans` and the due-checks read in
   `learnloop.intent.inline_checks`, because `pyproject.toml`'s acyclic contract forbids package cycles: the Reader,
   the tutor and the gap pipeline write through the projection (so it cannot sit in `passage_union`, which reads the
   Reader), and `scheduling` imports `curriculum` (so the read cannot sit in `curriculum`). Spec corrected.
7. **No backfill rows in `companion_exchange_context`**: a RAW_LEDGER holds what was recorded; the history reads an
   absent row as `backfill`. `surface` is unconstrained text until RD3 names its surfaces.
8. **`erase_ink` and `pad.submit_block` are not built**: they need `ink_strokes` (RD8a) and `pad_block_submissions`
   (RD4). An `erase_ink` op fails validation today.
9. **"Tutor adjustments"** have no recorded signal; RD0 defines them as exchanges whose question the gap pipeline read
   as a misconception (`learner_text_gaps`, `tutor_question`, kind `misconception`). Honest, and empty until such a
   reading exists.
10. **No server-side duplicate-open check**: "the target is already on the desk" depends on rendered ranges, so it is
    the client model's rule (RD1).
11. **Opaque client JSON** (`view`, block `payload`) is returned through the camelCase conversion; RD4's payload
    shapes should list ids rather than key objects by them.
12. **Exposure without the seen-passage rows**: the union reports how often and when last a passage was shown
    (`source_exposure_events`) and whether it is withheld, not when it was first seen: `reader_seen_spans` keeps one
    reader on purpose (`tests/test_reader_seen_passages.py`, "a new reader fails here on purpose").
13. **Due-check hosts** come from the goal's latest path (its first core section, else the first section not
    `assumed` or `already_shown`), or, without a goal, from the section of the LO's primary passage
    (`entity_source_links`, relation `primary`): that names where the LO's content is, which is what a host is, and
    never places learner writing.
14. **Fence 4's goal lens** cannot be a source module before it exists; it joins in the stage that builds it.

## 8. Tests, and fail-first evidence

New: `tests/test_reader_rd0_migration.py`, `test_reader_rd0_spans.py`, `test_reader_rd0_protocol.py`,
`test_reader_rd0_reads.py`, `test_reader_rd0_rpcs.py`, `test_reader_rd0_fences.py`; helpers `tests/desk_helpers.py`,
`tests/reader_rd0_migration_helpers.py`. Edited: the 17 earlier upgrade tests (admit `RD0_ADDED_OBJECTS`, a scripted
edit beside each `JOB_PROGRESS_ADDED_OBJECTS`), `test_rebuild_orchestrator.py` (stale rows planted in the two new
derived tables, so the umbrella's clear is checked on them), `test_notes_never_read.py` (two allowed files),
`test_mobile_allowlist.py` (the eight RPCs pinned desktop-only), `test_architecture.py` (four registered SQL owners),
`test_notes_as_learner_text.py`, `test_reader_formative_texts.py`, `test_workbench_text_gaps.py`,
`test_hint_feedback_texts.py` (each test listing the tables a gap reading may change admits
`learner_text_gap_spans`, the gap's derived passage rows, with why; their "never written" lists are unchanged), and
`test_drop_dead_tables_migration.py` (its upgrade now stops at migration 260, so a later migration's objects stay out
of its "nothing else changed" diff; the assertions themselves are unchanged). No assertion was loosened: every
change admits exactly the new derived table or the new migration's objects, or scopes an upgrade to its own
migration.

**Fail-first.** Each behaviour below was broken on purpose in the worktree (one line replaced), its test run, and the
file restored (`git status` clean after):

| Broken | Test | Result |
|---|---|---|
| the `seq` gap check | `test_a_batch_out_of_seq_order_is_refused_and_applies_nothing` | 1 failed |
| the stored-receipt lookup | `test_a_retried_batch_returns_its_stored_receipt_and_applies_nothing_again` | 1 failed |
| the desk's expected-version check | `test_a_stale_head_is_a_conflict_with_the_current_head_and_is_not_applied` | 1 failed |
| the block's expected-head check | `test_blocks_chain_and_a_stale_edit_returns_the_current_head` | 1 failed |
| the per-op savepoint | `test_an_op_refused_after_its_first_write_leaves_none_of_its_writes` | 1 failed |
| the tutor's write-through | `test_a_practice_question_is_projected_as_the_tutor_records_it` | 1 failed |
| one replayer's registration | `test_every_table_has_the_specs_role_and_each_derived_one_a_single_replayer` | 1 failed |

The append-only triggers, the one-chain indexes and the same-block trigger are new schema: their tests
(`test_the_ledgers_and_receipts_refuse_update_and_delete`, `test_a_block_has_one_chain_no_second_child_and_no_second_root`)
fail at the base, where the tables do not exist.

## 9. Persisted meaning: the playbook's test

The playbook (`docs/algorithm-change-playbook.md`) applies "when scoring, scheduling, projection, or admissibility
semantics change", and its first step is: "Decide whether the change alters persisted meaning. If it does, add a new
immediate-successor `algorithm_version`." RD0 alters none:

- the new WORKFLOW, RAW_LEDGER and RECEIPT tables are read by nothing that scores, schedules, certifies, admits or
  writes evidence (fence 1 holds it by contract);
- the two DERIVED projections are read only by the union read and the companion history (display; RD7's protection
  later); no scoring, scheduling or evidence path reads them, and the existing derived state is unchanged (the golden
  rebuild test passes with the two new replayers in the umbrella);
- the write-through adds rows to the new derived tables only; the Ask, the tutor and the gap pipeline write exactly
  what they wrote before (their tests pass unchanged), and `ask_provenance` returns the same places;
- step 5 ("A new `DERIVED` table must have exactly one registered rebuild owner; a new `RAW_LEDGER` or `RECEIPT` table
  must never be cleared by replay") holds and is tested; step 6's rebuild-equivalence is extended
  (`test_the_live_projection_equals_a_rebuild_for_every_adapter`, the orchestrator's golden test).

So, as the spec's §15.3 row says ("none (new tables, a DERIVED backfill, a read-only union read)"), no tag is taken;
D8 keeps mvp-0.65. `tests/test_identity_pins.py` is unchanged and passes; no identity, cache key or structured prompt
moves.

**Undo.** Before any vault applies 262, revert the landing (the new tables stay inert where applied). After, the
tables are additive and nothing reads them but the new RPCs, so a revert of the code leaves them unread; no restoring
successor is needed because no persisted meaning moved.

## 10. Commands and results

(Filled from the worktree runs; each pytest run in a memory-capped scope through the scratch wrapper, `-n 1`.)

Each pytest run: `uv run --no-sync pytest -q -n 1 -p no:cacheprovider -m "not arc_close" <files>` through the scratch
wrapper in a `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=1G` scope.

| Command | Result |
|---|---|
| the six new test files, during the build | all passed (`test_reader_rd0_protocol.py` 18, `_reads.py` 6, `_spans.py` 8, `_rpcs.py` + `test_mobile_allowlist.py` 362, `_fences.py` + desktop RPC contract + e0/notebook isolation + hint service + notes 37) |
| `scripts/affected_tests.py --files <the 28 changed src files>` | 1,374 test files (more than 150) |
| the 254 of them whose names match `reader|tutor|text_gap|learner_gap|gaps|rebuild|replay|table_role|notes|rd0|ask|provenance|question|workbench|intent|desk|mobile` (migration and schema tests apart), in seven chunks of at most 40 | 4,181 passed, 6 skipped, 6 xfailed; 5 failed, each fixed or explained: the three gap-table enumerations and the seen-passage guard (fixed in `98aeed2372`), and `test_reader_ca2_fix_orchestrator.py::test_223_…` (the missing 261, below) |
| 33 further files that count table writes (`table_counts` and kin), plus the four fixed files and two RD0 files, after the fixes | 731 passed, 7 skipped; 1 failed (`test_drop_dead_tables_migration.py`, fixed in `98aeed2372`) |
| the 49 migration and schema tests, the 16 range-asserting files, `test_drop_dead_tables_migration.py`, `test_migrations.py` | 287 passed, 28 failed: every failure is `range(N, migration_head() + 1)` meeting the missing 261 ("At index …: 262 != 261") |
| the same 28 node ids with an empty `migrations/261_d8_placeholder.sql` present (removed after) | 28 passed |
| the 19 edited test files that assert no migration range | 528 passed |
| `tests/test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py` | 398 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `uv run ruff check` | All checks passed! |
| `uv run lint-imports --no-cache` | Contracts: 51 kept, 0 broken. |
| `uv run python scripts/check_gate_partition.py` | collected 32972: landing 32906 + arc_close 66 |
| `npm ci` (shared npm cache) | added 280 packages |
| `npm run typecheck` | exit 0, no errors |
| `npx vitest run --maxWorkers=2 src/api` | 2 files, 6 tests passed |
| `cargo check --offline --manifest-path src-tauri/Cargo.toml` | Finished `dev` profile |
| the migration-head upgrade (CLAUDE.md's procedure) | applied `[262]`; checkpoint (0, 0, 0); journal `delete`; integrity ok; foreign keys clean; 41 objects added; only `schema_migrations` rows changed |

Pins and goldens: `tests/goldens/structure.toml`'s `first_level_packages` 47 → 51 (the spec's four backend packages,
each its own package so the fences can name it); no identity pin, effective default or CLI snapshot moved;
`tests/cli_surface.json` untouched. `desktop_validate.py`'s counts stand (no new TypeScript file). No bug-ledger row:
no defect was found in existing code.

## 11. What the orchestrator runs on owner copies

On backup-API copies (`learnloop.db.copies`), never a live vault:

1. `apply_migrations` under `upgrade_allowance(UPGRADE_SCRATCH_COPY)`: applies `[262]` (with D8's 261 first if it has
   landed), then `PRAGMA integrity_check` ok and `PRAGMA foreign_key_check` empty; schema diff = the 41 objects of
   `RD0_ADDED_OBJECTS`.
2. Counts per vault: rows each replayer derives (`rebuild_question_event_spans`, `rebuild_learner_text_gap_spans` on the
   copy, or `learnloop rebuild --shadow --json` and the two replayers' `rows_processed`), split by quality
   (`SELECT quality, COUNT(*) ... GROUP BY quality` on each table), and how many exchanges and gaps produced no row.
3. Live versus rebuild: after the migration the live tables are empty (nothing wrote through before it), so the check
   is a rebuild, then one more rebuild, compared row for row (idempotence), and, after one new Reader Ask and one gap
   reading on the copy, the write-through rows compared with a rebuild's.
4. `passage.union_range` over one section of each vault's most-read reading, and `companion.history` first page, timed.

## 12. What I did not verify

- Anything on owner copies (above), the packaged app, or a real client outbox (the RD-spike's).
- The span recipes against real `reader_answer_submitted` payloads beyond the shapes the code writes today and the
  test seeds (older payloads without `question_event_id` produce only the anchor row from `note_id`).
- Concurrency between two sidecars applying batches for one client (one learner; `BEGIN IMMEDIATE` serialises them).
- The landing gate, the whole suite, `npm test` beyond `src/api`, `npm run frontend:build`, and the durability lane.

## 13. After D8 landed (merge of main `544a6d529a`)

Migration 261 (`attempt_application_order`, mvp-0.65) is now under 262, so the number has no gap and deviation 1
above no longer applies. The merge took main's 261 fixture and redid the 262 upgrade on it (applied `[262]` only;
checkpoint (0, 0, 0); journal `delete`; integrity ok; foreign keys clean; 41 objects; only `schema_migrations` gains a
row; 7,704,576 bytes); the earlier upgrade diffs admit `RD0_ADDED_OBJECTS` beside `APPLICATION_ORDER_ADDED_OBJECTS`.
The diagnosis journey golden's `text_prerequisite` case gains its two derived passage rows (one
`question_event_spans`, one `learner_text_gap_spans`, both unanchored; nothing else moved) and `golden_json_lines`
rises by those 24 lines. Results after the merge:

| Command | Result |
|---|---|
| the 28 range-asserting upgrade tests | 28 passed |
| the migration set, 261's test, the rebuild orchestrator, table roles, the six RD0 test files | 396 passed |
| `tests/test_architecture.py` alone / `tests/test_test_layout.py` alone | 18 passed / 3 passed |
| identity pins, structure ratchets, public tip guards | 374 passed |
| the row-recording goldens (grade application, diagnosis journey, due queue, synthesis tail) and the ratchets, after regenerating the one case | 67 passed |
| `ruff check` / `lint-imports --no-cache` / `check_gate_partition.py` | All checks passed! / 51 kept, 0 broken / collected 33069: landing 33003 + arc_close 66 |
| `npx vitest run --maxWorkers=2` / `npm run frontend:build` | 328 files, 3656 tests passed / built |

