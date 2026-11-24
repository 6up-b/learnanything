---
title: ADR-006 Schema-v2 config with one-way compatibility
status: active
doc_version: 1.0.0
implementation_version: mvp-0.68
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-11-23
source_commit: 86f29b0d390ed2ecdbb0347d98ccb1175ac52728
source_commit_timestamp: "2026-11-23T23:12:28-05:00"
source_paths:
  - src/learnloop/config/schema.py
  - src/learnloop/config/compat.py
  - src/learnloop/config/loader.py
  - src/learnloop/config/template.py
tags:
  - learnloop/decision
  - learnloop/config
  - learnloop/compatibility
---

# ADR-006 Schema-v2 config with one-way compatibility

## Context

Legacy `[codex]`, aliases, and dead keys had to remain readable, but emitting them would perpetuate two authorities. A huge config module also mixed schema, loading, normalization, and template ownership.

## Decision

Emit minimal schema-v2 configuration with canonical discriminated AI profiles. Parse schema v1/legacy input through one-way compatibility normalization; ignore documented retired keys. Split schema, compatibility, loader/environment overlay, and template responsibilities.

## Consequences

- New vaults have one canonical shape.
- Existing vaults load without serializing legacy forms back out.
- Omitted values come from the typed schema. The effective-defaults golden records the resolved values in a single readable file. A changed default appears as its own line in review.

## Enforcement

Fixture-equivalence, effective-defaults golden, config-owner, schema/profile, and init tests. See [[Configuration]].

