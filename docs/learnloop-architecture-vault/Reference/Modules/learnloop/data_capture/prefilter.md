---
title: "learnloop.data_capture.prefilter"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/data_capture/prefilter.py"
source_paths:
  - "src/learnloop/data_capture/prefilter.py"
source_commit: "e2ddd03c640065633f2c492b62122e9750390244"
source_commit_timestamp: "2026-11-03T14:49:34-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.data_capture"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.data_capture.prefilter module"
  - "src/learnloop/data_capture/prefilter.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-data-capture"
---

# `learnloop.data_capture.prefilter`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.data_capture.prefilter` exists within [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] to own the behavior summarized by its module contract: A1: what was decided before the router saw candidates, linked into each committed decision.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py) |
| Source lines | 374 |
| Owning package | [[Reference/Modules/learnloop/data_capture/_package|learnloop.data_capture]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e2ddd03c640065633f2c492b62122e9750390244` |
| Commit timestamp | `2026-11-03T14:49:34-05:00` |

## Public API

- `canonical(value: Any) -> str` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 62)
- `content_hash(content: str) -> str` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 66)
- `code_revision() -> str` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 71) — The running code's revision: the environment's name for it, the checkout's commit, or the installed package's version, labelled.
- `class Material` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 96) — One build's prefilter, its parts already canonical, ready to link into its decisions.
  - `hashes(self) -> dict[str, str]` (line 108; public)
- `plan_pool_material(trace: Any, pool: Sequence[Any], *, session_present: bool, minutes: float, minutes_left: float | None, lanes_allowed: Sequence[str], reentry: bool, requested: Iterable[str], push: Iterable[str], deadlines: Mapping[str, str], open_problems: Iterable[str] | None, repair_rule: str, probes_planned_today: int, plan_config: Mapping[str, Any], versions: Mapping[str, Any]) -> Material` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 194) — The plan's pool: the scheduler's gates, then the lanes (A1's "no OfferTrace today").
- `today_offer_material(trace: Any, *, offered: Iterable[str], versions: Mapping[str, Any]) -> Material` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 251) — Today's composed offer: the same scheduler parts as the plan's pool.
- `decision_row_material(row: Mapping[str, Any], *, versions: Mapping[str, Any]) -> Material` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 268) — A decision whose path keeps no scheduler build: what its own row says it considered and refused, named as such (``scheduler_trace = 0``), so the report never reads it as a complete trace.
- `record(connection: Any, *, decision_id: str, decision_kind: str, material: Material | None, config: Any, at: str) -> bool` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 287) — Link ``material`` into a committed decision, on the caller's connection and transaction.
- `read(connection: Any, decision_id: str) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 327) — One decision's receipt with its parts resolved (read-only), or None.
- `admission_probability(receipt: Mapping[str, Any], practice_item_id: str) -> float | None` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 346) — The deterministic admission of an item: 1, 0, or None when the build never considered it.

### Module constants

- `RECEIPT_VERSION` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 52)
- `SURFACE_PLAN_POOL` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 53)
- `SURFACE_TODAY_OFFER` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 54)
- `SURFACE_DECISION_ROW` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 55)
- `CODE_REVISION_ENV` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 57)
- `_ROUND_DIGITS` ([src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py), line 59)

### Explicit exports

`__all__` declares:

- `CODE_REVISION_ENV`
- `Material`
- `RECEIPT_VERSION`
- `SURFACE_DECISION_ROW`
- `SURFACE_PLAN_POOL`
- `SURFACE_TODAY_OFFER`
- `admission_probability`
- `canonical`
- `code_revision`
- `content_hash`
- `decision_row_material`
- `plan_pool_material`
- `read`
- `record`
- `today_offer_material`

## Internal implementation anchors

- `_round(value: Any) -> Any` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 112)
- `_trace_parts(trace: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 116) — The scheduler's own parts of a build's trace (``OfferTrace``), ``{}`` with none.
- `_admission(admitted: Iterable[str], refused: Mapping[str, Iterable[str]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 157) — Deterministic admission as probability 1 and probability 0 (with why).
- `_material(surface: str, built: Mapping[str, Any], *, classification: Mapping[str, Any], inputs: Mapping[str, Any], config_extra: Mapping[str, Any], versions: Mapping[str, Any], considered: int, admitted: int, refused: int, session_present: bool, scheduler_trace: bool) -> Material` ([source](../../../../../../src/learnloop/data_capture/prefilter.py), line 168)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]] — imports `module`; statically calls `plan_pool_material`, `record`
- [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]] — imports `module`; statically calls `decision_row_material`, `record`
- [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]] — imports `canonical`, `code_revision`, `content_hash`; statically calls `canonical`, `code_revision`, `content_hash`
- [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]] — imports `module`; statically calls `decision_row_material`, `record`
- [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]] — imports `module`; statically calls `record`, `today_offer_material`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/data_capture/gates|learnloop.data_capture.gates]] — imports `receipts_on`; calls `receipts_on`
- [[Reference/Modules/learnloop/db/stores/data_capture|learnloop.db.stores.data_capture]] — imports `module`; calls `insert_prefilter_receipt`, `prefilter_part`, `prefilter_receipt`, `receipts_present`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `functools`, `hashlib`, `importlib`, `json`, `logging`, `os`, `pathlib`, `subprocess`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/engine|learnloop.daily_plan.engine]], [[Reference/Modules/learnloop/daily_plan/lesson_suggestion|learnloop.daily_plan.lesson_suggestion]], [[Reference/Modules/learnloop/router_objective/decision_state|learnloop.router_objective.decision_state]], [[Reference/Modules/learnloop/scheduling/controller_cutover|learnloop.scheduling.controller_cutover]], [[Reference/Modules/learnloop_sidecar/handlers/queue|learnloop_sidecar.handlers.queue]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a1_prefilter.py](../../../../../../tests/test_data_capture_a1_prefilter.py) — direct import
  - `test_a_decision_row_receipt_says_it_has_no_scheduler_trace`
  - `test_a_followups_interrupt_decision_has_the_builds_receipt`
  - `test_a_plan_built_with_no_session_links_the_schedulers_gates_into_its_decision`
  - `test_a_trace_refusal_names_every_reason_and_id`
  - `test_admission_is_probability_one_or_zero_and_the_routers_stays_conditional`
  - `test_the_code_revision_is_named_and_can_be_pinned`
  - `test_todays_offer_links_its_builds_receipt_with_every_gate`
- [tests/test_data_capture_codex_review.py](../../../../../../tests/test_data_capture_codex_review.py) — direct import
  - `test_f3_every_evaluated_probe_keeps_its_forecast_in_the_receipt_only`
  - `test_f8_a_crash_before_the_transaction_ends_loses_both_or_neither`
  - `test_f8_an_offers_receipt_commits_in_its_decisions_transaction`
  - `test_f8_the_staged_decisions_receipt_commits_with_it`
- [tests/test_data_capture_phone.py](../../../../../../tests/test_data_capture_phone.py) — direct import
  - `test_a_phone_offers_receipt_is_linked_and_names_what_it_held_back`

## Modification guidance

- Make changes here when the responsibility remains prefilter within learnloop.data_capture; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/data_capture/prefilter.py](../../../../../../src/learnloop/data_capture/prefilter.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
