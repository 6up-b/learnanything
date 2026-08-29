---
title: Content Pipeline
aliases:
  - Canonical Source Pipeline
  - Ingest Architecture
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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

The content pipeline turns trusted external material into immutable source records, structured Document IR, reviewed source-set membership, and canonical learning content. Acquisition/extraction mechanics live in infrastructure `learnloop.ingest`; workflow and synthesis ownership live in `learnloop.content`.

The authority/provenance meaning of each artifact lives in [[Source Authority and Provenance]].

## Durable checkpoint ladder

```mermaid
flowchart LR
    A[acquired] --> R[registered]
    R --> E[extracted]
    E --> I[inventoried]
    I --> S[synthesized]
    S --> P[proposed]
    P --> AP[applied]
```

Each stage is independently resumable. Batches, jobs, and dependencies live in SQLite. A queued job runs only when all dependencies completed; failed/blocked/cancelled prerequisites block downstream work rather than misreporting it as failed.

^checkpoint-ladder

## Stages and authorities

1. **Acquire:** fetch local bytes or remote content under explicit source/consent policy.
2. **Register:** content-address the asset and immutable revision; repeated bytes reuse identity.
3. **Extract:** produce Document IR with blocks, anchors, metadata, and health flags.
4. **Inventory:** use deterministic structure plus a routed structured provider to identify units/concepts when configured.
5. **Source-set assembly:** pin a revision and record role, authority, scope, and selection.
6. **Synthesize:** bootstrap a new map or reconcile an append against existing canonical content.
7. **Propose/apply:** validate authored output and persist canonical files/receipts.

The model never receives authority merely by returning JSON. Feature-owned synthesis contracts validate shape; domain gates validate references, coverage, provenance, and allowed mutations before application.

## Durable runner semantics

- One vault-writing worker holds a lease; bounded DB-only work may use a compatible parallel lane.
- `waiting_for_input` holds no lease, so consent/unit/budget questions do not stop unrelated jobs.
- Worker identity and heartbeat make stale running jobs recoverable.
- Retry identity is stage-specific and reuses completed revisions/extractions rather than duplicating them.
- Usage accumulates across attempts instead of being overwritten.
- Cancellation is observed through progress reporting and optional interrupt capabilities.

## Extraction choices

Local files, websites, YouTube/captions, Markdown/text, PDFs, and audio follow typed extractors. PDFs honor per-job/vault engine selection and may degrade from optional Marker extraction to pypdf with a visible health flag unless Marker was explicitly forced. Audio uses the dedicated transcription route and consent policy from [[AI Architecture#Task routes]].

## Legacy compatibility

The gen-2 source-ingestion implementation remains available through frozen `legacy_ingest` and `exam_ingest` queue aliases. The durable runner presents corrected effective status for known historical result/status mismatches while preserving raw audit records.

## Modification guidance

- Add acquisition/extraction mechanics under `learnloop.ingest`; keep workflow decisions in `content.pipeline`.
- Add a job type to the runner vocabulary, handler registry, durable queue tests, serializers, and restart/retry tests.
- Preserve idempotency identity and checkpoint semantics.
- Route new model work through [[AI Architecture]], never a local client factory.
- Keep source revisions immutable; append a new revision or proposal rather than mutating captured bytes.

## Workflows and tests

- [[Import Canonical Sources]]
- [[Build a Study Map]]
- [[Doctor Migrations and Recovery]]
- `tests/test_ingest_runner.py`
- `tests/test_ingest_jobs.py`
- `tests/test_ingest_queue_store.py`
- `tests/test_ingest_m3.py`
- `tests/test_inventory_merge_parallel.py`
- source extraction/transcript tests
