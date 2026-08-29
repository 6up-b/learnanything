---
title: ADR-009 Architecture rules are executable ratchets
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
decision_date: 2026-08-17
decision_status: accepted
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - pyproject.toml
  - tests/test_architecture.py
  - tests/architecture_function_local_domain_imports.txt
tags:
  - learnloop/decision
  - learnloop/architecture
  - learnloop/testing
---

# ADR-009 Architecture rules are executable ratchets

## Context

Package diagrams drift when imports, lazy imports, dynamic strings, SQL, and private helpers are unconstrained. A ban with no failing example can be vacuous.

## Decision

Encode layer rules in import-linter and AST/runtime tests. Freeze surviving cycle/function-local edges exactly; inventories may shrink but not grow. Each custom detector has a synthetic violation test.

## Consequences

- Architectural drift fails CI near the change.
- Existing debt is visible and reducible.
- Dynamic module references and f-string SQL count as architecture.

## Enforcement

Six kept import contracts plus architecture tests for infrastructure edges, private names, local imports, SQL owners, module importability, and constructed references. See [[Package Boundaries]].

