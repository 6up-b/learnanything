---
title: "Generated Reference Provenance"
type: "generated-provenance"
status: "current"
version: "2.0.0"
generated: true
generators:
  module_generate.py:
    source_commit: "195c2c91ae7d02ae1adfee0e2e0af635fe422a06"
    source_commit_timestamp: "2026-11-14T02:37:33-05:00"
    uncommitted_inputs: []
  desktop_generate.py:
    source_commit: "195c2c91ae7d02ae1adfee0e2e0af635fe422a06"
    source_commit_timestamp: "2026-11-14T02:37:33-05:00"
    uncommitted_inputs: []
  db_generate_reference.py:
    source_commit: "195c2c91ae7d02ae1adfee0e2e0af635fe422a06"
    source_commit_timestamp: "2026-11-14T02:37:33-05:00"
    uncommitted_inputs: []
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

Each generator records here the commit its notes were generated from, instead of in each note. It is the newest commit that changed a generator input (listed in `source_paths`) when that generator last ran, so committing a regeneration doesn't move it. A generator rewrites only its own row: running one alone never vouches for another's notes. ^generated-commit

| Generator | Writes | Source commit | Commit timestamp | Inputs since that commit |
|---|---|---|---|---|
| `_scripts/module_generate.py` | Reference/Modules/ (module notes, package maps, Module Catalog) | `195c2c91ae7d02ae1adfee0e2e0af635fe422a06` | `2026-11-14T02:37:33-05:00` | none |
| `_scripts/desktop_generate.py` | Reference/Desktop/ (TypeScript and Rust notes, area maps, Desktop Module Catalog) | `195c2c91ae7d02ae1adfee0e2e0af635fe422a06` | `2026-11-14T02:37:33-05:00` | none |
| `_scripts/db_generate_reference.py` | Reference/Database/Tables/, Reference/Configuration/Fields/, Database Catalog, Configuration Field Catalog | `195c2c91ae7d02ae1adfee0e2e0af635fe422a06` | `2026-11-14T02:37:33-05:00` | none |

`_scripts/generate_all.py` runs all three. A regeneration on a clean tree changes nothing; one after a source change touches only the notes whose facts changed, plus a generator's row here when its recorded commit moves.

Hand-written notes keep their own `source_commit_timestamp`; see [[Documentation Conventions]].
