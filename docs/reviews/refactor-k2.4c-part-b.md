# Refactor K2-20 and K2.4c part B: a revision a poller can read, and an oversized append in passes

Branch `refactor/k2.4c-b-split-appends`, cut from the K10.11/K10.12 tip with its status commit (`b1a651a920`). Two
steps, one commit series each: the ledger row K2-20 (due before arc K closes), and K2.4c part B, designed in
`refactor-k2.4c.md` "Part B" and decided by the owner on 2026-11-20: "split, one neighbourhood per run, using cached
tokens" (the free-text answer: "let's be sure that we take advantage of cached tokens as well"; the owner's
token-estimator note in the same answers: "keep shard_ordinal/shard_count out of the prompt so an unchanged chapter
is a checkpoint hit").

## Step 1: K2-20, proved and fixed

**The harm, by test.** `legacy_ingest`, `exam_ingest` and `source_exercise_import` write scheduler-visible practice
(the canonical-ingest proposal's auto-apply; a picked exercise written as an item) but did not bump the queue
revision on completion. The desktop is covered: its `get_queue_revision` reloads after any job that applies vault
content and answers `reloaded`, which its poll treats like a revision change. The phone is not: it polls
`/api/v1/queue-revision`, a read-only read of `Repository.queue_revision` that never reloads
(`learnloop_mobile/host.py`), and that number is all it compares. `tests/test_queue_revision_after_applying_jobs.py`
runs each job type through the ingest runner and reads only that revision: after each job completed with its
practice written, the revision had not moved (3 cases red on the base, commit `b7bbf6f4f2`). The legacy cases stand
in a run that writes a practice item for `ingest_canonical_source`'s auto-apply (which, read, bumps nothing); the
exercise case runs the real handler with the house fake.

**The fix.** The three rows of `content/pipeline/job_types.py` set `affects_queue`, so the runner bumps the revision
once each job row is completed, as for the other jobs that write practice (`bd84a4fa4d`). The characterization's
three rows change with them (`tests/test_job_types.py`); ledger K2-20 fixed. A queue revision is a freshness token,
not persisted meaning.

## Step 2: K2.4c part B

### What changed

- **The append's units** (`source_append._append_passes`, replacing `_append_unit`): the new inventories whole when
  their request fits `append_input_ceiling`, exactly as before; otherwise split in order (`select_new_inventories`'
  order: revision, then unit) into passes of whole inventories, each as large as fits under the ceiling with room
  for its span round (`synthesis_span_request_max_count` × `synthesis_span_char_cap` / 4, both existing settings).
  Sizes are the runner's own estimate of a rendered request (`_pass_tokens`), so the split point is the number the
  refusal computes: no new constant, no new threshold.
- **Each pass is asked as an append of its own inventories would be:** the run's one neighbourhood, and
  `shard_ordinal`/`shard_count` left at their defaults (`_append_contexts`), so its prompt and checkpoint key depend
  on its inventories alone and an unchanged pass is its checkpoint's answer again. No prompt template, prompt version
  or request changes; an append that fits is byte-identical.
- **The runner** (`source_set_synthesis._run_synthesis`): a run split into several units has each unit's client ids
  made local (`shard_N__`, as bootstrap's shards), and the units' answers are joined by the mode's
  `SynthesisCall.merge` (bootstrap: `_merge_synthesis`, as before; append: `_merge_append`, its items in pass order
  and each distinct summary once). Bootstrap's path is unchanged (it namespaced and merged as it does now).
- **After the passes** (`_within_the_brief`, only when split): same-title concepts folded (bootstrap's
  `_consolidate_same_title_concepts`), and the first restructure per target kept, the later ones dropped with a
  review record (`split_append_restructures`), since two updates of one entity in one proposal would conflict at
  apply. `_apply_concept_merges` writes `concept_relations` only on an answer that has the field (an append's
  model forbids extra keys; bootstrap's always has it, so nothing moves there).
- **The refusal stays** for what cannot be split: a single inventory whose request is over the ceiling alone is
  refused before anything is paid, by the budget's existing preflight over every unpaid pass, with the same code
  (`append_input_over_ceiling`). Its suggested action no longer says splitting "is not built yet": "a single
  section over it cannot be split into passes" (the golden `append_over_input_ceiling` moves by that string only).
- Comments and the vault's Build a Study Map note follow.

### Proofs

- **Fail-first** (`tests/test_append_split_passes.py`): an append whose request is one token over the ceiling was
  refused (`append_input_over_ceiling`). Run against the base's two synthesis modules, 8 of the file's 10 tests fail (the
two that pass: an append that fits is one request, and a single unit over the ceiling is refused); at the tip all 10
pass.
- **The same applied rows:** the same three-unit append run unsplit (one request) and split (three passes) applies
  the same `entity_source_links` rows (entity, extraction, locator, relation, status).
- **Crash and resume at every pass boundary:** the client dies on pass 1, 2 or 3; nothing is applied; the rerun asks
  only the crashed pass and those after it (the earlier passes are their checkpoints') and applies the same rows once.
- **Grouping:** with a one-token span reserve, two units share the first pass and the third gets the second; with
  the default reserve each unit has its own.
- **An append that fits is one request**, every unit in it.
- **A single unit over the ceiling** is refused before any call, nothing applied.
- **Spend per pass:** each pass is its own root request with its own receipt, under `append_output_tokens`, through
  the existing structured-call path (the transport's spend admission and receipts, the append budget's per-request
  input check, the generation limit); a metered automatic build admits each request separately, as before.
- **Cached tokens:** `render_structured_prompt` writes the task, then the context's fields sorted by name, so the
  brief, the change kind, the exam profile and the neighbourhood come before a pass's `new_inventories`: every pass
  of a split append sends the same prefix through the neighbourhood (the test checks it, and that it is most of each
  request), the part a provider's prompt cache can reuse. The receipts already record what providers report as
  cached input. No prompt change was needed for it.
- **Merge and dedupe** (pure): two passes' same-title concepts fold to one; two restructures of one target keep the
  first with a review record naming the dropped target; an unsplit answer is returned as the model wrote it.
- **Unchanged:** the 25 synthesis-tail goldens but the one refusal string; the apply-recovery tests; identity pins.

### Judgment calls to read first

1. **No total-input ceiling and no kill switch**, though the design proposed both: the brief rules out a made-up
   size threshold and a kill switch (the owner's default, 2026-11-16). What stops an append from paying for passes
   it cannot finish is the existing preflight, which checks every unpaid pass against the ceiling before the first is
   sent; what holds its money is the existing per-request spend admission and an automatic build's daily cap.
2. **No "part k of n" sentence**, which the design proposed: the owner's rule keeps the pass's position out of the
   prompt, and the brief forbids a prompt change. A pass is the model's view of an append of those inventories.
3. **One neighbourhood per run** (the design's option a, the owner's decision): selected once around all the new
   inventories by the head, recorded once in the manifest, sent with every pass.
4. **Passes are independent, not chained** (as designed): a pass's key never depends on another's answer, so a rerun
   after a changed answer re-pays only that pass; duplicates are handled after the passes.
5. **No progress line** ("part k of n" on the book card): `append_source` takes no progress callback today, and
   adding one is a separate UX change.
6. **Persisted meaning:** none. The playbook governs "scoring, scheduling, projection, or admissibility semantics";
   this changes what ingestion proposes (a proposal where there was a refusal) and reinterprets nothing stored. No
   algorithm tag; no migration (no new table or column).

### Cost (an estimate, from the request's shape; no owner book was opened)

With new inventories `I` tokens, a fixed part `F` per request (about 6,600 tokens plus the brief, exam profile and
revision diff) and a neighbourhood `N` (at most 24,000), a split into `n` passes costs about `I + n(F + N)` input,
plus up to `n` span rounds and up to `n × append_output_tokens` output, where today the append is refused. The `n - 1`
extra copies of `F + N` are the shared prefix of every pass, which a provider that caches prompts bills at its cached
rate. A retry after a failure part way pays only the passes not saved.

## Commands and results

All through the scratch wrapper (isolated home, config and temp dir), tests memory-capped at 3 GB with `-n 1`, one
command at a time.

| Command | Result |
|---|---|
| K2-20: `tests/test_queue_revision_after_applying_jobs.py` on the base | 3 failed (`assert 0 > 0`: the revision did not move) |
| K2-20 at its tip: the 28 test files among `affected_tests.py --files job_types.py`'s 207 that mention the queue revision, the three job types or `job_types`, plus the two edited test files | 799 passed, 5 skipped |
| Part B: `tests/test_append_split_passes.py` with the base's two synthesis modules | 8 failed, 2 passed |
| Part B: the same file at the tip | 10 passed |
| Part B affected tests: `affected_tests.py --files <the 4 changed src files>` listed 943; name filter: test files mentioning `append_source`, `create_study_map`, `source_set_synthesis`, `source_append`, `synthesis_tail`, `apply_recovery`, `run_synthesis`, `append_reconciliation`, `AppendReconciliation` or `consolidate_same_title`, those importing a helper that names the first four, and the apply-recovery files: 175 files, 5 chunks, `-m "not arc_close"` | 870 passed; 1,095 passed; 870 passed, 3 skipped; 656 passed; 213 passed |
| synthesis-tail golden `append_over_input_ceiling` rewritten (`SYNTHESIS_TAIL_GOLDEN_WRITE=1`) | 1 passed; the diff is the suggested action's two copies |
| `test_identity_pins.py`, `test_structure_ratchets.py`, `test_effective_defaults_golden.py`, `test_cli_help_snapshot.py`, `test_kill_switches.py`, `test_sqlite_file_copies.py` | 398 passed |
| `tests/test_test_layout.py` alone | 3 passed |
| `tests/test_architecture.py` alone | 18 passed |
| `ruff check` | All checks passed |
| `lint-imports --no-cache` | 52 kept, 0 broken |
| `scripts/check_gate_partition.py` | collected 33540: landing 33474 + arc_close 66 |
| `validate_vault.py` | passed (2,428 notes) |

No structure ratchet number moved; identity pins unchanged; no migration.


## Not verified

- The whole suite, the durability lane and the arc-close gate (the landing runs them).
- A real provider's cache hit rate on the passes' shared prefix (fakes only; the prefix is shown, not billed).
- The cost on a real book (estimate only).
