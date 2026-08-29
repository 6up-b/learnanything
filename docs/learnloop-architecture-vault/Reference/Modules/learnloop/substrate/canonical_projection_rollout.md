---
title: "learnloop.substrate.canonical_projection_rollout"
type: "module-reference"
status: "current"
refactor_status: "ACTIVE"
version: "1.0.0"
source_path: "src/learnloop/substrate/canonical_projection_rollout.py"
source_paths:
  - "src/learnloop/substrate/canonical_projection_rollout.py"
source_commit: "workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_worktree_state: "untracked"
generated: true
generated_at: "2026-08-18"
package: "learnloop.substrate"
layer: "domain"
concepts:
  - "Learning System"
  - "State and Persistence"
workflows:
  - "Inspect Persistent State"
  - "Rebuild and Shadow Compare"
aliases:
  - "learnloop.substrate.canonical_projection_rollout module"
  - "src/learnloop/substrate/canonical_projection_rollout.py"
tags:
  - "docs/module"
  - "architecture/reference"
  - "refactor/active"
  - "layer/domain"
  - "package/learnloop-substrate"
---

# `learnloop.substrate.canonical_projection_rollout`

> [!info] Generated source reference
> Facts in this note are generated from the Python AST, repository tests, and Git. Purpose and change guidance are conservative inferences from those facts. Regenerate with `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_generate.py`; do not hand-edit generated sections.

Up: [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] · Root: [[Module Catalog]] · Jump to [[#Public API|API]], [[#Who imports or calls it|callers]], [[#Tests that define behavior|tests]], or [[#Modification guidance|change guidance]].

## Why this module exists

`learnloop.substrate.canonical_projection_rollout` exists within [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] to own the behavior summarized by its module contract: Startup ownership for the canonical projection-version boundary.

The authoritative system-level explanation remains in [[Learning System]], [[State and Persistence]]; this note records where this source module participates rather than restating those concepts.

^module-purpose

## Source facts

| Fact | Value |
|---|---|
| Source | [src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py) |
| Source lines | 87 |
| Owning package | [[Reference/Modules/learnloop/substrate/_package|learnloop.substrate]] |
| Architecture layer | `domain` |
| Refactor status | `ACTIVE` |
| Worktree state | `untracked` |
| Source commit | `workspace/uncommitted @ HEAD 62fd1f6404cc3a3007c6f214ba9429c45ef0114f` |
| Commit timestamp | `2026-08-17T12:05:21-04:00` |

## Public API

- `refresh_canonical_projection_on_startup(vault: LoadedVault, repository: Repository, *, clock: Clock | None=None) -> str | None` ([source](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py), line 23) — Refresh the cache and stamp a changed projection baseline exactly once.

## Internal implementation anchors

No private top-level function or class definition is declared in this file.

## Who imports or calls it

> [!note] Static evidence boundary
> “Calls” below means a direct call through a statically imported name that the AST can resolve. Registry, entry-point, reflection, and string-based dispatch can add runtime consumers.

- [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]] — imports `refresh_canonical_projection_on_startup`; statically calls `refresh_canonical_projection_on_startup`

## Dependencies

### LearnLoop dependencies

- [[Reference/Modules/learnloop/clock|learnloop.clock]] — imports `Clock`
- [[Reference/Modules/learnloop/db/repositories|learnloop.db.repositories]] — imports `Repository`
- [[Reference/Modules/learnloop/learner/assessment_contracts|learnloop.learner.assessment_contracts]] — imports `CANONICAL_STATE_VERSIONS`
- [[Reference/Modules/learnloop/learner/facet_diagnostics|learnloop.learner.facet_diagnostics]] — imports `coverage_denominator_version`; calls `coverage_denominator_version`
- [[Reference/Modules/learnloop/ops/vault_lock|learnloop.ops.vault_lock]] — imports `vault_mutation_lock`; calls `vault_mutation_lock`
- [[Reference/Modules/learnloop/substrate/canonical_projection|learnloop.substrate.canonical_projection]] — imports `CANONICAL_PROJECTION_VERSION`, `project_canonical_facet_state`; calls `project_canonical_facet_state`
- [[Reference/Modules/learnloop/vault/models|learnloop.vault.models]] — imports `LoadedVault`

### Platform and third-party dependencies

- Standard library: `__future__`
- Third party: none imported directly

## Larger workflow participation

Use this module in context through:

- [[Inspect Persistent State]]
- [[Rebuild and Shadow Compare]]

Static participation evidence comes from [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]].

The workflow notes own end-to-end sequencing; this reference owns only the module-level source map, contracts, and change surface.

## Tests that define behavior

No test imports this module directly. These tests exercise a direct production consumer:

- [tests/test_canonical_projection_rollout.py](../../../../../../tests/test_canonical_projection_rollout.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_config_refactor.py](../../../../../../tests/test_config_refactor.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_dialogue_causal_join.py](../../../../../../tests/test_dialogue_causal_join.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_goal_scope_material.py](../../../../../../tests/test_goal_scope_material.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_graph_editor_reads.py](../../../../../../tests/test_graph_editor_reads.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_ingest_jobs.py](../../../../../../tests/test_ingest_jobs.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_ingest_latency_journey.py](../../../../../../tests/test_ingest_latency_journey.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_instrument_servability_journeys.py](../../../../../../tests/test_instrument_servability_journeys.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_km2_activation.py](../../../../../../tests/test_km2_activation.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_sidecar_adjudication.py](../../../../../../tests/test_sidecar_adjudication.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_sidecar_exams.py](../../../../../../tests/test_sidecar_exams.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]
- [tests/test_sidecar_goals.py](../../../../../../tests/test_sidecar_goals.py) — imports consumer [[Reference/Modules/learnloop_sidecar/context|learnloop_sidecar.context]]

## Modification guidance

- Change canonical projection rollout policy here when substrate owns the invariant; expose cross-domain use through public names and avoid new private or function-local dependency edges.
- Run the directly importing tests below, then the architecture/import-linter checks when imports or public ownership change.

### Regeneration and review checklist

1. Modify [src/learnloop/substrate/canonical_projection_rollout.py](../../../../../../src/learnloop/substrate/canonical_projection_rollout.py) and its owning tests.
2. Regenerate [[Module Catalog]] so imports, symbols, source provenance, and test anchors remain current.
3. Run `.venv/bin/python docs/learnloop-architecture-vault/_scripts/module_validate.py`.
4. If ownership or workflow behavior changed, update the linked canonical concept or workflow note—not a duplicate explanation here.
