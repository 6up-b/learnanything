# Phase 1 fixes: ingestion synthesis (I4, I5, I6)

These are the fix-round rows I4, I5 and I6 of the phase 1 adversarial review's ingestion report
(`docs/reviews/artifacts/phase-1-review/codex-ingestion.md`, findings 4-6, on main `e231d7fb59`). They were fixed on
branch `refactor/k2.3-manifest-records`, above K2.3's tip `8c13e8f4c3`, with one commit per row. Every row reproduced.
The tests are in `tests/test_synthesis_answer_reuse.py`.

The fail-first runs at `8c13e8f4c3` (before any of these commits), with the whole test file in the tree:
- 5 of 6 tests failed;
- the I4 guard (an unchanged two-pass shard) passed.

## I4: a completed shard stood for its first request only

**Reproduced.**

- **Failing test.** `test_a_completed_shard_does_not_answer_a_changed_span_round_request`.
  - The first build asks for a span, gets its span round answered, and fails at persist, so the shard row and both
    pass checkpoints are saved.
  - The rebuild runs with `synthesis_span_char_cap` 12, under which the resolved span text would be shorter.
  - **At the tip:** (base, span-round) calls were `(1, 1)` after the rebuild, so the changed span request never ran.
    The completed-shard row answered on the base request's key.
  - **Fixed:** `(1, 2)`. The base pass answers from its checkpoint, the changed span request is sent, and its spans
    are at most 12 characters.
- **Guard.** `test_an_unchanged_two_pass_shard_is_answered_by_its_checkpoints`, green on both: an unchanged two-pass
  shard makes no call.
- **Fix** (`d711ca58c4`). In `_run_synthesis`'s preflight, a shard row whose output records a span round
  (`span_request_count > 0`) is not used. Its passes run again, and each is answered by its own checkpoint when
  unchanged. The row key stays the base request's key: for a one-request shard, that key is the whole request it
  stands for. The import workflow note says so.
- **Callers.** `_run_synthesis` is called only by `_create_study_map` (both attempts of K2.3's loop). Append does not
  use shards. Revalidation reuses the stored candidate, not shards.
- **Siblings: stored results that stand for more than one request.**
  - The append call and its span round: one checkpoint per request and no aggregate row. Not affected.
  - Legacy ingest windows, GLM-OCR windows, the facet judges and the Decider: one checkpoint per request. Not affected.
  - Structuring and epigraphs: one request each. Not affected.
  - **The inventory row** (`source_unit_inventories`, K2.2's `inventory_row_key`): **the same shape, left as designed.**
    The row stands for all the windows a unit was read in, and its key renders the template over an empty context.
    So a change that only re-splits the windows (`input_budget_tokens`) or changes the view's code without moving the
    semantic hash is answered by the row, and the changed window requests are not sent. K2.2's judgment call 1 chose
    this on purpose, so cross-revision and cross-role reuse keep working. Changing it is a design question, not this
    row's fix: an open item below.
  - K2.3's proposal match compares rows after a full re-run. It is not a stored-result shortcut.
- **Not verified.** A shard row written before K2.2 is ignored by its key anyway. I did not check whether any stored
  row records a span round with its count missing; such a row would be treated as one-request.

## I6: a reused shard's span-round answer survived a rejection

**Reproduced.**

- **Failing test.** `test_a_rejected_reused_shard_drops_its_span_round_answer`. Three attempts:
  1. Fails before the gates (a two-pass shard is saved).
  2. Reuses the shard and is rejected by the gates.
  3. Normal.
  - **At the tip:** (base, span-round) calls `(2, 1)` after attempt 3. The rejected span answer was replayed, because
    only the base pass and the shard row had been registered for the discard.
  - **Fixed:** `(2, 2)`.
- **Fix.** I4's (`d711ca58c4`): a shard with a span round is no longer reused from its row. Both its passes are served
  through `run_pass`, registered, and dropped together on a rejection. Commit `844d349340` adds the test and removes
  the limit that `_SavedAnswers`' docstring recorded.
- **Callers of the registration.** Answers are registered only in `_run_synthesis` (`run_pass` and a reused
  one-request shard) and `_model_graph_structuring` (the structuring answer). The discard runs at two places:
  `_create_study_map`'s `synthesis_gate_failed` arm (D-9) and K2.3's rejected-proposal retry (D-16).
- **Siblings.** `_AppendCall` registers every request it serves, its span round included. The epigraph batch is
  dropped by its own call site. Neither had the gap.

## I5: a discard deleted whatever its key held, not the answer judged

**Reproduced.**

- **Failing tests.**
  - `test_a_bootstrap_rejection_keeps_a_fresh_answer_another_run_saved`. During the gates of a run, another run's
    effect is simulated: the judged pass checkpoint and shard row are dropped and a fresh answer is saved under the
    same keys. Then this run's gates reject.
    - **At the tip:** no `synthesis_pass` checkpoint was left, because the rejection deleted the fresh answer.
    - **Fixed:** the fresh answer and its shard row remain.
  - `test_an_append_rejection_keeps_a_fresh_answer_another_run_saved`: the same for the append call. At the tip, 0
    left; fixed, the fresh one remains.
  - `test_a_checkpoint_discard_keeps_an_answer_saved_after_the_one_judged`: the report's smallest test on
    `ModelCheckpoint`. Two checkpoint objects fetch the old answer; the first discards it and saves a fresh one; the
    second discards. At the tip it failed, but only for the missing `fetch` API; the two tests above show the
    behaviour.
- **Fix** (`4c1d4bad96`). A discard names the stored form of the answer it judged, and deletes only while the store
  still holds that form. It is one statement on the stored text, which every writer serializes the same way.
  - `ModelCheckpoint` (`ai/execution.py`):
    - `fetch()` returns the answer and the stored result it was read from;
    - `save()` returns what it stored;
    - `answer_stored()` returns both; `answer()` and `load()` keep their contracts;
    - `discard(stored)` passes the condition.
  - Stores: `discard_model_checkpoint(key, *, result=None)` in the `Repository` mixin (`delete_checkpoint` with
    `result_json = ?`), and passed through by the AD claim store and the hint-map store.
    `Repository.discard_synthesis_shard_result(key, *, output=None)` uses `output_json = ?`.
  - `_SavedAnswers` records `(key, stored form)` for:
    - each pass served by `run_pass` (fetched or saved);
    - each shard row reused (its row and the identical base-pass answer) or saved;
    - the structuring answer.

    The old preflight registration of every shard's key is gone: a discard follows a full run, so every shard was
    served by then.
  - `_AppendCall` records `(key, stored form)` per request.
- **K2.3's D-16 path** uses the same `_SavedAnswers.discard` and `_AppendCall.discard_answers`, so it follows the
  same rule. In the bootstrap path the saved answers are reset after the discard. The append path keeps its list; a
  second rejection's discard of an already-dropped answer deletes nothing, or deletes an identical fresh answer this
  same run judged.
- **Callers and siblings of the discard** (every caller of `discard_model_checkpoint` and
  `discard_synthesis_shard_result`):

  | site | before | now |
  |---|---|---|
  | `_SavedAnswers.discard` (bootstrap rejection; D-16) | by key | by the judged form |
  | `_AppendCall.discard_answers` (append rejection; D-16) | by key | by the judged form |
  | `vault_epigraphs` (a batch rejected whole) | by key, after reading | by the read or saved form |
  | `ModelCheckpoint.load` / `fetch` (an answer that no longer reads; used by inventory windows, synthesis passes, structuring, append, legacy windows, persona fires, the facet judge, the Decider, GLM-OCR) | by key, after reading | by the form read |
  | `practice_index/paid.py` `_recover` (an answer that no longer reads) | by key, after reading | by the form read |
  | `ops/pf_calls.py` (an answer that no longer reads) | by key, after reading | by the form read |
  | AD claim store, hint-map store, the test double in `test_model_work_checkpoints` (protocol implementations) | key only | pass `result` through |

  Checkpoint readers with no discard (`router_teach_back`, `field/classification`, `library_ask`, `passage_cues`) are
  not affected.
- **Assertions changed.** None. `test_model_work_checkpoints`' in-memory `_Store` follows the store protocol and gained
  the optional `result` condition.
- **Not verified.**
  - Real concurrency: the tests simulate the interleaving inside one process.
  - A stored checkpoint written by an older writer with another serialization would not match, and a rejection would
    then keep it. Every writer found is `insert_checkpoint` (`json.dumps(sort_keys=True)`) or the repository's `_json`.
  - A fresh answer whose text is identical to the judged one is indistinguishable from it and is dropped. It is the
    same answer, so a retry pays once more for it.

## Gates

- **Targeted tests.**
  - After each commit: `test_synthesis_answer_reuse`, `test_outer_cache_keys`, `test_source_set_synthesis`,
    `test_model_work_checkpoints`, `test_source_append`, `test_rerun_proposals`, `test_vault_epigraphs`,
    `test_glm_ocr`, `test_persona_gate` and `test_facet_identity`.
  - After `331619d1ce`: the store change reaches `Repository`, so every test file ran. That was 1,392 files with
    `-m "not arc_close"`, in 14 chunks of up to 100 at `-n 4` under the 5 GB cap behind the full-suite lock: 30,478
    passed, 0 failed.
- **Lint.** `lint-imports --no-cache`: 42 kept. `ruff check`: clean.
- **Vault validators.** All four pass.
- **Gate partition.** `check_gate_partition`: 30,714 collected (landing 30,654 + arc_close 60).
- **Regeneration.** References were regenerated once (`81b77a099a`); a second run changed nothing.
