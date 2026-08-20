---
title: ADR-005 Independent adapters
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - src/learnloop/cli
  - src/learnloop/tui
  - src/learnloop_sidecar
  - src/learnloop/app_launch.py
  - pyproject.toml
tags:
  - learnloop/decision
  - learnloop/adapters
---

# ADR-005 Independent adapters

## Context

CLI, TUI, and sidecar previously reused one another's helpers, turning presentation choices into indirect runtime dependencies and making headless behavior difficult to test.

## Decision

Each adapter calls public domain/application APIs and owns only translation/rendering. Adapters do not import one another. Cross-surface launch coordination lives in neutral `app_launch`.

## Consequences

- Domain behavior is reusable without importing UI stacks.
- Public CLI help and sidecar DTOs have separate compatibility oracles.
- Shared behavior must be promoted to a neutral/public owner, not copied from a private adapter helper.

## Enforcement

Three import-linter contracts, private-import AST scans, CLI help snapshot, and sidecar serializer snapshot. See [[Adapter Architecture]].

