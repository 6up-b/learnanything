FINDINGS

1. HIGH — Edits made during staging are overwritten despite the new pre-image check.
Where: src/learnloop/content/proposals/apply_protocol.py:200, :238, :262–274, :414. Pre-existing staging flaw left unprotected by K3.5, 4f85aa885e.
Scenario: Staging copies a vault file containing A. While compilation runs, the learner edits the real file to B. _diff_targets then compares the staged A against live B and records B as pre_hash, A as post_content. Materialization passes the new check and overwrites B. This also affects files unrelated to the proposal: the diff scans the whole staged tree. The pre-image must describe what staging originally read.
Why missed: test_an_accept_whose_target_changes_under_it_writes_nothing_and_rolls_back edits after stage_target_contents returns, after the incorrect pre-image capture window has closed.
Smallest test: Edit an unrelated valid YAML file after the staging copy but before _diff_targets; apply another proposal and assert the edit survives.
Confidence: certain from the write ordering; not executed.

2. HIGH — Deleting a pending item bypasses D-10 and recovery subsequently applies the deleted item.
Where: src/learnloop/content/proposals/proposals.py:1313–1315; src/learnloop/content/proposals/apply_protocol.py:469–475, :670–679; src/learnloop/db/repositories.py:18229–18247. D-10’s incomplete protection: 611673f094.
Scenario: An apply commits its intent and crashes before recording item decisions. The still-running phone host deletes one pending item. delete_proposal_item calls the guarded undo only when applied_change_batch_id exists, so this deletion succeeds. Recovery later materializes the deleted item from the intent and records its effects; updating the missing proposal row silently affects zero rows. The content is applied without an inbox item through which it can be undone.
Why missed: D-10 tests reject/undo, but never delete a pending item referenced by an intent. Adding an exception handler to the delete RPC does not make this branch raise.
Smallest test: Leave a pending intent before materialization; call delete_proposal_item on its item and require OutstandingApplyIntentError with the row preserved.
Confidence: certain; recovery and deletion were traced statically, not executed.

3. HIGH — K3.3 drops inventoried units that have never reached synthesis.
Where: src/learnloop_sidecar/handlers/ingest.py:1139–1150. Introduced by 84d2614688.
Scenario: A subject already has an applied map. Add another book with scoped units u1, u2 and u3, where u1 was inventoried separately but never synthesized. The collection build inventories u2/u3 and filters the append to those two, silently omitting u1. Inventory reuse and synthesis newness must be decided separately.
Why missed: The new test fixture already contains precisely this scenario: _with_partly_inventoried_member inventories u1 without synthesizing it. test_new_units_of_a_partly_inventoried_member_are_inventoried_and_appended then explicitly asserts that only u2/u3 reach synthesis. The test enshrines the coverage loss.
Smallest test: Keep that fixture; require inventory work only for u2/u3, but require the append context to contain u1/u2/u3.
Confidence: certain; the fixture and filtering agree directly. No execution.

4. HIGH — The completed-shard cache still ignores changes to its second request.
Where: src/learnloop/content/synthesis/source_set_synthesis.py:2885–2892, :2915–2927, :2944–2957; span truncation at :541. K2.2 key replacement: 78509793b6.
Scenario: A shard completes a base pass and a span round, then the run fails before completion. Retry with a larger synthesis_span_char_cap for a requested passage longer than the old cap. The base prompt is unchanged, so the completed shard answers immediately. The longer evidence never reaches the model, although the second-pass rendered request would differ. A completed shard needs to validate all request dependencies, not just its first request.
Why missed: test_outer_cache_keys changes the common prompt, affecting the first pass too. Its shard fixtures do not exercise changed span-round inputs.
Smallest test: Save a two-pass shard, fail after saving it, increase the span character cap, and assert the base checkpoint is reused while the changed second request executes.
Confidence: certain from the cache branch; not executed. The earlier shard key also omitted this dependency.

5. HIGH — D-9 can delete a newer paid answer that the rejecting run never used.
Where: src/learnloop/content/synthesis/source_append.py:140, :164–165; src/learnloop/content/synthesis/source_set_synthesis.py:2838–2842; src/learnloop/db/stores/model_calls.py:41. Introduced by 887dc67f8a.
Scenario: Runs A and B load the same rejected answer. A reaches its gate first and deletes the checkpoint. Retry C generates and saves a fresh answer under that key, then fails during persistence. B finally reaches its gate and deletes the key again, removing C’s fresh answer. C’s retry now pays again. The discard must identify the saved answer/version judged, not merely its request key.
Why missed: All discard proofs use serial attempts. Neither _AppendCall nor _SavedAnswers retains the answer identity needed for conditional deletion.
Smallest test: Have two call objects load the old answer; discard through the first, save a replacement, then discard through the second. Assert the replacement remains.
Confidence: certain for this interleaving; production concurrency frequency was not measured.

6. MEDIUM — A rejected cached shard leaves its rejected span-round answer reusable.
Where: src/learnloop/content/synthesis/source_set_synthesis.py:2890–2891, :2915–2927, :2838–2842. Introduced by D-9, 887dc67f8a.
Scenario: Attempt 1 saves a two-pass shard but fails before gating. Attempt 2 reuses that shard and fails a quality gate. Only the base-pass checkpoint is registered for discard; the span answer survives. Attempt 3 pays for a fresh base answer, requests the same spans, and replays the already-rejected span answer. It fails unnecessarily before a subsequent attempt can regenerate that answer.
Why missed: The bootstrap D-9 test has one pass and rejects its fresh output immediately. The record acknowledges the surviving span checkpoint, but the ledger marks D-9 fixed without testing this consequence.
Smallest test: Use the three-attempt sequence above, with identical span requests and a provider that would return a corrected second-pass answer. Require attempt 3 to call that provider.
Confidence: certain when the resolved span requests match; not executed.

7. MEDIUM — The book’s undo preflight is outside the lock protecting the operation.
Where: src/learnloop/content/pipeline/add_source.py:2104–2133; guarded rejection at src/learnloop/content/proposals/patches.py:416–417. Introduced as incomplete D-10 protection in 611673f094.
Scenario: Undo sees no outstanding intent. Before it advances the generation, another process commits an apply intent and crashes. Undo then advances the generation and cancels builds, only to encounter OutstandingApplyIntentError when it reaches reject_items. The command reports refusal after performing the mutations D-10 promises to prevent.
Why missed: test_the_book_cards_undo_is_refused_before_it_changes_anything installs the intent before the initial check. It never interleaves an apply between that check and the mutations.
Smallest test: Coordinate two callers so an apply commits its intent immediately after undo’s initial query; assert refusal leaves the generation and cancellation flags unchanged.
Confidence: likely; the unprotected interval is explicit, but the concurrent scenario was not executed.

8. MEDIUM — Re-inventory after a prompt edit returns an inventory ID that was never stored.
Where: src/learnloop/content/synthesis/source_unit_inventory.py:951–975; src/learnloop/db/repositories.py:20568–20574; persisted job result at src/learnloop/content/pipeline/jobs.py:1674. Newly exposed by K2.2, d2bf99f1de.
Scenario: Inventory a unit, edit the prompt without changing its label, and inventory again. The new request correctly misses the cache. persist_prepared_inventory generates a new ID, but the SQL conflict update preserves the existing row’s ID. The returned InventoryResult and job result nevertheless name the discarded new ID. Held-out signal records also use the supplied ID at repositories.py:20600.
Why missed: test_an_inventory_prompt_edited_under_the_same_label_is_paid_once checks the third, cache-hit result’s ID, not the second result produced by the update.
Smallest test: Add assert repo.get_unit_inventory(edited.inventory_id) is not None to that existing test.
Confidence: certain from the upsert and return values; downstream effects beyond the recorded dangling references were not executed.

CHECKED AND FOUND SOUND

K3.4 checks uncached append input before calling the provider and applies generation_limit to both reconciliation rounds.
Append budget failures preserve paid answers, recheck output size on reuse, and finalize both run records.
Fresh append gate failures register and discard both calls, including the span round.
K2.2’s SQL CASE distinguishes keyed rows from legacy rows; provider/model changes affect the new row key.
Binding rows preserve their origin’s request key instead of silently becoming keyless.
Current identity_extra callers do not overwrite purpose, prompt, schema or settings.
The LLM facet-judge key retains its output budget and requested reasoning effort.
GLM-OCR rejects and discards non-object saved answers before regeneration.
Recovery re-queries pending intents after acquiring the cross-process vault lock; secondary attachment does not automatically recover.
Recovery exceptions cause the primary sidecar to reload potentially changed files.
D-11 accepts both prefixed and bare hashes, and the changed writers use the shared hash function.
Migration 255 copies all nine existing columns, preserves the pending default, recreates the sole index, and has no migration-defined incoming foreign keys or triggers.
No remaining source references were found to the removed checkpoint helper names searched.
D-12 excludes wholly rejected proposals and counts pending proposals as sent, matching its stated policy for ordinary unmerged units.

COULD NOT CHECK

No tests, application code, migrations, subprocess crash harnesses or network requests were run; no files were written.
Actual concurrency frequency, filesystem durability under power loss, and provider truncation/billing behavior require execution.
The reported backup-vault spend measurements and migration row-preservation measurements were not independently reproduced.
Identity formulas and golden diffs were inspected; golden hashes were not recomputed.
Live vault data was not read, so the prevalence of these states is unknown.