---
title: "learnloop.instructional.wiring"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/instructional/wiring.py"
source_paths:
  - "src/learnloop/instructional/wiring.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.instructional"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.instructional.wiring module"
  - "src/learnloop/instructional/wiring.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-instructional"
---

# `learnloop.instructional.wiring`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.instructional.wiring` exists within [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] to own the behavior summarized by its module contract: What the adapters inject into ``find_practice`` and the tutor (SC12).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/instructional/wiring.py](../../../../../../src/learnloop/instructional/wiring.py) |
| Source lines | 57 |
| Owning package | [[Reference/Modules/learnloop/instructional/_package|learnloop.instructional]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `find_practice_injections(vault: LoadedVault, *, estimator: Any | None=None, screen_client: Any | None=None, judge_client: Any | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/instructional/wiring.py), line 14) — Keyword arguments for ``find_practice`` under the service's switches.
- `disabled_reason(vault: LoadedVault, *needed: str) -> str | None` ([source](../../../../../../src/learnloop/instructional/wiring.py), line 45) — Which switch keeps a caller's phases off (None: all on).

### Explicit exports

`__all__` declares:

- `disabled_reason`
- `find_practice_injections`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]] — imports `find_practice_injections`; statically calls `find_practice_injections`
- [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]] — imports `disabled_reason`, `find_practice_injections`; statically calls `disabled_reason`, `find_practice_injections`
- [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]] — imports `disabled_reason`, `find_practice_injections`; statically calls `disabled_reason`, `find_practice_injections`
- [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]] — imports `disabled_reason`; statically calls `disabled_reason`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `find_practice_injections`; statically calls `find_practice_injections`
- [[Reference/Modules/learnloop_sidecar/handlers/reader|learnloop_sidecar.handlers.reader]] — imports `find_practice_injections`; statically calls `find_practice_injections`
- [[Reference/Modules/learnloop_sidecar/handlers/reader_followups|learnloop_sidecar.handlers.reader_followups]] — imports `find_practice_injections`; statically calls `find_practice_injections`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/diagnosis/probe_robust|learnloop.diagnosis.probe_robust]] — imports `resolve_episode_channel`
- [[Reference/Modules/learnloop/instructional/discriminating|learnloop.instructional.discriminating]] — imports `make_valuer`; calls `make_valuer`
- [[Reference/Modules/learnloop/instructional/exercises|learnloop.instructional.exercises]] — imports `exercise_candidates`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/sources|learnloop.cli.sources]], [[Reference/Modules/learnloop/instructional/harvest|learnloop.instructional.harvest]], [[Reference/Modules/learnloop/instructional/needs|learnloop.instructional.needs]], [[Reference/Modules/learnloop/instructional/reader_followups|learnloop.instructional.reader_followups]], [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] and 2 more.

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_followup_valuation.py](../../../../../../tests/test_reader_followup_valuation.py) — direct import
  - `test_the_default_search_is_find_practice_with_the_exact_filters_system_initiated`
- [tests/test_tool_dispatch_policy.py](../../../../../../tests/test_tool_dispatch_policy.py) — direct import
  - `test_a_continuation_with_narrower_filters_is_refused`
  - `test_a_find_practice_tool_result_can_be_continued`

## Modification guidance

- Make changes here when the responsibility remains wiring within learnloop.instructional; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/instructional/wiring.py](../../../../../../src/learnloop/instructional/wiring.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
