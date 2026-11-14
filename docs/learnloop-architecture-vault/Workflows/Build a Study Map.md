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
  --json \
  --vault "$VAULT"
```

The model comes from the `canonical_ingest` route in `[ai.routing]` (the ChatGPT plan's `chatgpt_medium` profile by default); `--ai-provider <profile>` picks another profile for this run (see [[Configure AI Providers]]).

Without `--apply`, the result remains a proposal. The CLI's `--mode auto` chooses `append` when the vault already has evidence facets (in any subject) and `bootstrap` otherwise; the desktop's builds (a collection's build batch, and a bootstrap job queued with `auto`) decide per subject: `append` once a learning object is scoped to the source set's subject (`subject_has_applied_study_map`). An append sends the existing map only as the bounded neighbourhood around its new material (capped by `append_neighborhood_input_tokens`), and refuses before paying a request over `append_input_ceiling`. An append sends as new only the set's units that no kept synthesis of it has sent (a completed run whose proposal was not wholly rejected, read from the runs' manifests): a wholly new member whole, a partly sent one narrowed to its unsent units. If nothing is new it sends nothing and says so; `--new-revision <id>` sends the named revisions whole instead.

The response identifies the proposal/run, item counts, reuse state, gate diagnostics, and identifiability generation needs. Inspect pending proposals:

```bash
uv run learnloop proposals --json --vault "$VAULT"
```

> [!important] Gate invariant
> A candidate is applied only after referential, source-grounding, rubric, dependency, and identifiability gates accept it. Model output is a proposal; validators own acceptance.

### One head, one tail, two modes

Both modes open their run in one function, `open_synthesis_run` in `content/synthesis/source_set_synthesis.py`: it finds the source set, resolves the brief (with the learner's declared level), reads the set's inputs, lets the mode decide its scope, then persists the manifest that records all of it and opens the agent run and the synthesis run. An unknown source set (and, for bootstrap, a mode other than `auto` or `bootstrap`) is refused before anything is written. The mode's scope step is its own: bootstrap records the brief's scope and reads every scope unit; an append selects its new inventories and the neighbourhood around them, whose record (with each entity's match reasons, names tried in sorted order) the manifest keeps and whose context the request reads.

Everything after the head is one function too, `finish_synthesis_run`, beside it. It asks the model through one shard runner (`_run_synthesis`) for both modes: the run's input in units, each a base pass and at most one span round, every request answered by its checkpoint when the same request was paid before, held to the mode's budgets before it is sent and saved before its output is checked. Bootstrap's units are shards of the whole scope's inventories (each filed as a shard result, its ids made local, merged, then structured into a graph); an append's is one unit, its new inventories with the neighbourhood as context. Then it plans facet identity, normalizes, runs the synthesis gates and the instrument gates, compares the rows with the set's earlier proposals (an equal waiting proposal is the result; an equal wholly rejected one is paid for again, once), persists, finalizes the run rows, applies, and writes epigraphs. What the two modes decide differently is one record with a row each, `SynthesisMode` (`BOOTSTRAP`, and `APPEND` in `source_append.py`):

- the agent run's purpose, prompt template, output schema and prompt version, the mode the synthesis run records, and which budgets the manifest's `token_budget` names;
- the call (`SynthesisCall`): the request and its checkpoint key, the units, the pass context, and the budget rule: bootstrap's shard and total ceilings, or the append's `append_input_ceiling` for each request alone (refused typed, before paying) and `append_output_tokens` for each answer;
- the append's normalizer adds its own item kinds (provenance links, notation mappings, conflicts, restructures) and the client ids §10.3 auto-applies; the gates judge the append vocabulary;
- bootstrap keeps its candidate on the run for the zero-call repair below; append has none;
- what is applied: bootstrap the whole proposal (and the exam goal) when asked; append its routine links, then the study-map diff and the facet doctor;
- the gate-failure code (`synthesis_gate_failed` or `append_gate_failed`), the proposal's purpose and the epigraph digest.

A few differences are kept as they were until one rule is chosen: an append runs no identifiability analysis (so the invariant above holds for bootstrap only), has no typed client-id collision check, records its run's usage only with a new proposal and then without the call's record, records no resolved span hashes, declares no budgets on its receipts, drains its client's usage at the end of the run, and names the answers it dropped after a rejected match again at a later drop. The refactor bug ledger lists them (K2-9 to K2-15, K2-17).

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
