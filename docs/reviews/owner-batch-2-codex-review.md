# Owner batch 2: Codex review and fixes

Review of `b2a2bd2e..fix/owner-batch-2` (implementation final `14edd4af`),
Codex job `20261012-215249-RQLvsy`. Codex found two Medium defects and no High
ones. Both reproduced with failing tests and both are fixed. Branch
`fix/owner-batch-2`; not rebased onto main and not merged.

## Findings

| ID | Severity | Title | Verdict | Commit | Test or reason |
|---|---|---|---|---|---|
| F1 | Medium | Empty hypotheses remain cached and fail every rerun | fixed | `5ec28718` (test), `44a10e07` (fix) | `test_a_blank_hypothesis_is_never_checkpointed_and_a_fresh_run_asks_again`, `test_a_blank_checkpoint_from_earlier_code_is_discarded_and_asked_again` |
| F2 | Medium | Malformed writer output can exhaust the budget instead of becoming one failed case | fixed | `5ec28718` (test), `44a10e07` (fix) | `test_malformed_writer_json_is_one_failed_case_under_tight_caps[calls]`, `[dollars]`; guard: `test_a_transport_failure_of_the_writer_is_still_retried` |
| C1 | (claim) | The review's "not retried, not cached" claim for invalid or empty outputs is false | fixed | `44a10e07` | `docs/reviews/owner-batch-2.md` now says what the code does and points here |

All new tests are in `tests/test_recurrence_benchmarks.py`.

### F1: blank hypotheses were checkpointed

**Reproduced.** The OpenRouter writer returned `{"misconception": "   "}` for
one of four cases. Before the fix, the first run checkpointed all four results,
including the blank one: the test found 4 `pf_recurrence_hypothesis_writer`
checkpoints, not 3. A fresh run into a new output directory (a new
`PFCaller`, the same vault checkpoint store) sent 0 requests and failed the
case again. A blank checkpoint written by hand had the same effect.

**Fix.** `MisconceptionHypothesis` now has a field validator that rejects a
blank `misconception` (`diagnosis/recurrence/benchmarks.py`).
- Where the provider's output is parsed (`openai_chat._run_json_messages`
  under the metered single-request bound), a blank answer is `AIInvalidOutput`.
  It is raised before `PFCaller.call` reaches `save_model_checkpoint`, so it is
  never checkpointed. With F2's policy it is one failed case.
- A blank checkpoint saved by the earlier code no longer validates when it is
  loaded. `PFCaller.call` already discards a checkpoint that fails validation
  (`discard_model_checkpoint`), so the case is asked again and the new answer is
  checkpointed.
- It is a validator, not `min_length`, so the JSON schema is unchanged; this
  was checked by comparing `model_json_schema()` before and after. Every
  existing valid checkpoint key, which hashes the schema, still matches, so
  reruns into new output directories reuse the good checkpoints.
- B1's own `EmptyHypothesis` check stays as a fallback for clients that bypass
  validation.

**Tests.**
- `test_a_blank_hypothesis_is_never_checkpointed_and_a_fresh_run_asks_again`:
  - run 1: 4 requests, 1 failed case, 3 written, 3 checkpoints, none blank;
  - run 2 (new output directory, fresh caller): 1 request,
    `cached_by_role == {writer: 3}`, 0 failed, 4 written.
- `test_a_blank_checkpoint_from_earlier_code_is_discarded_and_asked_again`:
  one stored checkpoint is overwritten with a blank result. The next run sends
  1 request and replaces the checkpoint with the new answer.

### F2: malformed output was retried

**Reproduced.** The OpenRouter writer returned
`{"misconception": "Adds the numerators` with `finish_reason="stop"`. This is
`AIInvalidOutput`, not `AIOutputTruncated`, so `retry_truncated=False` did not
apply and `PFCaller` retried it. The test admits the plan exactly in one of
two ways:
- `max_calls` equal to the planned calls (7);
- `max_estimated_usd` equal to the plan's estimate plus half of one writer
  reservation.

Under both caps the run ended `over_budget` instead of completing.

**Fix.** `PFCaller.call(..., retry_truncated=...)` is replaced by
`retry_invalid_output: bool = True` (`ops/pf_calls.py`).
- With `False`, which B1 passes, any `AIInvalidOutput` raises at once.
  Truncated, malformed, schema-invalid and blank outputs are all subclasses or
  instances of it.
- Other `AIProviderUnavailable` failures (outages, timeouts) still retry under
  `max_retries`.
- The default is unchanged, so other PF roles still retry invalid output.
- The keyword was new on this branch (main never had `retry_truncated`), so
  the rename breaks no caller. The 5a harness fake in the tests takes the new
  name.

**Tests.**
- `test_malformed_writer_json_is_one_failed_case_under_tight_caps`, with
  `calls` and `dollars` caps:
  - the run completes with 4 writer requests (a spare queued response stays
    unused);
  - `failed_by_error == {"AIInvalidOutput": 1}`;
  - 3 written: the cases after the failed one continue;
  - the hypothesis view still has `n == 4`;
  - 0 metered retries;
  - the malformed response is in the bill (4 × $0.0002).
- `test_a_transport_failure_of_the_writer_is_still_retried`: one
  `AIProviderUnavailable` from the writer is retried. The result is 5 calls,
  1 subscription retry, 0 failed and 4 written. This test passed before the
  fix as well; it pins the part of the policy that must not change.

**Fail-first counts.** At `5ec28718` (tests only), the selection
`-k "blank or malformed or transport_failure or harness_contract"` gave
5 failed and 1 passed. The failures were the 2 F1 tests, the 2 F2
parametrizations (both `over_budget`), and
`test_b1_and_b3_run_through_phase_5as_harness_contract` (its fake took the new
keyword name). The passing test was the transport-failure guard.

### Codex's other notes

- **Spec conformance table.** Agreed. Every owner-directed item (advisory
  guard and `recurrence.require_guard`, writer-keyed cache, Markdown table,
  billed vs charged with split pricing, writer budget of 2000, truncation as a
  failed case) was assessed as implemented. The only defects were F1 and F2.
- **Missing negative tests** for malformed output and checkpoint recovery.
  These are now added (above).
- **No migration, table, replayer, serving-semantics or WAL change** in this
  fix. The defaults fingerprints are untouched: no config key changed.

## History check

- `git log b2a2bd2e..14edd4af` is one linear sequence of four commits:
  - `37e2723e`: plan and fail-first tests;
  - `947158bb`: implementation;
  - `8ad534b9`: regenerated reference;
  - `14edd4af`: record.
- The branch reflog shows only those four commits after its creation from
  `b2a2bd2e`. There are no resets, amends or rewrites. This matches the stage
  note that the original workflow instance edited nothing and the resumed
  instance made all four commits.
- `docs/reviews/owner-batch-2.md` lists the same commits, plan before
  implementation. Its only false claim, the failed-case behaviour, is corrected
  in `44a10e07`.
- This review adds:
  - `5ec28718`: fail-first tests;
  - `44a10e07`: the fix and the claim correction;
  - this record.

## Paid calls

None. Every test uses fakes (`tests/openai_fakes.py`, injected writers). No
real call was needed: the defects are in LearnLoop's own retry and checkpoint
logic, and the fakes drive the production OpenRouter parser.

## Gate (at `44a10e07`; this record adds docs only)

| Step | Result |
|---|---|
| `uv sync --extra dev --extra mobile` | ok |
| `uv pip install pypdfium2` | ok (5.14.0) |
| `uv run lint-imports --no-cache` | 12 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **8285 passed**, 0 failed (4m31s); 8280 at `8ad534b9` plus the 5 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **87 passed**, 8198 deselected |
| DB reference generate / validate | not run: no schema or config change |
| Frontend | not run: not changed |

All runs used `TMPDIR` = the worktree's `fixtures-local/tmp`.
