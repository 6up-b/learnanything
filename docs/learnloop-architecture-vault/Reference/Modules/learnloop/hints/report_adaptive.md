---
title: "learnloop.hints.report_adaptive"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/hints/report_adaptive.py"
source_paths:
  - "src/learnloop/hints/report_adaptive.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.hints"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.hints.report_adaptive module"
  - "src/learnloop/hints/report_adaptive.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-hints"
---

# `learnloop.hints.report_adaptive`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.hints.report_adaptive` exists within [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] to own the behavior summarized by its module contract: `learnloop hints report`: H2b's rows (spec_adaptive_hints_v1 §6.1, §6.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py) |
| Source lines | 337 |
| Owning package | [[Reference/Modules/learnloop/hints/_package|learnloop.hints]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `loads(value: Any) -> Any` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 46)
- `answered_id(row: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 53)
- `state_at_request(row: Mapping[str, Any]) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 59)
- `table_exists(connection: Any, name: str) -> bool` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 65)
- `ledger(connection: Any, task: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 70)
- `map_paths(connection: Any, map_ids: Iterable[str]) -> dict[str, dict[str, list[str]]]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 78) — Each referenced map's routes (id -> node path); structure only.
- `hint_target(row: Mapping[str, Any], routes: Mapping[str, list[str]]) -> str | None` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 95) — The hint's target node, or for a kind without one the next node from where it was placed (§6.1).
- `progress_by_next_placement(row: Mapping[str, Any], following: Mapping[str, Any], maps: Mapping[str, Mapping[str, list[str]]]) -> str | None` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 109) — ``reached`` / ``not_reached`` when the next hint's placement (the node the work had reached when more help was asked, on the same map and route) settles whether this hint's target was reached first; else None.
- `expertise_reversal(members: list[dict[str, Any]], *, summarize: Callable[[list[dict[str, Any]]], dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 132) — The same columns split by placement intent and by P(success) at request time (§6.3), per kind and level, where the row logged them.
- `help_seeking(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None, percentiles: Callable[[Iterable[float | None]], dict[str, Any]], share: Callable[[int, int], dict[str, Any]], when: Callable[[Any], Any], surface: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 164) — Help abuse and avoidance, as counts with their distributions (§6.3; H4: nothing is gated on them).
- `routes(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None, percentiles: Callable[[Iterable[float | None]], dict[str, Any]], when: Callable[[Any], Any], writer_prompt_version: str, surface: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 240) — Latency and cost per route (§6.3): the chooser, the writer, outcome placement and the maps.

### Module constants

- `SHORTCUTS` ([src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py), line 36)
- `ROUTE_OWNER_KINDS` ([src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py), line 38)
- `WRITER_DOWN_REASONS` ([src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py), line 40)
- `INTENTS` ([src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py), line 43)
- `ATTEMPT_SURFACES` ([src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py), line 202)

### Explicit exports

`__all__` declares:

- `ATTEMPT_SURFACES`
- `INTENTS`
- `ROUTE_OWNER_KINDS`
- `SHORTCUTS`
- `answered_id`
- `expertise_reversal`
- `help_seeking`
- `hint_target`
- `ledger`
- `map_paths`
- `progress_by_next_placement`
- `routes`
- `state_at_request`

## Internal implementation anchors

- `_band_p(value: float | None, median: float | None) -> str` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 126)
- `_avoidance(connection: Any, all_rows: list[dict[str, Any]], *, since: str | None, surface: str | None, percentiles: Callable[[Iterable[float | None]], dict[str, Any]]) -> dict[str, Any]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 208)
- `_receipts(connection: Any, *, since: str | None, percentiles: Callable[[Iterable[float | None]], dict[str, Any]], when: Callable[[Any], Any]) -> dict[str, dict[str, Any]]` ([source](../../../../../../src/learnloop/hints/report_adaptive.py), line 302)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]] — imports `module`; statically calls `answered_id`, `expertise_reversal`, `help_seeking`, `ledger`, `loads`, `map_paths`, `progress_by_next_placement`, `routes`
- [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]] — imports `module`; statically calls `hint_target`, `progress_by_next_placement`
- [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]] — imports `module`; statically calls `map_paths`

## Dependencies

### LearnLoop dependencies

No internal Python dependency was found by static analysis.

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]], [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]], [[Reference/Modules/learnloop/workbench/help_outcomes|learnloop.workbench.help_outcomes]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/hint_h2b_review_helpers.py](../../../../../../tests/hint_h2b_review_helpers.py) — imports consumer [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]]
- [tests/test_figures_help.py](../../../../../../tests/test_figures_help.py) — imports consumer [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]]
- [tests/test_help_assist_work_md_migration.py](../../../../../../tests/test_help_assist_work_md_migration.py) — imports consumer [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]]
- [tests/test_hint_report.py](../../../../../../tests/test_hint_report.py) — imports consumer [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]]
- [tests/test_hint_telemetry.py](../../../../../../tests/test_hint_telemetry.py) — imports consumer [[Reference/Modules/learnloop/hints/report|learnloop.hints.report]]
- [tests/test_figures_help_codex_review.py](../../../../../../tests/test_figures_help_codex_review.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_reader_rw2b_fix10.py](../../../../../../tests/test_reader_rw2b_fix10.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_reader_rw2b_fix14.py](../../../../../../tests/test_reader_rw2b_fix14.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_reader_rw2b_fix9.py](../../../../../../tests/test_reader_rw2b_fix9.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_rw2c_fix_round3.py](../../../../../../tests/test_rw2c_fix_round3.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]
- [tests/test_workbench_report.py](../../../../../../tests/test_workbench_report.py) — imports consumer [[Reference/Modules/learnloop/hints/report_workbench|learnloop.hints.report_workbench]]

## Modification guidance

- Make changes here when the responsibility remains report adaptive within learnloop.hints; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/hints/report_adaptive.py](../../../../../../src/learnloop/hints/report_adaptive.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
