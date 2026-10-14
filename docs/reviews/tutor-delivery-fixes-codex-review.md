# Tutor delivery fixes: Codex review and fixes

**Branch:** `tutor/delivery-fixes` (worktree `learnanything-ux-impl`, base main `4cf54a295` = mvp-0.22, not rebased; the orchestrator merges). **Reviewed:** `4cf54a295..4e7397731` by Codex (job `20261014-003108-wUxaXt`), six findings. **Stage record:** `docs/reviews/tutor-delivery-fixes.md`.

Each finding was reproduced first: a test that fails on the reviewed code, or for F1 also a direct run of the reviewed fallback. Then it was fixed. All six reproduced. None was rejected. The successor half of F5 is declined, with the reason given below. **Paid calls:** none ($0.00); every model and embedding call in the tests is a house fake. **Vaults:** the owner's working vaults were not opened. F6's label counts were measured read-only on the backup-API copies `fixtures-local/tdf-linear_algebra` and `fixtures-local/tdf-probability`.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Linked references bypass the practice-item source exclusions | **fixed** | `8420b7570` | `tests/test_tutor_delivery_fixes.py`: `test_a_linked_spans_reference_to_the_items_own_example_is_refused_by_its_database_link`, `..._to_a_re_extracted_copy_...`, `..._into_a_solution_regions_body_...`, `test_without_the_adapters_rules_a_linked_spans_references_are_not_followed`, `test_the_sidecar_injects_the_linked_reference_rules` |
| F2 | Medium | The labeller still silently truncates blocks at 6,000 characters | **fixed** | `70fa81739` | `test_the_t6_labeller_reads_a_block_past_the_embedding_recipes_cap_whole`, `test_a_trim_between_the_recipe_cap_and_the_block_length_is_counted`, `test_the_t6_labeller_counts_a_trim_at_the_passage_budget` |
| F3 | Medium | A crash between extraction completion and enqueue permanently loses backfill | **fixed** | `d4bdbd613` | `tests/test_source_vector_backfill.py`: `test_an_interruption_right_after_extraction_completes_still_indexes_the_source_on_retry`, `test_a_backfill_that_cannot_be_queued_fails_the_import_retryably_and_the_retry_queues_it`, `test_a_page_repair_queues_the_backfill_its_sources_current_extraction_owes` |
| F4 | Medium | Failed backfills are marked completed and announced as successful | **fixed** | `d4bdbd613` | `test_lock_contention_fails_the_backfill_retryably_and_a_retry_completes_it`, `test_a_provider_failure_after_a_saved_batch_fails_retryably_and_the_retry_buys_only_the_rest`, `test_a_backfill_over_its_money_cap_fails_and_names_the_cap` |
| F5 | Medium | Expanded delivery has no working rollback switch | **fixed** (kill switches); successor part declined | `29919610d`, `7fa49d2b6` | `test_the_expanded_delivery_kill_switch_restores_the_predecessors_reader_window` (4 cases), `..._restores_the_600_character_retrieved_span`, `..._keeps_a_linked_span_at_its_600_character_cut`, `test_the_complete_passages_kill_switch_restores_the_judges_900_characters`. Successor: see F5 below |
| F6 | Low | The TOC heuristic rejects ordinary numbered mathematical statements | **fixed** | `11104a42a` | `test_numbered_statements_ending_in_a_number_are_labels_and_toc_lines_are_not` (11 cases), `test_by_theorem_resolves_to_a_statement_ending_in_a_number` |

References regenerated in `a7dc4227b`.

## F1: a linked span's references keep the item's exclusions

**Reproduced.** The reviewed fallback (no span provider, or the provider keeps the linked spans) delivered the cited block in all three cases Codex named:

- **Database-only link.** `pi_eigen_1` links `Example 3.2` through `entity_source_links` only. The LO-linked passage says "as Example 3.2 shows", and the tutor received the example.
- **Re-extracted copy.** The item links the example in an older extraction of the same source, and the current extraction's copy was delivered.
- **Solution-region body.** An equation tagged `(3.4)` in the body after a `Solution.` lead was delivered, together with the block after it.

`item_source_keys` reads only the YAML provenance and the canonical exercise. The lead-word test sees only the lead block.

**Fix.** The fallback no longer has its own rule. It reuses the provider's own, by injection, the same seam the span provider uses (`tutor_qa` never imports `source_retrieval`).

`source_retrieval.tutor.linked_reference_filter` is `reference_filter` over the question's `tutor_scope`. That scope applies:

- the teaching exclusions;
- in practice and feedback contexts, `item_exclusions` across every relation and status, every extraction of the source by content hash, and the worked-example, exercise or solution body a linked block leads;
- every exercise and solution region with its body.

The scope is built lazily, on the first cited block. The sidecar passes the filter to `ask_question` and `build_tutor_opening`. Without it, a linked span's references are not followed (fail closed). The old `_linked_reference_filter` is removed. A positive control shows the same example still reaches another item of the same LO, as its scaffold.

## F2: the labeller reads the canonical block

**Reproduced.** In a 6,500-character block, the assumption after character 6,000 never reached the labeller, and the report said `label_trimmed = 0`. At a 6,400-character budget the passage was cut but counted as 0.

**Fix.** `recipes.source_block_passage` gives the recipe's "Section:" line plus the complete canonical block. `judge_passage` at the passage budget is now the only cut, counted once per candidate. Both labelling passes read the same candidate, so the count is per candidate, not per pass.

## F3: the backfill obligation survives an interruption

**Reproduced.**

- A worker that died right after `complete_extraction_run` committed (simulated with a `BaseException`) left a completed run. Its retry, after the lease was recovered, took the cached path and queued nothing.
- An enqueue error was logged and swallowed, and the import completed.

**Fix.** The import and repair handlers call `queue_source_vectors` on both the fresh path and the reused path.

It queues only what is owed (`source_vectors.backfill_owed`): the source's current extraction is not fully covered for `embedding.model`, and no queued or running job targets it. A retry or a covered repair therefore queues nothing and buys nothing. A further retry after the recovered one queued no second job and made no embedding call.

An obligation that cannot be queued fails the import retryably (`source_vectors_not_queued`). Its retry reuses the extraction, nothing is extracted again, and the job gets queued.

The stage's repair test changed with this. A repair whose parent is already covered now queues no job. The test now checks both cases: a parent imported while the automatic backfill was off is owed, and gets queued; a covered parent queues nothing.

## F4: a backfill that does not finish is not completed

**Reproduced.** Lock contention, a provider failure after a saved batch, and a run over its money cap each completed the job and announced "Meaning search index updated".

**Fix.** `handle_source_embedding_backfill` maps each report to a workflow state:

| Report | Job | Code, retryable |
|---|---|---|
| `complete` | completed ("updated", or "already up to date" when nothing was bought) | |
| `disabled`, `no_extraction` | completed, saying nothing was sent | |
| `busy` (another backfill holds the lock) | failed | `embedding_backfill_busy`, yes |
| `provider_failed` | failed | `embedding_provider_failed`, yes |
| `unavailable` | failed | `embedding_unavailable`, yes |
| `over_budget` | failed, naming `embedding.source_backfill_max_cost_usd` | `over_budget`, no |
| `blocked` (vector width or model mismatch, input limit) | failed | `embedding_index_conflict`, no |
| `cancelled` | cancelled | |

Lock contention gets its own type: `ops.embedding_backfill.BackfillLockBusy`, still a `ValueError`. Error details carry the aggregate report only. Batches paid before a failure stay saved: after a provider failure, the retry bought only the remaining block (embedder calls `[1, 1]`).

Two incidental fixes:

- The run's caps are now sized with the batch size it actually sends. They were bound to a default at definition time.
- The ingest queue has no deferral column, so lock contention is retried through the normal path (a failed, retryable job; `resume_batch`), not deferred in place.

## F5: rollback switches; no successor

**Fixed: two kill switches** (both default true, modelled defaults):

**`tutor_qa.expanded_delivery`** covers items 1 and 2 on the tutor's side. Off, it restores the predecessor's passages:

- In the Reader, the span view's window: the three ordinal-adjacent blocks before and after the primary block, furniture and empty blocks included, as 240-character previews, until the list holds max(4, spans + 2).
- Retrieved and pinned spans at `span_context`'s 600-character collapsed cut.
- Linked spans at their 600-character cut, not completed.

The Reader manifest follows the switch. The test compares the switched-off delivery with the predecessor `_reader_source_spans` from `4cf54a295`, embedded verbatim in the test. They are equal for one block, a quoted selection, a multi-block selection and a held-out neighbour. Item 3 keeps its own switch (`resolve_references`); with both off the delivery is the predecessor's.

**`source_retrieval.complete_passages`** covers item 2 on the judges' side. Off, the verifier, `find_sources`' checks and the T6 labeller read the predecessor's 900-character clip again (one `verify.judged_passage`). The labeller reads the embedded text, and the report's manifest is `t6-eval-v2`; on, it is `t6-eval-v3`.

The budgets stay as separate bounds.

**Declined: a successor version.** Under the algorithm-change playbook (step 1), a successor `algorithm_version` is minted when persisted meaning changes. This stage's changes don't change any persisted meaning:

- They change what one tutor answer and the retrieval benchmark's judges read.
- Nothing is scored, scheduled, projected or served differently.
- Replay reads none of it.

The owner's standing ruling (2026-10-12) is live changes behind kill switches, with no shadow stages by default. The switches above supply that. All fourteen `DEFAULTS_SNAPSHOT_BY_ALGORITHM` entries were recomputed because the effective config gained the two keys, and the template `.pyc` was cleared.

## F6: strong evidence for a table-of-contents line

**Reproduced.** `numbered_label("Theorem 3.2. The derivative of a constant is 0")` returned None: the weak rule (a trailing number plus two or more numbers) took it for a TOC line.

On the backup copies, that rule caught no TOC line at all. It rejected nine of Axler's own labels, such as "1.31 a number times the vector 0", "1.15 notation: 0" and "1.7 example: 2 and 3". Its only other hit was a course header, "6.041SC Probabilistic Systems ...".

**Fix.** Only strong evidence now counts:

- a `TableOfContents` block;
- leader dots;
- a page number in its own column (after a tab, three or more spaces, or a table cell).

A number-first label's number must stand alone, so the course code is still not a label.

Labels on the copies: linear algebra 58 → 67 (exactly those nine), probability 48 → 48.

## Gate

Run on `a7dc4227b` (the final code; later commits are documents). `TMPDIR` was the worktree's `fixtures-local/tmp`; the full suite and the durability lane ran under `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10701 passed**, 0 failed, 48 warnings (10 min 54 s; the stage's own gate had 10668) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10602 deselected, 1 warning |
| `db_generate_reference.py` / `db_validate_reference.py` | schema head 201 (unchanged), 319 table notes, 821 configuration leaves (was 819); errors [] |
| `validate_vault.py` | passed, 1102 notes |
| Frontend / `cargo check` | not run: nothing under `apps/` changed |

Targeted runs before the gate:

- the delivery and backfill files: 50 and 12 passed;
- tutor, retrieval, sidecar, ingest, runner, doctor, T6 and architecture suites: 113, 214 and 39 passed;
- configuration, upgrade pins, parameter registry and reader suites: 353 passed.

`uvx ruff check --select F` over the changed files reports only six findings that are already present at `4cf54a295`, on lines this stage did not touch.

## Re-review

**Reviewed:** `4e7397731..9e5aabbf8` by Codex (job `20261014-014539-wwSubZ`), verdict REOPENED on one finding. The re-review confirmed F1 fixed (database-only item links, re-extracted copies, worked-example continuations and solution-region bodies are refused, and nothing is followed without the injected filter). It also confirmed the long-passage correction (F2), the judge rollback (F5), the numeric-ending labels (F6) and all fourteen configuration fingerprints.

The owner paused the run on 2026-10-14 (about 02:20 to 09:00) after the F7 fix was committed. The run resumed on the clean tree at `15e6062d0`; main was not merged in. **Paid calls:** none ($0.00). **Vaults:** none opened.

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | High | Linked references bypass the practice-item source exclusions | confirmed fixed by the re-review | `8420b7570` | no further change |
| F7 | Medium | Replacing the reference filter removes protection for exercises without accurate role hints | **fixed** | `15e6062d0` | `tests/test_tutor_delivery_fixes.py`: `test_a_linked_captions_reference_to_an_exercise_caption_is_refused_while_practising`, `test_a_linked_spans_reference_to_an_exercise_with_a_missing_or_wrong_hint_is_refused` (hint None, `ordinary_prose`, `theorem`), `test_an_exercise_continuing_a_cited_theorem_is_cut_while_practising`, `test_a_retrieved_spans_reference_to_an_exercise_caption_is_refused_while_practising` |

References regenerated in `033e7d465`: the fix moved lines in `source_retrieval/tutor.py`, and `db_validate_reference.py` flagged seven configuration citations to stale lines.

### F7: the lead guard is back, for every path

**Reproduced.** Codex's scenario: an LO-linked caption, built by the production caption normalizer (`captions_to_ir`, which gives every caption `ordinary_prose`), cites "Exercise 3.2". In practice the tutor received the exercise caption.

The same happened with a Marker block "Problem 3.2. ..." that had no hint, an `ordinary_prose` hint or a `theorem` hint. An unhinted "Exercise:" block also continued a cited theorem's environment. And the retrieved path's filter followed the caption too.

Before F1, the predecessor's `_linked_reference_filter` checked `lead_role(block.text)` itself. F1 swapped that filter for the teaching scope's exclusions, which read role hints only, so the check was lost.

On resume, the six test cases were re-run with the fix's source change reverse-applied: all six failed. With the change re-applied, all six pass (the file: 56 passed).

**Fix.** `source_retrieval.tutor.reference_filter` is shared by the retrieved, pinned and linked paths. With an item (practice and feedback), it now refuses any block whose own lead names an exercise or a solution (`ITEM_BOUND_LEAD_ROLES`, read by `lead_role`), whatever the block's hint. The reason recorded is the predecessor's: "an exercise or solution, while the item is being practised".

`follow_references` asks the filter about the cited block and about each block that continues it. An exercise that follows a cited theorem therefore ends the theorem's environment. Outside practice and feedback nothing changes: the test's library-context filter allows the same block.

The stage record's exam rule (`docs/reviews/tutor-delivery-fixes.md`) says so.

### Re-review gate

Run on `033e7d465`. Its code is that of `15e6062d0`; the later commits change only documents. `TMPDIR` was the worktree's `fixtures-local/tmp`; the full suite and the durability lane ran under `flock /tmp/learnloop-fullsuite.lock`.

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile`; `uv pip install pypdfium2` | ok (pypdfium2 5.14.0) |
| `uv run lint-imports --no-cache` | 17 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **10707 passed**, 0 failed, 48 warnings (12 min 0 s; 10701 before plus F7's six cases) |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **99 passed**, 10608 deselected, 1 warning (2 min 45 s) |
| `db_generate_reference.py` / `db_validate_reference.py` | schema head 201 (unchanged), 319 table notes, 821 configuration leaves; errors [] |
| `validate_vault.py` | passed, 1102 notes |
| Frontend / `cargo check` | not run: nothing under `apps/` changed |
