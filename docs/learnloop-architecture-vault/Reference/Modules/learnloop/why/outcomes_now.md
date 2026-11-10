---
title: "learnloop.why.outcomes_now"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/why/outcomes_now.py"
source_paths:
  - "src/learnloop/why/outcomes_now.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.why"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.why.outcomes_now module"
  - "src/learnloop/why/outcomes_now.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-why"
---

# `learnloop.why.outcomes_now`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/why/_package|learnloop.why]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.why.outcomes_now` exists within [[Reference/Modules/learnloop/why/_package|learnloop.why]] to own the behavior summarized by its module contract: Every logged router decision's outcome as of now, derived from the ledgers at read time (read-only).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/why/outcomes_now.py](../../../../../../src/learnloop/why/outcomes_now.py) |
| Source lines | 36 |
| Owning package | [[Reference/Modules/learnloop/why/_package|learnloop.why]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `outcomes_now(connection: sqlite3.Connection, loaded: Any, sqlite_path: Path) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/why/outcomes_now.py), line 16) — ``{decision_id: outcome row}`` for every logged router decision, as :func:`derive_router_outcomes` derives it now for ``loaded``'s vault (its servable items, its outcome version, its Reader exposures).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]] — imports `outcomes_now`; statically calls `outcomes_now`
- [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]] — imports `outcomes_now`; statically calls `outcomes_now`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/data_capture/reading_exposures|learnloop.data_capture.reading_exposures]] — imports `module`; calls `for_version`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/router/outcomes|learnloop.router.outcomes]] — imports `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`; calls `derive_router_outcomes`, `outcome_version_for`, `servable_items_by_learning_object`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `held_for_review_attempts`, `pfc_assessments`; calls `held_for_review_attempts`, `pfc_assessments`

### Platform and third-party dependencies

- Standard library: `__future__`, `pathlib`, `sqlite3`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/router|learnloop.cli.router]], [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_arcb_close_fixes.py](../../../../../../tests/test_arcb_close_fixes.py) — imports consumer [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]]
- [tests/test_why_reader.py](../../../../../../tests/test_why_reader.py) — imports consumer [[Reference/Modules/learnloop/why/reader|learnloop.why.reader]]

## Modification guidance

- Make changes here when the responsibility remains outcomes now within learnloop.why; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/why/outcomes_now.py](../../../../../../src/learnloop/why/outcomes_now.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
