# Stage "sources-spend-accounting": Codex review fixes

**Branch:** `sources/canonical-practice` (worktree `learnanything-sources`), base `ca78c7b1` (the stage record).
**Input:** Codex's review of the stage (codex-job `20261013-120614-Jg6seR`): two Medium findings (F1, F2) and four claims of the stage record that did not hold.
**Scope:** the daily cap's accounting and its report only. The cap's value, the per-operation and batch caps, subscription billing, the ledger's schema and the lease timing are unchanged.

## Findings

Each finding was reproduced first with a test that fails on `ca78c7b1` (see "Fail-first evidence"), then fixed. Neither was rejected. All tests use fakes. No vault was opened and no paid call was made.

| ID | Severity | Title | Verdict | Commit | Tests |
|---|---|---|---|---|---|
| F1 | Medium | Legacy time windows suppress unrelated paid receipts | fixed | `f9740691` | `test_source_service_spend_accounting.py::test_a_same_second_pre_ledger_receipt_is_not_a_legacy_requests_own`, `::test_overlapping_legacy_requests_cover_only_their_own_receipts`, `::test_an_ambiguous_legacy_request_counts_conservatively_and_says_so`; the stage's `::test_an_upgrade_counts_each_request_recorded_before_reservation_links_once` (F14) still passes |
| F2 | Medium | Settled embeddings are repriced at the generic LLM rate | fixed | `f9740691` | `test_source_service_spend_accounting.py::test_a_settled_embedding_counts_its_reported_cost_not_its_tokens_at_the_service_rate`, `::test_a_receipt_without_a_cost_is_priced_at_its_requests_recorded_rate`, `::test_spend_since_counts_a_reported_cost_alongside_tokens` |

### Claims that did not hold

| Claim (stage record) | Verdict | Commit | Test or correction |
|---|---|---|---|
| "Each request counts exactly once" across the upgrade | fixed with F1; claim amended | `f9740691`, record | A legacy row now covers only a receipt correlated with it beyond doubt. Where identity is ambiguous both count (conservative), so the record now says "exactly once, except an ambiguous legacy row", and the report says how much (`legacy.uncertain_usd`). |
| "When every linked receipt reports its cost, it counts exactly that cost" | fixed with F2 | `f9740691` | `::test_a_settled_embedding_counts_its_reported_cost_not_its_tokens_at_the_service_rate` (nonzero tokens alongside the reported cost). |
| The shared envelope's report exposes the new breakdown | fixed | `8382b83e` | `SharedDailyEnvelope.report()` reads `service_spend_accounting` once: `metered_usd` and `remaining_usd` from it, and the whole breakdown under `accounting` (`reservations_usd`, `unlinked_receipts_usd`, reservations by state, `recovery`, `legacy`, `pricing`). `::test_the_shared_envelopes_report_carries_the_accounting` |
| The durability test exercises eight processes | fixed | `8382b83e` | The thread test's docstring now says eight threads sharing one process token. Two new durability tests spawn real OS processes: `::test_separate_processes_race_for_the_shared_cap` (eight processes, exactly four fit, each admitted row carries its own process's owner token) and `::test_a_killed_owner_process_is_recovered_while_a_live_ones_lease_holds` (an owner killed with SIGKILL after its $0.60 receipt and before reconciling is counted at $0.60 throughout, and reconciled by this process's admission once its 5 s lease runs out, while a live process's 0.25 s heartbeat keeps its own reservation in flight until it settles). |

## Fail-first evidence

The new tests were run against `ca78c7b1`'s `source_service.py` (the fixed store swapped out):

- **F1, Codex's reproduction (through migration 192).**
  - Setup: a database at migration 191; a pre-ledger $0.80 receipt at `…50.100`; a $0.10 reservation stamped `…50Z` (to the second), settled `…51Z`; its own $0.10 receipt at `…50.600`.
  - Unfixed: the day counted $0.10 (both receipts in the row's window), so $0.20 more would be admitted under $1. Fixed: $0.90, read before and after migrating; $0.20 is refused and $0.10 admitted.
- **F1, overlapping requests.** Two legacy rows overlap (`10–15 s` at $0.20; `12–14 s` at $0.30, settled at its 30,000 tokens at the request's $10 per million, above its $0.25 reported cost), and another path's $0.15 receipt starts while both are open. Unfixed: $0.50. Fixed: $0.65.
- **F1, ambiguous identity.** Two $0.10 receipts start during one $0.10 legacy row. Unfixed: $0.10. Fixed: $0.30, with `legacy.uncertain_requests` 2 and `uncertain_usd` $0.20.
- **F2, Codex's reproduction.** A settled query embedding (as `embed_queries` sends it, no reconciliation) reports 10,000 tokens and $0.001; the service rate is $10 per million. Unfixed: $0.10, and a $0.95 request is refused under $1. Fixed: $0.001, and $0.95 is admitted.
- **F2, recorded rate.** An embedding reporting 10,000 tokens and no cost, at its recorded $0.02 per million, and three unlinked receipts (1,000 tokens each: one reporting $0.004, one recording `pf.price_per_million` $2, one recording no rate). Unfixed: $0.13. Fixed: $0.0162. Lowering the service rate reprices only the receipt that recorded none.
- **F2, `spend_since`.** A receipt reporting $0.001 with 10,000 tokens. Unfixed: $0.10. Fixed: $0.001.
- **The report.** Unfixed: `KeyError: 'accounting'`.

## What the fix does

### F1: a legacy row covers only a receipt correlated with it

Nothing names a legacy row's receipt, and its stamps are to the second. So a receipt that merely started during its lifetime may be another request's: one from before the ledger, another path's, or an overlapping request's. `db.stores.source_service._correlate_legacy` now takes a receipt for a legacy row's own, and leaves it out of the total, only when all of these hold:

- it names no reservation, is metered, and started during the row's lifetime (from the second it was reserved in to the end of the second it last changed in);
- the row settled at exactly what the receipt shows. Every metered path of that era (`PaidCalls`, `PFCaller`, the import's authoring) reconciled with the reported cost, or with the larger of it and the reported tokens at its price. Both the rate the request recorded and the owner's rate are tried;
- the receipt is the row's only such candidate, and the row is the receipt's only one. Receipts of any owner kind are candidates: when a row's own receipt matches but is not a service kind (a query embedding), a stranger that also matches makes the pair ambiguous instead of covered.

Anything less is ambiguous. Two receipts of the row's cost in its lifetime, or a row settled at its estimate (no cost reported), cover nothing: the row counts its charge and the receipts count by their own cost. That may count a request twice, never less than was spent. The accounting's new `legacy` section reports `rows`, `correlated`, `uncorrelated`, `covered_requests`, `uncertain_requests` and `uncertain_usd`: the counted receipts that started during an uncorrelated legacy row's lifetime, the most that may be counted twice. `metered.legacy_covered_requests` is kept.

The receipt scan now starts at the earliest legacy lifetime that reaches the day, so a candidate before midnight is seen. A database read without migrating gets the same rule, computed in place.

### F2: a reported cost is never repriced

`_metered_cost` now returns a receipt's dollars and their basis:

- `reported`: the provider's reported cost, exactly, whatever its tokens;
- `recorded_rate`: no reported cost; its tokens at the rate its request recorded on its root receipt when it was admitted (`practice_index.price_per_million` for `PaidCalls` and query embeddings, `pf.price_per_million` for `PFCaller`);
- `owner_rate`: no cost and no recorded rate; its tokens at `source_service.llm_price_per_million`, the explicit fallback;
- `unpriced`: unknown. A linked one is bounded by its reservation's estimate; an unlinked one is counted in `metered.unpriced_requests`, as before.

The accounting's new `pricing` section counts each basis. `spend_since` (a batch's receipts-only report) uses the same rule and reports `pricing` too.

## Residual risks and judgment calls

1. **Ambiguous legacy rows count twice.** This is the conservative side the finding asked for, and it is labelled. It can arise only on a day a legacy row's lifetime reaches: a database that ran this branch between `8ac36a38` and `be57a8fe` (39 minutes on 2026-10-13), which means `fixtures-local` copies at most. A legacy row settled at its estimate (no cost reported) correlates only if a receipt happens to show exactly that estimate; otherwise its own service-kind receipt also counts.
2. **A unique value match is the evidence.** Suppose a legacy row's own receipt does not show its settlement (it settled at its estimate, or the import's authoring priced estimated tokens), and exactly one other receipt in its lifetime happens to show its charge to within 1e-9. That receipt is taken for the row's own. When the row's own receipt is a counted service kind, the total is unchanged: the two swap roles. When it is not (a query embedding), the day is short by at most that row's charge, on that day only.
3. **A reported cost is trusted as reported.** It is no longer floored at the owner's rate. A provider that reports a cost below what it bills would be undercounted; reported costs are the providers' billing records, which is what the finding asked to count.
4. **`PaidCalls` still reconciles its own budget at the larger of the reported cost and its tokens at its price.** That bounds one operation's own caps (unchanged, outside this stage). The daily cap now counts the reported cost for a settled request whose receipts all report one.
5. **Multi-process tests are timing-tolerant, not timing-free.** The killed-owner test waits up to 120 s for the dead owner's 5 s lease to pass, and relies on the live child's 0.25 s heartbeat renewing at least once in 5 s.

## Paid calls

None. All tests use fakes. No vault copy was opened, and no command ran against a vault.

## Gate

Environment: Python 3.12.14 and SQLite 3.53.1, with `TMPDIR` set to the worktree's `fixtures-local/tmp`. The gate ran at `0c81eecf`, the last code and reference commit. Only this record and the stage record's corrections follow it.

| Check | Result |
|---|---|
| `uv sync --extra dev --extra mobile` and `uv pip install pypdfium2` | done |
| `uv run lint-imports --no-cache` | 16 contracts kept, 0 broken |
| Full suite (`flock /tmp/learnloop-fullsuite.lock uv run pytest -n auto`) | 8977 passed, 0 failed, 0 skipped (46 warnings, the same count as the stage's gate; none from the new tests). Up from 8968; the 9 new tests are all in `test_source_service_spend_accounting.py`. |
| Durability lane (`flock /tmp/learnloop-fullsuite.lock uv run pytest -m durability`) | 97 passed, 8880 deselected, 0 failed (1 warning). Up from 95; the new ones are the two separate-process tests. |
| Frontend: `npm install`, `typecheck`, `test`, `frontend:build` | Not required: nothing under `apps/learnloop-tauri` changed. |
| `cargo check` | Not required: nothing under `src-tauri` changed. |
| DB references | The schema is unchanged (migration 192's comment only). `db_generate_reference.py` regenerated `source_service_spend`'s description and the source stamps; `db_validate_reference.py` 0 errors (`0c81eecf`). |

## Open questions for the owner

- None new. The stage record's lease-timing and migration-numbering questions stand.
