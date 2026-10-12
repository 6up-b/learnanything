# slice-2-t8: Codex review fixes

**Branch:** `slice-2/t8`, on top of `8e433697` (the stage record).
**Review:** codex-job `20261012-121539-M68Vla` (diff `974c5647..slice-2/t8`), 5 findings
(1 High, 3 Medium, 1 Low).
**Scope:** `src/learnloop/cli/success_head.py`, `src/learnloop/field/zero_data_llm.py`,
`src/learnloop/field/success_head_analysis.py` and the three T8 test files. There are no
migrations and no schema, config, frontend or shared-infrastructure changes. T8 still has
no live consumer.

## Findings

| ID | Severity | Title | Verdict | Commit | Test |
|---|---|---|---|---|---|
| F1 | High | Zero-data Codex calls can access the vault | **fixed** | `3cb2d80b` | `test_codex_predictions_are_isolated_turns_and_older_caches_are_not_reused`, `test_a_transport_that_cannot_isolate_the_turn_is_refused_before_any_call` (`tests/test_success_head_cli.py`); one real isolated Codex call (below) |
| F2 | Medium | The declared sequential evaluation gate is not enforced | **fixed** | `aa6b6229` | `test_a_failed_secondary_closes_the_gate_for_the_next_one` (`tests/test_success_head.py`) |
| F3 | Medium | Resume repeats paid work already committed to the ledger | **fixed** | `f7a7bf28` | `test_resume_recovers_committed_verdicts_when_the_cache_was_never_published`, `test_a_lost_cache_is_rebuilt_from_the_ledger_without_paying_again`, `test_ledger_verdicts_under_other_settings_are_not_recovered` (`tests/test_zero_data_llm.py`) |
| F4 | Medium | Concurrent preparations can publish another process's prediction | **fixed** | `f7a7bf28` | `test_concurrent_preparations_on_one_cache_never_both_pay` (`tests/test_zero_data_llm.py`) |
| F5 | Low | Subscription usage totals omit additional Codex turns | **fixed** | `f7a7bf28` | `test_codex_subscription_runs_unbounded_with_estimated_cost[enclosing_total × price]` (4 params, `tests/test_zero_data_llm.py`) |

Every finding reproduced before its fix, and none was rejected. F3–F5 share one commit
because they rewrite the same preparation loop.

## F1: zero-data Codex calls were not isolated

**Reproduction.** At `aa6b6229`, both new tests fail. They drive the real
`execute_structured_operation` with a fake structured transport, rather than
monkeypatching it as the stage's CLI test did.
- `--prepare-llm` accepted a transport that does not declare `ISOLATED_TURN`. It exited 0
  and sent every request.
- Checkpoints planted under the pre-fix settings were replayed: 0 of 7 requests were
  re-asked.

**Fix.**
- **Isolated turns.** The prediction call passes `isolated=True`.
  - `execute_structured_operation` already refuses a transport without `ISOLATED_TURN`
    before sending anything. The CLI reports that as `unavailable`, with no ledger row.
  - Codex runs the turn under its isolated-turn profile in a fresh empty directory, not
    in `vault_root`.
  - JSON repairs and regenerations stay isolated too.
  - Chat routes (`openai_chat`, `openrouter`) are isolated by construction and still
    pass.
- **Invalidation.** The route settings that key the cache now include
  `"turn": "isolated"`, which changes the settings hash.
  - Caches prepared without isolation are never replayed again. This covers this
    worktree's `fixtures-local/t8-llm-cache-fakes` and `t8-llm-cache-real`.
  - Their ledger rows are never recovered (see F3).

**Real call (verification, on the existing fakes copy).**
- **Setup.** One prediction, through `prepare_or_load_zero_data` with a single scored
  attempt.
  - Copy: `fixtures-local/t8-linear_algebra-FAKES`, a backup-API copy.
  - Cache: `fixtures-local/t8-llm-cache-real-isolated`.
  - Caps: 1 candidate, 1 call. A dry run came first.
- **What the debug log showed.** The Codex turn ran in a fresh
  `/tmp/learnloop-isolated-turn-*` directory with `isolated = true`.
  - Bubblewrap tool isolation was not configured on this copy (`sandboxed = false`), so
    the boundary was Codex's isolated-turn permission profile.
- **Result.** `p_success = 0.84`. A rerun made zero calls (`cached = 1`).

| Call | Route | Purpose | Usage and cost |
|---|---|---|---|
| 1 | Codex (`codex` profile, `gpt-5.6-sol`; subscription) | F1 interface check: one isolated zero-data prediction, after a dry run | 10,175 reported tokens against 3,424 planned. Cost `estimated_only`, no owner price, $0 metered. One judgment row and receipts recorded on the fakes copy |
| — | OpenRouter | — | 0 calls; $0 |

The earlier unisolated call recorded in `slice-2-t8.md` reported 16,385 tokens. The
isolated profile turns off Codex's tools, memories and skills, which plausibly accounts
for the smaller prompt.

## F2: a failed secondary did not close the gate

**Reproduction.** The analysis was run on synthetic arrays with 400 rows:
- `emb_ridge` gains 0.05 nats (the primary passes);
- `success_head` gains nothing over e* (`kill`);
- `success_head+difficulty` gains 0.06.

At `8e433697`, `success_head+difficulty` was labelled `interpreted`.

**Fix.** Each gated comparison is interpreted only if every earlier one passed, starting
with the primary.
- A comparison that is `kill`, `insufficient_data`, not run or `unavailable` closes the
  gate for the rest.
- Later comparisons are still computed and printed, but labelled `not_interpreted`.

This is the pre-registered hierarchy ("`success_head` against e*, … then
`success_head+difficulty` against e*"). The pre-registration and its hash are unchanged.

## F3: resume re-bought committed verdicts

**Reproduction.** The pre-fix module was run from the scratchpad with fault injection:
`os.replace` failed for the first checkpoint, after its judgment had committed.
- Resuming bought that prediction again: **2 calls and 2 judgments** for one request.
- The new tests also fail at `3cb2d80b`. The failed publication leaves `<key>.tmp`
  behind, and the summary has no `recovered` count.

**Fix.**
- **Ledger identity.** Each paid verdict is ledgered with
  `input_hash = sha256([model, prompt_version, settings_hash, request digest])`, the same
  identity that names its checkpoint file. `left_id` stays the request digest, and
  `judge_model` and `prompt_version` are stored in clear.
- **Recovery before buying.**
  - After reading the cache, preparation looks up each pending request's earliest valid
    committed verdict under that identity, publishes it, and leaves it out of the spend
    estimate. The dry run reports `recovered` and plans only the rest.
  - Right before each call, the ledger is checked again.
  - A recovered verdict is never bought again, whether its checkpoint was never
    published or the cache directory is new.
- **Durable publication.** The checkpoint is written to a uniquely named temporary file,
  fsynced and atomically renamed, and the directory is fsynced. A failure removes the
  temporary file and propagates; the CLI reports it as `invalid`. The next run then
  recovers the committed verdict.
- **Invalid verdicts.** These (score `NULL`) are still ledgered and never cached, so a
  later run re-asks them. This is unchanged and deliberate: the owner's rerun is the
  explicit retry.
- **Settings scope.** Verdicts under other settings are not recovered. One test covers
  this.

## F4: concurrent preparations on one cache both paid

**Reproduction.** With the pre-fix module, a second preparation started on the same cache
while the first one's call was in flight.
- Both paid, and 2 judgments were written for one request.
- The second preparation's arms used its own prediction (0.7), while the cache, and so
  every later replay, held the first one's (0.3).

**Fix.**
- **Lock.** A real preparation holds an advisory lock on `<cache>/.prepare.lock` for its
  whole run. The process releases it when it dies.
- **Read after locking.** The cache and ledger are read only after taking the lock.
- **Second preparation.** A second one on the same cache fails fast before any call,
  with "Another zero-data preparation is using this cache directory". This matches
  `embeddings backfill`'s lock. Once the first finishes, a rerun finds everything cached.
- **Temporary files** are uniquely named (see F3).
- **Residual.** Two preparations of the same vault on *different* cache directories are
  not locked against each other. The ledger check right before each call means only
  calls that are in flight at the same moment can both be paid. Because preparation is
  owner-run and explicit, this is noted rather than locked.

## F5: multi-turn Codex usage was undercounted

**Reproduction.** A Codex prediction made an initial turn and a JSON repair, each
reporting 10,100 tokens.
- The pre-fix `max` charged 10,100 per prediction: 60,600 for six predictions instead of
  121,200.
- That halves the estimated dollars when an owner price is given.

**Fix.**
- Usage is summed over the innermost receipts that reported it, so each physical turn
  counts once.
- A receipt is skipped when one of its descendants reported usage. An enclosing receipt
  that also totals its turns is therefore not added twice.
- The test runs both shapes (with and without an enclosing total), each with and without
  a price.

## Spec conformance after the fixes

- **R1 and §11 (zero-data, past-only).** Model access is now confined as well as the
  request builder: the Codex turn sees only its prompt.
- **R6 (pre-registration and report gates).** The hierarchical gate is enforced as
  registered.
- **Persistence, replay and durability.** Committed verdicts are recoverable,
  preparation is serialized per cache, and publication is durable. There are still no
  migrations and no new `DERIVED` tables.
- **Spend controls.** Subscription totals count every physical turn.

## Notes for the merge

- **Phase 2 has the same patterns.** `field/offline_llm.py` and `cli/field_llm.py`
  (`eval --prepare-llm`) send non-isolated requests and use the same
  max-usage/`.tmp`-checkpoint loop. That code is outside T8's scope, and router R0 is
  changing `offline_llm.py` in parallel. When R0 collapses T8's loop onto its variant
  machinery, carry over `isolated=True`, ledger-identity recovery, the cache lock and
  summed usage.
- **Ledger rows from before this fix.** T8 ledger rows written before this fix keep
  `input_hash = request digest`, on the fakes copy only. They are not recovered by
  design: they were unisolated.

## Gate

All run in this worktree at `f7a7bf28`, the final code commit.

| Check | Result |
|---|---|
| `uv sync --extra dev` (+ `uv pip install pypdfium2`) | ok |
| `uv run lint-imports --no-cache` | 10 contracts kept, 0 broken |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto` | **7128 passed**, 0 failed (172 s); the stage's 7118 plus the 10 new tests |
| `flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability` | **66 passed**, 7062 deselected |
| T8 tests (`test_success_head.py`, `test_zero_data_llm.py`, `test_success_head_cli.py`) | 19 + 21 + 12 = 52 passed |

- **Frontend:** unchanged, so no `npm` checks were needed.
- **Schema:** unchanged, so the DB reference scripts were not needed.
- **`learnloop_mobile`:** not touched, so `--extra mobile` was not needed.
