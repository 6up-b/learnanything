---
title: "learnloop.scheduling.frame_constraints"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/scheduling/frame_constraints.py"
source_paths:
  - "src/learnloop/scheduling/frame_constraints.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.scheduling"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.scheduling.frame_constraints module"
  - "src/learnloop/scheduling/frame_constraints.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-scheduling"
---

# `learnloop.scheduling.frame_constraints`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.scheduling.frame_constraints` exists within [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] to own the behavior summarized by its module contract: The staged frame's mandatory constraint evaluation, as one function both Today's staged frame and the "Check once" gate call.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py) |
| Source lines | 301 |
| Owning package | [[Reference/Modules/learnloop/scheduling/_package|learnloop.scheduling]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `item_role(item: Any, practice_mode: str | None) -> str` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 59) — An item's role in the plan: a fresh-evidence check, or ordinary practice.
- `unavailable(part: str, exc: BaseException) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 67)
- `freshness_unknown(exc: BaseException) -> dict[str, Any]` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 74) — P4's own fail-closed refusal of a fresh-evidence item whose surface's freshness cannot be established (here: the exposure ledger could not be read).
- `class GateItem` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 86) — A "Check once" candidate as the gate evaluates it: planned in the maintain lane, as a check (``lanes.classify``).
- `class FrameEvaluation` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 98) — The mandatory verdicts over the items evaluated, and what the frame's annotations read after them (the snapshot, the reservations, the roles).
- `surfaces_by_item(repository: Any) -> dict[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 113)
- `frame_candidate(vault: Any, item: Any, role: str, states: Mapping[str, Any], surfaces: Mapping[str, Any], reserved_surface_ids: frozenset[str]) -> Any` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 129)
- `attention_block(action: str, subtype: str | None, *, budget_minutes: float, source: str, lane: Any) -> Any` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 167)
- `fallback_snapshot(candidates: Mapping[str, Any], reserved_surface_ids: frozenset[str]) -> Any` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 177) — A snapshot without the exposure ledger, for when the controller snapshot cannot be built.
- `evaluate_mandatory(vault: Any, repository: Any, items: Sequence[Any], *, clock: Any=None, block_for: Callable[[Any, str], Any], log_prefix: str='router R2a: the staged frame', item_states: Callable[[], Any] | None=None) -> FrameEvaluation` ([source](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 196) — The mandatory verdicts of ``items`` (those the vault knows), fail closed.

### Module constants

- `_LOG` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 42)
- `FRESH_EVIDENCE_MODES` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 46)
- `FRESH_EVIDENCE_CHECKS` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 48)
- `ROLE_FRESH_EVIDENCE` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 50)
- `ROLE_PRACTICE` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 51)
- `CONSTRAINTS_UNAVAILABLE_KEY` ([src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py), line 56)

### Explicit exports

`__all__` declares:

- `CONSTRAINTS_UNAVAILABLE_KEY`
- `FRESH_EVIDENCE_CHECKS`
- `FRESH_EVIDENCE_MODES`
- `FrameEvaluation`
- `GateItem`
- `ROLE_FRESH_EVIDENCE`
- `ROLE_PRACTICE`
- `attention_block`
- `evaluate_mandatory`
- `fallback_snapshot`
- `frame_candidate`
- `freshness_unknown`
- `item_role`
- `surfaces_by_item`
- `unavailable`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]] — imports `CONSTRAINTS_UNAVAILABLE_KEY`, `FRESH_EVIDENCE_CHECKS`, `FRESH_EVIDENCE_MODES`, `ROLE_FRESH_EVIDENCE`, `ROLE_PRACTICE`, `attention_block`, `evaluate_mandatory`, `item_role`; statically calls `attention_block`, `evaluate_mandatory`
- [[Reference/Modules/learnloop/scheduling/intent/feasibility|learnloop.scheduling.intent.feasibility]] — imports `GateItem`, `ROLE_FRESH_EVIDENCE`, `attention_block`, `evaluate_mandatory`; statically calls `GateItem`, `attention_block`, `evaluate_mandatory`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `compile_assessment_contract`; calls `compile_assessment_contract`
- [[Reference/Modules/learnloop/scheduling/constraint_engine|learnloop.scheduling.constraint_engine]] — imports `module`; calls `evaluate`, `manifest`
- [[Reference/Modules/learnloop/scheduling/controller_snapshot|learnloop.scheduling.controller_snapshot]] — imports `module`; calls `Candidate`, `ControllerSnapshot`, `build_snapshot`
- [[Reference/Modules/learnloop/scheduling/staged_policy|learnloop.scheduling.staged_policy]] — imports `module`; calls `AttentionBlock`
- [[Reference/Modules/learnloop/substrate/activities|learnloop.substrate.activities]] — imports `fingerprint_of`, `surface_hash`; calls `fingerprint_of`, `surface_hash`
- [[Reference/Modules/learnloop/substrate/instrument_serving|learnloop.substrate.instrument_serving]] — imports `unservable_reason`; calls `unservable_reason`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/staged_frame|learnloop.daily_plan.staged_frame]], [[Reference/Modules/learnloop/scheduling/intent/feasibility|learnloop.scheduling.intent.feasibility]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_inversion.py](../../../../../../tests/test_ad23_inversion.py) — direct import
  - `test_the_codes_vocabulary_covers_the_incumbents_reasons`
- [tests/test_intent_fix_round7.py](../../../../../../tests/test_intent_fix_round7.py) — direct import
  - `test_f22_a_frame_error_names_its_input`
- [tests/test_mobile_v4_codex_review.py](../../../../../../tests/test_mobile_v4_codex_review.py) — direct import
  - `test_f12_the_media_lift_admits_no_new_measurement_on_the_phone`

## Modification guidance

- Change frame constraints policy here when scheduling owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/scheduling/frame_constraints.py](../../../../../../src/learnloop/scheduling/frame_constraints.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
