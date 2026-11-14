---
title: "learnloop.adaptive_difficulty.data_check"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/data_check.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/data_check.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.adaptive_difficulty"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.adaptive_difficulty.data_check module"
  - "src/learnloop/adaptive_difficulty/data_check.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.data_check`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.data_check` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: ``learnloop ad data-check`` (spec_adaptive_difficulty_v1 §14 AD1, §3.3, §17 Q1, Q3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/data_check.py](../../../../../../src/learnloop/adaptive_difficulty/data_check.py) |
| Source lines | 197 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `spearman(xs: list[float], ys: list[float]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 48) — Spearman's rho with an approximate 95% Fisher-z interval; n < 4 reports no interval.
- `data_check(vault: Any, sqlite_path: Any, *, repository: Any=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 73)

### Explicit exports

`__all__` declares:

- `data_check`
- `spearman`

## Internal implementation anchors

- `_ranks(values: list[float]) -> list[float]` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 33)
- `_has(connection: Any, table: str) -> bool` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 69)
- `_share(rows: list[dict[str, Any]], key: str) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 162)
- `_exam_units(vault: Any, connection: Any, repository: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/data_check.py), line 168)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]] — imports `data_check`; statically calls `data_check`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/content/sources/exam_material|learnloop.content.sources.exam_material]] — imports `exam_material`; calls `exam_material`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/field/outcomes|learnloop.field.outcomes]] — imports `load_attempt_rows`; calls `load_attempt_rows`
- [[Reference/Modules/learnloop/reader/reader_progression|learnloop.reader.reader_progression]] — imports `learning_objects_for_span`; calls `learning_objects_for_span`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `math`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/ad|learnloop.cli.ad]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Make changes here when the responsibility remains data check within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/data_check.py](../../../../../../src/learnloop/adaptive_difficulty/data_check.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
