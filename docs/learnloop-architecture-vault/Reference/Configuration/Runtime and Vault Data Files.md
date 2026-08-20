---
title: "Runtime and Vault Data Files"
status: "current"
doc_version: "1.0"
architecture_version: "post-refactor"
source_commit: "62fd1f6404cc3a3007c6f214ba9429c45ef0114f"
source_commit_timestamp: "2026-08-17T12:05:21-04:00"
last_verified: "2026-08-17"
aliases:
  - "Vault file formats"
  - "LearnLoop data files"
source_paths:
  - "src/learnloop/vault/paths.py"
  - "src/learnloop/vault/loader.py"
  - "src/learnloop/vault/models.py"
  - "src/learnloop/ingest/originals.py"
  - "tests/test_init.py"
  - "tests/test_subject_registry.py"
tags:
  - "learnloop/configuration/files"
  - "learnloop/vault/layout"
  - "learnloop/status/active"
---

# Runtime and Vault Data Files

The TOML config is only one part of a vault. LearnLoop deliberately separates human-reviewable authored definitions from machine state and derived assets. The authority boundary is explained in [[State and Persistence]]; this note is the file lookup map. ^vault-files-scope

## Vault-level files

| Path | Created | Function / authority |
|---|---|---|
| `learnloop.toml` | init | Required vault marker and typed override file; see [[learnloop.toml]] |
| `AGENTS.md` | init | Guardrail telling coding agents that the directory is user data |
| `concepts/concepts.yaml` | init | Canonical concept registry |
| `concepts/relations.yaml` | init | Canonical concept edges |
| `facets.yaml` | init | Canonical evidence-facet registry and aliases |
| `errors/error_types.yaml` | init | Error taxonomy; init seeds recall, scaffold, and arithmetic-slip types |
| `profile/goals.yaml` | init | Typed goals file loaded by the vault loader |
| `profile/goals.md` | init | Human-readable goal notes retained as a scaffolded surface |
| `profile/learner.yaml` | optional starting level | Human-editable declared learner starting level |
| `state.sqlite` or configured path | init | Durable machine state; see [[Database]] |
| `.learnloop/vault.lock` | first migration/mutation | Advisory cross-process lock metadata; blank while unlocked |

## Subject tree

`subjects/<subject-id>/` is created by `learnloop add-subject` or `learnloop init --subject`:

| Path | Function |
|---|---|
| `subject.md` | Subject metadata in YAML frontmatter plus human notes |
| `concept-graph.yaml` | Subject scope, exclusions, and ordering hints |
| `learning-objects/*.yaml` | Learning-object contracts |
| `practice-items/*.yaml` | Practice surfaces, rubrics, evidence facets, and source refs |
| `notes/*.md` | Learner/canonical/imported notes with frontmatter |

The loader validates cross-file IDs and reports issues rather than silently repairing authored content.

## Source library

New canonical sources live at vault level rather than under a subject:

- `sources/source_sets.yaml` — named pinned source sets;
- `sources/<source-id>/source.md` — work metadata and current revision pointer;
- `sources/<source-id>/revisions/<revision-id>.md` — immutable normalized display revision;
- content-addressed original bytes under the raw source store;
- `.learnloop/source-cache/extractions/<extraction-id>/` — derived IR/assets/cache.

Legacy subject-scoped source notes remain readable in place forever. End-to-end import behavior is documented in the vault's source-ingestion workflow notes rather than duplicated here.

## Optional/generated files

- `rubrics/*.yaml` — default rubric by practice mode.
- `media/animations/<hash>.mp4` — content-addressed animation render.
- `.env` — optional vault-local machine environment, never created by init.
- `.learnloop/source-cache/` — extraction cache, created on demand.

> [!note] Directories init intentionally does not create
> `prompts/`, `sessions/`, `exports/`, `.learnloop/backups/`, and `.learnloop/session-checkpoints/` are abandoned/absent surfaces, not missing scaffolding.

## Modification guidance

Use `VaultPaths` for canonical locations and `vault/yaml_io.py` for YAML/frontmatter I/O. Add file schemas to `vault/models.py`, preserve idempotent scaffold guards, and add loader/doctor tests for any new authority-bearing file.
