---
title: "learnloop.practice_index.usage"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/practice_index/usage.py"
source_paths:
  - "src/learnloop/practice_index/usage.py"
source_commit: "801326152516add59dcfa4016352f0be987aca83"
source_commit_timestamp: "2026-10-13T01:05:29-04:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.practice_index"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.practice_index.usage module"
  - "src/learnloop/practice_index/usage.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-practice-index"
---

# `learnloop.practice_index.usage`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.practice_index.usage` exists within [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] to own the behavior summarized by its module contract: Usage signals on find_practice proposals, logged now for later evaluation.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py) |
| Source lines | 148 |
| Owning package | [[Reference/Modules/learnloop/practice_index/_package|learnloop.practice_index]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `801326152516add59dcfa4016352f0be987aca83` |
| Commit timestamp | `2026-10-13T01:05:29-04:00` |

## Public API

- `record_practice_usage(repository: Repository, *, proposal_id: str, practice_item_id: str, signal: str, clock: Clock | None=None, text: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/usage.py), line 44) — Append one learner tap on a proposed item.
- `sweep_practice_usage(repository: Repository, *, window_hours: int, clock: Clock | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/usage.py), line 83) — Append ``practised`` for proposed items attempted within the window.
- `usage_summary(repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/practice_index/usage.py), line 120) — Aggregate counts by retrieval path, signal and judge; no learner text.

### Module constants

- `USAGE_TASK` ([src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py), line 35)
- `LEARNER_SIGNALS` ([src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py), line 36)
- `JOIN_PROMPT_VERSION` ([src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py), line 37)
- `LEARNER_TEXT_CHARS` ([src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py), line 41)

### Explicit exports

`__all__` declares:

- `LEARNER_SIGNALS`
- `USAGE_TASK`
- `record_practice_usage`
- `sweep_practice_usage`
- `usage_summary`

## Internal implementation anchors

- `_tap_rationale(text: str | None) -> str` ([source](../../../../../../src/learnloop/practice_index/usage.py), line 75)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]] — imports `record_practice_usage`, `usage_summary`; statically calls `record_practice_usage`, `usage_summary`
- [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]] — imports `USAGE_TASK`, `record_practice_usage`; statically calls `record_practice_usage`
- [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]] — imports `sweep_practice_usage`, `usage_summary`; statically calls `sweep_practice_usage`, `usage_summary`
- [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]] — imports `LEARNER_SIGNALS`, `record_practice_usage`; statically calls `record_practice_usage`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/ai/execution|learnloop.ai.execution]] — imports `content_key`; calls `content_key`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`, `SystemClock`, `parse_utc`, `utc_now_iso`; calls `SystemClock`, `parse_utc`, `utc_now_iso`
- [[Reference/Modules/learnloop/db/connection|learnloop.db.connection]] — imports `connect`; calls `connect`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/judgments|learnloop.db.stores.judgments]] — imports `append_judgment`; calls `append_judgment`
- [[Reference/Modules/learnloop/db/stores/practice_index|learnloop.db.stores.practice_index]] — imports `attempts_after`, `judgments_by_ids`, `judgments_for_task`, `proposal`, `proposals`; calls `attempts_after`, `judgments_by_ids`, `judgments_for_task`, `proposal`, `proposals`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `contextlib`, `datetime`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/cli/practice_index|learnloop.cli.practice_index]], [[Reference/Modules/learnloop/instructional/practice|learnloop.instructional.practice]], [[Reference/Modules/learnloop/practice_index/evaluation|learnloop.practice_index.evaluation]], [[Reference/Modules/learnloop_sidecar/handlers/practice_index|learnloop_sidecar.handlers.practice_index]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_learner_pick_proposal.py](../../../../../../tests/test_learner_pick_proposal.py) — direct import
  - `test_not_what_i_asked_keeps_the_learner_text`
- [tests/test_library_exercises.py](../../../../../../tests/test_library_exercises.py) — direct import
  - `test_use_this_one_opens_at_once_on_the_verbatim_stem_while_the_import_runs`
- [tests/test_practice_index_find.py](../../../../../../tests/test_practice_index_find.py) — direct import
  - `test_usage_signals_are_ledgered_and_joined_to_attempts`
- [tests/test_source_exercise_rpcs.py](../../../../../../tests/test_source_exercise_rpcs.py) — direct import
  - `test_picking_an_exercise_proposal_queues_its_import_and_records_the_pick`

## Modification guidance

- Make changes here when the responsibility remains usage within learnloop.practice_index; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/practice_index/usage.py](../../../../../../src/learnloop/practice_index/usage.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
