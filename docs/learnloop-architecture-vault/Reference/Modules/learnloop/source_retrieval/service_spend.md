---
title: "learnloop.source_retrieval.service_spend"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/source_retrieval/service_spend.py"
source_paths:
  - "src/learnloop/source_retrieval/service_spend.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.source_retrieval"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.source_retrieval.service_spend module"
  - "src/learnloop/source_retrieval/service_spend.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-source-retrieval"
---

# `learnloop.source_retrieval.service_spend`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.source_retrieval.service_spend` exists within [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] to own the behavior summarized by its module contract: The canonical-sources service's shared money bounds (spec_source_practice_and_probes_v1 SC10, §7.5).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py) |
| Source lines | 375 |
| Owning package | [[Reference/Modules/learnloop/source_retrieval/_package|learnloop.source_retrieval]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class SharedDailyEnvelope(SpendEnvelope)` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 153) — The daily cap, reserved transactionally in the vault database.
  - `__init__(self, vault: LoadedVault, repository: Repository, *, day: str, cap: float, clock: Clock | None=None, name: str=DAILY_ENVELOPE, owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS, price_per_million: float | None | object=_SERVICE_PRICE) -> None` (line 164; internal)
  - `_now(self) -> str` (line 184; internal)
  - `accounting(self, connection: sqlite3.Connection, now: str | None=None) -> dict[str, Any]` (line 187; public)
  - `_total(self) -> Decimal` (line 191; internal)
  - `reservation_ref(self, handle: object) -> str | None` (line 195; public)
  - `reserve(self, usd: Decimal) -> object` (line 198; public)
  - `unreserve(self, handle: object) -> None` (line 215; public)
  - `charge(self, usd: Decimal, handle: object=None) -> None` (line 223; public)
  - `settle(self, handle: object, actual: Decimal | None=None) -> None` (line 229; public)
  - `report(self) -> dict[str, object]` (line 238; public) — The inherited report (this process's refusals and ``estimated_only`` tally), with the day's total and its full breakdown (``accounting``: reservations by state, pending recovery, legacy coverage, pricing) from one read of ``service_spend_accounting``.
- `daily_accounting(connection: sqlite3.Connection, vault: LoadedVault, since: str, *, envelope: str=DAILY_ENVELOPE, now: str | None=None, owner_kinds: Sequence[str] | None=SERVICE_OWNER_KINDS, price_per_million: float | None | object=_SERVICE_PRICE) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 256) — The daily cap's total since ``since`` (UTC midnight): the one function admission, recovery and every report read.
- `subscription_providers(vault: LoadedVault) -> frozenset[str]` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 271) — Provider names whose profile bills the owner's subscription.
- `midnight(clock: Clock | None=None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 278)
- `service_spend_today(vault: LoadedVault, repository: Repository, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 282) — The service's spend since UTC midnight, as the daily cap counts it: metered dollars (``usd``: ``reservations_usd``, every reservation counted once with its receipts, plus ``unlinked_receipts_usd``) and the subscription's ``estimated_only`` tokens and dollars.
- `spend_report(vault: LoadedVault, repository: Repository, *, days: int=7, top: int=5, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 292) — The service's actual spend over the last ``days`` UTC days (today included), for setting caps from real use (owner, 2026-10-13): per day the metered receipt cost and the reservations, reserved vs settled; the largest operations; and today's daily guard (what admission counts, th…
- `daily_envelope(vault: LoadedVault, repository: Repository, clock: Clock | None=None) -> SpendEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 330) — The daily envelope for this database and UTC day, shared through the database by every process (one object per process for its threads).
- `service_spend(vault: LoadedVault, repository: Repository, *, max_usd: float | None=None, name: str='operation', clock: Clock | None=None) -> Iterator[dict[str, SpendEnvelope]]` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 347) — The daily envelope, plus one for this operation when ``max_usd`` is given.
- `batch_envelope(name: str, max_usd: float) -> SpendEnvelope` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 358)

### Module constants

- `DAILY_ENVELOPE` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 69)
- `PROCESS` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 71)
- `LEASE_SECONDS` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 76)
- `HEARTBEAT_SECONDS` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 77)
- `_SERVICE_PRICE` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 81)
- `_DAILY` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 83)
- `_DAILY_LOCK` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 84)
- `_LEASES` ([src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 150)

### Explicit exports

`__all__` declares:

- `DAILY_ENVELOPE`
- `HEARTBEAT_SECONDS`
- `LEASE_SECONDS`
- `SharedDailyEnvelope`
- `batch_envelope`
- `daily_accounting`
- `daily_envelope`
- `midnight`
- `service_spend`
- `service_spend_today`
- `spend_report`
- `subscription_providers`

## Internal implementation anchors

- `class _Leases` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 87) — This process's reservations in flight, whose leases it renews while it lives.
- `_clock_key(clock: Clock | None) -> str` ([source](../../../../../../src/learnloop/source_retrieval/service_spend.py), line 323) — One shared envelope per database and day for the system clock; an injected clock (a test's, a replay's) gets its own, stamped by it.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `spend_report`; statically calls `spend_report`
- [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]] — imports `service_spend`, `service_spend_today`; statically calls `service_spend`, `service_spend_today`
- [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `SharedDailyEnvelope`, `daily_accounting`, `midnight`; statically calls `SharedDailyEnvelope`, `daily_accounting`, `midnight`
- [[Reference/Modules/learnloop/hints/service|learnloop.hints.service]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/instructional/exposure|learnloop.instructional.exposure]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `batch_envelope`, `service_spend`, `subscription_providers`; statically calls `batch_envelope`, `service_spend`, `subscription_providers`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/instructional/reader_digest|learnloop.instructional.reader_digest]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `SharedDailyEnvelope`, `daily_envelope`, `midnight`; statically calls `SharedDailyEnvelope`, `daily_envelope`, `midnight`
- [[Reference/Modules/learnloop/instructional/screen|learnloop.instructional.screen]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/instructional/sources|learnloop.instructional.sources]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/source_retrieval/compare|learnloop.source_retrieval.compare]] — imports `service_spend`; statically calls `service_spend`
- [[Reference/Modules/learnloop/source_retrieval/deliverables|learnloop.source_retrieval.deliverables]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/source_retrieval/library_ask|learnloop.source_retrieval.library_ask]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/source_retrieval/passage_cues|learnloop.source_retrieval.passage_cues]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/source_retrieval/reading_paths|learnloop.source_retrieval.reading_paths]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/source_retrieval/section_coverage|learnloop.source_retrieval.section_coverage]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `SharedDailyEnvelope`, `midnight`; statically calls `SharedDailyEnvelope`, `midnight`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendEnvelope`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendEnvelope`, `SpendLimitExceeded`, `spend_envelopes`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/source_service|learnloop.db.stores.source_service]] — imports `SERVICE_OWNER_KINDS`, `charge_service_spend`, `release_service_spend`, `renew_service_spend_leases`, `reserve_service_spend`, `service_spend_accounting`, `service_spend_report`, `settle_service_spend`; calls `charge_service_spend`, `release_service_spend`, `renew_service_spend_leases`, `reserve_service_spend`, `service_spend_accounting`, `service_spend_report`, `settle_service_spend`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `SUBSCRIPTION_PROFILE_TYPES`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `decimal`, `pathlib`, `sqlite3`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]], [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/content/authoring/source_exercise_import|learnloop.content.authoring.source_exercise_import]], [[Reference/Modules/learnloop/figures/routes|learnloop.figures.routes]], [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] and 16 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_exam_protection.py](../../../../../../tests/test_exam_protection.py) — direct import
  - `test_the_daily_envelope_stamps_its_rows_with_the_injected_clock`
- [tests/test_sidecar_idle_threads.py](../../../../../../tests/test_sidecar_idle_threads.py) — direct import
  - `test_the_lease_heartbeat_ends_when_its_last_lease_is_dropped`
- [tests/test_source_service_spend_accounting.py](../../../../../../tests/test_source_service_spend_accounting.py) — direct import
  - `test_a_finished_request_counts_its_reported_cost_once`
  - `test_a_killed_owner_process_is_recovered_while_a_live_ones_lease_holds`
  - `test_a_live_owner_renews_its_lease`
  - `test_a_receipt_naming_a_released_reservation_still_counts`
  - `test_a_receipt_naming_a_reservation_that_is_gone_counts_by_its_own_cost`
  - `test_a_receipt_without_a_cost_is_priced_at_its_requests_recorded_rate`
  - `test_a_receipt_written_before_reconciliation_counts_its_cost`
  - `test_a_released_reservation_cannot_start_its_request`
  - `test_a_request_reserved_yesterday_counts_on_yesterdays_cap`
  - `test_a_request_settled_without_its_cost_counts_a_lower_reported_cost`
  - `test_a_request_settled_without_its_reported_cost_counts_its_receipt`
  - `test_a_settled_embedding_counts_its_reported_cost_not_its_tokens_at_the_service_rate`
  - `test_an_upgrade_counts_every_request_and_reports_the_unprovable_overlap`
  - `test_concurrent_admission_counts_the_unreconciled_receipt`
  - `test_recovery_reconciles_an_orphan_with_its_receipt`
  - `test_separate_processes_race_for_the_shared_cap`
  - `test_the_heartbeat_keeps_a_live_owners_lease`
- [tests/test_source_service_spend_envelopes.py](../../../../../../tests/test_source_service_spend_envelopes.py) — direct import
  - `test_a_settled_request_is_counted_once_not_by_its_receipt_and_its_reservation`
  - `test_the_daily_cap_is_shared_by_concurrent_processes`
  - `test_the_daily_guard_refuses_past_five_dollars`
  - `test_the_sources_report_shows_actual_spend_reserved_vs_settled_and_the_largest_operations`

## Modification guidance

- Make changes here when the responsibility remains service spend within learnloop.source_retrieval; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/source_retrieval/service_spend.py](../../../../../../src/learnloop/source_retrieval/service_spend.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
