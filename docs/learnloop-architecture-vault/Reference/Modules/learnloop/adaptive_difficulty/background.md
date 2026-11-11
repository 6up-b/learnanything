---
title: "learnloop.adaptive_difficulty.background"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/background.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/background.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.background module"
  - "src/learnloop/adaptive_difficulty/background.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.background`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.background` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: AD1's background jobs: never on a request path (spec §8.1 "off the critical path").

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py) |
| Source lines | 548 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `schedule_presentation_forecasts(vault: Any, sqlite_path: Any, presentation_id: str, *, clients: Clients | None=None, builds: Any=None, clock: Any=None, live_vault: Callable[[], Any] | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 115) — ``live_vault``: the provider of the vault loaded now (the sidecar's context's vault at check time), whose held-out predicate each request and record is checked against (fix round 4, V1).
- `prepare_items(vault: Any, repository: Any, item_ids: Iterable[str], *, clients: Clients | None=None, decider_factory: Callable[[], Any] | None=None, clock: Any=None, fence: Any=None, limit: int=PREPARE_LIMIT, live_vault: Callable[[], Any] | None=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 153) — Audit, then forecast (``llm_v1:item``), each item's current revision; once each.
- `schedule_item_preparation(vault: Any, sqlite_path: Any, item_ids: Iterable[str], *, clients: Clients | None=None, builds: Any=None, clock: Any=None, limit: int=PREPARE_LIMIT, live_vault: Callable[[], Any] | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 316) — Queue these items' current revisions for preparation, and start a run if none is running.
- `changed_revisions(previous: Any, vault: Any) -> list[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 506) — The active items whose current revision is new since ``previous`` (the vault as this process last loaded it): published, imported or edited.
- `schedule_new_revisions(previous: Any, vault: Any, sqlite_path: Any, *, item_ids: Iterable[str] | None=None, clients: Clients | None=None, builds: Any=None, live_vault: Callable[[], Any] | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 517) — Prepare the revisions published, imported or edited since the last load (Codex review F10).

### Module constants

- `LOG` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 53)
- `PREPARE_LIMIT` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 57)
- `_GUARD` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 59)
- `_INFLIGHT` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 60)
- `_DEFAULT` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 61)
- `_PREPARED` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 276)
- `_SETTLED` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 283)
- `_QUEUES` ([src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 313)

### Explicit exports

`__all__` declares:

- `PREPARE_LIMIT`
- `changed_revisions`
- `prepare_items`
- `schedule_item_preparation`
- `schedule_new_revisions`
- `schedule_presentation_forecasts`

## Internal implementation anchors

- `_registry(builds: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 64)
- `_injected(clients: Clients | None) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 75)
- `_launch(sqlite_path: Any, key: str, job: Callable[[Any], None], *, builds: Any, name: str) -> threading.Thread | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 79)
- `class _Withheld` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 184) — An item id the material view withholds: prepared as ``protected``, its content never read.
- `_prepare(vault: Any, repository: Any, items: list[Any], *, clients: Clients | None, decider_factory: Callable[[], Any] | None, clock: Any, fence: Any, live_vault: Callable[[], Any] | None, results: list[dict[str, Any]] | None=None, view: Any=None) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 191) — Prepare exactly these revisions (each an item as it was found), in order.
- `_settled(entry: dict[str, Any]) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 286)
- `class _Queue` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 294) — One vault's preparation queue (fix round 4, V2): the revisions waiting, in arrival order, as ``(item id, revision hash)`` keys only (the AD23 redesign: never content; Codex re-review F12: an edit mid-run queues the new revision beside the old one), and whether its one worker is…
- `_epoch_now(vault: Any, sqlite_path: Any) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 363) — The vault's protection epoch now (None when the predicate cannot be computed).
- `_resolve(op: Any, connection: Any, key: tuple[str, str]) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 376) — A queued key as the operation sees it: the current item when its revision is the key's, else the saved revision; :class:`_Withheld` when withheld; None when it is gone.
- `_admit(queue: _Queue, op: Any, path: str, limit: int, results: list[dict[str, Any]]) -> list[tuple[Any, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 394) — The run's batch, chosen inside its operation (the AD23 redesign; Codex verify F49, F50): every pending key already done at this epoch leaves the queue; a protected or gone one is settled without counting; the first ``limit`` visible ones are taken.
- `_start_run(sqlite_path: Any, queue: _Queue, *, builds: Any, limit: int) -> threading.Thread | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/background.py), line 437) — One run of at most ``limit`` visible revisions, unless the queue's worker is running.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]] — imports `_launch`; statically calls `_launch`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `schedule_new_revisions`; statically calls `schedule_new_revisions`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `schedule_item_preparation`, `schedule_presentation_forecasts`; statically calls `schedule_item_preparation`, `schedule_presentation_forecasts`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/feature_audit|learnloop.adaptive_difficulty.feature_audit]] — imports `audit_revision`, `item_revision`; calls `audit_revision`, `item_revision`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `forecast_history_presentation`; calls `forecast_history_presentation`
- [[Reference/Modules/learnloop/adaptive_difficulty/logs|learnloop.adaptive_difficulty.logs]] — imports `warn_failure`; calls `warn_failure`
- [[Reference/Modules/learnloop/adaptive_difficulty/material_view|learnloop.adaptive_difficulty.material_view]] — imports `detached_view`, `material_view`; calls `detached_view`, `material_view`
- [[Reference/Modules/learnloop/adaptive_difficulty/operation|learnloop.adaptive_difficulty.operation]] — imports `ad_operation`, `entry`, `epoch_of`; calls `ad_operation`, `entry`, `epoch_of`
- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `Clients`, `forecast_item`, `forecast_presentation`; calls `forecast_item`, `forecast_presentation`
- [[Reference/Modules/learnloop/adaptive_difficulty/spend|learnloop.adaptive_difficulty.spend]] — imports `module`; calls `models_off`
- [[Reference/Modules/learnloop/adaptive_difficulty/switches|learnloop.adaptive_difficulty.switches]] — imports `LLM_HISTORY`, `LLM_V1`, `LLM_V3_DECIDER`, `LLM_V3_LLM`, `any_background_work`, `feature_audit_enabled`, `outside_forecasters`; calls `any_background_work`, `feature_audit_enabled`, `outside_forecasters`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `BackgroundBuilds`; calls `BackgroundBuilds`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `logging`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/relatedness_jobs|learnloop.adaptive_difficulty.relatedness_jobs]], [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/ad23_contract_helpers.py](../../../../../../tests/ad23_contract_helpers.py) — direct import
- [tests/test_ad1_codex_review_fixes.py](../../../../../../tests/test_ad1_codex_review_fixes.py) — direct import
  - `test_overlapping_preparations_audit_a_revision_once`
  - `test_the_watchers_changed_items_are_prepared`
- [tests/test_ad1_fix_round4.py](../../../../../../tests/test_ad1_fix_round4.py) — direct import
  - `test_an_import_of_1000_revisions_prepares_at_most_20_per_run`
  - `test_two_watcher_batches_share_one_worker`
- [tests/test_ad1_fix_round5.py](../../../../../../tests/test_ad1_fix_round5.py) — direct import
  - `test_a_refused_spend_revision_is_retried_on_the_next_reload`
  - `test_an_exception_before_the_first_revision_keeps_the_whole_batch`
  - `test_an_exception_keeps_the_revision_that_raised_queued`
  - `test_busy_unavailable_and_incomplete_revisions_stay_queued`
- [tests/test_ad1_fix_round6.py](../../../../../../tests/test_ad1_fix_round6.py) — direct import
  - `test_a_harmless_reload_between_the_audits_check_and_its_record_is_retried`
  - `test_a_revision_that_keeps_raising_never_starves_the_rest`
  - `test_four_interrupted_checks_are_stale_and_retried`
- [tests/test_ad1_fix_round9.py](../../../../../../tests/test_ad1_fix_round9.py) — direct import
  - `test_the_queue_keeps_a_stopped_audit_for_a_retry`
- [tests/test_ad1_outside_and_cli.py](../../../../../../tests/test_ad1_outside_and_cli.py) — direct import
  - `test_background_jobs_run_off_the_request_path_once_each`
  - `test_without_an_injected_client_the_test_suite_starts_no_ad_job`
- [tests/test_ad_epoch.py](../../../../../../tests/test_ad_epoch.py) — direct import
  - `test_a_revision_prepared_while_protected_is_prepared_once_it_is_public`
  - `test_the_synchronous_preparation_counts_visible_revisions_only`
  - `test_twenty_protected_revisions_queued_first_never_hold_back_the_public_one`
- [tests/test_adaptive_difficulty_ad1.py](../../../../../../tests/test_adaptive_difficulty_ad1.py) — direct import
  - `test_ad1_switches_restore_predecessor`
  - `test_held_out_sentinel_never_reaches_ad_inputs`
  - `test_item_only_forecast_enters_inputs_only_if_received_before_serve`

## Modification guidance

- Make changes here when the responsibility remains background within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/background.py](../../../../../../src/learnloop/adaptive_difficulty/background.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
