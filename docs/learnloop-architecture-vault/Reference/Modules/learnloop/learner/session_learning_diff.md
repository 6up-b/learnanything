---
title: "learnloop.learner.session_learning_diff"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/learner/session_learning_diff.py"
source_paths:
  - "src/learnloop/learner/session_learning_diff.py"
generated: true
generated_at: "2026-11-02"
package: "learnloop.learner"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Start a Learning Cycle"
  - "Continue a Learning Cycle"
aliases:
  - "learnloop.learner.session_learning_diff module"
  - "src/learnloop/learner/session_learning_diff.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-learner"
---

# `learnloop.learner.session_learning_diff`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST and repository tests, at the commit in [[Reference/_generated|Generated Reference Provenance]]. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.learner.session_learning_diff` exists within [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] to own the behavior summarized by its module contract: Learning-state changes attributable to one completed practice session.

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/learner/session_learning_diff.py](../../../../../../src/learnloop/learner/session_learning_diff.py) |
| Source lines | 161 |
| Owning package | [[Reference/Modules/learnloop/learner/_package|learnloop.learner]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |

## Public API

- `session_learning_diff(vault: LoadedVault, repository: Repository, session_id: str) -> dict[str, object]` ([source](../../../../../../src/learnloop/learner/session_learning_diff.py), line 16)
- `session_learning_diffs(vault: LoadedVault, repository: Repository, sessions: list[dict]) -> dict[str, dict[str, object]]` ([source](../../../../../../src/learnloop/learner/session_learning_diff.py), line 41) — Compute every supplied session diff from one facet-timeline replay.

## Internal implementation anchors

- `_empty_diff() -> dict[str, object]` ([source](../../../../../../src/learnloop/learner/session_learning_diff.py), line 153)

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]] — imports `session_learning_diffs`; statically calls `session_learning_diffs`
- [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]] — imports `session_learning_diff`; statically calls `session_learning_diff`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `parse_utc`; calls `parse_utc`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/facet_evidence_timeline|learnloop.learner.facet_evidence_timeline]] — imports `facet_evidence_timelines`, `load_facet_timeline_snapshot`; calls `facet_evidence_timelines`, `load_facet_timeline_snapshot`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `datetime`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Start a Learning Cycle]]
- [[Continue a Learning Cycle]]

Static participation evidence comes from [[Reference/Modules/learnloop/learner/learner_review_feed|learnloop.learner.learner_review_feed]], [[Reference/Modules/learnloop_sidecar/handlers/sessions|learnloop_sidecar.handlers.sessions]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

- [tests/test_ux_phase4_feedback.py](../../../../../../tests/test_ux_phase4_feedback.py) — direct import
  - `test_f4_a_shared_facet_credits_only_the_topic_whose_answer_earned_it`
  - `test_f4_the_learning_diff_names_the_attempts_whose_points_raised_a_demonstrated_facet`
  - `test_the_learning_diff_names_the_facets_it_counts`
  - `test_the_session_finish_names_a_topic_shown_on_your_own`

## Modification guidance

- Change session learning diff policy here when learner owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/learner/session_learning_diff.py](../../../../../../src/learnloop/learner/session_learning_diff.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
