---
title: "learnloop.diagnosis.probe_authority"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/diagnosis/probe_authority.py"
source_paths:
  - "src/learnloop/diagnosis/probe_authority.py"
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
  - "learnloop.diagnosis.probe_authority module"
  - "src/learnloop/diagnosis/probe_authority.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-diagnosis"
---

# `learnloop.diagnosis.probe_authority`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.diagnosis.probe_authority` exists within [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] to own the behavior summarized by its module contract: Whose decision a probe is: the probe router's dispatch by origin (refactor G2).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/diagnosis/probe_authority.py](../../../../../../src/learnloop/diagnosis/probe_authority.py) |
| Source lines | 79 |
| Owning package | [[Reference/Modules/learnloop/diagnosis/_package|learnloop.diagnosis]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `router_pin(components: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 35) — Whether a presentation's selection components pin a router decision (whatever tag it was made at).
- `decision_owns(repository: Any, decision_id: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 41) — Whether the router decision ``decision_id`` is the probe router's: made at its tag (the row's own ``algorithm_version``, frozen when it was drawn, never the vault's tag now) and asking the probe.
- `pin_owned(repository: Any, components: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 56) — Whether a presentation's pin names a decision the probe router owns (:func:`decision_owns`).
- `router_selected_presentation(repository: Any, presentation: Any) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 63) — Whether this presentation is a probe the probe router selected.
- `router_selected_rows(repository: Any, rows: Iterable[Mapping[str, Any]]) -> bool` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 71) — Whether any of an episode's observation rows (``effective_episode_observations``, which carry their presentation's ``selection_components``) answered a probe the probe router selected.

### Module constants

- `ROUTER_DECISION_KEY` ([src/learnloop/diagnosis/probe_authority.py](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 23)
- `PROBE_ARMS` ([src/learnloop/diagnosis/probe_authority.py](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 25)
- `LIVE_STATUSES` ([src/learnloop/diagnosis/probe_authority.py](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 27)

### Explicit exports

`__all__` declares:

- `LIVE_STATUSES`
- `PROBE_ARMS`
- `ROUTER_DECISION_KEY`
- `decision_owns`
- `pin_owned`
- `router_pin`
- `router_selected_presentation`
- `router_selected_rows`

## Internal implementation anchors

- `_pin(components: Any) -> Mapping[str, Any] | None` ([source](../../../../../../src/learnloop/diagnosis/probe_authority.py), line 30)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]] — imports `router_selected_presentation`; statically calls `router_selected_presentation`
- [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]] — imports `router_selected_rows`; statically calls `router_selected_rows`
- [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]] — imports `LIVE_STATUSES`, `ROUTER_DECISION_KEY`, `decision_owns`; statically calls `decision_owns`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/algorithm_versions|learnloop.algorithm_versions]] — imports `PROBE_ROUTER_VERSIONS`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/diagnosis/probe_blocks|learnloop.diagnosis.probe_blocks]], [[Reference/Modules/learnloop/diagnosis/probe_completion|learnloop.diagnosis.probe_completion]], [[Reference/Modules/learnloop/diagnosis/probe_episodes|learnloop.diagnosis.probe_episodes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_probe_router_worth_gates.py](../../../../../../tests/test_probe_router_worth_gates.py) — direct import
  - `test_a_probe_of_another_origin_keeps_its_gates`
  - `test_a_router_selected_probe_is_served_answered_and_ended_with_every_legacy_worth_gate_raising`
  - `test_below_the_tag_a_pinned_router_decision_is_no_dispatch`
  - `test_the_count_bounds_a_router_selected_episode_and_value_decides_none_of_it`

## Modification guidance

- Change probe authority policy here when diagnosis owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/diagnosis/probe_authority.py](../../../../../../src/learnloop/diagnosis/probe_authority.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
