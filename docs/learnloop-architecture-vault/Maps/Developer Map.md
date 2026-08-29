---
title: Developer Map
aliases:
  - Developer MOC
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - ARCHITECTURE.md
  - tests/test_architecture.py
  - pyproject.toml
tags:
  - learnloop/development
  - moc
---

# Developer Map

## Start with the behavior, not the filename

| Change | Primary authority | Then inspect |
|---|---|---|
| scoring/evidence interpretation | [[Learning System]] and `attempts/` | [[Algorithm Versions and Reproducibility]], [[Attempt Processing]] |
| next-item policy | [[Scheduling and Selection]] and `scheduling/` | scheduler goldens, controller/constraint modules |
| provider or route | [[AI Architecture]] | `ai/routing.py`, provider profile config, parity tests |
| a structured AI operation | owning domain `ai_contracts.py` | [[ADR-002 Feature-owned structured AI contracts]] |
| new persistent state | [[State and Persistence]] | table role, write owner, migration, rebuild tests |
| source ingestion job | [[Content Pipeline]] | `content/pipeline/runner.py`, `jobs.py`, queue store |
| CLI command | `cli/` public domain API | help snapshot and adapter-independence tests |
| desktop screen or RPC | [[Desktop Architecture]] and [[Desktop Module Catalog]] | DTO, Rust command registration, sidecar method, serializer/RPC contract tests |
| compatibility behavior | `substrate/compat/` | fixture-backed explicit decision |

## Safe change sequence

1. Locate the concept authority and affected workflow.
2. Open relevant notes in [[Module Catalog]] and [[Database Catalog]].
3. Identify the executable oracle in **Important tests**.
4. Preserve package direction from [[Package Boundaries]].
5. If persisted meaning changes, follow [[Algorithm Versions and Reproducibility#Change protocol]].
6. Run focused tests, import contracts, architecture tests, and the full suite.

> [!failure] Common wrong turns
> - Adding provider-named methods instead of a feature-owned structured operation.
> - Writing raw SQL from a second owner.
> - Clearing a table because it “looks derived” without proving a lossless replay source.
> - Importing a private underscore name across a package boundary.
> - Making one adapter import another.
> - Reusing an algorithm version after changing persisted meaning.

## Oracles

- [[Testing and Invariants]]
- `tests/test_architecture.py`
- `tests/test_structured_transport_parity.py`
- `tests/test_provider_resolution_parity.py`
- `tests/test_rebuild_orchestrator.py`
- `tests/test_attempt_write_order.py`
- `tests/test_cli_help_snapshot.py`
- `tests/test_sidecar_serializer_snapshot.py`
