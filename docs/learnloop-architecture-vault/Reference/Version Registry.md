---
title: Version Registry
aliases:
  - Current Versions
status: active
doc_version: 1.0.0
implementation_version: mvp-0.9
last_reviewed: 2026-08-17
source_commit: 62fd1f6404cc3a3007c6f214ba9429c45ef0114f
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
source_paths:
  - pyproject.toml
  - src/learnloop/algorithm_versions.py
  - src/learnloop/config/schema.py
  - migrations
tags:
  - learnloop/reference
  - learnloop/version
  - learnloop/status
---

# Version Registry

| Version axis | Current value | Meaning |
|---|---|---|
| Python package | `0.1.0` | distribution version in `pyproject.toml` |
| Python runtime | `>=3.12` | supported interpreter floor |
| algorithm | `mvp-0.9` | persisted reveal-aware learning semantics |
| canonical projection base | `mvp-0.8` semantics | inherited by mvp-0.9 |
| knowledge-model activation | `mvp-0.7` | canonical state/contracts boundary |
| config schema | `2` | emitted `learnloop.toml`; schema 1 accepted |
| SQLite migration head | `156` | current schema ledger maximum |
| documentation | `1.0.0` | initial architecture-vault release |
| source inventory commit | `62fd1f6404cc…` | baseline commit plus current refactor worktree |

> [!important] Independent axes
> Package, schema, config, algorithm, prompt, contract, and documentation versions solve different problems. Never infer one from another.

## Per-artifact versions

Assessment contracts, prompt contracts, AI prompt versions, probe families, goal terminal contracts, and source revisions carry their own identities. Their module/table notes link to the exact owner.

## Change guidance

- Algorithm semantics: [[Algorithm Versions and Reproducibility#Change protocol]].
- Config/schema: [[Configuration]] and [[ADR-006 Schema-v2 config with one-way compatibility]].
- SQLite: [[State and Persistence#Open modes and migrations]].
- Documentation metadata: [[Documentation Conventions#Frontmatter contract]].

