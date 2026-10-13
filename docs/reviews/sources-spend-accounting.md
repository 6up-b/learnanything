# Stage "sources-spend-accounting": the daily cap counts every request once

**Branch:** `sources/canonical-practice` (worktree `learnanything-sources`), base `ee3115d5`.
**Input:** Codex's latest verification of the sources build on `ee3115d5`. It left one reopened finding (F2) and one new finding (F14) in the canonical-sources service's shared daily cap, `source_service.max_daily_cost_usd`.
**Scope:** the cap's accounting only. The cap's value, the per-operation and batch caps, and subscription billing are unchanged.

## Findings

Each finding was reproduced first, with a test that fails on `ee3115d5` (see "Fail-first evidence" below), and then fixed. Neither was rejected. All tests use fakes. No vault was opened and no paid call was made.

| ID | Severity | Title | Verdict | Commit | Tests |
|---|---|---|---|---|---|
| F2 | High (reopened) | A linked receipt was suppressed whether or not its reservation had been reconciled with it | fixed | `81f08f78`, `a4b8a16f` | `test_source_service_spend_accounting.py::test_a_receipt_written_before_reconciliation_counts_its_cost`, `::test_a_request_settled_without_its_reported_cost_counts_its_receipt`, `::test_a_request_settled_without_its_cost_counts_a_lower_reported_cost`, `::test_a_finished_request_counts_its_reported_cost_once`, `::test_concurrent_admission_counts_the_unreconciled_receipt` (durability lane), plus the recovery and fencing tests below |
| F14 | Medium | Upgrading double-counted requests settled before reservation links | fixed | `81f08f78` | `test_source_service_spend_accounting.py::test_an_upgrade_counts_each_request_recorded_before_reservation_links_once` |

### Crash window, recovery and fencing tests

All of these are in `test_source_service_spend_accounting.py`:

- `test_recovery_reconciles_an_orphan_with_its_receipt`: an orphan is reconciled up to its $0.60 receipt, or down to its $0.05 receipt.
- `test_an_orphan_whose_request_never_finished_keeps_its_estimate`: the receipt is `started` with no usage, so the request counts its estimate, never $0.
- `test_recovery_releases_an_unsent_reservation_only_after_its_owner_is_terminal`: the reservation is released only once its owner's lease has run out.
- `test_a_live_owner_renews_its_lease`.
- `test_the_heartbeat_keeps_a_live_owners_lease`: the real heartbeat thread renews the lease, and stops once nothing is held.
- `test_a_released_reservation_cannot_start_its_request`: the fence.
- `test_a_receipt_naming_a_released_reservation_still_counts`: defense in depth.
- `test_a_receipt_naming_a_reservation_that_is_gone_counts_by_its_own_cost`.
- `test_a_request_reserved_yesterday_counts_on_yesterdays_cap`.
- `test_subscription_requests_are_never_refused_by_the_shared_daily_cap`: a regression guard. It passes before and after the fix.

## Fail-first evidence

The new test file was run on `ee3115d5` (unfixed code): 10 failed, 1 passed. The test that passed is the subscription regression guard.

- **F2, Codex's reproduction.** Reserve $0.15 under a $1 cap, persist a completed $0.90 receipt naming the reservation, leave the reservation unreconciled, then reserve $0.20. The $0.20 was admitted, because the total was $0.15.
- **F2, in-process variant.** The receipt recorded $0.90, reconciliation never ran, and the request settled at its $0.15 estimate. The $0.20 was admitted.
- **F2, concurrency.** Eight processes each asked for $0.125 under a $1 cap, while a dead worker's $0.50 receipt was unreconciled ($0.125 reserved). Seven were admitted; four fit. Seven admissions means $1.375 of spend.
- **F14, upgrade.**
  - Setup:
    - a database at migration 191 with $0.30 of pre-ledger service receipts;
    - a $0.20 import settled before links, whose receipt names nothing;
    - a $0.05 query embedding settled before links;
    - a linked $0.10 request.
  - The total was $0.85; it should be $0.65. The $0.20 import was counted by its row and again by its receipt.
- **Recovery and fencing tests.** They errored with `no such column: lease_expires_at`, because no recovery existed.
- **`test_a_finished_request_counts_its_reported_cost_once`.** It raised `KeyError: 'reservations_usd'`, because the report had no per-reservation basis.

Some tests were added later:

- **`test_a_request_settled_without_its_cost_counts_a_lower_reported_cost`.** On `ee3115d5` it counts the $0.30 estimate where $0.05 is expected.
- **`test_a_released_reservation_cannot_start_its_request`.**
  - It was checked against the code with the fence disabled: `model_calls.released_reservations` was monkeypatched to return nothing, in a scratch wrapper.
  - Result: "DID NOT RAISE SpendLimitExceeded". The stalled owner's request was sent.

## What the fix does

### One accounting function

`db.stores.source_service.service_spend_accounting` gives the day's total. Admission, recovery, the envelope's report and `service_spend_today` all read it. `service_spend_today` backs `daily_cap_reason`.

Each request counts exactly once:

- **A reservation whose owner is alive** (lease unexpired) counts max(its charge, what the receipts naming it show). Its charge is the estimate, reconciled upward. This closes F2: a worker that dies between persisting its receipt and `PaidCalls._reconcile` leaves both, and the receipt counts.
- **A reconciled (`settled`) reservation** counts what its receipts show:
  - When every linked receipt reports its cost, it counts exactly that cost. This holds even when the owner settled without the cost (`a4b8a16f`).
  - Otherwise it counts the larger of the receipts' cost and its reconciled charge. The charge bounds a receipt whose finish was lost.
- **An orphan** is an in-flight reservation whose owner's lease has run out. It counts what recovery makes of it:
  - reconciled with its receipts, if it has any;
  - released ($0) if it has none, since every request writes its receipt before it is sent.
  - The total already counts each orphan this way, so a read-only report agrees with the admission that will recover it.
- **A released reservation** counts what its receipts show. That is $0 unless an owner presumed dead sent anyway; see the fence below.
- **A receipt naming no reservation of the envelope** counts once by its own cost. This covers spend from before the ledger, another path, or a reservation that no longer exists.
- **A linked receipt counts on its reservation's day.** A request reserved before midnight is not counted again the next day.
- **"What the receipts show"** is each linked leaf receipt's reported cost; when a receipt reports none, its tokens are priced at the owner's rate. An unfinished or unpriced receipt is bounded by the admitted estimate, never counted as free.
- **Linked receipts count whatever their owner kind.** Retrieval requests (query embeddings, reranks) carry the reservation, so they count even though the unlinked rule covers only the service's receipt kinds.

### Admission and recovery: one transaction

`reserve_service_spend` runs inside the reservation's BEGIN IMMEDIATE transaction. It computes the total, writes recovery's resolutions, checks the total plus the estimate against the cap, and inserts the reservation with its lease. No receipt can be written between the accounting and the recovery write.

Recovery's writes are compare-and-set on `state='in_flight'` and a still-expired lease. A renewal or the owner's own settlement wins.

### Owner liveness

- `PROCESS` is the owner's token on each reservation.
- A per-process heartbeat thread (`service_spend._Leases`) renews the leases of the reservations the process holds: every `HEARTBEAT_SECONDS` = 60, for `LEASE_SECONDS` = 300.
- The thread exits when nothing is held.
- An owner is terminal when its lease has run out.

### Fencing

- **Owner writes.**
  - `charge` applies only while the reservation is in flight.
  - `settle` and `unreserve` require the owner's token.
  - The heartbeat never revives a resolved row.
- **The release fence.**
  - `record_model_event("start")` inserts a root receipt that names reservations. In the same transaction, it checks that none of those reservations was released, and refuses if one was.
  - Recovery releases only a reservation that no receipt names. So either the receipt started first, and recovery reconciles instead, or the release did, and the request is refused before it is sent.
  - The refusal is `ReservationReleased`, which carries `spend_refused`. `SpendBudget.request` re-raises it as `SpendLimitExceeded`, because the db layer cannot import `ai.spend` without a new db↔ai cycle edge.
- **A late owner's settlement.**
  - With a reported cost, it records that cost, even on a row recovery resolved: what the owner paid is the truth.
  - Without one, a resolved row keeps recovery's resolution.

### Upgrade (F14): migration 192

- **Table rebuild.** It rebuilds `source_service_spend` (WORKFLOW) with:
  - `legacy`;
  - `lease_expires_at`;
  - `resolved_by` (`owner` or `recovery`);
  - the `released` state.
- **Legacy rows.** A row is legacy when no root receipt names it. Such a row counts its own charge. The unlinked service receipts that started during its lifetime, from its reservation to the end of the second it settled in, are its own request's and are not counted again.
  - This keeps the retrieval requests of that era counted: query embeddings and reranks are not among the service's receipt kinds.
  - It keeps pre-ledger receipts counted once.
- **Unmigrated databases.** A database read without migrating gets the same rule, computed in place.
- **Indexes.** It indexes `model_call_receipts` by `started_at` and `parent_call_id`, so the per-admission scan reads only the day's receipts and finds leaves by index.
- **Fixture.** The head fixture is now `migration_head_192`: 192 applied in place, rollback journal, `integrity_check` ok, `foreign_key_check` clean. Its README and the 10 test files and 2 scripts that name it follow.

### Reports

`service_spend_today` (and the shared envelope's report) now returns:

- `usd`;
- `reservations_usd`;
- `unlinked_receipts_usd`;
- `metered.linked_requests`, `metered.legacy_covered_requests` and `metered.unpriced_requests`;
- per-state reservation counts;
- the pending `recovery` list;
- `estimated_only` for subscription requests.

Superseded helpers were removed:

- `service_spend_total`;
- `service_spend_ids`;
- `unledgered_receipts_usd`;
- `spend_since(ledgered=...)`.

`spend_since` remains the receipts-only report for a batch (a harvest's spend since it started).

### Subscription requests

Unchanged. They reserve nothing, are never refused by money, and are tallied `estimated_only` (Slice A §5 rule 6).

## Residual risks and judgment calls

1. **Legacy rows in flight.** A legacy row still in flight crashed in the brief era before receipts named reservations. It keeps counting its estimate (conservative) and is never recovered, since its receipt cannot be identified.
   - If that request had finished above its estimate before the crash, the difference is undercounted, on that row's day only.
   - Only a database that ran this branch between `8ac36a38` and `be57a8fe` (39 minutes on 2026-10-13) can hold legacy rows. That means `fixtures-local` copies at most.
   - The owner's vaults will upgrade from main with an empty ledger.
2. **Pricing receipts that report no cost.** Such a receipt is priced at the single owner rate, `source_service.llm_price_per_million`, as before. For a linked embedding or rerank receipt that reports tokens but no cost, this can overstate (conservative). A settled request whose receipts all report their cost counts exactly that cost.
3. **A crashed process's unsent reservation** holds its estimate for up to `LEASE_SECONDS` (300 s). Then the next admission releases it.
4. **Orphans of past days** stay `in_flight` in the table. They count only toward their own day, which is over. Recovery runs on the day being admitted.
5. **"No receipt means never sent"** relies on every request under the envelope writing its receipt before it is sent.
   - This was checked for every live service path:
     - `PaidCalls` with a repository;
     - `query_vectors`;
     - the import's authoring admission;
     - `PFCaller`.
   - A `PaidCalls` without a repository is a dry run and makes no request.
   - A path that wrote no receipt would still be counted while its owner lives, and by its owner's settlement.
6. **The heartbeat is a daemon thread.** A full-suite `DeprecationWarning` (fork in a multi-threaded process, `test_migration_coordinator.py`) appears identically on `ee3115d5`. It is not new.

## Paid calls

None. All tests use fakes. No vault copy was opened, and no command ran against a vault.

## Gate

Environment: Python 3.12.14 and SQLite 3.53.1, with `TMPDIR` set to the worktree's `fixtures-local/tmp`. The gate ran at `bbac6253`, the last code and reference commit. Only this record follows it.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite (`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`) | 8968 passed, 0 failed (46 warnings, all of kinds already present on `ee3115d5`). Up from 8952; the 16 new tests are all in `test_source_service_spend_accounting.py`. |
| Durability lane (`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`) | 95 passed, 8873 deselected, 0 failed. Up from 94; the new one is `test_concurrent_admission_counts_the_unreconciled_receipt`. |
| Frontend: `npm install`, `typecheck`, `test`, `frontend:build` | Not required: nothing under `apps/learnloop-tauri` changed. |
| `cargo check` | Not required: nothing under `src-tauri` changed. |
| DB references (schema changed: migration 192) | `db_generate_reference.py` at head 192 (`source_service_spend` described); `db_validate_reference.py` 0 errors (`75cb0ed6`, restamped `bbac6253`) |

## Open questions for the owner

- **Lease timing.** `LEASE_SECONDS` = 300 and `HEARTBEAT_SECONDS` = 60 are process-liveness bounds, not money decisions. A shorter lease frees a crashed process's unsent reservation sooner.
- **Migration numbering.** Migration 192 is a placeholder on this unmerged branch. It will be renumbered with 184-191 at the merge onto main.
