---
title: ADR-003 Explicit table roles govern rebuild
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/db/table_roles.py
  - src/learnloop/substrate/rebuild_orchestrator.py
  - tests/test_table_roles.py
  - tests/test_rebuild_orchestrator.py
tags:
  - learnloop/decision
  - learnloop/persistence
  - learnloop/rebuild
---

# ADR-003 Explicit table roles govern rebuild

## Context

Names such as `*_state` do not reveal whether rows are reproducible. Several state-like tables contain reviewed or otherwise non-reconstructible artifacts; clearing them would lose authority.

## Decision

Classify every migration-head user table explicitly as RAW_LEDGER, DERIVED, RECEIPT, WORKFLOW, or COMPAT. Only DERIVED tables may be cleared, and each must have exactly one true clear-and-replay owner.

## Consequences

- Schema changes require a lifecycle decision.
- Preservation cannot be disguised as a “replayer.”
- The derived set is intentionally small (ten tables) and exact golden comparison is practical.

## Enforcement

Bidirectional registry/schema tests, synthetic unclassified-table failure, exact owner validation, stale-row injection, all-column golden equality, and idempotence. See [[State and Persistence#Table roles]].

