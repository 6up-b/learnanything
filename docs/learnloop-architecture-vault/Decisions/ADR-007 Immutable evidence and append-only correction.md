---
title: ADR-007 Immutable evidence and append-only correction
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - docs/algorithm-change-playbook.md
  - src/learnloop/attempts/regrade.py
  - src/learnloop/attempts/measurement_corrections.py
  - src/learnloop/attempts/reveal_ledger.py
tags:
  - learnloop/decision
  - learnloop/evidence
  - learnloop/replay
---

# ADR-007 Immutable evidence and append-only correction

## Context

Updating a historical attempt when grading/taxonomy semantics change destroys the ability to explain what was originally observed and replay old versions.

## Decision

Raw attempts, observations, contracts, and receipts are immutable. Regrades, measurement corrections, reveal/priming, taxonomy changes, and reinterpretations append explicit events or replacement projections; they never rewrite the original evidence.

## Consequences

- History remains auditable across algorithm versions.
- Read models/replay must interpret superseding events.
- Storage grows append-only but semantic debugging remains possible.

## Enforcement

Table roles, trigger/write tests, correction/regrade/reveal suites, replay equivalence, and algorithm-change playbook. See [[Evidence and Measurement#Correction]].

