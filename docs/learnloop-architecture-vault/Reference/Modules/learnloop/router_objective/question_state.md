---
title: "learnloop.router_objective.question_state"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/router_objective/question_state.py"
source_paths:
  - "src/learnloop/router_objective/question_state.py"
source_commit: "a4e0f59423a2c592bf171f22dd743cb094485201"
source_commit_timestamp: "2026-11-04T09:01:45-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.router_objective"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.router_objective.question_state module"
  - "src/learnloop/router_objective/question_state.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-router-objective"
---

# `learnloop.router_objective.question_state`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.router_objective.question_state` exists within [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] to own the behavior summarized by its module contract: RO0 rows 1, 2 and 3 at an ask: the state a question was asked in, computed before the model call.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py) |
| Source lines | 175 |
| Owning package | [[Reference/Modules/learnloop/router_objective/_package|learnloop.router_objective]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a4e0f59423a2c592bf171f22dd743cb094485201` |
| Commit timestamp | `2026-11-04T09:01:45-05:00` |

## Public API

- `fields_at_ask(repository: Any, *, context: str, practice_item_id: str | None, attempt_id: str | None, session_id: str | None, question_context: Mapping[str, Any], workbench_session_id: str | None=None) -> dict[str, Any]` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 128) — The columns RO0 adds or fills on one question row, on a fresh read; ``{}`` when it cannot be read.

### Module constants

- `STATE_VERSION` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 27)
- `PROCESS_FIELDS` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 29)
- `VISIBLE` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 32)
- `NOT_VISIBLE` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 33)
- `UNKNOWN` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 34)
- `_WORKED_LEVEL` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 36)
- `_ANSWER_KINDS` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 37)
- `_WORKED_KINDS` ([src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py), line 38)

### Explicit exports

`__all__` declares:

- `NOT_VISIBLE`
- `PROCESS_FIELDS`
- `STATE_VERSION`
- `UNKNOWN`
- `VISIBLE`
- `fields_at_ask`

## Internal implementation anchors

- `_dumps(value: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 41)
- `_visible_now(client: Any) -> str` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 45)
- `_attempt_state(context: str, attempt_id: str | None, attempt_progress: Any, *, has_item: bool) -> str` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 53)
- `_assists(connection: Any, practice_item_id: str) -> list[dict[str, Any]]` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 63)
- `_reveals(connection: Any, practice_item_id: str) -> dict[str, tuple[int, float]]` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 72)
- `_hints_before(assists: list[dict[str, Any]], session_id: str | None) -> int` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 80) — Hints shown on this item not yet attached to an attempt, in this session (the attempt's own window).
- `_preceding_move(connection: Any, assists: list[dict[str, Any]], *, context: str, practice_item_id: str | None, session_id: str | None) -> str` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 97) — The tutor's last move before this question: a hint's kind, an answer, or ``none``.
- `_opportunity(connection: Any, context: str, practice_item_id: str | None, session_id: str | None) -> tuple[str, str | None]` ([source](../../../../../../src/learnloop/router_objective/question_state.py), line 114) — What the question was asked from, and the presentation that opened it where one did.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]] — imports `module`; statically calls `fields_at_ask`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/stores/router_objective|learnloop.db.stores.router_objective]] — imports `module`; calls `column_present`, `table_present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `logging`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/tutor/tutor_qa|learnloop.tutor.tutor_qa]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ro0_question_state.py](../../../../../../tests/test_ro0_question_state.py) — direct import
  - `test_a_feedback_question_is_after_the_attempt`
  - `test_a_first_question_says_nothing_was_disclosed_and_visible_now_is_unknown`
  - `test_a_state_that_cannot_be_read_never_fails_the_question`
  - `test_ever_disclosed_and_visible_now_are_separate_fields`
  - `test_with_the_switch_off_nothing_is_written_whoever_sent_it`

## Modification guidance

- Make changes here when the responsibility remains question state within learnloop.router_objective; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/router_objective/question_state.py](../../../../../../src/learnloop/router_objective/question_state.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
