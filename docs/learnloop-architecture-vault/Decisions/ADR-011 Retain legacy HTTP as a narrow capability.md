---
title: ADR-011 Retain legacy HTTP as a narrow capability
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/ai/providers/codex_http.py
  - src/learnloop/ai/transport.py
  - tests/test_structured_transport_parity.py
tags:
  - learnloop/decision
  - learnloop/ai
  - learnloop/compatibility
---

# ADR-011 Retain legacy HTTP as a narrow capability

## Context

The HTTP endpoint adapter cannot provide an arbitrary `complete()` operation; it has endpoint-specific support for a historical subset. Pretending otherwise would make the protocol false, while deletion would remove an explicitly retained integration.

## Decision

Keep HTTP as an optional `OperationClient` with generic `complete_legacy` and exact capability declarations. It supports exactly eight known operations; all others fail locally with `AIProviderUnavailable` and make no request.

## Consequences

- The shared structured protocol remains honest.
- Features can retain compatible endpoint behavior during migration.
- New operations are unsupported unless deliberately implemented and added to the exact capability oracle.

## Enforcement

The 23-operation parity ledger proves exact-eight support and zero-egress degradation for the rest. See [[AI Architecture#Transport contract]].

