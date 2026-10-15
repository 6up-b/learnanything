# Exam protection by extraction identity

**Stage:** exam-protection-identity (the fourth redesign round on exam protection across readings), branch
`fix/reread-safety`, base `808dc9c01`.
**Commits:** `542adc886` (the change, its tests and the head fixture), `132e4cd78` (DB and config references),
`67e5f8a5f` (two tests in the durability lane), `535210d03` (scopes sealed to their reading), `daedc8b77`
(references again, the Pipeline Map), `90f203c4b` (signals read from the cache on a database not yet migrated, found
by the first full-suite run), `3a099b4eb` (references), and this record.
**Why:** the Codex verify of the protection redesign (`9b933cc21..808dc9c01`) confirmed F1 and F11 fixed, reopened
F2 and found F12-F15 (all but F15 High). Each one came from a mark whose place was inferred: a scope read on "the
first completed reading", a cached inventory's mutable binding, a confirmation that named no reading, signals read
only on the pinned revision, a protection filter behind a reading-order setting. The orchestrator's decision,
consistent with the owner's fail-closed and one-authority rules: every protection mark is bound to the immutable
identity of the extraction it was made on and is resolved only there.

## The rule as built

The one predicate is still `content/sources/exam_material.py` (its docstring, rules 2-4, is the normative text).

**Every kind of mark records the extraction (and revision) it was made on.**

| Mark | Where its reading is recorded | Written by |
|---|---|---|
| Source-set exam scope (`role_override: exam`) | `SourceSetMember.scope_extraction_id` and `scope_revision_id` in `sources/source_sets.yaml` (owner question A, decided this way; omitted from the YAML when not recorded), sealed to the scope's entries by `scope_seal` (`vault/scope_seal.py`: a hash of the book, the reading and every entry's unit id and role override; the pin is left out, so a refresh may advance it) | every writer of a scope: `vault.writer.upsert_source_set` seals a member that names its reading, keeps the sealed reading of an unchanged scope that a writer re-sends without it (an older desktop, a hand-built payload), and drops it for a changed scope or one re-sent under a seal its content no longer matches; `revision_refresh._advance_membership` and source deletion keep the whole member; the automatic build and quick add record the reading they chose units on; `learnloop source-set add --reading`; the sidecar's `upsert_source_set` / `get_source_set` (`scopeExtractionId`, `scopeRevisionId`, `scopeSeal`); the desktop's AddToCollection records the outline's reading and re-sends other members as received |
| Held-out selection mark (`held_out_evaluation`) | `exam_paper_metadata.marks_made_on` = `{extraction_id, revision_id}` in the extraction's unit selection | `save_unit_selection` with explicit exam use modes, the owner's marking |
| The owner's "Mark exam material on this reading" | the same key, plus `protection_marked` (now with the extraction, revision and proposal hash) | `exam_marking.mark_exam_material` |
| Held-out inventory signal | `source_held_out_signal_marks` (migration 225, RAW_LEDGER, append-only by trigger): the reading and revision the model run read, the unit, the role it ran under, the sorted span ids | `Repository.insert_unit_inventory` for a model run on its extraction, in the same transaction; never for a reuse (`reused_from_inventory_id`) |

The selection's reading is recorded explicitly by the writers that make marks, never stamped by the repository: a
path that copies modes from another reading's selection (with or without its metadata) produces marks that name no
reading, or another one, and those are ambiguous. `carry_selection` and `reanchor_selection_to` carry no held-out
mode, owner's mark or `marks_made_on`.

**Resolution.** A mark protects exactly the units or spans of the extraction it names, resolved there by unit id (a
unit id that does not resolve there holds that reading out whole). Nothing is rebound or inferred from positional unit
ids, creation order or content matching:

- A book is *protected* when any extraction of any revision carries any mark or signal (exact, ambiguous or
  unbound). An unprotected book is untouched.
- Marks and signals are found across every revision and extraction of the book, whatever the source sets pin or
  contain now (F14).
- A signal counts as protection when it was made under an exam role, on a book that is exam material now (an exam
  member of any set, an outline exam pick), on spans an exact exam scope names on the same reading, or (role not
  recorded: every backfilled row) on a book with a legacy exam scope. A textbook inventory whose model flagged
  something held out protects nothing, exactly as before.
- A reading is *marked exactly* by an owner's exact mark on it, unless an ambiguous mark may also be about it, in
  which case only the owner's marking action marks it. Where a book has no owner's mark at all, a reading with
  held-out signals of its own is marked by them. Every other extraction of a protected book is withheld whole, as
  held-out material (`unmarked_reading`).
- A legacy mark that names no reading it can be on is *ambiguous* (`SourceMarks.ambiguous`): a scope with no
  `scope_extraction_id`, one whose seal no longer matches (its units or its reading edited in `source_sets.yaml`
  outside the writer: the F12 hand edit, now with the field present), or one naming an extraction that does not
  exist, belongs to another book or to another revision than it says, may be about any reading; a selection whose
  marks have no `marks_made_on` naming it may be about its own reading. The book is protected and every reading such a mark may be about is withheld whole
  (`ambiguous_mark`) until the owner marks it. The card says why in plain words ("You marked exam material in this
  book before LearnLoop recorded which reading you marked it on…", `exam_marking.AMBIGUOUS_DETAILS`), doctor's
  `source:reading_held_back` says the same, and both offer "Mark exam material on this reading". The marking's
  suggestion includes the legacy marks' own units (by unit id on their reading, a legacy scope by id on every
  reading): it is shown by name and is never an authority.
- Inventory reuse never transfers marking authority and never erases the origin's signals (F2): protection reads the
  ledger, never the cache row a reuse rebinds. A reused inventory bound to another reading writes no ledger row.
- The owner's confirmation is bound to the reading and the proposal it showed (F13). `mark_plan` returns
  `proposal_hash` (the book, the reading and its revision, the units held out, where they were suggested from, and the
  reading's own marks as they stood). `mark_exam_material(extraction_id=, proposal_hash=)` finishes an owed carry-over,
  then, inside one `BEGIN IMMEDIATE` transaction, recomputes the plan and writes only when both match: exactly the
  confirmed units, the owner's mark and the reading they name, in one row write. Otherwise it raises
  `StaleMarkConfirmation` with the fresh plan, and the sidecar returns that confirmation (prefixed "This reading
  changed since you looked, so nothing was marked yet. Check it again:" when the call named one) and writes nothing.
  A confirmed call that names no confirmation (an older desktop) also gets a fresh confirmation.
- Every consumer applies the predicate whatever the settings (F15). The plan's reading step reads it in either order:
  `plan.reading_from_furthest` orders the step only, and a predicate that cannot be read offers no step. The other
  consumers listed in item 6 were checked and already read it unconditionally: find_sources' pool filter
  (`exam_withheld`, every policy and scope), `scope_for`'s post-attempt, assisted and teaching scopes, compare's and
  the tutor's pin filters, the leakage gate (practice generation and PF), the Reader's refusals
  (`reader_requests`, `reader_dialogue`, `tutor_qa`, the sidecar's quick and passage checks), the guide's
  `held_out_sections`, and margin cues. The library scope itself still excludes nothing (the sources merge's "found,
  then withheld" transparency, pinned by `test_sources_merge_composition`); every caller of it filters each hit.

Kept from the redesign, unchanged: F1 and F11's fixes (no carrier: a reading is never protected by content, alias or
label matching), selection saves preserving marks (`{}` clears), `carry_selection` stripping modes and the owner's
mark, build signals never releasing an owner-protected reading, page-repair children withheld, exam-scoped members
kept pinned on refresh.

## The verify's findings

| # | Sev | Finding | Fix | Tests (`tests/test_exam_protection_identity.py`) |
|---|---|---|---|---|
| F2 | High | A cache hit re-anchored A's held-out signal onto B's exact copy and bound the inventory to B: B counted as marked and its fragment copies y3, y4 were released (Reader refusal `[]`); with an exam scope on A, the rebinding removed A's own signal from A's partition | the ledger; reuse writes none | `test_f2_a_reused_inventory_never_releases_duplicate_or_fragment_copies`, `test_f2_reuse_never_erases_the_origins_signal[exact_scope, exam_member]` |
| F12 | High | Question A not fail-closed: a hand-edited scope naming B's reversed `u2` was read on A (A's Theory protected, A's question released, and `scope_for(post_attempt, library)` reopened it); an older interrupted extraction completing after a newer one became "first" and took the scope | `scope_extraction_id`; legacy and unplaceable scopes ambiguous | `test_f12_a_legacy_scope_over_reversed_unit_ids_withholds_every_reading`, `test_f12_a_scope_stays_on_its_reading_when_an_older_one_completes_later`, `test_f12_a_legacy_scope_never_follows_creation_order`, `test_f12_an_exact_scope_protects_the_units_of_the_reading_it_names`, `test_a_scope_naming_a_reading_it_cannot_be_on_fails_closed[extNowhere, other_source, wrong_revision]` |
| F13 | High | The card proposed B's u2; C completed before the owner confirmed; `confirmed=true` marked C with an empty selection and released it whole | confirmation bound to reading and proposal hash, applied atomically | `test_f13_a_confirmation_made_for_another_reading_returns_a_fresh_one` (both with no binding and with B's), `test_f13_a_changed_proposal_returns_a_fresh_confirmation`, `test_f13_the_confirmed_proposal_is_applied_exactly_and_bound_to_its_reading` |
| F14 | High | Refresh advanced an exam member from R1 (signal on A) to R2; signals were read on R2 only: gate `[]`, Reader refusal on R2's question `[]` | discovery across every revision, independent of membership | `test_f14_a_refresh_never_drops_signal_only_protection`, `test_f14_a_signal_made_on_an_exam_unit_protects_after_its_member_leaves` |
| F15 | Medium | With `plan.reading_from_furthest = false` the plan offered B's Theory on a reading held back whole | the predicate in either order | `test_f15_no_reading_order_offers_a_held_back_reading[True, False]`, `test_f15_the_plans_reading_step_never_offers_held_out_material_in_either_order[u4, dl1]` (through `set_plan_minutes`) |
| legacy | | a legacy mark fails closed and says so | ambiguity | `test_a_legacy_held_out_mark_withholds_every_reading_until_marked_exactly`, `test_a_held_out_mark_copied_onto_another_reading_is_never_exact`, `test_doctor_names_a_legacy_mark_plainly`, `test_an_exact_mark_never_resolves_a_reading_a_legacy_mark_may_also_be_about`, `test_an_exact_held_out_mark_under_a_legacy_scope_waits_for_the_owners_marking` |
| round trip | | the scope's reading through `source_sets.yaml` writers | | `test_the_scopes_reading_round_trips_through_the_writers` (writer and seal, re-send without the field, changed scope, refresh pinned and advanced), `test_the_scopes_reading_round_trips_through_the_sidecar` (camelCase out and back, seal kept); vitest `AddToCollection.test.tsx` |
| hand edit | | a scope edited in `source_sets.yaml` under its seal | seal | `test_a_scope_edited_outside_the_writer_names_no_reading[units, reading]` (no unprotected copy; a writer re-sending it does not re-seal it) |
| unaffected | | an unprotected book | | `test_a_textbook_with_held_out_signals_made_as_a_textbook_is_unaffected`, `test_reread_safety.py::test_redesign_an_unprotected_book_is_unaffected`; the owner's copies below |
| 225 | | the ledger's backfill | | `test_migration_225_backfills_each_signal_on_the_reading_it_was_made_on` |

**Fail-first.** The new file was run on `808dc9c01` before any change: **22 failed, 3 passed** (the passing three are
the controls: U4's order, which already filtered; the plan's U4 order; the unaffected textbook). The failures are the
verify's reproductions, failing on behaviour:

- F2: `[('extPB','y3'), ('extPB','y4')]` unprotected; A's signal gone after the reuse; B no longer withheld.
- F12: `[('extXA','x1')]` unprotected; `marked` moved from `extFirstCompleted` to `extOld`; the legacy reorder left
  `extOld`'s question unprotected; an exact scope on B protected A's Theory instead; the three unplaceable scopes
  withheld nothing.
- F13: the unbound confirmed call returned `marked` (C released); the binding API did not exist.
- F14: "the gate still knows the question" failed (`check_leakage` returned `[]` after the refresh); with the member
  gone, nothing was protected.
- F15: `ReadingTarget(... extXB ..., section_id='u1', section_title='Theory')`; the plan served `contents` (held out)
  with DL1's order.
- Legacy: a legacy mark protected A exactly and released nothing else; doctor's message named no legacy mark.
- Round trip: `scope_extraction_id` was dropped by the writer, and the sidecar refused the field
  (`UpsertSourceSetInput` forbids unknown fields).

The migration test, the two refinement tests (an exact mark on a reading a legacy mark may also be about) and the
sealed-scope test were written after the first run; they use the new ledger, confirmation and seal.

**Earlier tests updated to the rule.** Tests that wrote marks as the old code did now write them as writers do:
`test_reread_safety.py` (`_made_on` on direct selection writes, `_exam_sets(reading=…)` naming the scope's reading,
`_confirm_marking` going through the confirmation), `test_facet_authority.py` and `test_facet_authority_review.py`
(their members record the scope's reading), `test_source_retrieval_guards.py`. One expectation changed:
`test_facet_authority_review.py::test_an_undo_never_mints_a_candidate_whose_recorded_citations_no_longer_resolve`
now expects the second undo to be refused as `exam_authority` too. The exam paper's inventory was made as exam
material and holds the question out, and a signal is its book's protection whatever the sets say (F14), so clearing
the mark after the member left no longer turns the citation into a merely unresolved one.

## The owner's vaults

Backup-API copies (`learnloop.db.copies.copy_tree_with_databases`) of the main checkout's `fixtures/linear_algebra`
and `fixtures/probability`, under this worktree's `fixtures-local/epi-*`. Each was summarised first by `808dc9c01`'s
code (a `git archive` of its `src`, read-only) and then by this branch's, which migrated the copy (166-202 and 225),
and once more by the final code (`daedc8b77`, identical):

| | linear_algebra (base / now) | probability (base / now) |
|---|---|---|
| schema head | 165 / 225 | 165 / 225 |
| sources, extraction runs, inventories | 3, 4, 41 | 4, 4, 25 |
| inventories with a held-out signal | 1 / 1 | 0 / 0 |
| ledger rows (backfilled) | n/a / 1 (a video's inventory, role not recorded) | n/a / 0 |
| exam members, exam scope entries, selections with marks | 0, 0, 0 | 0, 0, 0 |
| protected books | none / none | none / none |
| exam material, held-out partition, held-out items | empty / empty | empty / empty |
| held-back readings | none / none | none / none |

Nothing changes for them. The one ledger row is a YouTube video's inventory whose model flagged six spans held out;
it is not exam material and the book has no exam scope, so it protects nothing. A role-agnostic rule would have held
that video's readings back. The main checkout's `git status --short fixtures/` was identical before and after the
copies; the databases' size and mtime are unchanged, each `-wal` is still empty, and only the gitignored `-shm`
index's mtime moved (the backup's read-only open).

## Persisted meaning (docs/algorithm-change-playbook.md)

No scoring, scheduling, projection or admissibility meaning changes, so there is **no algorithm successor**.

- **Migration 225** (a placeholder number; renumber it when it lands on main after the migrations queued ahead of
  it) adds `source_held_out_signal_marks`: RAW_LEDGER in `db/table_roles.py`, never cleared by a rebuild, never
  updated (trigger), deleted only with its book (`delete_source_artifact`). It is backfilled from
  `source_unit_inventories` exactly. A row whose usage names no inventory it was rebound from was written by the
  model run on its own extraction, because a rebind rewrites usage. A rebound row, or one whose usage cannot be
  read, gets no reading. Replay never reads it. A database read before it is migrated (a practice-index dry run
  reads the serving exclusions of a schema-166 rollback database it must never migrate) gets the same rows derived
  from the cache in memory, so it is protected exactly as after the migration (the migration test checks both).
- The head fixture moved to `fixtures/migration_head_225`: `migration_head_202` was renamed and only 225 was applied
  to it through `learnloop.db.migrate.apply_migrations` (`wal_checkpoint(TRUNCATE)`, `journal_mode=DELETE`,
  `integrity_check` ok, `foreign_key_check` clean, no companion files; 0 ledger rows, it has no inventories). The
  upgrade was applied to the tracked file in place rather than to a backup copy first; the checks above are on the
  result. Its README and every hard-coded path (21 test files, both reference scripts with `SCHEMA_HEAD`,
  `test_route_rules_in_grader.py`'s head assertion, `docs/decider-tier1-migration.md`) name 225.
- `marks_made_on` lives in `source_unit_selections.exam_paper_metadata_json` (WORKFLOW). `scope_extraction_id`,
  `scope_revision_id` and `scope_seal` are new optional `source_sets.yaml` member fields. Replay reads neither.
- No config field changed.

## RPCs, CLI, desktop

- No RPC was added. `source_action` takes `confirmedExtractionId` and `confirmedProposalHash`, and its marking
  confirmation carries `proposalHash` and `revisionId`. `upsert_source_set` / `get_source_set` members carry
  `scopeExtractionId`, `scopeRevisionId`, `scopeSeal`. All are desktop-only and additive; the mobile allowlist's
  comment names them.
- CLI: `learnloop source-set add --reading` (help snapshot regenerated: one entry).
- Desktop: the card's confirmation sends the binding and shows a fresh confirmation when the sidecar returns one;
  AddToCollection records the outline's reading for a scoped member and re-sends other members as received.
- Doctor's `source:reading_held_back` details gain `ambiguous`.

## Residuals and open questions for the owner

- **No way to un-protect.** Signals made under an exam role keep their book protected after it leaves every set
  (item 7's definition). If the owner re-roles an exam paper as something else, its readings stay held back as
  marked. An explicit "this book holds no exam material" action would be the owner's to decide.
- **Facet authority reads scopes positionally.** `facet_identity.authority` resolves a citation's role from member
  scopes by unit id on any reading of the pinned revision. The predicate overrides it to `exam` wherever it covers a
  span, so this can only over-protect (a wrong unit labelled exam), never release. It was left as is.
- **The cache still rebinds.** `source_unit_inventories` keeps one row per revision, which a reuse moves to another
  reading. Protection no longer reads it, but synthesis and coverage read inventories by revision (pre-existing).
- **Legacy marks in other vaults** hold their books back whole until marked: one tap on the card per reading. The
  owner's two vaults have none.
- **Editing the suggestion** (open question C of the redesign) is still open. The marking holds out the whole
  suggestion, which now includes legacy marks' own units.
- `goals.held_out_selection` (the owner-approved kill switch of the item serving rules) is unchanged and out of this
  rule's scope. The model-context protections were never behind it.

## Gate

Run on the final code tree (`3a099b4eb`; only this record follows). `TMPDIR` was the worktree's
`fixtures-local/tmp`. No paid calls ($0.00); every test uses fakes.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`, `uv pip install pypdfium2` | ok |
| `uv run lint-imports --no-cache` | 17 kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | first run on `daedc8b77`: 11,064 passed, 1 failed, `test_practice_index_adapters.py::test_batch_dry_runs_never_migrate_an_older_rollback_database` (`no such table: source_held_out_signal_marks` on the unmigrated database: a real failure, fixed in `90f203c4b`). Final run on `3a099b4eb`: **11,065 passed**, 0 failed (11 min 6 s) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **102 passed**, 10,963 deselected (on `3a099b4eb`; 100 before, plus the marking transaction and the 225 backfill tests) |
| `apps/learnloop-tauri`: `npm install`, `npm run typecheck` | ok, no errors |
| `npm test` (vitest) | **594 passed** in 83 files (591 before: one new marking test, two new AddToCollection tests) |
| `npm run frontend:build` | built |
| `cargo check` | not required: nothing under `src-tauri` changed |
| `db_generate_reference.py` / `db_validate_reference.py` | regenerated (`132e4cd78`, with the new table's purpose; `daedc8b77` after the seal; `3a099b4eb` after the fallback); validation passes with no errors (schema head 225, 322 table notes); `validate_vault.py` passes |
| CLI help / snapshots / RPC pins | `test_cli_help_snapshot.py` regenerated (`source-set add`); `test_sidecar_serializer_snapshot.py`, `test_controller_snapshot.py`, `test_mobile_allowlist.py` pass |
