---
title: ADR-002 Feature-owned structured AI contracts
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - docs/specs/REFACTOR_PROPOSAL.md
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

Providers implement a small `StructuredTransport.complete(StructuredRequest)` contract. Each domain owns context, prompt/version, result model, and semantic validation for its operations. Optional media and interruption capabilities are declared explicitly.

## Consequences

- New operations normally change one feature and the parity ledger, not every provider.
- Structured chat requests use the shared request envelope. The retired HTTP adapter is documented in [[ADR-018 The Codex transport is retired]].
- Feature contracts cannot depend on provider implementation details.
- Truly shared wire primitives remain in `ai.schemas`; duplicate feature models do not.

## Enforcement

The structured parity test exercises the registered operations through structured chat and asserts providers expose no feature-named methods. See [[AI Architecture#Feature-owned operations]].

