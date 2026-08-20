---
title: ADR-004 AI is optional and manual is typed
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/ai/routing.py
  - tests/test_provider_resolution_parity.py
tags:
  - learnloop/decision
  - learnloop/ai
  - learnloop/manual
---

# ADR-004 AI is optional and manual is typed

## Context

Provider availability is environmental. Treating manual mode as a broken/fake client made fallback ambiguous and risked coupling storage/scheduling to external services.

## Decision

Model manual as a first-class `ResolvedClient` no-client outcome. Core vault creation, storage, replay, scheduling, doctor, and manual/self-graded practice remain functional without a provider.

## Consequences

- Features must declare whether AI is required, optional, or manually substitutable.
- Provider diagnostics run only when explicitly relevant.
- Tests can distinguish manual policy from unavailable configuration.

## Enforcement

The six-path provider matrix covers manual, fallback, explicit selection, and disabled providers. See [[AI Architecture#Failure and manual behavior]].

