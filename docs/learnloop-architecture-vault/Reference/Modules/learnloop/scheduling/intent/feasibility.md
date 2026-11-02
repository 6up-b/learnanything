---
title: "learnloop.scheduling.intent.feasibility"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/intent/feasibility.py"
source_paths:
  - "src/learnloop/scheduling/intent/feasibility.py"
source_commit: "c1de0032d999d9d3f59dea633bdc007db0a9de59"
source_commit_timestamp: "2026-10-20T15:38:36-04:00"
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
  - "learnloop.scheduling.intent.feasibility module"
  - "src/learnloop/scheduling/intent/feasibility.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling-intent"
---

# `learnloop.scheduling.intent.feasibility`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.intent.feasibility` exists within [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] to own the behavior summarized by its module contract: The one "Check once" feasibility gate (DL2 fix round 6, orchestrator ruling).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py) |
| Source lines | 213 |
| Owning package | [[Reference/Modules/learnloop/scheduling/intent/_package|learnloop.scheduling.intent]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `c1de0032d999d9d3f59dea633bdc007db0a9de59` |
| Commit timestamp | `2026-10-20T15:38:36-04:00` |

## Public API

- `reserved_assessment_items(repository: Any) -> frozenset[str]` ([source](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 66) — The practice items whose surface holds a live assessment reservation (the staged frame's own read).
- `class CheckGate` ([source](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 77) — The gate for one intent view: each read once, on first use; the frame's evaluation once, over every due check's candidates together.
  - `__init__(self, vault: Any, repository: Any, *, now: datetime, admission: Callable[[str], Any] | None, candidate_ids: Iterable[str]) -> None` (line 81; internal)
  - `_protected(self, key: str) -> frozenset[str] | None` (line 103; internal) — One protected set, read once; None when it could not be read (round 7, F22: each input fails closed under its own name).
  - `_frame_refusals(self) -> dict[str, tuple[dict[str, Any], ...]]` (line 120; internal)
  - `refusal(self, item_id: str) -> dict[str, Any] | None` (line 163; public) — Why ``item_id`` can never be a check's item now, or None.

### Module constants

- `_LOG` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 45)
- `SOURCE` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 47)
- `HELD_OUT_KEY` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 48)
- `ASSESSMENT_RESERVATION_KEY` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 49)
- `EXAM_POOL_KEY` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 50)
- `ADMISSION_KEY` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 51)
- `UNAVAILABLE_KEY` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 52)
- `FRAME_INPUT` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 54)
- `_BLOCK_MINUTES` ([src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 56)

### Explicit exports

`__all__` declares:

- `ADMISSION_KEY`
- `ASSESSMENT_RESERVATION_KEY`
- `CheckGate`
- `EXAM_POOL_KEY`
- `HELD_OUT_KEY`
- `UNAVAILABLE_KEY`
- `reserved_assessment_items`

## Internal implementation anchors

- `_refusal(key: str, reason: str, **detail: Any) -> dict[str, Any]` ([source](../../../../../../../src/learnloop/scheduling/intent/feasibility.py), line 59)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]] — imports `CheckGate`; statically calls `CheckGate`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `FrozenClock`; calls `FrozenClock`
- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `module`; calls `held_out_items`
- [[Reference/Modules/learnloop/goals/exam_pool|learnloop.goals.exam_pool]] — imports `module`; calls `reserved_item_ids`
- [[Reference/Modules/learnloop/scheduling/controller_actions|learnloop.scheduling.controller_actions]] — imports `module`
- [[Reference/Modules/learnloop/scheduling/frame_constraints|learnloop.scheduling.frame_constraints]] — imports `GateItem`, `ROLE_FRESH_EVIDENCE`, `attention_block`, `evaluate_mandatory`; calls `GateItem`, `attention_block`, `evaluate_mandatory`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `datetime`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/scheduling/intent/serving|learnloop.scheduling.intent.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_intent_fix_round5.py](../../../../../../../tests/test_intent_fix_round5.py) — direct import
  - `test_f16_the_frames_constraints_refuse_a_reserved_check_on_their_own`
- [tests/test_intent_fix_round7.py](../../../../../../../tests/test_intent_fix_round7.py) — direct import
  - `test_f22_a_protected_set_error_names_its_input`

## Modification guidance

- Change feasibility policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/intent/feasibility.py](../../../../../../../src/learnloop/scheduling/intent/feasibility.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
