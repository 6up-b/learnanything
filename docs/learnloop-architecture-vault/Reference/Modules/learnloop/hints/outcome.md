---
title: "learnloop.hints.outcome"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/outcome.py"
source_paths:
  - "src/learnloop/hints/outcome.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.outcome module"
  - "src/learnloop/hints/outcome.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.outcome`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.outcome` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: Adaptive hints H2b: outcome placement (spec_adaptive_hints_v1 §6.1, §7.2-7.3, D11).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py) |
| Source lines | 696 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OutcomePlacementV1(WireModel)` ([source](../../../../../../src/learnloop/hints/outcome.py), line 97) — Where a submitted answer stands on the item's map (strict).
- `class OutcomeResult` ([source](../../../../../../src/learnloop/hints/outcome.py), line 107) — What one placement did.
  - `as_dict(self) -> dict[str, Any]` (line 120; public)
- `placement_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/hints/outcome.py), line 124)
- `env_off() -> bool` ([source](../../../../../../src/learnloop/hints/outcome.py), line 130) — The test suite's and a vault copy's guard (no real client without an injected one).
- `claim_key(attempt_id: str) -> str` ([source](../../../../../../src/learnloop/hints/outcome.py), line 136)
- `validate_placement(answer: OutcomePlacementV1, map_payload: Mapping[str, Any], answer_md: str) -> list[str]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 249) — Why a placement cannot be used (empty: usable).
- `hint_verdict(hint: Mapping[str, Any], answer: OutcomePlacementV1, map_payload: Mapping[str, Any]) -> tuple[str, str | None, str | None]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 269) — ``(verdict, reason, target)`` for one shown hint (§6.1's "reaches the hint's target node, or, for kinds without one, the next node").
- `build_prompt(item: Any, map_payload: Mapping[str, Any], answer_md: str, feedback: Mapping[str, Any] | None=None) -> str` ([source](../../../../../../src/learnloop/hints/outcome.py), line 297)
- `place_outcome(vault: LoadedVault, repository: Repository, attempt_id: str, *, client: Any | None=None, clock: Clock | None=None, fence: 'maps.BuildFence | None'=None) -> OutcomeResult` ([source](../../../../../../src/learnloop/hints/outcome.py), line 312) — Place one hinted attempt's final answer (§6.1) and write the verdicts.
- `schedule_outcome_placement(vault: LoadedVault, sqlite_path: Any, attempt_id: str, *, client: Any | None=None, clock: Clock | None=None, builds: 'maps.BackgroundBuilds | None'=None, on_done: Callable[[OutcomeResult], None] | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/hints/outcome.py), line 464) — Start outcome placement for a submitted attempt in the background (after the submit's response is built).
- `unplaced_attempts(sqlite_path: Any, *, since: str, limit: int=RECONCILE_LIMIT) -> list[str]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 569) — Hinted attempts submitted since ``since``, graded not fully correct with an answer, and never placed: the work a process that ended (or a vault switch that fenced it) left undone.
- `reconcile_outcome_placements(vault: LoadedVault, sqlite_path: Any, *, client: Any | None=None, clock: Clock | None=None, builds: 'maps.BackgroundBuilds | None'=None, limit: int=RECONCILE_LIMIT, on_done: Callable[[OutcomeResult], None] | None=None) -> threading.Thread | None` ([source](../../../../../../src/learnloop/hints/outcome.py), line 578) — At a vault's open: place, one after another in ONE background thread, the hinted attempts of the last :data:`RECONCILE_LOOKBACK_DAYS` days that were never placed (outcome work is launched in memory after a submit, so a process that ended first, a vault switch that fenced it, or…

### Module constants

- `LOG` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 71)
- `ROUTE_TASK` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 73)
- `PURPOSE` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 74)
- `OWNER_KIND` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 75)
- `PROMPT_VERSION` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 76)
- `LEDGER_TASK` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 77)
- `CLAIM_TASK` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 78)
- `VERDICTS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 79)
- `ANSWER_CHARS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 81)
- `_CAPS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 84)
- `_INSTRUCTIONS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 87)
- `MAP_CHANGED` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 160)
- `_INFLIGHT` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 445)
- `_INFLIGHT_GUARD` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 446)
- `RECONCILE_LOOKBACK_DAYS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 529)
- `RECONCILE_LIMIT` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 530)
- `RECONCILE_PAGE` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 534)
- `_NOTHING_PLACED` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 537)
- `_INTERRUPTED` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 539)
- `_STOP` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 541)
- `_PASS` ([src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py), line 689)

### Explicit exports

`__all__` declares:

- `LEDGER_TASK`
- `OWNER_KIND`
- `OutcomePlacementV1`
- `OutcomeResult`
- `PROMPT_VERSION`
- `RECONCILE_LIMIT`
- `RECONCILE_LOOKBACK_DAYS`
- `RECONCILE_PAGE`
- `ROUTE_TASK`
- `VERDICTS`
- `hint_verdict`
- `place_outcome`
- `placement_enabled`
- `reconcile_outcome_placements`
- `schedule_outcome_placement`
- `unplaced_attempts`
- `validate_placement`

## Internal implementation anchors

- `class _Due` ([source](../../../../../../src/learnloop/hints/outcome.py), line 145)
- `_recorded_map(connection: Any, item: Any, hints: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any] | None, frozenset[str]]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 163) — The map the hints were written on (fix round 4, F14): the newest hint's recorded ``map_id`` that loads, is the item's, and was built for the item revision both the hint and today's item are at (so the prompt's question is the one the attempt answered).
- `_due(vault: LoadedVault, repository: Repository, attempt_id: str) -> tuple[_Due | None, str]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 200) — The attempt to place, or why none is due (local reads only).
- `_routes(map_payload: Mapping[str, Any]) -> dict[str, list[str]]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 244)
- `_place_claimed(vault: LoadedVault, repository: Repository, item: Any, due: _Due, claim: Any, result: OutcomeResult, *, client: Any | None, clock: Clock | None) -> OutcomeResult` ([source](../../../../../../src/learnloop/hints/outcome.py), line 344)
- `_write(repository: Repository, due: _Due, answer: OutcomePlacementV1 | None, prompt: str, *, model: str, clock: Clock | None, claim: Any, invalid: Sequence[str] | None, result: OutcomeResult) -> None` ([source](../../../../../../src/learnloop/hints/outcome.py), line 410) — One verdict per shown hint row, fenced like a map's writes.
- `_hinted(sqlite_path: Any, attempt_id: str) -> bool` ([source](../../../../../../src/learnloop/hints/outcome.py), line 449) — The attempt has a shown hint and no placement yet (a cheap read before any thread: a retry answered from its receipt asks again, review F5).
- `_unplaced_page(sqlite_path: Any, *, since: str, limit: int, after: tuple[str, str] | None=None) -> list[tuple[str, str]]` ([source](../../../../../../src/learnloop/hints/outcome.py), line 544) — One page of :func:`unplaced_attempts` as ``(created_at, id)``, after the cursor ``after`` (the last candidate of the previous page).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `reconcile_outcome_placements`; statically calls `reconcile_outcome_placements`
- [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]] — imports `schedule_outcome_placement`; statically calls `schedule_outcome_placement`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/errors|learnloop.ai.errors]] — imports `AIInterrupted`, `AIInvalidOutput`, `AIProviderUnavailable`
- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/ai/schemas|learnloop.ai.schemas]] — imports `WireModel`
- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendBudget`, `SpendCaps`, `SpendLimitExceeded`, `spend_envelopes`; calls `SpendBudget`, `SpendCaps`, `spend_envelopes`
- [[Reference/Modules/learnloop/ai/transport|learnloop.ai.transport]] — imports `render_structured_prompt`; calls `render_structured_prompt`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `parse_utc`, `utc_now_iso`; calls `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/approach_maps|learnloop.db.stores.approach_maps]] — imports `module`; calls `map_row`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/hints/map_builder|learnloop.hints.map_builder]] — imports `module`; calls `_FencedRepository`, `_claimed`, `_fenced_txn`, `_require_live`, `maps_enabled`, `maps_envelope`
- [[Reference/Modules/learnloop/hints/writer|learnloop.hints.writer]] — imports `models_off`; calls `models_off`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `PaidCalls`, `plan_route`, `resolve_client`; calls `PaidCalls`, `plan_route`, `resolve_client`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `dataclasses`, `datetime`, `json`, `logging`, `os`, `pathlib`, `threading`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]], [[Reference/Modules/learnloop_sidecar/handlers/practice|learnloop_sidecar.handlers.practice]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_hint_h2b_fix4.py](../../../../../../tests/test_hint_h2b_fix4.py) — direct import
  - `test_f13_an_interrupted_placement_stops_the_pass_at_once`
  - `test_f13_failures_that_may_follow_a_call_never_exceed_the_bound`
  - `test_f14_a_hint_is_placed_on_its_own_map_when_a_newer_one_exists_for_another_revision`
  - `test_f14_reconcile_after_a_revision_never_judges_a_hint_against_the_new_map`
  - `test_f14_the_immediate_placement_follows_the_same_rule`
- [tests/test_hint_h2b_rereview.py](../../../../../../tests/test_hint_h2b_rereview.py) — direct import
  - `test_f8_the_bound_counts_placements_not_candidates`
  - `test_f8_unplaceable_candidates_never_starve_a_placeable_one`
- [tests/test_hint_h2b_review.py](../../../../../../tests/test_hint_h2b_review.py) — direct import
  - `test_f5_a_placement_interrupted_after_its_answer_was_checkpointed_is_not_paid_again`
  - `test_f5_a_placement_never_scheduled_is_resumed_when_the_vault_opens`
  - `test_f5_reconciliation_keeps_the_switches`
- [tests/test_hint_outcome.py](../../../../../../tests/test_hint_outcome.py) — direct import
  - `test_a_closed_registry_starts_nothing_and_a_dead_fence_writes_nothing`
  - `test_a_hinted_wrong_answer_is_placed_and_each_hint_judged_measurement_only`
  - `test_a_metered_route_needs_a_price_and_joins_the_maps_envelope`
  - `test_an_attempt_is_placed_once`
  - `test_an_unusable_placement_is_reasked_once_then_recorded_unknown`
  - `test_nothing_is_placed_when_none_is_due`
  - `test_the_verdict_in_code`
- [tests/test_hint_report.py](../../../../../../tests/test_hint_report.py) — direct import
- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f15_a_partly_correct_workbench_attempt_with_a_mapped_hint_starts_no_outcome_call`
  - `test_f3r_a_hints_claim_about_part_of_a_side_is_the_models_reading`

## Modification guidance

- Make changes here when the responsibility remains outcome within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/outcome.py](../../../../../../src/learnloop/hints/outcome.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
