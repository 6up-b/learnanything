---
title: "learnloop_sidecar.handlers.practice_index"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop_sidecar/handlers/practice_index.py"
source_paths:
  - "src/learnloop_sidecar/handlers/practice_index.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop_sidecar.handlers"
layer: "adapter"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
  - "Import Canonical Sources"
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop_sidecar.handlers.practice_index module"
  - "src/learnloop_sidecar/handlers/practice_index.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/adapter"
  - "package/learnloop-sidecar-handlers"
---

# `learnloop_sidecar.handlers.practice_index`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop_sidecar.handlers.practice_index` exists within [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] to own the behavior summarized by its module contract: Practice-index RPCs: find_practice proposes; nothing here serves or grades.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop_sidecar/handlers/practice_index.py](../../../../../../src/learnloop_sidecar/handlers/practice_index.py) |
| Source lines | 148 |
| Owning package | [[Reference/Modules/learnloop_sidecar/handlers/_package|learnloop_sidecar.handlers]] |
| Architecture layer | `adapter` |
| Refactor status | `ACTIVE` |

## Public API

- `class FindPracticeInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 20)
- `class CallerInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 44) — Who is asking.
- `class FindPracticeRpcInput(FindPracticeInput)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 52)
- `class PracticeUsageInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 57)
- `class PracticeCoverageInput(ParamsModel)` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 65)
- `find_practice_rpc(ctx: SidecarContext, params: FindPracticeRpcInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 74) — Ranked practice proposals for a request; the scheduler still serves.
- `plan_minutes_estimator(vault: Any, repository: Any) -> Any` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 109) — The daily plan's minutes estimator, built by the adapter (the service never imports the plan).
- `record_practice_usage_rpc(ctx: SidecarContext, params: PracticeUsageInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 130) — A learner tap on a proposal (practised, skipped, too easy, not what I asked).
- `get_practice_coverage(ctx: SidecarContext, params: PracticeCoverageInput) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 145) — Facets with few admissible items (targets for more practice).

### Module constants

- `FRONTEND_CALLER_KINDS` ([src/learnloop_sidecar/handlers/practice_index.py](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 70)

## Internal implementation anchors

- `_injected(vault: Any, repository: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop_sidecar/handlers/practice_index.py), line 118) — The service's arms and valuer, injected (practice_index never imports them), with the daily plan's minutes estimator built here (the service never imports the plan).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]] — imports `module`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `plan_minutes_estimator`; statically calls `plan_minutes_estimator`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `plan_minutes_estimator`; statically calls `plan_minutes_estimator`
- [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]] — imports `_injected`, `plan_minutes_estimator`; statically calls `_injected`, `plan_minutes_estimator`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/instructional/policy|learnloop.instructional.policy]] — imports `caller_for`, `caller_for_question_event`; calls `caller_for`, `caller_for_question_event`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `propose_practice`, `service_enabled`; calls `propose_practice`, `service_enabled`
- [[Reference/Modules/learnloop/instructional/wiring|learnloop.instructional.wiring]] — imports `find_practice_injections`; calls `find_practice_injections`
- [[Reference/Modules/learnloop/practice_index/coverage|learnloop.practice_index.coverage]] — imports `coverage_report`; calls `coverage_report`
- [[Reference/Modules/learnloop/practice_index/retrieval|learnloop.practice_index.retrieval]] — imports `IntentUnavailable`, `PracticeConstraints`, `find_practice`; calls `find_practice`
- [[Reference/Modules/learnloop/practice_index/usage|learnloop.practice_index.usage]] — imports `LEARNER_SIGNALS`, `record_practice_usage`; calls `record_practice_usage`
- [[Reference/Modules/learnloop/source_retrieval/policy|learnloop.source_retrieval.policy]] — imports `PolicyRefused`
- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `SidecarContext`
- [[Reference/Modules/learnloop_sidecar/dto|learnloop_sidecar.dto]] — imports `ParamsModel`, `versioned`; calls `versioned`
- [[Reference/Modules/learnloop_sidecar/errors|learnloop_sidecar.errors]] — imports `SidecarError`; calls `SidecarError`
- [[Reference/Modules/learnloop_sidecar/registry|learnloop_sidecar.registry]] — imports `method`; calls `method`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: `pydantic`

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]
- [[Import Canonical Sources]]
- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]], [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]], [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/source_service|learnloop_sidecar.handlers.source_service]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/reading_path_fixtures.py](../../../../../../tests/reading_path_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/recap_fixtures.py](../../../../../../tests/recap_fixtures.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix10_base_sequence.py](../../../../../../tests/rw2b_fix10_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2b_fix11_base_sequence.py](../../../../../../tests/rw2b_fix11_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_base_sequence.py](../../../../../../tests/rw2c_base_sequence.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/rw2c_state_parity.py](../../../../../../tests/rw2c_state_parity.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad1_attempt_columns.py](../../../../../../tests/test_ad1_attempt_columns.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_contract.py](../../../../../../tests/test_ad23_contract.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_intent_compose.py](../../../../../../tests/test_ad23_intent_compose.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad23_successor.py](../../../../../../tests/test_ad23_successor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]
- [tests/test_ad2_serving.py](../../../../../../tests/test_ad2_serving.py) — imports consumer [[Reference/Modules/learnloop_sidecar/handlers/__init__|learnloop_sidecar.handlers]]

## Modification guidance

- Change request/response adaptation or presentation here. Put reusable learning policy in its domain package, not in the adapter.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop_sidecar/handlers/practice_index.py](../../../../../../src/learnloop_sidecar/handlers/practice_index.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
