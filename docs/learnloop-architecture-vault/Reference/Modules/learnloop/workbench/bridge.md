---
title: "learnloop.workbench.bridge"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/workbench/bridge.py"
source_paths:
  - "src/learnloop/workbench/bridge.py"
source_commit: "e575da4c2ecce36ebc48e97417a86ec23167c062"
source_commit_timestamp: "2026-10-21T14:39:41-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.workbench"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.workbench.bridge module"
  - "src/learnloop/workbench/bridge.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-workbench"
---

# `learnloop.workbench.bridge`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.workbench.bridge` exists within [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] to own the behavior summarized by its module contract: Reader workbench RW2b: "Compare with the book" under a hint (spec_reader_workbench_v1 §5.2 bridging, G8).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/workbench/bridge.py](../../../../../../src/learnloop/workbench/bridge.py) |
| Source lines | 201 |
| Owning package | [[Reference/Modules/learnloop/workbench/_package|learnloop.workbench]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `e575da4c2ecce36ebc48e97417a86ec23167c062` |
| Commit timestamp | `2026-10-21T14:39:41-04:00` |

## Public API

- `bridge_for_hint(vault: Any, repository: Repository, *, workbench_session_id: str, hint_assist_id: str, item: Any, provider: Callable[..., Any] | None=None, envelope: Any | None=None, max_calls: int | None=None, draw_enabled: bool=False, seed: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/workbench/bridge.py), line 66) — Look for the passage; write the bridge row prepared (``shown = 0``).
- `verified_spans(spans: list[dict[str, Any]], manifest: dict[str, Any]) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/workbench/bridge.py), line 189) — The spans among ``spans`` that the listwise judge passed: those the manifest's ``span_keys`` name (``extraction_id/span_id``), in their order.

### Module constants

- `COMPARE_LINE` ([src/learnloop/workbench/bridge.py](../../../../../../src/learnloop/workbench/bridge.py), line 45)
- `NOTHING_LINE` ([src/learnloop/workbench/bridge.py](../../../../../../src/learnloop/workbench/bridge.py), line 46)

### Explicit exports

`__all__` declares:

- `COMPARE_LINE`
- `NOTHING_LINE`
- `bridge_for_hint`
- `verified_spans`

## Internal implementation anchors

- `_metered_verification(vault: Any) -> bool` ([source](../../../../../../src/learnloop/workbench/bridge.py), line 49) — Whether the bridge's paid step (T6's listwise verification) bills by the token: only then can the workbench's daily budget refuse it.
- `_settle(repository: Repository, assist_id: str, fields: dict[str, Any]) -> None` ([source](../../../../../../src/learnloop/workbench/bridge.py), line 61)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]] — imports `bridge_for_hint`; statically calls `bridge_for_hint`
- [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]] — imports `COMPARE_LINE`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/spend|learnloop.ai.spend]] — imports `SpendLimitExceeded`, `spend_envelopes`; calls `spend_envelopes`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `utc_now_iso`; calls `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/help_assists|learnloop.db.stores.help_assists]] — imports `module`; calls `assist`, `insert_assist`, `settle_bridge`
- [[Reference/Modules/learnloop/ids|learnloop.ids]] — imports `new_ulid`; calls `new_ulid`
- [[Reference/Modules/learnloop/practice_index/paid|learnloop.practice_index.paid]] — imports `plan_route`; calls `plan_route`
- [[Reference/Modules/learnloop/source_retrieval/recipes|learnloop.source_retrieval.recipes]] — imports `block_record_id`; calls `block_record_id`
- [[Reference/Modules/learnloop/source_retrieval/tutor|learnloop.source_retrieval.tutor]] — imports `TutorSpanProvider`; calls `TutorSpanProvider`
- [[Reference/Modules/learnloop/vault/hashes|learnloop.vault.hashes]] — imports `practice_item_hash`; calls `practice_item_hash`
- [[Reference/Modules/learnloop/workbench/check|learnloop.workbench.check]] — imports `session_calls_on`; calls `session_calls_on`
- [[Reference/Modules/learnloop/workbench/passage_draw|learnloop.workbench.passage_draw]] — imports `module`; calls `draw`, `new_seed`, `option_id`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/workbench_help|learnloop_sidecar.handlers.workbench_help]], [[Reference/Modules/learnloop_sidecar/handlers/workbench_rw2c|learnloop_sidecar.handlers.workbench_rw2c]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_reader_rw2b_review.py](../../../../../../tests/test_reader_rw2b_review.py) — direct import
  - `test_f9_the_search_runs_inside_the_workbench_envelope_and_a_spent_day_refuses_it`
  - `test_f9_the_search_takes_its_place_before_it_runs_so_a_second_one_is_refused`
- [tests/test_rw2c_fix_round2.py](../../../../../../tests/test_rw2c_fix_round2.py) — direct import
  - `test_fr2_1_an_example_waiting_on_its_bridge_never_searches_after_switch_off_or_cancel`
- [tests/test_workbench_route_example.py](../../../../../../tests/test_workbench_route_example.py) — direct import
  - `test_under_the_problems_cap_the_example_never_displaces_the_bridge`

## Modification guidance

- Make changes here when the responsibility remains bridge within learnloop.workbench; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/workbench/bridge.py](../../../../../../src/learnloop/workbench/bridge.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
