---
title: "learnloop.diagnosis.recurrence.display"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/recurrence/display.py"
source_paths:
  - "src/learnloop/diagnosis/recurrence/display.py"
source_commit: "a70b2c43964417511556251a4c84cd01103ff264"
source_commit_timestamp: "2026-10-12T16:11:18-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis.recurrence"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.recurrence.display module"
  - "src/learnloop/diagnosis/recurrence/display.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis-recurrence"
---

# `learnloop.diagnosis.recurrence.display`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.recurrence.display` exists within [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] to own the behavior summarized by its module contract: The escalated repair as one of the attempt's repair suggestions (Slice 2 §3.7).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/recurrence/display.py](../../../../../../../src/learnloop/diagnosis/recurrence/display.py) |
| Source lines | 83 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/recurrence/_package|learnloop.diagnosis.recurrence]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a70b2c43964417511556251a4c84cd01103ff264` |
| Commit timestamp | `2026-10-12T16:11:18-04:00` |

## Public API

- `escalation_suggestion_id(diagnosis_id: str) -> str` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 28)
- `is_escalation_suggestion(suggestion: Mapping[str, Any]) -> bool` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 32)
- `generated_repair(escalation: Mapping[str, Any] | None) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 36) — The escalation receipt's generated repair, with its suggestion id.
- `escalated_repair(repository: Any, attempt_id: str) -> dict[str, Any] | None` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 49) — The generated escalated repair of the diagnosis in force, if any.
- `displayed_repair_suggestions(vault: Any, repository: Any, attempt_id: str, suggestions: Iterable[Any] | None) -> list[dict[str, Any]]` ([source](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 58) — The attempt's repair suggestions as shown: the escalated repair first.

### Module constants

- `ESCALATION_SUGGESTION_PREFIX` ([src/learnloop/diagnosis/recurrence/display.py](../../../../../../../src/learnloop/diagnosis/recurrence/display.py), line 25)

### Explicit exports

`__all__` declares:

- `ESCALATION_SUGGESTION_PREFIX`
- `displayed_repair_suggestions`
- `escalated_repair`
- `escalation_suggestion_id`
- `generated_repair`
- `is_escalation_suggestion`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `displayed_repair_suggestions`; statically calls `displayed_repair_suggestions`
- [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]] — imports `escalation_suggestion_id`; statically calls `escalation_suggestion_id`
- [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]] — imports `displayed_repair_suggestions`, `generated_repair`, `is_escalation_suggestion`; statically calls `displayed_repair_suggestions`, `generated_repair`, `is_escalation_suggestion`
- [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]] — imports `displayed_repair_suggestions`, `is_escalation_suggestion`; statically calls `displayed_repair_suggestions`, `is_escalation_suggestion`
- [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]] — imports `displayed_repair_suggestions`; statically calls `displayed_repair_suggestions`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]], [[Reference/Modules/learnloop/diagnosis/recurrence/live|learnloop.diagnosis.recurrence.live]], [[Reference/Modules/learnloop/diagnosis/split/card|learnloop.diagnosis.split.card]], [[Reference/Modules/learnloop_sidecar/handlers/feedback|learnloop_sidecar.handlers.feedback]], [[Reference/Modules/learnloop_sidecar/handlers/serializers|learnloop_sidecar.handlers.serializers]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_causal_attribution_p0.py](../../../../../../../tests/test_causal_attribution_p0.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_causal_attribution_p1.py](../../../../../../../tests/test_causal_attribution_p1.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_causal_p2_acceptance.py](../../../../../../../tests/test_causal_p2_acceptance.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_causal_repair_mapping_p2.py](../../../../../../../tests/test_causal_repair_mapping_p2.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_causal_trace_consistency_p2.py](../../../../../../../tests/test_causal_trace_consistency_p2.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_common_repair_delivery.py](../../../../../../../tests/test_common_repair_delivery.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_diagnosis_adjudication.py](../../../../../../../tests/test_diagnosis_adjudication.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_diagnostic_augmentation.py](../../../../../../../tests/test_diagnostic_augmentation.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_dialogue_causal_join.py](../../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_durable_promotion_arms.py](../../../../../../../tests/test_durable_promotion_arms.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_minimal_repair_selection_a1.py](../../../../../../../tests/test_minimal_repair_selection_a1.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]
- [tests/test_missing_vocabulary_notes.py](../../../../../../../tests/test_missing_vocabulary_notes.py) — imports consumer [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]]

## Modification guidance

- Change display policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/recurrence/display.py](../../../../../../../src/learnloop/diagnosis/recurrence/display.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
