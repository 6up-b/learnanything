---
title: "learnloop.scheduling.intent.recall_targets"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/recall_targets.py"
source_paths:
  - "src/learnloop/scheduling/intent/recall_targets.py"
source_commit: "1d5ba0272bb7d749483eea0f91c9eda2030bc4e9"
source_commit_timestamp: "2026-10-20T00:37:51-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling.intent"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.intent.recall_targets module"
  - "src/learnloop/scheduling/intent/recall_targets.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.recall_targets`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.recall_targets` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: Per-intent recall targets at serving time (spec §5.3, Q8).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py) |
| Source lines | 147 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `1d5ba0272bb7d749483eea0f91c9eda2030bc4e9` |
| Commit timestamp | `2026-10-20T00:37:51-04:00` |

## Public API

- `ratio(target: float, weights: tuple[float, ...]) -> float` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 49) — The interval multiplier for ``target`` against the stored 0.90.
- `fsrs_eligible(row: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 62)
- `anchors_from_attempts(rows: Iterable[Mapping[str, Any]], *, held: frozenset[str]=frozenset()) -> dict[str, tuple[str, str]]` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 72) — ``{item id: (anchor created_at, attempt id)}``: the latest attempt per item that wrote FSRS state (eligible, and not ``held`` for review).
- `load_anchors(connection: Any) -> dict[str, tuple[str, str]]` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 91)
- `class EffectiveDue` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 102)
- `effective_due(*, due_at: str | None, anchor_at: str | None, target: float, weights: tuple[float, ...], has_state: bool=True) -> EffectiveDue` ([source](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 109) — §5.3's effective due for one item.

### Module constants

- `STORED_RETENTION` ([src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 41)
- `FALLBACK_NO_STATE` ([src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 43)
- `FALLBACK_NO_DUE` ([src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 44)
- `FALLBACK_NO_ANCHOR` ([src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 45)
- `FALLBACK_ANCHOR_NOT_BEFORE_DUE` ([src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py), line 46)

### Explicit exports

`__all__` declares:

- `EffectiveDue`
- `FALLBACK_ANCHOR_NOT_BEFORE_DUE`
- `FALLBACK_NO_ANCHOR`
- `FALLBACK_NO_DUE`
- `FALLBACK_NO_STATE`
- `STORED_RETENTION`
- `anchors_from_attempts`
- `effective_due`
- `fsrs_eligible`
- `load_anchors`
- `ratio`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]] — imports `effective_due`, `load_anchors`; statically calls `effective_due`, `load_anchors`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `STORED_RETENTION`
- [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]] — imports `effective_due`, `load_anchors`; statically calls `effective_due`, `load_anchors`
- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `EffectiveDue`, `effective_due`, `load_anchors`; statically calls `EffectiveDue`, `effective_due`, `load_anchors`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/stores/intent_reads|learnloop.db.stores.intent_reads]] — imports `module`; calls `attempts_for_anchor`
- [[Reference/Modules/learnloop/diagnosis/causal_activity_policy|learnloop.diagnosis.causal_activity_policy]] — imports `classify_attempt_activity`; calls `classify_attempt_activity`
- [[Reference/Modules/learnloop/held_grades|learnloop.held_grades]] — imports `held_for_review_attempts`; calls `held_for_review_attempts`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `datetime`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/intent_cost|learnloop.daily_plan.intent_cost]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop/intent/report|learnloop.intent.report]], [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_codex_review.py](../../../../../../../tests/test_intent_codex_review.py) — direct import
  - `test_f4_a_held_grade_never_becomes_the_anchor_through_the_real_attempt_path`
- [tests/test_intent_recall_targets.py](../../../../../../../tests/test_intent_recall_targets.py) — direct import
  - `test_effective_due_scales_the_interval_from_the_anchor`
  - `test_fallbacks_no_state_null_due_no_anchor_and_anchor_not_before_due`
  - `test_the_anchor_reproduces_every_stored_due_at_on_fixture_copies`
  - `test_the_anchor_skips_primed_retries_and_diagnostic_attempts_but_an_ordinary_review_moves_it`
  - `test_the_ratio_is_the_fsrs_interval_ratio_and_exactly_one_at_090`

## Modification guidance

- Change recall targets policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/recall_targets.py](../../../../../../../src/learnloop/scheduling/intent/recall_targets.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
