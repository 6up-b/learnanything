---
title: "learnloop.router_objective.diagnostic_payload"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/diagnostic_payload.py"
source_paths:
  - "src/learnloop/router_objective/diagnostic_payload.py"
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
  - "learnloop.router_objective.diagnostic_payload module"
  - "src/learnloop/router_objective/diagnostic_payload.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.diagnostic_payload`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.diagnostic_payload` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: What the diagnostic layer hands the router about one possible post-miss probe: the locked hypotheses, the probe's channel ``P(result | hypothesis)`` or its explicit absence, the repair each hypothesis needs, the probe's duration, whether its answer is already exposed, and the ha…

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py) |
| Source lines | 278 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Hypothesis` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 34) — One locked hypothesis: its id, its prior (or effective posterior) mass, and its cause class (one of :data:`miss_cause.CLASSES`: a gap, a slip, or unknown; the open hypothesis is unknown).
  - `__post_init__(self) -> None` (line 42; internal)
- `class Channel` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 50) — A complete channel: for each hypothesis id, in ``rows``' order, ``P(result | hypothesis)`` over ``results``.
  - `__post_init__(self) -> None` (line 61; internal)
  - `row(self, hypothesis: str) -> tuple[float, ...]` (line 70; public)
- `class MissingChannel` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 78) — No channel exists at the decision, and why (an unauthored probe, an instrument with no likelihood, ...).
- `class RepairOption` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 85) — One executable repair the policy may choose after the probe's result (or now, without it): the repair block (an :class:`types.Action` of kind repair on the factor's topic) and the hypotheses it covers.
- `class DiagnosticProbe` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 97) — The diagnostic payload of one probe candidate (design §2a's table), as plain values.
  - `__post_init__(self) -> None` (line 122; internal)
  - `effective_prior(self) -> dict[str, float]` (line 142; public) — Each hypothesis's mass after the routing weights, normalized; every locked hypothesis keeps its entry.
  - `summary(self) -> dict[str, Any]` (line 150; public) — The payload as plain JSON values (what the evaluator was given).
- `class OwnerDecisions` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 193) — The G2 design's owner decisions 1 to 3 as the evaluator's named inputs (decision 4, the launch tradeoff, is decided from the comparison report and changes no pricing).
  - `__post_init__(self) -> None` (line 205; internal)
  - `record(self) -> dict[str, Any]` (line 214; public)
- `posterior_table(probe: DiagnosticProbe) -> tuple[str, list[dict[str, Any]]]` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 235) — The results the policy can see and the posterior after each: ``(channel use, rows)``, each row ``{"result", "p", "posterior", "joint"}`` with ``joint[h] = p(h)·L(r|h)``.
- `effect_key(option: RepairOption | None, hypothesis: Hypothesis) -> str` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 261) — Which effect a repair has when ``hypothesis`` is true: its cause class's slope when the repair covers it, ``uncovered`` when it does not, ``none`` for no repair.
- `weights_from(mapping: Mapping[str, float]) -> tuple[tuple[str, float], ...]` ([source](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 270)

### Module constants

- `CLASSES_ORDER` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 26)
- `OPEN_HYPOTHESIS` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 28)
- `_ROW_TOLERANCE` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 30)
- `NO_INFORMATION_CREDIT` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 180)
- `CAUSE_CLASS_SLOPES` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 184)
- `PRACTICE_GAMMA` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 188)
- `PENDING` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 189)
- `DESIGN_RECOMMENDATIONS` ([src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py), line 227)

### Explicit exports

`__all__` declares:

- `CAUSE_CLASS_SLOPES`
- `CLASSES_ORDER`
- `Channel`
- `DESIGN_RECOMMENDATIONS`
- `DiagnosticProbe`
- `GAP`
- `Hypothesis`
- `MissingChannel`
- `NO_INFORMATION_CREDIT`
- `OPEN_HYPOTHESIS`
- `OwnerDecisions`
- `PENDING`
- `PRACTICE_GAMMA`
- `RepairOption`
- `SLIP`
- `UNKNOWN`
- `effect_key`
- `posterior_table`
- `weights_from`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `module`; statically calls `Channel`, `DiagnosticProbe`, `Hypothesis`, `MissingChannel`, `RepairOption`
- [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]] — imports `module`; statically calls `effect_key`, `posterior_table`
- [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]] — imports `DiagnosticProbe`

### Repository tooling consumers

- [scripts/probe_router_report.py](../../../../../../scripts/probe_router_report.py); calls `Channel`, `DiagnosticProbe`, `Hypothesis`, `MissingChannel`, `RepairOption`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/router_objective/miss_cause|learnloop.router_objective.miss_cause]] — imports `CLASSES`, `GAP`, `SLIP`, `UNKNOWN`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/router_objective/diagnostic_value|learnloop.router_objective.diagnostic_value]], [[Reference/Modules/learnloop/router_objective/types|learnloop.router_objective.types]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_action_kinds_complete.py](../../../../../../tests/test_action_kinds_complete.py) — direct import
  - `test_a_probe_with_a_diagnostic_payload_has_its_effect_through_the_successor_evaluator`
- [tests/test_check_value.py](../../../../../../tests/test_check_value.py) — direct import
  - `test_the_rollouts_refuse_typed_checks_and_this_path_refuses_untyped_ones`
- [tests/test_diagnostic_probe_value.py](../../../../../../tests/test_diagnostic_probe_value.py) — direct import
  - `test_a_missing_channel_is_explicit_and_earns_no_information_credit`
  - `test_a_probe_anywhere_in_a_sequence_appends_the_rest_and_the_tail_once`
  - `test_acting_now_is_always_valued_beside_the_probe`
  - `test_hypotheses_are_reweighted_never_removed`
  - `test_no_clairvoyance`
  - `test_the_owner_decisions_are_named_inputs_marked_pending`

## Modification guidance

- Make changes here when the responsibility remains diagnostic payload within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/diagnostic_payload.py](../../../../../../src/learnloop/router_objective/diagnostic_payload.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
