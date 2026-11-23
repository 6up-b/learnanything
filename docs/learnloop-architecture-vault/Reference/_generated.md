---
title: "Generated Reference Provenance"
type: "generated-provenance"
status: "current"
version: "2.0.0"
generated: true
generators:
  module_generate.py:
    source_commit: "943a2420403538d0c7b933ca2d288da00e5290e9"
    source_commit_timestamp: "2026-11-23T01:39:03-05:00"
    uncommitted_inputs:
      - "tests/goldens/structure.toml"
      - "tests/goldens/synthesis_normalize/append_links_restructure.json"
      - "tests/goldens/synthesis_normalize/blueprints.json"
      - "tests/goldens/synthesis_normalize/concept_references.json"
      - "tests/goldens/synthesis_normalize/edges.json"
      - "tests/goldens/synthesis_normalize/nominator_fails.json"
      - "tests/goldens/synthesis_normalize/practice_items.json"
      - "tests/goldens/synthesis_normalize/practice_items_off.json"
      - "tests/goldens/synthesis_normalize/retirements_skipped.json"
      - "tests/goldens/synthesis_normalize/reword_refused.json"
  desktop_generate.py:
    source_commit: "943a2420403538d0c7b933ca2d288da00e5290e9"
    source_commit_timestamp: "2026-11-23T01:39:03-05:00"
    uncommitted_inputs:
      - "tests/goldens/structure.toml"
      - "tests/goldens/synthesis_normalize/append_links_restructure.json"
      - "tests/goldens/synthesis_normalize/blueprints.json"
      - "tests/goldens/synthesis_normalize/concept_references.json"
      - "tests/goldens/synthesis_normalize/edges.json"
      - "tests/goldens/synthesis_normalize/nominator_fails.json"
      - "tests/goldens/synthesis_normalize/practice_items.json"
      - "tests/goldens/synthesis_normalize/practice_items_off.json"
      - "tests/goldens/synthesis_normalize/retirements_skipped.json"
      - "tests/goldens/synthesis_normalize/reword_refused.json"
  db_generate_reference.py:
    source_commit: "943a2420403538d0c7b933ca2d288da00e5290e9"
    source_commit_timestamp: "2026-11-23T01:39:03-05:00"
    uncommitted_inputs:
      - "tests/goldens/structure.toml"
      - "tests/goldens/synthesis_normalize/append_links_restructure.json"
      - "tests/goldens/synthesis_normalize/blueprints.json"
      - "tests/goldens/synthesis_normalize/concept_references.json"
      - "tests/goldens/synthesis_normalize/edges.json"
      - "tests/goldens/synthesis_normalize/nominator_fails.json"
      - "tests/goldens/synthesis_normalize/practice_items.json"
      - "tests/goldens/synthesis_normalize/practice_items_off.json"
      - "tests/goldens/synthesis_normalize/retirements_skipped.json"
      - "tests/goldens/synthesis_normalize/reword_refused.json"
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
| `_scripts/module_generate.py` | Reference/Modules/ (module notes, package maps, Module Catalog) | `943a2420403538d0c7b933ca2d288da00e5290e9` | `2026-11-23T01:39:03-05:00` | 10 changed or untracked path(s), listed below |
| `_scripts/desktop_generate.py` | Reference/Desktop/ (TypeScript and Rust notes, area maps, Desktop Module Catalog) | `943a2420403538d0c7b933ca2d288da00e5290e9` | `2026-11-23T01:39:03-05:00` | 10 changed or untracked path(s), listed below |
| `_scripts/db_generate_reference.py` | Reference/Database/Tables/, Reference/Configuration/Fields/, Database Catalog, Configuration Field Catalog | `943a2420403538d0c7b933ca2d288da00e5290e9` | `2026-11-23T01:39:03-05:00` | 10 changed or untracked path(s), listed below |

> [!warning] `module_generate.py` ran on uncommitted sources
> These inputs differed from its commit. Commit them and regenerate before landing.

- `tests/goldens/structure.toml`
- `tests/goldens/synthesis_normalize/append_links_restructure.json`
- `tests/goldens/synthesis_normalize/blueprints.json`
- `tests/goldens/synthesis_normalize/concept_references.json`
- `tests/goldens/synthesis_normalize/edges.json`
- `tests/goldens/synthesis_normalize/nominator_fails.json`
- `tests/goldens/synthesis_normalize/practice_items.json`
- `tests/goldens/synthesis_normalize/practice_items_off.json`
- `tests/goldens/synthesis_normalize/retirements_skipped.json`
- `tests/goldens/synthesis_normalize/reword_refused.json`

> [!warning] `desktop_generate.py` ran on uncommitted sources
> These inputs differed from its commit. Commit them and regenerate before landing.

- `tests/goldens/structure.toml`
- `tests/goldens/synthesis_normalize/append_links_restructure.json`
- `tests/goldens/synthesis_normalize/blueprints.json`
- `tests/goldens/synthesis_normalize/concept_references.json`
- `tests/goldens/synthesis_normalize/edges.json`
- `tests/goldens/synthesis_normalize/nominator_fails.json`
- `tests/goldens/synthesis_normalize/practice_items.json`
- `tests/goldens/synthesis_normalize/practice_items_off.json`
- `tests/goldens/synthesis_normalize/retirements_skipped.json`
- `tests/goldens/synthesis_normalize/reword_refused.json`

> [!warning] `db_generate_reference.py` ran on uncommitted sources
> These inputs differed from its commit. Commit them and regenerate before landing.

- `tests/goldens/structure.toml`
- `tests/goldens/synthesis_normalize/append_links_restructure.json`
- `tests/goldens/synthesis_normalize/blueprints.json`
- `tests/goldens/synthesis_normalize/concept_references.json`
- `tests/goldens/synthesis_normalize/edges.json`
- `tests/goldens/synthesis_normalize/nominator_fails.json`
- `tests/goldens/synthesis_normalize/practice_items.json`
- `tests/goldens/synthesis_normalize/practice_items_off.json`
- `tests/goldens/synthesis_normalize/retirements_skipped.json`
- `tests/goldens/synthesis_normalize/reword_refused.json`

`_scripts/generate_all.py` runs all three. A regeneration on a clean tree changes nothing; one after a source change touches only the notes whose facts changed, plus a generator's row here when its recorded commit moves.

Hand-written notes keep their own `source_commit_timestamp`; see [[Documentation Conventions]].
