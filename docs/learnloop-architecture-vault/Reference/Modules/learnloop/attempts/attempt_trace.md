---
title: "learnloop.attempts.attempt_trace"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/attempts/attempt_trace.py"
source_paths:
  - "src/learnloop/attempts/attempt_trace.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.attempts"
layer: "domain"
concepts:
  - "Learning System"
workflows:
  - "Process Model Output"
  - "Inspect Persistent State"
aliases:
  - "learnloop.attempts.attempt_trace module"
  - "src/learnloop/attempts/attempt_trace.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-attempts"
---

# `learnloop.attempts.attempt_trace`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.attempts.attempt_trace` exists within [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] to own the behavior summarized by its module contract: Attempt trace — the criterion DAG per attempt (KM §9.6, generalizing the longform trace to every multi-facet item).

The authoritative system-level explanation remains in [[Learning System]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/attempts/attempt_trace.py](../../../../../../src/learnloop/attempts/attempt_trace.py) |
| Source lines | 183 |
| Owning package | [[Reference/Modules/learnloop/attempts/_package|learnloop.attempts]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `class TraceTarget` ([source](../../../../../../src/learnloop/attempts/attempt_trace.py), line 36)
- `class TraceCriterion` ([source](../../../../../../src/learnloop/attempts/attempt_trace.py), line 43)
  - `as_dict(self) -> dict[str, object]` (line 55; public)
- `class AttemptTrace` ([source](../../../../../../src/learnloop/attempts/attempt_trace.py), line 74)
  - `has_dag(self) -> bool` (line 81; public) — True when some criterion actually declares a dependency (a real DAG).
  - `as_dict(self) -> dict[str, object]` (line 86; public)
- `build_attempt_trace(vault: LoadedVault, repository: Repository, attempt_id: str) -> AttemptTrace | None` ([source](../../../../../../src/learnloop/attempts/attempt_trace.py), line 99) — Reconstruct the per-branch criterion trace for one attempt (pure/derived).

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]] — imports `build_attempt_trace`; statically calls `build_attempt_trace`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/attempts/grading|learnloop.attempts.grading]] — imports `resolved_rubric`; calls `resolved_rubric`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/capability_mapping|learnloop.learner.capability_mapping]] — imports `CriterionOutcome`, `compile_criterion_targets`, `localize_criterion_outcomes`; calls `CriterionOutcome`, `compile_criterion_targets`, `localize_criterion_outcomes`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `FAILURE_THRESHOLD`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`, `dataclasses`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Process Model Output]]
- [[Inspect Persistent State]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/handlers/knowledge_model|learnloop_sidecar.handlers.knowledge_model]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No direct or one-hop consumer test was found by static import analysis.

> [!caution] Test gap signal
> Treat this as a navigation signal, not proof that behavior is untested: dynamic and higher-level coverage is outside this static map. Add focused coverage when changing isolated behavior here.

## Modification guidance

- Change attempt trace policy here when attempts owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/attempts/attempt_trace.py](../../../../../../src/learnloop/attempts/attempt_trace.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
