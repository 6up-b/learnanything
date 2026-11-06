---
title: "learnloop.delayed_checks"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/delayed_checks.py"
source_paths:
  - "src/learnloop/delayed_checks.py"
source_commit: "workspace/uncommitted @ HEAD a21f088b16f700d0b88634b19f64720fc58016ff"
source_commit_timestamp: "2026-11-06T03:32:49-05:00"
source_worktree_state: "modified"
generated: true
generated_at: "2026-11-02"
package: "learnloop"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.delayed_checks module"
  - "src/learnloop/delayed_checks.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop"
---

# `learnloop.delayed_checks`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/_package|learnloop]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.delayed_checks` exists within [[Reference/Modules/learnloop/_package|learnloop]] to own the behavior summarized by its module contract: The delayed check's item: the candidate rule, the picker and its receipt, the date (spec_teacher_v1 §13).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/delayed_checks.py](../../../../../src/learnloop/delayed_checks.py) |
| Source lines | 169 |
| Owning package | [[Reference/Modules/learnloop/_package|learnloop]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `modified` |
| Source commit | `workspace/uncommitted @ HEAD a21f088b16f700d0b88634b19f64720fc58016ff` |
| Commit timestamp | `2026-11-06T03:32:49-05:00` |

## Public API

- `attempted_items(repository: Any) -> set[str]` ([source](../../../../../src/learnloop/delayed_checks.py), line 24)
- `revealed_items(repository: Any, lesson_id: str) -> set[str]` ([source](../../../../../src/learnloop/delayed_checks.py), line 29) — Items this lesson exposed (a reveal row with basis ``lesson:<id>``), and items whose summed exposure already reaches the auto-prime threshold (an answer would be primed: never cold).
- `lineage(item: Any) -> set[str]` ([source](../../../../../src/learnloop/delayed_checks.py), line 44) — The structural kin an item declares: its family, its contrast pair, its shared stimulus and the source exercise it presents (any shared key makes two items the same material).
- `candidates(vault: Any, repository: Any, learning_object_id: str, *, exclude: Iterable[str], withheld: Any, attempted: set[str], revealed: set[str], excluded_lineage: set[str] | frozenset[str]=frozenset()) -> list[Any]` ([source](../../../../../src/learnloop/delayed_checks.py), line 62) — The candidate rule (§13 step 1) for one LO, in id order.
- `predicted_item_success(vault: Any, repository: Any, item: Any) -> float | None` ([source](../../../../../src/learnloop/delayed_checks.py), line 86) — The active predictor's predicted unassisted success on this item: the LO's mastery (its first update's prior when it has no evidence yet) through the item's own IRT parameters.
- `pick_with_receipt(vault: Any, repository: Any, items: Sequence[Any], *, seed_key: str='') -> tuple[Any | None, dict[str, Any]]` ([source](../../../../../src/learnloop/delayed_checks.py), line 116) — The candidate pitched nearest the band's middle by its own prediction, and what was decided.
- `due_days(vault: Any, repository: Any, *, purpose: str, lesson_item_ids: Sequence[str]) -> tuple[float, str]` ([source](../../../../../src/learnloop/delayed_checks.py), line 146) — Days until the check is due, and how they were set (``retrievability`` or ``fallback``).

### Module constants

- `PICK_VERSION` ([src/learnloop/delayed_checks.py](../../../../../src/learnloop/delayed_checks.py), line 19)
- `_EXACT_TIE` ([src/learnloop/delayed_checks.py](../../../../../src/learnloop/delayed_checks.py), line 21)

### Explicit exports

`__all__` declares:

- `PICK_VERSION`
- `attempted_items`
- `candidates`
- `due_days`
- `lineage`
- `pick_with_receipt`
- `predicted_item_success`
- `revealed_items`

## Internal implementation anchors

- `_band_middle(vault: Any) -> float` ([source](../../../../../src/learnloop/delayed_checks.py), line 104)
- `_uniform(seed: str) -> float` ([source](../../../../../src/learnloop/delayed_checks.py), line 109) — A uniform in [0, 1) from the seed (53 bits of a SHA-256, as the router's draws).

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `module`; statically calls `attempted_items`, `candidates`, `due_days`, `pick_with_receipt`, `revealed_items`
- [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]] — imports `module`; statically calls `candidates`
- [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]] — imports `PICK_VERSION`, `attempted_items`, `candidates`, `due_days`, `lineage`, `pick_with_receipt`, `revealed_items`; statically calls `attempted_items`, `candidates`, `due_days`, `lineage`, `pick_with_receipt`, `revealed_items`
- [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]] — imports `candidates`, `revealed_items`; statically calls `candidates`, `revealed_items`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/followup_serve/identity|learnloop.followup_serve.identity]] — imports `generated_probe_ids`; calls `generated_probe_ids`
- [[Reference/Modules/learnloop/learner/lesson_weight|learnloop.learner.lesson_weight]] — imports `predicted_success`; calls `predicted_success`
- [[Reference/Modules/learnloop/learner/mastery|learnloop.learner.mastery]] — imports `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`; calls `initial_mastery_state_for_learning_object`, `resolve_item_irt_params`
- [[Reference/Modules/learnloop/scheduling/fsrs|learnloop.scheduling.fsrs]] — imports `interval_for_retention`; calls `interval_for_retention`
- [[Reference/Modules/learnloop/serve_eligibility|learnloop.serve_eligibility]] — imports `AUTO_PRIME_REVEAL_THRESHOLD`
- [[Reference/Modules/learnloop/vault/lifecycle|learnloop.vault.lifecycle]] — imports `practice_item_serving_block`; calls `practice_item_serving_block`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `hashlib`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/daily_plan/objective_inputs|learnloop.daily_plan.objective_inputs]], [[Reference/Modules/learnloop/teacher/delayed|learnloop.teacher.delayed]], [[Reference/Modules/learnloop/teacher/te2|learnloop.teacher.te2]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_data_capture_a2_measurement.py](../../../../../tests/test_data_capture_a2_measurement.py) — direct import
  - `test_no_question_to_ask_is_recorded_unavailable_and_visible_on_the_outcome`
- [tests/test_data_capture_a6_delayed_pick.py](../../../../../tests/test_data_capture_a6_delayed_pick.py) — direct import
  - `test_the_pick_is_the_item_nearest_the_band_not_the_smallest_id`
  - `test_the_same_lo_has_a_different_prediction_per_item`

## Modification guidance

- Make changes here when the responsibility remains delayed checks within learnloop; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/delayed_checks.py](../../../../../src/learnloop/delayed_checks.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
