---
title: "learnloop.router_objective.decision_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/decision_state.py"
source_paths:
  - "src/learnloop/router_objective/decision_state.py"
source_commit: "2079aa1eb02ced81c4ed4449672db9e2e437e45b"
source_commit_timestamp: "2026-11-04T16:51:26-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.decision_state module"
  - "src/learnloop/router_objective/decision_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.decision_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.decision_state` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 rows 9 and 13 (spec_router_objective_v1 §4): what the router believed at one decision.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py) |
| Source lines | 376 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `2079aa1eb02ced81c4ed4449672db9e2e437e45b` |
| Commit timestamp | `2026-11-04T16:51:26-05:00` |

## Public API

- `class Material` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 54) — One decision's state, canonical, ready to link when the decision commits.
- `candidate_ids(vault: Any, candidates: Iterable[Mapping[str, Any]], *, extra_items: Iterable[str]=(), extra_los: Iterable[str]=()) -> tuple[list[str], list[str]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 75) — The items and LOs a decision's candidates name, in any of the shapes the ledger holds.
- `prepare(vault: Any, repository: Any, *, candidates: Iterable[Mapping[str, Any]], session_id: str | None, forgetting_curve: Callable[..., float], item_minutes: Mapping[str, Mapping[str, Any]] | None=None, block_minutes: Mapping[str, Any] | None=None, stop: Mapping[str, Any] | None=None, voi: Iterable[Mapping[str, Any]]=(), pick: tuple[str | None, str | None] | None=None, extra_items: Iterable[str]=(), extra_los: Iterable[str]=(), ad_fields: AdFields | Mapping[str, Any] | None=None, versions: Mapping[str, Any] | None=None, omitted: Mapping[str, Any] | None=None, clock: Clock | None=None) -> Material | None` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 290) — Read one decision's state.
- `record(connection: Any, *, decision_id: str, decision_kind: str, material: Material | None, config: Any, at: str) -> bool` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 355) — Link ``material`` into a committed decision, on the caller's transaction.

### Module constants

- `RECEIPT_VERSION` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 38)
- `_ROUND_DIGITS` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 40)
- `AD_NOT_READ` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 42)
- `AD_UNAVAILABLE` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 43)
- `_VOI_FIELDS` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 45)
- `_ACTIVE_BASIS` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 47)
- `_STAMP` ([src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py), line 48)

### Explicit exports

`__all__` declares:

- `AD_NOT_READ`
- `AD_UNAVAILABLE`
- `AdFields`
- `Material`
- `RECEIPT_VERSION`
- `candidate_ids`
- `prepare`
- `record`

## Internal implementation anchors

- `_round(value: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 67)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 71)
- `_item_rows(connection: Any, items: Sequence[str], now: datetime, weights: Any, forgetting_curve: Callable[..., float], minutes: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 103)
- `_lo_rows(connection: Any, los: Sequence[str], ad: Mapping[str, Any]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 123)
- `_reader_visits(connection: Any, since: str) -> tuple[list[tuple[datetime, datetime, float]], float]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 169) — The Reader visits reported since ``since``, each as ``(start, end, active seconds)``, and the active seconds of those that give no interval.
- `_in_window(visit: tuple[datetime, datetime, float], low: datetime, high: datetime) -> float` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 191) — A visit's active seconds inside ``[low, high]``.
- `_active_minutes(connection: Any, session_id: str | None, day_start: datetime, now: datetime) -> tuple[float | None, float, dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 201) — Session and day active minutes: attempts' latency and Reader visits' active seconds, two clocks apart from elapsed time.
- `_pending_reports(connection: Any, now_iso: str) -> dict[str, int | None]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 230) — What the learner or the router is still waiting to hear: each count None where the table is absent.
- `_goals(vault: Any) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 249)
- `_config_hash(config: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 262) — The config's hash, once per loaded config: a large dump, read at every decision.
- `_voi(decisions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 271)
- `_pick_verdict(verdicts: Sequence[Mapping[str, Any]], pick: tuple[str | None, str | None] | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/decision_state.py), line 275) — For a pick, the verdict in force on what was picked: on the item, else on its LO.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `candidate_ids`, `prepare`, `record`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `prepare`, `record`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `module`; statically calls `prepare`, `record`
- [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]] — imports `module`; statically calls `_pending_reports`, `_round`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `prepare`, `record`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `candidate_ids`, `prepare`, `record`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `objective_receipts_on`; calls `objective_receipts_on`
- [[Reference/Modules/learnloop/data_capture/prefilter|learnloop.data_capture.prefilter]] — imports `canonical`, `code_revision`, `content_hash`; calls `canonical`, `code_revision`, `content_hash`
- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `insert_decision_state`, `table_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/params/fitted_params|learnloop.params.fitted_params]] — imports `resolve_fsrs_weights`; calls `resolve_fsrs_weights`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]], [[Reference/Modules/learnloop/router_objective/tail_serve|learnloop.router_objective.tail_serve]], [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] and 1 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
  - `test_f8_a_phone_visits_active_time_reaches_the_routers_activity_readers`
- [tests/test_ro0_codex_review.py](../../../../../../tests/test_ro0_codex_review.py) — direct import
  - `test_f2_the_forced_shape_names_its_item`
  - `test_f3_a_list_that_served_no_head_still_decides_nothing_and_reads_no_ad`
  - `test_f3_the_staged_bridge_hands_its_decision_the_ad_reader`
- [tests/test_ro0_rows9_13_decision_state.py](../../../../../../tests/test_ro0_rows9_13_decision_state.py) — direct import
  - `test_a_path_that_reads_no_ad_says_so`
  - `test_a_state_that_cannot_be_read_never_touches_the_decision`
  - `test_ad_failing_is_said_and_everything_else_is_kept`
  - `test_the_candidate_shapes_of_the_ledger`
- [tests/test_ro6_codex_review.py](../../../../../../tests/test_ro6_codex_review.py) — direct import
  - `test_f4_a_diagnosis_queued_after_the_decisions_moment_never_enters_its_features`

## Modification guidance

- Make changes here when the responsibility remains decision state within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/decision_state.py](../../../../../../src/learnloop/router_objective/decision_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
