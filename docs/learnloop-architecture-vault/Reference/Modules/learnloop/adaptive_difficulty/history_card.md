---
title: "learnloop.adaptive_difficulty.history_card"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/history_card.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/history_card.py"
source_commit: "8d1272482fc14d002b0c0671f74e5f37d2427af9"
source_commit_timestamp: "2026-11-04T21:28:27-05:00"
source_worktree_state: "clean"
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
  - "learnloop.adaptive_difficulty.history_card module"
  - "src/learnloop/adaptive_difficulty/history_card.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.history_card`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.history_card` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: Router objective RO2's card, ``ad-forecast-state-v3`` (spec_router_objective_v1 §6.3).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py) |
| Source lines | 505 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `8d1272482fc14d002b0c0671f74e5f37d2427af9` |
| Commit timestamp | `2026-11-04T21:28:27-05:00` |

## Public API

- `available_sql(connection: Any, table: str) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 98) — A table's availability time in SQL: ``coalesce(received_at, created_at)`` where it has ``received_at``, else ``created_at`` (spec §6.3).
- `build_sections(vault: Any, connection: Any, item: Any, *, served_at: str, view: Any) -> dict[str, Any]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 257) — Every rung's sections, from the bounded reads (oldest entry first in each list), with the clocks' input (days since the latest exposure to the LO) and the reads that hit their limit.
- `rung_card(vault: Any, item: Any, built: Mapping[str, Any], rung: str, *, budget: int) -> tuple[dict[str, Any], dict]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 446) — The state sent for ``rung``: the served item, the rung's sections and every lower rung's, held to ``budget`` bytes by trimming oldest first within each rung (one entry per rung per round), with what it left out.
- `evidence_ids(state: Mapping[str, Any]) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 493) — Every evidence id a card carries (the rationale's citations are checked against it, unvalidated).

### Module constants

- `CARD_VERSION` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 58)
- `RUNGS` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 59)
- `SECTIONS` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 61)
- `ROW_LIMITS` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 68)
- `ANSWER_TEXT_LIMIT` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 73)
- `TEXT_LIMIT` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 74)
- `GAP_TEXT_LIMIT` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 75)
- `EXAM_TYPES` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 76)
- `READER_CONTEXTS` ([src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 77)

### Explicit exports

`__all__` declares:

- `CARD_VERSION`
- `ROW_LIMITS`
- `RUNGS`
- `SECTIONS`
- `available_sql`
- `build_sections`
- `evidence_ids`
- `rung_card`

## Internal implementation anchors

- `_excerpt(text: Any, limit: int) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 80)
- `_json(value: Any, default: Any) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 85)
- `_columns(connection: Any, table: str) -> set[str]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 94)
- `_marks(values: Sequence[Any]) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 108)
- `class _Days` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 112)
- `_result(correctness: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 123)
- `_withheld(vault: Any, view: Any, attempts: Sequence[Mapping[str, Any]]) -> Any` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 134) — ``learner_protection``'s set over what the view lets AD see: the withheld items (the view's) and the diagnostic probes (the vault's own modes); unknown items are withheld by ``known_items``.
- `_protection(withheld: Any, attempt: Mapping[str, Any]) -> str | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 155)
- `class _Reads` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 162) — Every bounded read the card makes, once per serve (shared by the rungs).
- `_topic(vault: Any, lo_id: Any) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 248)
- `_oldest_first(entries: list[dict[str, Any]]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 253)
- `_size(state: Mapping[str, Any]) -> int` ([source](../../../../../../src/learnloop/adaptive_difficulty/history_card.py), line 442)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]] — imports `module`; statically calls `_size`, `build_sections`, `evidence_ids`, `rung_card`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/outside|learnloop.adaptive_difficulty.outside]] — imports `HISTORY_STEM_LIMIT`, `answer_excerpts_enabled`, `history_card`, `item_view`; calls `answer_excerpts_enabled`, `history_card`, `item_view`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/learner_protection|learnloop.learner_protection]] — imports `PROBE_MODES`, `WITHHELD_EXAM`, `WITHHELD_PROBE`, `Withheld`, `attempt_protection`; calls `Withheld`, `attempt_protection`
- [[Reference/Modules/learnloop/router_objective_switches|learnloop.router_objective_switches]] — imports `attempt_time_sql`; calls `attempt_time_sql`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/history_forecast|learnloop.adaptive_difficulty.history_forecast]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro2_history_protection.py](../../../../../../tests/test_ro2_history_protection.py) — direct import
  - `test_the_budget_trims_oldest_first_within_each_rung_and_says_so`

## Modification guidance

- Make changes here when the responsibility remains history card within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/history_card.py](../../../../../../src/learnloop/adaptive_difficulty/history_card.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
