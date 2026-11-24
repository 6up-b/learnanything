---
title: Build a Study Map
aliases:
  - Inventory and Synthesis Workflow
  - Study Map Synthesis
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/cli/app.py
  - src/learnloop/content/synthesis/source_set_synthesis.py
  - src/learnloop/content/synthesis/source_append.py
  - src/learnloop/content/synthesis/normalize.py
  - src/learnloop/content/synthesis/source_coverage.py
  - src/learnloop/content/synthesis/synthesis_gates.py
  - src/learnloop/content/synthesis/synthesis_manifests.py
  - tests/test_source_set_synthesis.py
  - tests/test_synthesis_gates.py
  - tests/test_synthesis_manifests.py
tags:
  - learnloop/workflow
  - learnloop/content
  - learnloop/synthesis
---

# Build a Study Map

A Study Map build proposes learning objects, facets, dependencies, rubrics and practice items from a pinned source set. The [[Canonical Knowledge Model]] defines those objects. [[Learning System]] explains how they become evidence targets. Start with a vault at a [[ADR-019 The oldest supported tag|supported tag]] and a set prepared through [[Import Canonical Sources]].

## Inspect coverage

```bash
SET_ID=learning-science
learnloop source-coverage "$SET_ID" --json --vault "$VAULT"
```

Review the pinned revisions, selected units, roles and readiness flags. Fix the source set when it is missing material. The build uses the `canonical_ingest` route unless you select another profile with `--ai-provider`. See [[Configure AI Providers]].

## Pick the build mode

| Mode | What it sends | What happens on success |
|---|---|---|
| Bootstrap | The brief's scoped inventories, divided into shards and combined into a graph. | A proposal. `--apply` accepts it after the gates pass. |
| Append | Newly inventoried units and a bounded neighborhood of the current map. | One proposal across the passes. Routine links that pass the auto-apply conditions can be applied immediately. Other items wait for review. |

CLI `--mode auto` chooses append when the loaded vault already has evidence facets, including facets in another subject. The desktop chooses per subject. Use an explicit mode when that difference matters.

```bash
learnloop synthesize "$SET_ID" --mode bootstrap --json --vault "$VAULT"
learnloop synthesize "$SET_ID" --mode append --json --vault "$VAULT"
learnloop proposals --json --vault "$VAULT"
```

By default an append selects units that no kept synthesis of this set has sent. A completed run whose proposal was wholly rejected does not count as kept. If there are no new units, the CLI returns before resolving a provider. Use `--new-revision` to send an explicitly named revision whole.

An append that needs several requests groups whole inventories in reading order. Each group uses the run's bounded neighborhood and has a base request with at most one span round. A span round without room can leave the base answer as the result. A single inventory over the ceiling is refused. Completed, valid checkpoints let a retry reuse paid answers. The merged candidate passes through one downstream validation and proposal path. Each physical request remains subject to the applicable spend admission. See [[Reference/Modules/learnloop/content/synthesis/source_append|append mode]] and [[Synthesis Identity and Caches]].

## Apply deliberately

Review the proposal and its gate findings. For a bootstrap you intend to accept on success, run `synthesize` with `--mode bootstrap --apply`. On an append, read the result's applied and waiting items even if you omitted `--apply`. The append path applies routine links through its own gate.

```bash
learnloop accept "$PATCH_ID" --all --vault "$VAULT"
```

Acceptance publishes files under the vault mutation lock and records the apply intent. Use [[Content Pipeline]] for that write boundary and [[Database Catalog]] for table roles.

## Repair a preserved failed candidate

A bootstrap that failed hard gates can leave its merged candidate on the run. Inspect it before requesting another build.

```bash
learnloop synthesize-repair "$RUN_ID" --dry-run --json --vault "$VAULT"
learnloop synthesize-repair "$RUN_ID" --json --vault "$VAULT"
```

The repair derives mechanical fixes and can take a JSON `--ops-file` with `drop_dependency` or `remap_dependency` operations. It revalidates the saved candidate without a model call. `--apply` accepts a passing result. Append has no preserved-candidate repair. See [[Reference/Modules/learnloop/content/synthesis/source_set_synthesis|the shared run and bootstrap repair reference]].

## Confirm the learning surface

Run `learnloop doctor --json --vault "$VAULT"` after applying. Use `learnloop review --limit 5 --json --vault "$VAULT"` to see what the serving queue selects. Use [[Start a Learning Cycle]] to practice, and [[Debug a decision]] to inspect the scope, selected inventories and auto-apply decisions on a planner trace.

## Modification note

The shared run reads the source set and records its manifest. Mode definitions provide scope, budgets and application policy. The shared shard runner manages request checkpoints. Normalization and gates own the candidate's meaning and acceptance. Change those rules in the synthesis domain, with its gate and repair tests.
