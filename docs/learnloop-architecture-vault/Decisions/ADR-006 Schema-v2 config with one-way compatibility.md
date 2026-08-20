---
title: ADR-006 Schema-v2 config with one-way compatibility
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
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

Emit minimal schema-v2 configuration with canonical discriminated AI profiles. Parse schema v1/legacy input through one-way compatibility normalization; ignore documented retired keys. Split schema, compatibility, loader/environment overlay, and template/fingerprint responsibilities.

## Consequences

- New vaults have one canonical shape.
- Existing vaults load without serializing legacy forms back out.
- Omitted defaults are frozen by algorithm-version fingerprint instead of bloating every file.

## Enforcement

Fixture-equivalence, default fingerprint, config-owner, schema/profile, and init tests. See [[Configuration]].

