---
title: ADR-001 Domain ownership replaces generic services
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
  - ARCHITECTURE.md
tags:
  - learnloop/decision
  - learnloop/refactor
  - learnloop/domains
---

# ADR-001 Domain ownership replaces generic services

## Context

The former `learnloop.services` namespace contained hundreds of unrelated modules. Its path conveyed no ownership and made AI, persistence, adapters, and learning policy appear to be peers.

## Decision

Delete the generic layer and move behavior into cohesive domains: attempts, learner, scheduling, goals, diagnosis, curriculum, substrate, content, reader, tutor, ops, and params. Keep infrastructure (`db`, `ai`, `config`, `vault`, `ingest`) below those domains.

## Consequences

- A behavior has a discoverable owner and feature contracts can be colocated.
- Cross-domain edges remain visible; some cycles are frozen debt rather than hidden behind `services`.
- Imports and tests required broad migration, but no long-lived compatibility namespace remains inside the repository.

## Enforcement

No `learnloop.services` package/reference remains. Import-linter and architecture tests enforce layer direction and public names. See [[Architecture Overview#Domain ownership]] and [[Module Catalog]].

