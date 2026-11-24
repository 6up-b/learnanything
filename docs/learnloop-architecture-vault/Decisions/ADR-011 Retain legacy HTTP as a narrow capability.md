---
title: ADR-011 Retain legacy HTTP as a narrow capability
status: historical
doc_version: 1.1.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: superseded
superseded_by: ADR-018 The Codex transport is retired
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/ai/agent_harness.py
  - src/learnloop/ai/transport.py
  - tests/test_structured_transport_parity.py
tags:
  - learnloop/decision
  - learnloop/ai
  - learnloop/compatibility
---

# ADR-011 Retain legacy HTTP as a narrow capability

Superseded by [[ADR-018 The Codex transport is retired]]. This decision kept an eight-operation HTTP adapter during the earlier migration. The adapter and its parity row were removed in C4. See [[AI Architecture#Transport contract]] for the supported structured transport.
