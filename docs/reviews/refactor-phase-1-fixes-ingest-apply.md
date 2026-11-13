# Phase 1 fix round, group FR-B1: the apply protocol, the collection build, the inventory upsert

Rows I1, I2, I3, I7, I8 of `refactor-phase-1-review.md`. Branch `refactor/p1-fixes-ingest-apply`, based on main `e231d7fb59`. One commit per row. All five reproduced at the base tip.

## I1: the pre-image is what staging read

Failing tests (`tests/test_apply_recovery.py`):

- `test_a_file_edited_while_staging_ran_is_not_overwritten_with_the_stale_copy`: an unrelated file (`profile/goals.md`) edited after the staging copy was overwritten with the stale copy (the diff recorded the live edit as the pre-image).
- `test_a_target_changed_while_staging_ran_is_refused_and_keeps_the_edit`: a file the proposal creates, written live during staging, was overwritten; the apply did not refuse.
- `test_only_the_files_the_items_change_become_targets`: `stage_target_contents` returned `profile/goals.md` as a target.

Fix (`apply_protocol.py`): the staging copy is hashed right after the copy (`_tree_hashes`) and `_changed_targets` makes a target of a staged file only when it differs from that baseline; its `pre_hash` is the baseline hash (`None` for a new file). `_diff_targets`, which compared staged bytes with the live tree, is gone. A live file that no longer holds the baseline hash is already a conflict in `materialize_targets` (K3.5), so the apply writes nothing and rolls the intent back.

Callers and siblings checked: `stage_target_contents` is called by `patches._apply_accepted_locked` (the apply) and `patches._ask_span_support` (a dry staging whose targets are discarded); `pre_hash` is produced nowhere else (grep), the other `materialize_targets` callers (facet registry saves, doctor fixes) pass no pre-image and are unchanged. Not handled, as before: a file a writer would delete in staging is not a target (no writer deletes one today).

## I2: item changes while an apply is outstanding

Failing tests (`tests/test_apply_recovery.py`): `test_deleting_a_pending_item_is_refused_while_an_apply_is_outstanding` (the delete succeeded), `test_the_sidecar_delete_names_the_outstanding_intent`, `test_editing_an_item_an_outstanding_intent_names_is_refused`, `test_recovery_fails_loudly_when_an_intent_names_an_item_that_is_gone` (recovery completed silently). `test_rejecting_a_pending_item_is_refused_while_an_apply_is_outstanding` passed at the base tip (see the list below) and stays as a regression test.

Fix: `proposals.delete_proposal_item` takes the vault lock and calls `refuse_while_an_apply_is_outstanding(action="delete")` first (global, as accept and undo are). `perform_db_effects` raises `ApplyIntentItemMissing` when an intent's plan names an item with no row; recovery propagates it and the intent stays outstanding for the owner.

Every mutation of proposal items and patches, listed:

- `delete_proposal_item` (sidecar RPC, phone and MCP through the registry; no CLI command): hole, fixed.
- `edit_proposal_item` (sidecar, CLI `edit-proposal-item`) and `refresh_proposal_item_validation` (sidecar): hole (recovery applies the frozen plan while the inbox shows the edited payload). Fixed with the narrower `refuse_while_an_apply_names_items` (only an outstanding intent that names the item), under the lock; the sidecar handlers map it to `apply_intent_outstanding`. Judgment call: narrow rather than global, so an unrelated edit is not blocked by a conflicted intent that may stay for a long time.
- `reject_items`: its undo half was already refused globally, even with nothing to undo (`reject_applied_items` takes the lock and refuses first), so a pending reject was already refused; but the pending decision ran after that lock was released. Now one lock covers both.
- `reset_items` (`reset_proposal_item_decision`): moves only rejected, never-applied items back to pending. An item an intent names is pending when the intent is written and rejecting it is refused, so no item an intent names can be in that state; no change.
- `accept_items` / `apply_accepted_items`, `reject_applied_items`: refused already (K3.5, D-10).
- Internal callers `proposals.py` (generation-time reject of failed rows, payload normalization) run at proposal creation, before any apply can name the items.

Not verified: a real concurrent delete against a live apply (the tests use a pending intent).

## I3: inventory work and synthesis newness

Failing test: `test_new_units_of_a_partly_inventoried_member_are_inventoried_and_appended` rewritten to require inventory work for u2 and u3 only and u1, u2, u3 in the append (it failed: `new_unit_ids == {rev_more: [u2, u3]}`, u1 left out). Added: `test_an_inventoried_unit_a_kept_synthesis_sent_is_not_sent_again` (a unit a kept append sent stays out) and `test_a_fully_inventoried_unsent_member_is_appended_with_no_inventory_work`.

Fix (`handlers/ingest.py` `build_study_map`, append mode): `units_not_yet_sent` (the CLI's answer, D-12) is called once; per member, inventory work is the units with no row; the append gets every unit that has no row or that function reports unsent. A member with no inventory work is left out of `members` but still named in `new_revision_ids` (the batch needs no inventory job for it). The unit filter is set only when some scope unit is left out, as before.

Assertion changed: `tests/test_build_study_map_routing.py::test_existing_map_routes_to_append_over_new_members_only` seeded "rev_a is inventoried, so it counts as synthesized", the same conflation. It now pins `units_not_yet_sent` to "rev_a was sent" (the seam stands in for a kept synthesis run). The `new_unit_ids is None` assertion in the partly inventoried test replaces `{rev_more: [u2, u3]}` because all three units are now sent.

Callers and siblings: `units_not_yet_sent` is also used by the CLI `synthesize`; `add_source`'s keep-ahead append names its units explicitly; `source_set_synthesis._collect_inputs` and `source_coverage` read inventory rows for their own purposes (not a newness question). Note: `units_not_yet_sent` sees only inventoried units, so a unit with no row is treated as never sent without asking it.

## I7: the book card's undo

Failing test: `test_the_book_cards_undo_holds_the_vault_lock_from_its_check_to_its_last_change` (another writer acquired the vault lock while undo was advancing the generation). Fix: `add_source.undo_source_questions` runs its check, generation advance, cancellations and reverts under one `vault_mutation_lock` (re-entrant for `reject_items`). Caller: the sidecar's `first_run` handler only. A running build that holds the lock while it applies makes undo wait up to the lock timeout, then `VaultLockTimeout` propagates; not changed.

## I8: the inventory upsert's id

Failing tests (`tests/test_outer_cache_keys.py`): the existing prompt-edit test now also asserts `edited.inventory_id` is the stored row's id (it was the discarded new id); `test_an_inventory_rewritten_under_its_key_returns_and_marks_the_stored_id` (the insert returned `None`, and a held-out mark would carry the offered id).

Fix: `Repository.insert_unit_inventory` reads back and returns the id of the row holding the key, and writes the held-out mark with it; `persist_prepared_inventory` returns it. The rebinding branch of `prepare_unit_inventory` keeps its rule for a same-revision rebinding (the candidate's id) and takes the returned id for a new revision (its guessed `binding_id` was dangling when a binding row already existed). Callers using the returned id: `jobs.py` (job result) and the CLI `inventory` output; both only record it. Test helpers that call `insert_unit_inventory` ignore the return.

## Not verified

The full suite (changing `repositories.py` selects every test: the orchestrator runs it at landing); concurrent behaviour beyond the lock-contention probe; the vault reference regeneration (see the commit after this record).
