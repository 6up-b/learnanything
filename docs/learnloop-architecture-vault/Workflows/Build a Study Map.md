---
title: Build a Study Map
aliases:
  - Inventory and Synthesis Workflow
  - Study Map Synthesis
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/cli/app.py
  - src/learnloop/content/synthesis/source_set_synthesis.py
  - src/learnloop/content/synthesis/source_append.py
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

This workflow converts a pinned source set into proposed learning objects, facets, dependencies, rubrics, and practice items, validates the whole candidate, then optionally applies it. The semantics belong to [[Learning System]] and [[Canonical Knowledge Model]]; the steps here describe the operator boundary.

## Prerequisites

- a subject-scoped source set with pinned revisions from [[Import Canonical Sources]]
- `source-coverage <set-id>` reports ready, or its flags have been intentionally resolved
- the `canonical_ingest` route is ready; see [[Configure AI Providers]]
- vault `algorithm_version` is mvp-0.9 (mvp-0.7 or later is required to apply)

## 1. Inspect coverage

```bash
VAULT="$HOME/LearnLoop/linear-algebra"
SET_ID=learning-science

uv run learnloop source-coverage "$SET_ID" --json --vault "$VAULT"
```

Review selected units, revision pins, roles, and readiness flags. Fix source membership rather than asking synthesis to infer missing material.

## 2. Generate a staged candidate

```bash
uv run learnloop synthesize "$SET_ID" \
  --mode auto \
  --ai-provider codex \
  --json \
  --vault "$VAULT"
```

Without `--apply`, the result remains a proposal. `--mode auto` chooses `bootstrap` when no study map/facets have been applied and `append` when the subject already has one. Append mode limits regeneration to the affected neighborhood.

The response identifies the proposal/run, item counts, reuse state, gate diagnostics, and identifiability generation needs. Inspect pending proposals:

```bash
uv run learnloop proposals --json --vault "$VAULT"
```

> [!important] Gate invariant
> A candidate is applied only after referential, source-grounding, rubric, dependency, and identifiability gates accept it. Model output is a proposal; validators own acceptance.

## Apply deliberately

For a new run that should apply on success:

```bash
uv run learnloop synthesize "$SET_ID" \
  --mode auto --apply --json --vault "$VAULT"
```

For a separately reviewed patch, use the proposal id and its item selection:

```bash
uv run learnloop accept <patch-id> --all --vault "$VAULT"
```

Application occurs under the vault mutation lock. Afterward, observe subject files such as learning objects/practice items plus proposal and synthesis receipts in SQLite. Use [[Database Catalog]] for exact table ownership.

## 4. Repair a preserved failed candidate

Hard gate failures preserve the expensive merged candidate. First inspect the dry run:

```bash
uv run learnloop synthesize-repair <run-id> \
  --dry-run --json --vault "$VAULT"
```

Then apply mechanically safe repairs and revalidate without another model call:

```bash
uv run learnloop synthesize-repair <run-id> \
  --apply --json --vault "$VAULT"
```

An explicit JSON operations file can contain typed `drop_dependency` or `remap_dependency` operations. Use it only after reviewing the stored diagnostics.

> [!info] Zero-call recovery
> Repair works from the preserved candidate and checkpoints. It is not a second synthesis run and should retain provenance to the original source set and agent run.

## 5. Confirm the learning surface

```bash
uv run learnloop doctor --json --vault "$VAULT"
uv run learnloop review --limit 5 --json --vault "$VAULT"
```

The first command checks structural references and state health. The second proves eligible practice can be selected without starting a UI session. Continue with [[Start a Learning Cycle]].

## Modification note

- change source selection and unit policy in the source-set/inventory layer;
- change proposal generation in `content/synthesis` AI contracts and synthesis services;
- change acceptance rules in synthesis gates, with gate tests;
- do not weaken application validation in a CLI/desktop adapter.

## Related notes

- [[Learning System]]
- [[Canonical Knowledge Model]]
- [[Content Pipeline]]
- [[Start a Learning Cycle]]
