---
title: Content Pipeline
aliases:
  - Canonical Source Pipeline
  - Ingest Architecture
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/content/pipeline/runner.py
  - src/learnloop/content/pipeline/jobs.py
  - src/learnloop/content/sources
  - src/learnloop/content/synthesis
  - src/learnloop/ingest
tags:
  - learnloop/architecture
  - learnloop/content
  - learnloop/ingest
---

# Content Pipeline

The content pipeline turns captured material into immutable revisions, structured passages, unit inventories and proposed study content. Acquisition and extraction live in `learnloop.ingest`. The durable host and content decisions live in `learnloop.content`. [[Source Authority and Provenance]] explains which artifact owns each fact.

## Durable checkpoint ladder

Import registers an asset and a revision, then extracts Document IR with blocks, anchors and health flags. A source set pins a revision and records the subject, role and selected units. Inventory validates the units and their proposed concepts. Synthesis reads the pinned scope and the chosen inventories, validates the candidate, and stages a proposal. A revision can be pinned before inventory. Durable jobs run as their recorded dependencies complete, and a failed or cancelled prerequisite blocks dependents.

^checkpoint-ladder

The source-kind table owns recognition and capabilities. The desktop reads ingest eligibility, role choices, retry and reuse from the sidecar. [[Reference/Modules/learnloop/ingest/source_kinds|Source kinds]] and [[Import Canonical Sources]] are the extension point and operator procedure.

## Durable runner semantics

The host claims a job with a worker ID and attempt number. The handler renews the lease and checks ownership before publishing. A replaced attempt cannot publish new vault files or canonical state. Its own started model receipt and a valid paid checkpoint may still be finished under the late-record allowance. A job waiting for learner input releases its lease. Cancellation is checked at progress and work boundaries. A stale lease can become an interrupted failure that can be resumed.

Each job type declares its handler and host policy in [[Reference/Modules/learnloop/content/pipeline/job_types|the job type table]]. Handlers live beside their features. The host uses the row for lane selection, AI admission and vault reload. For jobs that can affect practice, it compares the practice snapshot and publishes a changed queue revision with the terminal state, including lease recovery. The watcher and runner share the published snapshot. The compatibility names `legacy_ingest` and `exam_ingest` still have handlers. See [[Import Canonical Sources#Worker ownership and lease recovery|worker ownership and lease recovery]] for retry and lease details.

## Extraction choices

The extractor registry chooses the PDF engine and its consent requirement. `auto` can use hosted GLM-OCR with consent or a configured self-hosted GLM-OCR server. Without an available GLM-OCR route, the local path can use Marker then pypdf. An explicit engine can fail instead of switching. A native PDF or audio route sends the file to the configured canonical ingest provider when readiness and consent allow it. The shared modality check supplies the same readiness reason to import and Settings. Read [[Privacy and Trust Boundaries#Source acquisition egress]] before selecting an engine. [[AI Architecture#Task routes]] explains the separate transcription route.

## Synthesis and apply

Bootstrap reads the brief's scope. Append selects new inputs and a bounded neighborhood of the current map. Both use the shared run setup, checkpointed shard runner, normalization, gate and proposal stages, with mode-specific rules. [[Build a Study Map]] gives the operating choices. [[Synthesis Identity and Caches]] explains how a validated answer is reused and why the manifest remains a record of the inputs.

Application commits a write-ahead intent with the target pre-images and new contents. It publishes the files, reconciles state and marks the intent applied. Recovery finishes a compatible pending intent and preserves a newer file when it conflicts. Pending or conflicted work blocks another accept. See [[Doctor Migrations and Recovery#Proposal apply recovery]].

## Modification guidance

Add acquisition and extraction to the source-kind and extractor authorities. Put a new durable handler beside its feature and register its host policy in the job table. Preserve lease fencing, stable revision identity and per-request checkpointing. Keep routing in [[AI Architecture]], and accept model output only through the feature's gates. To inspect the planner's scope, inventory and auto-apply records, use [[Debug a decision]].
