---
title: "learnloop.adaptive_difficulty.outcomes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/adaptive_difficulty/outcomes.py"
source_paths:
  - "src/learnloop/adaptive_difficulty/outcomes.py"
source_commit: "720de3fcf94e2c5856c0de04bafb85b735a83b96"
source_commit_timestamp: "2026-11-03T12:23:09-05:00"
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
  - "learnloop.adaptive_difficulty.outcomes module"
  - "src/learnloop/adaptive_difficulty/outcomes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-adaptive-difficulty"
---

# `learnloop.adaptive_difficulty.outcomes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.adaptive_difficulty.outcomes` exists within [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] to own the behavior summarized by its module contract: §5.3's outcome categories: help-adjusted, ordinal, with an explicit censored class.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py) |
| Source lines | 145 |
| Owning package | [[Reference/Modules/learnloop/adaptive_difficulty/_package|learnloop.adaptive_difficulty]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `720de3fcf94e2c5856c0de04bafb85b735a83b96` |
| Commit timestamp | `2026-11-03T12:23:09-05:00` |

## Public API

- `class HelpQuestion` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 45) — A help-equivalent practice question bound to the attempt: its logged progress marker.
  - `before_work(self) -> bool` (line 52; public)
  - `after_work(self) -> bool` (line 56; public)
- `class AttemptFacts` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 61)
- `help_timing(facts: AttemptFacts) -> str` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 74)
- `category(facts: AttemptFacts) -> int | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 87) — ``2``, ``1``, ``0``, :data:`CENSORED`, or None when the attempt is excluded (§5.3).
- `unassisted_success(category_value: int | None) -> float | None` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 109) — The binary event: 1 for ``Y = 2``, 0 otherwise; None when excluded.
- `help_questions_from_rows(rows: Iterable[dict]) -> tuple[HelpQuestion, ...]` ([source](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 118)

### Module constants

- `NO_DRAFT` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 31)
- `DRAFT_STARTED` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 32)
- `NONE` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 34)
- `BEFORE_WORK` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 35)
- `AFTER_WORK` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 36)
- `UNKNOWN` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 37)
- `ELIGIBLE_TYPES` ([src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py), line 40)

### Explicit exports

`__all__` declares:

- `AFTER_WORK`
- `AttemptFacts`
- `BEFORE_WORK`
- `DRAFT_STARTED`
- `ELIGIBLE_TYPES`
- `HELP_TYPES`
- `HelpQuestion`
- `NONE`
- `NO_DRAFT`
- `UNKNOWN`
- `category`
- `help_questions_from_rows`
- `help_timing`
- `unassisted_success`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]] — imports `module`
- [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]] — imports `module`; statically calls `unassisted_success`
- [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]] — imports `module`; statically calls `AttemptFacts`, `category`, `help_questions_from_rows`
- [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]] — imports `module`; statically calls `unassisted_success`
- [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]] — imports `module`; statically calls `AttemptFacts`, `category`, `unassisted_success`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/adaptive_difficulty/model|learnloop.adaptive_difficulty.model]] — imports `CENSORED`
- [[Reference/Modules/learnloop/adaptive_difficulty/priors|learnloop.adaptive_difficulty.priors]] — imports `module`
- [[Reference/Modules/learnloop/delayed_completion|learnloop.delayed_completion]] — imports `HELP_TYPES`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/adaptive_difficulty/arms|learnloop.adaptive_difficulty.arms]], [[Reference/Modules/learnloop/adaptive_difficulty/history_resolve|learnloop.adaptive_difficulty.history_resolve]], [[Reference/Modules/learnloop/adaptive_difficulty/replay|learnloop.adaptive_difficulty.replay]], [[Reference/Modules/learnloop/adaptive_difficulty/scoring|learnloop.adaptive_difficulty.scoring]], [[Reference/Modules/learnloop/router_objective/checks|learnloop.router_objective.checks]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ad23_fix_review.py](../../../../../../tests/test_ad23_fix_review.py) — direct import
  - `test_a_stuck_answer_is_forced_to_fail_only_when_empty`
  - `test_an_i_dont_know_answer_still_fails_whatever_its_grade`
- [tests/test_ad2_model.py](../../../../../../tests/test_ad2_model.py) — direct import
  - `test_unknown_hint_timing_never_read_as_after_work`

## Modification guidance

- Make changes here when the responsibility remains outcomes within learnloop.adaptive_difficulty; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/adaptive_difficulty/outcomes.py](../../../../../../src/learnloop/adaptive_difficulty/outcomes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
