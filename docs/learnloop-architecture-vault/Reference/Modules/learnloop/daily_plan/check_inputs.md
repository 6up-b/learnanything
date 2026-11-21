---
title: "learnloop.daily_plan.check_inputs"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/daily_plan/check_inputs.py"
source_paths:
  - "src/learnloop/daily_plan/check_inputs.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.daily_plan"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.daily_plan.check_inputs module"
  - "src/learnloop/daily_plan/check_inputs.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-daily-plan"
---

# `learnloop.daily_plan.check_inputs`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.daily_plan.check_inputs` exists within [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] to own the behavior summarized by its module contract: What a lesson offer's committed check needs from the vault before the router can price it (spec_teacher_v2 §7.4): whether a question exists for it now, and how long one check takes.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/daily_plan/check_inputs.py](../../../../../../src/learnloop/daily_plan/check_inputs.py) |
| Source lines | 159 |
| Owning package | [[Reference/Modules/learnloop/daily_plan/_package|learnloop.daily_plan]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class CheckMinutes` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 35) — One check's planning minutes, and where they came from.
  - `as_dict(self) -> dict[str, Any]` (line 44; public)
- `eligible_now(vault: Any, repository: Any, learning_object_id: str) -> bool` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 49) — Whether a delayed check could be committed on the LO now (the shared candidate rule; fail closed).
- `dry_check_minutes(vault: Any, repository: Any, learning_object_id: str, *, as_of: str) -> CheckMinutes` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 90) — One check's minutes on the LO from the plan's estimator over the evidence recorded by ``as_of``.
- `check_key(learning_object_id: str, purpose: str, ordinal: int) -> str` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 114) — A committed check's stable key within its offer: its topic, purpose and place, so two checks on one topic draw from streams of their own.
- `delivery_group(purpose: str) -> str` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 121) — The fitted posterior a check shares one propensity draw with: its purpose within the legacy regime.
- `check_sensors(vault: Any, repository: Any, learning_object_id: str, *, purpose: str, ordinal: int, now_iso: str, trials: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 129) — One committed check's record fields at a new decision: its key and group, the delivery posterior (the counts of ``purpose`` over ``trials``, classified as of ``now_iso``, seeded by the availability now) and its minutes, with the rollout path's versions.

### Module constants

- `ITEM_ESTIMATE` ([src/learnloop/daily_plan/check_inputs.py](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 30)
- `UNKNOWN_ITEM_ESTIMATE` ([src/learnloop/daily_plan/check_inputs.py](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 31)

### Explicit exports

`__all__` declares:

- `CheckMinutes`
- `ITEM_ESTIMATE`
- `UNKNOWN_ITEM_ESTIMATE`
- `check_key`
- `check_sensors`
- `delivery_group`
- `dry_check_minutes`
- `eligible_now`

## Internal implementation anchors

- `_evidence_as_of(vault: Any, repository: Any, as_of: str) -> Any` ([source](../../../../../../src/learnloop/daily_plan/check_inputs.py), line 65) — The estimator's duration evidence recorded by ``as_of``: the attempts known by then (the attempt ledger's availability rule) and the plan events written by then, read through the estimator's own explicit inputs.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]] — imports `check_sensors`; statically calls `check_sensors`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `dry_check_minutes`, `eligible_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/daily_plan/check_delivery|learnloop.daily_plan.check_delivery]] — imports `LEGACY_REGIME`, `module`; calls `counts`, `posterior`
- [[Reference/Modules/learnloop/daily_plan/estimates|learnloop.daily_plan.estimates]] — imports `ESTIMATE_DECIMALS`, `Estimator`, `load_duration_evidence`; calls `Estimator`, `load_duration_evidence`
- [[Reference/Modules/learnloop/db/attempt_availability|learnloop.db.attempt_availability]] — imports `attempt_time_sql`; calls `attempt_time_sql`
- [[Reference/Modules/learnloop/delayed_checks|learnloop.delayed_checks]] — imports `attempted_items`, `candidates`, `check_available`, `pick_with_receipt`, `revealed_items`; calls `attempted_items`, `candidates`, `check_available`, `pick_with_receipt`, `revealed_items`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `withheld_items`; calls `withheld_items`
- [[Reference/Modules/learnloop/router_objective/check_value|learnloop.router_objective.check_value]] — imports `POLICY_VERSION`, `STREAM_LAYOUT_VERSION`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/lesson_offer|learnloop.daily_plan.lesson_offer]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_check_credit_report.py](../../../../../../tests/test_check_credit_report.py) — direct import
  - `test_a_dependency_cannot_hide_a_request_to_write`
- [tests/test_check_inputs.py](../../../../../../tests/test_check_inputs.py) — direct import
  - `test_evidence_recorded_after_the_decision_is_not_read`
  - `test_the_adapters_write_nothing_and_call_no_model`
  - `test_the_brief_says_the_same_words_and_the_offer_reads_the_same_rule`
  - `test_the_minutes_are_the_plans_estimate_of_the_item_the_picker_would_choose`
  - `test_the_offer_adapter_fails_closed`
  - `test_with_no_candidate_the_estimators_unknown_item_estimate`

## Modification guidance

- Make changes here when the responsibility remains check inputs within learnloop.daily_plan; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/daily_plan/check_inputs.py](../../../../../../src/learnloop/daily_plan/check_inputs.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
