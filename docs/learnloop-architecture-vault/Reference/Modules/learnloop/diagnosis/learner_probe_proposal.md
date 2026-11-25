---
title: "learnloop.diagnosis.learner_probe_proposal"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/learner_probe_proposal.py"
source_paths:
  - "src/learnloop/diagnosis/learner_probe_proposal.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.diagnosis"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Import Canonical Sources"
  - "Build a Study Map"
aliases:
  - "learnloop.diagnosis.learner_probe_proposal module"
  - "src/learnloop/diagnosis/learner_probe_proposal.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.learner_probe_proposal`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.learner_probe_proposal` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: The probe router's learner lane: what the router reads about one factor's quick check, as plain values.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/learner_probe_proposal.py](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py) |
| Source lines | 71 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `class Proposal` ([source](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py), line 25) — One factor's possible quick check as the status read it (``causal_orchestrator._routed``).
  - `practice_item_id(self) -> str | None` (line 42; public)
  - `facts(self) -> dict[str, Any]` (line 46; public) — The repair lane's facts, as plain values: for the record and the card, never priced.
- `instrument_items(vault: Any, repository: Any, learning_object_id: str | None, factor_id: str | None=None) -> set[str]` ([source](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py), line 56) — The items on the learning object a probe may administer (bound to an instrument card, a diagnostic surface, or a probe candidate of the factor): the measurement a router decision arranges never takes one of them as its check, which would hold the probe's own instrument back as a…

### Module constants

- `CHANNEL_SOURCE` ([src/learnloop/diagnosis/learner_probe_proposal.py](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py), line 19)
- `PROBE_ACTION_REF` ([src/learnloop/diagnosis/learner_probe_proposal.py](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py), line 21)

### Explicit exports

`__all__` declares:

- `CHANNEL_SOURCE`
- `PROBE_ACTION_REF`
- `Proposal`
- `instrument_items`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]] — imports `CHANNEL_SOURCE`, `PROBE_ACTION_REF`, `instrument_items`; statically calls `instrument_items`
- [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]] — imports `instrument_items`; statically calls `instrument_items`
- [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]] — imports `Proposal`; statically calls `Proposal`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/probe_facts|learnloop.diagnosis.probe_facts]] — imports `ProbeProposalReads`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Import Canonical Sources]]
- [[Build a Study Map]]

Static participation evidence comes from [[Reference/Modules/learnloop/daily_plan/learner_probe|learnloop.daily_plan.learner_probe]], [[Reference/Modules/learnloop/daily_plan/measurement|learnloop.daily_plan.measurement]], [[Reference/Modules/learnloop/diagnosis/causal_orchestrator|learnloop.diagnosis.causal_orchestrator]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_router_fixes_mvp077.py](../../../../../../tests/test_probe_router_fixes_mvp077.py) — direct import
  - `test_r34_a_learned_draw_with_a_tiny_floor_logs_the_exact_share_through_the_persisted_row`

## Modification guidance

- Change learner probe proposal policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/learner_probe_proposal.py](../../../../../../src/learnloop/diagnosis/learner_probe_proposal.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
