---
title: "learnloop.learner.learner_review_feed"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/learner_review_feed.py"
source_paths:
  - "src/learnloop/learner/learner_review_feed.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.learner.learner_review_feed module"
  - "src/learnloop/learner/learner_review_feed.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.learner_review_feed`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.learner_review_feed` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Learner-facing changelog and standing working hypotheses.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/learner_review_feed.py](../../../../../../src/learnloop/learner/learner_review_feed.py) |
| Source lines | 220 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `build_learner_review_feed(vault: LoadedVault, repository: Repository) -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/learner_review_feed.py), line 31)

## Internal implementation anchors

- `_empty_belief_change() -> dict[str, Any]` ([source](../../../../../../src/learnloop/learner/learner_review_feed.py), line 14) — Zeroed belief-change fields shared by system-authored changelog entries.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]] — imports `build_learner_review_feed`; statically calls `build_learner_review_feed`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/diagnosis/remediation|learnloop.diagnosis.remediation]] — imports `misconception_status_history`; calls `misconception_status_history`
- [[Reference/Modules/learnloop/learner/session_learning_diff|learnloop.learner.session_learning_diff]] — imports `session_learning_diffs`; calls `session_learning_diffs`
- [[Reference/Modules/learnloop/learner/surfaced_beliefs|learnloop.learner.surfaced_beliefs]] — imports `surfaced_belief_corrections`; calls `surfaced_belief_corrections`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `typing`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/review|learnloop_sidecar.handlers.review]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_causal_p2_acceptance.py](../../../../../../tests/test_causal_p2_acceptance.py) — direct import
  - `test_projection_version_names_the_open_cause_union`
- [tests/test_contract_frontier_coverage.py](../../../../../../tests/test_contract_frontier_coverage.py) — direct import
  - `test_the_denominator_change_is_narrated_as_one_recalibration`
- [tests/test_coverage_denominator_boundary.py](../../../../../../tests/test_coverage_denominator_boundary.py) — direct import
  - `test_apply_writes_one_boundary_and_a_rerun_writes_none`
- [tests/test_durable_promotion_arms.py](../../../../../../tests/test_durable_promotion_arms.py) — direct import
- [tests/test_learner_review_system_entries.py](../../../../../../tests/test_learner_review_system_entries.py) — direct import
  - `test_review_feed_bulk_loads_timeline_history_once`
- [tests/test_surfaced_belief_corrections.py](../../../../../../tests/test_surfaced_belief_corrections.py) — direct import
  - `test_withdrawal_drops_the_belief_from_working_hypotheses`
  - `test_withdrawals_interleave_reverse_chronologically`

## Modification guidance

- Change learner review feed policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/learner_review_feed.py](../../../../../../src/learnloop/learner/learner_review_feed.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
