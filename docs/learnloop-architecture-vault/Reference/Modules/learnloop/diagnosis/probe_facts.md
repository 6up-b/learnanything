---
title: "learnloop.diagnosis.probe_facts"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_facts.py"
source_paths:
  - "src/learnloop/diagnosis/probe_facts.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.diagnosis.probe_facts module"
  - "src/learnloop/diagnosis/probe_facts.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_facts`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_facts` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: What is known about a possible probe before anyone decides whether to run it.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py) |
| Source lines | 260 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class ProbeFacts` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 27) — The facts about one possible probe, and the hard stops that hold.
  - `hard_stops(self) -> tuple[str, ...]` (line 65; public) — The names of the hard stops that hold, in the order the rule checks them.
- `probe_facts(*, repair_class_ids: Sequence[str | None], common_repair_covers: bool, expected_information_gain: float, probability_information_changes_repair: float, probe_burden_minutes: float, avoided_overteaching_minutes: float, pending_machine_checks: Sequence[str]=(), session_budget_minutes: float | None=None, learner_preference: str='allow', recent_diagnostic_burden: int=0) -> ProbeFacts` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 76) — The facts and hard stops for one possible probe, from values the caller gathered (units on :class:`ProbeFacts`; ``avoided_overteaching_minutes`` and ``session_budget_minutes`` are minutes).
- `channel_status(*, instrument: bool, separability_computed: bool) -> str` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 128) — Which of the three states the chosen instrument's channel is in (the ``CHANNEL_*`` names).
- `class ProbeProposalReads` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 137) — What the repair lane reads about one factor's possible probe before anyone judges it, as plain values.
  - `facts(self, *, session_budget_minutes: float | None=None) -> ProbeFacts` (line 172; public) — The facts these reads give, as the repair lane's verdict computes them.
- `class Thresholds(Protocol)` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 189) — The rule's thresholds, read only when the rule reaches them (``CausalProbeParameters`` is one).
  - `recent_diagnostic_limit(self) -> int` (line 193; public)
  - `__getitem__(self, key: str) -> float` (line 195; internal)
- `settled_by_repair_classes(*, common_repair_covers: bool, different_repairs: bool) -> tuple[str, str] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 198) — The rule's first two arms, ``(verb, reason)``, or None when the repair classes leave the question open.
- `probe_verdict(facts: ProbeFacts, thresholds: Thresholds) -> tuple[str, str]` ([source](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 210) — The repair lane's verdict on the facts, ``(verb, reason)``.

### Module constants

- `REFUSING_PREFERENCES` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 19)
- `HARD_STOP_MACHINE_CHECKS` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 21)
- `HARD_STOP_LEARNER_PREFERENCE` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 22)
- `HARD_STOP_SESSION_BUDGET` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 23)
- `CHANNEL_NO_INSTRUMENT` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 123)
- `CHANNEL_NO_SEPARABILITY_RECORD` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 124)
- `CHANNEL_SEPARABILITY_COMPUTED` ([src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py), line 125)

### Explicit exports

`__all__` declares:

- `CHANNEL_NO_INSTRUMENT`
- `CHANNEL_NO_SEPARABILITY_RECORD`
- `CHANNEL_SEPARABILITY_COMPUTED`
- `HARD_STOP_LEARNER_PREFERENCE`
- `HARD_STOP_MACHINE_CHECKS`
- `HARD_STOP_SESSION_BUDGET`
- `REFUSING_PREFERENCES`
- `ProbeFacts`
- `ProbeProposalReads`
- `Thresholds`
- `channel_status`
- `probe_facts`
- `probe_verdict`
- `settled_by_repair_classes`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `ProbeProposalReads`, `REFUSING_PREFERENCES`, `channel_status`, `settled_by_repair_classes`; statically calls `ProbeProposalReads`, `channel_status`, `settled_by_repair_classes`
- [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]] — imports `probe_facts`, `probe_verdict`; statically calls `probe_facts`, `probe_verdict`
- [[Reference/Modules/learnloop/diagnosis/learner_probe_proposal|learnloop.diagnosis.learner_probe_proposal]] — imports `ProbeProposalReads`
- [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]] — imports `settled_by_repair_classes`; statically calls `settled_by_repair_classes`

### Repository tooling consumers

- [scripts/probe_router_report.py](../../../../../../scripts/probe_router_report.py); calls `probe_facts`, `probe_verdict`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]], [[Reference/Modules/learnloop/diagnosis/causal_probe_coherence|learnloop.diagnosis.causal_probe_coherence]], [[Reference/Modules/learnloop/diagnosis/learner_probe_proposal|learnloop.diagnosis.learner_probe_proposal]], [[Reference/Modules/learnloop/followup_run/router|learnloop.followup_run.router]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_facts.py](../../../../../../tests/test_probe_facts.py) — direct import
  - `test_a_refusing_preference_is_a_hard_stop`
  - `test_a_session_budget_below_the_burden_as_given_is_a_hard_stop`
  - `test_a_threshold_is_read_only_when_the_ladder_reaches_it`
  - `test_every_hard_stop_is_named_in_the_rules_order`
  - `test_pending_machine_checks_are_a_hard_stop`
  - `test_the_repair_classes_alone_settle_two_cases`
  - `test_the_verdict_reads_the_facts_in_the_ladders_order`
- [tests/test_probe_proposal_reads.py](../../../../../../tests/test_probe_proposal_reads.py) — direct import
  - `test_a_missing_channel_is_a_status_and_not_the_zero_it_is_priced_at`
  - `test_gathering_writes_nothing_and_the_verdict_on_its_facts_is_the_statuss`
  - `test_the_reads_give_the_facts_the_verdict_computes_from_the_same_values`
- [tests/test_probe_router_worth_gates.py](../../../../../../tests/test_probe_router_worth_gates.py) — direct import

## Modification guidance

- Change probe facts policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_facts.py](../../../../../../src/learnloop/diagnosis/probe_facts.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
