---
title: ADR-022 Scope polled jobs to vault and epoch
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
decision_date: 2026-11-23
decision_status: accepted
last_reviewed: 2026-11-23
source_commit: 9038b096e7446d5f433f95d881de7e7c1bd0da15
source_commit_timestamp: "2026-11-23T19:57:34-05:00"
source_paths:
  - src/learnloop_sidecar/polled_jobs.py
  - src/learnloop_sidecar/background_jobs.py
  - src/learnloop_sidecar/context.py
  - apps/learnloop-tauri/src/api/poller.ts
  - tests/test_reader_rd3_fix_backend.py
tags:
  - learnloop/decision
  - learnloop/reader
  - learnloop/sidecar
---

# ADR-022 Scope polled jobs to vault and epoch

## Context

The sidecar responds serially. A slow model call held in an RPC would delay desk writes and reads behind it. Work can also finish after the learner changes vaults or closes the sidecar context.

## Decision

Run long work on a context-owned thread. Start returns a job id and poll reads its state immediately. Each registry indexes jobs and request records by vault and id. The job captures the background epoch for its liveness guard. Switching vaults interrupts the old vault's unfinished polled jobs. Closing ends the background epoch. A cancelled or interrupted job refuses its next model request before sending it.

## Consequences

- A request already sent can finish and record its facts in the original vault. A switch suppresses the interrupted job's result. A stale completion never wakes the current context's workers.
- Cancellation can report that work was sent or kept. Each root model-call receipt can carry the owning job.
- Registries bound active work and retained results. Registries that remember client ids keep their request records for the sidecar's lifetime, so an expired result never runs the same request again in that process.
- The desktop uses one poller with job keys and window ownership. See [[Reader workbench#Reading across the desk]], [[Add a menu verb]] and [[Reference/Modules/learnloop_sidecar/polled_jobs|Polled jobs]].

## Enforcement

`tests/test_reader_rd3_fix_backend.py` covers vault lookup, cancellation, stale completions, retention and receipts. `tests/test_hint_service.py` covers a background hint across a vault switch. The desktop's `api/poller.test.ts` covers coalescing, pause and backoff.

## What would reverse it

A durable worker or a different transport would need to prove the same vault isolation and request identity. It would need to preserve responsive reads and writes and still distinguish a request already sent from one stopped before send.
