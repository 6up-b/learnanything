---
title: "learnloop.followup_run.decision_view"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/decision_view.py"
source_paths:
  - "src/learnloop/followup_run/decision_view.py"
source_commit: "a01ecfbb27093bad0f8c7924a0558bfc49acbc22"
source_commit_timestamp: "2026-11-04T01:43:14-05:00"
source_worktree_state: "clean"
generated: true
generated_at: "2026-11-02"
package: "learnloop.followup_run"
layer: "domain"
concepts:
  - "Architecture Overview"
workflows:
  - "Initialize a Vault"
  - "Start a Learning Cycle"
aliases:
  - "learnloop.followup_run.decision_view module"
  - "src/learnloop/followup_run/decision_view.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.decision_view`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.decision_view` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: The router's decision, in one plain line (spec §6.4).

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/decision_view.py](../../../../../../src/learnloop/followup_run/decision_view.py) |
| Source lines | 105 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `a01ecfbb27093bad0f8c7924a0558bfc49acbc22` |
| Commit timestamp | `2026-11-04T01:43:14-05:00` |

## Public API

- `show_router_decisions(vault: Any) -> bool` ([source](../../../../../../src/learnloop/followup_run/decision_view.py), line 26)
- `decision_view(repository: Repository, decision_id: str | None) -> dict[str, Any] | None` ([source](../../../../../../src/learnloop/followup_run/decision_view.py), line 47) — The line and its *details*, or None for a decision the ledger doesn't hold.

### Module constants

- `_ARMS` ([src/learnloop/followup_run/decision_view.py](../../../../../../src/learnloop/followup_run/decision_view.py), line 17)
- `_DRAWS` ([src/learnloop/followup_run/decision_view.py](../../../../../../src/learnloop/followup_run/decision_view.py), line 20)
- `_MODELS` ([src/learnloop/followup_run/decision_view.py](../../../../../../src/learnloop/followup_run/decision_view.py), line 23)

### Explicit exports

`__all__` declares:

- `decision_view`
- `show_router_decisions`

## Internal implementation anchors

- `_parsed(value: Any) -> Any` ([source](../../../../../../src/learnloop/followup_run/decision_view.py), line 30)
- `_label(ref: str) -> str` ([source](../../../../../../src/learnloop/followup_run/decision_view.py), line 39)
- `_percent(value: float) -> str` ([source](../../../../../../src/learnloop/followup_run/decision_view.py), line 43)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `decision_view`, `show_router_decisions`
- [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]] — imports `decision_view`, `show_router_decisions`; statically calls `decision_view`, `show_router_decisions`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/db/stores/followup_serve|learnloop.db.stores.followup_serve]] — imports `module`; calls `any_feedback_held`, `present`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `json`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]], [[Reference/Modules/learnloop_sidecar/handlers/daily_plan|learnloop_sidecar.handlers.daily_plan]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
  - `test_f2_another_decisions_card_is_held_too_since_cards_list_open_problems`
- [tests/test_followup_router.py](../../../../../../tests/test_followup_router.py) — direct import
  - `test_the_decision_line_says_what_the_screen_should`

## Modification guidance

- Make changes here when the responsibility remains decision view within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/decision_view.py](../../../../../../src/learnloop/followup_run/decision_view.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
