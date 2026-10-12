---
title: ADR-016 Learner-blind grading with an asynchronous diagnoser
aliases:
  - Blind grading split
  - Slice 1 split decision
status: active
doc_version: 1.0.0
implementation_version: mvp-0.10
decision_date: 2026-10-12
decision_status: accepted
last_reviewed: 2026-10-12
source_commit: b71017782b0ebb640e116763383205f72a1826b6
source_commit_timestamp: "2026-10-12T04:42:11-04:00"
source_paths:
  - docs/specs/spec_blind_grading_diagnosis_split_v1.md
  - src/learnloop/attempts/blind_grading.py
  - src/learnloop/attempts/grading_support.py
  - src/learnloop/diagnosis/split/live.py
  - src/learnloop/diagnosis/split/jobs.py
  - src/learnloop/db/stores/diagnoses.py
  - src/learnloop_sidecar/post_attempt_worker.py
  - migrations/167_blind_grading_diagnosis_split.sql
  - tests/test_diagnosis_pipeline.py
  - tests/test_diagnosis_replay.py
tags:
  - learnloop/decision
  - learnloop/grading
  - learnloop/diagnosis
---

# ADR-016 Learner-blind grading with an asynchronous diagnoser

## Context

One model call used to both measure an answer and explain it, and it was handed the learner's prior traces. Every grade is evidence, so a grader primed by history could turn anchoring into evidence, while the explanation was limited to what fit in a grading prompt. The full argument and contracts are in `docs/specs/spec_blind_grading_diagnosis_split_v1.md`.

## Decision

- **Two roles.** A learner-blind grader measures the answer (score, criteria, first divergence, repaired trace, local error type, validity). An asynchronous diagnoser explains it across time from blind grades, typed prior hypotheses, the prerequisite neighbourhood and the misconception registry. The diagnoser never writes evidence.
- **The version gates it.** `mvp-0.10` (a P0 successor; `learnloop upgrade --to mvp-0.10`, owner-run) grades practice attempts blind. `diagnosis.split_enabled = false` is the kill switch: new attempts grade jointly exactly as in `mvp-0.9`.
- **Grader mode is per attempt.** A blind grade appends a `blind_grade_records` row. Replay reads that ledger, never today's config, so a vault can hold both shapes and rebuild both.
- **Causal fields come from the diagnosis on read.** A blind attempt's error events and feedback metadata carry only grader-owned fields. A completed diagnosis stores a causal view (the §4.2 mapping in reverse), and the repository lays it over the raw rows on read. Replay snapshots the raw rows and rewrites them unchanged.
- **The diagnosis is a durable job.** The submit request enqueues it in the same transaction that completes the attempt; a lease-fenced worker runs jobs in attempt order, and replay never calls a model.

## Consequences

- Submit latency does not include the diagnosis; repairs and guided redo appear when it lands, and the feedback view polls for it.
- A failed diagnosis leaves the attempt graded with no causal episode; doctor lists it and `learnloop diagnose retry` reruns it.
- Joint vaults are unchanged: no blind record means no overlay, and their rebuilds are byte-identical at the previous version.
- Calibration never pools joint and blind graders: blind grades carry their own grader identity in `raw_grade_events`.

## Related notes

- [[ADR-007 Immutable evidence and append-only correction]]
- [[ADR-003 Explicit table roles govern rebuild]]
- [[Design Decision Index]]
