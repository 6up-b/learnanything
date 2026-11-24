---
title: "learnloop.router_objective.check_replay"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/check_replay.py"
source_paths:
  - "src/learnloop/router_objective/check_replay.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.router_objective.check_replay module"
  - "src/learnloop/router_objective/check_replay.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.check_replay`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.check_replay` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: A lesson-offer decision's lossless numeric replay payload (the committed-check credit, ``mvp-0.62``): every number the numeric policy valued the decision's candidates on, as one canonical JSON string with its SHA-256 digest, so a later report can recompute the decision's values…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py) |
| Source lines | 161 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `encode(value: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 66) — ``value`` as plain JSON values: each supported dataclass as ``{"type", "fields"}`` with every field.
- `decode(value: Any) -> Any` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 82) — :func:`encode`'s inverse (lists come back as tuples); a dataclass missing any field is refused.
- `untyped(action: Action) -> Action` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 99) — ``action`` priced the predecessor's way: each typed check its ``(LO, days)`` pair, through every branch.
- `carries_typed_checks(actions: Sequence[Action]) -> bool` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 115) — Whether any candidate (or a branch of one) carries typed committed checks.
- `canonical(body: Mapping[str, Any]) -> str` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 125)
- `record(inputs: Inputs, actions: Sequence[Action], *, seed: str, draws: int, first_draws: int, max_draws: int, as_of: str, options: Mapping[str, Any], versions: Mapping[str, Any], sensors: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 129) — The payload for one decision's numeric answer, or None when a number cannot be written exactly (NaN or an infinity) or a type is not one this format knows: such a decision is not replayable, and says nothing else.
- `read(stored: Mapping[str, Any]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/check_replay.py), line 146) — A stored payload decoded, after its version and digest are checked (``ValueError`` otherwise).

### Module constants

- `REPLAY_VERSION` ([src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py), line 56)
- `TRACE_KEY` ([src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py), line 58)
- `_CLASSES` ([src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py), line 59)
- `_FROZENSET` ([src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py), line 62)
- `_REGISTRY` ([src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py), line 63)

### Explicit exports

`__all__` declares:

- `REPLAY_VERSION`
- `TRACE_KEY`
- `canonical`
- `carries_typed_checks`
- `decode`
- `encode`
- `read`
- `record`
- `untyped`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `module`; statically calls `read`, `record`
- [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]] — imports `module`; statically calls `carries_typed_checks`, `record`
- [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]] — imports `TRACE_KEY`

### Repository tooling consumers

- [scripts/check_credit_report.py](../../../../../../scripts/check_credit_report.py); calls `decode`, `encode`, `read`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/ad_link|learnloop.router_objective.ad_link]] — imports `AdLink`, `LessonCurve`
- [[Reference/Modules/learnloop/router_objective/diagnostic_payload|learnloop.router_objective.diagnostic_payload]] — imports `Channel`, `DiagnosticProbe`, `Hypothesis`, `MissingChannel`, `RepairOption`
- [[Reference/Modules/learnloop/router_objective/memory|learnloop.router_objective.memory]] — imports `Combiner`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `Action`, `CauseSplit`, `CheckCommitment`, `DatedUse`, `EffectSlope`, `Inputs`, `Learning`, `Price`, `Topic`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `hashlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/daily_plan/objective_chooser|learnloop.daily_plan.objective_chooser]], [[Reference/Modules/learnloop/router_objective/trace_assembly|learnloop.router_objective.trace_assembly]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_check_credit_activation.py](../../../../../../tests/test_check_credit_activation.py) — direct import
  - `test_both_tags_the_decisions_numeric_answer_and_its_trace`
  - `test_the_payload_is_lossless_and_refuses_what_it_cannot_hold`
  - `test_the_report_reads_a_new_decision_exactly`

## Modification guidance

- Make changes here when the responsibility remains check replay within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/check_replay.py](../../../../../../src/learnloop/router_objective/check_replay.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
