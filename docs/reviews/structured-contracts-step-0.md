# Structured contracts, step 0: the shared step with no caller

## Amended by step 5

The orchestrator clarified the owner's “one re-ask” decision: `MAX_STRUCTURED_RECOVERIES = 1`
counts **contract re-asks only**, not provider schema repairs. Each of the initial and corrective
attempts retains the provider's existing allowance of one schema repair, independently of the
contract credit. Every repair still requires the caller's explicit `admit`, remaining deadline
and no cancellation; outside a checked call the hooks remain inert. This supersedes the shared-credit
descriptions and stopping assertions below. Exact preservation wins: both previously successful
three-request follow-up sequences, and the captured four-request sequence, must remain successful.
See [the step-5 record](structured-contracts-step-5.md) for the changed assertions, durable adapter,
baseline, verification, and the separate unresolved question about existing transport retries.

Status: built on branch `ai/structured-contracts-0` from `2f761915a2`; not landed. Commits `a0ab70c423` (the
module, its registered count, the transport hook, tests) and `29a6b6f83b` (the provider hooks, their tests).

The owner decided on 2026-11-20 that every structured model call gets one shared step: an answer that parses but
fails a declared contract predicate is discarded and the request is sent once more with the stated requirement,
both calls receipted, inside the caller's existing budget. This step builds the mechanism only. No production
caller declares a contract, so no request, prompt, receipt, checkpoint, identity or behaviour changes. No prompt,
schema, config key, algorithm tag, kill switch or migration was added; no identity pin or golden moved.

## Public shape as built

`src/learnloop/ai/structured_contracts.py`:

- `Predicate(name, holds, requirement)`, frozen. `name` is snake_case; `requirement` is one nonblank line with no
  surrounding whitespace (checked at construction). `holds` must return a `bool`: `first_failure` raises
  `TypeError` otherwise, so a predicate returning a list or `None` cannot pass or fail by accident.
- `Contract = tuple[Predicate[T], ...]`, and `contract_of(*predicates)`, which refuses a non-predicate and two
  predicates with one name (a correction names its predicate). An empty contract is allowed: the declaration that
  the schema already says everything required.
- `first_failure(contract, answer)`: declared order, first failure wins, later predicates are not evaluated.
- `correction_prompt(first_prompt, predicate)`: `{first_prompt}\n\nThe previous answer failed validation:
  {name}. {requirement} Write the complete answer again, satisfying all the original requirements.` Byte-equal to
  the follow-up author's existing re-ask for all six of its reasons (tested through `request_authored_probe`).
- `MAX_STRUCTURED_RECOVERIES = 1`, and `RECOVERY_NOTE = "structured_recovery"` (the receipt note's key).
- `ContractRejected(Exception)`: raised by the shared check inside the operation; deliberately not an
  `AIProviderUnavailable`, so no existing outage retry catches it.
- `RecoveryState(recoveries=0, owed=None)` with `as_dict` / `from_dict`, for a durable job to store and restore.
- `RecoveryAllowance(admit=None, remaining_seconds=None, min_request_seconds=0.0, cancelled=None,
  state=RecoveryState(), record=None, defer=False)`.
- `Attempt(ordinal, prompt, timeout_seconds, correcting=None)`: what the caller's `send` is asked to send.
- `ContractFailure(reason, predicate, state, sends)`, handed to the caller's `failure`.
- `checked_structured_call(*, first_prompt, contract, send, recovery, checkpoint, failure, request_key=None,
  usage=None) -> T`, and `checked_structured_answer(...)` with the same arguments returning
  `CheckedAnswer(answer, reused, sends, state, discarded)`.
- Hooks read by the transport and providers: `claim_schema_repair()`, `recovery_remaining_seconds()`,
  `correction_in_flight()`. Outside a checked call they return `True`, `None`, `False`.
- Receipt recovery: `recovery_note(budget_json)` and `recover_from_receipts(receipts, *, first_prompt,
  request_key, contract, read)`.

Inert hooks in existing code:

- `transport.execute_structured_operation(..., check=None)`: when given, `check(result)` runs after
  `metadata["output_text"]` is set and before the operation's receipt closes. In `_execute_request`'s legacy branch,
  a correction in flight is refused with `AIProviderUnavailable` (the endpoint adapter builds its request from the
  legacy context, so the requirement would never reach the model).
- `providers/chatgpt_plan.py`: the schema-repair branch asks `claim_schema_repair()` after the existing
  `single_request` refusal; `complete()` takes `at = min(own deadline, now + recovery_remaining_seconds())` when a
  checked call is active, so a background stream's twenty-minute ceiling never restarts on a re-ask. With no
  checked call, `_monotonic()` is read exactly once, as before.
- `providers/openai_chat.py`: the same `claim_schema_repair()` in `_run_json_messages`'s repair branch.
- `params/parameter_registry.py`: `structured_contracts` joins `MODULE_INVENTORY` (whole-module audit, as
  `followup_run_jobs`), and `structured_contracts:MAX_STRUCTURED_RECOVERIES` is registered `constraint`,
  `structural`, rationale "keep: 2026-11-20 owner decision: one corrective recovery, shared by schema repair and
  parsed-contract re-ask; further admission remains caller-owned."

### Departures from the design, with reasons

1. **Two optional arguments and an outcome form.** `request_key` names the original request on a correction's
   receipt when the caller's checkpoint is not a `ModelCheckpoint` (PaidCalls keeps its own envelope), defaulting
   to `checkpoint.key`. `usage` mirrors `ModelCheckpoint.answer(usage=...)`. `checked_structured_answer` returns
   whether the answer was reused, how many requests were sent and the final state: callers and tests need them.
   `checked_structured_call` returns `T` as designed.
2. **The allowance's deadline is a callable, `remaining_seconds`, not an absolute time.** A durable job's
   deadline is wall-clock and persisted (UX-45 keeps a `datetime`); the plan provider's is monotonic. A callable
   lets each side read its own clock; the plan provider converts it at the moment it builds its deadline.
   `min_request_seconds` (default 0.0) carries the follow-up author's one-second floor when it adopts.
3. **`RecoveryState.owed` and `defer`.** A rejection is recorded as owed before the recovery is claimed, and the
   claim is recorded before the correction is sent. A restart then sends the owed correction, not the first request
   again, and never sends a claimed recovery twice. `defer=True` records the owed correction and fails with
   `correction_deferred`, which is the shape the durable follow-up job needs ("no synchronous second call inside
   `author_probe`").
4. **The schema repair needs the same admission as the contract re-ask.** Inside a checked call the plan or chat
   provider's repair is sent only if the recovery is unspent, not cancelled, within time and admitted by `admit`.
   An adopter that today relies on the plan route's hidden repair keeps it only by passing an `admit`. This follows
   "no ambient authorization", and it is a change an adoption step must name.
5. **An unparsed first answer whose provider made no repair here propagates unchanged.** Under `single_request`
   the provider raises `AIInvalidOutput` without repairing; that stays the caller's own handling (PaidCalls retries
   it under its retry cap). The step converts an `AIInvalidOutput` to a terminal failure only when a recovery was
   claimed or refused for it, or it came from a correction.
6. **A stale checkpoint's discard does not owe a correction.** The design's order sends the first request
   unchanged when no paid answer exists; the failed predicate is kept as `CheckedAnswer.discarded`.
7. **The terminal classification is the step's own.** `ContractRejected` is outside the
   `AIProviderUnavailable` tree, and every exhaustion goes through the caller's `failure`. Reordering PaidCalls'
   catches so its failure type is terminal there is adoption work (design step 16).
8. **Receipt recovery is a pure helper.** `recover_from_receipts` reruns the contract and checks the correction's
   linkage (note names the original key, a declared predicate, ordinal within the count, and the prompt hash is the
   deterministic correction's). PaidCalls' `receipt_answer` is unchanged: it already skips failed receipts, and
   finding a corrected receipt needs its prompt-hash lookup widened, which belongs to its adoption.
9. **Not hooked here:** E0's direct Messages branch (a caller, design step 22). The chat provider gets no deadline
   hook: it already treats `timeout_seconds` as the total deadline of its retry loop, and the design names only the
   plan provider's ceiling. The plan provider's `_Deadline.reason` still says `ceiling` for a background stream even
   when the call's own deadline is what cuts it.

## The state machine

```
start
  checkpoint hit?  -- holds the contract --> return it (reused, nothing sent)
                   -- fails ----------------> discard that exact stored value; note the predicate
  state.owed set?  -- unknown to the contract --------> failure(unknown_requirement), nothing sent
                   -- recoveries already spent -------> failure(contract_failed), nothing sent
                   -- claim refused ------------------> failure(<refusal>), nothing sent
                   -- claimed --> send the correction for owed
  otherwise        --> send the first request, unchanged
send (the ledger active; a correction's receipt carries the recovery note)
  ContractRejected or the returned answer fails --> rejected(predicate)
  AIInvalidOutput, first request, no repair claimed or refused here --> propagate (caller's own)
  AIInvalidOutput otherwise --> failure(schema_failed | the repair's refusal)
  AIOutputTruncated, any other exception --> propagate unchanged
  accepted --> save under the original key; return
rejected(predicate)
  recoveries spent --> failure(contract_failed)
  record owed = predicate
  defer --> failure(correction_deferred)
  claim: spent? cancelled? remaining <= min_request_seconds? admit()? (admit last; it may reserve budget)
    refused --> failure(recovery_spent | cancelled | deadline | recovery_refused)
    claimed --> record recoveries + 1; send the correction (back to send)
```

The provider's schema repair uses the same claim from inside the send (`claim_schema_repair`), so one credit
covers both: malformed, repaired, then contract-failing stops; contract-failing, then a malformed correction gets
no repair and stops.

## Receipt and checkpoint rules

- A rejected answer finishes its operation receipt as `failed` with `error_type = "ContractRejected"`; its answer
  stays in `output_text` for analysis. Its physical child receipts are unchanged honest records of the send.
  `completed_root_receipts` (and so PaidCalls' receipt recovery) never returns it.
- The correction is an ordinary operation receipt under the same owner. Its root `budget_json` carries
  `{"structured_recovery": {"request_key": ..., "failed": ..., "ordinal": 1}}` beside whatever the caller
  declared. A successful first request's receipt has no note: its bytes are as before.
- Only an accepted answer is saved, under the original key. A stored answer that fails the contract is discarded
  by its exact value, so a fresh answer another run saved meanwhile survives; the write-once slot keeps the first
  saved answer.
- `recover_from_receipts` reruns the contract on every receipt answer: one that parses but fails is never reused.

## The budget rule

The step holds no money. `admit` is the caller's retry slot and budget, asked last, just before a recovery would
be sent; `None` sends no recovery at all, whatever time or output budget remains. The correction runs on what
remains of the caller's one deadline (`Attempt.timeout_seconds`) and is refused when that is at or under
`min_request_seconds`, or when `cancelled()` is true; in those cases `admit` is not asked, so nothing is reserved.
The metered test shows the shape PaidCalls will take: the correction is admitted and charged by the caller's
`SpendBudget` as `calls=1, retries=1`, and with no retry left nothing further is sent.

## The registered count

`MAX_STRUCTURED_RECOVERIES = 1`, in `learnloop.ai.structured_contracts`, registered as above. The step's loop
honours the constant (a recovery is claimed only while `recoveries < MAX_STRUCTURED_RECOVERIES`), and the schema
repair and the contract re-ask spend the same count.

## Proof that nothing existing moved

1. **A capture of contract-free calls, base tree against new tree.** A scratch script (not tracked) ran, with fakes
   only: the plan route over the local fake server (a valid answer; a JSON-object repair; a `single_request`
   refusal; a background request; a budget stated in the prompt with a failed repair), the chat route on the
   OpenRouter adapter with the fake `openai` module (valid; repaired; `single_request` refusal), a
   `checkpointed(...).answer` cycle over an unreadable stored answer, and PaidCalls through
   `generate_dossiers` on a metered route (a transport failure, an invalid answer, then a dossier) in a fresh
   practice vault. It recorded the request bodies (7 plan, 4 chat, 3 paid), every receipt event (24 plan, 14 chat;
   6 receipt rows and 1 checkpoint row in the vault), results, checkpoint store calls and the PaidCalls charge,
   with ids, timestamps and the fake server's port masked. Base tree (the branch point's `src` and `migrations`
   exported by `git archive`) and new tree produced the same output, sha256
   `0925e1c4416ba5aa66ae25a8ea131e2f2e6c48929bf05b33cd4403f71497eade`; two runs of the new tree were identical.
   The capture includes both providers' repair requests, so a hook that was not inert would change the counts.
2. **Identity pins, shapes and the AST coverage scan pass unchanged** (no golden regenerated), as do the
   structure ratchets (no number rose: the new module joins no import cycle), the effective-defaults golden, the
   CLI surface snapshot, the kill-switch tests, the SQLite copy audit and the public-tip guards.
3. **Every existing test in the touched area passes unchanged**: the name-filtered selection below (plan route,
   chat and OpenRouter clients, transport parity, checkpoints, PaidCalls, registry audit, the follow-up author's
   retry) and every test file that calls `execute_structured_operation` or the providers' repair directly.
4. In tests: `test_without_a_contract_an_operation_and_its_receipt_are_as_before` (no note, completed receipt, hooks
   return `True` / `None` / `False`), the chat provider still repairs once outside a checked call, and a background
   plan request outside a checked call runs under its own ceiling.

## Tests (tests first) and fail-first evidence

New: `tests/test_structured_contracts.py` (42 tests, parametrized cases counted), `tests/structured_contracts_helpers.py` (shared doubles).
Extended, appended only, no existing assertion changed:

- `tests/test_model_work_checkpoints.py`: a held saved answer is reused with nothing sent; a failing one is
  discarded by its exact value and paid once (first request unchanged); the race (another run's fresh answer
  survives the discard); a rejected answer is never saved, the correction is saved under the original key and
  reused after a restart.
- `tests/test_chatgpt_plan_provider.py`: first request unchanged and one correction on the real plan transport
  (bodies equal except `input`; the rejected root receipt failed with its answer kept); malformed, repaired,
  contract-failing stops at two requests; contract-failing, malformed correction gets no repair; no admitted
  recovery sends no plan repair; a background request gets no fresh ceiling past the call's deadline.
- `tests/test_practice_index_paid.py`: on the metered OpenRouter adapter, the correction is admitted and charged as
  a retry; with no retry left nothing more is sent; the rejected answer stays only on a failed receipt and only the
  correction is recoverable, under its original key and no other.

The new module and the tests were written first, then run against the unchanged transport, providers and
registry; then the transport hook was added and the tests run again; then the provider hooks and the registry.

| Run | Result |
|---|---|
| The four test files, transport, providers and registry unchanged | 29 failed, 70 passed in 10.52s: every failure `execute_structured_operation() got an unexpected keyword argument 'check'` |
| Same, transport hook added | 6 failed, 93 passed in 10.15s: the five provider-hook tests (no repair refusal, no deadline cap: `DID NOT RAISE`) and one test of mine reading the deadline once too few times (fixed: the deadline is read for the first request, the recovery's admission and the correction) |
| Same plus `tests/test_registry_audit.py`, all hooks and the registration | 119 passed in 15.17s |

The pure contract and state-machine tests could only fail first by the module's absence. An attempt to run the
final tests against the exported base tree through `PYTHONPATH` ran the worktree's code instead (pytest's own
`pythonpath` setting comes first: 99 passed), so it is not counted as evidence.

## Commands and results

Every command ran through the scratch wrapper (empty home, Codex home and config directory; isolated temp dir).
Pytest ran through a runner script that refuses an empty target list and runs
`uv run --no-sync pytest -q -n 1 -p no:cacheprovider <targets>`, inside
`systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=1G`, one command at a time.

| Command | Result |
|---|---|
| runner: the four new/extended test files + `tests/test_registry_audit.py` | 119 passed in 15.17s |
| runner: `tests/test_identity_pins.py tests/test_structure_ratchets.py tests/test_effective_defaults_golden.py tests/test_cli_help_snapshot.py tests/test_kill_switches.py tests/test_sqlite_file_copies.py tests/test_public_tip_guards.py` | 400 passed in 80.42s |
| runner: `tests/test_test_layout.py` alone | 3 passed in 20.01s |
| runner: `tests/test_architecture.py` alone | 18 passed in 33.39s |
| runner, `-m "not arc_close"`: the 29 files named with model_work, checkpoint, chatgpt_plan, structured, practice_index_paid, registry_audit, followup_authoring, execution, transport, openai_chat or openrouter (one chunk) | 479 passed in 112.32s |
| runner, `-m "not arc_close"`: the 16 other test files that call `execute_structured_operation` or a provider repair directly, plus `tests/test_followup_generate_e2e.py` and `tests/test_t6_followup_composition.py` | 238 passed in 108.84s |
| runner: `tests/test_identity_pins.py` at the tip | 345 passed in 16.78s |
| `uv run --no-sync ruff check` | All checks passed! |
| `uv run --no-sync lint-imports --no-cache` | Contracts: 44 kept, 0 broken. |
| `uv run --no-sync python scripts/check_gate_partition.py` | collected 32173: landing 32108 + arc_close 65 |
| `git diff --check` | exit 0, no output |

`scripts/affected_tests.py --files` over the five changed source files lists 972 test files; the name filter above
(the brief's names plus transport, openai_chat and openrouter) and the direct-caller list were run instead.

## What section 7 of the design left open, as far as step 0 settles it

- **The crash test** (bounded, with fakes): a crash after the rejection and before the claim resumes with the
  correction, not the first request; a crash after the claim and before the corrected response sends nothing
  again; a crash after the corrected response and before the checkpoint save recovers the correction from its
  receipt under the original key, checkpoints it, and the next run reuses it with nothing sent. Not settled: a real
  process kill and the durable job's own storage of `RecoveryState` (follow-up adoption, step 5).
- **Admission**: proven at the step: nothing but `admit` authorizes a recovery (a deadline, spare time or an output
  budget does not), and admission is asked only after time and cancellation allow a request. Not settled: which
  existing authorization each A-boundary's real service adapter has; each adoption step must find it or stop
  after the rejection.

## What a live-route walk must check when the first caller adopts it

1. A valid first answer on the plan route: one request, prompt/schema/settings hashes unchanged, one operation
   receipt without a recovery note.
2. A real schema-valid empty answer: its operation receipt failed with the answer kept; the correction carries
   exactly the fixed requirement and nothing else; the second request is separately admitted and receipted with the
   note naming the original key; the accepted answer is reused after a restart with nothing sent.
3. Two bad answers: the caller's existing failure, and a second drain sends no third request.
4. The deadline: the correction runs on what remains; a depleted budget or time sends nothing; a background
   correction does not get a fresh twenty-minute ceiling (the physical stream, not a fake).
5. The repair interaction observed as physical requests: malformed, repaired, contract-failing stops; contract-
   failing, malformed correction stops. And whether the adopter passed an `admit` that keeps the plan route's repair.
6. Blindness: the first and correction payloads of a blind grade and a follow-up author differ only by the suffix.
7. One non-plan route (OpenRouter) with its own usage receipts and no provider fallback.

## What was not verified

No live or paid model call, no real stream cancellation or socket deadline, no real process kill, no durable job,
no desktop or phone surface, no vault of the owner's. The fakes cannot prove server streaming, physical billing or
cancellation (the fake server stands in for the plan route). The full landing and arc-close gates were not run
(the orchestrator's). The vault references were not regenerated (the landing does). No ledger row: no defect was
found. One observation for an adopter: the plan provider reads `request.timeout_seconds or <profile timeout>`, so a
caller passing `0.0` gets the profile's timeout; no caller passes zero today (PaidCalls and the follow-up author
refuse before sending), and inside a checked call the deadline hook bounds it anyway.
