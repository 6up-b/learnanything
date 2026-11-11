---
title: "learnloop.router.decisions"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router/decisions.py"
source_paths:
  - "src/learnloop/router/decisions.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router.decisions module"
  - "src/learnloop/router/decisions.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router"
---

# `learnloop.router.decisions`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router/_package|learnloop.router]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router.decisions` exists within [[Reference/Modules/learnloop/router/_package|learnloop.router]] to own the behavior summarized by its module contract: Router R1: decision rows for today's serving paths (spec_action_router_v1 §9).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py) |
| Source lines | 526 |
| Owning package | [[Reference/Modules/learnloop/router/_package|learnloop.router]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class OfferHeadMismatch(RuntimeError)` ([source](../../../../../../src/learnloop/router/decisions.py), line 100) — The recomposed realized outcome does not reproduce the served head.
  - `__init__(self, message: str, *, realized_head: str | None=None, served_head: str | None=None, slate_id: str | None=None) -> None` (line 109; internal)
- `offer_failure_record(exc: BaseException, *, slate_id: str | None, surface: str | None, parent_id: str | None=None) -> DecisionRecord` ([source](../../../../../../src/learnloop/router/decisions.py), line 123) — A Today offer whose router decision could not be logged, so it was published without one (``failed``): a head mismatch names the recomposed and the served heads; any other failure its type and where.
- `split_exclusions(exclusions: Mapping[str, Iterable[str]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router/decisions.py), line 192) — ``{"named": {reason: [ids]}, "counts": {reason: n}}``, sorted and deduplicated.
- `head_distribution(outcomes: Sequence[Any], head_of: Callable[[Sequence[Any]], str | None]) -> dict[str | None, float]` ([source](../../../../../../src/learnloop/router/decisions.py), line 213) — P(each item heads the offer) over the exploration's whole support.
- `build_today_offer_decision(trace: Any, *, offered: Sequence[Any], head_of: Callable[[Sequence[Any]], str | None], section_of: Callable[[Any], str], served_head: str | None, surface: str, policy: str, in_progress: Mapping[str, Any] | None=None, removed: Mapping[str, Iterable[str]] | None=None, inputs: Mapping[str, Any] | None=None, head_served: bool=True, created_at: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router/decisions.py), line 230) — The ``router_decisions`` row for one published Today offer.
- `record_decision(repository: Any, row: Mapping[str, Any], *, alongside: Callable[[Any], Any] | None=None) -> bool` ([source](../../../../../../src/learnloop/router/decisions.py), line 493) — Append one decision row in its own transaction; idempotent on its key.
- `logging_enabled(config: Any) -> bool` ([source](../../../../../../src/learnloop/router/decisions.py), line 505)

### Module constants

- `CONTINUE_REF` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 45)
- `STOP_REF` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 46)
- `DESIGN_SCHEDULER_EXPLORATION` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 48)
- `NOT_SERVED` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 50)
- `MODE_LEGACY_QUEUE` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 51)
- `DETERMINISTIC_TOLERANCE` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 54)
- `COUNTED_EXCLUSIONS` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 60)
- `_PLANNER_SIGNALS` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 80)
- `TODAY_OFFER_RECORD` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 118)
- `HEAD_MISMATCH` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 119)
- `DECISION_NOT_BUILT` ([src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py), line 120)

### Explicit exports

`__all__` declares:

- `CONTINUE_REF`
- `DESIGN_SCHEDULER_EXPLORATION`
- `MODE_LEGACY_QUEUE`
- `NOT_SERVED`
- `DECISION_NOT_BUILT`
- `HEAD_MISMATCH`
- `OfferHeadMismatch`
- `STOP_REF`
- `TODAY_OFFER_RECORD`
- `offer_failure_record`
- `build_today_offer_decision`
- `head_distribution`
- `logging_enabled`
- `record_decision`
- `split_exclusions`

## Internal implementation anchors

- `_round(value: Any) -> Any` ([source](../../../../../../src/learnloop/router/decisions.py), line 164)
- `_exact(probability: float) -> float` ([source](../../../../../../src/learnloop/router/decisions.py), line 170) — A candidate's head probability, to 12 decimals (the row keeps the chosen candidate's at full precision).
- `_canonical_hash(value: Any) -> str` ([source](../../../../../../src/learnloop/router/decisions.py), line 177)
- `_dumps(value: Any) -> str` ([source](../../../../../../src/learnloop/router/decisions.py), line 182)
- `_propensity(probability: float) -> tuple[float, str]` ([source](../../../../../../src/learnloop/router/decisions.py), line 186)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `build_today_offer_decision`, `logging_enabled`, `offer_failure_record`, `record_decision`; statically calls `build_today_offer_decision`, `logging_enabled`, `offer_failure_record`, `record_decision`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/stores/router|learnloop.db.stores.router]] — imports `ROUTER_LOG_VERSION`, `insert_router_decision`; calls `insert_router_decision`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/provenance|learnloop.provenance]] — imports `DecisionRecord`, `is_code`, `where`; calls `DecisionRecord`, `is_code`, `where`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f8_a_crash_before_the_transaction_ends_loses_both_or_neither`
- [tests/test_forced_withdrawal_records.py](../../../../../../tests/test_forced_withdrawal_records.py) — direct import
  - `test_the_builders_keep_ids_numbers_and_codes_only`
- [tests/test_router_offer_log.py](../../../../../../tests/test_router_offer_log.py) — direct import
  - `test_a_committed_presentation_is_logged_as_the_continue_choice`
  - `test_a_draft_in_progress_is_logged_as_the_continue_candidate`
  - `test_a_draw_composition_always_undoes_is_logged_as_deterministic`
  - `test_a_recomposition_that_disagrees_with_the_served_head_is_refused`
  - `test_an_empty_offer_logs_a_deterministic_stop`
  - `test_candidate_propensities_are_one_distribution_with_continue_counted_once`
  - `test_every_counterfactual_outcome_reproduces_the_build_that_draw_would_make`
  - `test_the_snapshot_hash_covers_the_decision_inputs_not_the_build_time`
  - `test_today_offer_logs_candidates_the_served_head_and_its_exact_propensity`

## Modification guidance

- Make changes here when the responsibility remains decisions within learnloop.router; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router/decisions.py](../../../../../../src/learnloop/router/decisions.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
