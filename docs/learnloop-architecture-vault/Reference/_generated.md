---
title: "Generated Reference Provenance"
type: "generated-provenance"
status: "current"
version: "1.0.0"
source_commit: "f52d13b937a5a2e979b1dca0cd32681c0e76debe"
source_commit_timestamp: "2026-11-09T21:19:11-05:00"
source_worktree_state: "clean"
generated: true
source_paths:
  - "src"
  - "tests"
  - "scripts"
  - "migrations"
  - "fixtures"
  - "apps/learnloop-tauri"
  - "docs/learnloop-architecture-vault/_scripts"
tags:
  - "docs/generated"
  - "learnloop/reference"
---

# Generated Reference Provenance

Every generated note under `Reference/` was generated from the sources at one commit, recorded here once instead of in each note. It is the newest commit that changed a generator input (listed in `source_paths`), so committing a regeneration doesn't move it. ^generated-commit

| Fact | Value |
|---|---|
| Source commit | `f52d13b937a5a2e979b1dca0cd32681c0e76debe` |
| Commit timestamp | `2026-11-09T21:19:11-05:00` |
| Inputs since that commit | none |

## Generators

| Generator | Writes |
|---|---|
| `_scripts/module_generate.py` | Reference/Modules/ (module notes, package maps, Module Catalog) |
| `_scripts/desktop_generate.py` | Reference/Desktop/ (TypeScript and Rust notes, area maps, Desktop Module Catalog) |
| `_scripts/db_generate_reference.py` | Reference/Database/Tables/, Reference/Configuration/Fields/, Database Catalog, Configuration Field Catalog |

Each generator rewrites this note with the same content. A regeneration on a clean tree changes nothing; one after a source change touches only the notes whose facts changed, plus this note when the recorded commit moves.

Hand-written notes keep their own `source_commit_timestamp`; see [[Documentation Conventions]].
