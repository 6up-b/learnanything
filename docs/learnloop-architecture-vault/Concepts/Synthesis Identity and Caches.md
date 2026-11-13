---
title: Synthesis Identity and Caches
aliases:
  - Synthesis Manifest
  - Rebuild Reuse
status: active
doc_version: 1.0.0
implementation_version: mvp-0.59
last_reviewed: 2026-11-13
source_commit: 7c3dc20ee6b03667f078df61f3b5df28ab445412
source_commit_timestamp: "2026-11-13T08:19:21-05:00"
source_paths:
  - src/learnloop/content/synthesis/synthesis_manifests.py
  - src/learnloop/content/synthesis/proposal_match.py
  - src/learnloop/content/synthesis/source_set_synthesis.py
  - src/learnloop/content/synthesis/source_append.py
  - src/learnloop/ai/execution.py
  - tests/test_rerun_proposals.py
tags:
  - learnloop/concept
  - learnloop/sources
  - learnloop/provenance
---

# Synthesis Identity and Caches

A study-map build (a bootstrap or an append) is paid for once per distinct request, and the learner sees one proposal per distinct result. Two different things make that true, and they are kept apart:

- **What decides reuse** is the request each paid call sends, and the rows a run proposes.
- **What records a run** is its manifest. Nothing looks a run up by it.

## The checkpoints decide what is paid

Every paid structured call of ingestion goes through one checkpoint cycle (`ai/execution.py`): inventory windows, synthesis passes, the concept graph structuring call, the append call and its span round, persona fire judgements, vault epigraphs and the facet identity judges. Its key is the rendered request: purpose, prompt, schema and provider settings. Two outer layers answer before them, each only for the request it was paid under: a unit's inventory row and a shard's completed result. See [[Import Canonical Sources]] for each key.

A rebuild therefore runs the whole orchestration again. Each call whose request is unchanged answers from its checkpoint at no cost. A call whose request changed is paid: a role override, a new concept edge, an inventory re-read in place, an edited prompt, a resolved brief. The gates, the facet plan and apply always run under today's code.

## The proposal rule decides what the learner sees

Running again normalizes to the same rows as the run it repeats. Writing them again would put a second copy in the review inbox. So `proposal_match` compares a run's normalized and gated rows with the proposals earlier runs of the same source set persisted under the same purpose, before anything is written:

| equal earlier proposal | result |
|---|---|
| an item still waits (whatever the others' decisions) | that proposal; nothing new is written; an apply the caller asked for applies its waiting items; no epigraphs |
| nothing waits, not all rejected (applied, or applied and rejected) | nothing new: nothing is written or applied |
| every item rejected | not offered again: the run's saved answers are dropped and it pays for fresh ones |
| none | a new proposal, as before |

"Equal" compares, per `client_item_id`, the item's type, operation, target, payload as proposed, source refs, audit (the instrument gates' verdicts), validation status and errors, and dependencies by client id. It leaves out what each run mints or the review writes: ids, timestamps, decisions, edits, applied batch and dependency status. A rejected item is never put back: a partly rejected proposal is returned as it is, and an apply takes only its waiting items.

## The manifest records what a run read

`synthesis_manifests` holds, for each run, the source set and members with their per-unit role overrides; revisions and their asset hashes; extractions and their extractor versions; each unit's inventory row by id, extraction and content hash, beside its version labels; the scope (an append's change, units, neighbourhood and revision-diff hash; the nominator's and judge's identity when on); the resolved brief (an append inherits the learner's level as a bootstrap does); prompt and schema versions; provider and model; the curriculum snapshot, its concept edges included; facet registry and task graph hashes; and the budgets.

Because it is a record, a field that moves (a budget, the task graph, a config dump) costs nothing, and an input it lacks makes the record incomplete, never a reuse wrong. Manifests written before it stopped being a key keep their bytes and are read as they are. The runs' manifests also say which units an append still has to send (`units_not_yet_sent`).

## What a rebuild costs

An identical rebuild makes no model calls, but it re-runs the CPU stages that the old run-level lookup skipped: normalization, the gates, the instrument gates, the facet plan and the proposal comparison. Measured on copies of real study maps of 100-200 items, that took about 0.35-1.2 s, where the lookup took 0.16-0.6 s. The gate stage itself takes milliseconds.

The first identical rebuild of a subject whose earlier run predates per-call checkpoints for structuring and persona fire judgements pays those calls once.

See also [[Build a Study Map]], [[Source Authority and Provenance]].
