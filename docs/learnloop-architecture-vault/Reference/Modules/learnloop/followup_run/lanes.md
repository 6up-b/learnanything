---
title: "learnloop.followup_run.lanes"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/followup_run/lanes.py"
source_paths:
  - "src/learnloop/followup_run/lanes.py"
source_commit: "7465040da518ecae8b84745591a2f06c89954d05"
source_commit_timestamp: "2026-11-04T03:21:04-05:00"
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
  - "learnloop.followup_run.lanes module"
  - "src/learnloop/followup_run/lanes.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-followup-run"
---

# `learnloop.followup_run.lanes`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.followup_run.lanes` exists within [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] to own the behavior summarized by its module contract: Which lane a miss takes (spec §4), read after its diagnosis.

The authoritative system-level explanation remains in [[Architecture Overview]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/followup_run/lanes.py](../../../../../../src/learnloop/followup_run/lanes.py) |
| Source lines | 98 |
| Owning package | [[Reference/Modules/learnloop/followup_run/_package|learnloop.followup_run]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `clean` |
| Source commit | `7465040da518ecae8b84745591a2f06c89954d05` |
| Commit timestamp | `2026-11-04T03:21:04-05:00` |

## Public API

- `class LaneChoice` ([source](../../../../../../src/learnloop/followup_run/lanes.py), line 21)
- `concrete_rivals(repository: Repository, factor: dict[str, Any]) -> tuple[str, ...]` ([source](../../../../../../src/learnloop/followup_run/lanes.py), line 28) — The factor's concrete cause hypotheses that still exist, in its own order.
- `select_lane(repository: Repository, workflow: dict[str, Any]) -> LaneChoice` ([source](../../../../../../src/learnloop/followup_run/lanes.py), line 45) — The probe lane needs an open factor with two rivals; anything else is practice.
- `settle_practice_lane(vault: Any, repository: Repository, row: Mapping[str, Any], *, reason: str, release: str=WF.RELEASE_PRACTICE_LANE, clock: Clock | None=None) -> bool` ([source](../../../../../../src/learnloop/followup_run/lanes.py), line 59) — The practice lane, or the one fallback: the predecessor's chooser runs once.

### Explicit exports

`__all__` declares:

- `LaneChoice`
- `concrete_rivals`
- `select_lane`
- `settle_practice_lane`

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]] — imports `concrete_rivals`, `select_lane`, `settle_practice_lane`; statically calls `concrete_rivals`, `select_lane`, `settle_practice_lane`
- [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]] — imports `module`; statically calls `settle_practice_lane`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/attempts|learnloop.attempts.attempts]] — imports `AttemptResult`
- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/causal_attribution|learnloop.diagnosis.causal_attribution]] — imports `OPEN_SET_CAUSE_ID`
- [[Reference/Modules/learnloop/diagnosis/followups|learnloop.diagnosis.followups]] — imports `evaluate_attempt_intervention_followup`; calls `evaluate_attempt_intervention_followup`
- [[Reference/Modules/learnloop/followup_serve/queue|learnloop.followup_serve.queue]] — imports `enqueue_need`; calls `enqueue_need`
- [[Reference/Modules/learnloop/followup_serve/workflow|learnloop.followup_serve.workflow]] — imports `module`; calls `finish`

### Platform and third-party dependencies

- Standard library: `__future__`, `collections`, `dataclasses`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Initialize a Vault]]
- [[Start a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/followup_run/jobs|learnloop.followup_run.jobs]], [[Reference/Modules/learnloop/followup_run/serving|learnloop.followup_run.serving]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_followup_codex_review.py](../../../../../../tests/test_followup_codex_review.py) — direct import
- [tests/test_followup_workflow.py](../../../../../../tests/test_followup_workflow.py) — direct import
  - `test_a_settled_workflow_takes_nothing_more`

## Modification guidance

- Make changes here when the responsibility remains lanes within learnloop.followup_run; otherwise move the behavior to its owning boundary.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.
- Treat `__all__` as an intentional compatibility surface and update consumers and documentation when it changes.

### Regeneration and review checklist

1. Modify [src/learnloop/followup_run/lanes.py](../../../../../../src/learnloop/followup_run/lanes.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
