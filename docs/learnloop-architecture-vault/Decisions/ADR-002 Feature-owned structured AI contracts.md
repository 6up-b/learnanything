---
title: ADR-002 Feature-owned structured AI contracts
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - REFACTOR_PROPOSAL.md
  - src/learnloop/ai/transport.py
  - tests/test_structured_transport_parity.py
tags:
  - learnloop/decision
  - learnloop/ai
---

# ADR-002 Feature-owned structured AI contracts

## Context

A provider protocol with one named method per feature required every provider to change whenever one domain added an operation. Central prompt/context/schema files also separated operation meaning from its owner.

## Decision

Providers implement a small `StructuredTransport.complete(StructuredRequest)` contract. Each domain owns context, prompt/version, result model, and semantic validation for its operations. Optional media/interrupt and retained HTTP capabilities are declared explicitly.

## Consequences

- New operations normally change one feature and the parity ledger, not every provider.
- SDK/chat parity is constructed through the shared request envelope.
- Feature contracts cannot depend on provider implementation details.
- Truly shared wire primitives remain in `ai.schemas`; duplicate feature models do not.

## Enforcement

The structured parity test exercises every operation through both transports and asserts providers expose no feature-named methods. See [[AI Architecture#Feature-owned operations]].

