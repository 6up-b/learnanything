---
title: "Generated Reference Provenance"
type: "generated-provenance"
status: "current"
version: "2.0.0"
generated: true
generators:
  module_generate.py:
    source_commit: "1368f8adc2e3b00a75549cb3d2abd3462b102a53"
    source_commit_timestamp: "2026-11-20T22:20:53-05:00"
    uncommitted_inputs: []
  desktop_generate.py:
    source_commit: "1368f8adc2e3b00a75549cb3d2abd3462b102a53"
    source_commit_timestamp: "2026-11-20T22:20:53-05:00"
    uncommitted_inputs: []
  db_generate_reference.py:
    source_commit: "1368f8adc2e3b00a75549cb3d2abd3462b102a53"
    source_commit_timestamp: "2026-11-20T22:20:53-05:00"
    uncommitted_inputs:
      - "docs/learnloop-architecture-vault/_scripts/db_generate_reference.py"
      - "scripts/refactor_measures.py"
      - "src/learnloop/db/stores/collection.py"
      - "src/learnloop/db/table_roles.py"
      - "src/learnloop/field/outcomes.py"
      - "src/learnloop/params/parameter_registry.py"
      - "src/learnloop/placement/state.py"
      - "src/learnloop/substrate/dataset.py"
      - "src/learnloop/substrate/intervention_outcomes.py"
      - "tests/goldens/structure.toml"
      - "tests/test_coldness_receipt.py"
      - "tests/test_collection_dataset.py"
      - "tests/test_family_memory_projection.py"
      - "tests/test_rebuild_history_appends.py"
      - "tests/test_structure_ratchets.py"
      - "tests/test_table_roles.py"
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
| `_scripts/module_generate.py` | Reference/Modules/ (module notes, package maps, Module Catalog) | `1368f8adc2e3b00a75549cb3d2abd3462b102a53` | `2026-11-20T22:20:53-05:00` | none |
| `_scripts/desktop_generate.py` | Reference/Desktop/ (TypeScript and Rust notes, area maps, Desktop Module Catalog) | `1368f8adc2e3b00a75549cb3d2abd3462b102a53` | `2026-11-20T22:20:53-05:00` | none |
| `_scripts/db_generate_reference.py` | Reference/Database/Tables/, Reference/Configuration/Fields/, Database Catalog, Configuration Field Catalog | `1368f8adc2e3b00a75549cb3d2abd3462b102a53` | `2026-11-20T22:20:53-05:00` | 16 changed or untracked path(s), listed below |

> [!warning] `db_generate_reference.py` ran on uncommitted sources
> These inputs differed from its commit. Commit them and regenerate before landing.

- `docs/learnloop-architecture-vault/_scripts/db_generate_reference.py`
- `scripts/refactor_measures.py`
- `src/learnloop/db/stores/collection.py`
- `src/learnloop/db/table_roles.py`
- `src/learnloop/field/outcomes.py`
- `src/learnloop/params/parameter_registry.py`
- `src/learnloop/placement/state.py`
- `src/learnloop/substrate/dataset.py`
- `src/learnloop/substrate/intervention_outcomes.py`
- `tests/goldens/structure.toml`
- `tests/test_coldness_receipt.py`
- `tests/test_collection_dataset.py`
- `tests/test_family_memory_projection.py`
- `tests/test_rebuild_history_appends.py`
- `tests/test_structure_ratchets.py`
- `tests/test_table_roles.py`

`_scripts/generate_all.py` runs all three. A regeneration on a clean tree changes nothing; one after a source change touches only the notes whose facts changed, plus a generator's row here when its recorded commit moves.

Hand-written notes keep their own `source_commit_timestamp`; see [[Documentation Conventions]].
